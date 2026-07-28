"""Throughput-normalized null-order ablation.

The sin^n null-order proxy charges order four nothing for its throughput:
`eff_tot` and the collecting area are identical between orders (ams.py:797-798),
so the only order dependence is the sin^n shape at ams.py:751. A physical
fourth-order nuller also loses light in the beam combiner -- Guyon et al.
(2013), Sec. 1, quote a theta^4 null on 25 % of the incident light against
theta^2 on 50 %.

This script re-runs the iso-mission-time endpoint search in two arms:

    control    throughput 0.15   (as reported in the thesis)
    penalized  throughput 0.075  (Guyon factor 0.5 applied to eff_tot)

Question answered: does the spectral-preference reversal of Sec. 5.6 survive
when order four is charged its throughput penalty, or is it an artifact of the
unnormalized proxy? Both arms are run on the same commit and the same
environment, so the comparison does not rely on previously reported numbers.

`N_I` is defined at the pre-efficiency reference plane, so scaling `eff_tot`
scales the delivered instrumental noise consistently with the signal and the
astrophysical background; the comparison stays at a single reference plane.

Deliberately not varied (one variable at a time): the baseline prescription
constant 0.589645 (ams.py:114-122) is derived for a second-order double
Bracewell and is retained at order four, so neither arm is baseline-optimal.

Usage, from anywhere (LIFEsim must be pip-installed, `pip install -e . --no-deps`):

    python -m lifesim.ams.ablation_throughput                 # full matrix
    python -m lifesim.ams.ablation_throughput --catalog hi    # one catalog
    python -m lifesim.ams.ablation_throughput --null-order 2  # order-2 reference

Every endpoint is appended to thesis/reproducibility/ablation_throughput.tsv as
soon as it is found, so a partial run is still usable.
"""

import argparse
import os
import time
from datetime import datetime, timezone

import matplotlib
matplotlib.use('Agg')  # headless: never block on a figure window

import numpy as np

_CWD = os.getcwd()
import lifesim
from lifesim import TradeSpaceExplorer, AgnosticMissionSimulator, ErrorBudget
os.chdir(_CWD)  # LIFEsim changes the working directory on import

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
CATALOG_DIR = os.path.join(REPO_ROOT, 'lifesim', 'catalogs')
RESULTS = os.path.join(REPO_ROOT, 'thesis', 'reproducibility',
                       'ablation_throughput.tsv')

# Guyon et al. (2013) Sec. 1: theta^4 null on 25 % of the light, theta^2 on 50 %.
ARMS = {'control': 0.15, 'penalized': 0.075}

# Budget families, keyed by the gradient mode `runner.py` uses.
#
# CAUTION -- the runner's names describe the direction the ramp travels, not
# which end of the band carries the weight, and the two readings are opposite.
# With m and n as set in `make_setter` (wl_min = 4 um, wl_max = 18.5 um):
#
#   'Short-Long'  ->  0 at wl_min, `budget` at wl_max  ->  LONG-weighted
#   'Long-Short'  ->  `budget` at wl_min, 0 at wl_max  ->  SHORT-weighted
#
# The labels written to the results file are the physical ones (which end
# carries the allowance), since that is what the thesis text compares.
FAMILIES = {'No': 'flat', 'Short-Long': 'long_weighted', 'Long-Short': 'short_weighted'}

# mission-time targets per catalog, matching thesis/reproducibility/run_matrix
TARGETS = {'hi': [5.5, 6.0], 'lo': [7.5, 8.0]}

COLUMNS = ('timestamp arm catalog null_order mtime_target_yr budget_family '
           'throughput eff_tot endpoint_ph_s_um mtime_achieved_yr residual_yr '
           'wall_s').split()


