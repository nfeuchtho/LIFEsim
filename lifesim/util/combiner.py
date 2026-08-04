"""Transmission of an arbitrary nulling interferometer from its combiner matrix.

The transmission maps used elsewhere in LIFEsim are written out in closed form
for one specific architecture, the four-aperture double Bracewell. That is exact
for the reference array but cannot describe any other design, so a comparison
between null orders has to be made with a shape ansatz rather than with a real
combiner.

This module removes that restriction. A nulling interferometer is fully
specified by

    positions : where the collectors sit in the array plane, in metres
    U         : the beam-combiner matrix, one row per output, one column
                per aperture

For a source at sky offset ``theta`` the aperture amplitudes are
``a_k = exp(2j*pi * r_k . theta / lambda)`` and output ``j`` has intensity

    T_j(theta) = | sum_k U_jk a_k |^2 .

Everything else follows: null order, throughput, chopping behaviour and the
rotation-averaged response are all consequences of ``(positions, U)`` rather
than assumptions layered on top of a fixed formula.

A lossless combiner has orthonormal rows. The fraction of collected light that
reaches a given set of outputs is then just the number of those outputs divided
by the number of apertures, which is where the throughput cost of a deeper null
comes from: only some outputs carry the deep null.
"""

import numpy as np
# numpy 2.0 renamed trapz to trapezoid and removed the old name; keep both
# working so the package runs against either major version.
_trapz = np.trapezoid if hasattr(np, 'trapezoid') else np.trapz



def array_response(positions, U, alpha, beta, wl):
    """Intensity of every combiner output for sources at ``(alpha, beta)``.

    Parameters
    ----------
    positions : array_like, shape (n_ap, 2)
        Aperture positions in the array plane, in metres.
    U : array_like, shape (n_out, n_ap)
        Beam-combiner matrix. Rows are outputs; orthonormal rows describe a
        lossless combiner.
    alpha, beta : array_like
        Sky offsets in radians, broadcastable against each other.
    wl : float
        Wavelength in metres.

    Returns
    -------
    numpy.ndarray, shape (n_out,) + broadcast shape of (alpha, beta)
        Output intensities for unit-amplitude input from each aperture.
    """
    positions = np.asarray(positions, dtype=float)
    U = np.asarray(U, dtype=complex)
    alpha, beta = np.broadcast_arrays(np.asarray(alpha, dtype=float),
                                      np.asarray(beta, dtype=float))

    # phase picked up at each aperture, shape (n_ap,) + sky shape
    phase = 2j * np.pi / wl * (positions[:, 0].reshape((-1,) + (1,) * alpha.ndim) * alpha
                               + positions[:, 1].reshape((-1,) + (1,) * alpha.ndim) * beta)
    a = np.exp(phase)

    amp = np.tensordot(U, a, axes=([1], [0]))       # (n_out,) + sky shape

    # Normalize per unit collected intensity. With unit amplitude at each of
    # n_ap apertures the array collects n_ap units, and a lossless combiner
    # conserves that across its outputs. Dividing by n_ap makes the outputs sum
    # to one, so a response is directly the fraction of collected light reaching
    # that output -- which is what makes designs with different aperture counts
    # comparable without a separate throughput bookkeeping step.
    return np.abs(amp) ** 2 / positions.shape[0]


def rotation_average(positions, U, r, wl, n_phi=1024, moment=1):
    """Rotation average of each output's transmission at angular radius ``r``.

    The array rotates about the line of sight during an observation, which for a
    circularly symmetric source is equivalent to averaging the response over the
    azimuth of the source. The result is a one-dimensional function of angular
    separation, which is what the simulator's tabulated lookup needs.

    Parameters
    ----------
    r : array_like
        Angular separations in radians.
    n_phi : int
        Number of rotation samples. The response is a trigonometric polynomial
        in the rotation angle, so a uniform grid converges geometrically.
    moment : int
        Average ``T**moment``. ``moment=1`` gives the mean response, which sets
        the background photon rate; ``moment=2`` gives the mean square, needed
        for the noise coefficients.

    Returns
    -------
    numpy.ndarray, shape (n_out, len(r))
    """
    r = np.atleast_1d(np.asarray(r, dtype=float))
    phi = (np.arange(n_phi) + 0.5) * 2.0 * np.pi / n_phi
    alpha = r[:, None] * np.cos(phi)[None, :]        # (n_r, n_phi)
    beta = r[:, None] * np.sin(phi)[None, :]

    T = array_response(positions, U, alpha, beta, wl)   # (n_out, n_r, n_phi)
    return (T ** moment).mean(axis=-1)


