"""Transactional assessment inbox/outbox, with explicit unsupported-domain results."""
import hashlib
import json
import uuid
from pdm.fresh_model import assess, InputError
from pdm.store import utcnow


class OperationalProcessing:
    def __init__(self,store): self.store=store

    def initialize(self):
        sequence='BIGSERIAL PRIMARY KEY' if self.store.postgres else 'INTEGER PRIMARY KEY AUTOINCREMENT'
        with self.store.transaction(write=True) as conn:
            if self.store.postgres: self.store.execute(conn,'SELECT pg_advisory_xact_lock(529418,4)')
            for sql in (
                'CREATE TABLE IF NOT EXISTS operational_assessments (id TEXT PRIMARY KEY, device_id TEXT NOT NULL, event_id TEXT NOT NULL, event_digest TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(device_id,event_id))',
                'CREATE TABLE IF NOT EXISTS operational_processing (receipt_id TEXT PRIMARY KEY REFERENCES ingest_receipts(id), state TEXT NOT NULL, assessment_id TEXT, payload TEXT NOT NULL, processed_at TEXT NOT NULL)',
                f'CREATE TABLE IF NOT EXISTS operational_outbox (id {sequence}, device_id TEXT NOT NULL, receipt_id TEXT NOT NULL UNIQUE REFERENCES ingest_receipts(id), payload TEXT NOT NULL)',
                'CREATE INDEX IF NOT EXISTS operational_device_cursor ON operational_outbox(device_id,id)',
            ): self.store.execute(conn,sql)

    def process_one(self):
        with self.store.transaction(write=True) as conn:
            suffix=' FOR UPDATE OF r SKIP LOCKED' if self.store.postgres else ''
            receipt=self.store.execute(conn,'SELECT r.* FROM ingest_receipts r WHERE NOT EXISTS (SELECT 1 FROM operational_processing p WHERE p.receipt_id=r.id) ORDER BY r.received_at,r.id LIMIT 1'+suffix).fetchone()
            if receipt is None: return None
            # Serialize different transport receipts for the same semantic device event.
            lock=' FOR UPDATE' if self.store.postgres else ''
            device=self.store.execute(conn,'SELECT * FROM ingest_devices WHERE id=?'+lock,(receipt['device_id'],)).fetchone()
            event=json.loads(receipt['envelope'])['event']
            event_digest=hashlib.sha256(json.dumps(event,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
            previous=self.store.execute(conn,'SELECT * FROM operational_assessments WHERE device_id=? AND event_id=?',(receipt['device_id'],event['event_id'])).fetchone()
            result={'receipt_id':receipt['id'],'device_id':receipt['device_id'],'assessment_id':None,'assessment':None,'state':'abstained','processed_at':utcnow()}
            if previous:
                if previous['event_digest']==event_digest:
                    result.update(state='duplicate',assessment_id=previous['id'],assessment=json.loads(previous['payload']))
                else:
                    result.update(state='quarantined',reason='semantic_event_conflict_original_retained')
            elif device['revoked_at'] is not None:
                result.update(state='blocked',reason='source_revoked_before_processing')
            elif receipt['sequence_status']=='out_of_order':
                result.update(state='superseded',reason='late_transport_event_no_retroactive_action')
            else:
                try:
                    assessment=assess(event)
                    result.update(state='assessed' if assessment['applicability']=='assessed' else 'abstained',assessment_id=uuid.uuid4().hex,assessment=assessment)
                    # Receipt scope is authoritative; client declarations confer no qualification.
                    assessment['source_scope']={k:receipt[k] for k in ('org_id','site_id','asset_id','device_id')}
                    assessment['receipt_id']=receipt['id']
                    self.store.execute(conn,'INSERT INTO operational_assessments(id,device_id,event_id,event_digest,payload,created_at) VALUES(?,?,?,?,?,?)',
                                       (result['assessment_id'],receipt['device_id'],event['event_id'],event_digest,json.dumps(assessment),result['processed_at']))
                except InputError as error:
                    result.update(state='rejected',reason='invalid_model_contract',field=error.field)
            payload=json.dumps(result,allow_nan=False)
            self.store.execute(conn,'INSERT INTO operational_processing(receipt_id,state,assessment_id,payload,processed_at) VALUES(?,?,?,?,?)',
                               (receipt['id'],result['state'],result['assessment_id'],payload,result['processed_at']))
            self.store.execute(conn,'INSERT INTO operational_outbox(device_id,receipt_id,payload) VALUES(?,?,?)',(receipt['device_id'],receipt['id'],payload))
            return result
