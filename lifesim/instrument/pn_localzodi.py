from typing import Union

import numpy as np

from lifesim.core.modules import PhotonNoiseStarModule
from lifesim.util.radiation import black_body
from lifesim.util.transmission_analytic import radial_average_tm


class PhotonNoiseLocalzodi(PhotonNoiseStarModule):
    """
    This class simulates the noise contribution of the thermal localzodical dust to the
    interferometric measurement of LIFE.
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

    def noise(self,
              index: Union[int, type(None)]):
        """
        Simulates the amount of photon noise originating from the localzodi leaking into the LIFE
        array measurement.

        Parameters
        ----------
        index: Union[int, type(None)]
            Specifies the planet for which to calculate the noise contribution. If an integer n is
            given, the noise will be calculated for the n-th row in the `data.catalog`. If `None`
            is given, the noise is caluculated for the parameters located in `data.single`.

        Returns
        -------
        lz_leak
            Localzodi leakage in [photon s-1] per wavelength bin.

        Notes
        -----
        All of the following parameters are needed for the calculation of the localzodi noise
        contribution and should be specified either in `data.catalog` or in `data.single`.

        lat_s : str
            Ecliptic latitude of the observed star in [rad].
        data.options.models['localzodi'] : str
            Specifies which localzodi model will be used.
        data.inst['wl_bins'] : np.ndarray
            Central values of the spectral bins in the wavelength regime in [m].
        data.inst['wl_widths'] : np.ndarray
            Widths of the spectral wavelength bins in [m].
        data.inst['hfov'] : np.ndarray
            Contains the half field of view of the observatory in [rad] for each of the spectral
            bins.
        data.inst['image_angle'] : np.ndarray
            Outer FoV radius in [rad] for each of the spectral bins, used as the disk radius
            over which the transmission map is analytically averaged.
        data.inst['telescope_area'] : float
            Area of all array apertures combined in [m^2].

        Raises
        ------
        ValueError
            If the specified localzodi model does not exits.
        """
        # TODO Implement longitude dependence of localzodi
        # TODO Find model after which this is calculated and reference

        if index is None:
            lat_s = self.data.single['lat']
        else:
            lat_s = self.data.catalog.lat.iloc[index]

        # check if the model exists
        if not ((self.data.options.models['localzodi'] == 'glasse')
                or (self.data.options.models['localzodi'] == 'darwinsim')):
            raise ValueError('Specified model does not exist')

        # fix the longitude of the observation. Since the simulation is static in time (planets not
        # moving), the longitude is fixed
        long = 3 / 4 * np.pi
        lat = lat_s

        # calculate the localzodi flux depending on the correct model
        if self.data.options.models['localzodi'] == 'glasse':
            temp = 270
            epsilon = 4.30e-8
            lz_flux_sr = epsilon * black_body(mode='wavelength',
                                              bins=self.data.inst['wl_bins'],
                                              width=self.data.inst['wl_bin_widths'],
                                              temp=temp)

        else:
            radius_sun_au = 0.00465047  # in AU
            tau = 4e-8
            temp_eff = 265
            temp_sun = 5777
            a = 0.22


            b_tot = black_body(mode='wavelength',
                               bins=self.data.inst['wl_bins'],
                               width=self.data.inst['wl_bin_widths'],
                               temp=temp_eff) + a \
                    * black_body(mode='wavelength',
                                 bins=self.data.inst['wl_bins'],
                                 width=self.data.inst['wl_bin_widths'],
                                 temp=temp_sun) \
                    * (radius_sun_au / 1.5) ** 2

            lz_flux_sr = tau * b_tot * np.sqrt(
                np.pi / np.arccos(np.cos(long) * np.cos(lat)) /
                (np.sin(lat) ** 2
                 + (0.6 * (self.data.inst['wl_bins'] / 11e-6) ** (-0.4) * np.cos(lat)) ** 2)
            )

        lz_flux = lz_flux_sr * (np.pi * self.data.inst['image_angle'] ** 2)

        # localzodi surface brightness is uniform across the (tiny) instrument FoV, so the
        # pixel-grid average of tm3 over the FoV equals its exact rotation (azimuthal)
        # average -- computed analytically here instead of via a brute 2D grid.
        arch = self.data.inst.get('architecture')
        if arch is not None:
            from lifesim.util.combiner import radial_average_general
            u_pos, U_mat, chop_pair = arch
            avg_tm = radial_average_general(
                u_pos, U_mat, chop_pair[1],
                R=self.data.inst['image_angle'],
                bl=self.data.inst['bl'],
                wl_bins=self.data.inst['wl_bins'],
                hfov=self.data.inst['hfov'],
                fov_taper=self.data.options.models['fov_taper'])
            return avg_tm * lz_flux * self.data.inst['telescope_area']

        avg_tm = radial_average_tm(R=self.data.inst['image_angle'],
                                   bl=self.data.inst['bl'],
                                   wl_bins=self.data.inst['wl_bins'],
                                   hfov=self.data.inst['hfov'],
                                   fov_taper=self.data.options.models['fov_taper'],
                                   # defaults to 2 via Instrument.apply_options(); the AMS
                                   # overwrites this shared instrument-state entry to model
                                   # other nulling architectures.
                                   nulling_order=self.data.inst.get('nulling_order', 2))

        # calculate the leakage contribution to the measurement
        lz_leak = avg_tm * lz_flux * self.data.inst['telescope_area']

        return lz_leak
