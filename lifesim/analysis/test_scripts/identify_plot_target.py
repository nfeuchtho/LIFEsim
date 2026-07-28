"""Identify the single planet drawn by the AMS budget-breakdown plot mode.

`Ams.plot_id` is a positional row index into the catalog as it stands after
pre-selection (`ams.py:634-636`), and `TradeSpaceExplorer` hardcodes 9 for
Hab2Max and 5 for Hab2Min. Every budget-breakdown figure in the thesis therefore
shows one arbitrary target's stellar and exozodiacal background, not an ensemble
average. This reports which target that is and where it sits in the distribution
of eligible targets, so the captions can say so.

    python identify_plot_target.py
"""
import os

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
import lifesim

PLOT_ID = {'hi': 9, 'lo': 5}


def pct(series, value):
    """Percentile rank of `value` within `series`, in percent."""
    return 100.0 * float((series < value).sum()) / len(series)


for tag, pid in PLOT_ID.items():
    bus = lifesim.Bus()
    bus.data.options.set_scenario('baseline')
    bus.data.catalog_from_ppop(
        input_path=os.path.join(REPO, 'lifesim', 'catalogs', f'catalog_hab2{tag}.txt'))
    cat = bus.data.catalog

    cat['is_interesting'] = False
    for name, exp in bus.data.options.optimization['experiments'].items():
        m = ((cat.radius_p >= exp['radius_p_min']) & (cat.radius_p <= exp['radius_p_max'])
             & (cat.temp_s >= exp['temp_s_min']) & (cat.temp_s <= exp['temp_s_max']))
        if exp['in_HZ']:
            m &= cat['habitable']
        cat['is_interesting'] |= m

    sel = cat[cat['is_interesting']]
    row = sel.iloc[pid]

    print(f'\n=== hab2{tag}, plot_id {pid} of {len(sel)} eligible planet rows')
    print(f'    host star nstar {int(row.nstar)}, distance {row.distance_s:.2f} pc, '
          f'T_eff {row.temp_s:.0f} K, R {row.radius_s:.3f} Rsun, L {row.l_sun:.4f} Lsun')
    print(f'    ecliptic latitude {np.rad2deg(row.lat):+.1f} deg, '
          f'HZ centre {row.hz_center:.3f} AU, exozodi level z {row.z:.2f}')
    print(f'    planet radius {row.radius_p:.2f} Rearth')

    # One row per eligible host star, so the percentiles describe the target
    # population the mission actually chooses from rather than planet counts.
    stars = sel.sort_values('nstar').groupby('nstar').first()
    for col, val, unit in [('distance_s', row.distance_s, 'pc'),
                           ('z', row.z, 'zodi'),
                           ('l_sun', row.l_sun, 'Lsun'),
                           ('temp_s', row.temp_s, 'K')]:
        s = stars[col]
        print(f'    {col:>10}: target {val:8.3f} {unit:5s} | ensemble median '
              f'{s.median():8.3f} | percentile {pct(s, val):5.1f} %')
