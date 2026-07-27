# Block: General scientific competence (revised draft)

External examiner report. Specialist field: mid-IR nulling interferometry and exoplanet
mission yield modelling. Document graded as it stands.

Basis of assessment: `thesis/main.tex` read in full (1280 lines) plus `main.pdf`;
`ANALYTIC_NOISE_REWRITE.md`; `lifesim/util/transmission_analytic.py`,
`lifesim/instrument/pn_localzodi.py`, `instrument.py`, pre-rewrite state at commit
`2fd5142`; `lifesim/ams/trade_space_explorer.py`, `ablation_throughput.py`;
all five files in `thesis/reproducibility/`; and the source PDFs for Lay 2004, Lay 2005,
Guyon+2013, Kennedy+2015, LIFE I/II/VI, P-Pop and Dannert's doctoral thesis.
Every number in Tables 4.1, 5.1, 5.6, 5.7 and B.2 was recomputed against the machine-written
TSVs; the 4/pi claim and the binomial coverage were recomputed independently.

---

## Verdict per sub-question

### 1. Sufficient familiarity with the literature? — **+**

The LIFE chain is handled with real command and, more importantly, **accurately**. Every
non-trivial attributed claim I could check against the source is correct, several of them
close to verbatim (see the citation audit). The positioning against Dannert's doctoral thesis
(main.tex:227) is precise about what is inherited versus inverted, and the two neighbouring
MSc theses (main.tex:229) are placed correctly rather than name-dropped. The
eta_Earth / stellar-scaffold population mismatch (main.tex:284) is a subtle point that most
candidates miss entirely, and it is disclosed unprompted.

Against that:

- `laugier2020kernel` appears **exactly once in the file** — as its own `\bibitem`
  (main.tex:1254). It is never cited (verified by counting key occurrences for all 15 keys;
  every other key occurs >= 2 times). Kernel nullers are precisely the "realizable
  higher-order combiner" the outlook (main.tex:987) asks for, so this is not a cosmetic
  omission — the literature that would answer the thesis's own principal open question is in
  the bibliography and unused.
- The Angel Cross carries the entire throughput penalty of Section 5.7, but Angel (1990) and
  Angel & Woolf (1997) are not cited; the design is known only through Guyon's one-sentence
  summary.
