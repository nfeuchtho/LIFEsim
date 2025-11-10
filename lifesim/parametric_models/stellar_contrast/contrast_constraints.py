import os
working_dir = os.getcwd()

import tqdm
from matplotlib.colors import LogNorm
from scipy import optimize

from objects import instrument
import utils.file_reader
from objects.planet import Planet
from objects.star import Star

import matplotlib.pyplot as plt
import numpy as np

from utils.case_study import CaseStudy
from utils.parametric_model import ParametricModel
from utils.star_generator import StarGenerator
from utils.unit_transformer import length_to_target

os.chdir(working_dir)

params = utils.file_reader.read_config('config/mission_params.yml')

# LIFE transmission map
life_instrument = instrument.Instrument(params['min_wavelength'] * 1e-6,
                                        params['max_wavelength'] * 1e-6,
                                        params['min_baseline'],
                                        params['max_baseline'],
                                        params['baseline'],
                                        params['baseline_ratio'])

# Instantiate the two catalogues
life_generator = StarGenerator('catalogues/LTC_3.csv')
toy_generator = StarGenerator('catalogues/star_examples.csv')

def part_one():
    """
    I.
    Plotting the stellar blackbody spectra.
    Takes a toy catalogue of stars and plots their spectra over the observed wavelength range.
    """

    stars = toy_generator.generate_population(10, life_instrument)

    wavelengths = np.linspace(life_instrument.min_wavelength,
                              life_instrument.max_wavelength, 1000)
    for star in stars:
        plt.plot(wavelengths/1e-6, star.intensity(wavelengths), label=f'${star.spectral_type}$')

    plt.title("Stellar Blackbody Spectra")

    plt.xlabel("Wavelength [$\mu m$]")
    plt.ylabel("Stellar Flux [$ph\ s^{-1}\ m^{-3}\ sr^{-1}$]")

    plt.legend()

    plt.savefig("results/plots/Stellar_Blackbody_Spectra.png")

    plt.show()

def part_two():
    """
    II.
    Introduction of the nulling interferometer.
    Computing the stellar and astrophysical contrast ratios for Earth and the Sun.
    """
    dist = 10

    sun = Star('G2', 5780, 1., life_instrument)
    sun.set_planets()

    earth = sun.planets[0]

    print(f'[ ] The integrated Earth-to-Sun astrophysical contrast ratio at {dist} parsec is equal to '
          f'{"%.2e" % earth.astrophysical_contrast_ratio(dist, True)}.')

    transmittivity, heatmap = sun.transmittivity(dist)

    print(f'[ ] The stellar contrast ratio is equal to {"%.2e" % transmittivity}.')

    alpha_max = np.arctan(sun.radius / length_to_target(dist, 'pc')) * 180 * 3600 / np.pi * 1e3

    plt.imshow(heatmap, extent=np.array([-1.2, 1.2, -1.2, 1.2])*alpha_max, cmap='hot')

    cbar = plt.colorbar(orientation='vertical')

    plt.title(f'Transmittivity Heatmap of the Sun (${dist}\ pc$)')
    plt.xlabel('$\Delta RA\ [mas]$')
    plt.ylabel('$\Delta Dec\ [mas]$')

    cbar.set_label('Integrated Transmittivity')

    plt.savefig(f'results/plots/Sun_Transmittivity_Heatmap_{dist}pc.png')

    plt.show()

def part_three():
    """
    III.
    Conducting case studies with the entire star catalogue to determine first plots of stellar contrast.
    Distance is varied.
    Baseline b is still fixed.
    """

    stars = life_generator.generate_population(50, life_instrument, spec_types=None)

    fig, ax = plt.subplots(1, 1)
    for dist in np.linspace(1, 30, 10):
        ax.plot(range(len(stars)), np.array([star.transmittivity(dist, resolution=0)[0] for star in stars]),
                 label=f'$d={round(dist, 2)}pc$')

    ax.set_xticks(np.linspace(0, len(stars), 5))
    ax.set_xticklabels(['F', 'G', 'K', 'M', ''])
    ax.set_yscale('log')
    ax.set_xlabel("Stellar Type")
    ax.set_ylabel("Stellar Contrast Ratio")
    ax.set_title('Stellar Contrast Ratio vs Stellar Type')

    ax.legend()

    fig.savefig('results/plots/Stellar_Contrast_Ratio_vs_Stellar_Type.png')
    fig.show()

def part_four():
    """
    IV.
    Conducting case studies with the entire star catalogue to achieve first results as an imshow plot.
    Distance is varied over five iterations from 2 pc to 30 pc, each one plot.
    In each plot, both the baseline and spectral type are varied.
    """

    stars = life_generator.generate_population(20, life_instrument, spec_types=None)

    for star in stars:
        star.set_planets()

    case_study = CaseStudy(stars)

    case_study.contrast_ratio((2, 30), (1, 200),'stellar', None)

def part_five():
    """
    V.
    Conducting case studies with the entire star catalogue to compute astrophysical contrast ratios.
    Each system is assumed to have one Earth-twin planet in the middle of the eHZ, otherwise the same as IV.
    Considering for the first time the resolution capabilities of the instrument to determine no-go zones.
    """

    stars = life_generator.generate_population(100, life_instrument, spec_types=None)

    for star in stars:
        star.set_planets()

    case_study = CaseStudy(stars)

    case_study.contrast_ratio((2, 30), (1, 200), 'astrophysical', None)


