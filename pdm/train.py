"""Reproduce whole-cutter-held-out damage-horizon baselines on measured data."""

import argparse
import hashlib
import json
import platform
from pathlib import Path
from time import perf_counter

import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from pdm.dataset import NUMERIC_CONTEXT, SOURCE_SHA256, SOURCE_VERSION, audit, load


def feature_names(cut, head):
    context = list(NUMERIC_CONTEXT)
    if head == "age":
        return context
    names = context + sorted(cut.current)
    return names + sorted(cut.vibration) if head == "fused" else names


def vector(cut, names):
    values = {**cut.context, **cut.current, **cut.vibration}
    return [values[name] for name in names]


def components(tools):
    """Tool groups linked by a shared physical workpiece stay together."""
    result = []
    remaining = set(tools)
    while remaining:
        group = {remaining.pop()}
        changed = True
        while changed:
            workpieces = set().union(*(tools[key].workpieces for key in group))
            linked = {key for key in remaining if workpieces & tools[key].workpieces}
            changed = bool(linked)
            group.update(linked)
            remaining.difference_update(linked)
        result.append(sorted(group))
    return sorted(result)


def fit_predict(train, test, names):
    pipeline = make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=2000))
    x = np.asarray([vector(cut, names) for cut, _ in train])
    y = np.asarray([min(remaining, 9) for _, remaining in train])
    weights = np.asarray([1 / sum(c.tool_id == cut.tool_id for c, _ in train) for cut, _ in train])
    weights *= len(weights) / weights.sum()
    pipeline.fit(x, y, logisticregression__sample_weight=weights)
    probabilities = np.zeros((len(test), 9))
    start = perf_counter()
    predicted = pipeline.predict_proba(np.asarray([vector(cut, names) for cut, _ in test]))
    elapsed = perf_counter() - start
    model = pipeline[-1]
    for column, category in enumerate(model.classes_):
        probabilities[:, int(category) - 1] = predicted[:, column]
    scaler = pipeline[0]
    artifact = {"features": names, "classes": model.classes_.tolist(), "mean": scaler.mean_.tolist(),
                "scale": scaler.scale_.tolist(), "coef": model.coef_.tolist(), "intercept": model.intercept_.tolist()}
    return probabilities, artifact, elapsed


def run(output: Path, split="cutter"):
    output.mkdir(parents=True, exist_ok=True)
    tools = load()
    observations = [(cut, tool.failure_cycle - cut.cycle) for tool in tools.values()
                    for cut in tool.cuts if cut.status == "ok"]
    predictions = []
    models = {}
    latency = []
    split_manifest = []
    groups = components(tools) if split == "workpiece" else [[key] for key in tools]
    for group in groups:
        held_out = "-".join(map(str, group))
        train = [(cut, remaining) for cut, remaining in observations if cut.tool_id not in group]
        test = [(cut, remaining) for cut, remaining in observations if cut.tool_id in group]
        split_manifest.append({"test_tools": group, "training_tools": sorted(set(tools) - set(group))})
        models[str(held_out)] = {}
        for head in ("age", "current", "fused"):
            names = feature_names(train[0][0], head)
            # Fit the artifact even for the single-cut damage tool with no test observation.
            scored = test or train[:1]
            probabilities, artifact, elapsed = fit_predict(train, scored, names)
            models[str(held_out)][head] = artifact
            if test:
                latency.append(elapsed / len(test) * 1000)
            for (cut, remaining), probability in zip(test, probabilities):
                predictions.append({"tool_id": cut.tool_id, "cycle": cut.cycle,
                                    "remaining": remaining, "head": head, "probabilities": probability.tolist(),
                                    "risk": float(probability[:5].sum())})
    metrics = {}
    for head in ("age", "current", "fused"):
        rows = [row for row in predictions if row["head"] == head]
        labels = [int(row["remaining"] <= 5) for row in rows]
        scores = [row["risk"] for row in rows]
        metrics[head] = {"average_precision": average_precision_score(labels, scores),
                         "brier": brier_score_loss(labels, scores),
                         "log_loss": log_loss(labels, scores, labels=[0, 1]),
                         "observations": len(rows), "positive_observations": sum(labels)}
    report = {"brand": "KerfPulse AI", "source_version": SOURCE_VERSION, "sha256": SOURCE_SHA256,
              "audit": audit(), "protocol": f"leave-{split}-group-out, fixed C=0.1, equal total training weight per cutter",
              "threshold": 0.5, "threshold_selection": "fixed before scoring; no held-out selection",
              "seed": 0, "python": platform.python_version(), "sklearn": sklearn.__version__,
              "metrics": metrics, "batch_amortized_inference_ms_p95": float(np.percentile(latency, 95)),
              "shared_workpiece_components": components(tools),
              "pending": ["nested grouped hyperparameter selection", "workpiece-disjoint sensitivity",
                          "leave-recipe-out sensitivity", "independent machine benchmark", "policy comparison"],
              "splits": split_manifest}
    for name, content in (("baseline-report.json", report), ("predictions.json", predictions), ("models.json", models)):
        (output / name).write_text(json.dumps(content, indent=2, allow_nan=False), encoding="utf-8")
    report["model_artifact_sha256"] = hashlib.sha256((output / "models.json").read_bytes()).hexdigest()
    (output / "baseline-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"metrics": metrics, "batch_amortized_inference_ms_p95": report["batch_amortized_inference_ms_p95"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts"))
    parser.add_argument("--split", choices=("cutter", "workpiece"), default="cutter")
    args = parser.parse_args()
    run(args.output, args.split)
