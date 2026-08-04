"""Aggregate the corrected-scheduler uncertainty campaign into the thesis stats.

Inputs (thesis/reproducibility/uncertainty/):
  {design}_{cat}_{family}_{target}_corrected[_offN].tsv   endpoint bootstrap shards
  zerobudget_{design}_{cat}_corrected[_offN].tsv          zero-budget spreads

Outputs (same directory):
  cell_stats.tsv     per (design, catalog, target, family): n, median, mean, sd,
                     relative sd, 16-84 and 2.5-97.5 intervals, infeasible count
  zpoints.tsv        per operating point: z = (T* - mean T0)/sd T0, relative-sd
                     range over families, feasibility fraction
  zfit.txt           Spearman(z, rel sd) with a bootstrap CI over operating
                     points, fitted on the eight ORIGINAL operating points and
                     validated on the held-out ones (new intermediate targets
                     and survey designs), which the campaign ran blind to the
                     fit. Threshold check: does z >= 3 separate cells whose
                     relative spread is below 40% on the held-out set?
"""
import glob
import os
import re
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
UDIR = os.path.abspath(os.path.join(HERE, '..', '..', '..',
                                    'thesis', 'reproducibility', 'uncertainty'))

ORIGINAL_POINTS = {  # the eight operating points of the strict-era Table 5.2
    ('bracewell4', 'hi', 5.5), ('bracewell4', 'hi', 6.0),
    ('bracewell4', 'lo', 7.5), ('bracewell4', 'lo', 8.0),
    ('triple6', 'hi', 4.0), ('triple6', 'hi', 4.5),
    ('triple6', 'lo', 5.5), ('triple6', 'lo', 6.0),
}

pat = re.compile(r'^(?P<design>.+?)_(?P<cat>hi|lo)_(?P<family>flat|short_weighted|'
                 r'long_weighted)_(?P<target>[0-9]+p[0-9]+)_corrected(_off\d+)?\.tsv$')

cells = {}
for path in sorted(glob.glob(os.path.join(UDIR, '*_corrected*.tsv'))):
    name = os.path.basename(path)
    if '_universes' in name or name.startswith('zerobudget'):
        continue
    m = pat.match(name)
    if not m:
        continue
    df = pd.read_csv(path, sep='\t')
    key = (m['design'], m['cat'], float(m['target'].replace('p', '.')),
           m['family'])
    cells.setdefault(key, []).append(df)

zb = {}
for path in sorted(glob.glob(os.path.join(UDIR, 'zerobudget_*_corrected*.tsv'))):
    if '_blmax' in path:
        continue
    df = pd.read_csv(path, sep='\t')
    key = (df['design'].iloc[0], df['catalog'].iloc[0][4:])
    zb.setdefault(key, []).append(df)
zb = {k: pd.concat(v).drop_duplicates('replicate') for k, v in zb.items()}

cell_rows, zrows = [], []
points = {}
for (design, cat, target, family), dfs in sorted(cells.items()):
    df = pd.concat(dfs).drop_duplicates('replicate').sort_values('replicate')
    v = df['endpoint_ph_s_um'].to_numpy(float)
    n = v.size
    feasible = v[v > 0]
    n_inf = int((v == 0).sum())
    med, mean, sd = np.median(v), v.mean(), v.std(ddof=1)
    p16, p84 = np.percentile(v, [16, 84])
    p2, p97 = np.percentile(v, [2.5, 97.5])
    rel = sd / mean if mean > 0 else np.inf
    cell_rows.append(f'{design}\thab2{cat}\t{target}\t{family}\t{n}\t'
                     f'{med:.1f}\t{mean:.1f}\t{sd:.1f}\t{100*rel:.1f}\t'
                     f'{p16:.1f}\t{p84:.1f}\t{p2:.1f}\t{p97:.1f}\t{n_inf}')
    points.setdefault((design, cat, target), {})[family] = (rel, n_inf, n)

