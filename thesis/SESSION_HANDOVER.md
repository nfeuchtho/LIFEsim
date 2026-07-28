# Handover — state as of 2026-07-28

Written so a session with no memory of the preceding work can pick this up. The
thesis is `thesis/main.tex`; the revision plan is `thesis/REVIEW_CHECKLIST.md`;
the examiner reports are in `thesis/reviews/`.

## The one thing to understand first

The thesis compared null orders using a `sin^n` **shape proxy**: the
double-Bracewell response raised to the fourth power, with throughput, collecting
area and the baseline prescription held fixed. That proxy has been replaced by an
**actual beam combiner**, and its numbers were wrong by a factor of about 4.6 in
the direction that flattered order four.

`lifesim/util/combiner.py` now describes an interferometer by its aperture
positions and combiner matrix, `T_j(theta) = |sum_k U_jk exp(2i pi r_k . theta /
lambda)|^2`. Everything else follows from that: null order, throughput, chopping,
the rotation-averaged response, and the baseline constant.

## What is validated, and against what

Do not take these on trust from prose; each was measured and can be rerun.

- The combiner expressed as the double Bracewell reproduces LIFEsim's closed-form
  `tm3`/`tm4` to 3e-14 and `azimuthal_average_tm` to 5e-16.
- `signal_noise_tables` reproduces the `ams.py` S(x)/N(x) block to 3e-15, scale
  factor exactly one.
- `radial_average_general` reproduces `radial_average_tm` to 2.6e-16 under the
  default Gaussian taper.
- End to end: the AMS driven by the combiner-as-double-Bracewell gives 5.3193 yr
  against the `sin^n` path's 5.3187 yr, the 0.012 % being the difference between
  the measured response peak and LIFEsim's hardcoded 0.589645.
- The null-order fitter returns exactly 2.0000 for the reference dark outputs
  without being told.

## Results from the physical architecture

Six-aperture "double triple nuller": each Bracewell pair replaced by a 1:-2:1
triple, the two triples recombined with a pi/2 relative phase. Two fourth-order
outputs that chop, 33.3 % of the collected light in the chopping pair.

- A four-aperture fourth-order array has only **one** deep output and therefore
  **cannot chop at all**. Six apertures are the minimum for a choppable
  fourth-order null. This is structural, from the row count of an orthonormal
  matrix, and it independently reproduces the 25 % and 50 % figures Guyon et al.
  quote for the Angel Cross and Darwin.
- Baseline constants are architecture specific: 0.5894 for the double Bracewell
  (LIFEsim hardcodes 0.589645), **1.1376** for the triple nuller. Run at the
  inherited constant the triple nuller operated at 31 % of its achievable signal,
  which is what made the first attempt look catastrophic.
- Mission time at zero budget, fixed total collecting area: Hab2Max 5.3187 ->
  **4.9800** yr (-6.4 %), Hab2Min 7.4100 -> **6.9624** yr (-6.0 %).
- Mechanism, confirmed and monotonic: median per-target SNR is only 0.93 of the
  reference and 71 % of targets are worse, but the **top 50 reference targets are
  1.20-1.22x better**. A mission observes the top of the distribution, not the
  median. The best targets are nearby and resolved, so they suffer most from
  second-order stellar leakage, which the deeper null removes.
- The **spectral reversal survives, 4/4**, with long-to-short ratios 1.28-1.91
  against the proxy's 1.36, clearing the integral-neutral reference every time.
- Magnitudes do not survive. Hab2Max 5.5 yr flat: proxy 641, physical **138**,
  reference 140. The change is not uniform either: 610 -> 394 at 6.0 yr,
  460 -> 222 for Hab2Min at 8.0 yr, but 65 -> 129 at 7.5 yr.

Data: `thesis/reproducibility/physical_architecture.tsv`, figures in
`thesis/images/tse/physical/`.

## What this obsoletes

