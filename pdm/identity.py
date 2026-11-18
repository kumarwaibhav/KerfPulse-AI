"""Named OIDC identity, server sessions, and explicit asset grants.

Identity-provider authentication never implies application authorization.
Local trusted administration owns grants; all reads recheck current grants.
"""
from datetime import datetime,timedelta,timezone
import hashlib
import json
import secrets
import uuid
from pdm.store import utcnow

ROLES=('operator','planner','technician','reliability','ot_admin','researcher')


def hashed(value):return hashlib.sha256(value.encode()).hexdigest()


class IdentityStore:
    def __init__(self,store):self.store=store

    def initialize(self):
        with self.store.transaction(write=True) as conn:
            if self.store.postgres:self.store.execute(conn,'SELECT pg_advisory_xact_lock(529418,6)')
            for sql in (
                'CREATE TABLE IF NOT EXISTS people (id TEXT PRIMARY KEY, issuer TEXT NOT NULL, subject TEXT NOT NULL, display_name TEXT NOT NULL, disabled INTEGER NOT NULL DEFAULT 0, UNIQUE(issuer,subject))',
                'CREATE TABLE IF NOT EXISTS people_sessions (id TEXT PRIMARY KEY, person_id TEXT NOT NULL REFERENCES people(id), csrf TEXT NOT NULL, expires_at TEXT NOT NULL)',
                'CREATE TABLE IF NOT EXISTS people_grants (person_id TEXT NOT NULL REFERENCES people(id), org_id TEXT NOT NULL, site_id TEXT NOT NULL, asset_id TEXT NOT NULL, role TEXT NOT NULL, PRIMARY KEY(person_id,org_id,site_id,asset_id,role))',
                'CREATE TABLE IF NOT EXISTS oidc_attempts (state TEXT PRIMARY KEY, binding TEXT NOT NULL, verifier TEXT NOT NULL, nonce TEXT NOT NULL, config_digest TEXT NOT NULL, expires_at TEXT NOT NULL)',
                'CREATE TABLE IF NOT EXISTS identity_audit (id TEXT PRIMARY KEY, person_id TEXT NOT NULL, action TEXT NOT NULL, payload TEXT NOT NULL, at TEXT NOT NULL)',
                'CREATE TABLE IF NOT EXISTS identity_login_limits (source TEXT PRIMARY KEY, window_start BIGINT NOT NULL, attempts INTEGER NOT NULL)',
            ):self.store.execute(conn,sql)

    def allow_login(self,source):
        import time
        now=int(time.time());key=hashed(source)
        with self.store.transaction(write=True) as conn:
            if self.store.postgres:self.store.execute(conn,'SELECT pg_advisory_xact_lock(529418,7)')
            self.store.execute(conn,'DELETE FROM identity_login_limits WHERE window_start<?',(now-60,))
            row=self.store.execute(conn,'SELECT * FROM identity_login_limits WHERE source=?',(key,)).fetchone()
            if row:
                if row['attempts']>=20:return False
                self.store.execute(conn,'UPDATE identity_login_limits SET attempts=attempts+1 WHERE source=?',(key,))
            else:
                count=self.store.execute(conn,'SELECT count(*) AS n FROM identity_login_limits').fetchone()['n']
                if count>=1000:return False
                self.store.execute(conn,'INSERT INTO identity_login_limits(source,window_start,attempts) VALUES(?,?,1)',(key,now))
        return True

    def audit(self,conn,person,action,payload):
        self.store.execute(conn,'INSERT INTO identity_audit(id,person_id,action,payload,at) VALUES(?,?,?,?,?)',
                           (uuid.uuid4().hex,person,action,json.dumps(payload),utcnow()))

    def attempt(self,config_digest):
        state=secrets.token_urlsafe(32);binding=secrets.token_urlsafe(32)
        value={'verifier':secrets.token_urlsafe(48),'nonce':secrets.token_urlsafe(32)}
        with self.store.transaction(write=True) as conn:
            self.store.execute(conn,'DELETE FROM oidc_attempts WHERE expires_at<?',(utcnow(),))
            count=self.store.execute(conn,'SELECT count(*) AS n FROM oidc_attempts').fetchone()['n']
            if count>=100:raise ValueError('Login capacity reached; retry after attempt expiry')
            self.store.execute(conn,'INSERT INTO oidc_attempts(state,binding,verifier,nonce,config_digest,expires_at) VALUES(?,?,?,?,?,?)',
                               (hashed(state),hashed(binding),value['verifier'],value['nonce'],config_digest,(datetime.now(timezone.utc)+timedelta(minutes=10)).isoformat()))
        return state,binding,value

    def consume(self,state,binding,config_digest):
        if not state or not binding or len(state)>200 or len(binding)>200:raise ValueError('Invalid login binding')
        with self.store.transaction(write=True) as conn:
            suffix=' FOR UPDATE' if self.store.postgres else ''
            row=self.store.execute(conn,'SELECT * FROM oidc_attempts WHERE state=?'+suffix,(hashed(state),)).fetchone()
            if not row or row['expires_at']<=utcnow() or not secrets.compare_digest(row['binding'],hashed(binding)) or row['config_digest']!=config_digest:
                raise ValueError('Login expired, replayed or browser binding mismatch')
            self.store.execute(conn,'DELETE FROM oidc_attempts WHERE state=?',(hashed(state),))
            return dict(row)

    def login(self,issuer,subject,display_name,token_expiry):
        person=hashed(issuer+'\0'+subject)
        token=secrets.token_urlsafe(40);csrf=secrets.token_urlsafe(32)
        expiry=min(datetime.fromtimestamp(token_expiry,timezone.utc),datetime.now(timezone.utc)+timedelta(hours=8)).isoformat()
        with self.store.transaction(write=True) as conn:
            self.store.execute(conn,'INSERT INTO people(id,issuer,subject,display_name) VALUES(?,?,?,?) ON CONFLICT(issuer,subject) DO UPDATE SET display_name=excluded.display_name',
                               (person,issuer,subject,display_name[:120]))
            # Serialize login with disabling/revocation operations.
            lock=' FOR UPDATE' if self.store.postgres else ''
            row=self.store.execute(conn,'SELECT disabled FROM people WHERE id=?'+lock,(person,)).fetchone()
            if row['disabled']:raise ValueError('Account disabled')
            self.store.execute(conn,'DELETE FROM people_sessions WHERE expires_at<?',(utcnow(),))
            self.store.execute(conn,'INSERT INTO people_sessions(id,person_id,csrf,expires_at) VALUES(?,?,?,?)',(hashed(token),person,csrf,expiry))
            self.audit(conn,person,'login',{})
        return token

    def session(self,token):
        if not isinstance(token,str) or len(token)>200:return None
        with self.store.transaction() as conn:
            row=self.store.execute(conn,'SELECT p.id,p.display_name,p.issuer,p.subject,s.csrf,s.expires_at FROM people_sessions s JOIN people p ON p.id=s.person_id WHERE s.id=? AND s.expires_at>? AND p.disabled=0',
                                   (hashed(token),utcnow())).fetchone()
            if not row:return None
            grants=self.store.execute(conn,'SELECT org_id,site_id,asset_id,role FROM people_grants WHERE person_id=?',(row['id'],)).fetchall()
            return {**dict(row),'grants':[dict(g) for g in grants]}

    def logout(self,token):
        with self.store.transaction(write=True) as conn:
            row=self.store.execute(conn,'SELECT person_id FROM people_sessions WHERE id=?',(hashed(token),)).fetchone()
            self.store.execute(conn,'DELETE FROM people_sessions WHERE id=?',(hashed(token),))
            if row:self.audit(conn,row['person_id'],'logout',{})

    def grant(self,person,org,site,asset,role,actor):
        if role not in ROLES or any(not isinstance(s,str) or not s.strip() or len(s)>100 for s in (org,site,asset,actor)):
            raise ValueError('Valid exact scope, role and actor required')
        with self.store.transaction(write=True) as conn:
            if not self.store.execute(conn,'SELECT id FROM people WHERE id=?',(person,)).fetchone():raise ValueError('Person must log in first')
            self.store.execute(conn,'INSERT INTO people_grants(person_id,org_id,site_id,asset_id,role) VALUES(?,?,?,?,?) ON CONFLICT DO NOTHING',(person,org,site,asset,role))
            self.audit(conn,person,'grant',{'org':org,'site':site,'asset':asset,'role':role,'actor':actor})

    def revoke(self,person,actor):
        if not actor.strip():raise ValueError('Actor required')
        with self.store.transaction(write=True) as conn:
            lock=' FOR UPDATE' if self.store.postgres else ''
            self.store.execute(conn,'SELECT id FROM people WHERE id=?'+lock,(person,)).fetchone()
            self.store.execute(conn,'DELETE FROM people_grants WHERE person_id=?',(person,))
            self.store.execute(conn,'DELETE FROM people_sessions WHERE person_id=?',(person,))
            self.audit(conn,person,'revoke_all_access',{'actor':actor})
