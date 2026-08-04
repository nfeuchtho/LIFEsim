# Pre-registration: independent-population validation of the z >= 3 criterion

Written 2026-08-03, BEFORE generating or inspecting any campaign result beyond
the single fidelity-pilot universe (seed 901, hab2max), which is excluded from
the analysis. Fixed herein; deviations will be reported as deviations.

## Claim under test

The margin criterion of Section 5.4: an iso-mission-time requirement is
quotable when z = (T* - mean T0)/sigma(T0) >= 3, where relative endpoint
spread falls below 40 %; below z ~ 3 spreads exceed 40 % and infeasible
draws appear. Previously validated across operating points and architectures
conditional on the shared catalog ensembles; under test here across genuinely
independent population realizations.

## Generation

- Tool: public P-Pop (github.com/kammerje/P-pop, cloned 2026-08-03), star
  input = the thesis's own 4505-star scaffold (StarCatalogs/LIFEScaffold.py,
  reads catalog_hab2hi.txt star columns), planet model
  Bryson2021Model1Hab2Low/High, Chen2017 masses, circular orbits, He2019
  stability, random orbit orientation, uniform albedos, Ertel2020 exozodi,
  Scenario 'baseline', 100 universes per realization.
- N = 20 independent realizations per scenario (hab2min, hab2max), seeds
  1..20 (hab2min) and 101..120 (hab2max). Seeds fixed here, before running.
- Fidelity acceptance per realization (checked before any endpoint search):
  planets/universe median within the thesis catalogs' observed range
  widened by 10 % (hab2min 1958-2154 eligible convention aside, raw-count
  check: within [6360, 8250] for hab2max, scaled equivalently for hab2min
  from its observed raw range), Rp and Finc quartiles within 15 % of the
  thesis catalog values. Realizations failing fidelity are excluded WITH
  REPORTED COUNT, not silently.

## Evaluation

- Anchor cells (design, scenario, target), chosen to span z ~ 2 to ~ 10 at
  their catalog-ensemble values: (bracewell4, hab2max, 5.5), (bracewell4,
  hab2min, 7.5), (bracewell4, hab2max, 6.0), (triple6, hab2max, 4.5).
- Per realization per anchor cell: corrected-rule scheduler, flat family
  only, zero-budget mission time and endpoint search with the production
  machinery (reproduce_endpoints.py path, upper_start 20000).
- Zero/no-allowance endpoints count as infeasible draws, included in
  infeasible fractions and excluded from spread statistics, exactly as in
  the bootstrap analysis.

## Analysis, fixed before results

1. Per anchor cell: between-realization mean, s.d., and relative spread of
   the endpoint; between-realization mean and s.d. of T0; z recomputed from
   between-realization statistics.
2. Success criterion for the claim: cells with between-realization
   z >= 3 show between-realization relative spread < 40 %, and cells with
   z < 3 show spread >= 40 % or nonzero infeasible fraction. The criterion
   passes if all four anchor cells classify consistently with the
   within-catalog prediction.
3. If between-realization spreads exceed within-catalog bootstrap spreads by
   more than a factor of 2 at z >= 3 cells, the thesis reports the bootstrap
   as an underestimate and quotes the between-realization interval as the
   headline uncertainty.
4. If z = 3 does not separate the regimes between realizations, the thesis
   replaces the hard threshold with the observed transition interval.
5. All numbers enter the thesis through generated artifacts and the ledger
   check, as elsewhere.

## Deviations

None at registration time.

## Outcomes — recorded 2026-08-04 after both rounds completed

- Round 1 (no binary suppression, 40 realizations): all four original anchors
  landed at z_between 6.9-24.6 (populations systematically easier than the
  thesis catalogs; T0 4.430+-0.101 / 6.325+-0.170 vs 5.3035 / 7.31), so the
  original anchors tested only the safe regime; amended low-z anchors
  (z ~ 2, ~ 3) were added per Amendment 1.
- Round 2 (BinarySuppression, 40 realizations): populations systematically
  harder (T0 5.650+-0.138 / 7.923+-0.199); two original anchors fell below
  feasibility (18-20/20 infeasible, consistent with their negative z).
- Mechanical classification: 11 of 13 cells consistent. Both inconsistent
  cells failed in the benign direction (spread BELOW 40 % just under z = 3:
  30.5 % at z = 2.98; 38.2 % at z = 2.53). Registered fallback engaged:
  the hard threshold is replaced by a calibrated transition interval,
  z ~ 2-2.5, with z >= 3 reported as a conservative sufficient margin. No
  z >= 3 cell in any round or configuration exceeded 40 % or produced an
  infeasible draw. Infeasible draws appear only below z ~ 2.
