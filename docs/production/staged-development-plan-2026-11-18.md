# Staged CNC predictive-maintenance delivery plan

Current date: 18 November 2026. Product: KerfPulse AI. Mission: turn qualified completed-cut measurements into traceable risk estimates and feasible human maintenance decisions, then measure whether those decisions help. Primary use case remains CNC cutting tools in measured steel machining. Bosch process anomalies are a separate research track.

## Honest readiness position

Working engineering/research build exists. Real benchmark training, fresh scoring, web UI, durable ingestion/assessment/outbox, source qualification, and named access have evidence. Factory launch is blocked by unconfirmed maintenance utility, incomplete operational workflow/reliability, and absent plant commissioning. No defensible completion percentage follows from passing software tests.

Latest verified model comparison:952 eligible cuts, 60 positives, eight connected-workpiece groups. Fused mean AP.3531 versus logistic.3252; paired interval includes zero. Acquisition candidate produced0 timely, 5 premature, 9 no-inspection outcomes across14 lives; five lives were supported, eight abstained by recipe, one lacked pre-damage observations. Serving release remains unchanged. No scientific superiority is claimed.

## Gate map

| Stage | State now | Required next result | Exit evidence |
|---|---|---|---|
| 0: Evidence and scope | Research review complete; limitations documented | Maintain immutable claims/data/model register | Eleven repository reviews, measured/synthetic distinctions, separate code/data rights |
| 1: Named operational access | Named OIDC, exact read scopes and UI isolation verified | Extend scoped history presentation and production identity policy | Signed-token security cases, actual browser login/logout, denied foreign/revoked access, no demo permission inheritance |
| 2: Decision research | Expanded comparison complete; negative acquisition result; diagnostic implemented | Build/test/run frozen first-stop experiment | Matched baselines, causal optional reads, training-only selection, per-tool outcomes/spend/coverage and uncertainty |
| 3: Raw-signal research | Catalog/loader/splits implemented; one Bosch file verified | Acquire/audit corpus; fit transparent anomaly baseline | Publisher hashes, recording-disjoint folds, units/rates, per-machine/period false-alarm metrics |
| 4: Engineer workflow | Demo reviews exist; named operations currently read-only | Transactional inspections, assignment, windows and verified outcomes | Positive/negative role journeys, concurrent retries, append-only transition history, assessment linkage |
| 5: Industrial connectivity | Authenticated HTTP receipts/spool exist; physical feed absent | Authenticated read-only protocol adapter and extractor attestation | Real protocol fixtures, exact units/schema/extractor hashes, gaps/reconnect/revocation and source-health evidence |
| 6: Reliability and release | Local Compose, tests and packages exist; full fresh-path gates incomplete | Declared load/soak, retention, encrypted restore, rollback and CI | Reconciled receipts/backlog, capacity/latency/errors, recovery time/data-loss bounds, secret-free owner-authored release |
| 7: Factory acceptance | External evidence absent | Commissioned field shadow then qualified advisory rollout | Independent-machine/prospective outcomes, measured inspection workload, site sign-off |

Stages2/3 can proceed as isolated research branches while stage4 software develops. Their models cannot become active plant advice merely because code runs. Stages5/7 require actual source/site cooperation for corresponding field claims.

## Stage1: close access foundation

Modules:`pdm/identity.py`, `pdm/oidc.py`, `pdm/operations_api.py`, `web/src/Operations.tsx`, `web/src/SourceHealth.tsx`.

Keep server-owned issuer/subject identity, opaque hashed sessions, browser-bound single-use state/nonce/PKCE, signed RS256 tokens, CSRF logout, expiry, disable/revoke and exact org/site/asset grants. No provider role claim or demo cookie grants machine rights. Named read roles do not yet imply write authorization.

Complete startup isolation, source-history presentation and endpoint-negative cases. Every future history/export/stream/write endpoint must use the same scope rule. Active long-lived feeds need grant/session rechecks. Public IdP deployment needs TLS, maintained production configuration and site availability policies; local Keycloak start-dev is evaluation only.

## Stage2: repair first-inspection endpoint

Follow [frozen first-stop protocol](../research/repository-review-2026-11-18/first-stop-protocol.md). Proposed new implementation:`pdm/first_stop_research.py` plus event-trace and counterfactual-label tests. Existing historical runner/results remain unchanged.

First implement deterministic trajectory simulation and trace schema. Test causal optional access, floor(n/4) quota, no acquisitions after fixation, missing cuts, domain abstention and no opportunity. Then generate training-only cross-fitted terminal labels. Freeze fingerprints and small inner grids before executing. Compare current-only, periodic, random, risk-margin and shallow terminal gate; full fusion remains resource reference.

Require timely/premature/late/no-inspection counts, equal-tool terminal loss, false-inspection workload, support coverage, actual pre-intervention acquisitions, AP/Brier, calibration and paired group uncertainty. Historical outputs lack per-event acquisition timing and did not fingerprint policy.py; do not invent missing historical evidence. Existing data informed this direction, so new results remain exploratory. Independent confirmation is a separate promotion gate.

## Stage3: distinct raw process-anomaly track

Follow [Bosch protocol](../research/repository-review-2026-11-18/bosch-experiment-protocol.md). Existing foundation:`pdm/bosch_data.py`. Proposed next modules: bounded verified acquisition command and `pdm/bosch_baseline.py`.

