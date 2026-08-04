"""Forest plot of the bootstrap uncertainty on every reported endpoint.

One row per entry of the results table: the reported point estimate against the
bootstrap distribution of the same quantity. A forest plot is the right display
here because the message is a comparison of intervals across cells, not the
shape of any one distribution -- and because it makes the controlling variable
visible at a glance, which is how far each operating point sits above its own
zero-budget time.

Reads thesis/reproducibility/uncertainty/*.tsv and writes a single figure.

    python plot_endpoint_uncertainty.py [outfile.pdf]
"""
import glob
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
UDIR = os.path.join(REPO, 'thesis', 'reproducibility', 'uncertainty')
BDIR = os.path.join(REPO, 'thesis', 'reproducibility', 'scheduler_boundary')
OUT = (sys.argv[1] if len(sys.argv) > 1
       else os.path.join(REPO, 'thesis', 'images', 'tse', 'endpoint_uncertainty.pdf'))

# The figure shows the eight operating points of the results table (the
# held-out and survey points appear in the z-relation figure instead). All
# values are read from the frozen artifacts rather than typed here: reported
# endpoints from the corrected re-derivation, z from the aggregated z table.
ORIGINAL = [('bracewell4', 'hab2hi', 5.5), ('bracewell4', 'hab2hi', 6.0),
            ('bracewell4', 'hab2lo', 7.5), ('bracewell4', 'hab2lo', 8.0),
            ('triple6', 'hab2hi', 4.0), ('triple6', 'hab2hi', 4.5),
            ('triple6', 'hab2lo', 5.5), ('triple6', 'hab2lo', 6.0)]

rep_frames = [pd.read_csv(f, sep='\t') for f in
              sorted(glob.glob(os.path.join(BDIR, 'endpoints_*_corrected.tsv')))]
rep_df = pd.concat(rep_frames, ignore_index=True)
REPORTED = {(r.design, r.catalog, r.target_yr):
            dict(rep_df[(rep_df.design == r.design) & (rep_df.catalog == r.catalog)
                        & (rep_df.target_yr == r.target_yr)]
                 [['family', 'endpoint_ph_s_um']].values)
            for r in rep_df.itertuples()}

zdf = pd.read_csv(os.path.join(UDIR, 'zpoints.tsv'), sep='\t')
ZSCORE = {(r.design, r.catalog, r.target_yr): r.z for r in zdf.itertuples()}

FAMCOL = {'flat': 'tab:blue', 'short_weighted': 'tab:orange', 'long_weighted': 'tab:green'}
FAMLAB = {'flat': 'Flat', 'short_weighted': 'Short-weighted', 'long_weighted': 'Long-weighted'}
# Short forms for the row labels; the legend carries the full names. Row labels
# are read at print size, so they are kept narrow to leave the axis its width.
FAMSHORT = {'flat': 'flat', 'short_weighted': 'short', 'long_weighted': 'long'}

endpoint_files = [f for f in glob.glob(os.path.join(UDIR, '*_corrected*.tsv'))
                  if '_universes' not in f and 'zerobudget' not in f
                  and 'cell_stats' not in f and 'zpoints' not in f]
frames = [pd.read_csv(f, sep='\t') for f in sorted(endpoint_files)]
if not frames:
    sys.exit(f'no corrected endpoint data under {UDIR}')
df = (pd.concat(frames, ignore_index=True)
      .drop_duplicates(['design', 'catalog', 'target_yr', 'family', 'replicate']))

rows = []
for (design, catalog, target), grp in df.groupby(['design', 'catalog', 'target_yr']):
    if (design, catalog, target) not in ORIGINAL:
        continue
    # The margin z -- the distance of the target above the configuration's own
    # feasibility boundary in sampling standard deviations of that boundary --
    # is the controlling variable (Section 5.4), so it orders the rows.
    z = ZSCORE[(design, catalog, target)]
    for family in ('flat', 'short_weighted', 'long_weighted'):
        v = grp[grp.family == family].endpoint_ph_s_um.to_numpy(dtype=float)
        if not v.size:
            continue
        rows.append(dict(design=design, catalog=catalog, target=target, family=family,
                         z=z, v=v,
                         reported=REPORTED.get((design, catalog, target), {}).get(family)))

