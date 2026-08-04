"""Collinear four-aperture array: does it admit a fourth-order chopping pair?

Construction: four apertures equally spaced on a line. Orthonormal real
combiner rows by moment cancellation (1-D rule, order 2(N-1) at the deepest):

    bright ~ (1, 1, 1, 1)      order 0
    o2     ~ (3, 1, -1, -3)    kills the 0th moment          -> intensity order 2
    o4     ~ (1, -1, -1, 1)    kills 0th and 1st moments     -> intensity order 4
    o6     ~ (1, -3, 3, -1)    kills 0th, 1st, 2nd moments   -> intensity order 6

(o4, o6) are the examiner's measured 4.000/6.000 outputs. Real rows are their
own conjugates, so neither real pairing is a kernel pair. But the lossless
remix (o4 +- i*o6)/sqrt(2) is an orthonormal CONJUGATE pair, each of intensity
order 4 (amplitude ~ psi^2 +- i psi^3), and its intensity difference is
4*Im(conj(a4)*a6), which need not vanish off-axis. If that difference
modulates with source azimuth, a four-aperture fourth-order choppable design
exists and the thesis's four-aperture impossibility argument fails as stated
(it counted orthogonal outputs of fixed real form, not lossless remixes).

Battery: orthonormality, measured null orders, conjugacy, kernel robustness
(piston sigma^2 -> sigma^3, amplitude exact), off-axis modulation of the
kernel difference around a ring, plus the same at several ring radii (a 1-D
array's modulation depends on the projected baseline, so sample azimuths
densely).
"""
import os
import sys

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, REPO)

from lifesim.util.combiner import null_order

BL = 1.0
WL = 10e-6
d = BL / 3.0                       # four apertures spanning one baseline BL
positions = np.column_stack([np.arange(4) * d - 1.5 * d, np.zeros(4)])

bright = np.ones(4) / 2.0
o2 = np.array([3.0, 1.0, -1.0, -3.0]) / np.sqrt(20.0)
o4 = np.array([1.0, -1.0, -1.0, 1.0]) / 2.0
o6 = np.array([1.0, -3.0, 3.0, -1.0]) / np.sqrt(20.0)

U_real = np.array([bright, o2, o4, o6], dtype=complex)
chop_a = (o4 + 1j * o6) / np.sqrt(2.0)
chop_b = (o4 - 1j * o6) / np.sqrt(2.0)
U_mix = np.array([bright, o2, chop_a, chop_b], dtype=complex)

for name, U in (('real rows', U_real), ('mixed pair', U_mix)):
    print(f'{name}: max |U U^H - I| = '
          f'{np.abs(U @ U.conj().T - np.eye(4)).max():.2e}')

print('\nmeasured null orders (real rows):')
for out, label in ((1, 'o2'), (2, 'o4'), (3, 'o6')):
    print(f'   {label}: {null_order(positions, U_real, out, WL, scale=BL):.4f}')
print('measured null orders (mixed pair):')
for out, label in ((2, 'chop_a'), (3, 'chop_b')):
    print(f'   {label}: {null_order(positions, U_mix, out, WL, scale=BL):.4f}')

print('\nconjugacy: max |chop_b - conj(chop_a)| =',
      f'{np.abs(U_mix[3] - U_mix[2].conj()).max():.2e}')

print('\nkernel robustness (slopes of log metric vs log sigma):')
rng = np.random.default_rng(20260731)
sigmas = np.logspace(-4, -1, 7)
for channel in ('piston', 'amplitude'):
    leak, kern = [], []
    for s in sigmas:
        if channel == 'piston':
            e = np.exp(1j * rng.normal(0, s, size=(40000, 4)))
        else:
            e = (1 + rng.normal(0, s, size=(40000, 4))).astype(complex)
        inten = np.abs(e @ U_mix[[2, 3]].T) ** 2
        leak.append(np.mean(0.5 * (inten[:, 0] + inten[:, 1])))
        kern.append(np.std(inten[:, 0] - inten[:, 1]))
    lg = np.log10(sigmas)
    s_leak = np.polyfit(lg, np.log10(leak), 1)[0]
    with np.errstate(divide='ignore'):
        lk = np.log10(kern)
    finite = np.isfinite(lk).all()
    s_kern = np.polyfit(lg, lk, 1)[0] if finite else np.nan
    note = '' if finite else ' (exact cancel)'
    print(f'   {channel:<10} leak {s_leak:5.2f}  kernel {s_kern:5.2f}{note}')

print('\noff-axis modulation of K = I_a - I_b (mixed pair):')
for x in (0.15, 0.3, 0.6):
    theta = x * WL / BL
    K = []
    for az in np.linspace(0, 2 * np.pi, 48, endpoint=False):
        kvec = 2 * np.pi / WL * theta * np.array([np.cos(az), np.sin(az)])
        e = np.exp(1j * positions @ kvec)
        inten = np.abs(U_mix @ e) ** 2 / 4.0
        K.append(inten[2] - inten[3])
    K = np.array(K)
    print(f'   ring x={x}: max |K| = {np.abs(K).max():.3e}, '
          f'RMS = {np.sqrt((K**2).mean()):.3e}, '
          f'sign changes: {int(np.sum(np.diff(np.sign(K)) != 0))}')
