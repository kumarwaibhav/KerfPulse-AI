import copy
from datetime import datetime,timedelta,timezone
import pytest
from pdm.store import Store
from pdm.device_ingest import DeviceIngest
from pdm.qualification import QualificationRegistry
from pdm.operational_processing import OperationalProcessing
from pdm.fresh_model import input_schema,release
from fastapi.testclient import TestClient
from pdm.api import create_app


def test_qualification_revisions_shadow_only_and_historical_lineage(tmp_path):
    store=Store('sqlite:///'+str(tmp_path/'q.db'));devices=DeviceIngest(store);devices.initialize()
    registry=QualificationRegistry(store);registry.initialize()
    source=devices.register_device('org','site','mill')
    event=copy.deepcopy(input_schema()['example']);event.update(asset_id='mill',data_origin='user-measured',clock_basis='observed')
    processor=OperationalProcessing(store)
    def submit(sequence):
        e={**event,'event_id':'event-'+str(sequence)}
        devices.ingest(source['token'],{'schema_version':1,'boot_id':'boot','sequence':sequence,'event':e})
        return processor.process_one()
    first=submit(1)
    assert first['assessment']['five_cut_score'] is None
    _,manifest=release()
    profile={'feature_schema_version':event['feature_schema_version'],'sensor_profile_version':event['sensor_profile_version'],
             'extractor_version':'publisher-summary-v1','model_digest':manifest['digest']}
    valid_until=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat()
    with pytest.raises(ValueError,match='advisory'):
        registry.record(source['device_id'],'advisory_approved',profile,'engineer','fixture-only extraction evidence',valid_until)
    q=registry.record(source['device_id'],'shadow_approved',profile,'engineer','protocol fixture only, not physical commissioning',valid_until)
    second=submit(2)
    assert second['assessment']['five_cut_score'] is not None
    assert second['assessment']['action']=='shadow_only'
    assert second['assessment']['qualification']['id']==q['id']
    registry.record(source['device_id'],'revoked',profile,'engineer','mapping withdrawn',valid_until)
    third=submit(3)
    assert third['assessment']['five_cut_score'] is None
    assert devices.get_receipt(source['token'],second['receipt_id'])['processing']==second
    assert first['assessment']['qualification']['state']=='unqualified'


def test_expired_mismatched_and_unassigned_sources_fail_closed(tmp_path):
    app=create_app('sqlite:///'+str(tmp_path/'access.db'))
    with TestClient(app) as client:
        client.get('/api/session')
        registry=QualificationRegistry(app.state.store)
        health=client.get('/api/fresh/source-health').json()
        assert health['sources']==[]
        source=app.state.devices.register_device('org','site','mill')
        registry.grant(health['workspace_id'],source['device_id'])
        assert client.get('/api/fresh/source-health').json()['sources'][0]['reason_codes']==['source_not_qualified','no_observations']
        event=copy.deepcopy(input_schema()['example']);event.update(asset_id='mill',data_origin='user-measured',clock_basis='observed')
        _,manifest=release()
        profile={'feature_schema_version':event['feature_schema_version'],'sensor_profile_version':event['sensor_profile_version'],
                 'extractor_version':'fixture-v1','model_digest':manifest['digest']}
        registry.record(source['device_id'],'shadow_approved',profile,'engineer','fixture evidence, not machine qualification',
                        (datetime.now(timezone.utc)+timedelta(days=1)).isoformat())
        with app.state.store.transaction() as conn:
            device=app.state.store.execute(conn,'SELECT * FROM ingest_devices WHERE id=?',(source['device_id'],)).fetchone()
            wrong=registry.resolve(conn,device,{**event,'sensor_profile_version':'unknown'})
            assert not wrong['eligible'] and wrong['reason']=='profile_mismatch'
        # Simulate expiry at read time without editing any historical registry rows.
        import pdm.qualification as module
        real_datetime=module.datetime
        class Later(real_datetime):
            @classmethod
            def now(cls,tz=None):return real_datetime.now(tz)+timedelta(days=2)
        from unittest.mock import patch
        with patch.object(module,'datetime',Later):
            with app.state.store.transaction() as conn:
                assert registry.resolve(conn,device,event)['reason']=='qualification_expired'
        changed_manifest={**manifest,'digest':'0'*64}
        with patch.object(module,'release',lambda:({},changed_manifest)):
            with app.state.store.transaction() as conn:
                blocked=registry.resolve(conn,device,event)
                assert blocked['reason']=='model_digest_changed' and not blocked['eligible']
        client.cookies.clear();client.get('/api/session')
        assert client.get('/api/fresh/source-health').json()['sources']==[]
        # No mutation route exists for a demo planner to approve a source.
        assert client.post('/api/fresh/qualification',json={}).status_code in (404,405)
