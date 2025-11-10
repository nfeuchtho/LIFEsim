from math import acosh

import pandas
import yaml

def read_config(config_path):
    """
    Reads a config file.

    :param config_path: Relative path to the config file.
    :return: Config dictionary.
    """

    with open(config_path) as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

def read_star_catalogue(path: str):
    """
    Takes a star catalogue and returns a dataframe of stars with the referenced values.

    :param path: Path to the star catalogue.
    :return: pandas.DataFrame with the relevant parameters (spectral type, temperature, radius).
    """

    # Only take relevant parameters.
    df = pandas.read_csv(path, usecols=['sim_sptype', 'mod_Teff', 'mod_R'], comment='#')

    # Filter out non-sun-like stars.
    df = df[df['sim_sptype'].str[0].isin(['F', 'G', 'K', 'M'])]

    # Delete duplicates (same temperature, same radius), no use for those.
    df = df.drop_duplicates(subset=['mod_Teff', 'mod_R'])

    return df
