import pytest

from pdm.research_runtime import admission_reasons, atomic_json


def test_resource_headroom_and_temperature():
    snapshot = dict(ram_available=3*2**30, commit_available=5*2**30, gpu_free=2*2**30, temperature=60, thermal_limit=80)
    assert admission_reasons(snapshot) == []
    for key, value, reason in [('ram_available', 1, 'ram'), ('commit_available', 1, 'commit'),
                               ('gpu_free', 1, 'vram'), ('temperature', 81, 'temperature')]:
        assert reason in admission_reasons({**snapshot, key: value})


def test_atomic_json_rejects_nonfinite_without_destroying_checkpoint(tmp_path):
    path = tmp_path/'checkpoint.json'
    atomic_json(path, {'valid': True})
    with pytest.raises(ValueError):
        atomic_json(path, {'score': float('nan')})
    assert path.read_text() == '{\n  "valid": true\n}'