Audit local disk reserve, acquire pinned recordings incrementally, persist hashes/provenance, inspect all machine/process/period/label combinations. Split full recordings before windows and learn all transforms on training partitions. Start statistical/spectral baseline before one temporal candidate. Compare machine shift and time shift separately. File-level anomaly labels cannot become wear/RUL targets.

Acceptance: complete/explicitly incomplete acquisition ledger; channel/units/rate checks; no partition overlap; recording-level PR/false-alarm/coverage metrics; reproducible environment; bounded memory. A new task needs a new model/qualification contract and separately labeled UI.

## Stage4: engineer action and outcome

Proposed modules:`pdm/operational_inspections.py`, `pdm/inspection_api.py`, `web/src/InspectionWorkflow.tsx`; preserve `pdm/operational_processing.py` assessment snapshots.

Implement one vertical journey first: authorized planner opens an inspection from a specific assessment; assigns an authorized technician within the same asset scope; selects a real feasible site window; operator records finding/evidence; authorized reviewer resolves. Persist actor, expected version, prior/new state, timestamp, due/expiry and exact assessment/model/qualification IDs. Unsupported/shadow evidence cannot become an approved machine-safety action.

Use one transaction for state transition plus audit/outbox. Retried requests have one effect. Deny viewer writes, foreign assignees/assets, stale versions, impossible dates and invalid transitions. Calendar tests include timezone/DST, overlapping windows, missed/expired assignments and paused production; suppressed alerts never mean healthy measurements. Later verified outcomes join immutable original predictions; no retrospective score edits.

Then add operator history/export and graphical source→assessment→inspection→outcome trace. Browser tests cover complete journey, bad inputs, network failure, concurrent edits, revoked access, keyboard/mobile and unavailable evidence. No public administration endpoint until roles and audit gates exist.

## Stage5: industrial input qualification

Existing modules:`pdm/device_ingest.py`, `pdm/device_api.py`, `pdm/edge_spool.py`, `pdm/qualification.py`. Proposed read-only adapters belong in a new bounded adapter package.

Choose one actual site protocol after observing available controller interfaces; do not add OPC-UA, MTConnect and MQTT indiscriminately. Register device identity, org/site/asset, units, rate, channel mapping, extractor version/digest and clock basis. Verify extraction parity against source bytes. Authentic protocol fixtures test decoding but are not plant commissioning.

Require encrypted/authenticated external transport, per-source scopes, reconnect without later sensor input, boot/sequence continuity, dedupe/conflict/gap handling, stale/future clock denial and bounded disk backpressure. Operational internal replay MQTT is not the external plant security profile. Raw sensor absence must never be replaced with normal values. Source/model/extractor revision mismatch abstains.

## Stage6: reliability, security and packaging

Freeze service profile and expected load before measurement. Fresh assessed path target remains20 events/s for600 seconds, with reconciled accepted/duplicate/quarantined/rejected/processed/outbox counts, backlog drain, p50/p95/p99 latency, errors and resource use. Follow with declared-duration soak and process/network/database fault injection. Historical replay load results cannot stand in for this new path.

Implement retention with protected audit references and dry-run evidence. Encrypt full database/config/artifact backup; restore into an isolated environment; verify counts, hashes, identity/grants, receipt cursors and model/source lineage. Record actual recovery time and data-loss window. Prove rollback to prior digest without changing historical assessments.

CI must reproduce benchmark assets, Python checks and frontend build with read-only repository permissions. Keep hardware/raw-data tests explicit and separate. Packages include only allowlisted source/docs and optional attributed measured assets. Never package private credentials, runtime databases, third-party caches or arbitrary downloaded binaries.

Publish only through verified GitHub account `kumarwaibhav`, with user-approved author/committer identity. Preserve original local history before correcting unpublished agent-authored commits. Never force-push shared history or publish backup refs.

## Stage7: site shadow and controlled launch

Commission read-only source and clocks with plant engineer. Agree actual inspection windows, response ownership, outcome definitions, alarm budget and acceptance thresholds before observing confirmation outcomes. Run prospective shadow first. Measure domain coverage, false/missed inspections, lead time, workload and later verified outcomes by asset/regime.

Advance to advisory use only after required validation and signed site acceptance. Readiness does not authorize automatic machine actuation or claim prevented downtime without measured counterfactual/operational evidence. A journal submission additionally needs literature novelty, matched ablations and transparent uncertainty; publication is not guaranteed.

## Resources and recurring cost

Heavy research retains2GiB physical RAM, 4GiB commit, 1GiB VRAM reserve and80°C thermal guard. GPU is used where measured workload benefits; deterministic linear fits, parsing and small audit jobs may be faster/cheaper on CPU. Pause safely under guard; preserve checkpoints; never kill user applications to satisfy utilization targets.

Open-source/local build/train/run avoids mandatory cloud fees. It does not make laptop power, storage, operations, TLS/identity hosting or unlimited public SaaS availability free. External hosting profiles need explicit current limits/costs and separate acceptance.

## Next concrete checkpoint

Finish verified identity/UI isolation and package this milestone. Then implement the frozen first-stop trajectory simulator/event trace and named inspection transition store as separate bounded slices, each with tests and receipts. Acquire Bosch incrementally only under its distinct protocol and resource/disk checks. Keep serving model unchanged until promotion evidence exists.
