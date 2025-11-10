import math

import numpy as np
from lifesim.parametric_models.stellar_contrast.objects.instrument import Instrument
from lifesim.parametric_models.stellar_contrast.objects.blackbody import Blackbody
from lifesim.parametric_models.stellar_contrast.objects.star import Star
from lifesim.parametric_models.stellar_contrast.utils.unit_transformer import length_to_target


class Planet(Blackbody):
    """
    A planetary object.

    Attributes:
        temperature: The effective temperature of the planet in Kelvin.
        radius: The radius of the planet in Earth radii.
        separation: The orbiting distance from the star in AU.
        star: The stellar object the planet is orbiting.
    """
    separation: float
    temperature: float
    radius: float
    star: Star

    def __init__(self,
                 radius: float,
                 separation: float,
                 instrument: Instrument,
                 star: Star):
        """
        Creates a new Planet object.

        :param radius: The radius of the planet in Earth radii.
        :param separation: The orbiting distance from the star in AU.
        :param instrument: The instrument used to map the object.
        :param star: The stellar object the planet is orbiting.
        """

        # Bond Albedo of Earth
        a_b = 0.306

        # Equilibrium temperature
        temperature = (star.temperature * math.sqrt(star.radius / (2 * length_to_target(separation, 'au'))) *
                       math.pow(1 - a_b, 1/4))

        super().__init__(temperature, length_to_target(radius, 'earth'), instrument)
        self.star = star
        self.separation = separation

    def min_resolved_baselines(self,
                               distance: float):
        """
        Computes the minimum baselines the instrument must have for the planet to be
        resolved in the given wavelength band.

        :param distance: The distance from the star to the observer in parsec.
        :return: A tuple (completely resolved, just barely resolved) of baselines in meters.
        """

        separation = length_to_target(self.separation, 'au')
        distance = length_to_target(distance, 'pc')

        # The angular separation, this must equal to the respective resolution.
        ang_separation = np.arctan(separation / distance)

        wl_min = self.instrument.min_wavelength
        wl_max = self.instrument.max_wavelength

        # Math to compute the baseline.
        bl_fully_resolved = 0.589645 * wl_max / ang_separation
        bl_barely_resolved = 0.589645 * wl_min / ang_separation

        return bl_fully_resolved, bl_barely_resolved

    def astrophysical_contrast_ratio(self,
                                     distance: float,
                                     comment_analysis: bool = False):
        """
        Computes the integrated astrophysical flux contrast ratio of planet and star for given orbital parameters.


        :param distance: The observing distance in pc.
        :param comment_analysis: If true, will comment data about the resolving power of the instrument.
        :return: The astrophysical contrast ratio.
        """

        dist_pc = distance
        distance = length_to_target(distance, 'pc')
        separation = length_to_target(self.separation, 'au')

        # Resolution analysis
        ang_separation = np.arctan(separation / distance)

        def baseline_calc(resolution):
            # Compute the baseline distance in pc for a given resolution.
            return round(separation / length_to_target(np.tan(resolution), 'pc'), 2)

        if comment_analysis:
            print(f'[ ] The resolution horizons for this planet (d = {dist_pc}) are as follows:')
            print(f'[ ] Ideal        (fully resolved):     d < {baseline_calc(self.instrument.resolution_minimum)} pc.')
            print(f'[!] Satisfactory (partially resolved): d < {baseline_calc(self.instrument.resolution_maximum)} pc.')
            print(f'[X] Unsuitable   (not resolved):       d > {baseline_calc(self.instrument.resolution_maximum)} pc.')

            print('')

            wl_min = self.instrument.min_wavelength
            wl_max = self.instrument.max_wavelength

            if ang_separation > self.instrument.resolution_minimum:
                print('[ ] This planet is IDEAL. It may be resolved in every imaged wavelength.')
            elif self.instrument.resolution_minimum > ang_separation > self.instrument.resolution_maximum:
                cutoff_wavelength = ang_separation * 2 * self.instrument.baseline
                resolved_fraction = round(100 * (cutoff_wavelength - wl_min)
                                          / (wl_max - wl_min), 2)
                print('[!] This planet is SATISFACTORY. It may be resolved only in a subset of imaged wavelengths '
                      f'(cutoff {round(cutoff_wavelength * 1e6, 2)} microns, '
                      f'resolved in {resolved_fraction}% of the band).')
            else:
                print('[X] This planet is UNSUITABLE. It cannot be resolved in the given wavelength band. '
                      'Take the results below with caution.')


        dist_planet_obs = np.sqrt(separation**2 + distance**2)
        return (self.distant_flux(dist_planet_obs, 'm', ignore_transmission_map=True)
                / self.star.distant_flux(distance, 'm'))