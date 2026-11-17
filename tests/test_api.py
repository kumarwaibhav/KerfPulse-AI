"""Regression checks for ownership, durable replay, budgets, and work-order state."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from copy import deepcopy
import os
import socket
import threading
import time
import uuid
from urllib.parse import quote

from fastapi.testclient import TestClient
import httpx
import pytest

from pdm.api import COOKIE, create_app
from pdm.store import Store, StoreError, utcnow


@pytest.fixture(params=["sqlite"] + (["postgresql"] if os.getenv("PDM_TEST_POSTGRES_URL") else []))
def database_url(request, tmp_path):
    if request.param == "sqlite":
        yield f"sqlite:///{tmp_path / 'test.sqlite3'}"
        return
    import psycopg
    schema = "test_" + uuid.uuid4().hex
    original = os.environ["PDM_TEST_POSTGRES_URL"]
    with psycopg.connect(original, autocommit=True) as connection:
        connection.execute(f"CREATE SCHEMA {schema}")
    try:
        separator = "&" if "?" in original else "?"
        yield original + separator + "options=" + quote(f"-csearch_path={schema}")
    finally:
        with psycopg.connect(original, autocommit=True) as connection:
            connection.execute(f"DROP SCHEMA {schema} CASCADE")


@pytest.fixture
def app(database_url, monkeypatch):
    monkeypatch.delenv("PDM_DEMO_ROLE", raising=False)
    monkeypatch.setattr("pdm.dataset.list_tools", lambda: [{"tool_id": 2, "cycles": 50}])
    return create_app(database_url)


def start(client, policy="decision"):
    response = client.post("/api/runs", json={"tool_id": 2, "policy": policy, "speed_ms": 100, "slot_interval": 3})
    assert response.status_code == 201, response.text
    return response.json()


def event(run, cycle, release=False, inspect=False, event_type="cut", quality="ok"):
    current = {"current": 0.25} if event_type == "cut" else {}
    features = {"current": current}
    if release:
        features["vibration"] = {"vibration": 0.5}
    result = {"schema_version": 1, "run_id": run["id"], "generation": run["generation"], "tool_id": run["tool_id"], "cycle": cycle, "event_type": event_type, "quality": quality, "source_version": "test-source", "replay_at": utcnow(), "features": features, "vibration_released": release}
    if inspect:
        result["decision"] = {"status": "inspect", "slot": cycle + 2, "risk": 0.7, "actionable_risk": 0.6, "model_version": "test", "reason": "Test inspection evidence"}
    return result


def test_cookie_ownership_origin_and_roles(app, monkeypatch):
    with TestClient(app) as alice, TestClient(app) as bob:
        assert alice.get("/api/runs").status_code == 401
        response = alice.get("/api/session")
        assert response.json() == {"role": "planner"}
        cookie = response.headers["set-cookie"].lower()
        assert "httponly" in cookie and "samesite=strict" in cookie
        run = start(alice)
        bob.get("/api/session")
        assert bob.get("/api/runs").json() == []
        assert bob.get(f"/api/runs/{run['id']}").status_code == 404
        assert bob.get(f"/api/runs/{run['id']}/export").status_code == 404
        assert bob.post(f"/api/runs/{run['id']}/pause", json={}).status_code == 404
        assert alice.post(f"/api/runs/{run['id']}/pause", json={}, headers={"origin": "https://untrusted.example"}).status_code == 403
        assert alice.post(f"/api/runs/{run['id']}/pause", content="", headers={"content-type": "application/x-www-form-urlencoded"}).status_code == 415
        monkeypatch.setenv("PDM_DEMO_ROLE", "viewer")
        assert alice.post(f"/api/runs/{run['id']}/pause", json={}).status_code == 403
        assert alice.get(f"/api/runs/{run['id']}").status_code == 200


def test_checkpoint_duplicate_budget_and_restart(app):
    with TestClient(app) as client:
        client.get("/api/session")
        run = start(client)
        store = app.state.store
        with pytest.raises(StoreError, match="prefix budget"):
            store.ingest(event(run, 1, release=True))
        assert store.get_run(run["id"])["last_cycle"] == 0
        assert store.ingest(event(run, 1))
        assert not store.ingest(event(run, 1))
        assert store.ingest(event(run, 2, event_type="gap", quality="gap"))
        assert store.ingest(event(run, 3))
        with pytest.raises(StoreError, match="prefix budget"):
            store.ingest(event(run, 4, release=True))
        assert store.ingest(event(run, 4))
        # A gap did not earn quota. Four accepted cuts now permit one release.
        assert store.ingest(event(run, 5, release=True))
        snapshot = client.get(f"/api/runs/{run['id']}").json()
        assert snapshot["run"]["eligible_count"] == 4
        assert snapshot["run"]["vibration_count"] == 1
        cursor = snapshot["cursor"]
        owner = store.session_id(client.cookies[COOKIE])
        assert store.events(run["id"], owner, cursor) == []
        restarted = client.post(f"/api/runs/{run['id']}/restart", json={}).json()
        assert restarted["generation"] == 2 and restarted["last_cycle"] == 0
        assert not store.ingest(event(run, 6))
        reset = client.get(f"/api/runs/{run['id']}").json()
        assert reset["readings"] == [] and reset["work_orders"] == []
        assert store.events(run["id"], owner, cursor)[0]["data"]["generation"] == 2


def test_first_order_transitions_and_terminal_commit(app):
    with TestClient(app) as client:
        client.get("/api/session")
        run = start(client)
        store = app.state.store
        assert store.ingest(event(run, 1, inspect=True))
        assert store.ingest(event(run, 2, inspect=True))
        snapshot = client.get(f"/api/runs/{run['id']}").json()
        assert len(snapshot["work_orders"]) == 1
        order_id = snapshot["work_orders"][0]["id"]
        route = f"/api/runs/{run['id']}/work-orders/{order_id}"
        assert client.post(route + "/complete", json={}).status_code == 409
        assert client.post(route + "/approve", json={}).json()["status"] == "approved"
        assert client.post(route + "/approve", json={}).json()["status"] == "approved"
        assert client.post(route + "/complete", json={"finding": "Inspection found a chipped cutting edge"}).json()["finding"] == "Inspection found a chipped cutting edge"
        assert client.post(route + "/dismiss", json={}).status_code == 409
        assert store.ingest(event(run, 3, event_type="damage"))
        completed = client.get(f"/api/runs/{run['id']}").json()
        assert completed["run"]["state"] == "completed"
        assert completed["run"]["eligible_count"] == 2
        assert client.get(f"/api/runs/{run['id']}/export").json()["provenance"]["license"] == "CC BY 4.0"


@pytest.mark.parametrize("patch", [{"features": []}, {"features": {"current": []}}, {"decision": []}, {"decision": {"status": "inspect", "slot": True}}, {"decision": {"status": "monitor", "risk": "0.5"}}, {"decision": {"status": "monitor", "risk": float("nan")}}, {"vibration_released": "false"}, {"schema_version": True}])
def test_malformed_telemetry_never_changes_checkpoint(app, patch):
    with TestClient(app) as client:
        client.get("/api/session")
        run = start(client)
        data = event(run, 1)
        data.update(deepcopy(patch))
        with pytest.raises(StoreError):
            app.state.store.ingest(data)
        assert app.state.store.get_run(run["id"])["last_cycle"] == 0


def test_concurrent_delivery_and_restarts_respect_limits(database_url):
    store = Store(database_url)
    store.initialize()
    owner = store.create_session("concurrency-test")["id"]
    run = store.create_run(owner, 2, "decision", 100, 3)
    data = event(run, 1)
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda _: store.ingest(data), range(6)))
    assert sum(results) == 1
    assert store.get_run(run["id"])["eligible_count"] == 1
    # Two completed runs race for the final active slot.
    candidates = [run]
    store.ingest(event(run, 2, event_type="damage"))
    second = store.create_run(owner, 2, "decision", 100, 3)
    store.ingest(event(second, 1, event_type="damage"))
    candidates.append(second)
    for _ in range(3):
        store.create_run(owner, 2, "decision", 100, 3)

    def restart(run):
        try:
            store.control(run["id"], owner, "restart")
            return True
        except StoreError:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(restart, candidates)) == 1
    assert sum(run["state"] == "running" for run in store.list_runs(owner)) == 4


def test_run_limits_and_invalid_inputs(app):
    with TestClient(app) as client:
        client.get("/api/session")
        assert client.post("/api/runs", json={"tool_id": True}).status_code == 422
        assert client.post("/api/runs", json={"tool_id": 99}).status_code == 422
        assert client.post("/api/runs", json={"tool_id": 2, "slot_interval": 4}).status_code == 422
        for _ in range(4):
            start(client)
        assert client.post("/api/runs", json={"tool_id": 2}).status_code == 409


def test_body_limit_applies_to_fixed_and_chunked_requests(app):
    with TestClient(app) as client:
        client.get("/api/session")
        headers = {"content-type": "application/json"}
        assert client.post("/api/runs", content=b"x" * 65537, headers=headers).status_code == 413
        chunks = iter([b"x" * 32768, b"x" * 32768, b"x"])
        assert client.post("/api/runs", content=chunks, headers=headers).status_code == 413
        assert client.get("/api/runs").json() == []


def test_sse_http_resume_and_ownership(app):
    import uvicorn

    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    address = f"http://127.0.0.1:{listener.getsockname()[1]}"
    server = uvicorn.Server(uvicorn.Config(app, log_level="error"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 10
        while not server.started and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert server.started
        with httpx.Client(base_url=address, timeout=5) as client:
            client.get("/api/session")
            run = start(client)
            snapshot = client.get(f"/api/runs/{run['id']}").json()
            app.state.store.ingest(event(run, 1))
            owner = app.state.store.session_id(client.cookies[COOKIE])
            batch = app.state.store.events(run["id"], owner, snapshot["cursor"])
            reading_id = next(item["id"] for item in batch if item["kind"] == "reading")
            with client.stream("GET", f"/api/runs/{run['id']}/events?after=0", headers={"Last-Event-ID": str(reading_id)}) as response:
                assert response.status_code == 200
                lines = []
                for line in response.iter_lines():
                    if not line:
                        break
                    lines.append(line)
                assert f"id: {reading_id + 1}" in lines
                assert "event: update" in lines
                assert any('"kind":"state"' in line for line in lines)
            assert client.get(f"/api/runs/{run['id']}/events", headers={"Last-Event-ID": "99999999999999999999999999999999"}).status_code == 400
            assert client.get(f"/api/runs/{run['id']}/events?after=-1").status_code == 422
            with ExitStack() as streams:
                for _ in range(4):
                    opened = streams.enter_context(client.stream("GET", f"/api/runs/{run['id']}/events?after=0"))
                    assert opened.status_code == 200
                assert client.get(f"/api/runs/{run['id']}/events").status_code == 429
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        listener.close()
    assert not thread.is_alive()
