# Channel model, assumptions and reproducibility

## What is specified and what is reconstructed

Wang et al., *Secure Beamforming for MISO Visible Light Communications With ISI and NLoS Components*, IEEE Wireless Communications Letters 13(3), 2024, DOI 10.1109/LWC.2024.3350544, give a 10 m × 10 m × 5 m room, four fixtures, 25 LEDs per fixture, 2.6 W per LED, a 1 cm² detector, Bob at (2,0,0) m and Eve at (−2,0,0) m. These are used directly. Equations (1)–(5) specify a Lambertian direct path and diffuse multipath with detector responsivity and concentrator gain. Their numerical section does not specify enough optical, geometric and timing information to reconstruct its channel matrices uniquely. The code is therefore an independent deterministic simulation under the following disclosed assumptions. It is not a digitisation, exact numerical replication or calibration to the paper's figure heights.

| Parameter absent or ambiguous in paper | Assumption in `ChannelConfig` |
|---|---|
| Coordinate origin | Room centred horizontally: x,y∈[−5,5] m, z∈[0,5] m |
| Fixture coordinates and ordering | (−2.5,−2.5,5), (−2.5,2.5,5), (2.5,−2.5,5), (2.5,2.5,5) m |
| LED arrangement | Each fixture is a downward-facing 5×5 planar array, pitch 0.1 m, total footprint 0.4×0.4 m |
| LED half-power semiangle | 60°, yielding Lambertian order m=1 |
| Photodiode orientation and area | Upward-facing, 10⁻⁴ m² |
| Detector field of view | 85° halfangle; out-of-FoV paths are removed |
| Responsivity | 0.53 A/W, wavelength-independent |
| Concentrator refractive index | 1.5; gain G=n²/sin²(FoV) as paper Eq. (5) |
| Optical spectrum/material reflectance | Scalar wavelength-independent diffuse wall reflectivity ρ=0.6; no spectral integration |
| Reflecting surfaces | Four vertical walls only; floor and ceiling absorb. No furniture, specular reflections, shadowing or obstruction |
| Wall quadrature | Centre-point finite elements of at most 1×1 m; full four walls covered with exact tile areas. Default gives 200 elements |
| Optical time resolution | Δt=0.5 ns; linear fractional-delay interpolation at intermediate propagation steps |
| Symbol interval | T_s=10 ns, with rectangular interval integration of channel impulses; electrical pulse shaping/equalisation is not specified by the source |
| Synchronisation | At each receiver, common timing origin equals its earliest visible direct path among all 100 LEDs. Different fixtures are not individually realigned |
| Tap definition | Row s=0 represents excess delay [0,T_s); row s=1 represents [T_s,2T_s), etc. Python row0 corresponds to paper symbol s=1 |
| Channel memory and reflection order | S=1…50 supported; l=0…6 supported when precomputed. Default l=4. Matrix contains all orders 0…l, not only order l |
| Randomness | Channel is deterministic. Seed 20261026 is recorded for reproducible external position experiments; no random rays or fitted channel coefficients are used |

The selected 10 ns symbol period places all direct fixture paths to the nominal Bob and Eve in their first interval. This is a consequence of the given geometry and explicit timing assumption, not an additional perfixture timing correction. Reflections can also arrive in the first interval. Changing symbol period, FoV, wall reflectivity or fixture coordinates can change the curves and their ordering; no universal agreement with the paper's numerical figure values is claimed.

## Discrete transport equations

For an LED at e and receiver r, the direct optical gain is

L₀=(m+1)A cosᵐ(φ)cos(θ)/(2πd²),

provided cosφ>0 and θ≤FoV. The code sums P_LED L₀ over the 25 LEDs of a fixture and multiplies by detector responsivity R and concentrator gain G. Thus the saved physical channel has units of received amperes for unit normalised modulation; it already includes LED optical power. Multiplying it by another 25 or another 2.6 W would double-count optical power.

Let wall element q have centre c_q, inward normal n_q and area A_q. The emitted optical power after the first reflection is the sum of each LED's incident Lambertian power multiplied by A_q and ρ. The element-to-element transition from emitting element p to receiving element q is

T_qp=ρ A_q max(n_p·u_pq,0) max(−n_q·u_pq,0)/(πd_pq²).

The zero self-transition and all back-facing pairs are excluded. On a convex empty rectangular room no further visibility test is required for these inward hemisphere wall-to-wall rays. Each transition also introduces a flight delay d_pq/c. Delays falling between temporal nodes split their mass linearly between the two adjacent nodes; this preserves integrated optical power. Recursive multiplication by this delayed transport operator produces wall-emission histories of orders 1…l. All paths represented by the finite-element discretisation are included at every order: higher orders are not approximated by an arbitrary decay factor or a single effective ray. Their geometry is still an approximation to continuous surfaces because centre-point quadrature replaces the surface integrals.

The final element-to-photodiode factor is

K_p(r)=RG A max(n_p·u_pr,0) max(−e_z·u_pr,0)/(πd_pr²),

with the detector FoV mask. Final flight delays are added before events are integrated into symbol intervals. Intermediate wall powers are optical watts, while receiver outputs are amperes. Sparse delay matrices share the same geometric operator but use weights for their respective integer delays. There is no transition normalisation chosen to force decay: if a geometry violates the quadrature energy check, construction fails with an instruction to refine the spatial mesh.

