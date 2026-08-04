"""Distance histogram of the 4505-star scaffold, stacked by spectral type (the scaffold is F/G/K only)
(Felix D2 feedback, p.16): how many targets sit in each 10-pc shell.

Reads the unique stars of universe 0 from catalog_hab2hi.txt (the scaffold is
shared between catalogs and universes). Writes
thesis/images/background/scaffold_distances.pdf.
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SRC = os.path.join(REPO, 'lifesim', 'catalogs', 'catalog_hab2hi.txt')
OUT = os.path.join(REPO, 'thesis', 'images', 'background',
                   'scaffold_distances.pdf')

df = pd.read_csv(SRC, sep='\t', skiprows=[0])
stars = df.drop_duplicates('Nstar')[['Nstar', 'Ds', 'Stype']]
print(f'{len(stars)} unique scaffold stars')
assert len(stars) == 4505, len(stars)

bins = np.arange(0, 55, 10)
order = ['K', 'G', 'F']
greys = ['0.25', '0.55', '0.80']

fig, ax = plt.subplots(figsize=(6.0, 3.2))
bottom = np.zeros(len(bins) - 1)
for st, g in zip(order, greys):
    d = stars.loc[stars.Stype.str.upper().str.startswith(st), 'Ds']
    h, _ = np.histogram(d, bins=bins)
    ax.bar(bins[:-1], h, width=np.diff(bins), align='edge', bottom=bottom,
           color=g, edgecolor='white', linewidth=0.6, label=f'{st} ({d.size})')
    bottom += h
for x, htot in zip(bins[:-1], bottom):
    ax.annotate(f'{int(htot)}', (x + 5, htot), ha='center', va='bottom',
                fontsize=9)
ax.set_xlabel('Distance [pc]', fontsize=10)
ax.set_ylabel('Scaffold stars per 10-pc shell', fontsize=10)
ax.set_xticks(bins)
ax.tick_params(labelsize=9)
ax.legend(fontsize=9, frameon=False, title='Spectral type', title_fontsize=9)
ax.set_ylim(0, bottom.max() * 1.12)
fig.tight_layout()
os.makedirs(os.path.dirname(OUT), exist_ok=True)
fig.savefig(OUT, bbox_inches='tight', pad_inches=0.04)
print('wrote', OUT)
counts, _ = np.histogram(stars.Ds, bins=bins)
print('per-shell totals:', dict(zip([f'{a}-{b}' for a, b in
                                     zip(bins[:-1], bins[1:])], counts)))
