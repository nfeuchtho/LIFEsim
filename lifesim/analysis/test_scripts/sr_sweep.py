"""
Spectral-resolution sensitivity sweep.

Question this answers: *can we just set spec_res=20?*  For the current,
photon-limited baseline (detector/thermal noise identically zero) the combined
one-hour SNR is provably independent of spectral resolution, so spec_res=20 is
bit-identical to spec_res=100.  The interesting case is when a per-channel
detector floor (dark current, thermal emission) is switched on: those terms do
NOT scale with the bin width, so finer binning splits a fixed noise floor across
more channels and the bulk SNR starts to depend on spec_res.

For every noise level we compute the per-planet bulk ``snr_1h`` on a fixed image
grid across a range of ``spec_res`` values and compare each against that same
level's high-resolution value (``REF_SPEC_RES``).  The reported metric is the
median relative SNR error, so ``err(spec_res=20)`` tells you exactly how
optimistic a spec_res=20 run is relative to the resolved truth.

The baseline scenario leaves ``dc_per_pix`` and all thermal temperatures at 0
(see ``lifesim/util/options.py``), so the ``'off'`` level reproduces the flat
behaviour seen in the image-size / spec-res convergence map; the other levels
turn the floor on with progressively larger values.

This is deliberately light: it runs a random catalog subsample (``N_SUB``) on a
single image size across ``N_CPU`` cores, so the whole sweep runs in a few
minutes.

Run with::

    python -m lifesim.analysis.test_scripts.sr_sweep
"""

import os

import numpy as np
import matplotlib.pyplot as plt

# LIFEsim changes the working directory on import, so switch back afterwards
# (same pattern as snr_convergence.py) -- CATALOG_PATH resolves against this dir.
working_directory = os.getcwd()
import lifesim
os.chdir(working_directory)


# ---------------------------------------------------------------------------
# Configuration -- edit here
# ---------------------------------------------------------------------------
# PPOP catalog, in the (gitignored) primary catalogs/ dir. Resolved absolutely
# so the sweep runs from any cwd.
CATALOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "..", "catalogs", "catalog_hab2hi.txt")

N_CPU = 8                                          # cores for multiprocessing SNR
IMAGE_SIZE = 160                                   # fixed (converged plateau)
SPEC_RES_SWEEP = [5, 10, 15, 20, 25, 30, 50,       # spec_res values to test
                  60, 70, 80, 90, 95]              # dense near ref to see the
                                                   # error dive as SR -> REF
REF_SPEC_RES = 100                                 # per-level "truth" (LIFE SR)

N_SUB = 400                    # random catalog subsample (SR sensitivity is a
RNG_SEED = 0                   # per-planet property; no need for the full cat)

# Detector-floor levels. 'off' = baseline (all zero -> flat, spec_res irrelevant).
# The others switch on the per-channel floor with growing strength. Values are
# illustrative knobs for the sweep, NOT calibrated LIFE numbers -- adjust freely.
#   dc  : dark current  [electron s-1 px-1]
#   det : detector environment temperature [K]
#   ota : OTA / mirror temperature [K]
#   ins : warm-instrument temperature [K]
NOISE_LEVELS = {
    'off':  dict(dc=0.0,  det=0.,  ota=0.,   ins=0.),
    'low':  dict(dc=0.01, det=11., ota=40.,  ins=40.),
    'mid':  dict(dc=1.0,  det=15., ota=70.,  ins=70.),
    'high': dict(dc=10.0, det=20., ota=100., ins=100.),
}

