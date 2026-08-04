"""Stage 1 of the architecture survey: production zero-budget mission times.

One corrected-scheduler AMS evaluation per (design, catalog) on the production
catalog -- no resampling, unlike zerobudget_spread.py -- because the survey's
operating targets are set by the rule "lowest half year above the zero-budget
time" and must come from the production ensemble, not a bootstrap draw.

Writes thesis/reproducibility/survey_stage1.tsv with design, catalog, zb_yr.
"""
import os
import sys

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, REPO)
_cwd = os.getcwd()
import lifesim
os.chdir(_cwd)

from lifesim.ams.ablation_throughput import build_bus, ARMS
from lifesim.ams.core.ams import AgnosticMissionSimulator
from lifesim.util.combiner import kernel5, collinear4

DESIGNS = {'kernel5_deep': (lambda r: kernel5(1.0, 'deep'), 4),
           'collinear4': (lambda r: collinear4(1.0), 4)}
OUT = os.path.join(REPO, 'thesis', 'reproducibility', 'survey_stage1.tsv')

rows = []
for catalog in ('hi', 'lo'):
    for design, (arch_fn, order) in DESIGNS.items():
        bus, instrument, opt = build_bus(catalog, ARMS['control'])
        bus.data.options.other['n_cpu'] = 8
        bus.data.options.optimization['strict_completion'] = False
        bus.data.options.optimization['retain_empty_universes'] = True
        ratio = bus.data.options.array['ratio']
        ams = AgnosticMissionSimulator(order, 7, 65 / 360 * 2 * np.pi, 0.8,
                                       12 * 3600, architecture=arch_fn(ratio),
                                       verbose=False)
        zb = ams.run(instrument, opt)
        rows.append(f'{design}\t{catalog}\t{zb:.4f}')
        print(f'{design} hab2{catalog}: zero-budget {zb:.4f} yr', flush=True)

with open(OUT, 'w') as fh:
    fh.write('design\tcatalog\tzb_yr\n' + '\n'.join(rows) + '\n')
print(f'wrote {OUT}')
