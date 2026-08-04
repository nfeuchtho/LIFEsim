#!/bin/bash
# SLURM array runner for jobs_uncertainty.txt. Submit from the repo root:
#
#   python lifesim/ams/gen_uncertainty_jobs.py --scheduler <strict|corrected> \
#       > jobs_uncertainty.txt
#   N=$(wc -l < jobs_uncertainty.txt)
#   sbatch --array=1-${N}%40 lifesim/ams/run_campaign_slurm.sh
#
# %40 caps concurrently running tasks; adjust to the allocation. If bluesky has
# no SLURM, use run_campaign_local.sh instead.
#SBATCH --job-name=lifesim-uncertainty
#SBATCH --cpus-per-task=2
#SBATCH --mem-per-cpu=4G
#SBATCH --time=08:00:00
#SBATCH --output=slurm-%A_%a.out

set -euo pipefail
export MPLBACKEND=Agg

cmd=$(sed -n "${SLURM_ARRAY_TASK_ID}p" jobs_uncertainty.txt)
echo "task ${SLURM_ARRAY_TASK_ID}: ${cmd}"
eval "${cmd}"
