import numpy as np
from scipy.special import j0, j1, comb


def _nulling_order_to_p(nulling_order):
    """Validates `nulling_order` and returns p = nulling_order / 2.

    Only even nulling orders have a nonzero rotation average: sin(x*cos(theta))**n
    is odd under theta -> theta+pi (which flips cos(theta) -> -cos(theta)) whenever
    n is odd, so a full-rotation average is identically zero for odd n -- not just
    unsupported, but physically degenerate. Even n reduces via the standard
    power-reduction formula to a pure cosine series in theta, which is what makes
    the closed form below possible.
    """
    if nulling_order < 2 or nulling_order % 2 != 0:
        raise ValueError('nulling_order must be a positive even integer '
                         f'(got {nulling_order}); odd orders average to zero '
                         'under a full array rotation.')
    return nulling_order // 2


def gauss_legendre_wavenumber(wl_lo, wl_hi, n=8):
    """Gauss-Legendre nodes/weights to integrate a function of wavelength over
    a bin [wl_lo, wl_hi], using the substitution u = 1/wl.

    Why u = 1/wl: the transmission terms are trig/Bessel functions of
    k*r = 2*pi*bl*r/wl -- a *chirp* in wl (instantaneous frequency
    ~ bl*r/wl**2 grows toward short wl). In u = 1/wl the same term is
    2*pi*bl*r*u, i.e. constant-frequency. A fixed low-order rule (same n
    everywhere) then resolves the oscillation uniformly across the whole
    band, instead of needing more nodes at short-wl / large-kr bins.

    wl_lo, wl_hi : array-like, shape (n_wl,)

    Returns
    -------
    wl_nodes : list of n arrays, each shape (n_wl,)
    weights : list of n arrays, each shape (n_wl,) -- already includes the
        1/u**2 Jacobian, so sum(w_j * f(wl_nodes_j)) approximates
        integral_{wl_lo}^{wl_hi} f(wl) dwl.
    """
    wl_lo = np.asarray(wl_lo, dtype=float)
    wl_hi = np.asarray(wl_hi, dtype=float)
    u_lo = 1.0 / wl_hi
    u_hi = 1.0 / wl_lo
    u_mid = 0.5 * (u_lo + u_hi)
    u_half = 0.5 * (u_hi - u_lo)

    x, w = np.polynomial.legendre.leggauss(n)

    wl_nodes = []
    weights = []
    for xj, wj in zip(x, w):
        u_j = u_mid + u_half * xj
        wl_nodes.append(1.0 / u_j)
        weights.append(wj * u_half / u_j ** 2)
    return wl_nodes, weights


def azimuthal_average_tm(r, bl, wl_bins, nulling_order=2):
    """Exact rotation (azimuthal) average of tm3/tm4 at fixed angular separation r [rad].

    tm3 = sin(pi*bl*r*cos(theta)/wl)**nulling_order
          * cos(ratio*pi*bl*r*sin(theta)/wl - pi/4)**2, with nulling_order=2 the
    standard double-Bracewell case. Averaging over the full 2*pi rotation angle
    theta collapses (even-power reduction + Jacobi-Anger expansion) to a closed
    form that is independent of `ratio` and of the +-pi/4 chop phase, so tm3 and
    tm4 share the identical rotation average, for any positive even
    `nulling_order` = 2*p:

        <tm> = 1/2 * C(2p,p)/4**p + sum_{j=1}^{p} (-1)**j * C(2p,p-j)/4**p * J0(j*k*r)

    with k = 2*pi*bl/wl (p=1 reproduces the original 1/4*(1-J0(k*r)) formula).
    See ANALYTIC_NOISE_REWRITE.md for the derivation and why odd orders don't work.

    r, bl, wl_bins must be broadcastable against each other.
    """
    p = _nulling_order_to_p(nulling_order)
    k = 2 * np.pi * bl / wl_bins
    kr = k * r
    result = 0.5 * comb(2 * p, p) / 4 ** p
    for j in range(1, p + 1):
        coeff = (-1.0) ** j * comb(2 * p, p - j) / 4 ** p
        result = result + coeff * j0(j * kr)
    return result


def disk_average_tm(R, bl, wl_bins, nulling_order=2):
    """Uniform-disk average (radius R [rad], no FoV taper) of tm3/tm4.

    Same harmonic sum as `azimuthal_average_tm`, with each J0(j*k*r) term
    integrated over the disk in closed form via d/dr[r*J1(cr)] = c*r*J0(cr):

        <tm>_disk = 1/2*C(2p,p)/4**p
                    + sum_{j=1}^{p} (-1)**j*C(2p,p-j)/4**p * 2*J1(j*k*R)/(j*k*R)
    """
    p = _nulling_order_to_p(nulling_order)
    k = 2 * np.pi * bl / wl_bins
    x = np.maximum(k * R, 1e-12)
    result = 0.5 * comb(2 * p, p) / 4 ** p
    for j in range(1, p + 1):
        coeff = (-1.0) ** j * comb(2 * p, p - j) / 4 ** p
        jx = j * x
        result = result + coeff * 2 * j1(jx) / jx
    return result


def radial_average_tm(R, bl, wl_bins, hfov=None, fov_taper='none', n_r=200, nulling_order=2):
    """Aperture/disk average of tm3 (== tm4) over radius R [rad], with optional
    gaussian FoV taper, replacing a brute 2D pixel-grid average.

    R may be a scalar or an array broadcastable against wl_bins (e.g. a
    wavelength-dependent FoV radius). Uses the substitution r = u*R with a
    fixed u in [0, 1] so a single quadrature grid works even when R varies per
    wavelength bin.
    """
    if fov_taper == 'none':
        return disk_average_tm(R, bl, wl_bins, nulling_order=nulling_order)
    if fov_taper != 'gaussian':
        raise ValueError('Nonexistent fov taper model')
    if hfov is None:
        raise ValueError('hfov required for gaussian taper')

    wl_bins = np.asarray(wl_bins, dtype=float)
    R_b = np.broadcast_to(np.asarray(R, dtype=float), wl_bins.shape)
    hfov_b = np.broadcast_to(np.asarray(hfov, dtype=float), wl_bins.shape)

    u = np.linspace(0.0, 1.0, n_r)[:, None]          # (n_r, 1)
    r = u * R_b[None, :]                             # (n_r, n_wl)
    ang_avg = azimuthal_average_tm(r, bl, wl_bins[None, :], nulling_order=nulling_order)
    taper = np.exp(-(np.pi / (4 * hfov_b[None, :]) * r) ** 2)
    integrand = ang_avg * taper * u
    return 2 * np.trapz(integrand, u[:, 0], axis=0)
