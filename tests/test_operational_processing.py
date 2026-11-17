import copy
import pytest
from pdm.store import Store
from pdm.device_ingest import DeviceIngest
from pdm.operational_processing import OperationalProcessing
from pdm.fresh_model import input_schema


def test_persisted_event_reaches_abstention_once_and_semantic_retry(tmp_path):
    store=Store('sqlite:///'+str(tmp_path/'operations.db'))
    devices=DeviceIngest(store); devices.initialize()
    processor=OperationalProcessing(store); processor.initialize()
    device=devices.register_device('org','site','mill')
    event=copy.deepcopy(input_schema()['example'])
    event.update(asset_id='mill',data_origin='user-measured',clock_basis='observed')
    envelope={'schema_version':1,'boot_id':'boot','sequence':1,'event':event}
    receipt=devices.ingest(device['token'],envelope)
    result=processor.process_one()
    assert result['receipt_id']==receipt['id']
    assert result['state']=='abstained'
    assert result['assessment']['applicability']=='unsupported_domain'
    assert result['assessment']['five_cut_score'] is None
    assert processor.process_one() is None
    devices.ingest(device['token'],{**envelope,'sequence':2})
    repeated=processor.process_one()
    assert repeated['state']=='duplicate'
    assert repeated['assessment_id']==result['assessment_id']
    changed=copy.deepcopy(event); changed['context']['HardnessMean']+=1
    devices.ingest(device['token'],{**envelope,'sequence':3,'event':changed})
    assert processor.process_one()['state']=='quarantined'
    with store.transaction() as conn:
        assert store.execute(conn,'SELECT count(*) AS n FROM operational_assessments').fetchone()['n']==1
        assert store.execute(conn,'SELECT count(*) AS n FROM operational_outbox').fetchone()['n']==3


def test_outbox_failure_rolls_back_assessment_and_retries(tmp_path,monkeypatch):
    store=Store('sqlite:///'+str(tmp_path/'rollback.db'))
    devices=DeviceIngest(store);devices.initialize()
    processor=OperationalProcessing(store)
    device=devices.register_device('org','site','mill')
    event=copy.deepcopy(input_schema()['example'])
    event.update(asset_id='mill',data_origin='user-measured',clock_basis='observed')
    receipt=devices.ingest(device['token'],{'schema_version':1,'boot_id':'boot','sequence':1,'event':event})
    execute=store.execute
    def fail_outbox(conn,sql,params=()):
        if sql.startswith('INSERT INTO operational_outbox'): raise RuntimeError('Injected database interruption')
        return execute(conn,sql,params)
    monkeypatch.setattr(store,'execute',fail_outbox)
    with pytest.raises(RuntimeError):processor.process_one()
    with store.transaction() as conn:
        assert execute(conn,'SELECT count(*) AS n FROM operational_assessments').fetchone()['n']==0
    monkeypatch.setattr(store,'execute',execute)
    processor.process_one()
    assert devices.get_receipt(device['token'],receipt['id'])['inference_status']=='abstained'
    events=devices.events(device['token'])
    assert len(events['events'])==1
    assert devices.events(device['token'],events['cursor'])['events']==[]
    other=devices.register_device('other-org','other-site','other-mill')
    assert devices.events(other['token'])['events']==[]
