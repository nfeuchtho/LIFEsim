"""Per-target SNR comparison between the two architectures under the current
sizing convention (shared 4 m collectors, so the six-aperture design carries
75.4 m^2 against 50.3). The previously reported median ratio of 0.93 and the
top-50 gain were measured when both designs shared a total area, so they do not
survive the convention change and are re-measured here.

Equal-area ablation (exact, no third run): every photon rate in the SNR chain
-- planet signal, stellar leakage, local- and exozodiacal backgrounds -- is
linear in the per-aperture collecting area, so a global area rescale multiplies
SNR by sqrt(area ratio) exactly. Dividing the measured per-target ratio by
sqrt(75.4/50.3) = sqrt(1.5) therefore isolates the combiner change (null
depth, response shape, and science-pair fraction together) at equal collecting
area. Writes thesis/reproducibility/snr_shift_architectures.tsv."""
import os
import sys

import numpy as np
import pandas as pd

REPO = r'C:\Users\nicol\Desktop\LIFE\LIFESim'
sys.path.insert(0, REPO)
_cwd = os.getcwd()
import lifesim
os.chdir(_cwd)
from lifesim.ams.ablation_throughput import build_bus, ARMS
from lifesim.ams.core.ams import AgnosticMissionSimulator
from lifesim.util.combiner import double_bracewell, double_triple_nuller

for cat in ('hi', 'lo'):
    bus, instrument, opt = build_bus(cat, ARMS['control'])
    bus.data.options.other['n_cpu'] = 2
    ratio = bus.data.options.array['ratio']
    snr = {}
    for tag, fn, order in (('ref', double_bracewell, 2), ('t6', double_triple_nuller, 4)):
        ams = AgnosticMissionSimulator(order, 7, 65 / 360 * 2 * np.pi, 0.8, 12 * 3600,
                                       architecture=fn(1.0, ratio), verbose=False)
        ams.run(instrument, opt)
        c = instrument.data.catalog
        # one row per host star, best planet, restricted to targets the mission can see
        s = c.sort_values(['nstar', 'snr_1h'], ascending=[True, False]).groupby('nstar').first()
        snr[tag] = s['snr_1h']

    a, b = snr['ref'].align(snr['t6'], join='inner')
    vis = a > 0
    a, b = a[vis], b[vis]
    r = b / a
    sqrt_area = np.sqrt(75.4 / 50.3)
    q = r / sqrt_area                     # equal-area combiner factor
    top = a.sort_values(ascending=False).index[:50]
    print(f'\nhab2{cat}: {len(a)} visible host stars')
    print(f'  median per-target SNR ratio (six-aperture / reference) {np.median(r):.4f}')
    print(f'  fraction of targets worse under the deeper null         {100*(r < 1).mean():.1f} %')
    print(f'  ratio over the reference top-50 targets, median         {np.median(b[top]/a[top]):.4f}')
    print(f'  16th-84th percentile of the ratio                       '
          f'{np.percentile(r,16):.3f} to {np.percentile(r,84):.3f}')
    print(f'  equal-area (/{sqrt_area:.4f}) median combiner factor    {np.median(q):.4f}')
    print(f'  equal-area top-50 median combiner factor                '
          f'{np.median(b[top]/a[top])/sqrt_area:.4f}')
    print(f'  equal-area fraction of targets below 1                  {100*(q < 1).mean():.1f} %')
    print(f'  equal-area 16th-84th percentile                         '
          f'{np.percentile(q,16):.3f} to {np.percentile(q,84):.3f}')
    out = pd.DataFrame({'nstar': a.index, 'snr_ref': a.values, 'snr_t6': b.values,
                        'ratio': r.values, 'ratio_equal_area': q.values,
                        'in_ref_top50': a.index.isin(top)})
    dst = os.path.join(REPO, 'thesis', 'reproducibility',
                       f'snr_shift_architectures_{cat}.tsv')
    out.to_csv(dst, sep='\t', index=False, float_format='%.6g')
    print(f'  written: {dst}')
