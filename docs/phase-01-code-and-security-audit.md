# Phase 1 and 2 audit before feature tests

Inspected actual source files and installed environment. Current callable features are dataset fetch/audit, whole-tool baseline training and offline policy comparison. Web API, authentication, MQTT persistence, work orders and rendered application are pending.

## Security inspection

The dataset URL is fixed HTTPS and checked against pinned SHA-256 and byte length before parsing. Training uses numeric source fields and writes JSON model artifacts without executable pickle deserialization. Identifiers and outcomes are excluded from prediction vectors. Local model artifacts contain public benchmark measurements and predictions. No account credentials are required or embedded.

[MEDIUM] `pdm/train.py` primary cutter split shares workpieces across folds. Separate dependency-disjoint validation remains pending. Baseline report explicitly records this limitation.

[MEDIUM] No deployed service or login implementation exists yet. Web permissions and browser security cannot pass until implemented and exercised.

[LOW] Dependency vulnerability audit pending. Exact training environment saved under artifacts/training-environment.lock.txt.

Tests may now exercise dataset integrity, train/test isolation and policy budget boundaries. No website feature test has been claimed.
