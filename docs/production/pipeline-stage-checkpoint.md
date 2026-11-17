# Operational pipeline and research-gate checkpoint

## Implemented

- Experiment identity now includes source observations/labels, preprocessing/inference code, feature lists, exact group partitions, Python/package versions, selected runtime settings and GPU/driver identity. Mismatched resumes fail closed. Duplicate seeds/families are rejected; finite search-space limits prevent an infinite unique-candidate loop.
- Calendar-conditioned regret-acquisition primitive and nested experiment runner added. Training gate labels are generated from training-only cross-fitted current/fused predictions. Optional outer-test features sit behind a callback invoked only after the cheap acquisition decision. Prefix quotas, unsupported breaks and invalid evidence are tested. The candidate experiment is implemented but not trained/evaluated yet.
- Device receipt consumer added as assessment-worker Compose service. Semantic duplicate events reuse the original assessment; conflicts are recorded without replacing original evidence. Revoked and late sources cannot create fresh advice. Assessment, processing state and outbox commit in one transaction; injected outbox failure rolls back assessment and allows clean retry.
- Device receipt retrieval now reports processing result. Device-scoped /api/v2/events supports bounded cursor catch-up; /api/v2/events/stream supports SSE, Last-Event-ID, repeated authorization and connection bounds. No demo-session permission grants access to these device feeds.
- PostgreSQL migration lookup now uses current_schema() instead of assuming public. Real operational verification runs in an isolated temporary schema and removes only that schema.

## Actual integration result

scripts/verify_operational.py ran inside the API container against PostgreSQL and a temporary loopback API/worker pair. HTTP intake, worker abstention, idempotent assessment, cursor catch-up and SSE delivery passed. Test data are authentic benchmark values used exclusively as protocol fixtures in the isolated schema. Operational public tables were not populated with these test observations.

The unqualified measured-source result remains unsupported_domain with unavailable score. This completes durable processing and auditable abstention; it does not qualify the source, prove real-machine accuracy, or complete the customer-facing operational UI.

## Research status and resource blocker

The expanded run was attempted with six families, twenty candidate configurations and seeds 17/29/43. It paused before fitting because available physical RAM stayed below the 2 GiB reserve (observed about .83 to 1.08 GiB). The primary agent stopped only this paused research process; user applications and WSL were untouched. No new expanded-comparison metrics exist. Initial CUDA findings remain unchanged.

Use a new fingerprint-compatible directory after memory headroom recovers:

```powershell
.venv-gpu/Scripts/python.exe -m pdm.gpu_benchmark --methods age_only context logistic current_no_age fused mlp --trials 20 --seeds 17 29 43 --output artifacts/gpu-development-expanded-v3
.venv-gpu/Scripts/python.exe -m pdm.acquisition_research --output artifacts/acquisition-regret-development-v1
Get-Content scripts/verify_operational.py -Raw | docker compose exec -T api python -
```

Candidate costs 1/20/.1 are fixed illustrative normalized decision/acquisition costs, not factory financial estimates. All policies share the chosen threshold and declared maximum budgets; actual acquisitions can differ. Current, full-fusion, periodic, random and learned-gate comparisons retain the no-opportunity cutter. Statistical superiority, energy savings and avoided downtime remain unproven.

## Next gates

Complete comparisons/uncertainty; qualify actual extractor/model/source contracts; add customer OIDC and role scopes; expose operational history/source health and inspections in the human UI; integrate authenticated MQTT and real protocol fixtures; validate fresh-path capacity/soak, retention, encrypted full restore and rollback. Physical commissioning and prospective outcomes remain external gates.

## Verification checkpoint

Full Python suite: 80 passed, one existing TestClient deprecation warning. Docker rebuild/startup passed configured checks, including assessment-worker heartbeat. PostgreSQL HTTP/worker/cursor/SSE integration passed in an isolated schema. Candidate experiment compiles and primitive tests pass; no candidate-training result claimed. Browser final result is appended after corrected rerun.

Corrected final browser rerun: 7 passed in 38.3 seconds using one Playwright worker. Initial failed CSV test and correction are retained in execution ledger.
