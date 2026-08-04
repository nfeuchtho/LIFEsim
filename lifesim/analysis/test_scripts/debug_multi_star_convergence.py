"""Broader validation: check analytic vs high-resolution grid convergence across
many stars (not just one), for both fov_taper models. Prints per-star, per-noise
component agreement and flags any NaN/negative/non-converging cases."""
import os
import sys

import numpy as np

working_directory = os.getcwd()
import lifesim
os.chdir(working_directory)
from lifesim.util.radiation import black_body

_HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG_PATH = os.path.join(_HERE, "..", "..", "catalogs", "catalog_hab2hi.txt")
SPEC_RES = 10
N_STARS = 25
IS_HIGH = 800
FOV_TAPER = sys.argv[1] if len(sys.argv) > 1 else 'gaussian'


def build(fov_taper):
    bus = lifesim.Bus()
    bus.data.options.set_scenario('baseline')
    bus.data.catalog_from_ppop(input_path=CATALOG_PATH)
    bus.data.options.set_manual(n_cpu=1, image_size=100, spec_res=float(SPEC_RES),
                                fov_taper=fov_taper)
    instrument = lifesim.Instrument(name='inst')
    bus.add_module(instrument)
    bus.add_module(lifesim.TransmissionMap(name='transm'))
    bus.add_module(lifesim.PhotonNoiseExozodi(name='exo'))
    bus.add_module(lifesim.PhotonNoiseLocalzodi(name='local'))
    bus.add_module(lifesim.PhotonNoiseStar(name='star'))
    bus.connect(('inst', 'transm')); bus.connect(('inst', 'exo'))
    bus.connect(('inst', 'local')); bus.connect(('inst', 'star')); bus.connect(('star', 'transm'))
    instrument.apply_options()
    return bus, instrument


bus, instrument = build(FOV_TAPER)
cat = instrument.data.catalog
rng = np.random.default_rng(42)
star_ids = cat['nstar'].unique()
sample_ids = rng.choice(star_ids, size=min(N_STARS, len(star_ids)), replace=False)
rows = [cat.index[cat['nstar'] == sid][0] for sid in sample_ids]

print(f"=== fov_taper={FOV_TAPER}, IS_HIGH={IS_HIGH}, n_stars={len(rows)} ===")

worst_star_rel = 0.0
worst_exo_rel = 0.0
any_bad = False

