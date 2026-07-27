"""Debug script: compare the NEW analytic (grid-free) noise terms against the
OLD grid-based computation at increasing grid resolution, to check whether the
old grid converges toward the analytic value (validates the analytic formula
and shows IS=100 was just too coarse) or does not (real bug in the new code)."""
import os

import numpy as np

working_directory = os.getcwd()
import lifesim
os.chdir(working_directory)
from lifesim.util.radiation import black_body

_HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG_PATH = os.path.join(_HERE, "..", "..", "catalogs", "catalog_hab2hi.txt")
SPEC_RES = 10
GRID_SIZES = [100, 200, 400, 800, 1600]

bus = lifesim.Bus()
bus.data.options.set_scenario('baseline')
bus.data.catalog_from_ppop(input_path=CATALOG_PATH)
bus.data.options.set_manual(n_cpu=1, image_size=100, spec_res=float(SPEC_RES))

instrument = lifesim.Instrument(name='inst')
bus.add_module(instrument)
bus.add_module(lifesim.TransmissionMap(name='transm'))
bus.add_module(lifesim.PhotonNoiseExozodi(name='exo'))
bus.add_module(lifesim.PhotonNoiseLocalzodi(name='local'))
bus.add_module(lifesim.PhotonNoiseStar(name='star'))
bus.connect(('inst', 'transm'))
bus.connect(('inst', 'exo'))
bus.connect(('inst', 'local'))
bus.connect(('inst', 'star'))
bus.connect(('star', 'transm'))

instrument.apply_options()

cat = instrument.data.catalog
i = 0
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
print("bl:", bl, " fov_taper:", fov_taper, " n_wl:", wl_bins.size)

wl_bins_r = wl_bins.reshape(-1, 1, 1)
image_angle_r = image_angle.reshape(-1, 1, 1)
hfov_r = hfov.reshape(-1, 1, 1)
L = bl / 2

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

l_sun = float(cat.iloc[i]['l_sun'])
alpha_ez = 0.34
r_in = 0.034422617777777775 * np.sqrt(l_sun)
r_0 = np.sqrt(l_sun)
sigma_zero = 7.11889e-8

radius_s = float(cat.iloc[i]['radius_s'])
temp_s = float(cat.iloc[i]['temp_s'])
Rs_au = 0.00465047 * radius_s
Rs_as = Rs_au / distance_s
Rs_rad = Rs_as / (3600. * 180.) * np.pi

# ---- NEW analytic (grid-free), fixed reference ----
noise_star_list = instrument.run_socket(s_name='photon_noise_star', method='noise', index=i)
noise_star_new = sum(np.asarray(n) for n in noise_star_list) if isinstance(noise_star_list, list) else np.asarray(noise_star_list)
noise_exo_list = instrument.run_socket(s_name='photon_noise_universe', method='noise', index=i)
noise_exo_new = sum(np.asarray(n) for n in noise_exo_list) if isinstance(noise_exo_list, list) else np.asarray(noise_exo_list)

print("\nNEW analytic noise_star (star+localzodi) [:5]:", noise_star_new[:5])
print("NEW analytic noise_exo (base, z=1)        [:5]:", noise_exo_new[:5])
if isinstance(noise_star_list, list):
    print("noise_star_list components (full, per component):")
    for j, comp in enumerate(noise_star_list):
        print(f"  component {j}: {np.asarray(comp)}")

for IS in GRID_SIZES:
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

    if fov_taper == 'gaussian':
        ap = np.ones_like(radius_map)
    else:
        ap = np.where(radius_map <= IS / 2, 1, 0)

    lz_leak_old = (ap * tm3).sum(axis=(-2, -1)) / ap.sum() * lz_flux * telescope_area

    # star leak (old), scale star's own grid resolution with IS too (was hardcoded 50)
    IS_star = max(IS // 2, 50)
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

    noise_star_old = lz_leak_old + sl_leak_old

    rel_star = np.abs(noise_star_old - noise_star_new) / np.abs(noise_star_new)
    rel_lz = np.abs(lz_leak_old - 0) # placeholder, filled below once we separate new lz/star
    argmax = int(np.argmax(rel_star))
    print(f"\nIS={IS:5d} (star grid {IS_star}): "
          f"median rel diff (star+lz) = {np.median(rel_star):.3e}, "
          f"max = {rel_star.max():.3e} at wl_bin idx={argmax} (wl={wl_bins[argmax]*1e6:.3f} um)")
    print(f"   per-bin rel diff: {np.array2string(rel_star, precision=3)}")
    print(f"   old[:3]={noise_star_old[:3]}  new[:3]={noise_star_new[:3]}")
    print(f"   lz_leak_old full: {lz_leak_old}")
    print(f"   sl_leak_old full: {sl_leak_old}")

    # exozodi (old grid), scaled to this IS
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
    ez_leak_old = (f_nu_disk * tm3 * ap).sum(axis=(-2, -1))
    rel_exo = np.abs(ez_leak_old - noise_exo_new) / np.abs(noise_exo_new)
    print(f"   EXOZODI median rel diff = {np.median(rel_exo):.3e}, max = {rel_exo.max():.3e}")
    print(f"   ez_leak_old[:3]={ez_leak_old[:3]}  exo_new[:3]={noise_exo_new[:3]}")
