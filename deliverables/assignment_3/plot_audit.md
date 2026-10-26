# Published-plot audit and approximate digitized reference points

Source: Wang, Yu, Lu and Su, *Secure Beamforming for MISO Visible Light Communications With ISI and NLoS Components*, IEEE Wireless Communications Letters 13(3), 908–912 (2024), DOI: 10.1109/LWC.2024.3350544. Inspected supplied PDF pages 4–5 (printed pages 911–912) and the Figure 1 schematic on PDF page 2.

## Provenance and permitted interpretation

`benchmark_points.csv` contains **100 approximate digitized readings**, NOT the authors' raw measurements, NOT solver results, and NOT independent reproductions. Values were read from a 180-dpi rasterization, with manual axis calibration and colour/marker inspection. Plot readings may be useful as comparison/error-bar anchors but must never be used to manufacture matching simulated curves. `estimatedreadingerror` is an approximate symmetric **reading tolerance in y units**, not a statistical standard error or confidence interval. No uncertainty in x was estimated; x coordinates are labelled grid values. All y units in this CSV are bits/s/Hz. CSV x units differ by original figure: Figure 3 uses dB, Figure 5 uses the plotted epsilon_E, and Figure 6 uses reflection order l.

Reading tolerances: Figure 3 and Figure 5 ±0.03 bits/s/Hz; Figure 6 ±0.010 bits/s/Hz because its axis is magnified. The three decimal places in Figure 6 record the digitization scale, not three-decimal author accuracy. No original figure image or full copyrighted paper is intended for GitHub publication. Images and extracted paper text in `reference_figures` are local inspection material only.

## Figure 2: SNR map

- Axes X and Y each span −5 to +5 m; receiver plane z=0.
- Colour bar spans −40 to +40 dB, with labelled 10-dB intervals. Saturation of the colour scale does not establish an exact extremum of ±40 dB.
- Labels identify Bob near (2,0) and Eve near (−2,0); the map has a high-SNR lobe around Bob and a deep low-SNR region near Eve.
- Caption only states optimal beamforming. It does not state all S, l, p, alpha/sigma settings, so the map is not an exact independently specified numerical target.
- A meaningful reconstruction should design a beamformer for the stated Bob/Eve pair, then evaluate that same beamformer over the plane; optimising a different beamformer at every grid point would answer a different question.

## Figure 3: rate against alpha/sigma

- Actual horizontal axis: **20 log10(alpha/sigma) in dB**, 0 to 20 with grid values every 2 dB. Do not insert the dB value itself in place of the linear ratio. The caption abbreviates this to alpha/sigma.
- Vertical axis: secrecy rate R in bits/s/Hz, labelled 0, 0.5, 1.0, 1.5, 2.0, 2.5; upper frame approximately 2.7.
- Caption: S=50, l=4, epsilon_B=0, epsilon_E=0.05.
- Twelve curves: p in {1,2,infinity}, with four legends each: optimal with ISI/NLoS (blue triangles), ZF with ISI/NLoS (red circles), robust with ISI/NLoS (black squares), optimal without ISI/NLoS (green stars).
- Curve groups are ordered p=infinity highest, p=2 middle, p=1 lowest. CSV includes each group's four series at 10 and 20 dB.
- At 20 dB, p=infinity gives approximately optimal 2.58, ZF 2.54, robust 2.37, no-ISI/NLoS optimal 2.25. ZF approaches the optimal curve over the shown range, but the plot alone cannot prove an asymptotic theorem outside its range.

## Figure 4: multiuser extension

- Two stacked panels, each with x values 1 through 6. Top x is number of Eves K_E; bottom x is number of Bobs K_B.
- Top y labels run 0 to 2.5, upper frame approximately 2.7; bottom y labels run 1.0 to 5.0, upper frame approximately 5.2. All rates are bits/s/Hz.
- Three legend entries: optimal (blue triangles), ZF (red circles), robust (black squares), repeated in p=infinity,2,1 groups.
- Caption: 20log10(alpha/sigma)=20 dB, S=50, l=4, epsilon_B=0, epsilon_E=0.05.
- Increasing K_E lowers the curves; increasing K_B raises them. p=infinity remains highest. Optical/power constraints are different across norms, so this is not an equal-total-power comparison unless an additional normalization is supplied.
- Additional users' exact positions/channel generation are not specified in the numerical paragraph or caption. The number/location of the nonswept party is also not explicitly supplied. Holding it at one is a plausible declared assumption, not a reported fact. No Figure 4 digitized CSV rows are supplied to avoid implying fully identified multiuser conditions.

## Figure 5: CSI uncertainty

