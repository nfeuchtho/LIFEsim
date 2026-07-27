# Block: Logical coherence and quality of presentation

External examiner report. Reviewer competence: general MSc physics; no specialist background in
nulling interferometry and no prior knowledge of the LIFE mission literature. Only `main.tex` and
`main.pdf` were consulted, as instructed. The compiled document is **50 pages**, not 49 — the
bibliography sits on p50 and is absent from the table of contents (see sub-question 5).

Physics correctness is explicitly *not* assessed here. Everything below concerns whether the work is
comprehensibly and honestly presented.

---

## Verdict per sub-question

### 1. Is the structure of the thesis logical and appropriate? — **+**

The macro-architecture is genuinely well conceived. The chain Introduction → Background → Methods →
Reduction → Exploration → Discussion → Conclusion is stated explicitly as a roadmap (main.tex:224,
p6–7) and each Background subsection ends with a one-sentence bridge into the next
(main.tex:272, 310, 346, 390, 413, 439, 445). That discipline is above average and I could follow the
skeleton without difficulty.

Three structural defects. First, the thesis promises "two linked tools", the AMS and the Trade Space
Explorer (main.tex:206, p5). The AMS gets a full Methods section with a flowchart (§3.3, pp22–26);
the **TSE gets no Methods section at all** — its entire algorithmic description is one paragraph
buried in the Results chapter (main.tex:624, p31–32). A named deliverable of the thesis is never
constructed for the reader. Second, and relatedly, §5.1 (main.tex:621–626) is pure methodology
(definition of the iso-mission-time budget, bracket search, stopping rules, monotonicity caveat)
sitting inside the chapter labelled "Trade Space Exploration"; Methods material is therefore spread
across Chapters 3, 4 and 5.1. Third, the Discussion adds very little: §6.1 (main.tex:834, p39)
restates the four headline numbers already given in §5.3 and Table 5.1, and the Conclusion
(main.tex:876, p42) states them a third time. Only §6.4/§6.5 (Limitations, Outlook) carry new
content.

Definition lag is the other structural weakness — see *Comprehension blockers* below. The single term
in the thesis title, "iso-mission-time", is first defined on p31 of 50 (main.tex:622).

### 2. Are the results and conclusions clearly and logically presented? — **o**

The central results table is clean and, importantly, **internally consistent**: I cross-checked every
number quoted in the abstract (main.tex:190), §5.2 (main.tex:700), §6.1 (main.tex:834) and the
Conclusion (main.tex:876) against Table 5.1 (main.tex:686–693, p33) and found no discrepancy. §5.3
opens with "Table 5.1 is the numerical answer to the central research question" (main.tex:733) —
exactly the signpost an examiner wants.

Against that: the central result *figures* are close to unusable. Figures 5.1 and 5.2 (p33) place
three panels at `0.32\textwidth` each, so the axis labels, tick labels and eight-entry legends are
sub-4 pt on the page — I could not read a single numerical value from the figure that is supposed to
demonstrate the thesis's headline finding. Figures 5.3, 5.4 and 5.5 (pp34, 36, 37) each present four
panels for cross-comparison but give **each panel its own independent colour scale** (Fig 5.3: 6–10,
8–10, 5–10, 6.5–10 yr; Fig 5.5: 0–2000, 0–1600, 0–1750, 0–1600), so the same colour means different
things in adjacent panels while the caption invites the reader to compare across them.

Five of twenty-one floats are never referenced in the text (see sub-question 5), including Figure 4.1
— the *only* figure that shows what a noise budget actually looks like.

Most seriously for comprehension: **the numbers are never anchored to anything**. After 50 pages I
still cannot say whether 140 ph s⁻¹ µm⁻¹ is a comfortable allowance or a hopeless one. Figure 4.1
implies the astrophysical background is of order 800–5000 in the same units, i.e. the allowance is a
few per cent to a few tens of per cent of it, but that ratio is never stated. One sentence would fix
this. Likewise, the choice of mission-time targets (5.5/6 yr for Hab2Max, 7.5/8 yr for Hab2Min) is
asserted without justification (main.tex:619, p31) — and the mismatched targets then actively damage
the catalog comparison, as the thesis itself concedes (main.tex:804).

### 3. Have the central questions been answered? — **+**

Yes, and unusually explicitly. The central question (main.tex:213) is answered and the answer is
pointed at by name (main.tex:733). The Conclusion closes each of the five sub-questions in a matched
bullet list (main.tex:879–885, pp42–43) in the order they were posed. This is exemplary practice and
should be preserved.

One sub-question is only half-closed. SQ3 asks "Can we reduce the AMS parameter space **without
significantly compromising fidelity**?" (main.tex:219). The Conclusion bullet (main.tex:882) answers
for the *numerical* reduction — analytic integration reproduces the grid calculation to the stated
validation precision. But the other reduction, the condensation of many independent noise mechanisms
into one aggregate $N_I(\lambda)$ (§4.1), is a *modelling* restriction whose fidelity cost is never
quantified or even bounded; Table 3.2 (p26) covers only the numerical rewrite. "Significantly" is
also never operationalised. See the tracking table below.

### 4. Are the facts clearly distinguishable from hypotheses and assumptions? — **+**

This is the thesis's strongest presentational feature and I want to say so plainly. Table 2.1's note
that the settings "should not be read as a claim that every value is the latest top-level LIFE
mission requirement" (main.tex:243), Table 3.1 "Interpretation boundary of the null-order proxy"
(p21), Table 3.2's closing line "Agreement with shared code establishes numerical consistency, not
independent empirical validation" (main.tex:555), the admission that "no ablation run isolates
leakage suppression" (main.tex:809), and the ranked limitations table (Table 6.1, p41) together form
a much more honest apparatus than is typical at this level.

Four slips, in order of severity:

