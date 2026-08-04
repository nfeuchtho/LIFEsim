"""Does the six-aperture result survive giving it the field of view its own collectors imply?

The simulator derives BOTH the collecting area and the single-aperture field of
view from options.array['diameter'] (instrument.py:92-105), and settings.yaml
pins num_apertures=4, diameter=4.0 for every run. Under the thesis's stated
equal-total-area convention, a six-aperture design has 3.266 m collectors, whose
beam solid angle is 1.5x larger -- so the published run gives it the field of
view of a 4 m collector while charging it the area of six 3.266 m ones.

Local zodiacal light is uniform, so its collected rate scales with that solid
angle. This measures whether the reported mission-time advantage survives.
"""
import os
import sys
import time

import numpy as np

REPO = r'C:\Users\nicol\Desktop\LIFE\LIFESim'
sys.path.insert(0, REPO)
_cwd = os.getcwd()
import lifesim
os.chdir(_cwd)
sys.path.insert(0, os.path.join(REPO, 'lifesim', 'ams'))

from lifesim.ams.ablation_throughput import build_bus, ARMS
from lifesim.ams.core.ams import AgnosticMissionSimulator
from lifesim.util.combiner import double_triple_nuller, double_bracewell

CAT = 'hi'
AREA = 4 * np.pi * (4.0 / 2.0) ** 2
D6 = 2.0 * np.sqrt(AREA / (6.0 * np.pi))
print(f'total collecting area {AREA:.4f} m^2 -> six-aperture diameter {D6:.5f} m')
print(f'field-of-view solid angle ratio (4.0/{D6:.4f})^2 = {(4.0/D6)**2:.4f}\n')

bus, instrument, opt = build_bus(CAT, ARMS['control'])
ratio = bus.data.options.array['ratio']

CASES = [
    ('reference double Bracewell, 4 x 4.00 m', double_bracewell(1.0, ratio), 2, 4, 4.0),
    ('triple nuller, as published (4 x 4.00 m)', double_triple_nuller(1.0, ratio), 4, 4, 4.0),
    (f'triple nuller, 6 x {D6:.3f} m (same area)', double_triple_nuller(1.0, ratio), 4, 6, D6),
]

out = {}
for label, arch, order, n_ap, diam in CASES:
    bus.data.options.array['num_apertures'] = n_ap
    bus.data.options.array['diameter'] = diam
    instrument.apply_options()
    area = instrument.data.inst['telescope_area']
    hfov10 = np.interp(10e-6, instrument.data.inst['wl_bins'], instrument.data.inst['hfov'])

    ams = AgnosticMissionSimulator(order, 7, 65 / 360 * 2 * np.pi, 0.8, 12 * 60 * 60,
                                   architecture=arch, verbose=False)
    t0 = time.time()
    mt = ams.run(instrument, opt)
    out[label] = mt
    print(f'{label:44s} area {area:7.3f} m^2  hfov(10um) {hfov10*206264806:7.1f} mas '
          f'-> zero-budget MT {mt:.4f} yr   ({time.time()-t0:.0f} s)')

ref = out[CASES[0][0]]
print()
for label, _, _, _, _ in CASES[1:]:
    print(f'{label:44s} {100*(out[label]-ref)/ref:+6.2f} % vs reference')
