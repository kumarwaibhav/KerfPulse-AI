"""Trusted-local qualification revisions; never client-declared permission."""
from datetime import datetime,timezone
import json
import uuid
from pdm.fresh_model import release
from pdm.store import utcnow


class QualificationRegistry:
    def __init__(self,store):self.store=store

    def initialize(self):
        with self.store.transaction(write=True) as conn:
            if self.store.postgres:self.store.execute(conn,'SELECT pg_advisory_xact_lock(529418,5)')
            for sql in (
                'CREATE TABLE IF NOT EXISTS source_qualifications (id TEXT PRIMARY KEY, device_id TEXT NOT NULL REFERENCES ingest_devices(id), revision INTEGER NOT NULL, payload TEXT NOT NULL, UNIQUE(device_id,revision))',
                'CREATE TABLE IF NOT EXISTS operator_source_grants (owner TEXT NOT NULL, device_id TEXT NOT NULL REFERENCES ingest_devices(id), PRIMARY KEY(owner,device_id))',
            ):self.store.execute(conn,sql)

    def record(self,device_id,state,profile,actor,evidence,valid_until):
        if state not in ('unqualified','extraction_verified','shadow_approved','revoked'):
            raise ValueError('Advisory approval disabled: no advisory-qualified model release exists')
        required={'feature_schema_version','sensor_profile_version','extractor_version','model_digest'}
        if not isinstance(profile,dict) or set(profile)!=required or any(not isinstance(v,str) or not 1<=len(v)<=128 for v in profile.values()):
            raise ValueError('Exact schema, sensor profile, extractor version and model digest required')
        if not isinstance(actor,str) or not actor.strip() or len(actor)>100 or not isinstance(evidence,str) or not 10<=len(evidence)<=2000:
            raise ValueError('Actor and bounded evidence reference/reason required')
        expiry=datetime.fromisoformat(valid_until.replace('Z','+00:00'))
        if expiry.tzinfo is None or expiry<=datetime.now(timezone.utc):raise ValueError('Future timezone-qualified expiry required')
        if state=='shadow_approved':
            _,manifest=release()
            if profile['model_digest']!=manifest['digest'] or any(profile[k]!=manifest[k] for k in ('feature_schema_version','sensor_profile_version')):
                raise ValueError('Shadow binding does not match verified active release')
        with self.store.transaction(write=True) as conn:
            lock=' FOR UPDATE' if self.store.postgres else ''
            device=self.store.execute(conn,'SELECT * FROM ingest_devices WHERE id=?'+lock,(device_id,)).fetchone()
            if device is None or device['revoked_at']:raise ValueError('Active registered source required')
            revision=self.store.execute(conn,'SELECT coalesce(max(revision),0)+1 AS n FROM source_qualifications WHERE device_id=?',(device_id,)).fetchone()['n']
            value={'id':uuid.uuid4().hex,'device_id':device_id,'revision':revision,'state':state,'profile':dict(profile),
                   'actor':actor,'evidence':evidence,'valid_until':expiry.isoformat(),'recorded_at':utcnow(),
                   'physical_commissioning':'not_established_by_this_record'}
            self.store.execute(conn,'INSERT INTO source_qualifications(id,device_id,revision,payload) VALUES(?,?,?,?)',
                               (value['id'],device_id,revision,json.dumps(value)))
            return value

    def resolve(self,conn,device,event):
        row=self.store.execute(conn,'SELECT payload FROM source_qualifications WHERE device_id=? ORDER BY revision DESC LIMIT 1',(device['id'],)).fetchone()
        record=json.loads(row['payload']) if row else {'id':None,'revision':0,'state':'unqualified'}
        result={**record,'eligible':False,'reason':'source_not_qualified'}
        if device['revoked_at']:result['reason']='device_revoked';return result
        if record['state']!='shadow_approved':return result
        if datetime.fromisoformat(record['valid_until'])<=datetime.now(timezone.utc):result['reason']='qualification_expired';return result
        try:_,manifest=release()
        except (OSError,ValueError,KeyError):result['reason']='model_unavailable';return result
        profile=record['profile']
        if profile['model_digest']!=manifest['digest']:result['reason']='model_digest_changed';return result
        if any(event[k]!=profile[k] for k in ('feature_schema_version','sensor_profile_version')):
            result['reason']='profile_mismatch';return result
        # Extractor is registered but not attested in current transport. Thus shadow only.
        result.update(eligible=True,reason='shadow_evaluation_only_extractor_attestation_pending')
        return result

    def grant(self,owner,device_id):
        if not isinstance(owner,str) or len(owner)!=64 or any(c not in '0123456789abcdef' for c in owner):raise ValueError('Workspace ID must be 64 hex characters')
        with self.store.transaction(write=True) as conn:
            if self.store.execute(conn,'SELECT id FROM sessions WHERE id=? AND expires_at>?',(owner,utcnow())).fetchone() is None:
                raise ValueError('Active workspace required')
            self.store.execute(conn,'INSERT INTO operator_source_grants(owner,device_id) VALUES(?,?) ON CONFLICT DO NOTHING',(owner,device_id))

    def health(self,owner):
        with self.store.transaction() as conn:
            sources=self.store.execute(conn,'SELECT d.* FROM ingest_devices d JOIN operator_source_grants g ON g.device_id=d.id WHERE g.owner=? ORDER BY d.id',(owner,)).fetchall()
            result=[]
            for device in sources:
                row=self.store.execute(conn,'SELECT * FROM ingest_receipts WHERE device_id=? ORDER BY received_at DESC,id DESC LIMIT 1',(device['id'],)).fetchone()
                reasons=[]
                event=json.loads(row['envelope'])['event'] if row else {}
                binding=self.resolve(conn,device,event) if row else self.resolve(conn,device,{'feature_schema_version':'','sensor_profile_version':''})
                if not binding['eligible']:reasons.append(binding['reason'])
                if not row:reasons.append('no_observations')
                else:
                    arrival_age=(datetime.now(timezone.utc)-datetime.fromisoformat(row['received_at'])).total_seconds()
                    if arrival_age>60:reasons.append('no_recent_receipts')
                    age=(datetime.now(timezone.utc)-datetime.fromisoformat(event['cut_completed_at'].replace('Z','+00:00'))).total_seconds()
                    if age>300:reasons.append('stale_observation')
                    if row['sequence_status']!='contiguous':reasons.append('transport_'+row['sequence_status'])
                processed=self.store.execute(conn,'SELECT payload FROM operational_processing WHERE receipt_id=?',(row['id'],)).fetchone() if row else None
                assessment=json.loads(processed['payload']) if processed else None
                result.append({'device_id':device['id'],'org_id':device['org_id'],'site_id':device['site_id'],'asset_id':device['asset_id'],
                               'qualification':binding,'health':'attention_required' if reasons else 'shadow_only','reason_codes':reasons,
                               'last_received_at':row['received_at'] if row else None,'evidence_cutoff':event.get('cut_completed_at'),
                               'processing':assessment,'physical_connection':'uncommissioned','source_mode':'device_uploaded_measurements'})
            return result
