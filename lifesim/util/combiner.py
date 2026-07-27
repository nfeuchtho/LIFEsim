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
