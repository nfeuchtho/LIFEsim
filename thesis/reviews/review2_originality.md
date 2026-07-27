# Block: Independent scientific thinking / originality (revised draft)

External examiner report. Field: mid-IR nulling interferometry / LIFE.
Primary document: `thesis/main.tex` (1281 lines), read in full.
Supporting material verified: `ANALYTIC_NOISE_REWRITE.md`, `lifesim/ams/`,
`lifesim/util/transmission_analytic.py`, pre-rewrite `pn_localzodi.py` /
`transmission.py` at commit `2fd5142`, `thesis/reproducibility/*.tsv`, git history
on branch `ams`, and the primary literature (Guyon 2013, Lay 2005, Dannert PhD
thesis, Norbruis 2023).

---

## Verdict per sub-question

### 1. How significant is the independent contribution of the student to the outcome of the thesis? — **+**

The code is unambiguously the student's own. `git log` on branch `ams` shows every
commit from `6e7b6f1` onward authored by `nfeuchtho@ethz.ch`; the preceding history
is Dannert's and other collaborators'. `git diff --stat 6e7b6f1 57d00db -- lifesim/`
gives 3516 insertions across `lifesim/ams/core/ams.py` (833 lines),
`trade_space_explorer.py` (731), `ablation_throughput.py` (421),
`util/transmission_analytic.py` (133), rewrites of `pn_star.py` / `pn_localzodi.py` /
`pn_exozodi.py`, and five validation scripts. This is not a parameter study on
somebody else's tool.

Within the AMS the inherited/added boundary is real and correctly drawn in the text.
The detection campaign is inherited (`optimizer.ahgs()`, `ams.py:395`), and the thesis
says so (main.tex:541, main.tex:548, "the inherited strict completion checks"). Everything
downstream — the per-universe time sheet, the follow-up/characterization charging model,
and the 90th-percentile return (`ams.py:415-486`) — is the student's, as is the
`ErrorBudget` modifier framework (`error_budget.py`, multiplicative + additive per
channel with cache invalidation) and the SNR-flow/filter-flow separation that makes
repeated inversion affordable. Section 6.2 (main.tex:955) identifies exactly that
separation as the methodological enabler, which is the correct self-assessment.

