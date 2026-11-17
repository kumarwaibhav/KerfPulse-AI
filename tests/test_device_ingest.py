"""Protocol fixtures only: relabelled benchmark values are not plant evidence."""
import copy
from concurrent.futures import ThreadPoolExecutor
import json

import pytest

from pdm.device_ingest import DeviceAuthError, DeviceIngest
from pdm.fresh_model import assess, input_schema
from pdm.store import Store, StoreError


@pytest.fixture
def service(tmp_path):
    service = DeviceIngest(Store("sqlite:///" + str(tmp_path / "devices.db")))
    service.initialize()
    return service


@pytest.fixture
def envelope():
    # Real schema example for contract coverage ONLY; these are not field measurements.
    event = copy.deepcopy(input_schema()["example"])
    event.update(asset_id="mill-1", data_origin="user-measured", clock_basis="observed")
    return {"schema_version": 1, "boot_id": "boot-1", "sequence": 1, "event": event}


def provision(service, asset="mill-1"):
    return service.register_device("org-1", "site-1", asset)


def test_durable_original_evidence_and_one_time_secret(service, envelope):
    device = provision(service)
    receipt = service.ingest(device["token"], envelope)
    assert receipt["status"] == "persisted"
    assert receipt["inference_status"] == "not_started"
    assert receipt["sequence_status"] == "contiguous"
    reopened = DeviceIngest(Store(service.store.url))
    reopened.initialize()
    saved = reopened.get_receipt(device["token"], receipt["id"])
    assert saved["envelope"] == envelope
    assert (saved["org_id"], saved["site_id"], saved["asset_id"]) == ("org-1", "site-1", "mill-1")
    with service.store.transaction() as connection:
        row = dict(service.store.execute(connection, "SELECT * FROM ingest_devices").fetchone())
        tables = service.store.execute(connection, "SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    assert device["token"] not in json.dumps(row)
    assert len(row["token_hash"]) == 64
    assert "sessions" not in [row["name"] for row in tables]
    assert "token_hash" not in service.authenticate(device["token"])
    # Ingestion never changes the existing model's measured-domain qualification.
    assert assess(saved["envelope"]["event"])["applicability"] == "unsupported_domain"


def test_authentication_rotation_revocation_and_scope(service, envelope):
    first, second = provision(service), provision(service, "mill-2")
    for bad in (None, "", "x", first["token"] + "x", "é" * 50, "x" * 201):
        with pytest.raises(DeviceAuthError):
            service.ingest(bad, envelope)
    with pytest.raises(StoreError, match="scope"):
        service.ingest(second["token"], envelope)
    receipt = service.ingest(first["token"], envelope)
    assert service.get_receipt(second["token"], receipt["id"]) is None
    injected = {**envelope, "org_id": "org-2"}
    with pytest.raises(StoreError):
        service.ingest(first["token"], injected)
    rotated = service.rotate_token(first["device_id"])
    with pytest.raises(DeviceAuthError):
        service.authenticate(first["token"])
    assert service.ingest(rotated, envelope)["status"] == "duplicate"
    service.revoke_device(first["device_id"])
    with pytest.raises(DeviceAuthError):
        service.ingest(rotated, envelope)
    with pytest.raises(DeviceAuthError):
        service.get_receipt(rotated, receipt["id"])
    with pytest.raises(StoreError):
        service.rotate_token(first["device_id"])


def test_idempotency_conflicts_and_original_preserved(service, envelope):
    token = provision(service)["token"]
    original = service.ingest(token, envelope)
    reordered = dict(reversed(list(envelope.items())))
    same = service.ingest(token, reordered)
    assert same["status"] == "duplicate" and same["id"] == original["id"]
    changed = copy.deepcopy(envelope)
    changed["event"]["context"]["HardnessMean"] += 1
    conflict = service.ingest(token, changed)
    repeated = service.ingest(token, changed)
    assert conflict["status"] == "quarantined"
    assert repeated["quarantine_id"] == conflict["quarantine_id"]
    assert service.get_receipt(token, original["id"])["envelope"] == envelope
    with service.store.transaction() as connection:
        row = service.store.execute(connection, "SELECT envelope FROM ingest_quarantine WHERE id=?", (conflict["quarantine_id"],)).fetchone()
        assert json.loads(row["envelope"]) == changed


def test_gaps_out_of_order_and_boot_reset(service, envelope):
    token = provision(service)["token"]
    gap = service.ingest(token, {**envelope, "sequence": 3})
    assert gap["sequence_status"] == "gap" and gap["missing_before"] == 2
    late = service.ingest(token, envelope)
    assert late["sequence_status"] == "out_of_order" and late["missing_before"] == 0
    assert service.ingest(token, {**envelope, "sequence": 4})["sequence_status"] == "contiguous"
    assert service.ingest(token, {**envelope, "boot_id": "boot-2"})["sequence_status"] == "contiguous"


def test_parallel_retries_commit_only_one_receipt(service, envelope):
    token = provision(service)["token"]
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda _: service.ingest(token, envelope), range(12)))
    assert len({row["id"] for row in results}) == 1
    assert sum(row["status"] == "persisted" for row in results) == 1
    assert sum(row["status"] == "duplicate" for row in results) == 11


@pytest.mark.parametrize("change", [
    lambda e: e.update(schema_version=True),
    lambda e: e.update(sequence=True),
    lambda e: e.update(sequence=2**63),
    lambda e: e.update(boot_id="x" * 101),
    lambda e: e["event"].update(data_origin="haas-benchmark-example"),
    lambda e: e["event"].update(clock_basis="demonstration"),
    lambda e: e["event"].update(org_id="forged"),
    lambda e: e["event"].update(sequence_number=False),
    lambda e: e["event"].update(cut_completed_at="2026-01-01"),
    lambda e: e["event"].update(cut_completed_at="9999-01-01T00:00:00Z"),
    lambda e: e["event"].update(features={}),
    lambda e: e["event"]["features"].update(outlier=float("nan")),
    lambda e: e["event"]["features"].update(outlier=1e13),
    lambda e: e["event"]["features"].update(NumberOfCycle=1),
    lambda e: e["event"]["context"].update(NumberOfCycle=-1),
    lambda e: e["event"].update(inspection_breaks=[True]),
    lambda e: e["event"].update(features={str(i): i for i in range(257)}),
    lambda e: e["event"].update(features={"x" * 70000: 1}),
])
def test_contract_rejection_leaves_no_receipt(service, envelope, change):
    token = provision(service)["token"]
    change(envelope)
    with pytest.raises(StoreError):
        service.ingest(token, envelope)
    with service.store.transaction() as connection:
        assert service.store.execute(connection, "SELECT COUNT(*) AS n FROM ingest_receipts").fetchone()["n"] == 0
