"""Named-user source access. Exact grants are rechecked for each request."""
from fastapi import APIRouter,Depends,HTTPException
from pdm.qualification import QualificationRegistry


def routes(store,person):
    router=APIRouter(prefix='/api/operations')
    registry=QualificationRegistry(store)

    @router.get('/sources')
    def sources(owner=Depends(person)):
        # No wildcard matching, provider-claim roles, or demo-workspace grant inheritance.
        with store.transaction() as conn:
            devices=store.execute(conn,'SELECT DISTINCT d.id FROM ingest_devices d JOIN people_grants g ON g.org_id=d.org_id AND g.site_id=d.site_id AND g.asset_id=d.asset_id WHERE g.person_id=? ORDER BY d.id',(owner['id'],)).fetchall()
        return {'workspace_id':owner['id'],'sources':registry.health_for_devices([r['id'] for r in devices]),
                'access':'Named identity with exact organization/site/asset grants'}

    @router.get('/sources/{device_id}/history')
    def history(device_id:str,owner=Depends(person)):
        with store.transaction() as conn:
            allowed=store.execute(conn,'SELECT d.id FROM ingest_devices d JOIN people_grants g ON g.org_id=d.org_id AND g.site_id=d.site_id AND g.asset_id=d.asset_id WHERE g.person_id=? AND d.id=?',(owner['id'],device_id)).fetchone()
            if not allowed:raise HTTPException(404,'Source not found')
            rows=store.execute(conn,'SELECT p.payload FROM operational_processing p JOIN ingest_receipts r ON r.id=p.receipt_id WHERE r.device_id=? ORDER BY p.processed_at DESC,p.receipt_id DESC LIMIT 100',(device_id,)).fetchall()
        import json
        return {'results':[json.loads(row['payload']) for row in rows]}

    return router
