# KerfPulse reference-project research and adoption decisions

Review date: **18 November 2026, Asia/Calcutta**. Twelve supplied links reduce to **11 unique repositories** because CNC Guard appeared twice. Three specialist research agents inspected immutable source snapshots; a fourth review pass spot-checked decisive claims across the completed reports. This is source research, not an execution benchmark of those projects.

## Read the detailed reports

| Report | Repositories | Coverage |
|---|---|---|
| [CNC and datasets](cnc-and-datasets.md) | Bosch, Shengwei, Pasindu | Authentic signals, labels, leakage, forecasting contracts, missing artifacts and physical units |
| [Platforms and operator workflows](platform-and-operator-workflows.md) | CNC Guard, Dhanush, Predictive Maintenance MCP, PHAEMOS | Actual inference, evidence contracts, access scopes, work orders, windows, edge recovery and rights |
| [IoT, cloud and deployment](iot-cloud-and-deployment.md) | Biswajit, Jeremyugo, AWS sample, Akshithakarampuri | Data origin, neural pipelines, temporal labels, cloud costs, MQTT, deployment and model promotion |

Reports contain exact commits, inspected-file evidence, immutable GitHub citations, limitations and module-specific adoption backlogs. Downloaded sources and API receipts remain in ignored `artifacts/reference-research/` and `.research-cache/`; they are not part of the application or publication bundle. No upstream script, notebook, executable model, cloud deployment or broker connection was run. No upstream source was copied into KerfPulse runtime. Embedded repository instructions were treated as material to inspect.

## Main decision

**Keep the measured steel-cut research task and durable, qualified operations pipeline. Add Bosch as a separately labeled process-anomaly experiment. Improve decision timing and operator workflow before adding larger models or conversational features.**

These references establish that sensor dashboards, MQTT, Random Forest/LSTM/CNN models, fusion, RAG and work orders already exist. Combining those components is not sufficient research novelty. Their metrics do not establish a benchmark that KerfPulse can legitimately claim to beat: targets, data origin, prevalence, splits and operating conditions differ.

## All 11 references: what they contribute

