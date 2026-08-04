"""Is the chopped output subtraction a kernel in the Martinache/Laugier sense?

A kernel observable is a combination of nulled-output intensities whose
response to small per-aperture errors cancels at the leading (second) order,
leaving a steeper scaling. The operational test needs no definition dispute:
inject per-aperture piston phases phi_k ~ N(0, sigma) (and separately relative
amplitude errors), sweep sigma, and fit the log-log slope of

    leak  = <(I_a + I_b)/2>       null leakage of the deep outputs
    kern  = std(I_a - I_b)        the chopped observable actually used
    ctrl  = std(I_a - I_dark)     a deliberately non-conjugate pairing
                                  (double Bracewell only; its 4th output is a
                                  real second-order dark row)

If the subtraction has the kernel property, kern scales one order steeper than
leak; ctrl should NOT (that is the control). On-axis source, unit amplitudes,
so ideal outputs are exactly zero and every nonzero intensity is error leakage.

Pure combiner-matrix arithmetic: no AMS, no catalog, runs in seconds.
"""
import os
import sys

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, REPO)

from lifesim.util.combiner import double_bracewell, double_triple_nuller

RNG = np.random.default_rng(20260729)
SIGMAS = np.logspace(-4, -1, 7)
NDRAW = 40_000


def leakage(U, rows, sigma, n_ap, channel):
    """Intensities of the given output rows under random per-aperture errors."""
    if channel == 'piston':
        phi = RNG.normal(0.0, sigma, size=(NDRAW, n_ap))
        e = np.exp(1j * phi)
    else:                                   # relative amplitude errors
        eps = RNG.normal(0.0, sigma, size=(NDRAW, n_ap))
        e = (1.0 + eps).astype(complex)
    fields = e @ U[rows].T                  # (NDRAW, len(rows))
    return np.abs(fields) ** 2


def slopes(name, positions, U, pair, extra_dark=None):
    n_ap = positions.shape[0]
    a, b = pair
    for channel in ('piston', 'amplitude'):
        leak, kern, ctrl = [], [], []
        for s in SIGMAS:
            rows = [a, b] + ([extra_dark] if extra_dark is not None else [])
            inten = leakage(U, rows, s, n_ap, channel)
            leak.append(np.mean(0.5 * (inten[:, 0] + inten[:, 1])))
            kern.append(np.std(inten[:, 0] - inten[:, 1]))
            if extra_dark is not None:
                ctrl.append(np.std(inten[:, 0] - inten[:, 2]))
        lg = np.log10(SIGMAS)
        fit = lambda y: np.polyfit(lg, np.log10(y), 1)[0]
        line = (f'{name:<22} {channel:<10} leak slope {fit(leak):5.2f}   '
                f'kernel slope {fit(kern):5.2f}')
        if ctrl:
            line += f'   control slope {fit(ctrl):5.2f}'
        print(line, flush=True)


print(f'{NDRAW} draws per sigma, sigma in [{SIGMAS[0]:.0e}, {SIGMAS[-1]:.0e}] rad')
print('slope = d log(metric) / d log(sigma); kernel property = kernel slope '
      'steeper than leak slope, control slope NOT steeper\n')

pos, U, pair = double_bracewell(1.0, 6.0)
slopes('double_bracewell', pos, U, pair, extra_dark=3)

pos, U, pair = double_triple_nuller(1.0, 6.0)
slopes('double_triple_nuller', pos, U, pair)
