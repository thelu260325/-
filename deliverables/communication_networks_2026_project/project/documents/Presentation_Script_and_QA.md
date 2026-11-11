# Ten-minute presentation script — reviewed 11 November 2026

This script matches the reviewed **15-slide** presentation. Sun Jiangeng presents slides 1–5; Qian Tu 6–10; Lu Zipeng 11–15. Each member has a 200-second allocation. These are rehearsal targets, not a measured recording. Speaking pace includes time for figures, pauses and handovers.

Only read the spoken paragraphs. Slide titles, speaker labels, timing tables and Q&A are not part of the timed speech.

| Slide | Speaker | Allocation (seconds) | Spoken words | Words/minute within allocation |
| --- | --- | ---: | ---: | ---: |
| 1 | Sun Jiangeng | 25 | 47 | 113 |
| 2 | Sun Jiangeng | 30 | 55 | 110 |
| 3 | Sun Jiangeng | 40 | 65 | 98 |
| 4 | Sun Jiangeng | 55 | 88 | 96 |
| 5 | Sun Jiangeng | 50 | 87 | 104 |
| 6 | Qian Tu | 40 | 72 | 108 |
| 7 | Qian Tu | 45 | 81 | 108 |
| 8 | Qian Tu | 40 | 70 | 105 |
| 9 | Qian Tu | 40 | 75 | 112 |
| 10 | Qian Tu | 35 | 70 | 120 |
| 11 | Lu Zipeng | 55 | 95 | 104 |
| 12 | Lu Zipeng | 40 | 70 | 105 |
| 13 | Lu Zipeng | 40 | 69 | 104 |
| 14 | Lu Zipeng | 45 | 89 | 119 |
| 15 | Lu Zipeng | 20 | 39 | 117 |

## Pronunciation and equation cues

- MEC: say “M E C”; SBS: “S B S”; OFDMA: “O F D M A”.
- M/M/1: “M M one”; M/D/1: “M D one”.
- λ: “lambda”; μ: “mu”; ρ: “rho”.
- Mbps or Mbit/s: “megabits per second”; MHz: “megahertz”.
- Keep denominator phrases together: “one divided by the difference between mu and lambda”; “C divided by two times the quantity one minus r”.

## Slide 1. End-to-End Performance Modelling and Analysis

**Speaker:** Sun Jiangeng — **allocation:** 25 seconds

Hello everyone. We are Sun Jiangeng, Qian Tu and Lu Zipeng. Our project follows product images from industrial cameras to an edge server for AI quality inspection. We ask how routing, wireless scheduling and server queues affect delivery time, and which upgrades can help when traffic increases.

## Slide 2. Three tasks, one image journey

**Speaker:** Sun Jiangeng — **allocation:** 30 seconds

The project has three connected tasks. We use graph theory to describe the network and select a route. We then use Shannon's formula and a polling schedule to calculate wireless delay. Finally, we use queueing theory to analyse the edge server. Python simulations test these calculations and connect the stages into a complete image journey.

## Slide 3. The numerical inputs are explicit assumptions

**Speaker:** Sun Jiangeng — **allocation:** 40 seconds

The brief gives no numerical parameters, so we clearly label ours as assumptions. We use four cameras, one-megabit images, twenty megahertz of bandwidth and a ten-decibel signal-to-noise ratio. The MEC, or multi-access edge computing server, processes fifty images per second on average. Our chosen mean-delay target is one hundred milliseconds. Lambda always means the total arrival rate across all four cameras, divided equally between them.

## Slide 4. A graph describes the available paths

**Speaker:** Sun Jiangeng — **allocation:** 55 seconds

The graph contains cameras, small base stations and the MEC server. Directed links carry capacities and propagation delays. Base station A can reach the server directly, or relay through base station B. The direct link has lower capacity than the two relay links. In this single-cell example, wireless images leave at least fourteen point six five milliseconds apart, while each relay link needs only one millisecond to transmit an image. Therefore these backhaul links do not queue. The wireless rate is available only to the camera currently scheduled.

## Slide 5. A faster route can have an extra hop

**Speaker:** Sun Jiangeng — **allocation:** 50 seconds

Dijkstra's algorithm minimises the sum of nonnegative link delays: image size divided by link capacity, plus propagation. The direct wired backhaul takes eleven milliseconds per image. The two-hop backhaul takes two point seven milliseconds. Including the common wireless payload gives a selected route weight of seventeen point one five milliseconds. That weight excludes the grant, polling wait and MEC processing, which we add separately. The relay saves eight point three milliseconds. Qian will now explain when a camera can transmit and how long its wireless stage takes.

