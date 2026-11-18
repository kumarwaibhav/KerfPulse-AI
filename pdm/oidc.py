"""Bounded OIDC authorization-code + PKCE login using signed ID tokens."""
import base64
from dataclasses import dataclass
import hashlib
import json
import os
import time
from urllib.parse import urlencode,urlparse,urlunparse
import httpx
import jwt
from fastapi import APIRouter,HTTPException,Request,Depends
from fastapi.responses import RedirectResponse

COOKIE='kerfpulse_person'
BINDING='kerfpulse_oidc_binding'


def safe_url(value,allow_loopback=False):
    url=urlparse(value)
    if url.username or url.password or url.fragment or url.query or not url.netloc:raise ValueError('Invalid configured identity URL')
    if url.scheme!='https' and not (allow_loopback and url.scheme=='http' and url.hostname in ('localhost','127.0.0.1','::1')):
        raise ValueError('OIDC requires HTTPS; explicit loopback exception only for local development')
    return value.rstrip('/')


@dataclass(frozen=True)
class Settings:
    issuer:str
    client_id:str
    public_url:str
    client_secret:str=''
    allow_loopback:bool=False
    backchannel_url:str=''

    @classmethod
    def environment(cls):
        issuer=os.getenv('PDM_OIDC_ISSUER','');client=os.getenv('PDM_OIDC_CLIENT_ID','');public=os.getenv('PDM_PUBLIC_URL','')
        if not any((issuer,client,public)):return None
        if not all((issuer,client,public)):raise ValueError('Complete OIDC configuration required')
        allow=os.getenv('PDM_OIDC_ALLOW_LOOPBACK_HTTP','false')=='true'
        if len(client)>120 or not client:raise ValueError('Invalid client identifier')
        back=os.getenv('PDM_OIDC_BACKCHANNEL_URL','')
        if back:
            parsed=urlparse(back)
            # Explicit private-network exception belongs solely to optional local Compose IdP.
            if not (allow and parsed.scheme=='http' and parsed.netloc=='identity:8080' and parsed.path in ('','/')):
                safe_url(back,allow)
            if parsed.path not in ('','/') or parsed.query or parsed.fragment or parsed.username or parsed.password:
                raise ValueError('Backchannel override must be an origin only')
        return cls(safe_url(issuer,allow),client,safe_url(public,allow),os.getenv('PDM_OIDC_CLIENT_SECRET',''),allow,back.rstrip('/'))

    @property
    def callback(self):return self.public_url+'/api/auth/callback'

    @property
    def digest(self):
        return hashlib.sha256(json.dumps([self.issuer,self.client_id,self.callback,self.client_secret,self.allow_loopback,self.backchannel_url]).encode()).hexdigest()


class Provider:
    def __init__(self,settings,transport=None):self.settings=settings;self.transport=transport

    def fetch(self,method,url,**kwargs):
        if self.settings.backchannel_url:
            incoming=urlparse(url);issuer=urlparse(self.settings.issuer);back=urlparse(self.settings.backchannel_url)
            if (incoming.scheme,incoming.netloc)!=(issuer.scheme,issuer.netloc):raise ValueError('Untrusted backchannel destination')
            url=urlunparse((back.scheme,back.netloc,incoming.path,incoming.params,incoming.query,''))
        with httpx.Client(timeout=10,follow_redirects=False,trust_env=False,transport=self.transport) as client:
            with client.stream(method,url,**kwargs) as response:
                response.raise_for_status();body=b''
                for chunk in response.iter_bytes():
                    body+=chunk
                    if len(body)>262144:raise ValueError('Identity response exceeds 256 KiB')
        result=json.loads(body)
        if not isinstance(result,dict):raise ValueError('Invalid identity response')
        return result

    def discovery(self):
        s=self.settings
        info=self.fetch('GET',s.issuer+'/.well-known/openid-configuration')
        if info.get('issuer')!=s.issuer:raise ValueError('Identity issuer mismatch')
        for key in ('authorization_endpoint','token_endpoint','jwks_uri'):
            value=safe_url(info[key],s.allow_loopback)
            if urlparse(value).netloc!=urlparse(s.issuer).netloc:raise ValueError('Cross-origin identity endpoint disabled')
        return info

    def exchange(self,code,attempt):
        s=self.settings;info=self.discovery()
        data={'grant_type':'authorization_code','code':code,'redirect_uri':s.callback,'client_id':s.client_id,'code_verifier':attempt['verifier']}
        if s.client_secret:data['client_secret']=s.client_secret
        result=self.fetch('POST',info['token_endpoint'],data=data)
        token=result.get('id_token')
        if not isinstance(token,str) or len(token)>32768:raise ValueError('Invalid ID token')
        header=jwt.get_unverified_header(token)
        if header.get('alg')!='RS256' or not isinstance(header.get('kid'),str):raise ValueError('Unsupported identity signature')
        keys=self.fetch('GET',info['jwks_uri']).get('keys',[])
        matching=[k for k in keys if k.get('kid')==header['kid'] and k.get('kty')=='RSA' and k.get('use','sig')=='sig' and k.get('alg','RS256')=='RS256']
        if len(matching)!=1:raise ValueError('Identity signing key unavailable or ambiguous')
        claims=jwt.decode(token,jwt.PyJWK(matching[0],algorithm='RS256').key,algorithms=['RS256'],audience=s.client_id,issuer=s.issuer,
                          options={'require':['iss','aud','exp','iat','sub','nonce']},leeway=30)
        if claims['nonce']!=attempt['nonce'] or not isinstance(claims['sub'],str) or not 1<=len(claims['sub'])<=255:
            raise ValueError('Identity nonce or subject mismatch')
        aud=claims['aud']
        if (isinstance(aud,list) and len(aud)>1 or 'azp' in claims) and claims.get('azp')!=s.client_id:
            raise ValueError('Identity authorized party mismatch')
        if claims['exp']<=time.time():raise ValueError('Expired identity token')
        return claims


