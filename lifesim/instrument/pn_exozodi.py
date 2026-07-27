import numpy as np
from typing import Union

from lifesim.core.modules import PhotonNoiseUniverseModule
from lifesim.util import constants
from lifesim.util.radiation import planck_law
from lifesim.util.transmission_analytic import azimuthal_average_tm, gauss_legendre_wavenumber


class PhotonNoiseExozodi(PhotonNoiseUniverseModule):
    """
    This class simulates the noise contribution of an exozodi disk to the interferometric
    measurement of LIFE.
    """

    def __init__(self,
                 name: str):
        super().__init__(name=name)
        """
        Parameters
        ----------
        name : str
            Name of the module.
        """

    def noise(self,
              index: Union[int, type(None)]):
        """
        Simulates the amount of photon noise originating from the exozodi of the observed system
        leaking into the LIFE array measurement.

        Parameters
        ----------
        index: Union[int, type(None)]
            Specifies the planet for which to calculate the noise contribution. If an integer n is
            given, the noise will be calculated for the n-th row in the `data.catalog`. If `None`
            is given, the noise is caluculated for the parameters located in `data.single`.

        Returns
        -------
        ez_leak
            Exozodi leakage in [photon s-1] per wavelength bin.

        Notes
        -----
        All of the following parameters are needed for the calculation of the exozodi noise
        contribution and should be specified either in `data.catalog` or in `data.single`.

        l_sun : float
            Luminosity of the observed star in [solar luminosities].
        distance_s : float
            Distance between the observed star and the LIFE array in [pc].
        z : float
            Zodi level in the observed system in [zodis].
        data.inst['image_angle'] : np.ndarray
            Outer FoV radius in [rad] for each of the spectral bins, used as the outer bound
            of the radial integral over the exozodi disk.
        wl_bins : np.ndarray
            Central values of the spectral bins in the wavelength regime in [m].
        wl_widths : np.ndarray
            Widths of the spectral wavelength bins in [m].
        data.inst['telescope_area'] : float
            Area of all array apertures combined in [m^2].
        data.inst['t_map'] : np.ndarray
            Transmission map of the TM3 mode of the array created by the
            lifesim.TransmissionMap module.
        """

        # read from catalog or single data depending on index specification
        if index is None:
            l_sun = self.data.single['l_sun']
            distance_s = self.data.single['distance_s']
        else:
            l_sun = self.data.catalog.l_sun.iloc[index]
            distance_s = self.data.catalog.distance_s.iloc[index]

        # calculate the parameters required by Kennedy2015
        alpha = 0.34
        r_in = 0.034422617777777775 * np.sqrt(l_sun)  # [AU]
        r_0 = np.sqrt(l_sun)
        sigma_zero = 7.11889e-8  # Sigma_{m,0} from Kennedy+2015 (doi:10.1088/0067-0049/216/2/23)

        wl_bins = self.data.inst['wl_bins']
        bl = self.data.inst['bl']
        fov_taper = self.data.options.models['fov_taper']
        diameter = self.data.options.array['diameter']
        # defaults to 2 (standard double Bracewell) via Instrument.apply_options(); the AMS
        # overwrites this shared instrument-state entry to model other nulling architectures --
        # see AgnosticMissionSimulator.get_snr and ANALYTIC_NOISE_REWRITE.md.
        nulling_order = self.data.inst.get('nulling_order', 2)

        # Kennedy2015 surface density/temperature depend only on the distance from the star, and
        # the exozodi disk is circularly symmetric, so the 2D pixel-grid sum reduces to a 1D
        # radial integral, using the exact rotation (azimuthal) average of tm3 in place of a
        # brute 2D transmission-map grid.
        au_per_rad = (3600. * 180. / np.pi) * distance_s  # AU per rad of angular separation
        r_in_rad = r_in / au_per_rad  # scalar inner cutoff (Kennedy2015 inner radius), fixed
        #   physical size -- does NOT scale with wl, unlike the outer FoV bound (image_angle).
        #   So k(wl)*r_in is a genuine chirp across a wl bin (unlike localzodi, where both the
        #   integration domain and hfov scale with wl and the chirp cancels identically).

        n_r = 200
        u = np.linspace(0.0, 1.0, n_r)[:, None]                      # (n_r, 1)

        # tm(r, wl) * planck(wl) chirps across a wl bin through this wl-dependence of both
        # k=2*pi*bl/wl and the outer integration bound image_angle(wl) -- integrate each bin
        # with Gauss-Legendre quadrature in wavenumber u=1/wl (see
        # transmission_analytic.gauss_legendre_wavenumber for why) instead of sampling only the
        # bin-center wavelength.
        wl_lo = self.data.inst['wl_bin_edges'][:-1]
        wl_hi = self.data.inst['wl_bin_edges'][1:]
        wl_nodes, gl_weights = gauss_legendre_wavenumber(wl_lo, wl_hi)

        threshold = self.data.options.other['fov_threshold']
        ez_leak = np.zeros_like(wl_bins)
        for wl_j, w_j in zip(wl_nodes, gl_weights):
            hfov_j = wl_j / (2. * diameter)
            if fov_taper == 'gaussian':
                image_angle_j = hfov_j * 4 / np.pi * np.sqrt(-np.log(threshold))
            elif fov_taper == 'none':
                image_angle_j = hfov_j
            else:
                raise ValueError('Nonexistent fov taper model')

            # guard against a pathological case where the inner (Kennedy2015) cutoff falls
            # outside the FoV -- no disk is visible, so the outer bound must not go below it
            outer_rad_j = np.maximum(image_angle_j, r_in_rad)

            # Sigma and temp are power laws in r, diverging toward r_in -- log-spaced radial
            # samples (r = r_in * (R/r_in)^u) resolve that steep near-r_in region with far
            # fewer points than a uniform-in-r grid would need.
            log_ratio_j = np.log(outer_rad_j / r_in_rad)              # (n_wl,)
            r_j = r_in_rad * np.exp(u * log_ratio_j[None, :])         # (n_r, n_wl)
            r_au_j = r_j * au_per_rad

            # calculate the temperature at all radii according to Kennedy2015 Eq. 2
            temp_map_j = 278.3 * (l_sun ** 0.25) / np.sqrt(r_au_j)

            # calculate the Sigma (Eq. 3) in Kennedy2015
            sigma_j = sigma_zero * (r_au_j / r_0) ** (-alpha)

            # get the black body radiation (per steradian) emitted by the interexoplanetary dust
            f_nu_sr_j = planck_law(x=wl_j[None, :], temp=temp_map_j, mode='wavelength') \
                        * sigma_j * self.data.inst['telescope_area']

            arch = self.data.inst.get('architecture')
            if arch is not None:
                from lifesim.util.combiner import azimuthal_average_general
                u_pos, U_mat, chop_pair = arch
                ang_avg_j = azimuthal_average_general(u_pos, U_mat, chop_pair[1],
                                                      r_j, bl, wl_j[None, :])
            else:
                ang_avg_j = azimuthal_average_tm(r_j, bl, wl_j[None, :],
                                                 nulling_order=nulling_order)
            if fov_taper == 'gaussian':
                taper_j = np.exp(-(np.pi / (4 * hfov_j[None, :]) * r_j) ** 2)
            else:
                taper_j = 1.0

            # jacobian for r = r_in*exp(u*log_ratio): dr = r*log_ratio du, combined with the
            # existing "* r" area element gives an extra factor of r (i.e. r**2 overall)
            integrand_j = f_nu_sr_j * ang_avg_j * taper_j * r_j ** 2
            ez_leak_j = 2 * np.pi * log_ratio_j * np.trapz(integrand_j, u[:, 0], axis=0)
            ez_leak += w_j * ez_leak_j

        return ez_leak