"""Local trusted administration. Never expose these actions through demo login."""
import argparse
import json
from pathlib import Path
from pdm.store import Store
from pdm.device_ingest import DeviceIngest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--org',required=True)
    parser.add_argument('--site',required=True)
    parser.add_argument('--asset',required=True)
    parser.add_argument('--output',type=Path,required=True,help='Private one-time credential file; must not exist')
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    store = Store()
    try:
        service = DeviceIngest(store); service.initialize()
        with args.output.open('x',encoding='utf-8') as file:
            value = service.register_device(args.org,args.site,args.asset)
            json.dump(value,file,indent=2)
        print(json.dumps({'device_id':value['device_id'],'credential_file':str(args.output),'qualification':'unconfigured'}))
    finally: store.close()


if __name__ == '__main__': main()
