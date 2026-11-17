# Requirement-to-evidence matrix

| Requirement | Implemented evidence | Remaining gate |
|---|---|---|
| KP-001 | Released model scores new tool identity; tests/test_fresh.py | Independent field validity |
| KP-002 | Bounded JSON/CSV importer, field errors and per-row results | Broader upload fuzzing; browser JSON/CSV, mixed rows and failure recovery passed |
| KP-003 | Physical source shown unconfigured | Asset/device registration and commissioning |
| KP-004 | Event clock/source/digest persisted and exported | Signed device provenance |
| KP-005 | Missing, stale and unsupported states | Qualified real mapping |
| KP-006 | Explicit target/horizon/calibration limits | Prospective calibration |
| KP-007 | User-provided absolute cut-break list | Actual plant schedule integration |
| KP-008 | Versioned approve/dismiss/complete history | Assignment/expiry/reassessment |
| KP-009 | Finding/source text and actor/time | Structured uncertainty/censoring protocol |
| KP-010 | Idempotent assessment; conflicting evidence durably quarantined and visible | Ordered device identity and durable receipts |
| KP-011 | Existing replay broker/SSE recovery tested | Fresh device spool/offline recovery |
| KP-012 | Demo session and planner checks | Customer OIDC/site/asset/device roles |
| KP-013 | Input/model/policy digest and review history | Full extractor/config/actor identity lifecycle |
| KP-014 | Released model distinct from fold bank | Approval/shadow/rollback registry |
| KP-015 | Seven browser scenarios passed; desktop/mobile workflow checks | Complete accessibility acceptance |
| KP-016 | Compose/setup, bounded PostgreSQL pool and real checkout/rollback test | Full application/OIDC recovery, encrypted off-site backup, incidents and fresh-device load qualification |
| KP-017 | Legacy benchmark preserved | New prospective confirmation cohort |

Tests are historical until run against the current source. Current-stage results are added to continuation-checkpoint.md with commands and actual outcomes. Hardware absence blocks physical commissioning and field claims, not the local demo.

Current source passed 36 Python tests and seven browser scenarios. Pool verification exercised 10 sequential and 40 concurrent transactions with rollback recovery and at most eight checked-out backends. The 600-second local replay regression passed: 46,439 events, 77.398/s, SSE p95 386.826 ms, no harness-reported failures. This does not cover fresh device ingestion or physical sources. No independent multi-agent sign-off is claimed; worker sessions exhausted their available usage, so the primary agent executed the current verification.

Local PostgreSQL restore verified 606 evidence digests, zero orphan assessments, and restored 54,055 replay readings; this is a database rehearsal, not full application/identity recovery.
