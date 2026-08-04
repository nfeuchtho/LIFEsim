"""Attribute the "Targets Lost" figure of the ecliptic yield plot to its causes.

`TradeSpaceExplorer.plot_yield` annotates the fraction of Experiment-1-eligible
host stars that receive zero SNR. That happens at `ams.py:393`, where a single
mask combines two independent cuts -- the limiting K-band magnitude and the
ecliptic-latitude field of regard -- so the annotated percentage is not the loss
to the zone of avoidance alone, even though the zone is the only cut the figure
draws. Both cuts act on catalog columns, so the split is recoverable without
evaluating any SNR.

    python decompose_target_loss.py [lim_mag] [for_deg]
"""
import os
import sys

import numpy as np
from scipy.integrate import quad_vec

# Importing lifesim changes the working directory, so resolve the catalog first.
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
import lifesim
from lifesim.util import constants

LIM_MAG = float(sys.argv[1]) if len(sys.argv) > 1 else 7.0
FOR_DEG = float(sys.argv[2]) if len(sys.argv) > 2 else 65.0
CAT = os.path.join(REPO, 'lifesim', 'catalogs', 'catalog_hab2hi.txt')


def k_band_mag(cat):
    """K-band apparent magnitude, transcribed from `Ams._filter` at ams.py:365-391."""
    k_band, k_band_width, dlambda_lambda = 2.2e-6, 0.58e-6, 0.23
    f_ref = 670 * 1.51e7 * dlambda_lambda
    flux = lambda wl: 2 * constants.c / (wl ** 4) / (
        np.exp(constants.h * constants.c / wl / constants.k / cat['temp_s']) - 1
    ) * np.pi * ((cat['radius_s'] * constants.radius_sun) / (10 * constants.m_per_pc)) ** 2
    k_flux = quad_vec(flux, k_band - k_band_width / 2, k_band + k_band_width / 2)[0]
    return -2.5 * np.log10(k_flux / f_ref) + 5 * (np.log10(cat['distance_s']) - 1)


bus = lifesim.Bus()
bus.data.options.set_scenario('baseline')
bus.data.catalog_from_ppop(input_path=CAT)
cat = bus.data.catalog

# The eligibility flag, as recomputed inside Ams.run at ams.py:270-287.
ONLY = sys.argv[3] if len(sys.argv) > 3 else None
cat['is_interesting'] = False
for name, exp in bus.data.options.optimization['experiments'].items():
    if ONLY and name != ONLY:
        continue
    m = ((cat.radius_p >= exp['radius_p_min']) & (cat.radius_p <= exp['radius_p_max'])
         & (cat.temp_s >= exp['temp_s_min']) & (cat.temp_s <= exp['temp_s_max']))
    if exp['in_HZ']:
        m &= cat['habitable']
    cat['exp_' + name] = m
    cat['is_interesting'] |= m

# One row per host star, eligible-first, as plot_yield does at line 627.
stars = cat.sort_values(['nstar', 'is_interesting'],
                        ascending=[True, False]).groupby('nstar').first()
eligible = stars[stars['is_interesting']]

mag = k_band_mag(eligible)
too_faint = (mag > LIM_MAG).to_numpy()
out_of_regard = (np.abs(eligible['lat']) > np.deg2rad(FOR_DEG)).to_numpy()
lost = too_faint | out_of_regard
n = len(eligible)

print(f'catalog {CAT}, lim_mag {LIM_MAG}, FoR {FOR_DEG} deg')
print(f'  eligible host stars                     {n}')
print(f'  lost to either cut                      {lost.sum():5d}  {100*lost.sum()/n:5.1f}%   <- the annotated number')
print(f'    outside the field of regard only      {(out_of_regard & ~too_faint).sum():5d}  '
      f'{100*(out_of_regard & ~too_faint).sum()/n:5.1f}%')
print(f'    fainter than the magnitude limit only {(too_faint & ~out_of_regard).sum():5d}  '
      f'{100*(too_faint & ~out_of_regard).sum()/n:5.1f}%')
print(f'    both                                  {(too_faint & out_of_regard).sum():5d}  '
      f'{100*(too_faint & out_of_regard).sum()/n:5.1f}%')
print(f'  field of regard, marginal total         {out_of_regard.sum():5d}  {100*out_of_regard.sum()/n:5.1f}%')
print(f'  magnitude limit, marginal total         {too_faint.sum():5d}  {100*too_faint.sum()/n:5.1f}%')
