# Ten-minute presentation script

Timing target: 600 seconds. Slides 1–5: Sun Jiangeng; 6–9: Qian Tu; 10–14: Lu Zipeng. Each member has 200 seconds. Rehearse and adjust pace; timings are targets, not measured delivery times.

## Slide 1. End-to-End Performance Modelling and Analysis

**Speaker:** Sun Jiangeng — **target:** 25 seconds

Good morning. We are Sun Jiangeng, Qian Tu and Lu Zipeng. Our project investigates how images travel from industrial cameras to an edge server for AI-based quality inspection. We combine network routing, wireless polling and queueing theory. Our central question is whether a fast processing server is enough to guarantee timely delivery of every image.

## Slide 2. Three tasks, one image journey

**Speaker:** Sun Jiangeng — **target:** 35 seconds

The assessment has three connected tasks. First, we model cameras, base stations and the edge server as a graph and select a route. Second, we use Shannon's formula and a clearly specified polling schedule to derive wireless delay. Third, we analyse an M/M/1 server using Little's law. We then compare theory with Python simulations and examine the complete chain. Our results concern communication and processing delays; the AI classifier itself is outside the model.

## Slide 3. An illustrative, fully declared baseline

**Speaker:** Sun Jiangeng — **target:** 40 seconds

The brief does not specify numerical inputs, so these are declared design assumptions. We use four cameras, one-megabit images, twenty megahertz of bandwidth and a ten-decibel signal-to-noise ratio. The edge server processes fifty images per second on average. We choose one hundred milliseconds as an illustrative mean-time target. Camera arrivals are independent Poisson streams. Baseline images have fixed size, while edge processing times are exponential. These are distinct assumptions about two different stages of the system.

## Slide 4. A graph makes the routing decision explicit

**Speaker:** Sun Jiangeng — **target:** 55 seconds

Each camera, base station and server is a graph vertex. Directed edges represent possible uplink and backhaul links. Camera nodes carry an arrival rate and image size. The edge server carries its processing rate and queue discipline. Link attributes include capacity and propagation delay. Base station A can reach the server directly, or cooperate with base station B. Our example has one active camera cell, so the faster backhaul links do not develop queues. The wireless capacity shown here is available only while a camera is scheduled. It is not simultaneously available to all four cameras.

## Slide 5. The extra hop is faster in this graph

**Speaker:** Sun Jiangeng — **target:** 45 seconds

We assign each link a nonnegative weight equal to image size divided by link capacity, plus propagation delay. Dijkstra's algorithm selects the smallest sum. The direct wired backhaul takes eleven milliseconds per image. The two-hop path takes only two point seven milliseconds because its links have higher capacity. Including the common wireless transmission, the selected route takes seventeen point one five milliseconds before polling and processing are added. It saves eight point three milliseconds. This is the shortest unloaded transmission route for this graph, rather than a guarantee about every possible congestion condition.

## Slide 6. Shannon gives the scheduled radio rate

**Speaker:** Qian Tu — **target:** 45 seconds

I will explain the wireless model. Shannon's capacity formula is bandwidth multiplied by the base-two logarithm of one plus the linear signal-to-noise ratio. Ten decibels corresponds to a linear value of ten. With twenty megahertz, the result is sixty-nine point one nine megabits per second. A one-megabit image therefore takes fourteen point four five milliseconds to transmit. This is an ideal capacity calculation. Actual throughput can be lower because of coding, interference and retransmissions. Our model grants all resource blocks to one camera at a time, which is a simple OFDMA scheduling case.

## Slide 7. A visit is not immediately available

**Speaker:** Qian Tu — **target:** 55 seconds

The base station visits cameras one to four cyclically. Each visit includes a grant interval and transmission of at most one image. An unused reservation remains idle. One visit lasts fourteen point six five milliseconds, and a full cycle lasts fifty-eight point six one milliseconds. Consider an isolated tagged image arriving at a random phase, with no older image waiting. Its mean residual wait is half a cycle. Adding the grant and transmission gives forty-three point nine six milliseconds. This particular formula assumes random arrival phase. A simultaneous batch at the start of a cycle would have a different average waiting time.

## Slide 8. Camera backlog adds another load effect

**Speaker:** Qian Tu — **target:** 55 seconds

At higher traffic loads, there may already be older images at the same camera. A new image can then miss more than one visit. For our reserved one-image polling rule, the exact mean wait is the cycle length divided by twice one minus the camera's visit utilisation. The report derives this using the queue observed after each visit and Little's law. At twenty-five images per second, the mean polling wait is forty-six point two five milliseconds. At forty images per second it is seventy point eight one milliseconds. The simulation agrees with this formula to within about zero point one four percent across the tested rates.

## Slide 9. Test each model, then connect the stages

**Speaker:** Qian Tu — **target:** 45 seconds

We use three experiments: the isolated M/M/1 server, the exact polling system and the actual connected chain. Each tested arrival rate has thirty independent replications. Each replication retains one hundred thousand images after a twenty-thousand-image warm-up. Confidence intervals are calculated from replication means, because delays within a run are correlated. Ten deterministic tests check the scheduling, queue recursion, route selection and lecture example. We also check that end-to-end delay equals the sum of its measured components. Lu will now explain the server analysis and the final results.

