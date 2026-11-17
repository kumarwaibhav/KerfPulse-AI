"""Nested causal acquisition experiment with training-only cross-fitted gain labels."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold
from pdm.acquisition_gate import AcquisitionState, choose_evidence, realized_decision_loss
from pdm.dataset import load
from pdm.gpu_benchmark import prepare, partitions
from pdm.train import feature_names
from pdm.validation import fit, probabilities
from pdm.policy import PolicyState, decide, outcome
from pdm.research_runtime import ResourceGuard, ExperimentLock, atomic_json


def cheap_features(cut,p):
    offset=3-cut.cycle%3
    entropy=-sum(v*math.log(max(v,1e-15)) for v in p)
    return list(p)+[entropy,offset,cut.cycle,cut.context['HardnessMean']]


def run(output):
    rows,groups=prepare();tools=load();report=[]
    from pdm.experiment_provenance import fingerprint
    folds=list(partitions(rows,groups,'workpiece'))
    configuration={'provenance':fingerprint(rows,groups,folds,['logistic','fused']),
                   'experiment_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   'gate_sha256':hashlib.sha256(Path(__file__).with_name('acquisition_gate.py').read_bytes()).hexdigest(),
                   'costs':[1.,20.,.1],'C':.01,'temperature':1.,'budget':.25,'seed':17}
    config_path=Path(output)/'configuration.json'
    if config_path.exists() and json.loads(config_path.read_text())!=configuration:
        raise ValueError('Candidate experiment fingerprint changed; choose a new output directory')
    atomic_json(config_path,configuration)
    guard=ResourceGuard(output,gpu=False)
    with ExperimentLock('artifacts/research-gpu.lock'):
        for fold,(train,test,key) in enumerate(folds):
            fold_path=Path(output)/f'fold-{fold}.json'
            if fold_path.exists():
                report.extend(json.loads(fold_path.read_text())['results'])
                continue
            guard.check(force=True)
            training=[rows[i] for i in train];testing=[rows[i] for i in test]
            names={head:feature_names(training[0][0],head) for head in ('current','fused')}
            oof={head:np.zeros((len(train),9)) for head in names}
            inner_groups=[groups[c.tool_id] for c,_ in training]
            for a,b in GroupKFold(n_splits=3).split(training,groups=inner_groups):
                for head in names:
                    model=fit([training[i] for i in a],names[head],.01)
                    oof[head][b]=probabilities(model,[training[i] for i in b],names[head],1.)
            features=[];gains=[]
            for i,(cut,remaining) in enumerate(training):
                offset=3-cut.cycle%3
                features.append(cheap_features(cut,oof['current'][i]))
                gains.append(realized_decision_loss(oof['current'][i],remaining,offset)-realized_decision_loss(oof['fused'][i],remaining,offset)-.1)
            gate=RandomForestRegressor(n_estimators=100,max_depth=2,min_samples_leaf=10,random_state=17,n_jobs=1).fit(features,gains)
            heads={head:fit(training,names[head],.01) for head in names}
            supported_recipes={cut.recipe for cut,_ in training}
            # Cheap test predictions available first. Optional test features remain behind callback.
            current=probabilities(heads['current'],testing,names['current'],1.)
            for tool_id in sorted({c.tool_id for c,_ in testing}):
                for policy in ('current','fused','periodic','random','regret_gate'):
                    acquisition=AcquisitionState();state=PolicyState();rng=random.Random(17)
                    unsupported=0
                    for i,(cut,remaining) in enumerate(testing):
                        if cut.tool_id!=tool_id:continue
                        if cut.recipe not in supported_recipes:
                            unsupported+=1
                            continue
                        gain=float(gate.predict([cheap_features(cut,current[i])])[0])
                        proposed=gain if policy=='regret_gate' else 1. if policy=='fused' or policy=='periodic' and cut.cycle%4==0 or policy=='random' and rng.random()<.25 else -1.
                        if policy=='current':proposed=-1.
                        def optional():return probabilities(heads['fused'],[(cut,remaining)],names['fused'],1.)[0]
                        chosen=choose_evidence(current[i],proposed,3-cut.cycle%3,acquisition,optional,budget=1. if policy=='fused' else .25)
                        decide(state,cut.cycle,chosen['probabilities'],chosen['probabilities'],'current',3,.05)
                    report.append({'fold':fold,'tool_id':tool_id,'policy':policy,'first_slot':state.first_slot,'outcome':outcome(tools[tool_id].failure_cycle,state.first_slot),
                                   'observations':acquisition.eligible,'unsupported_recipe_cuts':unsupported,'optional_acquisitions':acquisition.acquired})
            atomic_json(fold_path,{'training_tools':sorted({c.tool_id for c,_ in training}),'test_tools':sorted({c.tool_id for c,_ in testing}),
                                                         'results':[r for r in report if r['fold']==fold]})
        no_opportunity=[t.id for t in tools.values() if not any(c.status=='ok' for c in t.cuts)]
        for tool_id in no_opportunity:
            for policy in ('current','fused','periodic','random','regret_gate'):
                report.append({'tool_id':tool_id,'policy':policy,'first_slot':None,'outcome':'no_inspection','observations':0,'optional_acquisitions':0,'no_pre_damage_opportunity':True})
        result={'configuration':configuration,'results':report,'C':.01,'temperature':1.,'inspection_cost':1.,'missed_window_cost':20.,'acquisition_cost':.1,
                'warning':'Development hypothesis. Fixed illustrative costs; shared maximum prefix budget, not necessarily equal realized acquisitions. No sensing-energy or industrial ROI claim.',
                'no_opportunity_tools':[t.id for t in tools.values() if not any(c.status=='ok' for c in t.cuts)]}
        atomic_json(Path(output)/'report.json',result)
        print(json.dumps({'policies':sorted({r['policy'] for r in report}),'records':len(report)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('artifacts/acquisition-regret-development'))
    run(parser.parse_args().output)
