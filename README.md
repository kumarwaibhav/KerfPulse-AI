# KerfPulse AI

KerfPulse AI turns compatible completed-cut measurements into traceable inspection decision support. The fresh assessment screen accepts new tool-life identities through CSV/JSON, runs an explicitly released current-plus-context model, saves evidence and scores, and records human review. A separate research dashboard streams recorded 42CrMo4 steel milling measurements through MQTT with held-out evaluation models, durable replay, browser updates, and inspection work orders.

**Engineering demonstration, not a commissioned plant product.** Arbitrary plant uploads remain unsupported until sensor/extraction/domain qualification. The physical source is visibly unconfigured. There is no continuous RUL estimator, during-cut anomaly detector or autonomous machine control. See [current implementation and evidence](docs/production/continuation-checkpoint.md), [claims](docs/production/claims-and-limitations.md) and [production document index](docs/production/README.md).

The current benchmark is a reproducible research result. Nested workpiece holdout produced **2 timely scheduled inspections among 14 tools** for current-only and periodic policies and **1 among 14** for decision-aware and always-fused policies. Recipe holdout produced **1 among 14** for each policy. Decision-aware superiority is unsupported at the recorded settings. The app lets a reviewer inspect these outcomes, source quality, and evidence budgets.

## Start the complete local stack

Requirements are Python 3.12, Node.js 22, PowerShell 7, Docker with a running engine and Compose, and network access for first-time package/data downloads. Run from `E:/pdm_aiiot`.

```powershell
pwsh -File scripts/setup.ps1
docker compose up --build -d
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/healthz
```

