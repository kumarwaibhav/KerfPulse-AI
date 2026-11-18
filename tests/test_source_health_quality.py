"""Source health must describe the latest assessment as well as transport."""
import copy
from datetime import datetime, timedelta, timezone

import pytest

from pdm.device_ingest import DeviceIngest
from pdm.fresh_model import input_schema, release
from pdm.operational_processing import OperationalProcessing
from pdm.qualification import QualificationRegistry
from pdm.store import Store


@pytest.fixture
def source_health(tmp_path):
    store = Store('sqlite:///' + str(tmp_path / 'source-health.db'))
    store.initialize()
    devices = DeviceIngest(store)
    devices.initialize()
    registry = QualificationRegistry(store)
    owner = store.create_session('source-health-regression')['id']
    device = devices.register_device('org', 'site', 'mill')
    registry.grant(owner, device['device_id'])
    event = copy.deepcopy(input_schema()['example'])
    event.update(asset_id='mill', data_origin='user-measured', clock_basis='observed')
    _, manifest = release()
    profile = {
        'feature_schema_version': event['feature_schema_version'],
        'sensor_profile_version': event['sensor_profile_version'],
        'extractor_version': 'fixture-extractor-v1',
        'model_digest': manifest['digest'],
    }
    expiry = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    qualification = registry.record(
        device['device_id'], 'shadow_approved', profile, 'test-engineer',
        'Protocol fixture only; no physical commissioning.', expiry,
    )
    try:
        yield store, devices, registry, owner, device, event, profile, expiry, qualification
    finally:
        store.close()


def submit(source_health, event, *, sequence=1, process=True):
    store, devices, registry, owner, device, *_ = source_health
    receipt = devices.ingest(device['token'], {
        'schema_version': 1, 'boot_id': 'fixture-boot',
        'sequence': sequence, 'event': event,
    })
    processed = OperationalProcessing(store).process_one() if process else None
    return receipt, processed, registry.health(owner)[0]


def test_qualified_receipt_waiting_for_processing_requires_attention(source_health):
    event = source_health[5]
    _, processed, health = submit(source_health, event, process=False)
    assert processed is None
    assert health['qualification']['eligible'] is True
    assert health['processing'] is None
    assert health['health'] == 'attention_required'
    assert 'processing_pending' in health['reason_codes']


def test_missing_current_channels_cannot_report_healthy_shadow(source_health):
    event = source_health[5]
    assert len(event['features']) > 1
    event['features'].pop(next(iter(event['features'])))
    _, processed, health = submit(source_health, event)
    assert processed['state'] == 'abstained'
    assert processed['assessment']['applicability'] == 'insufficient_evidence'
    assert health['qualification']['eligible'] is True
    assert health['health'] == 'attention_required'
    assert 'missing_current_channels' in health['reason_codes']


def test_rejected_model_contract_cannot_report_healthy_shadow(source_health):
    event = source_health[5]
    event['features']['unknown_sensor_channel'] = 1.0
    _, processed, health = submit(source_health, event)
    assert processed['state'] == 'rejected'
    assert processed['reason'] == 'invalid_model_contract'
    assert health['qualification']['eligible'] is True
    assert health['health'] == 'attention_required'
    assert 'invalid_model_contract' in health['reason_codes']


def test_new_qualification_does_not_make_historical_assessment_current(source_health):
    _, devices, registry, owner, device, event, profile, expiry, first = source_health
    receipt, processed, before = submit(source_health, event)
    assert processed['state'] == 'assessed'
    assert before['processing']['assessment']['qualification']['id'] == first['id']
    second = registry.record(
        device['device_id'], 'shadow_approved', profile, 'test-engineer',
        'New qualification revision; historical assessment must retain its binding.', expiry,
    )
    after = registry.health(owner)[0]
    assert after['qualification']['id'] == second['id']
    assert after['processing']['assessment']['qualification']['id'] == first['id']
    assert devices.get_receipt(device['token'], receipt['id'])['processing'] == processed
    assert after['health'] == 'attention_required'
    assert 'assessment_qualification_changed' in after['reason_codes']