def chopped_rotation_average(positions, U, out_a, out_b, r, wl, n_phi=1024,
                             moment=2):
    """Rotation average of the chopped difference between two outputs.

    The planet signal is recovered from the difference of a chopping pair, so
    the quantity the simulator needs is the root-mean-square of that difference
    over a rotation, not the mean of either output alone.
    """
    r = np.atleast_1d(np.asarray(r, dtype=float))
    phi = (np.arange(n_phi) + 0.5) * 2.0 * np.pi / n_phi
    alpha = r[:, None] * np.cos(phi)[None, :]
    beta = r[:, None] * np.sin(phi)[None, :]

    T = array_response(positions, U, alpha, beta, wl)
    diff = T[out_a] - T[out_b]
    return (diff ** moment).mean(axis=-1)


def null_order(positions, U, out, wl, scale, r_probe=None):
    """Empirical null order of one output near the optical axis.

    Fits a power law to ``T(r)`` over a range of small separations and returns
    the exponent. A second-order null returns about 2, a fourth-order null about
    4. ``scale`` is a representative baseline in metres, used only to place the
    probe radii well inside the first fringe.
    """
    if r_probe is None:
        r_probe = np.geomspace(1e-4, 1e-3, 24) * wl / scale
    T = rotation_average(positions, U, r_probe, wl, moment=1)[out]
    good = T > 0
    if good.sum() < 3:
        return np.nan
    p = np.polyfit(np.log(r_probe[good]), np.log(T[good]), 1)
    return float(p[0])


_AZ_CACHE = {}


def azimuthal_spline(u_pos, U, out, x_max, n_phi=360, dx=0.01, chunk=2000):
    """Cached spline of the rotation-averaged response against ``x``.

    The rotation average of any array whose geometry scales with a single
    baseline depends on ``x = pi * bl * theta / lambda`` alone, so it can be
    tabulated once per architecture and interpolated thereafter. This is what
    keeps an arbitrary combiner as cheap as the closed-form reference: the
    expensive part, an average over rotation angle, is paid once on a grid
    rather than per target and per wavelength.

    The table is cached and grown on demand if a later call needs a larger
    ``x_max``.
    """
    from scipy.interpolate import make_interp_spline

    key = (u_pos.tobytes(), u_pos.shape, U.tobytes(), U.shape, int(out), n_phi, dx)
    cached = _AZ_CACHE.get(key)
    if cached is not None and cached[0] >= x_max:
        return cached[1]

    # Round the table's extent up a coarse ladder. Callers ask for whatever
    # range their star and wavelength need, and rebuilding for each of them
    # would cost far more than the table saves; snapping to powers of two means
    # a handful of rebuilds at most over an entire catalogue.
    x_top = float(2.0 ** np.ceil(np.log2(max(x_max * 1.1, 16.0))))
    n_x = int(np.ceil(x_top / dx)) + 1
    x_grid = np.linspace(0.0, x_top, n_x)

    phi = np.arange(n_phi) * 2.0 * np.pi / n_phi
    proj = (u_pos[:, 0][:, None] * np.cos(phi)[None, :]
            + u_pos[:, 1][:, None] * np.sin(phi)[None, :])
    row = np.asarray(U, dtype=complex)[out]

    vals = np.empty(n_x)
    for lo in range(0, n_x, chunk):
        hi = min(lo + chunk, n_x)
        arg = 2.0 * x_grid[lo:hi][:, None, None] * proj[None, :, :]
        amp = np.exp(1j * arg)
        resp = np.abs(np.einsum('k,xkp->xp', row, amp)) ** 2 / u_pos.shape[0]
        vals[lo:hi] = resp.mean(axis=-1)

    spline = make_interp_spline(x_grid, vals, k=3)
    _AZ_CACHE[key] = (x_top, spline)
    return spline


def azimuthal_average_general(u_pos, U, out, r, bl, wl_bins, n_phi=360):
    """General-architecture counterpart of ``azimuthal_average_tm``.

    Rotation average of one output's response at angular separation ``r``.
    ``r`` and ``wl_bins`` broadcast against each other exactly as in the closed-
    form version, so this is interchangeable at the call site. Used by the
    extended-source terms, which integrate this against a radial profile.
    """
    u_pos = np.asarray(u_pos, dtype=float)
    U = np.asarray(U, dtype=complex)
    phi = np.arange(n_phi) * 2.0 * np.pi / n_phi
    proj = (u_pos[:, 0][:, None] * np.cos(phi)[None, :]
            + u_pos[:, 1][:, None] * np.sin(phi)[None, :])      # (n_ap, n_phi)

    x = np.pi * bl * np.asarray(r, dtype=float) / np.asarray(wl_bins, dtype=float)
    spline = azimuthal_spline(u_pos, U, out, float(np.nanmax(x)) if x.size else 1.0,
                              n_phi=n_phi)
    return spline(x)


