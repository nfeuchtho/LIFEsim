"""
The image-size aliasing trap (discussion figure).

``is_sweep.py`` reports only the *median* absolute SNR error vs image size and,
read naively, shows a tempting ~1-OoM dip at image_size~100. This script shows
that dip is an **aliasing resonance, not convergence**: the exozodi/localzodi
FOV integral is sampled on an ``image_size x image_size`` grid, and the disk
inner-radius mask (``r_au <= image_size/2``) beats against the grid, so the
per-planet error *oscillates* with image size instead of decreasing
monotonically. At a few sizes (image_size~100) the whole error distribution
momentarily tightens by coincidence -- but the immediate neighbours blow up
again, so it is fragile (moves with catalog / disk model / reference).

To expose this we report, per image size, not just the median |error| but the
spread of the per-planet error: the 90th percentile and the RMS. Genuine
convergence drives median, p90 AND rms down together and keeps them down for
all larger sizes; a resonance notch tightens the median while the neighbours
stay large. The plot marks the trap (image_size=100) and the true plateau
(image_size=160).

Run on the ``no I/N`` floor -- the background-limited regime LIFE is designed
for, which is the worst (largest) case for the image-size error and gives the
cleanest resonance signature.

Run with::

    python -m lifesim.analysis.test_scripts.is_trap
"""

import os

import numpy as np
import matplotlib.pyplot as plt

from lifesim.analysis.test_scripts.sr_sweep import (
    build_instrument, set_noise_level, compute_snr,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
FIXED_SPEC_RES = 20
REF_IMAGE_SIZE = 512
FLOOR = 'off'                                       # 'no I/N' -- worst case for IS
IMAGE_SIZE_SWEEP = [50, 70, 91, 100, 113, 125,     # dense through the resonance
                    135, 145, 156, 160, 178, 200, 256]

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "is_sweep_out")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    bus, instrument = build_instrument()
    set_noise_level(instrument, FLOOR)

    isz = np.array(IMAGE_SIZE_SWEEP, dtype=float)
    med = np.full_like(isz, np.nan)      # median |error|
    p90 = np.full_like(isz, np.nan)      # 90th-percentile |error|
    rms = np.full_like(isz, np.nan)      # RMS error (whole population)

    snr_ref = compute_snr(instrument, REF_IMAGE_SIZE, FIXED_SPEC_RES)
    ok = snr_ref > 0
    ref = snr_ref[ok]

    for i, s in enumerate(isz):
        e = (compute_snr(instrument, s, FIXED_SPEC_RES)[ok] - ref) / ref
        med[i] = np.median(np.abs(e))
        p90[i] = np.percentile(np.abs(e), 90)
        rms[i] = np.sqrt(np.mean(e ** 2))
        print(f'   image_size={int(s):3d}: med={med[i]:.2e}  p90={p90[i]:.2e}  rms={rms[i]:.2e}')

    np.savez(os.path.join(OUT_DIR, 'is_trap.npz'),
             image_size=isz, med=med, p90=p90, rms=rms,
             ref_image_size=REF_IMAGE_SIZE, spec_res=FIXED_SPEC_RES, floor=FLOOR)

    plot(isz, med, p90, rms, os.path.join(OUT_DIR, 'is_aliasing_trap.png'))


def plot(isz, med, p90, rms, save_path):
    fig, ax = plt.subplots(figsize=(7.5, 5))

    ax.plot(isz, med, marker='o', color='tab:blue',   label='median |ΔSNR|/SNR')
    ax.plot(isz, p90, marker='s', color='tab:orange', label='90th percentile')
    ax.plot(isz, rms, marker='^', color='tab:red',    label='RMS (whole catalog)')

    ax.axvline(100, color='tab:red',  ls=':',  lw=1.4)
    ax.axvline(160, color='tab:green', ls='--', lw=1.4)
    ymax = ax.get_ylim()[1]
    ax.text(100, ymax, ' trap:\n image_size=100', va='top', ha='left',
            fontsize=8, color='tab:red')
    ax.text(160, ymax, ' plateau:\n image_size=160', va='top', ha='left',
            fontsize=8, color='tab:green')

    ax.set_yscale('log')
    ax.set_xlabel('Image Square Length (pixels)')
    ax.set_ylabel(f'per-planet SNR error  vs  image_size={REF_IMAGE_SIZE}')
    ax.set_title('Image-size aliasing trap (no I/N, spec_res=20)')
    ax.legend()
    ax.grid(True, which='both', alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f'\n>> Saved plot to {save_path}')
    if plt.get_backend().lower() != 'agg':
        plt.show()


# The __main__ guard is REQUIRED: get_snr uses joblib/loky multiprocessing,
# which re-imports this module in worker processes.
if __name__ == '__main__':
    main()
