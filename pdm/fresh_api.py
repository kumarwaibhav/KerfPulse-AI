"""Session-scoped, persistent assessment and optimistic human review."""
from datetime import datetime, timezone
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from pdm.fresh_model import assess, input_schema, InputError


def initialize_fresh(store):
    with store.transaction(write=True) as connection:
        if store.postgres:
            store.execute(connection, "SELECT pg_advisory_xact_lock(529418, 2)")
        store.execute(connection, "CREATE TABLE IF NOT EXISTS fresh_assessments (id TEXT PRIMARY KEY, owner TEXT NOT NULL, event_id TEXT NOT NULL, digest TEXT NOT NULL, payload TEXT NOT NULL, evidence TEXT NOT NULL, UNIQUE(owner,event_id))")
        # Additive upgrade retains assessments created before the ordered-history column.
        columns = store.execute(connection, "SELECT column_name AS name FROM information_schema.columns WHERE table_schema='public' AND table_name='fresh_assessments'").fetchall() if store.postgres else connection.execute("PRAGMA table_info(fresh_assessments)").fetchall()
        if "created_at" not in {row["name"] for row in columns}:
            store.execute(connection, "ALTER TABLE fresh_assessments ADD COLUMN created_at TEXT NOT NULL DEFAULT ''")
            for row in store.execute(connection, "SELECT id,payload FROM fresh_assessments").fetchall():
                store.execute(connection, "UPDATE fresh_assessments SET created_at=? WHERE id=?", (json.loads(row["payload"])["arrived_at"], row["id"]))
        store.execute(connection, "CREATE INDEX IF NOT EXISTS fresh_owner_history ON fresh_assessments(owner,created_at,id)")
        store.execute(connection, "CREATE TABLE IF NOT EXISTS fresh_conflicts (id TEXT PRIMARY KEY, owner TEXT NOT NULL, event_id TEXT NOT NULL, assessment_id TEXT NOT NULL, digest TEXT NOT NULL, evidence TEXT NOT NULL, arrived_at TEXT NOT NULL, UNIQUE(owner,event_id,digest))")
        # Demo records share the session retention boundary, including tables created by older versions.
        for table in ("fresh_assessments", "fresh_conflicts"):
            store.execute(connection, f"DELETE FROM {table} WHERE owner NOT IN (SELECT id FROM sessions)")


class Batch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    events: list[dict] = Field(min_length=1, max_length=30)


