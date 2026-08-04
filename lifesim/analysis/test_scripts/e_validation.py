"""External validation against LIFE VI (Kammerer et al. 2022), Table A.1.

The one gap no internal test touches: comparison against a number produced
outside this work. LIFE VI publishes predicted detection yields for a 2.5-yr
search with 4 x 2 m collectors at 5 % total throughput over Sun-like stars
(4800-6300 K, d < 20 pc), for the same hab2min/hab2max occurrence scenarios our
catalogs implement. Anchor rows (D = 2 m, 3-zodi median, opt-HZ baseline
optimization; median +84th/-16th over 1000 universes):

    hab2min: N_det 30 (+16/-10), opt-HZ 11 (+10/-6), con-HZ 5 (+6/-3), EEC 4 (+3/-3)
    hab2max: N_det 39 (+22/-18), opt-HZ 14 (+14/-8), con-HZ 8 (+8/-5), EEC 6 (+6/-4)

Design: configure our chain to LIFE VI's mission parameters, restrict the
stellar scaffold to their Sun-like definition, and run the fixed-campaign yield
twice -- corrected local-zodiacal normalization, and the pre-correction (pi/4)
arm. LIFE VI ran inherited LIFEsim, i.e. the defect era, so the prediction is:
pre-correction arm near the published rows, corrected arm below them by roughly
the defect's yield penalty.

Stated caveats (thesis Sect. 2.2 / C2b): our scaffold is not their target list
(no binarity screen; different star census inside 20 pc), our observing-sequence
optimization is the thesis's Experiment-1 configuration rather than their
HZ-yield maximization, and the planet-category windows use the solar-normalized
insolation bounds of their Table 1 rather than the spectral-type-dependent
Kopparapu limits. The comparison bounds agreement; it does not re-referee the
published numbers.

    python e_validation.py --catalog hi        # hab2max scenario
    python e_validation.py --catalog lo        # hab2min scenario
"""
import argparse
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

ANCHORS = {  # LIFE VI Table A.1, D=2.0 m, 3 zodi, opt-HZ optimization
    'lo': dict(total=(30.0, -10.0, 16.0), opt_hz=(11.0, -6.0, 10.0),
               con_hz=(5.0, -3.0, 6.0), eec=(4.0, -3.0, 3.0)),
    'hi': dict(total=(39.0, -18.0, 22.0), opt_hz=(14.0, -8.0, 14.0),
               con_hz=(8.0, -5.0, 8.0), eec=(6.0, -4.0, 6.0)),
}

ap = argparse.ArgumentParser()
ap.add_argument('--catalog', choices=['hi', 'lo'], required=True)
ap.add_argument('--t-search', type=float, default=2.5, help='search phase [yr]')
ap.add_argument('--n-cpu', type=int, default=4)
a = ap.parse_args()

OUT = os.path.join(REPO, 'thesis', 'reproducibility',
                   f'e_validation_{a.catalog}.tsv')
rows = ['catalog\tconfig\tcategory\tmean\tp16\tp84\tuniverses\tn_stars\tn_planets']

for config, scale in DEFECT_CONFIGS.items():
    bus, instrument, opt = build_bus(a.catalog, ARMS['control'])
    bus.data.options.other['n_cpu'] = a.n_cpu

    # LIFE VI mission parameters (their Table 2), overriding thesis defaults.
    arr = bus.data.options.array
    arr['diameter'] = 2.0
    arr['throughput'] = 0.05
    arr['quantum_eff'] = 0.7
    arr['wl_min'] = 4.0
    arr['wl_max'] = 18.5
    arr['spec_res'] = 20
    arr['t_slew'] = 10 * 3600

    o = bus.data.options.optimization
    o['opt_limit'] = 'time'
    o['t_search'] = a.t_search * YEAR

    cat = bus.data.catalog
    need = ['distance_s', 'temp_s', 'radius_p', 'nuniverse']
    missing = [c for c in need if c not in cat.columns]
    if missing:
        sys.exit(f'missing expected columns {missing}; have: {sorted(cat.columns)}')
    # insolation and semi-major axis: importer keeps P-Pop names if unmapped
    fcol = next((c for c in ('flux_p', 'finc_p', 'Finc', 'insolation_p')
                 if c in cat.columns), None)
    acol = next((c for c in ('semimajor_p', 'a_p', 'a')
                 if c in cat.columns), None)
    if fcol is None or acol is None:
        sys.exit(f'no insolation/semimajor column; have: {sorted(cat.columns)}')

    # Sun-like restriction of LIFE VI: 4800-6300 K, d < 20 pc.
    sel = (cat['distance_s'] < 20.0) & cat['temp_s'].between(4800.0, 6300.0)
    bus.data.catalog = cat[sel].reset_index(drop=True)
    bus.data.catalog['id'] = range(len(bus.data.catalog))
    n_stars = bus.data.catalog['nstar'].nunique()

    ratio = arr['ratio']
    # All-sky field of regard and no magnitude cut: LIFE VI applies neither.
    ams = AgnosticMissionSimulator(2, 99, np.pi / 2, 0.8, arr['t_slew'],
                                   architecture=double_bracewell(1.0, ratio),
                                   verbose=False)
    if scale != 1.0:
        ams.get_localzodi_budget().update_factors(
            multiplicative_factor=lambda args, s=scale: s)
    ams.run(instrument, opt)

    cat = bus.data.catalog
    r = cat['radius_p']
    f = cat[fcol]
    masks = {
        'total': np.ones(len(cat), dtype=bool),
        'opt_hz': (r.between(0.5, 1.5) & f.between(0.320, 1.776)).to_numpy(),
        'con_hz': (r.between(0.5, 1.5) & f.between(0.356, 1.107)).to_numpy(),
        'eec': ((r >= 0.8 * cat[acol] ** -0.5) & (r <= 1.4)
                & f.between(0.356, 1.107)).to_numpy(),
    }
    det = cat['detected'].to_numpy(dtype=bool)
    unis = np.sort(cat['nuniverse'].unique())
    print(f'\n=== hab2{a.catalog} {config} (localzodi x{scale:.4f}): '
          f'{n_stars} Sun-like stars, {len(cat)} planet rows, '
          f'{unis.size} universes, {a.t_search} yr search')
    for name, m in masks.items():
        per_uni = np.array([np.sum(det & m & (cat['nuniverse'] == u).to_numpy())
                            for u in unis], dtype=float)
        mean, p16, p84 = per_uni.mean(), *np.percentile(per_uni, [16, 84])
        anch = ANCHORS[a.catalog][name]
        print(f'  {name:<7}: mean {mean:6.2f}  16-84% [{p16:.0f}, {p84:.0f}]   '
              f'LIFE VI: {anch[0]:.0f} [{anch[0]+anch[1]:.0f}, {anch[0]+anch[2]:.0f}]',
              flush=True)
        rows.append(f'hab2{a.catalog}\t{config}\t{name}\t{mean:.3f}\t{p16:.1f}\t'
                    f'{p84:.1f}\t{unis.size}\t{n_stars}\t{len(cat)}')

with open(OUT, 'w') as fh:
    fh.write('\n'.join(rows) + '\n')
print(f'\nwrote {OUT}')
