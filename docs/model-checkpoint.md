# KerfPulse AI model checkpoint

Brand and tagline confirmed. UI specification saved in kerfpulse-design-specification.md.

Data audit passed pinned SHA-256 and size. 14 tools, 952 eligible pre-damage cuts, 21 missing ordinals, 2 conflicting rows quarantined. Terminal measurements remain outside prediction vectors.

Whole-cutter baseline average precision: age/recipe 0.2809, current 0.3102, fused 0.2498. Five-cut positive prevalence 60/952 (6.30%). These are pooled cut metrics, not event accuracy.

Shared-workpiece-disjoint sensitivity: age/recipe 0.2695, current 0.2846, fused 0.2405. Model C fixed at 0.1 before evaluation. Nested tuning, recipe holdout, calibrated uncertainty and independent dataset evaluation remain pending.

Corrected policy comparison at fixed threshold 0.5 and inspection interval 3: current 3/14 timely, periodic 3/14, decision 3/14, fused 2/14. Decision also had 1 late inspection. No demonstrated advantage for proposed policy. Prefix quota violation count 0. Scheduled inspections are scenario outcomes, not observed prevention.

Independent code review found and corrected [HIGH] forecast/inspection horizon mismatch. Bins now distinguish 1..8 further cuts and >8. Regression tests pin late versus timely counterexamples. [MEDIUM] shared-workpiece dependency addressed with additional component holdout. [LOW] latency surrogate excluded for first-cut failure. Batch-amortized timing must not be described as per-request latency.

CPU baselines used scikit-learn. RTX 4060 Laptop GPU detected with 8188 MiB, system RAM approximately 16 GB. No GPU training performed yet.

Overall status: model baseline checkpoint only. No production readiness score assigned. API, MQTT worker, complete UI, user-role enforcement, dependency vulnerability audit, browser end-to-end testing, deployment and five remaining specification documents are pending. Environment and source audit saved under artifacts. Raw benchmark signals have not been synthesized.

Reproduce from workspace root:

```powershell
.venv/Scripts/python.exe -m pdm.dataset audit
.venv/Scripts/python.exe -m pdm.train
.venv/Scripts/python.exe -m pdm.train --split workpiece --output artifacts/workpiece
.venv/Scripts/python.exe -m pdm.benchmark
.venv/Scripts/python.exe -m pytest -q
```
