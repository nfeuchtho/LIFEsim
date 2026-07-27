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
(see ``lifesim/util/options.py``), so the ``'off'`` level is flat vs. spec_res
by construction; the other levels turn the floor on with progressively larger
values.

NOTE: since the analytic noise rewrite (see ``ANALYTIC_NOISE_REWRITE.md``),
star/localzodi/exozodi noise no longer touch ``image_size`` at all -- it's a
pure per-wavelength-bin calculation now. So there is no ``image_size`` axis
left to sweep; this script (and the SNR itself) is only a function of
spec_res. The old 2D ``image_size`` x ``spec_res`` convergence map in
``snr_convergence.py`` is retired/legacy (pre-rewrite reference only).

This is deliberately light: it runs a random catalog subsample (``N_SUB``) on a
single image size across ``N_CPU`` cores, so the whole sweep runs in a few
minutes.

Run with::

    python -m lifesim.analysis.test_scripts.sr_sweep
"""

import os
import time

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
SPEC_RES_SWEEP = [5, 8, 10, 13, 15, 18, 20, 23, 25, 28, 30, 40,   # spec_res values
                  50, 55, 60, 65, 70, 75, 80, 85, 90, 93, 95, 98] # to test (2x density
                                                                  # vs. original; dense
                                                                  # near ref to see the
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


def compute_snr(instrument, spec_res):
    """Set spec_res, run the full-subsample SNR, return per-planet snr_1h
    sorted by catalog id (so trials line up element-wise with the reference).
    image_size is not a parameter here: the analytic noise rewrite made the
    noise physics independent of it (see module docstring)."""
    instrument.data.options.set_manual(spec_res=float(spec_res))
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
    # Per-level relative SNR error statistics across the catalog, vs each
    # level's own REF_SPEC_RES. The mean (or median) can converge to a small
    # value purely by averaging over many planets even while individual planets
    # remain badly off; the spread (std) is what actually certifies that *every*
    # planet is well sampled, not just the catalog on average.
    med_err = np.full((len(NOISE_LEVELS), len(sr)), np.nan)
    mean_err = np.full((len(NOISE_LEVELS), len(sr)), np.nan)
    std_err = np.full((len(NOISE_LEVELS), len(sr)), np.nan)
    # 16th/84th percentiles: the "1-sigma-equivalent" spread band. Unlike
    # mean +/- std it is always positive (the error distribution is one-sided),
    # so it plots cleanly on a log axis and does not need clipping.
    p16_err = np.full((len(NOISE_LEVELS), len(sr)), np.nan)
    p84_err = np.full((len(NOISE_LEVELS), len(sr)), np.nan)
    # Wall-clock time per compute_snr call. Physics cost doesn't depend on the
    # noise-level *values* (dc/thermal sockets always run, off level just feeds
    # them zeros), so this is really a spec_res-only timing; kept per-level
    # anyway so the plotted line/band is an average over len(NOISE_LEVELS)
    # repeated timings rather than a single noisy sample per spec_res.
    times = np.full((len(NOISE_LEVELS), len(sr)), np.nan)

    for li, level in enumerate(NOISE_LEVELS):
        set_noise_level(instrument, level)

        print(f'\n>> level={level!r}  {NOISE_LEVELS[level]}')
        snr_ref = compute_snr(instrument, REF_SPEC_RES)
        ok = snr_ref > 0

        for si, s in enumerate(sr):
            t0 = time.perf_counter()
            snr = compute_snr(instrument, s)
            times[li, si] = time.perf_counter() - t0
            rel = np.abs(snr[ok] - snr_ref[ok]) / snr_ref[ok]
            med_err[li, si] = np.median(rel)
            mean_err[li, si] = np.mean(rel)
            std_err[li, si] = np.std(rel)
            p16_err[li, si] = np.percentile(rel, 16)
            p84_err[li, si] = np.percentile(rel, 84)
            print(f'   spec_res={int(s):3d}: mean |dSNR|/SNR = {mean_err[li, si]:.3e}'
                  f'  std = {std_err[li, si]:.3e}  [p16,p84] = '
                  f'[{p16_err[li, si]:.3e}, {p84_err[li, si]:.3e}]'
                  f'  time = {times[li, si]:.3f} s')

        np.savez(os.path.join(OUT_DIR, 'sr_sweep.npz'),
                 spec_res=sr, med_err=med_err, mean_err=mean_err, std_err=std_err,
                 p16_err=p16_err, p84_err=p84_err, times=times,
                 levels=np.array(list(NOISE_LEVELS.keys())),
                 ref_spec_res=REF_SPEC_RES)

    plot(sr, mean_err, p16_err, p84_err, times,
         os.path.join(OUT_DIR, 'sr_error_vs_specres.png'))


LEVEL_COLORS = {
    'off':  'tab:blue',
    'low':  'tab:orange',
    'mid':  'tab:green',
    'high': 'tab:red',
}


def plot(sr, mean_err, p16_err, p84_err, times, save_path):
    """Mean per-planet relative SNR error (solid line) with a shaded 16th-84th
    percentile band showing the spread across the catalog. A low mean with a
    wide band would mean the catalog *average* has converged while individual
    planets have not -- the distinction the mean alone cannot show.

    Overlaid in the background (secondary y-axis, faint black line): compute
    time per spec_res, normalized to 1 at the lowest spec_res tried -- the
    cost side of the spec_res=20-is-enough argument, without a second panel
    competing for attention. Averaged over noise levels; the raw per-level
    spread is pure timing jitter (physics cost doesn't depend on the noise
    *values*, dc/thermal sockets run every time either way), not a real
    per-level effect, so it isn't worth plotting as a band.

    Title added ("Spectral Resolution" spelled out); axis/legend text uses the
    short form "SR" to keep labels compact."""
    with plt.rc_context({
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 13,
        'legend.fontsize': 10,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
    }):
        fig, ax = plt.subplots(figsize=(7, 4.5))
        for li, level in enumerate(NOISE_LEVELS):
            line, = ax.plot(sr, mean_err[li], color=LEVEL_COLORS[level],
                            label=LEVEL_LABELS[level], lw=1.8, zorder=3)
            ax.fill_between(sr, p16_err[li], p84_err[li],
                            color=line.get_color(), alpha=0.15, zorder=2)
        ax.axvline(20, color='0.6', ls='--', lw=1, zorder=1)
        ax.text(20.5, ax.get_ylim()[1], 'SR = 20', va='top', ha='left',
                fontsize=9, color='0.4')

        ax.set_yscale('log')
        ax.set_xlabel('Spectral Resolution (SR)')
        ax.set_ylabel(f'Relative SNR error (ref. SR = {REF_SPEC_RES})')
        ax.set_title('SNR sensitivity to spectral resolution across noise regimes')
        ax.grid(True, which='both', alpha=0.25)
        ax.set_axisbelow(True)

        time_norm = np.mean(times, axis=0)
        time_norm = time_norm / time_norm[0]
        ax_t = ax.twinx()
        ax_t.plot(sr, time_norm, color='black', alpha=0.22, lw=2.2, zorder=0)
        ax_t.set_ylabel(f'Normalized compute time (SR = {int(sr[0])} $\\rightarrow$ 1)',
                        color='0.45')
        ax_t.tick_params(axis='y', colors='0.45')
        ax_t.spines['right'].set_color('0.45')
        ax_t.set_ylim(bottom=1.0)

        ax.legend(loc='lower right', frameon=False)

        fig.tight_layout()
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f'\n>> Saved plot to {save_path}')
    if plt.get_backend().lower() != 'agg':
        plt.show()


# The __main__ guard is REQUIRED: get_snr uses joblib/loky multiprocessing,
# which re-imports this module in worker processes. Without the guard the
# workers would re-execute the sweep and spawn endlessly.
if __name__ == '__main__':
    main()
