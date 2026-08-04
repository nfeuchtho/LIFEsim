"""Sampling spread of the zero-budget mission time.

The endpoint bootstrap shows that how well a reported amplitude is determined
depends on how far its mission-time target sits above the configuration's
zero-budget time. Expressed as a fraction of that time the relation is monotonic
above about 8 %, but it misorders the two tightest operating points: Hab2Min at
7.5 yr has the smallest relative margin of all and is better behaved than
Hab2Max at 5.5 yr.

The likely reason is that the natural unit is not the zero-budget time but the
sampling spread of the 90th-percentile mission time itself. A target one such
spread above the boundary is precarious; one four spreads above is safe,
regardless of what those spreads are in years. This measures that spread
directly, so headroom can be expressed as a z-score.

Runs the same bootstrap resamples as endpoint_uncertainty.py, using the same
default seed, but evaluates only the zero-budget mission time -- no search, so
each replicate is one AMS evaluation rather than six to eight.

    python zerobudget_spread.py --catalog hi --design triple6 [--replicates 14]
"""
import argparse
import os
import sys
import time

import numpy as np
import pandas as pd

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, REPO)
_cwd = os.getcwd()
import lifesim
os.chdir(_cwd)

from lifesim.ams.ablation_throughput import build_bus, ARMS
from lifesim.ams.core.ams import AgnosticMissionSimulator
from lifesim.util.combiner import double_bracewell, double_triple_nuller, kernel5, collinear4

DESIGNS = {'bracewell4': (lambda r: double_bracewell(1.0, r), 2),
           'triple6': (lambda r: double_triple_nuller(1.0, r), 4),
           'kernel5_deep': (lambda r: kernel5(1.0, 'deep'), 4),
           'kernel5_shallow': (lambda r: kernel5(1.0, 'shallow'), 2),
           'collinear4': (lambda r: collinear4(1.0), 4)}

OUTDIR = os.path.join(REPO, 'thesis', 'reproducibility', 'uncertainty')

ap = argparse.ArgumentParser()
ap.add_argument('--catalog', choices=['hi', 'lo'], required=True)
ap.add_argument('--design', choices=list(DESIGNS), required=True)
ap.add_argument('--replicates', type=int, default=14)
ap.add_argument('--rep-offset', type=int, default=0,
                help='global index of the first replicate; shards across jobs')
ap.add_argument('--scheduler', choices=['strict', 'corrected'], default='strict',
                help='corrected = non-strict completion + retained empty universes')
ap.add_argument('--seed', type=int, default=20260728)
ap.add_argument('--n-cpu', type=int, default=2)
ap.add_argument('--bl-max', type=float, default=None,
                help='override the maximum nulling baseline in m '
                     '(envelope-sensitivity axis)')
a = ap.parse_args()

os.makedirs(OUTDIR, exist_ok=True)
tag = f'zerobudget_{a.design}_{a.catalog}'
if a.bl_max is not None:
    tag += f'_blmax{int(a.bl_max)}'
if a.scheduler != 'strict':
    tag += f'_{a.scheduler}'
if a.rep_offset:
    tag += f'_off{a.rep_offset}'
out = os.path.join(OUTDIR, tag + '.tsv')

bus, instrument, opt = build_bus(a.catalog, ARMS['control'])
bus.data.options.other['n_cpu'] = a.n_cpu
bus.data.options.optimization['strict_completion'] = (a.scheduler == 'strict')
bus.data.options.optimization['retain_empty_universes'] = (a.scheduler == 'corrected')
if a.bl_max is not None:
    bus.data.options.array['bl_max'] = a.bl_max
base = bus.data.catalog.copy()
universes = np.unique(base.nuniverse.to_numpy())
by_universe = {u: base[base.nuniverse == u] for u in universes}
ratio = bus.data.options.array['ratio']
arch_fn, order = DESIGNS[a.design]
arch = arch_fn(ratio)

# Per-replicate seeding from (seed, global_index): shard-stable, matches
# endpoint_uncertainty.py. Not bit-identical to the original sequential
# 14-replicate campaign.
vals = []
print(f'=== zero-budget spread, {a.design} hab2{a.catalog}, {a.replicates} resamples'
      f' (offset {a.rep_offset}, scheduler {a.scheduler})', flush=True)

for r in range(a.replicates):
    rng = np.random.default_rng([a.seed, a.rep_offset + r])
    draw = rng.choice(universes, size=universes.size, replace=True)
    parts = []
    for new_id, u in enumerate(draw):
        block = by_universe[u].copy()
        block['nuniverse'] = new_id
        parts.append(block)
    bus.data.catalog = pd.concat(parts, ignore_index=True)

    ams = AgnosticMissionSimulator(order, 7, 65 / 360 * 2 * np.pi, 0.8, 12 * 3600,
                                   architecture=arch, verbose=False)
    t0 = time.time()
    mt = ams.run(instrument, opt)          # no budget applied: this is MT(A=0)
    vals.append(float(mt))
    print(f'  replicate {r + 1}/{a.replicates}: {mt:.4f} yr '
          f'({time.time() - t0:.0f}s)', flush=True)

v = np.array(vals)
print(f'\n=== {a.design} hab2{a.catalog}: mean {v.mean():.4f}  sd {v.std(ddof=1):.4f} yr'
      f'  range {v.min():.4f}-{v.max():.4f}', flush=True)

with open(out, 'w') as fh:
    fh.write('design\tcatalog\treplicate\tzero_budget_mtime_yr\tscheduler\n')
    for i, x in enumerate(v):
        fh.write(f'{a.design}\thab2{a.catalog}\t{a.rep_offset + i}\t{x:.6f}\t'
                 f'{a.scheduler}\n')
print(f'wrote {out}')
