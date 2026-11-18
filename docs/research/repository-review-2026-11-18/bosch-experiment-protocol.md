# Bosch raw process-anomaly protocol, version 1

Status: integrity loader implemented; one authentic recording checked; **no anomaly model trained**. Date: 18 November 2026. Primary CNC cutter-damage model remains separate.

## Immutable acquisition and meaning

Repository commit: `d60581d6a3ab6015dcc5488c3d76112bb8e1bcb1`. Reviewed catalog SHA-256: `3dd398ff7187a8b50ca0aba46987c27f2a9d73b8fbbdb663b0163dedfd55f576`. Catalog contains1, 702 HDF5 recordings and952, 229, 265 stored bytes; it does not imply1, 702 independent failures. Data CC BY4.0; code BSD-3-Clause. Preserve attribution separately.

Target is recording-level normal/anomalous process, across three machines, process IDs and periods. No cutter damage time, tool-life endpoint, localized anomaly onset or RUL label is established by this catalog. A file-level bad label must not be assigned as precise onset ground truth to every short window.

`pdm/bosch_data.py` validates manifest bytes, path/filename lineage, local publisher Git blob SHA-1 and size before opening HDF5. Its SHA-256 receipt identifies actual sample bytes. Only bounded local floating N×3 datasets are accepted; virtual/external links, nonfinite arrays and oversized shapes fail. Chunk size is bounded. Units remain explicitly unqualified; 2kHz is publisher-declared, not independently measured sampling calibration.

One local sample:268, 288×3, 134.144 seconds at declared rate, SHA-256 `2f08bdf2b57c9a61d2f2026458c2f6e4396c14bcfc4bd713dee6002f67517df0`. The other1, 701 recordings were not acquired at this checkpoint. One normal file cannot train or validate anomaly detection.

```powershell
.venv-gpu/Scripts/python.exe -m pytest tests/test_bosch_data.py -q
.venv-gpu/Scripts/python.exe -m pdm.bosch_data --output artifacts/bosch-integrity-v1/report.json
```

Uses installed h5py/NumPy in research environment. No heavy runtime dependency added. Existing output is never overwritten; select a new receipt filename on repetition.

## Before fitting

1. Complete bounded checksum-verified acquisition from immutable publisher paths. Record every missing/rejected file. Do not eagerly load the corpus into memory.
2. Audit machine×process×period×label contingency table, durations, channel ranges, clipping and sensor documentation. Freeze process/period combinations with enough support before selecting models. Declare absent combinations.
3. Split **complete recordings before windowing**. Loader implements machine holdout and period holdout with disjoint file identities. Later periods are excluded from training in temporal tests. Separate windows of one recording must never cross partitions.
4. Freeze machine holdouts and later-period tests as separate scientific questions. Fit scalers, feature selection, anomaly thresholds and calibration on training-side data only. Retain recording/campaign grouping throughout uncertainty analysis.

## Initial frozen model scope

Compare transparent statistical/spectral features with a simple normal-only anomaly detector. Candidate features: per-axis RMS, peak/crest factor, kurtosis, spectral entropy and declared frequency-band power. Establish units and segmentation first. Report normal-only detection separately from any supervised classifier using bad labels.

Begin with no temporal neural model. After baseline qualification, permit one small temporal encoder with matched partitions, input duration, feature acquisition and resource accounting. New complexity must justify false-alarm and operational benefit rather than window-level accuracy alone.

Use recording-level PR metrics and false alarms per normal recording; only report per-hour burden when verified duration supports it. Give per-machine/process/period results, coverage and uncertainty. With three machines and70 anomalous recordings, effective independent evidence remains limited; pooled windows do not increase independent-machine count.

## Application boundary

Future UI must name process anomaly, exact data/model/units/qualification and cutoff. It cannot call the cutter-damage release or display unvalidated remaining life. Missing model/source/metadata remains unavailable. No sensor acquisition, model promotion, advisory approval or physical commissioning is implied by the integrity receipt.
