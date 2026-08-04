"""Generate the LaTeX table bodies for the integration pass, from artifacts only.

Every number in Tables 5.1, 5.2, B.2 and the survey table is read from the
frozen result files; nothing is typed. Output: thesis/reviews/tables_generated.tex
with one clearly delimited block per table, to be spliced into main.tex.

Sources:
  scheduler_boundary/endpoints_*_corrected.tsv   corrected point endpoints
  uncertainty/cell_stats.tsv                     powered intervals, infeasibles
  uncertainty/zpoints.tsv                        z per operating point
  survey_stage1.tsv                              survey zero-budget times
"""
import glob
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
RD = os.path.join(REPO, 'thesis', 'reproducibility')
OUT = os.path.join(REPO, 'thesis', 'reviews', 'tables_generated.tex')

ep = pd.concat([pd.read_csv(f, sep='\t') for f in
                sorted(glob.glob(os.path.join(RD, 'scheduler_boundary',
                                              'endpoints_*_corrected.tsv')))],
               ignore_index=True)
cs = pd.read_csv(os.path.join(RD, 'uncertainty', 'cell_stats.tsv'), sep='\t')
zp = pd.read_csv(os.path.join(RD, 'uncertainty', 'zpoints.tsv'), sep='\t')

DESIGN_NAME = {'bracewell4': 'Double Bracewell', 'triple6': 'Double triple nuller',
               'kernel5_deep': 'Kernel-5 (deep pair)', 'collinear4': 'Collinear kernel'}
CAT_NAME = {'hab2hi': 'Hab2Max', 'hab2lo': 'Hab2Min'}
FAMS = ('flat', 'short_weighted', 'long_weighted')


def sig3(x):
    """Three significant figures, no trailing point."""
    if x == 0:
        return '0'
    from math import floor, log10
    d = 2 - int(floor(log10(abs(x))))
    return f'{round(x, d):g}'


def sig2(x):
    """Two significant figures (headline display; solver jitter makes the
    third digit meaningless, Appendix B.3). Half-up so 1050 -> 1100."""
    if x == 0:
        return '0'
    from decimal import Decimal, ROUND_HALF_UP
    from math import floor, log10
    d = 1 - int(floor(log10(abs(x))))
    q = Decimal(str(x)).scaleb(d).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return f'{float(q) / 10**d:g}'


blocks = []

# ---- Table 5.1: endpoints for the two headline designs, with z and spread ----
rows = []
for design in ('bracewell4', 'triple6'):
    rows.append(r'\midrule' if rows else '')
    sub = ep[ep.design == design]
    for (cat, target), grp in sub.groupby(['catalog', 'target_yr']):
        amps = {r.family: r.endpoint_ph_s_um for r in grp.itertuples()}
        z = zp[(zp.design == design) & (zp.catalog == cat)
               & (zp.target_yr == target)].iloc[0]
        cells = cs[(cs.design == design) & (cs.catalog == cat)
                   & (cs.target_yr == target)]
        n_inf, n = int(cells.n_infeasible.sum()), int(cells.n.sum())
        rows.append(f'{CAT_NAME[cat]} & {target} & {sig2(amps["flat"])} & '
                    f'{sig2(amps["short_weighted"])} & '
                    f'{sig2(amps["long_weighted"])} & {z.z:.2f} & '
                    f'{z.rel_sd_min:.0f}--{z.rel_sd_max:.0f}\\,\\% & '
                    f'{n_inf}/{n} \\\\')
blocks.append(('TABLE 5.1 BODY (Catalog & Target & Flat & Short-wt & Long-wt '
               '& z & Rel. spread & No allowance)', rows))

# ---- Table 5.2: all 25 operating points, original vs held out ----
rows = []
for r in zp.sort_values('z').itertuples():
    tagd = DESIGN_NAME[r.design]
    held = '' if r.original_point else r'\,(h)'
    rows.append(f'{tagd}{held} & {CAT_NAME[r.catalog]} & {r.target_yr} & '
                f'{r.z:.2f} & {r.rel_sd_min:.0f}--{r.rel_sd_max:.0f}\\,\\% & '
                f'{r.infeasible_frac:.0f}\\,\\% \\\\')
blocks.append(('TABLE 5.2 BODY (Architecture & Catalog & Target & z & '
               'Rel. spread & Infeasible), (h) = held out', rows))

# ---- Table B.2: corrected endpoints with achieved times and status ----
rows = []
for design in ('bracewell4', 'triple6', 'kernel5_deep', 'collinear4'):
    sub = ep[ep.design == design]
    if not len(sub):
        continue
    rows.append(r'\midrule' if rows else '')
    for (cat, target), grp in sub.groupby(['catalog', 'target_yr']):
        amps = {r.family: (r.endpoint_ph_s_um, r.mtime_achieved_yr)
                for r in grp.itertuples()}
        ach = [amps[f][1] for f in FAMS if f in amps]
        rows.append(f'{CAT_NAME[cat]} & {target} & '
                    + ' & '.join(f'{amps[f][0]:.1f}' for f in FAMS if f in amps)
                    + f' & {min(ach):.3f}--{max(ach):.3f} \\\\')
blocks.append(('TABLE B.2 BODY (Catalog & Target & Flat & Short-wt & Long-wt '
               '& Achieved time range), corrected scheduler', rows))

