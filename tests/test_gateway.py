import json
from pathlib import Path

import pytest

from pdm.dataset import load
from pdm.gateway import ReplayModels
from pdm.inference import predict
from pdm.policy import PolicyState


def test_exported_nested_models_match_saved_out_of_fold_predictions():
    models = ReplayModels()
    tools = load()
    rows = json.loads(Path("artifacts/nested-workpiece/predictions.json").read_text())
    for row in rows:
        cut = tools[row["tool_id"]].cuts[row["cycle"] - 1]
        values = {**cut.context, **cut.current, **cut.vibration}
        actual = predict(models.by_tool[cut.tool_id][row["head"]], values)
        assert actual == pytest.approx(row["probabilities"], abs=1e-12)


def test_gateway_replays_every_original_ordinal_and_omits_terminal_features():
    models = ReplayModels()
    for tool in load().values():
        for policy in ("current", "periodic", "decision", "fused"):
            state = PolicyState()
            for cut in tool.cuts:
                event = models.event({"id": "test", "generation": 1, "policy": policy, "slot_interval": 3}, cut, state)
                assert event["cycle"] == cut.cycle
                if cut.status != "ok":
                    assert event["features"] == {}
                if policy != "fused":
                    assert state.released <= state.eligible // 4
