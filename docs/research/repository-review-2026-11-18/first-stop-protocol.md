# Frozen exploratory first-stop protocol, version 1

Status: **design frozen before new fitting; experiment not run**. Date: 18 November 2026. This protocol follows a retrospective diagnosis on already inspected outer outcomes. Every resulting comparison remains exploratory until confirmation on independent data. It does not repair or overwrite historical results.

## Question and endpoint

Can optional vibration acquisition improve the first actionable inspection, compared with using current alone, under the same observed calendar, source support and acquisition cap? Whole-tool first-inspection utility is primary. Per-cut AP/Brier, acquisition count and latency are secondary. No acquisition or model-complexity reduction alone establishes maintenance utility.

Use the pinned Piecuch–Żabiński CSV (`e125471f983e98ae326e2c47e15f633bb30738e285b9ad6e54b5e364d4d66dbc`), current exclusion rules and connected-workpiece groups. Keep outer groups intact. Preserve eligible cut chronology and missing cycles. Forecast follows a completed cut and can affect only a future break every three cycle positions. A timely first break precedes recorded damage by two through five cuts.

Exact recipe support is determined using each training partition only, including inner folds. Unsupported input abstains; it cannot be silently assigned a low risk. Report unsupported lives/cuts and lives without pre-damage observations separately from model misses.

## Matched experimental contract

- Retain current/fused heads with C=.01 and temperature=1 for the first diagnostic comparison, keeping these distinct from historically tuned expanded models.
- Compare current-only, periodic, seeded random, simple risk-margin and a shallow terminal-regret acquisition gate. Full fusion is a resource reference, not a budget-matched policy.
- Optional policies use **floor(n/4)** at every prefix of supported eligible observations. No acquisition is permitted during the first three observations. Use eligible-count scheduling rather than cycle modulo for periodic acquisition; missing cuts must not alter its contract silently.
- A gate sees current probabilities, their entropy, current known context, elapsed eligible count, remaining quota and next feasible break. It cannot read optional features before deciding, future labels, future sensor values or realized damage.
- Stop the scored trajectory when its first inspection is fixed. Record intervention time separately from scheduled inspection time. Any continued monitoring is a separate analysis with a separate cost denominator.
- Illustrative terminal loss on supported tool lives with a pre-damage opportunity: `inspection_exists + 20 * not_timely + .1 * acquisitions_before_first_decision`. Units are normalized research costs, not plant economics. Report all outcome counts alongside loss so one scalar cannot hide abstention or premature alarms.

## Learning and selection

Construct gate labels from training-only, component-disjoint cross-fitted trajectories. For each admissible acquisition decision compare acquire versus decline under the same frozen continuation policy and remaining quota, using completed-trajectory first-inspection loss. Equal total training weight per tool prevents long lives dominating labels. Counterfactual labels must never use outer evaluation outcomes.

Keep the first gate shallow: 100 trees, maximum depth2, minimum leaf10, seed17. Predeclare actionable threshold grid {.05,.1,.2,.5}; risk-margin widths {.05,.1,.2}; do not expand after seeing outer results. Select thresholds/margins using equal-tool inner terminal loss, then lower acquisition spend, then predeclared numeric order as deterministic tie-break. Report infeasible inner support and class/campaign counts; do not silently substitute outer data when a fold cannot train.

Freeze every source-code dependency hash, data/labels, feature order, partitions, costs, calendar, support rule, seed and environment in a new output directory. Historical acquisition configuration omitted `policy.py`; future fingerprint must explicitly include policy, gate and decision-loss dependencies. Reusing an old directory after any mismatch must fail.

## Required event trace

Every supported or abstained observed cut records tool/cycle/group, physical cutoff, partition/model digests, recipe-support decision, current probabilities, known next break, gate score/request, quota before/after, whether optional data were accessed, selected probabilities, action and first-inspection fixation. Optional probabilities stay absent when not acquired. Record later damage only in the separate evaluation join.

Tests must demonstrate: no optional read before request; no future-label feature; group-disjoint transforms and selection; quota respected for every prefix; no acquisition after fixation; missing-cycle chronology; unsupported and no-opportunity states; reproducible artifact recovery; invalid or stale model/source input abstains. Fault injection must not rewrite earlier traces.

## Report and promotion

Report equal-tool terminal loss, timely/premature/late/no-inspection counts, support coverage, no-opportunity count, actual acquisitions before intervention, false-inspection burden, AP/Brier, calibration, throughput and p50/p95 latency. Use paired connected-workpiece uncertainty, disclose few clusters and inspected-data status. Shared caps do not imply equal actual spending.

Retain the existing serving release unless separate model/source and utility gates pass. A positive exploratory result cannot authorize plant advice or establish general superiority. Independent cohort/prospective confirmation is mandatory for the corresponding claim.

## Executed diagnostic foundation

`pdm/first_stop_audit.py` checks saved code/data/split identities, aggregate/fold consistency, source-derived support and attainable observed timely slots. It records historical totals without inventing event timing. Nonzero acquisition totals with a first inspection have unavailable before/after counts because the historical run stored no trace. New audit outputs use exclusive creation and leave earlier artifacts unchanged.

```powershell
.venv/Scripts/python.exe -m pdm.first_stop_audit --output artifacts/first-stop-audit-v1/report.json
```

This command audits the saved run. It does not train the proposed terminal gate. Use a new output filename for another audit.
