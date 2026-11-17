import copy
import hashlib
import json
import pytest
from pdm.edge_spool import EdgeSpool, SpoolFull, flush_http
from pdm.fresh_model import input_schema


def test_spool_persists_and_requires_matching_receipt(tmp_path):
    path = tmp_path/'spool.db'
    event = {'boot_id':'boot','sequence':1,'event':input_schema()['example']}
    spool = EdgeSpool(path,max_events=1)
    key = spool.enqueue(event)
    assert spool.enqueue(event) == key
    assert len(EdgeSpool(path).pending()) == 1
    changed = copy.deepcopy(event); changed['sequence'] = 2
    with pytest.raises(SpoolFull): spool.enqueue(changed)
    with pytest.raises(ValueError): spool.acknowledge(key,{'status':'persisted','digest':'wrong'})
    assert len(spool.pending()) == 1
    receipt = {'status':'persisted','boot_id':'boot','sequence':1,'digest':hashlib.sha256(json.dumps(event,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
    spool.acknowledge(key,receipt)
    assert not spool.pending()


def test_http_transport_requires_secure_destination(tmp_path):
    spool = EdgeSpool(tmp_path/'buffer.db')
    with pytest.raises(ValueError): flush_http(spool,'http://untrusted.example','not-a-secret')
    with pytest.raises(ValueError): flush_http(spool,'https://user:secret@example.org','not-a-secret')
