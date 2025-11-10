import numpy as np


class Instrument:
    """
    An instrument object used to vary the important baseline parameter.

    Attributes:
        min_wavelength: Minimum wavelength of the instrument in m.
        max_wavelength: Maximum wavelength of the instrument in m.
        min_baseline: Minimum allowed baseline of the instrument in m.
        max_baseline: Maximum allowed baseline of the instrument in m.
        baseline: Nulling baseline of the instrument in m.
        baseline_ratio: Ratio of baseline to nulling baseline.
        resolution_maximum: The maximum resolution of the instrument in rad.
        resolution_minimum: The minimum resolution of the instrument in rad.
    """
    min_wavelength: float
    max_wavelength: float
    min_baseline: float
    max_baseline: float
    baseline: float
    baseline_ratio: float
    resolution_maximum: float
    resolution_minimum: float


    def __init__(self,
                 min_wavelength: float,
                 max_wavelength: float,
                 min_baseline: float,
                 max_baseline: float,
                 baseline: float,
                 baseline_ratio: float):
        """
        Creates a new instrument with a given baseline.

        :param min_wavelength: Minimum wavelength of the instrument in m.
        :param max_wavelength: Maximum wavelength of the instrument in m.
        :param min_baseline: Minimum allowed baseline of the instrument in m.
        :param max_baseline: Maximum allowed baseline of the instrument in m.
        :param baseline: Nulling baseline of the instrument in m.
        :param baseline_ratio: Ratio of baseline to nulling baseline.
        """

        self.min_wavelength = min_wavelength
        self.max_wavelength = max_wavelength

        self.min_baseline = min_baseline
        self.max_baseline = max_baseline

        self.baseline_ratio = baseline_ratio

        self.switch_baseline(baseline)

    def __copy__(self):
        """Creates a deep copy of the instrument."""

        return Instrument(self.min_wavelength,
                          self.max_wavelength,
                          self.min_baseline,
                          self.max_baseline,
                          self.baseline,
                          self.baseline_ratio)


    def switch_baseline(self, new_baseline, override_restrictions=False):
        """
        Sets a new baseline and updates the resolution and transmission maps accordingly.

        :param new_baseline: The new baseline to be used.
        :param override_restrictions: If set to True, the restrictions on the baseline are ignored. Defaults to False.
        """

        # Set to maximum allowed limit if outside
        if not override_restrictions:
            new_baseline = max(self.min_baseline, new_baseline)
            new_baseline = min(self.max_baseline, new_baseline)

        self.baseline = new_baseline

        self.resolution_maximum = self.min_wavelength / (2 * self.baseline)
        self.resolution_minimum = self.max_wavelength / (2 * self.baseline)

    def transmission_map_full(self,
                              beta: float,
                              alpha: float,
                              wavelength: float):
        """
        Returns the transmission map of LIFE for a given wavelength and deflection from the line of sight.
        Source: Life II paper (include details!)

        :param wavelength: Wavelength in meters
        :param alpha: Angular deflection in x from line of sight in radians
        :param beta: Angular deflection in y from line of sight in radians
        :return: Transmittivity for the given parameters (0 = destructive, 1 = constructive)
        """

        l = self.baseline / 2

        return (np.sin(2 * np.pi * l * alpha / wavelength) ** 2
                * np.cos(2 * np.pi * self.baseline_ratio * l * beta / wavelength - np.pi / 4) ** 2)

    def transmission_map_alpha_integrated(self,
                                          alpha: float,
                                          wavelength: float,
                                          max_alpha: float):
        """
        Returns the transmission map of LIFE for a given wavelength and deflection from the line of sight,
        but integrated over one spatial (angular) dimension.
        Source: Life II paper (include details!)

        :param wavelength: Wavelength in meters
        :param alpha: Angular deflection in x from line of sight in radians
        :param max_alpha: Maximum angular deflection in x from line of sight in radians
        :return: 1D-integrated transmittivity for the given parameters (0 = destructive, 1 = constructive)
        """

        l = self.baseline / 2

        return (np.sqrt(max_alpha ** 2 - alpha ** 2)
                * np.sin(2 * np.pi * l * alpha / wavelength) ** 2)