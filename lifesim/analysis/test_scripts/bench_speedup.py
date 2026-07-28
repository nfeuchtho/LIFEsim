"""Time the grid-based source model against the analytic one on identical input.

Run twice: once with the pre-rewrite worktree first on sys.path, once with the
current tree. Asserts which lifesim it actually imported so the two runs cannot
be confused.

    python bench_speedup.py old   /path/to/worktree
    python bench_speedup.py new   /path/to/repo
"""
import os, sys, time

TAG = sys.argv[1]
ROOT = os.path.abspath(sys.argv[2])
N_PLANETS = int(sys.argv[3]) if len(sys.argv) > 3 else 400

sys.path.insert(0, ROOT)
import matplotlib
matplotlib.use('Agg')
import numpy as np

_cwd = os.getcwd()
import lifesim
os.chdir(_cwd)

got = os.path.abspath(lifesim.__file__)
assert got.startswith(ROOT), f'imported {got}, expected under {ROOT}'
print(f'[{TAG}] lifesim from {got}', flush=True)

CAT = r'C:\Users\nicol\Desktop\LIFE\LIFESim\lifesim\catalogs\catalog_hab2hi.txt'

bus = lifesim.Bus()
bus.data.options.set_scenario('baseline')
bus.data.catalog_from_ppop(input_path=CAT)

# identical instrument settings for both trees
bus.data.options.set_manual(image_size=256, spec_res=20, n_cpu=1)

instrument = lifesim.Instrument(name='inst')
transm = lifesim.TransmissionMap(name='transm')
exo = lifesim.PhotonNoiseExozodi(name='exo')
local = lifesim.PhotonNoiseLocalzodi(name='local')
star = lifesim.PhotonNoiseStar(name='star')
for m in (instrument, transm, exo, local, star):
    bus.add_module(m)
for pair in [('inst', 'transm'), ('inst', 'exo'), ('inst', 'local'),
             ('inst', 'star'), ('star', 'transm')]:
    bus.connect(pair)
instrument.apply_options()

# same subset for both
cat = bus.data.catalog
bus.data.catalog = cat.iloc[:N_PLANETS].reset_index(drop=True)
n = len(bus.data.catalog)
n_stars = bus.data.catalog.nstar.nunique()
print(f'[{TAG}] {n} planets, {n_stars} unique stars, image_size=256', flush=True)

t0 = time.time()
instrument.get_snr()
dt = time.time() - t0

print(f'[{TAG}] Instrument.get_snr: {dt:.2f} s '
      f'({1000*dt/n:.2f} ms/planet, {1000*dt/n_stars:.2f} ms/star)', flush=True)
print(f'[{TAG}] extrapolated to 729,927 planets: {dt/n*729927/60:.1f} min', flush=True)