## Slide 6. Shannon gives an ideal scheduled rate

**Speaker:** Qian Tu — **allocation:** 40 seconds

Shannon's rate is bandwidth multiplied by the base-two logarithm of one plus the linear signal-to-noise ratio. Ten decibels converts to a linear value of ten. Our scheduled rate is sixty-nine point one nine megabits per second, so a one-megabit image needs fourteen point four five milliseconds. We assign all OFDMA resource blocks to one camera per visit, reusing them in time. This is a simplified scheduling case with an ideal radio rate.

## Slide 7. Random arrival phase creates polling wait

**Speaker:** Qian Tu — **allocation:** 45 seconds

The base station visits cameras one to four in a fixed cycle. Each visit includes overhead and at most one image. Empty visits remain reserved. One cycle lasts fifty-eight point six one milliseconds. For an isolated image arriving at a random phase, the mean wait is half a cycle. Adding its grant and payload gives forty-three point nine six milliseconds. This reference assumes no older image at that camera. It is different from a simultaneous batch arriving at the cycle boundary.

## Slide 8. Backlog increases the camera waiting time

**Speaker:** Qian Tu — **allocation:** 40 seconds

When older images are waiting, a new image may wait through several visits. For our reserved one-image rule, the mean polling wait is C divided by two times the quantity one minus r. Here r is the utilisation of one camera's reserved visits. At a total arrival rate of twenty-five images per second, the wait is forty-six point two five milliseconds. This wait excludes the image's own grant and payload.

## Slide 9. Image-size variability changes transmission service

**Speaker:** Qian Tu — **allocation:** 40 seconds

The brief also asks about random image size. If size X is exponential with mean S and transmission rate R is constant, duration X divided by R is exponential too. With Poisson input and a continuously available transmitter, that supports M/M/1. Fixed-size images instead give deterministic transmission service, supporting M/D/1 under those same conditions. Our cyclic polling and fixed overhead require separate treatment. MEC processing times are a different modelling assumption.

## Slide 10. Simulation tests each stage and the whole chain

**Speaker:** Qian Tu — **allocation:** 35 seconds

We simulate both the isolated M/M/1 server and the actual polled chain. Each arrival-rate experiment uses thirty independent runs, with one hundred thousand measured images after a twenty-thousand-image warm-up. Confidence intervals use run averages because successive image delays are correlated. Ten deterministic tests pass, including the lecture example. We also check that the measured delay components add up. Lu will now explain the server bound and final results.

## Slide 11. Little’s law gives the M/M/1 delay bound

**Speaker:** Lu Zipeng — **allocation:** 55 seconds

Here we analyse the required isolated server: Poisson arrivals, independent exponential processing and one server. State k counts waiting images plus the image being processed. Arrivals increase the state at rate lambda; departures reduce it at rate mu. Stability requires lambda below mu. Little's law connects the average number of images to their arrival rate and mean time. It gives T equal to one divided by the difference between mu and lambda. T includes waiting and processing. With mu equal to fifty and a one-hundred-millisecond limit, the maximum arrival rate is forty images per second.

## Slide 12. The isolated server follows the theoretical curve

**Speaker:** Lu Zipeng — **allocation:** 40 seconds

This plot compares simulated server time with M/M/1 theory. The largest relative difference in the mean is zero point six two percent. At forty images per second, theory gives one hundred milliseconds and simulation gives ninety-nine point three eight. Ten of eleven pointwise ninety-five-percent intervals cover theory. Universal coverage is not guaranteed. As load approaches processing capacity, waiting grows sharply, so spare capacity is important for low delay.

## Slide 13. End-to-end delay includes the upstream stages

**Speaker:** Lu Zipeng — **allocation:** 40 seconds

The complete chain has additional waiting and transmission stages. At twenty-five images per second, mean total delay is ninety-eight point five two milliseconds. At thirty, it is one hundred twelve point four eight. Twenty-five is therefore the highest tested rate meeting the mean target; it is not an exact continuous threshold. Polling changes the server's arrival pattern, so we simulate that actual pattern instead of assuming it remains Poisson.

## Slide 14. Radio and processing should be upgraded together

**Speaker:** Lu Zipeng — **allocation:** 45 seconds

