# Examiner's Report — Logical Coherence and Quality of Presentation

**Thesis:** *Iso-Mission-Time Random-Noise Error Budgets for LIFE with Arbitrary Nulling and Noise Models*
**Candidate:** Nicolas Feuchthofen — **Artifact:** `thesis/main.pdf`, 71 pp.
**Criterion graded:** Logical coherence and quality of presentation (only).
**Reader profile:** competent scientist, general undergraduate physics, *not* a specialist in LIFE, nulling interferometry, or yield modelling. No background literature and no source code were consulted; where I could not follow, that is recorded as a finding.

---

## 1. Verdict

This is a well-organised, intellectually honest thesis whose prose is above the standard of the level, and whose separation of what was measured from what was assumed is genuinely exemplary — better than most doctoral work I read. The causal architecture (mission goal → measurement → SNR → budget → reduction → inversion → interpretation) is signposted at every chapter boundary and I never lost the thread of the *argument*. What repeatedly failed me was the *apparatus*: the symbol set, the figure labelling, and the numerical bookkeeping. Six symbols carry two or three meanings each, one of them (`x`) is given two mutually contradictory definitions in the body text; the headline result appears as three different numbers in three tables; two cross-references point at content that is not at the target; a full-page flowchart is illegible at printed size; a substantive table caption is clipped off the bottom of p. 30 and lost from the printed document; and an entire paragraph is duplicated on p. 55, the two copies contradicting each other ("months" vs "years" of computer time). Several figure captions explicitly document that the figure's own labels are wrong rather than the figures being regenerated. None of these damages the logic; all of them damage the reading. The result is a thesis that is *good, with certain flaws* — not one whose flaws are merely minor.

---

## 2. Findings against the eight sub-questions

### 2.1 Is the structure of the thesis logical and appropriate?

**(+) The macro-structure is sound and explicitly motivated.** Ch. 1 introduction and research question → Ch. 2 background/measurement model → Ch. 3 simulator and transmission model → Ch. 4 reduction of the trade space → Ch. 5 exploration/results → Ch. 6 discussion → Ch. 7 conclusion → Appendices A (derivation) and B (reproducibility). The roadmap paragraph on p. 9 states this chain and the thesis then follows it.

**(++) Chapter-to-chapter bridging is a real craft strength.** Almost every section closes with a sentence that hands off to the next: p. 12 "These assumptions specify the required scientific outcome, but not the individual planets that must supply it"; p. 14 "The catalog fixes the systems and planets to be observed; the next step is..."; p. 15 "Having established what reaches the detector and how it is weighted, we can now quantify..."; p. 17 "The SNR expression identifies the quantities that limit a measurement, but the error budget can only be defined after those noise contributions have been separated by physical origin." A non-specialist reader is never dropped between sections. This is deliberate and it works.

**(-) There is no chapter called "Results", and the most consequential result is filed under "Trade Space Reduction".** Table 4.1 (p. 36) — the local-zodiacal normalization defect and its factor-1.5-to-11 propagation into the derived allowance — is arguably the single most important quantitative finding in the thesis, and it sits inside a chapter framed as methodological housekeeping. Chapter 4 is in substance half method (§4.1, §4.3) and half result (§4.2). The reader who navigates by the table of contents will not find it.

**(-) §5.3 "The Random-Noise Error Budget" — the section named for the central answer — contains no number.** Two paragraphs, both caveats ("must not be interpreted as a global cost ranking"; "does not provide independent limits at individual wavelengths"), and a pointer to Table 5.1. The thesis never gives its own headline result a prominent, affirmative statement of its own. §6.1 partially repairs this on p. 52, one chapter late.

**(o)** Chapters are consistently called "Sections" in the prose (p. 9 "Section 2 establishes the experiment... Section 3 builds the simulator... Section 4 reduces... Section 5 then presents"; p. 19 "in Section 1"; p. 55 "the trade space of Section 5"). The printed headings say "Chapter 2". In the LaTeX this comes from `\subsection` being used for what renders as 1.1/2.1, i.e. a skipped sectioning level. Harmless but wrong throughout.

### 2.2 Are the results and conclusions clearly and logically presented?

**(+) The conclusion is disciplined and does not overreach.** Ch. 7 answers the five sub-questions of §1.1 one by one, in order, and each bullet is bounded. The final sub-question answer ("A deeper null therefore buys reach rather than margin") is a fair, non-inflated summary of §5.7. The closing paragraph (p. 60) explicitly restates that "These allowances do not yet constitute subsystem requirements" — the thesis declines the overreach that was available to it.

