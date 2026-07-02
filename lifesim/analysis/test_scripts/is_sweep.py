"""
Image-size convergence sweep across detector-noise floors.

Companion to ``sr_sweep.py``. Where that script isolates the *spectral*
resolution, this one isolates the *image size* (spatial FOV sampling) that the
exozodi / localzodi background integrals are evaluated on
(``pn_exozodi.py`` / ``pn_localzodi.py`` sum over an ``image_size x image_size``
pixel grid).  The planet transmission (analytic spline) and the instrument
floor (dark current, thermal) do NOT depend on image size, so image size is a
pure numerical-discretization knob with a genuine converged limit -- unlike
spec_res under a floor, which has no plateau.

The spectral resolution is held fixed at ``FIXED_SPEC_RES=20`` and every trial
is compared, per planet, against a high-resolution spatial reference
(``REF_IMAGE_SIZE=512``) *at the same spec_res*, so the reported error is the
pure image-size discretization error, uncontaminated by the spec_res choice.

Running this for each detector-noise level demonstrates two things for the
thesis:
    * image_size=160 is converged (small error) in the background-limited
      regime LIFE is designed for, and
    * a per-channel floor only *dilutes* the image-size error (the floor is
      image-size-independent, so it grows the total noise while the spatial
      sampling error stays fixed) -- i.e. higher instrument noise makes the
      image-size choice *less* critical, the opposite of spec_res.

Run with::

    python -m lifesim.analysis.test_scripts.is_sweep
"""

import os

import numpy as np
import matplotlib.pyplot as plt

# reuse the exact bus/instrument + noise setup from the spec_res sweep so both
# studies share a single source of truth for the physics configuration.
from lifesim.analysis.test_scripts.sr_sweep import (
    build_instrument, set_noise_level, compute_snr, NOISE_LEVELS, LEVEL_LABELS,
)


# ---------------------------------------------------------------------------
# Configuration -- edit here
# ---------------------------------------------------------------------------
FIXED_SPEC_RES = 20                                # held fixed (SR shown safe)
IMAGE_SIZE_SWEEP = [50, 70, 91, 100, 113, 135,     # image sizes to test
                    156, 160, 178, 200, 256]
REF_IMAGE_SIZE = 512                               # spatial "truth"

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "is_sweep_out")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    bus, instrument = build_instrument()

    isz = np.array(IMAGE_SIZE_SWEEP, dtype=float)
    med_err = np.full((len(NOISE_LEVELS), len(isz)), np.nan)

    for li, level in enumerate(NOISE_LEVELS):
        set_noise_level(instrument, level)

        print(f'\n>> level={level!r}  {NOISE_LEVELS[level]}')
        snr_ref = compute_snr(instrument, REF_IMAGE_SIZE, FIXED_SPEC_RES)
        ok = snr_ref > 0

        for ii, s in enumerate(isz):
            snr = compute_snr(instrument, s, FIXED_SPEC_RES)
            rel = np.abs(snr[ok] - snr_ref[ok]) / snr_ref[ok]
            med_err[li, ii] = np.median(rel)
            print(f'   image_size={int(s):3d}: median |dSNR|/SNR = {med_err[li, ii]:.3e}')

        np.savez(os.path.join(OUT_DIR, 'is_sweep.npz'),
                 image_size=isz, med_err=med_err,
                 levels=np.array(list(NOISE_LEVELS.keys())),
                 ref_image_size=REF_IMAGE_SIZE, spec_res=FIXED_SPEC_RES)

    plot(isz, med_err, os.path.join(OUT_DIR, 'is_error_vs_imagesize.png'))


def plot(isz, med_err, save_path):
    fig, ax = plt.subplots(figsize=(7, 5))
    for li, level in enumerate(NOISE_LEVELS):
        ax.plot(isz, med_err[li], marker='o', label=LEVEL_LABELS[level])
    ax.axvline(160, color='0.6', ls='--', lw=1)
    ax.text(160, ax.get_ylim()[1], ' image_size=160', va='top', fontsize=8, color='0.4')
    ax.set_yscale('log')
    ax.set_xlabel('Image Square Length (pixels)')
    ax.set_ylabel(f'Median |ΔSNR| / SNR  vs  image_size={REF_IMAGE_SIZE}')
    ax.set_title(f'SNR error from spatial under-sampling (spec_res={FIXED_SPEC_RES})')
    ax.legend()
    ax.grid(True, which='both', alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f'\n>> Saved plot to {save_path}')
    if plt.get_backend().lower() != 'agg':
        plt.show()


# The __main__ guard is REQUIRED: get_snr uses joblib/loky multiprocessing,
# which re-imports this module in worker processes. Without the guard the
# workers would re-execute the sweep and spawn endlessly.
if __name__ == '__main__':
    main()
