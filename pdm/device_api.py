"""Device-authenticated durable receipts, separate from human demo sessions."""
import json
import asyncio
from fastapi import APIRouter, Header, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool
from pdm.device_ingest import DeviceAuthError
from pdm.store import StoreError


def router_for(service):
    router = APIRouter(prefix='/api/v2')
    active={}

    def token(header):
        if not header or not header.startswith('Bearer ') or len(header) > 210:
            raise HTTPException(401, 'Device bearer credential required')
        return header[7:]

    @router.post('/ingest/cuts')
    async def ingest(request: Request, authorization: str | None = Header(default=None)):
        credential = token(authorization)
        def unique_pairs(pairs):
            values = {}
            for key, value in pairs:
                if key in values: raise ValueError('Duplicate JSON key')
                values[key] = value
            return values
        try:
            body = json.loads(await request.body(),object_pairs_hook=unique_pairs)
        except (ValueError, UnicodeError):
            raise HTTPException(422, 'Invalid JSON or duplicate object keys') from None
        try:
            return await run_in_threadpool(service.ingest, credential, body)
        except DeviceAuthError:
            raise HTTPException(401, 'Invalid device credential') from None
        except StoreError as error:
            raise HTTPException(422, str(error)) from None

    @router.get('/receipts/{receipt_id}')
    def receipt(receipt_id: str, authorization: str | None = Header(default=None)):
        try:
            result = service.get_receipt(token(authorization), receipt_id)
        except DeviceAuthError:
            raise HTTPException(401, 'Invalid device credential') from None
        except StoreError as error:
            raise HTTPException(422, str(error)) from None
        if result is None:
            raise HTTPException(404, 'Receipt not found')
        return result

    @router.get('/events')
    def events(after: int=Query(default=0,ge=0,le=2**63-1),authorization: str | None=Header(default=None)):
        try:return service.events(token(authorization),after)
        except DeviceAuthError:raise HTTPException(401,'Invalid device credential') from None

    @router.get('/events/stream')
    async def stream(request: Request,after: int=Query(default=0,ge=0,le=2**63-1),authorization: str | None=Header(default=None)):
        credential=token(authorization)
        try:owner=await run_in_threadpool(service.authenticate,credential)
        except DeviceAuthError:raise HTTPException(401,'Invalid device credential') from None
        try:
            cursor=int(request.headers.get('last-event-id',str(after)))
            if not 0<=cursor<=2**63-1:raise ValueError()
        except ValueError:raise HTTPException(422,'Invalid stream cursor') from None
        key=owner['id']
        if active.get(key,0)>=4 or sum(active.values())>=32:raise HTTPException(429,'Stream capacity reached')
        active[key]=active.get(key,0)+1
        async def generate():
            nonlocal cursor
            try:
                while not await request.is_disconnected():
                    try:batch=await run_in_threadpool(service.events,credential,cursor)
                    except DeviceAuthError:
                        yield 'event: authorization_revoked\ndata: {}\n\n'
                        return
                    for event in batch['events']:
                        cursor=event['id']
                        yield 'id: '+str(cursor)+'\nevent: assessment\ndata: '+json.dumps(event['data'])+'\n\n'
                    if not batch['events']:
                        yield ': keepalive\n\n'
                        await asyncio.sleep(1)
            finally:
                active[key]-=1
                if not active[key]:del active[key]
        return StreamingResponse(generate(),media_type='text/event-stream',headers={'Cache-Control':'no-store','X-Accel-Buffering':'no'})

    return router
