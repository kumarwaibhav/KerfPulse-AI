"""Strict completed-cut contracts and released-model inference for new identities."""
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
import math
import os
from pathlib import Path
import uuid

from pdm.dataset import NUMERIC_CONTEXT, RECIPE_FIELDS, SOURCE_SHA256, load
from pdm.inference import predict


class InputError(ValueError):
    def __init__(self, field, message):
        self.field = field
        super().__init__(message)


@lru_cache(maxsize=1)
def release():
    path = Path(os.getenv("PDM_RELEASE_DIR", "artifacts/engineering-release"))
    content = (path / "model.json").read_bytes()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    if hashlib.sha256(content).hexdigest() != manifest["digest"] or manifest["source_sha256"] != SOURCE_SHA256:
        raise ValueError("Release integrity verification failed")
    return json.loads(content), manifest


def assess(event, *, qualification=None):
    if not isinstance(event, dict):
        raise InputError("event", "Expected a feature event object")
    allowed = {"event_id", "asset_id", "tool_life_id", "sequence_number", "cut_completed_at", "source_mode",
               "feature_schema_version", "sensor_profile_version", "context", "features", "inspection_breaks", "clock_basis", "data_origin"}
    if set(event) - allowed:
        raise InputError("event", "Unsupported fields: " + ", ".join(sorted(set(event) - allowed)))
    for key in allowed - {"context", "features", "inspection_breaks"}:
        if key not in event:
            raise InputError(key, "Required field")
    for key in ("event_id", "asset_id", "tool_life_id"):
        if not isinstance(event[key], str) or not 1 <= len(event[key]) <= 100 or any(ord(char) < 32 for char in event[key]):
            raise InputError(key, "Use a nonempty identifier up to 100 characters")
    cycle = event["sequence_number"]
    if type(cycle) is not int or not 1 <= cycle <= 100000:
        raise InputError("sequence_number", "Use a positive integer cut ordinal")
    if event["source_mode"] not in ("uploaded", "protocol_fixture"):
        raise InputError("source_mode", "Only uploaded or protocol_fixture events are enabled")
    if event["clock_basis"] not in ("demonstration", "observed") or event["data_origin"] not in ("haas-benchmark-example", "user-measured"):
        raise InputError("data_origin", "Declare supported origin and clock basis")
    try:
        cutoff = datetime.fromisoformat(event["cut_completed_at"].replace("Z", "+00:00"))
        if cutoff.tzinfo is None:
            raise ValueError()
    except (ValueError, TypeError, AttributeError) as error:
        raise InputError("cut_completed_at", "Use an ISO timestamp with timezone") from error
    now = datetime.now(timezone.utc)
    age = (now - cutoff).total_seconds()
    if age < -60:
        raise InputError("cut_completed_at", "Future evidence exceeds permitted clock skew")
    context, features = event.get("context"), event.get("features")
    if not isinstance(context, dict) or not isinstance(features, dict):
        raise InputError("features", "Context and features must be objects")
    if set(context) != set(NUMERIC_CONTEXT):
        raise InputError("context", "Required context keys: " + ", ".join(NUMERIC_CONTEXT))
    if context["NumberOfCycle"] != cycle:
        raise InputError("context.NumberOfCycle", "Must match sequence_number")
    for key, value in {**context, **features}.items():
        if type(value) not in (int, float) or not math.isfinite(value) or abs(value) > 1e12:
            raise InputError(key, "Expected a finite numeric measurement within transport limits")
    breaks = event.get("inspection_breaks", [])
    if not isinstance(breaks, list) or len(breaks) > 100 or any(type(s) is not int or s <= cycle for s in breaks):
        raise InputError("inspection_breaks", "Provide at most 100 future cut ordinals")
    result = {"event_id": event["event_id"], "asset_id": event["asset_id"], "tool_life_id": event["tool_life_id"],
              "sequence_number": cycle, "source_mode": event["source_mode"], "clock_basis": event["clock_basis"],
              "data_origin": event["data_origin"], "cutoff": cutoff.isoformat(), "arrived_at": now.isoformat(),
              "evidence_age_seconds": max(0, age), "feature_schema_version": event["feature_schema_version"],
              "policy_version": "human-review-cut-break-v1", "model_version": None, "five_cut_score": None,
              "actionable_score": None, "inspection_slot": None, "action": "monitor", "reason_codes": [],
              "applicability": "assessed", "target": "published cutter damage after completed cut",
              "horizon": "next five cuts; slot-relative window requires offsets within 1..8",
              "calibration_status": "benchmark estimate; plant calibration pending",
              "evidence_digest": hashlib.sha256(json.dumps(event, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()}
    try:
        model, manifest = release()
    except (OSError, ValueError, KeyError):
        result.update(applicability="model_unavailable", reason_codes=["release_unavailable"])
        return result
    result["model_version"] = manifest["release"] + ":" + manifest["digest"][:16]
    expected = set(model["features"]) - set(NUMERIC_CONTEXT)
    if set(features) - expected:
        raise InputError("features", "Unknown sensor features or prohibited outcome fields")
    if expected - set(features):
        result.update(applicability="insufficient_evidence", reason_codes=["missing_current_channels"])
        return result
    recipe = [context[key] for key in RECIPE_FIELDS]
    qualified_shadow = (qualification is not None and qualification.get('eligible') is True and
                        qualification.get('state')=='shadow_approved' and qualification.get('profile',{}).get('model_digest')==manifest['digest'])
    if (event["feature_schema_version"] != manifest["feature_schema_version"] or
            event["sensor_profile_version"] != manifest["sensor_profile_version"] or
            recipe not in manifest["supported_recipes"] or event["data_origin"] == "user-measured" and not qualified_shadow):
        result.update(applicability="unsupported_domain", reason_codes=["sensor_or_domain_qualification_pending"])
        return result
    if age > 300:
        result.update(applicability="stale", reason_codes=["evidence_older_than_300_seconds"])
        return result
    probability = predict(model, {**context, **features})
    result["five_cut_score"] = sum(probability[:5])
    result["probabilities"] = probability
    slot = min(breaks) if breaks else None
    if slot is None or slot - cycle + 5 > 8:
        result.update(action="no_feasible_slot", reason_codes=["no_supported_future_break"])
        return result
    result["inspection_slot"] = slot
    result["actionable_score"] = sum(probability[slot - cycle + 1:slot - cycle + 5])
    result["action"] = "review_recommended" if result["actionable_score"] >= .5 else "monitor"
    if qualified_shadow:
        result["action"] = "shadow_only"
        result["reason_codes"] = ["shadow_evaluation_only_no_operational_recommendation"]
        return result
    result["reason_codes"] = ["engineering_demonstration", "monitor_is_not_safety_clearance"]
    return result


def input_schema():
    model, manifest = release()
    tool = load()[2]
    candidates = []
    for cut in tool.cuts:
        if cut.status == "ok":
            candidates.append((sum(predict(model, {**cut.context, **cut.current})[2:6]), cut))
    cut = max(candidates, key=lambda item: item[0])[1]
    example = {"event_id": str(uuid.uuid4()), "asset_id": "engineering-demo-haas", "tool_life_id": "new-tool-life-" + uuid.uuid4().hex[:8],
               "sequence_number": cut.cycle, "cut_completed_at": datetime.now(timezone.utc).isoformat(), "source_mode": "uploaded",
               "feature_schema_version": manifest["feature_schema_version"], "sensor_profile_version": manifest["sensor_profile_version"],
               "context": cut.context, "features": cut.current, "inspection_breaks": [cut.cycle + 1],
               "clock_basis": "demonstration", "data_origin": "haas-benchmark-example"}
    unsupported = {**example, "event_id": str(uuid.uuid4()), "sensor_profile_version": "unqualified-controller-profile"}
    return {"feature_schema_version": manifest["feature_schema_version"], "sensor_profile_version": manifest["sensor_profile_version"], "context_fields": list(NUMERIC_CONTEXT),
            "feature_fields": sorted(set(model["features"]) - set(NUMERIC_CONTEXT)), "example": example,
            "examples": {"supported": example, "unsupported": unsupported}, "max_batch_rows": 30,
            "live_connection": {"status": "unconfigured", "label": "Physical commissioning pending"},
            "example_provenance": {"source": "Figshare v1 measured tool 2 cut", "cut": cut.cycle, "excluded_from_training": True,
                                   "selection": "High-score illustration selected from development data", "clock": "Demonstration timestamp substituted explicitly"}}
