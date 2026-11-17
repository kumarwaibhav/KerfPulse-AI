# Current-stage audit and feature coverage

Primary agent inspected actual model/release, upload parsing, API/session, persistence, Docker and browser sources, ran tests/builds/scans, and retained evidence. This is a scoped engineering audit; independent worker review was unavailable after usage limits. No complete penetration-test or production sign-off is claimed.

## Feature inventory and evidence

| Area | Features inspected/tested |
|---|---|
| Fresh import | Measured and unsupported examples, editable JSON preview, single/array/envelope JSON parsing, CSV import and quoted fields, CSV/JSON templates, byte/row caps, partial row errors |
| Forecast | New event/tool IDs, 72 current features plus six context fields, released artifact, no outcome inputs, missing/stale/unsupported/no-slot states, declared clock/source and digest |
| Persistence | Save/reload/history/export, identical retry, changed-evidence quarantine, original retained, session ownership and cleanup |
| Human workflow | Approve, dismiss, nonblank finding completion, optimistic version/state checks, actor/time/finding history |
| Research web | Replay configuration and policies, paired run, pause/resume, saved state, export, evidence table, data-quality gaps/conflict, benchmark metrics, dataset link |
| Delivery/UI | SSE socket-loss catch-up, light/dark persistence, desktop/mobile overflow checks, source labelling, failed-request feedback and retry |
| Runtime | PostgreSQL pool reuse/concurrency/rollback, Compose startup, short fresh HTTP comparison, 12-replay 600-second transport regression |

The inventory is not proof of exhaustive combinations. Browser scenarios do not cover a customer role hierarchy because that hierarchy does not exist. Full screen-reader/contrast testing, authenticated device boundaries and live field fault injection remain pending.

## Remaining severity-ranked findings

| ID | Severity / location | Consequence and next correction |
|---|---|---|
| C-01 | HIGH — pdm/api.py:137 | Public local session creation provides demo planner access; no customer OIDC. Keep loopback profile and add authenticated tenant/site/asset grants before public deployment. |
| C-02 | HIGH — deploy/mosquitto.conf:4 | Anonymous peers on the private Compose network can publish. Add per-device identity/TLS/topic ACLs and revocation tests before field intake. |
| C-03 | HIGH — pdm/fresh_model.py:99 | Actual user-measured domains are unqualified and intentionally abstain; current software cannot promise useful advice on arbitrary machines. Commission extraction and independently validate the supported domain. |
| C-04 | HIGH — pdm/fresh_model.py:49 | Origin is a client declaration, not signed device provenance. Add source registration and scoped authenticated ingestion/receipts; never treat the declaration as attestation. |
| C-05 | HIGH — pdm/fresh_api.py:56 | Fresh workflow is synchronous session upload, without device ordering/spool/restart receipts. Add durable scoped intake and failure-injection recovery before describing it as live industrial ingestion. |
| C-06 | MEDIUM — pdm/fresh_api.py:114 | Review supports approve/dismiss/complete but lacks assignment/expiry/calendar ownership and structured labels. Complete those lifecycle requirements before plant workflow approval. |
| C-07 | MEDIUM — pdm/api.py:248 | Health endpoint checks DB and legacy file existence, not full new-release readiness/commissioning. Add separate readiness semantics and artifact/source monitoring. |
| C-08 | MEDIUM — pdm/fresh_api.py:13 | Startup additive upgrade is not a complete migration/version governance system. Add explicit migration history, compatibility and rollback rehearsal. |

## Corrected this stage

Fresh inference no longer requires an archived cutter-ID fold lookup. PostgreSQL hot paths use bounded pooling. Conflicting uploads now persist separately and cannot replace accepted evidence. History order is independent of review updates. Expired-session fresh records are cleaned. New schema disallows outcome fields, freshness/domain checks fail closed, and UI separates assessment mode from replay.

Model usefulness remains an empirical open issue: earlier AP and timed-inspection results are preserved, and a polished dashboard does not resolve them. Proposed novelty is a hypothesis requiring matched independent validation.
