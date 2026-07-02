from copy import deepcopy

import numpy as np
import pandas as pd
from joblib import parallel_config, Parallel, delayed
from joblib_progress import joblib_progress
from matplotlib import pyplot as plt
from scipy.integrate import quad, quad_vec
from tqdm import tqdm
from scipy.interpolate import make_interp_spline, BSpline

from lifesim.ams.core.error_budget import ErrorBudget
from lifesim.util import constants
from lifesim.util.radiation import black_body


class AgnosticMissionSimulator:
    """
    Agnostic Mission Simulator (AMS).

    The AMS estimates the total time required to complete the LIFE search and
    characterization phases for a given instrument design, observing strategy and set of
    instrumental error budgets. It is "agnostic" in the sense that it does not depend on a
    specific hardware implementation; instrumental imperfections are instead expressed as
    additive and/or multiplicative :class:`~lifesim.ams.core.error_budget.ErrorBudget`
    contributions to the relevant photon noise terms.

    A typical workflow is

    1. Build a :class:`~lifesim.core.core.Bus` with an
       :class:`~lifesim.instrument.instrument.Instrument` and an
       :class:`~lifesim.optimize.optimizer.Optimizer` (with an AHGS module) connected, and
       load a target catalog.
    2. Create one or more :class:`~lifesim.ams.core.error_budget.ErrorBudget` instances
       describing the instrumental noise contributions to be investigated and pass them to
       the constructor.
    3. Call :meth:`run` with the instrument and optimizer. This computes the SNR of every
       target (:meth:`get_snr`), applies the magnitude/field-of-regard filters, runs the
       AHGS time-allocation optimizer and returns the required mission duration.

    Parameters
    ----------
    nulling_order : int
        Order of the nulling interferometer (exponent applied to the chopped transmission
        signal, e.g. ``2`` for a standard double Bracewell array).
    lim_mag : float
        Limiting K-band apparent magnitude. Stars fainter than this are excluded from the
        SNR computation (their SNR is set to zero).
    field_of_regard : float
        Half-opening angle of the field of regard around the ecliptic poles, in radians.
        Stars at an ecliptic latitude with ``abs(lat) > field_of_regard`` are excluded.
    science_overhead : float
        Fractional efficiency of the search phase (``t_efficiency``), i.e. the fraction of
        the total search time that is actually spent integrating on targets (the remainder
        is overhead).
    slew_time : float
        Time in seconds required to slew/repoint the array between observations
        (``t_slew``).
    leakage_budget : ErrorBudget, optional
        Error budget applied to the stellar leakage noise. Defaults to a budget with no
        effect (multiplicative factor 1, additive factor 0).
    localzodi_budget : ErrorBudget, optional
        Error budget applied to the local zodiacal light noise. Defaults as above.
    exozodi_budget : ErrorBudget, optional
        Error budget applied to the exozodiacal dust noise. Defaults as above.
    planet_signal_budget : ErrorBudget, optional
        Error budget applied to the planet signal flux. Defaults as above.
    planet_noise_budget : ErrorBudget, optional
        Error budget applied to the photon noise contributed by the planet itself. Defaults
        as above.
    plot_id : int, optional
        If set, :meth:`get_snr` switches into a diagnostic mode: instead of computing the
        SNR for the full catalog, it plots the noise budget breakdown for the star hosting
        the planet at this row index (positional index into the catalog) and exits the
        program. Used to visualize/debug error budgets, not for production runs.
    verbose : bool, default True
        If ``True``, progress information and log messages (see :meth:`log`) are printed.
    """

    def log(self, msg):
        """Prints ``msg`` prefixed with ``'[!]'`` if :attr:`verbose` is ``True``."""
        if self.verbose:
            print('[!]', msg)

    def get_baseline(hz_center, dist_s, wl_opt, min_bl, max_bl):
        """
        Computes the nulling baseline that places the first transmission peak at the center
        of the habitable zone, clipped to the array's allowed baseline range.

        Parameters
        ----------
        hz_center : float
            Angular separation of the habitable-zone center, in arcsec.
        dist_s : float
            Distance to the star, in pc.
        wl_opt : float
            Optimal/reference wavelength used for the baseline computation, in micron.
        min_bl : float
            Minimum allowed baseline length, in m.
        max_bl : float
            Maximum allowed baseline length, in m.

        Returns
        -------
        float
            The baseline length in m, clipped to ``[min_bl, max_bl]``.

        Notes
        -----
        The constant ``0.589645`` places the first transmission peak of a double Bracewell
        array (nulling order 2) onto the habitable-zone center; see Dannert et al. 2022 for
        its derivation.
        """
        hz_center_rad = hz_center / dist_s / (3600 * 180) * np.pi  # in rad

        # put first transmission peak of optimal wl on center of HZ
        # for the origin of the value 0.5.. see Dannert+2022
        bl = (0.589645 / hz_center_rad * wl_opt * 10 ** (-6))

        if bl < min_bl:
            bl = min_bl
        elif bl > max_bl:
            bl = max_bl

        return bl

    def __init__(self,
                 nulling_order,
                 lim_mag,
                 field_of_regard,
                 science_overhead,
                 slew_time,
                 leakage_budget=None,
                 localzodi_budget=None,
                 exozodi_budget=None,
                 planet_signal_budget=None,
                 planet_noise_budget=None,
                 plot_id=None,
                 verbose=True):

        self.__nulling_order = nulling_order

        # Compute savers
        self.snr_saved = None
        self.snr_maxsep_saved = None
        self.snr_array_current = False

        budgets = [ErrorBudget() if budget is None else budget
                   for budget in [leakage_budget, localzodi_budget, exozodi_budget,
                                  planet_signal_budget, planet_noise_budget]]

        for budget in budgets:
            budget.connect(self)

        self.__leakage_budget = budgets[0]
        self.__localzodi_budget = budgets[1]
        self.__exozodi_budget = budgets[2]
        self.__planet_signal_budget = budgets[3]
        self.__planet_noise_budget = budgets[4]

        # Agnostic Parameters
        self.lim_mag = lim_mag
        self.field_of_regard = field_of_regard
        self.science_overhead = science_overhead
        self.slew_time = slew_time
        self.verbose = verbose
        self.plot_id = plot_id

    def set_nulling_order(self, nulling_order):
        """
        Updates the nulling order of the array.

        If the new value differs from the current one, the cached SNR array is invalidated
        (:attr:`snr_array_current` is set to ``False``), forcing the next :meth:`run` to
        recompute the SNR for the full catalog.

        Parameters
        ----------
        nulling_order : int
            The new nulling order.
        """
        if self.__nulling_order != nulling_order:
            self.__nulling_order = nulling_order
            self.snr_array_current = False

    def run(self,
            instrument,
            optimizer,
            pre_select=True):
        """
        Runs a full AMS evaluation and returns the required mission duration.

        This is the main entry point of the AMS. It performs the following steps:

        1. Pushes :attr:`slew_time` and :attr:`science_overhead` into
           ``instrument.data.options`` and applies the instrument options.
        2. Optionally pre-selects the catalog (see ``pre_select``) to the targets that fall
           into at least one of the configured ``optimization['experiments']``.
        3. Computes the one-hour SNR of every (remaining) target via :meth:`get_snr`,
           unless the cached SNR array is still valid (:attr:`snr_array_current`). If
           ``instrument.data.options.other['n_cpu'] > 1`` and not in plot mode, the catalog
           is split into balanced per-star chunks and processed in parallel with
           :mod:`joblib`.
        4. Filters out targets that are too faint (:attr:`lim_mag`, K-band magnitude) or
           outside the :attr:`field_of_regard`.
        5. Calls ``optimizer.ahgs()`` to greedily distribute the available search time
           between targets, marking which planets are detected and at what time.
        6. For each detected, "interesting" target, determines whether it is followed up
           for orbit determination and spectral characterization, and accumulates the
           corresponding observation time. The columns ``follow_up``, ``t_orbit`` and
           ``t_char`` are written back to ``instrument.data.catalog``.
        7. Builds a per-universe time sheet (detection, orbit, characterization and total
           time) and returns the 90th percentile of the total mission time across all
           simulated universes.

        Parameters
        ----------
        instrument : lifesim.instrument.instrument.Instrument
            The instrument module providing the catalog (``instrument.data.catalog``) and
            instrument parameters (``instrument.data.inst``). Used as the ``bus`` for the
            simulation.
        optimizer : lifesim.optimize.optimizer.Optimizer
            The optimizer module (with a connected AHGS slope module) used to distribute the
            available search time between targets via ``optimizer.ahgs()``.
        pre_select : bool, default True
            If ``True``, the SNR is only computed for targets that fall into at least one of
            the configured ``optimization['experiments']`` (the catalog is reduced before
            :meth:`get_snr` and restored to the full catalog afterwards). If ``False``, the
            SNR is computed for the entire catalog, which is considerably slower but allows
            inspecting/optimizing on the full target sample.

        Returns
        -------
        float
            The mission duration, in years, required such that 90% of the simulated
            universes complete their detection, orbit-determination and characterization
            campaigns (i.e. the 90th percentile of the per-universe total time).

        Notes
        -----
        The SNR array is cached (:attr:`snr_saved`, :attr:`snr_maxsep_saved`) and only
        recomputed when :attr:`snr_array_current` is ``False``. This flag is reset whenever
        the nulling order (:meth:`set_nulling_order`) or one of the connected error budgets
        (:meth:`~lifesim.ams.core.error_budget.ErrorBudget.update_factors`) changes, allowing
        repeated calls to :meth:`run` with only the magnitude/field-of-regard cuts or the
        optimization settings changed to skip the expensive SNR calculation.
        """

        # Set global parameters
        instrument.data.options.set_manual(t_slew=self.slew_time,
                                           t_efficiency=self.science_overhead)

        if self.plot_id is not None:
            print('[!] Running in plot mode!')

        def select():
            bus = instrument
            # recalculate the interesting flag
            bus.data.catalog['is_interesting'] = False
            for exp in instrument.data.options.optimization['experiments'].keys():
                mask_exp = ((bus.data.catalog.radius_p
                             >= bus.data.options.optimization['experiments'][exp]['radius_p_min'])
                            & (bus.data.catalog.radius_p
                               <= bus.data.options.optimization['experiments'][exp]['radius_p_max'])
                            & (bus.data.catalog.temp_s
                               >= bus.data.options.optimization['experiments'][exp]['temp_s_min'])
                            & (bus.data.catalog.temp_s
                               <= bus.data.options.optimization['experiments'][exp]['temp_s_max']))

                if bus.data.options.optimization['experiments'][exp]['in_HZ']:
                    mask_exp = (mask_exp
                                & (bus.data.catalog['habitable']))

                bus.data.catalog['exp_' + exp] = mask_exp

                bus.data.catalog['is_interesting'] = np.logical_or(mask_exp, bus.data.catalog['is_interesting'])

            return bus.data.catalog[bus.data.catalog['is_interesting']] if pre_select else bus.data.catalog

        instrument.apply_options()

        if pre_select and not self.snr_array_current:
            self.log('Carrying out pre-selection, this means SNR is only computed for part of the catalog! '
                  'Set \'pre_select\' to False to avoid this.')
            l = instrument.data.catalog.shape[0]
            instrument.data.catalog = select()
            instrument.data.catalog.reset_index(drop=True, inplace=True)
            instrument.data.catalog['id'] = range(len(instrument.data.catalog))
            self.log(f'Pre-selection removed {(1-instrument.data.catalog.shape[0]/l)*100:.2f}% of the targets.')

        cat = instrument.data.catalog

        if 'name_s' in cat.columns:
            cat = cat.drop(['name_s'], axis=1)

        cpus = instrument.data.options.other['n_cpu'] if self.plot_id is None else 1

        if not self.snr_array_current:
            self.log('Physics-defining factors have changed, need to run full SNR flow.')
            if cpus > 1:
                from lifesim.instrument.instrument import balanced_partition_greedy
                # Multi Processing
                # divide the catalog into roughly equal chunks for each cpu
                n_star, occ_star = np.unique(cat.nstar, return_counts=True)
                star_groups = balanced_partition_greedy(occ=occ_star, items=n_star,
                                                        n_groups=cpus)

                sub_instruments = []
                for sg in star_groups:
                    sub_catalog = cat[np.isin(cat.nstar, sg)]
                    instr = deepcopy(instrument)
                    instr.data.catalog = sub_catalog
                    sub_instruments.append(instr)

                pbar = joblib_progress(
                    description=f"AMS | Calculating SNR | {cpus} Cores ", total=len(star_groups))

                with parallel_config(
                        backend="loky", inner_max_num_threads=1
                ), pbar if self.verbose else parallel_config(backend="loky", inner_max_num_threads=1):
                    results = Parallel(n_jobs=cpus)(
                        delayed(self.get_snr)(
                            instrument=instr,
                            verbose=False
                        )
                        for instr in sub_instruments)

                cat = pd.concat(results).reset_index(drop=True)
                cat.sort_values('id', inplace=True)

            else:
                # Single Processing
                cat = self.get_snr(instrument, verbose=self.verbose)

            # Save data to snr array. Filters will not touch it.
            self.snr_saved = cat['snr_1h'].to_numpy()
            self.snr_maxsep_saved = cat['maxsep_snr_1h'].to_numpy()
            self.snr_array_current = True
        else:
            self.log('No physics change, reusing SNR array.')

        self.log('Filtering SNR array...\r')
        # Filter Flow
        snr_filtered = np.zeros_like(self.snr_saved)
        maxsep_filtered = np.zeros_like(self.snr_maxsep_saved)

        # Filters = simple exclusions
        # Compute K-band magnitude
        # k_band center

        k_band = 2.2e-6

        # k band bin width
        k_band_width = 0.58e-6

        # convert units:
        # 1 Jy = 10^-26 J / (Hz * m^2)
        # Convert Hz to WL -> dlambda (K band width)
        # Convert J = W/s to photons per second -> lambda / (h * c)
        # --> 1 Jy = 1.51e7 * dlambda / lambda ph/s
        dlambda_lambda = 0.23

        # Campins, Reike, & Lebovsky (1985) from Jy to photons per second
        f_ref = 670 * 1.51e7 * dlambda_lambda

        flux = lambda wl: 2 * constants.c / (wl ** 4) / \
                (np.exp(constants.h * constants.c / wl / constants.k /
                        cat['temp_s']) - 1) * np.pi * ((cat['radius_s'] * constants.radius_sun)
                                                      / (10 * constants.m_per_pc)) ** 2

        k_flux = quad_vec(flux, k_band - k_band_width/2, k_band + k_band_width/2)[0]

        m_abs = -2.5 * np.log10(k_flux / f_ref)
        m_rel = m_abs + 5 * (np.log10(cat['distance_s']) - 1)

        mask = (m_rel <= self.lim_mag) & (abs(cat['lat']) <= self.field_of_regard)

        snr_filtered[mask] = self.snr_saved[mask]
        maxsep_filtered[mask] = self.snr_maxsep_saved[mask]

        cat['snr_1h'] = snr_filtered
        cat['maxsep_snr_1h'] = maxsep_filtered

        self.log('Starting optimization...')

        # Re-assign catalog for optimizer
        instrument.data.catalog = cat

        optimizer.ahgs()

        # Collect results to find the total mission time
        bus = instrument

        # collect the experiments
        exps = [col[4:] for col in bus.data.catalog.columns if col.startswith('exp_')]

        if not pre_select:
            bus.data.catalog = select()

        cat_det = bus.data.catalog[np.logical_and(
            bus.data.catalog.is_interesting,
            bus.data.catalog.detected
        )].sort_values('t_detected')

        cat_det['follow_up'] = False
        cat_det['t_orbit'] = 0.
        cat_det['t_char'] = 0.

        bus.data.catalog['follow_up'] = False

        # set up the time sheet that records the mission time per universe and per experiment
        columns = ['detection', 'orbit', 'characterization', 'total']
        for exp in exps:
            columns.append('n_' + exp)
        time_sheet = pd.DataFrame(index=np.unique(cat_det.nuniverse),
                                  columns=columns)

        # 1. get total time for detection campaign from every universe
        t_det = bus.data.catalog.t_detected.max()
        time_sheet['detection'] = t_det

        # 2. identify the follow_up targets for each universe
        cat_det.sort_values('maxsep_snr_1h', ascending=False, inplace=True)
        for nu in np.unique(cat_det.nuniverse):
            for exp in exps:
                mask_det = np.logical_and.reduce((cat_det.nuniverse == nu,
                                                  cat_det['exp_' + exp],
                                                  cat_det.t_detected <= t_det))
                # only set the top N targets to follow up where N is the sample size for the experiment
                mask_det_indices = cat_det[mask_det].index[
                    :bus.data.options.optimization['experiments'][exp]['sample_size']]
                cat_det.loc[mask_det_indices, 'follow_up'] = True
                time_sheet.loc[nu, 'n_' + exp] = len(mask_det_indices)

        # 3. calculate follow-up time for orbit and characterization
        cat_det.loc[cat_det.follow_up, 't_orbit'] = (
                (((bus.data.options.optimization['snr_target'] / cat_det[cat_det.follow_up].maxsep_snr_1h) ** 2)
                 * 60 * 60
                 + bus.data.options.array['t_slew'])
                * (bus.data.options.optimization['n_orbits'] - 1)
        )

        cat_det.loc[cat_det.follow_up, 't_char'] = (
            (((bus.data.options.optimization['snr_char'] / cat_det[cat_det.follow_up].maxsep_snr_1h) ** 2)
             * 60 * 60
             + bus.data.options.array['t_slew'])
        )

        for nu in np.unique(cat_det.nuniverse):
            mask_followup = np.logical_and.reduce(
                (cat_det.nuniverse == nu, cat_det.follow_up,
                 ))
            time_sheet.loc[nu, 'orbit'] = cat_det.loc[mask_followup, 't_orbit'].sum()
            time_sheet.loc[nu, 'characterization'] = cat_det.loc[mask_followup, 't_char'].sum()

        # 4. get total time
        time_sheet['total'] = time_sheet['detection'] + time_sheet['orbit'] + time_sheet['characterization']

        # 5. copy to original catalog
        cols = ['follow_up', 't_orbit', 't_char']
        mapping_df = cat_det.set_index('id')[cols]

        for col, fill_value, out_type in [
            ('follow_up', False, bool),
            ('t_orbit', 0.0, float),
            ('t_char', 0.0, float),
        ]:
            # map and infer object dtypes first
            s = bus.data.catalog['id'].map(mapping_df[col]).infer_objects(copy=False)
            # replace missing values without using .fillna
            s_filled = s.where(s.notna(), other=fill_value)
            # assign with desired type
            bus.data.catalog[col] = s_filled.astype(out_type)

        # To judge the success of missions, make a Gaussian distribution of time
        distribution = time_sheet['total'].to_numpy()

        # We take a cutoff such that 90% of missions are included, i.e., successful
        return np.percentile(distribution, 90) / 60 / 60 / 24 / 365.25

    def get_snr(self,
            instrument,
            verbose = True):
        """
        Computes the one-hour signal-to-noise ratio of every planet in the catalog under the
        configured error budgets.

        For each unique star in ``instrument.data.catalog``, the nulling baseline
        (:meth:`get_baseline`) and the star-dependent noise contributions (stellar leakage,
        local zodi and the zodi-level-1 exozodi background) are computed once and then
        applied to all of its planets/universes. The transmission-map response as a function
        of angular separation is tabulated on a 1-D grid and interpolated for each planet,
        avoiding a per-planet 360-point transmission-map evaluation.

        The configured :class:`~lifesim.ams.core.error_budget.ErrorBudget` instances are
        applied to the stellar leakage, local zodi, exozodi, planet signal and planet noise
        contributions before they are combined into the final SNR.

        Parameters
        ----------
        instrument : lifesim.instrument.instrument.Instrument
            The instrument module providing the catalog (``instrument.data.catalog``) and
            instrument parameters (``instrument.data.inst``, ``instrument.data.options``).
            ``instrument.apply_options()`` must have been called beforehand so that
            ``instrument.data.inst`` is up to date.
        verbose : bool, default True
            If ``True``, a progress bar is shown for the per-star physics loop.

        Returns
        -------
        pandas.DataFrame
            A copy of ``instrument.data.catalog`` with two additional columns:

            - ``'snr_1h'`` : the SNR after one hour of integration time, evaluated at the
              planet's actual angular separation (``angsep``).
            - ``'maxsep_snr_1h'`` : the SNR after one hour of integration time, evaluated at
              the planet's maximum angular separation (``maxsep``), used for
              characterization follow-up. Equal to ``'snr_1h'`` if the catalog has no
              ``'maxsep'`` column.

        Notes
        -----
        If :attr:`plot_id` is set, this method instead plots the noise budget breakdown
        (astrophysical noise, additional shot noise from the error budgets, and the
        individual stellar leakage / local zodi / exozodi contributions) for the star hosting
        the planet at that catalog row, then calls ``exit()``. This mode is intended for
        interactively inspecting error budgets and does not return.
        """

        # ------------------------------------
        #        D E F I N I T I O N S
        # ------------------------------------
        # Instrument-wide scope
        cat = instrument.data.catalog
        wl_bins = instrument.data.inst['wl_bins']

        # These two are absorbed into any grid
        eff_tot = instrument.data.inst['eff_tot']
        area = instrument.data.inst['telescope_area']

        # Degrees for transmission efficiency
        phi_space = np.linspace(0, 2 * np.pi, 360, endpoint=False)

        # ------------------------------------
        #  P R E  -  C A L C U L A T I O N S
        # ------------------------------------

        # Re-shape wl bins, required for transmission map
        wl_space = np.array([wl_bins])
        if wl_space.shape[-1] > 1:
            wl_space = np.reshape(wl_space, (wl_space.shape[-1], 1, 1))

        # Rescale hfov, required for transmission map
        hfov = instrument.data.inst['hfov']
        hfov = np.array([hfov])  # wavelength in m
        if hfov.shape[-1] > 1:
            hfov = np.reshape(hfov, (hfov.shape[-1], 1, 1))

        # Setup image angle and size for transmission map
        image_angle = instrument.data.inst['image_angle']
        image_angle = np.array([image_angle])  # wavelength in m
        if image_angle.shape[-1] > 1:
            image_angle = np.reshape(image_angle, (image_angle.shape[-1], 1, 1))
        image_size = instrument.data.options.other['image_size']

        # Compute FIXED alpha and beta for transmission map with static fov taper
        # generare 1D array that spans field of view
        angle = np.linspace(-1, 1, image_size)

        # angle matrix in x-direction ("alpha")
        alpha = np.tile(angle, (image_size, 1))

        # angle matrix in y-direction ("beta")
        beta = alpha.T

        # convert angle matrices to fov units
        alpha_fixed = alpha * image_angle
        beta_fixed = beta * image_angle

        # Compute static fov taper function for the noise sources
        radius_map = instrument.data.inst['radius_map']
        if instrument.data.options.models['fov_taper'] == 'gaussian':
            ap = np.ones_like(radius_map)
        elif instrument.data.options.models['fov_taper'] == 'none':
            ap = np.where(radius_map
                          <= instrument.options.other['image_size'] / 2, 1, 0)
        else:
            raise ValueError('Nonexistent fov taper model')

        ap_sum = ap.sum()

        # Some localzodi definitions
        # Since the simulation is static in time (planets not moving), the longitude is fixed
        long = 3 / 4 * np.pi
        radius_sun_au = 0.00465047  # in AU
        tau = 4e-8
        temp_eff = 265
        temp_sun = 5777
        a = 0.22

        # Compute the inbound flux
        b_tot = black_body(mode='wavelength',
                           bins=instrument.data.inst['wl_bins'],
                           width=instrument.data.inst['wl_bin_widths'],
                           temp=temp_eff) + a \
                * black_body(mode='wavelength',
                             bins=instrument.data.inst['wl_bins'],
                             width=instrument.data.inst['wl_bin_widths'],
                             temp=temp_sun) \
                * (radius_sun_au / 1.5) ** 2

        # Contrast
        image_size_star = 50
        # Compute FIXED alpha and beta for transmission map with static fov taper
        # generare 1D array that spans field of view
        angle = np.linspace(-1, 1, image_size_star)

        # angle matrix in x-direction ("alpha")
        alpha_star_base = np.tile(angle, (image_size_star, 1))

        # angle matrix in y-direction ("beta")
        beta_star_base = alpha_star_base.T

        # Convert into coordinates and make a cut-off outside the star
        x_map = np.tile(np.array(range(0, image_size_star)), (image_size_star, 1))
        y_map = x_map.T
        r_square_map = (x_map - (image_size_star - 1) / 2) ** 2 + (y_map - (image_size_star - 1) / 2) ** 2
        star_px = np.where(r_square_map < (image_size_star / 2) ** 2, 1, 0)
        star_px_sum = star_px.sum()

        wl_bin_widths = instrument.data.inst['wl_bin_widths']

        # EXO
        # reshape the mas per pixel array for calculation (to (n, 1, 1))
        mas_pix = np.array([instrument.data.inst['mas_pix']])
        if mas_pix.shape[-1] > 1:
            mas_pix = np.reshape(mas_pix, (mas_pix.shape[-1], 1, 1))
        rad_pix = np.array([instrument.data.inst['rad_pix']])
        if rad_pix.shape[-1] > 1:
            rad_pix = np.reshape(rad_pix, (rad_pix.shape[-1], 1, 1))

        wl_bin_widths_space = np.array([instrument.data.inst['wl_bin_widths']])
        if wl_bin_widths_space.shape[-1] > 1:
            wl_bin_widths_space = np.reshape(wl_bin_widths_space, (wl_bin_widths_space.shape[-1], 1, 1))

        # Setup function to quickly retrieve the transmission map if required, also save the FoV taper
        # that does not change
        static_fov_taper = np.exp(- (np.pi / 4 / hfov * np.sqrt(alpha_fixed ** 2 + beta_fixed ** 2)) ** 2)


        def transmission_map(bl, alpha=None, beta=None, map='tm3'):
            if alpha is None or beta is None:
                alpha = alpha_fixed
                beta = beta_fixed
                fov_taper = static_fov_taper if instrument.data.options.models['fov_taper'] == 'gaussian' else 1
            else:
                fov_taper = np.exp(- (np.pi / 4 / hfov * np.sqrt(alpha ** 2 + beta ** 2)) ** 2) \
                    if instrument.data.options.models['fov_taper'] == 'gaussian' else 1

            L = bl / 2
            sin_contrib = np.sin(2 * np.pi * L * alpha / wl_space) ** self.__nulling_order
            if map == 'tm3':
                tmap = sin_contrib * np.cos(2 * instrument.data.options.array['ratio']
                                           * np.pi * L * beta / wl_space - np.pi / 4) ** 2
            elif map != 'tm4':
                raise ValueError('Invalid transmission map requested')
            else:
                tmap = sin_contrib * np.cos(2 * instrument.data.options.array['ratio']
                                       * np.pi * L * beta / wl_space + np.pi / 4) ** 2
            tmap *= fov_taper
            return tmap

        # Random integration time (e.g., 1h)
        int_time = 60 * 60

        maxsep_exists = 'maxsep' in cat.columns

        n_wl = wl_bins.shape[0]

        # ------------------------------------------------------------------
        #   P E R  -  S T A R   P H Y S I C S
        # ------------------------------------------------------------------
        # Stellar leakage, local-zodi and the (zodi-level 1) exozodi base only depend on the star,
        # not on the individual planet. We therefore compute them exactly once per *unique* star
        # instead of once per planet. (This is the old memoization, hoisted out of the row loop so
        # the heavy per-star map computations are never repeated for planets of the same star.)
        nstar_arr = cat['nstar'].to_numpy()
        unique_stars, inverse = np.unique(nstar_arr, return_inverse=True)
        n_unique = unique_stars.shape[0]

        # one representative planet (row position) per unique star -- all stellar quantities are
        # identical across the planets/universes of a given star
        rep_pos = np.empty(n_unique, dtype=np.int64)
        rep_pos[inverse] = np.arange(nstar_arr.shape[0])

        hz_center_s = cat['hz_center'].to_numpy()[rep_pos]
        distance_star_s = cat['distance_s'].to_numpy()[rep_pos]
        temp_s_s = cat['temp_s'].to_numpy()[rep_pos]
        radius_s_s = cat['radius_s'].to_numpy()[rep_pos]
        l_sun_s = cat['l_sun'].to_numpy()[rep_pos]
        lat_s = cat['lat'].to_numpy()[rep_pos]

        wl_optimal = instrument.data.options.other['wl_optimal']
        bl_min = instrument.data.options.array['bl_min']
        bl_max = instrument.data.options.array['bl_max']

        # per-star results
        bl_s = np.empty(n_unique)
        noise_bg_star_s = np.empty((n_unique, n_wl))   # local-zodi + stellar leakage (after budgets)
        exozodi_astro_s = np.empty((n_unique, n_wl))   # exozodi astro signal at zodi level 1

        # plot mode targets one specific planet (positional id); resolve its star and zodi level
        plot_star = nstar_arr[self.plot_id] if self.plot_id is not None else None
        z_plot = cat['z'].to_numpy()[self.plot_id] if self.plot_id is not None else None

        for k in tqdm(range(n_unique), total=n_unique, disable=not verbose,
                      desc='AMS | SNR Calculation | Per-star physics '):

            hz_center = hz_center_s[k]
            distance_s = distance_star_s[k]
            temp_s = temp_s_s[k]
            radius_s = radius_s_s[k]
            l_sun = l_sun_s[k]
            lat = lat_s[k]

            # baseline and (static) transmission map for this star
            bl = AgnosticMissionSimulator.get_baseline(hz_center, distance_s,
                                                       wl_optimal, bl_min, bl_max)
            tmap = transmission_map(bl)

            # STELLAR LEAKAGE
            bb_star = black_body(
                mode='star',
                bins=wl_bins,
                width=wl_bin_widths,
                temp=temp_s,
                radius=radius_s,
                distance=distance_s
            )

            # convert units
            Rs_au = 0.00465047 * radius_s
            Rs_as = Rs_au / distance_s
            Rs_mas = float(Rs_as)
            Rs_rad = Rs_mas / (3600. * 180.) * np.pi

            # convert angle matrices to fov units
            alpha = alpha_star_base * Rs_rad
            beta = beta_star_base * Rs_rad

            tm_star = transmission_map(bl, alpha=alpha, beta=beta)

            noise_star_astro = ((star_px * tm_star).sum(axis=(-2, -1)) / star_px_sum *
                                bb_star * area)

            noise_star = self.__leakage_budget.evaluate(noise_star_astro, hz_center, distance_s,
                                                        radius_s, wl_bins)

            # LOCALZODI
            lz_flux_sr = tau * b_tot * np.sqrt(
                np.pi / np.arccos(np.cos(long) * np.cos(lat)) /
                (np.sin(lat) ** 2
                 + (0.6 * (wl_bins / 11e-6) ** (-0.4) * np.cos(lat)) ** 2)
            )

            lz_flux = lz_flux_sr * (np.pi * instrument.data.inst['image_angle'] ** 2)

            localzodi_noise_astro = (ap * tmap).sum(axis=(-2, -1)) / ap_sum * lz_flux * area

            localzodi_noise = self.__localzodi_budget.evaluate(localzodi_noise_astro, hz_center,
                                                               distance_s, lat, wl_bins)

            # EXOZODI (base, i.e. for a zodi level of 1)
            # calculate the parameters required by Kennedy2015
            alpha_ez = 0.34
            r_in = 0.034422617777777775 * np.sqrt(l_sun)
            r_0 = np.sqrt(l_sun)
            sigma_zero = 7.11889e-8  # Sigma_{m,0} from Kennedy+2015 (doi:10.1088/0067-0049/216/2/23)

            au_pix = mas_pix / 1e3 * distance_s

            # the radius as measured from the central star for every pixel in [AU]
            r_au = radius_map * au_pix

            # identify all pixels where the radius is larges than the inner radius by Kennedy+2015
            r_cond = ((r_au >= r_in)
                      & (r_au <= image_size / 2 * au_pix))

            # calculate the temperature at all pixel positions according to Kennedy2015 Eq. 2
            temp_map = np.where(r_cond,
                                278.3 * (l_sun ** 0.25) / np.sqrt(r_au), 0)

            # calculate the Sigma (Eq. 3) in Kennedy2015 and set everything inside the inner radius to 0
            sigma = np.where(r_cond,
                             sigma_zero *
                             (r_au / r_0) ** (-alpha_ez), 0)

            # get the black body radiation emitted by the interexoplanetary dust
            f_nu_disk = black_body(bins=wl_space,
                                   width=wl_bin_widths_space,
                                   temp=temp_map,
                                   mode='wavelength') \
                        * sigma * rad_pix ** 2 * area

            # add the transmission map, exozodi should be normalized
            exozodi_noise_astro = (f_nu_disk * tmap * ap).sum(axis=(-2, -1))

            # hab2hi: 9
            if self.plot_id is not None and unique_stars[k] == plot_star:

                X = wl_bins[:-1] * 1e6
                y = wl_bin_widths * 1e6

                total_noise_astro = (noise_star_astro + localzodi_noise_astro + z_plot * exozodi_noise_astro) / y

                exozodi_noise = exozodi_noise_astro * z_plot
                exozodi_noise = self.__exozodi_budget.evaluate(exozodi_noise,
                                                               hz_center,
                                                               distance_s, l_sun, wl_bins)

                total_noise = (noise_star + localzodi_noise + exozodi_noise) / y

                x_splines = np.linspace(X[0], X[-1], 1000)
                addition = (self.__leakage_budget.get_factors()[0]((None, None, None, wl_bins))) / y

                spl = make_interp_spline(X, addition[:-1], k=3)
                addition = spl(x_splines)

                spl = make_interp_spline(X, total_noise_astro[:-1], k=3)
                total_noise_astro = spl(x_splines)

                spl = make_interp_spline(X, total_noise[:-1], k=3)
                total_noise = spl(x_splines)

                plt.plot(x_splines, total_noise, color='tab:green', label='Total Noise')

                plt.fill_between(x_splines, total_noise_astro, total_noise, label='Error Budget', hatch='\\\\',
                                 facecolor='tab:green', edgecolor='tab:orange', alpha=0.25)

                plt.fill_between(x_splines, total_noise_astro, addition, hatch='\\\\',
                                 facecolor='tab:green', edgecolor='tab:orange', alpha=0.5,
                                 where=addition > total_noise_astro)

                plt.plot(x_splines, addition, color='tab:green', linestyle='-.',
                         label='Additional Shot Noise', alpha=0.5)

                plt.plot(x_splines, total_noise_astro, linestyle='--',
                         color='tab:orange', label='Astrophysical Noise', alpha=0.8)

                plt.plot(X, (noise_star_astro / y)[:-1], linestyle=':', color='tab:purple',
                         label='Stellar Leakage', alpha=0.4)
                plt.plot(X, (localzodi_noise_astro / y)[:-1], linestyle=':', color='tab:cyan',
                         label='Localzodi Noise', alpha=0.4)
                plt.plot(X, (z_plot * exozodi_noise_astro / y)[:-1], linestyle=':', color='tab:red',
                         label='Exozodi Noise', alpha=0.4)

                plt.legend(fontsize=7)

                plt.title('Astrophysical Noise and Error Budget (8 yrs, Short-Long Gradient)')

                #plt.yscale('log')
                plt.xlabel('Wavelength (micron)')
                plt.ylabel('Noise Contribution (ph s$^{-1}$ micron$^{-1}$)')

                plt.show()

                exit()

            bl_s[k] = bl
            noise_bg_star_s[k] = localzodi_noise + noise_star
            exozodi_astro_s[k] = exozodi_noise_astro

        # ------------------------------------------------------------------
        #   P L A N E T   R E S P O N S E   (tabulated + vectorized)
        # ------------------------------------------------------------------
        # For a point source the chopped-signal and noise transmission factors only depend on the
        # dimensionless parameter
        #       x = pi * bl * angsep_rad / wl .
        # After averaging over the array-rotation angle phi, both
        #       S(x) = sqrt(<(tm3 - tm4)^2>_phi)   and   N(x) = sqrt(<tm4^2>_phi)
        # are pure 1-D functions of x (the FoV taper is constant in phi and factors out, so it is
        # applied separately). We tabulate S and N once and interpolate, replacing the per-planet
        # 360-point transmission map with a vectorized table lookup over the whole catalog.
        ratio = instrument.data.options.array['ratio']
        order = self.__nulling_order
        cos_phi = np.cos(phi_space)
        sin_phi = np.sin(phi_space)

        # map per-star quantities back onto the per-planet axis (catalog order)
        bl_p = bl_s[inverse]
        noise_bg_star_p = noise_bg_star_s[inverse]
        exozodi_astro_p = exozodi_astro_s[inverse]

        angsep = cat['angsep'].to_numpy()
        angsep_rad = angsep / (3600 * 180) * np.pi
        if maxsep_exists:
            maxsep = cat['maxsep'].to_numpy()
            maxsep_rad = maxsep / (3600 * 180) * np.pi

        # x is largest at the smallest wavelength; build the table over the data range
        x_max = float((bl_p * angsep_rad).max())
        if maxsep_exists:
            x_max = max(x_max, float(np.nanmax(bl_p * maxsep_rad)))
        x_max = np.pi * x_max / wl_bins.min() * 1.001 + 1e-3
        x_max = max(x_max, 1e-3)

        n_grid = min(int(np.ceil(x_max / 0.01)) + 4, 400000)
        x_grid = np.linspace(0.0, x_max, n_grid)
        s_grid = np.empty(n_grid)
        nz_grid = np.empty(n_grid)

        # build the table in chunks to keep the (grid x phi) intermediate small
        for ga in range(0, n_grid, 20000):
            gb = min(ga + 20000, n_grid)
            xg = x_grid[ga:gb][:, None]
            g = np.sin(xg * cos_phi[None, :]) ** order
            beta_arg = ratio * xg * sin_phi[None, :]
            tm3_0 = g * np.cos(beta_arg - np.pi / 4) ** 2
            tm4_0 = g * np.cos(beta_arg + np.pi / 4) ** 2
            chop = tm3_0 - tm4_0
            s_grid[ga:gb] = np.sqrt((chop ** 2).mean(axis=1))
            nz_grid[ga:gb] = np.sqrt((tm4_0 ** 2).mean(axis=1))

        signal_spline = make_interp_spline(x_grid, s_grid, k=3)
        noise_spline = make_interp_spline(x_grid, nz_grid, k=3)

        # planet-separation independent background noise (per planet, per wl)
        z_p = cat['z'].to_numpy()
        hz_center_p = cat['hz_center'].to_numpy()
        distance_p = cat['distance_s'].to_numpy()
        l_sun_p = cat['l_sun'].to_numpy()

        exozodi_noise = exozodi_astro_p * z_p[:, None]
        exozodi_noise = self.__exozodi_budget.evaluate(exozodi_noise, hz_center_p, distance_p,
                                                       l_sun_p, wl_bins)
        noise_bg = (exozodi_noise + noise_bg_star_p) * int_time * eff_tot * 2

        # pure thermal planet flux (per planet, per wl)
        flux_planet_thermal = black_body(
            mode='planet',
            bins=wl_bins,
            width=wl_bin_widths,
            temp=cat['temp_p'].to_numpy()[:, None],
            radius=cat['radius_p'].to_numpy()[:, None],
            distance=distance_p[:, None]
        )

        gaussian_taper = instrument.data.options.models['fov_taper'] == 'gaussian'
        hfov_flat = np.asarray(instrument.data.inst['hfov'])

        def snr_for_sep(sep, sep_rad):
            # transmission-map signal/noise via the dimensionless table lookup
            x = np.pi * bl_p[:, None] * sep_rad[:, None] / wl_bins[None, :]
            signal = signal_spline(x)
            noise = noise_spline(x)
            if gaussian_taper:
                fov_taper = np.exp(- (np.pi / 4 / hfov_flat[None, :] * sep_rad[:, None]) ** 2)
                signal = signal * fov_taper
                noise = noise * fov_taper

            # Calculate the signal and photon noise flux received from the planet
            flux_planet = flux_planet_thermal * signal * eff_tot * area * int_time
            noise_planet = flux_planet_thermal * noise * eff_tot * area * int_time * 2

            flux_planet = self.__planet_signal_budget.evaluate(flux_planet, hz_center_p, distance_p,
                                                              sep, wl_bins)
            noise_planet = self.__planet_noise_budget.evaluate(noise_planet, hz_center_p, distance_p,
                                                              sep, wl_bins)

            # Add up the noise and calculate the SNR (white noise -> sum over wl bins)
            noise_total = noise_bg + noise_planet
            return np.sqrt((flux_planet ** 2 / noise_total).sum(axis=1))

        snr_result = snr_for_sep(angsep, angsep_rad)
        if maxsep_exists:
            maxsep_snr_result = snr_for_sep(maxsep, maxsep_rad)
        else:
            maxsep_snr_result = snr_result.copy()

        # Write data & finish, get ready to input into the optimizer
        return cat.assign(snr_1h=snr_result, maxsep_snr_1h=maxsep_snr_result)

    def get_leakage_budget(self):
        """Returns the :class:`~lifesim.ams.core.error_budget.ErrorBudget` applied to the
        stellar leakage noise."""
        return self.__leakage_budget
    def get_localzodi_budget(self):
        """Returns the :class:`~lifesim.ams.core.error_budget.ErrorBudget` applied to the
        local zodiacal light noise."""
        return self.__localzodi_budget
    def get_planet_signal_budget(self):
        """Returns the :class:`~lifesim.ams.core.error_budget.ErrorBudget` applied to the
        planet signal flux."""
        return self.__planet_signal_budget
    def get_planet_noise_budget(self):
        """Returns the :class:`~lifesim.ams.core.error_budget.ErrorBudget` applied to the
        photon noise contributed by the planet."""
        return self.__planet_noise_budget
