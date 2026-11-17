# KerfPulse AI product requirements

Version 1, 17 November 2026. Product owner is the project author. This specification combines the implemented benchmark replay with acceptance criteria for the software release and explicitly identified research/pilot milestones.

## Vision and mission

**Vision.** Give machining teams enough warning to inspect or replace a cutter before its damage disrupts production.

**Mission.** Connect a reproducible current/vibration model to an industrial telemetry path and an accountable inspection workflow. Every recommendation must show its measurement cutoff, model version, available evidence, production break, and resulting human decision. Deliver an inexpensive, hardware-free demonstration that a reviewer can run and audit.

The primary industrial problem is cutter damage during steel machining. The published Haas experiment supplies a real measured damage endpoint and 14 complete tool lives. An operator deciding whether to interrupt a cut needs more than a risk curve. A useful recommendation reaches the planner while a feasible break remains, with sufficient warning and a review workload the team can handle. This project makes that decision process measurable. [Dataset descriptor](https://pmc.ncbi.nlm.nih.gov/articles/PMC12006439/) · [Replacement-policy research](https://orbi.umons.ac.be/handle/20.500.12907/53600)

The commercial hypothesis is an on-premise or customer-hosted subscription for high-mix machining shops, initially sold as transparent monitoring and inspection decision support. Customer interviews must establish existing tool-change practice, scrap and interruption cost, controller access, available sensor data, and who can authorize a production pause. The prototype measures the workflow and benchmark decisions. A shadow pilot must measure actual adoption, outcomes, and support burden before a sales claim.

## Users and product journeys

| Persona | Job and information needed | Primary action |
|---|---|---|
| Operator | Monitor several machines and recognize when evidence warrants attention. Needs source state, current cut, risk trend, data quality, and inspection reason. | Open a tool run and review evidence. |
| Maintenance planner | Coordinate available production breaks, inspections, and work. Needs proposed slot, urgency, evidence, previous dispositions, and an auditable finding. | Approve, dismiss, and complete an inspection draft. |
| Reliability engineer or research reviewer | Determine whether sensing and policy improve decisions on unseen tools. Needs dataset lineage, model protocol, per-tool outcomes, budgets, and repeatable replay. | Compare policies and export run evidence. |

The showcase starts with the recorded source visibly labelled. The user chooses a cutter and a release policy, sets replay speed and inspection spacing, and starts a run. The dashboard updates after each source cut through the gateway, broker, worker, database, API, and browser. An inspection recommendation creates a draft. The planner approves it or records a dismissal. Completion records a finding. A reviewer repeats the same cutter under another policy and compares the result with the benchmark export.

## Priorities and functional requirements

P0 means required for the complete local release. P1 means the next development increment after local verification. P2 means the customer-pilot expansion described in the roadmap.

| ID | Priority | Requirement | Acceptance criteria |
|---|---|---|---|
| FR-001 | P0 | Load verified source and expose available cutters. | The loader verifies the pinned file hash and serves all 14 tool IDs with recipe and cut counts. Corrupted input fails with a readable error. |
| FR-002 | P0 | Start an isolated replay. | A planner submits tool, policy, speed, and inspection interval. The service returns a unique run, generation, state, and initial checkpoint. Invalid values produce a validation response without a run. |
| FR-003 | P0 | Transport replay through MQTT. | A gateway publishes QoS 1 messages and a worker persists accepted records. Browser readings come from persisted events. A repeated message produces one accepted cut and one quota debit. |
| FR-004 | P0 | Preserve chronology and evidence boundaries. | Original cycle numbers, gaps, and conflicts remain visible. Terminal records close the run. No terminal feature or outcome value is used in a preceding model score. |
| FR-005 | P0 | Enforce vibration release budget. | Decision-aware and periodic policies release at most `floor(n/4)` optional feature sets after `n` unique eligible cuts. Gaps, conflicts, retries and damage events do not mint quota. The always-fused reference shows its different resource use. |
| FR-006 | P0 | Expose four policy modes. | Current-only, periodic, decision-aware and always-fused modes use the same source/model family and slot rule. Each accepted reading shows risk, decision state, optional release, and model version. |
| FR-007 | P0 | Control replay. | Pause retains checkpoint. Resume continues from the next source ordinal. Restart increments generation and provides a fresh trajectory while old event identity cannot alter the new run. |
| FR-008 | P0 | Show an actionable inspection queue. | The first inspection recommendation produces at most one active draft per cutter/run generation with proposed future slot, source cut, evidence and reason. |
| FR-009 | P0 | Record work-order dispositions. | A planner can approve or dismiss a draft and complete an approved order with a finding. Illegal transitions return a readable error and preserve state. Viewer requests cannot mutate orders. |
| FR-010 | P0 | Resume browser updates. | Snapshot returns a cursor. Native SSE continues from that cursor. Reconnection catches up without duplicating displayed readings or work orders. |
| FR-011 | P0 | Export an audit record. | Export contains run configuration, persisted readings, orders, source/model versions and relevant replay outcomes. It uses the same authorized session scope as the UI. |
| FR-012 | P0 | Expose health and operating metrics. | Health distinguishes service readiness and broker/worker problems as implemented. Metrics include accepted events and relevant service counts. Logs retain run/generation/cycle identifiers without secrets. |
| FR-013 | P1 | Compare two selected runs in a reviewer view. | Equal cutter and calendar are explicit. Show current/periodic/decision tradeoffs and per-tool final outcomes. Different speed affects wall time only. |
| FR-014 | P1 | Package public showcase with quotas. | A bounded public profile caps active runs and run duration, scopes sessions, handles cold start, and removes expired demo records. Exact provider settings are verified before publishing. |
| FR-015 | P2 | Adapt an independent machine benchmark. | Versioned Stiehl adapter preserves its wear endpoint and supports held-machine folds with separate models. Publish endpoint-specific results. |
| FR-016 | P2 | Connect a customer's controller or historian. | Agree on read-only tags, units, sample windows, ownership, alert route, pilot retention, and maintenance outcomes. Run in shadow mode before operational use. |

## Nonfunctional requirements

| ID | Requirement | Release check |
|---|---|---|
| NFR-001 | Correctness and repeatability | A given source, model hash, policy, calendar, and input order yield the same decisions. Disconnection and retries leave quota and work orders consistent. |
| NFR-002 | Local performance | Target p95 publish-to-browser delivery below two seconds under 20 events/second for ten minutes. Publish measured hardware, load, event count, errors and percentile. This is an acceptance target until measured. |
| NFR-003 | Recovery | Durable checkpoint and idempotent ingestion survive worker/gateway restarts. Broker reconnect catches up and old generations cannot resume a restarted run. |
| NFR-004 | Access | Scope all run IDs to the browser session. Separate planner and viewer mutation rights. Reject cross-session run, stream, export and work-order access. Production identity mapping is a pilot integration requirement. |
| NFR-005 | Evidence quality | Display replay provenance and source cycle. Do not convert synthetic replay time to claimed source timestamps. Distinguish measured model outputs, simulated inspection outcomes, and operator-entered findings. |
| NFR-006 | Maintainability | Pin dependencies, keep model inference deterministic, use typed browser contracts, and keep broker/DB/API configuration outside code. |
| NFR-007 | Cost | All local training, inference, transport, storage, and UI use open-source packages. Local operation needs an existing computer. Hosted free services have quotas and idle behavior verified at release. |
| NFR-008 | Accessibility | Keyboard controls, meaningful status text, readable chart labels and numeric alternatives, visible focus, responsive layout, and color-independent warning meaning. |

## Success measures and evidence gates

**Software success** means the verified dataset can be acquired, a model artifact reproduced, and a complete run streamed through MQTT into the browser with inspection dispositions and export. Recovery and session-isolation checks must pass. Performance must be reported as measured. A failed external hosting or independent benchmark step remains visible in the release status.

**Research success** means the experiment answers the preregistered question with an auditable protocol and per-tool outcomes. Current recorded nested workpiece results are 2 timely events among 14 tools for current-only/periodic and 1 among 14 for decision-aware/fused. Recipe holdout gives 1 among 14 for each. The hypothesis is unsupported at those settings. Preserve that result and compare any subsequent policy revision under a new declared evaluation. AP improvements do not establish better inspection outcomes.

**Pilot success** will be defined with a customer before onboarding. Start with counts of actionable reviewed alerts, review time, accepted inspections, inspection findings, false reviews, deployment effort, and retained uptime/scrap records. Estimate money using customer-supplied inputs and a documented counterfactual. Market loss figures in consulting reports cannot substitute for these measures. [ABB survey scope](https://new.abb.com/news/detail/107660/abb-survey-reveals-unplanned-downtime-costs-125-000-per-hour)

| Risk | Detection and response |
|---|---|
| Small outcome sample and correlated cuts | Show all 14 tool outcomes, observable subset, grouped folds, and uncertainty. Add independent-machine validation before broad generalization. |
| Age/recipe shortcut | Include age-only and no-age sensor controls, hold recipes out, and purge linked workpieces. |
| Poor calibration in a shifted recipe | Surface unsupported recipe/data quality and retain empirical reliability by group. Keep operator approval. |
| Alert fatigue or premature replacement | Count first inspection timing and premature reviews. Review thresholds against actual planner cost and capacity in a pilot. |
| Free-host quotas and cold start | Keep repeatable local Compose release. Measure hosted start/recovery and bound sessions. |
| Novelty overlap | Cite active sensing and inspection/scheduling precedents. Evaluate the specific policy claim and retain negative findings. [Active sensing](https://doi.org/10.3390/s26165065) |

Initial implementation choices include a fixed threshold of 0.5, margin of 0.2, default three-cut inspection calendar, nine-class linear models, and selectable replay policies. These are documented experimental defaults. A service-grade product needs customer identity, support, backup validation, field outcome collection, and operating procedures established in the pilot.
