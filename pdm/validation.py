"""Nested group validation and temperature selection using training tools only."""

import argparse
import json
import hashlib
from collections import Counter, defaultdict
from pathlib import Path
from time import perf_counter

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from pdm.dataset import SOURCE_SHA256, SOURCE_VERSION, load
from pdm.train import components, feature_names, vector


def probabilities(model, rows, names, temperature):
    x = np.asarray([vector(cut, names) for cut, _ in rows])
    logits = model.decision_function(x) / temperature
    logits -= logits.max(axis=1, keepdims=True)
    values = np.exp(logits)
    values /= values.sum(axis=1, keepdims=True)
    result = np.zeros((len(rows), 9))
    result[:, model.classes_.astype(int) - 1] = values
    return result


def fit(rows, names, regularization):
    counts = Counter(cut.tool_id for cut, _ in rows)
    weights = np.asarray([1 / counts[cut.tool_id] for cut, _ in rows])
    weights *= len(rows) / weights.sum()
    model = make_pipeline(StandardScaler(), LogisticRegression(C=regularization, max_iter=3000))
    model.fit([vector(cut, names) for cut, _ in rows], [min(remaining, 9) for _, remaining in rows],
              logisticregression__sample_weight=weights)
    return model


def equal_tool_loss(rows, predicted):
    losses = defaultdict(list)
    for (cut, remaining), probability in zip(rows, predicted):
        losses[cut.tool_id].append(-np.log(max(probability[min(remaining, 9) - 1], 1e-15)))
    return float(np.mean([np.mean(values) for values in losses.values()]))


def tune(rows, names, component_ids):
    group_ids = [component_ids[cut.tool_id] for cut, _ in rows]
    folds = list(GroupKFold(n_splits=min(3, len(set(group_ids)))).split(rows, groups=group_ids))
    candidates = []
    for regularization in (0.01, 0.1, 1.0):
        predictions = {temperature: np.zeros((len(rows), 9)) for temperature in (0.5, 1.0, 2.0)}
        for train_indices, validation_indices in folds:
            inner_train = [rows[index] for index in train_indices]
            inner_test = [rows[index] for index in validation_indices]
            model = fit(inner_train, names, regularization)
            for temperature, predicted in predictions.items():
                predicted[validation_indices] = probabilities(model, inner_test, names, temperature)
        for temperature, predicted in predictions.items():
            candidates.append({"C": regularization, "temperature": temperature,
                               "inner_tool_balanced_log_loss": equal_tool_loss(rows, predicted)})
    selected = min(candidates, key=lambda entry: entry["inner_tool_balanced_log_loss"])
    return selected, candidates


def summarize(rows):
    labels = np.asarray([row["remaining"] <= 5 for row in rows])
    scores = np.asarray([sum(row["probabilities"][:5]) for row in rows])
    bins = []
    for lower in np.arange(0, 1, 0.1):
        included = (scores >= lower) & (scores < lower + 0.1)
        if lower > 0.89:
            included |= scores == 1
        if included.any():
            bins.append({"lower": float(lower), "n": int(included.sum()),
                         "mean_risk": float(scores[included].mean()),
                         "observed_rate": float(labels[included].mean())})
    return {"n": len(rows), "positive_cuts": int(labels.sum()),
            "average_precision": float(average_precision_score(labels, scores)),
            "brier": float(brier_score_loss(labels, scores)), "reliability_bins": bins}


