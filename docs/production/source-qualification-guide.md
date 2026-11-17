# Source/model qualification and operator health

## Implemented policy

Source qualification is a trusted-local, append-only registry. Each revision binds a registered device to feature schema, sensor profile, extractor version and exact model digest, together with actor, evidence reference/reason, recording time and expiry. Incoming events cannot set their own qualification. No demo-session API can approve a source.

States available are unqualified, extraction_verified, shadow_approved and revoked. Current released model is engineering-demonstration-only; advisory approval is disabled. Shadow approval authorizes research scoring under compatible profile and recipe, never an operational inspection recommendation. Extractor version is recorded but not attested by current device transport, so this stage cannot prove physical extraction equivalence. A local approval record does not establish factory commissioning.

Unqualified, expired, revoked, mismatched schema/profile or changed model digest fail closed. Model contract, missing channels, stale measurements and unsupported recipes still apply. Physical status remains uncommissioned. Shadow results carry action=shadow_only when an actionable window exists; they never create operational review requests. Normal browser uploads cannot use the internal qualification argument to bypass eligibility.

Registry changes affect only subsequent processing. Each assessment snapshots resolved qualification revision and model identifier. Revoking or replacing qualification never rewrites old assessment/outbox evidence. Duplicate event identities return original lineage; explicit new evidence identity is required for future reassessment.

## Operator access and UI

Open Score a New Cut. The Source qualification & health panel lists only explicitly assigned sources for the current workspace. It shows qualification/revision/expiry, physical commissioning status, cutoff/receipt time, processing outcome, and unqualified/stale/transport reasons. It refreshes every 15 seconds or on demand; network failure keeps an explicit outdated-status warning.

Without grants, panel shows no assigned sources and no live-factory claim. Expand Local evaluation source access to copy the workspace ID. It is not a bearer credential. Local administrator grants read access to a specific device; no device token is placed in browser storage or URLs. Grants are session-scoped local evaluation access, not customer OIDC or a complete role hierarchy. Session expiry removes access; operational evidence remains independent of demo-session cleanup.

## Local trusted commands

Use actual registered device and active workspace IDs, never sample placeholders as machine identity. Commands below execute against the running Compose database:

```powershell
docker compose exec -T api python -m pdm.qualification_admin grant --workspace WORKSPACE_ID --device DEVICE_ID
```

To record a revision, prepare a JSON profile with feature_schema_version, sensor_profile_version, extractor_version and model_digest from the exact verified bundle. Copy that file into the API container, then run:

```powershell
docker compose cp profile.json api:/home/app/profile.json
docker compose exec -T api python -m pdm.qualification_admin record --device DEVICE_ID --state extraction_verified --profile /home/app/profile.json --actor ENGINEER_ID --evidence "Actual evidence reference and limitations" --valid-until FUTURE_ISO_TIMESTAMP
```

Shadow approval uses the same command with state shadow_approved and requires a matching installed release. Use revoked to withdraw qualification. An expiry requires an actual future ISO timestamp with timezone. These are local administration tools; do not expose Docker access or these commands to untrusted users. No actual plant source was approved as part of this build.

## Verification

SQLite tests cover default abstention, shadow-only scoring, revoked revisions, expiry, model digest change, sensor mismatch, workspace isolation and historical lineage. PostgreSQL isolated-schema integration verifies HTTP intake, worker, shadow binding, revocation and immutable earlier results. Browser tests cover empty grants, qualification/health rendering, stale/gap reasons, network recovery and mobile overflow. UI fixture is explicitly synthetic interface metadata over a mocked response; no fabricated sensor data is trained or presented as field evidence.

## Remaining gates

Customer OIDC/roles, grant revocation administration, source/extractor attestation, approved model lifecycle, actual commissioning, fleet enrollment, fresh-path load/soak/retention and prospective predictive validity remain incomplete. Current local health labels are diagnostics from observations/registry, not proof of an always-connected physical transport.