def build_bus(catalog, throughput):
    """Assemble the bus as runner.py does, overriding `throughput` before
    `apply_options()` computes eff_tot = quantum_eff * throughput
    (instrument.py:94)."""
    cat_pth = os.path.join(CATALOG_DIR, f'catalog_hab2{catalog}.txt')
    if not os.path.exists(cat_pth):
        raise FileNotFoundError(cat_pth)

    bus = lifesim.Bus()
    bus.data.options.set_scenario('baseline')
    bus.data.catalog_from_ppop(input_path=cat_pth)

    os.chdir(HERE)  # build_from_config reads settings.yaml relative to cwd
    bus.build_from_config(filename='settings.yaml')
    bus.data.options.array['throughput'] = throughput

    instrument = lifesim.Instrument(name='inst')
    transm = lifesim.TransmissionMap(name='transm')
    exo = lifesim.PhotonNoiseExozodi(name='exo')
    local = lifesim.PhotonNoiseLocalzodi(name='local')
    star = lifesim.PhotonNoiseStar(name='star')
    opt = lifesim.Optimizer(name='opt')
    ahgs = lifesim.AhgsModule(name='ahgs')
    for module in (instrument, transm, exo, local, star, opt, ahgs):
        bus.add_module(module)

    for pair in [('inst', 'transm'), ('inst', 'exo'), ('inst', 'local'),
                 ('inst', 'star'), ('star', 'transm')]:
        bus.connect(pair)
    instrument.apply_options()
    for pair in [('transm', 'opt'), ('inst', 'opt'), ('opt', 'ahgs')]:
        bus.connect(pair)

    return bus, instrument, opt


def make_setter(bus, ams, gradient, widths):
    """Budget shapes as in runner.py: flat, or a linear ramp anchored at zero on
    one end of the band."""
    wl_max = bus.data.options.array['wl_max'] * 1e-6
    wl_min = bus.data.options.array['wl_min'] * 1e-6

    def setter(budget):
        if gradient == 'Short-Long':
            m = budget / (wl_max - wl_min)
            n = budget - wl_max * m
        elif gradient == 'Long-Short':
            m = -budget / (wl_max - wl_min)
            n = -wl_max * m
        else:  # 'No'
            m, n = 0, budget
        ams.get_leakage_budget().update_factors(
            additive_factor=lambda args: (m * args[3] + n) * widths)

    return setter


def append_row(row):
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    new = not os.path.exists(RESULTS)
    with open(RESULTS, 'a', encoding='utf8') as fh:
        if new:
            fh.write('\t'.join(COLUMNS) + '\n')
        fh.write('\t'.join(str(x) for x in row) + '\n')


SWEEP_RESULTS = os.path.join(REPO_ROOT, 'thesis', 'reproducibility',
                             'throughput_sweep.tsv')
SWEEP_COLUMNS = ('timestamp catalog null_order throughput eff_tot '
                 'mtime_zero_budget_yr wall_s').split()
SWEEP_THROUGHPUTS = [0.15, 0.125, 0.10, 0.075]


def run_sweep(catalogs, null_orders, throughputs):
    """Mission time at zero added budget as a function of total throughput.

    No endpoint search: one plain AMS evaluation per point. This isolates the
    throughput sensitivity of the mission-time model itself, independently of
    any noise allowance, and gives the zero-budget baselines against which the
    penalized arm of the ablation must be read.
    """
    for catalog in catalogs:
        for throughput in throughputs:
            bus, instrument, opt = build_bus(catalog, throughput)
            eff_tot = bus.data.inst['eff_tot']
            for order in null_orders:
                ams = AgnosticMissionSimulator(
                    order, 7, 65 / 360 * 2 * np.pi, 0.8, 12 * 60 * 60,
                    verbose=False)
                t0 = time.time()
                mtime = ams.run(instrument, opt)
                wall = round(time.time() - t0, 1)
                print(f'>> hab2{catalog} | order {order} | throughput '
                      f'{throughput} | {mtime:.4f} yr ({wall} s)', flush=True)

                os.makedirs(os.path.dirname(SWEEP_RESULTS), exist_ok=True)
                new = not os.path.exists(SWEEP_RESULTS)
                with open(SWEEP_RESULTS, 'a', encoding='utf8') as fh:
                    if new:
                        fh.write('\t'.join(SWEEP_COLUMNS) + '\n')
                    fh.write('\t'.join(str(x) for x in [
                        datetime.now(timezone.utc).isoformat(timespec='seconds'),
                        f'hab2{catalog}', order, throughput, eff_tot,
                        round(mtime, 6), wall]) + '\n')
    print(f'\nSweep results: {SWEEP_RESULTS}', flush=True)


