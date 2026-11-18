"""Same-origin dashboard API and durable replay event stream."""

import asyncio
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import secrets
import time

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from typing import Literal

from pdm import dataset
from pdm.store import Store, StoreError
from pdm.fresh_api import build_router, initialize_fresh
from pdm.device_ingest import DeviceIngest
from pdm.device_api import router_for
from pdm.identity import IdentityStore
from pdm.oidc import routes as identity_routes
from pdm.operations_api import routes as operations_routes


COOKIE = "pdm_session"


class BodyLimitMiddleware:
    """Bound API mutation bodies before JSON parsing, including chunked requests."""

    def __init__(self, app, max_bytes=65536):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in ("POST", "PUT", "PATCH", "DELETE") or not scope["path"].startswith("/api/"):
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        try:
            length = int(headers.get(b"content-length", b"0"))
            if length < 0:
                raise ValueError("Negative length")
        except ValueError:
            return await JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)(scope, receive, send)
        if length > self.max_bytes:
            return await JSONResponse({"detail": "Request body exceeds 64 KiB"}, status_code=413)(scope, receive, send)
        chunks = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > self.max_bytes:
                return await JSONResponse({"detail": "Request body exceeds 64 KiB"}, status_code=413)(scope, receive, send)
            chunks.append(chunk)
            if not message.get("more_body", False):
                break
        body = b"".join(chunks)
        supplied = False

        async def bounded_receive():
            nonlocal supplied
            if supplied:
                return await receive()
            supplied = True
            return {"type": "http.request", "body": body, "more_body": False}

        await self.app(scope, bounded_receive, send)


class RunInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_id: StrictInt
    policy: Literal["decision", "periodic", "current", "fused"] = "decision"
    speed_ms: int = Field(default=500, ge=100, le=10000, strict=True)
    slot_interval: int = Field(default=3, ge=1, le=3, strict=True)


class OrderInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    finding: str | None = Field(default=None, max_length=2000)


