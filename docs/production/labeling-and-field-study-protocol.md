# Labeling and field-study protocol

Record asset, tool life, cut exposure, inspection method, reviewer/time, damage definition, finding confidence, reason for replacement, whether advice was visible, intervention and follow-up. Preserve revisions and label maturity. A completed review is an operator record and does not become a training label automatically.

Preventive replacement censors untreated failure time. Negative five-cut labels require sufficient valid follow-up. Otherwise mark pending, unknown or censored. Separate shadow, advice-visible and post-intervention cohorts. Uninspected tools cannot be assumed healthy. Establish machine-specific event rate, censoring, cluster structure and decision cost before estimating pilot duration. Site accountable owner approves safety and workload criteria before prospective outcomes are reviewed.

## Proposed structured outcome record

| Field group | Required evidence |
|---|---|
| Identity | Organization/site/asset, tool installation ID, cutter geometry, workpiece batch and recipe |
| Exposure | Completed-cut ordinals, interruption/gap history and observation clock |
| Inspection | Method, magnification/instrument, inspector, observed_at, measurement units and attachments |
| Finding | Damage definition, wear measurement if available, uncertainty and reviewer adjudication |
| Intervention | Replaced/adjusted/continued, reason, time, advice-visible flag and downstream production effect |
| Label maturity | Pending/observed/censored/unknown, available follow-up and revision history |

Current application records finding/source as bounded text and review actor/time. The table is the next structured schema, not a claim that all fields are collected today. Completing a work item never silently retrains the model.

## Shadow-to-advisory study

Begin with a registered protocol and read-only shadow assessments hidden from operators' maintenance decisions. Keep existing safety and maintenance practice. Collect consecutive eligible lives, including quiet periods and failures without warning; do not select only successful examples. Have reviewers adjudicate outcomes before viewing scores where practical. Record missingness and source qualification failures.

Choose cohort size using observed event rate, clustering and expected uncertainty, not an arbitrary promise of a two-week pilot. After shadow validity, a separately authorized advice-visible study measures inspection burden, unexpected tool changes, scrap, downtime and documented decisions. A preventive replacement changes the counterfactual failure time; it cannot be counted as a proven avoided failure without an appropriate design. Report adverse outcomes and abstentions.

Release decisions require a reliability engineer, site maintenance owner and OT/IT owner. Hardware access and qualified mappings are external dependencies. Contracts, software testing and a preregistration template can be completed without them.
