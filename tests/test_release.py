"""Research-release split and serving parity, separate from predictive efficacy."""
import numpy as np

from pdm.dataset import load
from pdm.fresh_model import release
from pdm.inference import predict
from pdm.train import components
from pdm.validation import fit, probabilities


def test_release_split_and_training_metadata():
    tools = load()
    model, manifest = release()
    actual = {tool.id for tool in tools.values() if tool.id not in (2, 4) and any(c.status == 'ok' for c in tool.cuts)}
    assert set(manifest['training_tools']) == actual
    assert set(manifest['excluded_tools']) == {2, 4}
    assert manifest['eligible_training_rows'] == sum(c.status == 'ok' for tool in tools.values() if tool.id in actual for c in tool.cuts)
    for group in components(tools):
        assert not (set(group) & actual and set(group) & {2, 4})
    assert 11 in manifest['no_eligible_rows_tools']
    assert len(model['features']) == 78


def test_release_serving_matches_independent_sklearn_refit():
    tools = load()
    exported, manifest = release()
    rows = [(cut, tool.failure_cycle-cut.cycle) for tool in tools.values() if tool.id in manifest['training_tools']
            for cut in tool.cuts if cut.status == 'ok']
    model = fit(rows, exported['features'], manifest['parameters']['C'])
    held = [(cut, tools[2].failure_cycle-cut.cycle) for cut in tools[2].cuts if cut.status == 'ok']
    expected = probabilities(model, held, exported['features'], exported['temperature'])
    actual = np.asarray([predict(exported, {**cut.context, **cut.current}) for cut, _ in held])
    np.testing.assert_allclose(actual, expected, rtol=1e-8, atol=1e-10)
    np.testing.assert_allclose(actual.sum(axis=1), 1, atol=1e-12)
