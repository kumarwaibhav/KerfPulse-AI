# API and event contracts

The existing /api/session cookie is required. Scope derives from the server session. POST /api/fresh/assessments accepts {events:[event,...]} with 1–30 events, subject to the existing 64 KiB request limit. The browser bounds expanded files at 60 KiB. Response results contain one-based row numbers and either assessment or field/message errors. Successful rows persist even when another row is invalid. Retrying the identical event returns the same ID. Changed evidence reusing an event ID is quarantined and rejected as an accepted effect. Owner-scoped quarantine and deterministic history ordering are implemented; ordered device intake remains Stage 2.

GET /api/fresh/assessments returns owner-scoped history. GET /api/fresh/assessments/{id} returns an assessment. GET /api/fresh/assessments/{id}/export returns assessment plus original event. POST /api/fresh/assessments/{id}/review takes action, expected_version and optional finding. Draft can become approved or dismissed; approved can become completed with a nonblank finding. Conflict returns 409. History records action, actor, time and finding. Other sessions receive 404.

Assessments separate applicability (assessed, insufficient_evidence, unsupported_domain, stale, model_unavailable) from action (monitor, review_recommended, no_feasible_slot). A score is null if unavailable. Evidence digest, source clock, model digest/version and policy version remain attached. Monitor never constitutes a machine safety clearance. A calibrated plant failure probability and continuous RUL remain unsupported outputs.

## Quarantine and retention

Changed evidence under an accepted event ID is stored in a separate bounded quarantine, linked to the original assessment. Repeated delivery of the same conflicting digest returns the same quarantine ID. GET /api/fresh/conflicts exposes only that session's conflict records. Accepted evidence and review history remain unchanged. Limits are 300 assessments and 100 unique conflicts per demo session. Rejected malformed requests are not guaranteed an evidence record; no durable device receipt protocol exists yet.

Demo sessions expire after 24 hours. Cleanup removes their fresh assessments and conflicts; API startup also purges orphan records. Refresh/restart durability is not indefinite archival retention. Export important demo evidence before expiry. Customer retention, legal holds and audit administration need a separate operational policy.

History is ordered by a server-created timestamp plus ID, independent of later review updates. Startup performs an additive created_at column upgrade and history index creation under an initialization lock on PostgreSQL. This is a compatible local upgrade; it is not a complete versioned migration framework.

## Response and error behavior

| Condition | HTTP/row outcome | Effect |
|---|---|---|
| No session | 401 | No read or mutation |
| Viewer mutation | 403 | No assessment/review mutation |
| Cross-site browser write | 403 | Mutation rejected before handler |
| Request body over 64 KiB | 413 | No JSON parsing or write |
| Bad envelope/batch size | 422 | Batch rejected |
| Invalid row | 200 with row.errors | Other valid rows may commit |
| Same accepted event and digest | 200, original assessment | No second assessment |
| Same event with changed evidence | Row error and quarantine_id | Original retained, conflict stored within quota |
| Stale review version/state | 409 | History unchanged |
| Another session's assessment | 404 | No existence disclosure through that endpoint |
| Unsupported/stale/missing evidence | Saved assessment, null score | Explicit abstention; no inspection draft |

An event schema is supplied in schemas/completed-cut-event.schema.json. Dynamic checks such as clock skew, matching sequence, recipe compatibility and future inspection-break semantics still run on the server. CSV is a browser convenience format; it becomes the same canonical JSON envelope. Unknown CSV columns reach server validation and cannot add hidden outcome features.

## Example interpretation

At completed cut t=49, the next-five score covers damage at cuts 50..54. If the configured inspection break is s=50, the policy's actionable window covers damage at cuts 52..55, allowing two to five cut positions of lead after inspection. These are different windows; the actionable score is not a second independent model. The chosen high-score demonstration is not evidence of a timely successful maintenance intervention.
