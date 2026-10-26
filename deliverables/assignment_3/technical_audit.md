# Technical audit of Wang et al. (2024)

Internal technical evidence for the critique and Python reproduction. This is not the final ≤2,000-word report. Based on the complete supplied five-page article, including visual inspection of the equations on pp. 909–911. Mathematical counterexamples below are our own checks of the published formulation, not the authors' simulation data.

## 1. Important correction to text extraction: Eqs. (8)–(10) are consistent

The rendered PDF shows **sum of squared responses** in all three equations:

\[
\mathrm{SNR}_k=\frac{\alpha^2\sum_{s=1}^S(h_{k,s}w_s)^2}{\sigma^2},\qquad
R=\left[\frac12\log_2\frac{6\alpha^2\sum_s(h_{B,s}w_s)^2+3\pi e\sigma^2}
{\pi e\alpha^2\sum_s(h_{E,s}w_s)^2+3\pi e\sigma^2}\right]^+.
\]

Equation (10) maximises the same ratio before applying the monotone logarithm/positive part. **There is no squared-sum versus sum-of-squares inconsistency between (8)/(9) and (10).** Text extraction visually displaces parentheses/superscripts; do not base criticism on the extracted arrangement.

The positive-part transformation is harmless for finding a maximal nonnegative secrecy-rate objective because the zero beamforming matrix is feasible and gives ratio one. The corresponding positive-part rate is zero.

## 2. Proposition 1: independent constraints do not establish independent optimisation

The paper asserts: because the beamformers are independent, the fractional objective can be decoupled into independent quasiconvex subproblems. The constraints are separable over s, but a **ratio of sums is still coupled**. In Eq. (11), the contributions of every other component occur in the current component's objective. Algorithm 1 makes one sequential pass, with random initial W; it supplies no repeated sweeps, convergence test for the joint objective or proof of global optimality.

More strongly, Eq. (13) always maximises the desired amplitude for the selected ratio bound. Even with other components held fixed, increasing the current component's amplitude can lower the aggregate secrecy ratio if that component has an inferior signal ratio. A component may optimally be turned off.

### Analytic counterexample within Eq. (10)

Take N_F=1, S=2, alpha=sigma=1, any p (scalar norms coincide), and positive channel coefficients

\[
h_B=(3,1),\qquad h_E=(0.1,0.7).
\]

All beamformers satisfy |w_s|≤1. Both lower ratio bounds lie inside the paper's stated interval:

\[
\beta_{1,\min}=1/30,\qquad\beta_{2,\min}=0.7,
\qquad\sqrt{6/(\pi e)}=0.8382111776.
\]

For either component and every beta≥beta_min, Eq. (13) returns w_s=1: its objective is a positive scalar times w_s and the ratio constraint permits w_s=1. Thus the published independent construction cannot select w_2=0. With c=3*pi*e, evaluation gives:

| w=(w1,w2) | Eq. (10) ratio | Eq. (9) rate |
|---|---:|---:|
| (0,0) | 1.0000000000 | 0.0000000000 |
| (0,1) | 1.0609163262 | 0.0426554381 |
| (1,0) | **3.0974690381** | **0.8155449307** |
| (1,1) | 2.8645656523 | 0.7591582015 |

The feasible (1,0) outperforms the constructed (1,1). In this scalar case, t_s=w_s² ranges independently in [0,1]; the objective is linear-fractional over the square. Its maximum occurs at a vertex, so checking these four vertices certifies (1,0) as a global maximiser. This example disproves the general independent-amplitude-maximisation claim, rather than merely showing slow convergence in one numerical solver.

The example also embeds exactly into genuine **four-input MISO** with p=infinity. Let a=(1/4,1/4,1/4,1/4), h_B,1=3a, h_B,2=a, h_E,1=0.1a and h_E,2=0.7a. All entries are positive. Since a*w_s ranges over [-1,1] under ||w_s||infinity≤1, the scalar proof and numbers remain unchanged. Equation (13) sets each w_s to the all-ones vector; turning the entire second column off gives the better solution. This removes any reliance on N_F=1, which could otherwise be challenged as outside the word “MISO”.

