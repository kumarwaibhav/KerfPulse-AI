# CNC references: dataset, learning and operational evidence audit

Review date: 18 November 2026, Asia/Calcutta. Scope: the three user-supplied repositories below, their exact current default-branch commits, and their relevance to KerfPulse. This is a source and data audit, not a deployment certification or a reproduction of published model accuracy.

## Decision

**Bosch is the strongest additional measured-data resource in this group. Keep it as a separate process-anomaly research task.** Its labels do not support CNC cutter remaining life or a five-cut damage forecast. Shengwei provides a compact educational classifier workbench, but its default split shares raw observations between training and test. Pasindu illustrates a longer MQTT-to-forecast application, but its public snapshot lacks required model/scaler artifacts and contains inconsistent serving contracts. None supplies evidence that KerfPulse has beaten an industrial benchmark or become factory qualified.

## What was inspected and preserved

GitHub repository metadata, exact HEAD commits and complete non-truncated recursive trees were fetched with authenticated read-only GitHub API requests. Forty-one small text/notebook/configuration files were downloaded for inspection. Shengwei's CSV was additionally downloaded and parsed with Python's standard library. No third-party installation, notebook, training, service, generator, broker connection, infrastructure provisioner or executable model was run. Existing Bosch sample bytes were rehashed; the remaining approximately 952 MB corpus was not downloaded.

Evidence resides under ignored `artifacts/reference-research/cnc/`: per-owner `metadata.json`, `commit.json`, `tree.json`, fetched `files/`, dataset summaries, a window-index audit and `fetched-file-checksums.json`. These paths are local review evidence, not a redistribution bundle. Some downloaded configuration files contain upstream credential literals; their values are intentionally absent from this report. No credential was tested.

