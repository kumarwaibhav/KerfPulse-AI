"""Reproduce conditional acquisition counts and paired workpiece uncertainty."""
import argparse
import json
from pathlib import Path
import numpy as np
from pdm.dataset import load
from pdm.train import components
from pdm.research_runtime import atomic_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    report=json.loads((args.directory/'report.json').read_text())
    tools=load();clusters=components(tools)
    lookup={(row['policy'],row['tool_id']):row for row in report['results']}
    summary={}
    policies=('current','fused','periodic','random','regret_gate')
    if len(lookup)!=len(tools)*len(policies) or len(lookup)!=len(report['results']):raise ValueError('Incomplete or duplicate policy/tool cohort')
    for policy in policies:
        rows=[lookup[policy,t] for t in tools]
        n=sum(r['observations'] for r in rows);a=sum(r['optional_acquisitions'] for r in rows)
        summary[policy]={kind:sum(r['outcome']==kind for r in rows) for kind in ('timely','premature','late','no_inspection')}
        summary[policy].update(acquisitions=a,eligible_observations=n,acquisition_fraction=a/n if n else None)
    rng=np.random.default_rng(17);deltas=[]
    for _ in range(2000):
        keys=[t for i in rng.integers(0,len(clusters),len(clusters)) for t in clusters[i]]
        n=sum(lookup['current',t]['observations'] for t in keys)
        if n:
            deltas.append((sum(lookup['regret_gate',t]['optional_acquisitions'] for t in keys)-sum(lookup['periodic',t]['optional_acquisitions'] for t in keys))/n)
    all_cuts=sum(c.status=='ok' for t in tools.values() for c in t.cuts)
    n=summary['current']['eligible_observations']
    result={'summary':summary,'eligible_cut_coverage':n/all_cuts,'excluded_by_recipe_support':all_cuts-n,
            'gate_minus_periodic_acquisition_fraction_cluster_95_interval':np.percentile(deltas,[2.5,97.5]).tolist(),
            'replicates':len(deltas),'qualification':'Conditional development evidence on few workpiece clusters. Acquisition differences do not establish maintenance benefit.',
            'warning':'Illustrative threshold .05 and training-recipe support abstention; distinct from historical .5 policy. No compute, energy or avoided-downtime claim.'}
    atomic_json(args.directory/'comparison-analysis.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
