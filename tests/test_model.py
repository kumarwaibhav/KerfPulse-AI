import numpy as np
import pytest

from pdm.dataset import load
from pdm.inference import predict
from pdm.train import components, feature_names
from pdm.validation import fit, probabilities


def test_exported_inference_matches_training_pipeline():
    tools = load()
    rows = [(cut, tool.failure_cycle - cut.cycle) for tool in tools.values()
            for cut in tool.cuts if cut.status == "ok"]
    train = [(cut, remaining) for cut, remaining in rows if cut.tool_id not in (2, 4)]
    test = [(cut, remaining) for cut, remaining in rows if cut.tool_id == 2][:5]
    names = feature_names(train[0][0], "current")
    model = fit(train, names, 0.1)
    artifact = {"features": names, "classes": model.classes_.tolist(),
                "mean": model[0].mean_.tolist(), "scale": model[0].scale_.tolist(),
                "coef": model[-1].coef_.tolist(), "intercept": model[-1].intercept_.tolist(),
                "temperature": 2.0}
    exported = [predict(artifact, {**cut.context, **cut.current}) for cut, _ in test]
    np.testing.assert_allclose(exported, probabilities(model, test, names, 2.0), atol=1e-12)
    with pytest.raises(ValueError, match="Missing required"):
        predict(artifact, {})


def test_connected_workpieces_never_cross_components():
    tools = load()
    groups = components(tools)
    for group in groups:
        held = set().union(*(tools[key].workpieces for key in group))
        training = set().union(*(tool.workpieces for key, tool in tools.items() if key not in group))
        assert held.isdisjoint(training)
