"""Scheduler boundary behavior at the headline operating points.

The production scheduler applies two boundary choices the stated experiment does
not ask for:

1. Strict completion (ahgs.py): a universe counts as complete only when its
   detections *exceed* the sample size (51 for a stated 50), and an experiment
   completes only when the count of such universes *exceeds*
   opt_limit_factor * num_universe (91 for a stated 90 of 100).
2. Empty-universe omission (ams.py): universes with zero surviving detections
   are dropped from the 90th-percentile mission time.

The two act in opposite directions. This script measures each effect separately
and jointly at every headline operating point of Table 5.1, using the unrounded
reproduction amplitudes of Table B.2, plus the zero-budget time of every
configuration.

Modes:
    strict     historical behavior (baseline, reproduces the thesis numbers)
    nonstrict  completion at >= sample_size in >= ceil(factor * N) universes
    retain     empty universes kept in the percentile, strict completion
    corrected  both corrections together

One (design, catalog) pair per invocation so cells can run as independent jobs:

    python scheduler_boundary.py --design bracewell4 --catalog hi
"""
import argparse
import os
import sys
import time

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, REPO)
_cwd = os.getcwd()
import lifesim
os.chdir(_cwd)

from lifesim.ams.ablation_throughput import build_bus, ARMS, make_setter, FAMILIES
from lifesim.ams.core.ams import AgnosticMissionSimulator
from lifesim.util.combiner import double_bracewell, double_triple_nuller

GRADIENT = {v: k for k, v in FAMILIES.items()}      # family name -> setter key
OUTDIR = os.path.join(REPO, 'thesis', 'reproducibility', 'scheduler_boundary')

# Unrounded reproduction amplitudes of Table B.2 (ph/s/um), keyed by
# (design, catalog, target): (flat, short_weighted, long_weighted).
TABLE_B2 = {
    ('bracewell4', 'hi', 5.5): (142.4, 298.3, 210.5),
    ('bracewell4', 'hi', 6.0): (610.3, 1303.1, 1089.3),
    ('bracewell4', 'lo', 7.5): (62.2, 197.9, 156.7),
    ('bracewell4', 'lo', 8.0): (462.8, 973.9, 810.1),
    ('triple6', 'hi', 4.0): (241.4, 403.1, 556.9),
    ('triple6', 'hi', 4.5): (701.6, 1384.9, 1762.0),
    ('triple6', 'lo', 5.5): (177.3, 226.1, 602.2),
    ('triple6', 'lo', 6.0): (409.0, 733.9, 1313.7),
}
FAMILY_ORDER = ('flat', 'short_weighted', 'long_weighted')

MODES = {
    'strict': dict(strict_completion=True, retain_empty_universes=False),
    'nonstrict': dict(strict_completion=False, retain_empty_universes=False),
    'retain': dict(strict_completion=True, retain_empty_universes=True),
    'corrected': dict(strict_completion=False, retain_empty_universes=True),
}

ap = argparse.ArgumentParser()
ap.add_argument('--design', choices=['bracewell4', 'triple6'], required=True)
ap.add_argument('--catalog', choices=['hi', 'lo'], required=True)
ap.add_argument('--n-cpu', type=int, default=2)
a = ap.parse_args()

os.makedirs(OUTDIR, exist_ok=True)
tag = f'{a.design}_{a.catalog}'
out = os.path.join(OUTDIR, tag + '.tsv')

bus, instrument, opt = build_bus(a.catalog, ARMS['control'])
bus.data.options.other['n_cpu'] = a.n_cpu
widths = bus.data.inst['wl_bin_widths'] * 1e6
ratio = bus.data.options.array['ratio']
arch = (double_triple_nuller(1.0, ratio) if a.design == 'triple6'
        else double_bracewell(1.0, ratio))
order = 4 if a.design == 'triple6' else 2

ams = AgnosticMissionSimulator(order, 7, 65 / 360 * 2 * np.pi, 0.8, 12 * 3600,
                               architecture=arch, verbose=False)

targets = sorted(t for d, c, t in TABLE_B2 if d == a.design and c == a.catalog)

# Evaluation points: the zero-budget time once, then every Table B.2 amplitude.
points = [('zero', 'flat', 0.0)]
for t in targets:
    amps = TABLE_B2[(a.design, a.catalog, t)]
    points += [(t, fam, amp) for fam, amp in zip(FAMILY_ORDER, amps)]

rows = []
print(f'=== {tag}: {len(points)} evaluation points x {len(MODES)} modes', flush=True)
for target, family, amp in points:
    setter = make_setter(bus, ams, GRADIENT[family], widths)
    setter(amp)
    for mode, flags in MODES.items():
        bus.data.options.optimization['strict_completion'] = flags['strict_completion']
        bus.data.options.optimization['retain_empty_universes'] = flags['retain_empty_universes']
        t0 = time.time()
        mtime = ams.run(instrument, opt)
        wall = round(time.time() - t0, 1)
        n_uni = len(ams.last_time_sheet)
        rows.append(f'{a.design}\thab2{a.catalog}\t{target}\t{family}\t{amp}\t'
                    f'{mode}\t{mtime:.4f}\t{n_uni}\t{wall}')
        print(f'  {target} {family} {amp}: {mode:<10} {mtime:.4f} yr '
              f'({n_uni} universes, {wall}s)', flush=True)

with open(out, 'w') as fh:
    fh.write('design\tcatalog\ttarget_yr\tfamily\tamplitude_ph_s_um\tmode\t'
             'mtime_yr\tn_universes\twall_s\n')
    fh.write('\n'.join(rows) + '\n')
print(f'wrote {out}')

# Summary: effect of each correction against the strict baseline.
print(f'\n=== {tag} summary (delta vs strict, yr)')
by_key = {}
for r in rows:
    f_ = r.split('\t')
    by_key[(f_[2], f_[3], f_[5])] = float(f_[6])
for target, family, amp in points:
    base = by_key[(str(target), family, 'strict')]
    deltas = {m: by_key[(str(target), family, m)] - base
              for m in ('nonstrict', 'retain', 'corrected')}
    print(f'  {target} {family}: strict {base:.4f}  '
          + '  '.join(f'{m} {d:+.4f}' for m, d in deltas.items()), flush=True)
