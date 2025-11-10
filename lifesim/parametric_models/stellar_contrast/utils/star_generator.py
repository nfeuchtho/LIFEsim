from typing import Union

import pandas
import pandas as pd
from pandas import DataFrame

from lifesim.parametric_models.stellar_contrast.objects.instrument import Instrument
from lifesim.parametric_models.stellar_contrast.utils import file_reader
from lifesim.parametric_models.stellar_contrast.objects.star import Star

# Remove annoying pandas warning with no founding.
pandas.options.mode.chained_assignment = None

class StarGenerator:
    """
    Generates a population of stars based on a catalogue.

        Attributes:
        catalogue_path: DataFrame containing the catalogue.
    """
    catalogue: DataFrame

    def __init__(self,
                 catalogue_path: str):
        """
        Creates a new star generator.

        :param catalogue_path: The path to the star catalogue.
        """

        self.catalogue = file_reader.read_star_catalogue(catalogue_path)


    def generate_population(self,
                            size: int,
                            instrument: Instrument,
                            spec_types: Union[tuple, None] = ('F', 'G', 'K', 'M'),
                            interpolation_parameter: str = 'mod_Teff',
                            silent : bool = False):
        """
        Generates a homogeneous population of stars.
        If there are not enough distinct stars in the catalogue to create a homogeneous population,
        the remaining stars are interpolated at minimum differences based on the given parameter.

        :param size: Total size of population.
        :param instrument: The instrument used to map the population.
        :param spec_types: Tuple of spectral types to filter by in the final population. The elements are strings,
                            which are the leading substring of the spectral types (e.g., ('G2', 'F0', 'K')).
                            If None, no subdivision is performed and the entire catalogue is sampled.
        :param interpolation_parameter: The interpolation parameter to run. Standard is temperature, radius also works.
        :param silent: If true, no output is printed onto the console.
        :return: List of star objects, homogeneously distributed across the stellar types, most massive stars first.
        """

        total_stars = len(self.catalogue)

        if spec_types is not None:
            cats = [self.catalogue[self.catalogue['sim_sptype'].str.startswith(spectral_type)]
                    for spectral_type in spec_types]
        else:
            spec_types = ['ALL']
            cats = [self.catalogue]

        num_cats = len(spec_types)

        smallest = min(len(df) for df in cats)

        # Compute the number of stars per bin.
        clean_cut = size // num_cats
        remainder = size % num_cats

        # A bit of math with the remainder:
        # Let (i + 1) be the mathematical position of a bin (i.e., the ith bin) and r the remainder,
        # then we add an extra star to the requirements of that bin if and only if (i + 1) <= remainder.
        stars_per_category = [clean_cut + (1 if (i + 1) <= remainder else 0) for i in range(num_cats)]

        if smallest * num_cats < size:
            if not silent:
                print('[!] Warning: The stellar catalogue does not contain enough distinct stars to generate '
                      'a homogeneous population of stars. '
                      'Consider reducing the size or restricting the spectral types.')
                print(f'\n[!] The distribution of stars by the given filter is as follows:')
                for (i, df) in enumerate(cats):
                    print(f'[!] Type "{spec_types[i]}": {len(df)} stars ({stars_per_category[i]} required)')
                print(f'\n[!] Interpolating the remaining {size - smallest * num_cats} stars.')

            # Interpolate the remaining stars.
            # Iterate over each bin.
            for i in range(num_cats):

                available_stars = len(cats[i])
                required_stars = stars_per_category[i]

                if available_stars < required_stars:
                    # We need to interpolate.
                    # This is done by repeatedly increasing the finesse of the dataframe by
                    # temperature.

                    # We cannot interpolate from a single star!
                    if available_stars <= 1:
                        raise ValueError(
                            f'The catalogue does not contain more than one star of the type "{spec_types[i]}".'
                            f' Interpolation is impossible.')

                    # First, sort the dataframe by parameter.
                    cats[i].sort_values(interpolation_parameter, inplace=True)

                    # Next, run over all lines repeatedly until the difference is equalized.
                    diff = required_stars - available_stars
                    line_index = 0
                    while diff > 0:
                        # We start off at line 0.
                        # Then, a star is inserted at line 1 (interpolated lines 0 and 1).
                        # We then proceed to line 2, insert at 3 etc.
                        # Therefore, the line index li = (2 * iteration)
                        # However, if the line index reaches the final value, we have to skip back to line zero.
                        # Each turn the size of the dataframe increases by one, so we take care of that.

                        star_upper = cats[i].iloc[line_index].to_dict()
                        star_lower = cats[i].iloc[line_index + 1].to_dict()

                        def interpolation(val1, val2):
                            # Defines the interpolation algorithm. Linear for now.
                            return (val1 + val2) / 2

                        # We do not know the spectral type, so we mark that accordingly.
                        new_spec_type = 'Interpolated'
                        new_temp = interpolation(star_upper['mod_Teff'], star_lower['mod_Teff'])
                        new_radius = interpolation(star_upper['mod_R'], star_lower['mod_R'])

                        # In any case, we advance one line.
                        line_index += 1

                        # We do not wish to include more same-temperature stars, these falsify the result.
                        # If a star is inserted, the dataframe size increases by one.
                        # Thus, the line index must increase by two!
                        if new_temp != star_upper['mod_Teff']:
                            # Insert the new star.
                            row = DataFrame({'sim_sptype': new_spec_type,
                                             'mod_Teff': new_temp, 'mod_R': new_radius},
                                            [total_stars + diff])
                            cats[i] = pd.concat([cats[i].iloc[:line_index], row, cats[i].iloc[line_index:]])
                            diff -= 1
                            line_index += 1

                        # Finally, if we are at of or exceed the final index of the dataframe, we go back to square one.
                        if line_index >= len(cats[i]) - 1:
                            line_index = 0

        # We are now ready to run our selection process.
        # At this point, the dataframes are filled with at least the required number of stars.
        stars = []

        for (i, (df, star_count)) in enumerate(zip(cats, stars_per_category)):
            selection = df.sample(star_count)

            # Add stars to the final list.
            stars += [Star(row['sim_sptype'], row['mod_Teff'], row['mod_R'], instrument)
                for (_, row) in selection.iterrows()]

            # Remove the selected stars from the dataframe.
            df.drop(selection.index, inplace=True)

        # Sort the list of stars.
        stars.sort(key=lambda star: star.temperature, reverse=True)

        return stars
