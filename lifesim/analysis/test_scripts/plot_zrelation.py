"""The z-relation across every operating point and architecture.

Relative endpoint spread against the margin z, one marker per operating point:
filled markers are the eight original points the relation was stated on,
open markers the seventeen held-out points (intermediate targets and the
survey architectures), with a marker shape per design. The z >= 3 rule and
the ~40 % spread level it corresponds to are drawn as guides. This is the
out-of-sample validation figure for Sections 5.4 and 6.4.

Reads thesis/reproducibility/uncertainty/zpoints.tsv.

    python plot_zrelation.py [outfile.pdf]
"""
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SRC = os.path.join(REPO, 'thesis', 'reproducibility', 'uncertainty', 'zpoints.tsv')
OUT = (sys.argv[1] if len(sys.argv) > 1
       else os.path.join(REPO, 'thesis', 'images', 'tse', 'z_relation.pdf'))

MARK = {'bracewell4': ('o', 'Double Bracewell (4)'),
        'triple6': ('s', 'Double triple nuller (6)'),
        'kernel5_deep': ('D', 'Kernel-5, deep pair (5)'),
        'collinear4': ('^', 'Collinear kernel (4)')}

df = pd.read_csv(SRC, sep='\t')

fig, ax = plt.subplots(figsize=(6.5, 4.2))
for design, (m, label) in MARK.items():
    for orig, fill in ((1, 'full'), (0, 'none')):
        sub = df[(df.design == design) & (df.original_point == orig)]
        if not len(sub):
            continue
        # Marker: the flat-family spread (the classifier variable).
        # Bars: the range over the three budget families.
        ax.errorbar(sub.z, sub.rel_sd_flat,
                    yerr=[(sub.rel_sd_flat - sub.rel_sd_min).clip(lower=0),
                          (sub.rel_sd_max - sub.rel_sd_flat).clip(lower=0)],
                    fmt=m, fillstyle=fill, color='black', ecolor='0.6',
                    elinewidth=1.0, capsize=2, ms=6,
                    label=label if orig == 1 or
                    not len(df[(df.design == design) & (df.original_point == 1)])
                    else None)

ax.axvline(3.0, color='crimson', lw=1.0, ls='--', alpha=0.8)
ax.axhline(40.0, color='0.5', lw=0.8, ls=':', alpha=0.8)
ax.annotate('$z = 3$', (3.05, ax.get_ylim()[1] * 0.9), color='crimson', fontsize=9)
ax.set_xlabel('Margin $z$ above the feasibility boundary '
              '[sampling standard deviations]', fontsize=9.5)
ax.set_ylabel('Relative endpoint spread over resamples [%]', fontsize=9.5)
ax.tick_params(labelsize=8.5)
ax.grid(alpha=0.25)
handles, labels = ax.get_legend_handles_labels()
extra = [plt.Line2D([], [], marker='o', fillstyle='full', color='black', ls='',
                    label='original point'),
         plt.Line2D([], [], marker='o', fillstyle='none', color='black', ls='',
                    label='held out')]
ax.legend(handles=handles + extra, fontsize=8, framealpha=0.9)
fig.tight_layout()
os.makedirs(os.path.dirname(OUT), exist_ok=True)
fig.savefig(OUT)
print(f'wrote {OUT} ({len(df)} points)')