def radial_average_general(u_pos, U, out, R, bl, wl_bins, hfov=None,
                           fov_taper='none', n_r=200, n_phi=360):
    """General-architecture counterpart of ``transmission_analytic.radial_average_tm``.

    Computes the rotation-averaged response of one output, averaged again over a
    source disk of angular radius ``R`` with the optional Gaussian field-of-view
    taper. This is what the background terms need: for a circularly symmetric
    foreground the photon rate is this average times the accepted solid angle.

    ``u_pos`` are the aperture positions in units of the nulling baseline, so the
    same architecture can be scaled per star by passing that star's ``bl``.
    Signature and conventions follow ``radial_average_tm`` so the two are
    interchangeable at the call site.
    """
    u_pos = np.asarray(u_pos, dtype=float)
    U = np.asarray(U, dtype=complex)
    wl_bins = np.atleast_1d(np.asarray(wl_bins, dtype=float))
    R_b = np.broadcast_to(np.atleast_1d(np.asarray(R, dtype=float)), wl_bins.shape)

    u = np.linspace(0.0, 1.0, n_r)                       # radial quadrature nodes

    # theta = u * R(lambda); the rotation average depends only on
    # x = pi * bl * theta / lambda, so it comes from the cached table.
    r = u[:, None] * R_b[None, :]                        # (n_r, n_wl)
    x = np.pi * bl * r / wl_bins[None, :]
    spline = azimuthal_spline(u_pos, U, out, float(np.nanmax(x)), n_phi=n_phi)
    ang_avg = spline(x)                                  # (n_r, n_wl)

    if fov_taper == 'none':
        weight = 1.0
    elif fov_taper == 'gaussian':
        if hfov is None:
            raise ValueError('hfov required for gaussian taper')
        hfov_b = np.broadcast_to(np.atleast_1d(np.asarray(hfov, dtype=float)),
                                 wl_bins.shape)
        weight = np.exp(-(np.pi / (4.0 * hfov_b[None, :]) * r) ** 2)
    else:
        raise ValueError('Nonexistent fov taper model')

    return 2.0 * _trapz(ang_avg * weight * u[:, None], u, axis=0)


def signal_noise_tables(positions, U, chop, x_grid, bl, n_phi=360, chunk=20000):
    """Tabulate the chopped signal and single-output noise coefficients.

    The simulator looks these up against the dimensionless separation
    ``x = pi * bl * theta / lambda``. Writing the aperture positions in units of
    the baseline, the phase at aperture k becomes ``2x (u_k . n(phi))`` with
    ``n(phi)`` the rotation direction, so the response depends on the geometry
    and on ``x`` alone. One table therefore serves every star and every
    wavelength, exactly as for the closed-form reference array, and that is what
    keeps the evaluation cheap for an arbitrary architecture.

    Returns ``(s_grid, n_grid)``: the root-mean-square chopped response and the
    root-mean-square single-output response over one rotation.
    """
    u = np.asarray(positions, dtype=float) / float(bl)
    U = np.asarray(U, dtype=complex)
    a_out, b_out = chop

    phi = np.arange(n_phi) * 2.0 * np.pi / n_phi
    nx, ny = np.cos(phi), np.sin(phi)
    proj = u[:, 0][:, None] * nx[None, :] + u[:, 1][:, None] * ny[None, :]  # (n_ap, n_phi)

    x_grid = np.asarray(x_grid, dtype=float)
    s_grid = np.empty(x_grid.size)
    n_grid = np.empty(x_grid.size)

    for lo in range(0, x_grid.size, chunk):
        hi = min(lo + chunk, x_grid.size)
        xg = x_grid[lo:hi][:, None, None]                     # (nx, 1, 1)
        amp = np.exp(2j * xg * proj[None, :, :])              # (nx, n_ap, n_phi)
        out = np.einsum('ok,xkp->oxp', U, amp)                # (n_out, nx, n_phi)
        T = np.abs(out) ** 2 / u.shape[0]

        chopped = T[a_out] - T[b_out]
        s_grid[lo:hi] = np.sqrt((chopped ** 2).mean(axis=-1))
        n_grid[lo:hi] = np.sqrt((T[b_out] ** 2).mean(axis=-1))

    return s_grid, n_grid