- No engagement with the instability/systematic-noise literature beyond passing citations of
  Lay 2004 (Defrere, Absil, Lay's own Sec. 3.E), and no LIFE papers after VI.

Good, not excellent.

### 2. Are the aims/hypothesis/questions clearly formulated? — **++**

One central question (main.tex:213) stated as a single sentence with all four qualifiers
attached ("for a specified operating point", "a tested family", "Experiment 1", "a chosen
mission-time target"), decomposed into five sub-questions (main.tex:216-222), each closed
explicitly in the conclusion (main.tex:996-1001) — including sub-question 3, which is
answered *partially* and says so (main.tex:998). The bridge-quantity framing and the
pre-efficiency reference plane are defined before first use (main.tex:208). Section 2.6
(main.tex:429) pre-empts the obvious terminological objection by separating
*mechanism*-agnostic from *computationally* agnostic. This is well above the norm.

### 3. Are the methods and techniques properly described? — **+**

The derivation is inspectable (Appendix A), the scheduler is stated step by step
(main.tex:539-546), and the search is described accurately enough that I could match it to
code line for line: bracket [0, 50000] (`trade_space_explorer.py:61`), `epsilon = 0.05`
(line 98), termination `abs(cutoff-mtime) > epsilon and upper_start - lower > 10` (line 126),
exponential fit via `fsolve` (line 136), bracket invariant maintained at lines 148-155.
main.tex:676 describes all of this correctly.

Three descriptive defects, all concrete:

- **The removed grid code is described two different ways, and neither matches the code.**
  main.tex:632 says the tapered branch "formed the mean of the transmission over the square
  evaluation grid"; Appendix A.4 (main.tex:1097) says it "integrated pixels inside this circle
  but normalized one path with the enclosing square area". The actual pre-rewrite source
  (`git show 2fd5142:lifesim/instrument/pn_localzodi.py`) is
  `ap = np.ones_like(radius_map)` under `fov_taper='gaussian'`, so **both** numerator and
  denominator ran over the full square. The main text is right, the appendix is wrong, and
  they contradict each other.
- main.tex:1145 states the search "returns its last accepted amplitude". It returns
  `guess` unconditionally (`trade_space_explorer.py:162`), accepted or not.
- main.tex:550 refers to "the observing efficiency of 0.8 configured in Table 2.1".
  Table 2.1 (main.tex:259-273) has no observing-efficiency row.

### 4. Are the methods appropriate for the subject? — **+**

The core method choices are right and well argued. The azimuthal/radial reduction is the
correct tool for circularly symmetric backgrounds and is stated with its exact validity
boundary (main.tex:601, main.tex:1027 "not an approximation based on rapid rotation" —
correct, and the distinction most people get wrong). The u = 1/lambda substitution is
motivated by the physics of the phase (main.tex:658) rather than by convenience. The
iso-mission-time inversion is a well-posed question, and the monotonicity assumption is
labelled empirical rather than proved (main.tex:678). The null-order proxy is bounded by an
explicit "changed / preserved" table (Table 3.1).

The one substantive appropriateness problem is in the new Section 5.7 and is described under
Findings/Major: the Guyon throughput factor of 0.5 is applied to `eff_tot` **on top of** a
proxy whose transmission has already dropped by 25 percent, which the thesis itself measures
and tabulates elsewhere (main.tex:865, Table 5.5). The two are never netted.

### 5. Has the research been carried out carefully? — **o**

The *execution* is careful, and I want to record that clearly: every one of ~60 numbers in
Tables 4.1, 5.1, 5.6, 5.7 and B.2 reproduces from the machine-written TSVs at the stated
rounding, the four acknowledged rounding discrepancies at main.tex:1147 are exactly the four
that exist and no others, and the binomial coverage at main.tex:1177 recomputes to 0.955690
against the claimed 0.9557.

The *claims about* the execution are where it falls down, and there are enough of them to
pull this below "+":

- A provably wrong exactness claim, stated twice and load-bearing (Findings/Critical 1).
- A wrong component attribution in the broader-context paragraph (Findings/Major 2).
- Four internal numeric inconsistencies for the same quantities: 60 (Table 4.1) vs 65
  (Table 5.1) vs 62.2 (Table B.2) for Hab2Min/order 2/flat; 600 (Table 4.1) vs 590
  (Table 5.1) vs 596.5 (Table B.2) for Hab2Min/order 4/flat; "650" at main.tex:752 vs 640 in
  Table 5.1; and Table 4.1's own Ratio column (11.0, 5.3) computed from unrounded values that
  disagree with the rounded values printed beside them (690/60 = 11.5, not 11.0).
  main.tex:1149 addresses only one facet of one of these.
- main.tex:787 asserts "amplitudes below the reported value satisfy the corresponding
  mission-time target"; the thesis's own Table B.2 shows 15 of 24 rows achieved a time
  *above* the target (up to +0.045 yr), so for the majority of rows the statement is false.
  Appendix B.3 states the correct version; Section 5.3 states the opposite and is the
  sentence a reader will quote.

### 6. Have results been appropriately tested by statistical analyses and/or sensitivity tests? — **+**

Genuinely improved and, in the parts I could audit, sound.

Sound and sufficient:
- The independent reproduction (Table B.2) is real: rerun from a committed state, machine-written,
  and it *reports its own disagreements* rather than hiding them.
- Converting the 0.05 yr stopping tolerance into an amplitude uncertainty via the secant slope
  (main.tex:1145) is the right move, correctly caveated as a scale rather than an interval, and
  the resulting "no more than two significant digits" rule is honest.
- The rank-uncertainty treatment (Appendix B.4) is textbook-correct and I verified the number.
  The scoping sentence — that it excludes occurrence, stellar, dust, instrument and scheduler
  uncertainty and that universes share one real-star scaffold — is exactly right.
- The defect-impact measurement (Table 4.1) and the penalized-reversal test (Table 5.7) are
  both well designed: the second in particular answers a question the earlier draft could only
  flag, by moving the targets rather than abandoning the test.

Not sufficient:
- **The thesis's own #4-ranked limitation is still unquantified after a fresh campaign was
  run.** main.tex:552 and main.tex:975 say the rank interval cannot be turned into years
  "after the fact" because per-universe vectors were not retained. But `ablation_throughput.py`
  re-ran the AMS from scratch 57 times in July 2026. Retaining `distribution` at
  `ams.py:485` would have closed the gap for the four headline rows at zero marginal cost.
  This is now a choice, not an inherited constraint, and the text should not read as the latter.
- **The "17 to 29 percent throughput-independent fraction" (main.tex:911) is an endpoint-secant
  inference that the sweep's own intermediate points contradict.** Fitting T = a/eta + c to
  adjacent pairs of Table 5.6 gives slopes a = 0.851, 0.607, 0.613 yr per unit (1/eta) for
  Hab2Max order 2 — and the tau = 0.15/0.125 pair alone implies c = -0.35 yr, i.e. a *negative*
  fixed fraction. Hab2Min order 2 is well behaved (0.894, 0.899, 0.860); the others scatter by
  +/-15 percent. The measured *ratio* (1.71-1.83) is solid; the decomposition into "1/eta plus a
  fixed slew overhead" is not, and the scatter is scheduler discreteness that the thesis
  elsewhere warns about (main.tex:756) but does not apply here.
- No data file backs Figure 4.2 (spectral-resolution convergence), and `background_context.tsv`
  is the only one of the four new results with no run log retained.

### 7. Are previous studies and the strengths and limitations of the own work critically discussed? — **+**

This is the thesis's strongest habit. Table 6.1 ranks six limitations by their ability to move
the number rather than by ease of fixing. Table 3.1 fences the proxy. Table 3.2 states for each
validation check what it *cannot* establish, and main.tex:578 volunteers that the strongest
equality is the least independent one — that sentence alone is worth a lot. The
charged-time-versus-calendar-time warning (main.tex:550) and the instruction not to read
Table 5.1 across catalogs (main.tex:671) are both unforced. All four
`known_retention_limits` from `run_matrix_2026-07-24.yaml` appear in Appendix B; nothing in
that file is concealed. The paragraph at main.tex:960 — that an iso-mission-time requirement
inherits an *amplified* version of any background error, so a background correction
invalidates rather than perturbs the requirement — is a genuine, transferable insight and the
best paragraph in the document.

Held back by what is *not* discussed, all of it in the new material:
- The throughput double-count (Critical 1 / Major 1).
- The pre-efficiency reference plane makes N_I scale with eta (main.tex:887). That is a
  definition, and harmless at fixed eta — but Section 5.7 varies eta. A detector-side term of
  fixed absolute rate maps to a pre-efficiency rate that *doubles* when eta halves, so the
  penalized allowances of Table 5.7 are optimistic for exactly the terms N_I is most likely to
  aggregate. Not among the three boundaries listed at main.tex:915.
- The Guyon 50/25 comparison mixes two different sentences of the source (see audit); the
  thesis's like-for-like framing is defensible but its provenance is not stated.

### 8. Are the results placed in a broader context? — **+**

The right instinct, executed unevenly. Section 6.1's move — convert an abstract
ph/s/um allowance into "a few percent of an irreducible foreground" (main.tex:944) — is
exactly what an engineering reader needs, and the follow-through that local zodi supplies
1760 of 2260 ph/s/um at 10 um (main.tex:946, verified against `background_context.tsv`) is
what makes the 27.3 percent defect land. The refusal to propagate the correction into
published LIFE yields without rerunning them (main.tex:634) is correct restraint.

Weaknesses:
- The attribution error at main.tex:944 (Major 2) undercuts the paragraph it anchors.
- **No comparison to any published instrumental-noise allowance**, although the direct
  predecessor supplies one: Dannert's thesis Tables 3.4 and 3.5 give maximum allowed
  perturbations and "asymptotic upper limits in detector thermal background and dark current"
  for the fundamental-noise-limited regime. Those are the numbers a reader will want next to
  140 ph/s/um, they are in a source already cited eight times, and they are not brought in.
- No translation into engineering units (e-/s/pixel, an equivalent detector temperature) that
  would let a subsystem engineer sanity-check the allowance.

### 9. Are suggestions made for subsequent research? — **+**

Section 6.5 is concrete, prioritised and maps onto Table 6.1 one-to-one: replace sin^n with a
realizable combiner including normalized throughput and losses; allocate the aggregate to
subsystems at the same plane; make the completion criteria non-strict; retain per-universe
component times to enable bootstrap intervals; extend to inclined/asymmetric exozodi.
Appendix B.1 turns the last of these into a storage checklist. That is more actionable than
most outlooks.

Two gaps: nothing follows from Section 5.7 itself — the obvious next study is a null-order
versus throughput trade using the sweep machinery already built, and the obvious literature is
the kernel-null family sitting uncited in the bibliography. And there is no indication which
suggestion is cheapest or most urgent.

---

## Findings by severity

### Critical

**C1. The claim that the local-zodiacal 4/pi correction is exact and transmission-map
independent is wrong, and the 0.4 percent residual is misattributed.**
main.tex:632: *"The factor is exact rather than approximate, and does not depend on the
transmission map... any variation of the transmission across the field cancels between
numerator and denominator."* And: *"A direct measurement against the old grid returns 1.268,
and the residual 0.4 percent is that grid's own discretization error rather than a departure
from the identity."*

The pre-rewrite code (`git show 2fd5142:lifesim/instrument/pn_localzodi.py`, the
`fov_taper=='gaussian'` branch) is

```python
ap = np.ones_like(self.data.inst['radius_map'])          # full SQUARE
lz_flux = lz_flux_sr * (np.pi * image_angle**2)          # circular solid angle
lz_leak = (ap*t_map).sum(axis=(-2,-1)) / ap.sum() * lz_flux * area
```

with the Gaussian taper already baked into `t_map` (`transmission.py:169`,
`tm *= exp(-(pi/(4*hfov)*r)**2)`). The new path integrates over the **circle** of radius
`image_angle` (`pn_localzodi.py:128`, `radial_average_tm`). So

  new/old = mean_circle(f) / mean_square(f) = (4/pi) * rho,  rho = Int_circ f / Int_square f < 1,

and rho depends on the transmission map and the taper. The "variation cancels" argument fails
because numerator and denominator are over *different domains*.

Quantitatively: `image_angle = hfov*(4/pi)*sqrt(-ln(fov_threshold))` (`instrument.py:111`)
with `fov_threshold = 0.01` (`settings.yaml:54`), so z = R/w = sqrt(-ln 0.01) = 2.146 and the
pure-taper prediction is (4/pi)(1-e^-z^2)/erf(z)^2 = **1.2666**. A converged 2001x2001
evaluation of the actual tm3 x taper gives **1.26748 / 1.26781 / 1.26844** at
(10 um, 20 m), (4 um, 60 m), (18.5 um, 15 m) — i.e. the ratio is 1.267-1.268, it *varies with
wavelength and baseline*, and it is systematically below 4/pi = 1.27324 by ~0.4 percent. The
measured 1.268 is therefore explained exactly by the tapered flux in the corners of the
square, not by discretization. `ANALYTIC_NOISE_REWRITE.md:175` even records that the ratio was
"~1.268 regardless of grid resolution, i.e. not a discretization effect", then contradicts
itself at line 191; the thesis inherited the wrong half.

Consequences: (i) the exactness sentence must go; (ii) Appendix A.4's description of the old
code (main.tex:1097) is factually wrong; (iii) main.tex:636 and the Table 4.1 caption say
restoring pi/4 "reproduces the pre-correction path identically" and that "the two
configurations differ only in the defect" — it reproduces it to 0.4 percent, and
`ablation_throughput.py:200` hard-codes `PI_OVER_4` with the same incorrect justification in
its comment.

Science impact: **none** — 0.4 percent, and the production runs used the correct circular
integral throughout. But this is a stated-as-exact mathematical claim, used twice, that is not
exact, and it sits under the thesis's most-advertised finding. Reported as Critical because of
what it is, not what it changes.

### Major

**M1. The Guyon throughput penalty is charged partly twice; the headline "cost exceeds benefit
by a factor of three to five" is closer to a factor of two.**
The thesis knows the proxy is lossy: main.tex:865 and Table 5.5 record the far-field envelope
average falling from 1/4 to 3/16, "a 25 percent reduction", and `background_context.tsv`
confirms local-zodi transmission at exactly 0.75000 x order-2 at every wavelength. In
LIFEsim's normalization the four outputs sum to unity, so the two chopped dark outputs carry
2 x 1/4 = **50 percent** at order two and 2 x 3/16 = **37.5 percent** under the sin^4 proxy —
i.e. the proxy has already spent half the distance from Guyon's 50 percent to his 25 percent.
Section 5.7 then applies the full Guyon factor 0.5 to `eff_tot` (main.tex:887;
`ablation_throughput.py:13`, whose docstring asserts the proxy "charges order four nothing for
its throughput"), landing at an effective 18.75 percent — *below* the Angel Cross. The netted
factor is ~2/3, not 1/2.

Recomputing from the thesis's own Table 5.6 at tau = 0.10 (eta = 0.06, the closest netted
point): zero-budget time 6.09 yr (Hab2Max) and 8.55 yr (Hab2Min). The conclusion "no
admissible allowance at any target" **survives** (6.09 > 6.0; 8.55 > 8.0). But the cost/benefit
ratio becomes 1.63/0.85 = **1.9** and 2.51/1.37 = **1.8**, not the 3-5 asserted in the
abstract (main.tex:192), main.tex:913 and main.tex:950. A factor-of-two-to-three overstatement
of the flagship new number.

**M2. "the difference being the suppressed stellar leakage" is wrong: 44 percent of the drop is
the proxy's own throughput loss.**
main.tex:944 states the band-averaged background falls from ~4300 to ~2350 ph/s/um between
orders, "the difference being the suppressed stellar leakage". Width-weighted band averages
from `background_context.tsv` (Hab2Max): order 2 = star 1098.7 + localzodi 2970.1 +
exozodi 305.3 = 4374.1; order 4 = star 0.3 + localzodi 2227.6 + exozodi 198.1 = 2426.0.
Of the 1948 ph/s/um drop, stellar leakage supplies 1098 (56 percent), local zodi 742
(38 percent) and exozodi 107 (5.5 percent). The zodiacal drop is the 1/4 -> 3/16 transmission
loss the thesis documents two sections earlier. The attribution as written reinforces exactly
the confusion behind M1.

**M3. Section 5.3 contradicts Appendix B.3 on what the reported amplitudes guarantee.**
main.tex:787: "amplitudes below the reported value satisfy the corresponding mission-time
target under the monotonic-search assumption." Table B.2 / `ablation_throughput.tsv` show 15
of 24 control rows with positive residuals — Hab2Max/5.5/flat achieves 5.541 yr against a
5.5 yr target, Hab2Max/6.0/short 6.045, Hab2Min/8.0/flat 8.036, and so on. For those rows the
reported amplitude does not meet the target, and neither do amplitudes just below it.
Appendix B.3 (main.tex:1145) states this correctly; Section 5.3 states the opposite.

**M4. The thesis's own #4 limitation could have been closed by the new runs and was not.**
main.tex:552 / main.tex:975 present the missing per-universe time vectors as an unrecoverable
property of the old campaign. `ablation_throughput.py` re-ran the full AMS 57 times in
July 2026; `ams.py:485` computes `np.percentile(distribution, 90)` and discards
`distribution`. Storing it for the eight primary rows would have converted the correct but
abstract rank interval [X_(84), X_(96)] into an interval in years — the single most valuable
missing statistic in the thesis. Presenting it as an inherited constraint is no longer accurate.

### Minor

- **m1.** Same quantity, three values: Hab2Min/order 2/flat is 60 (Table 4.1, main.tex:648),
  65 (Table 5.1, main.tex:742; abstract main.tex:190; main.tex:942; main.tex:992) and 62.2
  (Table B.2). Hab2Min/order 4/flat is 600 (Table 4.1), 590 (Table 5.1, abstract) and 596.5
  (Table B.2). main.tex:1149 discusses only the "65" facet and never reconciles Table 4.1.
- **m2.** main.tex:752 gives the Hab2Max order-4 5.5 yr flat allowance as "650"; Table 5.1 says
  640 and the reproduction 641.2.
- **m3.** Table 4.1's Ratio column is computed from unrounded endpoints (751.99/62.17 = 11.0)
  but printed beside rounded ones (690/60 = 11.5). Same for the 5.3 entry.
- **m4.** main.tex:944 quotes ~4300 and ~2350; the width-weighted band averages are 4374/2426
  (Hab2Max) and 4340/2403 (Hab2Min) — rounded down by 2-3 percent with no stated convention.
- **m5.** "largest for the shortest campaigns" (main.tex:911) is not a trend: ordering by
  campaign length gives 28.7 percent (4.47 yr), 17.4 percent (5.32 yr), 21.4 percent (6.04 yr),
  20.9 percent (7.41 yr). Only the extremum holds.
- **m6.** main.tex:913 and main.tex:950 say "three to five"; the largest ratio in the four
  comparisons is 4.39/0.85 = 5.16.
- **m7.** main.tex:1145 "returns its last accepted amplitude" — the code returns the last
  `guess` regardless (`trade_space_explorer.py:162`); on a bracket-width termination that can
  be a rejected one.
- **m8.** main.tex:550 cites Table 2.1 for an observing efficiency of 0.8 that Table 2.1 does
  not contain (main.tex:259-273).
- **m9.** `background_context.tsv` sums per-bin **medians** of the three components
  (`ablation_throughput.py:309-310`); a sum of medians is not the median of the sum, and
  main.tex:944 reads as the latter.
- **m10.** `laugier2020kernel` is in the bibliography and never cited.
- **m11.** Appendix A.2 attributes the uniform-disk leakage to Lay 2005; Lay 2005 Sec. 2.D.2
  states it comes from "Eqs. (10) and (11) of Ref. 11", and its reference 11 is Lay 2004.
- **m12.** The abstract credits the u-quadrature with "permitting accurate wavelength-bin
  quadrature"; `ANALYTIC_NOISE_REWRITE.md:378` records the error it removed as <= 0.3 percent
  (star) and <= 0.03 percent (exozodi) at R = 20. The thesis nowhere states that magnitude,
  which leaves the change sounding larger than it was.
- **m13.** No retained run log for `background_context.tsv`, unlike the other three new results;
  and no data file at all behind Figure 4.2.

---

## Citation audit table

| Claim location | Reference | Supported? | Note |
|---|---|---|---|
| main.tex:326 stellar and local-zodi leakage "nominally independent of the array rotation angle... appear at zero frequency" | Lay 2004, Sec. 4 | **Yes** | Source: "The photon rates obtained for the stellar and local zodi geometric leakages are nominally independent of the array rotation angle, and would therefore appear as DC ... contributions." Near-verbatim, correctly scoped. |
| main.tex:326 "for rotationally symmetric sources the detected signal does not depend on the rotation angle of the array" | Dannert+2022 (LIFE II), Sec. 2 | **Yes** | Source sentence matches almost word for word, including the star / local zodi / homogeneous face-on exozodi enumeration. |
| main.tex:402, Table 2.4 exozodi = smooth face-on disk "tied to established exozodiacal modeling" | Kennedy+2015 | **Yes** | T_BB = 278.3 L^0.25 r^-0.5 K; surface density power law alpha = 0.34; r_in = 0.034 AU, r_out = 10 AU; treated as 2D face-on. Hedged correctly ("follows the prescription used in LIFEsim"). |
| main.tex:503 / 885 second-order Bracewell 50 percent (two of four outputs) vs fourth-order Angel Cross 25 percent (one of four) | Guyon+2013, Sec. 1 | **Yes, but conflated** | Guyon's direct 50-vs-25 contrast is *2-aperture* Bracewell vs 4-aperture Angel Cross. The "4-aperture, two of four outputs, 50 percent" figure comes from his *next* sentence about Darwin. The thesis's like-for-like framing is the better comparison but its provenance is not stated. |
| main.tex:1058 uniform-disk stellar leakage "given by Lay" | Lay 2005 | **Partially** | Lay 2005 does present it (Sec. 2.D.2, the J1 form) but explicitly attributes it to "Eqs. (10) and (11) of Ref. 11" = Lay 2004. Primary source should be Lay 2004, or both. |
| Table 2.2 eta_earth = 0.19 (+0.19/-0.10), 0.34 (+0.38/-0.19) | Kammerer+2022 (LIFE VI), Table 1 | **Yes** | Exact match, EEC row, per Sun-like star — and the thesis correctly notes it is *not* a fraction of stars (main.tex:284). |
| main.tex:284/286 hab2min/hab2max = Bryson model-1 hab2-stars low/high bound; difference driven by >500 d extrapolation | LIFE VI Sec. 2.2 | **Yes** | Source: low bound = completeness beyond 500 d held at its 500 d value (conservative); high bound = set to zero (optimistic). Direction correct. |
| Table 2.3 caption "LIFE paper VI uses a narrower EEC subset, 0.8 a_p^-0.5 R_E <= R_p <= 1.4 R_E" | LIFE VI Table 1, note (c) | **Yes** | Matches. |
| main.tex:284 LIFE VI stellar sample "single and wide binary main-sequence stars within 20 pc" | LIFE VI abstract/Sec. 2 | **Yes** | Matches. |
| Table 2.1 "SNR 7 follows the LIFE yield-study detection convention" | LIFE VI | **Yes** | "we required a conservatively high signal-to-noise ratio (S/N) of 7 integrated over the full wavelength range for detection". |
| Table 2.1 "44.1 is the integrated broadband equivalent of SNR 10 at 11.2 um, R = 50" | Dannert 2025 thesis | **Yes** | "S/N_{11.2 um} = 10 for R = 50. This corresponds to an equivalent integrated S/N = 44.1." Verbatim. (Ultimate origin is Konrad+2022; crediting Dannert for the 44.1 conversion is correct.) |
| main.tex:671 "A 10 h slew is the inherited baseline" | Dannert 2025 thesis | **Yes** | "By assuming a slew time of 10 h..." |
| main.tex:227 predecessor "already introduces an aggregate instrumental photon-noise term... fundamental-noise-limited criterion... effect on detection yield" | Dannert 2025 thesis, Sec. 3.4.2 / App. 3.5 / Ch. 5 | **Yes** | "We collect all additional photon noise sources into the..."; App. 3.5 constrains perturbations for the fundamental-noise-limited regime; Ch. 5 couples to yield. Non-claiming framing is correct and creditable. |
| main.tex:284 P-Pop places a hypothetical system around every stellar target, Kepler-constrained | Kammerer & Quanz 2018 | **Yes** | Standard description of the tool. |
| main.tex:605, 616, 1059 Bessel integral rep., derivative identity, power series | NIST DLMF 10.9.1, 10.6.6a, 10.2.2 | **Yes** | Identities correct; the DLMF equation numbers are cited individually, which is good practice. |
| main.tex:1101 circular FoV "consistent with the continuous field-of-view convention in the LIFE source model" | LIFE II | **Yes** | "The effective field-of-view is assumed to be FoV = lambda/D in diameter as we assume the light will be coupled into single-mode fibers", with a solid-angle integral. Supports the circular convention. |
| main.tex:632/1097 description of the removed grid path | source code at commit 2fd5142 | **No** | See Critical 1. Appendix A.4's version is contradicted by the code; the exactness inference is invalid. |
| main.tex:944 "the difference being the suppressed stellar leakage" | own `background_context.tsv` | **No** | Stellar leakage is 56 percent of the drop; see Major 2. |
| main.tex:284 "4505 nearby stars ... out to roughly 50 pc", verified from catalog files | own catalogs | Not checked | 316 MB of catalog; claim is internally sourced and plausibly checked, but I could not verify it independently. |

Overall: the citation record is **accurate**. Of 18 checkable attributions, 15 are fully
supported, two carry provenance imprecision (Guyon, Lay 2005), and the only outright failures
are claims about the candidate's *own* code, not about the literature.

---

## Concrete remaining edits

Ordered by impact.

1. **Net the Guyon factor against the proxy's own 25 percent loss (main.tex:885-915, 950,
   abstract:192).** Insert after main.tex:887: *"The proxy is not throughput-neutral: its two
   chopped outputs carry 2 x 3/16 = 37.5 percent of the collected light in the far field
   against 2 x 1/4 = 50 percent at order two (Section 5.6), so part of the Guyon loss is
   already charged. The netted factor is 25/37.5 = 2/3, i.e. tau = 0.10 in Table 5.6, rather
   than 0.5."* Then replace the cost/benefit numbers: at tau = 0.10 the cost is 1.63 yr
   (Hab2Max) and 2.51 yr (Hab2Min) against benefits of 0.85 and 1.37, so **"a factor of about
   two"** replaces "three to five" in the abstract, main.tex:913 and main.tex:950. State that
   the infeasibility conclusion is unchanged (6.09 > 6.0 yr; 8.55 > 8.0 yr) and that the
   tau = 0.075 arm is retained as a conservative bound.

2. **Delete the exactness claim and correct the two descriptions of the old code
   (main.tex:626-632, 636, Table 4.1 caption, main.tex:1097).** Replace main.tex:632's last
   three sentences with: *"The tapered branch summed the transmission over the full square
   evaluation grid, divided by the square pixel count, and multiplied by the circular solid
   angle; the corrected path integrates the same quantity over the circle. The two therefore
   differ by (4/pi) x rho, where rho is the fraction of the tapered transmission integral
   falling inside the inscribed circle. With the production taper (fov_threshold = 0.01) rho =
   0.995, so the correction is 1.267-1.268 rather than 4/pi = 1.2732; the measured 1.268 is
   this value, not a discretization residual."* Rewrite Appendix A.4 (main.tex:1097) to match —
   it currently says the old code integrated inside the circle, which is false for the default
   branch. Soften main.tex:636 and the Table 4.1 caption from "reproduces the pre-correction
   path identically" to "reproduces it to 0.4 percent", and fix the comment at
   `ablation_throughput.py:196-199`.

3. **Fix the attribution at main.tex:944 and add the component split.** Replace "the difference
   being the suppressed stellar leakage" with: *"Of that 1950 ph/s/um difference, suppressed
   stellar leakage supplies about 1100 and the proxy's own 25 percent envelope-transmission
   loss supplies most of the remainder (local zodi 2970 -> 2228, exozodi 305 -> 198)."*
   Numbers from `background_context.tsv`, width-weighted.

4. **Repair main.tex:787.** Replace "amplitudes below the reported value satisfy the
   corresponding mission-time target" with: *"each reported amplitude satisfies the achieved
   time given in Table B.2, which lies within 0.05 yr of the nominal target and exceeds it in
   fifteen of the twenty-four rows; the target itself is met only to that tolerance."*

5. **Close the rank-uncertainty gap for the eight primary rows, or restate why not
   (main.tex:552, 975, 1145, Appendix B.4).** The reproduction campaign already reruns the AMS;
   capture `distribution` at `ams.py:485` and report [X_(84), X_(96)] in years alongside the
   90th percentile for the eight rows of Table B.2. If that is out of scope for the submission,
   change the wording from "cannot be converted ... after the fact" to "was not retained by the
   reproduction runs reported here", which is the accurate statement now that a fresh campaign
   exists.

6. **Reconcile Table 4.1 with Tables 5.1 and B.2 (main.tex:646-656, 738-752).** Adopt one
   convention — two significant figures from Table B.2 — throughout: 62 not 60/65, 596 not
   590/600, 641 not 640/650. Recompute the Table 4.1 Ratio column from the values printed
   beside it, or state that it uses unrounded inputs. Fix "650" at main.tex:752.

7. **Report the sweep's local slopes (main.tex:911).** Add: *"Fitted to adjacent efficiency
   pairs rather than to the endpoints, the implied constant fraction ranges from below zero to
   about 30 percent, reflecting the discrete target-set and percentile changes discussed in
   Section 5.3; the 17-29 percent figure is an endpoint secant, not a resolved
   decomposition."* Drop "largest for the shortest campaigns".

8. **State the reference-plane caveat in Section 5.7 (after main.tex:915).** *"A fourth
   boundary: because N_I is referred to the pre-efficiency plane, halving eta halves the
   delivered instrumental noise. A detector-side term of fixed absolute rate would instead
   double at that plane, so the penalized allowances of Table 5.7 are optimistic for exactly
   the terms N_I is most likely to aggregate."*

9. **Cite Laugier+2020, Angel (1990) and Angel & Woolf (1997) (main.tex:503, 987).** Kernel
   nullers are the concrete answer to the outlook's "realizable higher-order combiner", and the
   Angel Cross is currently known to the reader only through one sentence of Guyon. State the
   Guyon provenance explicitly at main.tex:503 (2-aperture Bracewell vs Darwin's 4-aperture
   50 percent).

10. **Place the allowance against the predecessor's numbers (Section 6.1).** Compare 140 and
    65 ph/s/um with Dannert's Tables 3.4/3.5 asymptotic limits on detector thermal background
    and dark current, and give one engineering translation (e-/s/pixel at the adopted QE and
    binning). Two sentences; large gain in credibility.

11. **Housekeeping.** Fix main.tex:1145 ("last accepted" -> "last evaluated"); fix main.tex:550's
    reference to a Table 2.1 row that does not exist (add the row or cite `settings.yaml`);
    state that the component figures in Section 6.1 are per-bin medians summed across
    components; correct "three to five" -> "three to five, reaching 5.2"; retain a run log for
    the background-context evaluation and a data file behind Figure 4.2; add Lay 2004 alongside
    Lay 2005 at main.tex:1058.

---

## Suggested block grade

# 5.25

**Justification.** The competence on display is real and, in the areas that matter most for
this block, verifiable. The citation record survived a source-by-source audit — fifteen of
eighteen attributions fully supported, several near-verbatim, and the two subtlest points in
the whole document (Lay's rotation-angle *independence* rather than rotation *averaging*, and
the eta_Earth / stellar-scaffold population mismatch) are handled correctly and unprompted.
The analytic derivation in Appendix A is correct, general, and validated against the right
independent references. The research question is unusually well posed and every sub-question
is closed, including the one that can only be closed partially. The validation matrix states
what each check cannot establish and includes its worst rows. The reproduction in Appendix B.3
is honest to the point of reporting its own disagreements, and the binomial rank calculation is
correct to four figures. The limitations table is ranked by consequence rather than
convenience, and the paragraph at main.tex:960 on requirement amplification is a genuine
contribution to how this class of result should be quoted.

Against that, the flagship *new* material is where the errors concentrate, and that is the
material an examiner weights most. The throughput ablation charges part of its penalty twice
because the proxy's own 25 percent transmission loss — measured, tabulated and discussed
elsewhere in the same thesis — is never netted out; the headline "three to five times" becomes
"about two" when it is. The 4/pi correction, the thesis's most-advertised finding, is asserted
to be exact and transmission-map-independent when it is neither, on an argument that does not
follow, with the 0.4 percent residual misattributed and the actual code described two
incompatible ways. The broader-context paragraph attributes a background reduction to stellar
leakage when 44 percent of it is the proxy's throughput. Section 5.3 states a guarantee its own
Appendix B.3 disproves for the majority of rows. And the thesis's self-identified fourth
limitation was closable at zero cost by the very campaign that produced the new tables, and was
not closed. None of these invalidates a number; all of them are claims the candidate makes
about their own work that do not hold up, which is the specific competence this block grades.

That combination — excellent framing, excellent literature handling, excellent execution,
recurrent over-claiming about the execution — sits above "good with certain flaws" (5.0) and
below "very good with minor flaws" (5.5). Hence 5.25.

**What would raise it half a grade (to 5.5-5.75).** Edits 1-4 are sufficient and are all
achievable in a day. Concretely: net the Guyon factor and restate the cost/benefit as ~2x
(edit 1); delete the exactness claim, correct both descriptions of the removed code, and
attribute the 0.4 percent to the corner flux (edit 2); fix the stellar-leakage attribution in
Section 6.1 with the component split (edit 3); repair the guarantee sentence at main.tex:787
(edit 4). Adding edit 5 — even a two-line statement of [X_(84), X_(96)] in years for the eight
primary rows — would close the last substantive statistical gap and, with edit 10's comparison
against Dannert's published subsystem limits, would carry the block to 5.75. A 6.0 in this
block would additionally require the null-order proxy to be replaced by, or at minimum
benchmarked against, a realizable combiner from the kernel-null literature already sitting
uncited in the bibliography.