## Slide 10. The required M/M/1 mean-delay bound

**Speaker:** Lu Zipeng — **target:** 50 seconds

The server state counts waiting images plus the image being processed. Arrivals increase the state at rate lambda; completions reduce it at rate mu when the server is occupied. Stability requires lambda smaller than mu. Using the geometric stationary probabilities and Little's law gives mean system time one divided by mu minus lambda. This includes both waiting and processing. Setting that mean to at most one hundred milliseconds, with a service rate of fifty images per second, gives a maximum arrival rate of forty images per second. This bound applies to the isolated Poisson-input server, not automatically to the complete image journey.

## Slide 11. Theory and simulation agree at the server

**Speaker:** Lu Zipeng — **target:** 40 seconds

The curve shows the rapid increase in queueing delay as the arrival rate approaches the processing rate. Simulated means closely follow the theoretical values, with a maximum relative difference of zero point six two percent. At forty images per second, theory gives one hundred milliseconds and simulation gives ninety-nine point three eight milliseconds. Error bars represent pointwise ninety-five-percent confidence intervals. Ten of eleven intervals cover the theoretical mean. We report that outcome explicitly rather than adjusting random seeds to force all points to match.

## Slide 12. The complete chain has a lower latency capacity

**Speaker:** Lu Zipeng — **target:** 45 seconds

Connecting the stages changes the answer. At twenty-five images per second, mean end-to-end delay is ninety-eight point five two milliseconds. At thirty images per second, it rises to one hundred twelve point four eight milliseconds. Therefore twenty-five is the highest tested rate meeting the mean target, not a proven exact threshold. Polling changes the server's arrival statistics, so simply adding an M/M/1 server time is only an approximation. The component plot shows both camera waiting and server processing. Twenty images per second provides more operating margin in the baseline.

## Slide 13. Upgrade radio and processing together

**Speaker:** Lu Zipeng — **target:** 40 seconds

We also compare four designs at the same offered load. The baseline mean is about one hundred seventy-four milliseconds. A faster server alone gives one hundred ten milliseconds, and more bandwidth alone gives one hundred twenty-eight milliseconds. Combining both upgrades gives fifty-seven point three one milliseconds, a reduction of about sixty-seven percent. However, about nine point five percent of images still exceed one hundred milliseconds. The combined upgrade meets the chosen mean target, while a strict reliability requirement would need further design work.

## Slide 14. Design for the whole journey

**Speaker:** Lu Zipeng — **target:** 25 seconds

Our conclusions are threefold. Route capacity matters as well as hop count. Polling delay increases with camera backlog. And an isolated server delay bound is not an end-to-end guarantee. Our code, diagrams and data make these findings reproducible. The next engineering step would be to measure real traffic and processing times, then specify a numerical reliability target. Thank you. We welcome your questions.

# Suggested answers for the question session

**Why use M/M/1 if polling changes the arrival process?** The assignment explicitly requires an M/M/1 node model. We validate that model separately, then simulate the actual scheduler-generated traffic. We do not claim its MEC input remains Poisson.

**What does T include?** In the required M/M/1 task, T is Ws: waiting plus processing at the selected node. Our end-to-end result additionally includes camera polling, grant, radio transmission and backhaul.

**Why is lambda max 40/s in one place but 25/s elsewhere?** Forty is the exact isolated-MEC mean-delay bound for mu=50 and Tmax=0.1. Twenty-five is the highest tested end-to-end rate below the same mean target. Upstream delays consume budget.

**How can two backhaul hops be faster than one?** Each selected link is 1 Gbit/s rather than 100 Mbit/s. For a 1 Mbit image, two serializations and their propagation sum to 2.7 ms, compared with 11 ms directly.

**Is this still OFDMA?** The SBS allocates all RBs to one camera in each visit, then changes the recipient in time. It is a simple central scheduling case; simultaneous multi-camera RB allocation would require different bandwidth and delay calculations.

**Why not use (N−1)τ/2 for polling wait?** That expression describes a particular simultaneous batch or discrete camera position. Our reference image arrives at a random continuous phase, giving a residual wait of C/2. Queued images add backlog, so the loaded mean is C/[2(1−r)].

**What if image sizes are exponential?** At fixed rate R, X/R is exponential with rate R/E[X]. A continuously available transmission server with Poisson input then has an M/M/1 model. Fixed overhead and polling change that simple model.

**Why is the baseline MEC exponential when image size is fixed?** Radio payload duration and AI processing duration are different random variables. The required queue model assumes variable exponential processing, independently of the baseline radio image size.

**Does a 100 ms mean imply every image meets 100 ms?** No. At the isolated-MEC boundary, about 36.8% exceed it. In our upgraded integrated example the miss fraction is about 9.51%. A reliability requirement needs its own probability target.

**Are the inputs measured from a real factory?** No. They are explicit illustrative assumptions because the brief supplies no numerical values. The results are conditional on those inputs.

**What is the main limitation?** Constant SNR and fixed cyclic reservations simplify real scheduling. Actual traffic, processing variability, retransmissions, competing cells and finite buffers must be measured or modelled before deployment.

**Why do not all 95% intervals contain theory?** Confidence intervals have a repeated-sampling interpretation and are pointwise. With eleven intervals, universal coverage is not guaranteed. We report all results and retain the original seeds.
