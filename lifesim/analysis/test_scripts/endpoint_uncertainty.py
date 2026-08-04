"""Sampling uncertainty of one reported iso-mission-time endpoint.

Every amplitude this thesis reports is a point estimate. The mission time it is
solved against is the 90th percentile of times over 100 synthetic universes, so
the endpoint inherits the sampling variability of that percentile -- and because
the search runs where the completion curve is steep, that variability is
amplified rather than merely transmitted.

Method: a nonparametric bootstrap over the universe ensemble. Each replicate
draws 100 universes with replacement from the 100 available and relabels them
0..99, so it is a same-size resample of the ensemble the percentile is taken
over; num_universe follows from the column (optimizer.py:69). Nothing else
changes -- same catalog, same stars, same instrument, same search tolerance.

An endpoint of exactly zero is a result, not a failure: it means that resample
could not reach the target even with no added noise, so the operating point is
infeasible for it.

Caveat for the write-up: bootstrapping a high quantile is coarse, because the
resampled order statistic is discrete and over-dispersed relative to the true
sampling distribution. The interval this produces is an upper bound on the
standard error rather than an unbiased estimate.

One cell per invocation so cells can run as independent jobs:

    python endpoint_uncertainty.py --catalog hi --target 5.5 --family flat \
        --design bracewell4 --replicates 14

Campaign notes (2026-07-29):

- Replicates are now seeded individually from (seed, global_index), where
  global_index = --rep-offset + local index. A cell can therefore be sharded
  across jobs (--rep-offset 0/100/200 ...) and the union is identical to one
  long run. This CHANGES the draws relative to the original 14-replicate
  campaign, which advanced one generator sequentially; results are
  statistically equivalent but not bit-identical to it.
- --scheduler corrected runs with non-strict completion and retained empty
  universes (see scheduler_boundary.py); default strict reproduces the
  historical behavior.
- Retention: per-universe component times for every replicate are written to
  <tag>_universes.tsv and the endpoint-search bracket and status to the main
  TSV, closing the raw-product retention gap of Appendix B.
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

from lifesim.ams.ablation_throughput import build_bus, ARMS, make_setter, FAMILIES
from lifesim.ams.core.ams import AgnosticMissionSimulator
from lifesim.ams.trade_space_explorer import TradeSpaceExplorer
from lifesim.util.combiner import double_bracewell, double_triple_nuller, kernel5, collinear4

DESIGNS = {'bracewell4': (lambda r: double_bracewell(1.0, r), 2),
           'triple6': (lambda r: double_triple_nuller(1.0, r), 4),
           'kernel5_deep': (lambda r: kernel5(1.0, 'deep'), 4),
           'kernel5_shallow': (lambda r: kernel5(1.0, 'shallow'), 2),
           'collinear4': (lambda r: collinear4(1.0), 4)}

GRADIENT = {v: k for k, v in FAMILIES.items()}      # family name -> setter key
OUTDIR = os.path.join(REPO, 'thesis', 'reproducibility', 'uncertainty')

ap = argparse.ArgumentParser()
ap.add_argument('--catalog', choices=['hi', 'lo'], required=True)
ap.add_argument('--target', type=float, required=True)
ap.add_argument('--family', choices=list(GRADIENT), required=True)
ap.add_argument('--design', choices=list(DESIGNS), default='bracewell4')
ap.add_argument('--replicates', type=int, default=14)
ap.add_argument('--rep-offset', type=int, default=0,
                help='global index of the first replicate; shards a cell across jobs')
ap.add_argument('--scheduler', choices=['strict', 'corrected'], default='strict',
                help='corrected = non-strict completion + retained empty universes')
ap.add_argument('--upper-start', type=int, default=20000)
ap.add_argument('--seed', type=int, default=20260728)
# Cells are run several at a time and the analytic rewrite left nothing worth
# parallelising inside one, so keep each cell narrow rather than letting the
# settings.yaml default of eight oversubscribe the machine.
ap.add_argument('--n-cpu', type=int, default=2)
a = ap.parse_args()

os.makedirs(OUTDIR, exist_ok=True)
tag = f'{a.design}_{a.catalog}_{a.family}_{str(a.target).replace(".", "p")}'
if a.scheduler != 'strict':
    tag += f'_{a.scheduler}'
if a.rep_offset:
    tag += f'_off{a.rep_offset}'
out = os.path.join(OUTDIR, tag + '.tsv')
out_uni = os.path.join(OUTDIR, tag + '_universes.tsv')

bus, instrument, opt = build_bus(a.catalog, ARMS['control'])
bus.data.options.other['n_cpu'] = a.n_cpu
bus.data.options.optimization['strict_completion'] = (a.scheduler == 'strict')
bus.data.options.optimization['retain_empty_universes'] = (a.scheduler == 'corrected')
base = bus.data.catalog.copy()
universes = np.unique(base.nuniverse.to_numpy())
by_universe = {u: base[base.nuniverse == u] for u in universes}
widths = bus.data.inst['wl_bin_widths'] * 1e6
ratio = bus.data.options.array['ratio']
arch_fn, order = DESIGNS[a.design]
arch = arch_fn(ratio)

# Each replicate is seeded from (seed, global_index) so shards of one cell are
# independent of job boundaries and their union equals one long run.
rows, uni_rows, vals = [], [], []
print(f'=== {tag}: {a.replicates} bootstrap replicates over {universes.size} universes'
      f' (offset {a.rep_offset}, scheduler {a.scheduler})', flush=True)

YR = 60 * 60 * 24 * 365.25

for r in range(a.replicates):
    gidx = a.rep_offset + r
    rng = np.random.default_rng([a.seed, gidx])
    draw = rng.choice(universes, size=universes.size, replace=True)
    parts = []
    for new_id, u in enumerate(draw):
        block = by_universe[u].copy()
        block['nuniverse'] = new_id
        parts.append(block)
    bus.data.catalog = pd.concat(parts, ignore_index=True)

    ams = AgnosticMissionSimulator(order, 7, 65 / 360 * 2 * np.pi, 0.8, 12 * 3600,
                                   architecture=arch, verbose=False)
    tse = TradeSpaceExplorer(ams, opt, instrument)
    setter = make_setter(bus, ams, GRADIENT[a.family], widths)
    t0 = time.time()
    endpoint = tse.locate_mission_cutoff(a.target, upper_start=a.upper_start,
                                         setter_func=setter)
    setter(endpoint)
    achieved = ams.run(instrument, opt)
    wall = round(time.time() - t0, 1)
    vals.append(float(endpoint))
    search = getattr(tse, 'last_search',
                     dict(status='n/a', lower=np.nan, upper=np.nan, its=-1))
    rows.append(f'{a.design}\thab2{a.catalog}\t{a.target}\t{a.family}\t{gidx}\t'
                f'{endpoint:.4f}\t{achieved:.4f}\t{search["status"]}\t'
                f'{search["lower"]:.4f}\t{search["upper"]:.4f}\t{search["its"]}\t'
                f'{a.scheduler}\t{wall}')
    for nu, sheet_row in ams.last_time_sheet.iterrows():
        uni_rows.append(f'{gidx}\t{nu}\t{sheet_row["detection"] / YR:.6f}\t'
                        f'{sheet_row["orbit"] / YR:.6f}\t'
                        f'{sheet_row["characterization"] / YR:.6f}\t'
                        f'{sheet_row["total"] / YR:.6f}')
    print(f'  {tag} replicate {gidx} ({r + 1}/{a.replicates}): {endpoint:.1f} ph/s/um '
          f'(achieved {achieved:.3f} yr, {search["status"]}, {wall}s)', flush=True)

v = np.array(vals)
n_zero = int((v == 0).sum())
print(f'\n=== {tag} summary')
print(f'    mean {v.mean():.1f}  median {np.median(v):.1f}  sd {v.std(ddof=1):.1f} '
      f'({100 * v.std(ddof=1) / max(v.mean(), 1e-9):.0f} % of mean)')
print(f'    range {v.min():.1f}-{v.max():.1f}  16th-84th {np.percentile(v, 16):.1f}-'
      f'{np.percentile(v, 84):.1f}  infeasible replicates {n_zero}/{a.replicates}',
      flush=True)

with open(out, 'w') as fh:
    fh.write('design\tcatalog\ttarget_yr\tfamily\treplicate\tendpoint_ph_s_um\t'
             'mtime_achieved_yr\tsearch_status\tbracket_lo\tbracket_hi\t'
             'search_its\tscheduler\twall_s\n')
    fh.write('\n'.join(rows) + '\n')
with open(out_uni, 'w') as fh:
    fh.write('replicate\tuniverse\tdetection_yr\torbit_yr\tchar_yr\ttotal_yr\n')
    fh.write('\n'.join(uni_rows) + '\n')
print(f'wrote {out}\nwrote {out_uni}')
