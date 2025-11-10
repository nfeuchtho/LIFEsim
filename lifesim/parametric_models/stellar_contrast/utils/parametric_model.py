import multiprocessing
import lifesim
from itertools import repeat
from multiprocessing import Pool

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
from scipy import optimize
from tqdm import tqdm

from lifesim.parametric_models.stellar_contrast.objects.star import Star

class ParametricModel:
    """
    A parametric model to perdict stellar contrasts.

    Attributes:
        parameter_space: The parameter space of the model.
        id: The ID of the model.
        ID: The global ID counter.
    """


    ID = 0

    def __init__(self,
                 parameter_space: np.ndarray = None):
        """
        Creates a new parametric model.
        If a parameter space is provided, it will be used to initialize the model.

        :param parameter_space: Defaults to None, a numpy array of the model parameters.
        """
        self.parameter_space = parameter_space
        self.id = ParametricModel.ID
        ParametricModel.ID += 1

    def contrast_for_star(self, args):
        """
        Parallelized operation for the contrast ratio computation.

        :param args: A tuple containing in order the star, distance cuts, wavelength containers and wavelength widths.
        :return: The resulting 2D contrast array.
                The primary index stands for the distances, and the second for the wavelength.
        """
        star, dist_cuts, wl_containers, wl_widths = args

        dist_count = len(dist_cuts)
        wl_count = len(wl_containers)

        star.set_planets()
        planet = star.planets[0]

        contrasts = np.empty((dist_count, wl_count))
        for (dist_index, dist) in enumerate(dist_cuts):
            optimistic_baseline = planet.min_resolved_baselines(dist)[0]

            # Set the baseline
            star.instrument.switch_baseline(optimistic_baseline)

            contrasts[dist_index] = star.transmittivity(dist, wl_bins=(wl_containers, wl_widths))[0]

        return contrasts

    def setup(self,
                 stars: list[Star],
                 dist_cuts: np.ndarray,
                 wl_containers: np.ndarray,
                 wl_widths: np.ndarray,
                 debug: bool = False):
        """
        Trains the parametric model which is fitted based on an ascending-sorted (!) dataset.

        :param stars: Cut of stars to use.
        :param dist_cuts: Array of distance cuts to use. Denotes the centerpoints.
        :param wl_containers: Array of wavelength containers to use. Denotes the centerpoints.
        :param wl_widths: Array of wavelength widths to use.
        :param debug: If yes, will plot the model and its deviations.

        :return: The referenced simulated contrasts for comparison as a 3D numpy array.
        """

        temp_cuts = np.array([star.temperature for star in stars])

        temp_count = len(temp_cuts)
        dist_count = len(dist_cuts)
        wl_count = len(wl_containers)

        # Create the meshgrid for evaluation.
        temps, dists, wls = np.meshgrid(temp_cuts, dist_cuts, wl_containers, indexing='ij')

        # Now, compute the actual physical contrasts, parallelize for maximum speed.
        with Pool(multiprocessing.cpu_count()) as pool:
            contrasts = np.array(list(tqdm(pool.imap(self.contrast_for_star,
                                                     zip([star.__copy__() for star in stars], repeat(dist_cuts),
                                                         repeat(wl_containers), repeat(wl_widths))),
                                           desc=f'Building model (ID {self.id}) (computing contrasts)...',
                                           total=len(stars))))

        # We now start building the model.
        sol_temp, _ = optimize.curve_fit(self.__temp_model, temp_cuts,
                                         contrasts[:, dist_count // 2, wl_count // 2].flatten(),
                                         p0=[1e3, 5000, 1000], maxfev=1_000_000)

        sol_dist, _ = optimize.curve_fit(self.__dist_model, dist_cuts,
                                         contrasts[temp_count - 1, :, 0].flatten(),
                                         p0=[12.05, 6.83, 0.317], maxfev=10_000_000)

        sol_wl, _ = optimize.curve_fit(self.__wl_model, wl_containers,
                                       contrasts[temp_count // 2, dist_count // 2, :].flatten(),
                                       p0=[1e-5, 2.8 * 1e5], maxfev=100_000)

        if debug:
            fig, ax = plt.subplots(1, 1)

            # Visualize fits for various data types
            # Wavelength
            for temp_sel in (0, temp_count // 2, -1):
                for dist_sel in (0, dist_count // 2, -1):
                    ax.scatter(wl_containers * 1e6, contrasts[temp_sel, dist_sel, :].flatten(),
                               label=f'd={dist_cuts[dist_sel]:.0f}pc, T={temp_cuts[temp_sel]:.0f}K')

            ax.plot(wl_containers * 1e6, self.__wl_model(wl_containers, *sol_wl), label='Model', linestyle='-')

            ax.set_yscale('log')
            ax.set_xlabel('Wavelength [$\mu m$]')
            ax.set_ylabel('Stellar Contrast Ratio')
            ax.legend()

            plt.title('Stellar Contrast Ratio vs Wavelength in 3D dependence')

            plt.savefig(f'results/parametric_model/Contrast_WL_ID{self.id}.png')

            plt.show()

            fig, ax = plt.subplots(1, 1)
            # Distance
            for temp_sel in (0, temp_count // 2, -1):
                for wl_sel in (0, wl_count // 2, -1):
                    ax.scatter(dist_cuts, contrasts[temp_sel, :, wl_sel].flatten(),
                               label=f'w={wl_containers[wl_sel] * 1e6:.0f}um, T={temp_cuts[temp_sel]:.0f}K')

            ax.plot(dist_cuts, self.__dist_model(dist_cuts, *sol_dist), label='Model', linestyle='-')

            ax.set_yscale('log')
            ax.set_xlabel('Distance [$pc$]')
            ax.set_ylabel('Stellar Contrast Ratio')
            ax.legend()

            plt.title('Stellar Contrast Ratio vs Distance in 3D dependence')

            plt.savefig(f'results/parametric_model/Contrast_Dist_ID{self.id}.png')

            plt.show()

            fig, ax = plt.subplots(1, 1)
            # Temperature
            for dist_sel in (0, dist_count // 2, -1):
                for wl_sel in (0, wl_count // 2, -1):
                    ax.scatter(temp_cuts, contrasts[:, dist_sel, wl_sel].flatten(),
                               label=f'w={wl_containers[wl_sel] * 1e6:.0f}um, d={dist_cuts[dist_sel]:.0f}pc')

            ax.plot(temp_cuts, self.__temp_model(temp_cuts, *sol_temp), label='Model')

            ax.set_yscale('log')
            ax.set_xlabel('Temperature [$K$]')
            ax.set_ylabel('Stellar Contrast Ratio')
            ax.legend()

            plt.title('Stellar Contrast Ratio vs Temperature in 3D dependence')

            plt.savefig(f'results/parametric_model/Contrast_Temp_ID{self.id}.png')

            plt.show()

        # Time to put it all together. Excluding the multiplicative constant (last element),
        # we can now run the full fit.
        self.parameter_space = np.concatenate((sol_temp[1:], sol_dist[1:], sol_wl[1:], np.array([-1])))

        reference = contrasts
        contrasts = contrasts.flatten()
        temps = temps.flatten()
        dists = dists.flatten()
        wls = wls.flatten()

        sol, _ = optimize.curve_fit(self.__full_model, (temps, dists, wls), contrasts,
                                    p0=sol_wl[0] * np.exp(-sol_dist[0]) * sol_temp[0],  # First guess for A
                                     maxfev=100_000)

        # The model is now complete.
        self.parameter_space[-1] = sol

        if debug:

            print(f'\nFinal parameters: {self.parameter_space}\n')

            fig = plt.figure()
            ax = fig.add_subplot(projection='3d')

            final_residual = self.__full_model((temps, dists, wls), sol)

            errors = np.log10(np.divide(final_residual, contrasts))

            print('Model Performance: ')
            print(f'Overshoot: {round(np.max(errors), 2)} orders of magnitude off')
            print(f'Undershoot: {round(np.min(errors), 2)} orders of magnitude off')
            print(f'Average Error: {round(np.mean(errors), 2)} orders of magnitude off')

            exceedances = np.sum(np.where(np.abs(errors) > 1, 1, 0))
            print(f'Exceedance Rate (|OoM| > 1): {round(exceedances / len(errors) * 100, 2)}%')

            im = ax.scatter(temps, dists, wls * 1e6,
                            c=contrasts, norm=LogNorm(), alpha=0.8, cmap='hot')

            cb = fig.colorbar(im)

            cb.set_label('Stellar Contrast')

            ax.set_xlabel('Effective Stellar Temperature [K]')
            ax.set_ylabel('Distance [pc]')
            ax.set_zlabel('Wavelength [$\mu m$]')

            fig.savefig(f'results/plots/Stellar_Contrast_Ratio_WL_Temp_Dist_ID{self.id}.png')

            plt.show()

        return reference

    def evaluate_at(self, t, d, w):
        """
        Evaluates the parametric model at a given temperature, distance and wavelength.

        :param t: The temperature to evaluate at in Kelvin.
        :param d: The distance to evaluate at in parsec.
        :param w: The wavelength to evaluate at in meters.
        :return: The predicted contrast ratio.
        """

        if self.parameter_space is None:
            raise TypeError('Trying to evaluate a parametric model without parameters. Call setup first.')
        response = self.__full_model(([t], [d], [w]), self.parameter_space[-1])[0]
        return response

    def __temp_model(self, x, a, b, c):
        # Model function for contrast in terms of temperature.
        return a * np.exp(-((x - b) / c) ** 2)

    def __dist_model(self, x, a, b, c):
        # Model function for contrast in terms of distance.
        return np.exp(b * np.exp(-c * x) - a)

    def __wl_model(self, x, a, b):
        # Model function for contrast in terms of wavelength.
        return a * np.exp(-b * x)

    def __full_model(self, x, a):
        # Full model function.
        probe_count = len(x[0])
        values = np.empty(probe_count)
        for (pos, (t, di, w)) in enumerate(zip(*x)):
            temp_contrib = self.__temp_model(t, 1, *self.parameter_space[:2])
            dist_contrib = self.__dist_model(di, 0, *self.parameter_space[2:4])
            wl_contrib = self.__wl_model(w, 1, *self.parameter_space[4:-1])
            values[pos] = a * temp_contrib * dist_contrib * wl_contrib
        return values
