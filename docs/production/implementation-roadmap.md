# Dependency-ordered implementation roadmap

Sprint 1 delivers the bounded fresh-data slice: audit repository (lead), pin release/input contract (ML), fresh inference and durable review (backend), CSV/JSON UI and evidence history (frontend), then source and browser verification (QA). Current implemented slice uses server-session identity and reference publisher features. See acceptance matrix for verification state.

Sprint 2 delivers scoped asset/device identity, typed ordered intake, conflict quarantine, explicit migrations/pooling, receipts and bounded spool (platform), plus calibrated load generator with at least 12000 events in ten minutes (performance). Repeat historical stress first, instrument connection/commit/queue stages, and compare one change at a time.

Stage 3 adds read-only OPC UA client against a fixture and source-adapter health contracts, deterministic extraction and commissioning record (OT). Physical qualification stays blocked by hardware/mapping.

Stage 4 adds new baselines, training-only policy selection, independent-machine task and prospective label plan (research/reliability). Preserve negative results.

Stage 5 validates staging identity, backups/restore, promotion/rollback and UX accessibility (platform/security/QA). Stage 6 collects shadow data on commissioned equipment; Stage 7 limits advisory production to approved domain. Stage 8 expands only with repeatable commissioning and independent-site evidence.

Engineering estimates are sprint-sized proposals. Field efficacy has no calendar estimate until machine access, event rate and outcome maturity are known.

## Dependency-ordered acceptance work

| Stage | Owner role | Deliverable | Exit evidence |
|---|---|---|---|
| 1: Fresh evidence | ML/backend/frontend | Released artifact, strict import, applicability, persisted review, quarantine and export | Unit/API/browser results and demonstrable new-identity scoring |
| 2: Platform reliability | Platform/performance | Bounded pooling, migrations, scoped durable intake, application receipts, calibrated open-loop load | Rollback/concurrency/restart tests; no lost/duplicated accepted effects; backlog reconciled |
| 3: Read-only integration | OT/security | Adapter interface, authenticated HTTP/MQTT, reference OPC UA fixture client, bounded edge spool | Real protocol fixture tests, reconnect/gap/reset/permission failures; no claim of physical connection |
| 4: Identity/workflow | Security/product | Customer OIDC, org/site/asset/device scopes, assignment/expiry, structured findings and calendar source | Negative authorization matrix and full human lifecycle acceptance |
| 5: Research validation | Reliability/ML | Strong baselines/ablations, frozen grouped protocol, independent machine qualification | Reproducible comparison and predeclared cost/coverage/uncertainty gates |
| 6: Operations | Release/site IT | Private staging, TLS, metrics, encrypted backup, restore and rollback | Second-operator installation, actual RPO/RTO, incident rehearsal |
| 7: Field shadow | Site/reliability | Commissioned mappings, consecutive fresh evidence and mature outcomes | Independent numerical and predictive validity with reviewed labels |
| 8: Advisory use | Site accountable owner | Restricted approved-domain rollout with human review | Signed service/model/workload acceptance and monitored rollback criteria |

Stage 1 is a demonstrable engineering slice, not completion of KP-001..017 in production. Pooling work in Stage 2 does not authorize skipping device identity, receipts or field evidence. None of these stages enables autonomous machine control.

## Immediate next critical path

Finish the current 600-second replay regression and archive the exact image/source hashes. Then implement scoped device registration, authenticated fresh ingress and durable receipts before routing fresh MQTT events. Add spool fault-injection tests before advertising reconnect safety. Commission an OPC UA fixture as a protocol test only. The first physical pilot waits for real sensor mapping and machine access; other software stages continue independently.
