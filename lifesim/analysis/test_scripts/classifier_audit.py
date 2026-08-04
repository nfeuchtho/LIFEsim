"""Round-7 P0.2 audit: one classifier definition for the z-criterion.

The operational classifier is the FLAT-family relative endpoint spread: flat is
the directly comparable scalar allowance (Section 5.3) and the family the
pre-registered independent-population campaign evaluated. This script computes,
for every operating point in zpoints.tsv, the flat-family spread from the raw
replicate shards, alongside the per-family min/max already quoted, and reports
the pass/fail count under the flat rule and under the worst-family rule.

Spread definition: identical to analyze_uncertainty.py -- mean and sd over ALL
returned replicates, with no-allowance replicates entering as zeros and also
counted separately as infeasible. (The independent-population campaign instead
excludes zeros from its spread; no z >= 3 cell in either analysis contains a
zero, so the two definitions coincide everywhere the criterion is applied.)

Writes thesis/reproducibility/uncertainty/classifier_audit.tsv and augments
zpoints.tsv with a rel_sd_flat column (in place, backed up to zpoints_pre_audit.tsv).
"""
import glob
import os
import shutil

import numpy as np
import pandas as pd

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
UDIR = os.path.join(REPO, 'thesis', 'reproducibility', 'uncertainty')
ZP = os.path.join(UDIR, 'zpoints.tsv')

FAMES = {'flat': 'flat', 'short_weighted': 'short', 'long_weighted': 'long'}


def family_spread(design, cat, target, family):
    tag = ('%g' % target).replace('.', 'p')
    if 'p' not in tag:
        tag += 'p0'
    pat = os.path.join(UDIR, f'{design}_{cat.replace("hab2", "")}_{family}_{tag}_corrected*.tsv')
    files = [f for f in glob.glob(pat) if not f.endswith('_universes.tsv')]
    if not files:
        return None, 0
    vals = (pd.concat([pd.read_csv(f, sep='\t') for f in files])
            .drop_duplicates('replicate'))
    v = vals['endpoint_ph_s_um'].to_numpy(float)
    if v.size < 3 or v.mean() <= 0:
        return None, v.size
    # Same convention as analyze_uncertainty.py: zeros included in the spread.
    return float(v.std(ddof=1) / v.mean() * 100), int(v.size)


z = pd.read_csv(ZP, sep='\t')
rows = []
for r in z.itertuples():
    out = {'design': r.design, 'catalog': r.catalog, 'target_yr': r.target_yr,
           'z': r.z, 'original_point': r.original_point,
           'rel_sd_min': r.rel_sd_min, 'rel_sd_max': r.rel_sd_max}
    for fam in ('flat', 'short_weighted', 'long_weighted'):
        s, n = family_spread(r.design, r.catalog, r.target_yr, fam)
        out[f'rel_sd_{FAMES[fam]}'] = None if s is None else round(s, 1)
        out[f'n_{FAMES[fam]}'] = n
    rows.append(out)

audit = pd.DataFrame(rows).sort_values('z')
audit.to_csv(os.path.join(UDIR, 'classifier_audit.tsv'), sep='\t', index=False)
print(audit.to_string(index=False))

flat_ok = audit.rel_sd_flat.notna()
assert flat_ok.all(), 'missing flat family for some cell'
sane = np.isfinite(audit.rel_sd_flat) & (
    (audit.rel_sd_flat >= audit.rel_sd_min - 0.2) &
    (audit.rel_sd_flat <= audit.rel_sd_max + 0.2))
assert sane.all(), 'flat spread outside quoted family range somewhere'

held = audit[audit.original_point == 0]
h3 = held[held.z >= 3]
print(f'\nheld-out z>=3 cells: {len(h3)}')
print(f'  flat rule  (<40%%): {int((h3.rel_sd_flat < 40).sum())}/{len(h3)} pass')
print(f'  worst rule (<40%%): {int((h3.rel_sd_max < 40).sum())}/{len(h3)} pass')
viol = h3[h3.rel_sd_max >= 40]
if len(viol):
    print('  worst-family exceedances:')
    print(viol[['design', 'catalog', 'target_yr', 'z', 'rel_sd_flat',
                'rel_sd_short', 'rel_sd_long', 'rel_sd_max']].to_string(index=False))
below = held[held.z < 3]
print(f'held-out z<3 cells: {len(below)}; flat spreads: '
      f'{below.rel_sd_flat.tolist()}')

shutil.copy(ZP, os.path.join(UDIR, 'zpoints_pre_audit.tsv'))
z2 = z.merge(audit[['design', 'catalog', 'target_yr', 'rel_sd_flat']],
             on=['design', 'catalog', 'target_yr'])
assert len(z2) == len(z)
z2.to_csv(ZP, sep='\t', index=False)
print('\nzpoints.tsv augmented with rel_sd_flat (backup: zpoints_pre_audit.tsv)')
