# Thesis revision checklist

Source: three independent examiner-style reviews against the official ETH grading
sheet, 2026-07-27. Full reports in the session scratchpad:
`review_originality.md`, `review_scientific_competence.md`, `review_presentation.md`.

Reviewer grades: originality **5.0**, scientific competence **4.75**,
presentation **4.75**. Methodological competence and work process not assessed
(cannot be judged from the thesis alone).

**Deadlines**
- Diff draft to supervisor: **2026-07-28, night**
- Final thesis: **~2026-08-10**

**Rule for the diff:** include items where his feedback changes what you do next,
plus anything cheap. Everything else waits.

---

## Tier 0 — tonight, before anything else

- [ ] Commit the dirty `lifesim/ams/` tree (branch `ams`). New results must be
      attributable; `run_matrix_2026-07-24.yaml` already records that the previous
      raw grids were lost. Retain them this time.
- [ ] Launch the throughput-normalized order-4 ablation. ~2 h from prior TSE run
      timestamps; runs unattended overnight and may land in tomorrow's diff.

---

## Tier S — must be in the diff (~6 h)

- [ ] **S1. Related-work / positioning subsection** after `main.tex:224`, plus a
      §6.1 paragraph placing `N_I` next to Dannert 2025 §3.4.2 `sigma_ph,inst`
      (Eq. 3.22) and the Lay 2004 perturbation levels.
      *Why #1:* the only item that moves all three blocks, and all three reviewers
      converged on it independently. No related-work section exists anywhere in the
      thesis. This is also where the size of the project becomes visible — see
      "Making the work visible" below. **(2 h)**

- [ ] **S2. M7 — mission time is not wall-clock time.** Define it explicitly in
      §2.4 or §3.3.2 and state the conversion. With `opt_limit: experiments` the
      0.8 observing efficiency is inert (`ahgs.py:191,222`), so reported time is
      integration + slew only; a stated 5.5 yr is ~6.9 yr calendar at the
      configured efficiency. "on-source" and "wall-clock" appear nowhere.
      *Why early:* changes how every headline number reads. Better challenged
      tomorrow than in week two. **(30 m)**

- [ ] **S3. M8 — complete the validation matrix** (Table 3.2, `main.tex:540-557`).
      Add the exozodi order-4/6 brute-grid deviations (~10 % on some stars,
      4.5-5.4 % at order 2) and the exozodi log-spacing defect (up to 35 % before
      fix), with the existing attribution to old-grid aliasing near the Kennedy
      `r_in` cusp. Report the 10.9 % median full-catalog SNR shift in §4.2 — it is
      the single most informative number about the local-zodi correction and is
      currently absent.
      *Why:* the matrix presently reports only the checks that went well, while the
      supervisor holds the internal brief that records the rest. **(1 h)**

- [ ] **S4. C2 — uncertainty on the headline numbers.** Add the final
      `[lower, upper]` bracket and the stopping reason per row of Table 5.1, and
      quote intervals rather than point estimates in the abstract
      (`main.tex:190`). The eps = 0.05 yr stop rule
      (`trade_space_explorer.py:127`) maps via the thesis's own slope to roughly
      +/- 40 ph s^-1 um^-1 on a reported value of 65; two significant figures imply
      a precision `main.tex:624` explicitly disclaims.
      *Why:* kills the SQ6 `-` outright, and the data already exists. **(2 h)**

- [ ] **S5. C1 — document the approval.** The supervisor has approved the analytic
      rewrite. Record the provenance in Appendix B.2 rather than softening the
      claim at `main.tex:582, 619, 876`, and fix the stale status line in
      `ANALYTIC_NOISE_REWRITE.md:3` ("NOT yet supervisor-approved") plus its §8
      reference to `.bak` files that are no longer in the tree.
      *Why:* two documents currently contradict each other in front of the person
      who signed it. **(20 m)**

---

## Tier A — cheap, high yield, include if the day holds (~5 h)

- [ ] **A1. Formal compliance sweep.** Declaration of Originality (ETH requirement,
      currently absent); reference the 5 orphaned floats (Tables 2.2, 2.3, 2.5,
      5.2 and Fig. 4.1); point to Appendix B from the body; add References to the
      TOC; fix the wrong cross-reference at `main.tex:807` (cites Eq. 4.4 for a
      ratio needing Eqs. 4.3 and 4.4 together); expand "MT" on first use.
      *Why:* clears the only `-` in the presentation block and requires no
      thinking. **(1.5 h)**

- [ ] **A2. Citation batch.**
      - M10: cite Lay 2004 §4.A and Dannert 2022 §2.2.3 at `main.tex:317` and
        `main.tex:605` (both state rotation-angle independence verbatim);
        `main.tex:317` currently cites `lay2005imaging`, the wrong Lay paper.
      - M6: at `main.tex:611`, quote both the analytic limit 4/pi = 1.2732 and the
        measured 1.268, and say which is which. "approximately 27.3 %" implies an
        exactness the derivation does not have, since transmission x taper is not
        uniform over the domain. The abstract's "about 27 %" is fine.
      - M11: cite the stellar catalog at `main.tex:275`, and add one sentence
        noting the eta_Earth values in Table 2.2 are LIFE VI's, averaged over its
        20 pc sample, while the scaffold runs to 50 pc.
      - M9: justify the mission-time targets (5.5 / 6.0 / 7.5 / 8.0 yr) at
        `main.tex:619` against the LIFE baseline, or state plainly that they are
        arbitrary comparison points. They are the dominant lever on the answer
        (`main.tex:700`: 140 -> 610 for half a year). **(1.5 h)**