# Order by z so the controlling variable reads down the axis.
rows.sort(key=lambda r: (r['z'], r['family']))

# Sized to the printed text width so the figure is included at scale 1 and the
# font sizes below are the sizes that reach the page.
fig, ax = plt.subplots(figsize=(6.5, 0.30 * len(rows) + 0.9))
labels = []
for i, r in enumerate(rows):
    v, c = r['v'], FAMCOL[r['family']]
    lo, hi = np.percentile(v, 16), np.percentile(v, 84)
    ax.plot([v.min(), v.max()], [i, i], color=c, lw=1.0, alpha=0.45, zorder=2)
    ax.plot([lo, hi], [i, i], color=c, lw=4.0, alpha=0.85, zorder=3)
    ax.plot(np.median(v), i, 'o', color=c, ms=4.5, zorder=4)
    if r['reported']:
        ax.plot(r['reported'], i, marker='|', color='black', ms=11, mew=1.6, zorder=5)
    n_zero = int((v == 0).sum())
    if n_zero:
        ax.annotate(f'{n_zero}/{v.size} infeasible', (0, i), xytext=(4, 0),
                    textcoords='offset points', va='center', fontsize=8.5, color='crimson')
    design = 'Bracewell' if r['design'] == 'bracewell4' else 'Triple nuller'
    cat = 'Hab2Max' if r['catalog'] == 'hab2hi' else 'Hab2Min'
    labels.append(f"{design}, {cat}, {r['target']:.1f} yr "
                  f"(z={r['z']:.1f}), {FAMSHORT[r['family']]}")

ax.set_yticks(range(len(rows)))
ax.set_yticklabels(labels, fontsize=9)
ax.tick_params(axis='x', labelsize=8.5)
ax.set_xscale('symlog', linthresh=10)
ax.set_xlabel('Iso-mission-time endpoint [ph s$^{-1}$ $\\mu$m$^{-1}$]', fontsize=10)
ax.set_ylim(-0.7, len(rows) - 0.3)
# Least-determined (lowest z) rows read from the top, matching the caption and
# the top-down ordering of the z-table.
ax.invert_yaxis()
ax.grid(axis='x', alpha=0.25)
# No title: the caption in the thesis states what the bars mean, and a title
# wide enough to repeat it overruns the axes at print width.
handles = [plt.Line2D([], [], color=FAMCOL[f], lw=4, label=FAMLAB[f]) for f in FAMCOL]
# Lower left: after the axis inversion the high-z rows at the bottom all sit
# at high amplitude, so the bottom-left of the axes is empty, whereas the top
# rows carry the infeasibility annotations near zero.
ax.legend(handles=handles, fontsize=8.5, loc='lower left', framealpha=0.9)
fig.tight_layout()
os.makedirs(os.path.dirname(OUT), exist_ok=True)
fig.savefig(OUT, bbox_inches='tight', pad_inches=0.05)
print(f'wrote {OUT} ({len(rows)} cells)')

print(f"\n{'cell':52s}{'z':>7s}{'median':>9s}{'sd/mean':>9s}{'infeas':>8s}")
for r in rows:
    v = r['v']
    print(f"{r['design']} {r['catalog']} {r['target']:.1f} {r['family']:15s}"[:52].ljust(52)
          + f"{r['z']:7.2f}{np.median(v):9.1f}"
          + f"{100 * v.std(ddof=1) / max(v.mean(), 1e-9):8.0f}%"
          + f"{int((v == 0).sum()):5d}/{v.size}")