_BL_CACHE = {}


def baseline_constant(u_pos, U, chop, x_hi=12.0, n=6000, n_phi=720):
    """Baseline prescription constant for an architecture.

    LIFEsim sizes the array so that the first peak of the chopped response falls
    on the habitable-zone centre, via ``bl = c / theta_HZ * lambda_opt`` with a
    constant ``c`` fixed for the double Bracewell. That constant is simply the
    location of the response peak in units of ``pi``, and it is architecture
    specific: a design with a different fringe pattern peaks elsewhere and is
    badly mis-sized by another design's constant.

    Returning it from the architecture itself lets every design be evaluated at
    its own optimum, which is the only comparison that means anything.
    """
    key = (u_pos.tobytes(), u_pos.shape, np.asarray(U).tobytes(), tuple(chop),
           x_hi, n, n_phi)
    if key in _BL_CACHE:
        return _BL_CACHE[key]

    # coarse scan for the peak, then refine locally
    x = np.linspace(1e-4, x_hi, n)
    s, _ = signal_noise_tables(u_pos, U, chop, x, bl=1.0, n_phi=n_phi)
    i = int(np.argmax(s))
    lo = x[max(i - 2, 0)]
    hi = x[min(i + 2, n - 1)]
    xf = np.linspace(lo, hi, 400)
    sf, _ = signal_noise_tables(u_pos, U, chop, xf, bl=1.0, n_phi=n_phi)

    const = float(xf[int(np.argmax(sf))] / np.pi)
    _BL_CACHE[key] = const
    return const


def double_bracewell(bl, ratio):
    """LIFE's reference architecture as ``(positions, U)``.

    Four collectors on a rectangle: the nulling baseline ``bl`` along the first
    axis, the imaging baseline ``ratio * bl`` along the second. Each side pair
    forms a Bracewell null, and the two nulled outputs are recombined with a
    relative phase of pi/2 to give the two chopped dark outputs.

    Returns ``(positions, U, (out_a, out_b))`` where the last item names the
    chopping pair. Outputs are ordered ``[bright, chop_a, chop_b, dark]``.
    """
    x, y = bl / 2.0, ratio * bl / 2.0
    positions = np.array([[-x, -y],
                          [+x, -y],
                          [-x, +y],
                          [+x, +y]], dtype=float)

    e_m = np.exp(-1j * np.pi / 4) / 2.0
    e_p = np.exp(+1j * np.pi / 4) / 2.0

    U = np.array([
        [0.5, 0.5, 0.5, 0.5],                    # constructive
        [e_m, -e_m, e_p, -e_p],                  # chopped dark output A
        [e_p, -e_p, e_m, -e_m],                  # chopped dark output B
        [0.5, 0.5, -0.5, -0.5],                  # remaining orthogonal output
    ], dtype=complex)
    return positions, U, (1, 2)


def angel_cross(bl):
    """Four apertures on a square, combined to a fourth-order null.

    Two crossed Bracewell pairs. The amplitude of the deep output goes as the
    product of the two fringe terms, so its intensity vanishes to fourth order
    in the offset. Of the four orthogonal outputs only one carries that null,
    which is the origin of the 25 % figure quoted for this design: there is no
    second deep output to chop against, so this architecture cannot support the
    chopping scheme LIFE relies on. It is included as a reference point rather
    than as a candidate.
    """
    h = bl / 2.0
    positions = np.array([[-h, -h], [+h, -h], [-h, +h], [+h, +h]], dtype=float)
    U = np.array([
        [0.5, 0.5, 0.5, 0.5],        # bright
        [0.5, -0.5, -0.5, 0.5],      # crossed Bracewell: fourth-order null
        [0.5, 0.5, -0.5, -0.5],      # second-order
        [0.5, -0.5, 0.5, -0.5],      # second-order
    ], dtype=complex)
    return positions, U, (1, None)