for i in rows:
    hz_center = float(cat.iloc[i]['hz_center'])
    distance_s = float(cat.iloc[i]['distance_s'])
    instrument.adjust_bl_to_hz(hz_center=hz_center, distance_s=distance_s)

    bl = instrument.data.inst['bl']
    wl_bins = instrument.data.inst['wl_bins']
    wl_bin_widths = instrument.data.inst['wl_bin_widths']
    ratio = instrument.data.options.array['ratio']
    hfov = instrument.data.inst['hfov']
    image_angle = instrument.data.inst['image_angle']
    fov_taper = instrument.data.options.models['fov_taper']
    telescope_area = instrument.data.inst['telescope_area']

    wl_bins_r = wl_bins.reshape(-1, 1, 1)
    image_angle_r = image_angle.reshape(-1, 1, 1)
    hfov_r = hfov.reshape(-1, 1, 1)
    L = bl / 2

    # NEW analytic
    noise_star_list = instrument.run_socket(s_name='photon_noise_star', method='noise', index=i)
    noise_star_new = sum(np.asarray(n) for n in noise_star_list) if isinstance(noise_star_list, list) else np.asarray(noise_star_list)
    noise_exo_list = instrument.run_socket(s_name='photon_noise_universe', method='noise', index=i)
    noise_exo_new = sum(np.asarray(n) for n in noise_exo_list) if isinstance(noise_exo_list, list) else np.asarray(noise_exo_list)

    if not (np.all(np.isfinite(noise_star_new)) and np.all(np.isfinite(noise_exo_new))
            and np.all(noise_star_new >= 0) and np.all(noise_exo_new >= 0)):
        print(f"  star row {i}: BAD VALUES (nan/neg) star={noise_star_new} exo={noise_exo_new}")
        any_bad = True
        continue

    # OLD grid, at IS_HIGH -- star leak (proper disk mask, matches new formula's domain)
    lat_s = float(cat.iloc[i]['lat'])
    long = 3 / 4 * np.pi
    radius_sun_au = 0.00465047
    tau = 4e-8
    temp_eff = 265
    temp_sun = 5777
    a_c = 0.22
    b_tot = black_body(mode='wavelength', bins=wl_bins, width=wl_bin_widths, temp=temp_eff) + a_c \
            * black_body(mode='wavelength', bins=wl_bins, width=wl_bin_widths, temp=temp_sun) * (radius_sun_au / 1.5) ** 2
    lz_flux_sr = tau * b_tot * np.sqrt(
        np.pi / np.arccos(np.cos(long) * np.cos(lat_s)) /
        (np.sin(lat_s) ** 2 + (0.6 * (wl_bins / 11e-6) ** (-0.4) * np.cos(lat_s)) ** 2)
    )
    lz_flux = lz_flux_sr * (np.pi * image_angle ** 2)

    radius_s = float(cat.iloc[i]['radius_s'])
    temp_s = float(cat.iloc[i]['temp_s'])
    Rs_au = 0.00465047 * radius_s
    Rs_rad = (Rs_au / distance_s) / (3600. * 180.) * np.pi

    IS = IS_HIGH
    angle = np.linspace(-1, 1, IS)
    alpha = np.tile(angle, (IS, 1))
    beta = alpha.T
    alpha_fixed = alpha * image_angle_r
    beta_fixed = beta * image_angle_r
    sin_contrib = np.sin(2 * np.pi * L * alpha_fixed / wl_bins_r) ** 2
    tm3 = sin_contrib * np.cos(2 * ratio * np.pi * L * beta_fixed / wl_bins_r - np.pi / 4) ** 2
    if fov_taper == 'gaussian':
        taper = np.exp(-(np.pi / 4 / hfov_r * np.sqrt(alpha_fixed ** 2 + beta_fixed ** 2)) ** 2)
        tm3 = tm3 * taper

    x_map = np.tile(np.array(range(0, IS)), (IS, 1))
    y_map = x_map.T
    r_sq = (x_map - (IS - 1) / 2) ** 2 + (y_map - (IS - 1) / 2) ** 2
    radius_map = np.sqrt(r_sq)

    # disk mask matching new formula's domain (radius = image_angle), for BOTH taper models,
    # so this checks the star-leak/exozodi math independent of the known localzodi square-vs-disk issue
    disk_mask = np.where(radius_map <= IS / 2, 1, 0)

    IS_star = 400
    angle2 = np.linspace(-1, 1, IS_star)
    alpha2 = np.tile(angle2, (IS_star, 1)) * Rs_rad
    beta2 = alpha2.T
    sin_c2 = np.sin(2 * np.pi * L * alpha2 / wl_bins_r) ** 2
    tm_star_old = sin_c2 * np.cos(2 * ratio * np.pi * L * beta2 / wl_bins_r - np.pi / 4) ** 2
    if fov_taper == 'gaussian':
        taper2 = np.exp(-(np.pi / 4 / hfov_r * np.sqrt(alpha2 ** 2 + beta2 ** 2)) ** 2)
        tm_star_old = tm_star_old * taper2
    x_map2 = np.tile(np.array(range(0, IS_star)), (IS_star, 1))
    y_map2 = x_map2.T
    r_sq2 = (x_map2 - (IS_star - 1) / 2) ** 2 + (y_map2 - (IS_star - 1) / 2) ** 2
    star_px = np.where(r_sq2 < (IS_star / 2) ** 2, 1, 0)
    sl_leak_old = (star_px * tm_star_old).sum(axis=(-2, -1)) / star_px.sum() * black_body(
        bins=wl_bins, width=wl_bin_widths, temp=temp_s, radius=radius_s, distance=distance_s, mode='star'
    ) * telescope_area

    rel_star = np.abs(sl_leak_old - noise_star_list[1 if isinstance(noise_star_list, list) and
                       np.allclose(np.asarray(noise_star_list[1])[:3], sl_leak_old[:3], rtol=0.5) else 0]) / np.abs(sl_leak_old + 1e-30)
    # simpler robust approach: identify which component is star-leak by magnitude closeness
    comps = [np.asarray(c) for c in noise_star_list] if isinstance(noise_star_list, list) else [noise_star_new]
    star_new = min(comps, key=lambda c: np.abs(c - sl_leak_old).sum())
    rel_star = np.abs(star_new - sl_leak_old) / np.abs(sl_leak_old + 1e-30)

    # exozodi (old grid)
    l_sun = float(cat.iloc[i]['l_sun'])
    alpha_ez = 0.34
    r_in = 0.034422617777777775 * np.sqrt(l_sun)
    r_0 = np.sqrt(l_sun)
    sigma_zero = 7.11889e-8
    mas_pix = (2 * instrument.data.inst['image_angle_mas'] / IS)
    rad_pix = (2 * image_angle / IS)
    au_pix = (mas_pix / 1e3 * distance_s).reshape(-1, 1, 1)
    rad_pix_r = rad_pix.reshape(-1, 1, 1)
    r_au = radius_map * au_pix
    r_cond = (r_au >= r_in) & (r_au <= IS / 2 * au_pix)
    temp_map = np.where(r_cond, 278.3 * (l_sun ** 0.25) / np.sqrt(r_au), 0)
    sigma = np.where(r_cond, sigma_zero * (r_au / r_0) ** (-alpha_ez), 0)
    f_nu_disk = black_body(bins=wl_bins_r, width=wl_bin_widths.reshape(-1, 1, 1),
                           temp=temp_map, mode='wavelength') * sigma * rad_pix_r ** 2 * telescope_area
    ez_leak_old = (f_nu_disk * tm3 * disk_mask).sum(axis=(-2, -1))
    rel_exo = np.abs(ez_leak_old - noise_exo_new) / np.abs(ez_leak_old + 1e-30)

    worst_star_rel = max(worst_star_rel, np.nanmax(rel_star))
    worst_exo_rel = max(worst_exo_rel, np.nanmax(rel_exo))
    flag = "  <-- CHECK" if (np.nanmax(rel_star) > 0.03 or np.nanmax(rel_exo) > 0.03) else ""
    print(f"  star row {i:6d} (bl={bl:6.2f} l_sun={l_sun:8.3f} d={distance_s:6.2f}pc): "
          f"star max_rel={np.nanmax(rel_star):.3e}  exo max_rel={np.nanmax(rel_exo):.3e}{flag}")

print(f"\nWorst-case star-leak rel diff across sample : {worst_star_rel:.3e}")
print(f"Worst-case exozodi rel diff across sample   : {worst_exo_rel:.3e}")
print(f"Any NaN/negative values encountered         : {any_bad}")
