"""Durable measured-cut inbox; persistence is not inference or qualification.

Registry mutators are trusted administration calls, never device-facing routes.
The caller must authorize administrators and bound HTTP bodies before decoding.
"""
from datetime import datetime, timezone
import hashlib
import hmac
import json
import math
import secrets
import uuid

from pdm.dataset import NUMERIC_CONTEXT
from pdm.store import StoreError, utcnow

MAX_PAYLOAD_BYTES = 65536
MAX_SEQUENCE = 2**63 - 1


class DeviceAuthError(StoreError):
    pass


def _identifier(value, field):
    if not isinstance(value, str) or not 1 <= len(value) <= 100 or any(ord(c) < 32 for c in value):
        raise StoreError(f"Invalid {field}")
    return value


def _canonical(envelope):
    try:
        content = json.dumps(envelope, sort_keys=True, separators=(",", ":"), allow_nan=False)
        size = len(content.encode("utf-8"))
    except (ValueError, TypeError, RecursionError, UnicodeError) as error:
        raise StoreError("Envelope must contain finite JSON values") from error
    if size > MAX_PAYLOAD_BYTES:
        raise StoreError("Envelope exceeds 65536 bytes")
    return content


def _validate(envelope):
    if not isinstance(envelope, dict) or set(envelope) != {"schema_version", "boot_id", "sequence", "event"}:
        raise StoreError("Expected schema_version, boot_id, sequence and event")
    if type(envelope["schema_version"]) is not int or envelope["schema_version"] != 1:
        raise StoreError("Unsupported envelope schema_version")
    _identifier(envelope["boot_id"], "boot_id")
    if type(envelope["sequence"]) is not int or not 1 <= envelope["sequence"] <= MAX_SEQUENCE:
        raise StoreError("sequence must be a positive signed 64-bit integer")
    event = envelope["event"]
    required = {"event_id", "asset_id", "tool_life_id", "sequence_number", "cut_completed_at", "source_mode",
                "feature_schema_version", "sensor_profile_version", "context", "features", "clock_basis", "data_origin"}
    if not isinstance(event, dict) or required - set(event) or set(event) - required - {"inspection_breaks"}:
        raise StoreError("Invalid completed-cut event fields")
    for key in ("event_id", "asset_id", "tool_life_id", "feature_schema_version", "sensor_profile_version"):
        _identifier(event[key], key)
    if (event["data_origin"], event["clock_basis"], event["source_mode"]) != ("user-measured", "observed", "uploaded"):
        raise StoreError("Device inbox requires declared user-measured, observed, uploaded evidence")
    cycle = event["sequence_number"]
    if type(cycle) is not int or not 1 <= cycle <= 100000:
        raise StoreError("Invalid cut sequence_number")
    try:
        cutoff = datetime.fromisoformat(event["cut_completed_at"].replace("Z", "+00:00"))
        if cutoff.tzinfo is None or (cutoff - datetime.now(timezone.utc)).total_seconds() > 60:
            raise ValueError()
    except (ValueError, TypeError, AttributeError, OverflowError) as error:
        raise StoreError("cut_completed_at requires a timezone and at most 60 seconds future skew") from error
    context, features = event["context"], event["features"]
    if not isinstance(context, dict) or set(context) != set(NUMERIC_CONTEXT) or context["NumberOfCycle"] != cycle:
        raise StoreError("Invalid context or mismatched cut ordinal")
    if not isinstance(features, dict) or not 1 <= len(features) <= 256:
        raise StoreError("Provide 1..256 measured feature fields")
    if set(features) & set(NUMERIC_CONTEXT):
        raise StoreError("Feature names must not overlap context fields")
    for key, value in list(context.items()) + list(features.items()):
        _identifier(key, "measurement name")
        if type(value) not in (int, float) or not math.isfinite(value) or abs(value) > 1e12:
            raise StoreError("Measurements must be finite numbers within transport limits")
    breaks = event.get("inspection_breaks", [])
    if not isinstance(breaks, list) or len(breaks) > 100 or any(type(n) is not int or not cycle < n <= 100000 for n in breaks):
        raise StoreError("Invalid future inspection ordinals")