def kernel5(bl, pair='deep'):
    """Five apertures on a regular pentagon with the 5-point DFT combiner.

    Row 0 is bright; rows j and 5-j are complex conjugates, giving two
    kernel/chopping pairs on the same hardware: (1, 4) couples to the
    fundamental harmonic of the aperture ring and nulls to second order,
    while (2, 3) has a vanishing first moment by harmonic orthogonality and
    nulls to fourth order (measured 2.0000 and 4.0000; see
    analysis/test_scripts/kernel5_check.py). The fourth-order pair carries
    2/5 of the collected light and modulates off-axis, so a five-aperture
    array supports the output subtraction at fourth order --- the
    counterexample to the six-aperture-minimum statement.

    ``pair='deep'`` returns the fourth-order pair (2, 3); ``pair='shallow'``
    the second-order pair (1, 4). Both matrices are identical; only the
    designated chopping pair differs, which makes the two configurations a
    null-depth comparison with every resource variable held fixed.

    The nuller family is due to Martinache & Ireland (2018) and Laugier et
    al. (2020); designating the fourth-order conjugate pair for LIFE-style
    chopping is what this work adds.
    """
    phi = 2.0 * np.pi * np.arange(5) / 5.0
    positions = (bl / 2.0) * np.column_stack([np.cos(phi), np.sin(phi)])
    U = np.array([[np.exp(2j * np.pi * j * k / 5) / np.sqrt(5.0)
                   for k in range(5)] for j in range(5)])
    return positions, U, ((2, 3) if pair == 'deep' else (1, 4))


def collinear4(bl):
    """Four apertures equally spaced on a line, with a fourth-order kernel pair.

    Real moment-cancelling rows give outputs of intensity order 2, 4 and 6
    (the 1-D ``2(N-1)`` rule at the deepest). The order-4 and order-6 rows
    remix losslessly into the conjugate pair ``(o4 +- i*o6)/sqrt(2)``, both of
    intensity order four, whose difference modulates off-axis: a four-aperture
    fourth-order array that supports LIFE-style output subtraction, carrying
    half the collected light (see analysis/test_scripts/collinear4_check.py).

    Together with ``kernel5`` this replaces the six-aperture-minimum claim:
    a fourth-order chop pair requires two rows whose amplitudes vanish to at
    least second order, and any two such rows can be remixed into one. The
    practical limit is the baseline envelope, not the aperture count: the
    pair's response peaks at x ~ 6.35 against the double Bracewell's 1.85, so
    at the mission's 100 m cap most catalog stars sit off-peak.
    """
    d = bl / 3.0
    positions = np.column_stack([np.arange(4) * d - 1.5 * d, np.zeros(4)])
    bright = np.ones(4) / 2.0
    o2 = np.array([3.0, 1.0, -1.0, -3.0]) / np.sqrt(20.0)
    o4 = np.array([1.0, -1.0, -1.0, 1.0]) / 2.0
    o6 = np.array([1.0, -3.0, 3.0, -1.0]) / np.sqrt(20.0)
    U = np.array([bright, o2,
                  (o4 + 1j * o6) / np.sqrt(2.0),
                  (o4 - 1j * o6) / np.sqrt(2.0)], dtype=complex)
    return positions, U, (2, 3)


def double_triple_nuller(bl, ratio):
    """Six apertures giving a choppable fourth-order null.

    The direct analogue of LIFE's architecture with each two-aperture Bracewell
    pair replaced by a three-aperture nuller of amplitudes 1 : -2 : 1. A single
    such triple has amplitude proportional to ``2(cos psi - 1)``, second order in
    the offset, so its intensity vanishes to fourth order -- the one-dimensional
    ``2(N-1)`` rule for ``N = 3``. Two triples separated along the imaging
    baseline are recombined with a relative phase of pi/2, exactly as the two
    Bracewell pairs are in the reference design, which produces two deep outputs
    of opposite modulation sign and therefore restores chopping.

    Six apertures are the minimum for this: a four-aperture fourth-order array
    has only one deep output and cannot chop.
    """
    d = bl / 2.0
    y = ratio * bl / 2.0
    positions = np.array([[-d, -y], [0.0, -y], [+d, -y],
                          [-d, +y], [0.0, +y], [+d, +y]], dtype=float)

    triple = np.array([1.0, -2.0, 1.0]) / np.sqrt(6.0)
    e_m = np.exp(-1j * np.pi / 4) / np.sqrt(2.0)
    e_p = np.exp(+1j * np.pi / 4) / np.sqrt(2.0)

    chop_a = np.concatenate([e_m * triple, e_p * triple])
    chop_b = np.concatenate([e_p * triple, e_m * triple])
    bright = np.ones(6) / np.sqrt(6.0)

    U = np.array([bright, chop_a, chop_b], dtype=complex)
    return positions, U, (1, 2)
