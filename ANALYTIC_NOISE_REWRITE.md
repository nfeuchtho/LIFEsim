# Analytic (grid-free) astrophysical noise rewrite

Status: **implemented, self-consistent, supervisor-approved (2026-07).** The old
grid-based code is preserved in two places: the `.bak`/`.new` pairs under
`code_review_backups/` (not `.bak` files sitting next to the sources, as section 8
originally described), and -- more reliably -- commit `2fd5142` in the project
repository, which is the pre-rewrite state. The rewrite itself is commit `93dde44`.
Since git now holds both states, the backup directory is redundant and is excluded
from version control.

This document is written to (a) brief the supervisor on what changed and why, and
(b) let a future session (or a different person) pick this up cold.

## 1. Origin / motivation

Supervisor's original question: for a given source spectrum (planet BB, star BB,
exozodi BB), LIFEsim samples the transmission map at the *center wavelength* of each
spectral bin rather than integrating transmission x spectrum over the bin. Could this
be done analytically (e.g. with sympy)?

Conclusion reached before any code was touched: **no** — the transmission map is a
trig function of `1/wavelength` (`sin(2*pi*L*alpha/wl)`-type terms) and the source
spectrum is a Planck function with no closed-form antiderivative. Product of the two
has no clean analytic wavelength integral; a few-point Gauss-Legendre quadrature per
bin would work but is *more* expensive than the current single-point sample, not less
(the whole spatial grid has to be re-evaluated at each extra wavelength node, since the
transmission map depends on wavelength through the same term that's being integrated).

This led to a different question, which turned out to be much more productive:
**is the spatial (`image_size` x `image_size` pixel grid) integration used for the
astrophysical noise sources (star leakage, local zodi, exozodi) itself avoidable?**
The answer is yes, analytically, for all three -- this document is about that work.

## 2. The core mathematical result

Star leakage, local-zodi and exozodi noise are all computed as an integral of a
transmission map `tm3(alpha, beta)` against a **circularly symmetric** source
distribution (uniform stellar disk, uniform local-zodi flux across the tiny
instrument FoV, or the radially-symmetric Kennedy+2015 exozodi disk profile) over a
2D pixel grid of size `image_size x image_size`.

Physical fact established with the user: the LIFE array **rotates**, and the
noise terms are meant to represent the rotation-averaged (azimuthally-averaged)
transmission. For a circularly symmetric source, azimuthally averaging the
transmission map is mathematically equivalent to evaluating a single static snapshot
and integrating over the source's radial coordinate -- i.e. the existing single-snapshot
grid sum was already implicitly computing something close to the rotation average, just
via brute-force 2D pixel summation.

**Framing check against the literature (verified against Lay 2004 and LIFE paper II,
Dannert et al. 2022):** the papers do not describe this as "rotation averaging" the
noise. Lay (2004), Sec. 4, states that the stellar and local-zodi geometric leakage
photon rates are "nominally independent of the array rotation angle" and therefore
appear as a DC (zero-frequency) term -- i.e. rotation's stated purpose in these papers
is to *modulate the planet signal* for chopping/lock-in extraction, not to average down
the background noise. The noise terms are rotation-*invariant by construction*, given
an assumption of circular source symmetry -- not rotation-*averaged* as a physical
process. Dannert et al. (2022), Sec. 2.2.3/2.3, make the same point explicitly: "if
only rotationally symmetric sources ... are considered, the detected signal does not
depend on the rotation angle of the array," and their own noise calculation is a static
single-snapshot 2D grid integral over the full FoV -- exactly what the old LIFEsim code
did.

The mathematical identity used in this rewrite still holds: a full-rotation azimuthal
average of a circularly symmetric map integrates to the same value as a single static
snapshot integrated over radius (same integral, relabeled variable) -- so the closed-form
results in this document are numerically correct. But the physical justification should
be stated as the papers state it: these noise terms are rotation-angle-*independent*
because the assumed source geometry (uniform stellar disk, uniform local zodi, and --
importantly -- a *homogeneous, face-on* exozodi disk) is circularly symmetric, not
because rotation itself performs an averaging operation on an otherwise
angle-dependent quantity.

**Caveat for an inclined/asymmetric exozodi model (see also section 13, item 5):** Lay
(2004) treats the exozodi disk generally as *elliptical/inclined*, and shows this
produces genuine even-harmonic modulation with rotation angle -- it only reduces to a
DC (rotation-invariant) term under the added assumption of central symmetry. LIFE
paper II adopts that symmetric-disk assumption as its **default** model, and this
rewrite inherits the same assumption (via the Kennedy et al. 2015 radially-symmetric
profile). If a future version of LIFEsim/AMS supports inclined or otherwise
non-axisymmetric exozodi disks, the closed-form/quadrature approach in this document
does **not** carry over -- the harmonic terms that vanish under the symmetry assumption
would no longer cancel, and the full 2D (or at least 2D-reduced, angle-resolved)
transmission integral would be needed again for that source term specifically.

`tm3 = sin(2*pi*L*alpha/wl)^2 * cos(2*ratio*pi*L*beta/wl - pi/4)^2`, with
`alpha = r*cos(theta)`, `beta = r*sin(theta)`, `L = baseline/2`.

Expanding via the Jacobi-Anger identity and averaging over `theta` (full rotation),
all oscillatory harmonics vanish and only the DC term survives:

```
<tm3>_theta(r) = <tm4>_theta(r) = 1/4 * (1 - J0(4*pi*L*r/wl))
```

(independent of `ratio` and of the +-pi/4 chop phase -- confirmed numerically against
a brute 2D grid to 0.03% at finite grid resolution, converging further with resolution).

For a **uniform disk** of radius `R` (no FoV taper), the radial integral of this has a
further closed form (using `d/dr[r*J1(kr)] = k*r*J0(kr)`):

```
<tm3>_disk(R) = 1/4 * (1 - 2*J1(kR)/(kR)),   k = 4*pi*L/wl = 2*pi*baseline/wl
```

This is now implemented once, in `lifesim/util/transmission_analytic.py`:
- `azimuthal_average_tm(r, bl, wl_bins)` -- the pointwise formula above.
- `disk_average_tm(R, bl, wl_bins)` -- the closed-form uniform-disk average (used for
  the `fov_taper='none'` case: exact, zero grid, zero quadrature).
- `radial_average_tm(R, bl, wl_bins, hfov, fov_taper, n_r=200)` -- for
  `fov_taper='gaussian'`, the taper factor `exp(-(pi/(4*hfov)*r)^2)` is itself a
  function of `r` only, so it factors into the same azimuthal average; the disk
  integral is then done with a 200-point radial quadrature (`r = u*R` substitution,
  `u` uniform on `[0,1]`) rather than a closed form. Verified converged to <0.01%
  against a 20000-point quadrature even at the largest baseline/wavelength ratio in
  the array's design range (`kR ~ 215`).

For exozodi, the Kennedy+2015 surface density/temperature profile depends only on `r`
(radially symmetric) too, but is **not** uniform -- it's a power law diverging toward
the inner cutoff `r_in`. This is handled with a **log-spaced** radial substitution
(`r = r_in * (R/r_in)^u`, `u` uniform on `[0,1]`) rather than a linear one; see
section 4 for why the linear version was insufficient.

### Net effect
`image_size x image_size` (up to 1600x1600 in convergence tests, 100 in production
default) pixel evaluations per star per noise term collapse to either an O(1) closed
form or a ~200-point 1D quadrature. This is the source of the ~5x measured overall
speedup (the SNR calculation also includes the planet-signal term, which was already
grid-free before this work, and per-planet catalog bookkeeping, which this change
doesn't touch -- so 5x is the *net* speedup on the whole `get_snr` call, not the noise
term in isolation, which is faster than 5x on its own).

## 3. Is a circular FoV physically consistent, given the detector is square?

Question raised during review: the sky-plane field of view is treated as circular
(disk-domain averaging) -- but real detectors are square/rectangular arrays of
pixels. Isn't that a geometry mismatch?

No -- because the circular FoV and the square detector are **two different stages of
the signal chain** and were never the same object, even before this rewrite:

- **Sky-plane coupling efficiency** (what `image_size`/the transmission-map grid
  represents): per the paper (Dannert et al. 2022), "the effective field-of-view is
  assumed to be FoV=lambda/D **in diameter** as we assume the light will be coupled
  into **single-mode fibers**." A single-mode fiber has one spatial mode; its angular
  coupling-efficiency profile (how much of an off-axis source's flux gets injected) is
  intrinsically circularly symmetric (roughly Gaussian for a step-index fiber -- this
  is exactly where the `fov_taper='gaussian'` model comes from). This spatial
  filtering happens *before* any detector. There is no square pixel array at this
  stage of the signal chain; `image_size` was always a **numerical grid** used to
  discretize this sky-plane integral, never a model of real hardware.
- **The real detector** (`options.array['pixel_size'] = 23e-6` m,
  `options.array['pix_per_wl'] = 2.2`, used only in `pn_thermal.py` /
  `en_darkcurrent.py`): this is the spectrometer detector that records the
  *dispersed spectrum* after the single-mode-fiber output, i.e. a 1D wavelength axis
  (with some cross-dispersion), not a 2D sky image. It has its own real pixel size in
  meters and is completely independent of `image_size` (which has no units/physical
  size at all -- confirmed in `options.py`, these are two disjoint parameter
  families). This detector's noise contributions (thermal, dark current) were never
  touched by this rewrite and never depended on `image_size`/`radius_map` in the
  first place (verified in section 6, "Explicitly NOT changed").

So: the old code's `image_size x image_size` **square** pixel grid was itself just a
Cartesian numerical-integration mesh for a physically circular quantity (the
fiber-coupling efficiency vs sky position) -- an implementation detail, not a second
physical detector. Switching that mesh to an exact disk-domain analytic average
doesn't introduce a geometry mismatch; if anything it removes one (the old square
*grid*, not a square *detector*, was the artifact -- see the local-zodi bug below,
which is a direct consequence of this square-grid-vs-circular-model mismatch).

## 4. The local-zodi normalization bug (found during validation, NOT introduced by this rewrite)

While validating the analytic rewrite against the existing grid code, star leakage and
exozodi converged cleanly toward the analytic value as grid resolution increased (see
section 6). Local-zodi did not -- it disagreed by a **constant factor of ~1.268
regardless of grid resolution**, i.e. not a discretization effect.

Root cause: the old local-zodi formula is

```python
lz_flux = lz_flux_sr * (pi * image_angle**2)          # assumes a CIRCULAR aperture
lz_leak = (ap * t_map).sum() / ap.sum() * lz_flux * area   # ap.sum() is a SQUARE pixel count
```

Under `fov_taper='gaussian'` (the default), `ap = ones_like(...)` covers the *entire
square* pixel grid, so `ap.sum()` is the pixel count of a `2*image_angle` side square
(area `4*image_angle^2`), not a circle (area `pi*image_angle^2`). The `lz_flux`
prefactor assumes the latter. This silently multiplies the whole term by
`(pi*image_angle^2) / (4*image_angle^2) = pi/4 ~ 0.785` relative to a
domain-consistent calculation -- i.e. local-zodi noise was being **under-computed by
about `4/pi ~ 1.273x`** (confirmed numerically: measured ratio 1.268, converging
toward the exact geometric value 1.2732 as grid resolution -> infinity; residual gap
is old-grid discretization noise).

This bug is **independent of the AMS/image_size work** -- it is a latent unit/area
convention mismatch present in the original (pre-AMS, presumably pre-existing since
before this repository's LIFEsim fork) local-zodi implementation. It was only
*exposed* now because switching to a domain-consistent analytic formula removes the
accidental suppression.

Checked against the original LIFEsim methods paper (Dannert et al. 2022, LIFE paper
II, arXiv:2203.00471): the effective field of view is explicitly described as
**"FoV = lambda/D in diameter"**, integrated via solid angle `dOmega` over "the
complete field-of-view" -- i.e. the paper's own model is a **circular** FoV, not a
square pixel grid. So the domain-consistent (disk-based) formula used in this rewrite
matches the published model; the old code's square-grid-under-gaussian-taper behavior
was itself the deviation from the paper.

**Confirmed, not just plausible -- independently re-derived directly against the
paper.** Dannert et al. (2022), Eq. 17 (p.6; identical to F. Dannert's own thesis,
Eq. 3.17, p.62), gives the noise flux as the continuous solid-angle integral
`S(lambda) = Integral[ Tm(theta,lambda) * I(theta,lambda) * t * A * eta ] dOmega`, with
the lambda/D-diameter FoV justified by single-mode-fiber coupling -- a fiber mode's
angular coupling-efficiency profile is intrinsically azimuthally symmetric (Gaussian
for a step-index fiber), so there is no physical basis for a *square* collection domain
anywhere in the paper's model. The paper's only implementation remark ("integrated over
a two-dimensional artificial image covering the full field-of-view") describes how the
old code *discretized* the integral, not a claim that the true aperture is square.

The strongest evidence this is a genuine implementation bug rather than an intentional
convention: **the old code is internally inconsistent with itself.** Its own
`fov_taper='none'` branch masks `ap` to a circular disk, exactly matching the
`pi*image_angle**2` prefactor (self-consistent). Only the `fov_taper='gaussian'` branch
(LIFEsim's *default* setting) drops that mask in favor of the full square grid, breaking
the same self-consistency the other branch maintains. If a square domain were the
intended convention, the `'none'` branch would use one too -- it doesn't. This
independently confirms the ~pi/4 (`4/pi ~ 1.273x`) mismatch is a bug local to the
`'gaussian'`-taper code path, not a deliberate modeling choice.

**This is flagged for supervisor sign-off before being treated as final** -- it
changes local-zodi noise (and hence total noise/SNR, since local-zodi dominates at
longer wavelengths) by a non-trivial ~27%. Star leakage and exozodi do not have this
bug (their old-code domains were already consistent circular disks).

## 5. The exozodi log-spacing bug (introduced by this rewrite, found and fixed during validation)

The Kennedy+2015 exozodi profile has `temp ~ r^-0.5`, `sigma ~ r^-0.34`, diverging
toward the inner cutoff `r_in`. The first implementation used a **uniform-in-r**
quadrature (`r = r_in + u*(R - r_in)`, `u` uniform), which badly undersamples that
steep near-`r_in` region whenever `r_in` is small relative to the FoV -- common for
low-luminosity stars. This caused errors up to **35%** for some stars in a 25-star
random sample (found via `debug_multi_star_convergence.py`, not caught by the initial
single-star check).

Fix: log-spaced radial samples, `r = r_in * (R/r_in)^u` with `u` uniform on `[0,1]`
(implemented in `pn_exozodi.py` / `ams.py`'s exozodi block). Verified:
- n_r=200 (current setting) reproduces a 500000-point reference to 5 significant
  figures for the worst case found.
- Re-ran the 25-star convergence check after the fix: worst-case exozodi deviation
  dropped from 35% to ~1-3%, consistent with the *old grid's own* known aliasing
  behavior (see `[[project_convergence_params]]` memory: `image_size=100` is a known
  aliasing trap; old-grid-vs-analytic deviation was non-monotonic with increasing old
  grid resolution -- 2.78% at IS=800, 1.68% at IS=1600, 1.76% at IS=3200 -- confirming
  the *old grid* is the noisy reference here, not the new analytic code, which was
  separately confirmed converged in its own right (n_r=200 vs n_r=2000 agree to
  0.001%).

## 6. Validation performed

- **Single-star, multi-resolution convergence** (`debug_analytic_noise.py`): old grid
  at IS = 100/200/400/800/1600 compared against the fixed analytic value for one star;
  star+localzodi combined error shrinks monotonically with grid resolution (down to
  ~0.9%) *before* the localzodi bug was understood -- this is what first flagged
  "something's off" and led to isolating the localzodi issue via per-component
  comparison.
- **Multi-star convergence** (`debug_multi_star_convergence.py`, 25 randomly sampled
  stars spanning the baseline/luminosity/distance range): confirmed after fixes,
  worst-case star-leak deviation 0.5%, worst-case exozodi deviation ~1-3% (both taper
  models: `'gaussian'` and `'none'`), no NaN/negative values anywhere in the sample.
- **Quadrature self-convergence**: `radial_average_tm`'s n_r=200 checked against
  n_r=20000 at the worst-case (largest baseline/wavelength) `kR ~ 215` -- agrees to
  <0.01%. Exozodi's log-spaced n_r=200 checked against n_r=2000 -- agrees to 0.001%.
- **Full-catalog smoke test** (`verify_snr.py`, 729,925 planets from
  `catalog_hab2hi.txt`): after porting the fix to both `instrument.py` and `ams.py`,
  the two independent code paths (Instrument.get_snr vs AgnosticMissionSimulator.get_snr)
  agree **exactly** (0.000 max/median relative difference) across the full catalog --
  expected, since they now share the same closed-form/quadrature formulas, and confirms
  the AMS port was done correctly (bit-identical to the validated Instrument path).
- Before the AMS port, the same full-catalog comparison (Instrument, fixed, vs AMS,
  still old code) showed the expected ~10.9% median deviation, entirely attributable
  to the known localzodi bug in the still-unfixed AMS path -- consistent with section 4.

## 7. Files changed

- `lifesim/util/transmission_analytic.py` **(new)** -- shared analytic helpers
  (`azimuthal_average_tm`, `disk_average_tm`, `radial_average_tm`, and, added later for the
  wavelength-bin fix in section 9, `gauss_legendre_wavenumber`).
- `lifesim/instrument/pn_star.py` -- stellar leakage: grid + socket call removed,
  replaced with `radial_average_tm`. Later (section 9) the center-wl-point sample was
  replaced with `gauss_legendre_wavenumber`-based bin integration.
- `lifesim/instrument/pn_localzodi.py` -- local-zodi: grid removed, replaced with
  `radial_average_tm` (this is where the normalization bug was found/fixed). Not touched
  by the section 9 wl-quadrature fix (no chirp there -- see section 9).
- `lifesim/instrument/pn_exozodi.py` -- exozodi: grid removed, replaced with a
  log-spaced 1D radial integral. Includes a guard for the (not observed in the
  current catalog, but possible in principle) case `r_in > image_angle`. Later
  (section 9) wrapped in a `gauss_legendre_wavenumber` loop over wl bins.
- `lifesim/instrument/instrument.py` -- removed the three now-unnecessary
  `transmission_map()` (t_map) calls that fed the old noise grids (per-star loop in
  `get_snr_single_processing`, and two occurrences in `get_spectrum`-family methods).
  `apply_options()` still computes `rad_pix`/`mas_pix`/`radius_map` (needed by
  `ams.py`'s pre-port code initially, kept since nothing besides the now-removed
  consumers needed removing them, and the plotting/GUI transmission-map path may still
  reference them via `data.inst`).
- `lifesim/ams/core/ams.py` -- same rewrite ported into
  `AgnosticMissionSimulator.get_snr`'s per-star physics block. Also added an explicit
  `NotImplementedError` guard: **the analytic rotation-average formula was derived
  specifically for `nulling_order=2`** (double Bracewell); if `nulling_order != 2` is
  ever configured, the old code would have silently used the wrong (but at least
  self-consistent) grid math, whereas the new code raises loudly instead of silently
  computing wrong physics. In practice `nulling_order=2` is the only value used
  anywhere in this codebase/its tests as far as could be found. Later (section 9) the
  stellar-leakage and exozodi blocks were wrapped in the same `gauss_legendre_wavenumber`
  loop, with nodes/weights/hfov/image_angle-per-node hoisted out of the per-star loop
  since bin edges are instrument-wide, not per-star.

### Explicitly NOT changed
- Thermal (OTA/instrument/detector-housing) and dark-current noise
  (`pn_thermal.py`, `en_darkcurrent.py`) -- verified these never referenced
  `image_size`/`radius_map`/pixel grids at all; they're pure per-wavelength-bin
  analytic formulas, untouched and unaffected.
- Planet signal/noise transmission efficiency -- was already grid-free (phi-angle
  spline lookup table) in both `instrument.py` and `ams.py` before this work.
- `transmission.py`'s `transmission_map()` method itself (still supports building an
  actual `image_size x image_size` pixel image) -- left alone on purpose, since it's
  used for visualization/GUI plotting (`gen_transmission_fig.py`, `spectrum_gui.py`),
  where you genuinely need a rendered 2D image. Not a noise-computation path.
- The `image_size` option itself (`options.py`/`settings.yaml`) -- still exists,
  still used by the visualization path above. Only purged from the noise-integral
  code, not from the options schema.

## 8. Backups (do not delete before supervisor sign-off)

`lifesim/instrument/*.bak` -- pristine pre-rewrite originals (transmission.py,
pn_star.py, pn_localzodi.py, pn_exozodi.py, instrument.py), taken before any edits
this session. `lifesim/instrument/*.new` -- snapshots of the rewritten versions taken
mid-session for a controlled before/after comparison; effectively redundant with the
current live files now but harmless to keep alongside `.bak` until cleanup is
approved.

Debug/validation scripts (new, untracked, safe to keep or delete independent of the
`.bak` question): `lifesim/analysis/test_scripts/debug_analytic_noise.py`,
`lifesim/analysis/test_scripts/debug_multi_star_convergence.py`,
`lifesim/analysis/test_scripts/validate_wl_quadrature.py` (section 9).

## 9. Wavelength-bin integration (added after section 1, once transmission was cheap)

Section 1 established that a per-bin quadrature over wavelength (rather than sampling the
bin-center wl only) was analytically intractable and, at the time, *too expensive* to bother
with -- extra wl nodes meant re-evaluating the full 2D transmission grid. That objection no
longer holds: after the rewrite above, the transmission terms are O(1) closed forms or a cheap
200-point radial quadrature, so extra wl nodes per bin are nearly free.

**Root cause of the center-point error:** `tm(wl) * planck(wl)` is a *chirp* in wl wherever the
relevant transmission argument is `k*r = 2*pi*bl*r/wl` with `r` a **physical size that does not
itself scale with wl** (instantaneous frequency `~ bl*r/wl**2` grows toward short wl). This is
true for:
- the stellar disk radius `Rs_rad` (pn_star.py/ams.py stellar-leakage term), and
- the exozodi's Kennedy2015 inner cutoff `r_in` (pn_exozodi.py/ams.py exozodi term, `r_in` is a
  fixed AU converted to a fixed angular radius via distance).

It is **not** true for local-zodi: there, the transmission is averaged over the disk
`R = image_angle(wl)`, and both `image_angle` and `hfov` scale linearly with wl (by
construction, `hfov = wl/(2D)`), so `k*R` and the gaussian-taper argument are wl-*independent*
identically -- no chirp, no fix needed. `pn_localzodi.py` was left untouched.

**Fix:** `transmission_analytic.gauss_legendre_wavenumber(wl_lo, wl_hi, n=8)` -- Gauss-Legendre
quadrature in wavenumber `u = 1/wl` instead of wl. In `u`, `k*r = 2*pi*bl*r*u` is
constant-frequency (no chirp), so a fixed low-order rule stays accurate across the whole band
regardless of baseline/separation, unlike a naive linear-in-wl rule. Wired into
`pn_star.py`/`pn_exozodi.py` and mirrored in `ams.py`'s per-star physics block (same node/weight
computation hoisted out of the per-star loop since bin edges are instrument-wide, not per-star).

**Validation** (`validate_wl_quadrature.py`): n=8 quadrature matches an n=64 reference to
~1e-13 (machine precision) for both star-leak and exozodi, across `spec_res` in {5,10,20,50} and
25 random stars. The old center-point sampling error (relative to the n=64 reference) is real
but modest at the default `spec_res=20`: <=0.3% star-leak, <=0.03% exozodi even at the worst
`kr_in` found across the full catalog (~2.4, star `distance_s=1.35pc, l_sun=1.65`); it grows to
a few percent only at deliberately coarse `spec_res=5`. Not a landmine like the local-zodi bug --
a real, essentially-free correction, not a large physics finding on its own.

Full-catalog AMS-vs-Instrument bit-identity check (`validate_ams_snr.py`, 2000-star subsample)
re-run after porting to `ams.py`: max relative SNR difference 4.2e-16 (machine precision) --
confirms the port didn't diverge from the `Instrument` path.

## 10. AMS delegates noise physics to the instrument's own modules (deduplication)

`ams.py` used to carry its own full copy of the stellar-leakage/local-zodi/exozodi physics,
kept manually in sync with `pn_star.py`/`pn_localzodi.py`/`pn_exozodi.py` by porting every fix
twice (as done for sections 4/5/9 above). Replaced with delegation: `AgnosticMissionSimulator
.get_snr` now looks up the instrument's own connected `PhotonNoiseStar`/`PhotonNoiseLocalzodi`/
`PhotonNoiseExozodi` module instances (via `instrument.sockets[s_name]['modules']`, matched by
`isinstance`, since the generic `run_socket` aggregation sums star+localzodi together and AMS
needs them separate for the per-component error budgets) and calls `.noise(index=i)` on each
directly, exactly as `Instrument.get_snr_single_processing` does internally. The per-star
baseline is likewise now set via `instrument.adjust_bl_to_hz(...)` (reading back
`instrument.data.inst['bl']`) instead of AMS's own duplicate `get_baseline` formula -- this also
fixes a latent inconsistency where AMS ignored the `fixed_baseline` option that `Instrument`
respects (harmless in practice since no run has used `fixed_baseline=True` with AMS so far, but
strictly more correct now).

Net effect: any future physics fix to the three noise modules (like section 9) now only needs to
be made once. `ams.py` no longer imports `transmission_analytic`/`planck_law` directly, and lost
~150 lines of duplicated per-star physics. (The `nulling_order != 2` guard from this point in the
work was superseded by the general-even-order derivation in section 12 below.)

Re-validated after the refactor: `validate_ams_snr.py` (2000-star subsample) still gives max
relative SNR difference 4.2e-16 (machine precision, unchanged from before the refactor).

## 12. Generalizing to any even nulling order (needed for order-4 thesis runs)

The rotation-average closed form (section 2) was originally derived only for `nulling_order=2`
(standard double Bracewell), guarded with a hard `NotImplementedError` in `ams.py`. The thesis
needs `nulling_order=4`. Re-derived the closed form for general nulling order.

**Why only even orders work at all:** `tm3 = sin(x*cos(theta))**n * cos(ratio*x*sin(theta) -
pi/4)**2` with `x = pi*bl*r/wl`. Under the full-rotation average over `theta` in `[0, 2*pi)`,
`sin(x*cos(theta))**n` is *odd* under `theta -> theta+pi` (which flips `cos(theta) ->
-cos(theta)`) whenever `n` is odd -- so its rotation average is identically zero for odd `n`, not
merely unsupported. This matches the physical constraint that nulling order is always even.

**General closed form**, for `nulling_order = 2p`: even powers of sine reduce via the standard
power-reduction formula to a finite cosine series in `theta`, each harmonic of which collapses
under the rotation average (Jacobi-Anger) into a single `J0`, giving

```
<tm> = 1/2 * C(2p,p)/4**p + sum_{j=1}^{p} (-1)**j * C(2p,p-j)/4**p * J0(j*k*r)
```

with `k = 2*pi*bl/wl` (independent of `ratio` and the chop phase, exactly as for `p=1`, which
reproduces the original `1/4*(1-J0(k*r))`). The disk-average generalizes the same way, replacing
each `J0(j*k*r)` term with its own closed-form radial integral `2*J1(j*k*R)/(j*k*R)`. Implemented
as a `for j in range(1, p+1)` accumulation (p is small -- 1, 2, 3, ... -- so no need for a vector
formulation) in `azimuthal_average_tm`/`disk_average_tm`/`radial_average_tm`
(`transmission_analytic.py`), each now taking a `nulling_order=2` keyword.

**Wiring, kept AMS- and LIFEsim-independent per explicit instruction:** `nulling_order` is *not*
part of the `Options` schema (`options.py`/`settings.yaml`) and is *not* a parameter on any
`noise()` method -- both were tried and reverted. Instead it's a single shared instrument-state
entry, `instrument.data.inst['nulling_order']`, mirroring how `bl` already works:
- `Instrument.apply_options()` defaults it to `2` -- plain LIFEsim (`Instrument.get_snr`) never
  touches it again, so it is always the standard double Bracewell.
- `AgnosticMissionSimulator.get_snr` validates `self.__nulling_order` (positive even integer,
  else `ValueError`) and overwrites `instrument.data.inst['nulling_order']` at the top of every
  call, before the per-star loop -- so the AMS's setting always wins for its own run, and a
  subsequent plain `instrument.get_snr()` call on the same instrument silently resets it back to
  2 via its own `apply_options()`, with no special-casing needed anywhere.
- `pn_star.py`/`pn_localzodi.py`/`pn_exozodi.py` read `self.data.inst.get('nulling_order', 2)`
  internally and pass it to the `transmission_analytic` calls -- no new parameters on `noise()`.

**Validation**: closed-form vs. a brute `theta`-average (2,000,000-point grid) at orders 2/4/6,
several `x` and `ratio` values -- machine precision (`~1e-16`) in every case
(`disk_average_tm` similarly checked against a brute 2D rotation+radial grid, agreeing to the
grid's own ~1e-5 discretization level). End-to-end: order-4 star+localzodi vs. a brute
grid (`IS=400`) across 15 random stars agrees to <0.7% (ordinary grid discretization, same order
as the existing order-2 checks). Exozodi at order 4/6 showed up larger (~10%) brute-grid
deviation on a few stars at first, traced to the *already-known* old-grid aliasing behavior near
the Kennedy2015 `r_in` cusp (section 5) -- confirmed present at `nulling_order=2` on the exact
same stars/grid (4.5-5.4%), i.e. a coarse-reference artifact, not an order-4 bug. Exozodi's own
quadrature (`n_r=200` vs `n_r=2000`) self-converges to <1e-5 at orders 2/4/6. Odd order (e.g. 3)
correctly raises `ValueError`. `validate_ams_snr.py` unaffected (still 4.2e-16 at the default
order 2). Confirmed a plain `instrument.get_snr()` call after an AMS `nulling_order=4` run resets
`data.inst['nulling_order']` back to 2 automatically (via its own `apply_options()`), i.e. the two
branches cannot leak state into each other.

## 13. Open items / decisions needed from supervisor

1. **Local-zodi ~27% correction** (section 4) -- confirm this should be adopted.
   Re-verified directly against Dannert et al. (2022) Eq. 17 / Dannert thesis Eq. 3.17:
   the paper's model has no square-domain justification, and the old code's own
   `fov_taper='none'` branch already used the circular convention -- only the default
   `'gaussian'` branch was inconsistent. High confidence this is a genuine bug fix, not
   a modeling choice reversal; still changes existing SNR numbers non-trivially and
   should be a deliberate, documented decision, not something that ships silently.
2. Whether to purge `image_size` from `options.py`/`settings.yaml` entirely, or leave
   it for the visualization path (current state: left in place, scoped decision
   already discussed with user -- visualization is fine to keep pixel-grid-based).
3. Whether/when to delete the `.bak`/`.new` files and the debug scripts once the
   above is confirmed.
4. Thesis text should reflect: (a) the switch from point-sampled wavelength bins was
   investigated and found analytically intractable / not worth it (section 1); (b)
   the spatial-grid-to-analytic noise rewrite and its speedup; (c) the local-zodi
   normalization correction as a distinct, citable finding; (d) the wavenumber-quadrature
   fix to the wavelength-bin sampling itself (section 9) -- reopened once (b) made extra
   wl nodes cheap, and a nice example of the same substitution trick (chirp-removal by
   working in a wavelength-invariant variable) applying at both the spatial and spectral
   integration stages; (e) the general-even-nulling-order closed form (section 12) -- a clean
   generalization of the section-2 result, and the fact that odd orders average to zero under
   rotation is itself a nice citable explanation for why nulling order is always even.
5. **Outlook item for thesis:** the closed-form/quadrature noise formalism in this
   document relies on circular symmetry of the source distributions -- correct for
   LIFEsim's current default models (uniform stellar disk, uniform local zodi,
   homogeneous face-on exozodi per Kennedy et al. 2015), but Lay (2004) shows a
   general *inclined/elliptical* exozodi disk produces genuine rotation-angle-dependent
   even-harmonic modulation rather than a pure DC term. Extending this analytic
   framework to non-axisymmetric exozodi models (a more realistic disk geometry) is a
   natural next step / limitation to flag explicitly in the thesis outlook -- see the
   framing note added to section 2 above.