DEFECT_RESULTS = os.path.join(REPO_ROOT, 'thesis', 'reproducibility',
                              'localzodi_defect_impact.tsv')
DEFECT_COLUMNS = ('timestamp catalog null_order config localzodi_scale '
                  'mtime_zero_budget_yr mtime_target_yr flat_endpoint_ph_s_um '
                  'wall_s').split()

# The pre-correction local-zodiacal path averaged the transmission over the whole
# square evaluation grid and then multiplied by the circular solid angle,
# suppressing the uniform foreground by pi/4 in the uniform-domain limit.
# Multiplying the corrected term by pi/4 restores that behaviour to within the
# margin by which the realized ratio (~1.267, the corner flux admitted by the
# square domain) differs from 4/pi = 1.2732, so the two configurations differ in
# the defect and in nothing else of consequence.
PI_OVER_4 = np.pi / 4.0
DEFECT_CONFIGS = {'corrected': 1.0, 'pre_correction': PI_OVER_4}

# primary mission-time target per catalog, as reported in the thesis
PRIMARY_TARGET = {'hi': 5.5, 'lo': 7.5}


def run_defect_impact(catalogs, null_orders, upper_start):
    """What the inherited local-zodiacal normalization defect was worth.

    Reports, for each catalog and null order, the mission time required with no
    added budget and the largest tolerated flat allowance, computed once with the
    corrected local-zodiacal normalization and once with the pre-correction one.
    The difference converts the known median SNR shift into the quantities the
    thesis actually reports.
    """
    for catalog in catalogs:
        bus, instrument, opt = build_bus(catalog, ARMS['control'])
        widths = bus.data.inst['wl_bin_widths'] * 1e6
        target = PRIMARY_TARGET[catalog]

        for order in null_orders:
            for config, scale in DEFECT_CONFIGS.items():
                ams = AgnosticMissionSimulator(
                    order, 7, 65 / 360 * 2 * np.pi, 0.8, 12 * 60 * 60,
                    verbose=False)
                if scale != 1.0:
                    ams.get_localzodi_budget().update_factors(
                        multiplicative_factor=lambda args, s=scale: s)

                t0 = time.time()
                mtime_zero = ams.run(instrument, opt)

                tse = TradeSpaceExplorer(ams, opt, instrument)
                endpoint = tse.locate_mission_cutoff(
                    target, upper_start=upper_start,
                    setter_func=make_setter(bus, ams, 'No', widths),
                    plot_data=None)
                wall = round(time.time() - t0, 1)

                print(f'>> hab2{catalog} | order {order} | {config}: '
                      f'zero-budget {mtime_zero:.4f} yr | flat endpoint '
                      f'{endpoint} ph/s/um at {target} yr ({wall} s)', flush=True)

                os.makedirs(os.path.dirname(DEFECT_RESULTS), exist_ok=True)
                new = not os.path.exists(DEFECT_RESULTS)
                with open(DEFECT_RESULTS, 'a', encoding='utf8') as fh:
                    if new:
                        fh.write('\t'.join(DEFECT_COLUMNS) + '\n')
                    fh.write('\t'.join(str(x) for x in [
                        datetime.now(timezone.utc).isoformat(timespec='seconds'),
                        f'hab2{catalog}', order, config, round(scale, 6),
                        round(mtime_zero, 6), target, endpoint, wall]) + '\n')
    print(f'\nDefect-impact results: {DEFECT_RESULTS}', flush=True)


BACKGROUND_RESULTS = os.path.join(REPO_ROOT, 'thesis', 'reproducibility',
                                  'background_context.tsv')


class _RecordingBudget(ErrorBudget):
    """An ErrorBudget that records the astrophysical term handed to it.

    The AMS accepts externally supplied budgets, so this captures the background
    spectra without modifying the simulator. Factors are left at their defaults,
    so the recorded run is identical to an ordinary zero-budget run.
    """

    def __init__(self, store, key):
        super().__init__()
        self._store = store
        self._key = key

    def evaluate(self, astro, *args):
        self._store.setdefault(self._key, []).append(np.asarray(astro, dtype=float))
        return super().evaluate(astro, *args)


