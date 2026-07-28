# Grading round 3 — synthesis and verification

Three independent examiners graded the rewritten thesis against the ETH sheet.
Each read only the thesis; none saw the prior rounds, the checklist, the
handover, or git history, and none was told a target grade.

| Block | Grade | Examiner profile |
|---|---|---|
| Independent scientific thinking / originality | **5.00** | LIFE specialist |
| General scientific competence | **5.25** | LIFE specialist |
| Logical coherence and presentation | **5.25** | writing expert, undergraduate physics only |

Methodological Competence and Work Process are not judgeable from a thesis and
were skipped, as in the earlier rounds.

## The one finding that changes a conclusion

**The six-aperture design is run with the field of view of a 4 m collector while
being charged the collecting area of six 3.266 m ones. Correcting it reverses
the headline result.**

`instrument.py:92-105` derives both quantities from the same option:

```
telescope_area = num_apertures * pi * (diameter/2)^2
hfov           = wl / (2 * diameter)
```

and `settings.yaml` pins `num_apertures: 4, diameter: 4.0` for every run.
Nothing in `ablation_throughput.py` or `combiner.py` changes either. So the
six-aperture run inherits the reference's total area -- which is what "equal
total collecting area" is supposed to mean, and it is satisfied -- but also
inherits the reference's *per-collector beam*, which under that same convention
should be 1.2247x wider in angle and 1.5x in solid angle. Local zodiacal light
is a uniform foreground, so its collected rate scales with that solid angle, and
by the thesis's own Section 6.1 it is the dominant fourth-order background term.

Measured, Hab2Max, zero budget:

| Configuration | Area | hfov at 10 um | Mission time | vs reference |
|---|---|---|---|---|
| Reference double Bracewell, 4 x 4.000 m | 50.265 m^2 | 257.8 mas | 5.3193 yr | -- |
| Triple nuller **as published** | 50.265 m^2 | 257.8 mas | 4.9800 yr | **-6.38 %** |
| Triple nuller, 6 x 3.266 m, equal total area | 50.265 m^2 | 315.8 mas | 6.1823 yr | **+16.22 %** |
| Triple nuller, 6 x 4.000 m, equal per-aperture diameter | 75.398 m^2 | 257.8 mas | 3.7191 yr | -30.08 % |

The first two rows reproduce the thesis (5.3187 and 4.9800 yr) to the search
tolerance, so this is the same calculation, not a different one.

The published configuration is neither self-consistent convention. It takes the
area of the equal-area comparison and the field of view of the larger-collector
comparison. Both defensible conventions exist -- equal total area at +16.2 %, or
equal per-aperture diameter at -30.1 % but with 1.5x the collecting area and so
not an equal-area claim -- and the published -6.4 % is between them and is
neither. The abstract's "at equal collecting area a six-aperture fourth-order
design completes the programme about six percent sooner" does not survive.

Reproduce: `scratchpad/fov_test.py` (three cases, about a minute).

### What this does and does not touch

Affected: the mission-time advantage, the fourth-order amplitudes of Table 5.1
and Table B.2, and every fourth-order operating-point scan, since all were run
in this configuration.

Probably not affected, but **must be rechecked rather than assumed**: the
spectral reversal. A wider field of view raises the local-zodiacal term, which
rises toward long wavelengths, and that is the term the long-weighted family
hides noise beneath -- so the reversal plausibly strengthens. Unverified.

Not affected: the analytic background reduction and its validation, the
local-zodiacal normalisation correction, the amplification result, the speedup,
the chopping/aperture-count argument, and the whole second-order half.

## Section 6.1 quotes proxy numbers for the realizable design

Confirmed independently. `run_background_context` (`ablation_throughput.py:299`)
constructs the AMS **without an `architecture=` argument**, so its order-four
rows come from the `sin^4` null-order proxy, not the combiner.

Measured far-field rotation average per deep output:

| Response | far-field <T> | ratio to order two |
|---|---|---|
| Double Bracewell | 0.2500 = 1/4 | -- |
| Triple nuller (realizable) | 0.1666 = **1/6** | **0.6667** |
| sin^4 proxy | 0.1875 = 3/16 | 0.7500 |

The tabulated local-zodiacal ratio is 0.75000 exactly, which identifies the
table as the proxy. Section 6.1 states 0.7500 and "the ratio 3/16 to 1/4",
contradicting Section 5.6, which quotes 1/4 and 1/6 for the actual designs.

The same section then says the fourth-order allowances are "about a quarter of
the reduced background, which is a far more comfortable one". That holds only
with the proxy allowance of 641; with the thesis's own realizable 138 the figure
is about 6 %, comparable to order two's 3 % and not comfortable. This is
leftover proxy text that survived the rewrite, and it breaches the boundary the
thesis itself draws two pages earlier.

## Presentation defects, all verified

- **Duplicated paragraph**, `main.tex` 991 and 993, near-identical and
  contradictory: "months of computer time" against "years". Months is correct
  from the thesis's own Section 6.3 figures.
- **Symbol collision.** `x` is `pi*b*theta/lambda` at Eq. 3.5 and `2*pi*b*R/lambda`
  in Section 4.2 and Appendix A.2 -- different argument *and* a factor of two.
  The physics is right (`x^4/256` over `x^2/32` is `x^2/8`); the notation is not.
- **Table 3.2 overruns its page**: `Overfull \vbox (111.59 pt too high)`. The
  caption collides with the footer and its closing caveat is clipped out of the
  printed document. Compile checks were passing because they counted errors and
  undefined references, not overfull boxes.
- Rounding inconsistency: the same allowance appears as 140, 142 and 142.4, and
  as 65, 62 and 62.2, across Table 5.1, Table 5.2 and Table B.2. Appendix B.3
  flags it but no table is corrected.

One presentation claim did **not** hold: the abstract does not quote 65 as an
allowance; that "65" is the field of regard.

## Unsourced but correct

Section 6.4's "a factor of several" and "some fifteen degrees" check out against
the retained proxy figures: the idealised feasibility edge is near 47 degrees
against the realizable 61, and the flat allowance 641 against 138 is 4.6x.
Correct, but the figures supporting them were removed in the rewrite, so a
reader cannot verify either. Cheap to fix by stating the numbers.

## Examiner-identified items not independently verified here

Raised by the scientific-competence examiner, plausible, not yet checked by me:
the "6e-12" agreement attached to a background response that reportedly agrees
only to ~2e-5; the four-aperture chopping argument reportedly failing for a
collinear array with measured orders 4.000 and 6.000; Appendix B.3's 6.8 % and
11.9 % computed against rounded Table 5.1 values rather than Table B.2; and the
order-two integral-neutral margins sitting inside their own tolerance. The
literature gap -- no Bracewell 1978, no Angel & Woolf 1997 despite both
architectures being studied by name -- is easy to confirm and easy to fix.
