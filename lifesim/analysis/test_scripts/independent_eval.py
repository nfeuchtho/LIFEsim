"""Evaluate one anchor cell on one independent P-Pop realization.

Pre-registered campaign (thesis/reproducibility/independent_ensembles/
PREREGISTRATION.md): corrected-rule scheduler, flat family, zero-budget
mission time plus endpoint search, production machinery throughout.

    python independent_eval.py --catalog-file <realization.txt> \
        --scenario hab2max --design bracewell4 --target 5.5 --seedtag seed101
"""
import argparse
import os
import sys
import time

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, REPO)
_cwd = os.getcwd()
import lifesim
os.chdir(_cwd)

from lifesim.ams.ablation_throughput import build_bus, ARMS, make_setter, FAMILIES
from lifesim.ams.core.ams import AgnosticMissionSimulator
from lifesim.ams.trade_space_explorer import TradeSpaceExplorer
from lifesim.util.combiner import double_bracewell, double_triple_nuller

GRADIENT = {v: k for k, v in FAMILIES.items()}
OUTDIR = os.path.join(REPO, 'thesis', 'reproducibility', 'independent_ensembles')

ap = argparse.ArgumentParser()
ap.add_argument('--catalog-file', required=True)
ap.add_argument('--scenario', choices=['hab2min', 'hab2max'], required=True)
ap.add_argument('--design', choices=['bracewell4', 'triple6'], required=True)
ap.add_argument('--target', type=float, required=True)
ap.add_argument('--seedtag', required=True)
ap.add_argument('--n-cpu', type=int, default=2)
a = ap.parse_args()

os.makedirs(OUTDIR, exist_ok=True)
cat_token = 'lo' if a.scenario == 'hab2min' else 'hi'
tag = f'{a.design}_{a.scenario}_{str(a.target).replace(".", "p")}_{a.seedtag}'
out = os.path.join(OUTDIR, tag + '.tsv')

bus, instrument, opt = build_bus(cat_token, ARMS['control'],
                                 catalog_path=a.catalog_file)
bus.data.options.other['n_cpu'] = a.n_cpu
bus.data.options.optimization['strict_completion'] = False
bus.data.options.optimization['retain_empty_universes'] = True
widths = bus.data.inst['wl_bin_widths'] * 1e6
ratio = bus.data.options.array['ratio']
arch = (double_triple_nuller(1.0, ratio) if a.design == 'triple6'
        else double_bracewell(1.0, ratio))
order = 4 if a.design == 'triple6' else 2

ams = AgnosticMissionSimulator(order, 7, 65 / 360 * 2 * np.pi, 0.8, 12 * 3600,
                               architecture=arch, verbose=False)
tse = TradeSpaceExplorer(ams, opt, instrument)

t0 = time.time()
zb = ams.run(instrument, opt)
setter = make_setter(bus, ams, GRADIENT['flat'], widths)
endpoint = tse.locate_mission_cutoff(a.target, upper_start=20000,
                                     setter_func=setter)
setter(endpoint)
achieved = ams.run(instrument, opt)
search = getattr(tse, 'last_search',
                 dict(status='n/a', lower=np.nan, upper=np.nan, its=-1))
wall = round(time.time() - t0, 1)

with open(out, 'w') as fh:
    fh.write('design\tscenario\ttarget_yr\tseedtag\tzero_budget_yr\t'
             'endpoint_ph_s_um\tmtime_achieved_yr\tsearch_status\twall_s\n')
    fh.write(f'{a.design}\t{a.scenario}\t{a.target}\t{a.seedtag}\t{zb:.4f}\t'
             f'{endpoint:.4f}\t{achieved:.4f}\t{search["status"]}\t{wall}\n')
print(f'>> {tag}: zb {zb:.4f} yr, endpoint {endpoint:.1f} '
      f'({search["status"]}, {wall}s)', flush=True)