def run_background_context(catalogs, null_orders):
    """Astrophysical background spectral density, for scale against N_I.

    Reports the median over catalog stars of the stellar-leakage, local-zodiacal
    and exozodiacal terms, converted to ph/s/micron at the same pre-efficiency
    single-output plane as the reported allowance, so the two are directly
    comparable.
    """
    from lifesim.util.combiner import double_bracewell, double_triple_nuller
    rows = []
    for catalog in catalogs:
        bus, instrument, opt = build_bus(catalog, ARMS['control'])
        # The SNR flow is dispatched to worker processes when n_cpu > 1
        # (ams.py:307), and the recording budgets below would then fill a dict in
        # the child rather than here. One evaluation is cheap; run it in-process.
        bus.data.options.other['n_cpu'] = 1
        wl_bins = np.asarray(bus.data.inst['wl_bins']) * 1e6          # micron
        widths = np.asarray(bus.data.inst['wl_bin_widths']) * 1e6     # micron

        ratio = bus.data.options.array['ratio']
        for order in null_orders:
            store = {}
            # Drive this from the same realizable architectures the results use.
            # Without an architecture the AMS falls back to the sin^n null-order
            # proxy, whose far-field average is 3/16 at order four against the
            # triple nuller's 1/6, so the reported background would not be the
            # background the reported allowances were measured against.
            arch = (double_bracewell(1.0, ratio) if order == 2
                    else double_triple_nuller(1.0, ratio))
            ams = AgnosticMissionSimulator(
                order, 7, 65 / 360 * 2 * np.pi, 0.8, 12 * 60 * 60, verbose=False,
                architecture=arch,
                leakage_budget=_RecordingBudget(store, 'star'),
                localzodi_budget=_RecordingBudget(store, 'localzodi'),
                exozodi_budget=_RecordingBudget(store, 'exozodi'))
            ams.run(instrument, opt)

            comp = {}
            for key in ('star', 'localzodi', 'exozodi'):
                stacked = np.concatenate([a.reshape(-1, len(widths))
                                          for a in store.get(key, [])], axis=0)
                comp[key] = np.median(stacked, axis=0) / widths   # ph/s/micron
            total = comp['star'] + comp['localzodi'] + comp['exozodi']

            for j, wl in enumerate(wl_bins):
                rows.append([f'hab2{catalog}', order, round(float(wl), 3),
                             round(float(comp['star'][j]), 4),
                             round(float(comp['localzodi'][j]), 4),
                             round(float(comp['exozodi'][j]), 4),
                             round(float(total[j]), 4)])

            band = float(np.sum(total * widths) / np.sum(widths))
            print(f'>> hab2{catalog} order {order}: band-averaged astrophysical '
                  f'background {band:.1f} ph/s/micron; at 10 um '
                  f'{float(total[np.argmin(abs(wl_bins - 10))]):.1f}', flush=True)

    os.makedirs(os.path.dirname(BACKGROUND_RESULTS), exist_ok=True)
    with open(BACKGROUND_RESULTS, 'w', encoding='utf8') as fh:
        fh.write('catalog\tnull_order\twl_um\tstar\tlocalzodi\texozodi\ttotal\n')
        for r in rows:
            fh.write('\t'.join(str(x) for x in r) + '\n')
    print(f'\nBackground context: {BACKGROUND_RESULTS}', flush=True)


BREAKEVEN_RESULTS = os.path.join(REPO_ROOT, 'thesis', 'reproducibility',
                                 'breakeven_throughput.tsv')


