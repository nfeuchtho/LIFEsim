

Parametric Model Approximation
---

This file contains the parameters used for the four-dimensional parametric model and its description.

---

_Description:_<br>
The parametric model aims to reduce the complex four-dimensional physical dependence of stellar contrast on 
*observing distance $d$*, *stellar temperature $T$*, and *wavelength $\lambda$* (henceforth referred to as variables) 
to a mathematical model with minimal loss of predictive fidelity.

A reduction takes place by making a few assumptions:

1. The complex four-dimensional equation relating the stellar contrast to the variables is completely separable, i.e.
$$
C(d,\ T,\ \lambda) = A\ C_T(T) \ C_d(d) \ C_\lambda(\lambda).
$$
The functions $C_i$ are defined as the contrast functions. $A$ is a global scaling parameter. This description 
makes it possible to simplify the problem into three independent one-dimensional equations.


2. The contrast functions $C_T$, $C_d$, and $C_\lambda$ may be chosen only based on the appearance of detailed data. 
The data is generated from an instrument simulation on cuts along all three variable axes.<br>
These cuts define areas of each variable where we assume the axis to be constant-valued, referred to as a *container*.
The containers do not have to be equidistantly spaced, nor do they need to share the same granularity. The model must
respect this degree of freedom.


3. The governing top-level mission parameters (see config file for a conclusive list), but especially any limits on 
nulling baseline and/or the observed wavelengths are chosen beforehand based on the capabilities of the 
instrument and universally place both restrictive and permissive constraints on the variables and the parametric model.


4. Independently optimized, the contrast functions are combined to form the full parametric model by optimizing for the
constant scale factor $A$.

---

_Current State_:<br>
Based on the simulated data and the assumptions above, the following functional forms have been chosen:
$$
C_T(T) \approx a\ e^{-(\frac{T-b}{c})^2}
$$
$$
C_d(d) \approx e^{be^{-cd} - a}
$$
$$
C_\lambda(\lambda) \approx a\ e^{-b\lambda}
$$


The full model is hence constituted of a six-parameter description.

The current best parameters may be referred to in the table below (40x40x40 simulation grid).

|  Function   | Parameter | Value (no units)      |
|:-----------:|:---------:|-----------------------|
|             |    $A$    | $5.46 \times 10^{-3}$ |
|    $C_T$    |    $b$    | $4.58 \times 10^3$    |
|             |    $c$    | $1.21 \times 10^3$    |
|    $C_d$    |    $b$    | $1.01 \times 10^1$    |
|             |    $c$    | $6.07$                |
| $C_\lambda$ |    $b$    | $2.90 \times 10^5$    |

For the contrast calculations, we are primarily interested in orders of magnitude (OoM).<br>
The parametric model must preserve these whenever possible. For any prediction $C(d,\ T,\ \lambda)$ the OoM deviation
from the physical contrast $C_{phys}(d,\ T,\ \lambda)$ is defined as
$$
\Delta(d,\ T,\ \lambda) = \log_{10}{\frac{C(d,\ T,\ \lambda)}{C_{phys}(d,\ T,\ \lambda)}}.
$$
When the prediction undershoots the physical value, the OoM is negative. When it overshoots, it is positive.

As an example, consider $\Delta(d,\ T,\ \lambda) = \pm 1$.<br>
In this case, the data point yields a prediction one order of magnitude larger (smaller) than the physical value.

Calculating $\Delta$ for all containers, we may give an estimate for the performance of the model.
Conventional co-variance metrics do not apply here, as the contrast values are so small that any difference may seem insignificant, 
even if deviating by several orders of magnitude.

---

The parametric model currently performs as:

_Maximum Overshoot: $1.12$ OoM<br>_
_Maximum Undershoot: $-3.56$ OoM<br>_
_Average Miss: $-0.18$ OoM<br>_

While being acceptable in the average case, we must still be careful to refine the model and reduce the marginal errors.