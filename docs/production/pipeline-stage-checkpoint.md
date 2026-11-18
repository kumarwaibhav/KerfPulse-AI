# Operational pipeline and research-gate checkpoint

## Latest continuation — 18 November 2026

This section supersedes pending-state descriptions in historical sections below. Expanded comparison and acquisition experiments completed in the prior qualification milestone; negative/uncertain results remain unchanged. See [current staged plan](staged-development-plan-2026-11-18.md) and [eleven-repository research](../research/repository-review-2026-11-18/README.md).

Named OIDC code/PKCE login, bounded signed-token validation, opaque sessions, exact org/site/asset read grants, local grant/revoke administration and Operations UI implemented. Actual local Keycloak browser login, default no-grants, empty scoped source list, CSRF rejection, logout and post-logout denial passed. No device/source grant or physical qualification was created. Local Keycloak profile is development-only; public IdP hosting and named inspection writes remain open.

Source health now includes processing pending, unsupported/missing model evidence, rejected input, changed qualification revision and quarantined transport conflict reasons. Historical assessments remain immutable. Fresh source reads wait for demo initialization. Named Operations starts independently of demo-session capacity. Nine isolated browser scenarios passed after UI fixes, 39.6 seconds; temporary test project/network/volumes removed, existing operational data retained.

Bosch integrity/recording-partition foundation implemented. Actual HDF5 verification passed for one 268,288×3 recording with publisher blob/size and SHA-256 match. Catalog: 1,702 recordings; 1,701 not acquired locally. No anomaly model trained or RUL target inferred. Five targeted raw-data/audit tests passed in GPU research environment using installed h5py. Research protocols saved before future fitting.

First-stop diagnostic checks saved data/code/split identities and fold/report consistency against pinned measurements. It reproduces five supported lives, eight recipe abstentions, one no-pre-damage life, 375 supported and 577 unsupported cuts. Historical nonzero acquisitions cannot be divided before/after first inspection: event traces were not saved. Original experiment omitted policy.py from dependency fingerprint. Both limitations remain explicit; no historical artifact was repaired or rewritten. Future protocol requires event traces and complete dependency hashes. Source-byte line endings are preserved by Git attributes for reproducible hashes.

Python suite passed 109 tests with one optional h5py test skipped in native runtime and one existing TestClient warning before final added saved-artifact regression. Final total appended after execution. Runtime Python and production npm dependency audits found no known vulnerabilities at this check; scans are not full security certification. Git/Docker packaging excludes private identity credentials and downloaded reference caches.

Open gates: first-stop experiment implementation/execution, complete Bosch acquisition/anomaly baselines, named inspection/calendar/assignment/outcome workflow, industrial adapters/extractor attestation, fresh-path capacity/soak/restore/rollback, independent-machine and prospective validation. No factory-ready or superiority claim.

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


Final continuation checks:110 Python tests passed,1 optional h5py skip,1 existing TestClient warning (29.06s). Five raw/audit tests passed in research environment; final nine browser scenarios passed in39.6s. Actual local Keycloak and PostgreSQL operational integration passed. Full npm audit retains4 high package entries from one unpatched build-tool Picomatch advisory; production npm/runtime Python scans had no known findings. See identity-research-verification-2026-11-18.md. No new model training/promotion or physical commissioning claimed.