The finite time horizon exceeds (l+1) times the room diagonal divided by c, with interpolation padding, so every path through the retained orders fits. User-requested S may still truncate the represented output. Delays beyond S T_s are discarded rather than folded into the final tap. Linear time interpolation may place a very small tail fraction just before its physical support; any such negative *excess* time is clamped into the causal first interval. This bounds numerical timing error without inventing additional received energy.

## API and comparisons

```python
from channel import ChannelConfig, VLCChannel

model = VLCChannel(ChannelConfig(max_reflections=6))
HB = model.matrix((2.0, 0.0, 0.0), S=50, max_reflections=4)  # (50,4)
HE = model.matrix((-2.0, 0.0, 0.0), S=50, max_reflections=4)
by_order = model.components((2.0, 0.0, 0.0), S=50, max_reflections=4)  # (5,50,4)
los = model.matrix((2.0,0.0,0.0), S=50, max_reflections=0)
first_interval = model.matrix((2.0,0.0,0.0), S=50, max_reflections=4,
                              first_tap_only=True)  # zeros rows1…49
all_paths_no_temporal_resolution = model.dc_gain((2.0,0.0,0.0),4)[None,:]
```

`S=1` means truncation to the first interval; it is not the same as integrating the entire channel into a single nondispersive coefficient. `first_tap_only=True` retains the requested shape and removes later intervals. `dc_gain` sums all retained optical paths independent of truncation. A report must state which operation defines its no-ISI baseline. This avoids conflating ignoring multipath delays with discarding delayed energy. `component_dc_gain` gives each individual reflection order before summation. Identical calls return identical results; an LRU cache retains up to 512 receiver/S/order combinations. Arrays returned to callers are copies so their modification cannot corrupt cached channels.

Use a single documented reference gain for all terminals and all scenarios if the beamforming simulation scales the physical channels to dimensionless values. For example, divide every Bob/Eve matrix by the same nominal Bob direct-row Euclidean norm and scale noise consistently. Do not independently normalise each channel or scenario: doing so changes Bob/Eve ratios and multipath gains. Raw physical matrices should also be retained in the output.

## Cost and numerical checks

Let P be wall element count, F fixture count, T temporal bin count, N the total number of LEDs and L the maximum reflection order. Geometry construction costs O(P²+NP). A source-history step costs O(NP). Each subsequent reflected-history step costs O(P²TF) in the worst case; CSR delay kernels omit zero hemispherical transfers. Retained histories need O(LPTF) memory, plus O(P²) sparse transition entries (at most twice the nonzero geometric entries because fractional delays split weights). Transfer coefficients/delays are computed once; no frequency-domain P²T tensor is stored. A new receiver's full L-order matrix costs O(LPTF+NF) after precomputation. Different uncertainty samples reuse the same precomputed wall histories. No new wall-transport recursion is required for each receiver.

At the default four-reflection setting P=200 and T=514. Order six uses a longer automatically computed horizon. Refining wall width from 1 m to 0.5 m gives P=800, making the dominant P² transport about sixteen times more expensive before temporal effects; use a limited convergence study rather than silently replacing the entire sweep with this costlier mesh.

`python channel.py` checks 11 conditions covering finite nonnegative coefficients, deterministic repeated calls, Bob/Eve mirror symmetry, total impulse/DC energy agreement, S-prefix agreement, direct-path timing for the nominal geometry, analytic one-LED on-axis LOS, positive reflected terms and decay by order, monotonic addition of reflection power, and correct first-tap truncation. Optical energy checks also verify each reflected wall-emission history does not exceed ρ times the preceding emitted power (with a 2% quadrature tolerance); default maximum wall-to-wall transfer fraction is about 0.4171, below ρ=0.6. These are model/numerical checks rather than evidence that the unspecified source model has been recovered exactly.

A spatial refinement check at Bob with l=4 gives the following integrated gains (symmetry repeats each listed fixture gain twice). These checks change only quadrature resolution, without fitting optical parameters or beamformers:

| Wall target width | Elements | First fixture DC gain (A) | Third fixture DC gain (A) | Six-order precomputation time |
|---|---:|---:|---:|---:|
| 2 m | 60 | 3.0654722×10⁻⁵ | 7.4513907×10⁻⁵ | 0.12 s |
| 1 m | 200 | 3.0143575×10⁻⁵ | 7.3884447×10⁻⁵ | 0.57 s |
| 0.5 m | 800 | 2.9982104×10⁻⁵ | 7.3546305×10⁻⁵ | 5.75 s |

The vector-relative difference ||H_DC(1 m)−H_DC(0.5 m)||₂/||H_DC(0.5 m)||₂ is 0.004718, or 0.472%, at the nominal Bob. This supports the default mesh for integrated gain at this point; it does not establish convergence of every individual temporal tap, every receiver location or the final optimisation. All retained impulse bins must still be checked when evaluating timing sensitivity.

With `OPENBLAS_NUM_THREADS=1`, a six-order model took about 0.51 s to precompute at 1 m resolution. Evaluating 100 different receivers with l=4 took 1.13 s, suggesting approximately 11 s for 1000 new receiver positions on that machine. Repeating the cached 100 positions took about 0.0005 s. These are observed timings, not runtime guarantees.