for (design, cat, target), fams in sorted(points.items()):
    if (design, cat) not in zb:
        print(f'[!] no zero-budget spread for {design} hab2{cat}; skipping z')
        continue
    t0 = zb[(design, cat)]['zero_budget_mtime_yr'].to_numpy(float)
    z = (target - t0.mean()) / t0.std(ddof=1)
    rels = [fams[f][0] for f in fams]
    # The classifier variable: flat is the directly comparable scalar
    # allowance and the family the pre-registered independent campaign uses.
    rel_flat = fams['flat'][0]
    inf_frac = sum(fams[f][1] for f in fams) / sum(fams[f][2] for f in fams)
    zrows.append((design, cat, target, z, min(rels), max(rels), inf_frac,
                  (design, cat, target) in ORIGINAL_POINTS, rel_flat))

with open(os.path.join(UDIR, 'cell_stats.tsv'), 'w') as fh:
    fh.write('design\tcatalog\ttarget_yr\tfamily\tn\tmedian\tmean\tsd\t'
             'rel_sd_pct\tp16\tp84\tp2p5\tp97p5\tn_infeasible\n')
    fh.write('\n'.join(cell_rows) + '\n')

with open(os.path.join(UDIR, 'zpoints.tsv'), 'w') as fh:
    fh.write('design\tcatalog\ttarget_yr\tz\trel_sd_min\trel_sd_max\t'
             'infeasible_frac\toriginal_point\trel_sd_flat\n')
    for r in zrows:
        fh.write(f'{r[0]}\thab2{r[1]}\t{r[2]}\t{r[3]:.3f}\t{100*r[4]:.1f}\t'
                 f'{100*r[5]:.1f}\t{100*r[6]:.1f}\t{int(r[7])}\t{100*r[8]:.1f}\n')

# The relation and threshold test run on the flat-family spread (the
# classifier variable); the family range stays in zpoints for the figure.
za = np.array([(r[3], r[8], r[7]) for r in zrows], float)
orig, held = za[za[:, 2] == 1], za[za[:, 2] == 0]


def spearman(x, y):
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    return np.corrcoef(rx, ry)[0, 1]


lines = [f'operating points: {len(za)} total, {len(orig)} original, {len(held)} held out',
         'classifier variable: flat-family relative spread (zeros included, '
         'as in cell_stats)']
if len(orig) > 2:
    rho = spearman(orig[:, 0], orig[:, 1])
    boots = []
    rng = np.random.default_rng(20260801)
    for _ in range(10000):
        i = rng.integers(0, len(orig), len(orig))
        if np.unique(i).size > 2:
            boots.append(spearman(orig[i, 0], orig[i, 1]))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    lines.append(f'Spearman(z, rel spread), original points: {rho:.3f} '
                 f'[{lo:.3f}, {hi:.3f}] (95% bootstrap over points)')
if len(held) > 2:
    rho_h = spearman(held[:, 0], held[:, 1])
    lines.append(f'Spearman, held-out points: {rho_h:.3f}')
    thr_ok = int(np.sum((held[:, 0] >= 3) & (held[:, 1] < 0.40)))
    thr_all = int(np.sum(held[:, 0] >= 3))
    below_ok = int(np.sum((held[:, 0] < 3) & (held[:, 1] >= 0.40)))
    below_all = int(np.sum(held[:, 0] < 3))
    lines.append(f'held-out z>=3 with rel spread <40%: {thr_ok}/{thr_all}; '
                 f'held-out z<3 with rel spread >=40%: {below_ok}/{below_all}')

with open(os.path.join(UDIR, 'zfit.txt'), 'w') as fh:
    fh.write('\n'.join(lines) + '\n')
print('\n'.join(lines))
print(f'\nwrote cell_stats.tsv ({len(cell_rows)} cells), zpoints.tsv '
      f'({len(zrows)} points), zfit.txt')
