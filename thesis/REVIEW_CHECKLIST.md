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

**There is no defense and no exam.** The presentation was held two months ago,
already with outdated results. The grade comes from the written document alone.
Two consequences that reorder everything below:

1. Nothing can be explained verbally. Every comprehension blocker is permanent,
   so the presentation block — the one carrying the only `-` — is weighted
   heavier in practice than its share of the grading sheet suggests. Tier B is
   promoted into the diff, and so is the formal-compliance sweep A1.
2. The supervisor is away and it is holiday season, so **tomorrow's diff may be
   the only substantive feedback round left**. It must therefore carry the
   framing decisions he could disagree with (S1 positioning, the S2 mission-time
   definition, the Guyon normalization in the ablation), because those are
   expensive to get wrong and cheap for him to correct in one line.

**Rule for the diff:** include items where his feedback changes what you do next,
plus anything cheap. Everything else waits.

---

## Tier 0 — tonight, before anything else

- [x] Commit the dirty `lifesim/ams/` tree (branch `ams`) and push. Two commits:
      `93dde44` (analytic rewrite, 26 files) and `0314771` (thesis sources).
      LIFEsim also editable-installed into the conda env
      (`pip install -e . --no-deps`) -- it was not installed before, and only
      imported when the working directory happened to be the repo root.
- [x] Launch the throughput-normalized order-4 ablation. Far cheaper than
      feared: ~70 s per endpoint search, so the full 24-cell matrix runs in under
      half an hour rather than overnight. Script:
      `lifesim/ams/ablation_throughput.py`; results:
      `thesis/reproducibility/ablation_throughput.tsv`.

---

## Tier S — must be in the diff (~6 h)

- [x] **S1. Related-work / positioning subsection** after `main.tex:224`, plus a
      §6.1 paragraph placing `N_I` next to Dannert 2025 §3.4.2 `sigma_ph,inst`
      (Eq. 3.22) and the Lay 2004 perturbation levels.
      *Why #1:* the only item that moves all three blocks, and all three reviewers
      converged on it independently. No related-work section exists anywhere in the
      thesis. This is also where the size of the project becomes visible — see
      "Making the work visible" below. **(2 h)**

- [x] **S2. M7 — mission time is not wall-clock time.** Define it explicitly in
      §2.4 or §3.3.2 and state the conversion. With `opt_limit: experiments` the
      0.8 observing efficiency is inert (`ahgs.py:191,222`), so reported time is
      integration + slew only; a stated 5.5 yr is ~6.9 yr calendar at the
      configured efficiency. "on-source" and "wall-clock" appear nowhere.
      *Why early:* changes how every headline number reads. Better challenged
      tomorrow than in week two. **(30 m)**

- [x] **S3. M8 — complete the validation matrix** (Table 3.2, `main.tex:540-557`).
      Add the exozodi order-4/6 brute-grid deviations (~10 % on some stars,
      4.5-5.4 % at order 2) and the exozodi log-spacing defect (up to 35 % before
      fix), with the existing attribution to old-grid aliasing near the Kennedy
      `r_in` cusp. Report the 10.9 % median full-catalog SNR shift in §4.2 — it is
      the single most informative number about the local-zodi correction and is
      currently absent.
      *Why:* the matrix presently reports only the checks that went well, while the
      supervisor holds the internal brief that records the rest. **(1 h)**

- [x] **S4. C2 — uncertainty on the headline numbers.** Add the final
      `[lower, upper]` bracket and the stopping reason per row of Table 5.1, and
      quote intervals rather than point estimates in the abstract
      (`main.tex:190`). The eps = 0.05 yr stop rule
      (`trade_space_explorer.py:127`) maps via the thesis's own slope to roughly
      +/- 40 ph s^-1 um^-1 on a reported value of 65; two significant figures imply
      a precision `main.tex:624` explicitly disclaims.
      *Why:* kills the SQ6 `-` outright, and the data already exists. **(2 h)**