| Repository | Pinned HEAD | Last commit, UTC | Status at review | Inventory |
|---|---|---|---|---|
| [Bosch CNC_Machining](https://github.com/boschresearch/CNC_Machining/tree/d60581d6a3ab6015dcc5488c3d76112bb8e1bcb1) | `d60581d6a3ab6015dcc5488c3d76112bb8e1bcb1` | 2024-06-06 08:37:46 | Archived; GitHub page records 2026-02-19 archival | 1,709 files; 1,702 are HDF5 recordings |
| [Shengwei CNC-Predictive-Maintenance](https://github.com/shengwei-peng/CNC-Predictive-Maintenance/tree/20308e0cc0093882f66d3602d15c2d234b0f311b) | `20308e0cc0093882f66d3602d15c2d234b0f311b` | 2024-07-13 10:03:22 | Public, not archived | Seven files: two Python sources, CSV, README, requirements, license and ignore file |
| [Pasindu lathe system](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/tree/99d3897a10d1e8abb0b36a0b00d5c95799125782) | `99d3897a10d1e8abb0b36a0b00d5c95799125782` | 2025-11-27 08:08:50 | Public, not archived | 90 files, including InfluxDB storage/log files and three model configuration directories |

Dates and counts are observations from the saved API responses; they are not inferred maintenance guarantees. The Bosch companion paper dates to 2022. This review retains it because the user explicitly requested the repository; it must not be relabeled as a 2023–2026 paper.

## 1. Bosch Research CNC_Machining

### Evidence and task

This is a companion dataset and loader, rather than an end-to-end maintenance SaaS. Publisher describes measured Bosch CISS tri-axial acceleration at 2 kHz from three brownfield CNC milling machines and 15 process IDs. Labels identify normal/anomalous process recordings across historical acquisition periods. Code is BSD-3-Clause; dataset is separately CC-BY-4.0. Preserve both attribution sets. [Dataset description and distinct licenses](https://github.com/boschresearch/CNC_Machining/blob/d60581d6a3ab6015dcc5488c3d76112bb8e1bcb1/README.md#L14-L52).

The corpus should not be presented as a live internet feed. Replay can deliver historical measured waveforms through a live software pipeline; that demonstrates processing and latency, while new-machine validity remains a separate question. No cutter-change chronology, wear measurement, remaining-life target or future damage timestamp was established from the inspected materials. That rules out treating `bad` as “will fail within five cuts.”

### Actual inventory, not inferred sample counts

The complete pinned Git tree contains **1,702 HDF5 files totaling 952,229,265 stored bytes**. Counts below were computed from manifest paths. They count recordings, not independent faults, continuous hours, cutters or independent production campaigns. [Pinned data tree](https://github.com/boschresearch/CNC_Machining/tree/d60581d6a3ab6015dcc5488c3d76112bb8e1bcb1/data).

| Machine | Good recordings | Bad recordings | Total | Bad recording fraction |
|---|---:|---:|---:|---:|
| M01 | 485 | 34 | 519 | 6.55% |
| M02 | 617 | 27 | 644 | 4.19% |
| M03 | 530 | 9 | 539 | 1.67% |
| All | 1,632 | 70 | 1,702 | 4.11% |

All process names OP00–OP14 appear somewhere in the manifest. Filename periods are February 2019, August 2019, February 2020, August 2020, February 2021 and August 2021. This does not mean every machine/process/period/class combination has data. A prospective protocol must audit that contingency table before choosing folds.

KerfPulse already retains one authentic file, `data/research/bosch/data/M01/OP00/good/M01_Aug_2019_OP00_000.h5`. This review independently confirmed size **1,434,336 bytes** and SHA-256 **`2f08bdf2b57c9a61d2f2026458c2f6e4396c14bcfc4bd713dee6002f67517df0`**. Earlier local loader evidence records shape 268,288 × 3, float64; that shape was not re-executed in this review. Its approximately 134.144-second duration is calculated using the declared 2 kHz rate. [Publisher sample](https://github.com/boschresearch/CNC_Machining/blob/d60581d6a3ab6015dcc5488c3d76112bb8e1bcb1/data/M01/OP00/good/M01_Aug_2019_OP00_000.h5) · [Prior local evidence](../../production/cuda-research-checkpoint.md).

### Loader and notebook audit

`data_loader_utils.py` reads HDF5 `vibration_data` and optionally attaches a caller-provided class to filename metadata. Its directory walker discards parent paths, so calling it on an arbitrary nested root can misresolve filenames; use explicit manifest paths instead. It eagerly accumulates arrays in lists. The plotting helper hardcodes 2,000 Hz and uses an endpoint-inclusive time axis. For a precise signal axis, use `arange(n)/fs`. [Loader and plotting implementation](https://github.com/boschresearch/CNC_Machining/blob/d60581d6a3ab6015dcc5488c3d76112bb8e1bcb1/utils/data_loader_utils.py#L29-L123).

The five-cell exploration notebook enumerates machine/process/class directories, loads arrays and plots one example. It contains no model-training benchmark, held-out split, probability calibration, measured deployment latency or automated qualification. Loading every uncompressed float64 recording eagerly can require substantially more RAM than the stored compressed corpus size. [Exploration notebook](https://github.com/boschresearch/CNC_Machining/blob/d60581d6a3ab6015dcc5488c3d76112bb8e1bcb1/Data_explorer.ipynb).

### Proposed research protocol: valuable but not yet executed

1. Acquire a manifest-pinned corpus with byte and digest checks; retain source filenames, machine, process, period and label separately from features. Reject malformed HDF5, wrong channel counts, nonfinite values and impossible rate metadata.
2. Partition complete recordings before windowing. Keep all windows from a recording in one partition. Hold out a machine for cross-machine evaluation and separately hold out later periods for drift. Do not average those distinct shifts into one claim.
3. Train a simple spectral/statistical baseline before a temporal encoder: RMS, crest factor, kurtosis, band power and spectral entropy can serve as transparent candidates. Calculate transforms using training data only; calibrate thresholds on training-side validation.
4. Compare normal-only anomaly detection against labeled anomaly classification. These have different supervision and cannot share a “zero-shot” claim. Report PR-AUC, false alarms per normal recording/hour when duration is known, machine-level breakdowns and abstention coverage.
5. Test a single optional raw temporal branch only after signal units, clipping and segmentation are audited. File-level labels do not identify the exact start of an anomaly; avoid silently treating every small window as localized ground truth.
6. Expose a separate “process anomaly” panel with domain/model identity. It must not call the existing cutter-damage model or display unvalidated RUL. Model promotion remains blocked until the new task's qualification contract is satisfied.

These are proposed KerfPulse experiments, not results attributed to Bosch. Three machines and 70 abnormal recordings still provide weak support for broad industrial generalization, and anomalous recordings may be correlated within campaigns. Machine/period performance, uncertainty and missing combinations matter more than impressive pooled window counts.

### End-to-end applicability

There is no backend, web operator workflow, IoT intake, user authorization, CMMS scheduling, model registry or CI test suite in this pinned repository. That is appropriate for a dataset resource. Its value is measured signal diversity and useful domain-shift axes, not reusable production application code. An archived repository can remain valuable data while requiring local dependency pinning and regression tests.

## 2. Shengwei CNC-Predictive-Maintenance

### What the application implements

This is a Streamlit CSV-upload workbench. Operators select one of six classifiers, optional imbalance samplers, window length, number of future steps and holdout size, then run preprocessing, training and plots. This is interactive local model experimentation, not continuous device ingestion. No durable model export, scoped device identity, inspection lifecycle or CMMS write is present in the seven-file snapshot. [Actual UI and execution sequence](https://github.com/shengwei-peng/CNC-Predictive-Maintenance/blob/20308e0cc0093882f66d3602d15c2d234b0f311b/main.py#L5-L89).

The project carries an MIT license. The README calls the CSV historical CNC data, but inspected materials do not identify a lab release, machine identity, acquisition hardware, annotation protocol, maintenance outcome audit or separate source-dataset license. The repository's code license does not establish the origin and rights of an unidentified third-party dataset. Treat measurement provenance as **unverified**, rather than calling it either real industrial ground truth or synthetic. [License](https://github.com/shengwei-peng/CNC-Predictive-Maintenance/blob/20308e0cc0093882f66d3602d15c2d234b0f311b/LICENSE) · [Declared data fields](https://github.com/shengwei-peng/CNC-Predictive-Maintenance/blob/20308e0cc0093882f66d3602d15c2d234b0f311b/README.md#L35-L79).

### Independent CSV audit

Pinned `data/data.csv` is **425,372 bytes**, SHA-256 **`8d1af28bec47e19cb480d20ce5014d6ab511d6ede051a0e36047e40898c40f16`**. Standard-library parsing found **1,214 rows**, 21 columns, no empty cells, 1,194 false labels and **20 true labels (1.65%)**. Columns comprise timestamp, 18 electrical measurements for machine/spindle, RPM and `Anomaly`. No cutter-life identifier or documented failure-time target appears in those columns. [Pinned CSV](https://github.com/shengwei-peng/CNC-Predictive-Maintenance/blob/20308e0cc0093882f66d3602d15c2d234b0f311b/data/data.csv).

Timestamps are ordered from 2023-05-04 21:06:25 to 2023-05-05 13:36:19. Of 1,213 adjacent intervals, 1,136 are one second and 70 are two seconds. Seven other intervals are 13, 14, 228, 317, 1,114, 14,139 and **42,293 seconds**. Therefore “future step” is a next-row label, not a fixed elapsed-time horizon. See `data-summary.json` for derived counts.

### Training and leakage findings

Source inspection found the following, independent of any accuracy claim:

| Severity for adoption | Actual behavior | Consequence |
|---|---|---|
| High | Correlation selection precedes splitting | Test covariates influence retained features |
| High | Overlapping windows precede shuffled `train_test_split` | Train/test share underlying observations |
| High | Estimator object reused across future-step fits | Multi-step vanilla heads can reference the final fitted object |
| High | Oversampling precedes threshold cross-validation | Synthetic/duplicated training points can cross internal folds |
| Medium | No gap-aware segmentation | Windows join distant operating periods |
| Medium | Timestamp enters features | Session/time shortcuts need explicit ablation |
| Medium | No scaling for distance/linear classifiers | Mixed units distort comparability |

These findings follow the order and estimator references in [preprocessing, fitting and splitting](https://github.com/shengwei-peng/CNC-Predictive-Maintenance/blob/20308e0cc0093882f66d3602d15c2d234b0f311b/utils.py#L30-L156). Correlation pruning also removes a variable based on weak pairwise correlation with another input; that is not evidence of irrelevance to the outcome.

**Independent overlap check:** reproducing only default index geometry with NumPy 2.4.2, seed 0, five-row input, one-step target and 200 test windows produced 1,209 windows, of which 1,009 train and 200 test. **All 200 test windows shared at least one raw input row with training.** Thirty-five input-plus-target spans crossed a gap longer than two seconds. This was an audit of indices; no repository code or classifier was executed and no estimate of accuracy inflation is asserted. Results saved in `window-geometry-audit.json`.

The plotting code produces classification reports, balanced accuracy, ROC and precision-recall curves. No committed numeric benchmark, machine-held-out results, calibration analysis or fault-event/lead-time utility evidence was found. Therefore this repository supplies no valid numerical target that KerfPulse can claim to beat. [Evaluation charts](https://github.com/shengwei-peng/CNC-Predictive-Maintenance/blob/20308e0cc0093882f66d3602d15c2d234b0f311b/utils.py#L280-L380).

### Transferable value and boundaries

Useful presentation idea: show class prevalence, precision-recall tradeoff and selected operating threshold together, with the evaluation protocol visible. Threshold tuning and imbalance handling are established methods, not novel contributions. KerfPulse should retain nested component grouping and include simple models before trying more complex ones.

Do not import the split, feature-selection sequence or sampler placement. A corrected comparison would split machine/campaign groups before transforms and window construction, prevent raw-row overlap, preserve gaps, fit samplers inside training folds, instantiate a fresh estimator per horizon and freeze thresholds without outer-test access. Do not use this small provenance-unverified CSV as KerfPulse's principal scientific evidence.

No authentication, tenancy, rate limiting, transactional storage, streaming recovery, deployment manifest or automated tests were found. Requirements pin a large 2024 environment, including scikit-learn 1.5.0, Streamlit 1.36.0 and XGBoost 2.1.0; package age alone is not a vulnerability finding. Dependencies were not installed or security-scanned for this review. [Requirements](https://github.com/shengwei-peng/CNC-Predictive-Maintenance/blob/20308e0cc0093882f66d3602d15c2d234b0f311b/requirements.txt).

## 3. Pasindu Predictive-Maintainance-System-For-Lathe-Machine

### Intended architecture versus checked code

The visible design connects MQTT → InfluxDB → per-workspace PatchTST forecasting → FastAPI → HTML/Chart.js dashboard. Spark distributes workspace training; scripts describe Windows/systemd startup and periodic retraining. This is useful architectural prior art: IoT plus transformer forecasting plus dashboard is already an existing combination. Its existence does not establish fault prevention or research novelty. [HTTP application](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/blob/99d3897a10d1e8abb0b36a0b00d5c95799125782/FYP-Machine-Condition-Prediction/main.py#L3-L71) · [Bridge](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/blob/99d3897a10d1e8abb0b36a0b00d5c95799125782/vm-automation/mqtt_to_influx_bridge_vm.py#L53-L95).

### Data authenticity and training task

`GenerateData.py` creates randomized current, acceleration and temperature values for named workspaces and randomly injects enlarged signals with a 5% branch. Its entrypoint sends these synthetic readings every two seconds. Those readings are useful protocol fixtures, not authentic CNC deterioration or a licensed industrial benchmark. No traceable measured run-to-failure release was identified. [Generator](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/blob/99d3897a10d1e8abb0b36a0b00d5c95799125782/GenerateData.py#L58-L84) · [Injection and entrypoint](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/blob/99d3897a10d1e8abb0b36a0b00d5c95799125782/GenerateData.py#L169-L218).

The inspected training script forecasts six future sensor channels, using 50 context rows and ten future rows, two hidden layers, dimension 128, batch eight and two epochs. It mean-fills and scales the complete series before an 80/20 sequence split, has no purge at overlapping-window boundaries and no timestamp-gap split. Best validation loss is recorded, but corresponding best weights are not restored before final save. These are forecasting experiments, not labeled impending-fault classification, uncertainty-calibrated RUL or maintenance-policy tests. [Configuration](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/blob/99d3897a10d1e8abb0b36a0b00d5c95799125782/spark-apps/train_distributed.py#L35-L62) · [Preprocessing and train loop](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/blob/99d3897a10d1e8abb0b36a0b00d5c95799125782/spark-apps/train_distributed.py#L171-L374).

### Reproduction blockers and inference correctness

| Finding | Evidence | Implication |
|---|---|---|
| Required artifacts missing | Pinned tree contains three model `config.json`/`generation_config.json` pairs, but no model weights or scaler pickle files | Loader skips workspaces without scalers; public snapshot alone cannot forecast |
| Serving context contradicts model | Saved config context is 50; inference hardcodes 1,800, while validation uses 50 | Main path violates trained input contract; runtime reproduction still needed to observe exact library error |
| Forecast units wrong for UI | Scaled predictions stored and returned without inverse transform; dashboard prints A and °C | Numbers do not represent declared engineering units |
| Alert state invented when absent | Dashboard substitutes anomaly score 0.1 when no scores arrive | Missing assessment can appear healthy |
| Stream logging breaks success path | Caller reads `alerts['message']`, but success result contains only `status` | Exception after a forecast; loop catches it, concealing degraded operation |

Source references: [model configuration](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/blob/99d3897a10d1e8abb0b36a0b00d5c95799125782/FYP-Machine-Condition-Prediction/FYP-Machine-Condition-Prediction/model_cnc-mill-5-axis_20251124_093154/config.json#L10-L47), [loader and inference contract](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/blob/99d3897a10d1e8abb0b36a0b00d5c95799125782/FYP-Machine-Condition-Prediction/services/inference_service.py#L78-L207), [dashboard fallback and units](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/blob/99d3897a10d1e8abb0b36a0b00d5c95799125782/FYP-Machine-Condition-Prediction/static/dashboard.html#L408-L500), [stream response access](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/blob/99d3897a10d1e8abb0b36a0b00d5c95799125782/FYP-Machine-Condition-Prediction/services/real_influx_streamer.py#L130-L145).

Validation calculates MAE/RMSE/MAPE on scaled, clipped values and calls `max(0,100-average_MAPE)` accuracy. This is not classification accuracy or fault detection recall. Ten recent targets do not demonstrate an independent test cohort. No reproducible held-out benchmark scores, prospective failure outcomes or calibrated anomaly thresholds were found. [Validation calculation](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/blob/99d3897a10d1e8abb0b36a0b00d5c95799125782/FYP-Machine-Condition-Prediction/services/inference_service.py#L209-L279).

### Security and deployment adoption findings

These are source-level risks for anyone copying this design, not claims that a deployed upstream service was attacked or currently compromised.

| Priority | Finding | Adoption requirement |
|---|---|---|
| High | Broker explicitly allows anonymous clients; Compose publishes MQTT and InfluxDB on all host interfaces | Use authenticated per-device ACLs, TLS and restricted network binding |
| High | Credential-like literals appear in database/bridge/training settings | Do not reuse; supply private scoped secrets and rotation |
| High | Model/scaler deserialization uses pickle and an unsafe torch-load fallback | Accept only trusted verified artifacts; prefer restricted formats |
| High | FastAPI data/validation routes have no inspected identity or asset-scope checks | Add server-side user/device authorization |
| Medium | Flux strings interpolate workspace identifiers | Validate IDs and use safe query parameters |
| Medium | Bridge substitutes absent sensor fields with zero and omits supplied source timestamp | Reject missing fields; preserve event time and receipt time separately |

Evidence: [broker configuration](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/blob/99d3897a10d1e8abb0b36a0b00d5c95799125782/mqtt-broker/config/mosquitto.conf#L1-L10), [Compose exposure and initialization settings](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/blob/99d3897a10d1e8abb0b36a0b00d5c95799125782/docker-compose.yml#L5-L43), [model loading](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/blob/99d3897a10d1e8abb0b36a0b00d5c95799125782/FYP-Machine-Condition-Prediction/services/inference_service.py#L78-L110), [query interpolation](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/blob/99d3897a10d1e8abb0b36a0b00d5c95799125782/FYP-Machine-Condition-Prediction/services/real_influx_streamer.py#L61-L101), [bridge field defaults](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/blob/99d3897a10d1e8abb0b36a0b00d5c95799125782/vm-automation/mqtt_to_influx_bridge_vm.py#L62-L82).

Compose also references absent `spark-apps/Dockerfile` and root `run_monthly_training.sh`. Several README-listed setup/test/anomaly scripts are absent from the full pinned tree; no executable automated test suite or CI configuration was found. Local automation hardcodes another developer's Windows paths. Therefore restart and monthly-training descriptions are not evidence of portable, tested deployment. [Compose build/scheduler references](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/blob/99d3897a10d1e8abb0b36a0b00d5c95799125782/docker-compose.yml#L45-L110) · [Hardcoded task setup](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/blob/99d3897a10d1e8abb0b36a0b00d5c95799125782/local-automation/install_monthly_training.ps1#L16-L76).

README says MIT near its end, but no standalone complete LICENSE notice appears in the tree and GitHub API license detection is null. Record this as **declared MIT, incomplete checked license evidence**, not “definitely unlicensed.” Obtain/verify the applicable full notice before copying code. No source was copied into KerfPulse. [License assertion](https://github.com/Pasindu2000B/Predictive-Maintainance-System-For-Lathe-Machine/blob/99d3897a10d1e8abb0b36a0b00d5c95799125782/README.md#L630-L632).

### What KerfPulse should learn

Useful product concept: show measured history, forecast, actual later outcome and model identity in one linked view. Implement immutable prediction-to-later-outcome joins, not a rolling validation button that can repeatedly reuse training-period data. A monthly training schedule is insufficient promotion control: candidate validation, signed/digested bundles, rollback and human approval remain separate gates.

Do not use this generator to meet KerfPulse's measured-data requirement; do not equate sensor forecasting error with probability of cutter failure; do not infer normal health from unavailable output. Missing evidence should remain visible and should block advice.

## Cross-reference synthesis for KerfPulse

| Capability | Bosch | Shengwei | Pasindu | KerfPulse decision |
|---|---|---|---|---|
| Credible measured data | Official measured corpus, explicit data license | CSV present; acquisition provenance unverified | Synthetic generator confirmed; stored DB provenance unverified | Acquire Bosch separately; retain pinned primary cutter dataset |
| Direct five-cut damage task | No | No documented equivalence | No | No cross-task accuracy comparison |
| Cross-machine research axes | Three machine IDs, periods and process IDs | No machine ID in supplied CSV | Workspace names; no independent machine evaluation | Use Bosch for separate domain-shift anomaly evaluation |
| Model evaluation quality | No training benchmark supplied | Shared-window test and other risks | Forecast split/serving inconsistencies | Keep grouped nested evaluation and explicit uncertainty |
| Full workflow evidence | Dataset only | Upload/train/plot only | Multiple layers present, artifacts/paths missing | Borrow concepts after verification, not readiness labels |
| Research novelty impact | Prior art for brownfield CNC signal monitoring | Prior art for classifier/threshold UI | Prior art for MQTT + transformer + web forecasting | Novelty must lie in a tested decision mechanism, not stack combination |

KerfPulse's current strongest justified result remains the saved grouped comparison: fused mean AP .3531 versus logistic .3252, with paired difference interval spanning zero; acquisition-regret candidate produced no timely inspections and is not promoted. These repository reviews do not change those experimental outcomes. Existing source/model qualification and named-access work address operational trust, not predictive superiority. [Current research checkpoint](../../production/qualification-research-checkpoint.md) · [Research objective audit](../../production/research-objective-audit.md).

### Prioritized next work, with acceptance gates

1. **P0 — Keep claims and contracts exact.** Distinguish historical replay, fresh completed-cut forecasting, process anomalies and absent/unsupported evidence in UI/API. Accept when named task, horizon, input schema, units, source identity and qualification status accompany every result; unqualified input cannot become plant advice.
2. **P1 — Add Bosch acquisition/manifest and a small loader audit.** Preserve CC-BY attribution and immutable checksums. Accept only finite three-channel arrays with explicit machine/process/period/file lineage; complete recordings partitioned before windows; no bulk eager-loading dependency.
3. **P1 — Freeze separate Bosch anomaly protocol.** Compare a transparent baseline with one temporal candidate under machine and temporal holdouts. Report false-alarm burden, PR metrics and coverage. Accept only a reproducible task-specific report; this cannot promote cutter-RUL claims.
4. **P1 — Repair maintenance research objective before complexity.** Maintain a distinct first-inspection outcome and optional-acquisition cost. Test training-only selection against current-only and simple policies. Accept only matched protocol/cost/support reporting with uncertainty; independent confirmation remains required after inspecting current outcomes.
5. **P2 — Add outcome-linked evidence views.** Join immutable forecast IDs to later measurements/inspection reviews. Show original physical units, stale-state warnings and unavailable states. Accept with browser tests for failure, missing fields, cross-tenant denial and preserved history.
6. **P2 — Preserve bounded, authenticated ingestion.** Model automatic retraining as a candidate-building job, not release approval. Accept with receipt reconciliation, revocation, duplicate/conflict recovery, qualified artifacts and rollback evidence.

### Limits and remaining research

This audit did not install upstream environments, load upstream executable artifacts, run their models, reproduce chart metrics or contact their exposed infrastructure. Binary InfluxDB files were inventoried but not opened, so their sensor authenticity and embedded secrets are unknown. Bosch HDF5 corpus counts come from Git metadata; only the pre-existing local example was rehashed. Unit calibration and exact physical fault semantics still require publisher study/metadata and eventually plant commissioning.

No compared project establishes KerfPulse's novelty by exclusion. A literature and patent review plus matched ablations would still be needed for a publishable claim. These findings establish useful engineering lessons and disqualify several tempting shortcuts; they do not promise publication, free unlimited hosting, superiority or safe autonomous machine control.