At forty images per second, we compare four designs using the same traffic assumptions. A faster server alone and more bandwidth alone still miss the mean target. Combining forty megahertz with a server rate of seventy-five images per second reduces the mean to fifty-seven point three one milliseconds, about sixty-seven percent below baseline. The bandwidth comparison holds SNR fixed at ten decibels, so power and cost must also be considered. About nine point five percent of images still miss the deadline: a low mean is not a per-image guarantee.

## Slide 15. Design for the whole image journey

**Speaker:** Lu Zipeng — **allocation:** 20 seconds

To conclude, link capacity matters as well as hop count. Polling and server queues both affect delay. A server-only bound cannot guarantee end-to-end performance, and mean delay must be distinguished from deadline reliability. Thank you. We welcome your questions.

# Suggested answers for the question session

These answers are for the Q&A after the timed presentation.

**Why use M/M/1 if polling changes the arrivals?** Task 3 explicitly requires an M/M/1 node model. We validate that isolated model, then simulate the actual scheduler-generated MEC input. We do not assert that polling preserves Poisson arrivals.

**Does lambda mean the rate from one camera?** All plotted and quoted lambda values are aggregate rates across four cameras. Each independent camera has rate lambda/4.

**What does T include?** For the isolated M/M/1 task, T is Ws: queue waiting plus processing. End-to-end time additionally includes camera polling, grant, payload transmission and backhaul.

**Why are 40/s and 25/s different?** 40/s is the exact isolated-MEC mean-delay bound at mu=50/s and Tmax=0.1 s. 25/s is the highest tested end-to-end point below the same mean limit; 30/s fails. We have not identified the exact continuous threshold.

**Why can two backhaul hops be faster?** Each relay link is 1 Gbit/s rather than the direct link’s 100 Mbit/s. Two 1 ms serializations plus 0.7 ms propagation give 2.7 ms, compared with 10+1=11 ms directly. The 17.15 ms route weight adds radio payload but excludes the grant and all queueing.

**Is the polling scheduler an OFDMA model?** It is a deliberately simplified scheduler on an OFDMA-capable radio: all RBs go to one camera per visit and are reused in time. General OFDMA can schedule cameras simultaneously on disjoint RB sets; that would require different bandwidth and delay calculations.

**Why C/2 rather than (N−1)τ/2?** C/2 is the residual wait of an isolated image arriving at a random continuous phase. A simultaneous batch at cycle start is different: its mean wait before a slot is (N−1)(g+τ)/2. Under load, older images add backlog and the reserved-visit mean wait becomes C/[2(1−r)].

**What changes when image size is exponential?** At constant R, size X exponential with mean S gives X/R exponential with rate R/S. A continuously available transmission server with independent Poisson input then supports M/M/1. A fixed-size baseline would give M/D/1 under those conditions. If exponential service was already assumed, the new assumption supports that same M/M/1 model. Fixed overhead or cyclic polling require separate treatment.

**Why fixed-size images but exponential MEC service?** Image transmission duration and AI processing duration belong to different stages. The baseline fixes the radio payload size while following the requested exponential-processing assumption for the MEC.

**Does a 100 ms mean imply all images meet 100 ms?** No. At the isolated-MEC boundary, the exponential system-time tail gives about 36.8% deadline misses. In the combined-upgrade chain, the measured miss fraction is 9.51%. A reliability requirement needs its own probability target.

**Why is there a small difference between the two baseline simulations?** The arrival-rate sweep gives 174.47 ms at 40/s; the separately seeded controlled resource comparison gives 174.18 ms. Their 95% intervals overlap. Both use the same baseline parameters, and the comparison percentages use the controlled baseline.

**What is held fixed when bandwidth doubles?** SNR remains 10 dB. Maintaining this SNR over twice the bandwidth may require more received power; the comparison is not a fixed-total-power experiment. Spectrum, hardware and energy costs are not quantified.

**Why does one point lie outside a 95% confidence interval?** The intervals are pointwise estimates across repeated experiments; universal coverage of eleven points is not guaranteed. Ten of eleven contain theory, and all mean relative errors are below 0.62%. Seeds were retained.

**What are the main modelling difficulties and limitations?** We had to reconcile OFDMA with a specific polling rule, separate waiting from total time, and account for non-Poisson MEC input after scheduling. Constant SNR, exponential independent processing, infinite buffers and one active cell remain simplifying assumptions. Real deployment requires measurements and finite-buffer, interference and retransmission modelling.

**Are the parameter values specified by the teacher?** No. Four cameras, the image size, SNR, processing rate and 100 ms target are declared illustrative choices. The assignment provides the modelling tasks and distributions but no numeric parameter table.
