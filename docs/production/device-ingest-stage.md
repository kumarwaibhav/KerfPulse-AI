# Device ingestion foundation: durable inbox stage

`pdm.device_ingest.DeviceIngest` is a standalone service over the existing `Store` transaction interface. It does not expose a route, deploy a gateway, run inference, operate machinery, or commission a sensor. Operational device, boot, receipt and quarantine records have no dependency on demo sessions or demo cleanup.

## Integration contract

Initialize `DeviceIngest(store).initialize()` during trusted service startup. A trusted administrative orchestration layer must authorize `register_device(org_id, site_id, asset_id)`, `rotate_token(device_id)` and `revoke_device(device_id)`. These methods themselves do not implement administrator authentication. Registration fixes immutable scope and returns a random bearer credential once; only its SHA-256 hash is stored. Rotation invalidates the old credential immediately after commit. Revocation blocks subsequent ingestion and receipt retrieval. Existing records remain retained. The credential digest comparison uses `hmac.compare_digest`; this does not make the full database-backed request constant-time.

Device ingress calls `ingest(token, envelope)` and acknowledges success only after the method returns and its transaction commits. The envelope is exactly:

```json
{"schema_version": 1, "boot_id": "unique-boot-identity", "sequence": 1, "event": {"...": "completed-cut fields"}}
```

`event` follows the completed-cut field structure in `pdm.fresh_model.input_schema()` but must declare `data_origin=user-measured`, `clock_basis=observed` and `source_mode=uploaded`. The benchmark example is demonstration evidence and must not be relabelled for a real submission. Tests adapt the example exclusively as protocol fixtures; this supplies no physical validation. All provided values, timestamps and identifiers survive persistence without generated sensor values. The provisioned asset must match `event.asset_id`; organization and site come exclusively from the registry. Unknown envelope/event fields are rejected. Feature names and values are bounded transport fields; inbox acceptance does not establish compatibility with any model's feature set or a calibrated sensor profile.

The envelope has a 65,536-byte canonical JSON bound, at most 256 feature fields, 100-character identifiers/measurement names, finite numeric values of absolute magnitude at most 1e12, and at most 100 future inspection ordinals. Device sequence is 1..2^63-1; the cut ordinal follows the existing 1..100000 contract. The two sequences have distinct meanings. UTC offsets are required on observed timestamps and evidence more than 60 seconds into the future is rejected. Old evidence can be durably retained; no freshness qualification is performed here.

Before a future HTTP adapter decodes JSON it must bound the raw body, reject duplicate JSON keys, authenticate bearer credentials without logging them, and apply TLS, rate limits and capacity controls. Translate `DeviceAuthError` to 401 and other contract errors to 422; choose a documented conflict response containing the durable quarantine receipt. Existing demo cookies are not device credentials or administrator authorization. Do not publish registry administration without real administrator identity and scope authorization.

## Receipts, retries and ordering

The idempotency key is `(device_id, boot_id, sequence)`. SHA-256 covers sorted-key, compact, finite JSON. JSON key order is irrelevant; numeric spelling such as `1` versus `1.0` remains distinct. An exact retry returns the original ID with `status=duplicate`. A different payload at the same key is persisted in quarantine and returns `status=quarantined` plus `quarantine_id`; the original is never overwritten. Repeating the same conflict returns the same quarantine ID. Reusing the same event ID at a different transport key is not deduplicated: a future consumer must define its own event identity policy before creating effects.

`status=persisted` means committed inbox evidence, with `inference_status=not_started`. It does not mean an assessment, alert or work order exists. `get_receipt(token, id)` retrieves original evidence only for that device; other devices receive no record even within the same organization. A conflict response carries the original receipt digest; the conflicting evidence and its own digest are retained in the quarantine table.

