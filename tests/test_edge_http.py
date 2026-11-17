"""Real loopback HTTP using measured benchmark values as explicit test fixtures."""
import copy
import os
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

from pdm.device_ingest import DeviceIngest
from pdm.edge_spool import EdgeSpool, flush_http
from pdm.fresh_model import input_schema
from pdm.store import Store


def test_real_http_spool_delivery_and_duplicate_receipt(tmp_path):
    database = 'sqlite:///'+str(tmp_path/'http.db')
    service = DeviceIngest(Store(database)); service.initialize()
    device = service.register_device('protocol-test','fixture-site','fixture-mill')
    event = copy.deepcopy(input_schema()['example'])
    # Contract transport test only; benchmark values are not physical observations.
    event.update(asset_id='fixture-mill',data_origin='user-measured',clock_basis='observed')
    envelope = {'schema_version':1,'boot_id':'fixture-boot','sequence':1,'event':event}
    spool = EdgeSpool(tmp_path/'edge.db'); spool.enqueue(envelope)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); port = sock.getsockname()[1]
    base = 'http://127.0.0.1:'+str(port)
    process = subprocess.Popen([sys.executable,'-m','uvicorn','pdm.api:app','--host','127.0.0.1','--port',str(port)],
                               env={**os.environ,'PDM_DATABASE_URL':database},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                with urlopen(base+'/healthz',timeout=.2): break
            except OSError: time.sleep(.1)
        assert process.poll() is None
        assert flush_http(spool,base,device['token']) == 1
        assert not spool.pending()
        spool.enqueue(envelope)
        assert flush_http(spool,base,device['token']) == 1
        with service.store.transaction() as conn:
            assert service.store.execute(conn,'SELECT count(*) AS n FROM ingest_receipts').fetchone()['n'] == 1
    finally:
        process.terminate(); process.wait(timeout=10)
