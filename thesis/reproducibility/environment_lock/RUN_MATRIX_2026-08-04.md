# Run matrix and environment closure — round-7 archive (2026-08-04)

## Machines and interpreters

| Role | Host | Interpreter | Lock file |
|---|---|---|---|
| Analysis, tables, figures, thesis build | local Windows 11 workstation | conda env `LIFEsim`, Python 3.13.5 | `local_pip_freeze.txt` |
| Endpoint/uncertainty/survey campaigns | bluesky.ethz.ch, `/home/ipa/quanz/user_accounts/nfeuchtho/LIFESim` | venv, Python 3.13.5 | `cluster_lifesim_env.txt` |
| P-Pop realization generation | bluesky.ethz.ch, `/home/ipa/quanz/user_accounts/nfeuchtho/P-pop` | venv-ppop, Python 3.13.5 | `cluster_ppop_env.txt` |

TeX: TeX Live 2024 pdflatex (Windows), `main.tex`, three passes.

## Campaigns feeding the thesis (corrected completion rule throughout,
## `strict_completion=True`, `retain_empty_universes=True`)

1. **Endpoint bootstrap (catalog resampling)** —
   `lifesim/analysis/test_scripts/endpoint_uncertainty.py`, sharded seeding
   (replicate index = seed; shards `_corrected`, `_off50`, `_off100`,
   `_off200`), 300 replicates at requirement targets, 100 at primary,
   50 at held-out cells. Outputs `uncertainty/{design}_{cat}_{family}_{target}_corrected*.tsv`.
2. **Zero-budget spreads** — `zerobudget_spread.py`, same sharding,
   `zerobudget_*_corrected*.tsv`, plus `blmax200` sensitivity arms.
3. **Architecture survey** — `survey_stage1.py` (`survey_stage1.tsv`),
   designs `bracewell4, triple6, kernel5_deep/shallow, collinear4`
   from `lifesim/util/combiner.py`, each at its own response-peak constant.
4. **Independent P-Pop realizations** — public P-Pop (kammerje/P-pop,
   cloned 2026-08-03) + `StarCatalogs/LIFEScaffold.py` on the 4505-star
   scaffold. Round 1 seeds 1..20 (hab2min), 101..120 (hab2max), Scenario
   `baseline`, no suppression; round 2 seeds 1001..1020, 1101..1120 with
   `ScalingModel=BinarySuppression`; pilot seed 901 (excluded), acceptance
   draw seed 905. `np.random.seed(seed)` per realization. Evaluation:
   `independent_eval.py` (corrected rule, flat family, zb + endpoint
   search), analysis `analyze_independent.py`; protocol and amendments in
   `independent_ensembles/PREREGISTRATION.md`.
5. **Round-7 audits (local)** — `photon_ledger.py`,
   `snr_shift_architectures.py` (equal-area ablation),
   `classifier_audit.py`, `solver_separation.py`, `analyze_uncertainty.py`,
   `gen_tables.py` + `check_ledger.py` (66/66).

## Source state

- Round-6 archive commit: `dd47101` (branch `ams`), clean-tree rebuild
  verified. The round-7 edits build on it; the round-7 commit is recorded in
  git history alongside this file.
- Historical caveat, unchanged: the ORIGINAL (defect-era) production
  campaigns ran from a dirty working tree and cannot be reproduced
  bit-for-bit; the corrected-rule reruns in Appendix B are the reproducible
  record. This file does not claim otherwise.

## Data pinned outside git

- 82 realization catalogs (~12 GB) on bluesky, hashed in
  `independent_ensembles/realizations_sha256.txt`.
- Everything else: `thesis/reproducibility/MANIFEST.sha256`
  (regenerate with `scratchpad finalize_manifests` equivalent; the manifest
  in the round-7 commit supersedes the 2026-08-04 morning one).
