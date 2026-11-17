"""Persist MQTT telemetry before acknowledging delivery."""

import json
import logging
import os
import threading

import paho.mqtt.client as mqtt
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties

from pdm.store import Store, StoreError, utcnow


LOGGER = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO)
    store = Store()
    store.initialize()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=os.getenv("MQTT_WORKER_ID", "kerfpulse-persistence"), protocol=mqtt.MQTTv5, manual_ack=True)
    username = os.getenv("MQTT_USERNAME")
    if username:
        client.username_pw_set(username, os.getenv("MQTT_PASSWORD"))
    if os.getenv("MQTT_TLS", "false").lower() == "true":
        client.tls_set()
    connected = threading.Event()
    stopping = threading.Event()

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            LOGGER.error("MQTT connection rejected: %s", reason_code)
            return
        client.subscribe(os.getenv("MQTT_TOPIC", "pdm/replay/events"), qos=1)
        connected.set()
        store.status("worker_at", utcnow())
        store.status("connected", "true")

    def on_disconnect(client, userdata, flags, reason_code, properties):
        connected.clear()
        store.status("connected", "false")

    def on_message(client, userdata, message):
        try:
            if len(message.payload) > 262144:
                raise StoreError("Telemetry packet exceeds 256 KiB")
            payload = json.loads(message.payload)
            if not isinstance(payload, dict):
                raise StoreError("Telemetry must be an object")
            store.ingest(payload, wire_bytes=len(message.payload))
        except (StoreError, ValueError, TypeError, KeyError, AttributeError) as error:
            # Invalid data is deliberately rejected so a poison packet cannot block a run.
            LOGGER.warning("Rejected telemetry packet %s: %s", message.mid, error)
            store.status("last_rejection_at", utcnow())
        # Database outages propagate and leave delivery unacknowledged for a restarted worker.
        if message.qos:
            client.ack(message.mid, message.qos)

    def heartbeat():
        iterations = 0
        while not stopping.wait(10):
            if connected.is_set():
                try:
                    store.status("worker_at", utcnow())
                    iterations += 1
                    if iterations % 6 == 0:
                        store.cleanup()
                except Exception:
                    LOGGER.exception("Persistence heartbeat failed")

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    session = Properties(PacketTypes.CONNECT)
    session.SessionExpiryInterval = 86400
    client.connect_async(os.getenv("MQTT_HOST", "127.0.0.1"), int(os.getenv("MQTT_PORT", "1883")), clean_start=False, properties=session)
    monitor = threading.Thread(target=heartbeat, daemon=True)
    monitor.start()
    try:
        client.loop_forever(retry_first_connection=True)
    finally:
        stopping.set()
        client.disconnect()
        monitor.join(timeout=2)
        store.close()


if __name__ == "__main__":
    main()