**(--) The same quantity is reported as three different numbers, and the abstract and conclusion quote a value the thesis's own appendix disowns.** The Hab2Max 5.5-yr flat allowance is **140** (Table 5.1, p. 41), **142** (Table 5.3, p. 51), **142.4** (Table B.2, p. 69). The Hab2Min 7.5-yr flat allowance is **65** (Table 5.1), **62** (Table 4.1, p. 36), **62.2** (Table B.2). Appendix B.3 (p. 68) then states plainly: *"Table 5.1 rounds most amplitudes to the nearest ten, but the smallest entry is given as 65, which is neither the nearest ten nor two significant figures of the reproduced 62.2 ... the values in Table B.2 should be preferred where the two disagree."* Yet **65 is what the Discussion (p. 52) and the Conclusion (p. 58) both quote**. Honesty in the appendix does not excuse propagating the disowned value into the two places a reader is most likely to cite. Table 5.3's caption, which sits ten pages after Table 5.1 and differs from it, does not mention rounding at all.

**(-) Text and table disagree within two sentences.** p. 36: *"the allowance collapses from 690 to 60"*; Table 4.1 immediately above gives 686 and 62. Both roundings are defensible in isolation; adjacent, they read as an error.

**(--) The Discussion asserts quantitative results that appear nowhere in the thesis.** p. 53: *"Holding throughput, collecting area and the baseline prescription fixed while deepening the null describes no realizable instrument, and doing so overstates the fourth-order allowances by a factor of several and places the feasibility boundary in field of regard some fifteen degrees too far."* No table, figure or number anywhere in Ch. 5 supports "a factor of several" or "fifteen degrees" — the idealized-response run these come from is never presented. Compounding this, the **abstract** ("for a realizable six-aperture combiner as well as for an idealized response") and the **conclusion** (p. 59, same claim) both bank the idealized-response comparison as an established result. A reader who goes looking for it in the results chapter will not find it. This is the clearest case in the thesis of a conclusion outrunning its presented evidence.

**(+) Where results *are* presented, the reasoning from result to interpretation is explicit and checkable.** §5.2's integral-neutral control (p. 42: a ramp from 0 to *A* has mean *A*/2, so the neutral endpoint is twice the flat amplitude, and the observed endpoints exceed it in all four rows at each order) is a genuinely good piece of argumentation: the author anticipated that "ramp endpoint vs flat amplitude" is not an apples-to-apples comparison and built the control before the reader could object.

### 2.3 Have the central questions been answered?

**(+) Yes, and the answer is located where the question was posed.** The italic central question of §1.1 (p. 7) and its five bullet sub-questions are each closed in Ch. 7 in the same order, and each closure is bounded rather than asserted. Sub-question 2 in particular is answered with an unusual and creditable admission (p. 58): *"The two reductions must be judged separately, and only one of them is validated here"* — the modelling reduction is declared answered only partially.

**(-) The abstract does not contain the answer.** Three dense paragraphs give the 27 % correction, the 1.5–11 amplification, the ordering reversal, the "six percent sooner", the six-aperture minimum — but **not the allowance numbers themselves** (140 and 65 ph s⁻¹ µm⁻¹). The quantity the whole thesis exists to determine is absent from its summary. A reader scanning the abstract learns what changed and what reversed, but not what the answer *is*.

**(-) The central question is a 57-word sentence with three subordinate clauses and an em-dash parenthesis** (p. 7). I had to read it three times to establish that "it" in "such that it completes Experiment 1" refers to the mission and not to the requirements. It also introduces a third label — *instrument*-agnostic — alongside *mechanism*-agnostic and *architecture*-agnostic, which §2.6 (p. 19) then reconciles into only two senses. The thesis is aware the word is overloaded and says so; the correct fix was to rename one of them, not to document the collision.

### 2.4 Are facts clearly distinguishable from hypotheses and assumptions?

**(++) This is the outstanding quality of the thesis and it is sustained from p. 12 to p. 69.** Specific evidence:

