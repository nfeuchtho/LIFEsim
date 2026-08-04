#!/bin/bash
# Cluster-side orchestrator: waits for the running uncertainty campaign to
# finish, then runs survey stage 1 (production zero-budget times), generates
# the survey job list from them, and launches the survey with 16 workers.
# Run detached:  screen -dmS lifesim-survey bash lifesim/ams/survey_bootstrap.sh
set -uo pipefail
cd /home/ipa/quanz/user_accounts/nfeuchtho/LIFESim
export MPLBACKEND=Agg
source venv/bin/activate

echo "[survey_bootstrap] waiting for campaign finish marker..."
until grep -q "campaign finished" campaign.log 2>/dev/null; do sleep 600; done
echo "[survey_bootstrap] campaign drained at $(date), starting stage 1"

python -u lifesim/analysis/test_scripts/survey_stage1.py \
    > survey_stage1.log 2>&1 || { echo "[survey_bootstrap] stage 1 FAILED"; exit 1; }

S1=thesis/reproducibility/survey_stage1.tsv
zbhi=$(awk -F'\t' '$2=="hi"{a[$1]=$3} END{printf "%s,%s", a["kernel5_deep"], a["collinear4"]}' "$S1")
zblo=$(awk -F'\t' '$2=="lo"{a[$1]=$3} END{printf "%s,%s", a["kernel5_deep"], a["collinear4"]}' "$S1")
echo "[survey_bootstrap] zero-budgets: hi=$zbhi lo=$zblo"

python lifesim/ams/gen_survey_jobs.py --zb-hi "$zbhi" --zb-lo "$zblo" \
    > jobs_survey.txt || { echo "[survey_bootstrap] job generation FAILED"; exit 1; }
echo "[survey_bootstrap] $(wc -l < jobs_survey.txt) survey jobs, launching"

bash lifesim/ams/run_survey_local.sh 16 jobs_survey.txt > survey.log 2>&1
echo "[survey_bootstrap] survey finished at $(date)"
