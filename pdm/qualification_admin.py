"""Local trusted qualification administration; no demo-session promotion route."""
import argparse
import json
from pathlib import Path
from pdm.store import Store
from pdm.device_ingest import DeviceIngest
from pdm.qualification import QualificationRegistry


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    grant=sub.add_parser('grant');grant.add_argument('--workspace',required=True);grant.add_argument('--device',required=True)
    record=sub.add_parser('record');record.add_argument('--device',required=True)
    record.add_argument('--state',choices=['unqualified','extraction_verified','shadow_approved','revoked'],required=True)
    record.add_argument('--profile',type=Path,required=True);record.add_argument('--actor',required=True)
    record.add_argument('--evidence',required=True);record.add_argument('--valid-until',required=True)
    args=parser.parse_args();store=Store()
    try:
        store.initialize();DeviceIngest(store).initialize();registry=QualificationRegistry(store)
        if args.command=='grant':
            registry.grant(args.workspace,args.device);print(json.dumps({'granted':args.device,'scope':'read-only source health'}))
        else:
            value=registry.record(args.device,args.state,json.loads(args.profile.read_text(encoding='utf-8')),args.actor,args.evidence,args.valid_until)
            print(json.dumps(value,indent=2))
    finally:store.close()


if __name__=='__main__':main()
