"""Why is kernel5_shallow's zero-budget mission time 17.6 yr?

Two hypotheses from the smoke test:

  A. Physics: the (1,4) pair's chopped transmission is intrinsically weak, and
     mission time scales roughly as the inverse square of the modulated signal.
  B. Bug: the AMS uses the concrete architecture for the signal tables but the
     sin^order proxy elsewhere (backgrounds, baseline sizing), so a pentagon at
     order 2 gets mismatched treatment -- which would also poison kernel5_deep.

Checks, all local and cheap:
  1. Peak RMS chopped transmission and its similarity-variable location for all
     four designs, from signal_noise_tables directly.
  2. The noise transmission (nz) at the same peak, and the signal/sqrt(noise)
     figure of merit each design is sized on.
  3. Ratio of mission-time predictions from the pure signal argument:
     t ~ (s_peak^2 / nz_peak)^-1 relative to bracewell4, compared against the
     measured zero-budget ratios (5.32 : 5.36 : 17.59 for b4 : k5d : k5s).
     Agreement -> hypothesis A (physics). Disagreement -> hypothesis B (bug).
"""
import os
import sys

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, REPO)

from lifesim.util.combiner import (double_bracewell, double_triple_nuller,
                                   kernel5, signal_noise_tables)

DESIGNS = {
    'bracewell4': double_bracewell(1.0, 6.0),
    'triple6': double_triple_nuller(1.0, 6.0),
    'kernel5_deep': kernel5(1.0, 'deep'),
    'kernel5_shallow': kernel5(1.0, 'shallow'),
}

x_grid = np.linspace(0.01, 12.0, 4000)
print(f'{"design":<16} {"s_peak":>8} {"x_peak":>7} {"nz@peak":>8} '
      f'{"FoM=s^2/nz":>11} {"t_rel (pred)":>13}')
fom = {}
for name, (pos, U, pair) in DESIGNS.items():
    s, nz = signal_noise_tables(pos, U, pair, x_grid, bl=1.0)
    i = int(np.argmax(s))
    fom[name] = s[i] ** 2 / max(nz[i], 1e-30)
    print(f'{name:<16} {s[i]:8.4f} {x_grid[i]:7.3f} {nz[i]:8.4f} '
          f'{fom[name]:11.5f}', end='')
    print(f' {fom["bracewell4"] / fom[name]:13.3f}' if 'bracewell4' in fom
          else ' (reference)')

print('\nmeasured zero-budget ratios vs bracewell4 (hi catalog): '
      'k5_deep 5.3576/5.3193 = 1.007, k5_shallow 17.5929/5.3193 = 3.307')
print('prediction column t_rel is the same ratio from transmission alone '
      '(area is equal for the two kernel5 modes, so it cancels between them).')
