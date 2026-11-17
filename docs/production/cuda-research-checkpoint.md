# CUDA research checkpoint — 2026-11-17

Initial nested workpiece-group experiment completed. Six model families, three candidate configurations per family, seed 17; 952 eligible observations, 60 five-cut positives. All preprocessing/tuning/calibration stayed within training folds. These are development results on an already explored dataset, not independent confirmation.

| Method | AP | Brier | Timely / 14 | Premature / 14 |
|---|---:|---:|---:|---:|
| age_only | 0.1572 | 0.0613 | 0 | 0 |
| context | 0.1507 | 0.0607 | 0 | 0 |
| logistic | 0.3274 | 0.0502 | 2 | 1 |
| current_no_age | 0.3286 | 0.0502 | 2 | 1 |
| xgboost | 0.3224 | 0.0510 | 1 | 3 |
| mlp | 0.3267 | 0.0629 | 2 | 5 |

Policy uses unchanged threshold .5, inspection interval three cuts and first drafted slot. Cutter 11 has no pre-damage opportunity and stays in the fourteen-cutter denominator. No model promoted. GPU MLP/XGBoost do not establish improvement; MLP produced more premature reviews and worse Brier than logistic. The earlier AP .355 used a different candidate grid; do not merge scores or label this a matched regression without reproducing identical grids.

## Runtime evidence

Official PyTorch 2.10.0+cu128 and XGBoost 3.4.1 both executed real work on cuda:0. The probe used measured benchmark features and 20 optimization steps. FP32/AMP maximum logit difference .0013898. Driver 592.00; CUDA runtime 12.8; RTX 4060 Laptop 8 GB. Probe results do not evaluate prediction quality.

## Commands

```powershell
pwsh -File scripts/setup-gpu.ps1
.venv-gpu/Scripts/python.exe -m pdm.gpu_benchmark --methods age_only context logistic current_no_age xgboost mlp --trials 3 --seeds 17 --output artifacts/gpu-development-initial
.venv/Scripts/python.exe -m scripts.evaluate_gpu_policy artifacts/gpu-development-initial
```

Full planned search remains 20 candidates, seeds 17/29/43, matched baselines and recipe holdouts. Completed folds/trials resume with exact runner/configuration hash; interrupted trial restarts. Raw-window/temporal candidate, acquisition gate, independent datasets and scientific novelty remain pending. Serving model unchanged.


## Platform gate from this implementation

Updated local image built and Compose services reached their configured health checks. Current source passed the expanded Python suite (see execution ledger) and seven browser scenarios. Device receipt API is implemented separately from demo ownership; evidence persists without a demo session and does not imply completed inference. Full customer identity, source qualification and inference worker remain open.

One external Bosch raw HDF5 file is now downloaded and verified at immutable commit d60581d6a3ab6015dcc5488c3d76112bb8e1bcb1. It contains vibration_data with shape 268288 x 3 and float64 values. Download size 1434336 bytes; SHA-256 2f08bdf2b57c9a61d2f2026458c2f6e4396c14bcfc4bd713dee6002f67517df0. Publisher Git blob SHA-1 also matched. This is raw-loader feasibility, not validation on another cutter-damage dataset.
