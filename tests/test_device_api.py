import copy
import json
from fastapi.testclient import TestClient
from pdm.api import create_app
from pdm.fresh_model import input_schema


def test_authenticated_device_http_receipts_and_scope(tmp_path):
    app = create_app('sqlite:///'+str(tmp_path/'api.db'))
    with TestClient(app) as client:
        a = app.state.devices.register_device('org','site','mill')
        b = app.state.devices.register_device('other','site','other-mill')
        event = copy.deepcopy(input_schema()['example'])
        event.update(asset_id='mill',data_origin='user-measured',clock_basis='observed')
        body = {'schema_version':1,'boot_id':'boot','sequence':1,'event':event}
        assert client.post('/api/v2/ingest/cuts',json=body).status_code == 401
        headers = {'Authorization':'Bearer '+a['token']}
        duplicate_json = json.dumps(body).replace('"schema_version": 1','"schema_version": 1, "schema_version": 1')
        assert client.post('/api/v2/ingest/cuts',content=duplicate_json,headers={**headers,'Content-Type':'application/json'}).status_code == 422
        response = client.post('/api/v2/ingest/cuts',json=body,headers=headers)
        assert response.status_code == 200
        receipt = response.json()
        assert receipt['inference_status'] == 'not_started'
        assert client.post('/api/v2/ingest/cuts',json=body,headers=headers).json()['id'] == receipt['id']
        path = '/api/v2/receipts/'+receipt['id']
        assert client.get(path,headers=headers).json()['envelope'] == body
        assert client.get(path,headers={'Authorization':'Bearer '+b['token']}).status_code == 404
        app.state.devices.revoke_device(a['device_id'])
        assert client.get(path,headers=headers).status_code == 401
