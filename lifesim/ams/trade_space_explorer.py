"""
Trade-space exploration plots for the Agnostic Mission Simulator (AMS).

This module provides :class:`TradeSpaceExplorer`, which bundles a set of plotting and
root-finding routines that repeatedly call
:meth:`~lifesim.ams.core.ams.AgnosticMissionSimulator.run` while scanning over AMS
attributes (e.g. ``lim_mag``, ``field_of_regard``, ``slew_time``) or error budgets, in
order to visualize how the required mission time depends on these trade-space
parameters.
"""

import os
import re

import matplotlib as mpl
import cmocean.cm as cmo
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm
from scipy.interpolate import RegularGridInterpolator

_RESUME_HEAD = re.compile(r'>> TSE Run No\. (\d+) / (\d+)')
_RESUME_CUT = re.compile(r'>> Budget CUTOFF found: (\d+) ph/s')
_RESUME_IMP = re.compile(r'>> Impossible to reach MT target')


def recover_scan_progress(log_path):
    """Recover completed grid points from an interrupted scan's log.

    A scan is hours long and writes nothing but its figure at the end, so an
    interruption loses everything. Each grid point does announce its run number
    and then its verdict, and the loop visits points in a fixed order, so the
    run number alone identifies the cell. Returns ``{run_index: cutoff}`` with
    run indices zero-based, an infeasible point recorded as ``0.0``.

    Resuming from this is exact rather than approximate: the only state the loop
    carries between points is ``upper_limits`` and ``j_cutoff``, and both are
    pure functions of the cutoffs already found, so replaying the recorded
    values rebuilds them precisely.
    """
    done = {}
    if not log_path:
        return done
    if not os.path.exists(log_path):
        # Silently returning nothing here means an unnoticed full recomputation,
        # which is hours. Say so instead.
        print(f'>> WARNING: resume log not found, computing every point: {log_path}',
              flush=True)
        return done
    with open(log_path, errors='replace') as fh:
        txt = fh.read()
    for m in _RESUME_HEAD.finditer(txt):
        tail = txt[m.end(): m.end() + 4000]
        cut, imp = _RESUME_CUT.search(tail), _RESUME_IMP.search(tail)
        if cut and (imp is None or cut.start() < imp.start()):
            done[int(m.group(1)) - 1] = float(cut.group(1))
        elif imp:
            done[int(m.group(1)) - 1] = 0.0
    return done
from scipy.optimize import fsolve

# Interactive exploration wants a GUI backend, but importing this module must not
# force one: batch and cluster runs have no display, and a caller that has
# already selected a file backend has done so deliberately. Only switch when the
# current backend is still an interactive one, and never fail if Qt is absent.
_NON_INTERACTIVE = ('agg', 'pdf', 'svg', 'ps', 'cairo', 'template')
try:
    import os as _os
    if (_os.environ.get('MPLBACKEND') is None
            and mpl.get_backend().lower() not in _NON_INTERACTIVE):
        mpl.use('Qt5Agg')
except Exception:
    pass

