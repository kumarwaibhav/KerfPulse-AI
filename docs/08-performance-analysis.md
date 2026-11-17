# KerfPulse AI performance and validation

This report evaluates the local recorded-telemetry release on 17 November 2026. Start with [How KerfPulse works](07-how-kerfpulse-works.md) for source details, model setup, architecture and a screen-by-screen walkthrough.

## Model quality and maintenance decisions

There were 60 positive cuts among 952 scored cuts. A positive cut was followed by recorded damage within five cut positions. A system that always predicts no damage would report 93.7% cut accuracy and detect zero positives. Average precision (AP) summarizes how well near-damage cuts rise in the ranking. The reference AP for an uninformative ranking is approximately 0.063 on this sample. ROC AUC describes ranking of positive against negative cuts. Brier score averages squared probability error, where lower is better. A constant probability of 6.3% yields a Brier score of about 0.059. [Why precision–recall matters for rare events](https://doi.org/10.1371/journal.pone.0118432)

| Holdout | Inputs | AP | ROC AUC | Brier |
|---|---|---:|---:|---:|
| Workpiece groups | Age and cutting context | 0.218 | 0.710 | 0.0578 |
| Workpiece groups | Current plus context | **0.355** | **0.862** | **0.0502** |
| Workpiece groups | Current, vibration and context | 0.305 | 0.843 | 0.0589 |
| Cutting recipe and linked workpieces | Age and cutting context | 0.184 | 0.655 | 0.0586 |
| Cutting recipe and linked workpieces | Current plus context | **0.335** | **0.866** | **0.0515** |
| Cutting recipe and linked workpieces | Current, vibration and context | 0.292 | 0.847 | 0.0594 |

At a 0.50 cutoff on **five-cut risk**, the workpiece current model correctly flagged **20 of 60** positive cuts and flagged **22 of 892** negative cuts. That is 47.6% precision, 33.3% recall and 2.47% false-positive rate. It missed 40 positives. Recipe holdout detected 19 of 60 with 22 false positives. Mean predicted risk was 7.43% and 6.90%, respectively, against 6.30% observed. This describes calibration on the archive. Every test tool was run to damage, so the score cannot be read as a calibrated failure probability for a production fleet with different maintenance behavior.

The independent reviewer reproduced all 5,712 nine-class probability vectors across both protocols from the exported coefficients and verified artifact hashes. Maximum absolute discrepancy was `1.11e-15`. A separate workpiece-group bootstrap of the saved predictions yields 95% intervals of approximately **−0.008 to +0.209 AP** and **−0.0224 to −0.0010 Brier** for current minus fused on workpiece holdout. These intervals resample retained predictions and omit retraining and machine-to-machine uncertainty. Current has better observed results, with a wide interval for the AP advantage.

The actual inspection criterion is more demanding. A cut can justify a break when the observed damage falls two to five cuts after that break. There were **53 actionable cuts**, and workpiece current achieved AP **0.300** against **0.276** for fused. At 0.50, current crossed on eight actionable and 11 other cuts. Crossings repeat over one life. The benchmark records one first draft per tool.

| Policy, three-cut calendar and 0.50 threshold | Timely | Premature | Late | No draft | Vibration releases | Serialized JSON |
|---|---:|---:|---:|---:|---:|---:|
| Current only | 2 | 3 | 1 | 8 | 0 | 3.97 MB |
| Periodic, every fourth eligible cut | 2 | 3 | 1 | 8 | 232 | 4.59 MB |
| Decision-aware | 1 | 3 | 2 | 8 | 60 | 4.13 MB |
| Always fused | 1 | 3 | 2 | 8 | 952 | 6.52 MB |

Decision-aware released **74% fewer vibration summaries** than periodic and sent **10.1% fewer total serialized bytes**. Compared with always fused it sent **36.7% fewer bytes**. This measures JSON payload size for a standardized replay envelope. MQTT framing, TCP/TLS overhead and eventual cloud bills are outside the calculation. Current-only sent the least data and tied periodic on timely slots. Decision-aware and periodic shared the same maximum quota and spent different amounts. A future efficiency comparison needs policies matched on actual spend.

One tool explains the timely difference between decision-aware and periodic. For tool 2, at cut 46, the current actionable probability was about 0.51 and the fused estimate about 0.49. The proposed break after cut 48 would have preceded observed damage at cut 50. The additional modality suppressed the draft in the selective policy. A paired 5,000-replicate tool bootstrap gives −7.1 percentage points with a 95% interval from −21.4 to 0.0. All four policies gave 1/14 timely on recipe holdout. This sample leaves substantial uncertainty about performance on new tools.

Threshold sensitivity reveals a tradeoff. For current-only on workpiece holdout, threshold 0.20 gave four timely, five premature and five no-draft outcomes. Threshold 0.65 gave three timely and eleven no-draft outcomes. A stricter cutoff can suppress an early first draft and leave room for a later timely draft. This sweep is descriptive. Choosing a deployment threshold from these held-out results would invalidate their role as a final evaluation. Use new runs or an inner decision-tuning protocol with measures of inspection cost and missed damage.

## Platform and browser verification

- **Correctness.** Thirty Python tests and four Chrome browser tests passed. Coverage includes isolation, input contracts, invalid probabilities and ordinals, duplicate ingestion, restart generations, order transitions, quota enforcement, model hash/feature behavior, first-cut damage, paired replay, export, and SSE recovery after forcibly closing the stream socket. The earlier broker interruption retained 50 source ordinals exactly once, with 11 expected periodic releases.
- **Gateway.** Full traversal of 14 tool lives by four policies exercised 3,952 records, of which 3,808 were scored cut records. Model export parity held, terminal features were absent and prefix violations were zero. Local per-event generation p95 was 0.68 ms. A separate 50-cycle Compose smoke measured 9.8 ms p95 from gateway event creation to persistence-worker receipt.
- **Chrome.** One browser replay measured 550 ms median, **1.17 s p95** and 1.63 s maximum from gateway event creation to the browser SSE callback. First chart appeared in 1.42 s and approval became visible in 338 ms. The chart resized without horizontal overflow at five viewport widths from 360 to 1440 px. No page or console errors were observed. This was a smoke profile on the same host as separate activity and should not be interpreted as multi-user browser latency.

| Fresh Chrome visit | Runs | Median largest content paint | Median start-replay readiness | CLS |
|---|---:|---:|---:|---:|
| Local desktop | 5 | 0.82 s | 1.39 s | 0.03 |
| Local mobile viewport | 5 | 0.71 s | 1.05 s | 0.04 |
| Emulated 1.6 Mbps mobile with 150 ms latency and 4× CPU slowdown | 3 | 7.70 s | 9.57 s | 0.04 |

The initial visit transferred about **975 kB**, including **823 kB JavaScript**. Chart and canvas chunks made up **545 kB** of JavaScript and loaded eagerly. The tested server returned JavaScript without compression or explicit asset cache directives. Slow-mobile results exceed the 2.5 s LCP target. These emulated values are lab measurements. Field-user percentile metrics and Interaction to Next Paint require separate collection. [Core Web Vitals definitions](https://developers.google.com/search/docs/appearance/core-web-vitals)

### Sustained concurrent replay

The agreed target was at least 20 events/s for ten minutes and p95 under two seconds. An isolated local Compose project replayed the same recorded cutter life in 12 runs, across four demo sessions. Each run requested 100 ms pace with periodic vibration, and each client followed its SSE feed. The Docker engine reported four CPUs and 3.33 GiB available memory on the Ryzen 7 7435HS host. SSE timing measures client receipt using event and receipt wall clocks. The ten-minute window and throughput use the test client's monotonic clock.

| Measure | Result |
|---|---:|
| SSE readings received during measurement | 175 |
| Average delivered readings/s | **0.292** |
| Readings delivered by minute | 42, 13, 15, 17, 16, 15, 17, 15, 13, 12 |
| Gateway to ingestion p95 | **59.42 s** |
| Gateway to SSE subscriber p50 / p95 / p99 | **43.80 / 59.67 / 62.76 s** |
| Completed 50-cut runs inside the test window | **0 of 12** |
| Observed order violations or HTTP exceptions in the harness | 0 |
| Final PostgreSQL status after backlog drained | 12 runs completed, 600 readings |

**The sustained target failed on throughput and latency.** The similar ingestion and SSE tail timings put most of the measured delay before or during persistence. The running code polls each SSE stream every 250 ms, opens a PostgreSQL connection per store transaction and rechecks the session in each loop. The gateway scans runs and waits for MQTT publication, and the worker commits one reading at a time. These are plausible sources of contention. The exact share attributable to each requires profiling or a controlled change. The test covers contention in a local single-worker stack. It does not establish a maximum production capacity across other hardware or deploy configurations.

A follow-up control started 12 new replays with zero SSE subscribers. Snapshots taken around 60–61 seconds showed **45 persisted source positions and zero completed runs**. The comparable first sustained window delivered 42 positions with SSE. Removing subscribers did not recover throughput in this control. Focus the first profiling pass on gateway polling and MQTT acknowledgements, broker backlog, and worker connection and commit time. The API polling pattern remains a separate scalability concern. [Gateway publication](../pdm/gateway.py) · [Worker acknowledgment](../pdm/worker.py) · [Store transactions](../pdm/store.py) · [SSE polling](../pdm/api.py)

## Readiness verdict and priorities

| Rank | Finding | What closes it |
|---|---|---|
| High | Sustained concurrent replay misses the throughput and latency budgets | Instrument broker backlog and per-stage transaction latency. Measure pooled PostgreSQL connections and changed SSE delivery in an A/B load test, then rerun the same ten-minute gate. |
| High | Inspection-window coverage is 2/14 for the default policy on one testbed | Tune decisions in training folds using inspection costs. Evaluate on independent machines and then in shadow mode against technician-reviewed outcomes. |
| High | Plant rollout needs customer authentication, deployment verification, machine integration and an operational monitoring/restore test | Establish the actual tenancy and identity provider, use a documented controller mapping, and complete a hosted/pilot acceptance run. |
| Medium | Slow mobile has 7.70 s lab LCP and the dashboard fetches large chart chunks immediately | Defer chart code until a replay or chart is visible. Serve compressed immutable build assets and rerun the browser profile. |
| Medium | Vibration policies spend different actual amounts under the same cap | Compare matched-spend baselines and measure timely inspection, review workload and payload jointly. |

KerfPulse has a complete, executable model pipeline for the current research scope. It acquires measured data, constructs grouped splits, fits and evaluates models, exports them, and performs online inference during replay. The dataset and evaluation design are research-based. The application and model still need the acceptance evidence above for plant production use. The work does not yet establish a new algorithm or a measured improvement in real maintenance outcomes.

## Research contribution and limits

The useful research contribution is a reproducible test of the whole maintenance decision: completed-cut data availability, a hard prefix transmission limit, a future inspection slot, and the first decision scored against observed damage. The app also turns gaps, conflicting records, deferrals and work-order outcomes into observable audit events. Grouped holdouts make the benchmark more relevant to unseen tools and recipes.

Adaptive sensing and CNC prognostics already exist. A recent edge fault-warning study uses a cheap sensor screen before more expensive confirmation. Other authors combine adaptive sensor fusion with uncertainty-aware CNC tool prognostics. A same-benchmark paper classifies tool condition into four states. Its classification metrics answer a different question from our held-out damage horizon and timed inspection metric. Our contribution is the combination and the transparent evaluation. Lower feature traffic came with lower observed timely coverage compared with periodic release in the workpiece test. [Active sensor acquisition](https://doi.org/10.3390/s26165065) · [CNC prognostics digital twin](https://www.mdpi.com/2075-1702/14/3/335) · [Same-benchmark classification study](https://link.springer.com/article/10.1186/s44147-026-01210-4)

KerfPulse is useful as a deployment rehearsal, an operator-training walkthrough and a model-policy comparison bench. It lets a team inspect what evidence a planner sees and what arrives too early or too late. Validating a plant workflow requires independent machines, naturally maintained tools, operational base rates, actual communication links and technician-reviewed inspection outcomes. The Stiehl set provides a starting point for independent machine testing with a distinct measured flank-wear threshold. [Stiehl multi-machine dataset](https://data.mendeley.com/datasets/zpxs87bjt8/3)

## Reproduce the measurements

From the repository root after setup:

```powershell
.venv/Scripts/python.exe -m scripts.analyze_model
.venv/Scripts/python.exe -m pytest -q
npm.cmd --prefix web run test:e2e
.venv/Scripts/python.exe scripts/verify_live.py
```

Use an isolated local Compose project for the sustained test. This harness uses multiple clients and repeatedly replays the same measured tool life through independent runs. It checks event order, counts actual SSE records received per minute, and keeps the latency measurement separate from browser rendering.

```powershell
$env:PDM_HTTP_PORT = '18087'
docker compose -p kerfpulse-performance up --no-build -d --wait
.venv/Scripts/python.exe scripts/stress_replay.py --workers 12 --seconds 600 --output artifacts/replay-stress-final.json
docker compose -p kerfpulse-performance down
```


## Later continuation: fresh assessment and pooled replay, 2026-11-17

This result follows the earlier failed capacity checkpoint; do not replace or merge the experiments. Bounded psycopg-pool connections replaced a new PostgreSQL connection per transaction. The same 300-event short HTTP workload at 10/s saved every unique assessment before and after the change; p95 response changed from 623.312 ms to 61.002 ms. The workload repeats authentic publisher features with new event IDs and an explicit demonstration clock; no physical telemetry is claimed.

The 12-client replay regression then received 46,439 events over 600 seconds, 77.398/s, with SSE p50 196.454 ms, p95 386.826 ms, p99 714.671 ms and ingest p95 188.947 ms. Every one-minute window exceeded 1,200 events and the harness reported no ordering/count failures; target_passed is true. Tested image: sha256:ae08ef3ae1eb107b8b942301ce060be17bb6120542e36fb6df2a9e99a4817e37. This is a local achieved-load observation, not a guaranteed maximum capacity or a production SLO. Pooling does not change the earlier model AP, calibration, or weak timed-inspection findings.

Raw results: artifacts/fresh-http-load-before-pool.json, artifacts/fresh-http-load-after-pool.json and artifacts/replay-stress-after-pool-600s.json. Reproduce using the explicit local URL:

```powershell
.venv/Scripts/python.exe scripts/stress_fresh.py --url http://127.0.0.1:8000 --seconds 30 --rate 10
.venv/Scripts/python.exe scripts/stress_replay.py --url http://127.0.0.1:8000 --workers 12 --seconds 600 --output artifacts/replay-stress-repeat.json
```
