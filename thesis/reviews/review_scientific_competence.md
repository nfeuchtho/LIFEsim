# Block: General scientific competence

External examiner report — MSc thesis, *Instrument-Agnostic Iso-Mission-Time Noise Budgets for LIFE Using a Null-Order Proxy* (N. Feuchthofen, IPA / Quanz Group).
Document graded: `C:\Users\nicol\Desktop\LIFE\LIFESim\thesis\main.tex` (1104 lines, read in full incl. Appendices A/B and bibliography).

**Verification method.** Every recomputable number in the thesis was independently recomputed from the production inputs (`lifesim/catalogs/catalog_hab2{lo,hi}.txt`), the production source tree, or by re-deriving the algebra. Every non-trivial attributed claim was checked against the source PDF text. Where I could not verify something, I say so explicitly.

---

## Verdict per sub-question

### 1. Sufficient familiarity with the literature — **o**

The core LIFE literature that *is* used is used accurately, and I verified it line by line. η⊕ = 0.19⁺⁰·¹⁹₋₀.₁₀ / 0.34⁺⁰·³⁸₋₀.₁₉ (main.tex:285–286) reproduces Kammerer et al. 2022 (LIFE VI) Table 1, EEC row, Sun-like columns, exactly. SNR = 7 (main.tex:256) is verbatim LIFE VI ("a conservatively high signal-to-noise ratio (S/N) of 7 for detection"). SNR = 44.1 (main.tex:266) is verbatim Dannert 2025 ("S/N₁₁.₂ μm = 10 for R = 50 … corresponds to an equivalent integrated S/N = 44.1"). The 10 h inherited slew (main.tex:619) is in Dannert 2025 ("By assuming a slew time of 10 h"). The Kennedy et al. 2015 citation (main.tex:393) is genuinely supported: the production code implements Kennedy Eq. 2 (T = 278.3 L^0.25 r^−0.5) and Eq. 3 (α = 0.34, Σ_m,0 = 7.12 × 10⁻⁸ at r₀ = √L AU, r_in = 0.034 √L AU) exactly (`pn_exozodi.py:78–81,137,140`).

Against this, three gaps are serious. (a) The **direct predecessor is never engaged**. Dannert 2025 §3.4.2 defines an aggregate *instrumental photon noise term* σ_ph,inst collecting "all additional photon noise sources", defines a fundamental-noise-limited criterion σ_fund ≥ σ_inst (his Eq. 3.22, plus a 5× variant), and Chapter 5 / Fig. 5.7 studies "Impact of instrumental noise on yields". That is conceptually the same object as N_I and the same framing as main.tex:418. The thesis cites `dannert2025thesis` six times, but only for inherited constants and to say systematics are excluded, and asserts at main.tex:206 that the reference studies "do not yet provide the wavelength-dependent iso-mission-time boundary for a mechanism-independent aggregate random-noise term". The *iso-mission-time inversion* is new; the aggregate-random-noise-term concept is not, and the thesis does not say so. (b) **No higher-order-nulling literature at all**, although a fourth-order null proxy is the thesis's central novelty and §6.5 calls for "a realizable higher-order combiner". Guyon et al. 2013 (*Optimal Beam Combiner Design for Nulling Interferometers*) and Laugier et al. 2020 (*Kernel nullers for an arbitrary number of apertures*) are both sitting in the candidate's own literature folder and are uncited. (c) The **bibliography has 11 entries** (main.tex:1031–1101). Missing are the Kaltenegger+2017 habitable-zone model that actually defines Experiment-1 eligibility (`habitable.py`), any reference for the `darwinsim` local-zodiacal surface-brightness model — the very term the thesis corrects by 27 % — and Mugnier et al. 2006, which LIFE II invokes for the incoherent-combination argument the thesis relies on.

### 2. Aims / hypothesis / questions clearly formulated — **+**

Unusually disciplined. §1.1 (main.tex:210–222) states one central question with its scope built in ("For a specified operating point and a tested family of additive random-noise budgets…"), five sub-questions, and the Conclusion (main.tex:878–885) closes each of the five explicitly and in order. The abstract (main.tex:188–192) ends with an explicit anti-overclaim paragraph, and main.tex:208 pre-emptively states what the bridge quantity is *not*. Deductions: the "dimension of the AMS parameter space" sub-question resolves to "formally infinite-dimensional" (main.tex:431), which is a definitional rather than a scientific answer, and the thesis itself concedes the 10-dimensional / 317-year illustration is "illustrative rather than a claim" (main.tex:442) — I confirm 10¹⁰ s = 316.9 yr, so the arithmetic is right, but it is rhetoric, not analysis. More importantly, the mission-time targets 5.5/6.0 yr (Hab2Max) and 7.5/8.0 yr (Hab2Min) are introduced at main.tex:619 with no justification and no citation, yet they are the single strongest driver of the answer (140 → 610 for half a year, main.tex:700).

### 3. Methods and techniques properly described — **o**

