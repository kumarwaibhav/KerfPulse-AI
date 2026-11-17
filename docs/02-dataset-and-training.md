# Dataset and model training

This guide defines the measured data, training boundary, and commands used by KerfPulse AI. The executable results are in JSON artifacts produced by the commands below. Read each artifact's protocol and source hash before comparing numbers.

## Acquisition and rights

| Dataset | Role | Endpoint and modalities | Reuse and acquisition |
|---|---|---|---|
| Piecuch–Żabiński, 2025, Figshare v1 | Primary complete replay and damage-warning experiment | Fourteen cutter lives during 42CrMo4 steel milling on one Haas VF-1. Eight vibration channels at 25 kHz and twelve current channels at 500 Hz. Published endpoint is cutter or blade damage. | CC BY 4.0. The checked feature CSV is 1,797,280 bytes. Raw archive is 25,345,272,829 bytes. Fetch the feature CSV through the loader. Keep raw processing as a separate experiment. [Metadata](https://api.figshare.com/v2/articles/28589216) · [Descriptor](https://pmc.ncbi.nlm.nih.gov/articles/PMC12006439/) |
| Denkena, Klemme and Stiehl, 2023, Mendeley v3 | Independent machine-transfer experiment | Nine cutters on three machining centers. Force at 25 kHz and controller torque/position at 500 Hz. Measured flank wear reaches about 150 µm. | CC BY 4.0. The archive is approximately 10.62 GB with individual indexed HDF5 records. Create an explicit adapter and endpoint definition before training. [Version 3](https://data.mendeley.com/datasets/zpxs87bjt8/3) |
| Bosch CNC production dataset | Optional industrial anomaly/ingest stress test | Three production machines and operation-level good/bad vibration recordings. | CC BY 4.0. It supports a distinct anomaly task. [Authors' repository](https://github.com/boschresearch/CNC_Machining) |
| MTConnect public demo | Optional standards/ingest demonstration | Live machine controller observations, with agent sequence and instance metadata. | The agent software license alone does not grant rights to republish observations. Read and display ephemeral observations only after terms review. The training feature contract and labels differ from the Haas measurements. [Official playground](https://www.mtconnect.org/playground.html) |

The initial release uses the primary dataset. Attribution accompanies the fixture and export. Record the original DOI, creator, source URL, version, license URL, source hashes, transformation version, and modification summary. Commercial sharing and adaptation under CC BY require appropriate attribution and change notices. [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-train.txt
.venv/Scripts/python.exe -m pdm.dataset fetch
.venv/Scripts/python.exe -m pdm.dataset audit
```

Run from `E:/pdm_aiiot`. The loader verifies the pinned bytes before parsing. A failed checksum stops acquisition. Resolve a changed upstream release by publishing a new manifest and audit. Preserve the pinned input until that change has been reviewed.

## Exact parsing and chronology contract

The feature file has a numeric header followed by descriptive field names. Parse the second header, use semicolon separators, and convert decimal commas in metadata. Sensor aggregates contain decimal points. The source has 968 rows and 131 columns. Its 120 signal features are minimum, maximum, mean, standard deviation, skewness, and kurtosis for 20 channels. Retain `TollIndex`, the spelling in the file, as lineage and holdout identity. Use `NumberOfCycle` as the original cut ordinal. [Source file](https://ndownloader.figshare.com/files/52968974) · [Authors' data definitions](https://pmc.ncbi.nlm.nih.gov/articles/PMC12006439/)

| Audit finding | Required handling |
|---|---|
| Fourteen distinct tools and seven recipe combinations | Report tool counts in addition to cut counts. A long run contributes many correlated rows. |
| Tool 2 has two different observations at cycle 34 | Quarantine both rows. Keep one explicit conflict state for the source ordinal. Neither observation earns release quota or supplies a model vector. |
| Twenty-one absent cycle positions across seven tools | Preserve gaps. A missing cut advances the source ordinal and does not mint an accepted measurement or optional evidence budget. |
| Fourteen terminal rows with `CycleToFailure=0` | Publish observed damage as the terminal event. Exclude terminal features from forecasts. |
| Tool 11 fails on its first cut | Include its outcome in the all-tool event denominator. Mark lack of a pre-damage measurement opportunity. |
| Five shared workpiece identifiers connect tools | Exclude direct identifiers and test connected workpiece/tool components as held-out groups. |
| Sensor extrema can reach acquisition limits | Record a possible clipping quality flag when verified. A limit value alone cannot establish a fault. |

The resulting eligible feature dataset has **952 pre-damage observations** after terminal-row exclusion and duplicate quarantine. The observed five-cut outcome window contains **60 positive cuts**. These counts describe repeated observations from 13 observable tool lives. Use `CycleToFailure` as the source outcome. Never recompute it from row count or repair gap ordinals using row position. The source CSV supplies no wall-clock timestamp for the aggregate cut. Keep source ordinal, simulated replay time, and service ingestion time as distinct fields. [Checked CSV](https://ndownloader.figshare.com/files/52968974)

The shared-workpiece components are computed by the loader and training code. A component includes all cutters linked by any repeated workpiece ID, even through another cutter. The sensitivity protocol holds out the entire component, which reduces contamination from material or workpiece identity shared with training.

## Causal features and target

Every score is made after one complete cut and concerns subsequent cuts. Permit age, recipe values available before that cut, and measurements available at its completion. `FileName`, `SampleIndex`, `TollIndex`, terminal ordinal, and both source target columns remain outside the model. Use `MillingToolType`, `ADOC`, `RDOC`, and `ToolHolderLength` as recipe fields. The current implementation also includes `HardnessMean` and observed age in all three heads, so reported models assume the workpiece hardness was measured and known before cutting. That assumption is supported by the controlled source's material metadata and must be verified for a customer connector. Refit without hardness when it is unavailable. The `age` head therefore means age plus recipe and hardness context.

Export nine outcome classes representing **1 through 8 further cuts and more than 8**. This extends the basic five-cut forecast so a future inspection slot can be evaluated with two to five cuts of lead remaining at that slot. For cut `t`, five-cut damage risk is the sum of classes 1 through 5. For next slot `s`, actionable risk sums offsets `s−t+2` through `s−t+5`. The exposed calendar intervals of one, two, or three cuts keep those offsets within the explicit classes. Use the class labels saved in the JSON model to place probabilities. Classes absent from training receive zero mass.

## Training commands and artifacts

The initial baseline fits standardized multinomial logistic regression with fixed `C=0.1`. Each training tool receives equal total sample weight. Whole-tool holdout creates out-of-fold probabilities for three heads named `age`, `current`, and `fused`. The exported JSON contains feature order, scaler means/scales, classes, coefficients, and intercepts. Numeric runtime inference reproduces the fitted scikit-learn calculation.

```powershell
.venv/Scripts/python.exe -m pdm.train
.venv/Scripts/python.exe -m pdm.benchmark
```

These commands write `artifacts/baseline-report.json`, `artifacts/models.json`, `artifacts/predictions.json`, and `artifacts/policy-benchmark.json`. The fixed threshold is 0.5. The periodic policy promotes every fourth accepted cut. The decision policy requests vibration when actionable risk is within 0.2 of that threshold and quota exists. The always-fused policy is an unconstrained resource reference. Explicitly choose the matching artifact directory for policy evaluation.

Nested validation fits preprocessing on inner training data and selects `C` from `{0.01, 0.1, 1.0}` and temperature from `{0.5, 1.0, 2.0}` using up to three inner component-disjoint folds. The objective is nine-class log loss, averaged equally over tools. Outer workpiece holdout excludes every linked component. Outer recipe holdout also purges workpiece-linked training tools. Temperature selection is an empirical calibration adjustment. Report its held-out reliability and retain the raw probabilities.

```powershell
.venv/Scripts/python.exe -m pdm.validation --protocol workpiece --output artifacts/nested-workpiece
.venv/Scripts/python.exe -m pdm.validation --protocol recipe --output artifacts/nested-recipe
.venv/Scripts/python.exe -m pdm.benchmark --artifacts artifacts/nested-workpiece
.venv/Scripts/python.exe -m pdm.benchmark --artifacts artifacts/nested-recipe
.venv/Scripts/python.exe -m pytest -q
```

Each nested output directory contains `models.json`, `predictions.json`, and `report.json`. The report stores tuning candidates, selected settings, training/test/purged tools, source hash, model artifact hash, pooled cut metrics, reliability bins, and elapsed training time. Persist the command, Python and dependency versions, seed, and hardware with a reproducibility release. Baseline latency is a batch-amortized CPU measurement and needs separate per-event service profiling.

## Results recorded on 17 November 2026

The existing validation checkpoint reports the following pooled cut statistics. Recompute the JSON artifacts when changing code, data, or dependencies.

| Outer holdout | Head | Average precision | Brier score |
|---|---|---:|---:|
| Workpiece component | Age and recipe | 0.217641 | 0.057790 |
| Workpiece component | Current | 0.355090 | 0.050182 |
| Workpiece component | Fused | 0.304930 | 0.058912 |
| Recipe with workpiece purge | Age and recipe | 0.184008 | 0.058558 |
| Recipe with workpiece purge | Current | 0.335462 | 0.051544 |
| Recipe with workpiece purge | Fused | 0.291713 | 0.059393 |

Current selected temperature 1 in the recorded workpiece and recipe runs. Report sensor value in terms of measured changes over age/recipe and current controls. The observed ranking supports keeping current-only as a serious candidate. The matched workpiece policy benchmark produced 2 timely scheduled inspections among 14 tools for current-only and periodic policies, and 1 among 14 for decision-aware and always-fused policies. The recipe benchmark produced 1 timely inspection among 14 tools for every policy. The recorded hypothesis is unsupported at these settings. Inspect per-tool outcomes and report premature, late, and absent inspections alongside the timely counts. The application uses nested-workpiece JSON models and their verified artifact hash.

## Policy evaluation and uncertainty

Count each accepted, unique, finite current record once. Permit at most `floor(n/4)` optional vibration sets after `n` such records. A retry cannot debit twice or create quota. A gap, conflict, and terminal event cannot earn quota. Use same-cut buffered vibration only after the current-only decision requests it. Continuous source capture and edge buffering still occur in this setup, so the measured saving is transmitted feature records and serialized bytes. Sensor power and physical sampling savings require hardware measurement or a separately labelled model.

Evaluate the **first scheduled inspection slot** per tool. If damage occurs at `d` and the booked slot is after cut `s`, classify `2 ≤ d−s ≤ 5` as timely, `d−s > 5` as premature, and `d−s < 2` as late. An abstention or deferred case that never receives an inspection is missed. Retain all 14 outcomes and show the 13 tools with pre-damage opportunity separately. Report raw per-tool results, optional releases, quotas, premature reviews per 100 accepted cuts, coverage, lead, payload bytes, and calibration. Use paired tool-level resampling and show the small denominator. Calendar and cost sensitivities are scenario results.

Before a paper claim, add a simple risk-margin control at matched budgets to the executed periodic comparison. Include event-level age-only and always-fused references and no-age sensor sensitivity to detect schedule shortcuts. Freeze acquisition margins, thresholds, and slot rules before evaluating outer folds. If tuning them, tune on inner fold outcomes only. A later improvement must be evaluated on a fresh held-out protocol or explicitly described as exploratory.

The independent-machine experiment requires a versioned Stiehl adapter, verified endpoint, per-machine fold manifests, and a distinct model artifact. Its wear threshold differs from Haas damage. Label these endpoints in all tables. A hardware-free app can demonstrate ingestion and decision behavior while field generalization and prevented-damage efficacy remain milestones for a real customer shadow pilot.
