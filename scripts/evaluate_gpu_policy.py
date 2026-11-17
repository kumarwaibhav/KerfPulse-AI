"""Evaluate recorded out-of-fold predictions under unchanged fixed policy."""
import argparse
import json
from pathlib import Path
from pdm.dataset import load
from pdm.policy import PolicyState, decide, outcome
from pdm.research_runtime import atomic_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    report=json.loads((args.directory/'report.json').read_text())
    tools=load(); results=[]
    for method in report['methods']:
        for seed in report['seeds']:
            observations=[]
            for path in args.directory.glob(f'{method}-fold*-seed{seed}.json'):
                observations.extend(json.loads(path.read_text())['predictions'])
            outcomes=[]
            for tool in tools.values():
                state=PolicyState()
                for row in sorted([r for r in observations if r['tool_id']==tool.id],key=lambda r:r['cycle']):
                    decide(state,row['cycle'],row['probabilities'],row['probabilities'],'current',3,.5)
                outcomes.append({'tool_id':tool.id,'first_slot':state.first_slot,'outcome':outcome(tool.failure_cycle,state.first_slot),
                                 'no_pre_damage_opportunity':not any(c.status=='ok' for c in tool.cuts)})
            results.append({'method':method,'seed':seed,'outcomes':outcomes,
                            'summary':{kind:sum(o['outcome']==kind for o in outcomes) for kind in ('timely','premature','late','no_inspection')}})
    result={'threshold':.5,'slot_interval':3,'purpose':'Fixed historical policy; no threshold tuned on outer predictions', 'results':results}
    atomic_json(args.directory/'fixed-policy-report.json',result)
    print(json.dumps({r['method']:r['summary'] for r in results},indent=2))


if __name__=='__main__': main()
