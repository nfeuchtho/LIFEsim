"""Five-aperture pentagon DFT nuller: does it break the six-aperture-minimum claim?

Construction: N=5 apertures on a regular pentagon of circumradius matching the
nulling-baseline convention; combiner U = 5-point DFT matrix rows (orthonormal
by construction). Row 0 is bright; rows j and 5-j are complex conjugates, so
(1,4) and (2,3) are candidate chopping pairs.

Harmonic argument to test: the first moment of row j against pentagon positions
couples only to harmonics +-1, so rows 2 and 3 should have vanishing first AND
surviving second moment -> amplitude ~ theta^2 -> fourth-order null. If the
(2,3) pair also modulates off-axis (nonzero, sign-structured kernel), then a
five-aperture fourth-order choppable design exists and the thesis's bolded
"six are the minimum" is wrong as stated.

Checks:
  1. Orthonormality of U.
  2. Measured null order of every output (combiner.null_order).
  3. Conjugacy of pairs (1,4) and (2,3).
  4. Kernel robustness of both pairs (piston sigma^2 -> sigma^3, amplitude exact).
  5. Off-axis modulation: K(phi) = I_a - I_b around a ring at fixed offset --
     must be nonzero and change sign with source azimuth for chopping to work.
"""
import os
import sys

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, REPO)

from lifesim.util.combiner import null_order, array_response

N = 5
BL = 1.0                      # circumradius; similarity variable handles scale
WL = 10e-6

phi_k = 2 * np.pi * np.arange(N) / N
positions = BL * np.column_stack([np.cos(phi_k), np.sin(phi_k)])
U = np.array([[np.exp(2j * np.pi * j * k / N) / np.sqrt(N) for k in range(N)]
              for j in range(N)])

print('1. orthonormality: max |U U^H - I| =',
      f'{np.abs(U @ U.conj().T - np.eye(N)).max():.2e}')

print('\n2. measured null orders (power-law fit near axis):')
for out in range(N):
    try:
        order = null_order(positions, U, out, WL, scale=BL)
        print(f'   output {out}: {order:.4f}')
    except Exception as e:
        print(f'   output {out}: bright or fit failed ({e})')

print('\n3. conjugacy: max |U[4]-conj(U[1])| =',
      f'{np.abs(U[4] - U[1].conj()).max():.2e},',
      'max |U[3]-conj(U[2])| =', f'{np.abs(U[3] - U[2].conj()).max():.2e}')

print('\n4. kernel robustness (slopes of log metric vs log sigma):')
rng = np.random.default_rng(20260730)
sigmas = np.logspace(-4, -1, 7)
for (a, b), label in [((1, 4), 'pair (1,4)'), ((2, 3), 'pair (2,3)')]:
    for channel in ('piston', 'amplitude'):
        leak, kern = [], []
        for s in sigmas:
            if channel == 'piston':
                e = np.exp(1j * rng.normal(0, s, size=(40000, N)))
            else:
                e = (1 + rng.normal(0, s, size=(40000, N))).astype(complex)
            inten = np.abs(e @ U[[a, b]].T) ** 2
            leak.append(np.mean(0.5 * (inten[:, 0] + inten[:, 1])))
            kern.append(np.std(inten[:, 0] - inten[:, 1]))
        lg = np.log10(sigmas)
        s_leak = np.polyfit(lg, np.log10(leak), 1)[0]
        with np.errstate(divide='ignore'):
            lk = np.log10(kern)
        s_kern = (np.polyfit(lg, lk, 1)[0] if np.isfinite(lk).all() else np.nan)
        note = ' (exact cancel)' if not np.isfinite(lk).all() else ''
        print(f'   {label} {channel:<10} leak {s_leak:5.2f}  kernel {s_kern:5.2f}{note}')

print('\n5. off-axis modulation of K = I_a - I_b, ring at theta = 0.3 lambda/BL:')
theta = 0.3 * WL / BL
for (a, b) in [(1, 4), (2, 3)]:
    K = []
    for az in np.linspace(0, 2 * np.pi, 12, endpoint=False):
        alpha, beta = theta * np.cos(az), theta * np.sin(az)
        Ia = np.abs(array_response(positions, U, alpha, beta, WL)[a]) ** 2 \
            if array_response.__code__.co_argcount else None
        K.append(None)
    # array_response signature: (positions, U, alpha, beta, wl) -> field/intensity?
    # fall back to direct evaluation to avoid signature guessing:
    K = []
    for az in np.linspace(0, 2 * np.pi, 12, endpoint=False):
        kvec = 2 * np.pi / WL * theta * np.array([np.cos(az), np.sin(az)])
        e = np.exp(1j * positions @ kvec)
        inten = np.abs(U @ e) ** 2 / N
        K.append(inten[a] - inten[b])
    K = np.array(K)
    print(f'   pair ({a},{b}): max |K| = {np.abs(K).max():.3e}, '
          f'sign changes over azimuth: {int(np.sum(np.diff(np.sign(K)) != 0))}')
