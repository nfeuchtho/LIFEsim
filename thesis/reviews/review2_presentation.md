# Block: Logical coherence and quality of presentation (revised draft)

External examiner, writing-quality block only. Judged as a self-standing document by a
reader with general MSc physics training and no LIFE-specific background. No oral defense
exists, so every gap below is treated as permanent.

Summary judgement in one sentence: the argumentative architecture and the honesty about
assumptions are well above the MSc norm, but the document contradicts its own tables in
three places, drops its most consequential result from the Conclusion, and renders its
principal results figure at a size at which it cannot be read.

---

## Verdict per sub-question

| # | Sub-question | Tag |
|---|---|---|
| 1 | Is the structure logical and appropriate? | **+** |
| 2 | Are results and conclusions clearly and logically presented? | **o** |
| 3 | Have the central questions been answered? | **++** |
| 4 | Are facts clearly distinguishable from hypotheses and assumptions? | **+** |
| 5 | Formal requirements for diagrams, tables, literature sources | **o** |
| 6 | Is there an informative summary/abstract? | **+** |
| 7 | Is the text comprehensible and correct? | **+** |
| 8 | Is the layout well done? | **o** |

**1. Structure — +.** The causal chain is stated at main.tex:233 and then actually followed;
every subsection ends with a bridge sentence into the next (main.tex:281, 319, 355, 399, 424,
452). Section 1.2 (main.tex:224–231) separates inherited from new work explicitly, which is
rare and valuable. Three structural deductions: (a) top-level divisions are printed as
"Chapter 3" on the opening page (PDF p. 22) but referred to as "Section 3" everywhere in the
text (main.tex:233), so "Section 3" and "Section 3.3" denote different levels of the same
hierarchy; (b) the Conclusion (main.tex:991–1003) omits Section 5.7 entirely, i.e. the section
the Discussion itself calls the one that "reverses the engineering reading" (main.tex:950);
(c) main.tex:446 re-defines "agnostic parameter" after main.tex:427 already did.

**2. Results and conclusions — o.** The prose presentation of results is genuinely clear, and
main.tex:754 (the integral-neutral check) and main.tex:756 (do not interpolate the table) are
model paragraphs. But the results are undermined by internal numerical contradictions
(blockers 3 and 4 below) and by Figures 5.1/5.2 being unreadable at the printed size
(blocker 1). A reader cannot verify the headline number of the thesis from the thesis.

**3. Central questions — ++.** The central question (main.tex:213) is answered at main.tex:787
and again at main.tex:992. All five sub-questions are closed as an explicit bullet list at
main.tex:995–1001, in the same order they were asked. Sub-question 3 is answered "for the
numerical reduction and only partially for the modelling one" (main.tex:998) with the reason
given — that is the correct way to close a question you have only half answered. No question
is left dangling. This is the strongest part of the block.

