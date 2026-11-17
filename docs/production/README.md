# KerfPulse engineering showcase: document index

These documents distinguish implemented and verified software from planned plant capabilities. Start with the checkpoint and claims register. The full KP-001..017 scope is not complete in production.

| Document | Purpose |
|---|---|
| [Current checkpoint](continuation-checkpoint.md) | Actual code, commands, results and next critical path |
| [State and gaps](current-state-and-gap-analysis.md) | Audited legacy baseline and severity-ranked gaps |
| [PRD v2](prd-v2.md) | Personas, scope, requirements and acceptance |
| [Architecture](system-architecture.md) | Current and proposed boundaries, flows and state transitions |
| [Sensor contract](sensor-and-feature-contract.md) | Measurement semantics, clock, compatibility and commissioning |
| [API contracts](api-and-event-contracts.md) | Admission, errors, persisted assessments, quarantine and review |
| [Research plan](research-and-validation-plan.md) | Training, model card, hypotheses, evaluation and claim boundaries |
| [Field labeling](labeling-and-field-study-protocol.md) | Mature outcomes, uncertainty, censoring and pilot design |
| [Security](security-and-threat-model.md) | Current controls and remaining threats |
| [Operations](deployment-and-operations.md) | Setup, pooling, monitoring, backup and rollback |
| [Roadmap](implementation-roadmap.md) | Dependency-ordered engineering and field gates |
| [Acceptance matrix](acceptance-and-evidence-matrix.md) | Requirement-to-evidence mapping |
| [Claims](claims-and-limitations.md) | Defensible pitch and explicit limits |
| [Demo guide](hackathon-demo-guide.md) | Engineer/investor demonstration and questions |

The fresh release is a transparent baseline, not a demonstrated novel algorithm. A working software demonstration is a separate milestone from independent-machine predictive validity and plant commissioning.

[Current-stage audit](audit-current-stage.md) includes feature inventory and exact source locations for remaining findings. The evidence/ directory contains aggregate load, dependency, pool and restore receipts plus the release manifest and desktop screenshot; private record payloads/backups are excluded.

Latest implementation: [CUDA research checkpoint](cuda-research-checkpoint.md), [execution ledger](execution-ledger.md), and [device intake contract](device-ingest-stage.md). These supersede earlier statements that authenticated HTTP intake is entirely absent; source qualification and operational inference remain incomplete.

Next pathway: [roadmap ahead](roadmap-ahead.md). Current processing and research work: [pipeline-stage checkpoint](pipeline-stage-checkpoint.md).
