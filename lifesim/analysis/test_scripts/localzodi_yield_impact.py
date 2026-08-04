"""What the local-zodiacal normalization correction does to a detection yield.

Section 4.2 establishes that the inherited pixel-grid path divided a circular
field of view's integrated flux by the area of its enclosing square, suppressing
the uniform local-zodiacal foreground by pi/4, and quantifies the resulting shift
in per-target SNR. It stops there: the thesis reports the SNR shift and the
change in its own iso-mission-time allowances, but never states what the
correction does to a yield of the kind LIFE VI reports.

That is the quantity the LIFE literature actually publishes, so this measures it
directly. The optimizer is run in its fixed-search-time mode -- the mode a yield
study uses, rather than the mission-time inversion the rest of this thesis runs
in -- once with the corrected normalization and once with the pre-correction
one, with nothing else changed. The difference is the yield penalty the defect
was hiding.

    python localzodi_yield_impact.py [t_search_years]
"""
import os
import sys

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, REPO)
_cwd = os.getcwd()
import lifesim
os.chdir(_cwd)

from lifesim.ams.ablation_throughput import build_bus, ARMS, DEFECT_CONFIGS
from lifesim.ams.core.ams import AgnosticMissionSimulator
from lifesim.util.combiner import double_bracewell

YEAR = 365.25 * 24 * 3600
T_SEARCH = float(sys.argv[1]) * YEAR if len(sys.argv) > 1 else None

OUT = os.path.join(REPO, 'thesis', 'reproducibility', 'localzodi_yield_impact.tsv')
rows = ['catalog\tt_search_yr\tconfig\tlocalzodi_scale\texperiment\tdetected\tuniverses']

for catalog in ('hi', 'lo'):
    yields = {}
    for config, scale in DEFECT_CONFIGS.items():
        bus, instrument, opt = build_bus(catalog, ARMS['control'])
        o = bus.data.options.optimization
        # A yield is detections within a fixed search campaign, not the time
        # needed to complete one, so switch the optimizer's stopping rule.
        o['opt_limit'] = 'time'
        if T_SEARCH:
            o['t_search'] = T_SEARCH
        t_search_yr = o['t_search'] / YEAR

        ratio = bus.data.options.array['ratio']
        ams = AgnosticMissionSimulator(2, 7, 65 / 360 * 2 * np.pi, 0.8, 12 * 3600,
                                       architecture=double_bracewell(1.0, ratio),
                                       verbose=False)
        if scale != 1.0:
            ams.get_localzodi_budget().update_factors(
                multiplicative_factor=lambda args, s=scale: s)
        ams.run(instrument, opt)

        det = dict(bus.data.optm['exp_detected'])
        # exp_detected is summed over synthetic universes; a yield study quotes
        # the per-universe mean, which is what the optimizer itself prints.
        n_uni = bus.data.optm['num_universe']
        yields[config] = {k: v / n_uni for k, v in det.items()}
        for k, v in yields[config].items():
            rows.append(f'hab2{catalog}\t{t_search_yr:.3f}\t{config}\t{scale:.6f}\t'
                        f'{k}\t{v:.3f}\t{n_uni}')
        print(f'hab2{catalog} {config:14s} (localzodi x{scale:.4f}): '
              + ', '.join(f'{k} {v:.2f}' for k, v in yields[config].items())
              + f'   [{t_search_yr:.2f} yr search, {n_uni} universes]', flush=True)

    print(f'\n=== hab2{catalog}: effect of the correction')
    for k in yields['corrected']:
        pre, cor = yields['pre_correction'][k], yields['corrected'][k]
        print(f'  {k}: {pre:.2f} -> {cor:.2f} detections, '
              f'{cor - pre:+.2f} ({100 * (cor - pre) / max(pre, 1e-9):+.1f} %)')
    print()

with open(OUT, 'w') as fh:
    fh.write('\n'.join(rows) + '\n')
print(f'wrote {OUT}')