def run_breakeven(catalogs, tol=2e-4):
    """Throughput at which a fourth-order null stops paying for itself.

    Solves t_4(tau) = t_2(tau_nominal) for tau, both at zero added budget. The
    result is the throughput a fourth-order architecture must retain for its
    deeper null to shorten the mission at all, and it can be compared directly
    against the output efficiency of any proposed combiner.

    `run()` calls `instrument.apply_options()`, which recomputes eff_tot from
    the options, so the throughput can be varied without rebuilding the bus.
    """
    rows = []
    for catalog in catalogs:
        bus, instrument, opt = build_bus(catalog, ARMS['control'])
        nominal = ARMS['control']

        def mtime(order, tau):
            bus.data.options.array['throughput'] = tau
            ams = AgnosticMissionSimulator(order, 7, 65 / 360 * 2 * np.pi, 0.8,
                                           12 * 60 * 60, verbose=False)
            return float(ams.run(instrument, opt))

        t_ref = mtime(2, nominal)
        lo, hi = 0.05, nominal          # f(lo) > 0, f(hi) < 0
        f_hi = mtime(4, hi) - t_ref
        f_lo = mtime(4, lo) - t_ref
        print(f'hab2{catalog}: order-2 reference {t_ref:.4f} yr | '
              f'order-4 at tau={hi} is {f_hi:+.4f} yr, at tau={lo} is {f_lo:+.4f} yr',
              flush=True)
        if f_hi > 0 or f_lo < 0:
            print('>> break-even not bracketed; skipping', flush=True)
            continue

        it = 0
        while hi - lo > tol:
            mid = 0.5 * (lo + hi)
            if mtime(4, mid) - t_ref > 0:
                lo = mid
            else:
                hi = mid
            it += 1
        tau_star = 0.5 * (lo + hi)
        retention = tau_star / nominal
        print(f'>> hab2{catalog}: break-even throughput {tau_star:.5f} '
              f'({100*retention:.1f}% of nominal) after {it} bisections', flush=True)
        rows.append([f'hab2{catalog}', round(t_ref, 6), round(tau_star, 6),
                     round(retention, 5), it])

    os.makedirs(os.path.dirname(BREAKEVEN_RESULTS), exist_ok=True)
    with open(BREAKEVEN_RESULTS, 'w', encoding='utf8') as fh:
        fh.write('catalog\tmtime_order2_nominal_yr\tbreakeven_throughput\t'
                 'retention_fraction\tbisections\n')
        for r in rows:
            fh.write('\t'.join(str(x) for x in r) + '\n')
    print(f'\nBreak-even results: {BREAKEVEN_RESULTS}', flush=True)


SNRSHIFT_RESULTS = os.path.join(REPO_ROOT, 'thesis', 'reproducibility',
                                'localzodi_snr_shift.tsv')


def run_snr_shift(catalogs, null_orders):
    """Catalog-wide SNR shift caused by the local-zodiacal correction.

    Compares the one-hour SNR of every catalog target computed with the
    corrected local-zodiacal normalization against the pre-correction one. The
    thesis quotes a median shift for this quantity; this recomputes it from the
    current code rather than inheriting it.
    """
    rows = []
    for catalog in catalogs:
        bus, instrument, opt = build_bus(catalog, ARMS['control'])
        for order in null_orders:
            snr = {}
            for config, scale in DEFECT_CONFIGS.items():
                ams = AgnosticMissionSimulator(
                    order, 7, 65 / 360 * 2 * np.pi, 0.8, 12 * 60 * 60, verbose=False)
                if scale != 1.0:
                    ams.get_localzodi_budget().update_factors(
                        multiplicative_factor=lambda args, s=scale: s)
                ams.run(instrument, opt)
                snr[config] = np.asarray(ams.snr_saved, dtype=float).copy()

            a, b = snr['corrected'], snr['pre_correction']
            good = np.isfinite(a) & np.isfinite(b) & (b > 0)
            rel = (a[good] - b[good]) / b[good]      # negative: correction lowers SNR
            med, p16, p84 = (float(np.median(rel)), float(np.percentile(rel, 16)),
                             float(np.percentile(rel, 84)))
            print(f'>> hab2{catalog} order {order}: median SNR shift '
                  f'{100*med:+.2f}%  [16th {100*p16:+.2f}%, 84th {100*p84:+.2f}%]  '
                  f'over {good.sum()} targets', flush=True)
            rows.append([f'hab2{catalog}', order, int(good.sum()),
                         round(med, 6), round(p16, 6), round(p84, 6)])

    os.makedirs(os.path.dirname(SNRSHIFT_RESULTS), exist_ok=True)
    with open(SNRSHIFT_RESULTS, 'w', encoding='utf8') as fh:
        fh.write('catalog\tnull_order\tn_targets\tmedian_rel_shift\t'
                 'p16_rel_shift\tp84_rel_shift\n')
        for r in rows:
            fh.write('\t'.join(str(x) for x in r) + '\n')
    print(f'\nSNR-shift results: {SNRSHIFT_RESULTS}', flush=True)