def create_app(database_url=None, *, oidc_provider_factory=None):
    store = Store(database_url)
    devices = DeviceIngest(store)
    identity = IdentityStore(store)
    streams = {}

    @asynccontextmanager
    async def lifespan(app):
        store.initialize()
        initialize_fresh(store)
        devices.initialize()
        identity.initialize()
        try:
            yield
        finally:
            store.close()

    app = FastAPI(title="KerfPulse replay API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(BodyLimitMiddleware)
    app.state.store = store
    app.state.devices = devices
    app.state.identity = identity
    app.include_router(router_for(devices))
    auth_router, named_person = identity_routes(identity,oidc_provider_factory)
    app.include_router(auth_router)
    app.include_router(operations_routes(store,named_person))

    @app.middleware("http")
    async def boundary(request, call_next):
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            origin = request.headers.get("origin")
            allowed = {str(request.base_url).rstrip("/")}
            allowed.update(item.strip().rstrip("/") for item in os.getenv("PDM_ALLOWED_ORIGINS", "").split(",") if item.strip())
            if request.headers.get("sec-fetch-site") == "cross-site" or origin and origin.rstrip("/") not in allowed:
                return JSONResponse({"detail": "Request origin is not allowed"}, status_code=403)
            if request.url.path.startswith("/api/") and request.headers.get("content-type", "").split(";")[0] != "application/json":
                return JSONResponse({"detail": "JSON content type required"}, status_code=415)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(StoreError)
    async def store_error(request, error):
        return JSONResponse({"detail": str(error)}, status_code=409)

    def session(request: Request):
        result = store.session(request.cookies.get(COOKIE))
        if result is None:
            raise HTTPException(401, "Start a dashboard session first")
        return result

    def planner(owner=Depends(session)):
        # Role is also enforced at request time so changing deployment mode takes effect immediately.
        if owner["role"] != "planner" or os.getenv("PDM_DEMO_ROLE", "planner") == "viewer":
            raise HTTPException(403, "This session has viewer access")
        return owner

    app.include_router(build_router(store, session, planner))

    @app.get("/api/session")
    def open_session(request: Request, response: Response):
        owner = store.session(request.cookies.get(COOKIE))
        if owner is None:
            token = secrets.token_urlsafe(32)
            role = "viewer" if os.getenv("PDM_DEMO_ROLE") == "viewer" else "planner"
            owner = store.create_session(token, role)
            secure = os.getenv("PDM_SECURE_COOKIE", "").lower() == "true" or request.url.scheme == "https"
            response.set_cookie(COOKIE, token, max_age=86400, httponly=True, secure=secure, samesite="strict", path="/")
        return {"role": "viewer" if os.getenv("PDM_DEMO_ROLE") == "viewer" else owner["role"]}

    @app.get("/api/tools")
    def tools(owner=Depends(session)):
        try:
            return dataset.list_tools()
        except dataset.DatasetError as error:
            raise HTTPException(503, str(error)) from error

    @app.get("/api/runs")
    def runs(owner=Depends(session)):
        return store.list_runs(owner["id"])

    @app.post("/api/runs", status_code=201)
    def start(body: RunInput, owner=Depends(planner)):
        try:
            valid = {tool["tool_id"] for tool in dataset.list_tools()}
        except dataset.DatasetError as error:
            raise HTTPException(503, str(error)) from error
        if body.tool_id not in valid:
            raise HTTPException(422, "Unknown source cutter")
        return store.create_run(owner["id"], **body.model_dump())

    @app.get("/api/runs/{run_id}")
    def snapshot(run_id: str, owner=Depends(session)):
        result = store.snapshot(run_id, owner["id"])
        if result is None:
            raise HTTPException(404, "Run not found")
        return result

    @app.post("/api/runs/{run_id}/{action}")
    def control(run_id: str, action: Literal["pause", "resume", "restart"], owner=Depends(planner)):
        result = store.control(run_id, owner["id"], action)
        if result is None:
            raise HTTPException(404, "Run not found")
        return result

    @app.post("/api/runs/{run_id}/work-orders/{order_id}/{action}")
    def order(run_id: str, order_id: str, action: Literal["approve", "dismiss", "complete"], body: OrderInput, owner=Depends(planner)):
        result = store.work_order(run_id, owner["id"], order_id, action, body.finding)
        if result is None:
            raise HTTPException(404, "Work order not found")
        return result

    @app.get("/api/runs/{run_id}/events")
    async def events(run_id: str, request: Request, after: int = Query(default=0, ge=0, le=9223372036854775807), owner=Depends(session)):
        if await asyncio.to_thread(store.get_run, run_id, owner["id"]) is None:
            raise HTTPException(404, "Run not found")
        header = request.headers.get("last-event-id")
        try:
            cursor = int(header) if header is not None else after
            if not 0 <= cursor <= 9223372036854775807:
                raise ValueError("Cursor outside database integer range")
        except ValueError as error:
            raise HTTPException(400, "Invalid event cursor") from error
        if streams.get(owner["id"], 0) >= 4:
            raise HTTPException(429, "Session has four open event streams")
        streams[owner["id"]] = streams.get(owner["id"], 0) + 1

        async def stream():
            nonlocal cursor
            ping_at = time.monotonic()
            try:
                while not await request.is_disconnected():
                    if await asyncio.to_thread(store.session, request.cookies.get(COOKIE)) is None:
                        return
                    batch = await asyncio.to_thread(store.events, run_id, owner["id"], cursor)
                    if batch is None:
                        return
                    for item in batch:
                        cursor = item["id"]
                        data = json.dumps({"kind": item["kind"], "data": item["data"]}, separators=(",", ":"))
                        yield f"id: {cursor}\nevent: update\ndata: {data}\n\n"
                    if time.monotonic() - ping_at > 15:
                        yield ": keep-alive\n\n"
                        ping_at = time.monotonic()
                    await asyncio.sleep(0.25)
            finally:
                streams[owner["id"]] -= 1
                if streams[owner["id"]] == 0:
                    del streams[owner["id"]]

        return StreamingResponse(stream(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache, no-store"})

    @app.get("/api/runs/{run_id}/export")
    def export(run_id: str, owner=Depends(session)):
        result = store.snapshot(run_id, owner["id"])
        if result is None:
            raise HTTPException(404, "Run not found")
        result["provenance"] = {"doi": dataset.SOURCE_VERSION, "sha256": dataset.SOURCE_SHA256, "license": "CC BY 4.0", "creators": "Grzegorz Piecuch and Tomasz Żabiński", "source_url": dataset.SOURCE_URL, "mode": "Recorded telemetry replay", "transformation": "Completed-cycle statistics with conflicting duplicate quarantined and source gaps retained"}
        result["interpretation"] = "Inspection drafts are replay decisions. Operator findings are manually entered observations. Damage prevention and commercial savings require a field trial."
        return JSONResponse(result, headers={"Content-Disposition": f'attachment; filename="kerfpulse-{run_id}.json"'})

    @app.get("/api/evaluation")
    def evaluation(owner=Depends(session)):
        directory = Path(os.getenv("PDM_MODEL_DIR", "artifacts/nested-workpiece"))
        try:
            report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
            policy = json.loads((directory / "policy-benchmark.json").read_text(encoding="utf-8"))
            return {"report": report, "policy": policy, "source": dataset.audit()}
        except (OSError, ValueError, dataset.DatasetError) as error:
            raise HTTPException(404, "Evaluation artifact is not available") from error

    @app.get("/healthz")
    def health():
        try:
            service = store.health()
        except Exception:
            return JSONResponse({"status": "unavailable"}, status_code=503)
        directory = Path(os.getenv("PDM_MODEL_DIR", "artifacts/nested-workpiece"))
        return {"status": "ok", "database": "postgresql" if store.postgres else "sqlite", "mqtt": service, "dataset": dataset.source_path().is_file(), "model": (directory / "models.json").is_file()}

    @app.get("/metrics")
    def metrics():
        values = store.metrics()
        names = {"runs": "pdm_saved_runs", "cuts": "pdm_accepted_cuts", "releases": "pdm_optional_vibration_releases", "bytes": "pdm_ingested_payload_bytes"}
        content = "".join(f"# TYPE {name} gauge\n{name} {values[key]}\n" for key, name in names.items())
        return Response(content, media_type="text/plain; version=0.0.4")

    static = Path(os.getenv("PDM_WEB_DIR", "web/dist"))
    if (static / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=static / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def index(path: str):
        if path.startswith(("api/", "assets/")):
            raise HTTPException(404, "Resource not found")
        if (static / "index.html").is_file():
            return FileResponse(static / "index.html")
        return JSONResponse({"service": "KerfPulse", "dashboard": "Build web/dist with npm run build in web/", "api": "/docs"})

    return app


app = create_app()


def main():
    import uvicorn
    uvicorn.run("pdm.api:app", host=os.getenv("PDM_HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")))


if __name__ == "__main__":
    main()
