"""
AMS validation: compare the AMS SNR against the LIFEsim Instrument SNR.

The Agnostic Mission Simulator reimplements the astrophysical-noise physics of
LIFEsim in a vectorized, per-star-memoized form (``AgnosticMissionSimulator.get_snr``).
With no instrument noise -- i.e. the thermal and dark-current terms switched off,
which is the baseline default -- and no error budget applied, this must reproduce
the SNR of the standard LIFEsim ``Instrument.get_snr`` exactly, since both evaluate
the same stellar-leakage, local-zodi, exozodi and planet-signal terms.

This script computes both on the same catalog and reports the per-target relative
difference (mean, standard deviation, maximum). A vanishing difference validates
the SNR flow that underlies every trade-space result in the thesis.

Run with::

    python -m lifesim.analysis.test_scripts.validate_ams_snr
"""

import os

import numpy as np

# LIFEsim changes the working directory on import; switch back so CATALOG_PATH
# resolves against this file (same pattern as the sweep scripts).
working_directory = os.getcwd()
import lifesim
from lifesim import AgnosticMissionSimulator
os.chdir(working_directory)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CATALOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "..", "catalogs", "catalog_hab2hi.txt")

IMAGE_SIZE = 160               # converged plateau (see thesis image-size study)
SPEC_RES = 20                  # converged spectral resolution
N_SUB = 2000                   # random catalog subsample for a fast, well-sampled test
RNG_SEED = 0


def build_instrument():
    """Bus/instrument as in runner.py, with the thermal + dark-current modules
    present but left at their zero baseline so there is *no* instrument noise --
    exactly the regime in which the AMS must match LIFEsim."""
    bus = lifesim.Bus()

    bus.data.options.set_scenario('baseline')
    bus.data.catalog_from_ppop(input_path=CATALOG_PATH)
    bus.data.options.set_manual(image_size=IMAGE_SIZE, spec_res=float(SPEC_RES), n_cpu=1)

    # random subsample for a quick but statistically meaningful comparison
    cat = bus.data.catalog
    if N_SUB is not None and N_SUB < len(cat):
        bus.data.catalog = cat.sample(n=N_SUB, random_state=RNG_SEED).reset_index(drop=True)
        bus.data.catalog['id'] = range(len(bus.data.catalog))

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

    # explicitly zero the instrument-noise floor (baseline default, set for clarity)
    opt = instrument.data.options
    opt.array['dc_per_pix'] = 0.0
    opt.thermal['detector_temperature'] = 0.
    opt.thermal['ota_temperature'] = 0.
    opt.thermal['instrument_temperature'] = 0.

    instrument.apply_options()
    return bus, instrument


def main():
    bus, instrument = build_instrument()

    # --- Reference: standard LIFEsim Instrument SNR ---
    instrument.get_snr()
    inst_cat = instrument.data.catalog.sort_values('id')
    snr_inst = inst_cat['snr_1h'].to_numpy()

    # --- AMS SNR: default (empty) error budgets -> pure astrophysical, null order 2 ---
    ams = AgnosticMissionSimulator(nulling_order=2, lim_mag=99.,
                                   field_of_regard=np.pi / 2, science_overhead=0.8,
                                   slew_time=0.0, verbose=False)
    ams_cat = ams.get_snr(instrument, verbose=False).sort_values('id')
    snr_ams = ams_cat['snr_1h'].to_numpy()

    # --- Compare per target ---
    ok = snr_inst > 0
    rel = np.abs(snr_ams[ok] - snr_inst[ok]) / snr_inst[ok]

    print('\n=== AMS vs LIFEsim Instrument SNR (no instrument noise) ===')
    print(f'targets compared (SNR > 0): {int(ok.sum())}')
    print(f'mean   |dSNR|/SNR : {rel.mean():.3e}')
    print(f'std    |dSNR|/SNR : {rel.std():.3e}')
    print(f'median |dSNR|/SNR : {np.median(rel):.3e}')
    print(f'max    |dSNR|/SNR : {rel.max():.3e}')


if __name__ == '__main__':
    main()
