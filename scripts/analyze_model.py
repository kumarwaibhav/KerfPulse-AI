"""Audit retained held-out predictions without retraining or selecting a threshold."""

from collections import Counter
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, confusion_matrix, roc_auc_score

from pdm.dataset import load
from pdm.gateway import ReplayModels
from pdm.policy import PolicyState, decide, outcome
from pdm.train import components


def metrics(rows):
    truth = np.asarray([row["remaining"] <= 5 for row in rows])
    score = np.asarray([sum(row["probabilities"][:5]) for row in rows])
    return {"average_precision": average_precision_score(truth, score), "roc_auc": roc_auc_score(truth, score),
            "brier": brier_score_loss(truth, score), "mean_probability": float(score.mean()),
            "confusion_at_0_5": confusion_matrix(truth, score >= .5).tolist()}


def main():
    tools = load()
    report = {"dataset": {"eligible": 952, "damage_within_5": 60, "independent_machine_count": 1},
              "protocols": {}, "model_artifact": "nested-workpiece"}
    for protocol in ("workpiece", "recipe"):
        rows = json.loads(Path(f"artifacts/nested-{protocol}/predictions.json").read_text())
        heads = {name: [row for row in rows if row["head"] == name] for name in ("age", "current", "fused")}
        outcomes = {}
        for name, items in heads.items():
            outcomes[name] = metrics(items)
        # Paired bootstrap respects every connected group of cutters sharing a workpiece.
        groups = components(tools)
        current, fused = heads["current"], heads["fused"]
        truth = np.array([row["remaining"] <= 5 for row in current])
        current_score = np.array([sum(row["probabilities"][:5]) for row in current])
        fused_by_cut = {(row["tool_id"], row["cycle"]): sum(row["probabilities"][:5]) for row in fused}
        fused_score = np.array([fused_by_cut[row["tool_id"], row["cycle"]] for row in current])
        indexes = [np.array([i for i, row in enumerate(current) if row["tool_id"] in group], dtype=int) for group in groups]
        rng = np.random.default_rng(172026)
        delta = []
        for _ in range(3000):
            idx = np.concatenate([indexes[i] for i in rng.integers(len(groups), size=len(groups))])
            if not truth[idx].any() or truth[idx].all():
                continue
            delta.append([average_precision_score(truth[idx], current_score[idx]) - average_precision_score(truth[idx], fused_score[idx]),
                          brier_score_loss(truth[idx], current_score[idx]) - brier_score_loss(truth[idx], fused_score[idx])])
        # This sensitivity sweep is descriptive. The deployed operating point remains fixed.
        indexed = {(row["tool_id"], row["cycle"], row["head"]): row["probabilities"] for row in rows}
        sweep = {}
        for threshold in (.2, .35, .5, .65, .8):
            sweep[str(threshold)] = {}
            for policy in ("current", "periodic", "decision", "fused"):
                counts = Counter()
                releases = 0
                for tool in tools.values():
                    state = PolicyState()
                    for cut in tool.cuts:
                        if cut.status == "ok":
                            decide(state, cut.cycle, indexed[tool.id, cut.cycle, "current"],
                                   indexed[tool.id, cut.cycle, "fused"], policy, threshold=threshold)
                    counts[outcome(tool.failure_cycle, state.first_slot)] += 1
                    releases += state.released
                sweep[str(threshold)][policy] = {**counts, "vibration_releases": releases}
        report["protocols"][protocol] = {"heads": outcomes, "threshold_sensitivity": sweep,
                                         "bootstrap": {"resamples": len(delta), "difference": "current minus fused",
                                                       "AP_95_interval": np.quantile(np.asarray(delta)[:, 0], [.025, .975]).tolist(),
                                                       "Brier_95_interval": np.quantile(np.asarray(delta)[:, 1], [.025, .975]).tolist()}}
    runtime = ReplayModels()
    payload = {}
    for policy in ("current", "periodic", "decision", "fused"):
        bytes_sent, vibration_releases = 0, 0
        for tool in tools.values():
            state = PolicyState()
            for cut in tool.cuts:
                event = runtime.event({"id": "audit", "generation": 1, "policy": policy, "slot_interval": 3}, cut, state)
                bytes_sent += len(json.dumps(event, allow_nan=False, separators=(",", ":")).encode())
                vibration_releases += event["vibration_released"]
        payload[policy] = {"serialized_json_bytes": bytes_sent, "vibration_releases": vibration_releases}
    report["gateway_payload"] = payload
    Path("artifacts/model-performance-analysis.json").write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({"protocols": {key: {"heads": result["heads"], "bootstrap": result["bootstrap"]}
                                     for key, result in report["protocols"].items()}, "payload": payload}, indent=2))


if __name__ == "__main__":
    main()
