"""
Convergence study: SNR vs. image size and spectral resolution.

Re-computes the image-size / spectral-resolution convergence map
(cf. ``lifesim/ams/legacy_plots/snr_imagesize_specres.png``) for the *current*
SNR implementation (``Instrument.get_snr`` -> ``get_snr_single_processing``),
which now also accounts for the non-astrophysical noise sources:

    * thermal emission of OTA / instrument / detector  (PhotonNoiseThermal,
      connected to the ``photon_noise_instrument`` socket), and
    * detector dark current                            (ElectronNoiseDarkCurrent,
      connected to the ``electron_noise_detector`` socket).

These two modules are NOT added in ``runner.py``, so they must be added and
connected here -- otherwise those sockets return nothing and the new noise
terms silently contribute zero.

For every (image_size, spec_res) grid point the one-hour SNR of the whole
catalog is computed and compared, per planet, against a high-resolution
reference (``REF_IMAGE_SIZE``, ``REF_SPEC_RES``). The reported metric is the
bulk RMSD of the SNR across the catalog, matching the legacy definition
``sqrt(mean((snr - snr_ref) ** 2))``.

This is intentionally a heavy, long-running script: the reference alone
(spec_res=100, image_size=512) is expensive, and the grid runs ``get_snr`` once
per node. The RMSD grid is check-pointed to disk after every node so a run can
be inspected / resumed and a crash does not lose progress.

Run with::

    python -m lifesim.analysis.test_scripts.snr_convergence
"""

import os
import time

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from scipy.interpolate import RegularGridInterpolator
import cmocean.cm as cmo

# LIFEsim changes the working directory on import, so switch back afterwards
# (same pattern as runner.py) -- CATALOG_PATH is resolved against this dir.
working_directory = os.getcwd()
import lifesim
os.chdir(working_directory)


# ---------------------------------------------------------------------------
# Configuration -- edit here
# ---------------------------------------------------------------------------
CATALOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "..", "catalogs", "catalog_hab2hi.txt")  # PPOP catalog
N_CPU = 25                                      # cores for the multiprocessing SNR

# Trial grid (axes of the convergence map). Kept comparable to the legacy plot
# so old/new maps can be compared directly.
IMAGE_SIZES = np.unique(np.linspace(5, 200, 10).astype(int))   # x-axis (pixels)
SPEC_RES = np.unique(np.linspace(5, 50, 10).astype(int))       # y-axis

# High-resolution reference ("ground truth"). This is the slow one.
REF_IMAGE_SIZE = 512
REF_SPEC_RES = 100

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "convergence_out")


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
def build_instrument():
    """Build the bus/instrument exactly as in runner.py, plus the two
    non-astrophysical noise modules the new SNR function relies on."""
    bus = lifesim.Bus()

    bus.data.options.set_scenario('baseline')
    bus.data.catalog_from_ppop(input_path=CATALOG_PATH)
    bus.data.options.set_manual(n_cpu=N_CPU)

    instrument = lifesim.Instrument(name='inst')
    bus.add_module(instrument)

    # transmission map + astrophysical noise sources (as in runner.py)
    bus.add_module(lifesim.TransmissionMap(name='transm'))
    bus.add_module(lifesim.PhotonNoiseExozodi(name='exo'))
    bus.add_module(lifesim.PhotonNoiseLocalzodi(name='local'))
    bus.add_module(lifesim.PhotonNoiseStar(name='star'))

    # NEW: non-astrophysical noise sources now included in get_snr
    bus.add_module(lifesim.PhotonNoiseThermal(name='thermal'))
    bus.add_module(lifesim.ElectronNoiseDarkCurrent(name='dc'))

    bus.connect(('inst', 'transm'))
    bus.connect(('inst', 'exo'))
    bus.connect(('inst', 'local'))
    bus.connect(('inst', 'star'))
    bus.connect(('star', 'transm'))
    bus.connect(('inst', 'thermal'))   # -> photon_noise_instrument socket
    bus.connect(('inst', 'dc'))        # -> electron_noise_detector socket

    return bus, instrument


def compute_snr(instrument, image_size, spec_res):
    """Set the resolution, run the full-catalog SNR, and return the per-planet
    SNR sorted by catalog ``id`` (so reference and trials line up element-wise).

    ``get_snr`` calls ``apply_options`` internally, which regenerates the
    wavelength bins (from ``spec_res``) and the radius map (from ``image_size``).
    """
    instrument.data.options.set_manual(image_size=int(image_size),
                                       spec_res=float(spec_res))
    instrument.apply_options()
    instrument.get_snr()
    cat = instrument.data.catalog.sort_values('id')
    return cat['snr_1h'].to_numpy()


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
def _fine_grid(data, n=500):
    """Interpolate a (len(SPEC_RES), len(IMAGE_SIZES)) array onto an n×n grid."""
    interp = RegularGridInterpolator((SPEC_RES, IMAGE_SIZES), data, method='slinear',
                                     bounds_error=False, fill_value=None)
    si_fine = np.linspace(IMAGE_SIZES[0], IMAGE_SIZES[-1], n)
    sr_fine = np.linspace(SPEC_RES[0], SPEC_RES[-1], n)
    Xf, Yf = np.meshgrid(si_fine, sr_fine)
    return si_fine, sr_fine, Xf, Yf, interp((Yf, Xf))


