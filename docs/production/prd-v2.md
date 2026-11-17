# KerfPulse v2 product requirements

## Problem and outcome

An operator needs to decide whether newly completed cutter evidence warrants human review for an inspection at the next available production break. KerfPulse packages validated evidence, a bounded forecast, reasons and an auditable review trail. Success for the engineer/investor showcase is a label-free measurement submission from an unseen tool identity, traceable assessment, saved human review and an explicit unqualified connection state. Plant success requires separate operational and model gates.

## Actors and scope

| Actor | Workflow |
|---|---|
| Operator | See assigned assets, evidence cutoff/freshness, applicability and review status. |
| Maintenance planner | Review and manage inspection proposals, ownership and available breaks. |
| Technician | Record method, finding, completion, uncertainty and observed time. |
| Reliability engineer | Evaluate evidence, model scope, calibration, policy and monitored outcomes. |
| OT/IT administrator | Register and qualify mappings and sources, provision identity and run operations. |
| Researcher | Reproduce experiments in a segregated context and submit candidates for controlled promotion. |

The local demo uses session-scoped planner/viewer access. Named operators, planners, technicians and administration become distinct roles in staging with customer identity and authorization. Software remains read-only against CNC controls throughout this plan.

Four source modes have distinct user labels and provenance: **Live physical source**, **Uploaded measurements**, **Recorded benchmark replay**, and **Protocol test fixture**. A connection remains unqualified until commissioned. Browser uploads and protocol fixtures assess completed cuts; during-cut anomaly detection and a continuous RUL estimate require distinct endpoints, models and validation. The current forecast classes support only the stated cut-position horizons.

## Requirements and observable acceptance

| ID | Requirement | Acceptance |
|---|---|---|
| KP-001 | Score an unseen tool from valid, supported completed-cut input. | Submit label-free event with a new tool-life ID; registered current model evaluates it without benchmark-ID lookup and result reloads. |
| KP-002 | Import bounded CSV and JSON with preview and row errors. | Preview a valid two-row import before submit; valid row persists, malformed row shows field and reason, oversized batch is rejected, re-upload returns the same assessment. |
| KP-003 | Commission identifiable live sources. | Authorized OT user registers site, asset, device and versioned mapping; connection advertises capabilities and remains unqualified until approved tests pass. |
| KP-004 | Preserve source and freshness. | Assessment and export carry mode, cut cutoff, arrival, asset/tool, schema, model/policy and digest; replay and fixture never claim a live device. |
| KP-005 | Gate applicability. | Unsupported schema/domain, missing evidence and stale qualified evidence produce distinct statuses with no numeric forecast. |
| KP-006 | Give bounded interpretation. | UI and API identify damage within next five cut positions, separate inspection-window score, benchmark-only calibration and model version. |
| KP-007 | Respect available breaks. | A configured calendar selects a feasible supported break. A break beyond the explicit model horizon returns no supported window. Demo calendar is visibly fixed. |
| KP-008 | Persist human review. | Eligible proposal supports approval/dismissal and completion; wrong state/stale version rejected; history survives refresh. Full scope adds actor assignment, expiry and reassessment. |
| KP-009 | Observe outcomes. | A technician records a review finding with provenance, method, uncertainty and observation time. Pending/censored observations remain distinct from verified damage labels. |
| KP-010 | Provide durable ingestion. | A repeated identity with same evidence has one accepted effect; changed evidence under same ID is quarantined and visible to the correct owner. |
| KP-011 | Recover with explicit gaps. | Inject broker/worker/DB loss, out-of-order events and bounded buffer exhaustion; device receipts, stale state and durable effects reconcile. |
| KP-012 | Enforce role and scope. | Attempt accessing another tenant, site, asset, stream, export and device topic. Backend denies every unauthorized call. |
| KP-013 | Audit decisions. | Retrieve assessed input digest, evidence cutoff, lineage and append-only review transitions from authorized history/export. |
| KP-014 | Govern models. | A bundle with a wrong hash or feature version cannot activate. Promote approved shadow candidate and roll back while preserving historical result lineage. |
| KP-015 | Keep the interface usable. | Complete preview, submit, status explanation and review using keyboard and touch; inspect focus, contrast and reduced motion. |
| KP-016 | Deploy and recover repeatably. | A second engineer installs fresh staging, upgrades, restores a backup and rolls back the model using checked commands, with measured RPO/RTO. |
| KP-017 | Preserve research integrity. | Replay and fresh assessments remain distinct and historical 2/14 versus 1/14 comparison remains visible and reproducible. |

## Nonfunctional and promotion gates

- Adopt a bounded synchronous import first. Publish request, row and storage limits with the [API contract](api-and-event-contracts.md); asynchronous bulk queues depend on measured demand.
- Initial sustained target is 20 completed-cut events per second for 600 seconds, p95 event-to-SSE under two seconds, bounded backlog and reconciled effects. Measure browser rendering separately. Lab targets are LCP ≤2.5 s, INP ≤200 ms and CLS ≤0.1 for the declared profile.
- Field utility requires decision costs, exposure and review workload agreed with a site before the final cohort. Independent machines, qualified mappings and prospective mature labels precede an operational claim.
- Open decisions requiring site data include actual break/calendar source, compatible sensor configuration, identity provider, data retention policy, action thresholds and acceptable review workload. These inputs do not block local development.

Test mapping and open evidence are maintained in the [acceptance matrix](acceptance-and-evidence-matrix.md).
