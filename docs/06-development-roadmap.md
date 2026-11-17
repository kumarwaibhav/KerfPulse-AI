# Development and research roadmap

The project produces a reproducible software-only CNC telemetry application and a measured inspection-policy study. Keep software correctness, statistical conclusions, and industrial benefit tied to their own evidence. This roadmap starts from the source, model and application work already present on 17 November 2026. The six-to-eight-week schedule below is a planning estimate for one developer, with customer access determining the field-pilot schedule.

## Milestones and release evidence

| Stage | Work and dependencies | Deliverable and exit gate |
|---|---|---|
| **1. Source and baseline** | Fetch the pinned CC BY fixture, audit parsing/chronology, quarantine conflicts, preserve gaps and exclude terminal labels. Fit age, current, and fused baseline heads. | Source hash/audit and reproducible artifacts. Complete in the current source/model checkpoint. Verify on a fresh environment. |
| **2. Validation** | Hold out workpiece/tool components, purge shared workpieces for recipe holdout, tune preprocessing/model/temperature only within training groups. Replay policy from matched artifacts. | Split manifests, tuning candidates, JSON model hash, per-tool outcomes, empirical reliability and negative findings. Nested model/policy reports are present. Tool-level uncertainty and independent-machine replication remain research work. |
| **3. Complete local application** | Run broker, database, API, worker and gateway. Build UI and connect real persisted SSE, replay controls, inspection disposition and export. | Repeatable start command, browser walkthrough, API/transport logs, and successful complete run. Verify integration before marking release. |
| **4. Reliability and audit** | Test duplicate packets, gaps, conflict, stale generations, interrupted processes, role/session boundary, browser reconnect and concurrent run limits. Measure actual event delivery latency. | Release evidence that records test count, environment, pass/fail, failures fixed and residual issues. Performance target is p95 under two seconds at 20 events/second for ten minutes. |
| **5. Independent benchmark** | Build the Stiehl v3 adapter and validate wear labels, units and machine identity. Train separate endpoint-specific models and evaluate a held machine. | Versioned adapter, machine fold manifests, results and sensitivity. Decide whether the policy advantage generalizes. Source data has a different wear endpoint. [Stiehl v3](https://data.mendeley.com/datasets/zpxs87bjt8/3) |
| **6. Public showcase** | Choose a currently available free hosting profile, configure private broker/process supervision, PostgreSQL persistence, session caps and HTTPS. Test restart, cold start and an expired session. | Working URL only after observed success. Retain canonical local Compose installation. Render and Neon candidates require current quota verification. [Render](https://render.com/docs/free) · [Neon](https://github.com/neondatabase/website/blob/main/content/faqs/free-plan-limits-and-quotas.md) |
| **7. Paper package** | Freeze the final protocol, collect statistical intervals, add the independent endpoint, explain prior-art overlap and negative results, and preserve reproducibility files. | Manuscript draft, plots, per-tool tables, source/model manifests, commands and reviewer reproduction guide. Verify journal scope, current indexing/category and fee-free publication route before submission. |
| **8. Customer shadow pilot** | Confirm buyer and operator workflow, read-only controller access, tag/feature mapping, feasible breaks, alert route, retention, identity and backup needs. | Pilot agreement and acceptance measures, operator findings and reviewed data additions. Benefits measured against an agreed baseline determine commercialization. |

## Dependency-ordered weekly plan

**Week 1 — data and baseline.** Reproduce the verified 968-row source, 952 eligible pre-damage records, 21 missing source positions, one conflicting source ordinal and fourteen damage outcomes. Record the feature exclusion list and shared-workpiece components. Train basic heads and run leakage/inference tests. Keep all tool outcomes visible.

**Week 2 — honest model and policy validation.** Reproduce nested workpiece and recipe reports. Compare first inspection outcomes on matching prediction artifacts. Fixed settings currently give two timely workpiece inspections for current/periodic and one for decision/fused. Keep this unsupported hypothesis result. Add an event-level age-only control, no-age sensitivity, simple risk-margin comparator, per-tool paired intervals and the upload-budget sensitivity. Any subsequent model or policy change is tagged exploratory unless evaluated under a newly frozen test.

**Weeks 3–4 — connected application.** Complete same-origin UI and API. Verify session ownership, typed run inputs, chronological replay, transactional MQTT ingestion, event outbox and SSE recovery. Show optional releases, publication bytes and source quality. Link the first inspection draft to approval/completion and user-entered findings. Run the documented cutter-2 and cutter-11 walkthroughs.

**Week 5 — reproducible release.** Build the Docker image from pinned dependencies and artifacts. Verify PostgreSQL and SQLite test profiles, broker reconnection, process restart, paused in-flight records and generation reset. Benchmark actual end-to-end latency with known hardware. Produce a release checklist with observed evidence. Add hosted deployment only after local success and current provider checks.

**Weeks 6–8 — independent validation and publication.** Process the Stiehl dataset offline, build a distinct wear model, hold out machines and retain the endpoint difference. Review false inspections with a manufacturing-domain reader. Compile plots, confidence intervals, sensitivity studies, failure cases and methods. Target *Reliability Engineering & System Safety* if the final contribution is the validated inspection decision method. A broader IoT systems paper requires measured transport/resource evidence, while a signal-processing paper requires a substantive sensing-method advance. [Journal scope](https://shop.elsevier.com/journals/reliability-engineering-and-system-safety/0951-8320)

## Research design and improvement decisions

1. **Freeze a primary comparison.** Timely first scheduled inspection on all 14 cutters is primary. Also show 13 tools with observable pre-damage opportunity and raw outcomes. Periodic and decision-aware policies share models, source cuts, calendar and prefix cap. Candidate revisions that improve AP alone do not pass the decision gate.
2. **Measure the sensing contribution.** Compare age plus recipe against current and fused heads. Test no-age sensors and recipe holdout. Current nested AP exceeds fused AP in existing reports, making additional vibration a hypothesis to test. The app must retain this empirical result.
3. **Separate uncertainty types.** Class probabilities express learned outcome estimates. Temperature is selected on grouped training predictions. Reliability bins show empirical calibration. Small tool counts and shifted recipes limit confidence in population results. Bootstrap by tool or connected component and retain per-group counts.
4. **Keep costs reproducible.** Expose inspection cost, unused-tool penalty, scrap and interruption values as scenario inputs with provenance. Change them over a stated range. Report a decision curve and input sensitivity. Actual savings need an intervention study with maintenance records.
5. **Keep budget semantics precise.** The cap concerns optional vibration summaries sent by the virtual edge. Log actual current/vibration/metadata payload sizes. Raw sensor duty-cycle, memory, compute and energy are distinct measurements requiring waveform processing and hardware or an explicit simulator.

## Build and verification instructions

```powershell
pwsh -File scripts/setup.ps1
.venv/Scripts/python.exe -m pdm.validation --protocol recipe --output artifacts/nested-recipe
.venv/Scripts/python.exe -m pdm.benchmark --artifacts artifacts/nested-recipe
.venv/Scripts/python.exe -m pytest -q
npm.cmd --prefix web run typecheck
npm.cmd --prefix web run build
docker compose up --build -d
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/healthz
```

Save the exact source revision and command output with release results. Then complete a browser run, an inspection disposition, an export and restart/reconnect checks. Inspect database counts to confirm idempotency. Exercise a second browser session against the first session's run ID and verify denial. A healthy API alone is insufficient to verify the entire telemetry path.

## PRD acceptance mapping and handoff

The product requirements define P0 local release, P1 public/reviewer expansion and P2 pilot adapters. The functional specification defines run and order states. The architecture document defines actual APIs and deployment configuration. Use these together at review. File delivery order is source audit, dataset/training, PRD, architecture, functional specification and this roadmap. README is the executable entry point.

Before handing the software to a customer, add authenticated customer identity, per-asset authorization, a verified live input adapter, operating runbook, backup restore evidence, model/data retention process and support owner. Alert recommendations remain subject to authorized human inspection decisions. Review findings before admitting them as training labels. Automatic controller writes, automated shutdown and purchase execution would require distinct field validation and explicit operational authorization.

The source validation and local code can be reproduced without paid AI services. The previous research used primary-source checks and Codex reviewers. Gemini, Octopus runner and a multi-provider council were not executed in that review because their documented dependencies were unavailable or paid. No publication, business result, free-host uptime guarantee or physical edge measurement follows from a successful local web demonstration.
