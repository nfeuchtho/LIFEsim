"""Validate the wavenumber-quadrature bin integration (gauss_legendre_wavenumber,
wired into pn_star.py/pn_exozodi.py) against (a) the old center-point-per-bin
sample and (b) a very fine reference quadrature (n=64), across several spec_res
values and several stars (including tight/close-in habitable-zone systems where
kr = 2*pi*bl*r/wl is large and the chirp across a bin matters most)."""
import os

import numpy as np

working_directory = os.getcwd()
import lifesim
os.chdir(working_directory)
from lifesim.util.radiation import planck_law, black_body
from lifesim.util.transmission_analytic import (radial_average_tm, azimuthal_average_tm,
                                                 gauss_legendre_wavenumber)

_HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG_PATH = os.path.join(_HERE, "..", "..", "catalogs", "catalog_hab2hi.txt")
N_STARS = 15
SPEC_RES_LIST = [5, 10, 20, 50]
N_REF = 64


def build(spec_res):
    bus = lifesim.Bus()
    bus.data.options.set_scenario('baseline')
    bus.data.catalog_from_ppop(input_path=CATALOG_PATH)
    bus.data.options.set_manual(n_cpu=1, image_size=100, spec_res=float(spec_res))
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


def star_leak_center_point(instrument, radius_s, distance_s, temp_s, Rs_rad):
    fov_taper = instrument.data.options.models['fov_taper']
    avg_tm = radial_average_tm(R=Rs_rad, bl=instrument.data.inst['bl'],
                               wl_bins=instrument.data.inst['wl_bins'],
                               hfov=instrument.data.inst['hfov'], fov_taper=fov_taper)
    return avg_tm * black_body(bins=instrument.data.inst['wl_bins'],
                               width=instrument.data.inst['wl_bin_widths'],
                               temp=temp_s, radius=radius_s, distance=distance_s,
                               mode='star') * instrument.data.inst['telescope_area']


def star_leak_quadrature(instrument, radius_s, distance_s, temp_s, Rs_rad, n):
    fov_taper = instrument.data.options.models['fov_taper']
    diameter = instrument.data.options.array['diameter']
    bl = instrument.data.inst['bl']
    wl_lo = instrument.data.inst['wl_bin_edges'][:-1]
    wl_hi = instrument.data.inst['wl_bin_edges'][1:]
    wl_nodes, gl_weights = gauss_legendre_wavenumber(wl_lo, wl_hi, n=n)
    from lifesim.util import constants
    geom = np.pi * ((radius_s * constants.radius_sun) / (distance_s * constants.m_per_pc)) ** 2
    sl_leak = np.zeros_like(instrument.data.inst['wl_bins'])
    for wl_j, w_j in zip(wl_nodes, gl_weights):
        hfov_j = wl_j / (2. * diameter)
        avg_tm_j = radial_average_tm(R=Rs_rad, bl=bl, wl_bins=wl_j, hfov=hfov_j, fov_taper=fov_taper)
        planck_j = planck_law(x=wl_j, temp=temp_s, mode='wavelength') * geom
        sl_leak += w_j * avg_tm_j * planck_j
    return sl_leak * instrument.data.inst['telescope_area']


def exo_leak_quadrature(instrument, l_sun, distance_s, n):
    fov_taper = instrument.data.options.models['fov_taper']
    diameter = instrument.data.options.array['diameter']
    bl = instrument.data.inst['bl']
    wl_bins = instrument.data.inst['wl_bins']
    threshold = instrument.data.options.other['fov_threshold']

    alpha_ez = 0.34
    r_in = 0.034422617777777775 * np.sqrt(l_sun)
    r_0 = np.sqrt(l_sun)
    sigma_zero = 7.11889e-8
    au_per_rad = (3600. * 180. / np.pi) * distance_s
    r_in_rad = r_in / au_per_rad

    n_r = 200
    u = np.linspace(0.0, 1.0, n_r)[:, None]

    wl_lo = instrument.data.inst['wl_bin_edges'][:-1]
    wl_hi = instrument.data.inst['wl_bin_edges'][1:]
    wl_nodes, gl_weights = gauss_legendre_wavenumber(wl_lo, wl_hi, n=n)

    ez_leak = np.zeros_like(wl_bins)
    for wl_j, w_j in zip(wl_nodes, gl_weights):
        hfov_j = wl_j / (2. * diameter)
        if fov_taper == 'gaussian':
            image_angle_j = hfov_j * 4 / np.pi * np.sqrt(-np.log(threshold))
        else:
            image_angle_j = hfov_j
        outer_rad_j = np.maximum(image_angle_j, r_in_rad)
        log_ratio_j = np.log(outer_rad_j / r_in_rad)
        r_j = r_in_rad * np.exp(u * log_ratio_j[None, :])
        r_au_j = r_j * au_per_rad
        temp_map_j = 278.3 * (l_sun ** 0.25) / np.sqrt(r_au_j)
        sigma_j = sigma_zero * (r_au_j / r_0) ** (-alpha_ez)
        f_nu_sr_j = planck_law(x=wl_j[None, :], temp=temp_map_j, mode='wavelength') \
                    * sigma_j * instrument.data.inst['telescope_area']
        ang_avg_j = azimuthal_average_tm(r_j, bl, wl_j[None, :])
        if fov_taper == 'gaussian':
            taper_j = np.exp(-(np.pi / (4 * hfov_j[None, :]) * r_j) ** 2)
        else:
            taper_j = 1.0
        integrand_j = f_nu_sr_j * ang_avg_j * taper_j * r_j ** 2
        ez_leak_j = 2 * np.pi * log_ratio_j * np.trapz(integrand_j, u[:, 0], axis=0)
        ez_leak += w_j * ez_leak_j
    return ez_leak