- Table 2.1 caption, p. 12: *"They define this study's controlled comparison; they should not be read as a claim that every value is the latest top-level LIFE mission requirement."*
- p. 12: the SNR 44.1 characterization threshold is explicitly labelled *"a retained broadband proxy"*, not a physical statement, and the paragraph ends *"The output is conditional on all these assumptions."*
- Table 2.5, p. 18: a four-column noise taxonomy whose fourth column is literally *"Treatment and boundary"*, including an "Excluded terms" row naming what the model does *not* represent.
- Table 3.2, p. 30: a validation matrix whose third column states *what each check can and cannot establish*, followed on p. 31 by *"The strongest equality ... is deliberately narrow: both routes share underlying physical modules."* Declaring one's strongest validation to be weak is rare and correct.
- p. 29: *"It is not a calendar duration, because no duty cycle, downlink, calibration, or safe-mode overhead is applied to it"*, with the 5.5 yr → ~6.9 yr elapsed conversion spelled out and the admission that *"the allowances in Section 5 are correspondingly optimistic if the reader interprets the target as elapsed time."*
- p. 34–35: the local-zodiacal defect is argued as a defect rather than asserted, on internal evidence (two branches of the inherited routine disagreeing on the same physical configuration), and the scope of the claim is then fenced: *"the present work does not attempt to propagate it into any previously published LIFE yield number."*
- p. 49: *"no ablation run isolates leakage suppression from the simultaneous extended-source and planet-throughput changes"* — the author names the experiment he did not run.
- Table 6.1, p. 56: six ranked limitations with consequences, ordered by *"relevance to the thesis's central numerical and architectural claims, not ease of remediation."*
- Appendix B.3, p. 68: the thesis reproduces its own headline table and reports where it disagrees with itself.

I record this as the thesis's best presentational achievement without qualification.

**(-) The one place the discipline slips is p. 53** (see §2.2 above): a bare quantitative assertion with no evidential trail, in a thesis that elsewhere fences every number.

**(-) Density of hedging occasionally suppresses the signal.** §5.3 and §5.1 read as pure caveat. There is such a thing as so much qualification that the reader cannot tell what was found; pp. 40 and 44 approach it.

### 2.5 Formal requirements for diagrams, tables and literature sources

**(+) Literature apparatus is clean.** 15 numbered references, consistent author-title-journal-volume-page-year order, DOIs rendered as live links, "LIFE paper II / VI" nicknames used consistently in text so the reader can track the inherited chain. Citation placement is correct (before the full stop, grouped `[1, 3]`). **(o)** Ref. [12] gives an arXiv link where the rest give DOIs; ref. [15] (DLMF) helpfully names the three specific equations used.

**(--) Table 3.2 (p. 30) overruns the text block: its caption collides with the page-number footer and its last sentence is lost from the printed document.** The LaTeX caption ends *"...The first, third and fourth rows were recomputed for this document from the committed source, and their scripts are listed in Appendix B; the remaining entries are carried over from the development record and were not re-derived here."* **None of that sentence appears in the PDF.** Page 31 resumes with body text. This is not a cosmetic overfull box: the information lost is precisely the caveat distinguishing which validation rows are current evidence and which are historical, in the thesis's own validation table. A reader of the printed document is given a validation matrix with no indication that most of it was not re-derived.

**(--) Figure 3.1 (p. 27) is unreadable at printed size.** A full-page landscape flowchart in which the box text ("Get next planet / star from catalog", "Compute location& baselines, stellar leakage", "Save stellar data to memo dict") renders at roughly 4 pt. I could recover the *shape* of the two flows from the caption's colour key, but not a single decision condition from the diagram itself. Everything I actually learned about the simulation phase came from the prose on p. 26 and the caption; the figure contributed nothing a reader can use.

**(-) No List of Figures, no List of Tables, no nomenclature/symbol table, no list of abbreviations.** For a document carrying `N_I`, `B_i`, `s_i`, `n_i`, `x`, `φ`, `ψ`, `ϑ`, `θ`, `b`, `r`, `A`, `M`, `q`, `η`, `η_⊕`, `T_j`, `U_jk`, `R`, `R_FoV`, `R_max`, `u`, `p`, `n`, `μ_3`, `μ_4`, `C_S,i`, `V_i` this is a real omission. Table 2.4 (p. 17) is an excellent partial nomenclature for the SNR interface only, and its existence shows the author knew such a table was needed — it should have been extended to the whole document and moved to the front matter.

**(-) No declaration of originality and no acknowledgements.** ETH normally expects the former.

