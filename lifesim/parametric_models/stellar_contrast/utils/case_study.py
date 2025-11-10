import multiprocessing
from itertools import repeat
from multiprocessing import Pool
from typing import Union

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
from scipy import optimize
from scipy.interpolate import make_interp_spline
from tqdm import tqdm

from lifesim.parametric_models.stellar_contrast.objects.star import Star


class CaseStudy:
    """
    A case study to implement parallel computing in varying parameters.

    Attributes:
        stars: The star list of the case study. Not to be modified.
    """
    stars: list[Star]

    def __init__(self,
                 stars : list[Star]):
        """
        Creates a new case study for the given generator of stars.

        :param stars: The star list of the case study. Not to be modified.
        """

        self.stars = stars

    def contrast_ratio_worker(self,
                                args: tuple[float, float, int, str]):
        """
        Parallelized operation for the contrast ratio computation.

        :param args: A tuple containing in order the baseline, distance, the resolution and the mode.
        :return: The resulting 3D contrast ratio array over all stars and planets.
                The primary index stands for the baselines, the second for the star and the third for the planet.
        """

        baseline, dist, resolution, mode = args

        if mode == 'astrophysical':
            ratios = np.empty((resolution, (len(self.stars[0].planets))))
        else:
            ratios = np.empty((resolution, 1))

        for (i, star) in enumerate(self.stars):
            new_star = star.__copy__()
            new_star.instrument.switch_baseline(baseline)
            new_star.set_planets()
            if mode == 'astrophysical':
                for (j, planet) in enumerate(new_star.planets):
                    ratios[i][j] = planet.astrophysical_contrast_ratio(dist)
            elif mode == 'stellar':
                ratios[i][0] = new_star.transmittivity(dist, resolution=0)[0]

        return ratios

    def contrast_ratio(self,
                        distance_range: tuple[float, float],
                        baseline_range: tuple[float, float],
                        mode: str,
                        spectral_types: Union[tuple, None] = ('F', 'G', 'K', 'M')):
        """
        Conducts a contrast ratio analysis (stellar or astrophysical) and plots the results.

        :param distance_range: The range of distances to be used in the study.
        :param baseline_range: The range of baselines to be used in the study.
        :param mode: The mode of the contrast ratio analysis, either 'stellar' or 'astrophysical'.
        :param spectral_types: The spectral types to be used in the contrast ratio analysis.
                                If empty, the interpolation is strictly according to temperature.
        """

        resolution = len(self.stars)

        if mode != 'stellar' and mode != 'astrophysical':
            raise ValueError('Mode must be either "stellar" or "astrophysical".')

        if spectral_types is None:
            spectral_types = ('F', 'G', 'K', 'M', '')
        else:
            spectral_types += '',

        baselines = np.linspace(*baseline_range, resolution)

        def make_smooth(x, y):
            # Interpolates y(x) based on Spline interpolation.
            x_new = np.linspace(x.min(), x.max(), 300)

            spl = make_interp_spline(x, y)
            smoothed_y = spl(x_new)

            return x_new, smoothed_y

        # We iterate over the distances and conduct the study independently.
        for dist in np.linspace(*distance_range, 5):
            # Vary the baseline.
            with Pool(multiprocessing.cpu_count()) as pool:
                result = np.array(list(tqdm(pool.imap(self.contrast_ratio_worker,
                                                      zip(baselines, repeat(dist), repeat(resolution), repeat(mode))),
                                desc=f'Computing Ratio for d = {dist} pc', total=len(baselines))))

            for index in range(len(result[0][0])):
                # Plot the resulting contrast ratio image based on mode.
                im = result[:, :, index]

                fig, ax = plt.subplots(1, 1)

                im = ax.imshow(im[::-1], norm=LogNorm(),
                               extent=np.array([*baseline_range, *baseline_range]))

                x = np.linspace(*baseline_range, resolution)
                if mode == 'astrophysical':

                    planets = [star.planets[index] for star in self.stars]

                    _, partly_resolved = make_smooth(x, [planet.min_resolved_baselines(dist)[0]
                                                         for planet in planets])
                    x, not_resolved = make_smooth(x, [planet.min_resolved_baselines(dist)[1]
                                                      for planet in planets])
                    ax.plot(x, partly_resolved, color='black', linewidth=0.2)

                    ax.fill_between(x, y1=baseline_range[1], y2=partly_resolved, alpha=0.0, label='fully resolved')

                    ax.fill_between(x, partly_resolved, y2=not_resolved, edgecolor='black', alpha=1, facecolor='none',
                                    hatch='..', linewidth=0.0, label='partly resolved')

                    ax.plot(x, not_resolved, color='black', linewidth=0.2)

                    ax.fill_between(x, not_resolved, y2=baseline_range[0], edgecolor='black', alpha=1, facecolor='none',
                                    hatch='xx', linewidth=0.0, label='not resolved')

                    ax.legend()

                ax.set_xlim(*baseline_range)
                ax.set_ylim(*baseline_range)

                ax.set_xticks(np.linspace(*baseline_range, len(spectral_types)))
                ax.set_xticklabels(spectral_types)

                cbar = fig.colorbar(im, orientation='vertical')
                ax.set_title(f'{mode.capitalize()} Contrast Ratio ($d={dist}pc$)')
                ax.set_xlabel('Spectral Type')
                ax.set_ylabel('Baseline Length $[m]$')
                cbar.set_label(f'{mode.capitalize()} Contrast Ratio')

                fig.savefig(f'results/plots/{mode.capitalize()}'
                            f'_Contrast_Ratio_vs_Spectral_Type_Baseline'
                            f'_{dist}pc_'
                            f'Pl{index}.png')
                plt.show()
