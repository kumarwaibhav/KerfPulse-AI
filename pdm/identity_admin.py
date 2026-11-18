"""Trusted local people/grant administration. Never expose Docker access publicly."""
import argparse
import json
from pdm.identity import IdentityStore,ROLES
from pdm.store import Store


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('list')
    grant=sub.add_parser('grant')
    for key in ('person','org','site','asset','actor'):grant.add_argument('--'+key,required=True)
    grant.add_argument('--role',choices=ROLES,required=True)
    revoke=sub.add_parser('revoke');revoke.add_argument('--person',required=True);revoke.add_argument('--actor',required=True)
    args=parser.parse_args();store=Store()
    try:
        identity=IdentityStore(store);identity.initialize()
        if args.command=='list':
            with store.transaction() as conn:
                print(json.dumps([dict(r) for r in store.execute(conn,'SELECT id,issuer,subject,display_name,disabled FROM people ORDER BY display_name').fetchall()],indent=2))
        elif args.command=='grant':
            identity.grant(args.person,args.org,args.site,args.asset,args.role,args.actor)
            print(json.dumps({'granted':args.person,'role':args.role,'asset':args.asset}))
        else:
            identity.revoke(args.person,args.actor);print(json.dumps({'access_revoked':args.person,'sessions_revoked':True}))
    finally:store.close()


if __name__=='__main__':main()