def exo_leak_center_point(instrument, l_sun, distance_s):
    fov_taper = instrument.data.options.models['fov_taper']
    bl = instrument.data.inst['bl']
    wl_bins = instrument.data.inst['wl_bins']
    wl_bin_widths = instrument.data.inst['wl_bin_widths']
    image_angle = instrument.data.inst['image_angle']
    hfov = instrument.data.inst['hfov']

    alpha_ez = 0.34
    r_in = 0.034422617777777775 * np.sqrt(l_sun)
    r_0 = np.sqrt(l_sun)
    sigma_zero = 7.11889e-8
    au_per_rad = (3600. * 180. / np.pi) * distance_s
    r_in_rad = r_in / au_per_rad
    outer_rad = np.maximum(image_angle, r_in_rad)

    n_r = 200
    log_ratio = np.log(outer_rad / r_in_rad)
    u = np.linspace(0.0, 1.0, n_r)[:, None]
    r = r_in_rad * np.exp(u * log_ratio[None, :])
    r_au = r * au_per_rad
    temp_map = 278.3 * (l_sun ** 0.25) / np.sqrt(r_au)
    sigma = sigma_zero * (r_au / r_0) ** (-alpha_ez)
    f_nu_sr = black_body(bins=wl_bins[None, :], width=wl_bin_widths[None, :],
                         temp=temp_map, mode='wavelength') * sigma * instrument.data.inst['telescope_area']
    ang_avg = azimuthal_average_tm(r, bl, wl_bins[None, :])
    if fov_taper == 'gaussian':
        taper = np.exp(-(np.pi / (4 * hfov[None, :]) * r) ** 2)
    else:
        taper = 1.0
    integrand = f_nu_sr * ang_avg * taper * r ** 2
    return 2 * np.pi * log_ratio * np.trapz(integrand, u[:, 0], axis=0)


for spec_res in SPEC_RES_LIST:
    bus, instrument = build(spec_res)
    cat = instrument.data.catalog
    rng = np.random.default_rng(7)
    star_ids = cat['nstar'].unique()
    sample_ids = rng.choice(star_ids, size=min(N_STARS, len(star_ids)), replace=False)
    rows = [cat.index[cat['nstar'] == sid][0] for sid in sample_ids]

    worst_star_old, worst_star_new = 0.0, 0.0
    worst_exo_old, worst_exo_new = 0.0, 0.0
    worst_kr = 0.0

    for i in rows:
        hz_center = float(cat.iloc[i]['hz_center'])
        distance_s = float(cat.iloc[i]['distance_s'])
        instrument.adjust_bl_to_hz(hz_center=hz_center, distance_s=distance_s)

        radius_s = float(cat.iloc[i]['radius_s'])
        temp_s = float(cat.iloc[i]['temp_s'])
        l_sun = float(cat.iloc[i]['l_sun'])
        Rs_au = 0.00465047 * radius_s
        Rs_rad = (Rs_au / distance_s) / (3600. * 180.) * np.pi

        bl = instrument.data.inst['bl']
        wl_bins = instrument.data.inst['wl_bins']
        au_per_rad = (3600. * 180. / np.pi) * distance_s
        r_in = 0.034422617777777775 * np.sqrt(l_sun)
        r_in_rad = r_in / au_per_rad
        kr = 2 * np.pi * bl * r_in_rad / wl_bins.min()
        worst_kr = max(worst_kr, kr)

        star_ref = star_leak_quadrature(instrument, radius_s, distance_s, temp_s, Rs_rad, n=N_REF)
        star_new = star_leak_quadrature(instrument, radius_s, distance_s, temp_s, Rs_rad, n=8)
        star_old = star_leak_center_point(instrument, radius_s, distance_s, temp_s, Rs_rad)

        exo_ref = exo_leak_quadrature(instrument, l_sun, distance_s, n=N_REF)
        exo_new = exo_leak_quadrature(instrument, l_sun, distance_s, n=8)
        exo_old = exo_leak_center_point(instrument, l_sun, distance_s)

        rel_star_old = np.abs(star_old - star_ref) / np.abs(star_ref + 1e-300)
        rel_star_new = np.abs(star_new - star_ref) / np.abs(star_ref + 1e-300)
        rel_exo_old = np.abs(exo_old - exo_ref) / np.abs(exo_ref + 1e-300)
        rel_exo_new = np.abs(exo_new - exo_ref) / np.abs(exo_ref + 1e-300)

        worst_star_old = max(worst_star_old, np.nanmax(rel_star_old))
        worst_star_new = max(worst_star_new, np.nanmax(rel_star_new))
        worst_exo_old = max(worst_exo_old, np.nanmax(rel_exo_old))
        worst_exo_new = max(worst_exo_new, np.nanmax(rel_exo_new))

    print(f"spec_res={spec_res:5.0f}  worst kr_in={worst_kr:8.2f}  "
          f"star: old={worst_star_old:.3e} new(n=8)={worst_star_new:.3e}  "
          f"exo: old={worst_exo_old:.3e} new(n=8)={worst_exo_new:.3e}")