PHYSICAL_RESULTS = os.path.join(REPO_ROOT, 'thesis', 'reproducibility',
                                'physical_architecture.tsv')
PHYSICAL_FIGDIR = os.path.join(REPO_ROOT, 'thesis', 'images', 'tse', 'physical')


def run_physical(catalogs, upper_start, n_cpu=None, design='triple6'):
    """Endpoint searches driven by a concrete beam combiner.

    Replaces the sin^n null-order proxy with the six-aperture double triple
    nuller, sized to its own response peak rather than to the reference array's.
    Produces the amplitudes the order-four half of the results table reports,
    together with the budget-shape figures, from a physically realizable design.
    """
    from lifesim.util.combiner import (double_triple_nuller, baseline_constant,
                                       double_bracewell)
    os.makedirs(PHYSICAL_FIGDIR, exist_ok=True)

    for catalog in catalogs:
        bus, instrument, opt = build_bus(catalog, ARMS['control'])
        if n_cpu:
            bus.data.options.other['n_cpu'] = int(n_cpu)
        ratio = bus.data.options.array['ratio']
        widths = bus.data.inst['wl_bin_widths'] * 1e6
        # 'bracewell4' runs the reference array through the same general-combiner
        # path as the fourth-order design, so the two halves of the results table
        # share a provenance instead of mixing a production campaign with fresh
        # architecture runs.
        arch = (double_triple_nuller(1.0, ratio) if design == 'triple6'
                else double_bracewell(1.0, ratio))
        order = 4 if design == 'triple6' else 2
        print(f'\n=== hab2{catalog} | six-aperture triple nuller | baseline '
              f'constant {baseline_constant(*arch):.6f} (reference '
              f'{baseline_constant(*double_bracewell(1.0, ratio)):.6f}) ===',
              flush=True)

        for target in TARGETS[catalog]:
            for gradient, family in FAMILIES.items():
                ams = AgnosticMissionSimulator(
                    order, 7, 65 / 360 * 2 * np.pi, 0.8, 12 * 60 * 60,
                    architecture=arch, verbose=False)
                tse = TradeSpaceExplorer(ams, opt, instrument)
                setter = make_setter(bus, ams, gradient, widths)

                tag = f'phys_{design}_{catalog}_{family}_{str(target).replace(".", "p")}'
                t0 = time.time()
                endpoint = tse.locate_mission_cutoff(
                    target, upper_start=upper_start, setter_func=setter,
                    plot_data={'cat': catalog, 'gradient': gradient,
                               'save': os.path.join(PHYSICAL_FIGDIR, tag + '.pdf')})
                setter(endpoint)
                achieved = ams.run(instrument, opt)
                wall = round(time.time() - t0, 1)

                print(f'>> {target} yr | {family}: {endpoint} ph/s/um | '
                      f'achieved {achieved:.4f} yr ({wall} s)', flush=True)

                os.makedirs(os.path.dirname(PHYSICAL_RESULTS), exist_ok=True)
                new = not os.path.exists(PHYSICAL_RESULTS)
                with open(PHYSICAL_RESULTS, 'a', encoding='utf8') as fh:
                    if new:
                        fh.write('timestamp\tcatalog\tarchitecture\tmtime_target_yr\t'
                                 'budget_family\tendpoint_ph_s_um\tmtime_achieved_yr\t'
                                 'wall_s\n')
                    fh.write('\t'.join(str(x) for x in [
                        datetime.now(timezone.utc).isoformat(timespec='seconds'),
                        f'hab2{catalog}', design, target, family,
                        endpoint, round(achieved, 6), wall]) + '\n')
    print(f'\nPhysical-architecture results: {PHYSICAL_RESULTS}', flush=True)


