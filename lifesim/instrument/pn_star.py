from typing import Union

import numpy as np

from lifesim.core.modules import PhotonNoiseStarModule, TransmissionModule
from lifesim.util.radiation import planck_law
from lifesim.util import constants
from lifesim.util.transmission_analytic import radial_average_tm, gauss_legendre_wavenumber


class PhotonNoiseStar(PhotonNoiseStarModule):
    """
    This class simulates the noise contribution of central star to the interferometric measurement
    of LIFE due to leakage through the null.
    """

    def __init__(self,
                 name: str):
        """
        Parameters
        ----------
        name : str
            Name of the module.
        """

        super().__init__(name=name)
        self.add_socket(s_name='transmission_star',
                        s_type=TransmissionModule)

    def noise(self,
              index: Union[int, type(None)]):
        """
        Simulates the amount of photon noise originating from the star of the observed system
        leaking into the LIFE array measurement.

        Parameters
        ----------
        index: Union[int, type(None)]
            Specifies the planet for which to calculate the noise contribution. If an integer n is
            given, the noise will be calculated for the n-th row in the `data.catalog`. If `None`
            is given, the noise is caluculated for the parameters located in `data.single`.

        Returns
        -------
        sl_leak
            Stellar leakage in [photon s-1] per wavelength bin.

        Notes
        -----
        All of the following parameters are needed for the calculation of the exozodi noise
        contribution and should be specified either in `data.catalog` or in `data.single`.

        radius_s : float
            Radius of the observed star in [sun radii].
        distance_s : float
            Distance between the observed star and the LIFE array in [pc].
        temp_s : float
            Temperature of the observed star in [K].
        data.inst['wl_bins'] : np.ndarray
            Central values of the spectral bins in the wavelength regime in [m].
        data.inst['wl_widths'] : np.ndarray
            Widths of the spectral wavelength bins in [m].
        data.inst['telescope_area'] : float
            Area of all array apertures combined in [m^2].

        Raises
        ------
        ValueError
            If the specified transmission map does not exits.
        """

        if index is None:
            radius_s = self.data.single['radius_s']
            distance_s = self.data.single['distance_s']
            temp_s = self.data.single['temp_s']
        else:
            radius_s = self.data.catalog.radius_s.iloc[index]
            distance_s = self.data.catalog.distance_s.iloc[index]
            temp_s = self.data.catalog.temp_s.iloc[index]

        # convert units
        Rs_au = 0.00465047 * radius_s
        Rs_as = Rs_au / distance_s
        Rs_mas = float(Rs_as)
        Rs_rad = Rs_mas / (3600. * 180.) * np.pi

        # Stellar disk is circularly symmetric on the sky, so the pixel-grid average of
        # tm3 over the stellar disk equals its exact rotation (azimuthal) average -- computed
        # analytically here instead of via a brute 2D transmission-map grid.
        fov_taper = self.data.options.models['fov_taper']
        diameter = self.data.options.array['diameter']
        bl = self.data.inst['bl']
        # defaults to 2 (standard double Bracewell) via Instrument.apply_options(); the AMS
        # overwrites this shared instrument-state entry to model other nulling architectures --
        # see AgnosticMissionSimulator.get_snr and ANALYTIC_NOISE_REWRITE.md.
        nulling_order = self.data.inst.get('nulling_order', 2)

        # tm(wl) * planck(wl) oscillates as a chirp in wl (freq ~ bl*Rs_rad/wl**2), so the
        # old center-point-per-bin sample can be badly wrong for wide bins / large baselines.
        # Integrate the product over each bin with Gauss-Legendre quadrature in wavenumber
        # u=1/wl, which turns the chirp into a constant-frequency oscillation -- a fixed
        # low-order rule then stays accurate across the whole band. See
        # ANALYTIC_NOISE_REWRITE.md and transmission_analytic.gauss_legendre_wavenumber.
        wl_lo = self.data.inst['wl_bin_edges'][:-1]
        wl_hi = self.data.inst['wl_bin_edges'][1:]
        wl_nodes, gl_weights = gauss_legendre_wavenumber(wl_lo, wl_hi)

        geom = np.pi * ((radius_s * constants.radius_sun)
                        / (distance_s * constants.m_per_pc)) ** 2

        sl_leak = np.zeros_like(self.data.inst['wl_bins'])
        for wl_j, w_j in zip(wl_nodes, gl_weights):
            hfov_j = wl_j / (2. * diameter)
            avg_tm_j = radial_average_tm(R=Rs_rad, bl=bl, wl_bins=wl_j,
                                         hfov=hfov_j, fov_taper=fov_taper,
                                         nulling_order=nulling_order)
            planck_j = planck_law(x=wl_j, temp=temp_s, mode='wavelength') * geom
            sl_leak += w_j * avg_tm_j * planck_j

        sl_leak *= self.data.inst['telescope_area']

        return sl_leak
