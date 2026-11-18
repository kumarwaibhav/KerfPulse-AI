"""Prepare private local IdP credentials and provision a named evaluation user.

No credentials are printed. No sources or grants are automatically created.
"""
import argparse
import json
from pathlib import Path
import secrets
import time
import httpx


def prepare():
    root=Path('artifacts/private-identity');root.mkdir(parents=True,exist_ok=True)
    path=root/'local.env'
    if not path.exists():
        password=secrets.token_urlsafe(32)
        with path.open('x',encoding='utf-8') as file:file.write('KC_ADMIN_USERNAME=kerfpulse-local-admin\nKC_ADMIN_PASSWORD='+password+'\n')
        with (root/'administrator.json').open('x',encoding='utf-8') as file:
            json.dump({'username':'kerfpulse-local-admin','password':password,'url':'http://localhost:8080/admin'},file,indent=2)
    return root,path


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',action='store_true');args=parser.parse_args()
    root,path=prepare()
    if args.prepare:
        print('Private local identity configuration prepared; no credentials printed.');return
    env=dict(line.split('=',1) for line in path.read_text().splitlines() if '=' in line)
    # Cold local providers can spend several seconds initializing password hashing.
    with httpx.Client(base_url='http://localhost:8080',timeout=30,trust_env=False) as client:
        for attempt in range(90):
            try:
                response=client.get('/realms/kerfpulse/.well-known/openid-configuration')
                if response.status_code==200:break
            except httpx.HTTPError:pass
            time.sleep(1)
        else:raise RuntimeError('Local Keycloak did not become ready')
        response=client.post('/realms/master/protocol/openid-connect/token',data={'grant_type':'password','client_id':'admin-cli',
                             'username':env['KC_ADMIN_USERNAME'],'password':env['KC_ADMIN_PASSWORD']})
        response.raise_for_status();headers={'Authorization':'Bearer '+response.json()['access_token']}
        username='local-engineer'
        users=client.get('/admin/realms/kerfpulse/users',params={'username':username,'exact':'true'},headers=headers)
        users.raise_for_status()
        if not users.json():
            credential_path=root/'engineer.json'
            if credential_path.exists():
                password=json.loads(credential_path.read_text(encoding='utf-8'))['password']
            else:
                password=secrets.token_urlsafe(24)
                # Persist before the remote mutation so timeout/retry retains the same password.
                with credential_path.open('x',encoding='utf-8') as file:
                    json.dump({'username':username,'password':password,'url':'http://localhost:8000/?workspace=operations',
                               'scope':'Local evaluation account; no machine grants assigned'},file,indent=2)
            response=client.post('/admin/realms/kerfpulse/users',headers=headers,json={'username':username,'enabled':True,'firstName':'Local','lastName':'Engineer','email':'local-engineer@kerfpulse.invalid',
                                'credentials':[{'type':'password','value':password,'temporary':False}]})
            response.raise_for_status()
        elif not (root/'engineer.json').exists():
            raise RuntimeError('Existing local-engineer account found without private credential file; use Keycloak administration to recover it')
    print('Local named account ready. Credentials remain in artifacts/private-identity/engineer.json; no machine grants assigned.')


if __name__=='__main__':main()
