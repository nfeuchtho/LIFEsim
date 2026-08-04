"""Budget-shape figures drawn against the ensemble background, with uncertainty.

Replaces the simulator's plot mode for these panels. That mode resolves one
target by positional index (ams.py:634-636) and draws that star's background, so
the published figures combine an amplitude derived from the whole ensemble with
background curves belonging to a single arbitrary target -- one that sits at the
83rd percentile of the eligible population in distance and the 90th in effective
temperature. Here the background is the ensemble median that
run_background_context already computes, so amplitude and background refer to
the same population.

The imposed budget is an analytic function of its amplitude, flat or a ramp
anchored at zero on one end of the band, so the bootstrap interval on the
amplitude maps directly onto a band around the imposed curve. That band is the
point of the figure: the allowance is a measured quantity with a sampling
uncertainty, not a line.

    python plot_budget_shapes.py <design> <catalog> <target> [outfile.pdf]
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
REPRO = os.path.join(REPO, 'thesis', 'reproducibility')

design, catalog, target = sys.argv[1], sys.argv[2], float(sys.argv[3])
out = (sys.argv[4] if len(sys.argv) > 4 else
       os.path.join(REPO, 'thesis', 'images', 'tse',
                    f'budget_shapes_{design}_{catalog}_{str(target).replace(".", "p")}.pdf'))

order = 4 if design == 'triple6' else 2
bg = pd.read_csv(os.path.join(REPRO, 'background_context.tsv'), sep='\t')
bg = bg[(bg.catalog == f'hab2{catalog}') & (bg.null_order == order)].sort_values('wl_um')
if bg.empty:
    sys.exit(f'no background rows for hab2{catalog} order {order}')
wl = bg.wl_um.to_numpy()

FAMILIES = ['flat', 'short_weighted', 'long_weighted']
TITLE = {'flat': 'Flat', 'short_weighted': 'Short-weighted', 'long_weighted': 'Long-weighted'}


def shape(family, amp):
    """Imposed N_I as a function of wavelength, normalised to endpoint `amp`."""
    if family == 'flat':
        return np.full_like(wl, amp)
    frac = (wl - wl.min()) / (wl.max() - wl.min())
    # A ramp is named by the end that carries the allowance.
    return amp * (frac if family == 'long_weighted' else 1.0 - frac)


fig, axes = plt.subplots(1, 3, figsize=(10.8, 3.8), sharey=True)
for ax, family in zip(axes, FAMILIES):
    ttok = str(target).replace('.', 'p')
    tag = f'{design}_hab2{catalog}_{family}_{ttok}'
    # Corrected campaign shards only: the directory also holds the superseded
    # strict-era files and per-universe retention tables, which must not enter.
    hits = [h for h in glob.glob(os.path.join(
                REPRO, 'uncertainty',
                f'{design}_{catalog}_{family}_{ttok}_corrected*.tsv'))
            if '_universes' not in os.path.basename(h)]
    if not hits:
        print(f'  no corrected bootstrap data for {tag}, drawing without a band',
              file=sys.stderr)
        v = None
    else:
        v = (pd.concat([pd.read_csv(h, sep='\t') for h in sorted(hits)])
             .drop_duplicates('replicate').endpoint_ph_s_um.to_numpy(dtype=float))

    ax.plot(wl, bg.total, color='0.25', lw=1.4, label='Astrophysical background')
    ax.plot(wl, bg.star, color='tab:red', lw=0.9, ls=':', label='Stellar leakage')
    ax.plot(wl, bg.localzodi, color='tab:brown', lw=0.9, ls='-.', label='Local zodi')
    ax.plot(wl, bg.exozodi, color='tab:purple', lw=0.9, ls=(0, (4, 2)), label='Exozodi')

    if v is not None and v.size:
        med = np.median(v)
        lo, hi = np.percentile(v, 16), np.percentile(v, 84)
        ax.fill_between(wl, bg.total + shape(family, lo), bg.total + shape(family, hi),
                        color='tab:green', alpha=0.25, lw=0,
                        label='16th--84th percentile of the endpoint')
        ax.plot(wl, bg.total + shape(family, med), color='tab:green', lw=1.6,
                label=f'Background + budget (median {med:.0f})')
        ax.plot(wl, shape(family, med), color='tab:green', lw=1.0, ls='--',
                label='Imposed $N_I(\\lambda)$')
        n_zero = int((v == 0).sum())
        note = f'{v.size} replicates'
        if n_zero:
            note += f', {n_zero} with no allowance'
        ax.text(0.03, 0.04, note, transform=ax.transAxes, fontsize=7.5,
                color='crimson' if n_zero else '0.35')

    ax.set_title(TITLE[family], fontsize=10)
    ax.set_xlabel('Wavelength [$\\mu$m]')
    ax.set_yscale('log')
    ax.grid(alpha=0.25)

axes[0].set_ylabel('Spectral photon rate [ph s$^{-1}$ $\\mu$m$^{-1}$]')
# Legend below the panels: the upper left of the first panel carries the
# background curves, and a boxed legend there hides exactly what is being shown.
_h, _l = axes[0].get_legend_handles_labels()
fig.legend(_h, _l, fontsize=8, loc='lower center', ncol=4, frameon=False,
           bbox_to_anchor=(0.5, -0.01))
name = 'six-aperture fourth-order design' if design == 'triple6' else 'reference array'
fig.suptitle(f'Final budgets, {name}, '
             f"{'Hab2Max' if catalog == 'hi' else 'Hab2Min'} at {target:g} yr "
             f'(ensemble-median background)', fontsize=10.5)
fig.tight_layout(rect=(0, 0.10, 1, 1))
os.makedirs(os.path.dirname(out), exist_ok=True)
fig.savefig(out, bbox_inches='tight', pad_inches=0.06)
print(f'wrote {out}')
