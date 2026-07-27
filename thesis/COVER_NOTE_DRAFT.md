# Cover note draft — to send with main_diff.pdf

Draft in your voice; edit freely. The ordering is deliberate: the changelog comes
first because the last results you presented were already outdated, so without it
the new numbers get read against a stale prior.

---

Dear <supervisor>,

Attached is the current draft with changes marked against the version you read on
10 July.

**Where the numbers stand relative to the presentation.** The results you saw
predate the analytic background rewrite, so the headline amplitudes have moved.
The current values are in Table 5.1, and Appendix B.3 now reproduces the whole
table from a committed code state so the numbers can be checked independently.
Twenty of the twenty-four amplitudes reproduce to the precision reported; four
differ by a single rounding step, which is the search tolerance rather than a
disagreement. I also now record the mission time each reported amplitude actually
delivers, since the search stops within 0.05 yr of the target and the amplitude
belongs to the achieved time rather than the nominal one.

**The main new result is in Section 5.7.** The null-order proxy holds optical
throughput fixed between orders, which flatters order four: a realizable
four-aperture fourth-order combiner delivers the deep null on a quarter of the
collected light against a half for the second-order arrangement (Guyon et al.
2013). Charging that penalty removes every admissible allowance at every target
studied. The zero-budget mission time alone rises to 7.65 yr for Hab2Max and
10.79 yr for Hab2Min, so no target is reachable before any noise is added at all.
A throughput sweep puts this on a curve: required time scales sub-linearly in
1/throughput, with a slew-dominated fraction of 17-29% that does not scale, and
the cost of halving efficiency exceeds the benefit of the deeper null by three to
five times. The practical reading is the opposite of what the raw order-four
column suggests.

**Other substantive changes.**

- A "Relation to Prior Work" subsection now states what is inherited and what is
  new. In particular the aggregate instrumental noise term is no longer claimed
  as novel, since your Section 3.4.2 already defines one; what is new is the
  iso-mission-time inversion.
- Mission time is now defined explicitly as charged time, integration plus slew.
  The configured 0.8 observing efficiency is inert in experiment-limited mode, so
  a 5.5 yr target corresponds to roughly 6.9 yr elapsed at that duty cycle.
- The validation matrix now includes the exozodiacal checks that came out worst,
  with their attribution to reference-grid aliasing near the Kennedy inner
  cutoff, and Section 4.2 reports the 10.9% median full-catalog SNR shift caused
  by the local-zodiacal correction.
- The local-zodiacal defect is now stated as inherited upstream code rather than
  something introduced here, with the taper-branch inconsistency given as the
  evidence.
- Section 4.2 shows the spectral-resolution trade behind the choice of R = 20.
- Figure 4.1 previously used a plot generated before the physics change; it now
  uses the current one.

**Still to come before submission.**

- Propagating the local-zodiacal correction into a published yield number, rather
  than only reporting its effect on SNR.
- A fidelity assessment for the aggregate-N_I reduction itself, which is
  currently argued rather than measured.
- Repeating the penalized search at targets beyond 7.65 and 10.79 yr, to see
  whether the spectral reversal survives the throughput penalty.
- Final language pass and the declaration of originality.

**Three questions.**

1. Is halving the efficiency the right control for the null-order comparison, or
   would you prefer the order-four case normalized a different way?
2. Is the mission-time reading correct, that the returned quantity is integration
   plus slew with the observing efficiency inert? Everything downstream depends
   on it.
3. Do you want the local-zodiacal correction traced through to a published yield
   number? It affects results computed through the default tapered path, and I
   have not attempted to quantify that beyond the SNR shift.

Best regards,
Nicolas
