# Student Project HS 2025
## Finding top-level mission constraints on stellar contrast with LIFE

---
**Research Question**

_Assuming we observe sun-like stars of types F, G, K and M at distances between two and 30 parsec with varying 
interferometry baselines, what are top-level mission constraints on the stellar nulling contrast ratios 
LIFE must deliver to be able to satisfactorily detect terrestrial planets in the empirical Habitable Zone of their stars?_

---

**CURRENT PHASE:** Coding

**Project Deadline**: 1st December 2025

---
**Phase Description: Coding**

Work in this phase consists entirely of building the codebase. The tasks are sub-structured into eight parts:

I. Simulating and correctly scaling the black body spectra of both planet and star.

II. Adding nulling interferometry to compute the astrophysical and stellar contrast ratios for a star 
in terms of radius and temperature.

III. Varying the spectral types at a constant instrument baseline and distance to achieve first results concerning 
the behavior of the stellar contrast ratio.

IV. Varying both the spectral type and the instrument baseline at constant distance cuts to achieve results concerning 
the behavior of the stellar contrast ratio.

V. Varying the spectral type and the instrument baseline at varying distance cuts to achieve results concerning 
the behavior of the astrophysical contrast ratio.

VI. Finding a parametric model for the stellar contrast ratio in four dimensions (dependent on wavelength, 
stellar temperature, and distance).

VII. Integrating the parametric model from VI. with LIFEsim to establish a forwarding-model to the yield calculator.

**VIII. Tweaking the parametric model to vary the stellar contrast ratio globally, running yields with it to 
find the lowest permissible contrast values for the mission goal (*top-level mission constraints*).**


---

**Schedule**

|          Week          | Phase                | Details                                 | Completed |
|:----------------------:|----------------------|-----------------------------------------|:---------:|
| 1    (18.09. - 25.09.) | Orientation          | getting familiar, reading               |     ✔     |
|  2-6  (25.09. - now)   | Coding (I-VII)       | writing the entire codebase             |   I-VI    |
|        delayed         | Collecting Results   | confirming results, formatting          |           |
|        delayed         | Writing Report       | writing the report and submitting       |           |
|       (December)       | (Presenting Results) | (presenting the results in the group)   |           |

---

Project is complete up to:
- generating black body spectra and scaling them with distance
- adding configurable transmission maps to compute the astrophysical contrast ratio for various planetary bodies in 
edge-on circular orbits
- using nulling interferometry to compute the stellar contrast ratio for a star in terms of radius and temperature.
- using the LIFESim luminosity-dependent calculator for the eHZ by employing the mass-luminosity-radius relationship 
for main-sequence stars
- varying the instrument baseline and the spectral type of the star to generate an imshow plot of stellar contrasts 
at fixed distances
- varying the instrument baseline and the spectral type of the star to generate an imshow plot of 
astrophysical and stellar contrasts at fixed distances
- integrating with a proper star catalogue to increase sample size of stars up to about 200
- adding parallel computing to massively speed up the simulation runs
- changing the parameters of observed planetary bodies to determine the importance of inner/outer habitable 
zone boundary placement 
- creating a parametric model for the stellar contrast ratio in four dimensions (dependent on wavelength, 
stellar temperature, and distance) to achieve reasonable errors while keeping the number of parameters low
- data validation: verify sufficient accuracy of the parametric model in interpolation

Project needs work in regard to:
- full data validation of the entire codebase (LIFEsim integration)
- use the validated data to enable a forwarding-model to the yield calculator
- **finding *top-level mission constraints* for the stellar contrast ratio by modifying the parametric model and 
monitoring the resulting yields in LIFEsim (project goal)**


**This document is dynamically updated.**