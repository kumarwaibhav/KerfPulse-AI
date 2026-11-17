# Research and validation plan

Preserve nested workpiece/recipe metrics and original first-inspection benchmark separately. The engineering release trains one current-only model with fixed C=.01, temperature=1 and equal total training weight per tool, excluding tools 2 and 4. Runtime selects this release without looking up the submitted identity. The measured example is selected from excluded tool 2 for illustration. Its outcome is not a new confirmation experiment and no new AP is claimed.

Future experiments add a no-age ablation and a justified tree baseline using component-group nested folds, and a separate Stiehl wear-threshold task with held-machine folds. Evaluate thresholds inside development folds using predeclared inspection costs and workload. Collect a prospective untouched cohort before claiming a novel improvement. Report exposure, abstention, precision/recall, calibration, timely/premature/late/missed/no-opportunity outcomes and group-level uncertainty. Causal raw windows, anomaly detection and survival analysis require separately verified data and endpoints.

Model card for haas-current-engineering-v1: target published cutter damage; outputs nine buckets (1..8 cuts plus >8); input 72 current summaries plus six context values; release digest artifacts/engineering-release/manifest.json; historical workpiece AP .355 is evaluation of the earlier nested protocol, not a score for this release. Supported use is engineering demonstration under the reference schema. Approver status is engineering demonstration only. Physical qualification, model promotion and rollback registry remain pending.

## Training and serving chain

1. Fetch pinned publisher v1 CSV and verify SHA-256 e125471f983e98ae326e2c47e15f633bb30738e285b9ad6e54b5e364d4d66dbc.
2. Retain missing ordinals as quality events; quarantine the conflicting pair. Exclude terminal measurements from predictors. Derive benchmark labels only in offline research.
3. For the demonstration release, exclude cutters 2 and 4 together because they share a linked workpiece group. Cutter 11 has no eligible preceding observation. The release fits 867 cuts from 11 effective training cutters.
4. Fit a scaler on training rows, then multiclass logistic regression with equal total weight per tool, C=.01 and max_iter=3000. Target is remaining cut-position class 1..8 or greater than 8. No exact continuous lifetime estimate exists.
5. Export standardized coefficients, class mapping, scaler, temperature, manifest and content digest. Runtime performs numeric inference without importing scikit-learn or selecting a model by uploaded identity.
6. Run serving parity, feature/target rejection, applicability, persistence and browser checks. Do not reuse these engineering tests as evidence of independent predictive generalization.

Build manifest records effective training cutters, row count, no-opportunity cutters, code digest and Python/scikit-learn versions. Floating-point library/thread differences can change the artifact's byte digest on retraining; identity is the digest, not just its friendly version string. Preserve the exact approved artifact for reproducibility.

## Research hypotheses and falsification

| Candidate contribution | Experiment | Failure criterion |
|---|---|---|
| Context-aware forecasts transfer beyond tool age | Compare age-only, context-only, current+context and no-age models with grouped nested folds | No consistent benefit or improvement lost under workpiece/recipe grouping |
| Optional sensing helps when action is feasible | Match current/fused/periodic/selective policies under the same calendar, thresholds and exposure | Timely-inspection utility does not improve or workload/cost exceeds limits |
| Abstention improves deployment safety | Evaluate compatibility failures and selective risk/coverage with independent machines | Unsupported data receive confident scores; useful coverage collapses |
| Workflow produces useful outcome data | Prospective shadow cohort with reviewed mature outcomes and intervention tracking | Missing/censored outcomes prevent reliable assessment or labels are contaminated by advice |

These are research questions, not established algorithmic novelty. Logistic regression, a dashboard, MQTT, uncertainty labels or adding two common models together are not by themselves novel contributions. A journal claim needs a scoped, falsifiable improvement and evidence against strong matched baselines.

## Evaluation protocol

Freeze all preprocessing, grouping, policies and metrics before the final cohort. Use no random cut-level train/test split: cuts from one tool and linked workpieces are dependent. Tune regularization, temperature, thresholds and acquisition policy inside development folds. Keep recipe shifts distinct from workpiece shifts. Report rare-event base rate alongside average precision; report Brier and reliability bins without interpreting one-machine calibration as plant calibration.

For event-level policy outcomes, count timely, premature, late, missed and no-opportunity lives separately; preserve the first-draft convention to avoid choosing the best warning retrospectively. Report tool/workpiece cluster uncertainty and paired policy differences. Small clusters make confidence intervals wide. Analyze censoring and interventions before computing prospective labels. No fabricated failure times or synthetic sensor evidence may enter confirmation evaluation.

## Current research conclusion

Historical current workpiece AP approximately .355 and Brier .0502 show measurable discrimination in that benchmark protocol. They do not overcome the weak 2/14 timely inspection result. The selective strategy's 1/14 result does not establish superiority. This software release adds operational traceability and new-identity inference; it does not establish a new scientific accuracy result or a plant-safe action policy.
