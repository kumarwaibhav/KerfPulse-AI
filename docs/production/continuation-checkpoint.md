# Continuation checkpoint — 2026-11-17

## Implemented in this stage

- Single engineering model release for new tool-life identities, separate from archived fold heads; 867 eligible cuts, 11 effective training cutters, tools 2/4 excluded together and tool 11 without eligible rows. Artifact digest, source checksum, effective training IDs, code and library versions are recorded.
- Strict completed-cut contract, no future-label fields; declared source/clock, freshness, missing channels, profile/recipe checks and explicit unavailable-score states.
- Session-scoped assessment/history/export API. Original evidence and model/policy identifiers persist. Same event/digest returns the original assessment. Conflicting digests enter a bounded visible quarantine.
- Optimistic human approve/dismiss/complete state transitions and finding/source history. Demo sessions and their data expire after 24 hours; this is not a customer archival policy.
- Browser Score a New Cut flow with measured example, unsupported example, CSV/JSON templates, preview/edit, bounded file import, partial row errors, network failure feedback, persisted assessments, review and export.
- Bounded PostgreSQL pooling with rollback/reuse checks; API/gateway/worker close pools on normal shutdown. SQLite remains supported.
- Updated Docker build/setup/source package and a thirteen-document production plan, plus schema, index and this checkpoint.

## Current verification

Commands ran against actual source and the local Docker stack:

| Check | Observed result |
|---|---|
| .venv/Scripts/python.exe -m pytest -q | 36 passed; one Starlette/httpx TestClient deprecation warning |
| npm run build / Docker frontend build | TypeScript and production Vite build passed |
| npm run test:e2e in web | 7 passed, including fresh CSV/JSON, partial row validation, dismissal/completion/export, network error recovery, mobile overflow and legacy replay/SSE recovery |
| docker compose up --build -d --wait | API, PostgreSQL, MQTT, worker and gateway started; Compose dependency health checks passed |
| verify_postgres_pool.py in API container | 10 sequential and 40 concurrent transactions, rollback recovery passed, <=8 concurrent backend connections |
| npm audit --json | Zero known reported vulnerabilities |
| pip_audit -r requirements.txt | No known vulnerabilities reported; JSON saved in artifacts/runtime-dependency-audit.json |

Browser cases are workflow scenarios, not proof every role/element is covered. No OIDC/customer-role test is claimed because those roles are not implemented. Dependency scans do not constitute a complete penetration test.

## Performance evidence

Same short synchronous HTTP workload, four session owners, new event/tool identities and repeated authentic publisher features with explicit demonstration clocks:

| 300 events at 10/s over 30 seconds | Before pool | After pool |
|---|---:|---:|
| Saved / unique assessments | 300 / 300 | 300 / 300 |
| Errors | 0 | 0 |
| Request p50 | 69.39 ms | 20.04 ms |
| Request p95 | 623.31 ms | 61.00 ms |
| Request max | 1348.95 ms | 127.25 ms |

This is a local comparison, not a randomized causal study or sustained fresh-ingestion service guarantee. Original raw outputs: artifacts/fresh-http-load-before-pool.json and artifacts/fresh-http-load-after-pool.json.

Twelve replay subscribers over 60 seconds received 4800 events (80/s), p95 SSE 374.766 ms and p95 ingest 165.418 ms, with no harness-reported failures. Its target_passed remains false because duration is below 600 seconds. The separate 600-second run passed its defined local replay regression gate: 46,439 events, 77.398/s, 928 completed generations, SSE p50 196.454 ms / p95 386.826 ms / p99 714.671 ms, ingest p95 188.947 ms, no harness-reported failures. All ten one-minute windows exceeded 1,200 received events. Raw result: artifacts/replay-stress-after-pool-600s.json. This is replay transport under the tested local profile, not fresh device-ingest, browser-rendering, physical commissioning or field accuracy qualification.

Tested image: sha256:ae08ef3ae1eb107b8b942301ce060be17bb6120542e36fb6df2a9e99a4817e37. Source hashes are in artifacts/fresh-source-hashes.json. Historical failed 600-second test remains preserved separately; results must not be merged.

## Demonstration and remaining work

Open http://127.0.0.1:8000, choose Score a New Cut, load measured example and validate. Approve review, record a finding explicitly describing its source, complete and export. Submit unsupported example to show abstention. The sample is selected for illustration, not proof of a timely successful intervention.

Physical source remains unconfigured. Arbitrary newly measured plant data receives unsupported_domain until mapping, extraction and predictive qualification. Fresh authenticated device HTTP/MQTT intake, reference OPC UA integration, durable edge spool/receipts, customer identity/scopes, real scheduling/assignment/expiry, structured outcomes, model promotion/rollback, independent-machine validation and prospective field utility remain incomplete. Hardware absence does not block those independent software tasks.

Next critical path: scoped device registration and authenticated durable fresh ingestion, followed by spool/protocol fixture recovery tests. Production readiness is not claimed.

Independent agent audit was unavailable after worker usage limits; primary-agent commands and evidence above are the current verification, not a multi-agent approval.


## Final added checks

Two release tests verify effective training rows/group exclusions and numeric serving parity against a scikit-learn refit on the declared training rows; final Python suite is 36 passed, one deprecation warning, 14.27 seconds. This is implementation parity, not new predictive-efficacy evidence.

A consistent pg_dump was restored into a disposable PostgreSQL container with no network or published ports. Restore plus verification took 70.902 seconds locally. Restored counts were 606 assessments, 65 sessions, 54,055 replay readings and zero orphan assessments. All 606 canonical evidence digests matched their assessment/database digests. This validates local database backup restoration; it does not validate encrypted off-site backup, customer identity recovery, full application recovery or cloud RPO/RTO.

Source archive: release/kerfpulse-ai.zip. Showcase archive with verified benchmark/model assets: release/kerfpulse-ai-showcase.zip. Both exclude credentials, database volumes, private backups, caches and dependency directories. SHA-256 sidecars are generated for each. Review NOTICE.md for benchmark attribution.
