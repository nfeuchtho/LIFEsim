"""Photon-rate ledger for the architecture comparison (round-7 P0.1 audit).

One row per (architecture, quantity), pinning every normalization the
comparison rests on to one explicit convention:

- aperture count N, collector area (shared 4 m collectors);
- per-output sky-averaged response <R> computed from the combiner row norm
  (for a lossless combiner with unit-norm rows and per-aperture fields
  carrying 1/N of the collected light, <R> = 1/N exactly);
- fraction of collected light in the chopped science pair (2/N);
- the architecture-independent product N * A_ap * <R> = A_ap that makes a
  uniform background's absolute rate identical between designs;
- the idealized sin^(2p) proxy averages (1/4, 3/16) whose ratio 0.750 is NOT
  the realizable scaling and must never be quoted against measured rates;
- measured background ratios (order 4 / order 2) from
  thesis/reproducibility/background_context.tsv.

Writes thesis/reproducibility/photon_ledger.tsv.
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, REPO)
from lifesim.util.combiner import double_bracewell, double_triple_nuller  # noqa: E402

OUT = os.path.join(REPO, 'thesis', 'reproducibility', 'photon_ledger.tsv')
BG = os.path.join(REPO, 'thesis', 'reproducibility', 'background_context.tsv')

rows = []
for name, fn, n_ap in (('bracewell4', double_bracewell, 4),
                       ('triple6', double_triple_nuller, 6)):
    positions, U, pair = fn(1.0, 6.0)
    # Some combiners return only the physically used rows of the lossless
    # matrix; every returned row must still be orthonormal.
    assert U.shape[1] == n_ap
    assert np.allclose(U @ U.conj().T, np.eye(U.shape[0]), atol=1e-12)
    row_norms = np.sum(np.abs(U) ** 2, axis=1)
    assert np.allclose(row_norms, 1.0)
    # Sky-average of the response map per output: with per-aperture fields
    # sqrt(1/N), the cross terms average to zero over the sky, leaving
    # sum_k |U_jk|^2 / N = 1/N.
    mean_response = row_norms[pair[0]] / n_ap
    area = n_ap * np.pi * 2.0 ** 2          # shared 4 m collectors -> r = 2 m
    rows.append(dict(architecture=name, n_apertures=n_ap,
                     collecting_area_m2=round(area, 1),
                     mean_response_per_output=f'1/{n_ap}',
                     mean_response_value=round(mean_response, 6),
                     science_pair_fraction=round(2.0 / n_ap, 4),
                     uniform_bg_invariant_NAapR_m2=round(
                         area / n_ap, 4)))       # N * A_ap * (1/N) = A_ap

led = pd.DataFrame(rows)

bg = pd.read_csv(BG, sep='\t')
meas = []
for cat in bg.catalog.unique():
    d2 = bg[(bg.catalog == cat) & (bg.null_order == 2)].set_index('wl_um')
    d4 = bg[(bg.catalog == cat) & (bg.null_order == 4)].set_index('wl_um')
    for term in ('localzodi', 'exozodi', 'star', 'total'):
        r = d4[term] / d2[term]
        meas.append(dict(catalog=cat, term=term,
                         ratio_4_over_2_median=round(float(r.median()), 4),
                         ratio_min=round(float(r.min()), 4),
                         ratio_max=round(float(r.max()), 4)))
meas = pd.DataFrame(meas)

with open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
    fh.write('# Convention ledger (one lossless-combiner convention throughout)\n')
    led.to_csv(fh, sep='\t', index=False)
    fh.write('\n# Idealized sin^(2p) proxy sky-averages (Appendix A): '
             'order2 = 1/4, order4 = 3/16; ratio 0.750 -- proxy-only.\n')
    fh.write('# Realizable per-output averages: 1/4 and 1/6; ratio 2/3. '
             'For a uniform background the absolute rate is N*A_ap*<R> = A_ap, '
             'identical between designs.\n')
    fh.write('\n# Measured background ratios, order 4 / order 2, from '
             'background_context.tsv\n')
    meas.to_csv(fh, sep='\t', index=False)

print(led.to_string(index=False))
print()
print(meas.to_string(index=False))
print(f'\nledger written: {OUT}')
