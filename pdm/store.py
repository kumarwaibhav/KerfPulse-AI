"""Durable sessions, replay checkpoints, work orders, and event outbox."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import threading
import uuid


def utcnow():
    return datetime.now(timezone.utc).isoformat()


class StoreError(ValueError):
    pass


class Store:
    def __init__(self, database_url=None):
        self.url = database_url or os.getenv("PDM_DATABASE_URL") or os.getenv("DATABASE_URL") or "sqlite:///data/pdm.sqlite3"
        self.postgres = self.url.startswith(("postgres://", "postgresql://"))
        self._pool = None
        self._pool_lock = threading.Lock()
        if not self.postgres:
            self.path = self.url.removeprefix("sqlite:///")
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)

    def _connection_pool(self):
        if self._pool is None:
            with self._pool_lock:
                if self._pool is None:
                    from psycopg.rows import dict_row
                    from psycopg_pool import ConnectionPool
                    size = int(os.getenv("PDM_DB_POOL_SIZE", "8"))
                    if not 1 <= size <= 32:
                        raise ValueError("PDM_DB_POOL_SIZE must be within 1..32")
                    self._pool = ConnectionPool(self.url, min_size=1, max_size=size,
                                                timeout=10, max_waiting=64, open=True,
                                                kwargs={"row_factory": dict_row, "connect_timeout": 10},
                                                check=ConnectionPool.check_connection)
        return self._pool

    def close(self):
        if self._pool is not None:
            self._pool.close()

    def pool_stats(self):
        return self._pool.get_stats() if self._pool is not None else {}

    @contextmanager
    def transaction(self, write=False):
        if self.postgres and os.getenv("PDM_DB_POOL", "true").lower() != "false":
            # Context commits/rolls back and returns an idle connection; it never closes a borrowed socket.
            with self._connection_pool().connection() as connection:
                yield connection
            return
        if self.postgres:
            import psycopg
            from psycopg.rows import dict_row
            connection = psycopg.connect(self.url, row_factory=dict_row, connect_timeout=10)
        else:
            connection = sqlite3.connect(self.path, timeout=15)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA busy_timeout=15000")
            if write:
                connection.execute("BEGIN IMMEDIATE")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def execute(self, connection, sql, params=()):
        return connection.execute(sql.replace("?", "%s") if self.postgres else sql, params)

    def initialize(self):
        sequence = "BIGSERIAL PRIMARY KEY" if self.postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
        statements = [
            "CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, role TEXT NOT NULL, expires_at TEXT NOT NULL)",
            "CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE, tool_id INTEGER NOT NULL, policy TEXT NOT NULL, speed_ms INTEGER NOT NULL, slot_interval INTEGER NOT NULL, state TEXT NOT NULL, generation INTEGER NOT NULL, last_cycle INTEGER NOT NULL DEFAULT 0, eligible_count INTEGER NOT NULL DEFAULT 0, vibration_count INTEGER NOT NULL DEFAULT 0, wire_bytes BIGINT NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
            "CREATE TABLE IF NOT EXISTS readings (run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE, generation INTEGER NOT NULL, cycle INTEGER NOT NULL, payload TEXT NOT NULL, PRIMARY KEY (run_id, generation, cycle))",
            "CREATE TABLE IF NOT EXISTS work_orders (id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE, generation INTEGER NOT NULL, tool_id INTEGER NOT NULL, cycle INTEGER NOT NULL, slot INTEGER NOT NULL, status TEXT NOT NULL, reason TEXT, model_version TEXT, finding TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, UNIQUE(run_id,generation))",
            f"CREATE TABLE IF NOT EXISTS outbox (id {sequence}, run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE, kind TEXT NOT NULL, payload TEXT NOT NULL)",
            "CREATE INDEX IF NOT EXISTS outbox_run_id ON outbox(run_id,id)",
            "CREATE INDEX IF NOT EXISTS runs_state ON runs(state)",
            "CREATE TABLE IF NOT EXISTS service_status (name TEXT PRIMARY KEY, value TEXT NOT NULL)",
        ]
        with self.transaction(write=True) as connection:
            if self.postgres:
                # Serialize schema creation across API, gateway and worker on first boot.
                self.execute(connection, "SELECT pg_advisory_xact_lock(529418, 1)")
            for sql in statements:
                self.execute(connection, sql)
        if not self.postgres:
            with self.transaction() as connection:
                connection.execute("PRAGMA journal_mode=WAL")

    @staticmethod
    def session_id(token):
        return hashlib.sha256(token.encode()).hexdigest()

    def session(self, token):
        if not token:
            return None
        with self.transaction() as connection:
            row = self.execute(connection, "SELECT * FROM sessions WHERE id=? AND expires_at>?", (self.session_id(token), utcnow())).fetchone()
            return dict(row) if row else None

    def create_session(self, token, role="planner"):
        expires = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        owner = self.session_id(token)
        with self.transaction(write=True) as connection:
            if self.postgres:
                self.execute(connection, "LOCK TABLE sessions IN SHARE ROW EXCLUSIVE MODE")
            self.execute(connection, "DELETE FROM sessions WHERE expires_at<?", (utcnow(),))
            self._purge_fresh(connection)
            count = self.execute(connection, "SELECT COUNT(*) AS n FROM sessions").fetchone()["n"]
            if count >= int(os.getenv("PDM_MAX_SESSIONS", "100")):
                raise StoreError("Demo session capacity reached")
            self.execute(connection, "INSERT INTO sessions(id,role,expires_at) VALUES(?,?,?)", (owner, role, expires))
        return {"id": owner, "role": role, "expires_at": expires}

    @staticmethod
    def public_run(row):
        result = dict(row)
        result.pop("session_id", None)
        return result

    def _run(self, connection, run_id, owner=None, lock=False):
        sql = "SELECT * FROM runs WHERE id=?"
        params = [run_id]
        if owner:
            sql += " AND session_id=?"
            params.append(owner)
        if lock and self.postgres:
            sql += " FOR UPDATE"
        return self.execute(connection, sql, params).fetchone()

    def _outbox(self, connection, run_id, kind, data):
        self.execute(connection, "INSERT INTO outbox(run_id,kind,payload) VALUES(?,?,?)", (run_id, kind, json.dumps(data, separators=(",", ":"), allow_nan=False)))

    def create_run(self, owner, tool_id, policy, speed_ms, slot_interval):
        with self.transaction(write=True) as connection:
            # Serialize the owner's quota check in both supported databases.
            lock = " FOR UPDATE" if self.postgres else ""
            session = self.execute(connection, "SELECT id FROM sessions WHERE id=? AND expires_at>?" + lock, (owner, utcnow())).fetchone()
            if not session:
                raise StoreError("Session expired")
            if self.postgres:
                self.execute(connection, "LOCK TABLE runs IN SHARE ROW EXCLUSIVE MODE")
            active = self.execute(connection, "SELECT COUNT(*) AS n FROM runs WHERE session_id=? AND state IN ('running','paused')", (owner,)).fetchone()["n"]
            total = self.execute(connection, "SELECT COUNT(*) AS n FROM runs WHERE session_id=?", (owner,)).fetchone()["n"]
            if active >= 4 or total >= 30:
                raise StoreError("Session limit reached: four active runs and thirty saved runs")
            global_active = self.execute(connection, "SELECT COUNT(*) AS n FROM runs WHERE state IN ('running','paused')").fetchone()["n"]
            if global_active >= int(os.getenv("PDM_MAX_ACTIVE_RUNS", "16")):
                raise StoreError("Demo replay capacity reached")
            now = utcnow()
            run_id = str(uuid.uuid4())
            self.execute(connection, "INSERT INTO runs(id,session_id,tool_id,policy,speed_ms,slot_interval,state,generation,created_at,updated_at) VALUES(?,?,?,?,?,?,'running',1,?,?)", (run_id, owner, tool_id, policy, speed_ms, slot_interval, now, now))
            run = self.public_run(self._run(connection, run_id))
            self._outbox(connection, run_id, "state", run)
            return run

    def get_run(self, run_id, session_id=None):
        with self.transaction() as connection:
            row = self._run(connection, run_id, session_id)
            return self.public_run(row) if row else None

    def list_runs(self, owner):
        with self.transaction() as connection:
            rows = self.execute(connection, "SELECT * FROM runs WHERE session_id=? ORDER BY created_at DESC", (owner,)).fetchall()
            return [self.public_run(row) for row in rows]

    def running_runs(self):
        with self.transaction() as connection:
            rows = self.execute(connection, "SELECT runs.* FROM runs JOIN sessions ON sessions.id=runs.session_id WHERE runs.state='running' AND sessions.expires_at>? ORDER BY runs.created_at", (utcnow(),)).fetchall()
            return [self.public_run(row) for row in rows]

    def control(self, run_id, owner, action):
        if action not in ("pause", "resume", "restart"):
            raise StoreError("Unknown replay command")
        with self.transaction(write=True) as connection:
            if action == "restart":
                lock = " FOR UPDATE" if self.postgres else ""
                session = self.execute(connection, "SELECT id FROM sessions WHERE id=? AND expires_at>?" + lock, (owner, utcnow())).fetchone()
                if not session:
                    raise StoreError("Session expired")
                if self.postgres:
                    self.execute(connection, "LOCK TABLE runs IN SHARE ROW EXCLUSIVE MODE")
            row = self._run(connection, run_id, owner, lock=True)
            if not row:
                return None
            if action == "restart":
                active = self.execute(connection, "SELECT COUNT(*) AS n FROM runs WHERE session_id=? AND state IN ('running','paused') AND id<>?", (owner, run_id)).fetchone()["n"]
                if active >= 4:
                    raise StoreError("Session has four active runs")
                if row["state"] == "completed":
                    global_active = self.execute(connection, "SELECT COUNT(*) AS n FROM runs WHERE state IN ('running','paused')").fetchone()["n"]
                    if global_active >= int(os.getenv("PDM_MAX_ACTIVE_RUNS", "16")):
                        raise StoreError("Demo replay capacity reached")
                self.execute(connection, "UPDATE runs SET state='running',generation=generation+1,last_cycle=0,eligible_count=0,vibration_count=0,wire_bytes=0,updated_at=? WHERE id=?", (utcnow(), run_id))
            elif row["state"] != "completed":
                state = "paused" if action == "pause" else "running"
                self.execute(connection, "UPDATE runs SET state=?,updated_at=? WHERE id=?", (state, utcnow(), run_id))
            run = self.public_run(self._run(connection, run_id))
            self._outbox(connection, run_id, "state", run)
            return run

    def ingest(self, payload, wire_bytes=None):
        """Commit one source cycle and its side effects before MQTT acknowledgement."""
        if not isinstance(payload, dict):
            raise StoreError("Telemetry must be an object")
        event = dict(payload)
        required = ("run_id", "generation", "tool_id", "cycle", "event_type", "quality", "source_version", "replay_at")
        if any(key not in event for key in required) or type(event.get("schema_version")) is not int or event["schema_version"] != 1:
            raise StoreError("Unsupported telemetry contract")
        for key in ("run_id", "source_version", "replay_at"):
            if not isinstance(event[key], str) or not 1 <= len(event[key]) <= 200:
                raise StoreError(f"Invalid {key}")
        for key in ("generation", "tool_id", "cycle"):
            if isinstance(event[key], bool) or not isinstance(event[key], int) or event[key] < 1:
                raise StoreError(f"Invalid {key}")
        if event["event_type"] not in ("cut", "gap", "damage"):
            raise StoreError("Invalid telemetry event type")
        if event["quality"] not in ("ok", "gap", "conflict", "unsupported", "missing"):
            raise StoreError("Invalid telemetry quality")
        try:
            original = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode()
        except (TypeError, ValueError) as error:
            raise StoreError("Telemetry must contain finite JSON values") from error
        if wire_bytes is not None and type(wire_bytes) is not int:
            raise StoreError("Invalid telemetry size")
        event["wire_bytes"] = len(original) if wire_bytes is None else wire_bytes
        if event["wire_bytes"] < 0 or event["wire_bytes"] > 262144:
            raise StoreError("Telemetry packet size outside supported range")
        features = event.get("features", {})
        if not isinstance(features, dict):
            raise StoreError("Features must be an object")
        current = features.get("current", {})
        vibration = features.get("vibration", {})
        if not isinstance(current, dict) or not isinstance(vibration, dict):
            raise StoreError("Feature channels must be objects")
        eligible = event["event_type"] == "cut" and bool(current)
        released = event.get("vibration_released", False)
        if type(released) is not bool:
            raise StoreError("Vibration release flag must be boolean")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for features in (current, vibration) for value in features.values()):
            raise StoreError("Feature values must be finite numbers")
        if released != bool(vibration) or released and not eligible:
            raise StoreError("Vibration release requires current and optional evidence")
        if event["event_type"] != "cut" and (current or vibration):
            raise StoreError("Gap and damage events cannot carry inference features")
        decision = event.get("decision")
        if decision is None:
            decision = {}
        if not isinstance(decision, dict):
            raise StoreError("Decision must be an object")
        if decision:
            if decision.get("status") not in ("monitor", "inspect", "insufficient_evidence", "no_feasible_slot", "deferred"):
                raise StoreError("Invalid decision status")
            if event["event_type"] != "cut":
                raise StoreError("Gap and damage events cannot carry model decisions")
            for field in ("risk", "actionable_risk"):
                value = decision.get(field)
                if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1):
                    raise StoreError("Decision risks must be finite probabilities")
            for field in ("reason", "model_version"):
                value = decision.get(field)
                if value is not None and (not isinstance(value, str) or len(value) > 2000):
                    raise StoreError(f"Invalid decision {field}")
        if decision.get("status") == "inspect" and (not eligible or type(decision.get("slot")) is not int or decision["slot"] <= event["cycle"]):
            raise StoreError("Inspection requires current evidence and a future slot")
        event["received_at"] = utcnow()
        with self.transaction(write=True) as connection:
            row = self._run(connection, event["run_id"], lock=True)
            if not row or row["generation"] != event["generation"] or row["state"] == "completed":
                return False
            if row["tool_id"] != event["tool_id"]:
                raise StoreError("Telemetry cutter differs from run")
            if event["cycle"] <= row["last_cycle"]:
                return False
            if event["cycle"] != row["last_cycle"] + 1:
                raise StoreError("Replay must record every source cycle, including gaps")
            count = row["eligible_count"] + int(eligible)
            releases = row["vibration_count"] + int(released)
            if row["policy"] in ("decision", "periodic") and releases > count // 4:
                raise StoreError("Vibration release exceeds the prefix budget")
            if row["policy"] == "current" and released:
                raise StoreError("Current-only run cannot release vibration")
            self.execute(connection, "INSERT INTO readings(run_id,generation,cycle,payload) VALUES(?,?,?,?)", (row["id"], row["generation"], event["cycle"], json.dumps(event, separators=(",", ":"), allow_nan=False)))
            state = "completed" if event["event_type"] == "damage" else row["state"]
            self.execute(connection, "UPDATE runs SET last_cycle=?,eligible_count=?,vibration_count=?,wire_bytes=wire_bytes+?,state=?,updated_at=? WHERE id=?", (event["cycle"], count, releases, event["wire_bytes"], state, event["received_at"], row["id"]))
            self._outbox(connection, row["id"], "reading", event)
            if decision.get("status") == "inspect":
                existing = self.execute(connection, "SELECT id FROM work_orders WHERE run_id=? AND generation=?", (row["id"], row["generation"])).fetchone()
                if not existing:
                    order = {"id": str(uuid.uuid4()), "run_id": row["id"], "generation": row["generation"], "tool_id": row["tool_id"], "cycle": event["cycle"], "slot": decision["slot"], "status": "draft", "reason": decision.get("reason"), "model_version": decision.get("model_version"), "finding": None, "created_at": event["received_at"], "updated_at": event["received_at"]}
                    self.execute(connection, "INSERT INTO work_orders(id,run_id,generation,tool_id,cycle,slot,status,reason,model_version,finding,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", tuple(order.values()))
                    self._outbox(connection, row["id"], "work_order", order)
            self._outbox(connection, row["id"], "state", self.public_run(self._run(connection, row["id"])))
            self._status(connection, "last_ingest_at", event["received_at"])
        return True

    def snapshot(self, run_id, owner):
        with self.transaction(write=True) as connection:
            row = self._run(connection, run_id, owner)
            if not row:
                return None
            # The run lock prevents a reading being committed between state and history.
            if self.postgres:
                row = self._run(connection, run_id, owner, lock=True)
            params = (run_id, row["generation"])
            readings = self.execute(connection, "SELECT payload FROM readings WHERE run_id=? AND generation=? ORDER BY cycle", params).fetchall()
            orders = self.execute(connection, "SELECT * FROM work_orders WHERE run_id=? AND generation=? ORDER BY created_at", params).fetchall()
            cursor = self.execute(connection, "SELECT COALESCE(MAX(id),0) AS id FROM outbox WHERE run_id=?", (run_id,)).fetchone()["id"]
            return {"run": self.public_run(row), "readings": [json.loads(item["payload"]) for item in readings], "work_orders": [dict(order) for order in orders], "cursor": cursor}

    def events(self, run_id, owner, after, limit=100):
        with self.transaction() as connection:
            if not self._run(connection, run_id, owner):
                return None
            rows = self.execute(connection, "SELECT id,kind,payload FROM outbox WHERE run_id=? AND id>? ORDER BY id LIMIT ?", (run_id, after, limit)).fetchall()
            return [{"id": row["id"], "kind": row["kind"], "data": json.loads(row["payload"])} for row in rows]

    def work_order(self, run_id, owner, order_id, action, finding=None):
        transitions = {"approve": ("draft", "approved"), "dismiss": ("draft", "dismissed"), "complete": ("approved", "completed")}
        if action not in transitions:
            raise StoreError("Unknown work-order action")
        with self.transaction(write=True) as connection:
            run = self._run(connection, run_id, owner, lock=True)
            if not run:
                return None
            row = self.execute(connection, "SELECT * FROM work_orders WHERE id=? AND run_id=? AND generation=?", (order_id, run_id, run["generation"])).fetchone()
            if not row:
                return None
            previous, target = transitions[action]
            if row["status"] == target:
                return dict(row)
            if row["status"] != previous:
                raise StoreError(f"Cannot {action} a {row['status']} work order")
            self.execute(connection, "UPDATE work_orders SET status=?,finding=?,updated_at=? WHERE id=?", (target, finding if finding is not None else row["finding"], utcnow(), order_id))
            order = dict(self.execute(connection, "SELECT * FROM work_orders WHERE id=?", (order_id,)).fetchone())
            self._outbox(connection, run_id, "work_order", order)
            return order

    def _status(self, connection, name, value):
        self.execute(connection, "INSERT INTO service_status(name,value) VALUES(?,?) ON CONFLICT(name) DO UPDATE SET value=excluded.value", (name, value))

    def status(self, name, value):
        with self.transaction(write=True) as connection:
            self._status(connection, name, value)

    def health(self):
        with self.transaction() as connection:
            rows = self.execute(connection, "SELECT name,value FROM service_status").fetchall()
            return {row["name"]: row["value"] for row in rows}

    def cleanup(self):
        with self.transaction(write=True) as connection:
            self.execute(connection, "DELETE FROM sessions WHERE expires_at<?", (utcnow(),))
            self._purge_fresh(connection)

    def _purge_fresh(self, connection):
        # Gateway/worker also run before optional feature schemas are installed.
        for table in ("fresh_assessments", "fresh_conflicts"):
            sql = "SELECT to_regclass(?) AS name" if self.postgres else "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            row = self.execute(connection, sql, (table,)).fetchone()
            if row and row["name"]:
                self.execute(connection, f"DELETE FROM {table} WHERE owner NOT IN (SELECT id FROM sessions)")

    def metrics(self):
        with self.transaction() as connection:
            runs = self.execute(connection, "SELECT COUNT(*) AS runs,COALESCE(SUM(eligible_count),0) AS cuts,COALESCE(SUM(vibration_count),0) AS releases,COALESCE(SUM(wire_bytes),0) AS bytes FROM runs").fetchone()
            return dict(runs)