- [x] **S5. C1 — document the approval.** The supervisor has approved the analytic
      rewrite. Record the provenance in Appendix B.2 rather than softening the
      claim at `main.tex:582, 619, 876`, and fix the stale status line in
      `ANALYTIC_NOISE_REWRITE.md:3` ("NOT yet supervisor-approved") plus its §8
      reference to `.bak` files that are no longer in the tree.
      *Why:* two documents currently contradict each other in front of the person
      who signed it. **(20 m)**

---

## Tier A — cheap, high yield, include if the day holds (~5 h)

- [x] **A1. Formal compliance sweep.** Orphaned floats now all referenced (the
      real list was Fig. "transmission maps", Table "noise taxonomy", Fig. 4.1
      "budget example", Table 5.2 "null order synthesis"); Appendix B pointed to
      from two places in the body; References added to the TOC via
      `\addcontentsline`; "MT" expanded in the Table 5.1 header. The cross-
      reference fault was worse than reported: the small-star `align` block
      carried a single label on the second equation, so every reference to the
      x^2/8 ratio resolved to the order-four expression alone. Both equations are
      now labelled and both citing sentences reference the pair.
      **Declaration of Originality is deliberately deferred** -- it is the last
      step before submission, see below.

- [x] **A2. Citation batch.**
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

- [x] **A3. Terminology.** Resolve the two incompatible meanings of "agnostic"
      (mechanism-agnostic in the title and Introduction vs. a parameter class not
      requiring SNR recomputation at `main.tex:416, 433`). Unify the budget-shape
      names across plot titles, captions and text — "Short-weighted" currently
      carries the embedded plot title "Long-Short Gradient" (Figs 5.1/5.2), and
      Fig. 4.1 calls the same curve "Additional Shot Noise". **(1.5 h)**

- [x] **A4. Integral-normalised ramp comparison.** Neutral endpoint = 2 x flat;
      holds in 8/8 rows. Pure arithmetic on existing numbers, strengthens the
      null-order inversion at zero cost. Best ratio on the list. **(30 m)**

- [x] **A5. Attribution cites.** Lay (2005) Eq. 17 for
      `<T2>_disk = 1/4 [1 - 2 J1(x)/x]` at `main.tex:936` — claim only the
      even-order and extended-profile extension. Guyon et al. 2013 §1 at
      `main.tex:488` for the Angel Cross throughput trade (theta^4 null on 25 % of
      light vs theta^2 on 50 %); it is established physics, not an artifact of the
      ansatz. **(20 m)**

**Cut line.** Tier S + A is roughly 11 h — a full working day. Everything below
waits for the post-diff fortnight.

---

## Tier B — comprehension, stretch for the diff

- [x] B1. "pre-efficiency reference plane" now defined inline where the
      Introduction first relies on it, with a forward pointer to its precise fixing.
- [x] B2. "iso-mission-time" defined at its first use in the body. The same
      sentence also carried the overstated novelty claim and the "initially
      counter-intuitive" framing; both are corrected there.
- [x] B3. Fig. 4.1 is now referenced from the text, and its caption states the
      ramp direction unambiguously and that the curves are photon-rate spectral
      densities rather than variances. **Still open:** the caption does not name
      the catalog or null order, which could not be recovered from the figure.
- [x] B4. SQ3 split into its numerical and modelling reductions in the
      Conclusion. The numerical one is validated; the modelling one is stated as
      exact for genuinely independent terms and untested for a realistic noise
      inventory, so the sub-question is answered as partial rather than closed.

---

## Tier C — after the diff, before 2026-08-10

- [x] C1. **Throughput-normalized order-4 ablation.** DONE and promoted into the
      thesis as Section 5.7. The penalized configuration reaches no target at
      all, which is a stronger result than the intended separation of null depth
      from throughput and is now a headline finding rather than a control.
