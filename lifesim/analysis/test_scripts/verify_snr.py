"""
Verify the instrument SNR against the AMS SNR.

``Instrument.get_snr`` (-> ``get_snr_single_processing``) was ported from
``AgnosticMissionSimulator.get_snr``. This script checks the port reproduces
the AMS result on an identical instrument/catalog.

IMPORTANT -- the new non-astrophysical noise sources (thermal OTA / instrument /
detector emission and detector dark current) are intentionally NOT connected
here. The AMS does not model them (by design), so including them would make the
comparison meaningless. With ``PhotonNoiseThermal`` / ``ElectronNoiseDarkCurrent``
left unconnected, the ``photon_noise_instrument`` and ``electron_noise_detector``
sockets return nothing and those noise terms are exactly zero -- matching the
AMS, which then differs from the instrument only in code path, not in physics.

The AMS is run with default (identity) error budgets and nulling order 2
(double Bracewell), so both paths compute the same pure astrophysical-noise SNR.

"""

import os

import numpy as np

# LIFEsim changes the working directory on import, so switch back afterwards.
working_directory = os.getcwd()
import lifesim
from lifesim import AgnosticMissionSimulator
os.chdir(working_directory)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# catalogs/ lives next to this script (lifesim/ams/), so resolve relative to it
# -> runnable regardless of the current working directory.
_HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG_PATH = os.path.join(_HERE, "..", "..", "catalogs", "catalog_hab2hi.txt")
IMAGE_SIZE = 100        # same resolution for both paths -> physics must match
SPEC_RES = 10
SAVE_PLOT = True        # save an inst-vs-AMS scatter to convergence_out/


def build_instrument():
    """Bus/instrument with the astrophysical noise sources only -- thermal and
    dark-current modules are deliberately omitted to match the AMS."""
    bus = lifesim.Bus()

    bus.data.options.set_scenario('baseline')
    bus.data.catalog_from_ppop(input_path=CATALOG_PATH)
    # n_cpu=1 -> single-process path, trivial ordering, no MP overhead for a check
    bus.data.options.set_manual(n_cpu=1,
                                image_size=IMAGE_SIZE,
                                spec_res=float(SPEC_RES))

    instrument = lifesim.Instrument(name='inst')
    bus.add_module(instrument)

    bus.add_module(lifesim.TransmissionMap(name='transm'))
    bus.add_module(lifesim.PhotonNoiseExozodi(name='exo'))
    bus.add_module(lifesim.PhotonNoiseLocalzodi(name='local'))
    bus.add_module(lifesim.PhotonNoiseStar(name='star'))
    # NOTE: PhotonNoiseThermal / ElectronNoiseDarkCurrent intentionally NOT added.

    bus.connect(('inst', 'transm'))
    bus.connect(('inst', 'exo'))
    bus.connect(('inst', 'local'))
    bus.connect(('inst', 'star'))
    bus.connect(('star', 'transm'))

    return bus, instrument


def main():
    bus, instrument = build_instrument()
    instrument.apply_options()

    # --- AMS SNR: identity error budgets, nulling order 2 (double Bracewell) ---
    # lim_mag / field_of_regard / science_overhead / slew_time only matter in
    # ams.run(); get_snr ignores them, so any harmless values are fine here.
    ams = AgnosticMissionSimulator(nulling_order=2,
                                   lim_mag=0.0,
                                   field_of_regard=0.0,
                                   science_overhead=0.8,
                                   slew_time=0.0,
                                   verbose=False,
                                   plot_id=None)
    cat_ams = ams.get_snr(instrument, verbose=False)
    snr_ams = cat_ams.sort_values('id')['snr_1h'].to_numpy()

    # --- Instrument SNR: new function, non-astro noise disabled by omission ---
    instrument.get_snr()
    snr_inst = instrument.data.catalog.sort_values('id')['snr_1h'].to_numpy()

    # --- Compare (aligned by catalog id) ---
    assert snr_ams.size == snr_inst.size, 'catalogs differ in length'

    diff = snr_inst - snr_ams
    abs_diff = np.abs(diff)
    mask = snr_ams > 1e-6
    rel = np.full_like(snr_ams, np.nan)
    rel[mask] = abs_diff[mask] / snr_ams[mask]

    print('\n================ instrument vs AMS SNR ================')
    print(f'planets compared      : {snr_ams.size}')
    print(f'max |dSNR|            : {abs_diff.max():.3e}')
    print(f'mean |dSNR|           : {abs_diff.mean():.3e}')
    print(f'RMSD                  : {np.sqrt(np.mean(diff ** 2)):.3e}')
    print(f'max relative diff     : {np.nanmax(rel):.3e}')
    print(f'median relative diff  : {np.nanmedian(rel):.3e}')

    order = np.argsort(abs_diff)[::-1][:5]
    print('\nlargest absolute deviations:')
    for idx in order:
        print(f'  row {idx:6d}: inst={snr_inst[idx]:.5f}  ams={snr_ams[idx]:.5f}  '
              f'd={diff[idx]:+.2e}  rel={rel[idx]:.2e}')

    # crude pass/fail: agreement to better than 0.1% in the bulk
    ok = np.nanmedian(rel) < 1e-3 and np.nanmax(rel[np.isfinite(rel)]) < 1e-2
    print(f'\nVERDICT: {"PASS" if ok else "CHECK"} '
          f'(median rel < 1e-3 and max rel < 1e-2)')
    print('======================================================\n')

    if SAVE_PLOT:
        import matplotlib
        matplotlib.use('Agg')   # no GUI, just write the file
        import matplotlib.pyplot as plt

        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'convergence_out')
        os.makedirs(out_dir, exist_ok=True)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))

        lim = max(snr_ams.max(), snr_inst.max())
        ax1.plot([0, lim], [0, lim], 'k--', lw=1, label='1:1')
        ax1.scatter(snr_ams, snr_inst, s=4, alpha=0.3)
        ax1.set_xlabel('AMS SNR')
        ax1.set_ylabel('Instrument SNR')
        ax1.set_title('SNR: instrument vs AMS')
        ax1.legend()

        ax2.hist(rel[np.isfinite(rel)], bins=60)
        ax2.set_xlabel('relative |dSNR| / SNR$_{AMS}$')
        ax2.set_ylabel('planets')
        ax2.set_title('Relative deviation')

        out = os.path.join(out_dir, 'verify_snr_inst_vs_ams.png')
        fig.savefig(out, dpi=150, bbox_inches='tight')
        print(f'>> Saved comparison plot to {out}')


if __name__ == '__main__':
    main()
