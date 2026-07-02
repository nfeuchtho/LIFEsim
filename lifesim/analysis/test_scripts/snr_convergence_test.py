"""
Quick test run of snr_convergence with a tiny 4x4 grid and a modest reference.
Purpose: preview the two-panel plot layout without waiting for the full grid.
"""
import os
import sys

# Patch the module-level constants before importing the functions
import lifesim.analysis.test_scripts.snr_convergence as sc

import numpy as np

sc.IMAGE_SIZES = np.array([10, 30, 60, 100])
sc.SPEC_RES    = np.array([5, 10, 20, 35])
sc.REF_IMAGE_SIZE = 150
sc.REF_SPEC_RES   = 50
_HERE = os.path.dirname(os.path.abspath(__file__))
sc.CATALOG_PATH = os.path.join(_HERE, "..", "..", "catalogs", "catalog_hab2hi.txt")
sc.OUT_DIR = os.path.join(_HERE, "convergence_out_test")

import time

if __name__ == '__main__':
    os.makedirs(sc.OUT_DIR, exist_ok=True)

    bus, instrument = sc.build_instrument()

    print(f'>> Computing reference SNR '
          f'(image_size={sc.REF_IMAGE_SIZE}, spec_res={sc.REF_SPEC_RES}) ...')
    snr_ref = sc.compute_snr(instrument, sc.REF_IMAGE_SIZE, sc.REF_SPEC_RES)
    print(f'>> Reference done ({snr_ref.size} planets).')

    rmsd  = np.full((len(sc.SPEC_RES), len(sc.IMAGE_SIZES)), np.nan)
    times = np.full((len(sc.SPEC_RES), len(sc.IMAGE_SIZES)), np.nan)
    n_total = len(sc.SPEC_RES) * len(sc.IMAGE_SIZES)

    for i, res in enumerate(sc.SPEC_RES):
        for j, size in enumerate(sc.IMAGE_SIZES):
            k = i * len(sc.IMAGE_SIZES) + j + 1
            print(f'\n>> [{k}/{n_total}] spec_res={int(res)}, image_size={int(size)}x{int(size)}')
            t0 = time.perf_counter()
            snr = sc.compute_snr(instrument, size, res)
            times[i, j] = time.perf_counter() - t0
            rmsd[i, j] = np.sqrt(np.mean((snr - snr_ref) ** 2))
            print(f'>> RMSD = {rmsd[i, j]:.4g}   time = {times[i, j]:.2f} s')
            np.savez(os.path.join(sc.OUT_DIR, 'rmsd_grid.npz'),
                     rmsd=rmsd, times=times,
                     image_sizes=sc.IMAGE_SIZES, spec_res=sc.SPEC_RES,
                     ref_image_size=sc.REF_IMAGE_SIZE, ref_spec_res=sc.REF_SPEC_RES)

    sc.plot_map(rmsd, times, os.path.join(sc.OUT_DIR, 'snr_convergence_test.png'))
