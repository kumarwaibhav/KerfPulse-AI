from test_oidc import oidc,start


def test_login_throttled_and_uppercase_https_cookie_secure(oidc,monkeypatch):
    client,_,state=oidc
    monkeypatch.setenv('PDM_PUBLIC_URL','HTTPS://example.org')
    response=client.get('https://example.org/api/auth/login')
    assert response.status_code==302 and 'Secure' in response.headers['set-cookie']
    for _ in range(19):assert client.get('https://example.org/api/auth/login').status_code==302
    assert client.get('https://example.org/api/auth/login').status_code==429