It is an audit instance of the stated optimisation model, not a recreation of the reported room geometry. The coefficients can all be scaled to small optical channel gains if alpha/sigma is increased by the reciprocal scaling, preserving the ratios and rates.

For fixed other components, the sign of the derivative with respect to t_s is the sign of

\[
6h_{B,s}^2-F(W)\pi e h_{E,s}^2.
\]

This makes the missing amplitude decision explicit. In the example, the weak component's standalone high-SNR ratio is approximately 1.434, below the strong component's aggregate ratio 3.097; adding it degrades the result.

This does not imply that the authors' plotted four-fixture examples fail. It limits the general global-optimality claim. A corrected global fractional method or an independent low-dimensional global benchmark should be distinguished from literal Algorithm 1.

## 3. Algorithm 1 has a dB/linear perturbation ambiguity

Step 8 specifies 0 < 20 log10(Delta beta_s) < epsilon. For the stated epsilon=0.2 dB, this implies **1 < Delta beta_s < 1.023293**, not a small additive number. Steps 13–14 then evaluate beta_s + Delta beta_s, even though beta_s lies below approximately 0.8382. This is not a local finite-difference perturbation within the interval.

A reasonable numerical interpretation would add a small perturbation in dB and convert back, or multiply linear beta by 10^(delta_dB/20), but either is a disclosed implementation repair. Do not silently state that a repaired implementation is an exact transcription of the printed algorithm.

Other implementation ambiguities: the printed sums in Algorithm 1 reuse the current s/beta_s notation for all terms, unlike Eq. (11)'s separation of the fixed other components; zero desired responses make beta_i=h_E,i*w_i/(h_B,i*w_i) undefined; random initial W and random seed are unspecified. The lower-bound problem (12) deliberately lacks the amplitude constraint because it normalises h_B*w=1 to find a directional ratio. Do not call that omission alone a bug.

## 4. Robust constraints: exact support-function reformulation

For the paper's spherical uncertainty set h=hat(h)+e, ||e||2≤epsilon,

\[
\min_e hw=\hat h w-\epsilon\|w\|_2,\qquad
\max_e|hw|=|\hat h w|+\epsilon\|w\|_2.
\]

Therefore Eq. (20) at fixed nonnegative beta can be implemented using

\[
\hat h_Bw-\epsilon_B\|w\|_2\ge t,\quad
|\hat h_Ew|+\epsilon_E\|w\|_2\le\beta t,\quad
\|w\|_p\le1.
\]

These are convex constraints. Enforcing t≥0 is consistent with the intended nonnegative guaranteed Bob response. For evaluating the actual worst squared response without this sign restriction, the correct expression is

\[
\min_e(hw)^2=\big[\max(|\hat h w|-\epsilon\|w\|_2,0)\big]^2.
\]

Do not square (hat(h)w-epsilon||w||2) when the interval crosses zero: its true minimum is zero. Maximum squared Eve response is (|hat(h)w|+epsilon||w||2)².

For independent per-tap Bob and Eve balls, worst-case sum-of-powers evaluation is the sum of these extrema. A shared physical receiver position induces correlations across fixtures and taps, whereas the independent balls permit otherwise impossible combinations. Thus the spherical/product approximation can be conservative relative to position uncertainty; Monte Carlo position averages do not certify the analytical worst-case guarantee.

The article states midpoint nominal channel coefficients and half-ranges. To enclose a complete component-wise box with half-width vector delta in one Euclidean ball, epsilon=||delta||2 suffices; max(delta) generally does not. The article does not provide a full mapping from position-circle radius to epsilon, so a reproduction must declare its own mapping rather than imply it was supplied.

## 5. Multiuser extrema in Eqs. (14)–(15)

Equation (14) uses sum_s max_j |h_Ej,s*w_s|². For one worst noncolluding Eve receiving all branches, the conventional expression is max_j sum_s |h_Ej,s*w_s|². These are not generally equal; the former is at least as large and can be conservative. Equation (15) similarly uses sum_s max_j |h_Bj,s*w_s|² instead of max_j sum_s |h_Bj,s*w_s|² for selecting a single Bob, potentially producing an optimistic composite receiver.

