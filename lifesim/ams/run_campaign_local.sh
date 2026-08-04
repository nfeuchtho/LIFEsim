#!/bin/bash
# Non-SLURM fallback: run jobs_uncertainty.txt with a bounded worker pool.
#
#   python lifesim/ams/gen_uncertainty_jobs.py --scheduler <strict|corrected> \
#       > jobs_uncertainty.txt
#   nohup bash lifesim/ams/run_campaign_local.sh 16 > campaign.log 2>&1 &
#
# Argument = number of concurrent jobs (each job uses 2 CPUs; pick cores/2).
set -uo pipefail
export MPLBACKEND=Agg

WORKERS=${1:-8}
xargs -a jobs_uncertainty.txt -d '\n' -P "${WORKERS}" -I{} bash -c '{}' \
  2>&1 | tee -a campaign_jobs.log
echo "campaign finished"
