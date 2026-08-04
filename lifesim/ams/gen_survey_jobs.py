"""Generate the survey-C job list (stage 2), given kernel5_deep zero-budget times.

Stage 1 (run first, minutes): one zero-budget evaluation of kernel5_deep per
catalog to fix the operating targets by the standard rule -- the lowest half
year above the zero-budget time, and the half year after that.

    python -u lifesim/analysis/test_scripts/zerobudget_spread.py \
        --design kernel5_deep --catalog hi --replicates 1 --scheduler corrected

Stage 2 (this file): full treatment for kernel5_deep, documentation row for
kernel5_shallow, and the bl_max=200 m envelope-sensitivity axis for the three
viable designs. Pass the stage-1 zero-budget times:

    python gen_survey_jobs.py --zb-hi 5.30 --zb-lo 7.02 > jobs_survey.txt

(The envelope axis needs a --bl-max option on zerobudget_spread.py; add it
before generating, or drop those lines.)
"""
import argparse
import math

ap = argparse.ArgumentParser()
ap.add_argument('--zb-hi', type=str, required=True,
                help='corrected zero-budget times hab2hi [yr] as '
                     '"kernel5_deep,collinear4", e.g. "5.30,3.29"')
ap.add_argument('--zb-lo', type=str, required=True,
                help='corrected zero-budget times hab2lo [yr], same format')
a = ap.parse_args()

EP = 'python -u lifesim/analysis/test_scripts/endpoint_uncertainty.py'
RE = 'python -u lifesim/analysis/test_scripts/reproduce_endpoints.py'
ZB = 'python -u lifesim/analysis/test_scripts/zerobudget_spread.py'
FAMILIES = ('flat', 'short_weighted', 'long_weighted')


def targets(zb):
    t1 = math.ceil(zb * 2) / 2 + (0.5 if math.ceil(zb * 2) / 2 - zb < 1e-9 else 0.0)
    return (t1, t1 + 0.5)


jobs = []
for cat, zb_pair in (('hi', a.zb_hi), ('lo', a.zb_lo)):
    # Full treatment for both viable new designs. zb arguments carry two
    # comma-separated zero-budget times per catalog: kernel5_deep,collinear4.
    zbs = dict(zip(('kernel5_deep', 'collinear4'),
                   (float(x) for x in str(zb_pair).split(','))))
    for design, zb in zbs.items():
        t1, t2 = targets(zb)
        # point endpoints at both targets, all families, corrected scheduler
        jobs.append(f'{RE} --design {design} --catalog {cat} '
                    f'--scheduler corrected --targets {t1},{t2}')
        # bootstrap for z: 50 replicates per cell, both targets, all families
        for t in (t1, t2):
            for fam in FAMILIES:
                jobs.append(f'{EP} --design {design} --catalog {cat} '
                            f'--target {t} --family {fam} --replicates 50 '
                            f'--scheduler corrected --n-cpu 2')
        # zero-budget spread for sigma(T0)
        jobs.append(f'{ZB} --design {design} --catalog {cat} --replicates 50 '
                    f'--scheduler corrected --n-cpu 2')
    # documentation row: kernel5_shallow, zero-budget only (narrow high-x
    # fringes: at the 100 m envelope most catalog stars sit near-blind, so
    # mission times exceed any adopted target; collinear4's broad response
    # shoulder makes it robust to the same clamping and it gets the full
    # treatment above)
    jobs.append(f'{ZB} --design kernel5_shallow --catalog {cat} --replicates 14 '
                f'--scheduler corrected --n-cpu 2')
    # envelope-sensitivity axis: zero-budget at bl_max = 200 m for every
    # design, including the trapped ones -- the axis measures whether they
    # become mission-viable once the formation can stretch
    for design in ('bracewell4', 'triple6', 'kernel5_deep',
                   'kernel5_shallow', 'collinear4'):
        jobs.append(f'{ZB} --design {design} --catalog {cat} --replicates 14 '
                    f'--scheduler corrected --bl-max 200 --n-cpu 2')

print('\n'.join(jobs))