def run(output, protocol):
    output.mkdir(parents=True, exist_ok=True)
    tools = load()
    groups = components(tools)
    component_ids = {tool: index for index, group in enumerate(groups) for tool in group}
    rows = [(cut, tool.failure_cycle - cut.cycle) for tool in tools.values()
            for cut in tool.cuts if cut.status == "ok"]
    if protocol == "recipe":
        recipes = sorted({tool.recipe for tool in tools.values()})
        groups = [[tool.id for tool in tools.values() if tool.recipe == recipe] for recipe in recipes]
    predictions, manifests, models = [], [], {}
    started = perf_counter()
    for test_tools in groups:
        excluded_components = {component_ids[tool] for tool in test_tools}
        train = [(cut, remaining) for cut, remaining in rows
                 if component_ids[cut.tool_id] not in excluded_components]
        test = [(cut, remaining) for cut, remaining in rows if cut.tool_id in test_tools]
        training_ids = sorted({cut.tool_id for cut, _ in train})
        manifest = {"test_tools": test_tools, "training_tools": training_ids,
                    "purged_tools": sorted(set(tools) - set(test_tools) - set(training_ids)), "heads": {}}
        if not test:
            manifest["status"] = "no_pre_damage_observation"
            manifests.append(manifest)
            continue
        assert not ({component_ids[key] for key in training_ids} & excluded_components)
        for head in ("age", "current", "fused"):
            names = feature_names(train[0][0], head)
            selected, candidates = tune(train, names, component_ids)
            model = fit(train, names, selected["C"])
            key = "-".join(map(str, test_tools))
            scaler, classifier = model[0], model[-1]
            models.setdefault(key, {})[head] = {
                "features": names, "classes": classifier.classes_.tolist(),
                "mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist(),
                "coef": classifier.coef_.tolist(), "intercept": classifier.intercept_.tolist(),
                "temperature": selected["temperature"], "training_tools": training_ids,
                "test_tools": test_tools,
            }
            predicted = probabilities(model, test, names, selected["temperature"])
            raw = probabilities(model, test, names, 1.0)
            manifest["heads"][head] = {"selected": selected, "candidates": candidates}
            for (cut, remaining), probability, uncalibrated in zip(test, predicted, raw):
                predictions.append({"tool_id": cut.tool_id, "cycle": cut.cycle, "head": head,
                                    "remaining": remaining, "probabilities": probability.tolist(),
                                    "uncalibrated_probabilities": uncalibrated.tolist(),
                                    "recipe_supported": cut.recipe in {tools[key].recipe for key in training_ids}})
        manifests.append(manifest)
    metrics = {head: summarize([row for row in predictions if row["head"] == head])
               for head in ("age", "current", "fused")}
    for head, values in metrics.items():
        subset = [row for row in predictions if row["head"] == head]
        raw_rows = [{**row, "probabilities": row["uncalibrated_probabilities"]} for row in subset]
        values["uncalibrated"] = summarize(raw_rows)
        observed = { (cut.tool_id, cut.cycle): (cut, remaining) for cut, remaining in rows }
        ordered = [observed[row["tool_id"], row["cycle"]] for row in subset]
        values["tool_balanced_multiclass_loss"] = equal_tool_loss(ordered, [row["probabilities"] for row in subset])
        values["uncalibrated_tool_balanced_multiclass_loss"] = equal_tool_loss(
            ordered, [row["uncalibrated_probabilities"] for row in subset])
    model_bytes = json.dumps(models, allow_nan=False).encode("utf-8")
    (output / "models.json").write_bytes(model_bytes)
    report = {"source": SOURCE_VERSION, "source_sha256": SOURCE_SHA256,
              "protocol": protocol, "outer_folds": manifests, "metrics": metrics,
              "seconds": perf_counter() - started,
              "model_artifact_sha256": hashlib.sha256(model_bytes).hexdigest(),
              "selection": "Inner component-disjoint GroupKFold; C and temperature minimize equal-tool 9-class log loss",
              "calibration_limit": "Empirical held-out reliability only. No guaranteed coverage under domain shift."}
    (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    (output / "predictions.json").write_text(json.dumps(predictions, allow_nan=False), encoding="utf-8")
    print(json.dumps({"protocol": protocol, "seconds": report["seconds"], "metrics": metrics}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", choices=("workpiece", "recipe"), default="workpiece")
    parser.add_argument("--output", type=Path, default=Path("artifacts/nested-workpiece"))
    args = parser.parse_args()
    run(args.output, args.protocol)
