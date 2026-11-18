# Identity, reference research and raw-data milestone verification

Date: 18 November 2026. Status:verified engineering continuation; factory launch remains blocked. This document records completed checks and remaining findings, rather than a numerical readiness score without a validated rubric.

## Executed checks

| Check | Actual result | Scope/limit |
|---|---|---|
| Native Python suite | 110 passed, 1 optional h5py test skipped, 1 existing TestClient deprecation warning; 29.06s | Includes named access, signed OIDC claims, source health, source/fingerprint audit and prior platform regression |
| Research-environment targeted tests |5 passed in2.82s | Includes actual Bosch HDF5 bytes and recording partitions; uses installed h5py |
| Saved first-stop regression |3 tests passed in4.93s | Actual saved run and source verified; missing acquisition timing retained as unknown |
| TypeScript/Vite build | Passed | React interface compiled; no plant-validity implication |
| Isolated browser suite |9 passed in39.6s | Replay, fresh inference, review/export, SSE recovery, named Operations UI, delayed demo-session initialization and mobile rendering |
| Actual local Keycloak browser | Login/PKCE/RS256, no grants, scoped empty sources, CSRF denial, logout and post-logout denial passed | No mocked IdP tokens; no physical device/source grants created; local development profile only |
| PostgreSQL operational integration | HTTP intake, worker abstention, idempotency, cursor/SSE, shadow binding, revocation, lineage and source health passed | Unique temporary schema removed afterward; operational public tables not filled with protocol fixtures |
| Runtime Python dependency audit | No known vulnerabilities found | Runtime requirements only; advisory databases are time-dependent |
| Production npm dependency audit |0 findings | Build/development dependencies excluded by this scan |
| Full npm dependency audit |4 high package entries, 0 critical | One underlying unpatched Picomatch advisory; details below |
| Bosch audit |1 publisher-verified local recording, 1, 701 missing | Catalog1, 702; sample268, 288×3, 134.144s at publisher-declared2kHz; raw units unqualified |
| First-stop audit |375 supported/577 unsupported cuts; 5 supported/8 unsupported/1 no-pre-damage lives | Retrospective analysis only; no new model fitting |

Browser rendering fixtures are explicitly labeled in tests. They do not supply training data or replace actual server authorization tests. Historical measured values in integration fixtures exercise protocol behavior; they are not represented as live factory measurements.

## Findings and disposition

| Severity | Finding | Location | Disposition |
|---|---|---|---|
| HIGH, dependency advisory | Picomatch<=4.0.7 can exhibit ReDoS for attacker-controlled repeated extglob patterns; audit propagates through fdir, tinyglobby, Vite | `web/package-lock.json`, installed `node_modules/picomatch` entry | **Open:** registry latest4.0.7, 4.0.8 absent; advisory lists no patched release. Do not claim full audit clean |
| MEDIUM, fixed | Fresh workspace could request source health before session cookie existed, producing401 on fast navigation | `web/src/App.tsx`, `web/tests/source-health.spec.ts` | Wait for demo initialization; deterministic delayed-session regression passes |
| MEDIUM, fixed | Named Operations inherited demo capacity/error presentation and requested demo sessions | `web/src/App.tsx`, `web/tests/operations.spec.ts` | Lazy demo startup; named view independent; no demo-session request verified |
| MEDIUM, fixed | Generated private identity credentials/reference caches could enter Docker build context | `.dockerignore` | Explicit exclusions added; selective Docker COPY also excludes these files |
| MEDIUM, research limitation | Historical acquisition totals cannot identify savings before first intervention | `pdm/acquisition_research.py`, saved report schema | Preserve totals; new audit reports unknown timing; future event trace/terminal objective required |
| MEDIUM, research limitation | Historical configuration omitted policy.py dependency hash | `pdm/experiment_provenance.py` historical contract | Do not rewrite saved configuration; audit records current policy hash and explicit attestation gap; future runner must fingerprint all dependencies |
| MEDIUM, open production scope | Public IdP operations, centrally enforced provider logout, full named inspection writes and field authorization policy incomplete | `pdm/oidc.py`, `pdm/operations_api.py` | Local access foundation only; production rollout blocked until scoped acceptance |
| LOW | Existing Starlette TestClient/httpx deprecation | Test environment | Non-failing warning retained; migration requires compatible supported test-client dependency validation |

Picomatch is in the frontend **build/development tree**. Production image serves compiled static assets with Python/FastAPI; Node/Vite and its dependency tree are not copied into the final image. Inspected project configuration does not accept user-supplied glob expressions. Development/preview servers are explicitly loopback-bound, and builds must use trusted workspace configuration. These limits reduce application exposure; they do not fix the underlying dependency. [Reviewed upstream advisory GHSA-fc5q-39xc-vjpf](https://github.com/advisories/GHSA-fc5q-39xc-vjpf).

No forced Vite downgrade or unsupported dependency version was introduced to suppress the audit. Retest against a maintained patched release when available; keep full audit finding visible until then.

## Reproduce

```powershell
Set-Location E:/pdm_aiiot
.venv/Scripts/python.exe -m pytest -q
.venv-gpu/Scripts/python.exe -m pytest tests/test_bosch_data.py tests/test_first_stop_audit.py -q
npm.cmd --prefix web run build
pwsh -NoProfile -File scripts/verify-browser.ps1 -Port 18001
pwsh -NoProfile -File scripts/setup-identity.ps1
node scripts/verify-identity.mjs
Get-Content scripts/verify_operational.py -Raw | docker compose exec -T api python -
npm.cmd --prefix web audit --json
```

Local IdP test reads generated credentials from ignored private files; it never prints them or grants machine access. Full npm audit currently exits nonzero for the disclosed advisory. New raw/audit output paths use exclusive creation: choose a new filename instead of overwriting an earlier receipt.

## Remaining launch blockers

Publication verification: first GitHub Actions run44221439456 completed successfully, reproducing measured benchmark assets, frontend build and Python checks on a clean Windows runner. Published snapshot487fc2892d5514334318a71feda9dc4de60182f9 used authenticated account kumarwaibhav and owner display name, but its configured email was linked by GitHub to profile kumar-waibhav. Future author/committer email is pinned to verified account130293310+kumarwaibhav@users.noreply.github.com. Shared history is retained; publication helper validates every later commit and the immutable baseline.

Demonstrated first-inspection utility and independent-machine/prospective validity; trained/qualified raw-signal branch; complete named inspection/calendar/assignment/outcome workflow; authenticated read-only industrial adapter and extractor attestation; fresh-path load/soak/retention/encrypted restore/rollback; production identity/deployment controls; signed site acceptance. These are explicit staged work, not completed by passing the checks above.
