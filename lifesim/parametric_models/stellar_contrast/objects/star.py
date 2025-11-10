from lifesim.parametric_models.stellar_contrast.objects.instrument import Instrument
from lifesim.parametric_models.stellar_contrast.objects.blackbody import Blackbody
from lifesim.parametric_models.stellar_contrast.utils.unit_transformer import length_to_target
from lifesim.parametric_models.stellar_contrast.utils.lifesim_importer import get_ehz

class Star(Blackbody):
    """
    A stellar object.

    Attributes:
        spectral_type: The spectral type of the star.
        temperature: The effective temperature of the star in Kelvin.
        radius: The radius of the star in m.
        instrument: The instrument used to map the object.
    """
    spectral_type: str
    temperature: float
    radius: float
    instrument: Instrument
    planets: list

    def __init__(self,
                 spectral_type: str,
                 temperature: float,
                 radius: float,
                 instrument: Instrument):
        """
        Creates a new Star object.

        :param spectral_type: The spectral type of the star.
        :param temperature: The effective temperature of the star in Kelvin.
        :param radius: The radius of the star in solar radii.
        :param instrument: The instrument used to map the object.
        """

        # Use LIFESim to compute the habitable zone.
        inner_edge, outer_edge = get_ehz(temperature, radius)

        super().__init__(temperature, length_to_target(radius, 'sun'), instrument)
        self.spectral_type = spectral_type
        self.h_inner = inner_edge
        self.h_outer = outer_edge

        self.planets = list()

    def __copy__(self):
        """
        Creates a deep copy of the star, also deep-copies the instrument, but not the planets.

        :return: A deep copy of the star.
        """

        new_star = Star(self.spectral_type, self.temperature,
                    length_to_target(self.radius, 'm', 'sun'), self.instrument.__copy__())
        return new_star

    def set_planets(self):
        """
        Creates a set of planets around the star.
        There is one planet at the inner and one at the outer edge of the habitable zone.

        :return: List of planets. (inner, outer)
        """
        from lifesim.parametric_models.stellar_contrast.objects.planet import Planet

        self.planets = [Planet(1, self.h_inner, self.instrument, self),
                Planet(1, self.h_outer, self.instrument, self)]
