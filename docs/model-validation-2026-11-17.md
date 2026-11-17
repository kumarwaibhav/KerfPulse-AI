# Model validation checkpoint — 17 November 2026

KerfPulse AI continued with model validation before web implementation.

## Protocol

Outer workpiece-component holdout and outer recipe holdout both exclude all linked workpieces from training. Inner three-fold component-disjoint validation selects C from 0.01, 0.1 and 1, and temperature from 0.5, 1 and 2. Selection minimizes nine-class log loss averaged equally over tools. Scalers fit within each training fold. Classes represent 1 through 8 further cuts and more than 8. Outer labels never select parameters.

## Results

| Protocol | Inputs | Average precision | Brier score |
|---|---|---:|---:|
| Workpiece | Age and recipe | 0.217641 | 0.057790 |
| Workpiece | Current | 0.355090 | 0.050182 |
| Workpiece | Fused | 0.304930 | 0.058912 |
| Recipe | Age and recipe | 0.184008 | 0.058558 |
| Recipe | Current | 0.335462 | 0.051544 |
| Recipe | Fused | 0.291713 | 0.059393 |

All rows summarize 952 measured eligible cuts, 60 five-cut positives. AP and Brier are pooled cut statistics. Only 13 tools have pre-damage observations. Independent dataset and event-level uncertainty remain pending. Current models selected temperature 1, so no calibration gain is claimed for current. Workpiece fused tool-balanced multiclass loss improved from 0.852294 to 0.844458 after temperature selection. Recipe temperatures remained 1.

## Audit and fixes

Independent reviewer checked outer and inner workpiece separation, recipe separation, probability normalization and source keys. [MEDIUM] repeated cycle calls could mint quota, fixed by rejecting non-increasing cycle ordinals before mutation. [MEDIUM] floating inspection intervals could mutate state before failing, fixed by strict integer validation. Probability, threshold and policy validation precede state updates. JSON inference reproduces fitted pipeline probabilities within absolute tolerance 1e-12.

13 regression tests passed. Model files, raw and tempered probabilities, tuning candidates, split manifests and SHA-256 model hashes saved in artifacts/nested-workpiece and artifacts/nested-recipe. Original baseline and its policy benchmark remain separate. Nested models have not yet been evaluated through inspection-policy benchmark. No claim of improved inspection outcomes follows from improved ranking alone.

## Reproduction

```powershell
.venv/Scripts/python.exe -m pdm.validation --output artifacts/nested-workpiece
.venv/Scripts/python.exe -m pdm.validation --protocol recipe --output artifacts/nested-recipe
.venv/Scripts/python.exe -m pytest -q
```

Next model work is matched-artifact inspection replay and tool-level uncertainty, then independent-machine evaluation and service integration. CPU remains sufficient for these linear experiments. GPU training has not been run. No deployed app or complete website audit exists yet.