# Physical (thesis-facing) legend labels for each floor level. I/N = instrument
# noise (dark current + thermal) relative to the astrophysical background.
LEVEL_LABELS = {
    'off':  'no I/N',
    'low':  'bg-limited',
    'mid':  'I/N-limited',
    'high': 'I/N-dominated',
}

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sr_sweep_out")


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
def build_instrument():
    """Bus/instrument as in runner.py, plus the thermal + dark-current modules
    whose sockets get_snr consumes (otherwise those terms silently return 0)."""
    bus = lifesim.Bus()

    bus.data.options.set_scenario('baseline')
    bus.data.catalog_from_ppop(input_path=CATALOG_PATH)
    bus.data.options.set_manual(n_cpu=N_CPU)      # multiprocessing SNR path

    # random subsample -- SR sensitivity is a per-planet property
    cat = bus.data.catalog
    if N_SUB is not None and N_SUB < len(cat):
        bus.data.catalog = cat.sample(n=N_SUB, random_state=RNG_SEED).reset_index(drop=True)

    instrument = lifesim.Instrument(name='inst')
    bus.add_module(instrument)

    bus.add_module(lifesim.TransmissionMap(name='transm'))
    bus.add_module(lifesim.PhotonNoiseExozodi(name='exo'))
    bus.add_module(lifesim.PhotonNoiseLocalzodi(name='local'))
    bus.add_module(lifesim.PhotonNoiseStar(name='star'))
    bus.add_module(lifesim.PhotonNoiseThermal(name='thermal'))
    bus.add_module(lifesim.ElectronNoiseDarkCurrent(name='dc'))

    bus.connect(('inst', 'transm'))
    bus.connect(('inst', 'exo'))
    bus.connect(('inst', 'local'))
    bus.connect(('inst', 'star'))
    bus.connect(('star', 'transm'))
    bus.connect(('inst', 'thermal'))
    bus.connect(('inst', 'dc'))

    return bus, instrument


def set_noise_level(instrument, level):
    """Switch the per-channel detector floor on/off by writing the thermal
    temperatures and dark current directly into the options."""
    p = NOISE_LEVELS[level]
    opt = instrument.data.options
    opt.array['dc_per_pix'] = p['dc']
    opt.thermal['detector_temperature'] = p['det']
    opt.thermal['ota_temperature'] = p['ota']
    opt.thermal['instrument_temperature'] = p['ins']


def compute_snr(instrument, image_size, spec_res):
    """Set the resolution, run the full-subsample SNR, return per-planet snr_1h
    sorted by catalog id (so trials line up element-wise with the reference)."""
    instrument.data.options.set_manual(image_size=int(image_size),
                                       spec_res=float(spec_res))
    instrument.apply_options()
    instrument.get_snr()
    cat = instrument.data.catalog.sort_values('id')
    return cat['snr_1h'].to_numpy()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    bus, instrument = build_instrument()

    sr = np.array(SPEC_RES_SWEEP, dtype=float)
    # median relative SNR error vs each level's own REF_SPEC_RES
    med_err = np.full((len(NOISE_LEVELS), len(sr)), np.nan)

    for li, level in enumerate(NOISE_LEVELS):
        set_noise_level(instrument, level)

        print(f'\n>> level={level!r}  {NOISE_LEVELS[level]}')
        snr_ref = compute_snr(instrument, IMAGE_SIZE, REF_SPEC_RES)
        ok = snr_ref > 0

        for si, s in enumerate(sr):
            snr = compute_snr(instrument, IMAGE_SIZE, s)
            rel = np.abs(snr[ok] - snr_ref[ok]) / snr_ref[ok]
            med_err[li, si] = np.median(rel)
            print(f'   spec_res={int(s):3d}: median |dSNR|/SNR = {med_err[li, si]:.3e}')

        np.savez(os.path.join(OUT_DIR, 'sr_sweep.npz'),
                 spec_res=sr, med_err=med_err,
                 levels=np.array(list(NOISE_LEVELS.keys())),
                 ref_spec_res=REF_SPEC_RES, image_size=IMAGE_SIZE)

    plot(sr, med_err, os.path.join(OUT_DIR, 'sr_error_vs_specres.png'))


def plot(sr, med_err, save_path):
    fig, ax = plt.subplots(figsize=(7, 5))
    for li, level in enumerate(NOISE_LEVELS):
        ax.plot(sr, med_err[li], marker='o', label=LEVEL_LABELS[level])
    ax.axvline(20, color='0.6', ls='--', lw=1)
    ax.text(20, ax.get_ylim()[1], ' spec_res=20', va='top', fontsize=8, color='0.4')
    ax.set_yscale('log')
    ax.set_xlabel('Spectral Resolution')
    ax.set_ylabel(f'Median |ΔSNR| / SNR  vs  spec_res={REF_SPEC_RES}')
    ax.set_title(f'SNR error from under-resolving (image_size={IMAGE_SIZE})')
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