- [ ] **A3. Terminology.** Resolve the two incompatible meanings of "agnostic"
      (mechanism-agnostic in the title and Introduction vs. a parameter class not
      requiring SNR recomputation at `main.tex:416, 433`). Unify the budget-shape
      names across plot titles, captions and text — "Short-weighted" currently
      carries the embedded plot title "Long-Short Gradient" (Figs 5.1/5.2), and
      Fig. 4.1 calls the same curve "Additional Shot Noise". **(1.5 h)**

- [ ] **A4. Integral-normalised ramp comparison.** Neutral endpoint = 2 x flat;
      holds in 8/8 rows. Pure arithmetic on existing numbers, strengthens the
      null-order inversion at zero cost. Best ratio on the list. **(30 m)**

- [ ] **A5. Attribution cites.** Lay (2005) Eq. 17 for
      `<T2>_disk = 1/4 [1 - 2 J1(x)/x]` at `main.tex:936` — claim only the
      even-order and extended-profile extension. Guyon et al. 2013 §1 at
      `main.tex:488` for the Angel Cross throughput trade (theta^4 null on 25 % of
      light vs theta^2 on 50 %); it is established physics, not an artifact of the
      ansatz. **(20 m)**

**Cut line.** Tier S + A is roughly 11 h — a full working day. Everything below
waits for the post-diff fortnight.

---

## Tier B — comprehension, stretch for the diff

- [ ] B1. Define "pre-efficiency reference plane" at `main.tex:208`, where the
      Introduction's central claim first rests on it. It is currently only
      implicitly defined eight pages later as "after area, before eta" in Table 2.4.
- [ ] B2. Move the "iso-mission-time" definition forward. The term is in the title
      and is defined on p31 of 50.
- [ ] B3. Reference Fig. 4.1 in the text and complete its caption: catalog, null
      order, operating point, and whether the shaded region is a rate or a
      variance. It is the only drawing of an actual noise budget in the thesis.
- [ ] B4. Scope SQ3 honestly pending the Tier C assessment — state that the
      *modelling* reduction (collapsing instrumental random terms into one
      aggregate `N_I`) has no fidelity assessment yet, and give "significantly" a
      threshold.

---

## Tier C — after the diff, before 2026-08-10

- [ ] C1. **Throughput-normalized order-4 ablation.** Separates null order from
      throughput change, which are currently confounded. An examiner will ask.
      *(launched in Tier 0; may arrive early)*
- [ ] C2. **Local-zodi impact on published LIFE yields.** Extend the 10.9 % median
      SNR shift into yield deltas for the published configuration. **Strongest
      remaining novelty lever** — it turns a housekeeping footnote into a
      contribution to the collaboration.
- [ ] C3. **SQ3 aggregate-`N_I` fidelity assessment.** Split `N_I` into components,
      show the aggregate reproduces the split within a stated tolerance. Converts
      the one open research question into a result.
- [ ] C4. Minor findings m1-m7 from the scientific-competence report (redundant
      eligibility filters, `n_i` RMS labelling in Table 2.4, the 0.589645 baseline
      constant retained at order four, promoting retention limits from Appendix B
      into §6.4's Table 6.1, the unverifiable 26.7 % in Fig. 5.6's caption, missing
      tolerance and sample size at `main.tex:807`).
- [ ] C5. Full text polish once all numbers are frozen. Language, tense, redundancy,
      layout, float placement.

---

## Cover note to send with the diff

- [ ] List what is still coming (Tier C) so gaps read as planned work, not
      oversights.
- [ ] Ask directly: is the throughput-normalized ablation the right control for the
      null-order comparison?
- [ ] Ask directly: does he want the local-zodi yield impact quantified for the
      collaboration, given it affects published numbers?
- [ ] Confirm the mission-time reading in S2 before it propagates into the final.

---

## Making the work visible

The supervisor's read that this project contains a mountain of content is correct,
and the evidence is concrete:

- ~4,000 lines of AMS / TSE / analytic code, git-attributable to the student
- Closed-form reformulation of all three circularly symmetric background terms,
  validated at seven independent boundaries
- Two real defects found in upstream LIFEsim: the local-zodi normalisation
  (10.9 % median full-catalog SNR shift) and the exozodi log-spacing defect
  (up to 35 % before fix)
- A full trade-space exploration: 2 catalogs x 2 null orders x 3 budget families
  x 4 mission-time targets, each endpoint an iterative root-find over complete
  scheduler runs, over 100 universes and 4,505 stars
- A complete analytic derivation (Appendix A) and a reproducibility and rank-
  statistics treatment (Appendix B)

**The problem is that none of the three reviewers could see it.** One could not
determine what was the student's versus LIFEsim's. One capped originality partly
because the AMS appears on kickoff slide 11. One found the novelty claim
overstated because a related result in Dannert 2025 was never compared. An
earlier graphify review independently reached the same conclusion — "concise with
specific gaps", with an estimated net addition of 10-15 pages of exposition.

The gap between the size of the work and a 5.0 originality grade *is* the finding.
Closing it is the top-10 % path, and S1 is where it starts.
