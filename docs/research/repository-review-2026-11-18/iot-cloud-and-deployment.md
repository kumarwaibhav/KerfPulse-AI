# IoT, cloud deployment and maintenance-assistant reference audit

Research date: **18 November 2026, Asia/Calcutta**. Scope: four user-supplied public GitHub repositories. This is a source audit and design assessment, not a reproduction of their training runs or deployment benchmarks.

## Decision

These references provide useful engineering patterns, but **none supplies a verified, transferable CNC model that establishes KerfPulse's accuracy or factory readiness**. Keep KerfPulse's measured steel-cut dataset, grouped evaluation, source qualification and human review. Borrow design ideas through independent implementation. Do not replace the measured-data research path with generated telemetry or treat a dashboard, an LSTM artifact, or an LLM explanation as validation.

Most useful transfers are explicit data/model cards and modality ablations from `smart-factory-predictive-maintenance`, versioned data processing and model-promotion structure from Jeremyugo, and the separation of inference, document-grounded explanation, notifications and infrastructure from AWS. The small ESP32 project demonstrates physical-to-model wiring, while also showing why units, authentication, provenance and safety boundaries need explicit contracts. Evidence for each assessment follows below.

## Method and evidence limits

- GitHub pages and REST metadata were checked online. Each repository was shallow-cloned into ignored `.research-cache/references/` and pinned to the commit below. Metadata and tracked-file inventories are saved in ignored `artifacts/reference-research/iot/snapshot.json`.
- Source, configuration, requirements, selected tests, notebook code and saved metric files were read. Notebook JSON and Keras archive JSON were inspected as data. No repository code, notebook, dependency installer, cloud template, MQTT publisher, model loader or supplied binary was executed. Pickles were not deserialized.
- A byte-for-byte SHA-256 comparison verified that Biswajit's bundled CSV matches the official UCI download. This verifies file identity and **synthetic provenance**, not predictive validity. No reference data were added to KerfPulse training.
- **Code-confirmed** means present in the pinned source. **Reported** means a repository artifact or README asserts a result. **Inference/risk** means a consequence reasoned from source, without reproducing execution. Absence findings refer to the inspected tracked tree, not all unpublished work an author might have.
- Code and dataset rights are separate. GitHub metadata identifies MIT-0 for AWS; no root license was found in the other three pinned tracked trees. This audit does not copy their implementation into KerfPulse. AI4I's upstream dataset has its own CC BY 4.0 terms. [UCI dataset and license](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset).

| Reference | Pinned commit | Commit date, UTC | Archive state at check | Code license found | Primary value |
|---|---|---|---|---|---|
| biswajit328/smart-factory-predictive-maintenance | `3c763f3263b4d7352951e17cf0f10b8bf3143a91` | 2026-04-25 | Not archived | None found | Stronger prototype structure, honest simulation boundary, grouped neural training |
| Jeremyugo/End-to-End-Predictive-Maintenance-IoT-with-GenAI | `0e8f47bc25b3f1140b4d6a08a6e0b73cf1dcaa84` | 2025-07-17 | Not archived | None found | Delta/Spark, MLflow, orchestration and maintenance retrieval patterns |
| aws-samples/sample-predictive-maintenance | `a8aca4ed9b8bdc202d5802a81d40738b87ece01d` | 2026-04-21 | Not archived | MIT-0 | Cloud service decomposition, document-grounded analysis and notifications |
| Akshithakarampuri/AIoT-predictive-maintenance | `bc3242607de3d604aaa38ed4739360e3c086fe76` | 2026-08-23 | Not archived | None found | Small sensor → MQTT → model → dashboard example |

Commit dates describe code snapshots. They do not establish a recent independent evaluation or a 2026 production certification. All source links below are immutable commit links.

## 1. Neural smart-factory project: substantive implementation, synthetic evidence

