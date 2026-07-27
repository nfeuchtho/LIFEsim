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

The throughput ablation, the throughput sweep and the break-even criterion
(Sections 5.7 and parts of 6.1, plus their abstract sentences) all interrogated
the proxy. The question they answered — what throughput must a fourth-order
design retain — is now answered by running the design. That material needs
replacing, not amending.

## Still true and still needed

Everything from the grading-sheet review that is not about null order stands: the
related-work section, the mission-time definition, the local-zodiacal correction
and its amplification result, the background-scale context, the reproduction
appendix. See `REVIEW_CHECKLIST.md`.

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

## A caution learned the hard way

`ANALYTIC_NOISE_REWRITE.md` is itself AI-written and is **not** an independent
record. One of its numbers, a 10.9 % median SNR shift, did not reproduce; the
measured value is 9.1-9.8 %. Several entries in the validation matrix are still
inherited from it and are marked as such in that table's caption. Treat its
claims as hypotheses to check, not as measurements.