What is described is described precisely, and I verified it against code. The reference-plane convention in Table 2.4 (main.tex:351–369) is correct: `pn_star.py:120` returns ph s⁻¹ after area and before η, and `ams.py:771` forms `noise_bg = (exozodi + star + localzodi) * int_time * eff_tot * 2`, matching V_i = 2ηt[B_i + N_I,i + A F_p,i n_i] exactly. s_i = √⟨(T₃−T₄)²⟩ and n_i = √⟨T₄²⟩ (main.tex:375) match `ams.py:756–757` and `transmission.py:222–223` exactly. The scheduler steps (main.tex:523–531) match `ams.py:429–484` step for step, including "at least 51 detections in at least 91 universes" (verified against `ahgs.py:263–266`: `(counts > 50).sum() > 0.9 × 100`). The claim that the 0.8 observing efficiency "neither caps nor rescales the returned time" in experiment-limited mode (main.tex:533) is correct — `obs_time` is only used under `opt_limit == 'time'` (`ahgs.py:191,222`).

The deductions are that **four load-bearing model ingredients are never stated**: the exozodiacal radial profile (Appendix A.3, main.tex:965, refers only to "the adopted smooth radial brightness profile", defeating the appendix's stated purpose at main.tex:893 of making the result "independently inspectable without requiring the reader to reconstruct the mathematics from code"); the habitable-zone model (Kaltenegger+2017 'MS', `options.py:198`) that defines the eligibility flag; the fact that LIFEsim's own thermal and dark-current photon-noise modules (`pn_thermal.py`, `en_darkcurrent.py`) are **not connected** in the production run (`runner.py:44–49` adds only exozodi, local-zodi and star), so the "astrophysical" floor B_i is not LIFEsim's standard noise floor; and the fact that ecliptic **longitude is frozen at 3π/4** for every target (`pn_localzodi.py:87`, with an open `# TODO Implement longitude dependence` at line 72). One described parameter is simply wrong: main.tex:624 says the search "starts with an amplitude bracket from 0 to 50,000", but the production script uses `upper_start=5000` (`runner.py:113`). The field-of-view taper is described as deliberately unspecified ("without assuming a particular taper formula", main.tex:422) although a specific Gaussian exp[−(πr/4h_fov)²] with a threshold-derived outer radius is what runs (`transmission_analytic.py:131`, `pn_exozodi.py:119`).

### 4. Methods appropriate for the subject — **+**

The central methodological choice is sound and the mathematics is correct. I re-derived Appendix A in full. The even-power reduction (main.tex:897–905) is the standard identity and checks at p = 1. The claim at main.tex:906 that the imaging factor "contributes one half after full azimuthal integration" is not an approximation but exact: cos²(ψ ∓ π/4) = (1 ± sin 2ψ)/2, sin^{2p}φ is even and sin 2ψ odd under φ_az → φ_az + π, so the cross term vanishes identically. Eq. 4.2 (main.tex:589–595) is then correct and reproduces ⟨T₂⟩ = ¼(1 − J₀) and ⟨T₄⟩ = 1/16(3 − 4J₀(x) + J₀(2x)) at p = 1, 2. The disk average via 2J₁(aR)/(aR) is correct; the small-star limits x²/32 and x⁴/256 and the ratio x²/8 all check against the J₁ power series. Far-field averages ¼ → 3/16 = a 25 % reduction (main.tex:820) is right. The wavenumber substitution u = 1/λ is well motivated (phase ∝ b/λ) and is the right way to kill the chirp. The bracketed monotone search and the ensemble percentile are appropriate instruments for the question.

Deductions: (i) the planet self-noise coefficient is an **RMS** √⟨T₄²⟩ where a photon *rate* should carry the **mean** ⟨T₄⟩; this is inherited from LIFEsim (`transmission.py:223`), not introduced here, but the thesis presents both s_i and n_i as "RMS coefficients" (Table 2.4) without noting that only one of them is a variance-consistent weighting. (ii) The baseline prescription constant 0.589645 is derived for a *second-order* double Bracewell (`ams.py:115–117`) and is retained unchanged at order four; Table 3.1 lists this under "Preserved between orders", so it is disclosed, but the order-four configuration is therefore not even baseline-optimal. (iii) No ablation isolates leakage suppression from the simultaneous throughput change — the thesis concedes this itself (main.tex:809).

### 5. Research carried out carefully — **+**

Independent verification was strikingly successful. Streaming both production catalogs I recover Table 2.3 (main.tex:293–306) **exactly**: 486,244 / 729,925 planet rows, 4505 stars, 100 universes, 205,715 / 318,654 eligible rows, per-universe ranges 1958–2154 and 3049–3331, medians 2058.5 and 3194 — every digit. Max catalog distance is 50.00 pc, confirming main.tex:275. Recomputing x = 2πbR★/λ over all 4505 stars with the production baseline prescription gives median fourth-to-second-order leakage ratios of 6.33 × 10⁻⁵ at 10 μm and 1.85 × 10⁻⁵ at 18.5 μm (thesis: "about 6.3 × 10⁻⁵" and "about 1.9 × 10⁻⁵", main.tex:807) and min x = 0.00504 at 18.5 μm (thesis: "remains above 0.005", main.tex:807) — a tight, correct, and non-obvious bound. The binomial coverage of [X₍₈₄₎, X₍₉₆₎] is 0.95569 (thesis: "approximately 0.9557", main.tex:1024). Appendix B.2 provides SHA-256 hashes for catalogs, source closure, result tree and validation scripts, and honestly records that the production tree was dirty.

Deductions: raw per-evaluation grids, scheduler logs and per-universe time vectors are gone; no environment lock; some Table 5.1 values were recovered from rendered vector PDFs rather than raw output (disclosed at main.tex:1021). The methods text disagrees with the production script on the search bracket (§3 above). And the thesis asserts "approved" three times for a physics change whose only internal record says the opposite (see Critical C1).

### 6. Results tested by statistical analysis / sensitivity tests — **−**

This is the weakest area. What exists is correct: Appendix B.3 (main.tex:1023–1026) is a valid distribution-free rank statement, correctly computed, and correctly caveated as narrower than a physical uncertainty analysis. A genuine two-parameter operating-point sensitivity **is** present (Fig. 5.4 magnitude × FoR, Fig. 5.5 slew × FoR, for both catalogs and both null orders), and Fig. 5.3 shows the two-endpoint contour scans that rule out an endpoint artifact. So the check "is a sensitivity analysis over the operating point present?" — yes, for the flat family, and the thesis correctly restricts the transfer (main.tex:738).

But: **no confidence interval appears on any number in Table 5.1 or in the abstract**, while the numbers are printed to two significant figures (65, 140, 590, 650…) — a precision the thesis's own text says is unsupported (main.tex:624: "The two alternative stopping rules do not support a universal ±5 amplitude uncertainty"). The presentation therefore contradicts the caveat. Worse, the sampled quantity's sample size is unknown: `ams.py` builds the time sheet on `np.unique(cat_det.nuniverse)`, so universes with no detected eligible planet are dropped, yet Table 6.1 row 4 and Appendix B.3 both assume exactly n = 100 (main.tex:859, 1024). There is no bootstrap, no repeat run, no sensitivity to the number of universes, to the habitable-zone model, to the exozodi level distribution, or to the observing efficiency, and global monotonicity is asserted as "an empirical property" (main.tex:626) without a reported test.

### 7. Previous studies and own strengths/limitations critically discussed — **o**

The *own* limitations are handled well. Table 6.1 (main.tex:849–866) ranks six limitations that are the real ones, in a defensible order, with the unnormalized proxy correctly placed first. Appendix B.1/B.2 discloses the retention failures, including the awkward one (main.tex:1021: order-four Hab2Min 8-yr values "recovered from the complete vector result PDFs"). Cross-checking against `run_matrix_2026-07-24.yaml`'s `known_retention_limits`, **all four** are disclosed somewhere — though three of the four appear only in Appendix B, not in §6.4, which structurally demotes them.

Three things known internally are absent from the thesis entirely. The exozodiacal log-spacing quadrature defect (up to 35 % error before the fix, `ANALYTIC_NOISE_REWRITE.md` §5) is not mentioned; the ~10.9 % median full-catalog SNR shift caused by the local-zodi correction (§6 of the same brief) — the single most informative number about the correction's impact — is not reported; and the order-4/6 exozodi brute-grid deviations (~10 % on some stars, 4.5–5.4 % at order 2 on the same stars) are absent, which is why Table 3.2's end-to-end row covers "stellar and local-zodiacal terms" only, with no explanation of the omission. On *previous studies*, there is effectively no critical discussion: no comparison to LIFE I/VI yields, none to Dannert 2025 Ch. 3/5.

### 8. Results placed in a broader context — **−**

Programmatic context is good: the introduction and conclusion explain clearly why an iso-mission-time allowance matters to LIFE, and main.tex:208 and 735 are exemplary in defining the hand-off to a later subsystem allocation. Quantitative context is absent. The reader finishes the thesis without any means of judging whether 140 or 650 ph s⁻¹ μm⁻¹ is a demanding or a comfortable requirement. Nothing states what fraction of the astrophysical background the allowance represents at any wavelength — a single number available from Fig. 4.1's own data. Nothing compares N_I to Dannert 2025's σ_inst or to the Lay-2004-derived perturbation levels tabulated in that same thesis (amplitude 0.1 %, phase 0.001 rad, collector position 1 cm rms at 10 μm). Nothing compares mission times or yields to LIFE VI. The material for all of this is in the candidate's own literature folder.

### 9. Suggestions for subsequent research — **+**

§6.5 (main.tex:870–873) is concrete and tied to the identified limitations: replace the sin^n proxy with a realizable higher-order combiner including aperture geometry, normalized throughput, optical losses and instability terms; allocate the aggregate to subsystems at the same reference plane; use non-strict completion criteria and retain failed universes; save per-universe component times to enable bootstrap or rank intervals *in years*; extend the analytic framework to inclined/asymmetric exozodi disks. Appendix B.1 adds a specific five-item retention checklist. These are implementable, not decorative. Two obvious next steps that the thesis itself identifies as missing are not carried into the outlook: the ablation run isolating leakage suppression from throughput change (flagged at main.tex:809), and any comparison against an existing instrumental noise budget.

---

## Findings by severity

### Critical

**C1 — "Approved physics model" is asserted three times with no supporting record, and is contradicted by the only internal document that speaks to it.**
*Location:* main.tex:582 ("The approved physics rewrite"), main.tex:619 ("All results use the approved analytic background model"), main.tex:876 ("Under the approved physics model").
*What is wrong:* `ANALYTIC_NOISE_REWRITE.md:3` states "Status: **implemented, self-consistent, NOT yet supervisor-approved**", and its §13 item 1 lists the ~27 % local-zodi correction as an open decision requiring sign-off ("should be a deliberate, documented decision, not something that ships silently"). The word "approved" appears **zero** times in `thesis/revisions/supervisor_read_2026-07-10.tex` — the version the supervisor read — and three times in the current main.tex (modified 2026-07-24). No approval artifact exists in the repository, and Appendix B.2's otherwise meticulous provenance table records no such decision.
*Why it matters:* the 4/π local-zodi correction changes every headline number in the thesis (the brief measures a ~10.9 % median full-catalog SNR shift). "Approved" is the only thing carrying that change, and it is exactly the kind of adjective an examiner will ask to see evidence for. If approval was granted verbally after 10 July, the record simply does not show it; as written the claim is unsupported.
*Fix:* either cite the approval (date, decision, who) in Appendix B.2 and update `ANALYTIC_NOISE_REWRITE.md`'s status line, or delete the adjective and replace it with a factual statement ("the analytic background model adopted in this work").

**C2 — Headline numbers are quoted to two significant figures with no uncertainty, and the thesis's own data imply the search tolerance alone can be comparable to the smallest of them.**
*Location:* abstract main.tex:190; Table 5.1 main.tex:679–698; conclusion main.tex:876.
*What is wrong:* the search terminates when mission time is within ε = 0.05 yr of target **or** the amplitude bracket is ≤ 10 wide (`trade_space_explorer.py:127`, matching main.tex:624). Using the thesis's own secant slope for Hab2Min flat (65 at 7.5 yr → 460 at 8.0 yr, i.e. 790 ph s⁻¹ μm⁻¹ per year), a ±0.05 yr time tolerance maps to roughly ±40 in amplitude — on a reported value of 65. The secant overestimates the local slope if A(T) is convex, so treat ±40 as an upper bound; even a factor-three reduction leaves ~±20 %. The bracket-width rule alone gives ±5, i.e. ±8 % on 65. The thesis anticipates the objection (main.tex:624) and then declines to give any number, while printing 65, 140, 590, 650 as if precise to ±5.
*Why it matters:* the abstract's two headline sentences are unqualified. In a defense this is the first number to be challenged, and the thesis provides no defensible interval.
*Fix:* report, for each row of Table 5.1, the final bracket [lower, upper] and the stopping reason (both are printed by `locate_mission_cutoff` and cost nothing to retain), and quote amplitudes as intervals in the abstract and conclusion. Round to the precision the bracket supports.

**C3 — The direct predecessor's equivalent quantity is never compared, and the novelty claim overstates the gap.**
*Location:* main.tex:206; discussion §6.1–6.2 (main.tex:833–841); outlook main.tex:870–873.
*What is wrong:* Dannert 2025 §3.4.2 already defines an aggregate instrumental photon-noise term σ_ph,inst collecting "all additional photon noise sources", already defines a fundamental-noise-limited criterion (Eq. 3.22, plus a 5× variant), and Chapter 5 already studies the yield impact of instrumental noise. The thesis's claim that the reference studies "do not yet provide the wavelength-dependent iso-mission-time boundary for a mechanism-independent aggregate random-noise term" is defensible only for the *iso-mission-time inversion*; the aggregate-random-noise concept itself is inherited, and the thesis does not acknowledge it.
*Why it matters:* it simultaneously overstates originality and forfeits the one available external reference point for the headline number. This is the finding that most damages sub-questions 1, 7 and 8 at once.
*Fix:* one paragraph in §6.1 stating the relationship to Dannert 2025 §3.4.2/Eq. 3.22 and Ch. 5, and placing N_I next to σ_inst at a common wavelength, even as an order-of-magnitude statement.

### Major

**M1 — The number of universes actually entering the 90th percentile is unknown, while the statistics assume exactly 100.**
`ams.py` builds `time_sheet` on `np.unique(cat_det.nuniverse)`, so universes with no detected eligible planet are dropped — the thesis says so at main.tex:533 and 857. Yet Table 6.1 row 4 ("The 100 universes resolve only a sampled 90th percentile") and Appendix B.3 both compute with n = 100, and the hedge at main.tex:535 ("Fewer retained universes require different ranks") is never converted into a reported number. *Fix:* report n per run; if n = 100 always, say so and the problem disappears.

**M2 — "Amplitudes below the reported value satisfy the corresponding mission-time target" is not what the algorithm guarantees.**
main.tex:733. `locate_mission_cutoff` returns `guess`, the last evaluated point, not the last *admissible* bracket endpoint (`trade_space_explorer.py:162`). If the loop exits on bracket width after a "too optimistic" guess, the returned value has mission time *above* target, and only amplitudes below the (unreported) `lower` endpoint are verified. Relatedly, the algorithm never clamps `guess` into (lower, upper), so the "bracket invariant is retained" claim at main.tex:624 is stronger than the code enforces, and the `if abs(mtime-cutoff) > epsilon and lower == 0: return 0` branch (`trade_space_explorer.py:158–160`) can report "not realizable" — the dark regions of Figs. 5.4/5.5, per main.tex:626 — for a genuinely small but non-zero allowance. *Fix:* return and report `lower`, or state the caveat.

**M3 — LIFEsim's own thermal and dark-current photon noise are excluded from the reference floor, and this is never stated.**
`runner.py:44–49` connects only exozodi, local-zodi and star noise modules; `pn_thermal.py` and `en_darkcurrent.py` are never instantiated, although `settings.yaml` still carries their parameters (`primary_temp: 48`, `primary_emissivity: 0.025`, `dc_per_pix: 1`). The framing at main.tex:208 ("A later engineering allocation can map detector, optical, thermal, and control-noise terms to that plane") makes this *consistent*, but Table 2.5's "Excluded terms" row lists only calibration bias, drift, correlated instability and confusion. A LIFE-literate reader will assume the standard LIFEsim noise set is present. Because the excluded terms are Poisson terms that would otherwise sit inside B_i, their omission directly inflates N_I. *Fix:* add a row to Table 2.5 and one sentence in §2.5.

**M4 — Ecliptic longitude is frozen at 3π/4 for every target in the dominant long-wavelength background.**
`pn_localzodi.py:87` (`long = 3/4 * np.pi`), with an open `# TODO Implement longitude dependence of localzodi` at line 72. Table 2.5 correctly lists the modelled dependence as "λ, target ecliptic latitude, field of view", but nowhere says longitude was frozen as a simplification. This matters specifically because the thesis's order-four conclusion is that *zodiacal backgrounds dominate* (main.tex:809), so the least-modelled term carries the central claim. *Fix:* state the frozen-longitude assumption in §2.5 and add it to Table 6.1.

**M5 — The `darwinsim` local-zodiacal surface-brightness model is unreferenced in the thesis and in the code.**
`pn_localzodi.py:73` carries a literal `# TODO Find model after which this is calculated and reference`. The thesis's flagship analytic contribution is a 27 % correction to precisely this term, yet the underlying dust model has no citation anywhere. *Fix:* identify and cite the model (or state explicitly that it is inherited and unattributed in the source framework).

**M6 — The 4/π correction is presented as an exact geometric identity when the quantity being renormalized is a non-uniform transmission-weighted integral.**
Appendix A.4 (main.tex:975–984) derives the factor as Ω_circ/Ω_square = π/4, which is exact only if the transmission-times-taper is uniform over the domain. It is not. The internal brief's own numerical measurement is 1.268, not 1.2732 (`ANALYTIC_NOISE_REWRITE.md` §4), and attributes the 0.4 % residual to old-grid discretization; the sign is equally consistent with a genuine square-corner contribution. The abstract's "about 27 %" is safe; main.tex:611's "an increase of approximately 27.3 %" implies an exactness the derivation does not have. *Fix:* state the analytic limit and the measured value, and say which is quoted. I could not verify the old grid code directly — the `.bak` files referenced in `ANALYTIC_NOISE_REWRITE.md` §8 are no longer present in the tree.

**M7 — Mission time is not wall-clock time, and the thesis never says so.**
Verified: with `opt_limit: experiments`, the 0.8 observing efficiency is inert (`ahgs.py:191,222`), so the returned time is integration + slew only. main.tex:533 states the mechanism but draws no consequence, and the words "on-source" and "wall-clock" appear nowhere. A stated "5.5 yr mission time" would correspond to ~6.9 yr of calendar time if the configured 0.8 efficiency were applied. Since the whole thesis is calibrated against mission-time targets, this changes how every headline number should be read. *Fix:* define "mission time" explicitly in §2.4 or §3.3.2 and state the conversion.

**M8 — Validation matrix omits the one term whose independent cross-check was worst.**
Table 3.2 (main.tex:540–557) reports exozodi **self**-convergence only, while reporting an end-to-end image-sampling check for "stellar and local-zodiacal terms". The internal brief records exozodi order-4/6 brute-grid deviations of ~10 % on some stars (and 4.5–5.4 % at order 2 on the same stars), attributed to old-grid aliasing near the Kennedy r_in cusp. The attribution may well be right; the omission is not defensible without saying so. The exozodi log-spacing defect (up to 35 % before fix) and the ~10.9 % median full-catalog SNR shift from the local-zodi correction are likewise absent. *Fix:* add both rows to Table 3.2 with their stated interpretation, and report the 10.9 % figure in §4.2 — it is the most informative single number about the correction.

**M9 — Mission-time targets (5.5 / 6.0 / 7.5 / 8.0 yr) are unjustified and uncited.**
main.tex:619. They are the dominant lever on the answer (main.tex:700: 140 → 610 for half a year) and are introduced without rationale. `settings.yaml` carries `t_search: 78840000` s = 2.5 yr, which is not obviously related. *Fix:* justify against the LIFE mission baseline, or state explicitly that they are arbitrary comparison points.

**M10 — Load-bearing conceptual claim about rotation-angle independence has no citation, and the citation that is present points at the wrong Lay paper.**
main.tex:605 ("Rotation does not 'average away' a circular background; rather, circular symmetry makes its integrated response independent of rotation angle") is uncited, although the internal brief records that exactly this was verified against Lay 2004 §4 and Dannert 2022 §2.2.3/2.3. Lay 2004 states it verbatim: "The photon rates obtained for the stellar and local zodi geometric leakages are nominally independent of the array rotation angle, and would therefore appear as DC … zero frequency contributions." Dannert 2022 states it verbatim: "If only rotationally symmetric sources … are considered, the detected signal does not depend on the rotation angle of the array." main.tex:317 instead cites `lay2005imaging` (the *imaging properties* paper), which I could not find to support the statement; `lay2004systematic` is in the bibliography but not cited here. *Fix:* cite Lay 2004 §4.A and Dannert 2022 §2.2.3 at both main.tex:317 and main.tex:605.

**M11 — The stellar scaffold has no source at all.**
main.tex:275 asserts "a common scaffold of 4505 nearby stars … out to roughly 50 pc" with no citation. I verified both numbers from the input files (4505 unique `nstar`, max distance 50.00 pc), so the statement is *true* — but it is not the LIFE VI sample, which is explicitly d < 20 pc (LIFE VI §2.1, LIFE I abstract). Since the η⊕ values in Table 2.2 are LIFE VI's, "averaged over our input catalog", the occurrence normalisation and the stellar sample come from different catalogs. *Fix:* identify and cite the stellar catalog, and add one sentence noting that the quoted η⊕ were averaged over LIFE VI's 20 pc sample.

### Minor

**m1 —** main.tex:807 and Table 5.2 attribute the x²/8 ratio to `\ref{eq: leakage small star}`, which resolves to Eq. 4.4 (⟨T₄⟩ alone). The ratio needs Eqs. 4.3 and 4.4 together; it is derived properly in Appendix A.2 but the main-text cross-reference is imprecise.

**m2 —** Experiment-1's three eligibility filters are not independent: the `habitable` flag already enforces 0.5 ≤ R_p ≤ 1.5 (`data.py:375–379`), so the radius cut in Table 2.1 is redundant with the HZ flag. Harmless, but the thesis presents them as three conditions.

**m3 —** The planet self-noise coefficient n_i = √⟨T₄²⟩ is an RMS where a photon rate warrants a mean ⟨T₄⟩. Inherited from LIFEsim (`transmission.py:223`), so not an error introduced here, but Table 2.4 labels both s_i and n_i as "RMS coefficients" without noting that only s_i is a matched-modulation amplitude and n_i is a variance weight.

**m4 —** The baseline prescription constant 0.589645 (`ams.py:115–117`) is derived for a second-order double Bracewell and is retained at order four. Disclosed via Table 3.1's "Preserved between orders", but worth one explicit sentence in §5.6, since it means the order-four configuration is not baseline-optimal.

**m5 —** Three of the four `known_retention_limits` in `run_matrix_2026-07-24.yaml` are disclosed only in Appendix B, not in §6.4's ranked limitations table. Consider promoting "raw grids and scheduler logs unavailable" and "no environment lock" into Table 6.1.

**m6 —** The 26.7 % figure in Fig. 5.6's caption (main.tex:799) cannot be verified from the retained products; it is stated without derivation.

**m7 —** main.tex:807's "Direct positive quadrature agrees with the analytic order-four response over the complete catalog range" gives no tolerance and no sample size; every other validation statement in the thesis does.

---

## Citation audit table

| Claim location | Reference | Supported? | Note |
|---|---|---|---|
| main.tex:256 — detection SNR 7 | Kammerer 2022 (LIFE VI) | **Yes** | Verbatim: "a conservatively high signal-to-noise ratio (S/N) of 7 for detection". |
| main.tex:266 — SNR 44.1 = integrated equivalent of S/N 10 at 11.2 μm, R = 50 | Dannert 2025 thesis | **Yes** | Verbatim: "S/N₁₁.₂ μm = 10 for R = 50 … equivalent integrated S/N = 44.1". |
| main.tex:275 — P-Pop draws Kepler-constrained occurrence/orbits | Kammerer & Quanz 2018 | **Yes** | Correct paper for P-Pop. |
| main.tex:275 — 4505-star scaffold to ~50 pc | *(none)* | **Uncited** | Numbers verified true from the input files; but LIFE VI/LIFE I use d < 20 pc, so this is a different stellar sample with no source. |
| main.tex:277 — hab2min/hab2max extrapolation beyond 500 d | Bryson 2021 + LIFE VI | **Yes** | LIFE VI §2.2 describes low/high-bound completeness extrapolation beyond 500 d exactly as summarised. |
| main.tex:285–286 — η⊕ 0.19⁺⁰·¹⁹₋₀.₁₀ / 0.34⁺⁰·³⁸₋₀.₁₉ | Bryson 2021 + LIFE VI | **Yes** | LIFE VI Table 1, EEC row, Sun-like columns, digit for digit. Caveat: averaged over LIFE VI's 20 pc catalog, not this 50 pc one. |
| main.tex:304 — EEC radius definition 0.8a⁻⁰·⁵ ≤ R_p ≤ 1.4 | LIFE VI | **Yes** | LIFE VI Table 1, EEC row (0.8⁽ᶜ⁾–1.4 R⊕). |
| main.tex:313 — b sets null envelope, rb sets fringes, r = 6 | Dannert 2022 (LIFE II) | **Yes** | Standard LIFE II notation. |
| main.tex:317 — symmetric backgrounds stay constant under rotation | Lay 2005 + Dannert 2022 | **Partially** | Dannert 2022 §2.2.3 supports it verbatim. Lay **2005** is the imaging paper; the verbatim statement is in Lay **2004** §4.A, which is in the bibliography but not cited here. Wrong Lay paper. |
| main.tex:388 — SNR convention follows LIFE II | Dannert 2022 | **Yes** | LIFE II Eqs. 20–21 match, including √Σ SNR². |
| main.tex:388, 409 — systematics outside this model | Lay 2004 + Dannert 2025 | **Yes** | Correct use of Lay 2004. |
| main.tex:393 — exozodi model follows Kennedy et al. 2015 | Kennedy 2015 + Dannert 2022 | **Yes** | Code implements Kennedy Eqs. 2–3 exactly (T = 278.3 L^0.25 r^−0.5, α = 0.34, Σ_m,0 = 7.12e−8, r_in = 0.034√L). But the profile is never stated in the thesis, including in Appendix A.3 which claims to make the calculation inspectable. |
| main.tex:584, 597, 926, 942 — Bessel identities | NIST DLMF | **Yes** | DLMF 10.9.1, 10.6.6a, 10.2.2 are the right identities; all three derivations re-checked and correct. |
| main.tex:605 — circular symmetry ⇒ rotation-angle independence | *(none)* | **Uncited** | Load-bearing conceptual claim; verbatim support exists in Lay 2004 §4.A and Dannert 2022 §2.2.3, and the internal brief records that this was checked. |
| main.tex:619 — 10 h slew is the inherited baseline | Dannert 2025 | **Yes** | "By assuming a slew time of 10 h". |
| main.tex:619 — LIFE working FoR reference is 90°, K-mag limit ~8 | *(none)* | **Uncited** | Stated as "the working LIFE field-of-regard reference" and "current project estimates"; no source given for either. |
| main.tex:860 — inclined/asymmetric disks create rotation-dependent structure | *(none)* | **Uncited** | Lay 2004 §4.A states it directly (elliptical exozodi ⇒ even-harmonic modulation); the internal brief cites it; the thesis does not. |
| main.tex:206 — reference studies do not provide an aggregate random-noise treatment | Quanz 2022, Dannert 2022, Dannert 2025 | **No** | Dannert 2025 §3.4.2 defines σ_ph,inst as an aggregate of "all additional photon noise sources" and Eq. 3.22 as a fundamental-noise-limited criterion; Ch. 5 studies its yield impact. The *iso-mission-time inversion* is new; the aggregate term is not. |
| §3.2 / §6.5 — fourth-order null, "realizable higher-order combiner" | *(none)* | **Uncited** | No nulling-architecture literature cited anywhere; Guyon et al. 2013 and Laugier et al. 2020 are in the candidate's literature folder and unused. |
| §2.2 — habitable-zone flag | *(none)* | **Uncited** | Kaltenegger+2017 'MS' model is what runs (`habitable.py`, `options.py:198`); never named or cited. |
| §2.5 / Appendix A.4 — local-zodiacal surface brightness | *(none)* | **Uncited** | `darwinsim` model; the source code itself carries `# TODO Find model after which this is calculated and reference` (`pn_localzodi.py:73`). |

---

## Concrete actionable edits

Ordered by impact.

1. **main.tex:582, 619, 876** — remove or evidence "approved". Either add to Appendix B.2 a dated record of the supervisor decision adopting the analytic background model and the 4/π local-zodi correction (and update `ANALYTIC_NOISE_REWRITE.md:3`), or replace all three occurrences with "the analytic background model adopted in this work". Do not leave an unevidenced approval adjective attached to the change that moves every headline number.

2. **Table 5.1 (main.tex:679–698) and abstract (main.tex:190)** — add a bracket column. For each row report the final [lower, upper] amplitude bracket and the stopping reason (both already printed by `locate_mission_cutoff`); quote the abstract's numbers as intervals. If the brackets cannot be recovered, re-run the eight inversions — each is one TSE call — rather than shipping bare two-significant-figure numbers that the thesis's own main.tex:624 says are unsupported.

3. **§6.1, after main.tex:836** — add a paragraph relating N_I to Dannert 2025 §3.4.2 (σ_ph,inst) and Eq. 3.22, and to the Lay-2004 perturbation levels tabulated there (0.1 % amplitude, 0.001 rad phase, 1 cm collector position rms at 10 μm). State at one wavelength what fraction of the astrophysical background 140 and 650 ph s⁻¹ μm⁻¹ represent. Without this the reader cannot tell whether the answer is good or bad news.

4. **main.tex:733** — replace "amplitudes below the reported value satisfy the corresponding mission-time target" with a statement of what the search actually guarantees: the reported value is the last evaluated point; only amplitudes below the final admissible bracket endpoint have been verified. Report that endpoint.

5. **Table 5.1 caption / §5.2, after main.tex:733** — add the integral-normalised comparison the thesis currently declines. A linear ramp with endpoint A has half the band-integrated allowance of a flat budget of amplitude A, so the neutral endpoint is 2×flat. Every row then supports the central claim: at order 2, short-weighted beats 2×flat in 4/4 rows (300 vs 280; 1300 vs 1220; 200 vs 130; 970 vs 920) while long-weighted does not (except Hab2Min 7.5); at order 4, long-weighted beats 2×flat in 4/4 rows (1470 vs 1300; 2240 vs 1880; 1260 vs 1180; 1860 vs 1580) and short-weighted never does. This strengthens the thesis's headline result at zero computational cost and removes the "unequal spectral integrals" objection it currently concedes.

6. **main.tex:624** — correct "0 to 50,000" to the value actually used in production (`runner.py:113`: `upper_start=5000`), and state that 50,000 is only the library default.

7. **Table 2.5 (main.tex:395–411) and §2.5** — add an "Excluded (modelled but disconnected)" row covering instrument thermal emission and detector dark current, noting that the inherited `pn_thermal.py` / `en_darkcurrent.py` modules were not connected for these runs and that those terms are therefore inside N_I, not inside B_i. Add one sentence stating that ecliptic longitude is frozen at 3π/4 for all targets.

8. **Appendix A.3 (main.tex:957–965)** — write down the exozodiacal profile actually used: T(r) = 278.3 L^0.25 r^−0.5 K, Σ(r) = Σ_m,0 (r/r₀)^−0.34 with Σ_m,0 = 7.12 × 10⁻⁸, r₀ = √L AU, r_in = 0.034√L AU, evaluated on a log-spaced radial grid. Cite Kennedy 2015 Eqs. 2–3. Also name and cite the habitable-zone model (Kaltenegger+2017) in §2.2.

9. **Table 3.2 (main.tex:540–557)** — add two rows: exozodi end-to-end versus image sampling at orders 2/4/6 (with the ~10 % worst case and its old-grid-aliasing interpretation), and the full-catalog SNR change produced by the local-zodi correction (~10.9 % median). Then state in §4.2 that the correction moves catalog-wide SNRs by that amount — currently the thesis reports the 27 % rate change but never its SNR consequence.

10. **Appendix B.3 (main.tex:1023–1026) and Table 6.1 row 4** — report the number of universes actually entering the percentile in each production run. If it is not 100, recompute the rank interval; if it is 100, say so and the caveat at main.tex:535 can be dropped.

11. **main.tex:317 and 605** — cite Lay 2004 §4.A and Dannert 2022 §2.2.3 for the rotation-angle-independence statement; cite Lay 2004 §4.A again at Table 6.1 row 5 for the inclined-disk even-harmonic argument. Reserve `lay2005imaging` for imaging claims.

12. **main.tex:611** — state both the analytic limit (4/π = 1.2732) and the numerically measured old-vs-new ratio (1.268), and say which is quoted; note that the π/4 identity is exact only in the uniform-response limit.

13. **main.tex:619** — justify the mission-time targets 5.5/6.0 and 7.5/8.0 yr against a stated LIFE baseline, or say explicitly that they are arbitrary comparison points chosen to bracket the feasible region.

14. **§2.4 or §3.3.2** — define "mission time" as detection + orbit + characterization integration plus slew, exclusive of the configured 0.8 observing efficiency, and state the wall-clock conversion.

15. **§3.2 and §6.5** — cite at least Guyon et al. 2013 and Laugier et al. 2020 when introducing the sin^n proxy and when calling for a realizable higher-order combiner. A thesis whose central novelty is a fourth-order null should not cite zero papers on nulling architectures.

---

## Suggested block grade

### **4.75**

**Justification.** The execution is genuinely strong where it can be checked. I independently reproduced Table 2.3 to every digit, the median leakage ratios at 10 and 18.5 μm, the min-x bound of 0.005, the binomial coverage 0.9557, the 317-year illustration, the far-field ¼ → 3/16, and every algebraic step of Appendix A — including the non-obvious point that the imaging factor contributes exactly one half, not approximately. The reference-plane convention, the SNR chain, the scheduler and the completion criterion all match the production code line for line. That is careful, competent, honest work, and it earns "+" on aims, method appropriateness, care, and outlook.

The block is nonetheless held down by three things that an examiner will press in the defense. First, the central results carry no uncertainty of any kind while being printed to a precision the thesis itself says is unsupported, and the sample size of the sampled percentile is unknown. Second, the headline number is never placed next to any external reference point, even though the direct predecessor — cited six times — contains the equivalent quantity, and the thesis's novelty claim overstates the gap it fills. Third, the physics change that moves every number is labelled "approved" three times with no record, and the only internal document on the matter says the opposite. Alongside these, four load-bearing model ingredients (exozodi profile, HZ model, thermal/dark-current exclusion, frozen ecliptic longitude) are undocumented, and the methods text disagrees with the production script on the search bracket.

Nine tags: **o, +, o, +, +, −, o, −, +**. No sub-question is excellent; two are weak; none is unsatisfactory. That is "good with certain flaws" pulled down by a weak statistical and contextual treatment — 4.75, not 5.0.

**What would raise it half a grade (to ~5.25).** Four edits, all cheap:
1. Put a defensible interval on every number in Table 5.1 and in the abstract (actionable edit 2), and report the number of universes entering the percentile (edit 10).
2. Add one paragraph comparing N_I to Dannert 2025 §3.4.2/Eq. 3.22 and to the Lay-2004 perturbation levels, plus one number saying what fraction of the astrophysical background the allowance represents (edit 3).
3. Resolve the "approved" claim, in either direction (edit 1).
4. Add the integral-normalised ramp comparison (edit 5) — it costs nothing and converts the thesis's central result from an endpoint comparison it disclaims into a normalised comparison it can defend.

Doing all four, plus documenting the four missing model ingredients (edits 7–8), would put this block at 5.5.