**(-) Layout: five badly underfilled pages out of 71** — p. 26 (~30 % full), p. 31 (3 lines), p. 38 (2 lines), p. 57 (1 paragraph), p. 60 (1 paragraph) — caused by float placement and `\clearpage` before every chapter. p. 11 carries Fig. 2.1 with roughly half the page blank beneath it. In a 71-page document, seven per cent of the pages being near-empty is visible to any reader.

**(-) Consistent typographic artifact: every chapter's opening paragraph begins with a stray leading space** (pp. 6, 10, 22, 32, 39, 61 — " Human curiosity extends far beyond Earth.", " This project is conducted...", etc.). Small, but it recurs at the most visible position on six pages.

**(o) Running header crowding on pp. 66–69**: the chapter title "Reproducibility and Statistical Interpretation" fills the header line and abuts "IPA / Quanz Group" on the left and the author name on the right.

### 2.6 Is there an informative summary/abstract?

**(+) The abstract is structurally correct** — it states what was built (AMS + trade-space explorer), what was changed (analytic reformulation, 27 % local-zodiacal correction), what was found (the 1.5–11 amplification; the short→long reversal with null order; the four-aperture chopping incompatibility; six per cent sooner at equal area), and what it means (the closing "iso-mission-time amplitudes within tested budget families, not wavelength-by-wavelength subsystem requirements"). It carries real numbers rather than promises. The final sentence is a properly scoped disclaimer.

**(--) It omits the actual answer** (140 and 65 ph s⁻¹ µm⁻¹) — see §2.3.

**(-) It is not readable by a non-specialist.** Paragraph 2 opens with *"For the second-order double-Bracewell reference, the short-weighted ramp admits the largest endpoint, consistent with geometric stellar leakage dominating the short-wavelength variance"* — five undefined terms in one sentence (second-order, double-Bracewell, short-weighted ramp, endpoint, geometric stellar leakage). "Hab2Max and Hab2Min", "field of regard 65°", "LIFEsim", "slew time" all arrive unexplained. An abstract is the one page guaranteed to be read outside the subfield; this one is written for readers who already know the answer.

### 2.7 Is the text comprehensible and correct, grammatically and scientifically?

**(+) Sentence-level writing is strong.** Clean, declarative, low on padding, and it uses parallel structure to carry contrasts well (p. 51: *"the deeper null wins where the schedule is tight and the best targets set the pace, loses where the schedule is loose and the marginal targets do"*). I found no grammatical errors of consequence and no misused technical vocabulary within the physics I can judge.

**(--) An entire paragraph is duplicated on p. 55, and the two copies contradict each other.** Both begin *"This is what converts the central question from a description into a procedure. A single endpoint search evaluates the mission six to eight times, a two-dimensional operating-point scan evaluates it a few hundred times..."*. The first says the trade space *"would have taken **months** of computer time"*; the second, three lines later, says *"would have taken **years** of computer time"*. (Confirmed as `main.tex` lines 991 and 993.) This is a draft-merge artifact that survived to submission, in the Discussion chapter, and it simultaneously duplicates text and states two different figures for the same quantity. Of everything in this report, this is the finding that most directly indicates the document was not read end-to-end before it was handed in.

**(--) Notation: six symbols carry multiple meanings, and one is defined twice with contradictory factors.**
- **`x`** — Eq. 3.5, p. 25: `x = πbθ/λ`. §4.2, p. 34 and Appendix A.2, p. 62: `x = 2πbR/λ`. These differ by a factor of two with no reconciling sentence (θ diameter vs R radius is *never* stated). Since the thesis's central physical scaling — the `x²/8` fourth-to-second-order leakage ratio of §5.6 and Eq. A.10 — depends on which `x` is meant, this is not a cosmetic collision. I could not close it and stopped trying.
- **`A`** — total effective collecting area (Table 2.4, p. 17), the additive modifier *function* (Eq. 3.1, p. 22), and the reported budget amplitude (Eqs. 5.1–5.3, p. 41). Three meanings, two of them within the noise model.
- **`T_4`** — output 4 (p. 17, `n_i = √⟨T_4²⟩`) and the *order-four* rotation-averaged response (Eq. 4.4, p. 34; Eq. A.4, p. 62). The double subscript in Eqs. 3.2–3.3 (`T_{3,2}`, `T_{4,2}`) is never explained — the reader must infer that the second index is the null order.
- **`θ`** — array rotation angle (Eq. 2.1, p. 15, and Fig. 2.2b), bold sky-offset vector (Eq. 3.4, p. 23), and scalar angular separation (Eq. 3.5, p. 25). Boldface disambiguates one of the three.
- **`R`** — spectral resolving power (Table 2.1, p. 12; p. 36 `R = λ/Δλ = 20`; Table 3.2 `R = 5, 10, 20, 50`) and angular disk radius (§4.2 p. 34, Eq. A.5 p. 62), the two uses appearing two pages apart.
- **`i`** — wavelength-bin index (Table 2.4, Eqs. 2.3–2.4) and the imaginary unit (Eq. 3.4). **`j`** — output index (Eq. 3.4) and cosine-harmonic summation index (Eq. 4.2, Eq. A.1).

