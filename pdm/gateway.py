"""Replay verified completed cuts through a persistent MQTT gateway."""

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt

from pdm.dataset import SOURCE_SHA256, SOURCE_VERSION, load
from pdm.inference import predict
from pdm.policy import PolicyState, decide

LOGGER = logging.getLogger(__name__)


class ReplayModels:
    def __init__(self):
        directory = Path(os.getenv("PDM_MODEL_DIR", "artifacts/nested-workpiece"))
        content = (directory / "models.json").read_bytes()
        report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
        if report.get("source_sha256") != SOURCE_SHA256 or report.get("source") != SOURCE_VERSION:
            raise ValueError("Model source does not match the verified dataset")
        digest = hashlib.sha256(content).hexdigest()
        if digest != report["model_artifact_sha256"]:
            raise ValueError("Model artifact checksum mismatch")
        self.models = json.loads(content)
        self.version = digest[:16]
        self.by_tool = {tool_id: heads for heads in self.models.values()
                        for tool_id in heads["current"]["test_tools"]}

    def event(self, run, cut, state):
        event = {"schema_version": 1, "run_id": run["id"], "generation": run["generation"],
                 "source_version": SOURCE_VERSION, "tool_id": cut.tool_id, "cycle": cut.cycle,
                 "replay_at": datetime.now(timezone.utc).isoformat(),
                 "event_type": "cut", "quality": cut.status, "features": {},
                 "vibration_released": False}
        if cut.status != "ok":
            event["event_type"] = "damage" if cut.status == "damage" else "gap"
            event["quality"] = "ok" if cut.status == "damage" else cut.status
            return event
        values = {**cut.context, **cut.current, **cut.vibration}
        heads = self.by_tool.get(cut.tool_id)
        if heads is None:
            raise ValueError("No held-out model available for this cutter")
        current = predict(heads["current"], values)
        fused = predict(heads["fused"], values)
        decision = decide(state, cut.cycle, current, fused, run["policy"], run["slot_interval"])
        event["features"]["current"] = cut.current
        if decision["vibration_released"]:
            event["features"]["vibration"] = cut.vibration
        event["vibration_released"] = decision.pop("vibration_released")
        decision["model_version"] = self.version
        decision["reason"] = "Held-out benchmark model; inspection slot evaluated at current completed cut"
        event["decision"] = decision
        return event


def main():
    from pdm.store import Store

    logging.basicConfig(level=logging.INFO)
    store = Store()
    store.initialize()
    models = ReplayModels()
    tools = load()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="kerfpulse-gateway")
    username = os.getenv("MQTT_USERNAME")
    if username:
        client.username_pw_set(username, os.getenv("MQTT_PASSWORD"))
    if os.getenv("MQTT_TLS", "false").lower() == "true":
        client.tls_set()
    client.reconnect_delay_set(min_delay=1, max_delay=20)
    client.connect_async(os.getenv("MQTT_HOST", "127.0.0.1"), int(os.getenv("MQTT_PORT", "1883")))
    client.loop_start()
    due = {}
    heartbeat_at = 0.0
    try:
        while True:
            if time.monotonic() >= heartbeat_at:
                store.status("gateway_heartbeat", datetime.now(timezone.utc).isoformat())
                heartbeat_at = time.monotonic() + 10
            if not client.is_connected():
                time.sleep(0.5)
                continue
            for run in store.running_runs():
                key = (run["id"], run["generation"])
                if time.monotonic() < due.get(key, 0):
                    continue
                checkpoint = run.get("last_cycle") or 0
                tool = tools[run["tool_id"]]
                if checkpoint >= len(tool.cuts):
                    continue
                state = PolicyState(eligible=run["eligible_count"], released=run["vibration_count"],
                                    last_cycle=checkpoint)
                event = models.event(run, tool.cuts[checkpoint], state)
                payload = json.dumps(event, allow_nan=False, separators=(",", ":"))
                info = client.publish(os.getenv("MQTT_TOPIC", "pdm/replay/events"), payload, qos=1)
                try:
                    info.wait_for_publish(timeout=5)
                except RuntimeError:
                    LOGGER.warning("MQTT publication interrupted; retrying uncommitted source cycle")
                # The store checkpoint is the authority. Retransmission carries the same event key.
                due[key] = time.monotonic() + max(run["speed_ms"] / 1000, 0.1)
            time.sleep(0.05)
    finally:
        client.loop_stop()
        client.disconnect()
        store.close()


if __name__ == "__main__":
    main()
