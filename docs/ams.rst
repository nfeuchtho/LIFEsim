The Agnostic Mission Simulator
===============================

Overview
--------

The Agnostic Mission Simulator (AMS), implemented in
:class:`lifesim.ams.core.ams.AgnosticMissionSimulator`, is a tool for estimating the total
mission time required by LIFE to complete its search and characterization goals for a given
instrument design, observing strategy and set of *instrumental* error budgets.

It is called "agnostic" because it does not assume any specific hardware implementation.
Instead of modelling a concrete sub-system (e.g. a particular fringe tracker or wavefront
control loop), instrumental imperfections are expressed abstractly as additional noise terms
on top of the purely astrophysical noise (stellar leakage, local zodiacal light, exozodiacal
dust and the planet's own photon noise). These additional terms are described by
:class:`lifesim.ams.core.error_budget.ErrorBudget` objects (see :ref:`ams-error-budgets`
below), which allows the impact of e.g. "X additional photons per second per micron of
leakage at long wavelengths" on the overall mission timeline to be quantified without having
to model where those photons come from.

The AMS sits on top of the regular LIFEsim simulation: it still uses an
:class:`~lifesim.instrument.instrument.Instrument` (for the instrument parameters and target
catalog) and an :class:`~lifesim.optimize.optimizer.Optimizer` with a connected
:class:`~lifesim.optimize.ahgs.AhgsModule` (for distributing the available search time between
targets). It does, however, use its own, vectorized implementation of the SNR computation
(:meth:`~lifesim.ams.core.ams.AgnosticMissionSimulator.get_snr`) rather than
``instrument.get_snr()``, since it needs to be re-evaluated many times when scanning over
error budgets, instrument parameters or strategy choices.

Setting Up the AMS
------------------

As with a regular LIFEsim simulation, start by creating a :class:`~lifesim.core.core.Bus`,
adding an :class:`~lifesim.instrument.instrument.Instrument`, the noise modules, a
:class:`~lifesim.instrument.transmission.TransmissionMap`, an
:class:`~lifesim.optimize.optimizer.Optimizer` and an
:class:`~lifesim.optimize.ahgs.AhgsModule`, and connecting and configuring them as described in
:doc:`example`. Settings can also be loaded from a YAML configuration file (see
``lifesim/ams/settings.yaml`` for a complete example) using

.. code-block:: python

    bus.build_from_config(filename='settings.yaml')

The catalog is loaded as usual, e.g. with ``bus.data.catalog_from_ppop(...)``.

The most important options for the AMS are found in ``bus.data.options.optimization``,
in particular ``'experiments'`` (the named target samples used both to pre-select interesting
targets and to size the characterization follow-up campaigns), ``'snr_target'``,
``'snr_char'`` and ``'n_orbits'``. See :class:`lifesim.util.options.Options` for a full
description of all available options.

Once the bus is set up, create the AMS itself

.. code-block:: python

    import numpy as np
    from lifesim import AgnosticMissionSimulator

    ams = AgnosticMissionSimulator(
        nulling_order=2,           # order of the nulling interferometer
        lim_mag=7.0,                # limiting K-band magnitude
        field_of_regard=65 / 360 * 2 * np.pi,  # half-opening angle around the ecliptic poles, in rad
        science_overhead=0.8,       # fraction of search time spent integrating (`t_efficiency`)
        slew_time=12 * 60 * 60,      # slew time between targets, in s (`t_slew`)
        verbose=True,
    )

The constructor arguments ``science_overhead`` and ``slew_time`` are written into
``instrument.data.options.array['t_efficiency']`` and
``instrument.data.options.array['t_slew']`` respectively the first time
:meth:`~lifesim.ams.core.ams.AgnosticMissionSimulator.run` is called.

.. _ams-error-budgets:

Error Budgets
-------------

A :class:`~lifesim.ams.core.error_budget.ErrorBudget` describes how an astrophysical noise
contribution :math:`N_{\mathrm{astro}}` (e.g. the photon flux leaking through the nuller from
the host star) is modified by instrumental effects:

.. math::

    N_{\mathrm{tot}} = N_{\mathrm{astro}} \cdot f_{\mathrm{mult}} + f_{\mathrm{add}}

where ``f_mult`` and ``f_add`` are user-supplied functions of
``(hz_center, distance_s, <noise-specific argument>, wl_bins)``. By default both factors are
the identity (``f_mult = 1``, ``f_add = 0``), i.e. the budget has no effect.

The AMS holds one error budget for each of the following noise contributions, which can be
passed to its constructor (each defaults to a no-op budget if omitted):

============================ ============================================================
Constructor argument          Applied to
============================ ============================================================
``leakage_budget``             Stellar leakage (the residual starlight passing the nuller)
``localzodi_budget``           Local zodiacal light
``exozodi_budget``              Exozodiacal dust around the target star
``planet_signal_budget``        The planet's signal flux
``planet_noise_budget``          Photon noise from the planet itself
============================ ============================================================

For example, to add a constant 500 ph/s/micron of additional leakage noise across all
wavelengths

.. code-block:: python

    from lifesim import ErrorBudget

    widths = bus.data.inst['wl_bin_widths'] * 1e6  # bin widths in micron

    leakage_budget = ErrorBudget(
        additive_factor=lambda args: 500 * widths
    )

    ams = AgnosticMissionSimulator(
        nulling_order=2, lim_mag=7.0,
        field_of_regard=65 / 360 * 2 * np.pi,
        science_overhead=0.8, slew_time=12 * 60 * 60,
        leakage_budget=leakage_budget,
    )

The argument tuple ``args`` passed to ``additive_factor``/``multiplicative_factor`` is
``(hz_center, distance_s, <extra>, wl_bins)``, where ``<extra>`` is the planet's host-star
radius for the leakage budget, the ecliptic latitude for the local-zodi budget, the host
star's luminosity for the exozodi budget, and the planet's angular separation for the planet
signal/noise budgets.

Once the AMS has been constructed, an existing budget can also be replaced at runtime via

.. code-block:: python

    ams.get_leakage_budget().update_factors(
        additive_factor=lambda args: 1000 * widths
    )

Calling :meth:`~lifesim.ams.core.error_budget.ErrorBudget.update_factors` (or
:meth:`~lifesim.ams.core.ams.AgnosticMissionSimulator.set_nulling_order`) automatically
invalidates the AMS' cached SNR array, so the next
:meth:`~lifesim.ams.core.ams.AgnosticMissionSimulator.run` call recomputes the SNR for the
whole catalog. Changing other AMS attributes directly (``lim_mag``, ``field_of_regard``,
``slew_time``, ``science_overhead``) does *not* require recomputing the SNR, since they only
affect the filtering and time-allocation steps - this makes scans over the limiting magnitude
or field of regard considerably faster than scans over the error budgets.

Running the AMS
----------------

With the bus, instrument, optimizer and AMS set up, run the simulation with

.. code-block:: python

    mission_time = ams.run(instrument, opt)

:meth:`~lifesim.ams.core.ams.AgnosticMissionSimulator.run` performs the following steps:

1. Applies the instrument options and, if ``pre_select=True`` (the default), reduces the
   catalog to the targets that fall into at least one of the configured
   ``optimization['experiments']``. This significantly speeds up the SNR calculation but means
   the SNR is *not* available for targets outside of these experiments. Set
   ``pre_select=False`` to compute the SNR for the entire catalog.
2. Computes the one-hour SNR (and the SNR at maximum angular separation, used for
   characterization) for every remaining target via
   :meth:`~lifesim.ams.core.ams.AgnosticMissionSimulator.get_snr`. If
   ``bus.data.options.other['n_cpu'] > 1``, this step is parallelized across CPU cores by
   splitting the catalog into balanced groups of stars.
3. Filters out stars that are fainter than ``lim_mag`` (K-band) or lie outside the
   ``field_of_regard``.
4. Calls ``opt.ahgs()`` to greedily distribute the available search time
   (``optimization['t_search'] * array['t_efficiency']``) between targets.
5. For every detected, "interesting" target, determines whether it is followed up for orbit
   determination (``optimization['n_orbits']`` visits) and, if
   ``optimization['characterization']`` is enabled, spectral characterization
   (``optimization['snr_char']``), and accumulates the corresponding time.
6. Builds a per-universe time sheet of detection, orbit-determination and characterization
   time, and returns the **90th percentile of the total mission time across all simulated
   universes, in years**.

The catalog (``instrument.data.catalog``/``bus.data.catalog``) is updated in place with the
columns ``'snr_1h'``, ``'maxsep_snr_1h'``, ``'is_interesting'``, ``'exp_<name>'`` (one boolean
column per experiment), ``'detected'``, ``'t_detected'``, ``'follow_up'``, ``'t_orbit'`` and
``'t_char'``, which can be used for further analysis as described in the *Interpreting
Results* section of :doc:`example`.

Because the SNR array is cached on the AMS instance
(:attr:`~lifesim.ams.core.ams.AgnosticMissionSimulator.snr_saved`), repeatedly calling
:meth:`~lifesim.ams.core.ams.AgnosticMissionSimulator.run` after only changing ``lim_mag``,
``field_of_regard`` or the ``optimization`` settings is comparatively cheap. This is
exploited by :class:`~lifesim.ams.plotter.TradeSpaceExplorer` (see
:ref:`ams-trade-space-exploration` below), e.g. its
:meth:`~lifesim.ams.plotter.TradeSpaceExplorer.locate_mission_cutoff` method, which performs a
root-finding search over an error budget to find the value at which a target mission time is
reached, and its
:meth:`~lifesim.ams.plotter.TradeSpaceExplorer.plot_limmag_impact_for_impact`/
:meth:`~lifesim.ams.plotter.TradeSpaceExplorer.plot_cutoff_for_slewtime` methods, which scan the
mission time or an error-budget cutoff over grids of limiting magnitude, field of regard or
slew time.

The AHGS Optimizer
-------------------

Step 4 above is performed by :meth:`lifesim.optimize.optimizer.Optimizer.ahgs`, which delegates
the actual time allocation to a connected :class:`~lifesim.optimize.ahgs.AhgsModule`
(``lifesim/optimize/ahgs.py``, exported as :class:`lifesim.AhgsModule`). At each iteration, the
AHGS ("A Heuristic Greedy Scheduler") algorithm picks the star/planet observation that yields
the best SNR-per-time ratio, accumulates the corresponding integration (and, in characterization
mode, slew and characterization) time, and repeats until the search time budget is exhausted.

The production implementation precomputes, once in ``distribute_time``, a per-star NumPy index
array (``_star_rows``) into the catalog. Each iteration then:

1. Calls ``obs_array_star`` for every star, which operates purely on the precomputed
   ``_star_rows`` slices (no pandas ``.loc``/boolean-mask scans of the full catalog) to build a
   cost matrix of shape ``(n_stars, [2,] max_occurrence)`` (the extra leading dimension of 2 is
   used in characterization mode to track detection vs. characterization cost separately).
2. Runs a single global ``np.argmin`` over this cost matrix to select the next star/planet to
   observe.
3. Calls ``observe_star`` to update that star's bookkeeping and accumulated time.

Legacy and Reference Implementations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``lifesim/optimize/`` also contains several non-production AHGS implementations, kept for
benchmarking and correctness comparisons. None of these are imported by
``lifesim/__init__.py`` or used by the AMS:

============================ ================================================================
Module                         Description
============================ ================================================================
``ahgs_queue.py``               Previous production implementation. Same pandas-free per-star
                                 NumPy bookkeeping as ``ahgs.py``, but selects the next
                                 observation via a heap-based priority queue
                                 (:class:`~lifesim.optimize.observation_queue.ObservationQueue`)
                                 instead of ``np.argmin``.
``ahgs_arr.py``                  Older pandas-based argmin/array implementation, predating the
                                  per-star NumPy bookkeeping.
``ahgs_ref.py``                  Original pre-optimization pandas baseline (``AhgsModuleRef``),
                                  using the heap-based ``ObservationQueue``.
``observation_queue.py``         Shared :class:`~lifesim.optimize.observation_queue.ObservationQueue`
                                  heap implementation used by ``ahgs_queue.py`` and ``ahgs_ref.py``.
============================ ================================================================

**Why ``np.argmin`` over a heap:** ``ahgs.py`` (argmin-based) was benchmarked against
``ahgs_queue.py`` (heap-based) on synthetic catalogs matching the real ``nstar``/``nuniverse``
distributions of ``catalog_hab2lo.txt`` and ``catalog_hab2hi.txt``, in characterization mode,
over roughly 6000 optimization iterations. Results were bit-identical between the two
(``snr_current``, ``detected``, ``t_detected``, etc. all matched exactly):

============================ ================== ========================== ========
Catalog scale                  ``ahgs_queue.py``   ``ahgs.py`` (production)   Speedup
============================ ================== ========================== ========
N=32k, max_occurrence~200       1.96 s              0.37 s                    5.3x
N=486k, max_occurrence=231       5.0 s              2.8 s                     1.8x
(hab2lo, full catalog)
N=730k, max_occurrence=541       8.7 s              4.0 s                     2.2x
(hab2hi, full catalog)
============================ ================== ========================== ========

The argmin approach wins because, in characterization mode, requeuing a star after an
observation requires up to ``max_occurrence`` (231-541 in these catalogs) individual
Python-level ``heapq`` push operations, whereas the argmin approach only performs a single
vectorized ``np.argmin`` call per iteration. Future contributors should be aware of this before
re-introducing a priority queue into the production path for "optimization" purposes.

.. note::

   The benchmark above used a single-experiment configuration with
   ``optimization['characterization'] = True`` and ``optimization['opt_limit'] = 'experiments'``.
   Non-characterization mode, ``opt_limit = 'time'``, and the multi-experiment "RECOUNTING"
   rebuild path were not separately stress-tested, although the relevant code paths are shared
   with / structurally identical to the previously-validated ``ahgs.py``/``ahgs_arr.py``
   comparison.

Diagnostic Plotting
~~~~~~~~~~~~~~~~~~~~

Passing a ``plot_id`` to the :class:`~lifesim.ams.core.ams.AgnosticMissionSimulator`
constructor switches :meth:`~lifesim.ams.core.ams.AgnosticMissionSimulator.get_snr` into a
diagnostic mode: as soon as it reaches the star hosting the planet at catalog row ``plot_id``,
it plots a breakdown of the astrophysical noise, the additional noise introduced by the error
budgets, and the individual stellar leakage / local zodi / exozodi contributions as a function
of wavelength, then exits. This is useful for visually inspecting the effect of an error
budget on a single target, but ``plot_id`` should be left as ``None`` (the default) for
production AMS runs.

.. _ams-trade-space-exploration:

Trade Space Exploration
-------------------------

``lifesim/ams/plotter.py`` provides
:class:`~lifesim.ams.plotter.TradeSpaceExplorer`, a collection of plotting and
root-finding methods built around repeated calls to
:meth:`~lifesim.ams.core.ams.AgnosticMissionSimulator.run`. A
:class:`~lifesim.ams.plotter.TradeSpaceExplorer` is constructed once from the AMS,
optimizer and instrument

.. code-block:: python

    from lifesim import TradeSpaceExplorer

    tse = TradeSpaceExplorer(ams, opt, instrument)

so that the individual exploration methods only need the parameters specific to the
scan they perform, e.g.

.. code-block:: python

    tse.visualize_planet_choice()
    tse.visualize_filters()

    tse.plot_limmag_impact_for_impact()
    tse.plot_linear_regression_additive()

    cutoff = tse.locate_mission_cutoff(cutoff=10, upper_start=50_000)

    tse.plot_cutoff_for_mag(MT_goal=7)
    tse.plot_cutoff_for_slewtime(MT_goal=7)

The available methods are

============================================================== ============================================================
Method                                                          Description
============================================================== ============================================================
:meth:`~lifesim.ams.plotter.TradeSpaceExplorer.locate_mission_cutoff`
                                                                 Root-finding search for the additive leakage budget at
                                                                 which the mission time matches a target value.
:meth:`~lifesim.ams.plotter.TradeSpaceExplorer.plot_snr_imagesize_specres`
                                                                 SNR sensitivity to ``image_size``/``spec_res``.
:meth:`~lifesim.ams.plotter.TradeSpaceExplorer.plot_limmag_impact_for_impact`
                                                                 Mission time vs. limiting magnitude and field of regard.
:meth:`~lifesim.ams.plotter.TradeSpaceExplorer.plot_linear_regression_additive`
                                                                 Mission time vs. a linear additive leakage gradient.
:meth:`~lifesim.ams.plotter.TradeSpaceExplorer.plot_cutoff_for_mag`
                                                                 Iso-mission-time leakage budget vs. limiting magnitude and
                                                                 field of regard.
:meth:`~lifesim.ams.plotter.TradeSpaceExplorer.plot_cutoff_for_slewtime`
                                                                 Iso-mission-time leakage budget vs. slew time and field of
                                                                 regard.
:meth:`~lifesim.ams.plotter.TradeSpaceExplorer.visualize_filters`
                                                                 Sky distribution of targets and field-of-regard cuts.
:meth:`~lifesim.ams.plotter.TradeSpaceExplorer.visualize_planet_choice`
                                                                 Radius-temperature distribution of selected planets.
============================================================== ============================================================

Several methods (:meth:`~lifesim.ams.plotter.TradeSpaceExplorer.plot_limmag_impact_for_impact`,
:meth:`~lifesim.ams.plotter.TradeSpaceExplorer.plot_linear_regression_additive`,
:meth:`~lifesim.ams.plotter.TradeSpaceExplorer.plot_cutoff_for_mag` and
:meth:`~lifesim.ams.plotter.TradeSpaceExplorer.plot_cutoff_for_slewtime`) directly modify
``ams.lim_mag``, ``ams.field_of_regard``, ``ams.slew_time`` and/or the AMS' error budgets as
they scan through the trade space, so the AMS is left in the state of the last grid point
evaluated.


API Documentation
------------------

lifesim.ams.core.ams module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lifesim.ams.core.ams
   :members:
   :undoc-members:
   :show-inheritance:

lifesim.ams.core.error_budget module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lifesim.ams.core.error_budget
   :members:
   :undoc-members:
   :show-inheritance:

lifesim.ams.plotter module
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lifesim.ams.plotter
   :members:
   :undoc-members:
   :show-inheritance:
