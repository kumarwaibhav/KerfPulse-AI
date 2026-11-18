"""Adversarial checks for the named-session and exact-scope boundaries."""
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from pdm.api import create_app
from pdm.oidc import COOKIE, Provider, Settings


def test_disabling_person_invalidates_existing_named_cookie(tmp_path):
    app = create_app('sqlite:///' + str(tmp_path / 'disabled-person.db'))
    with TestClient(app) as client:
        identity = app.state.identity
        token = identity.login('https://identity.example', 'employee', 'Engineer', time.time() + 600)
        owner = identity.session(token)
        device = app.state.devices.register_device('org', 'site', 'mill')
        identity.grant(owner['id'], 'org', 'site', 'mill', 'operator', 'local-admin')
        client.cookies.set(COOKIE, token, path='/api')
        assert client.get('/api/operations/sources').json()['sources'][0]['device_id'] == device['device_id']
        with app.state.store.transaction(write=True) as conn:
            app.state.store.execute(conn, 'UPDATE people SET disabled=1 WHERE id=?', (owner['id'],))
        assert identity.session(token) is None
        assert client.get('/api/operations/sources').status_code == 401
        assert client.get('/api/operations/sources/' + device['device_id'] + '/history').status_code == 401


def test_removed_grant_cannot_be_reused_from_existing_named_session(tmp_path):
    app = create_app('sqlite:///' + str(tmp_path / 'removed-grant.db'))
    with TestClient(app) as client:
        identity = app.state.identity
        token = identity.login('https://identity.example', 'employee', 'Engineer', time.time() + 600)
        owner = identity.session(token)
        granted = app.state.devices.register_device('org', 'site', 'mill')
        unrelated = app.state.devices.register_device('other-org', 'site', 'mill')
        identity.grant(owner['id'], 'org', 'site', 'mill', 'operator', 'local-admin')
        client.cookies.set(COOKIE, token, path='/api')
        assert [s['device_id'] for s in client.get('/api/operations/sources').json()['sources']] == [granted['device_id']]
        assert client.get('/api/operations/sources/' + unrelated['device_id'] + '/history').status_code == 404
        with app.state.store.transaction(write=True) as conn:
            app.state.store.execute(conn, 'DELETE FROM people_grants WHERE person_id=?', (owner['id'],))
        # Session remains valid, but its earlier grant snapshot confers no access.
        assert identity.session(token) is not None
        assert client.get('/api/operations/sources').json()['sources'] == []
        assert client.get('/api/operations/sources/' + granted['device_id'] + '/history').status_code == 404


@pytest.mark.parametrize('endpoint', ['authorization_endpoint', 'token_endpoint', 'jwks_uri'])
def test_provider_rejects_cross_origin_discovery_endpoints(endpoint):
    issuer = 'https://identity.example'
    discovery = {
        'issuer': issuer,
        'authorization_endpoint': issuer + '/authorize',
        'token_endpoint': issuer + '/token',
        'jwks_uri': issuer + '/keys',
    }
    discovery[endpoint] = 'https://other.example/collect'
    requests = []

    def respond(request):
        requests.append(str(request.url))
        return httpx.Response(200, json=discovery)

    provider = Provider(Settings(issuer, 'client', 'https://application.example'), transport=httpx.MockTransport(respond))
    with pytest.raises(ValueError, match='Cross-origin identity endpoint disabled'):
        provider.discovery()
    assert requests == [issuer + '/.well-known/openid-configuration']
