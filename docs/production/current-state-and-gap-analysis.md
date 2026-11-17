# KerfPulse current state and gaps

Scope is the local source tree and saved benchmark artifacts. This document records the replay baseline before the fresh-data change. The [acceptance matrix](acceptance-and-evidence-matrix.md) owns verification of subsequent stages.

## Architecture observed before this stage

| Area | Observed implementation |
|---|---|
| Dataset and training | `pdm/dataset.py` verifies the pinned publisher CSV and translates observed cuts, gaps and conflicts. `pdm/validation.py` runs nested workpiece and recipe holdouts. `pdm/benchmark.py` compares the first drafted inspection on each complete life. |
| Inference and policy | `pdm/inference.py` evaluates exported standardized multiclass logistic coefficients. `pdm/gateway.py` selects a fold model using an archived cutter identifier and computes current and fused heads. `pdm/policy.py` applies the demonstration calendar and caps optional releases. |
| Persistence and delivery | `pdm/worker.py` consumes MQTT QoS 1, writes reading, draft and outbox events through `pdm/store.py`, then acknowledges. Store uses SQLite for local development or PostgreSQL in Compose. `pdm/api.py` serves scoped snapshots and polls durable events for SSE; clients use a resume cursor. |
| Application | `web/src/App.tsx` renders the replay, performance, evidence and data screens. Planner actions approve, dismiss or record completion. Session ownership and role checks exist in the API. |
| Deployment | `compose.yaml` defines API, gateway, worker, PostgreSQL and Mosquitto. Host web binding is loopback. The Docker image consumes previously built model material and the verified CSV. MQTT is private to the local network and anonymous in the engineering profile. |
| Verification | `tests/` covers inference, parsing, policy, API isolation and replay persistence. `web/tests/dashboard.spec.ts` exercises the browser and reconnect. `scripts/verify_live.py` and `scripts/stress_replay.py` are separate transport and replay load harnesses. Their historical outputs do not certify a new build. |

## Evidence chronology

- Publisher study describes 968 recorded cuts, 14 cutters, one Haas VF-1 milling 42CrMo4, 12 current and eight vibration channels. Local parsing retains 952 usable pre-damage observations, 60 positive five-cut outcomes, 21 gaps and a quarantined conflicting pair at cutter 2 cut 34. Cutter 11 had no preceding cut to score. [Study](https://doi.org/10.1038/s41597-025-04923-y)
- Earlier **3/14** results belong to the earlier checkpoint. The matched nested workpiece policy experiment yields **2/14** timely for current-only or periodic, **1/14** for decision-aware or fused. Recipe holdout yielded **1/14** per policy. AP for current plus context is approximately **0.355** on workpiece holdout and **0.335** on recipe holdout. Workpiece Brier is **0.0502**. These are one-machine results. [Training evidence](../02-dataset-and-training.md) · [Detailed metrics](../08-performance-analysis.md)
- Earlier release notes recorded that the sustained measurement was pending. The later saved 600-second run with 12 subscribers received **175 events**, **0.292/s**, about **59.67 s p95** to SSE. Its 12 initial runs represented at most 600 records before completion and replenishment never occurred within the measurement window. This failed replay scenario is a regression check. It cannot certify sustained offered load at 20 events/s. [Stress output](../../artifacts/replay-stress-final.json)
- The prior 50-cycle Compose smoke observed **9.779 ms** gateway-to-ingest p95. The broker restart test retained 50 unique ordinals with 11 vibration releases. These are different workloads and measurements from the stress scenario. [Compose smoke](../../artifacts/live-integration.json) · [Restart evidence](../../artifacts/broker-recovery.json)

## Findings register

| ID and severity | Evidence and consequence | Correction, owner and verification | Status at baseline |
|---|---|---|---|
| F-01 High | `pdm/gateway.py` selects a held-out head by archive cutter ID. An unseen tool is outside that inference path. | ML/backend release a separate artifact with a feature and domain contract. Score an unseen ID with label-free input and compare deployed coefficient parity. | Fresh stage scope |
| F-02 High | No qualified physical mapping, raw extraction parity or independent machine. A matching feature name alone does not establish compatibility. | OT/ML map units, channels, timing and segmentation, compare paired captures, then run independent and prospective evaluation. | Physical evidence pending |
| F-03 High | `pdm/store.py` establishes a connection per transaction; gateway waits for publish, worker commits per event and SSE polls database. Capacity target failed before/during persistence. | Platform instrument timing, test pooling and delivery refactors with calibrated load, repeat 12-run regression and 20/s gate. | Observed failed gate |
| F-04 High | Demo session identity, private anonymous MQTT, local launch. Customer scopes, revocation, device ACLs and authenticated operations missing. | Security/platform qualify OIDC plus site/asset grants, per-device TLS ACLs and negative authorization tests. | Production gate open |
| F-05 High | First-draft replay outcome shows 2/14 timely. Refit and delivery performance cannot establish useful field policy. | Research and site owner preregister cost/workload thresholds, mature outcomes and field comparison. | Model gate open |
| F-06 High | No bounded field spool or durable receipt integrated across device and persistence. Broker ACK alone cannot retire source evidence. | OT/platform add stable IDs, durable receipts and spool recovery with DB/broker failure injection. | Proposed |
| F-07 Medium | Research replay drafts and feedback are a limited workflow; real scheduling, assignment, expiry and outcome labeling need distinct semantics. | Product/backend keep replay intact, implement review history for fresh data, version calendars and implement full lifecycle before plant use. | Partly scoped |
| F-08 Medium | Charts and JS dominate cold-load bytes. Emulated constrained-mobile LCP was 7.70 s. | Frontend defer heavy modules and measure on declared browser profiles. | Historical failed profile |
| F-09 High | Separate staging, restore, release promotion and oversight evidence absent from existing smoke. | Platform/release verify installation and backup restoration, pin compatible artifact bundle, rehearse application/model rollback. | Qualification pending |

Check this document against the [feature contract](sensor-and-feature-contract.md), [acceptance matrix](acceptance-and-evidence-matrix.md) and [claims register](claims-and-limitations.md) before a demo or release.
