import os

# LIFESim changes the working directory, so we must switch back to the original folder.
working_directory = os.getcwd()
from lifesim.util.habitable import single_habitable_zone
os.chdir(working_directory)

def get_ehz(temperature: float,
            radius: float):
    """
    Computes the boundaries of the habitable zone for a star of a given temperature and radius.

    :param temperature: The temperature of the star in Kelvin.
    :param radius: The radius of the star in solar radii.
    :return: The inner and outer edges of the habitable zone in AU.
    """
    _, _, _, inner_edge, outer_edge, _ = single_habitable_zone('MS', temperature, radius)
    return inner_edge, outer_edge