Example: two receivers have per-component powers (4,1) and (1,4). Sum of maxima is 8, whereas maximum sum is 5. They coincide if the same receiver is extremal on every component. Explicit per-component selection could motivate a different model, but that scheduling/receiver assumption must be stated. Do not claim the expressions can never be meaningful; identify the missing assumption for the stated noncolluding/selected-user interpretation.

## 6. Physical model and comparison limits

Equation (7) contains different past data symbols as ISI; the paper invokes special combining schemes such as MRC, citing [11], to obtain parallel components and Eq. (8). The supplied letter does not detail the receiver processing, sampling, normalisation or temporal beamformer implementation. This is an implementation/reproducibility limitation, not sufficient evidence to assert that MRC or the cited scheme is categorically invalid.

If W were instead implemented as a simultaneous FIR transmit filter x_n(mu)=alpha*sum_s w_n,s*d_(mu-s+1), the worst-case sample-amplitude constraint would require a row sum sum_s |w_n,s| bound. The printed per-column p-norm bounds alone do not establish that FIR amplitude property. Since the actual intended architecture is not fully specified here, describe this as a clarification required, not as a proven violation of an architecture the paper never explicitly defines.

At the same numerical radius, the feasible sets satisfy B_1 subset B_2 subset B_infinity. Consequently the optimal objectives necessarily order p=infinity≥2≥1 for identical channels. This ordering does not compare equal physical optical budgets; the paper itself identifies different norm constraints with different intensity/power constraints. It should not be read as a separate algorithmic advantage.

NLoS additions may improve the reported geometry but can also benefit Eve. Plots support scenario-specific improvement, not a universal monotonic secrecy theorem. Increasing S adds signal components and independent design variables in the stated objective; without clarifying equal-energy/temporal normalisation it is not a controlled proof that arbitrary physical ISI is harmless.

## 7. Reproducibility: what is stated and what is absent

Stated: room 10×10×5 m³; N_L=25 LEDs/fixture; N_F=4 fixtures; PD area 1 cm²; each LED radiant power 2.6 W; Bob (2,0,0), Eve (-2,0,0); algorithm tolerance 0.2 dB; 1000 random position realisations for robust results. Captions specify S=50,l=4 for Figs.3–5; alpha/sigma sweep shown as 20log10(alpha/sigma); Fig.6 varies l and S.

Not sufficiently specified in the supplied letter:

- exact four-fixture positions and 25-LED layout/spacing;
- LED half-power angle/Lambertian order, PD FoV, refractive index, responsivity and exact orientations;
- wall/ceiling/floor reflection material/spectral coefficients, reflectance treatment and source spectrum;
- surface discretisation, integration/quadrature method and truncation/convergence settings for multipath;
- symbol duration, pulse shape, time sampling and precise mapping of CIR to the S discrete components;
- receiver combining normalisation/implementation;
- position-circle radii, distribution within circles, and mapping to the dimensionless/numerical epsilon values;
- random seed/initial W; exact solver settings and treatment of algorithm ambiguities;
- full multiuser placement protocol; explicit common physical power normalisation for p comparisons;
- machine-readable reference results or original implementation.

Some missing channel choices may be available in cited references [11]–[13]. They are **not specified in this supplied letter**; do not imply that no source anywhere provides them. An assumed-parameter reproduction must enumerate assumptions and distinguish qualitative trend reproduction from exact numerical figure replication.

## 8. Recommended executable audit/reproduction subexperiments

1. Directly evaluate the four-vertex scalar counterexample and assert the best ratio/rate. This tests the claimed decoupling independently of CVX/SOCP solver behaviour.
2. For one component S=1, compare the beta-search SOCP result with a dense angular/global low-dimensional search; this isolates a valid special case from the multi-component claim.
3. Test spherical support formulas against deterministic extrema and random uncertainty samples; include a Bob interval crossing zero.
4. Test multiuser sum-max versus max-sum on the explicit (4,1)/(1,4) power example.
5. Under a fully logged assumed room configuration, reproduce the p-norm ordering, SNR increase/uncertainty deterioration and ZF high-SNR tendency where nonzero Bob-preserving Eve-null space exists. Label these as conditional trends, not recovered author data.
6. If graph data are digitised, keep reference-digitisation error separate from simulation mismatch; digitised values do not replace channel reproduction.

No channel or solver source was modified in this audit.