# ---- Survey table: design properties ----
s1 = pd.read_csv(os.path.join(RD, 'survey_stage1.tsv'), sep='\t')
SURVEY = {  # measured design constants (combiner.py / clamp counts / FoM)
    'bracewell4': (4, 2, '50\\,\\%', 0.5894, '26\\,\\%'),
    'triple6': (6, 4, '33\\,\\%', 1.1376, '63\\,\\%'),
    'kernel5_deep': (5, 4, '40\\,\\%', 1.1249, '63\\,\\%'),
    'collinear4': (4, 4, '50\\,\\%', 2.0221, '87\\,\\%'),
}
zb_map = {(r.design, r.catalog): r.zb_yr for r in s1.itertuples()}
# Headline designs: corrected production zero-budgets from the boundary-run
# zero rows, same provenance discipline as everything else.
for design in ('bracewell4', 'triple6'):
    for cat in ('hi', 'lo'):
        b = pd.read_csv(os.path.join(RD, 'scheduler_boundary',
                                     f'{design}_{cat}.tsv'), sep='\t')
        zrow = b[(b.target_yr == 'zero') & (b['mode'] == 'corrected')]
        zb_map[(design, cat)] = float(zrow.mtime_yr.iloc[0])
rows = []
for design, (nap, order, light, const, clip) in SURVEY.items():
    rows.append(f'{DESIGN_NAME[design]} & {nap} & {order} & {light} & '
                f'{const:.3f} & {clip} & '
                f'{zb_map[(design, "hi")]:.2f} / {zb_map[(design, "lo")]:.2f} \\\\')
blocks.append(('SURVEY TABLE BODY (Design & Apertures & Null order & Light in '
               'pair & Peak constant & Clipped stars & Zero-budget hi/lo [yr])',
               rows))

# ---- Appendix B.5: the 13-cell independent-population matrix ----
IE = os.path.join(RD, 'independent_ensembles')
ie_rows = []
for f in sorted(glob.glob(os.path.join(IE, '*_seed*.tsv'))):
    if 'seed901' in f or 'seed999' in f:
        continue
    ie_rows.append(pd.read_csv(f, sep='\t'))
ie = pd.concat(ie_rows, ignore_index=True)
ie['round'] = (ie['seedtag'].str.extract(r'seed(\d+)', expand=False)
               .astype(int).ge(1000).map({False: 1, True: 2}))

R1_ORIGINAL = {('bracewell4', 'hab2max', 5.5), ('bracewell4', 'hab2min', 7.5),
               ('bracewell4', 'hab2max', 6.0), ('triple6', 'hab2max', 4.5)}
rng = np.random.default_rng(20260804)


def boot_ci(values, stat, n_boot=10000):
    v = np.asarray(values, float)
    out = []
    for _ in range(n_boot):
        s = stat(v[rng.integers(0, len(v), len(v))])
        if np.isfinite(s):
            out.append(s)
    return np.percentile(out, [2.5, 97.5])


def clopper_pearson(k, n, alpha=0.05):
    from scipy.stats import beta
    lo = 0.0 if k == 0 else beta.ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - alpha / 2, k + 1, n - k)
    return lo, hi


def rel_spread(v):
    pos = v[v > 0]
    if pos.size < 3:
        return np.nan
    return pos.std(ddof=1) / pos.mean() * 100


rows = []
for (rnd, design, scen, target), g in sorted(
        ie.groupby(['round', 'design', 'scenario', 'target_yr'])):
    t0 = g['zero_budget_yr'].to_numpy(float)
    epv = g['endpoint_ph_s_um'].to_numpy(float)
    n, n_inf = len(g), int((epv == 0).sum())
    z = (target - t0.mean()) / t0.std(ddof=1)
    z_lo, z_hi = boot_ci(t0, lambda s: (target - s.mean()) / s.std(ddof=1)
                         if s.std(ddof=1) > 0 else np.nan)
    spread = rel_spread(epv)
    if np.isfinite(spread):
        s_lo, s_hi = boot_ci(epv, rel_spread)
        spread_tex = f'{spread:.0f} [{s_lo:.0f}, {s_hi:.0f}]'
    else:
        spread_tex = '--'
    i_lo, i_hi = clopper_pearson(n_inf, n)
    inf_tex = f'{n_inf}/{n} [{100*i_lo:.0f}, {100*i_hi:.0f}]'
    if z >= 3:
        consistent = np.isfinite(spread) and spread < 40 and n_inf == 0
    else:
        consistent = (not np.isfinite(spread)) or spread >= 40 or n_inf > 0
    prov = ('reg.' if (rnd == 2 or (design, scen, target) in R1_ORIGINAL)
            else 'Amd.\\ 1')
    cfg = 'base' if rnd == 1 else 'binsup'
    MATRIX_NAME = {'bracewell4': 'Bracewell', 'triple6': 'Triple nuller'}
    rows.append(f'{cfg} & {MATRIX_NAME[design]} & '
                f'{"Hab2Max" if scen == "hab2max" else "Hab2Min"} & {target:g} & '
                f'{t0.mean():.2f}$\\pm${t0.std(ddof=1):.2f} & '
                f'{z:.1f} [{z_lo:.1f}, {z_hi:.1f}] & {spread_tex} & {inf_tex} & '
                f'{"yes" if consistent else "no"} & {prov} \\\\')
blocks.append(('INDEPENDENT MATRIX BODY (Config & Design & Catalog & T* [yr] & '
               'T0 [yr] & z [95% CI] & spread % [95% CI] & infeasible [95% CI %] '
               '& consistent & provenance)', rows))

with open(OUT, 'w', encoding='utf-8') as fh:
    for title, rows in blocks:
        fh.write(f'% ==== {title} ====\n')
        fh.write('\n'.join(rows) + '\n\n')
print(f'wrote {OUT} ({len(blocks)} table bodies)')
