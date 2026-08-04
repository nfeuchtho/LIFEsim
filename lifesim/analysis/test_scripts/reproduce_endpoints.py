"""Re-derive the Table 5.1/B.2 endpoint amplitudes on the production catalog.

Same search as the production campaign (locate_mission_cutoff at each cell of
Table 5.1), no bootstrap resampling. The --scheduler flag selects the historical
strict completion or the corrected behavior measured by scheduler_boundary.py,
so the two endpoint sets can be compared cell by cell.

One (design, catalog) pair per invocation:

    python reproduce_endpoints.py --design bracewell4 --catalog hi \
        --scheduler corrected
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
from lifesim.ams.trade_space_explorer import TradeSpaceExplorer
from lifesim.util.combiner import double_bracewell, double_triple_nuller, kernel5, collinear4

DESIGNS = {'bracewell4': (lambda r: double_bracewell(1.0, r), 2),
           'triple6': (lambda r: double_triple_nuller(1.0, r), 4),
           'kernel5_deep': (lambda r: kernel5(1.0, 'deep'), 4),
           'kernel5_shallow': (lambda r: kernel5(1.0, 'shallow'), 2),
           'collinear4': (lambda r: collinear4(1.0), 4)}

GRADIENT = {v: k for k, v in FAMILIES.items()}
OUTDIR = os.path.join(REPO, 'thesis', 'reproducibility', 'scheduler_boundary')

TARGETS = {('bracewell4', 'hi'): (5.5, 6.0), ('bracewell4', 'lo'): (7.5, 8.0),
           ('triple6', 'hi'): (4.0, 4.5), ('triple6', 'lo'): (5.5, 6.0)}
FAMILY_ORDER = ('flat', 'short_weighted', 'long_weighted')

ap = argparse.ArgumentParser()
ap.add_argument('--design', choices=list(DESIGNS), required=True)
ap.add_argument('--targets', type=str, default=None,
                help='comma-separated mission-time targets in years; overrides '
                     'the built-in TARGETS table (required for kernel5 designs)')
ap.add_argument('--catalog', choices=['hi', 'lo'], required=True)
ap.add_argument('--scheduler', choices=['strict', 'corrected'], required=True)
ap.add_argument('--upper-start', type=int, default=20000)
ap.add_argument('--n-cpu', type=int, default=2)
a = ap.parse_args()

os.makedirs(OUTDIR, exist_ok=True)
tag = f'endpoints_{a.design}_{a.catalog}_{a.scheduler}'
out = os.path.join(OUTDIR, tag + '.tsv')

bus, instrument, opt = build_bus(a.catalog, ARMS['control'])
bus.data.options.other['n_cpu'] = a.n_cpu
bus.data.options.optimization['strict_completion'] = (a.scheduler == 'strict')
bus.data.options.optimization['retain_empty_universes'] = (a.scheduler == 'corrected')
widths = bus.data.inst['wl_bin_widths'] * 1e6
ratio = bus.data.options.array['ratio']
arch_fn, order = DESIGNS[a.design]
arch = arch_fn(ratio)

ams = AgnosticMissionSimulator(order, 7, 65 / 360 * 2 * np.pi, 0.8, 12 * 3600,
                               architecture=arch, verbose=False)
tse = TradeSpaceExplorer(ams, opt, instrument)

rows = []
print(f'=== {tag}', flush=True)
targets = (tuple(float(t) for t in a.targets.split(','))
           if a.targets else TARGETS[(a.design, a.catalog)])
for target in targets:
    for fam in FAMILY_ORDER:
        setter = make_setter(bus, ams, GRADIENT[fam], widths)
        t0 = time.time()
        endpoint = tse.locate_mission_cutoff(target, upper_start=a.upper_start,
                                             setter_func=setter)
        setter(endpoint)
        achieved = ams.run(instrument, opt)
        wall = round(time.time() - t0, 1)
        search = getattr(tse, 'last_search',
                         dict(status='n/a', lower=np.nan, upper=np.nan, its=-1))
        rows.append(f'{a.design}\thab2{a.catalog}\t{target}\t{fam}\t'
                    f'{endpoint:.4f}\t{achieved:.4f}\t{search["status"]}\t'
                    f'{search["lower"]:.4f}\t{search["upper"]:.4f}\t'
                    f'{search["its"]}\t{a.scheduler}\t{wall}')
        print(f'  {target} {fam}: {endpoint:.1f} ph/s/um '
              f'(achieved {achieved:.4f} yr, {search["status"]}, {wall}s)',
              flush=True)

with open(out, 'w') as fh:
    fh.write('design\tcatalog\ttarget_yr\tfamily\tendpoint_ph_s_um\t'
             'mtime_achieved_yr\tsearch_status\tbracket_lo\tbracket_hi\t'
             'search_its\tscheduler\twall_s\n')
    fh.write('\n'.join(rows) + '\n')
print(f'wrote {out}')
