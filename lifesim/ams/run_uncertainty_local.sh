#!/usr/bin/env bash
# Bootstrap uncertainty for every cell of the results table: two architectures,
# two catalogues, two mission-time targets each, three budget families = 24.
#
# Cells share no state and each writes its own file, so they parallelise the way
# the Stage B scans do. Raising n_cpu inside a run buys nothing after the
# analytic rewrite, so the cells themselves are the unit of parallelism; run a
# few at a time and let the rest queue.
#
#   bash lifesim/ams/run_uncertainty_local.sh [replicates] [concurrency]

set -u
cd "$(dirname "$0")/../.." || exit 1

PY="${PY:-C:/Users/nicol/.conda/envs/LIFEsim/python.exe}"
REP="${1:-14}"
CONC="${2:-6}"
OUT=thesis/reproducibility/uncertainty
mkdir -p "$OUT"

# Each design is evaluated at its own targets, the lowest half year above its
# zero-budget time and the half year after that.
run_cell() {   # design catalog target family
  local tag="$1_$2_$4_${3/./p}"
  "$PY" -u lifesim/analysis/test_scripts/endpoint_uncertainty.py \
      --design "$1" --catalog "$2" --target "$3" --family "$4" \
      --replicates "$REP" > "$OUT/$tag.log" 2>&1
}

pids=()
launched=0
for spec in "bracewell4 hi 5.5" "bracewell4 hi 6.0" \
            "bracewell4 lo 7.5" "bracewell4 lo 8.0" \
            "triple6 hi 4.0"    "triple6 hi 4.5" \
            "triple6 lo 5.5"    "triple6 lo 6.0"; do
  set -- $spec
  for fam in flat short_weighted long_weighted; do
    # Throttle: wait for the oldest job once the pool is full.
    while [ "$(jobs -rp | wc -l)" -ge "$CONC" ]; do sleep 5; done
    echo ">> $1 hab2$2 $3 yr $fam"
    run_cell "$1" "$2" "$3" "$fam" &
    pids+=($!)
    launched=$((launched + 1))
  done
done

echo "launched $launched cells, concurrency $CONC, $REP replicates each"
wait
echo "all cells finished"