Repository: [biswajit328/smart-factory-predictive-maintenance](https://github.com/biswajit328/smart-factory-predictive-maintenance/tree/3c763f3263b4d7352951e17cf0f10b8bf3143a91).

### Data and actual prediction tasks

The bundled `predictive_maintenance.csv` has 10,000 rows and 339 positive `Machine failure` labels. Its SHA-256 is `dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e`, identical to the official UCI AI4I 2020 CSV downloaded during this audit. These are synthetic rows, not recorded CNC run-to-failure signals. UCI identifies six inputs, rule-derived failure mechanisms and synthetic construction. [Bundled CSV][B1], [upstream provenance](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset).

**v1** is a current-row failure classifier. Inputs include machine type, air/process temperature, speed, torque and tool wear. Feature engineering adds temperature difference, mechanical power and interactions. IDs and the five failure-mode target columns are excluded. Splitting uses stratified random rows, approximately 70/10/20; preprocessing is fitted inside the training pipeline. Those are appropriate precautions for this tabular experiment. They do not establish a future warning horizon or independent physical-machine generalization. [Feature exclusions and transformations][B2], [split and preprocessing][B3].

**v2** is a different task. The simulator generates machine IDs, five-minute timestamps, ten numeric sensor channels, degradation progression and failure events. Vibration, pressure, current, acoustics and humidity are generated. The same hidden fault-progress variable affects multiple channels before a generated breakdown; the horizon label asks whether breakdown occurs in the next eight steps. This yields a nominal 40-minute simulated warning task. It does not recover real temporal structure from AI4I. The data card correctly distinguishes this simulation from factory telemetry. [Simulator and horizon construction][B4], [data card][B5].

### Model and evaluation

v2 builds 18-reading windows. Thermal, mechanical and nominal electrical branches use Conv1D layers, normalization and global pooling; branch embeddings concatenate before dense sigmoid classification. The electrical grouping includes pressure and acoustic channels as well as current, so it is a design grouping rather than a physical sensor taxonomy. Training uses class weighting and validation PR-AUC early stopping. [Architecture and training][B6].

Machine IDs are partitioned **before selecting training/validation/test windows**. Branch scalers fit only training inputs. Validation probabilities select the threshold; test probabilities are evaluated afterward. This is a useful anti-window-leakage pattern. Ten generated machines still come from one simulator, and two held-out generated machines are not two independently commissioned machines. No confidence interval or independent real-machine result was found in the inspected evaluation artifacts. [Machine split and scaling][B7], [threshold selection][B8].

| Saved result, not rerun | v1 AI4I classifier | v2 generated time series |
|---|---:|---:|
| Test rows/windows | 2,000 | 206 |
| Positive test rows/windows | 68 | 16 |
| ROC-AUC | 0.9848 | 0.9928 |
| Average precision, artifact field `pr_auc` | 0.8619 | 0.8890 |
| Precision | 0.9322 | 0.6667 |
| Recall | 0.8088 | 1.0000 |
| Brier score | 0.0097 | 0.0397 |

These numbers are saved repository outputs, not independently reproduced results. Different data, tasks, prevalence and grouping prevent ranking them against KerfPulse's grouped pre-damage steel-cut experiment. [v1 metric artifact][B9], [v2 metric artifact][B10]. The v2 artifact also records a negative mechanical-branch ablation drop: removing that branch slightly improved saved AP. That cautions against assuming all fusion branches help. Ablation is informative here; it is not a causal explanation of a physical fault. [Branch-ablation artifact][B11].

### Working application shape and gaps

The API implements health/metadata, complete-reading prediction, event fusion, stream reset and a simulation endpoint. Prediction first returns a warm-up state until enough readings exist. A separate HTML dashboard service and a static site are included. These are actual serving paths, not only README diagrams. [API source][B12].

Sensor events fuse by `(machine_id, timestamp)` once all required sensors arrive. Machine windows live in memory. Incomplete fusion rows have no inspected TTL/cap, and restart clears them. Redis/Postgres connectivity is probed, but the inspected serving implementation does not use those services as a durable assessment/receipt store. Compose presence is therefore not evidence of transactional durability. [Fusion buffer][B13], [inference state][B14], [infrastructure probes][B15].

The MQTT bridge batches JSON and retries a failed HTTP batch, but its queue is unbounded and process-local. Broker configuration permits anonymous access and disables persistence; no TLS or credential handling appears in the bridge connection. These are demo choices, not patterns to adopt for plant ingress. [Bridge][B16], [broker configuration][B17].

**Source-review security concern:** `/simulate/run` accepts output and dashboard paths without a shown authorization dependency or path allowlist; those values reach CSV/HTML writers. If this API were exposed, clients could request writes wherever service permissions allow. Exploitability was not executed. Do not transplant this endpoint into KerfPulse. [Request and route][B18], [CSV writer][B19], [HTML writer][B20].

Tests cover model smoke training, features, coercion, warm-up, reset, dashboard responses and simulator behavior. CI includes Python 3.10/3.11 tests and separate lint/format/type checks. This audit did not execute them or verify their current CI status. Authentication/tenant isolation, durability and prospective operator utility are not demonstrated by those tests. [Tests][B21], [CI configuration][B22]. The model card itself identifies prototype intent and missing real-telemetry/maintenance-workflow validation. [Limitations][B23].

**KerfPulse transfer:** maintain an equally visible data/model card, add real-data modality ablations, make warm-up/abstention explicit, and measure sensor completeness. Preserve KerfPulse's existing durable receipt/worker/outbox architecture. Do not import synthetic channels, memory-only transport or headline accuracy.

## 2. Wind-turbine GenAI project: useful data-platform ideas, major validation gaps

Repository: [Jeremyugo/End-to-End-Predictive-Maintenance-IoT-with-GenAI](https://github.com/Jeremyugo/End-to-End-Predictive-Maintenance-IoT-with-GenAI/tree/0e8f47bc25b3f1140b4d6a08a6e0b73cf1dcaa84).

### What code implements

Spark reads landing-directory JSON/Parquet, appends to bronze Delta tables and uses checkpoints. The ingestion code sets `availableNow=True`: it processes currently available files and terminates, rather than maintaining a permanently connected machine broker session. Silver aggregation computes hourly energy mean and sensor standard deviations/percentiles per turbine. A second implementation attempts watermarked processing and keyed Delta upserts. This is substantive data engineering, but it is **file-stream ingestion**, not proof of live OT connectivity. [Ingestion][J1], [aggregation and upsert][J2].

The tracked tree includes turbine, historical-health and incoming-data tables. Delta transaction metadata records 30 turbine metadata rows and 512 historical-health rows in their initial writes. Sensor names are generic A–F, with energy and geographical/model/state context. No industrial lab citation, physical sensor specification, calibrated units, commissioning record or independently licensed benchmark provenance was found in the inspected tree. Consequently, measured-versus-generated origin remains **unverified**, not assumed measured and not declared synthetic without evidence. [Turbine metadata transaction][J3], [health schema/transaction][J4].

### Label and leakage risks

Training data join hourly sensor aggregates to turbine metadata and historical health **only by turbine ID**. Health `start_time` and `end_time` are not applied as interval conditions. All matching health records can attach to each hourly reading. The target then maps `abnormal_sensor == 'ok'` to `ok`, otherwise `faulty`. This is an important source-confirmed limitation: the target is sensor-status classification, not a defined future-failure or RUL horizon. Many-to-many/time-misaligned labels are a risk because the historical table includes intervals. Their observed effect was not measured here. [Training-set join][J5], [health interval schema][J4].

The training module stratifies random rows, retaining 75% for training. It does not split by turbine or time. A turbine's repeated hours and joined historical states can therefore occur on both sides. The Hyperopt objective fits a random forest and optimizes **F1 on the same training rows**. Fifty such trials do not replace grouped inner validation. These two choices prevent treating a high saved score as evidence of future-turbine generalization. [Split][J6], [optimization objective][J7].

The saved score file reports F1 0.99, precision 0.98, recall 0.99. It is an artifact claim, not reproduced. The evaluation also compares registered models on the saved test set and uses that comparison for promotion, so this set is serving model-selection duties. The comparison explicitly sets `pos_label='ok'`; fault-specific recall must be reported separately before interpreting operational fault detection. No calibrated probabilities, uncertainty intervals or first actionable maintenance timing were found in the inspected evaluation flow. [Saved score][J8], [evaluation and promotion][J9].

### Model registry, orchestration and human use

The pipeline includes imputation/encoding/scaling, MLflow artifacts, a label-decoding wrapper, a registration gate and Dagster train → evaluate → register assets on a three-hour schedule. These are useful design motifs. Automatic repeated training does not itself justify automatic release: the comparator must use an immutable validation protocol, required classes, drift gates and rollback. [Model pipeline][J10], [registration][J11], [Dagster graph][J12].

The Streamlit interface is primarily chat. Users supply an OpenAI key; the agent can load a registered model for a provided feature row, retrieve turbine information and retrieve similar reports. It uses `gpt-3.5-turbo` for conversation and local Ollama embeddings with Chroma for retrieval. Numeric sensor strings are embedded as text; no metric-learning or retrieval-quality evaluation was found. A conversational response is not measured fault validity or a controlled work order. [Chat and model calls][J13], [prediction/retrieval tools][J14], [vector representation][J15].

No named tenant/site/asset authorization, append-only approval/inspection workflow or CMMS transaction was found in inspected UI/tools. Do not give an LLM authority to infer provenance, qualify a source, promote a model or command machinery. Tool response schemas and evidence citations need independent enforcement if this idea is adopted.

### Reproducibility, cost and rights

Several modules import `utils.config`, but that module is absent from the pinned tracked tree. The root requirements list only six LangChain/Pydantic packages, omitting major imports such as Spark/Delta, MLflow, scikit-learn, Hyperopt, Evidently, Dagster and Streamlit. No root license, automated test suite or deployment stack was found. These are source-level reproducibility blockers; no fresh-install experiment was attempted. OpenAI conversation has an external paid-service dependency; using local embeddings does not make the full path free. [Imports][J1], [requirements][J16], [OpenAI call][J13].

**KerfPulse transfer:** retain append-only raw evidence and reproducible materialized features; build explicit model-promotion receipts and an operator evidence drawer. Optional document retrieval can explain an already-issued assessment, with approved documents and visible citations. Avoid introducing Spark/Delta for the laptop workload until measured scale warrants it. Do not adopt random-hour splitting, training-F1 optimization or interval-free health joins.

## 3. AWS sample: service architecture reference, not a free measured-data benchmark

Repository: [aws-samples/sample-predictive-maintenance](https://github.com/aws-samples/sample-predictive-maintenance/tree/a8aca4ed9b8bdc202d5802a81d40738b87ece01d).

### Data and infrastructure flow

The sample separates SiteWise/OPC-UA ingestion, S3 storage, SageMaker inference, Lambda analysis, Bedrock document retrieval, SNS notification and Grafana visualization. CDK/CloudFormation files exist for these components. This is useful integration reference material, but deployment was not executed or costed in an AWS account. [Stack source][A1], [sample architecture][A2].

Training uses UCI **AI4I 2020 synthetic data**, not CNC vibration/current waveforms from a lab. The preprocessing notebook removes IDs and failure-mode target columns, encodes type and makes a random 80/20 split. The supplied OPC-UA workshop server separately generates temperature, speed, torque, wear and failure values with `Math.random()`. A functioning live transport carrying generated values is not a live measured dataset. [Preprocessing][A3], [OPC-UA generation][A4], [UCI provenance](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset).

SageMaker training uses XGBoost image version `0.90-1`, `binary:hinge`, depth 5 and 100 rounds. This produces hard class decisions, not calibrated future-risk probabilities. Its target identifies failure in the current synthetic row. No defined CNC horizon, wear progression or continuous RUL follows from this target. [Training configuration][A5].

### Evaluation and inference defects worth learning from

The evaluation notebook later reads `fulldataset.csv`, which preprocessing wrote from **all rows before splitting**. That data contains training rows. Therefore the shown evaluation procedure does not establish an independent held-out score. There is also a CSV-header mismatch: the full CSV is written without a header, then read with default header inference and accessed as column `'0'`. The notebook requests asynchronous endpoint invocation after a shown endpoint configuration lacking asynchronous settings. These are static execution risks, not failures reproduced in this review. [Full-data export][A6], [evaluation input and request][A7], [endpoint configuration][A8].

The intake Lambda reads only `Records[0]`, drops duplicate timestamp/alias pairs, pivots tags and maps aliases by keyword. It hard-codes encoded type to 1. Most importantly, missing columns, empty data or all-null required rows cause an entire **dummy normal-feature row** to replace unavailable evidence. That fallback violates KerfPulse's measured-data and fail-closed requirements. Preserve a validation failure and abstention instead. [Lambda evidence preparation][A9].

The inference Lambda calls a hard-coded endpoint, converts outputs to integers and writes CSV results back to S3. The analysis Lambda selects failed rows, retrieves manual context when configured, generates advice, stores a report and sends SNS. That is an alert/explanation chain. It does not implement scheduling feasibility, assigned work orders, qualified source approval or a human inspection outcome loop. [Inference output][A10], [analysis and SNS][A11].

Reliability concern from source: handlers catch exceptions and return a `statusCode: 500` object. For asynchronous S3-triggered Lambda, merely returning such an object is not the same as raising a failed invocation for service retry handling. Both handlers inspect the first event record only. No idempotent durable job/notification key is visible in these functions; repeated trigger delivery could repeat analysis or SNS. This is a reason to keep KerfPulse's receipt deduplication and transactional outbox, not a claim that this sample was load-tested and failed. [Inference handler][A9], [analysis handler][A11].

### Security, tests, deployment cost and rights

The CDK code includes positive safeguards: S3 public-access blocking and SSL enforcement, notebook placement in a VPC, encrypted notebook volume and controlled service roles. It also includes broad-policy suppressions and sample-resource deletion policies that require a deployment-specific review. These are infrastructure constructs, not a SaaS human authorization model. No KerfPulse-compatible named tenant/asset workflow is supplied. [S3 controls][A1], [notebook and policies][A12].

The only inspected unit test imports a nonmatching `project.project_stack` namespace and contains a commented example assertion. It does not demonstrate the current inference or Bedrock workflow. No model reproduction or end-to-end cloud test was run here. [Test file][A13].

This stack is **not an always-free architecture**. Training provisions `ml.c4.4xlarge`; endpoint configuration uses `ml.m5.xlarge`; other files create notebook, private networking/interface endpoints, OpenSearch, storage and Bedrock/SNS/Lambda usage. The README itself lists cost drivers and manual cleanup for endpoints/knowledge bases. No current dollar estimate is asserted here because regional pricing, usage and account credits were not queried. KerfPulse's zero recurring infrastructure budget excludes adopting this full stack as its default. [Instance configurations][A5], [endpoint][A8], [cost and cleanup notes][A14].

AWS code license is MIT-0; AI4I and included manuals have separate provenance/rights. The sample's license does not certify every industrial document or incoming customer dataset for redistribution. [Code license][A15], [UCI dataset license](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset).

**KerfPulse transfer:** independently implement clear transport → validated inference → evidence-grounded explanation → reviewed action boundaries. Keep local open-source services and explicit qualification. If later adding a cloud adapter, use provider-neutral event contracts, durable retry/deduplication, cost budgets and an integration-test environment. Never copy the dummy-data fallback or publish an inflated all-data score.

## 4. ESP32/LSTM project: actual inference wiring, unverified RUL science

Repository: [Akshithakarampuri/AIoT-predictive-maintenance](https://github.com/Akshithakarampuri/AIoT-predictive-maintenance/tree/bc3242607de3d604aaa38ed4739360e3c086fe76).

### Actual implementation

Firmware reads LM35-style temperature ADC conversion, current ADC voltage and a digital vibration pin. It publishes three fields every two seconds over MQTT. Therefore the vibration value is a switch state, not a high-rate waveform; the current expression converts ADC counts to volts without the shown sensor sensitivity/offset needed to establish amperes. Treating this input as interchangeable with industrial vibration statistics or calibrated current would be invalid. [Sensor conversion and publication][K1].

The listener applies a supplied scaler, appends each reading to a global 20-row sequence and calls `model.predict`. When full, it emits a binary fault message if predicted days are below seven, writes a latest JSON file and rewrites a CSV history. This is an actual inference call in source, not a random score generator. No time-gap validation, source calibration check or model-domain qualifier is shown. [Listener][K2].

Safe archive inspection, without loading Keras weights, found input shape `[None,20,3]`, LSTM layers 64 and 32 units, Dropout layers and one linear output. Archive metadata records Keras 3.10.0 and a February 2026 save timestamp. This establishes artifact structure, not training quality or meaningful day units. The tracked tree contains no training data, training program, split manifest, failure-label definition, scaler-fit provenance or evaluation predictions. Consequently MAE ~0.4 days, RMSE ~0.48 and R² ~0.99 are **README-only claims**, not independently verifiable results. [Artifacts in tracked tree][K3], [reported metrics][K4].

### Operator UI and inconsistencies

Streamlit polls JSON/CSV, displays three readings, RUL, trend graphs, a raw-packet panel and a computed health percentage. That percentage is `clip(days/30*100)`, not a calibrated probability of good condition. The UI changes severity at three/seven days, while the listener uses seven days and README describes seven/fourteen-day bands. One threshold policy should govern UI and decision generation. [Dashboard status][K5], [derived health gauge][K6], [listener threshold][K2].

The firmware can stop a motor based on the received fault flag. This is actuator code, not evidence of a validated safety-rated control system. It must not be adopted into KerfPulse's software-only read-only advisory scope. [Actuation][K7].

### Reproducibility and operational risks

- Listener expects model/scaler files in the working-directory root, but committed artifacts are under `models/`. Following documented root commands therefore needs an unshown path correction or file move. [Paths][K8], [artifact directory][K3].
- Requirements pin two different Plotly versions and omit imported TensorFlow and Paho MQTT. A clean install plus listener start is not reproducibly specified. No install was attempted in this review. [Requirements][K9], [imports][K2].
- Public broker, shared topics and port 1883 appear without TLS or credentials. No per-device identity, org/site/asset scope or receipt acknowledgement is implemented in this listener. Its one global buffer could mix publishers using the shared topic. [Broker and buffering][K2].
- JSON overwrites are not shown as atomic, CSV history is reread and rewritten for every prediction, and no retention/backpressure/restart recovery is present. The dashboard suppresses read exceptions. These choices may hide partial writes or stale data; they do not demonstrate reliable real-time service. [Persistence][K10], [dashboard file handling][K11].
- No code license, dataset license, automated test suite, deployment configuration or independent industrial validation was found in the pinned tree. No third-party credentials were reproduced in this report.

**KerfPulse transfer:** show a concise signal → model → operator trace, with warm-up status, last received timestamp and model identity. Require exact units, sampling contract and source identity. Keep all actuator control outside the product's qualified scope. A supplied LSTM binary without training provenance is not an acceptable replacement model.

## 5. Cross-project comparison and implications

| Question | Smart-factory neural | Turbine GenAI | AWS sample | ESP32/LSTM |
|---|---|---|---|---|
| Verified measured CNC benchmark? | No: verified AI4I synthetic plus generated stream | Provenance unverified; generic turbine tables | No: AI4I synthetic plus generated OPC-UA | Hardware read code exists; no training benchmark/provenance |
| Actual inference implementation? | Yes, RF and temporal CNN services | Yes, MLflow RF prediction tool | Yes, hosted XGBoost invocation | Yes, scaler + LSTM call |
| Valid future horizon? | v2 only: simulated next eight steps | No: joined sensor-status label | No: current-row failure flag | RUL days asserted; label construction absent |
| Strongest evaluation practice | Machine-disjoint simulated windows, training-only scaler, validation threshold | Pipeline preprocessing and saved evaluations | Excludes failure-mode target columns | No evaluation code found |
| Key validity risk | Simulator tests its own generated structure; only two test machines | Interval-free joins, random hours, train-F1 selection | Full-data evaluation; dummy missing-evidence fallback | Unknown data/split, units and target; undocumented model provenance |
| Reliable live ingress evidence? | Process-local fusion/retry; anonymous broker | Checkpointed file ingestion; no inspected OT client | Cloud integration templates; workshop data generator | Plain shared public MQTT, global sequence |
| Closed maintenance workflow? | Recommendation strings; no inspected tickets | Chat/retrieval; no reviewed work-order transaction | Reports and SNS; no assigned/closed work-order loop | Fault flag and motor action; no inspection outcomes |
| Recurring paid dependency? | Not inherently, local open-source stack | OpenAI chat as implemented | Yes, several AWS services | Blynk/cloud services and physical hardware assumptions |
| Comparable evidence to beat KerfPulse? | No matched dataset/task/protocol | No | No | No |

The pattern is clear: connecting sensors, inference and a UI is already established practice. Multi-sensor fusion, LSTM/CNN scoring, RAG explanations, MQTT and MLflow are not sufficient novelty claims. These repositories establish existing implementation overlap; they do not constitute a complete literature novelty search. KerfPulse's defensible research question remains whether causally budgeted optional sensing and calendar-aware first-inspection decisions improve utility under domain abstention. Existing negative acquisition results must remain visible, and new experiments must be predeclared and evaluated on independent evidence before superiority is claimed.

## 6. Concrete adoption backlog for KerfPulse

These are recommendations, not changes completed by this research agent.

| Priority | Independently implement or preserve | KerfPulse target | Acceptance evidence |
|---|---|---|---|
| P0 | Preserve fail-closed evidence validation; forbid normal-value substitution | `pdm/qualification.py`, `pdm/operational_processing.py` | Missing/invalid/unqualified input creates unavailable score with reason; immutable receipt and lineage remain |
| P0 | Source contract includes units, sample frequency, extractor hash and source identity | Device registration, qualification contracts, operator source health | Wrong unit/profile/model/extractor revision abstains; never silently map switch vibration to waveform features |
| P0 | Audit target/feature temporal alignment before fitting | Dataset construction and grouped validation | Historical state joins use known-at-prediction time; training/test components disjoint; future outcome only in labels |
| P1 | Keep durable receipt, retry and transactional outbox instead of process-memory bridge patterns | `pdm/device_ingest.py`, `pdm/edge_spool.py`, `pdm/operational_processing.py` | Restart, duplicate, conflict, gap and retry tests reconcile receipt/assessment/outbox without repeated effect |
| P1 | Expose warm-up, stale, incomplete, unsupported and quarantined states as distinct UI outcomes | `web/src/SourceHealth.tsx`, `web/src/Operations.tsx` | Operators can identify reason and next action; zero risk is never displayed for unavailable evidence |
| P1 | Versioned model card, modality ablation and operating-threshold provenance | Model registry/research artifacts and model evidence UI | Every displayed result links dataset fingerprint, task, group split, model digest, threshold and uncertainty |
| P1 | Evaluate first actionable inspection rather than only per-row AP | `pdm/acquisition_research.py`, `pdm/policy.py` | Separate support coverage, timely/premature/missed outcomes and acquisitions before intervention; no outer-test tuning |
| P2 | Approved-document retrieval attached to an existing assessment | New optional explanation service, scoped operations API | Retrieval citation identifies document/revision; tenant scope enforced before retrieval; no LLM model/source promotion or actuation |
| P2 | Validation-gated model promotion with approval/rollback receipt | Existing qualification/registry pipeline | Validation cannot reuse final confirmation set for release selection; failed gates leave active model unchanged |
| P3 | Provider-neutral industrial/cloud adapters only after local reliability gates | Future protocol adapters and deployment profiles | Authenticated read-only feed, bounded retries, declared costs, restore/reconciliation evidence and site acceptance |

For the laptop deployment, adding Spark, Delta, multiple LLM agents or managed cloud services is not justified by these references alone. Measure workload first. A smaller durable, auditable system with honest abstention is more relevant to this product than a larger stack with unsupported plant claims.

## Source index

[B1]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/data/predictive_maintenance.csv
[B2]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/src/features.py#L24-L51
[B3]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/src/preprocess.py#L30-L75
[B4]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/src/v2_streaming.py#L55-L163
[B5]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/docs/DATA_CARD.md#L13-L63
[B6]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/src/v2_neural.py#L177-L269
[B7]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/src/v2_neural.py#L102-L151
[B8]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/src/v2_neural.py#L276-L300
[B9]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/outputs/metrics.json#L1-L58
[B10]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/outputs/v2/neural_metrics.json
[B11]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/outputs/v2/branch_importance.csv
[B12]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/src/v2_api.py#L117-L203
[B13]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/src/v2_inference.py#L125-L163
[B14]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/src/v2_inference.py#L166-L207
[B15]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/src/infra_health.py
[B16]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/src/v2_mqtt_bridge.py#L32-L100
[B17]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/deploy/mosquitto.conf#L1-L4
[B18]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/src/v2_api.py#L79-L82
[B19]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/src/v2_inference.py#L288-L318
[B20]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/src/v2_dashboard.py#L145-L152
[B21]: https://github.com/biswajit328/smart-factory-predictive-maintenance/tree/3c763f3263b4d7352951e17cf0f10b8bf3143a91/tests
[B22]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/.github/workflows/ci.yml
[B23]: https://github.com/biswajit328/smart-factory-predictive-maintenance/blob/3c763f3263b4d7352951e17cf0f10b8bf3143a91/docs/MODEL_CARD.md#L80-L112
[J1]: https://github.com/Jeremyugo/End-to-End-Predictive-Maintenance-IoT-with-GenAI/blob/0e8f47bc25b3f1140b4d6a08a6e0b73cf1dcaa84/src/data_ingestion.py#L58-L86
[J2]: https://github.com/Jeremyugo/End-to-End-Predictive-Maintenance-IoT-with-GenAI/blob/0e8f47bc25b3f1140b4d6a08a6e0b73cf1dcaa84/src/data_transformation.py#L50-L140
[J3]: https://github.com/Jeremyugo/End-to-End-Predictive-Maintenance-IoT-with-GenAI/blob/0e8f47bc25b3f1140b4d6a08a6e0b73cf1dcaa84/data/bronze/bronze_turbine/_delta_log/00000000000000000000.json#L1-L2
[J4]: https://github.com/Jeremyugo/End-to-End-Predictive-Maintenance-IoT-with-GenAI/blob/0e8f47bc25b3f1140b4d6a08a6e0b73cf1dcaa84/data/bronze/bronze_historical_turbine_status/_delta_log/00000000000000000000.json#L1-L2
[J5]: https://github.com/Jeremyugo/End-to-End-Predictive-Maintenance-IoT-with-GenAI/blob/0e8f47bc25b3f1140b4d6a08a6e0b73cf1dcaa84/src/create_training_set.py#L40-L52
[J6]: https://github.com/Jeremyugo/End-to-End-Predictive-Maintenance-IoT-with-GenAI/blob/0e8f47bc25b3f1140b4d6a08a6e0b73cf1dcaa84/src/train_ml_model.py#L177-L200
[J7]: https://github.com/Jeremyugo/End-to-End-Predictive-Maintenance-IoT-with-GenAI/blob/0e8f47bc25b3f1140b4d6a08a6e0b73cf1dcaa84/src/train_ml_model.py#L234-L246
[J8]: https://github.com/Jeremyugo/End-to-End-Predictive-Maintenance-IoT-with-GenAI/blob/0e8f47bc25b3f1140b4d6a08a6e0b73cf1dcaa84/model/evaluation/score.txt#L27-L29
[J9]: https://github.com/Jeremyugo/End-to-End-Predictive-Maintenance-IoT-with-GenAI/blob/0e8f47bc25b3f1140b4d6a08a6e0b73cf1dcaa84/src/evaluate_model.py#L147-L190
[J10]: https://github.com/Jeremyugo/End-to-End-Predictive-Maintenance-IoT-with-GenAI/blob/0e8f47bc25b3f1140b4d6a08a6e0b73cf1dcaa84/src/train_ml_model.py#L85-L129
[J11]: https://github.com/Jeremyugo/End-to-End-Predictive-Maintenance-IoT-with-GenAI/blob/0e8f47bc25b3f1140b4d6a08a6e0b73cf1dcaa84/src/register_model.py#L41-L86
[J12]: https://github.com/Jeremyugo/End-to-End-Predictive-Maintenance-IoT-with-GenAI/blob/0e8f47bc25b3f1140b4d6a08a6e0b73cf1dcaa84/dagster_pipeline/model_training_pipeline.py#L12-L51
[J13]: https://github.com/Jeremyugo/End-to-End-Predictive-Maintenance-IoT-with-GenAI/blob/0e8f47bc25b3f1140b4d6a08a6e0b73cf1dcaa84/ai_agent/agent.py#L19-L60
[J14]: https://github.com/Jeremyugo/End-to-End-Predictive-Maintenance-IoT-with-GenAI/blob/0e8f47bc25b3f1140b4d6a08a6e0b73cf1dcaa84/ai_agent/tools.py#L30-L125
[J15]: https://github.com/Jeremyugo/End-to-End-Predictive-Maintenance-IoT-with-GenAI/blob/0e8f47bc25b3f1140b4d6a08a6e0b73cf1dcaa84/ai_agent/vector.py#L15-L84
[J16]: https://github.com/Jeremyugo/End-to-End-Predictive-Maintenance-IoT-with-GenAI/blob/0e8f47bc25b3f1140b4d6a08a6e0b73cf1dcaa84/requirements.txt#L1-L6
[A1]: https://github.com/aws-samples/sample-predictive-maintenance/blob/a8aca4ed9b8bdc202d5802a81d40738b87ece01d/scale_predictive_maintance_poc/combined_stack.py#L28-L115
[A2]: https://github.com/aws-samples/sample-predictive-maintenance/blob/a8aca4ed9b8bdc202d5802a81d40738b87ece01d/README.md#L35-L66
[A3]: https://github.com/aws-samples/sample-predictive-maintenance/blob/a8aca4ed9b8bdc202d5802a81d40738b87ece01d/notebooks/Data_Pre-Processing.ipynb#L284-L360
[A4]: https://github.com/aws-samples/sample-predictive-maintenance/blob/a8aca4ed9b8bdc202d5802a81d40738b87ece01d/iot-assets/sitewise_workshop_server_v2.js#L350-L364
[A5]: https://github.com/aws-samples/sample-predictive-maintenance/blob/a8aca4ed9b8bdc202d5802a81d40738b87ece01d/notebooks/ModelTraining-Evaluation-and-Deployment.ipynb#L148-L171
[A6]: https://github.com/aws-samples/sample-predictive-maintenance/blob/a8aca4ed9b8bdc202d5802a81d40738b87ece01d/notebooks/Data_Pre-Processing.ipynb#L350-L363
[A7]: https://github.com/aws-samples/sample-predictive-maintenance/blob/a8aca4ed9b8bdc202d5802a81d40738b87ece01d/notebooks/ModelTraining-Evaluation-and-Deployment.ipynb#L290-L341
[A8]: https://github.com/aws-samples/sample-predictive-maintenance/blob/a8aca4ed9b8bdc202d5802a81d40738b87ece01d/notebooks/ModelTraining-Evaluation-and-Deployment.ipynb#L226-L244
[A9]: https://github.com/aws-samples/sample-predictive-maintenance/blob/a8aca4ed9b8bdc202d5802a81d40738b87ece01d/lambda/inference_lambda.py#L7-L76
[A10]: https://github.com/aws-samples/sample-predictive-maintenance/blob/a8aca4ed9b8bdc202d5802a81d40738b87ece01d/lambda/inference_lambda.py#L78-L129
[A11]: https://github.com/aws-samples/sample-predictive-maintenance/blob/a8aca4ed9b8bdc202d5802a81d40738b87ece01d/lambda/process_anomaly_data.py#L85-L300
[A12]: https://github.com/aws-samples/sample-predictive-maintenance/blob/a8aca4ed9b8bdc202d5802a81d40738b87ece01d/scale_predictive_maintance_poc/combined_stack.py#L285-L470
[A13]: https://github.com/aws-samples/sample-predictive-maintenance/blob/a8aca4ed9b8bdc202d5802a81d40738b87ece01d/tests/unit/test_project_stack.py#L1-L15
[A14]: https://github.com/aws-samples/sample-predictive-maintenance/blob/a8aca4ed9b8bdc202d5802a81d40738b87ece01d/README.md#L545-L588
[A15]: https://github.com/aws-samples/sample-predictive-maintenance/blob/a8aca4ed9b8bdc202d5802a81d40738b87ece01d/LICENSE#L1-L14
[K1]: https://github.com/Akshithakarampuri/AIoT-predictive-maintenance/blob/bc3242607de3d604aaa38ed4739360e3c086fe76/esp32_code/esp.ino#L53-L75
[K2]: https://github.com/Akshithakarampuri/AIoT-predictive-maintenance/blob/bc3242607de3d604aaa38ed4739360e3c086fe76/mqtt_listener.py#L15-L97
[K3]: https://github.com/Akshithakarampuri/AIoT-predictive-maintenance/tree/bc3242607de3d604aaa38ed4739360e3c086fe76/models
[K4]: https://github.com/Akshithakarampuri/AIoT-predictive-maintenance/blob/bc3242607de3d604aaa38ed4739360e3c086fe76/README.md#L32-L39
[K5]: https://github.com/Akshithakarampuri/AIoT-predictive-maintenance/blob/bc3242607de3d604aaa38ed4739360e3c086fe76/app.py#L62-L84
[K6]: https://github.com/Akshithakarampuri/AIoT-predictive-maintenance/blob/bc3242607de3d604aaa38ed4739360e3c086fe76/app.py#L126-L151
[K7]: https://github.com/Akshithakarampuri/AIoT-predictive-maintenance/blob/bc3242607de3d604aaa38ed4739360e3c086fe76/esp32_code/esp.ino#L77-L95
[K8]: https://github.com/Akshithakarampuri/AIoT-predictive-maintenance/blob/bc3242607de3d604aaa38ed4739360e3c086fe76/mqtt_listener.py#L19-L32
[K9]: https://github.com/Akshithakarampuri/AIoT-predictive-maintenance/blob/bc3242607de3d604aaa38ed4739360e3c086fe76/requirements.txt
[K10]: https://github.com/Akshithakarampuri/AIoT-predictive-maintenance/blob/bc3242607de3d604aaa38ed4739360e3c086fe76/mqtt_listener.py#L99-L142
[K11]: https://github.com/Akshithakarampuri/AIoT-predictive-maintenance/blob/bc3242607de3d604aaa38ed4739360e3c086fe76/app.py#L40-L57