Two things reduce the tag from `++`. First, the TSE's scientific core is 130 lines
(`trade_space_explorer.py:61-194`): a bracketed root-find with an exponential secant
proposal. It is competent and correctly instrumented (bracket invariant maintained,
`ams.py`-side caching exploited), but it is a standard numerical driver, and the
remaining ~600 lines of `trade_space_explorer.py` are plotting. Second, main.tex:524
("The only remaining step is to use LIFEsim to distribute the available observation
time") actually *under*-attributes: the distribution phase is the student's code, not
LIFEsim's. Conservative, but it costs the reader a correct picture of the contribution.

### 2. Does the thesis show scientific originality? — **o**

The central reframing is real: fixing the science outcome (Experiment 1 within a
stated mission time) and inverting for the tolerated aggregate random-noise amplitude,
resolved in wavelength (main.tex:206, main.tex:227). The novelty language is
disciplined — the claims are confined to three items at main.tex:231 and the aggregate
noise term is explicitly disclaimed as inherited (main.tex:227).

But the positioning against the direct predecessor is not accurate, and this is the
weakest point in the whole block. main.tex:227 asserts: "Where the predecessor
propagates an assumed instrumental noise level forward to a yield, this thesis fixes
the science outcome ... and inverts for the largest random-noise amplitude compatible
with it." Dannert's PhD thesis also inverts. Its Chapter 5 is titled *"Outlook —
Requirements for LIFE"* and its own summary states: "**By inverting the forward yield
model, we identify the Pareto-front in sensitivity-contrast space** under LIFE's
scientific objectives and subsequently provide first indications for resulting key
mission requirements." Dannert further writes that "the subset of least demanding
'successful' parameters is called the Pareto-Front, and any point on this front can be
identified as mission requirements. This derivation of mission requirements is the core
goal of the LIFE instrument science working group." His Tables 3.4 and 3.5 already
report *maximum allowed* perturbation rms and *asymptotic upper limits* on detector
thermal background and dark current. So "inversion for a tolerated instrumental noise
level" is not the delta. The genuine delta is narrower and defensible — the criterion
is completion *time* for a catalog programme rather than a fundamental-noise-limited
ratio at a single Earth-twin at 10 pc; the allowance is resolved in wavelength across
budget-shape families; and it runs over the full P-Pop ensemble with a percentile
scheduler. main.tex:206 ("What the reference studies do not provide is its inversion")
is, as written, incorrect.

A second gap: `laugier2020kernel` appears exactly once in main.tex — at line 1254, the
bibliography entry itself. It is never cited in the body. Laugier, Cvetojević &
Martinache (2020), kernel nullers for an arbitrary number of apertures, is precisely
the literature that constructs realizable higher-order nulls, i.e. the literature the
$\sin^n$ proxy is standing in for. An uncited entry in exactly the area where the
thesis's central architectural device is weakest reads as a scholarship gap, not an
oversight.

### 3. Are there new ideas or established ideas used in a new way? — **+**

This is the block's strongest sub-question, and the answer is genuinely positive.

- The even-order azimuthal reduction (main.tex:608-615, implemented in
  `transmission_analytic.py:60-105`) is correct and verified: power-reduction of
  $\sin^{2p}$ into a cosine series, each harmonic collapsing to $J_0(jkr)$ via the
  Jacobi–Anger/NIST integral, then $J_0(jkR)\to 2J_1(jkR)/(jkR)$ under disk averaging.
  The observation that odd orders average identically to zero under a full rotation
  (`transmission_analytic.py:5-19`) is a clean, citable explanation of why nulling
  order is always even, and it is enforced as a `ValueError` rather than left as a
  comment.
- The same substitution trick applied twice at different stages — $u=1/\lambda$ to
  de-chirp the spectral integrand (main.tex:1084-1090, `gauss_legendre_wavenumber`)
  after the spatial grid removal made extra nodes affordable — is the kind of
  transferable idea an examiner wants to see. The dependency is real: the technical
  brief records that the wavelength quadrature was rejected as too expensive *before*
  the spatial rewrite and reopened *after* it.
- Reusing the general azimuthal average *inside* a 1-D radial quadrature for tapered
  and extended (Kennedy) profiles is the part that genuinely does not follow from the
  second-order literature, and main.tex:1058 says so with the right calibration.
- The methodological caution at main.tex:960 — a requirement defined where the
  completion curve is steep inherits an amplified version of any background error, so
  a background correction *invalidates* rather than perturbs it — is a real insight,
  correctly generalized beyond this study.

Honest limits. main.tex:1058 also claims the general even-order extension does not
follow from the second-order case. Lay (2005) Eq. (17), inherited from Lay (2004)
Eqs. (10)–(11), already gives uniform-disk stellar leakage for an *arbitrary* array as
a double sum $\sum_j\sum_k 2F_*A_jA_k\cos\phi_{jk}\,J_1(2\pi B_{jk}\theta_*/\lambda)/
(2\pi B_{jk}\theta_*/\lambda)$, with the small-star expansion $[1-0.125(2\pi B\theta_*/
\lambda)^2]$ — i.e. the $2J_1(x)/x$ structure and the $x^2/8$ scaling are both already
there, with null order entering through the $\cos\phi_{jk}$ coefficients. The student's
defence is that a $\sin^4$ envelope is not the pairwise response of any physical
four-aperture combiner, so Lay's sum does not directly cover the proxy. That defence
holds, but the thesis does not make it, and the claim as printed will draw fire.

### 4. Are the results of the thesis novel and important? — **o**

Three results, of unequal standing.

**(a) The throughput-penalized fourth-order result — verified, and the best-executed
new result in the draft.** `thesis/reproducibility/throughput_sweep.tsv` reproduces
Table 5.6 (main.tex:901-904) digit for digit (5.318721/4.467216/7.409976/6.041650 at
$\tau=0.15$; 9.712240/7.653264/13.268285/10.787400 at $\tau=0.075$).
`ablation_throughput.tsv` shows endpoint `0` at all four targets in the penalized arm,
for both catalogs and all three families, with the zero-budget times 7.653/10.787 yr
exceeding every target — so main.tex:889 and main.tex:913 are exactly supported. The
scaling analysis (time grows as $1.71$–$1.83\times$ under halved efficiency, not
$2\times$, implying a 17–29% throughput-independent slew fraction, main.tex:911) is a
nice piece of independent reasoning that falls straight out of the sweep.

Two caveats an examiner will press. The result is arithmetically almost immediate once
$\eta\to\eta/2$ is granted — it is a one-parameter ablation, not a discovery; its value
is in reversing the engineering reading (main.tex:950), which the thesis states well.
More seriously, the factor of two rests on a slightly garbled reading of Guyon.
main.tex:503 says "for a fixed four-aperture array, a second-order Bracewell
arrangement delivers 50% throughput using two of four outputs, whereas the fourth-order
Angel Cross design uses only one of four, or 25%." Guyon (2013, §1) actually writes:
"in the 4-aperture Angel Cross design, 25% of the light is used ... while a simpler
**2-aperture** Bracewell offers 50% throughput." The four-aperture 50% figure comes from
a *different* sentence (the Darwin study: "a 4-aperture geometry in a circle, with a
2nd order null ... with a 50% efficiency"). The net factor of two survives, and is in
fact the right comparison for LIFE — but the attribution merges two sentences. Worse,
Guyon's own Prediction 3 states that effective throughput *increases* with aperture
count, giving 60% for a $\theta^4$ null with five apertures. The thesis notes the
factor is "taken from one specific pair of architectures rather than from a general
law" (main.tex:915), which is honest, but stops one sentence short of the counter-
direction its own source supplies — and never cites Laugier 2020, where the general
construction lives.

**(b) The spectral reversal surviving the penalty — verified, but the test proves
slightly less than the framing implies.** All six penalized-feasible rows in
`ablation_throughput.tsv` are reproduced correctly in Table 5.7 (main.tex:924-929), and
I re-derived the integral-neutral comparison independently: long-weighted exceeds
$2\times$flat in all six rows (142.6 vs 76.8; 411.4 vs 268.1; 837.9 vs 555.6; 154.2 vs
97.1; 377.7 vs 218.0; 626.3 vs 369.2), and short-weighted clears it only at Hab2Max
9.0 yr (641.2 vs 555.6) — exactly as main.tex:936 states. The reporting is precise.
The framing at main.tex:915 presents this as settling "whether the spectral reversal is
itself an artifact of the unnormalized throughput." But $\eta$ is a wavelength-flat
scalar at the pre-efficiency plane, so it cannot by itself reorder wavelength-weighted
families; only the nonlinear scheduling could. The test is therefore a useful empirical
confirmation of a mild risk, not the elimination of a serious one. The informative
missing ablation is the one the thesis itself names and does not run: separating
leakage suppression from the simultaneous $1/4\to3/16$ envelope change (main.tex:863).
That admission is correctly placed and correctly worded.

**(c) The local-zodiacal correction — a genuinely important finding, carrying a
demonstrably false exactness claim.** The finding itself is real and well-evidenced.
I read the pre-rewrite code at commit `2fd5142`: `pn_localzodi.py` computes
`lz_leak = (ap*t_map).sum()/ap.sum() * lz_flux * area` with
`lz_flux = lz_flux_sr * pi*image_angle**2`, and under the *default*
`fov_taper='gaussian'` sets `ap = np.ones_like(radius_map)` — the full square grid —
while the `'none'` branch masks `ap` to a circular disk. The internal-inconsistency
argument at main.tex:628 is therefore exactly right, and this is a defect the LIFE
collaboration should want to know about. The propagation analysis is also right and
well done: `localzodi_defect_impact.tsv` reproduces Table 4.1 exactly, and the
disproportion (27.3% background error → allowance factors 1.5–11) is the sharpest
methodological point in the thesis.

**But main.tex:632 is wrong.** It claims: "The factor is exact rather than approximate,
and does not depend on the transmission map ... A direct measurement against the old
grid returns 1.268, and the residual 0.4% is that grid's own discretization error
rather than a departure from the identity." The supporting argument — "since a mean and
an area must refer to the same domain, the two differ by the ratio of the areas alone,
and any variation of the transmission across the field cancels between numerator and
denominator" — is the error. The two means are over *different* domains (old = mean over
the square; new = mean over the inscribed circle), so nothing cancels. The exact ratio is
$(4/\pi)\cdot\left[\int_{\rm circ}T\,\tau\right]/\left[\int_{\rm sq}T\,\tau\right]$, and
the Gaussian taper does **not** vanish outside the inscribed circle: `instrument.py:104`
sets `image_angle = hfov*(4/pi)*sqrt(-log(fov_threshold))` with
`fov_threshold = 0.01`, so the taper is exactly 0.01 at $r=R$ and $10^{-4}$ at the
corners, over an extra area of $(4-\pi)R^2$.

I ran the resolution sweep the thesis did not. Building `tm3` with the taper exactly as
`transmission.py` does, and comparing against `radial_average_tm` (n_r = 20000) at four
$(\lambda,b)$ points spanning the production range:

| image_size | ratio (new/old) | deviation from $4/\pi$ |
|---|---|---|
| 100 | 1.2915 | +1.43% |
| 400 | 1.2725 | −0.06% |
| 1600 | 1.2678 | −0.43% |
| 4000 | 1.2668 | −0.50% |

The ratio converges *away* from $4/\pi=1.27324$, monotonically, toward $\approx1.2668$.
The pure-taper closed form confirms the limit analytically:
$\langle\tau\rangle_{\rm circ}/\langle\tau\rangle_{\rm sq} = \frac{(1-e^{-c})/c}{(\pi/4c)\,{\rm erf}^2(\sqrt c)}
= 1.2665$ with $c=-\ln 0.01$. So the "measured 1.268" quoted at main.tex:632 is, to its
own precision, the *converged and correct* value — and $4/\pi$ is the approximation.
The thesis has the relationship exactly backwards, and the claim is repeated in the
abstract (main.tex:188, "correcting an exact $4/\pi$ error").

Consequences, stated fairly. **No reported number changes**: production runs use the
circle-domain analytic formula, which is the correct one. The knock-on is confined to
two sentences that are now unsupported — main.tex:636 ("Because the multiplicative
factor is exact, restoring it reproduces the pre-correction path identically") and
main.tex:652 ("obtained by restoring the exact $\pi/4$ factor, so the two configurations
differ only in the defect"). `ablation_throughput.py:200-201` applies
`PI_OVER_4 = 0.785398` as a uniform multiplicative scale, whereas the true old-path
ratio is $\approx 1/1.2668 = 0.7894$; the pre-correction arm is therefore mis-modelled
by ~0.5%, which is negligible against results quoted as "factors of 1.5 to 11" but is
not "identical". This is a repairable text-and-caption fix, not a results problem —
but it is a claim of *exactness* made in the abstract and shown false by a calculation
the thesis's own code makes trivial to run.

One further calibration point on importance. The dramatic factor of 11 is partly
manufactured by the target-selection rule. main.tex:671 selects each catalog's primary
target as "the smallest half-year step at which a non-trivial positive allowance still
exists," which places Hab2Min order-two at a 7.5 yr target against a 7.41 yr zero-budget
time — a 0.09 yr margin. The amplification is largest precisely *because* the target was
chosen to sit at the feasibility edge. Both facts are stated in the thesis; they are
never connected, and connecting them would make the argument stronger, not weaker.

---

## Strongest evidence of originality

1. **The analytic grid-free reduction is real mathematics, correctly derived, correctly
   validated, and correctly bounded.** `transmission_analytic.py:60-133` implements the
   general even-order sum; the validation matrix (main.tex:563-571) reports the
   independent checks including the ones that *failed first* — the exozodi log-spacing
   defect found at up to 35% error and fixed (main.tex:570). Reporting a self-inflicted
   bug found by one's own convergence check is a mark of scientific seriousness, not a
   weakness.
2. **The local-zodiacal defect discovery**, and specifically the internal-inconsistency
   argument (tapered branch normalizes by the square, untapered branch by the circular
   mask — verified against `2fd5142:pn_localzodi.py`). This is the most citable single
   finding in the thesis and is of direct interest to the collaboration.
3. **The decision to charge the fourth-order proxy a cost the proxy does not model**
   (Section 5.7), and then to report that it reverses the thesis's own headline
   comparison (main.tex:950). Deliberately constructing the ablation most damaging to
   your own attractive result is exactly the independent scientific thinking this block
   is meant to reward.
4. **The "requirements at a feasibility boundary amplify background errors" caution**
   (main.tex:656, main.tex:960), correctly generalized past this study.
5. **Systematic under-claiming where under-claiming is right**: main.tex:578 states that
   the $4.2\times10^{-16}$ AMS-vs-Instrument agreement is "deliberately narrow" because
   both routes share modules — which is true and nearly tautological after the
   deduplication documented in the technical brief §10. A weaker candidate would have
   sold that number as validation.

---

## Weakest points / where an examiner will still push back

1. **The $4/\pi$ exactness claim is false** (main.tex:188, 632, 636, 652). Demonstrated
   above by resolution sweep and closed form. This is the one place where the thesis
   states something an informed reader can disprove in ten minutes with the thesis's
   own code. It is also self-inflicted: the correct statement ("$4/\pi$ to within 0.5%;
   the residual is the taper's leakage into the corners, not grid noise") is *more*
   impressive, because it shows the student understands the geometry rather than
   asserting it.
2. **The prior-work positioning against Dannert understates the predecessor**
   (main.tex:206, 227). Dannert Ch. 5 inverts the forward yield model to a Pareto front
   and calls requirement derivation "the core goal of the LIFE instrument science
   working group"; Tables 3.4/3.5 already give maximum allowed perturbations and
   asymptotic noise upper limits. The supervisor is the author of that thesis. This
   will be the first question asked.
3. **Laugier 2020 is in the bibliography and never cited** (main.tex:1254, sole
   occurrence). Kernel nullers for arbitrary aperture counts is the direct literature
   on realizable higher-order nulls, i.e. on the one device the thesis proxies. Guyon's
   own Prediction 3 (throughput *rises* with aperture count; 60% for a $\theta^4$ null
   with five apertures) also goes uncited, and it materially softens the headline
   negative conclusion.
4. **The Guyon 50%/25% attribution merges two separate sentences** (main.tex:503).
   Guyon's 50% in that sentence is a *two*-aperture Bracewell; the four-aperture 50%
   figure is the Darwin example elsewhere on the same page. The physics survives; the
   citation precision does not.
5. **The reversal-survives-the-penalty test is weaker than framed** (main.tex:915). A
   wavelength-flat efficiency cannot itself reorder wavelength-weighted families. The
   ablation that would matter — separating leakage suppression from the $1/4\to3/16$
   envelope change — is named but not run (main.tex:863).
6. **Internal numerical inconsistencies that erode confidence in the reported novelty.**
   main.tex:752 quotes the Hab2Max order-four flat allowance as **650** where Table 5.1
   (main.tex:739) says 640 and Table 5.4 (main.tex:1166) says 641.2. Table 4.1
   (main.tex:648-649) rounds the Hab2Min corrected allowances to **60** and **600**,
   while Table 5.1 (main.tex:742-743) gives **65** and **590** — from the identical
   underlying values 62.2 and 596.5. The thesis discusses the "65" rounding at
   main.tex:1149 but never reconciles Table 4.1.
7. **"Two earlier master's theses in the same programme"** (main.tex:229). Norbruis 2023
   is TU Delft, Faculty of Aerospace Engineering (verified from the title page);
   instructor J. Loicq. Only Binkert is ETH. The *content* description of Norbruis
   (LIFEsim-derived model, P-Pop, multi-objective Pareto over geometry/aperture/
   temperature) is accurate.
8. **The TSE is a driver, not a contribution.** `locate_mission_cutoff` is 130 lines of
   standard bracketed root-finding; the remainder of the file is plotting. The thesis
   names the TSE alongside the AMS in the abstract and introduction as though the two
   were comparable contributions. They are not.

---

## Concrete remaining edits

Ordered by grade impact.

1. **main.tex:632 (and abstract main.tex:188; captions main.tex:636, 652).** Replace the
   exactness claim. The defect is exactly "divide by the wrong area", but the *numerical*
   factor is not exactly $4/\pi$, because the numerator domain also changes and the
   Gaussian taper is 0.01 (not 0) at $r=R$. Correct text: the correction is $4/\pi$ to
   within 0.5%; the exact factor is $(4/\pi)\int_{\rm circ}T\tau / \int_{\rm sq}T\tau
   \approx 1.267$; the measured 1.268 is the converged value, not $4/\pi$ with grid
   noise. Add the resolution sweep (IS = 100/400/1600/4000 → 1.2915/1.2725/1.2678/1.2668)
   as one line or a footnote — it converges *away* from $4/\pi$, which is the point.
   Amend main.tex:636/652 to say the pre-correction arm reconstructs the defective path
   to ~0.5%, not "identically". Abstract: "an exact $4/\pi$ error" → "a $4/\pi$
   normalization error".
2. **main.tex:206 and main.tex:227.** Rewrite the Dannert delta. Acknowledge explicitly
   that Dannert Ch. 5 inverts the forward yield model to a Pareto front and that his
   Tables 3.4/3.5 already report maximum allowed perturbations and asymptotic noise
   limits. State the surviving delta precisely: completion *time* for a catalog
   programme rather than a fundamental-noise-limited ratio at a single Earth-twin;
   wavelength-resolved across budget-shape families; full P-Pop ensemble with a
   percentile scheduler. Delete "What the reference studies do not provide is its
   inversion" (main.tex:206).
3. **main.tex:503 and main.tex:915.** Fix the Guyon attribution — the 50% in the sentence
   being paraphrased is a two-aperture Bracewell; the four-aperture 50% is the Darwin
   example. Then add one sentence citing Guyon's Prediction 3 (effective throughput
   rises with aperture count; 60% for a $\theta^4$ null with five apertures) and
   `laugier2020kernel` as the general construction, and note that a fourth-order design
   with more than four apertures need not pay the factor of two. This *strengthens* the
   limitation paragraph at main.tex:915 and repairs the uncited-reference problem in one
   move.
4. **main.tex:752.** "from 650 to 940 at order four" → 640, to agree with Table 5.1 and
   Table 5.4. Separately, reconcile Table 4.1 (main.tex:648-649: 60, 600) with Table 5.1
   (main.tex:742-743: 65, 590) — pick one rounding convention for 62.2 and 596.5 and
   apply it in both tables, or cross-reference main.tex:1149 from Table 4.1's caption.
5. **main.tex:229.** "Two earlier master's theses in the same programme" → Norbruis is
   TU Delft (Aerospace Engineering), Binkert is ETH. One clause.
6. **main.tex:915.** Qualify the penalized-reversal test: state that $\eta$ is
   wavelength-flat at the pre-efficiency plane and therefore cannot by itself reorder
   wavelength-weighted families, so the test confirms that the nonlinear scheduling does
   not reorder them either. This converts an overstated claim into a precise one at no
   cost, and it pairs naturally with the honest gap already declared at main.tex:863.
7. **main.tex:656 / main.tex:671.** Connect the target-selection rule to the
   amplification factor: state that the extreme factor of 11 arises at Hab2Min order two
   because the selection rule places the target 0.09 yr above the zero-budget time, so
   the amplification is largest by construction where the target is nearest the
   feasibility edge. Two sentences; makes the methodological point sharper.
8. **main.tex:1058.** Pre-empt the Lay objection. Add half a sentence noting that Lay
   (2005) Eq. 17 already gives uniform-disk leakage for an arbitrary array as a pairwise
   $2J_1/x$ sum, and that the present extension is needed because the $\sin^n$ proxy is
   not the pairwise response of a physical combiner. This is the student's own defence;
   stating it costs nothing and closes an obvious line of attack.
9. **main.tex:231.** Consider adding the local-zodiacal correction to the list of three
   new items. It is currently the only major finding excluded from the thesis's own
   novelty list while featuring prominently in the abstract — an odd asymmetry that
   reads as either false modesty or inconsistency.
10. **main.tex:524.** "use LIFEsim to distribute the available observation time" —
    clarify that only the detection campaign (`optimizer.ahgs()`) is inherited, and that
    the follow-up charging, per-universe time sheet and percentile are AMS code. Correct
    under-attribution costs the student credit in exactly this grading block.

---

## Suggested block grade

### **5.0** (good; certain flaws)

**Justification.** The independent contribution is not in doubt: ~3500 lines of
student-authored code verified by git, a correct closed-form derivation with a
published validation matrix that includes a self-found and self-fixed defect, discovery
of a genuine latent bug in inherited LIFEsim code, and a self-designed ablation that
deliberately undercuts the thesis's own attractive result. The "established ideas used
in a new way" dimension is clearly positive — the de-chirping substitution reused at
two independent integration stages, the general even-order Bessel reduction reused
inside radial quadrature for tapered sources, and the feasibility-boundary
amplification insight are all real. Every headline number I could check against
`thesis/reproducibility/` reproduces exactly, and my independent re-derivation of the
integral-neutral comparison in Table 5.7 confirms all six rows.

What holds it at 5.0 rather than 5.5 is that both remaining defects sit *inside* the
originality claims themselves. The $4/\pi$ exactness claim is asserted in the abstract
and disproved by a ten-minute calculation with the thesis's own code — and the argument
given for it (means over different domains cancelling) is visibly wrong on the page.
The prior-work section, which is otherwise the most improved part of the draft,
mispositions the one predecessor the examining committee knows best, by claiming the
inversion as new when Dannert Ch. 5 performs an inversion and states requirement
derivation as its explicit goal. Add an uncited Laugier 2020 in exactly the area where
the $\sin^n$ proxy is weakest, a merged Guyon attribution carrying the headline negative
result, and three internal numerical inconsistencies between tables, and the picture is
"good work with certain flaws", not "very good with minor flaws".

Below 5.0 is not defensible: the work is manifestly the student's, the mathematics is
correct, the ablations are real and reproducible, and the self-criticism (Table 6.1
ranked limitations, main.tex:863, main.tex:578, main.tex:1149) is of a standard well
above the median MSc thesis.

### What would raise it half a grade to 5.5

Edits 1, 2 and 3, in that order — nothing else is required.

- Edit 1 converts a false claim into a demonstrated one and, done properly (with the
  resolution sweep), turns the weakest paragraph in the thesis into evidence of exactly
  the geometric understanding the block is grading.
- Edit 2 makes the novelty claim survive contact with the supervisor's own thesis. A
  narrower, accurate delta scores higher in this block than a broad, inaccurate one.
- Edit 3 closes the uncited-reference gap and simultaneously strengthens the limitation
  paragraph on the headline negative result, by letting Guyon's own aperture-count
  argument bound the conclusion.

Edits 4–5 are cheap accuracy repairs that should be made regardless. Edits 6–10 are
polish that would consolidate 5.5 but will not by themselves move the grade. Reaching
6.0 in this block would require the missing ablation itself — separating leakage
suppression from the $1/4\to3/16$ envelope change (main.tex:863) — or propagating the
local-zodiacal correction into a published LIFE yield number, which main.tex:634
explicitly and reasonably defers.