def plot_map(rmsd, times, save_path):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    ax_rmsd, ax_time = axes

    extent = (IMAGE_SIZES[0], IMAGE_SIZES[-1], SPEC_RES[0], SPEC_RES[-1])

    # --- left panel: RMSD heatmap + contour lines ---
    si_f, sr_f, Xf, Yf, rmsd_fine = _fine_grid(rmsd)

    im = ax_rmsd.imshow(rmsd_fine, norm=LogNorm(), extent=extent,
                        origin='lower', aspect='auto', cmap=cmo.thermal)
    cbar = fig.colorbar(im, ax=ax_rmsd, orientation='vertical')
    cbar.set_label('Bulk SNR RMSD')

    r_min, r_max = np.nanmin(rmsd_fine), np.nanmax(rmsd_fine)
    r_exp_lo, r_exp_hi = np.floor(np.log10(r_min)), np.ceil(np.log10(r_max))
    rmsd_levels = [v for v in np.logspace(r_exp_lo, r_exp_hi, int(r_exp_hi - r_exp_lo) + 1)
                   if r_min < v < r_max]
    if rmsd_levels:
        cs = ax_rmsd.contour(Xf, Yf, rmsd_fine, levels=rmsd_levels,
                             colors='white', linewidths=1.2, linestyles='solid')
        ax_rmsd.clabel(cs, fmt={v: str(v) for v in rmsd_levels},
                       inline=True, fontsize=8)

    ax_rmsd.set_xlabel('Image Square Length (pixels)')
    ax_rmsd.set_ylabel('Spectral Resolution')
    ax_rmsd.set_title('SNR RMSD (incl. thermal + dark-current noise)')

    # --- right panel: computation time heatmap + iso-time contours ---
    if times is not None and not np.all(np.isnan(times)):
        _, _, _, _, time_fine = _fine_grid(times)

        im_t = ax_time.imshow(time_fine, norm=LogNorm(), extent=extent,
                              origin='lower', aspect='auto', cmap=cmo.thermal)
        cbar_t = fig.colorbar(im_t, ax=ax_time, orientation='vertical')
        cbar_t.set_label('Wall-Clock Time (s)')

        t_min, t_max = np.nanmin(time_fine), np.nanmax(time_fine)
        exp_lo, exp_hi = np.floor(np.log10(t_min)), np.ceil(np.log10(t_max))
        time_levels = [v for v in np.logspace(exp_lo, exp_hi, int(exp_hi - exp_lo) + 1)
                       if t_min < v < t_max]
        if time_levels:
            cs_t = ax_time.contour(Xf, Yf, time_fine, levels=time_levels,
                                   colors='white', linewidths=1.2, linestyles='dashed')
            ax_time.clabel(cs_t, fmt={v: f'{v:.4g} s' for v in time_levels},
                           inline=True, fontsize=8)
    else:
        ax_time.text(0.5, 0.5, 'No timing data', ha='center', va='center',
                     transform=ax_time.transAxes)

    ax_time.set_xlabel('Image Square Length (pixels)')
    ax_time.set_ylabel('Spectral Resolution')
    ax_time.set_title(f'Parallelized Computation Time ({N_CPU} cores)')

    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f'>> Saved plot to {save_path}')
    if plt.get_backend().lower() != 'agg':
        plt.show()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    bus, instrument = build_instrument()

    print(f'>> Computing reference SNR '
          f'(image_size={REF_IMAGE_SIZE}, spec_res={REF_SPEC_RES}) -- this is slow ...')
    snr_ref = compute_snr(instrument, REF_IMAGE_SIZE, REF_SPEC_RES)
    np.save(os.path.join(OUT_DIR, 'snr_ref.npy'), snr_ref)
    print(f'>> Reference done ({snr_ref.size} planets).')

    rmsd  = np.full((len(SPEC_RES), len(IMAGE_SIZES)), np.nan)
    times = np.full((len(SPEC_RES), len(IMAGE_SIZES)), np.nan)
    n_total = len(SPEC_RES) * len(IMAGE_SIZES)

    for i, res in enumerate(SPEC_RES):
        for j, size in enumerate(IMAGE_SIZES):
            k = i * len(IMAGE_SIZES) + j + 1
            print(f'\n>> [{k}/{n_total}] spec_res={int(res)}, '
                  f'image_size={int(size)}x{int(size)}')

            t0 = time.perf_counter()
            snr = compute_snr(instrument, size, res)
            times[i, j] = time.perf_counter() - t0

            rmsd[i, j] = np.sqrt(np.mean((snr - snr_ref) ** 2))
            print(f'>> RMSD = {rmsd[i, j]:.4g}   time = {times[i, j]:.2f} s')

            # check-point after every node so a long run can be resumed/inspected
            np.savez(os.path.join(OUT_DIR, 'rmsd_grid.npz'),
                     rmsd=rmsd,
                     times=times,
                     image_sizes=IMAGE_SIZES,
                     spec_res=SPEC_RES,
                     ref_image_size=REF_IMAGE_SIZE,
                     ref_spec_res=REF_SPEC_RES)

    plot_map(rmsd, times, os.path.join(OUT_DIR, 'snr_imagesize_specres_new.png'))


# The __main__ guard is REQUIRED: get_snr uses joblib/loky multiprocessing,
# which re-imports this module in worker processes. Without the guard the
# workers would re-execute the study and spawn endlessly.
if __name__ == '__main__':
    main()
