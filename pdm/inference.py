"""Numeric JSON inference for exported linear horizon models."""

import math


def predict(artifact, values):
    """Return probabilities for remaining cuts 1..8 and >8."""
    features = artifact["features"]
    missing = set(features) - set(values)
    if missing:
        raise ValueError(f"Missing required model features: {sorted(missing)}")
    inputs = [float(values[name]) for name in features]
    if any(not math.isfinite(value) for value in inputs):
        raise ValueError("Model inputs must be finite")
    scaled = [(value - mean) / scale for value, mean, scale in
              zip(inputs, artifact["mean"], artifact["scale"])]
    temperature = artifact.get("temperature", 1.0)
    logits = [(sum(coef * value for coef, value in zip(weights, scaled)) + bias) / temperature
              for weights, bias in zip(artifact["coef"], artifact["intercept"])]
    exponentials = [math.exp(value - max(logits)) for value in logits]
    total = sum(exponentials)
    result = [0.0] * 9
    for category, value in zip(artifact["classes"], exponentials):
        result[int(category) - 1] = value / total
    return result
