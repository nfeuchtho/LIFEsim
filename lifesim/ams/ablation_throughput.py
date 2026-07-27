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
from lifesim import TradeSpaceExplorer, AgnosticMissionSimulator
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


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--catalog', choices=['hi', 'lo'], action='append',
                    help='hi = Hab2Max, lo = Hab2Min. Repeatable; default both.')
    ap.add_argument('--arm', choices=list(ARMS), action='append',
                    help='Repeatable; default both.')
    ap.add_argument('--null-order', type=int, default=4)
    ap.add_argument('--upper-start', type=int, default=5000)
    ap.add_argument('--sweep', action='store_true',
                    help='Run the zero-budget throughput sensitivity sweep '
                         'instead of the endpoint-search ablation.')
    args = ap.parse_args()

    catalogs = args.catalog or ['hi', 'lo']
    arms = args.arm or list(ARMS)

    if args.sweep:
        run_sweep(catalogs, [2, 4], SWEEP_THROUGHPUTS)
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