- **main.tex:887 (p43):** "They define a **validated** bridge from scientific yield to an explicit
  engineering trade space." §3.3.3 explicitly says the checks are *not* independent empirical
  validation (main.tex:555, 559). The Conclusion therefore contradicts the Methods on the one word
  that matters most.
- **main.tex:190 (abstract, p2):** "stellar leakage is suppressed by three to five orders of
  magnitude". §5.6 reports median ratios of 6.3×10⁻⁵ and 1.9×10⁻⁵ (main.tex:807) — about 4.2 and 4.7
  orders. Neither "three" nor "five" is supported anywhere in the text; the spread across stars that
  would justify the range is never reported.
- **main.tex:836 (p39):** "The result is **robust** within the tested proxy." Robustness was not
  tested — no sensitivity study, no repeated runs, no ablation. The evidence is that the reversal
  appears in two catalogs and two targets, which is a weaker and perfectly reportable statement.
- **"approved"** (main.tex:582, 619, 876) and the surrounding vocabulary of internal project status
  ("legacy", "inherited", "the completed data collection", "final calculations", "production
  campaign") — approved by whom, on what criterion? To an outside reader this reads as an appeal to
  authority substituting for an argument.

Abstract paragraph 2 also states the null-order reversal as a physical fact before paragraph 3 walks
it back to a proxy artefact; a reader who stops after paragraph 2 is misled.

### 5. Have the formal requirements for diagrams, tables, literature sources etc. been met? — **–**

This is the weakest block and the reason the overall grade is held down.

**Unreferenced floats — five of twenty-one (24%).** Verified by matching every `\label` against every
`\ref` in main.tex:
- Table 2.2, η⊕ values (main.tex:290, p11) — never cited in text.
- Table 2.3, catalog inventory (main.tex:305, p11) — never cited.
- Table 2.5, noise taxonomy (main.tex:410, p16) — never cited.
- **Figure 4.1, the noise-budget illustration (main.tex:578, p28) — never cited.**
- Table 5.2, null-order synthesis (main.tex:827, p38) — never cited.

Also **Appendix B is never referenced from the main text** (`\label{app: reproducibility}`,
main.tex:986, has no matching `\ref`); Appendix A is properly referenced at main.tex:613. An entire
appendix that no sentence points the reader to.

**Bibliography.** The 11 entries are formatted consistently and completely (author, quoted title,
italic journal, volume, article number, year, resolvable DOI) — this part is done well. But
"References" (p50) does not appear in the table of contents (pp3–4), because `thebibliography` is
used raw with no `\addcontentsline`. Eleven references is also thin for an MSc thesis and every one
of them is either LIFE-internal, a LIFE input model, or Lay; there is no engagement with any
comparable mission concept or with the wider nulling literature.

**Missing formal front/back matter.** No List of Figures, no List of Tables, and — importantly for
ETH — **no Declaration of Originality**. If one exists it is not bound into this PDF.

**Cross-reference error.** main.tex:807 (p36): "Equation 4.4 predicts a fourth-to-second-order ratio
of approximately x²/8." Eq. 4.4 is ⟨T₄⟩ = x⁴/256 + O(x⁶) and predicts no ratio at all; the ratio
needs Eqs. 4.3 *and* 4.4, or Eq. A.10. Should read "Equations 4.3 and 4.4 give a ratio…".

**Notation and unit inconsistencies** (details in the line-level list): text uses `µm` while every
figure axis says "micron"; text uses "yr" while figure titles use "yrs"; thousands separators are
thin-spaced in tables (`486\,244`) but comma-separated in text (`50,000`, main.tex:624); Table 5.1
rounds everything to the nearest 10 except the value 65; the abbreviation **"MT"** appears in the
Table 5.1 header (main.tex:683) and in four figure colourbar labels ("Iso-MT Budget") and is **never
expanded anywhere in the thesis**; Figure 2.1 (p9), reproduced from Dannert, labels the long baseline
`qb` while the entire thesis text uses `rb` — the caption does not mention the relabelling.

**Hyperlink styling.** `hyperref` is loaded without `hidelinks`/`colorlinks` (main.tex:27), so the
printed document carries red boxes around every internal reference, green boxes around every
citation, and cyan boxes around every DOI. On p17 the red box around "Section 5" visually swallows
the following semicolon.

### 6. Is there an informative summary/abstract? — **+**

Yes, and a good one. Three paragraphs, ~330 words, structured as method → results → limitation. It
is quantitative (140→650, 65→590 ph s⁻¹ µm⁻¹, 27% normalization correction, floating-point agreement)
and it states the central limitation explicitly and unambiguously in paragraph 3 (main.tex:192) —
many theses do not. All numbers check out against Table 5.1.

Two weaknesses. It is not self-contained for a non-specialist: "Hab2Max", "Hab2Min", "LIFEsim",
"double-Bracewell", "local-zodiacal normalization", "90th-percentile mission time", "budget shapes"
and "endpoint" all appear with no gloss, and a reader outside the LIFE project cannot decode the
second paragraph. And it contains the one unsupported number in the thesis ("three to five orders of
magnitude", main.tex:190). Adding six or seven words of gloss would make it stand alone.

### 7. Is the text comprehensible and correct, both grammatically and scientifically? — **o**

Grammar and spelling are clean. I found no German-English interference, no agreement errors, and no
malformed sentences. Tense is mostly consistent (present for the document, past for the completed
runs), with minor jumpiness in the abstract.

What holds this at **o** is not grammar but *readability*, and it is systematic:

- **Symbol collisions.** `A` means total collecting area (Table 2.4, main.tex:358), the additive
  modifier function (Eq. 3.1, main.tex:452), *and* the budget amplitude (main.tex:431, 635; Eqs.
  5.1–5.3). `n` means null order (Eq. 3.4), the RMS single-output planet-noise coefficient (`n_i`,
  Table 2.4), *and* the number of summed noise sources (main.tex:569). `i` indexes wavelength bins
  everywhere except main.tex:569, where it silently indexes noise sources. That last equation — the
  defining equation of the aggregate budget, and the only unnumbered display in the thesis — manages
  to collide two symbols at once.
- **Nominalization tic.** "approved", "completed", "retained", "inherited", "legacy", "production"
  and "final" as pre-modifiers occur 30 times in main.tex. "Throughout the completed data
  collection" (main.tex:243), "the approved physics rewrite removes the science dependence on image
  size" (main.tex:582), "the retained smooth spectra" (main.tex:547). Each is individually
  survivable; cumulatively they make the prose opaque.
- **Undefined terms used as if defined:** "null depth" (only in the §3.2 title, main.tex:456 — the
  section is entirely about null *order*, never depth), "experiment-limited mode" (main.tex:533,
  used once), "image size 400" (main.tex:550 — 400 what?), "MT" (main.tex:683), "time sheet"
  (main.tex:533, informal).
- **One outright unit error:** "FoR $\pi/2$ retains the full sky" (main.tex:436, p17) mixes radians
  and degrees in the same sentence as "FoR 65°".
- **One uncited empirical claim:** "Current project estimates place the K-band limiting magnitude
  near 8" (main.tex:619) — no citation, no "private communication".
- **Voice inconsistency:** "For me, this scientific promise…" (main.tex:204) is the only first-person
  singular in the document; everything else is "we" or passive.

Scientific *statements* are, as far as I can judge without subfield expertise, carefully phrased. The
correction of the common misconception at main.tex:605 ("Rotation does not 'average away' a circular
background; rather, circular symmetry makes its integrated response independent of rotation angle")
is genuinely good expository writing.

### 8. Is the layout of the thesis well done? — **o**

The design is attractive and consistent: the coloured chapter-opening bar with the large numeral, the
grey chapter subtitle line, a clean three-part running header, sensible 1-inch margins, `booktabs`
rules throughout, no bare vertical rules in tables. Heading hierarchy is consistent and the TOC is
correctly nested to subsubsection level.

Against that:

- **Roughly six pages of dead whitespace.** p7 (four lines then blank), p19 (two paragraphs then
  blank), p25 (three paragraphs then blank), p30 (half blank), p43 (half blank), p49 (two paragraphs
  then blank). Cause: `\clearpage` before every `\chapteropening`, `\raggedbottom`, `placeins` at
  section level, `\parskip 3mm` plus `\onehalfspacing`. p25 in particular is blank because Table 3.2
  is declared `[H]` (main.tex:540) and cannot float back.
- **Figure 3.1 (p23)** is set landscape at `0.95\linewidth` but the flowchart's internal labels are
  around 4 pt and unreadable at print size; roughly 45% of the landscape page is blank below it. It
  is the only figure explaining the tool the thesis built.
- **Narrow `p{}` columns produce bad hyphenation and stretched interword spacing** in five tables —
  Table 2.1 ("Catalog flag re-quired", p10), Table 2.5 ("Modeled depen-dence", "Independent
  Poisson-like vari-ance", p16), Table 3.1 ("Stellar␣␣␣and␣␣␣extended-background", p21), Table 3.2
  ("Shared-route SNR com-parison", "vec-torization", "discretiza-tion", p26), Table 6.1 ("Symmetric
  exozodia-cal model", p41). Notably, a `RaggedRight` column type `R` is *defined* at main.tex:73 and
  never used.
- **"Chapter" vs "Section".** The opening pages say "Chapter 2" (main.tex:143) while every
  cross-reference in the text says "Section 2" (main.tex:224 and throughout) — the same unit under two
  names, because `article` class is being dressed as `report`.
- The References page (p50) is the only top-level unit without the chapter-opening design, and the
  long appendix titles overflow the centred header field on pp47–49.

---

## Comprehension blockers

Ordered by severity. These are places where I, as a competent reader outside the subfield, lost the
thread.

**1. What is the pre-efficiency single-output reference plane, and where is it? (main.tex:208, p6)**
The Introduction's key claim is that the thesis produces "an allowed single-output random count rate
at a defined pre-efficiency reference plane". At that point I have been given no optical train, no
definition of "single output", and no explanation of what "pre-efficiency" means. The clarification
arrives only implicitly, in Table 2.4 on p14, as the phrase "after area, before η". *Needed:* one
sentence in the Introduction — "the allowance is quoted as a photon rate at one of the two dark
outputs, after multiplication by the collecting area but before optical throughput and detector
efficiency are applied" — plus a marked reference plane on Figure 2.1.

**2. "Agnostic" carries two incompatible meanings. (title; main.tex:416, 433, p16–18)**
The thesis title says "Instrument-Agnostic", the tool is the "Agnostic Mission Simulator", and the
Introduction says the work is "mechanism-agnostic" about noise origin. Then §2.6 defines an "agnostic
parameter" as limiting magnitude, field of regard, or slew time — i.e. a computational category
meaning "does not require SNR recomputation". These are unrelated senses of the same word, and the
thesis half-admits it at main.tex:433 ("not quantities literally independent of every architecture").
I re-read §2.6 three times. *Needed:* rename the parameter class to "global parameters" or
"filter parameters", or add an explicit warning at first use that the word is being reused.

**3. What did the author build, and what was inherited? (main.tex:188, 227, 231, 509)**
The abstract says the thesis "develops an Agnostic Mission Simulator". §2.2 says the geometry is
"retained" from LIFEsim. §3.3.2 says "the only remaining step is to **use LIFEsim** to distribute the
available observation time". §3.3.3 says AMS and "the standard source routine" share underlying
physical modules. I could not determine where LIFEsim stops and the AMS begins, or which parts of the
result are new work. *Needed:* a short "What is new in this thesis" paragraph at the end of §1, and
one clarifying sentence in §3.3 stating that the AMS reimplements the source model and calls the
inherited LIFEsim scheduler.

**4. The figure legend and the thesis text name the same three budget shapes differently. (p28, p33)**
The text calls the families flat / short-weighted / long-weighted (main.tex:631–633). The embedded
plot titles in Figures 5.1 and 5.2 call them "No Gradient" / "**Long-Short** Gradient" / "**Short-Long**
Gradient" — and the mapping is inverted relative to what the words suggest: subcaption (b)
"Short-weighted" carries the title "Long-Short Gradient". Figure 4.1's caption compounds this by
describing "a linear distribution from short to long wavelengths" without saying which end is high.
Figure 4.1's legend then introduces a *third* name, "Additional Shot Noise", for the same curve the
caption calls "the budget distribution". Three vocabularies for three objects. *Needed:* regenerate
the figures with the thesis's own vocabulary, or delete the embedded titles entirely (they duplicate
the subcaptions and cost legibility).

**5. Figure 4.1 is never referenced and is the only place a noise budget is actually drawn. (p28)**
This figure is what finally made §4.1 click for me — and the text never sends the reader to it. Its
caption also does not state the catalog, null order, magnitude, field of regard, slew time, or which
of the three shapes it uses, and its 5-year mission time is not one of the four targets used
anywhere else in the thesis. I could not tell whether the shaded region is a photon *rate* or a
*variance*, given that the text is careful to say variances add. *Needed:* reference it from
main.tex:573, give it a full operating point in the caption, and state the plotted quantity.

**6. The title's key term is defined on page 31. (title; main.tex:622)**
"Iso-mission-time" appears in the title, the abstract, the Introduction and the Chapter 5 subtitle
before §5.1 finally defines it. It is a simple idea — the largest added noise that still meets a
chosen mission-time target — and one sentence in the Introduction would remove 30 pages of
uncertainty. Same problem, lesser degree, for "budget amplitude" (used main.tex:206, defined
main.tex:635) and "90th-percentile mission time" (used in the abstract, defined main.tex:530).

**7. Why 5.5 and 6 years, and 7.5 and 8 years? (main.tex:619, p31)**
The mission-time targets are the denominators of every number in the thesis, and they are simply
asserted. Is 5.5 yr a LIFE requirement, a nominal mission duration, a round number? And because the
two catalogs use different targets, the catalog comparison is confounded — the thesis notes this
itself at main.tex:804 but does not explain why the design was chosen that way. *Needed:* two
sentences of justification, and ideally one matched-target row pair in Table 5.1.

**8. Where does SNR 44.1 come from? (main.tex:256, 266, p10)**
Described as "the integrated broadband equivalent of a legacy per-channel requirement of SNR 10 at
11.2 µm and R=50". I cannot reconstruct 44.1 from that sentence, and the number propagates into every
result via Eq. 3.7. *Needed:* the one-line calculation, in the caption or in Appendix A.

**9. Table 3.1's two columns imply a row correspondence that does not exist. (p21)**
"Near-axis intensity power sin²φ → sin⁴φ" sits beside "Four collectors and collecting area"; the two
have nothing to do with each other. A two-column table format promises paired rows. *Needed:* either
two separate itemised lists, or a caption note that the columns are independent lists.

---

## Research question tracking table

| # | Sub-question (main.tex) | Answered? | Where | Quality of the answer |
|---|---|---|---|---|
| CQ | Max budget amplitude compatible with completing Experiment 1 within a chosen mission-time target (main.tex:213, p6) | **Yes** | Table 5.1 (p33); stated as the answer at main.tex:733 (p34); repeated main.tex:834 (p39), main.tex:876 (p42) | Strong. Explicitly signposted, numerically complete for 8 catalog/target/order combinations, internally consistent with abstract and conclusion. Weakened only by the unjustified choice of targets and by the absence of any scale reference for the numbers. |
| SQ1 | Dimension of the AMS parameter space (main.tex:217) | **Yes** | §2.6 main.tex:431 (p17–18); Conclusion bullet 1, main.tex:880 (p42) | Good. Formally infinite-dimensional (8 free functions + 3 scalars), reduced to 1/4/5 depending on what varies. Clear and consistently repeated. |
| SQ2 | Which source-model computations can be reused (main.tex:218) | **Yes** | §3.3.1 main.tex:494–496 (p22) + Fig 3.1 (p23); Conclusion bullet 2, main.tex:881 | Good in prose; the supporting figure is illegible at print size, so the answer rests entirely on the two-paragraph text. |
| SQ3 | Can the space be reduced **without significantly compromising fidelity** (main.tex:219) | **Partly** | §4.1–§4.2 (pp27–30); Table 3.2 (p26); Conclusion bullet 3, main.tex:882 | Weakest. The *numerical* reduction (analytic vs grid) is validated to stated precision. The *modelling* reduction — collapsing all instrumental random terms into one aggregate $N_I$ — has no fidelity assessment at all, and "significantly" is never given a threshold. The Limitations table (row 3, p41) concedes the issue but the sub-question is not reopened and closed. |
| SQ4 | Locate the maximum tolerated amplitude for flat and linear-ramp budgets (main.tex:220) | **Yes** | §5.1–§5.3, Table 5.1 (p33), Fig 5.3 (p34); Conclusion bullet 4, main.tex:883 | Good, with an honest caveat that these are search point estimates under an empirically-observed rather than proven monotonicity (main.tex:626). |
| SQ5 | How does changing null order alter the tolerated spectral budget shapes (main.tex:221) | **Yes** | §5.2 (p32–33), §5.6 (pp36–38), Table 5.2 (p38); Conclusion bullet 5, main.tex:884 | Good and appropriately hedged ("leading physical interpretation", "no ablation run isolates leakage suppression"). Undermined presentationally by Table 5.2 never being referenced and by the illegibility of Figs 5.1/5.2. |

**Net:** no sub-question is abandoned; one (SQ3) is closed only for half of what it asks.

---

## Figure and table audit

| Label / number | Page | Referenced in text? | Caption standalone? | Legible? | Issues |
|---|---|---|---|---|---|
| (title logo, `figure` env, main.tex:178) | 1 | n/a | no caption | yes | Decorative image inside a float environment; use plain `\includegraphics`. |
| Fig 2.1 double-Bracewell layout | 9 | Yes (main.tex:231) | Yes | Yes | Reproduced figure labels the long baseline **`qb`**; the whole thesis uses `rb`. Caption must note the relabelling. Reference plane for $N_I$ not marked (see blocker 1). |
| Fig 2.2a/2.2b transmission maps | 13 | Yes (main.tex:315, 317) | Yes — states λ, b, r, zoom | Yes; colourbars readable | Best figure in the thesis. Parent label `fig: transmission maps` unused. |
| Table 2.1 study assumptions | 10 | Yes (main.tex:243) | Yes, with sourcing note | Yes | "Catalog flag re-quired" hyphenates badly; SNR 44.1 derivation not given. |
| **Table 2.2 η⊕** | 11 | **No** | Yes | Yes | Never cited. Insert a reference at main.tex:277. |
| **Table 2.3 catalog inventory** | 11 | **No** | Mostly — but the range "1958–2154" is not identified as min–max | Yes | Never cited. Insert a reference at main.tex:277. |
| Table 2.4 SNR symbols | 14 | Yes (main.tex:349) | Yes | Yes | Good. This is where "pre-efficiency" is effectively defined, 8 pages after first use. |
| **Table 2.5 noise taxonomy** | 16 | **No** | Yes | Yes, but bad hyphenation in narrow columns | Never cited. Insert a reference at main.tex:393. |
| Table 3.1 proxy boundary | 21 | Yes (main.tex:470) | Yes | Yes | Two-column layout falsely implies paired rows (blocker 9); stretched interword spacing. |
| Fig 3.1 AMS flowchart | 23 | Yes (main.tex:494) | Yes — explains the colour code | **No** — internal labels ~4 pt | The only figure of the tool built by the thesis. Enlarge, or split into two portrait figures. ~45% of the page is blank. |
| Table 3.2 validation matrix | 26 | Yes (main.tex:538) | Yes, with the crucial "not independent empirical validation" note | Yes, but heavy hyphenation | `[H]` placement (main.tex:540) leaves p25 three-quarters empty. "Image size 400" — units missing. Three different phrasings for machine precision. |
| **Fig 4.1 budget example** | 28 | **No** | **No** — no catalog, null order, magnitude, FoR, slew; 5 yr is not a study target; plotted quantity (rate vs variance) unstated | Marginal — axis text small but readable | Legend says "Additional Shot Noise", caption says "budget distribution"; embedded title "Short-Long Gradient" vs caption "from short to long wavelengths". x-axis appears to stop near 17 µm although the band is 4–18.5 µm. |
| Fig 5.1 order-2 budget shapes | 33 | Yes (main.tex:635) | Yes, and it states the interpretation | **No** — three panels at 0.32 width | Embedded titles contradict subcaptions (blocker 4). Delete in-plot titles, use two rows of larger panels, or move to a landscape page. |
| Fig 5.2 order-4 budget shapes | 33 | Yes (main.tex:635) | Yes, and cross-refers to Fig 5.1 | **No** — same problem | Same. These two figures are the visual core of the thesis's headline claim. |
| **Table 5.1 final amplitudes** | 33 | Yes (main.tex:702, 733, 883, 1021) | Partly — "common operating point" is not restated | Yes | See detailed audit below. |
| Fig 5.3 2-D ramp-endpoint scans | 34 | Yes (main.tex:704) | Yes | Axes yes; **colour comparison no** | Four independent colour scales in a four-panel comparison figure. Contour labels differ between panels. Units "micron" not µm. |
| Fig 5.4 magnitude × FoR | 36 | Yes (main.tex:740) | Yes, and explains the dark region | Yes | Four independent colourbar ranges again. In-plot titles say "yrs" (text uses "yr") and omit catalog/order. Colourbar label uses the undefined "Iso-MT". |
| Fig 5.5 slew × FoR | 37 | Yes (main.tex:768) | Yes | Yes | Same three issues as Fig 5.4. |
| Fig 5.6 ecliptic yield view | 38 | Yes (main.tex:804) — but only to say what it is *not* evidence of | **No** — "26.7%" is never said to be 26.7% *of what* | Yes | Orphaned: it illustrates the field-of-regard cut but sits in §5.5 "Catalog Dependence". Move to §5.4 or delete. |
| **Table 5.2 null-order synthesis** | 38 | **No** | Yes — genuinely good standalone summary | Yes | Never cited. This is the best single-page summary of the thesis's finding and no sentence points at it. Reference it at main.tex:809. |
| Table 6.1 ranked limitations | 41 | Yes (main.tex:847) | Yes, including what "priority" means | Yes, minor hyphenation | Strong table. |
| Table B.1 provenance hashes | 48 | Yes (main.tex:1001) | Yes, including the honest note that the repo was not clean | Yes | Good. |

### Table 5.1 — detailed check (the central results table)

- **Internal consistency: passes.** Every ordering claim in the text holds in the table. Order 2:
  short-weighted is the largest of the three in all four rows (300>210>140; 1300>1090>610; 200>150>65;
  970>810>460). Order 4: long-weighted is largest in all four rows (1470>1080>650; 2240>1830>940;
  1260>1000>590; 1860>1460>790). Order 4 exceeds order 2 in every one of the twelve matched cells.
- **External consistency: passes.** Abstract (main.tex:190) 140→650 and 65→590; §5.2 (main.tex:700)
  140→610, 650→940, 65→460, 590→790; §6.1 (main.tex:834) 140/65→650/590; Conclusion (main.tex:876)
  identical. All match the table.
- **Rounding is inconsistent.** 23 of 24 values are multiples of 10; the single exception is **65**
  (Hab2Min, 7.5 yr, order 2). Significant figures range from 2 (65, 140) to 3 (1080, 1470, 2240).
  Appendix B.2 refers to "the precision used in Table 5.1" (main.tex:1021) without ever stating what
  that precision is. *Fix:* state the rule in the caption ("all amplitudes rounded to the nearest 10
  ph s⁻¹ µm⁻¹") and round 65 → 70, or state that values below 100 are given to the nearest 5.
- **No uncertainty column.** §5.1 (main.tex:624) explains carefully that the two stopping rules give
  different and non-symmetric bracket widths, and §6.4 (main.tex:868) says no single error bar is
  recoverable. That honesty is correct — but the table should then carry a "stopping rule" or
  "final bracket width" column, or at minimum a caption sentence, rather than presenting 24 bare
  point estimates.
- **Missing operating point.** The caption says "the common operating point" without restating
  magnitude 7, FoR 65°, 12 h slew. A results table must stand alone.
- **"MT target"** is undefined (see above). Header formatting: the `\multicolumn{3}{c}{Amplitude…}`
  unit line sits under three left-headed columns without a `\cmidrule`, so on p33 it reads as slightly
  detached from the columns it governs.

---

## Line-level language and formatting fixes

### A. Substantive wording (each of these changes what a reader concludes)

1. **main.tex:887** — *"They define a validated bridge from scientific yield to an explicit engineering
   trade space"* → *"They define a numerically verified bridge from scientific yield to an explicit
   engineering trade space"*. §3.3.3 states the checks are not empirical validation; the Conclusion
   must not contradict it.
2. **main.tex:190** (abstract) — *"stellar leakage is suppressed by three to five orders of magnitude"*
   → *"the median stellar leakage is suppressed by roughly four to five orders of magnitude across the
   band"*, and add the corresponding min/max across the 4505 stars to §5.6 so the range is supported.
3. **main.tex:836** — *"The result is robust within the tested proxy"* → *"The reversal appears in both
   catalogs, at both mission-time targets, and in the full two-endpoint contour scans"*. State the
   evidence, not a robustness claim that was not tested.
4. **main.tex:582** — *"The approved physics rewrite removes the science dependence on image size."* →
   *"The analytic reformulation removes the dependence of the production SNR on the spatial image
   size."* Apply the same treatment to "approved" at main.tex:619 and main.tex:876.
5. **main.tex:619** — *"Current project estimates place the K-band limiting magnitude near 8"* — add a
   citation, or write *"(F. Dannert, private communication)"*, or delete the claim and justify
   magnitude 7 directly from Fig 5.4.
6. **main.tex:619** — add two sentences justifying the mission-time targets, e.g. *"The targets follow
   the nominal LIFE primary mission duration of X yr; Hab2Min is evaluated at longer targets because
   its less favourable occurrence scenario cannot complete Experiment 1 within the Hab2Max targets at
   any non-negative budget."* (Adjust to the true reason.)
7. **main.tex:433/416 and the title** — resolve the double meaning of "agnostic". Minimum fix: at
   main.tex:416 insert *"Note that 'agnostic' is used here in a second, narrower sense than in the
   thesis title: an agnostic parameter is one that can be changed without recomputing source physics."*
   Better fix: rename the class to *global parameters*.
8. **main.tex:208** — after *"at a defined pre-efficiency reference plane"*, add *"— that is, a photon
   rate at one destructive output, after multiplication by the collecting area but before optical
   throughput and detector quantum efficiency are applied (Table 2.4)."*
9. **main.tex:206 or 224** — add one sentence defining the title term: *"An iso-mission-time budget is
   the largest added noise amplitude, within a chosen spectral shape, that still completes the
   observing programme within a stated mission-time target."*
10. **main.tex:831** — *"The thesis asks two connected questions"* → *"The thesis posed one central
    question and five sub-questions (Section 1.1). This chapter interprets the answers to the two that
    drive the numerical result:"* — as written, the Discussion re-frames the thesis in terms that do
    not map onto §1.1.
11. **main.tex:807** — *"Equation 4.4 predicts a fourth-to-second-order ratio of approximately x²/8"* →
    *"Equations 4.3 and 4.4 together give a fourth-to-second-order ratio of approximately x²/8 (Eq.
    A.10)"*. Change `\ref{eq: leakage small star}` accordingly.
12. **main.tex:509** — *"The only remaining step is to use LIFEsim to distribute the available
    observation time"* → *"The AMS then calls the inherited LIFEsim scheduler to distribute the
    available observation time"* — and add a "what is new here" paragraph at the end of §1.
13. **main.tex:733** — after this paragraph, add the missing scale anchor: *"For comparison, the total
    astrophysical background at the adopted operating point ranges from about X to Y ph s⁻¹ µm⁻¹ over
    the band (Fig. 4.1), so the second-order flat allowance corresponds to roughly Z% of it."*

### B. Notation and symbols

14. **main.tex:569** — rewrite the aggregate-budget equation to remove two collisions: currently
    `N_B(\lambda) = \sum_{i=1}^{n} N_i(\lambda) + N_I(\lambda)` uses `i` for noise sources (elsewhere:
    wavelength bins) and `n` for their count (elsewhere: null order). Replace with
    `N_B(\lambda) = \sum_{k\in\{\mathrm{leak},\mathrm{lz},\mathrm{ez}\}} N_k(\lambda) + N_I(\lambda)`,
    number the equation, and state its relation to `B_i` from Table 2.4 (currently the same quantity
    has two names).
15. **main.tex:431, 635 and Eqs. 5.1–5.3** — rename the budget amplitude from `A` (which is already
    collecting area in Table 2.4 and the additive modifier in Eq. 3.1) to `A_0` or `N_0`.
16. **main.tex:452** — rename the additive modifier `A` to `\mathcal{A}` and the multiplicative `M` to
    `\mathcal{M}` in Eq. 3.1.
17. **main.tex:456** — section title *"Modified Double Bracewell Null Depth Approach"* → *"Modified
    Double-Bracewell Null-Order Proxy"*. The section never discusses null depth and the term is never
    defined; also add the missing hyphen in "Double-Bracewell", which is hyphenated everywhere else.
18. **main.tex:683 and Figs 5.4/5.5 axis labels** — expand "MT" to "mission time" in the Table 5.1
    header, and regenerate the colourbar labels as "Iso-mission-time budget".
19. **Figure 2.1 caption, main.tex:236** — append *"The original figure denotes the imaging baseline
    ratio by $q$; this thesis writes it as $r$, so the labelled length $qb$ corresponds to $rb$ here."*
20. **main.tex:436** — *"FoR $\pi/2$ retains the full sky"* → *"FoR $90^\circ$ retains the full sky"*.

### C. Numbers, units and consistency (group fixes)

21. **Unit notation.** Text uses `\upmu`m; all figure axes and colourbars say "micron". Regenerate
    figure labels as `µm` (or state the equivalence once). Same for "yrs" in figure titles vs "yr" in
    text, and for the parenthesis/bracket mix in axis units (Fig 4.1 uses `( )`, Figs 5.3–5.5 use `[ ]`).
22. **Thousands separators.** main.tex:624 `50,000` and main.tex:442 `10^{10}` vs the thin-spaced
    `486\,244`, `126\,552\,381` in Tables 2.3 and B.1. Standardise on thin spaces: `50\,000`.
23. **Spelled-out vs numeric.** main.tex:546 *"two thousand sampled targets"* → *"2000 sampled targets"*,
    to match "15 stars" and "$2\times10^6$ angle samples" in the same table.
24. **Table 5.1 rounding.** State the convention in the caption and make 65 conform (see above).
25. **main.tex:550** — *"Below 0.7% at image size 400"* → *"Below 0.7% at an image size of 400 pixels
    per side"*.
26. **Table 2.3** — state whether "1958–2154" is the min–max or an inter-percentile range.
27. **main.tex:807** — *"outside the cancellation-sensitive numerical regime of the direct Bessel sum"*
    — give the threshold, e.g. *"outside the regime $x \lesssim 10^{-3}$ in which the direct Bessel sum
    loses precision to cancellation"*.

### D. Style and grammar (low severity, grouped)

28. **main.tex:204** — delete *"For me, "*. It is the only first-person singular in the thesis.
29. **main.tex:227** — *"This project is conducted within the scope of the LIFE space mission."* →
    *"This thesis was carried out within the LIFE mission study."*
30. **main.tex:243** — *"throughout the completed data collection"* → *"in all final simulation runs"*.
31. **main.tex:439** — *"Knowing the starting points and limits, we can now go back to the performance
    of the instrument."* → *"With the parameter classes defined, we can now state how instrument
    performance is measured."*
32. **main.tex:533** — *"In experiment-limited mode"* → define the mode at first use, or delete the
    clause. *"omitted from the time sheet"* → *"omitted from the mission-time distribution"*.
33. **main.tex:535** — *"a distribution-free binomial calculation gives approximately 95.6% coverage
    for the population 90th percentile between the 84th and 96th order statistics"* → *"the interval
    between the 84th and 96th order statistics contains the population 90th percentile with
    probability approximately 95.6%, by a distribution-free binomial argument."*
34. **main.tex:571** — *"As is evident from the blackbody behavior of the background noise sources, we
    must keep the wavelength dependence"* → *"Because each background follows a different blackbody
    spectrum, the wavelength dependence must be retained."*
35. **main.tex:700** — *"consistent across catalogs and both Hab2Max mission-time targets"* →
    *"consistent across both catalogs and both mission-time targets"*. As written it silently excludes
    Hab2Min's targets, which Table 5.1 shows do obey the ordering.
36. **main.tex:420** — *"a star emits more strongly in the shorter wavelengths"* → *"across 4–18.5 µm a
    stellar photon rate falls with increasing wavelength"*.
37. **main.tex:619** — *"still permits acceptable mission times"* → say what acceptable means, or
    *"still admits a positive budget at the adopted targets (Fig. 5.4)"*.
38. **Nominalization sweep.** "approved / completed / retained / inherited / legacy / production /
    final" as pre-modifiers occur 30 times. Roughly two thirds can be deleted with no loss:
    "the completed scans" → "the scans"; "the retained smooth spectra" → "the modelled spectra";
    "the completed products" → "the saved outputs"; "final calculations" → "the calculations".
39. **Bridge-sentence sweep.** Eight "Having established X, we can now Y" transitions (main.tex:272,
    310, 346, 390, 413, 439, 445, and the chapter openers). Keep about four; the rest read
    formulaically and inflate the Background chapter.

### E. LaTeX and layout

40. **main.tex:27** — `\usepackage{hyperref}` → `\usepackage[hidelinks]{hyperref}`, or
    `\hypersetup{colorlinks=true, linkcolor=black, citecolor=black, urlcolor=black}`. This removes the
    red/green/cyan boxes and fixes the swallowed semicolon at p17 (main.tex:420).
41. **main.tex:1031** — add `\addcontentsline{toc}{section}{References}` before `\begin{thebibliography}`
    so the bibliography appears in the TOC; consider giving it the `\chapteropening` styling for
    consistency with every other top-level unit.
42. **Add** a Declaration of Originality (ETH requirement) and, optionally, a List of Figures and List
    of Tables — with 21 floats the latter would earn their page.
43. **main.tex:540** — `\begin{table}[H]` → `[htbp]`. The `[H]` is what leaves p25 three-quarters blank.
44. **main.tex:73** — the `RaggedRight` column type `R` is defined and never used. Apply it to the
    narrow `p{}` columns in Tables 2.1, 2.5, 3.1, 3.2 and 6.1 to fix the hyphenation and interword
    stretching on pp10, 16, 21, 26, 41.
45. **main.tex:143 vs 224** — resolve "Chapter N" on the opening page against "Section N" in every
    cross-reference. Either switch the opening pages to "Section", or redefine the cross-reference
    macro to print "Chapter".
46. **main.tex:105** — long appendix titles overflow the centred header on pp47–49. Use
    `\chapteropening` with a short header title, or `\markboth` with an abbreviated form.
47. **main.tex:466–468** — Eq. 3.4 numbers two side-by-side equations as one, whereas their order-two
    counterparts (Eqs. 3.2, 3.3) are numbered separately. Make the pair consistent.
48. **main.tex:320, 372, 381, 385, 512** — single equations wrapped in `align` with no alignment point;
    use `equation`. Cosmetic.
49. **main.tex:178–181** — the title-page logo is inside a `figure` float; use plain `\includegraphics`
    in a `center` environment so it cannot migrate.
50. **Duplicate package loads** — `fancyhdr` (4, 19), `lettrine` (5, 20), `geometry` (6, 21), `dcolumn`
    (9, 22), `amsmath` (13, 16). Unused packages: `circuitikz`, `pdfpages`, `wrapfig`, `csvsimple`,
    `pgfplots`, `nicefrac`, `xfrac`, `soul`, `titlesec`, `gensymb`, and `siunitx` (loaded but every
    unit in the document is hand-typed — using `\SI` would guarantee the µm/micron consistency asked
    for in item 21).
51. **Whitespace.** pp7, 19, 25, 30, 43, 49 are half-empty or worse. Fixing item 43, enlarging Fig 3.1,
    and merging the two-paragraph tails of §2.7 and §3.3.3 into the preceding pages would recover
    about four pages.
52. **Figures 5.1/5.2** — regenerate at two-per-row or full-width, delete the embedded plot titles
    (redundant with the subcaptions), and enlarge the legend. This is the highest-value single
    graphical fix in the thesis.
53. **Figures 5.3, 5.4, 5.5** — use one shared colour normalisation per figure, or state explicitly in
    each caption that the panels use independent scales and that colours are not comparable across
    panels.

---

## Suggested block grade

# 4.75

(between "satisfactory — several flaws" and "good — certain flaws")

**Justification.** Three things in this block are done genuinely well and I want them on the record.
The fact/assumption discipline is better than most theses at this level: the interpretation-boundary
table for the proxy, the validation matrix that states what each check *cannot* establish, the "no
ablation run isolates leakage suppression" admission, and the ranked limitations table are the work of
someone who is trying not to oversell. The research-question bookkeeping is exemplary — five
sub-questions posed in §1.1 and five closed by name in the Conclusion, in order. And the results table
is numerically self-consistent: every figure quoted in the abstract, the Discussion and the Conclusion
traces back correctly to Table 5.1, which is not something one can take for granted.

What holds the grade below 5.0 is presentational execution rather than thinking. Five of twenty-one
floats — including the only illustration of what a noise budget looks like, and the best one-page
summary of the central finding — are never referenced in the text, and an entire appendix is
orphaned. The two figures that carry the headline claim (Figs 5.1, 5.2, p33) are physically
unreadable, and their embedded titles use a naming convention opposite to the thesis's own. Three
multi-panel comparison figures give each panel an independent colour scale. The title's key term is
defined on p31 of 50; "pre-efficiency reference plane" is used on p6 and explained on p14; "MT" is
never expanded; "null depth" appears only in a section title about null order; the symbol `A` carries
three distinct meanings and `n` three more. The word "agnostic" is used in two incompatible senses,
one of them in the title. The bibliography is missing from the table of contents and the Declaration
of Originality is missing from the document. And after 50 pages the reader still has no scale against
which to judge whether 140 ph s⁻¹ µm⁻¹ is good news.

**To reach 5.25–5.5, in order of return on effort:**

1. Reference the five orphaned floats and Appendix B, and regenerate Figures 5.1/5.2 at readable size
   with the thesis's own shape vocabulary. (Items 52, and audit rows for Tables 2.2, 2.3, 2.5, 5.2 and
   Fig 4.1.) This alone moves sub-questions 2 and 5 up a tag.
2. Add three sentences to the Introduction: the definition of "iso-mission-time", the definition of the
   pre-efficiency reference plane, and a "what is new in this thesis versus inherited LIFEsim"
   statement. (Items 8, 9, 12.)
3. Add one scale-anchoring sentence after main.tex:733 and two sentences justifying the mission-time
   targets. (Items 6, 13.)
4. Fix the symbol collisions in Eq. 4.1 and the amplitude `A` (items 14–16), expand "MT", correct
   "validated" and "three to five orders" (items 1, 2, 18).
5. `hidelinks`, `[htbp]` instead of `[H]`, `RaggedRight` in the narrow table columns, References in the
   TOC, Declaration of Originality. (Items 40–44.)

To reach 5.5+, the Discussion would additionally have to stop restating the Results and start
interpreting them against something external — even a single comparison to a published LIFE noise
level would transform the reader's ability to judge the significance of the answer.
