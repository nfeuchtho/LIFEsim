"""Fraction of catalog stars whose requested nulling baseline hits the clamp.

The per-star sizing (instrument.adjust_bl_to_hz -> apply_baseline) requests
bl = peak_const / hz_center_rad * wl_optimal, clipped to [bl_min, bl_max].
peak_const is each architecture's own response-peak constant. A design whose
peak sits at a larger similarity variable requests proportionally longer
baselines, and every clipped star sits off its fringe maximum with degraded
SNR. This counts, per design and catalog, the unique-star clip fractions.
"""
import os
import sys

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, REPO)
_cwd = os.getcwd()
import lifesim
os.chdir(_cwd)

from lifesim.ams.ablation_throughput import build_bus, ARMS
from lifesim.util.combiner import (double_bracewell, double_triple_nuller,
                                   kernel5, baseline_constant)

DESIGNS = {
    'bracewell4': double_bracewell(1.0, 6.0),
    'triple6': double_triple_nuller(1.0, 6.0),
    'kernel5_deep': kernel5(1.0, 'deep'),
    'kernel5_shallow': kernel5(1.0, 'shallow'),
}

for catalog in ('hi', 'lo'):
    bus, instrument, opt = build_bus(catalog, ARMS['control'])
    cat = bus.data.catalog.drop_duplicates('nstar')
    hz_rad = (cat['hz_center'] / cat['distance_s'] / (3600 * 180) * np.pi).to_numpy()
    wl_opt = bus.data.options.other['wl_optimal'] * 1e-6
    bl_min = bus.data.options.array['bl_min']
    bl_max = bus.data.options.array['bl_max']
    print(f'\n=== hab2{catalog}: {hz_rad.size} unique stars, '
          f'clamp [{bl_min:.0f}, {bl_max:.0f}] m, wl_opt {wl_opt*1e6:.1f} um')
    print(f'{"design":<16} {"const":>7} {"median bl":>10} {"clip@max":>9} '
          f'{"clip@min":>9} {"in range":>9}')
    for name, arch in DESIGNS.items():
        c = baseline_constant(*arch)
        bl = c / hz_rad * wl_opt
        hi_frac = float(np.mean(bl > bl_max))
        lo_frac = float(np.mean(bl < bl_min))
        print(f'{name:<16} {c:7.4f} {np.median(bl):9.1f}m {hi_frac:9.1%} '
              f'{lo_frac:9.1%} {1 - hi_frac - lo_frac:9.1%}')
