import copy
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from pdm.api import create_app
from pdm.fresh_model import assess, input_schema, InputError


def test_unknown_identity_scoring_and_qualification():
    event = input_schema()['example']
    event['tool_life_id'] = 'unseen-identity'
    result = assess(event)
    assert result['applicability'] == 'assessed'
    assert result['model_version'].startswith('haas-current-engineering-v1:')
    assert 0 <= result['five_cut_score'] <= 1
    event['sensor_profile_version'] = 'other'
    assert assess(event)['five_cut_score'] is None
    assert assess(event)['applicability'] == 'unsupported_domain'


def test_fresh_persistence_review_and_owner_boundary(tmp_path):
    app = create_app('sqlite:///' + str(tmp_path / 'fresh.db'))
    with TestClient(app) as client:
        client.get('/api/session')
        event = input_schema()['example']
        created = client.post('/api/fresh/assessments', json={'events': [event]}).json()['results'][0]['assessment']
        assert created['action'] == 'review_recommended'
        path = '/api/fresh/assessments/' + created['id']
        same = client.post('/api/fresh/assessments', json={'events': [event]}).json()['results'][0]['assessment']
        assert same['id'] == created['id']
        changed = copy.deepcopy(event)
        changed['context']['HardnessMean'] += 1
        conflict = client.post('/api/fresh/assessments', json={'events': [changed]}).json()['results'][0]
        assert conflict['errors'] and conflict['quarantine_id']
        repeated = client.post('/api/fresh/assessments', json={'events': [changed]}).json()['results'][0]
        assert repeated['quarantine_id'] == conflict['quarantine_id']
        assert len(client.get('/api/fresh/conflicts').json()) == 1
        assert client.get(path+'/export').json()['evidence'] == event
        assert client.post(path+'/review', json={'action':'approve','expected_version':1}).status_code == 200
        assert client.post(path+'/review', json={'action':'approve','expected_version':1}).status_code == 409
        assert client.post(path+'/review', json={'action':'complete','expected_version':2,'finding':'Protocol review exercise, source explicitly recorded.'}).status_code == 200
        assert client.get(path+'/export').json()['assessment']['review']['status'] == 'completed'
        client.cookies.clear()
        client.get('/api/session')
        assert client.get(path).status_code == 404
        assert client.get('/api/fresh/conflicts').json() == []


def test_evidence_quality_and_horizon_fail_closed():
    event = input_schema()['example']
    missing = copy.deepcopy(event)
    missing['features'].pop(next(iter(missing['features'])))
    assert assess(missing)['applicability'] == 'insufficient_evidence'
    stale = {**event, 'cut_completed_at': (datetime.now(timezone.utc)-timedelta(minutes=10)).isoformat()}
    assert assess(stale)['applicability'] == 'stale'
    assert assess(stale)['five_cut_score'] is None
    future = {**event, 'cut_completed_at': (datetime.now(timezone.utc)+timedelta(minutes=10)).isoformat()}
    with pytest.raises(InputError, match='Future evidence'):
        assess(future)
    for breaks in ([], [event['sequence_number']+4]):
        result = assess({**event, 'inspection_breaks': breaks})
        assert result['action'] == 'no_feasible_slot'
        assert result['actionable_score'] is None
    unqualified = assess({**event, 'data_origin': 'user-measured'})
    assert unqualified['applicability'] == 'unsupported_domain'
    assert unqualified['five_cut_score'] is None
    for key, value in [('future_damage', 1), ('rul', 5)]:
        with pytest.raises(InputError, match='Unsupported fields'):
            assess({**event, key: value})
    invalid = copy.deepcopy(event)
    invalid['features'][next(iter(invalid['features']))] = float('nan')
    with pytest.raises(InputError, match='finite numeric'):
        assess(invalid)


def test_fresh_permissions_and_input_bounds(tmp_path, monkeypatch):
    with TestClient(create_app('sqlite:///' + str(tmp_path / 'bounds.db'))) as client:
        assert client.get('/api/fresh/assessments').status_code == 401
        client.get('/api/session')
        event = input_schema()['example']
        assert client.post('/api/fresh/assessments', json={'events': []}).status_code == 422
        assert client.post('/api/fresh/assessments', json={'events': [event]}, headers={'Origin': 'https://attacker.invalid'}).status_code == 403
        assert client.post('/api/fresh/assessments', content='x'*70000, headers={'Content-Type':'application/json'}).status_code == 413
        monkeypatch.setenv('PDM_DEMO_ROLE', 'viewer')
        assert client.post('/api/fresh/assessments', json={'events': [event]}).status_code == 403