def part_six():
    """
    VI.
    Estimating a parameter model for the four-dimensional stellar extinction curve using reduced 3D-results.
    """

    bins = 5

    # Small population for testing & plotting
    # Individualize instruments
    stars = life_generator.generate_population(bins, life_instrument, spec_types=None)[::-1]

    wl = np.linspace(life_instrument.min_wavelength, life_instrument.max_wavelength, bins + 1)
    wl_bins = np.array([(wl[i + 1] + wl[i]) / 2 for i in range(bins)])
    wl_widths = np.ones(bins) * (life_instrument.max_wavelength - life_instrument.min_wavelength) / bins

    dist_cuts = np.linspace(5, 30, bins)
    temp_cuts =  np.array([star.temperature for star in stars])

    temps, wls = np.meshgrid(temp_cuts, wl_bins, indexing='ij')

    fig = plt.figure()
    ax = fig.add_subplot()


    data = np.empty((bins, bins))
    for i, star in enumerate(stars):
        star.set_planets()
        star.instrument.switch_baseline(star.planets[0].min_resolved_baselines(10)[0])
        data[i] = star.transmittivity(5, wl_bins=(wl_bins, wl_widths))[0]
    data = data[:, 20]

    def model(x, a, b, c, d, e):
        values = np.empty_like(x)
        for i, xi in enumerate(x):
            if xi < a:
                values[i] = b * np.exp(c*xi)
            else:
                values[i] = d * np.exp(-e*xi)
        return values

    sol, _ = optimize.curve_fit(model, temp_cuts, data,
                                p0=[5500, 1e-10, 0.0001, 10, 0.0001],
                                maxfev=1_000_000)

    print(sol)

    ax.scatter(temp_cuts, data)
    #ax.plot(temp_cuts,  np.log10(model(temp_cuts, *sol)))

    #ax.scatter(temps.flatten(), wls.flatten(), data.flatten(), alpha=0.8)

    plt.show()

def part_seven():
    """
    VII.
    Utilizing a parameter model to perform conclusive parameter research, getting a parametrized initial condition.
    Running multiple models to predict their ability to interpolate points to anywhere within the mission range.
    Successful accomplishment of this stage constitutes the first step of DATA VALIDATION.
    """

    bins = 40

    def reduce_dataset(stars, dist_cuts, wl_bins, wl_widths, factor):
        return stars[::factor], dist_cuts[::factor], wl_bins[::factor], wl_widths[::factor]

    # Small population for testing and plotting
    # Individualize instruments
    stars = life_generator.generate_population(bins, life_instrument, spec_types=None)[::-1]

    wl = np.linspace(life_instrument.min_wavelength, life_instrument.max_wavelength, bins + 1)
    wl_bins = np.array([(wl[i + 1] + wl[i]) / 2 for i in range(bins)])
    wl_widths = np.ones(bins) * (life_instrument.max_wavelength - life_instrument.min_wavelength) / bins

    dist_cuts = np.linspace(3, 30, bins)

    # Compare the following three models.
    print('\n ---   M O D E L   V A L I D A T I O N   ---\n')

    # The first one takes the full dataset. We also define the "truth", the highest resolution simulated contrasts.
    model_full = ParametricModel()
    truth_values = model_full.setup(stars, dist_cuts, wl_bins, wl_widths)

    # The next model takes half the dataset.
    half_dataset = reduce_dataset(stars, dist_cuts, wl_bins, wl_widths, 2)
    model_half = ParametricModel()
    model_half.setup(*half_dataset)

    # The final one only takes a quarter.
    quarter_dataset = reduce_dataset(*half_dataset, 2)
    model_quarter = ParametricModel()
    model_quarter.setup(*quarter_dataset)

    # Compare first the final parameters.
    print('\nI. Parameter Deviations.')
    print(f'Difference Array for the HALF model: '
          f'{np.abs(model_half.parameter_space - model_full.parameter_space)}')
    print(f'Difference Array for the QUARTER model: '
          f'{np.abs(model_quarter.parameter_space - model_full.parameter_space)}')

    print('\nII. Model Interpolation Performance.')
    def compute_residuals(model):
        residuals = np.array([[[np.log10(model.evaluate_at(star.temperature, dist, wl) / truth_values[s][d][w])
                                for (w, wl) in enumerate(wl_bins)]
                               for (d, dist) in enumerate(dist_cuts)]
                              for (s, star) in enumerate(stars)])
        return residuals.flatten()
    resid_full = compute_residuals(model_full)
    resid_half = compute_residuals(model_half)
    resid_quarter = compute_residuals(model_quarter)

    for s, res in (('FULL', resid_full), ('HALF', resid_half), ('QUARTER', resid_quarter)):
        exceedances = np.sum(np.where(np.abs(res) > 1, 1, 0))
        print(f'{s} model (MAX, MIN, AVG, EXC) (OoM): '
              f'({round(np.max(res), 2)}, {round(np.min(res), 2)}, {round(np.mean(res), 2)}, '
              f'{round(exceedances / len(res) * 100, 2)}%)')

    print('\nIII. Case Example: the sun at 10 parsec, integrated over wavelength.')
    sun = Star('G2',  5780, 1., life_instrument)
    earth = Planet(1, 1, life_instrument, sun)
    life_instrument.switch_baseline(earth.min_resolved_baselines(10)[0])

    def sum_up(contrast):
        return sum([c * w for c, w in zip(contrast, wl_widths)])

    full_contrast = sum_up(sun.transmittivity(10, wl_bins=(wl_bins, wl_widths))[0])
    print(f'Truth Contrast: {full_contrast}')
    for s, model in (('FULL', model_full), ('HALF', model_half), ('QUARTER', model_quarter)):
        prediction = [model.evaluate_at(sun.temperature, 10, w) for w in wl_bins]
        print(f'{s} model: {sum_up(prediction)}')


if __name__ == '__main__':
    import matplotlib as mpl
    mpl.use('Qt5Agg')

    #part_one()
    #part_two()
    #part_three()
    #part_four()
    #part_five()
    #part_six()
    part_seven()