| Repository | Source-confirmed role and evidence | Value to KerfPulse | Adoption boundary |
|---|---|---|---|
| **Bosch CNC_Machining** | Official measured 2 kHz three-axis vibration; 1,702 recordings across three machines; normal/anomalous process labels | Best additional real-signal resource for domain-shift and anomaly research | No established cutter-damage horizon or RUL labels. Preserve separate task/model. Code BSD-3; data CC BY 4.0. [Pinned source](https://github.com/boschresearch/CNC_Machining/blob/d60581d6a3ab6015dcc5488c3d76112bb8e1bcb1/README.md) |
| **Shengwei CNC-Predictive-Maintenance** | Streamlit classifier workbench; CSV has 1,214 rows, 20 positives; provenance unverified. Default index audit: all 200 test windows share raw input rows with training | Interactive feature, class-imbalance and threshold exploration | Reject overlapping-window evaluation and pre-split supervised selection. MIT code does not resolve unidentified dataset origin. [Pinned implementation](https://github.com/shengwei-peng/CNC-Predictive-Maintenance/blob/20308e0cc0093882f66d3602d15c2d234b0f311b/utils.py) |
| **Pasindu lathe system** | MQTT/InfluxDB/PatchTST/API/dashboard structure; synthetic generator; missing weights/scalers; training/serving context conflict | Forecast-to-later-outcome view and retraining-job concept | Do not adopt generated readings, missing-output normal defaults or inconsistent units. README MIT assertion needs complete license evidence. [Pinned inference](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/blob/99d3897a10d1e8abb0b36a0b00d5c95799125782/FYP-Machine-Condition-Prediction/services/inference_service.py) |
| **CNC Guard Dashboard** | Randomly generated NASA-style CSVs; formula-based RUL; random confidence; canned chat/diagnosis paths | Clear alert → evidence → technician-booking journey | UI inspiration only; generated confidence cannot become evidence. No code license found. [Pinned generator](https://github.com/Lokeshloki159/cnc-guard-dashboard/blob/600ef0dfb489dd0d54d9ac1cca21d22de60fa97d/server/generateNasaData.js) |
| **Dhanush predictive-maintenance-system** | Saved Random Forest inference on synthetic AI4I; current-row classification | Single/batch inference and transparent metric presentation | Different task from future CNC failure. No code license found. [Pinned training](https://github.com/Dhanush-1213/predictive-maintenance-system/blob/e8436b9fb292f8e7572677931439c143eaeb25b7/backend/train_model.py) |
| **Predictive Maintenance MCP** | Bearing diagnostics, evidence/attestation contracts, append-only lineage and blinded evaluation; separate ML fallback has split/transform weaknesses | Strongest evidence and claim-discipline reference | Do not confuse fault hypotheses with calibrated failure probabilities. MIT code versus bundled noncommercial sample-data terms. [Pinned repository](https://github.com/LGDiMaggio/predictive-maintenance-mcp/tree/2171f0969baef0c7aa3dbeb50846d2ccc0c7b63c) |
| **PHAEMOS** | IoT platform, Isolation Forest, alerts, tickets, maintenance windows and edge spool | Strongest workflow breadth and maintenance-window reference | Missing-model zero/normal fallback and inconsistent asset checks must not transfer. AGPL software requires a separate reuse decision. [Pinned repository](https://github.com/phaemos/phaemos/tree/c54f922b442c7813516ce4cc8c1bab933970716c) |
| **Biswajit smart-factory** | Real RF/CNN training and serving; verified synthetic AI4I plus generated temporal streams; machine-disjoint simulated windows | Training-only transforms, model/data cards, branch ablation and warm-up states | Simulated test machines are not independently measured machines. Keep durable storage and authenticated ingress. No root code license found. [Pinned neural pipeline](https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/src/v2_neural.py) |
| **Jeremyugo turbine GenAI** | Spark/Delta, MLflow, Dagster and retrieval; unverified sensor origin; time-interval-free health joins and training-F1 tuning | Data versioning, orchestration and explicit candidate promotion structure | Do not inherit label join, row split or reported F1 as a valid future-machine benchmark. Paid chat dependency as implemented. No root code license found. [Pinned training](https://github.com/Jeremyugo/End-to-End-Predictive-Maintenance-IoT-with-GenAI/blob/0e8f47bc25b3f1140b4d6a08a6e0b73cf1dcaa84/src/train_ml_model.py) |
| **AWS sample-predictive-maintenance** | Managed-cloud inference/explanation/notification templates; synthetic AI4I and generated OPC-UA; missing evidence becomes dummy normal features | Service boundaries and document-grounded maintenance explanations | Keep unavailable state instead of dummy values. Full-dataset evaluation is not held-out evidence. Managed services are not a zero-recurring-cost default. MIT-0 code. [Pinned repository](https://github.com/aws-samples/sample-predictive-maintenance/tree/a8aca4ed9b8bdc202d5802a81d40738b87ece01d) |
| **Akshithakarampuri AIoT** | ESP32 → MQTT → scaler/LSTM → dashboard; model structure present, training provenance absent | Concise signal-to-operator trace and explicit warm-up | Digital vibration switch and ADC voltage cannot substitute industrial waveform/current contracts. Public broker/global buffer unsuitable for scoped operations. No code license found. [Pinned repository](https://github.com/Akshithakarampuri/AIoT-predictive-maintenance/tree/bc3242607de3d604aaa38ed4739360e3c086fe76) |

The detailed reports provide narrower line-level evidence and distinguish README-only statements from source-confirmed behavior. Static concerns are not assertions that a live upstream service was exploited. Missing license findings mean no checked complete grant was found, not that ownership or all possible permission has been adjudicated.

## Dataset decision: answer the right industrial question

| Data/task | What it can evaluate | What it cannot establish | Decision |
|---|---|---|---|
| Existing Piecuch–Żabiński 2025 measured Haas steel-cut summaries | Completed-cut damage-horizon ranking and inspection-policy research across connected workpiece groups | General steel-industry accuracy, continuous during-cut detection, independent-machine utility or field-confirmed RUL | Retain primary cutter task; original source and release artifacts unchanged |
| Bosch real acceleration | Process anomaly detection and machine/period/process shift under a newly frozen protocol | Five-cut tool failure or remaining tool life without corresponding labels | Add separate research track, not a replacement target |
| AI4I and generated temporal streams in references | Software demonstrations and explicitly synthetic algorithm exercises | Measured production CNC performance | Exclude from KerfPulse's measured-data accuracy claims |
| Unidentified CNC/turbine CSVs or supplied LSTM binaries | Source-code review and artifact inspection | Authenticity, target validity, industrial generalization or commercial dataset rights without further evidence | Do not train the release on them |

No reviewed repository supplies a free public live plant feed with guaranteed valid labels. Historical measured data can be streamed through a real-time software pipeline. That tests transport, inference and workflow; it does not turn historical observations into newly commissioned plant measurements. Fresh customer measurements require the separate qualification path.

## Revised implementation pathway

### Gate A — trustworthy operator access and evidence

Preserve default abstention, exact model/source binding and immutable assessment lineage. Finish named OIDC sessions and exact organization/site/asset read grants before expanding operational history or human write actions. Authenticate every detail/history/export/stream path consistently; demo research permissions never become factory permissions.

Expose missing, stale, incomplete, pending, unsupported and quarantined states separately. A missing model or sensor must never yield zero risk, “healthy,” random confidence or substituted normal values. Existing named-access implementation and actual verification status are recorded in [identity documentation](../../production/named-access-and-identity.md) and the [current build checkpoint](../../production/pipeline-stage-checkpoint.md).

### Gate B — research objective before model capacity

Current acquisition-regret experiment produced no timely inspections. Current-only matched outcomes without optional acquisitions. Lower acquisition count alone is therefore not a useful maintenance improvement. The immediate per-cut objective differs from the first-inspection endpoint, and acquisition continues after that first decision is fixed.

Freeze a new exploratory first-stop protocol: matched support/calendar/budgets, acquisitions only before intervention, training-only group-disjoint selection, equal-tool loss and simple policy baselines. Preserve all previous outputs. Outer outcomes already informed this direction, so confirmation requires new independent evidence. See [objective audit](../../production/research-objective-audit.md).

Acceptance requires paired timely/premature/missed/no-opportunity outcomes, domain coverage, actual acquisition spend and group uncertainty. AP and model size alone cannot satisfy this gate. No promise to beat a benchmark is made.

### Gate C — independent raw-signal anomaly track

Acquire Bosch recordings from the pinned manifest with verified bytes/hashes and attribution. Inspect channel units, finite values, machine/process/period combinations and durations. Split full recordings before constructing windows; learn all transforms only on training partitions. Audit machine holdout and later-period shift separately. Start with transparent statistical/spectral features and one simple detector; add one temporal candidate only after those baselines and contracts pass.

Report recording-level metrics, false-alarm burden, coverage and uncertainty. File-level labels do not localize anomaly onset inside every window. Give the webapp a separate task/model identity; do not display this anomaly score as cutter RUL.

### Gate D — close the engineer workflow

Add assessment-linked alert episodes, acknowledgment, assignment, due time, actual maintenance windows, findings and resolution. Enforce authorized state transitions and retain the immutable assessment/model/source revision. An alert booking is not evidence that inspection occurred. Link later verified outcomes to original predictions rather than rewriting predictions retrospectively.

Operator views should show source → quality/qualification → model evidence → feasible action → recorded outcome. Prioritize traceability and actionable states over an LLM chat screen. Any later document assistant must retrieve approved, scoped material and cite its revision; it cannot approve models or operate machinery.

### Gate E — reliability and field acceptance

Keep bounded durable edge spool, matching receipts, semantic deduplication, transactional assessment/outbox and authenticated source identity. Test offline recovery without subsequent sensor input, restart races, conflict quarantine, full buffers and revoked grants. Complete declared capacity/soak, encrypted restore, rollback and retention checks before release claims.

Factory readiness still requires physically commissioned read-only sources, independent-machine/prospective validation and site acceptance. These repository reviews cannot replace those gates.

## What changed versus what remains proposed

This research produced three detailed reports and this consolidated adoption plan. Existing KerfPulse implementation work continues separately: named sessions/scoped source reads, source-health diagnostic corrections, isolated browser verification and a startup-race fix. Current executed checks belong in the production checkpoint, not in upstream benchmark tables.

No reference model was promoted, benchmark data silently substituted, third-party source copied, or new predictive superiority established. The strongest useful path remains a smaller qualified system whose scores, uncertainty and human actions can be traced end to end.