def routes(identity,provider_factory=None):
    router=APIRouter(prefix='/api/auth')
    def settings():
        try:s=Settings.environment()
        except ValueError:raise HTTPException(503,'Identity configuration invalid') from None
        if s is None:raise HTTPException(503,'Named login is not configured')
        return s
    def provider(s):return provider_factory(s) if provider_factory else Provider(s)

    def person(request:Request):
        value=identity.session(request.cookies.get(COOKIE))
        if value is None:raise HTTPException(401,'Named login required')
        return value

    @router.get('/me')
    def me(request:Request):
        try:configured=Settings.environment() is not None
        except ValueError:raise HTTPException(503,'Identity configuration invalid') from None
        value=identity.session(request.cookies.get(COOKIE))
        return {'configured':configured,'authenticated':value is not None,'person':value}

    @router.get('/login')
    def login(request:Request):
        s=settings()
        if (request.url.scheme,request.url.netloc)!=(urlparse(s.public_url).scheme,urlparse(s.public_url).netloc):
            return RedirectResponse(s.public_url+'/api/auth/login',status_code=302)
        if not identity.allow_login(request.client.host if request.client else 'unknown'):
            raise HTTPException(429,'Login request limit reached. Retry after one minute.',headers={'Retry-After':'60'})
        try:
            info=provider(s).discovery()
            state,binding,value=identity.attempt(s.digest)
        except (ValueError,KeyError,httpx.HTTPError):raise HTTPException(503,'Identity provider unavailable or incompatible') from None
        challenge=base64.urlsafe_b64encode(hashlib.sha256(value['verifier'].encode()).digest()).decode().rstrip('=')
        response=RedirectResponse(info['authorization_endpoint']+'?'+urlencode({'client_id':s.client_id,'redirect_uri':s.callback,'response_type':'code',
            'scope':'openid profile','state':state,'nonce':value['nonce'],'code_challenge':challenge,'code_challenge_method':'S256'}),status_code=302)
        response.set_cookie(BINDING,binding,max_age=600,httponly=True,secure=urlparse(s.public_url).scheme=='https',samesite='lax',path='/api/auth')
        return response

    @router.get('/callback')
    def callback(request:Request):
        s=settings()
        try:
            if len(request.query_params.getlist('state'))!=1 or len(request.query_params.getlist('code'))!=1:raise ValueError('Ambiguous callback')
            code=request.query_params['code']
            if not 1<=len(code)<=4096:raise ValueError('Invalid authorization code')
            attempt=identity.consume(request.query_params['state'],request.cookies.get(BINDING),s.digest)
            claims=provider(s).exchange(code,attempt)
            name=claims.get('name',claims.get('preferred_username','Signed-in user'))
            if not isinstance(name,str):name='Signed-in user'
            session=identity.login(s.issuer,claims['sub'],name,claims['exp'])
        except (ValueError,KeyError,TypeError,httpx.HTTPError,jwt.PyJWTError):
            raise HTTPException(401,'Login failed or expired. Start a new login attempt.') from None
        response=RedirectResponse('/?workspace=operations',status_code=302)
        response.set_cookie(COOKIE,session,max_age=28800,httponly=True,secure=urlparse(s.public_url).scheme=='https',samesite='lax',path='/api')
        response.delete_cookie(BINDING,path='/api/auth')
        return response

    @router.post('/logout')
    def logout(request:Request,owner=Depends(person)):
        csrf=request.headers.get('x-csrf-token','')
        if not secrets_compare(csrf,owner['csrf']):raise HTTPException(403,'CSRF token required')
        identity.logout(request.cookies[COOKIE])
        from fastapi.responses import JSONResponse
        response=JSONResponse({'signed_out':True,'provider_session':'unchanged; sign out of provider separately on shared devices'})
        response.delete_cookie(COOKIE,path='/api')
        return response

    return router,person


def secrets_compare(a,b):
    import secrets
    return isinstance(a,str) and len(a)<=200 and secrets.compare_digest(a,b)
