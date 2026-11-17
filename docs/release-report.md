# Local release verification

Verification date is 17 November 2026. This report records observed checks and explicit remaining work. The local source package and the research documents can be inspected now. The five-service Compose deployment and browser tests passed on this machine.

## Source and model evidence

The verified Figshare input is 1,797,280 bytes with SHA-256 `e125471f983e98ae326e2c47e15f633bb30738e285b9ad6e54b5e364d4d66dbc`. It has 968 rows, 14 cutters, 21 missing ordinals and two conflicting rows at tool 2 cycle 34. The loader preserves the gap/conflict states and excludes terminal features from inference. After exclusions, 952 measured pre-damage observations remain. Source and model manifests are saved alongside artifacts.

Nested workpiece-component and recipe validation have been run. Inner grouped validation selects regularization and temperature using training data. The recorded workpiece AP/Brier results are 0.217641/0.057790 for context, 0.355090/0.050182 for current, and 0.304930/0.058912 for fused evidence. Recipe results are 0.184008/0.058558, 0.335462/0.051544, and 0.291713/0.059393. These are pooled cut metrics. The first-inspection benchmark gives two timely workpiece events for current/periodic and one for decision/fused among fourteen tools. Recipe holdout gives one timely case for each. The decision-aware hypothesis is unsupported at the recorded settings.

The deployed replay models are loaded from `artifacts/nested-workpiece`. Their hash is checked against `report.json`. Runtime JSON inference has regression checks against fitted scikit-learn probabilities. All heads include workpiece hardness, recipe and cut age, which assumes pre-cut context availability. The virtual edge currently computes both scores and selectively transmits vibration summaries, so this release's resource measurements concern payloads and released features.

## Backend checks received

The backend reviewer reported 28 API/store tests passing across SQLite and PostgreSQL 17-alpine, fourteen per database, before a subsequent test expansion. Both database profiles were exercised through real Uvicorn/httpx SSE with `Last-Event-ID`. Checks included authorization/session boundary, valid and invalid order transitions, snapshot consistency, run quotas, stale generations, packet validation, duplicate idempotency and prefix budget. The final default Python suite passed 30 tests, including bounded request bodies and SSE connection limits. PostgreSQL was independently tested and the final Compose application was exercised against it.

The backend runtime dependency audit completed with eighteen dependency entries and zero known vulnerabilities at the time checked. Its machine-readable output is `artifacts/backend-runtime-dependency-audit.json`. A dependency audit describes known package advisories for its input and date. Code and operational security also depend on the separate source review and deployment configuration.

## Application verification status

| Area | Recorded status |
|---|---|
| Source/model reproduction | Recorded source audit, nested workpiece/recipe models and matched policy benchmark present. |
| API/store | 30 final Python tests passed. Isolated PostgreSQL checks and live Compose smoke passed. |
| Gateway/broker/worker | Passed on 50 source cycles through actual MQTT and PostgreSQL. Gateway-to-ingest p95 was 9.8 ms. Clean-volume startup passed after schema initialization was serialized. |
| Browser interactions and visual check | Two Chrome Playwright tests passed. Covered pause and resume, session reload, paired replay, work-order completion, export, evidence filters, both themes, and 390 px layout. |
| TypeScript and production web bundle | Docker TypeScript and Vite production build passed. npm audit reported zero known vulnerabilities. |
| End-to-end load target | The two-second p95, 20-event/second, ten-minute target requires a measured run. |
| Public hosting | Local source package only. Hosted deployment remains a separate verified step. |
| Independent-machine experiment | Stiehl adapter and held-machine experiment remain roadmap work. |

## Package inspection

`pwsh -File scripts/package.ps1` produced a source archive at `release/kerfpulse-ai.zip`. The first inspected archive contained 51 entries and all six requested documents. Python ZIP CRC testing passed. The archive inspection found no `.env`, `.venv`, `node_modules`, `__pycache__`, `.pyc` or SQLite database/WAL/SHM files. `.env.example` is intentionally included. Final package content and checksum are regenerated after this report and README edits. Read the adjacent `kerfpulse-ai.zip.sha256.json` and verify it against the archive before sharing.

The package uses an explicit source allowlist. It excludes downloaded data, model artifacts, frontend build output and installed dependencies. After extraction, run setup to fetch the pinned source, reproduce the nested models and web bundle, generate a local database password, and build Compose. The recipient requires Python, Node.js, PowerShell and Docker with a running engine. The canonical entry point is README.

## Remaining evidence for stronger claims

The release provides a reproducible hardware-free research application. Field reliability, prevented damage, commercial savings, physical sensor/edge power measurements, a statistically supported policy advantage and public-host availability require their corresponding roadmap evidence. Preserve the current negative policy result. A revised method is evaluated under a newly declared protocol and compared with the same controls.

## Fixed issues

- **[HIGH]** `pdm/store.py` initial PostgreSQL schema creation could collide across processes. Serialized PostgreSQL DDL with a transaction-scoped advisory lock and gated worker startup on API health. Verified clean-volume startup.
- **[MEDIUM]** `web/src/styles.css` replay cards overflowed at 390 px. Fixed grid minimum sizing and switched to a single card column on narrow displays. Verified in Chrome.
- **[MEDIUM]** `scripts/package.ps1` left copied tests under the repository root; pytest collected duplicate modules. Added test discovery scope and staging cleanup, and included Playwright sources in the archive.
- **[MEDIUM]** Test environment audit flagged pip and pytest pins. Raised the installer and pytest versions and reran the Python suite.

All 3,952 archived replay events were exercised in gateway verification. Model export matched nested predictions within 5 × 10⁻¹⁶, with 0.68 ms event-generation p95 and zero prefix violations. The 50-cycle live smoke measured transport and ingestion, while the specified ten-minute end-to-browser load target remains open. Public hosting credentials and a destination repository are not configured for this workspace.

Broker restart recovery passed during periodic replay. PostgreSQL retained all 50 source ordinals exactly once and 11 vibration releases. The refreshed Python requirements audit and npm audit reported zero known advisories. Audit outputs are saved under artifacts.