- [x] C2. **Local-zodi impact.** DONE, in the tractable form. A published-yield
      delta is not reachable: the stellar scaffold here is 4505 stars to 50 pc
      against LIFE VI's 358 within 20 pc, the instrument-noise modules are absent,
      and the operating point differs, so there is no published yield number to
      perturb. Measured instead within this study, which is the quantity a reader
      can act on: the defect shortens the zero-budget mission time by 0.50-0.84 yr
      but changes the tolerated flat allowance by factors of 1.5 to 11. Reported
      in Section 4.2 with Table 4.2, generalized in Section 6.3, and stated in the
      abstract. The pi/4 factor is exact, so the pre-correction path is reproduced
      identically rather than approximated.
- [ ] C2b. **Optional follow-up:** the amplification result suggests re-examining
      whether any published LIFE requirement was derived through the tapered
      local-zodiacal path. Not attempted; would need the collaboration's own
      configurations rather than this scaffold.
- [ ] C3. **SQ3 aggregate-`N_I` fidelity assessment.** Split `N_I` into components,
      show the aggregate reproduces the split within a stated tolerance. Converts
      the one open research question into a result.
- [x] C6. **Penalized arm at feasible mission-time targets.** DONE. The
      reversal survives: long-weighted is largest in all six tested cases across
      both catalogs, by factors of 1.3 to 2.6, and clears the integral-neutral
      reference in every one. Reported as Table 5.3 in Section 5.7. Original note
      follows. The Guyon-penalized
      order-four configuration cannot complete Experiment 1 at 5.5 or 6.0 yr at
      all: with zero added noise it already needs 7.65 yr, so the endpoint search
      correctly returns no admissible budget. Rerun the penalized arm at 8.0, 8.5
      and 9.0 yr to test whether the *ordering* among budget families -- the
      actual reversal claim -- survives the throughput penalty.
- [x] C7. **Throughput sensitivity sweep.** DONE and promoted into the thesis as
      Section 5.7 plus a rewritten Section 6.1 and an abstract sentence. Result:
      mission time scales sub-linearly in 1/throughput (ratio 1.71-1.83 for a
      halving, against 2.0 for pure 1/tau), implying a throughput-independent,
      slew-dominated fraction of 17-29%. The throughput cost of a deeper null
      exceeds its leakage-suppression benefit by a factor of three to five, so a
      penalized order-four configuration reaches no target at all. Data:
      `thesis/reproducibility/throughput_sweep.tsv`.
- [x] C7b. **Background context.** DONE and reported in Section 6.1. The
      band-averaged astrophysical background is about 4300 ph/s/micron at null
      order two and 2350 at order four, so the second-order flat allowances are
      roughly 3% (Hab2Max) and 1.5% (Hab2Min) of it, against about a quarter at
      order four. Local-zodiacal light supplies 78-86% of that background, which
      is why a 27.3% error in it moved the requirement so far. Original note
      follows.
- [ ] C7b-orig. **Superseded:** state what fraction of the astrophysical
      background the reported allowances represent at one wavelength. Reviewer 2
      flagged its absence as the reason a reader cannot judge whether 140 or 640
      is demanding or comfortable. Requires evaluating `N_B(lambda)` at the
      operating point; not yet done.
- [ ] C4. Minor findings m1-m7 from the scientific-competence report (redundant
      eligibility filters, `n_i` RMS labelling in Table 2.4, the 0.589645 baseline
      constant retained at order four, promoting retention limits from Appendix B
      into §6.4's Table 6.1, the unverifiable 26.7 % in Fig. 5.6's caption, missing
      tolerance and sample size at `main.tex:807`).
- [ ] C5. Full text polish once all numbers are frozen. Language, tense, redundancy,
      layout, float placement.

---

## Final step before submission

- [ ] **Declaration of Originality.** Download the current official ETH form,
      sign it, place the PDF in `thesis/`, and include it with `\includepdf`
      (the `pdfpages` package is already loaded in the preamble). Do not
      reconstruct the wording by hand; use the current official template. This
      is the last action before the thesis is sent off.

## Cover note to send with the diff

- [ ] **Lead with what changed since the presentation.** He last saw results two
      months ago and they were already outdated then. Without an explicit
      changelog he will read the new numbers against a stale prior and aim his
      feedback at the wrong target. State what moved, why, and which conclusions
      survived.
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
