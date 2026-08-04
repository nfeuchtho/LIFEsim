"""Generate the Phase-1 uncertainty campaign job list (one shell command per line).

Campaign layout (2026-07-29, PLAN_TO_6.0.md Phase 1 A+B):

- Tier 1, requirement rows: the four secondary-target cells x 3 families at 300
  replicates, sharded 3 x 100.
- Tier 2, primary rows: the four primary-target cells x 3 families at 100
  replicates, sharded 2 x 50.
- Held-out z points: nine new operating points x 3 families at 50 replicates,
  one shard each. These are NOT used to fit the z relation; they validate it
  out of sample. Includes one deliberate low-z probe (triple6 lo 5.25).
- Zero-budget spread: four configurations at 300 replicates, sharded 3 x 100.

Every job runs with --n-cpu 2; parallelism comes from job count. Total ~99 jobs,
individually 2.5-6 h at ~200 s per endpoint replicate.

    python gen_uncertainty_jobs.py --scheduler corrected > jobs_uncertainty.txt
"""
import argparse

ap = argparse.ArgumentParser()
ap.add_argument('--scheduler', choices=['strict', 'corrected'], required=True,
                help='decide via the scheduler_boundary.py verdict before submitting')
a = ap.parse_args()

EP = 'python -u lifesim/analysis/test_scripts/endpoint_uncertainty.py'
ZB = 'python -u lifesim/analysis/test_scripts/zerobudget_spread.py'
FAMILIES = ('flat', 'short_weighted', 'long_weighted')

SECONDARY = [('bracewell4', 'hi', 6.0), ('bracewell4', 'lo', 8.0),
             ('triple6', 'hi', 4.5), ('triple6', 'lo', 6.0)]
PRIMARY = [('bracewell4', 'hi', 5.5), ('bracewell4', 'lo', 7.5),
           ('triple6', 'hi', 4.0), ('triple6', 'lo', 5.5)]
HELD_OUT = [('bracewell4', 'hi', 5.75), ('bracewell4', 'hi', 6.25),
            ('bracewell4', 'lo', 7.75), ('bracewell4', 'lo', 8.25),
            ('triple6', 'hi', 4.25), ('triple6', 'hi', 4.75),
            ('triple6', 'lo', 5.25), ('triple6', 'lo', 5.75),
            ('triple6', 'lo', 6.25)]

jobs = []


def endpoint_jobs(cells, total, shard):
    for design, cat, target in cells:
        for fam in FAMILIES:
            for off in range(0, total, shard):
                jobs.append(
                    f'{EP} --design {design} --catalog {cat} --target {target} '
                    f'--family {fam} --replicates {shard} --rep-offset {off} '
                    f'--scheduler {a.scheduler} --n-cpu 2')


endpoint_jobs(SECONDARY, 300, 100)
endpoint_jobs(PRIMARY, 100, 50)
endpoint_jobs(HELD_OUT, 50, 50)

for design, cat in [('bracewell4', 'hi'), ('bracewell4', 'lo'),
                    ('triple6', 'hi'), ('triple6', 'lo')]:
    for off in range(0, 300, 100):
        jobs.append(f'{ZB} --design {design} --catalog {cat} --replicates 100 '
                    f'--rep-offset {off} --scheduler {a.scheduler} --n-cpu 2')

print('\n'.join(jobs))
