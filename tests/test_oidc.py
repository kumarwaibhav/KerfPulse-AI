"""Real signed ID tokens and HTTP-client protocol fixtures; no fake plant data."""
import base64
import hashlib
import json
import time
from urllib.parse import urlparse,parse_qs
import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from pdm.api import create_app
from pdm.oidc import Provider,COOKIE


@pytest.fixture
def oidc(tmp_path,monkeypatch):
    for key,value in {'PDM_OIDC_ISSUER':'https://id.example/realm','PDM_OIDC_CLIENT_ID':'kerfpulse','PDM_PUBLIC_URL':'http://127.0.0.1:8000','PDM_OIDC_ALLOW_LOOPBACK_HTTP':'true'}.items():monkeypatch.setenv(key,value)
    private=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    jwk=json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(private.public_key()));jwk.update(kid='test-key',use='sig',alg='RS256')
    state={'nonce':None,'challenge':None,'claims_override':{},'token_calls':0}
    def transport(request):
        if request.url.path.endswith('/.well-known/openid-configuration'):
            return httpx.Response(200,json={'issuer':'https://id.example/realm','authorization_endpoint':'https://id.example/auth','token_endpoint':'https://id.example/token','jwks_uri':'https://id.example/keys'})
        if request.url.path=='/keys':return httpx.Response(200,json={'keys':[jwk]})
        if request.url.path=='/token':
            form=parse_qs(request.content.decode());verifier=form['code_verifier'][0]
            assert base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')==state['challenge']
            assert form['redirect_uri']==['http://127.0.0.1:8000/api/auth/callback']
            state['token_calls']+=1
            claims={'iss':'https://id.example/realm','aud':'kerfpulse','sub':'subject','iat':int(time.time()),'exp':int(time.time())+600,'nonce':state['nonce'],'name':'Test Engineer',**state['claims_override']}
            token=jwt.encode(claims,private,algorithm='RS256',headers={'kid':'test-key'})
            return httpx.Response(200,json={'id_token':token,'access_token':'must-not-be-stored'})
        raise AssertionError('Unexpected identity URL')
    app=create_app('sqlite:///'+str(tmp_path/'oidc.db'),oidc_provider_factory=lambda s:Provider(s,httpx.MockTransport(transport)))
    with TestClient(app,base_url='http://127.0.0.1:8000',follow_redirects=False) as client:
        yield client,app,state


def start(client,state):
    response=client.get('/api/auth/login');assert response.status_code==302
    params=parse_qs(urlparse(response.headers['location']).query)
    state.update(nonce=params['nonce'][0],challenge=params['code_challenge'][0])
    assert params['code_challenge_method']==['S256']
    return params['state'][0]


def test_oidc_pkce_login_nonce_session_and_replay(oidc):
    client,app,state=oidc
    challenge=start(client,state)
    callback='/api/auth/callback?code=single-use-code&state='+challenge
    response=client.get(callback)
    assert response.status_code==302 and response.headers['location']=='/?workspace=operations'
    assert 'HttpOnly' in response.headers['set-cookie']
    me=client.get('/api/auth/me').json()
    assert me['authenticated'] and me['person']['display_name']=='Test Engineer'
    assert me['person']['grants']==[]
    assert client.get('/api/operations/sources').json()['sources']==[]
    assert client.get(callback).status_code==401
    assert state['token_calls']==1
    with app.state.store.transaction() as conn:
        all_rows=app.state.store.execute(conn,'SELECT * FROM people_sessions').fetchall()
        assert 'must-not-be-stored' not in str([dict(r) for r in all_rows])


@pytest.mark.parametrize('bad',[{'nonce':'wrong'},{'aud':'other-app'},{'iss':'https://attacker.invalid'},{'exp':1},{'azp':'other-app'},{'iat':9999999999}])
def test_bad_signed_claims_rejected(oidc,bad):
    client,_,state=oidc
    challenge=start(client,state);state['claims_override']=bad
    assert client.get('/api/auth/callback?code=code&state='+challenge).status_code==401
    assert not client.get('/api/auth/me').json()['authenticated']


def test_cross_browser_binding_and_duplicate_callback_keys(oidc):
    client,_,state=oidc
    challenge=start(client,state)
    original=client.cookies.get('kerfpulse_oidc_binding')
    client.cookies.clear()
    assert client.get('/api/auth/callback?code=code&state='+challenge).status_code==401
    assert state['token_calls']==0
    client.cookies.set('kerfpulse_oidc_binding',original,path='/api/auth')
    assert client.get('/api/auth/callback?code=code&state='+challenge+'&state='+challenge).status_code==401
