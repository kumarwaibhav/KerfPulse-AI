"""Exercise the running HTTP -> MQTT -> PostgreSQL -> HTTP workflow."""

import argparse
from datetime import datetime
import json
from pathlib import Path
import time

import httpx


def verify(base_url):
    started = time.perf_counter()
    with httpx.Client(base_url=base_url, timeout=10) as owner, httpx.Client(base_url=base_url, timeout=10) as stranger:
        assert owner.get("/healthz").raise_for_status().json()["database"] == "postgresql"
        assert owner.get("/api/runs").status_code == 401
        owner.get("/api/session").raise_for_status()
        stranger.get("/api/session").raise_for_status()
        assert owner.post("/api/runs", json={"tool_id": 2, "speed_ms": 1}).status_code == 422
        assert owner.post("/api/runs", json={"tool_id": 2}, headers={"Origin": "https://example.invalid"}).status_code == 403
        run = owner.post("/api/runs", json={"tool_id": 2, "policy": "current", "speed_ms": 100, "slot_interval": 3}).raise_for_status().json()
        path = "/api/runs/" + run["id"]
        assert stranger.get(path).status_code == 404
        owner.post(path + "/pause", json={}).raise_for_status()
        assert owner.get(path).json()["run"]["state"] == "paused"
        owner.post(path + "/resume", json={}).raise_for_status()
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            snapshot = owner.get(path).raise_for_status().json()
            if snapshot["run"]["state"] == "completed":
                break
            time.sleep(0.2)
        else:
            raise AssertionError("MQTT replay failed to reach the archived damage event")
        assert snapshot["run"]["last_cycle"] == 50
        assert len(snapshot["readings"]) == 50
        assert snapshot["readings"][-1]["event_type"] == "damage"
        assert snapshot["readings"][-1]["features"] == {}
        assert snapshot["run"]["vibration_count"] == 0
        latency_ms = sorted((datetime.fromisoformat(row["received_at"]) - datetime.fromisoformat(row["replay_at"])).total_seconds() * 1000
                            for row in snapshot["readings"])
        order = snapshot["work_orders"][0]
        order_path = path + "/work-orders/" + order["id"]
        assert stranger.post(order_path + "/approve", json={}).status_code == 404
        owner.post(order_path + "/approve", json={}).raise_for_status()
        owner.post(order_path + "/complete", json={"finding": "Software replay QA exercise; no physical inspection performed."}).raise_for_status()
        assert owner.get(path).json()["work_orders"][0]["status"] == "completed"
        export = owner.get(path + "/export").raise_for_status().json()
        assert export["provenance"]["license"] == "CC BY 4.0"
        generation = owner.post(path + "/restart", json={}).raise_for_status().json()["generation"]
        owner.post(path + "/pause", json={}).raise_for_status()
        assert generation == 2
        report = {"checks": "HTTP session isolation, input validation, origin, pause/resume, actual MQTT replay, PostgreSQL persistence, order transitions, export, restart",
                  "source_cycles": 50, "model_version": order["model_version"],
                  "gateway_to_ingest_p95_ms": latency_ms[47],
                  "seconds": time.perf_counter() - started, "status": "passed"}
        Path("artifacts/live-integration.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    verify(parser.parse_args().url)
