"""Round-7 P1.2: separate endpoint-search (solver) noise from sampling spread.

Each replicate stores the amplitude the search returned AND the mission time
that amplitude actually delivers (mtime_achieved_yr). The search stops inside
a +-0.05 yr tolerance or a 10 ph/s/um bracket, so part of the endpoint's
replicate-to-replicate variation is solver jitter, not sampling. Within one
cell the local amplitude-time slope converts achieved-time scatter into its
amplitude-equivalent; regressing the endpoint on the achieved-time residual
and removing the fitted component gives a solver-corrected spread. Because
achieved-time scatter also carries real per-resample feasibility variation,
the corrected value is a LOWER bound on the sampling spread and the raw value
an UPPER bound; classification is robust if both sides of 40 % agree.

Writes thesis/reproducibility/uncertainty/solver_separation.tsv.
"""
import glob
import os

import numpy as np
import pandas as pd

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
UDIR = os.path.join(REPO, 'thesis', 'reproducibility', 'uncertainty')

zp = pd.read_csv(os.path.join(UDIR, 'zpoints.tsv'), sep='\t')

rows = []
for r in zp.itertuples():
    tag = ('%g' % r.target_yr).replace('.', 'p')
    if 'p' not in tag:
        tag += 'p0'
    cat = r.catalog.replace('hab2', '')
    pat = os.path.join(UDIR, f'{r.design}_{cat}_flat_{tag}_corrected*.tsv')
    files = [f for f in glob.glob(pat) if not f.endswith('_universes.tsv')]
    df = (pd.concat([pd.read_csv(f, sep='\t') for f in files])
          .drop_duplicates('replicate'))
    v = df['endpoint_ph_s_um'].to_numpy(float)
    dt = df['mtime_achieved_yr'].to_numpy(float) - r.target_yr
    mean = v.mean()
    raw = v.std(ddof=1) / mean * 100
    # Project out the achieved-time component (solver tolerance jitter).
    A = np.vstack([np.ones_like(dt), dt]).T
    coef, *_ = np.linalg.lstsq(A, v, rcond=None)
    resid = v - A @ coef
    corrected = resid.std(ddof=1) / mean * 100
    solver_amp = abs(coef[1]) * dt.std(ddof=1)
    rows.append(dict(design=r.design, catalog=r.catalog, target_yr=r.target_yr,
                     z=r.z, original_point=r.original_point, n=len(v),
                     mean_flat=round(mean, 1),
                     dt_sd_yr=round(float(dt.std(ddof=1)), 4),
                     slope_ph_per_yr=round(float(coef[1]), 1),
                     solver_amp_ph=round(float(solver_amp), 1),
                     raw_rel_sd=round(raw, 1),
                     corrected_rel_sd=round(corrected, 1)))

out = pd.DataFrame(rows).sort_values('z')
out.to_csv(os.path.join(UDIR, 'solver_separation.tsv'), sep='\t', index=False)
print(out.to_string(index=False))

flip = out[((out.raw_rel_sd < 40) != (out.corrected_rel_sd < 40))]
print(f'\ncells whose <40% classification differs between bounds: {len(flip)}')
if len(flip):
    print(flip.to_string(index=False))