The throughput ablation, the throughput sweep and the break-even criterion all
interrogated the proxy. The question they answered -- what throughput must a
fourth-order design retain -- is now answered by running the design instead.
**This replacement is done**: Section 5.7 is now "Comparing Realizable
Architectures", and the discussion, conclusion and abstract follow it. Their data
files remain under `thesis/reproducibility/` but are no longer cited by the
thesis. Do not reinstate them.

## Still true and still needed

Everything from the grading-sheet review that is not about null order stands: the
related-work section, the mission-time definition, the local-zodiacal correction
and its amplification result, the background-scale context, the reproduction
appendix. See `REVIEW_CHECKLIST.md`.

## State as of 2026-07-28, late afternoon

The thesis has been rewritten end to end around the physical combiner and now
compiles at 69 pages with no undefined references and no placeholders. The
framing did not change: the goal is still an instrument-agnostic requirement on
the aggregate random-noise budget, and the simulator is still the means. What
changed is that the means now exists, so the central question can be answered as
posed rather than in a weakened form.

**Title** is now *Iso-Mission-Time Random-Noise Error Budgets for LIFE with
Arbitrary Nulling and Noise Models*. The previous one ended "Using a Null-Order
Proxy", which is no longer true; an earlier draft's "Optimal" was dropped
because nothing is optimised over the space of spectral distributions, only
three families compared.

**Speedup, measured and settled.** Both the pre-rewrite and current source models
memoize the expensive work per host star. This was established by holding the
star set fixed and raising the planets per star from 2.6 to 218, which left the
runtime unchanged in both, so the comparison is per star and symmetric. An
earlier per-planet extrapolation was wrong by about sixty times and has been
withdrawn. Measured on identical input with eight workers, extrapolated to 4505
stars:

| Full catalogue pass | image size 100 | image size 512 |
|---|---|---|
| Pre-rewrite grid | 1.2 min | 24.6 min |
| Closed-form background | 0.43 min | 0.43 min |
| Plus simulator vectorization | -- | about 15 s |

Production yield runs use image size **512**, not the 100 in
`lifesim/ams/settings.yaml` nor the 256 in `options.py`. The grid cost scales as
the square of it and the closed form does not depend on it at all, so **there is
no single speedup factor**: roughly three at 100, sixty at 512, about two orders
of magnitude overall once vectorization is included. Section 6.3 reports it as a
scaling and keeps the three contributions distinct, since a change of algorithm,
a change of implementation and a capability the grid never had are different
claims. Benchmark: `lifesim/analysis/test_scripts/bench_speedup.py`, which
asserts which tree it imported; recreate the old tree with
`git worktree add <path> 2fd5142`.

**A second amplification result, stronger than the first.** The reference array
was re-run through the general-combiner path (`--physical --design bracewell4`).
The two models agree to 0.012 % in mission time and 1.6e-4 in median per-target
SNR, yet three of twelve endpoints move by 4.3 %, 6.8 % and 11.9 %. A model
difference of order 1e-4 therefore produces a requirement difference of order
1e-1 -- a far smaller perturbation than the 27 % normalization correction, and a
sharper demonstration of the same point. Reported in Appendix B.3 as a
sensitivity measurement. **Table 5.1 deliberately keeps the production values**
rather than substituting the re-run: it is no more correct, and substituting it
would conceal exactly what it demonstrates.

## Remaining before a grading re-run

Nothing from the review rounds is open. The next step is a fresh grading pass on
the rewritten thesis, which the author deferred until the rewrite was complete.

### Done 2026-07-28, evening

**The operating-point scans are now described from their own data.** The
two-dimensional scans wrote only figures, so the numbers behind them existed
only as colours. They are recoverable from the cluster logs, which print each
grid point's parameters and its located cutoff or its failure;
`lifesim/analysis/test_scripts/recover_stageb_grids.py` parses all four back and
writes `thesis/reproducibility/stageb_grids.tsv`, 900 cells. What that showed:

- Along magnitude at the adopted field of regard, the fourth-order allowance
  moves by only 1.21x (Hab2Max) and 1.86x (Hab2Min) across the whole range, and
  is *exactly constant* above magnitude 6.4 for Hab2Max. Along field of regard
  at fixed magnitude it moves 2.44x and 2.80x. The near-vertical contours were
  asserted before; they are now measured.
- The lowest feasible field of regard does not move with limiting magnitude at
  all: 61 degrees at every magnitude, both catalogs.
- The claim that the fourth-order design tolerates pointing "several degrees"
  more restrictive was overstated. It is **one grid step**, 61 against 65
  degrees at 3.6-degree spacing, so the margin is resolved but not measured.
  The caption now says so.
- Slew time dominates magnitude by a wide margin: at fixed field of regard the
  allowance moves 14.4x and 24.0x across the slew range against 1.21x and 1.86x
  across magnitude. Only 41.8 % and 39.1 % of the slew grids are feasible at
  any noise level.
- **The colour scales differ between panels** and the captions now say so; the
  fourth-order maps look darker mostly because their peaks are lower.

**Figure 5.6 is decoded and its percentage is sourced, with a correction.** The
radial axis is host-star distance in parsec and the polar angle is ecliptic
*latitude*, with longitude beyond 180 degrees reflected through the origin, so
longitude is not resolved and the figure is not a sky map. The annotated 26.7 %
counts eligible hosts zeroed by the single mask at `ams.py:393`, which combines
the magnitude limit and the field of regard. Reproduced exactly by
`decompose_target_loss.py` and decomposed: field of regard 7.5 points, magnitude
limit 20.5 points. **The loss is dominated by the cut the figure does not draw.**
That also explains the saturation in Section 5.4 -- the magnitude cut removes
far more stars but removes faint ones, which a top-50 sample does not want.
Reproducing 26.7 % also confirms that "interesting" there means Experiment 1
alone; including Experiment 2 gives 4493 stars and 36.0 %. Data in
`thesis/reproducibility/target_loss_decomposition.tsv`.

**The budget-breakdown figures now disclose what they show.** Figure 5.4 already
carried the clause, but it forward-referenced a statement Figure 5.3 never made,
and Figure 4.1 said nothing at all. `identify_plot_target.py` resolves the
plotted target: the same host star for both catalogs, 46.0 pc, 6303 K, ecliptic
latitude -34.9 degrees, habitable-zone centre 0.977 AU. It is **not typical** --
83rd percentile in distance, 90th in effective temperature, so more distant and
hotter than the median and correspondingly less resolved. Figure 4.1 now carries
the full disclosure, separating the amplitude (an ensemble quantity, from the
mission-time search over the whole catalog) from the background curves beneath
it (one arbitrary target), and points at the ensemble median in Section 6.1 and
`background_context.tsv`. Note that `run_background_context` was already
computing the median over catalog stars, so no new figure was needed.

Thesis now 71 pages, no undefined references, no errors.

## In flight as of 2026-07-28, early morning

Six jobs are running on the bluesky cluster, launched with `--stage-b` and
`nohup`, one per scan and catalogue. They write only their own figure and share
no files, so they cannot collide.

| Job | Cost per grid point | Estimate |
|---|---|---|
| `mag` hi / lo | endpoint search, ~165 s | ~2 h |
| `slew` hi / lo | endpoint search, ~165 s | ~4 h |
| `linear` hi / lo | single evaluation, ~22 s | ~1-1.5 h |

Output lands in `thesis/images/tse/physical/` as
`phys_<catalog>_<scan>_<target>.pdf`. These replace the order-four
operating-point figures. **The order-two figures do not need regenerating**: the
reference architecture is unchanged and the combiner framework reproduces its
results to 0.012 %.

If they are not there, check `stageb_<scan>_<catalog>.log` on the cluster.

## Two results from the cluster run worth putting in the thesis

**Cross-machine reproducibility.** The twelve-cell physical run was repeated on
the cluster -- different machine, operating system, core count and numpy major
version -- and the six Hab2Max endpoints agree with the local values to between
2.6e-12 and 4.1e-11 relative. Since the search is stopped on a tolerance rather
than converged to machine precision, that independence is worth stating in
Appendix B; it is exactly what an examiner probes.

