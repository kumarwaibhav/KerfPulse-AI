from datetime import datetime,timezone
import time
import pytest
from fastapi.testclient import TestClient
from pdm.api import create_app
from pdm.oidc import COOKIE,Settings,safe_url


def test_people_access_denies_demo_and_exact_scope_rechecked(tmp_path):
    app=create_app('sqlite:///'+str(tmp_path/'identity.db'))
    with TestClient(app) as client:
        client.get('/api/session')
        assert client.get('/api/operations/sources').status_code==401
        token=app.state.identity.login('https://identity.example','person-1','Engineer',time.time()+600)
        owner=app.state.identity.session(token)
        a=app.state.devices.register_device('org-1','site-1','mill-1')
        app.state.devices.register_device('org-2','site-1','mill-1')
        app.state.devices.register_device('org-1','site-2','mill-1')
        app.state.devices.register_device('org-1','site-1','mill-2')
        client.cookies.set(COOKIE,token,path='/api')
        assert client.get('/api/operations/sources').json()['sources']==[]
        app.state.identity.grant(owner['id'],'org-1','site-1','mill-1','operator','local-admin')
        sources=client.get('/api/operations/sources').json()['sources']
        assert [s['device_id'] for s in sources]==[a['device_id']]
        assert client.get('/api/operations/sources/not-granted/history').status_code==404
        assert client.post('/api/auth/logout',json={}).status_code==403
        assert client.post('/api/auth/logout',json={},headers={'X-CSRF-Token':owner['csrf']}).status_code==200
        assert client.get('/api/operations/sources').status_code==401
        client.cookies.set(COOKIE,token,path='/api')
        assert client.get('/api/operations/sources').status_code==401


def test_login_state_single_use_and_revoke(tmp_path):
    app=create_app('sqlite:///'+str(tmp_path/'attempt.db'))
    with TestClient(app):
        identity=app.state.identity
        state,binding,attempt=identity.attempt('pinned-configuration')
        with pytest.raises(ValueError):identity.consume(state,'other-browser','pinned-configuration')
        with pytest.raises(ValueError):identity.consume(state,binding,'changed-config')
        assert identity.consume(state,binding,'pinned-configuration')['nonce']==attempt['nonce']
        with pytest.raises(ValueError):identity.consume(state,binding,'pinned-configuration')
        token=identity.login('https://identity.example','subject','Name',time.time()+300)
        owner=identity.session(token)
        identity.revoke(owner['id'],'admin')
        assert identity.session(token) is None
        expired=identity.login('https://identity.example','subject','Name',time.time()-1)
        assert identity.session(expired) is None


def test_unconfigured_or_bad_identity_fails_closed(tmp_path,monkeypatch):
    for key in ('PDM_OIDC_ISSUER','PDM_OIDC_CLIENT_ID','PDM_PUBLIC_URL'):monkeypatch.delenv(key,raising=False)
    with TestClient(create_app('sqlite:///'+str(tmp_path/'config.db'))) as client:
        assert client.get('/api/auth/me').json()['configured'] is False
        assert client.get('/api/auth/login').status_code==503
        monkeypatch.setenv('PDM_OIDC_ISSUER','http://remote.invalid')
        assert client.get('/api/auth/me').status_code==503
    for url in ('http://remote.invalid','https://user:password@example.org','https://example.org/#fragment'):
        with pytest.raises(ValueError):safe_url(url,True)