**(--) Two cross-references point at content that is not at the target.**
- p. 28 *"the configured 0.8 observing efficiency"* and p. 29 *"the observing efficiency of 0.8 configured in Table 2.1"* — **Table 2.1 contains no observing-efficiency row.** Verified against the source: the table's thirteen rows run from "Qualifying sample" to "Baseline ratio and bounds" with no such entry. The 5.5 yr → 6.9 yr elapsed-time conversion on p. 29, one of the thesis's more important interpretive caveats, rests entirely on a number the reader is told to look up and cannot find.
- p. 50 *"The baseline prescription of Section 3.6 places the first peak of the chopped response on the habitable-zone centre"* — §3.6 (pp. 25–31) says nothing about a baseline prescription. The prescription is in §2.3 (p. 14), and the constants 0.5894 / 1.1376 appear nowhere else in the thesis. This is the pivot of §5.7's whole "each sized to its own response peak" argument and it is unsourced within the document.

**(-) Mixed US/UK spelling throughout.** `optimise`/`optimised` (pp. 9) alongside `optimized`/`Optimize` (pp. 12, 28, 45); `behaviour` (p. 23) alongside `behavior` (pp. 33, 56); `modelling` (pp. 19, 34, 59) alongside `modeling` (pp. 18, 34); `colour` (pp. 45, 46) alongside US `favorable`, `neighborhood`, `normalization`, `characterize`; `centre` alongside `center`. Verified across the source.

**(-) Voice inconsistency.** p. 6: *"For me, this scientific promise makes the practical definition of LIFE especially consequential."* The thesis is otherwise written in "we"/"this thesis". A single first-person-singular sentence in the second paragraph of the introduction reads as a leftover from a proposal.

**(-) "Iso-MT" appears in the axis labels and panel titles of Figs. 5.4 and 5.5 and is never expanded anywhere in the document.**

### 2.8 Is the layout of the thesis well done?

**(+) The chapter-opening design is handsome and functional** — a maroon rule, "Chapter N", a large ghosted numeral, the chapter title, and a one-line grey subtitle stating what the chapter is *for* ("Building a simulator that is agnostic to both the noise mechanism and the array"). These subtitles do real navigational work and I used them.

**(+) Body typography is professional**: consistent margins, well-set equations with sensible numbering, booktabs-style tables with no vertical rules, a clean four-field running header, a hyperlinked and correctly coloured TOC.

**(-) Float management is the weak point** — see §2.5 (five near-empty pages, one clipped table, one illegible landscape figure, Fig. 2.1 orphaned on a half-empty p. 11).

**(--) Figures 5.1 and 5.2 (pp. 42–43) are unreadable at printed size in their most information-dense element.** Each is a 2×2 arrangement of ~0.45-textwidth panels carrying a seven-entry in-panel legend rendered at roughly 3–4 pt. The legend is the only thing that tells the reader which curve is which. I could not read either legend without magnification, which means I could not read the figures.

---

## 3. Where I got lost — page by page

