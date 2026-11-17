# Deployment and operations

Local engineering profile is Docker Compose with PostgreSQL, Mosquitto, API/UI, legacy replay gateway and worker. Fresh inference runs in the API using the same numeric inference helper as benchmark replay. Fresh intake commits assessment and submitted evidence in one transaction. Run scripts/setup.ps1 with PowerShell 7 to reproduce data, legacy model and engineering release, then docker compose up --build -d. Health endpoint checks service/database and legacy artifact presence. Inspect individual freshness before claiming a source is connected.

Private staging requires OIDC, scoped fixture devices, migration/version verification, application-level device receipts and a passing sufficient-volume load gate. Shadow pilot further requires actual commissioning and reviewed outcomes. Qualified human advisory production requires model utility and service reliability acceptance signed by site ownership.

Proposed recovery targets are server RPO <=15 minutes and RTO <=4 hours; restore and encryption evidence remains required. Capture PostgreSQL backups with restricted access, exercise restore in an isolated instance, and test matching source/model manifests before rollback. Preserve all historical assessment artifacts. No hosted destination is configured. Remaining inputs are an authorized hosting destination, secrets/identity settings and qualified machine mapping.

## Repeatable local operation

```powershell
Set-Location E:/pdm_aiiot
# First installation/reproduction; requires downloads and model fitting.
pwsh -File scripts/setup.ps1
# Start existing prepared source and artifacts.
docker compose up --build -d --wait
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/healthz
# Verification
.venv/Scripts/python.exe -m pytest -q
npm.cmd --prefix web run test:e2e
Get-Content scripts/verify_postgres_pool.py -Raw | docker compose exec -T api python -
```

PostgreSQL transactions now borrow bounded connections through psycopg-pool 3.3.3. Default maximum is eight per Store/process, one minimum, 64 queued checkout requests, and ten-second checkout timeout. PDM_DB_POOL_SIZE accepts 1..32. PDM_DB_POOL=false restores connection-per-transaction for controlled comparisons. Different processes have separate pools; size their sum against database capacity. Checkout validation discards broken connections; transaction context rolls back exceptions before reuse. [Psycopg pool documentation](https://www.psycopg.org/psycopg3/docs/advanced/pool.html).

API lifespan and replay service shutdown close their pools. This change does not add durable edge buffering, connection-level customer identity, or asynchronous batch processing. SQLite development still uses serialized local write transactions.

## Monitoring and operational meaning

Use /healthz for current database/service status; its legacy model and dataset flags are existence checks, not full model qualification or commissioning checks. Physical status remains unconfigured. /metrics exposes aggregate saved-run/cut/release/byte counters from the replay store; it does not yet represent fresh source queue depth or service-level error budgets. Monitor API errors, pool wait/checkout time, outbox growth, worker heartbeats, source freshness and export/backup failures before pilot use.

During an incident, stop accepting field advice if source identity, freshness or model compatibility is uncertain. Keep original evidence; do not repair a conflicting event by overwriting its accepted payload. Restart only the affected application service with docker compose restart api, worker or gateway. Broker/DB outages require checking persisted effects and cursors after recovery. Never delete named volumes as a recovery shortcut.

## Release and rollback

Archive exact source package, image digest, dataset checksum, model/manifest bundle, configuration references and verification receipts. The source ZIP excludes data, models, credentials, databases and dependency caches; setup regenerates verified inputs. Preserve exact approved model artifacts separately because numerical refitting need not reproduce byte-identical coefficients. Never package .env or database credentials in an investor bundle.

For rollback, restore a previously tested image and compatible model bundle together. Keep existing historical evidence/model identifiers. The fresh schema upgrade is additive; full down-migrations and controlled model promotion remain open gates. Restore rehearsal must use an isolated database and compare counts/digests before declaring a backup usable.


## Verified local restore rehearsal

Run `pwsh -NoProfile -File scripts/verify_restore.ps1` from the workspace after starting Compose. It takes a consistent custom-format pg_dump, starts a unique disposable PostgreSQL container without network/ports, restores without project credentials, checks restored records and canonical assessment evidence digests, saves aggregate evidence and removes only its own fixture/anonymous volume. It does not stop or remove project services/volumes.

Current rehearsal restored 606 assessments and 54,055 readings, with zero orphan assessments and all 606 evidence digests matching, in 70.902 seconds. Raw dump and row material remain in artifacts/private-backup, excluded from both release packages. This local backup is not encrypted or an approved off-site retention mechanism. Aggregate restore-verification.json contains no record payloads. Full application/OIDC recovery and field RPO/RTO remain unverified.

`pwsh -File scripts/package.ps1` produces the source archive; add `-IncludeAssets` for the showcase archive with pinned public data, nested research artifacts and engineering release. First installation still needs Docker/base images and package downloads. Do not replace .env with real credentials in either archive.