class TradeSpaceExplorer:
    """
    Collection of trade-space exploration plots built around a single AMS configuration.

    Each explorer method scans one or more AMS attributes or error budgets over a grid,
    repeatedly calling :meth:`~lifesim.ams.core.ams.AgnosticMissionSimulator.run` (which
    in turn uses :attr:`optimizer` and :attr:`instrument`), and visualizes the resulting
    mission times. Since :attr:`ams`, :attr:`optimizer` and :attr:`instrument` are stored
    once on the explorer, the individual methods only need the parameters specific to the
    scan they perform.

    Parameters
    ----------
    ams : lifesim.ams.core.ams.AgnosticMissionSimulator
        The AMS instance whose :meth:`~lifesim.ams.core.ams.AgnosticMissionSimulator.run`
        method is repeatedly called to evaluate the mission time for the points of the
        trade space under investigation. Many of the explorer methods directly modify
        attributes of this instance (e.g. ``lim_mag``, ``field_of_regard``, ``slew_time``)
        or its connected error budgets.
    optimizer : lifesim.optimize.optimizer.Optimizer
        The optimizer module (with a connected AHGS module), passed to
        ``ams.run()``.
    instrument : lifesim.instrument.instrument.Instrument
        The instrument module providing the catalog (``instrument.data.catalog``) and
        instrument parameters (``instrument.data.inst``, ``instrument.data.options``).

    Attributes
    ----------
    ams : lifesim.ams.core.ams.AgnosticMissionSimulator
    optimizer : lifesim.optimize.optimizer.Optimizer
    instrument : lifesim.instrument.instrument.Instrument
    """

    def __init__(self, ams, optimizer, instrument):
        self.ams = ams
        self.optimizer = optimizer
        self.instrument = instrument

    def locate_mission_cutoff(self, cutoff=10, upper_start=50_000, setter_func=None, plot_data=None):
        """
        Finds the additive leakage-budget level at which the mission time equals ``cutoff``.

        The search assumes that the mission time grows monotonically and roughly
        exponentially with the budget value. It evaluates the mission time at the lower
        (``0``) and upper (``upper_start``) bounds, fits an exponential
        ``m_time = a * exp(b * budget)`` through these two points, inverts it to obtain a
        guess for the cutoff, evaluates the mission time at the guess, and then tightens
        whichever bound the guess is closest to. This repeats until the guess is within
        ``epsilon = 0.05`` years of ``cutoff`` or the bounds have converged to within
        10 ph/s.

        Parameters
        ----------
        cutoff : float, default 10
            Target mission time, in years.
        upper_start : float, default 50_000
            Initial upper bound for the budget value, in ph/s/micron.
        setter_func : callable, optional
            Called as ``setter_func(budget)`` to apply a trial ``budget`` value
            to the AMS before calling ``self.ams.run()``. Defaults to setting a flat
            additive leakage budget of ``budget`` ph/s/micron across all wavelength bins,
            i.e.
            ``self.ams.get_leakage_budget().update_factors(additive_factor=lambda args: budget * wl_bin_widths)``.

        Returns
        -------
        float
            The budget value at which the mission time matches ``cutoff``. Returns
            ``upper_start`` if the mission time at the upper bound already meets or is
            below ``cutoff``, and ``0`` if the mission time at a budget of ``0`` already
            meets or exceeds ``cutoff`` (i.e. the target is unreachable, no extra noise is
            permissible).
        """

        lower = 0
        epsilon = 0.05

        if setter_func is None:
            setter_func = lambda bud: self.ams.get_leakage_budget().update_factors(
                additive_factor=lambda args: bud * self.instrument.data.inst['wl_bin_widths'] * 1e6)

        mtime = -1
        its = 2

        print(f' > Finding budget CUTOFF for MT target ({cutoff} yrs)')

        setter_func(upper_start)
        high_mtime = self.ams.run(self.instrument, self.optimizer)
        print(f' > Upper Bound MT: {high_mtime:.2f} yrs @ {int(upper_start)} ph/s')
        if high_mtime < cutoff or abs(high_mtime - cutoff) <= epsilon:
            print('>> Cancelling procedure: upper bound matches or is below MT target (fluctuation?)')
            print(f'>> Budget CUTOFF found: {int(upper_start)} ph/s (1 iteration)')
            self.last_search = dict(status='censored_upper', lower=lower,
                                    upper=upper_start, mtime=high_mtime, its=1)
            return upper_start

        setter_func(lower)
        low_mtime = self.ams.run(self.instrument, self.optimizer)
        print(f' > Lower Bound MT: {low_mtime:.2f} yrs @ {int(lower)} ph/s')
        if low_mtime >= cutoff or abs(low_mtime - cutoff) <= epsilon:
            print('>> Cancelling procedure: lower bound matches or is above MT target (2 iterations)')
            self.last_search = dict(status='zero_budget_at_or_above_target', lower=0,
                                    upper=upper_start, mtime=low_mtime, its=2)
            return 0

        print(' > Ready to start iterations')

        # Mission time is a step function of the budget, because detections are
        # discrete, so a target falling between two steps admits no amplitude
        # within `epsilon`. The bracket then stops shrinking -- the exponential
        # fit returns a guess equal to the lower bound, which is reassigned to
        # itself -- and the loop above never exits. Observed at 1395 iterations
        # with the bracket frozen 12 wide. Stop on stagnation or on a cap and
        # report the best bracket instead of spinning.
        max_its = 200
        stalled = 0
        while abs(cutoff - mtime) > epsilon and upper_start - lower > 10:
            if its >= max_its or stalled >= 3:
                print(f'>> Stopping: no amplitude reaches the target to within '
                      f'{epsilon} yr; bracket [{int(lower)}, {int(upper_start)}] '
                      f'after {its} iterations. Reporting the bracket midpoint.')
                self.last_search = dict(status='bracket_midpoint', lower=lower,
                                        upper=upper_start, mtime=mtime, its=its)
                return 0.5 * (lower + upper_start)
            prev_bracket = (lower, upper_start)
            print('---------------------------')
            print(f' > Iteration {its + 1}')
            print('---------------------------')

            fluxes = np.array([lower, upper_start])
            m_times = np.array([low_mtime, high_mtime])

            fnc = lambda x: m_times - x[0] * np.exp(x[1] * fluxes)

            a, b = fsolve(fnc, np.array([m_times[0], 1 / upper_start]))

            # Invert exponential function to locate cutoff
            guess = max(np.log(cutoff / a) / b, 0)
            print(f' > Lower Bound: {int(lower)} ph/s | Guess: {int(guess)} ph/s | '
                  f'Upper Bound: {int(upper_start)} ph/s')
            setter_func(guess)
            mtime = self.ams.run(self.instrument, self.optimizer)
            print(f' > Retrieved Guess MT: {mtime:.2f} yrs')
            print(' > Iteration Result: GUESS', end=' ')
            if abs(mtime - cutoff) < epsilon:
                print(f'ACCEPTED')
            elif mtime > cutoff:
                print(f'REJECTED (too optimistic)')
                upper_start = guess
                high_mtime = mtime
            else:
                print(f'REJECTED (too pessimistic)')
                lower = guess
                low_mtime = mtime
            stalled = stalled + 1 if (lower, upper_start) == prev_bracket else 0
            its += 1

        if abs(mtime - cutoff) > epsilon and lower == 0:
            print(f'>> MT target is not realizable: no extra photons permissible ({its} iterations)')
            self.last_search = dict(status='unreachable', lower=0,
                                    upper=upper_start, mtime=mtime, its=its)
            return 0

        print(f'>> Budget CUTOFF found: {int(guess)} ph/s ({its} iterations)')
        self.last_search = dict(status='converged', lower=lower,
                                upper=upper_start, mtime=mtime, its=its)

        if plot_data is None:
            return guess

        catalog_choice = plot_data['cat']
        gradient = plot_data['gradient']

        # Plot-IDs:
        # Hi: 9
        # Lo: 5
        if catalog_choice == 'lo':
            plot_id = 5
        elif catalog_choice == 'hi':
            plot_id = 9
        else:
            raise ValueError(f'Unknown catalog choice: {catalog_choice}')

        # Retrieve data-plot object from AMS
        prev_id = self.ams.plot_id
        self.ams.plot_id = plot_id
        fig, ax = self.ams.run(self.instrument, self.optimizer)
        self.ams.plot_id = prev_id

        # Name the budget family by which end of the band carries the allowance,
        # not by the direction the ramp travels. The two readings are opposite --
        # 'Short-Long' rises towards long wavelengths and is therefore the
        # long-weighted family -- and titles phrased the other way have been
        # misread against their captions.
        family = {'No': 'Flat', 'Short-Long': 'Long-Weighted',
                  'Long-Short': 'Short-Weighted'}.get(gradient, gradient)
        ax.set_title(f'Astrophysical Noise and Error Budget '
                     f'({cutoff} yrs, {family} Budget)')

        # plt.yscale('log')
        ax.set_xlabel('Wavelength (micron)')
        ax.set_ylabel('Noise Contribution (ph s$^{-1}$ micron$^{-1}$)')

        save_path = plot_data.get('save')
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            plt.close(fig)
        else:
            plt.show()

        return guess

    def plot_snr_imagesize_specres(self):
        """
        Scans the SNR sensitivity to the ``image_size`` and ``spec_res`` instrument options.

        For a 10x10 grid of ``spec_res`` in ``[5, 50]`` and ``image_size`` in
        ``[5, 200]``, recomputes ``self.instrument.get_snr()`` and compares the resulting
        ``snr_1h`` column to a reference computed with the instrument's current settings
        (taken to be the high-resolution baseline). Plots the RMSD between the trial and
        reference SNR as a log-scale heatmap, interpolated onto a finer grid, with contour
        lines at RMSD levels of ``1e-2``, ``1e-1`` and ``1``.

        Notes
        -----
        Mutates ``self.instrument.data.options`` (via ``set_manual``) and
        ``self.instrument.data.catalog`` (via ``get_snr()``) as a side effect; the options
        are left at the last grid point evaluated.
        """

        instrument = self.instrument

        specres = np.linspace(5, 50, 10)
        imsize = np.linspace(5, 200, 10)

        full_set = np.empty((10, 10))

        print('>> Starting RES-SIZE trials, getting reference SNRs with high input variables.')
        instrument.get_snr()
        snr_ref = instrument.data.catalog['snr_1h'].to_numpy()
        print(f'>> Reference computed successfully.')

        for i, res in enumerate(specres):
            for j, size in enumerate(imsize):
                print(f'\n>> Iteration {i * 10 + j + 1} / 100: Res: {int(res)}, Size: {int(size)}x{int(size)} :')
                instrument.data.options.set_manual(image_size=int(size), spec_res=int(res))
                instrument.get_snr()
                snr = instrument.data.catalog['snr_1h'].to_numpy()
                rms = np.sqrt(np.mean((snr - snr_ref) ** 2))
                print(f'>> RMSD: {rms}')
                full_set[i, j] = rms

        fig, ax = plt.subplots(1, 1)

        interp = RegularGridInterpolator((np.linspace(5, 200, 10),
                                          np.linspace(5, 50, 10)), full_set, method='slinear')

        X, Y = np.meshgrid(np.linspace(5, 200, 1000), np.linspace(5, 50, 1000))

        grid = interp((X, Y)).T

        im = ax.imshow(grid[::-1], norm=LogNorm(), extent=(5, 200, 5, 50), aspect='auto')

        cbar = fig.colorbar(im, orientation='vertical')

        cbar.set_label('Bulk SNR RSMD')

        ax.set_xlabel('Image Square Length (pixels)')
        ax.set_ylabel('Spectral Resolution')

        contours = plt.contour(X, Y, interp((X, Y)).T, [1e-2, 1e-1, 1], colors='black')
        ax.clabel(contours, manual=True)

        plt.show()

    def plot_limmag_impact_for_impact(self):
        """
        Scans the required mission time over a grid of limiting magnitude and field of regard.

        For a 15x15 grid of K-band limiting magnitudes in ``[8.85, 10.5]`` and fields of
        regard in ``[26, 90]`` degrees, sets ``self.ams.lim_mag``/
        ``self.ams.field_of_regard`` and calls ``self.ams.run()``. Plots the resulting
        mission time as a heatmap (capped at 15 yrs) with contour lines at 5, 7 and 10 yrs.

        Notes
        -----
        Once the mission time exceeds 15 yrs for a given (limiting magnitude, field of
        regard) pair, the remaining, more restrictive fields of regard for that limiting
        magnitude are filled with the same value without being evaluated, since the
        mission time only increases further as the field of regard shrinks.
        """

        ams = self.ams

        RES = 15

        limmag = np.linspace(8.85, 10.5, RES)
        fors = np.linspace(26, 90, RES)
        times = np.empty((RES, RES))

        # x axis: field of regard
        # y axis: limiting magnitude

        for (i, mag) in enumerate(limmag):
            ams.lim_mag = mag
            for (j, forr) in enumerate(fors):
                print(f'\n>> AMS Run No. {i*RES + j + 1} / {RES**2} (M={mag:.2f}mag, FoR={round(forr)}°) :')
                ams.field_of_regard = forr * 2 * np.pi / 360
                time = ams.run(self.instrument, self.optimizer)
                times[i, j] = time
                print(f'>> MT: {time:.2f} yrs')
                if time > 15:
                    print('>> WARNING: MT exceeds 15 yrs, skipping rest of column.')
                    times[i, j:] = time
                    break

        fig, ax = plt.subplots(1, 1)

        im = ax.imshow(times[::-1], extent=(26, 90, 8.85, 10.5), aspect='auto', vmax=15, interpolation='gaussian')

        cbar = fig.colorbar(im, orientation='vertical', extend='max')

        cbar.set_label('Required Mission Time [yrs]')

        ax.set_xlabel('Field of Regard [°]')
        ax.set_ylabel('Limiting Magnitude [mag]')

        contours = plt.contour(fors, limmag, times, [6, 7, 10], colors='black')
        ax.clabel(contours, manual=True)

        plt.title('Limiting Magnitude and Field of Regard vs. Mission Time')

        plt.show()

    def plot_linear_regression_additive(self, save_path=None,
                                        title='Additive TSE with Linear Noise Budget',
                                        grid_out=None, grid_meta=None):
        """
        Scans the required mission time over a grid of linear additive leakage budgets.

        ``title`` overrides the panel title (empty string for none). When
        ``grid_out`` is given, every evaluated grid point is appended to that
        TSV as ``design catalog target_yr short_budget long_budget mtime_yr``
        using the identifying fields of the ``grid_meta`` dict, so the raw
        grid behind the figure is retained.

        Fixes ``self.ams.lim_mag = 7``, ``self.ams.field_of_regard = 65°`` and
        ``self.ams.slew_time = 12 hrs``. For a 15x15 logarithmic grid of "leading"
        (short-wavelength) and "terminating" (long-wavelength) additive leakage levels in
        ``[10**2, 10**4.6]`` ph/s/micron, sets the leakage budget's additive factor to the
        linear function interpolating between these two endpoints across the
        ``[wl_min, wl_max]`` range and calls ``self.ams.run()``. Plots the resulting
        mission time on log-log axes (capped at 10 yrs) with contour lines at 5, 6 and
        8 yrs.

        Notes
        -----
        Once the mission time exceeds 10 yrs for a given leading-budget row, the
        remaining, larger terminating budgets in that row are filled with the same value
        without being evaluated.
        """

        ams = self.ams
        instrument = self.instrument

        RES = 15

        # ASSUMING
        ams.lim_mag = 7
        ams.field_of_regard = 65 * 2 * np.pi / 360
        ams.slew_time = 12 * 60 * 60

        addspace = np.logspace(2, 4.6, RES)

        times = np.empty((RES, RES))

        # x axis: Terminating Addition
        # y axis: Leading Addition

        for (i, leading) in enumerate(addspace):
            for (j, terminating) in enumerate(addspace):
                print(f'\n>> AMS Run No. {i*RES + j + 1} / {RES**2} (Short = {round(leading)} ph/s, '
                      f'Long = {round(terminating)} ph/s) :')
                m = ((terminating - leading) /
                     (instrument.data.options.array['wl_max'] * 1e-6 - instrument.data.options.array['wl_min'] * 1e-6))
                n = terminating - instrument.data.options.array['wl_max'] * 1e-6 * m
                ams.get_leakage_budget().update_factors(
                    additive_factor=lambda args: (m * args[3] + n)
                                                   * instrument.data.inst['wl_bin_widths'] * 1e6)
                time = ams.run(instrument, self.optimizer)
                times[i, j] = time
                print(f'>> MT: {time:.2f} yrs')
                if time > 10:
                    print('>> Notice: MT exceeds 10 yrs, skipping rest of column.')
                    times[i, j:] = time
                    break

        if grid_out is not None:
            meta = grid_meta or {}
            header = not os.path.exists(grid_out)
            with open(grid_out, 'a') as fh:
                if header:
                    fh.write('design\tcatalog\ttarget_yr\tshort_budget\t'
                             'long_budget\tmtime_yr\n')
                for (i, leading) in enumerate(addspace):
                    for (j, terminating) in enumerate(addspace):
                        fh.write(f'{meta.get("design", "?")}\t'
                                 f'{meta.get("catalog", "?")}\t'
                                 f'{meta.get("target_yr", "?")}\t'
                                 f'{leading:.4f}\t{terminating:.4f}\t'
                                 f'{times[i, j]:.4f}\n')

        X, Y = np.meshgrid(addspace, addspace)

        fig, ax = plt.subplots(1, 1)

        im = ax.pcolormesh(X, Y, times, shading='gouraud', vmax=10, cmap=cmo.thermal)

        cbar = fig.colorbar(im, ax=ax, orientation='vertical', extend='max')
        cbar.set_label('Required Mission Time [yrs]')

        ax.set_xscale('log')
        ax.set_yscale('log')

        contours = ax.contour(X, Y, times, levels=[6, 7, 8, 9], colors='black')
        ax.clabel(contours)

        ax.set_xlabel('Long-Wavelength Budget [ph s$^{-1}$ micron$^{-1}$]')
        ax.set_ylabel('Short-Wavelength Budget [ph s$^{-1}$ micron$^{-1}$]')
        if title:
            ax.set_title(title)

        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            plt.close('all')
        else:
            plt.show()

    def plot_cutoff_for_mag(self, MT_goal, save_path=None, resume_from=None):
        """
        Maps the iso-mission-time additive leakage budget over limiting magnitude and
        field of regard.

        Fixes ``self.ams.slew_time = 12 hrs``. For a 15x15 grid of K-band limiting
        magnitudes in ``[6, 9]`` and fields of regard in ``[40, 90]`` degrees (both
        descending), sets ``self.ams.lim_mag``/``self.ams.field_of_regard`` and calls
        :meth:`locate_mission_cutoff` to find the flat additive leakage budget (in
        ph/s/micron) at which the mission time equals ``MT_goal`` years. Plots the
        resulting budget as a heatmap with contour lines at 500, 1000 and 2000
        ph/s/micron, and saves the figure to ``tse_iso_<MT_goal>yrs.png`` in the current
        working directory.

        Parameters
        ----------
        MT_goal : float
            Target mission time, in years, passed to :meth:`locate_mission_cutoff`.

        Notes
        -----
        Each search is upper-bounded by the smallest cutoff found so far for the same
        field of regard at a less restrictive limiting magnitude, since a fainter limiting
        magnitude can only require a smaller (or equal) budget. Once a cutoff of ``0`` is
        found (``MT_goal`` is unreachable even without extra noise), the remaining, more
        restrictive fields of regard for that limiting magnitude are set to ``0`` without
        being evaluated, and this also caps all subsequent (fainter limiting magnitude)
        rows.
        """

        ams = self.ams

        RES = 15

        limmag = np.linspace(6, 9, RES)[::-1]
        fors = np.linspace(40, 90, RES)[::-1]
        cutoffs = np.empty((RES, RES))

        # ASSUMING
        ams.slew_time = 12 * 60 * 60

        # x axis: field of regard
        # y axis: limiting magnitude

        upper_limits = np.ones(RES) * 50_000

        done = recover_scan_progress(resume_from)
        if done:
            print(f'>> Resuming: {len(done)} of {RES**2} grid points recovered from '
                  f'{resume_from}', flush=True)

        j_cutoff = RES
        for (i, mag) in enumerate(limmag):
            ams.lim_mag = mag
            for (j, forr) in enumerate(fors):
                idx = i * RES + j
                print(f'\n>> TSE Run No. {idx + 1} / {RES**2} (M={mag:.2f}mag, FoR={round(forr)}°) :')
                if idx in done:
                    cutoff = done[idx]
                    cutoffs[i, j] = cutoff
                    # Reproduce the state the live path would have left behind.
                    upper_limits[j:][upper_limits[j:] > cutoff] = cutoff
                    if cutoff == 0:
                        j_cutoff = min(j_cutoff, j)
                    print(f'>> Recovered from log: {cutoff:.0f} ph/s')
                    continue
                if j >= j_cutoff:
                    print('>> Impossible to reach MT target, no budget permissible.')
                    cutoffs[i, j] = 0
                    continue
                ams.field_of_regard = forr * 2 * np.pi / 360

                cutoff = self.locate_mission_cutoff(upper_start=upper_limits[j], cutoff=MT_goal)
                cutoffs[i, j] = cutoff
                upper_limits[j:][upper_limits[j:] > cutoff] = cutoff
                if cutoff == 0:
                    print('>> Notice: MT target is impossible to achieve! All more restrictive options are also ruled out.')
                    j_cutoff = j

        fig, ax = plt.subplots(1, 1)

        X, Y = np.meshgrid(fors, limmag)
        im = ax.pcolormesh(X, Y, cutoffs, shading='gouraud', cmap=cmo.thermal)

        cbar = fig.colorbar(im, orientation='vertical')

        cbar.set_label('Iso-MT Budget [ph s$^{-1}$ micron$^{-1}$]')

        ax.set_xlabel('Field of Regard [°]')
        ax.set_ylabel('Limiting Magnitude [mag]')

        contours = plt.contour(fors, limmag, cutoffs, [250, 500, 1000, 2000], colors='black')
        ax.clabel(contours)

        plt.title(f'Lim. Mag. / FoR vs. Iso-MT Budget ({MT_goal} yrs)')

        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            plt.close('all')
        else:
            plt.show()

    def plot_cutoff_for_slewtime(self, MT_goal, save_path=None, resume_from=None):
        """
        Maps the iso-mission-time additive leakage budget over slew time and field of regard.

        Fixes ``self.ams.lim_mag = 7``. For a 15x15 grid of slew times in ``[1, 30]`` hrs
        and fields of regard in ``[40, 90]`` degrees (descending), sets
        ``self.ams.slew_time``/``self.ams.field_of_regard`` and calls
        :meth:`locate_mission_cutoff` to find the flat additive leakage budget (in
        ph/s/micron) at which the mission time equals ``MT_goal`` years. Plots the
        resulting budget as a heatmap with contour lines at 500, 1000 and 2000
        ph/s/micron, and saves the figure to ``tse_iso_<MT_goal>yrs.png`` in the current
        working directory.

        Parameters
        ----------
        MT_goal : float
            Target mission time, in years, passed to :meth:`locate_mission_cutoff`.

        Notes
        -----
        See :meth:`plot_cutoff_for_mag` for the row/column short-circuiting behaviour,
        which is identical except that rows correspond to slew time instead of limiting
        magnitude.
        """

        ams = self.ams

        RES = 15

        # ASSUMING
        ams.lim_mag = 7

        slews = np.linspace(1, 30, RES)
        fors = np.linspace(40, 90, RES)[::-1]
        cutoffs = np.empty((RES, RES))

        # x axis: field of regard
        # y axis: limiting magnitude

        upper_limits = np.ones(RES) * 50_000

        done = recover_scan_progress(resume_from)
        if done:
            print(f'>> Resuming: {len(done)} of {RES**2} grid points recovered from '
                  f'{resume_from}', flush=True)

        j_cutoff = RES
        for (i, slew) in enumerate(slews):
            ams.slew_time = slew * 60 * 60
            for (j, forr) in enumerate(fors):
                idx = i * RES + j
                print(f'\n>> TSE Run No. {idx + 1} / {RES**2} (ST={round(slew)}hrs, FoR={round(forr)}°) :')
                if idx in done:
                    cutoff = done[idx]
                    cutoffs[i, j] = cutoff
                    # Reproduce the state the live path would have left behind.
                    upper_limits[j:][upper_limits[j:] > cutoff] = cutoff
                    if cutoff == 0:
                        j_cutoff = min(j_cutoff, j)
                    print(f'>> Recovered from log: {cutoff:.0f} ph/s')
                    continue
                if j >= j_cutoff:
                    print('>> Impossible to reach MT target, no budget permissible.')
                    cutoffs[i, j] = 0
                    continue
                ams.field_of_regard = forr * 2 * np.pi / 360

                cutoff = self.locate_mission_cutoff(upper_start=upper_limits[j], cutoff=MT_goal)
                cutoffs[i, j] = cutoff
                upper_limits[j:][upper_limits[j:] > cutoff] = cutoff
                if cutoff == 0:
                    print('>> Notice: MT target is impossible to achieve! All more restrictive options are also ruled out.')
                    j_cutoff = j

        fig, ax = plt.subplots(1, 1)

        X, Y = np.meshgrid(fors, slews)
        im = ax.pcolormesh(X, Y, cutoffs, shading='gouraud', cmap=cmo.thermal)

        cbar = fig.colorbar(im, orientation='vertical')

        cbar.set_label('Iso-MT Budget [ph s$^{-1}$ micron$^{-1}$]')

        ax.set_xlabel('Field of Regard [°]')
        ax.set_ylabel('Slew Time [hrs]')

        contours = plt.contour(fors, slews, cutoffs, [500, 1000, 2000], colors='black')
        ax.clabel(contours)

        plt.title(f'Slew Time and Field of Regard vs. Iso-MT Budget ({MT_goal} yrs)')

        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            plt.close('all')
        else:
            # historical default; note plot_cutoff_for_mag documents the same
            # filename, so an explicit save_path is preferable
            plt.savefig(f'tse_iso_{MT_goal}yrs.png')
            plt.show()

    def visualize_filters(self, consider_uninteresting=True):
        """
        Plots the sky distribution of targets and the field-of-regard cuts in an edge-on
        ecliptic projection.

        Calls ``self.ams.run(self.instrument, self.optimizer, pre_select=not
        consider_uninteresting)`` and then, in a polar projection (radius = distance to
        star, angle = ecliptic latitude/longitude), plots the "interesting" stars (those
        falling into at least one configured experiment) split into detected,
        undetected-but-visible and invisible (outside ``lim_mag``/``field_of_regard``),
        and optionally the "uninteresting" stars. Overlays the ecliptic plane, the
        field-of-regard cutoffs and the resulting "zone of avoidance", and annotates the
        fraction of interesting targets lost to the field-of-regard cut.

        Parameters
        ----------
        consider_uninteresting : bool, default True
            If ``True``, ``self.ams.run()`` is called with ``pre_select=False``
            (computing the SNR for the entire catalog) and the "uninteresting" stars are
            also plotted. If ``False``, only the pre-selected "interesting" stars are
            evaluated and plotted, which is considerably faster.
        """

        ams = self.ams

        # Run AMS
        ams.run(self.instrument, self.optimizer, pre_select=not consider_uninteresting)

        # Get catalog
        cat = self.instrument.data.catalog

        # Now go to individual stars. Interesting flag is set by sorting (if there is an interesting planet we take it).
        # This procedure ensures that we have complementary stellar catalogs
        # - an interesting star is not in the non-interesting catalog and vice versa.
        cat = cat.sort_values(['nstar', 'is_interesting'], ascending=[True, False]).groupby('nstar').first()

        exp_stars = cat[cat['is_interesting']]
        not_exp_stars = cat[~cat['is_interesting']]

        def plot_star_pop(cata, **kwargs):

            # Extract distances & latitudes
            dists = cata['distance_s']
            lats = cata['lat']
            lons = cata['lon']

            # Add appropriate symmetry for plotting, not necessary for the maths!
            lats[lons > np.pi] += np.pi

            # Plot!
            ax.scatter(lats, dists, **kwargs)

        # We now a cutoff to use for filtering, too!
        interesting_visible = exp_stars[exp_stars['snr_1h'] > 0]

        int_vis_detected = interesting_visible[interesting_visible['detected']]
        int_vis_undetected = interesting_visible[~interesting_visible['detected']]

        interesting_invisible = exp_stars[exp_stars['snr_1h'] == 0]

        fig = plt.figure()
        ax = fig.add_subplot(projection='polar')

        plot_star_pop(int_vis_detected, color='green', marker='*', s=20,
                      label='Interesting/Visible\n(Detected)', zorder=4)
        plot_star_pop(int_vis_undetected, color='tab:red', marker='D', s=3,
                      label='Interesting/Visible\n(Not Detected)', zorder=3, alpha=0.2)
        plot_star_pop(interesting_invisible, color='black', marker='D', s=2,
                      label='Interesting/Invisible', alpha=0.4,
                      zorder=2)
        if consider_uninteresting:
            plot_star_pop(not_exp_stars, color='black', marker='x', s=6, linewidths=0.7, label='Uninteresting', alpha=0.5,
                          zorder=1)

        distance_fix = [0, 1.05*cat['distance_s'].max()]

        ax.plot([0, 0], distance_fix, color='tab:orange', linestyle='--', linewidth=1, label='Ecliptic Plane',
                zorder=6)
        ax.plot([np.pi, np.pi], distance_fix, color='tab:orange', linestyle='--', linewidth=1, zorder=7)

        cutoff = ams.field_of_regard
        # Cutoff plotting
        for angle in (0, np.pi):
            ax.plot([angle + cutoff, angle + cutoff], distance_fix, color='tab:purple', linestyle='-', linewidth=1.5,
                    zorder=6)

        # Mirrored Edge
        for angle in (0, np.pi):
            ax.plot([np.pi - cutoff + angle, np.pi - cutoff + angle], distance_fix, color='tab:purple',
                    linestyle='-', linewidth=1.5, zorder=6)

        # Create "Kill Area"
        complement = np.pi/2 - cutoff
        for start_point in (np.pi/2, 3 * np.pi / 2):
            angle = np.linspace(start_point - complement, start_point + complement, 1000)
            ax.fill_between(angle, 0, distance_fix[-1],
                            color='tab:purple', alpha=0.4,
                            label='Zone of Avoidance' if start_point == np.pi/2 else None, zorder=5)

        ax.scatter([0], [0], color='tab:orange', s=30, zorder=8)

        ax.yaxis.set_zorder(100)
        ax.legend(loc='lower left', fontsize=8).set_zorder(100)

        target_loss = interesting_invisible.shape[0]/exp_stars.shape[0] * 100
        ax.text(0.5, 0.8, f'Targets Lost:\n{target_loss:.1f}%', transform=ax.transAxes, fontsize=8,
                verticalalignment='bottom', ha='center', va='center', color='black', zorder=100,
                bbox=dict(boxstyle='round', facecolor='tab:orange', alpha=0.85))

        plt.title(f'Yields and Cutoffs ({int(cutoff/(2*np.pi)*360)}° FoR, Lim. Mag. {ams.lim_mag} mag) '
                  f'(Ecliptic Perspective)')

        ax.grid(True, alpha=0.6)

        plt.show()

    def visualize_planet_choice(self):
        """
        Plots the radius-temperature distribution of "interesting" planets and their
        detection status.

        Calls ``self.ams.run(self.instrument, self.optimizer)`` and then scatter-plots the
        "interesting" planets (those falling into at least one configured experiment),
        grouped into detected, undetected-but-visible and invisible (outside
        ``lim_mag``/``field_of_regard``), in the planet radius-temperature plane.
        """

        ams = self.ams

        # Run AMS
        ams.run(self.instrument, self.optimizer)

        # Get catalog
        cat = self.instrument.data.catalog

        # Retrieve planets
        exp_planets = cat[cat['is_interesting']]

        def plot_star_pop(cata, **kwargs):

            # Extract distances & latitudes
            temps = cata['temp_p']
            rads = cata['radius_p']

            # Plot!
            ax.scatter(rads, temps, **kwargs)

        # We now a cutoff to use for filtering, too!
        interesting_visible = exp_planets[exp_planets['snr_1h'] > 0]

        int_vis_detected = interesting_visible[interesting_visible['detected']]
        int_vis_undetected = interesting_visible[~interesting_visible['detected']]

        interesting_invisible = exp_planets[exp_planets['snr_1h'] == 0]

        fig = plt.figure()
        ax = fig.add_subplot()

        plot_star_pop(int_vis_detected, color='green', marker='*', s=0.5,
                      label='Interesting/Visible\n(Detected)', zorder=4)
        plot_star_pop(int_vis_undetected, color='tab:red', marker='D', s=0.5,
                      label='Interesting/Visible\n(Not Detected)', zorder=3, alpha=0.2)
        plot_star_pop(interesting_invisible, color='black', marker='D', s=0.5,
                      label='Interesting/Invisible', alpha=0.4,
                      zorder=2)

        plt.title(f'Planet Yields and Filters ({int(ams.field_of_regard/(2*np.pi)*360)}° FoR, Lim. Mag. {ams.lim_mag} mag)')

        ax.yaxis.set_zorder(100)
        ax.legend(fontsize=8).set_zorder(100)

        ax.set_xlabel('Radius [R$_{Earth}$]')
        ax.set_ylabel('Temperature [K]')

        plt.show()