| Page | What blocked me |
|---|---|
| **2** | Abstract ¶2 assumes "second-order double-Bracewell", "short-weighted ramp", "endpoint", "geometric stellar leakage", "Hab2Max/Hab2Min", "field of regard" are known. I could not evaluate the claim on first reading. Also: no allowance number anywhere in the abstract, so I finished it not knowing the answer. |
| **7** | The 57-word italic research question. Three passes to resolve the referent of "it" and to notice that "instrument-agnostic" is a third variant of a word §2.6 says has two senses. |
| **11** | Fig. 2.1 labels the long dimension **`qb`**. `q` is defined nowhere in the thesis; the text (p. 14) uses **`r`** for the baseline ratio. I assumed q = r but could not confirm it. The small red dot at the centre of the figure is never mentioned. The four "(constructive)/(destructive)" sub-labels are at the limit of legibility. |
| **23** | `T_{3,2}` and `T_{4,2}` (Eqs. 3.2–3.3) — I could not determine what the second subscript meant until Eq. 4.2 on p. 34, eleven pages later, made "null order" the plausible reading. |
| **23** | Eq. 3.4 uses `i` as the imaginary unit six pages after `i` was fixed as the wavelength-bin index (Table 2.4, Eq. 2.3), and `j` as the output index — later reused as a harmonic index in Eq. 4.2. |
| **25** | Eq. 3.5, `x = πbθ/λ`, described as *"the same dimensionless separation the reference response depends on"*. I carried this definition forward and it broke at p. 34. |
| **27** | Fig. 3.1. Illegible. I could not read a single decision condition. |
| **30** | Table 3.2's caption runs into the page-number footer and its final sentence is **absent from the document**. I could not tell which validation rows are current and which are inherited — which is exactly what the missing sentence says. Separately, "Below 0.7 % at **image size 400**" — 400 of what unit? never stated. |
| **33** | Fig. 4.1: the caption says *"The dashed green line is the imposed N_I(λ)"*, but the legend offers both "Error Budget" and "Additional Shot Noise" in green. I could not decide which curve was N_I. The legend's `Localzodi`/`Exozodi` do not match the prose's "local-zodiacal"/"exozodiacal". The panel title reads "Short-Long Gradient" while the caption calls it the long-weighted family. |
| **34** | `x = 2πbR/λ` — contradicts Eq. 3.5 by a factor of two, with no reconciling sentence. **This is where I stopped being able to verify the thesis's central scaling argument.** Simultaneously `R` switches from resolving power to disk radius, and `⟨T_2⟩`/`⟨T_4⟩` switch from meaning outputs to meaning orders. Three collisions on one page. |
| **36** | Text says "collapses from 690 to 60"; the table directly above says 686 and 62. |
| **42–43** | Fig. 5.1's caption tells me the panel titles are named by the wrong convention and asks me to invert them mentally. Fig. 5.2, on the facing page, labels the same three families by the *other* convention ("Flat Budget / Short-Weighted Budget / Long-Weighted Budget"). I had two naming schemes for one set of three objects across a page turn. Both figures' legends are too small to read. |
| **44** | Fig. 5.3: axes are logarithmic and the caption does not say so; the four panels have different colour ranges (6–10, 8–10, 6–10, 8–10) and the caption does not say so — although Figs. 5.4 and 5.5 flag exactly this in bold. Worse, **dark = short mission time = good** here, whereas in Figs. 5.4/5.5 **dark = no admissible budget = infeasible**. §5.1 (p. 40) primes the reader with *"the plotted dark region represents this physically infeasible operating point"* four pages before Fig. 5.3 inverts it. I misread panel (a) on first pass. The saturated yellow (≥ 10 yr?) is never defined. |
| **46, 48** | "Iso-MT" in every panel title and colourbar label, never expanded. The black contours are labelled 150/250/500/1000/1600 with no statement of what quantity they contour. |
| **41 / 50 / 51** | The six-aperture design is called "Double triple nuller" (Table 3.1), "Triple nuller" (Table 5.1), "Triple nuller, 6 apertures" (Table 5.2), "Double triple nuller" (Table 5.3), "Double triple nuller, six apertures" (Table B.2), and in prose "the six-aperture fourth-order design", "the deeper null", "a realizable fourth-order design". Six names, one object. |
| **50** | *"The baseline prescription of Section 3.6..."* — not in §3.6. The constants 0.5894 and 1.1376, on which the entire architecture comparison rests, appear here and nowhere else, unsourced. |
| **51** | Table 5.3 gives 142 where Table 5.1 gave 140 for the same quantity, with no note. |
| **53** | *"...overstates the fourth-order allowances by a factor of several and places the feasibility boundary in field of regard some fifteen degrees too far."* No supporting number anywhere in the thesis. I could not check this and it is claimed as a result in both abstract and conclusion. |
| **55** | The duplicated paragraph, the two copies disagreeing on months vs years. I read it three times assuming I had misread. |
| **28–29** | *"the observing efficiency of 0.8 configured in Table 2.1"* — it is not in Table 2.1. The elapsed-time caveat (5.5 → 6.9 yr) depends on it. |

---

## 4. Figures and tables, one line each

**Figures**

