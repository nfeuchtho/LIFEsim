"""Aperture-geometry sketch of the surveyed designs (Felix D2 feedback,
p.26): positions drawn from the same combiner.py constructors the results
use, at unit nulling baseline and the production imaging ratio 6.

Writes thesis/images/methods/architecture_sketch.pdf.
"""
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, REPO)
from lifesim.util.combiner import (double_bracewell, double_triple_nuller,
                                   kernel5, collinear4)  # noqa: E402

OUT = os.path.join(REPO, 'thesis', 'images', 'methods',
                   'architecture_sketch.pdf')

panels = [
    ('Double Bracewell (4)', double_bracewell(1.0, 6.0)[0]),
    ('Double triple nuller (6)', double_triple_nuller(1.0, 6.0)[0]),
    ('Kernel-5 pentagon (5)', kernel5(1.0)[0]),
    ('Collinear kernel (4)', collinear4(1.0)[0]),
]

fig, axes = plt.subplots(1, 4, figsize=(10.5, 3.0))
for ax, (title, pos) in zip(axes, panels):
    ax.scatter(pos[:, 0], pos[:, 1], s=140, facecolor='0.25',
               edgecolor='black', zorder=3)
    for j, (x, y) in enumerate(pos):
        ax.annotate(str(j + 1), (x, y), color='white', ha='center',
                    va='center', fontsize=7, zorder=4)
    ax.set_title(title, fontsize=10)
    ax.set_aspect('equal')
    span = max(abs(pos).max(), 0.8) * 1.35
    ax.set_xlim(-span, span)
    ax.set_ylim(-span, span)
    ax.axhline(0, color='0.85', lw=0.7, zorder=1)
    ax.axvline(0, color='0.85', lw=0.7, zorder=1)
    ax.set_xticks([])
    ax.set_yticks([])
for spine_ax in axes:
    for sp in spine_ax.spines.values():
        sp.set_color('0.6')
axes[0].set_ylabel('imaging axis $\\rightarrow$', fontsize=9)
axes[0].set_xlabel('nulling axis $\\rightarrow$', fontsize=9)
fig.tight_layout()
os.makedirs(os.path.dirname(OUT), exist_ok=True)
fig.savefig(OUT, bbox_inches='tight', pad_inches=0.04)
print('wrote', OUT)
for title, pos in panels:
    print(title, pos.round(3).tolist())