**4. Fact vs assumption — +.** Excellent throughout Chapters 2–5: main.tex:252 ("should not be
read as a claim that every value is the latest top-level LIFE mission requirement"),
main.tex:279, main.tex:497 (Table 3.1 is an "interpretation boundary" table), main.tex:501,
main.tex:578, main.tex:592, main.tex:678, main.tex:748, main.tex:863, main.tex:915, Table 6.1.
Two deductions: (a) the Conclusion states 640 and 590 (main.tex:992) with no mention that a
realizable combiner removes them entirely, so the Conclusion read alone yields the opposite
engineering message from the Discussion; (b) the abstract asserts the throughput result
(main.tex:192) without the caveat that the factor comes from "one specific pair of
architectures rather than from a general law" (main.tex:915).

**5. Diagrams, tables, sources — o.** Positives: every float is referenced; all 15 tables and 12
figures resolve; no `??` anywhere; captions are unusually informative and mostly standalone;
the bibliography is complete, uniformly formatted, and DOI-linked. Negatives, all countable:
figure-internal panel titles contradict the thesis's own terminology (PDF p. 38); undefined
abbreviations inside figures ("SR", "I/N" on p. 35; "interesting", "Localzodi", "Zone of
Avoidance" on pp. 31/43); "micron" on figure axes vs `$\upmu$m` in text; reference [12]
(Laugier) never cited; multi-citation lists unsorted ("[9, 2]", "[8, 2]", "[6, 4]"); Table 3.2's
caption collides with the page footer (PDF p. 28); Table 5.1's spanned "Amplitude" header has
no `\cmidrule`.

**6. Abstract — +.** Self-contained enough to stand alone, quantitative, states its operating
point, and states its own limitations in a dedicated third paragraph — better than most.
Three deductions: it never says what the mission programme actually is (Experiment 1, 50
planets, detection + characterization) so "mission time" is undefined for an abstract-only
reader; it quotes 65 ph s⁻¹ µm⁻¹, a value the thesis's own Appendix B.3 says should not be
used (main.tex:1149); and "three to five orders of magnitude" (main.tex:190) is not supported
by any number in the thesis, which shows ~4 to ~4.7 orders (main.tex:861, main.tex:946).

**7. Text — +.** Precise, consistent present tense, calibrated hedging, no waffle. Deductions
for: several 300-word paragraphs (main.tex:658, 671); several 50+-word sentences
(main.tex:206, 326, 950); mixed British/American spelling (see fix 21); three symbol
collisions (see fixes 26–27); five terms used without definition (see fix list).
No German-English interference detected.

**8. Layout — o.** The chapter-opening design (maroon bar, ghosted numeral) is attractive and
applied consistently, headers are suppressed on opening pages, equation/figure/table
numbering is coherently sectioned. Deductions: hyperref links are printed as coloured boxes
on every citation and cross-reference throughout the PDF; Table 3.2 overruns into the footer
(p. 28) and forces a four-line page 29; five further pages are ≥50% white (pp. 5, 11, 35, 46,
56); "Figure" and "5.6" are split across pages 42/43; the appendix running header is crowded
edge-to-edge (p. 58); the `geometry` block is over-constrained (`total={8.5in,11in}` plus four
explicit 1-in margins, main.tex:60–67).

---

## Comprehension blockers

Ordered by severity. These are the places where I, as an outside reader, could not resolve
the text against itself.

**B1. The principal results figure cannot be read, and its panel titles say the opposite of
its subcaptions. (PDF p. 38; main.tex:689–729)**
Figures 5.1 and 5.2 are the visual answer to the central question. Each has three panels at
`0.32\textwidth`, each carrying a seven-entry legend and full axis labels. At print size the
legend and tick labels are illegible — and these are the *same* PDF files that Figure 4.1
(PDF p. 31) shows at `0.8\linewidth` precisely because they need that width. Worse: panel (b),
subcaptioned "Short-weighted", carries the internal title "Long-Short Gradient", and panel (c),
subcaptioned "Long-weighted", carries "Short-Long Gradient". A reader naturally maps
"Short-Long" to short-weighted and concludes the figure contradicts the caption. Since the
entire null-order reversal claim rests on which panel is which, this is the most damaging
single defect in the block.
*Reader needs:* one figure per row (or 2×3 across a full page) at ≥0.45 width, regenerated
titles reading "Flat" / "Short-weighted" / "Long-weighted", and legend entries matching the
thesis vocabulary ("Local-zodiacal", "Imposed budget $N_I$", not "Localzodi Noise",
"Additional Shot Noise").

**B2. The Conclusion omits the result the Discussion calls decisive. (main.tex:991–1003; PDF
pp. 51–52)**
Section 5.7 and Discussion §6.1 establish that charging a realizable fourth-order combiner its
throughput penalty removes *every* admissible order-four allowance, and that the cost exceeds
the null-depth benefit by 3–5× (main.tex:913, 950). The Conclusion reports "The order-four
proxy raises them to 640 and 590" (main.tex:992) and never mentions the penalty. A reader who
reads abstract + conclusion (the normal reading pattern) receives a pro-fourth-order message
from the Conclusion and an anti-fourth-order message from the abstract. They cannot tell which
is the thesis's position.
*Reader needs:* two sentences in the Conclusion, and a sixth sub-question bullet or a closing
sentence stating that the order-four allowances are an upper bound that a realizable combiner
does not reach.

**B3. The headline Hab2Min allowance has three different values in the thesis. (main.tex:648,
742, 1147–1149; PDF pp. 33, 39, 47, 51, 59)**
Table 4.1 (main.tex:648) gives the corrected Hab2Min order-two flat allowance as **60**; the
prose at main.tex:656 repeats "collapses from 690 to 60"; Table 5.1 (main.tex:742) gives **65**;
the abstract (main.tex:190), Discussion (main.tex:942) and Conclusion (main.tex:992) all quote
**65**; Appendix B.3 reports the reproduced value as **62.2** and explicitly says 65 "is neither
the nearest ten nor two significant figures" and that Table B.2 "should be preferred where the
two disagree" (main.tex:1149). Table 4.1's own ratio column says 11.0, which is 690/62.2 and
not 690/60 = 11.5 — so Table 4.1 is internally inconsistent as printed. Separately,
main.tex:752 says the order-four Hab2Max flat budget "grows from **650** to 940" on the same
PDF page (39) where Table 5.1 prints **640**.
*Reader needs:* one number, propagated everywhere. Given that the thesis's own appendix
disowns 65, the fix is to correct Table 5.1's four rounding-step errors and re-round Table 4.1
consistently, then update abstract/Discussion/Conclusion. Leaving a known-wrong number in the
headline table and confessing it in Appendix B reads as unfinished work, not as candour.

**B4. The reproduction section contradicts its own machine-written table on the facing page.
(main.tex:1145 vs Table B.2; PDF pp. 59–60)**
The text states "The residuals of the rerun span $-0.044$ to $+0.034$ yr". Table B.2 gives
achieved times of 5.455 and 6.045 yr against targets of 5.5 and 6.0, i.e. residuals of −0.045
and +0.045. Both bounds in the sentence are wrong, and the table that disproves them is on the
next page. Appendix B.3 exists to establish that the numbers are trustworthy; an error here is
disproportionately costly. The following slope estimate ("roughly $6\times10^2$ to
$1.5\times10^3$ ph s⁻¹ µm⁻¹ per year") is also not derivable from Table B.2: the flat-family
secants are 379, 605, 801 and 936 per year, and the short-weighted secants reach ~2010.
*Reader needs:* corrected span (−0.045 to +0.045), and either the family the slope range refers
to or the full range 3.8×10² to 2.0×10³.

**B5. A parameter that caveats every number in the thesis is not where the thesis says it is,
and the mode it applies in is never defined. (main.tex:548, 550; PDF pp. 26–27)**
"In experiment-limited mode, the configured 0.8 observing efficiency neither caps nor rescales
the returned time" — "experiment-limited mode" appears once and is never defined. Two
sentences later: "the observing efficiency of 0.8 configured in Table \ref{tab: study
assumptions}". Table 2.1 has thirteen rows and none of them is observing efficiency. The
0.8 is then used to derive the 5.5 yr → 6.9 yr elapsed-time caveat that applies to every
result in the thesis. I could not verify the input to the most important caveat in the
document.
*Reader needs:* an "Observing efficiency 0.8" row in Table 2.1 with its role stated, and either
a definition of "experiment-limited mode" at first use or its deletion.

**B6. Figure 5.6 cannot be decoded. (main.tex:850–855; PDF p. 43)**
The caption explains only that "interesting" means Experiment-1-eligible and that "the 26.7%
value is specific to this catalog and selection" — without saying 26.7% *of what* (the figure
itself says "Targets Lost"). Neither the angular coordinate, the radial coordinate (ticked
10°–50°), nor the purple "Zone of Avoidance" is explained anywhere, and none of these terms
appears in the text. The text says the FoR filter is $|\beta_\mathrm{ecl}|\leq 65^\circ$, which
I could not reconcile with a radial axis topping out near 50°.
*Reader needs:* a caption naming both axes, defining the zone of avoidance, relating it to the
$65^\circ$ filter, and completing the 26.7% sentence.

**B7. Three unreferenced background magnitudes in the Discussion. (main.tex:944, 946; PDF
pp. 47–48)**
"the astrophysical background averages about 4300 ph s⁻¹ µm⁻¹ across the band at null order
two and about 2350 at order four" and then "Near 10 µm the local-zodiacal term supplies roughly
1760 of the 2260 present at order two, and about 1320 of 1530 at order four". These eight
numbers appear nowhere else in the thesis, are supported by no table, figure or cross-reference,
and the second set is roughly half the first, which reads as a contradiction until the reader
works out that one is a band average and the other a value at 10 µm. This paragraph does the
important job of giving the allowance a sense of scale, and it is the one place where the
reader must simply take the author's word.
*Reader needs:* a cross-reference to where these were measured, and an explicit "band average"
vs "at 10 µm" contrast in the sentence itself.

**B8. Cross-reference points at the wrong section. (main.tex:915; PDF p. 45)**
"The baseline prescription constant of Section \ref{sec: methods: AMS}" resolves to Section 3.3
(the AMS), which contains no baseline prescription. The habitable-zone-centre prescription is
introduced in Section 2.3 (main.tex:322) and repeated in Section 2.6 (main.tex:435), and the
constant itself is never given.

**B9. Terms used before or without definition.** Each is a small stall, but they accumulate:
- "hab2 stars" (main.tex:286) — quoted, never expanded; the catalog names Hab2Min/Hab2Max
  depend on it.
- "Kennedy inner cutoff" (main.tex:569) — used in the validation table with no definition.
- "unit-exozodi response" (main.tex:511) — used once, undefined.
- "field of regard" is used at main.tex:190 (abstract) and main.tex:317, but defined only at
  main.tex:449.
- "operating point" is used in the central research question (main.tex:213) but only fixed at
  main.tex:671 / Appendix B.1.
- "SR" and "I/N" appear only inside Figure 4.2 (PDF p. 35); the text uses $R$ and $N_I$.

---

## Research question tracking table

| Question (main.tex) | Answered? | Where | Quality of answer |
|---|---|---|---|
| **Central**: max budget amplitude compatible with Experiment 1 at a chosen mission-time target (213) | Yes | Table 5.1 (main.tex:731–750); asserted as the answer at main.tex:787; restated main.tex:992 | Good. Explicitly scoped to "the tested families and operating points". Weakened by the 60/65/62.2 tangle (B3) and by the Conclusion not restating the operating point. |
| **SQ1**: dimension of the AMS parameter space (217) | Yes | main.tex:444; closed main.tex:996 | Very good. Distinguishes the formally infinite-dimensional raw space from the 1/4/5 scalar dimensions actually searched, and names the discrete scenario choices. |
| **SQ2**: which source-model computations are reusable (218) | Yes | main.tex:509–511, Fig. 3.1; closed main.tex:997 | Very good. Symmetric statement of what is reused *and* what forces recomputation. |
| **SQ3**: can the space be reduced without compromising fidelity (219) | Partially, and says so | main.tex:583–601, Table 3.2; closed main.tex:998 | Excellent handling. Splits the question into a numerical reduction (validated) and a modelling reduction (exact under a stated condition whose coverage is untested) and declares the second only partially answered. This is the right way to close an incompletely answered question. |
| **SQ4**: locate the max amplitude for flat and linear-ramp budgets (220) | Yes | Table 5.1; search described main.tex:676; closed main.tex:999 | Good, with an honest "point estimates" framing and a quantified search uncertainty in Appendix B.3 — undercut by the residual-span error (B4). |
| **SQ5**: how null order alters the tolerated spectral shapes (221) | Yes | §5.2, §5.6, Table 5.2; closed main.tex:1000 | Very good. The reversal is triangulated three ways (endpoints, integral-neutral check main.tex:754, 2-D contours Fig. 5.3) and then re-tested under the throughput penalty (Table 5.4). The "no ablation run isolates leakage suppression" admission at main.tex:863 is exactly right. |

**No sub-question is left open.** SQ3 is deliberately half-closed with reasons, which I count as
answered rather than unanswered.

---

## Figure and table audit

### Figures

| Label | Ref'd? | Caption standalone? | Legible? | Issues |
|---|---|---|---|---|
| 2.1 double-bracewell-layout | Yes (240) | Yes | Yes | Figure labels the imaging baseline **$qb$**; text uses **$rb$** (main.tex:322, 470). Caption must say "the ratio written $q$ in the original is $r$ here". Bottom half of PDF p. 11 blank (`\newpage` at main.tex:249). |
| 2.2a/2.2b transmission maps | Yes (324, 326, 332) | Yes | Yes | Clean. Axes, units, colourbars and legends all labelled. No action. |
| 3.1 simphase flowchart | Yes (509) | Yes | Marginal | Box text ≈5 pt on a landscape A4 (PDF p. 25). Either split into "SNR flow" and "filter flow" as two portrait figures, or enlarge nodes. Landscape page number prints rotated on the spine edge. |
| 4.1 budget example | Yes (590) | Yes — the best caption in the thesis | Yes | Axis reads "ph s⁻¹ micron⁻¹"; text uses µm. Legend uses "Localzodi Noise" / "Additional Shot Noise" / "Error Budget" — none of these is the thesis's term. The shaded allowance is barely visible against the background at order two; consider a log ordinate or an inset. |
| 4.2 specres convergence | Yes (658) | Yes | Yes | "SR" and "I/N" undefined (text uses $R$, $N_I$). Sits alone on PDF p. 35 with ~40% white above and below. |
| 5.1 budget shapes no2 | Yes (596, 687, 863) | Yes | **No** | See B1. Panel titles contradict subcaptions. Subfigures carry no `\label`, so main.tex:596 must hand-write "(c)". |
| 5.2 budget shapes no4 | Yes (687) | Yes | **No** | Same as 5.1. |
| 5.3 tse linear additive | Yes (758, 863) | Yes | Borderline | All four panels titled identically ("Additive TSE with Linear Noise Budget") — uninformative. Colourbar ranges differ per panel (10.0 vs 6.5–10.0); the caption does not warn, so the panels look comparable and are not. Axes read "micron". |
| 5.4 iso magfor | Yes (794) | Yes | Yes | Per-panel colourbar maxima differ (500/400/800/600) without a caption note. Title abbreviation "Iso-MT" unused in text. |
| 5.5 iso slewfor | Yes (822) | Yes | Yes | Same colourbar caveat. |
| 5.6 tse yield | Yes (858) — but "Figure"/"5.6" splits across pp. 42/43 | **No** | Marginal | See B6. Radial tick labels overlap the data. |

### Tables

| Label | Ref'd? | Caption standalone? | Issues |
|---|---|---|---|
| 2.1 study assumptions | Yes (252, 550) | Yes | Does **not** contain the 0.8 observing efficiency that main.tex:550 says it configures (B5). "Catalog flag re-quired" hyphenates badly in the narrow column. |
| 2.2 eta earth | Yes (284) | Yes | Fine. Uncertainty semantics stated. |
| 2.3 catalog inventory | Yes (284) | Yes | Fine; the "verified from the input files" framing is good practice. |
| 2.4 snr symbols | Yes (358) | Yes | $A$ = collecting area here, $A$ = additive modifier at main.tex:465, $A$ = budget amplitude at main.tex:683. Three meanings, two of them inside equations the reader must hold simultaneously. No numeric value given for $A$, so the reader cannot check any rate. |
| 2.5 noise taxonomy | Yes (404) | Yes | Fine. |
| 3.1 proxy boundary | Yes (483, 885) | Yes | Fine — one of the strongest devices in the thesis. |
| 3.2 validation matrix | Yes (555, 998) | Yes | `[H]` placement drives the caption into the page-28 footer and leaves p. 29 with four lines of text. "Kennedy inner cutoff" undefined. |
| 4.1 localzodi impact | Yes (636, 960) | Yes | Flat allowance **60** contradicts Table 5.1's **65**; printed ratio **11.0** ≠ 690/60 = 11.5 (B3). The "between 10 and 16%" at main.tex:636 is only true relative to the *pre-correction* time; relative to the corrected time it is 9.4–13.9%. State the denominator. |
| 5.1 budget shapes | Yes (671, 756, 787, 885, 889, 999, 1143, 1147) | Yes | Four of 24 values are disowned by Appendix B.3. Spanned "Amplitude" header needs `\cmidrule(lr){4-6}`. Values printed to 3–4 significant figures while main.tex:1145 says none should be read beyond two. |
| 5.2 null order synthesis | Yes (865) | Yes | Fine. Verified against main.tex:1039 (1/4 and 3/16). |
| 5.3 throughput sweep | Yes (891) | Yes | Verified: ratios 1.71–1.83 ✓, throughput-independent fraction 17.5–28.9% ✓, "largest for the shortest campaigns" ✓. But main.tex:913's "3.19" should be **3.18** (7.65 − 4.47). |
| 5.4 penalized reversal | Yes (915) | Yes | I checked all six rows: ratios ✓, "largest in all six cases" ✓, "exceeds twice the flat amplitude in every one" ✓, "short-weighted clears that reference only in the most relaxed Hab2Max case" ✓. Fully consistent — the best-verified table in the thesis. |
| 6.1 ranked limitations | Yes (963) | Yes | Fine; the priority-not-tractability note is a good touch. |
| B.1 provenance hashes | Yes (1120) | Yes | Hashes wrap mid-string with no continuation marker; a reader cannot tell one wrapped hash from two. Use `\seqsplit` or a two-line `\texttt` with an explicit break glyph. |
| B.2 reproduction | Yes (1149) | Yes | Contradicts the residual span stated one page earlier (B4). |

Nothing is unreferenced, and every `\ref` resolves. Reference **[12] Laugier et al.** is in the
bibliography (main.tex:1254) and cited nowhere — delete it or cite it.

---

## Line-level language and formatting fixes

### Numerical corrections (do these first)

1. **main.tex:752** — `from 650 to 940 at order four` → `from 640 to 940 at order four`. Table 5.1 on the same page prints 640.
2. **main.tex:1145** — `The residuals of the rerun span $-0.044$ to $+0.034$\,yr` → `The residuals of the rerun span $-0.045$ to $+0.045$\,yr`. (From Table B.2: 5.455 and 6.045 against 5.5 and 6.0.)
3. **main.tex:1145** — `roughly $6\times10^{2}$ to $1.5\times10^{3}$\,ph\,s$^{-1}$\,$\upmu$m$^{-1}$ per year` → `roughly $4\times10^{2}$ to $2\times10^{3}$\,ph\,s$^{-1}$\,$\upmu$m$^{-1}$ per year across the three families` (flat secants: 379, 605, 801, 936; short-weighted reaches ≈2010).
4. **main.tex:648** — reconcile the Hab2Min order-two corrected allowance with Table 5.1. Recommended: print `62` in Table 4.1 and `62` in Table 5.1, keep ratio `11.0`. Then update main.tex:190 (abstract), 656, 942, 992.
5. **main.tex:1147–1149** — after fixing Table 5.1's four rounding-step entries, rewrite this passage as confirmation rather than as a confession: `All twenty-four amplitudes reproduce to the precision reported in Table~\ref{tab: budget shapes}.` Retain the sentence about relative uncertainty at small amplitudes.
6. **main.tex:913** — `costs between 3.19 and 5.86\,yr` → `costs between 3.18 and 5.86\,yr`.
7. **main.tex:190 and 913** — `suppressed by three to five orders of magnitude` → `suppressed by roughly four orders of magnitude (median across catalog stars)`. Nothing in the thesis supports "three".
8. **main.tex:636** — `by 0.50 to 0.84\,yr, between 10 and 16\%` → `by 0.50 to 0.84\,yr, or 10 to 16\% of the uncorrected time`.
9. **main.tex:944–946** — add a source and disambiguate the two reference points: `Taking the median over catalog stars at the same reference plane, and measuring on the production run of Section~\ref{sec: tse}, the astrophysical background averages about 4300\,ph\,s$^{-1}$\,$\upmu$m$^{-1}$ across the band at null order two ... Near $10\,\upmu$m, where the band-integrated total is lower than its average, the local-zodiacal term supplies roughly 1760 of 2260 ...`

### Broken or misdirected references

10. **main.tex:550** — either add to Table 2.1 the row `Observing efficiency & 0.8 & Duty cycle; not applied to the returned time`, or change the sentence to `the observing efficiency of 0.8 configured in the AMS`.
11. **main.tex:548** — define or delete `experiment-limited mode`. Suggested: `In the experiment-limited mode used throughout---in which the scheduler runs until the experiment completes rather than until a fixed time budget is exhausted---the configured 0.8 observing efficiency neither caps nor rescales the returned time.`
12. **main.tex:915** — `The baseline prescription constant of Section \ref{sec: methods: AMS}` → `The habitable-zone-centre baseline prescription of Section \ref{sec: intro: signal collection}`.
13. **main.tex:1254** — delete the uncited Laugier entry, or cite it (the natural place is main.tex:503, alongside Guyon).
14. Throughout — insert non-breaking spaces before every `\ref`: `Figure~\ref{...}`, `Table~\ref{...}`, `Section~\ref{...}`, `Eq.~\ref{...}`. There are currently **zero** in the file; this is what split "Figure / 5.6" across PDF pp. 42–43.
15. Throughout — sort multi-citation lists so they print ascending: main.tex:326 (`[9, 2]`), 397 (`[9, 7]`), 402 (`[8, 2]`), 420, 284 (`[6, 4]`), 624.
16. Throughout — pick one of `Fig.`/`Figure` and one of `Eq.`/`Eqs.`/`Equations`. Currently mixed at main.tex:324/332, 501/624/861.

### Undefined terms

17. **main.tex:286** — after `the lower and upper ``hab2 stars'' extrapolation scenarios`, add: `(``hab2'' denotes the optimistic habitable-zone boundary definition of that occurrence model).`
18. **main.tex:569** — `near the Kennedy inner cutoff` → `near the inner radius at which the adopted Kennedy exozodiacal profile is truncated`.
19. **main.tex:511** — `the unit-exozodi response` → `the response to a one-zodi reference exozodiacal disk, which is rescaled per system`.
20. **main.tex:449** — `FoR $\pi/2$ retains the full sky` → `FoR $90^\circ$ retains the full sky` (main.tex:671 already uses degrees for the same quantity).

### Language and register

21. **British/American mixing** — the thesis is otherwise American (characterize, favorable, neighborhood, optimized, behavior). Fix: main.tex:229 `programme`→`program`, `neighbouring`→`neighboring`, `optimisation`→`optimization`, `optimises`→`optimizes`; main.tex:936 `programme`→`program`; main.tex:429, 628, 998 (×2) `modelling`→`modeling` (or change main.tex:402 to `modelling` — but pick one); main.tex:322, 402, 435 `centre`→`center` (or change main.tex:450).
22. **main.tex:204** — `For me, this scientific promise makes the practical definition of LIFE especially consequential.` → `This scientific promise makes the practical definition of LIFE's performance limits especially consequential.` (First person is out of register for the rest of the document, and "definition of LIFE" is ambiguous.)
23. **main.tex:206** — split the 45-word sentence: `What the reference studies do not provide is the inversion of that mapping. This thesis computes the wavelength-dependent \textit{iso-mission-time} boundary for a mechanism-independent aggregate random-noise term: the set of noise-budget amplitudes that all lead to the same required mission time.`
24. **main.tex:326** — split at the colon: `The symmetric backgrounds, being nearly axisymmetric, stay approximately constant under this rotation. Lay reports that the stellar and local-zodiacal geometric leakage rates are nominally independent of the array rotation angle and therefore appear at zero frequency; Dannert et al. state correspondingly that for rotationally symmetric sources the detected signal does not depend on the array rotation angle \cite{dannert2022life2,lay2004systematic}.`
25. **main.tex:452** — `We employ a practical science iso-performance approach.` → `We adopt an operational, science-referenced definition of instrument performance.`
26. **Symbol collision, $A$** — main.tex:367 (collecting area), main.tex:465 (additive modifier), main.tex:683 (budget amplitude). Rename the budget amplitude to $A_0$ or $\mathcal{A}$ in main.tex:444, 683–686, 748, 754, and Table 5.1's header. The area/amplitude clash is acute because Eq. 2.4 (`$AF_{p,i}n_i$`) and Eq. 5.1 (`$N_\mathrm{flat}=A$`) are both live in the same discussion.
27. **Symbol collision, $n$** — main.tex:477 (null order), main.tex:370 ($n_i$, planet-noise coefficient), main.tex:588 (number of noise terms), main.tex:532 ($n_\mathrm{orbits}$). At minimum change main.tex:588's summation limit from $n$ to $K$ and its index from $i$ to $k$ (since $i$ is the bin index everywhere else): `N_B(\lambda) = \sum_{k=1}^{K} N_k(\lambda) + N_I(\lambda)`.
28. **main.tex:284** — `Since planets are not known around most of them` → `Since planets are not known around most of these 4505 stars` (the antecedent is four sentences upstream, across an intervening digression about LIFE paper VI).
29. **main.tex:446** — delete `In addition to the variable ones, there are parameters termed \textit{agnostic}: global filters or overheads scanned without recomputing source physics, not quantities literally independent of every architecture.` and open with `The agnostic parameters are evaluated on simple grids:` — main.tex:427 and main.tex:429 already define the term twice.
30. **main.tex:634** — `median relative SNR shift of about 10.9\%` → `median relative SNR reduction of about 10.9\%` (sign is not otherwise recoverable).
31. **main.tex:552** — `gives approximately 95.6\% coverage for the population 90th percentile between the 84th and 96th order statistics` → `gives the interval between the 84th and 96th order statistics approximately 95.6\% coverage of the population 90th percentile`.
32. **main.tex:676** — `50,000` → `50\,000` (the thesis uses thin-space grouping elsewhere: 486\,244, 190\,077\,716).
33. **main.tex:671** — split this 330-word paragraph after `...not optimized requirements.` and add citations for the three unsourced LIFE baseline values: the $90^\circ$ working field of regard, the K-band limiting magnitude near 8, and the ~five-year mission duration. Only the 10 h slew currently carries a reference.
34. **main.tex:658** — split this 300-word paragraph after `...31 bins over 4--18.5\,$\upmu$m.`
35. **main.tex:915** — `Three boundaries limit how far this conclusion can be carried.` → `Two boundaries limit how far this conclusion can be carried, and a third potential objection can be settled outright.` As written the paragraph announces three limits and delivers two limits plus an answered question.
36. **main.tex:190** — `Final calculations compare three additive budget shapes` → `The production calculations compare three additive budget shapes`. More generally, `final` and `completed` appear as content-free intensifiers ~20 times (main.tex:206, 231, 252, 457, 671, 678, 706, 727, 818, 846, 853, 861, 939, 992, 1120, and in six float captions). Strike them; the reader assumes reported work is completed.
37. **Abstract, main.tex:188** — add one clause defining the programme, e.g. after the second sentence: `The observing programme is fixed throughout: detection and broadband characterization of 50 catalog planets in the habitable zones of Sun-like stars.` Without it, "mission time" has no referent for an abstract-only reader.
38. **main.tex:992** — restate the operating point in the Conclusion: `...at limiting magnitude 7, field of regard $65^\circ$, and 12\,h slew time, the nominal second-order null permits...`, and append two sentences on the throughput penalty (see B2).

### Layout and preamble

39. **main.tex:27** — add `\hypersetup{hidelinks}` (or `colorlinks=true` with muted colours) after `\usepackage{hyperref}`. Every citation and cross-reference currently prints inside a coloured box.
40. **main.tex:557** — change `\begin{table}[H]` to `[htbp]`. The `[H]` forces Table 3.2 past the bottom margin (caption collides with the footer on PDF p. 28) and leaves p. 29 with four lines.
41. **main.tex:60–67** — replace the over-constrained block with `\geometry{a4paper,margin=25mm}`. `total={8.5in,11in}` is a US-Letter page size being used as a body size on A4.
42. **main.tex:2–46** — duplicated `\usepackage` lines (`fancyhdr`, `lettrine`, `geometry`, `dcolumn`, `amsmath`) and several never-used packages (`circuitikz`, `pdfpages`, `csvsimple`, `wrapfig`, `rotating`, `xfrac`, `nicefrac`, `soul`). Source hygiene only; no rendered effect.
43. **main.tex:665** — move `Thus spatial image size is no longer a science parameter...` onto its own line after `\end{figure}` for source legibility.
44. **main.tex:105** — the centre header carries the full section title and collides with the left and right headers on Appendix B pages (PDF p. 58). Either shorten via an optional `\chapteropening` argument or drop `\leftmark` from `\chead`.
45. **main.tex:249** — remove the `\newpage` after Figure 2.1; it leaves the lower half of PDF p. 11 blank for no reason.
46. **main.tex:1181–1186** — the References page has no running header and no chapter-opening block, breaking the visual system used by every other top-level division. Give it a `\chapteropening`-style page or normalise the header.
47. **main.tex:733** — add `\cmidrule(lr){4-6}` under the spanned `Amplitude` header of Table 5.1 (same for Table B.2, main.tex:1154).
48. Consider adding a one-page **list of symbols** after the table of contents. With $A$, $n$, $N_i$/$N_I$, $s_i$/$n_i$, $x$, $\eta$/$\tau$, $b$/$r$, $\vartheta$/$\varphi$/$\phi$/$\psi$ all in play, and three of them reused, this would remove several of the stalls listed above at low cost.

---

## Suggested block grade

### **5.0** (good, with certain flaws) — a strong 5.0, half a step below 5.25.

**Justification.** On the two sub-questions that carry the most weight in this block — is the
structure logical, and have the central questions been answered — this thesis performs at the
top of the range. The causal chain from science goal to engineering allowance is stated up
front and actually followed; each section closes with a bridge into the next; the research
questions are asked once and closed once, in order, with one of them honestly declared only
half answered and the reason given. The discipline about what the work *is not* (Table 3.1,
Table 6.1, main.tex:252, 279, 501, 592, 678, 748, 863) is better than I usually see at MSc
level, and Section 5.7 — charging the proxy a cost the proxy does not represent, and then
reporting that it destroys the headline result — is intellectually honest work that many
authors would have quietly omitted.

What holds the grade at 5.0 rather than 5.5 is that the document contradicts itself on the
record in three places (640 vs 650 on one page; 60 vs 65 vs 62.2 across five; a residual span
refuted by the table on the facing page), renders its central results figure at a size where
the panels cannot be told apart and labels those panels with terms that invert the caption's
meaning, and drops its most consequential finding from the Conclusion. With no defense
available, a reader who trips on any one of these has no recourse. Two further cross-references
point at content that is not there (Table 2.1's observing efficiency, Section 3.3's baseline
constant). The layout is competent but unfinished: boxed hyperlinks throughout, a caption
overrunning a footer, six pages more than half white.

None of these is a defect of thinking. All of them are defects of the last pass.

**What would raise it to 5.5.** Everything needed is mechanical and could be done in a day:

1. Fix the four numerical contradictions (fixes 1–8) and propagate one Hab2Min value into the
   abstract, Table 4.1, Table 5.1, the Discussion and the Conclusion.
2. Re-lay Figures 5.1 and 5.2 at a legible size and regenerate the panel titles so they read
   "Flat / Short-weighted / Long-weighted" instead of "No / Long-Short / Short-Long Gradient".
3. Add two sentences on the throughput penalty to the Conclusion, and restate the operating
   point there.
4. Repair the two misdirected cross-references and add the missing Table 2.1 row.
5. Re-caption Figure 5.6 so both axes, the zone of avoidance, and the 26.7% are defined.
6. `\hypersetup{hidelinks}`, `[H]`→`[htbp]` on Table 3.2, non-breaking spaces before every
   `\ref`, delete the uncited Laugier entry, normalise British/American spelling.

Doing items 1–3 alone would move sub-questions 2 and 4 up a step and take the block to 5.25.
Doing all six would make it a defensible 5.5. A 6.0 would additionally require resolving the
$A$/$n$ symbol collisions, a symbol list, and the paragraph-length surgery of fixes 33–34.