| # | p. | Assessment |
|---|---|---|
| 2.1 | 11 | (--) Label `qb` uses a symbol (`q`) defined nowhere; text uses `r`. Unexplained red dot. Sub-labels at legibility limit. Orphaned on a half-empty page. Source correctly attributed. |
| 2.2a | 16 | (+) Axes (α, β in mas), colourbars ("transmission", "differential response") and markers all decodable from figure + caption. (o) Two panels have different colour ranges; obvious from the two bars but not stated. |
| 2.2b | 16 | (+) Clean, self-explaining; caption correctly notes the chopped and unchopped responses carry different weightings. "53 mas" in the title is unmotivated but harmless. |
| 3.1 | 27 | (--) Illegible at printed size. Caption's colour key is good and is the only usable part. |
| 4.1 | 33 | (+/--) Caption is one of the best in the thesis — it names the plotted target, gives its percentile rank in distance and temperature, and warns it is not typical. (--) But the caption's "dashed green line is N_I" cannot be matched to a legend containing two green non-solid entries; panel title contradicts the caption's family name; legend uses code names (`Localzodi`, `Exozodi`). Caption cites `ams.py:634-636`, unresolvable for a reader. |
| 4.2 | 37 | (+) Best-executed figure in the thesis. Dual y-axes both labelled with units, four regimes distinguished, median-plus-band construction stated, the adopted R = 20 marked with a dashed line and explained. Fully decodable from figure + caption. |
| 5.1 | 42 | (--) In-panel legends unreadable at print size; panel titles use a naming convention the caption itself declares wrong; shared y-scale not stated. |
| 5.2 | 43 | (--) Same legend problem; uses a *different* naming convention from Fig. 5.1 on the facing page. Caption does the right thing in confirming the same target is plotted in both. |
| 5.3 | 44 | (--) Colour scales differ between panels without a caption warning (contrast Figs. 5.4/5.5, which warn in bold); log axes unstated; dark/light semantics inverted relative to Figs. 5.4/5.5; saturated region undefined. |
| 5.4 | 46 | (+) Caption is strong — grid spacing (3.6°), meaning of dark regions, and **"Colour scales differ between panels"** in bold, with peak values quoted so the panels can be compared numerically. (-) "Iso-MT" unexpanded; contour values unexplained. |
| 5.5 | 48 | (+) Same strengths, same two weaknesses. Quotes the infeasible-fraction percentages in the caption, which is exactly right. |
| 5.6 | 49 | (++) The best caption in the thesis: a "Reading the axes" paragraph and a "Reading the percentage" paragraph, a full decomposition of the 26.7 % into 6.3/19.2/1.3, and a bolded conclusion. (-) But the caption exists to argue against the figure's own annotation ("Targets Lost: 26.7 %" attached to the zone-of-avoidance wedges); the figure should have been redrawn. Radial gridline labels overlap the data; legend is small. |

**Tables**

