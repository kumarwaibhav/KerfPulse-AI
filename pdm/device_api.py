"""Device-authenticated durable receipts, separate from human demo sessions."""
import json
from fastapi import APIRouter, Header, HTTPException, Request
from starlette.concurrency import run_in_threadpool
from pdm.device_ingest import DeviceAuthError
from pdm.store import StoreError


def router_for(service):
    router = APIRouter(prefix='/api/v2')

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

    return router
