import astroconst as const
import scipy.constants as constants

def length_to_target(distance: float,
                     unit: str,
                     target: str = 'm'):
    """
    Transforms the distance from the given unit to another unit.

    :param distance: The distance in either AU, pc, sun [radii], earth [radii], or m[eters].
    :param unit: The unit the distance is in.
    :param target: The target unit. Standard is m
    :return: The distance in meters
    """

    transformations = {'m': 1, 'au': const.au, 'pc': constants.parsec, 'sun': const.r_sun, 'earth': const.r_earth}

    if unit not in transformations:
        raise ValueError(f'Unknown unit ({unit}).')

    # Find the length in meters first.
    to_meters = distance * transformations[unit]

    if target not in transformations:
        raise ValueError(f'Unknown target unit ({target}).')

    # Finally, transform to the target unit and return.
    return to_meters / transformations[target]