"""Pre-registered analysis of the independent-ensemble campaign.

Implements exactly the analysis fixed in PREREGISTRATION.md before any result
existed: per anchor cell, between-realization statistics of the zero-budget
time and flat endpoint, z recomputed from between-realization quantities, and
the four-cell classification test of the z >= 3 criterion.

Reads thesis/reproducibility/independent_ensembles/*.tsv, writes
independent_summary.tsv and prints the verdict.
"""
import glob
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
IDIR = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'thesis',
                                    'reproducibility', 'independent_ensembles'))

rows = []
for f in sorted(glob.glob(os.path.join(IDIR, '*_seed*.tsv'))):
    if 'seed901' in f or 'seed999' in f:
        continue
    rows.append(pd.read_csv(f, sep='\t'))
df = pd.concat(rows, ignore_index=True)
df['round'] = (df['seedtag'].str.extract(r'seed(\d+)', expand=False)
               .astype(int).ge(1000).map({False: 1, True: 2}))
print(f'{len(df)} evaluations loaded')

out = []
for (rnd, design, scen, target), g in df.groupby(['round', 'design', 'scenario', 'target_yr']):
    t0 = g['zero_budget_yr'].to_numpy(float)
    ep = g['endpoint_ph_s_um'].to_numpy(float)
    feasible = ep[ep > 0]
    n_inf = int((ep == 0).sum())
    z_between = (target - t0.mean()) / t0.std(ddof=1)
    rel = (feasible.std(ddof=1) / feasible.mean() * 100
           if len(feasible) > 2 else float('nan'))
    out.append(dict(round=rnd, design=design, scenario=scen, target_yr=target,
                    n=len(g), n_infeasible=n_inf,
                    t0_mean=t0.mean(), t0_sd=t0.std(ddof=1),
                    z_between=z_between,
                    ep_mean=feasible.mean() if len(feasible) else 0.0,
                    ep_relsd_pct=rel))

s = pd.DataFrame(out).sort_values(['round', 'z_between'])
s.to_csv(os.path.join(IDIR, 'independent_summary.tsv'), sep='\t', index=False)
print(s.to_string(index=False,
                  float_format=lambda x: f'{x:.3f}'))

print('\n=== Pre-registered classification test (z >= 3 <-> rel spread < 40%,'
      ' z < 3 <-> spread >= 40% or infeasibles):')
ok = True
for r in s.itertuples():
    if r.z_between >= 3:
        cell_ok = r.ep_relsd_pct < 40 and r.n_infeasible == 0
    else:
        cell_ok = r.ep_relsd_pct >= 40 or r.n_infeasible > 0
    ok &= cell_ok
    print(f'  R{r.round} {r.design} {r.scenario} {r.target_yr}: z_between {r.z_between:.2f}, '
          f'spread {r.ep_relsd_pct:.1f}%, infeasible {r.n_infeasible}/{r.n} -> '
          f'{"CONSISTENT" if cell_ok else "INCONSISTENT"}')
print(f'\nVERDICT: {"criterion HOLDS between independent realizations" if ok else "criterion FAILS the pre-registered test"}')
