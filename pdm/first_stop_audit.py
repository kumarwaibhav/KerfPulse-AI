"""Read-only first-inspection audit of saved acquisition experiment; no fitting."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

POLICIES = ('current','fused','periodic','random','regret_gate')


def prefix_quota(eligible):
    """Proposed next protocol uses floor(n/4), unlike historical ceil budget."""
    if type(eligible) is not int or eligible < 0:
        raise ValueError('Nonnegative integer eligible count required')
    return eligible//4


def timely_slots(damage_cycle, observed_cycles, interval=3):
    if type(damage_cycle) is not int or damage_cycle < 1 or interval != 3:
        raise ValueError('Positive damage cycle and frozen three-cut calendar required')
    cycles=list(observed_cycles)
    if any(type(c) is not int or not 0<c<damage_cycle for c in cycles) or len(set(cycles))!=len(cycles):
        raise ValueError('Unique observed pre-damage cycles required')
    # A missing recorded cycle cannot create an inspection decision opportunity.
    return sorted({(c//3+1)*3 for c in cycles if 2<=damage_cycle-(c//3+1)*3<=5})


def audit(directory,output):
    from pdm.dataset import load,SOURCE_SHA256
    from pdm.gpu_benchmark import prepare,partitions
    from pdm.experiment_provenance import fingerprint
    from pdm.policy import outcome
    directory=Path(directory)
    report_bytes=(directory/'report.json').read_bytes()
    report=json.loads(report_bytes)
    saved=json.loads((directory/'configuration.json').read_text())
    if report['configuration']!=saved:
        raise ValueError('Report configuration differs from saved configuration')
    root=Path(__file__).parent
    for name,key in (('acquisition_research.py','experiment_sha256'),('acquisition_gate.py','gate_sha256')):
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=saved[key]:
            raise ValueError('Historical acquisition implementation differs from saved fingerprint')
    rows,groups=prepare();folds=list(partitions(rows,groups,'workpiece'));tools=load()
    current=fingerprint(rows,groups,folds,['logistic','fused'])
    # Read-only analysis may use another environment; data, code and split must match.
    for key in ('schema_version','code','observations_sha256','partitions_sha256','features'):
        if current[key]!=saved['provenance'][key]:
            raise ValueError('Source/code/split fingerprint mismatch: '+key)
    if saved['costs']!=[1.,20.,.1] or saved['budget']!=.25:
        raise ValueError('This audit supports only the frozen historical cost/budget protocol')
    records=report['results'];by_key={}
    for value in records:
        key=(value['tool_id'],value['policy'])
        if key in by_key or value['policy'] not in POLICIES:
            raise ValueError('Duplicate/unknown tool-policy result')
        by_key[key]=value
    if set(by_key)!={(tool,policy) for tool in tools for policy in POLICIES}:
        raise ValueError('Incomplete or unexpected tool-policy cohort')
    support={};fold_ids={};fold_records=[]
    for number,(train,test,_) in enumerate(folds):
        training={rows[i][0].tool_id for i in train};testing={rows[i][0].tool_id for i in test}
        fold=json.loads((directory/f'fold-{number}.json').read_text())
        if sorted(training)!=fold['training_tools'] or sorted(testing)!=fold['test_tools']:
            raise ValueError('Fold identities disagree with verified source partitions')
        if {groups[t] for t in training}&{groups[t] for t in testing}:
            raise ValueError('Connected workpiece leakage')
        recipes={rows[i][0].recipe for i in train}
        for tool in testing:
            support[tool]=[c.cycle for c,_ in rows if c.tool_id==tool and c.recipe in recipes]
            fold_ids[tool]=number
        fold_records.extend(fold['results'])
    if sorted(fold_records,key=lambda v:(v['tool_id'],v['policy']))!=sorted(
            [r for r in records if 'fold' in r],key=lambda v:(v['tool_id'],v['policy'])):
        raise ValueError('Fold results differ from aggregate report')
    audited=[]
    for tool in tools.values():
        observed=[c.cycle for c in tool.cuts if c.status=='ok']
        supported=support.get(tool.id,[])
        available=timely_slots(tool.failure_cycle,supported)
        kind='no_pre_damage_observation' if not observed else 'unsupported_recipe' if not supported else 'supported'
        policy_results={}
        possible_slots={(c//3+1)*3 for c in supported}
        for policy in POLICIES:
            row=by_key[(tool.id,policy)];slot=row['first_slot'];acquired=row['optional_acquisitions']
            if row['observations']!=len(supported) or row.get('unsupported_recipe_cuts',0)!=len(observed)-len(supported):
                raise ValueError('Saved support counts differ from source')
            if supported and row.get('fold')!=fold_ids[tool.id]:
                raise ValueError('Wrong held-out fold')
            if slot is not None and (type(slot) is not int or slot not in possible_slots):
                raise ValueError('First slot has no supported recorded decision opportunity')
            if row['outcome']!=outcome(tool.failure_cycle,slot):
                raise ValueError('Saved first-stop outcome disagrees with source damage')
            if type(acquired) is not int or not 0<=acquired<=len(supported):
                raise ValueError('Invalid saved acquisition count')
            before=acquired if slot is None or acquired==0 else None
            policy_results[policy]={'first_slot':slot,'outcome':row['outcome'],
                'lead_cuts':None if slot is None else tool.failure_cycle-slot,'total_acquisitions':acquired,
                'acquisitions_before_first_decision':before,
                'acquisitions_after_first_decision':0 if before is not None else None,
                'acquisition_timing_evidence':'Derivable: no inspection or no acquisitions' if before is not None else 'Unavailable: historical run saved totals, not event traces'}
        audited.append({'tool_id':tool.id,'damage_cycle':tool.failure_cycle,'cohort_status':kind,
            'observed_eligible_cuts':len(observed),'supported_cuts':len(supported),
            'unsupported_cuts':len(observed)-len(supported),'attainable_timely_slots':available,'policies':policy_results})
    result={'audit_version':1,'source_sha256':SOURCE_SHA256,'historical_report_sha256':hashlib.sha256(report_bytes).hexdigest(),
        'historical_configuration_sha256':hashlib.sha256((directory/'configuration.json').read_bytes()).hexdigest(),
        'analysis_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'analysis_policy_sha256':hashlib.sha256((root/'policy.py').read_bytes()).hexdigest(),
        'fingerprint_check':'Saved data/code/split/feature fingerprints matched',
        'historical_fingerprint_gap':'Original configuration did not fingerprint policy.py; this audit records current outcome semantics, not historical dependency attestation',
        'analysis_environment':{k:v for k,v in current.items() if k in ('python','platform','packages')},
        'coverage':dict(Counter(r['cohort_status'] for r in audited)),
        'supported_cuts':sum(r['supported_cuts'] for r in audited),'unsupported_cuts':sum(r['unsupported_cuts'] for r in audited),
        'historical_budget':'ceil(n*.25); acquisition allowed from first eligible cut',
        'next_protocol_budget':'floor(n/4); first three eligible cuts cannot acquire',
        'historical_acquisition_scope':'Full recorded supported life, including continued loop after first inspection fixation',
        'training':'Not run; retrospective diagnostic only',
        'qualification':'Exploratory single-machine audit; no superiority, policy benefit or production promotion',
        'tools':audited}
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as file:json.dump(result,file,indent=2,allow_nan=False)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,default=Path('artifacts/acquisition-regret-development-v1'))
    parser.add_argument('--output',type=Path,default=Path('artifacts/first-stop-audit-v1/report.json'))
    args=parser.parse_args();result=audit(args.directory,args.output)
    print(json.dumps({k:result[k] for k in ('coverage','supported_cuts','unsupported_cuts','training')}))
