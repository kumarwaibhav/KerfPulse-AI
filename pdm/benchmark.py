"""Compare inspection policies using untouched out-of-fold predictions."""

import json
import argparse
import hashlib
import random
from collections import Counter
from pathlib import Path

from pdm.dataset import load
from pdm.policy import PolicyState, decide, outcome


def run(directory=Path("artifacts")):
    rows = json.loads((directory / "predictions.json").read_text())
    scores = {(row["tool_id"], row["cycle"], row["head"]): row["probabilities"] for row in rows}
    results = []
    for tool in load().values():
        for policy in ("current", "periodic", "decision", "fused"):
            state = PolicyState()
            for cut in tool.cuts:
                if cut.status != "ok":
                    continue
                decide(state, cut.cycle, scores[tool.id, cut.cycle, "current"],
                       scores[tool.id, cut.cycle, "fused"], policy)
                if policy != "fused" and state.released > state.eligible // 4:
                    raise AssertionError("Optional vibration prefix quota violated")
            results.append({"tool_id": tool.id, "policy": policy, "first_slot": state.first_slot,
                            "damage_cycle": tool.failure_cycle, "eligible_cuts": state.eligible,
                            "releases": state.released, "outcome": outcome(tool.failure_cycle, state.first_slot)})
    summary = {policy: dict(Counter(row["outcome"] for row in results if row["policy"] == policy))
               for policy in ("current", "periodic", "decision", "fused")}
    report = {"threshold": 0.5, "slot_interval": 3, "margin": 0.2, "all_tools": 14,
              "observable_tools": 13, "prefix_violations": 0, "summary": summary, "results": results,
              "interpretation": "Scheduled inspection scenarios on recorded trajectories. Prevented damage is unobserved."}
    report["prediction_sha256"] = hashlib.sha256((directory / "predictions.json").read_bytes()).hexdigest()
    # Resample complete tool lives so correlated cuts are never independent replicates.
    paired = {policy: {row["tool_id"]: int(row["outcome"] == "timely") for row in results
                       if row["policy"] == policy} for policy in summary}
    generator = random.Random(20261117)
    tools = sorted(paired["current"])
    differences = []
    for _ in range(5000):
        sampled = generator.choices(tools, k=len(tools))
        differences.append(sum(paired["decision"][key] - paired["periodic"][key] for key in sampled) / len(tools))
    differences.sort()
    report["paired_tool_bootstrap"] = {
        "comparison": "decision minus periodic timely proportion", "replicates": 5000,
        "seed": 20261117, "unit": "complete cutter life", "tools": len(tools),
        "difference": sum(paired["decision"][key] - paired["periodic"][key] for key in tools) / len(tools),
        "percentile_95_interval": [differences[124], differences[4874]],
        "limitation": "Fourteen tools on one machine provide limited precision and external validity."
    }
    (directory / "policy-benchmark.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts"))
    run(parser.parse_args().artifacts)
