"""Per-target SNR comparison between the two architectures under the current
sizing convention (shared 4 m collectors, so the six-aperture design carries
75.4 m^2 against 50.3). The previously reported median ratio of 0.93 and the
top-50 gain were measured when both designs shared a total area, so they do not
survive the convention change and are re-measured here."""
import os
import sys

import numpy as np

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
    top = a.sort_values(ascending=False).index[:50]
    print(f'\nhab2{cat}: {len(a)} visible host stars')
    print(f'  median per-target SNR ratio (six-aperture / reference) {np.median(r):.4f}')
    print(f'  fraction of targets worse under the deeper null         {100*(r < 1).mean():.1f} %')
    print(f'  ratio over the reference top-50 targets, median         {np.median(b[top]/a[top]):.4f}')
    print(f'  16th-84th percentile of the ratio                       '
          f'{np.percentile(r,16):.3f} to {np.percentile(r,84):.3f}')
