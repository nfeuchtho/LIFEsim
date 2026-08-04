"""
Generate transmission-map illustration figures for the thesis background,
straight from LIFEsim's own TransmissionMap module (no external/paper figure).

Outputs into thesis/images/intro/:
  transmission_maps.png   -- destructive output (tm4) + chopped map (tm3-tm4)
  transmission_modulation.png -- planet transmission curve vs array rotation
"""
import os

working_directory = os.getcwd()
import numpy as np
import lifesim
os.chdir(working_directory)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = os.path.abspath(os.path.join(
    working_directory, "thesis", "images", "intro"))
os.makedirs(OUT, exist_ok=True)

IMAGE_SIZE = 512

# --- build a minimal bus with the transmission module + instrument ----------
bus = lifesim.Bus()
bus.data.options.set_scenario('baseline')
bus.data.options.set_manual(image_size=IMAGE_SIZE, spec_res=10.)

instrument = lifesim.Instrument(name='inst')
transm = lifesim.TransmissionMap(name='transm')
bus.add_module(instrument)
bus.add_module(transm)
bus.connect(('inst', 'transm'))
instrument.apply_options()

# pick one representative wavelength bin (~10 micron)
wl_bins = bus.data.inst['wl_bins']
idx = int(np.argmin(np.abs(wl_bins - 10e-6)))
wl = wl_bins[idx]
bl = bus.data.inst['bl']
print(f'using wl bin {idx}: {wl*1e6:.2f} micron, baseline {bl} m')

# zoom the field of view to a few fringes so the pattern is legible
# (the full instrument FoV is ~1400 mas -> a fine barcode at ratio 6).
ZOOM_MAS = 300.0
image_angle = ZOOM_MAS / 1000.0 / 3600.0 / 180.0 * np.pi   # rad
hfov = image_angle

# demo planet on first bright nulling fringe, alpha = wl/(2*bl)
r_peak_mas = wl / (2.0 * bl) * (3600000. * 180.) / np.pi
angsep_arcsec = r_peak_mas / 1000.0
# temporarily reduce the module to a single wl so the maps/curves are 2D
bus.data.inst['wl_bins'] = np.array([wl])
bus.data.inst['hfov'] = np.array([hfov])
bus.data.inst['image_angle'] = np.array([image_angle])

_, _, tm3, tm4, tm_chop = transm.transmission_map(
    map_selection=['tm3', 'tm4', 'tm_chop'],
    hfov=np.array([hfov]),
    image_angle=np.array([image_angle]),
    image_size=IMAGE_SIZE,
    fov_taper='none')

tm4 = np.squeeze(tm4)
tm_chop = np.squeeze(tm_chop)

# axis extent in milli-arcseconds
ext_mas = image_angle * (3600000. * 180.) / np.pi
extent = [-ext_mas, ext_mas, -ext_mas, ext_mas]

# =====================================================================
# Figure 1: single destructive output + chopped map
# =====================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))

im1 = ax1.imshow(tm4, origin='lower', extent=extent, cmap='inferno')
ax1.set_title('Single destructive output')
ax1.set_xlabel(r'$\alpha$ [mas]')
ax1.set_ylabel(r'$\beta$ [mas]')
ax1.plot(0, 0, 'c*', ms=15, mec='k', mew=0.6, label='star (on null)')
ax1.plot(r_peak_mas, 0, 'o', color='lime', ms=8, mec='k', mew=0.6,
         label='planet')
ax1.legend(loc='upper right', fontsize=8, framealpha=0.9)
fig.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04, label='transmission')

vmax = np.abs(tm_chop).max()
im2 = ax2.imshow(tm_chop, origin='lower', extent=extent, cmap='RdBu_r',
                 vmin=-vmax, vmax=vmax)
ax2.set_title('Chopped map (difference of two outputs)')
ax2.set_xlabel(r'$\alpha$ [mas]')
ax2.set_ylabel(r'$\beta$ [mas]')
ax2.plot(0, 0, 'y*', ms=15, mec='k', mew=0.6)
ax2.plot(r_peak_mas, 0, 'o', color='lime', ms=8, mec='k', mew=0.6)
# dashed circle: path the planet traces as the array rotates
th = np.linspace(0, 2*np.pi, 200)
ax2.plot(r_peak_mas*np.cos(th), r_peak_mas*np.sin(th), 'k--', lw=0.8, alpha=0.6)
fig.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04, label='differential response')

fig.tight_layout()
p1 = os.path.join(OUT, 'transmission_maps.png')
fig.savefig(p1, dpi=150, bbox_inches='tight')
print('saved', p1)

# =====================================================================
# Figure 2: rotational modulation of a planet at fixed angular separation
# =====================================================================
# place the demo planet on the first bright fringe of the nulling direction,
# alpha = wl/(2*bl) in rad -> a clean, few-lobe modulation as the array rotates
r_peak_mas = wl / (2.0 * bl) * (3600000. * 180.) / np.pi
angsep_arcsec = r_peak_mas / 1000.0
print(f'planet angsep for modulation demo: {r_peak_mas:.1f} mas')

# reset wl_bins for the curve routine (uses single wl already set)
chop_curve, tm4_curve = transm.transmission_curve(angsep=angsep_arcsec, phi_n=360)
chop_curve = np.squeeze(chop_curve)
tm4_curve = np.squeeze(tm4_curve)
phi_deg = np.linspace(0, 360, chop_curve.size, endpoint=False)

fig2, ax = plt.subplots(figsize=(7.5, 4.2))
ax.axhline(0, color='0.6', lw=0.8)
ax.plot(phi_deg, chop_curve, color='C3', lw=2,
        label='planet signal (chopped)')
ax.plot(phi_deg, tm4_curve, color='C0', lw=1.4, ls='--',
        label='single output (unchopped)')
ax.set_xlabel('array rotation angle [deg]')
ax.set_ylabel('transmission')
ax.set_xlim(0, 360)
ax.set_title(f'Rotational modulation of a planet at {r_peak_mas:.0f} mas')
ax.legend(loc='upper right', fontsize=9)
fig2.tight_layout()
p2 = os.path.join(OUT, 'transmission_modulation.png')
fig2.savefig(p2, dpi=150, bbox_inches='tight')
print('saved', p2)
