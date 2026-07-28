#!/usr/bin/env bash
# Stage B, all six fourth-order operating-point scans, as independent jobs.
#
# The analytic reduction made the per-star SNR cheap enough that raising n_cpu
# inside one run no longer helps -- 4, 8, 16 and 32 workers time the same, and
# 32 is slightly slower through dispatch overhead. What is left to parallelise
# is the scans themselves, which share no state and each write only their own
# figure, so they cannot collide. This is the same shape as the cluster
# submission, with the worker count per job cut to suit one machine.
#
# Each scan runs at the fourth-order design's OWN operating point, the lowest
# half year above its zero-budget time (Hab2Max 3.7191 -> 4.0, Hab2Min 5.0851
# -> 5.5), not the reference's 5.5 and 7.5.
#
#   bash lifesim/ams/run_stage_b_local.sh [n_cpu_per_job]
#
# Watch progress with:  tail -f thesis/reproducibility/stageb6_mag_hi.log

set -u
cd "$(dirname "$0")/../.." || exit 1

PY="${PY:-C:/Users/nicol/.conda/envs/LIFEsim/python.exe}"
NCPU="${1:-2}"
OUT=thesis/reproducibility
mkdir -p "$OUT"

# catalogue:target -- each design at its own primary operating point
declare -A TARGET=( [hi]=4.0 [lo]=5.5 )

pids=()
for scan in mag slew linear; do
  for cat in hi lo; do
    log="$OUT/stageb6_${scan}_${cat}.log"
    echo ">> launching $scan/$cat at ${TARGET[$cat]} yr, ${NCPU} workers -> $log"
    nohup "$PY" lifesim/ams/ablation_throughput.py \
        --stage-b "$scan" --catalog "$cat" \
        --targets "${TARGET[$cat]}" --n-cpu "$NCPU" \
        > "$log" 2>&1 &
    pids+=($!)
  done
done

echo
echo "launched ${#pids[@]} jobs: ${pids[*]}"
echo "figures land in thesis/images/tse/physical/ as phys_<cat>_<scan>_<target>.pdf"
wait
echo "all Stage B scans finished"