def run_stage_b(catalogs, scans, n_cpu=None, upper_start=5000, resume_dir=None):
    """Two-dimensional operating-point scans with the physical combiner.

    Each scan is a grid of endpoint searches -- 15 x 15 for the magnitude and
    slew scans -- so a single scan is hours and all six are of order a day. They
    are selectable individually so they can be submitted as separate jobs rather
    than one long one, and each writes its figure as soon as it finishes.

    Raising ``n_cpu`` is the main lever on a cluster: the SNR flow is dispatched
    across that many workers, and the default of eight comes from settings.yaml
    rather than from anything about the problem.
    """
    from lifesim.util.combiner import double_triple_nuller
    os.makedirs(PHYSICAL_FIGDIR, exist_ok=True)

    # Scan outer, catalogue inner. The thesis uses these figures in Hab2Max /
    # Hab2Min pairs, so completing a pair before starting the next scan means an
    # interrupted run still leaves usable figures. Rebuilding the bus per scan
    # costs a catalogue reload of a few seconds against scans lasting hours.
    for scan in scans:
        for catalog in catalogs:
            bus, instrument, opt = build_bus(catalog, ARMS['control'])
            if n_cpu:
                bus.data.options.other['n_cpu'] = int(n_cpu)
            ratio = bus.data.options.array['ratio']
            # These scans belong to the fourth-order design, whose zero-budget
            # time is well below the reference's, so its operating point is not
            # PRIMARY_TARGET. Read the first entry of TARGETS instead, which
            # --targets overrides, and which the caller sets to the lowest half
            # year above this architecture's own zero-budget time.
            target = TARGETS[catalog][0]
            arch = double_triple_nuller(1.0, ratio)

            ams = AgnosticMissionSimulator(
                4, 7, 65 / 360 * 2 * np.pi, 0.8, 12 * 60 * 60,
                architecture=arch, verbose=False)
            tse = TradeSpaceExplorer(ams, opt, instrument)
            tag = f'phys_{catalog}_{scan}_{str(target).replace(".", "p")}'
            out = os.path.join(PHYSICAL_FIGDIR, tag + '.pdf')
            # A scan is hours long and writes only its figure, so an interrupted
            # run loses everything unless its log is replayed back in.
            # Resolve against REPO_ROOT: importing lifesim changes the working
            # directory to lifesim/gui, so a relative path given on the command
            # line would silently resolve to nothing and quietly disable resume.
            resume_from = None
            if resume_dir:
                base = (resume_dir if os.path.isabs(resume_dir)
                        else os.path.join(REPO_ROOT, resume_dir))
                resume_from = os.path.join(base, f'stageb6_{scan}_{catalog}.log')

            print(f'\n=== hab2{catalog} | scan {scan} | target {target} yr | '
                  f'n_cpu {bus.data.options.other["n_cpu"]} ===', flush=True)
            t0 = time.time()
            if scan == 'mag':
                tse.plot_cutoff_for_mag(target, save_path=out, resume_from=resume_from)
            elif scan == 'slew':
                tse.plot_cutoff_for_slewtime(target, save_path=out, resume_from=resume_from)
            elif scan == 'linear':
                # The linear scan is one evaluation per point rather than a
                # search, so a restart is cheap and no resume path exists.
                tse.plot_linear_regression_additive(save_path=out)
            else:
                raise ValueError(f'unknown scan: {scan}')
            print(f'>> {scan} done in {(time.time()-t0)/3600:.2f} h -> {out}',
                  flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--catalog', choices=['hi', 'lo'], action='append',
                    help='hi = Hab2Max, lo = Hab2Min. Repeatable; default both.')
    ap.add_argument('--arm', choices=list(ARMS), action='append',
                    help='Repeatable; default both.')
    ap.add_argument('--null-order', type=int, default=4)
    ap.add_argument('--upper-start', type=int, default=5000)
    ap.add_argument('--resume-dir', type=str, default=None,
                    help='Directory holding logs from an interrupted --stage-b '
                         'run. Grid points already decided there are replayed '
                         'rather than recomputed; the loop state they imply is '
                         'rebuilt exactly, so resuming is not an approximation.')
    ap.add_argument('--sweep', action='store_true',
                    help='Run the zero-budget throughput sensitivity sweep '
                         'instead of the endpoint-search ablation.')
    ap.add_argument('--defect-impact', action='store_true',
                    help='Quantify the inherited local-zodiacal normalization '
                         'defect by rerunning with and without it.')
    ap.add_argument('--stage-b', choices=['mag', 'slew', 'linear'], action='append',
                    help='Two-dimensional operating-point scan with the physical '
                         'combiner. Repeatable; each is hours, so prefer one per job.')
    ap.add_argument('--n-cpu', type=int, default=None,
                    help='Override the worker count for the SNR flow. The main '
                         'lever on a cluster; settings.yaml defaults to 8.')
    ap.add_argument('--design', choices=['triple6', 'bracewell4'],
                    default='triple6',
                    help='Which architecture the --physical run evaluates.')
    ap.add_argument('--physical', action='store_true',
                    help='Run the endpoint searches with the six-aperture '
                         'physical beam combiner instead of the sin^n proxy.')
    ap.add_argument('--snr-shift', action='store_true',
                    help='Recompute the catalog-wide SNR shift caused by the '
                         'local-zodiacal correction.')
    ap.add_argument('--breakeven', action='store_true',
                    help='Solve for the throughput at which a fourth-order null '
                         'ceases to shorten the mission relative to order two.')
    ap.add_argument('--background-context', action='store_true',
                    help='Report the astrophysical background spectral density '
                         'for scale against the reported allowances.')
    ap.add_argument('--targets', type=str, default=None,
                    help='Comma-separated mission-time targets overriding the '
                         'defaults. Needed for the penalized arm, whose '
                         'zero-budget time already exceeds every default target.')
    args = ap.parse_args()

    if args.targets:
        override = [float(t) for t in args.targets.split(',')]
        for key in TARGETS:
            TARGETS[key] = override

    catalogs = args.catalog or ['hi', 'lo']
    arms = args.arm or list(ARMS)

    if args.sweep:
        run_sweep(catalogs, [2, 4], SWEEP_THROUGHPUTS)
        return

    if args.defect_impact:
        run_defect_impact(catalogs, [2, 4], args.upper_start)
        return

    if args.background_context:
        run_background_context(catalogs, [2, 4])
        return

    if args.breakeven:
        run_breakeven(catalogs)
        return

    if args.snr_shift:
        run_snr_shift(catalogs, [2, 4])
        return

    if args.physical:
        run_physical(catalogs, args.upper_start, n_cpu=args.n_cpu,
                     design=args.design)
        return

    if args.stage_b:
        run_stage_b(catalogs, args.stage_b, n_cpu=args.n_cpu,
                    upper_start=args.upper_start, resume_dir=args.resume_dir)
        return

    for catalog in catalogs:
        for arm in arms:
            throughput = ARMS[arm]
            bus, instrument, opt = build_bus(catalog, throughput)
            eff_tot = bus.data.inst['eff_tot']
            widths = bus.data.inst['wl_bin_widths'] * 1e6
            print(f'\n=== hab2{catalog} | {arm} | throughput={throughput} | '
                  f'eff_tot={eff_tot} | order={args.null_order} ===', flush=True)

            for target in TARGETS[catalog]:
                for gradient, family in FAMILIES.items():
                    ams = AgnosticMissionSimulator(
                        args.null_order, 7, 65 / 360 * 2 * np.pi, 0.8, 12 * 60 * 60,
                        verbose=False)
                    tse = TradeSpaceExplorer(ams, opt, instrument)

                    setter = make_setter(bus, ams, gradient, widths)

                    t0 = time.time()
                    endpoint = tse.locate_mission_cutoff(
                        target, upper_start=args.upper_start,
                        setter_func=setter, plot_data=None)

                    # `locate_mission_cutoff` stops once it is within epsilon =
                    # 0.05 yr of the target and returns its last guess, not the
                    # exact admissible endpoint. Re-evaluate at that guess so the
                    # mission time it actually delivers is on record: the reported
                    # amplitude belongs to `mtime_achieved`, not to `target`.
                    setter(endpoint)
                    achieved = ams.run(instrument, opt)
                    residual = round(achieved - target, 4)
                    wall = round(time.time() - t0, 1)

                    print(f'>> {target} yr | {family}: {endpoint} ph/s/um '
                          f'| achieved {achieved:.4f} yr (residual {residual:+.4f}) '
                          f'({wall} s)', flush=True)
                    append_row([datetime.now(timezone.utc).isoformat(timespec='seconds'),
                                arm, f'hab2{catalog}', args.null_order, target, family,
                                throughput, eff_tot, endpoint, round(achieved, 6),
                                residual, wall])

    print(f'\nResults: {RESULTS}', flush=True)


if __name__ == '__main__':
    main()
