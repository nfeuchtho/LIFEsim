import numpy as np
import scipy.integrate
from scipy import constants

from lifesim.parametric_models.stellar_contrast.objects.instrument import Instrument
from lifesim.parametric_models.stellar_contrast.utils.unit_transformer import length_to_target

class Blackbody:
    """
    A black body object.

    Attributes:
        temperature: The effective temperature of the black body in Kelvin.
        radius: The radius of the black body in meters.
        instrument: The instrument used to map the object.
    """
    temperature: float
    radius: float
    instrument: Instrument

    def __init__(self,
                 temperature: float,
                 radius : float,
                 instrument: Instrument):
        """
        Creates a Blackbody object.

        :param temperature: The temperature of the Blackbody in Kelvin.
        :param radius: The radius of the Blackbody in meters.
        :param instrument: The instrument used to map the object.
        """
        self.temperature = temperature
        self.radius = radius
        self.instrument = instrument

    def intensity(self,
                  wavelength: float):
        """
        Returns the flux of the black body at a certain wavelength.

        :param wavelength: observed wavelength in m
        :return: flux density of a black body for the given parameters in units ph/(s m3 sr-1)
        """

        a = 2 * constants.h * constants.c ** 2

        b = constants.h * constants.c / (wavelength * constants.k * self.temperature)

        intensity = a / (wavelength ** 5 * (np.exp(b) - 1))

        # Change W to ph/s
        intensity *= wavelength / (constants.h * constants.c)

        return intensity

    def transmittivity(self,
                       distance: float,
                       resolution: int = 0,
                       wl_bins: tuple[np.ndarray, np.ndarray] = None,
                       unit: str ='pc'):
        """
        Computes the stellar transmittivity and generates a transmittivity heatmap for the black body
        based on the transmission map.

        :param distance: The distance from the black body to the observer.
        :param resolution: The resolution of the heatmap. If 0, no heatmap is generated.
        :param wl_bins: The wavelength bins to use for the integration. Array of centerpoints and bin widths.
        :param unit: The unit of the distance parameter, standard is pc. Accepts m, au or pc.
        :return: Integrated stellar transmittivity ratio and the transmittivity heatmap as a 2D numpy array
                (the second return value is None if no heatmap is generated).
        """

        if self.instrument is None:
            return 1, None

        flux_mapped = self.distant_flux(distance, unit, wl_bins=wl_bins)
        flux_pure = self.distant_flux(distance, unit, wl_bins=wl_bins, ignore_transmission_map=True)

        if wl_bins is not None:
            stellar_contrast = np.divide(flux_mapped, flux_pure)
        else:
            stellar_contrast = flux_mapped / flux_pure

        heatmap = None

        if resolution > 0:

            wl_min = self.instrument.min_wavelength
            wl_max = self.instrument.max_wavelength

            # We need to integrate the heatmap separately over the wavelength only.
            alpha_max = np.arctan(self.radius / distance)

            samp = np.linspace(-1.2*alpha_max, 1.2*alpha_max, resolution)

            # We sample points uniformly from a square with a side length of two object radii.
            # Then, the transmission map is integrated over the wavelength
            # and then taken at the uniformly sampled points.
            # Points outside the object are rejected and their values set to zero.

            def integrand(wavelength, beta, alpha):
                # Generate a swapped integrand
                return self.instrument.transmission_map_full(beta, alpha, wavelength)

            heatmap = np.array([[scipy.integrate.quad(
                integrand, wl_min, wl_max, (beta, alpha))[0]
                                 / (wl_max - wl_min)
                                 if alpha ** 2 + beta ** 2 <= alpha_max ** 2
                                 else 0
                                 for alpha in samp] for beta in samp])

        return stellar_contrast, heatmap

    def __distant_flux_helper(self,
                              distance: float,
                              unit: str,
                              wl_bins: tuple[np.ndarray, np.ndarray],
                              ignore_transmission_map: bool):
        """
        Helper for integrating the observed flux of the uniformly radiating spherical black body
        through the transmission map. Will be vectorized if a numpy array is fed.

        :param distance: The distance from the surface of the sphere to the observer (scalar).
        :param unit: The unit of the distance parameter, standard is pc. Accepts m, au or pc.
        :param wl_bins: The wavelength bins to use for summation. Array of centerpoints and bin widths.
                                If None, full integration is performed instead and a scalar is returned.
        :param ignore_transmission_map: Whether to ignore the transmission map (total black body flux).
        :return: The observed integrated flux of the black body in units ph / (s m^2) for each wavelength bin.
        """
        wl_min = self.instrument.min_wavelength
        wl_max = self.instrument.max_wavelength

        if wl_bins is not None:
            wl_bins, wl_widths = wl_bins

        distance = length_to_target(distance, unit)

        #print(distance)

        # Compute maximum deflection from the line of sight due to finite radius
        alpha_max = np.arctan(self.radius / distance)

        # If no transmission map is needed, we can simply integrate over wavelength.
        if ignore_transmission_map:
            if wl_bins is None:
                return (scipy.integrate.quad(self.intensity, wl_min, wl_max)[0]
                        * np.pi * alpha_max ** 2)
            else:
                return np.array([self.intensity(wl) * np.pi * alpha_max ** 2 * w for wl, w in zip(wl_bins, wl_widths)])

        # Computing the total flux, we need to solve a three-dimensional integral.
        # 1. The wavelength must be integrated over the instrument range
        # 2. The transmission map must be integrated in the form of a disc centered at zero where
        #  2.1 the radius of the disc goes from zero to the maximum angular diameter of the object and
        #  2.2 the angle forms a full circle (zero to 2*pi).

        # We also note that the transmission map is a feature of the instrument.
        # This means the black body radiation intensity is first subjected to the inverse square law.
        # We can, however, move this factor outside the integral given the cosmic distances.
        alpha_range = (-alpha_max, alpha_max)
        wavelength_range = (wl_min, wl_max)

        # Use the transmission map to speed up the calculations.

        def integrand(alpha, wavelength):
            return (self.intensity(wavelength)
                   * self.instrument.transmission_map_alpha_integrated(alpha, wavelength, alpha_max))

        if wl_bins is None:
            flux = scipy.integrate.nquad(integrand,
                                             [alpha_range, wavelength_range])[0]
        else:
            flux = np.array([scipy.integrate.quad(integrand, -alpha_max, alpha_max, args=wl)[0] * w
                             for wl, w in zip(wl_bins, wl_widths)])

        return flux

    def distant_flux(self,
                     distance: float,
                     unit: str = 'pc',
                     wl_bins: tuple[np.ndarray, np.ndarray] = None,
                     ignore_transmission_map: bool = False):
        """
        Integrates the observed flux of the uniformly radiating spherical black body
        through the transmission map. Will be vectorized if a numpy array is fed.

        :param distance: The distance from the surface of the sphere to the observer (array or scalar).
        :param unit: The unit of the distance parameter, standard is pc. Accepts m, au or pc.
        :param ignore_transmission_map: Whether to ignore the transmission map (total black body flux).
        :param wl_bins: The wavelength bins to use for summation. Array of centerpoints and bin widths.
                                If None, full integration is performed instead and a scalar is returned.
        :return: The observed integrated flux of the black body in units ph / (s m^2) for each wavelength bin.
        """
        if isinstance(distance, np.ndarray):
            return np.vectorize(self.__distant_flux_helper)(
                (distance, unit,  wl_bins, ignore_transmission_map))
        else:
            return self.__distant_flux_helper(distance, unit, wl_bins, ignore_transmission_map)