class DeviceIngest:
    def __init__(self, store):
        self.store = store

    def initialize(self):
        statements = [
            "CREATE TABLE IF NOT EXISTS ingest_devices (id TEXT PRIMARY KEY, org_id TEXT NOT NULL, site_id TEXT NOT NULL, asset_id TEXT NOT NULL, token_hash TEXT NOT NULL, revoked_at TEXT, created_at TEXT NOT NULL)",
            "CREATE TABLE IF NOT EXISTS ingest_boots (device_id TEXT NOT NULL REFERENCES ingest_devices(id), boot_id TEXT NOT NULL, high_sequence BIGINT NOT NULL, PRIMARY KEY(device_id,boot_id))",
            "CREATE TABLE IF NOT EXISTS ingest_receipts (id TEXT PRIMARY KEY, device_id TEXT NOT NULL REFERENCES ingest_devices(id), org_id TEXT NOT NULL, site_id TEXT NOT NULL, asset_id TEXT NOT NULL, boot_id TEXT NOT NULL, sequence BIGINT NOT NULL, digest TEXT NOT NULL, envelope TEXT NOT NULL, sequence_status TEXT NOT NULL, missing_before BIGINT NOT NULL, received_at TEXT NOT NULL, UNIQUE(device_id,boot_id,sequence))",
            "CREATE TABLE IF NOT EXISTS ingest_quarantine (id TEXT PRIMARY KEY, receipt_id TEXT NOT NULL REFERENCES ingest_receipts(id), digest TEXT NOT NULL, envelope TEXT NOT NULL, received_at TEXT NOT NULL, UNIQUE(receipt_id,digest))",
            "CREATE INDEX IF NOT EXISTS ingest_receipts_scope ON ingest_receipts(org_id,site_id,asset_id,received_at)",
        ]
        with self.store.transaction(write=True) as connection:
            if self.store.postgres:
                self.store.execute(connection, "SELECT pg_advisory_xact_lock(529418, 3)")
            for statement in statements:
                self.store.execute(connection, statement)

    @staticmethod
    def _token(device_id):
        token = device_id + "." + secrets.token_urlsafe(32)
        return token, hashlib.sha256(token.encode()).hexdigest()

    def register_device(self, org_id, site_id, asset_id):
        """Trusted admin only: immutable server-side scope, one-time token return."""
        for key, value in (("org_id", org_id), ("site_id", site_id), ("asset_id", asset_id)):
            _identifier(value, key)
        device_id = uuid.uuid4().hex
        token, digest = self._token(device_id)
        with self.store.transaction(write=True) as connection:
            self.store.execute(connection, "INSERT INTO ingest_devices(id,org_id,site_id,asset_id,token_hash,created_at) VALUES(?,?,?,?,?,?)",
                               (device_id, org_id, site_id, asset_id, digest, utcnow()))
        return {"device_id": device_id, "org_id": org_id, "site_id": site_id, "asset_id": asset_id, "token": token}

    def _authenticate(self, connection, token, lock=False):
        if not isinstance(token, str) or not 1 <= len(token) <= 200 or not token.isascii():
            raise DeviceAuthError("Invalid device credential")
        device_id = token.split(".", 1)[0]
        suffix = " FOR UPDATE" if lock and self.store.postgres else ""
        row = self.store.execute(connection, "SELECT * FROM ingest_devices WHERE id=?" + suffix, (device_id,)).fetchone()
        supplied = hashlib.sha256(token.encode()).hexdigest()
        valid = hmac.compare_digest(supplied, row["token_hash"] if row else "0" * 64)
        if not valid or row is None or row["revoked_at"] is not None:
            raise DeviceAuthError("Invalid device credential")
        return row

    def authenticate(self, token):
        with self.store.transaction() as connection:
            row = self._authenticate(connection, token)
            return {key: row[key] for key in ("id", "org_id", "site_id", "asset_id")}

    def rotate_token(self, device_id):
        """Trusted admin only; revoked devices cannot be silently re-enabled."""
        _identifier(device_id, "device_id")
        token, digest = self._token(device_id)
        with self.store.transaction(write=True) as connection:
            changed = self.store.execute(connection, "UPDATE ingest_devices SET token_hash=? WHERE id=? AND revoked_at IS NULL", (digest, device_id))
            if changed.rowcount != 1:
                raise StoreError("Active device not found")
        return token

    def revoke_device(self, device_id):
        """Trusted admin only; revocation serialized with in-flight ingestion."""
        _identifier(device_id, "device_id")
        with self.store.transaction(write=True) as connection:
            changed = self.store.execute(connection, "UPDATE ingest_devices SET revoked_at=? WHERE id=?", (utcnow(), device_id))
            if changed.rowcount != 1:
                raise StoreError("Device not found")

    @staticmethod
    def _receipt(row, status="persisted", quarantine_id=None):
        result = {key: row[key] for key in ("id", "device_id", "org_id", "site_id", "asset_id", "boot_id", "sequence", "digest", "sequence_status", "missing_before", "received_at")}
        result.update(status=status, inference_status="not_started")
        if quarantine_id:
            result["quarantine_id"] = quarantine_id
        return result

    def ingest(self, token, envelope):
        # Authenticate first, then snapshot the JSON to avoid mutable caller races.
        self.authenticate(token)
        content = _canonical(envelope)
        envelope = json.loads(content)
        _validate(envelope)
        digest = hashlib.sha256(content.encode()).hexdigest()
        boot_id, sequence = envelope["boot_id"], envelope["sequence"]
        with self.store.transaction(write=True) as connection:
            device = self._authenticate(connection, token, lock=True)
            if envelope["event"]["asset_id"] != device["asset_id"]:
                raise StoreError("Event asset does not match provisioned device scope")
            params = (device["id"], boot_id, sequence)
            existing = self.store.execute(connection, "SELECT * FROM ingest_receipts WHERE device_id=? AND boot_id=? AND sequence=?", params).fetchone()
            if existing:
                if hmac.compare_digest(digest, existing["digest"]):
                    return self._receipt(existing, "duplicate")
                quarantine = self.store.execute(connection, "SELECT id FROM ingest_quarantine WHERE receipt_id=? AND digest=?", (existing["id"], digest)).fetchone()
                quarantine_id = quarantine["id"] if quarantine else uuid.uuid4().hex
                if not quarantine:
                    self.store.execute(connection, "INSERT INTO ingest_quarantine(id,receipt_id,digest,envelope,received_at) VALUES(?,?,?,?,?)", (quarantine_id, existing["id"], digest, content, utcnow()))
                return self._receipt(existing, "quarantined", quarantine_id)
            boot = self.store.execute(connection, "SELECT high_sequence FROM ingest_boots WHERE device_id=? AND boot_id=?", params[:2]).fetchone()
            high = boot["high_sequence"] if boot else 0
            status = "out_of_order" if sequence <= high else "gap" if sequence > high + 1 else "contiguous"
            row = dict(id=uuid.uuid4().hex, device_id=device["id"], org_id=device["org_id"], site_id=device["site_id"], asset_id=device["asset_id"], boot_id=boot_id, sequence=sequence, digest=digest, envelope=content, sequence_status=status, missing_before=max(0, sequence - high - 1), received_at=utcnow())
            keys = tuple(row)
            self.store.execute(connection, "INSERT INTO ingest_receipts(" + ",".join(keys) + ") VALUES(" + ",".join("?" for _ in keys) + ")", tuple(row.values()))
            if boot:
                self.store.execute(connection, "UPDATE ingest_boots SET high_sequence=? WHERE device_id=? AND boot_id=?", (max(sequence, high), *params[:2]))
            else:
                self.store.execute(connection, "INSERT INTO ingest_boots(device_id,boot_id,high_sequence) VALUES(?,?,?)", params)
            return self._receipt(row)

    def get_receipt(self, token, receipt_id):
        """Device-scoped receipt and original evidence; no cross-device lookup."""
        _identifier(receipt_id, "receipt_id")
        with self.store.transaction() as connection:
            device = self._authenticate(connection, token)
            row = self.store.execute(connection, "SELECT * FROM ingest_receipts WHERE id=? AND device_id=?", (receipt_id, device["id"])).fetchone()
            if row is None:
                return None
            return {**self._receipt(row), "envelope": json.loads(row["envelope"])}
