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
from lifesim.instrument.pn_star import PhotonNoiseStar
from lifesim.instrument.pn_localzodi import PhotonNoiseLocalzodi
from lifesim.instrument.pn_exozodi import PhotonNoiseExozodi

import matplotlib as mpl

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
                 architecture=None,
                 verbose=True):

        self.__nulling_order = nulling_order

        # Optional concrete beam combiner as (unit_positions, U, chop_pair), with
        # aperture positions in units of the nulling baseline. When set, the
        # transmission comes from that combiner rather than from the sin^n
        # proxy, and the noise modules follow via data.inst['architecture'].
        self.__architecture = architecture

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

        # Must precede apply_options(): the baseline prescription reads the
        # architecture to size the array to its own response peak.
        instrument.data.inst['architecture'] = self.__architecture

        # apply_options derives BOTH the collecting area and the single-aperture
        # field of view from options.array (instrument.py:92-105) --
        # area = num_apertures * pi * (diameter/2)^2 and hfov = wl / (2*diameter).
        # An architecture with an aperture count other than the configured one
        # would otherwise be charged the configured array's area while keeping
        # its field of view, which is not any physical instrument: the two must
        # come from the same collectors. Taking the count from the architecture
        # fixes the collector diameter and lets the total area follow it, so
        # every design is built from identically sized apertures and shares the
        # reference's field of view.
        if self.__architecture is not None:
            n_ap = int(np.asarray(self.__architecture[0]).shape[0])
            instrument.data.options.array['num_apertures'] = n_ap

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

        if self.plot_id is not None:
            return self.get_snr(instrument, self.verbose)

        cpus = instrument.data.options.other['n_cpu']

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
        # Universes with zero surviving detections are historically absent from this
        # index and therefore from the percentile below.
        # optimization['retain_empty_universes'] = True keeps every universe in the
        # catalog, with zero follow-up time.
        if bus.data.options.optimization.get('retain_empty_universes', False):
            sheet_index = np.unique(bus.data.catalog.nuniverse)
        else:
            sheet_index = np.unique(cat_det.nuniverse)
        time_sheet = pd.DataFrame(index=sheet_index,
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
        # No-op on the historical index; fills the retained empty universes with zero
        # follow-up time.
        time_sheet = time_sheet.fillna(0.)
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

        # Retained for inspection: per-universe component times behind the returned
        # percentile.
        self.last_time_sheet = time_sheet

        # We take a cutoff such that 90% of missions are included, i.e., successful
        return np.percentile(distribution, 90) / 60 / 60 / 24 / 365.25

    def get_snr(self,
            instrument,
            verbose = True):
        """
        Computes the one-hour signal-to-noise ratio of every planet in the catalog under the
        configured error budgets.

        For each unique star in ``instrument.data.catalog``, the nulling baseline
        (:meth:`Instrument.adjust_bl_to_hz`) and the star-dependent noise contributions
        (stellar leakage, local zodi and the zodi-level-1 exozodi background, delegated to
        ``instrument``'s own connected ``PhotonNoiseStar``/``PhotonNoiseLocalzodi``/
        ``PhotonNoiseExozodi`` modules) are computed once and then applied to all of its
        planets/universes. The transmission-map response as a function of angular separation is
        tabulated on a 1-D grid and interpolated for each planet, avoiding a per-planet
        360-point transmission-map evaluation.

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

        wl_bin_widths = instrument.data.inst['wl_bin_widths']

        if self.__nulling_order < 2 or self.__nulling_order % 2 != 0:
            raise ValueError(
                f'nulling_order must be a positive even integer (got {self.__nulling_order}); '
                'odd orders average to zero under a full array rotation, so the closed-form '
                'noise formulas (transmission_analytic.py) have no solution for them.')

        # Push the configured nulling order onto the shared instrument state -- LIFEsim proper
        # always defaults this to 2 (Instrument.apply_options()); the AMS is the only caller that
        # overwrites it, keeping the two branches independent (see ANALYTIC_NOISE_REWRITE.md).
        # The delegated noise modules below pick it up via `self.data.inst['nulling_order']`.
        instrument.data.inst['nulling_order'] = self.__nulling_order
        # Same channel for a concrete combiner: when present the noise modules
        # evaluate the physical response instead of the sin^n proxy.
        instrument.data.inst['architecture'] = self.__architecture

        # Star-leak/local-zodi/exozodi noise is delegated to the instrument's own connected
        # PhotonNoiseStar/PhotonNoiseLocalzodi/PhotonNoiseExozodi modules instead of
        # reimplementing the same physics here -- keeps this in sync automatically with any
        # future fix to those modules (see ANALYTIC_NOISE_REWRITE.md), instead of needing a
        # duplicate port every time.
        def _find_module(s_name, cls):
            for module in instrument.sockets[s_name]['modules']:
                if isinstance(module, cls):
                    return module
            raise ValueError(f'Instrument has no {cls.__name__} connected to socket "{s_name}"; '
                             f'AMS.get_snr requires it to compute noise.')

        star_module = _find_module('photon_noise_star', PhotonNoiseStar)
        localzodi_module = _find_module('photon_noise_star', PhotonNoiseLocalzodi)
        exozodi_module = _find_module('photon_noise_universe', PhotonNoiseExozodi)

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
        radius_s_s = cat['radius_s'].to_numpy()[rep_pos]
        l_sun_s = cat['l_sun'].to_numpy()[rep_pos]
        lat_s = cat['lat'].to_numpy()[rep_pos]

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
            radius_s = radius_s_s[k]
            l_sun = l_sun_s[k]
            lat = lat_s[k]
            i = int(rep_pos[k])

            # sets instrument.data.inst['bl'] from this star's habitable-zone center, exactly
            # as Instrument.get_snr does -- the noise modules below read it off the instrument.
            instrument.adjust_bl_to_hz(hz_center=hz_center, distance_s=distance_s)
            bl = instrument.data.inst['bl']

            noise_star_astro = np.asarray(star_module.noise(index=i))
            noise_star = self.__leakage_budget.evaluate(noise_star_astro, hz_center, distance_s,
                                                        radius_s, wl_bins)

            localzodi_noise_astro = np.asarray(localzodi_module.noise(index=i))
            localzodi_noise = self.__localzodi_budget.evaluate(localzodi_noise_astro, hz_center,
                                                               distance_s, lat, wl_bins)

            # exozodi at zodi level 1 -- the z scaling is applied vectorially after the loop
            exozodi_noise_astro = np.asarray(exozodi_module.noise(index=i))

            if self.plot_id is not None and unique_stars[k] == plot_star:

                fig, ax = plt.subplots()

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

                ax.plot(x_splines, total_noise, color='tab:green', label='Total Noise')

                ax.fill_between(x_splines, total_noise_astro, total_noise, label='Error Budget', hatch='\\\\',
                                 facecolor='tab:green', edgecolor='tab:orange', alpha=0.25)

                ax.fill_between(x_splines, total_noise_astro, addition, hatch='\\\\',
                                 facecolor='tab:green', edgecolor='tab:orange', alpha=0.5,
                                 where=addition > total_noise_astro)

                ax.plot(x_splines, addition, color='tab:green', linestyle='-.',
                         label='Additional Shot Noise', alpha=0.5)

                ax.plot(x_splines, total_noise_astro, linestyle='--',
                         color='tab:orange', label='Astrophysical Noise', alpha=0.8)

                ax.plot(X, (noise_star_astro / y)[:-1], linestyle=':', color='tab:purple',
                         label='Stellar Leakage', alpha=0.4)
                ax.plot(X, (localzodi_noise_astro / y)[:-1], linestyle=':', color='tab:cyan',
                         label='Localzodi Noise', alpha=0.4)
                ax.plot(X, (z_plot * exozodi_noise_astro / y)[:-1], linestyle=':', color='tab:red',
                         label='Exozodi Noise', alpha=0.4)

                ax.legend(fontsize=7)

                return fig, ax

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

        if self.__architecture is not None:
            # A concrete beam combiner: build the same table from the physical
            # response instead of the sin^n shape proxy. The tabulation itself is
            # unchanged, because the rotation average of any array whose geometry
            # scales with one baseline is still a function of x alone.
            from lifesim.util.combiner import signal_noise_tables
            u_pos, U_mat, chop_pair = self.__architecture
            s_grid, nz_grid = signal_noise_tables(u_pos, U_mat, chop_pair,
                                                  x_grid, bl=1.0,
                                                  n_phi=phi_space.size)
        else:
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