- Horizontal axis epsilon_E (caption epsilon_E,s), from 0 to 0.50 in 0.05 increments. Epsilon_B annotation groups are 0, 0.2 and 0.4.
- Vertical axis R in bits/s/Hz, labels 0 to 2.5; upper frame approximately 2.7.
- Caption: 20log10(alpha/sigma)=20 dB, p=infinity, S=50, l=4.
- Four legend entries: robust with ISI/NLoS (black squares), ZF with ISI/NLoS (red circles), robust without ISI/NLoS (purple diamonds), and optimal with ISI/NLoS (blue triangles).
- Blue is the approximately 2.58 perfect-CSI upper bound, not a claim that imperfect-CSI optimal designs have no uncertainty cost.
- Robust-with-ISI/NLoS endpoints as epsilon_E moves 0→0.5: epsilon_B=0 gives about 2.58→0.96; epsilon_B=0.2 gives about 1.71→0.39; epsilon_B=0.4 gives about 1.24→0.16.
- CSV includes x=0,0.05,0.25,0.50 for all labelled groups.
- Equation (17) defines epsilon_k as an l2 **channel-error bound**. The plotted 0.05 is not explicitly 5 cm, 5% error, or a position-circle radius. A geometry→channel uncertainty mapping and normalization must be disclosed by a reproduction. The separate epsilon=0.2 dB in numerical settings is the Algorithm 1 search tolerance.

## Figure 6: reflection order and ISI comparison

- Horizontal axis reflection order l=1,2,3,4,5,6. The figure does not include l=0, so it cannot directly furnish a numerical no-reflection baseline.
- Vertical axis R is **zoomed to 2.00–2.60**, with labelled 0.05 increments. Do not mistake it for a zero-origin rate axis.
- Caption: 20log10(alpha/sigma)=20 dB, p=infinity, epsilon_B=0, epsilon_E=0.05.
- Three annotated groups: optimal (highest), ZF (middle), robust (lowest). Each has red triangles for S=1 (without ISI), blue open circles for S=50 (with ISI).
- CSV includes all six plotted x positions for all six series.
- Approximate S=50 endpoints l=1→6: optimal 2.333→2.579; ZF 2.280→2.550; robust 2.040→2.274. Rates largely saturate around l=4.
- S=50 appears approximately 0.008–0.010 above S=1 for the illustrated curves, comparable to the individual reading tolerance. The visible result supports lack of a substantial ISI penalty **under the proposed model/combining/beamforming assumptions**, not a general conclusion that ISI improves communication or is harmless in every VLC system.

## Apparent cross-figure discrepancy to retain, not tune away

At the stated common condition p=infinity, S=50, l=4, epsilon_B=0, epsilon_E=0.05 and 20log10(alpha/sigma)=20 dB:

- Figure 3 robust curve reads approximately **2.37 ±0.03**.
- Figure 5 robust curve at epsilon_E=0.05 reads approximately **2.27 ±0.03**.
- Figure 6 robust S=50 at l=4 reads approximately **2.274 ±0.010**.

The roughly 0.10 difference between Figure 3 and the other two is larger than the stated reading tolerances. It may reflect an omitted setting, averaging convention, plotting inconsistency, or a reading limitation. This audit does **not** establish its cause or prove an author error. Do not introduce hidden calibration factors merely to force a reproduction through every point.

## Geometry and simulation settings: what the paper actually fixes

The numerical section supplies: W×L×D=10×10×5 m³; N_L=25 LEDs/fixture; N_F=4 fixtures; A=1 cm²; P_n,i=2.6 W; algorithm tolerance=0.2 dB; nominal Bob=(2,0,0) m; Eve=(−2,0,0) m; robust results averaged over 1,000 random position realizations.

Figure 1 is a **generic array schematic**, with fixture labels 1,2,3,4,5,6,7,…,N_F. It is not a measured floor plan or a specific four-fixture 2×2 drawing. No fixture coordinates, pitches, or emitter locations are printed. A symmetric 2×2 ceiling arrangement is an explicit implementation assumption, not an exact value inferred from Figure 1.

Other numerical items not fully specified in the supplied letter include individual LED spacing within a fixture; numerical half-power semiangle; PD field of view; responsivity and concentrator index; spectral power/reflectance choices; surface discretization; symbol time/delay binning into S channel rows; position-circle radii and position sampling distribution; uncertainty normalization and geometry→channel-bound mapping; extra-user locations and random seeds; detailed MRC/parallel-channel implementation. Some channel definitions cite external sources, but those citations do not by themselves provide this paper's exact simulation parameter file.

An independent implementation can therefore reproduce an explicitly stated model, optimization logic and qualitative trends, and compare against these approximate anchors. A claim of exact author-result replay requires the missing settings, raw data/code or author confirmation. Digitized reference points are evidence for comparison, not an alternative to the required Python reproduction.