**Parallelism no longer helps, and that is a consequence of the rewrite.**
Measured on the cluster, one AMS evaluation takes essentially the same time at 4,
8, 16 and 32 workers, with 32 marginally *slower* through dispatch overhead. The
multiprocessing in `ams.py` was built when the per-star SNR was a pixel-grid
integration; the analytic reduction made that part so cheap that only the serial
stages remain -- scheduling, filtering, the percentile. Use eight workers and
parallelise across scans instead. This belongs in the discussion of what the
reductions buy.

## Environment traps, all fixed but worth knowing

Three failures appeared only on the cluster, each invisible locally because the
working directory, the display and the numpy version all happened to be right:

- LIFEsim was never pip-installed, so `import lifesim` worked only from the
  repository root. Fixed with `pip install -e . --no-deps`; a batch job needs it.
- `trade_space_explorer` called `mpl.use('Qt5Agg')` unconditionally at import,
  overriding the Agg backend and failing on a headless node. It now leaves a
  non-interactive backend alone and never raises if Qt is absent.
- numpy 2.0 removed `np.trapz`. Five call sites now resolve the name at import.
  Note `requirements.txt` pins numpy 1.20.3 for Linux, which cannot build on
  Python 3.12, while `setup.py` asks for >=1.24.2 unbounded; those two disagree
  and should be reconciled. A numpy 2 environment also needs astropy >= 6.1,
  since older astropy references `np.trapz` at import.

## Next steps, in order

1. **Stage B**: the six two-dimensional scans at order four, which feed the
   operating-point figures. Hours each; intended for a cluster.
2. **Speed benchmark**: the thesis claims no number for the speedup. The
   pre-rewrite grid modules are in commit `2fd5142`, so the honest measurement is
   old path against new on the same catalogue and machine. Must run alone or it
   measures contention. Note that "faster than before" (grid elimination,
   vectorization, tabulation) and "possible at all" (arbitrary combiners) are
   different claims and should not be merged.
3. **Rewrite**: Section 3.2 through the Conclusion, the abstract, and the framing.
   The simulator being architecture-agnostic at closed-form cost is arguably now
   a co-equal contribution to the noise allowance, which is a decision the author
   has flagged but not made.

## Environment

Conda env `LIFEsim` at `C:\Users\nicol\.conda\envs\LIFEsim` (Python 3.12).
LIFEsim is editable-installed there (`pip install -e . --no-deps`); before that it
only imported when the working directory happened to be the repo root.
Catalogues under `lifesim/catalogs/` are gitignored and are 181 MB and 121 MB.
Collection script: `lifesim/ams/ablation_throughput.py`, with modes
`--sweep --defect-impact --background-context --breakeven --snr-shift --physical`.

## Open issue: what the budget figures actually show

Every budget-breakdown figure -- Figure 4.1, Figures 5.1 and 5.2, and the twelve
regenerated ones under `images/tse/physical/` -- is produced by the simulator's
plot mode, which at `ams.py:634-636` resolves **one specific planet** by
positional index (9 for Hab2Max, 5 for Hab2Min) and draws that planet's stellar
and exozodiacal background.

The figures therefore combine an amplitude derived from the whole ensemble, via
the mission-time search, with background curves belonging to a single arbitrary
target. That is a reasonable illustration, but no caption says so, and Figure
4.1's caption currently implies a general configuration. Every such caption needs
a clause naming the target and stating that the curves are that target's, not an
ensemble average.

## A caution learned the hard way

`ANALYTIC_NOISE_REWRITE.md` is itself AI-written and is **not** an independent
record. One of its numbers, a 10.9 % median SNR shift, did not reproduce; the
measured value is 9.1-9.8 %. Several entries in the validation matrix are still
inherited from it and are marked as such in that table's caption. Treat its
claims as hypotheses to check, not as measurements.