- Between-realization sigma(T0) is comparable to or smaller than the
  within-catalog bootstrap values (registered analysis item 3): the
  bootstrap intervals are conservative.
- Finding beyond the registered questions: the occurrence-model
  CONFIGURATION (binary-suppression choice) moves T0 by 5-15 %, an order of
  magnitude beyond sampling uncertainty; the thesis catalogs lie between the
  two tested configurations (2.5 sigma from suppressed, 8 sigma from
  unsuppressed). Exact-configuration closure requires the original P-Pop
  config (intermediate suppression variant); reported as a bracket, not
  tuned to match.

## Amendment 1 — 2026-08-03, after first evaluation round

**Deviation found and documented.** The generated ensembles pass all
registered fidelity checks but carry a systematic +6 % excess of
Experiment-1-eligible planets per universe (seed101: min/med/max
3250/3387/3551 against the thesis catalogs' 3049/3194/3331), concentrated in
the extrapolated habitable-zone corner of the Bryson model, most plausibly
from the unknown Scenario setting of the original generation (this campaign
used 'baseline'). Consequence: between-ensemble zero-budget times are ~16 %
shorter than the catalog values, and the four registered anchor cells all
landed at z_between >= 6.9 — the z ~ 2 and z ~ 3 anchors were not reached,
so the registered classification test passed only vacuously.

**Amended design, fixed before any new evaluation.** The low-z anchors are
re-established using the between-ensemble statistics measured in round one
(independent_summary.tsv), on the same 40 ensembles:

- bracewell4 / hab2max: T0 = 4.430 +- 0.101 -> targets 4.632 (z ~ 2.0) and
  4.733 (z ~ 3.0)
- bracewell4 / hab2min: T0 = 6.325 +- 0.170 -> targets 6.665 (z ~ 2.0) and
  6.835 (z ~ 3.0)
- triple6 / hab2max: T0 = 3.028 +- 0.060 -> target 3.148 (z ~ 2.0)

100 evaluations (5 cells x 20 realizations), corrected rule, flat family,
same machinery. Success criterion unchanged: cells at z_between >= 3
classify as determined (spread < 40 %, no infeasibles), cells below as
undetermined (spread >= 40 % or infeasibles present). The z ~ 2 cells are
predicted to show spreads approaching the endpoint magnitude and a nonzero
infeasible fraction; the z ~ 3 cells to sit near the 40 % boundary.

In parallel, the Scenario knob is tested (single-universe draws under
'optimistic' and 'pessimistic') for population fidelity against the thesis
eligible-count statistics; if a variant reproduces them, the full original
protocol re-runs on regenerated ensembles as confirmation. Round-one results
remain reported as the independent-population test at high z.

## Correction to the Outcomes note — 2026-08-04 (round-7 audit)

The Outcomes section says zero endpoints are "excluded from spread statistics,
exactly as in the bootstrap analysis." The exclusion is exactly as REGISTERED
here; the catalog-bootstrap pipeline (analyze_uncertainty.py) instead includes
zeros in its spread. The discrepancy is immaterial where the criterion is
applied -- no z >= 3 cell in either analysis contains a zero endpoint, so the
two definitions coincide on every classified cell -- but the cross-reference
was wrong and is corrected here rather than silently rewritten. The round-7
classifier audit (uncertainty/classifier_audit.tsv) fixes the classified
variable as the flat-family spread under the bootstrap pipeline's definition.

## Amendment 2 — 2026-08-03, before the binsup validation completes

Knob test outcome: Scenario = 'baseline' confirmed (optimistic/pessimistic
miss by roughly a factor of two in each direction); the missing configuration
value is ScalingModel = BinarySuppression, whose single-universe draw
reproduces the thesis eligible count to 0.1 % (3197 vs median 3194) while
undershooting the raw count by about 7 % (suppressed planets are
predominantly outside the Experiment-1 window); the residual raw difference
is documented, not hidden.

Automated acceptance gate, fixed before the validation result exists: the
100-universe BinarySuppression realization (seed 905) is accepted if its
corrected-rule zero-budget time lies within 0.15 yr of the thesis catalog
value 5.3035 yr. On acceptance, 40 realizations regenerate with the corrected
configuration (same seeds 1..20 / 101..120 plus 1000 offset to keep rounds
distinguishable: 1001..1020 / 1101..1120) and the ORIGINAL registered
protocol (four anchor cells, registered thresholds) re-runs on them as round
two. On rejection, the pipeline stops for human review. The gate executes
unattended; this amendment is its pre-declaration.
