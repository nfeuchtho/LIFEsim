#!/bin/bash
# Survey runner: like run_campaign_local.sh but with a jobs-file argument and
# its own log. A separate file so the campaign runner is never overwritten
# while a campaign is executing it.
set -uo pipefail
export MPLBACKEND=Agg

WORKERS=${1:-8}
JOBS=${2:-jobs_survey.txt}
xargs -a "${JOBS}" -d '\n' -P "${WORKERS}" -I{} bash -c '{}' \
  2>&1 | tee -a survey_jobs.log
echo "survey finished"
