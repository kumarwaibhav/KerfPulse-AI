"""Real HTTP/SSE + worker verification in an isolated PostgreSQL schema.

Run inside API container. Authentic archived values are protocol fixtures only;
this test never writes them into the operational public schema as plant data.
"""
import copy
import json
import os
import re
import socket
import subprocess
import sys
import time
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
from urllib.request import Request,urlopen
import uuid
from pdm.store import Store
from pdm.device_ingest import DeviceIngest
from pdm.fresh_model import input_schema
from pdm.fresh_model import release
from pdm.qualification import QualificationRegistry
from datetime import datetime,timedelta,timezone


def main():
    base=Store()
    if not base.postgres:raise RuntimeError('PostgreSQL required')
    schema='verify_operational_'+uuid.uuid4().hex
    api=worker=None;temporary=None
    with base.transaction(write=True) as conn:base.execute(conn,'CREATE SCHEMA '+schema)
    try:
        url=urlsplit(base.url)
        query=dict(parse_qsl(url.query));query['options']='-csearch_path='+schema
        scoped_url=urlunsplit((url.scheme,url.netloc,url.path,urlencode(query),url.fragment))
        temporary=Store(scoped_url);temporary.initialize()
        devices=DeviceIngest(temporary);devices.initialize()
        source=devices.register_device('isolated-protocol-fixture','test-site','test-mill')
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        environment={**os.environ,'PDM_DATABASE_URL':scoped_url}
        api=subprocess.Popen([sys.executable,'-m','uvicorn','pdm.api:app','--host','127.0.0.1','--port',str(port)],env=environment,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        worker=subprocess.Popen([sys.executable,'-m','pdm.operational_worker'],env=environment,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        root='http://127.0.0.1:'+str(port)
        for _ in range(100):
            try:
                with urlopen(root+'/healthz',timeout=.2):break
            except OSError:time.sleep(.1)
        event=copy.deepcopy(input_schema()['example'])
        event.update(asset_id='test-mill',clock_basis='observed',data_origin='user-measured')
        envelope={'schema_version':1,'boot_id':'isolated-fixture','sequence':1,'event':event}
        headers={'Authorization':'Bearer '+source['token'],'Content-Type':'application/json'}
        def request(path,body=None):
            with urlopen(Request(root+path,data=json.dumps(body).encode() if body is not None else None,headers=headers),timeout=10) as response:return json.load(response)
        receipt=request('/api/v2/ingest/cuts',envelope)
        for _ in range(100):
            saved=request('/api/v2/receipts/'+receipt['id'])
            if saved['inference_status']!='not_started':break
            time.sleep(.1)
        assert saved['inference_status']=='abstained'
        assert saved['processing']['assessment']['five_cut_score'] is None
        assert request('/api/v2/ingest/cuts',envelope)['id']==receipt['id']
        batch=request('/api/v2/events');assert len(batch['events'])==1
        assert not request('/api/v2/events?after='+str(batch['cursor']))['events']
        with urlopen(Request(root+'/api/v2/events/stream',headers=headers),timeout=5) as response:
            first=response.readline().decode().strip()
            assert first=='id: '+str(batch['cursor'])
        with temporary.transaction() as conn:
            assert temporary.execute(conn,'SELECT count(*) AS n FROM operational_assessments').fetchone()['n']==1
        registry=QualificationRegistry(temporary)
        _,manifest=release()
        profile={'feature_schema_version':event['feature_schema_version'],'sensor_profile_version':event['sensor_profile_version'],
                 'extractor_version':'isolated-publisher-fixture-v1','model_digest':manifest['digest']}
        expiry=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()
        qualification=registry.record(source['device_id'],'shadow_approved',profile,'isolated-test','Protocol fixture only, no physical qualification',expiry)
        second=request('/api/v2/ingest/cuts',{**envelope,'sequence':2,'event':{**event,'event_id':'shadow-fixture'}})
        for _ in range(100):
            shadow=request('/api/v2/receipts/'+second['id'])
            if shadow['inference_status']!='not_started':break
            time.sleep(.1)
        assert shadow['processing']['assessment']['action']=='shadow_only'
        assert shadow['processing']['assessment']['qualification']['id']==qualification['id']
        registry.record(source['device_id'],'revoked',profile,'isolated-test','Fixture qualification withdrawn',expiry)
        third=request('/api/v2/ingest/cuts',{**envelope,'sequence':3,'event':{**event,'event_id':'revoked-fixture'}})
        for _ in range(100):
            revoked=request('/api/v2/receipts/'+third['id'])
            if revoked['inference_status']!='not_started':break
            time.sleep(.1)
        assert revoked['processing']['assessment']['five_cut_score'] is None
        assert request('/api/v2/receipts/'+second['id'])['processing']==shadow['processing']
        browser_token=uuid.uuid4().hex+uuid.uuid4().hex
        workspace=temporary.create_session(browser_token)
        registry.grant(workspace['id'],source['device_id'])
        with urlopen(Request(root+'/api/fresh/source-health',headers={'Cookie':'pdm_session='+browser_token}),timeout=5) as response:
            health=json.load(response)
        assert len(health['sources'])==1 and health['sources'][0]['qualification']['state']=='revoked'
        assert health['sources'][0]['processing']['assessment']['five_cut_score'] is None
        assert 'source_not_qualified' in health['sources'][0]['reason_codes']
        print(json.dumps({'database':'postgresql','isolation':'unique temporary schema, removed after test','http_ingest':'passed','worker_abstention':'passed',
                          'idempotent_assessment':'passed','cursor_catchup':'passed','sse_delivery':'passed','shadow_binding':'passed',
                          'qualification_revocation':'passed','historical_lineage':'passed','operator_source_health':'passed','qualification':'not physically commissioned'}))
    finally:
        for process in (api,worker):
            if process is not None:
                process.terminate();process.wait(timeout=15)
        if temporary:temporary.close()
        if not re.fullmatch('verify_operational_[0-9a-f]{32}',schema):raise RuntimeError('Unexpected verification schema')
        with base.transaction(write=True) as conn:base.execute(conn,'DROP SCHEMA '+schema+' CASCADE')
        base.close()


if __name__=='__main__':main()
