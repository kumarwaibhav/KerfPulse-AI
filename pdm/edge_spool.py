"""Bounded durable edge outbox. Delete only after matching application receipt."""
import hashlib
import json
from pathlib import Path
import sqlite3
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import urlparse


class SpoolFull(RuntimeError): pass


class EdgeSpool:
    def __init__(self, path, max_events=10000, max_bytes=256*2**20):
        self.path = str(path)
        self.max_events, self.max_bytes = max_events, max_bytes
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        conn = self.connection()
        try:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('CREATE TABLE IF NOT EXISTS spool (id TEXT PRIMARY KEY, digest TEXT NOT NULL, payload TEXT NOT NULL, bytes INTEGER NOT NULL)')
            conn.commit()
        finally: conn.close()

    def connection(self):
        conn = sqlite3.connect(self.path,timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA synchronous=FULL')
        return conn

    def enqueue(self, envelope):
        payload = json.dumps(envelope,sort_keys=True,separators=(',',':'),allow_nan=False)
        size = len(payload.encode())
        if size > 65536: raise ValueError('Event exceeds 64 KiB')
        key = str(envelope['boot_id'])+':'+str(envelope['sequence'])
        digest = hashlib.sha256(payload.encode()).hexdigest()
        conn = self.connection()
        try:
            conn.execute('BEGIN IMMEDIATE')
            old = conn.execute('SELECT digest FROM spool WHERE id=?',(key,)).fetchone()
            if old:
                if old['digest'] != digest: raise ValueError('Conflicting local event identity')
                return key
            count, used = conn.execute('SELECT count(*),coalesce(sum(bytes),0) FROM spool').fetchone()
            if count >= self.max_events or used+size > self.max_bytes: raise SpoolFull('Edge buffer full; evidence not accepted')
            conn.execute('INSERT INTO spool(id,digest,payload,bytes) VALUES(?,?,?,?)',(key,digest,payload,size))
            conn.commit()
            return key
        finally: conn.close()

    def pending(self, limit=30):
        conn = self.connection()
        try:
            return [dict(row) for row in conn.execute('SELECT * FROM spool ORDER BY rowid LIMIT ?',(min(max(limit,1),100),))]
        finally: conn.close()

    def acknowledge(self, key, receipt):
        conn = self.connection()
        try:
            conn.execute('BEGIN IMMEDIATE')
            row = conn.execute('SELECT * FROM spool WHERE id=?',(key,)).fetchone()
            if not row: return
            original = json.loads(row['payload'])
            if (receipt.get('status') not in ('persisted','duplicate') or receipt.get('digest') != row['digest'] or
                    receipt.get('boot_id') != original['boot_id'] or receipt.get('sequence') != original['sequence']):
                raise ValueError('Unmatched receipt; evidence retained')
            conn.execute('DELETE FROM spool WHERE id=?',(key,))
            conn.commit()
        finally: conn.close()


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Ingest redirects disabled to protect device credential')


def flush_http(spool, base_url, token, timeout=10):
    url = urlparse(base_url)
    if url.username or url.password or url.query or url.fragment:
        raise ValueError('Use a clean trusted ingest base URL')
    if url.scheme != 'https' and not (url.scheme=='http' and url.hostname in ('127.0.0.1','localhost','::1')):
        raise ValueError('Device traffic requires HTTPS except loopback development')
    opener = build_opener(NoRedirect())
    delivered = 0
    for row in spool.pending():
        request = Request(base_url.rstrip('/')+'/api/v2/ingest/cuts',data=row['payload'].encode(),
                          headers={'Content-Type':'application/json','Authorization':'Bearer '+token})
        with opener.open(request,timeout=timeout) as response:
            raw = response.read(65537)
            if len(raw)>65536: raise ValueError('Receipt exceeds limit')
            receipt = json.loads(raw)
        spool.acknowledge(row['id'],receipt)
        delivered += 1
    return delivered