Open [KerfPulse AI](http://127.0.0.1:8000). Setup installs Python dependencies into `.venv`, verifies the 1.8 MB dataset, trains nested-workpiece artifacts, runs the matched policy benchmark, builds the frontend, and creates a random local database password in `.env` if absent. The model commands use CPU and can take several minutes. Docker builds the same-origin API/UI image and starts PostgreSQL, Mosquitto, persistence worker and replay gateway. Check actual container health and a completed dashboard run before treating startup as verified.

Choose **Score a New Cut**, then **Load measured example** and **Validate and score**. The measured publisher example has a new event/tool identity and an explicit demonstration clock. It carries no future damage label. Approve inspection, record a sourced finding, complete review and export its evidence. Unsupported measurements produce an unavailable score. CSV/JSON templates document the exact supported summary interface; raw physical extraction is not supplied by the importer.

Choose **New replay** for the separate research workflow, select a cutter and policy, and optionally launch a paired comparison. Three cycle positions between inspection breaks is the experimental default. Use **Approve**, then **Record completion** to capture an inspection finding. Export the run for source/model provenance. Research streams stay labelled **Recorded telemetry replay**.

```powershell
docker compose logs --tail 100 api worker gateway
docker compose down
```

`docker compose down` stops services and retains named data volumes. The application is bound to localhost port 8000. PostgreSQL and the broker use the private Compose network. A public deployment needs its own HTTPS, private broker, secret configuration and provider verification.

## Native development

Install and prepare data/model/UI assets with the setup command above. The API, worker and gateway must share one database and MQTT broker. For a native SQLite development session, set the same variables in each of three PowerShell terminals. Point `MQTT_HOST` and `MQTT_PORT` at an available local Mosquitto broker.

```powershell
$env:PDM_DATABASE_URL = 'sqlite:///data/pdm.sqlite3'
$env:PDM_MODEL_DIR = 'artifacts/nested-workpiece'
$env:MQTT_HOST = '127.0.0.1'
$env:MQTT_PORT = '1883'
```

Run one long-lived command in each terminal.

```powershell
.venv/Scripts/python.exe -m uvicorn pdm.api:app --host 127.0.0.1 --port 8000
```

```powershell
.venv/Scripts/python.exe -m pdm.worker
```

```powershell
.venv/Scripts/python.exe -m pdm.gateway
```

FastAPI serves the built bundle from `web/dist`. To iterate on the frontend, use `npm.cmd --prefix web run dev` in another terminal and open the Vite URL printed in that terminal. Its `/api` and health proxy points to the native API. Set `PDM_ALLOWED_ORIGINS` on the API to the exact Vite origin for write requests. Rebuild with `npm.cmd --prefix web run build` to return to same-origin static serving.

## Reproduce data, models and checks

```powershell
.venv/Scripts/python.exe -m pdm.dataset fetch
.venv/Scripts/python.exe -m pdm.dataset audit
.venv/Scripts/python.exe -m pdm.train
.venv/Scripts/python.exe -m pdm.benchmark
.venv/Scripts/python.exe -m pdm.validation --protocol workpiece --output artifacts/nested-workpiece
.venv/Scripts/python.exe -m pdm.benchmark --artifacts artifacts/nested-workpiece
.venv/Scripts/python.exe -m pdm.validation --protocol recipe --output artifacts/nested-recipe
.venv/Scripts/python.exe -m pdm.benchmark --artifacts artifacts/nested-recipe
.venv/Scripts/python.exe -m pytest -q
npm.cmd --prefix web run typecheck
npm.cmd --prefix web run build
```

The research replay uses `artifacts/nested-workpiece/models.json` and validates its SHA-256 against `report.json`. `predictions.json` and `policy-benchmark.json` document matched held-out outcomes. The baseline writes to the root `artifacts` directory. Nested validation selects regularization and temperature on training groups and saves all candidates and split manifests. Existing test evidence and new integration checks are documented separately in `docs/`.

The fixture contains 968 recorded cuts from 14 cutters, 120 sensor features plus metadata/targets, and seven recipe combinations. Parsing preserves 21 missing source cycle positions and quarantines both conflicting records at tool 2 cycle 34. Excluding terminal rows and conflicts yields 952 eligible pre-damage cuts. Cutter 11 was damaged in its first cut. It remains in the fourteen-tool event denominator and has no prior observed warning opportunity.

## Evidence, limitations and deployment status

- The sensor/degradation study comes from one industrial Haas VF-1 under controlled experiments. It supports unseen-tool tests in that setting. Independent-machine validation is a roadmap milestone.
- A warning after a completed cut concerns later cuts. Damage-cycle features and future labels are excluded. Models export nine classes for one through eight further cuts and more than eight.
- The release cap is `floor(n/4)` optional vibration feature sets after `n` unique accepted cuts. Same-cycle data is buffered at the virtual edge. Recorded release bytes quantify transmission. Physical sensor energy savings and raw capture duty-cycle need separate measurement.
- Scheduled inspection, planner approval and manually entered finding are recorded workflow outcomes. Prevented damage, customer savings and operational safety require a field study.
- Local source/model work and runtime code are present. Use observed build/test/runtime evidence in the release report for verification status. A hosted public URL and service uptime are claimed only after deployment succeeds.

The candidate public profile uses Render Free and Neon Free, subject to their idle, resource and storage limits. Multi-process supervision and private broker configuration are required for that profile. Local Compose is the canonical deployment. Customer rollout begins with read-only shadow monitoring, a verified controller mapping, authenticated customer identity and an agreed inspection/outcome process.

### Push the source to GitHub

From the workspace root, initialize the repository and review the staged file list before publishing. The ignore rules exclude `.env`, local data, generated models, build output and release archives.

```powershell
git init -b main
git add .
git diff --cached --name-only
git commit -m "Add KerfPulse AI application and research benchmark"
gh repo create kerfpulse-ai --private --source . --remote origin --push
```

For an existing destination, add its Git URL with `git remote add origin <repository-url>` and use `git push -u origin main`. Run setup after cloning to reproduce the data and models before building the Docker image.

Observed test, transport, browser and package evidence is maintained in [Local release verification](docs/release-report.md). Read that report for verified status and outstanding acceptance measurements.

## Create a source package

```powershell
pwsh -File scripts/package.ps1
Get-FileHash release/kerfpulse-ai.zip -Algorithm SHA256
```

The archive is written to `release/kerfpulse-ai.zip` with a SHA-256 JSON sidecar. It includes application source, documents, tests, deployment files and `.env.example`. Downloaded data, trained artifacts, dependencies, local credentials and runtime databases are excluded. After extracting, run setup to reproduce data, models and the frontend. Archive CRC and excluded-path inspection results are recorded in the release report.

## Documents

| Document | Contents |
|---|---|
| [Research and source audit](docs/01-research-and-source-audit.md) | Industrial failure taxonomy, four-use-case decision, dataset selection, primary-source corrections and prior-art boundary. |
| [Dataset and training](docs/02-dataset-and-training.md) | Data rights, parser/chronology contract, causal features, commands, validation, actual metrics and evaluation milestones. |
| [Product requirements](docs/03-product-requirements.md) | Vision, mission, personas, numbered requirements, acceptance measures and commercialization hypothesis. |
| [Architecture and stack](docs/04-architecture-and-tech-stack.md) | Five-service data flow, versions, API, state/persistence, configuration and operating profiles. |
| [Functional specification](docs/05-functional-specification.md) | Views, replay/order states, comparison, errors, source quality and reviewer walkthrough. |
| [Development roadmap](docs/06-development-roadmap.md) | Dependency milestones, validation/paper work, release tests and customer-pilot steps. |
| [How KerfPulse works](docs/07-how-kerfpulse-works.md) | Plain-language dataset, model, architecture and dashboard walkthrough. |
| [Performance analysis](docs/08-performance-analysis.md) | Held-out model results, decision and bandwidth tradeoffs, browser profile, sustained load and production readiness. |

## Data attribution

Grzegorz Piecuch and Tomasz Żabiński, *A new open dataset from a milling process – data for classification and estimation of tool life*, Scientific Data 12, 650 (2025), DOI `10.1038/s41597-025-04923-y`. Dataset release `10.6084/m9.figshare.28589216.v1`, CC BY 4.0. This project transforms completed-cycle statistics, excludes future labels from model features, quarantines conflicting records, preserves source gaps, and adds a replay clock. Source SHA-256 is `e125471f983e98ae326e2c47e15f633bb30738e285b9ad6e54b5e364d4d66dbc`. [Paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12006439/) · [Pinned data release](https://doi.org/10.6084/m9.figshare.28589216.v1) · [License](https://creativecommons.org/licenses/by/4.0/)

Fresh inference uses `artifacts/engineering-release/model.json` and `manifest.json`; reproduce it with `.venv/Scripts/python.exe -m pdm.release_model`. Never substitute the fold-model bank for the fresh release. The release is an engineering baseline; historical nested AP and policy results are not fresh-model confirmation metrics.