Sequence tracking is per device and boot. `contiguous` means the sequence immediately follows the arrival high-water mark; `gap` reports `missing_before` at arrival; `out_of_order` identifies an unseen lower ordinal. These are immutable arrival diagnostics, not a current count of missing messages. Late arrivals do not rewrite prior receipts or prove a gap remains open. The sender must persist its boot identity and retry sequence across connection loss and use a fresh boot identity when restarting its counter. This is not protection against a compromised device deliberately choosing new identities. SQLite write transactions serialize ingestion; PostgreSQL locks the device row to serialize retries, rotation and revocation for that device.

## Verification and remaining gates

Local SQLite tests cover durable reopen, exact evidence preservation, hashed credential storage, authentication failure, rotation, revocation, scope mismatch, canonical retries, conflict retention, gaps, out-of-order arrival, boot reset, concurrent retries, size bounds and invalid contracts. The existing model continues to mark user-measured evidence as `unsupported_domain`; this module does not change that gate.

Before a physical pilot: provision real administrator/device identities; add and verify a bounded transport adapter; define retention, quota, backup/restore and monitoring; exercise PostgreSQL migrations, concurrency and failure recovery against a running server; verify offline device spool/retry behavior and clocks; obtain actual sensor/profile qualification evidence. A consumer, durable processing state, retries, idempotent assessment effects, and explicit quarantine review remain separate work. No end-to-end hardware test, inference completion, production readiness, or public deployment is claimed by this stage.


## HTTP and edge integration added

/api/v2/ingest/cuts now accepts device bearer credentials independently of demo sessions. The application body cap remains 64 KiB; duplicate JSON keys are rejected. Database work is dispatched off the async event loop. /api/v2/receipts/{id} returns only that device's receipt/evidence. No public provisioning endpoint exists; local trusted administration uses pdm.device_admin and writes the one-time token to a private file rather than logs.

pdm.edge_spool persists before sending, bounds logical queued payload bytes and event count, and deletes only after an application receipt matches status, digest, boot and sequence. Requests follow no redirects, protecting the bearer credential; HTTPS is mandatory except loopback development. Conflict/mismatched receipts retain evidence. A real temporary loopback server test verifies retry produces one stored receipt. Tests use authentic benchmark values as protocol fixtures only and supply no plant-validity evidence.

This is a tested ingestion foundation. Automatic backoff daemon, source registration UI, MQTT ACLs, operational quotas/retention, inference consumption and full pipeline fault injection remain open. Incoming measured values do not gain model qualification merely by receiving a durable receipt.


### Provision against the running Compose database

The native CLI defaults to the native SQLite configuration. For the running PostgreSQL stack, execute inside the API container, then copy its one-time private file to an ignored local directory. No credential value is printed:

```powershell
New-Item -ItemType Directory -Force artifacts/private-device | Out-Null
docker compose exec -T api python -m pdm.device_admin --org evaluation-org --site evaluation-site --asset mill-1 --output /home/app/device-credentials/mill-1.json
docker compose cp api:/home/app/device-credentials/mill-1.json artifacts/private-device/mill-1.json
```

The output path must not already exist. Provisioning is local trusted administration, not customer identity authorization. Protect that private file using the host's access controls; do not commit or distribute it. Genuine compatible observations can be queued using EdgeSpool and delivered with flush_http; no benchmark example should be relabelled as actual field evidence. Current ingest records remain unqualified and inference is not started.


## Durable inference-consumer stage

The Compose assessment-worker now consumes operational receipts. Its result and durable event outbox commit atomically. Device-scoped receipt GET reports processing state and assessment/abstention. /api/v2/events returns bounded cursor catch-up, while /api/v2/events/stream emits authorized SSE with cursor recovery and repeated credential checks. Raw input retention is separate from these notifications.

Semantic event identity is device plus event_id: identical events carried under another transport sequence reuse the assessment; changed semantic evidence is quarantined in processing without replacing the original. Out-of-order and revoked pending sources cannot produce fresh advice. Model contract failures become explicit rejected records; database failures roll back and retry.

Current user-measured evidence remains unqualified, so successful processing normally reports abstained/unsupported_domain with no score. This is processing completion, not a physical-source approval. Customer role-scoped browser views, source qualification/promotion, operational retention/capacity, and authenticated MQTT remain pending.