class Review(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str
    expected_version: int = Field(ge=1, strict=True)
    finding: str | None = Field(default=None, max_length=2000)


def build_router(store, session, planner):
    router = APIRouter(prefix="/api/fresh")

    def get(connection, owner, key):
        row = store.execute(connection, "SELECT * FROM fresh_assessments WHERE owner=? AND id=?", (owner, key)).fetchone()
        if row is None:
            raise HTTPException(404, "Assessment not found")
        return row

    @router.get("/schema")
    def schema(owner=Depends(session)):
        return input_schema()

    @router.post("/assessments")
    def upload(body: Batch, owner=Depends(planner)):
        results = []
        for index, event in enumerate(body.events, 1):
            try:
                result = assess(event)
                with store.transaction(write=True) as connection:
                    if store.postgres:
                        store.execute(connection, "SELECT pg_advisory_xact_lock(hashtext(?))", (owner["id"],))
                    row = store.execute(connection, "SELECT * FROM fresh_assessments WHERE owner=? AND event_id=?", (owner["id"], event["event_id"])).fetchone()
                    if row:
                        if row["digest"] != result["evidence_digest"]:
                            existing = store.execute(connection, "SELECT id FROM fresh_conflicts WHERE owner=? AND event_id=? AND digest=?", (owner["id"], event["event_id"], result["evidence_digest"])).fetchone()
                            key = existing["id"] if existing else str(uuid.uuid4())
                            count = store.execute(connection, "SELECT count(*) AS n FROM fresh_conflicts WHERE owner=?", (owner["id"],)).fetchone()["n"]
                            if not existing and count >= 100:
                                raise InputError("event_id", "Conflict quarantine is full; original evidence retained. No conflicting effect accepted.")
                            if not existing:
                                store.execute(connection, "INSERT INTO fresh_conflicts(id,owner,event_id,assessment_id,digest,evidence,arrived_at) VALUES(?,?,?,?,?,?,?)", (key, owner["id"], event["event_id"], row["id"], result["evidence_digest"], json.dumps(event), datetime.now(timezone.utc).isoformat()))
                            results.append({"row": index, "quarantine_id": key, "errors": [{"field": "event_id", "message": "Conflicting duplicate quarantined. Original assessment retained."}]})
                            continue
                        result = json.loads(row["payload"])
                    else:
                        count = store.execute(connection, "SELECT count(*) AS n FROM fresh_assessments WHERE owner=?", (owner["id"],)).fetchone()["n"]
                        if count >= 300:
                            raise InputError("events", "Session assessment limit is 300")
                        result["id"] = str(uuid.uuid4())
                        status = "draft" if result["action"] == "review_recommended" else "not_requested"
                        result["review"] = {"status": status, "version": 1, "history": []}
                        store.execute(connection, "INSERT INTO fresh_assessments(id,owner,event_id,digest,payload,evidence,created_at) VALUES(?,?,?,?,?,?,?)", (result["id"], owner["id"], event["event_id"], result["evidence_digest"], json.dumps(result), json.dumps(event), result["arrived_at"]))
                results.append({"row": index, "assessment": result})
            except ValueError as error:
                results.append({"row": index, "errors": [{"field": getattr(error, "field", "event"), "message": str(error)}]})
        return {"results": results}

    @router.get("/assessments")
    def history(owner=Depends(session)):
        with store.transaction() as connection:
            rows = store.execute(connection, "SELECT payload FROM fresh_assessments WHERE owner=? ORDER BY created_at DESC,id DESC", (owner["id"],)).fetchall()
            return [json.loads(row["payload"]) for row in rows]

    @router.get("/conflicts")
    def conflicts(owner=Depends(session)):
        with store.transaction() as connection:
            rows = store.execute(connection, "SELECT * FROM fresh_conflicts WHERE owner=? ORDER BY arrived_at DESC", (owner["id"],)).fetchall()
            return [{key: json.loads(value) if key == "evidence" else value for key, value in dict(row).items() if key != "owner"} for row in rows]

    @router.get("/assessments/{key}")
    def detail(key: str, owner=Depends(session)):
        with store.transaction() as connection:
            return json.loads(get(connection, owner["id"], key)["payload"])

    @router.get("/assessments/{key}/export")
    def export(key: str, owner=Depends(session)):
        with store.transaction() as connection:
            row = get(connection, owner["id"], key)
            return {"assessment": json.loads(row["payload"]), "evidence": json.loads(row["evidence"])}

    @router.post("/assessments/{key}/review")
    def review(key: str, body: Review, owner=Depends(planner)):
        transitions = {"approve": ("draft", "approved"), "dismiss": ("draft", "dismissed"), "complete": ("approved", "completed")}
        if body.action not in transitions:
            raise HTTPException(422, "Unknown review action")
        if body.action == "complete" and not (body.finding and body.finding.strip()):
            raise HTTPException(422, "Record a finding and its source")
        with store.transaction(write=True) as connection:
            if store.postgres:
                store.execute(connection, "SELECT pg_advisory_xact_lock(hashtext(?))", (owner["id"],))
            row = get(connection, owner["id"], key)
            result = json.loads(row["payload"])
            state = result["review"]
            previous, target = transitions[body.action]
            if state["version"] != body.expected_version or state["status"] != previous:
                raise HTTPException(409, "Review changed. Reload the assessment.")
            state.update(status=target, version=state["version"] + 1)
            state["history"].append({"action": body.action, "actor": owner["id"][:12], "at": datetime.now(timezone.utc).isoformat(), "finding": body.finding})
            store.execute(connection, "UPDATE fresh_assessments SET payload=? WHERE id=? AND owner=?", (json.dumps(result), key, owner["id"]))
            return result

    return router