| # | p. | Assessment |
|---|---|---|
| 2.1 | 12 | (+) Three-column quantity/value/role structure is excellent — the "Role in the calculation" column pre-empts most questions. Units given on every dimensional entry. (--) Does not contain the observing efficiency 0.8 that pp. 28–29 say it contains. |
| 2.2 | 13 | (+) Correct: asymmetric 1σ bounds shown, and the caption states what they are dominated by and that η⊕ is a mean per star, not an occurrence fraction. |
| 2.3 | 14 | (+) Provenance stated ("measured from the exact input files"), thin-space thousands separators, medians given, and an explicit warning against comparing to LIFE paper VI. (-) "Planet rows" is undefined jargon; the "1958–2154" range is not identified as min–max over universes. |
| 2.4 | 17 | (++) Model of its kind — symbol, meaning *at the stated interface*, and units including dimensionless "1". Exactly the table the rest of the thesis needed and does not have. |
| 2.5 | 18 | (++) Term / physical origin / modelled dependence / treatment-and-boundary, with an explicit "Excluded terms" row. The boundary column is what makes assumptions auditable. |
| 3.1 | 24 | (+) Compact and load-bearing (it carries the four-aperture chopping argument). (-) "Deep outputs" and "Light in pair" are used as column heads before either is defined in the text. |
| 3.2 | 30 | (--) Overruns the page, collides with the footer, and **loses its final sentence from the printed document** — the sentence that says which rows were re-derived. "Image size 400" has no unit. Otherwise the comparison/result/interpretation structure is excellent. |
| 4.1 | 36 | (+) Grouped headers with units, a ratio column, and a caption that states exactly what differs between the two configurations. Arguably the most important table in the thesis, and it is well built. (-) Filed in a "reduction" chapter; text on the same page rounds its numbers differently. |
| 5.1 | 41 | (+) Units in a spanning header, bolding explained in the caption, and an explicit warning that ramp endpoints are not cost rankings. (--) Contains the "65" that Appendix B.3 disowns; uses "Triple nuller" where Tables 3.1/5.3 use "Double triple nuller". |
| 5.2 | 50 | (+) Effective synthesis table; each row is a mechanism with its two-architecture values side by side. (-) Uses `x` without restating which definition. |
| 5.3 | 51 | (-) Units only in the caption, not the header; bolding not explained (Table 5.1's caption does explain it); gives 142/129 against Table 5.1's 140/130 with no note about rounding. |
| 6.1 | 56 | (++) Ranked limitations with consequences, and a caption stating the ranking criterion. This is how a limitations section should be presented. |
| B.1 | 66 | (+) SHA-256 identity record with sizes and counts; honest that the working tree was unclean. Appropriate for an appendix. |
| B.2 | 69 | (++) Unrounded reproduction with an "Achieved time [yr]" range column that makes the search tolerance visible. Substantively better than Table 5.1 — which is the problem: the better table is the one the reader is not pointed to from the abstract or conclusion. |

---

## 5. Best achievement

**The separation of fact from assumption, sustained across the whole document and built into its tables.** Table 2.5's "Treatment and boundary" column, Table 3.2's "what each check can and cannot establish", Table 6.1's ranked limitations, the p. 29 charged-time-vs-calendar-time caveat, the p. 49 admission that no ablation run isolates the mechanism, and an appendix that reproduces the thesis's own headline table and reports where it disagrees with itself — these are not boilerplate hedges but structural choices that make the work auditable by a reader who cannot check the code. Coupled with the chapter-bridging prose and the several genuinely excellent captions (Figs. 4.2 and 5.6, Table 2.4), this is presentation of a high standard.

## 6. Opportunity for improvement

**A single careful pass over the apparatus would have moved this thesis up a full grade band.** In order of return: (i) read the document end to end before submission — the duplicated, self-contradicting paragraph on p. 55, the clipped caption on p. 30, and the two dangling cross-references are all things a linear read catches; (ii) build a nomenclature table and enforce it — `x`, `A`, `T_4`, `θ`, `R`, `i`, `j` cannot mean two things each, and `x` in particular is *contradictorily* defined; (iii) regenerate the figures rather than writing captions that apologise for their labels — Figs. 4.1, 5.1, 5.2 and 5.6 all contain captions arguing against the plot above them, and Figs. 5.1/5.2 use two conventions for one set of families; (iv) fix one number per quantity and use it everywhere, in particular replacing the disowned 65 in the abstract-and-conclusion chain; (v) either present the idealized-response comparison or delete the "factor of several / fifteen degrees" claim and the abstract's and conclusion's reliance on it; (vi) put the allowance numbers in the abstract, and give §5.3 an affirmative statement of the result before its caveats.

---

## 7. Suggested grade

# **5.25**

**Justification against the scale wording.** This is not 5.5 ("very good, only minor flaws"). A duplicated paragraph whose two copies contradict each other, a table caption clipped out of the printed document, a full-page figure that cannot be read, two cross-references to content that is not at the target, a symbol given two contradictory definitions in the body text, and three different values for the thesis's headline number are not minor flaws — they are, collectively, evidence that the document was not proofread as a whole, and two of them (the `x` contradiction, the missing idealized-response evidence) directly impede a reader's ability to verify the central argument. Nor is it 4.5 ("satisfactory, several flaws"): the structure is logical and explicitly signposted, every central question is answered where it was asked, the conclusions are bounded rather than inflated, the distinction between measured, assumed and argued is maintained with genuine rigour, the reference apparatus is clean, and the sentence-level writing is better than the level requires. "Good, certain flaws" describes it precisely — the flaws are real, numerous and concrete, but each is locally repairable and none of them is a failure of thought. The quarter-step above 5 recognises that the fact/assumption discipline (§2.4) and the caption craft of Figs. 4.2 and 5.6 and Tables 2.4, 2.5 and 6.1 are of a standard I would normally associate with the band above, and that it is the finishing rather than the conception of the presentation that fell short.
