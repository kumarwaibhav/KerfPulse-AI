"""Matched nested group evaluation on authentic completed-cut summaries.

Outputs are development comparisons, never automatic operational promotions.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import time

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

from pdm.dataset import load, NUMERIC_CONTEXT, SOURCE_SHA256
from pdm.train import components, vector
from pdm.research_runtime import ResourceGuard, ExperimentLock, atomic_json


def prepare():
    tools = load()
    groups = {key: i for i, group in enumerate(components(tools)) for key in group}
    rows = [(c, t.failure_cycle-c.cycle) for t in tools.values() for c in t.cuts if c.status == 'ok']
    return rows, groups


def names_for(cut, method):
    if method == 'age_only': return ['NumberOfCycle']
    if method == 'context': return list(NUMERIC_CONTEXT)
    context = [k for k in NUMERIC_CONTEXT if method != 'current_no_age' or k != 'NumberOfCycle']
    return context + sorted(cut.current) + (sorted(cut.vibration) if method == 'fused' else [])


def partitions(rows, groups, protocol):
    keys = sorted(set(groups[c.tool_id] if protocol == 'workpiece' else c.recipe for c, _ in rows))
    for key in keys:
        test = [i for i,(c,_) in enumerate(rows) if (groups[c.tool_id] if protocol == 'workpiece' else c.recipe) == key]
        excluded = {groups[rows[i][0].tool_id] for i in test}
        train = [i for i,(c,_) in enumerate(rows) if groups[c.tool_id] not in excluded]
        yield train, test, str(key)


def candidates(method, count):
    if count<1:raise ValueError('At least one candidate required')
    maximum={'xgboost':81,'random_forest':48,'mlp':81}.get(method)
    if maximum is not None and count>maximum:raise ValueError('Requested candidates exceed unique search space')
    rng = random.Random(17)
    if method in ('age_only','context','logistic','current_no_age','fused'):
        return [{'C': float(v)} for v in np.geomspace(.001,10,count)]
    values = []
    while len(values) < count:
        if method == 'xgboost':
            value = {'max_depth':rng.choice([2,3,4]),'eta':rng.choice([.02,.05,.1]),'rounds':rng.choice([60,120,200]),'reg_lambda':rng.choice([1,5,20])}
        elif method == 'random_forest':
            value = {'max_depth':rng.choice([3,5,8,None]),'min_samples_leaf':rng.choice([2,4,8,16]),'max_features':rng.choice(['sqrt',.5,1.0])}
        elif method == 'mlp':
            value = {'width':rng.choice([16,32,64]),'dropout':rng.choice([0,.2,.4]),'lr':rng.choice([.0003,.001,.003]),'weight_decay':rng.choice([.001,.01,.1]),'epochs':60}
        else: raise ValueError('Unknown model family')
        if value not in values: values.append(value)
    return values


def balanced_weights(ids):
    return np.asarray([len(ids)/(len(set(ids))*ids.count(k)) for k in ids],dtype=np.float32)


def loss(y, p, ids):
    value = -np.log(np.maximum(p[np.arange(len(y)),y],1e-15))
    return float(np.mean([value[np.asarray(ids)==k].mean() for k in set(ids)]))


def calibrate(p, temperature):
    logits = np.log(np.maximum(p,1e-15))/temperature
    logits -= logits.max(axis=1,keepdims=True)
    exp = np.exp(logits)
    return exp/exp.sum(axis=1,keepdims=True)


def fit_predict(method, config, x, y, ids, xt, seed, guard):
    guard.check()
    weights = balanced_weights(ids)
    if method == 'mlp':
        import torch
        if not torch.cuda.is_available(): raise RuntimeError('Neural benchmark requires verified CUDA')
        random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
        scaler = StandardScaler().fit(x)
        train = torch.as_tensor(scaler.transform(x),dtype=torch.float32,device='cuda')
        target = torch.as_tensor(y,dtype=torch.long,device='cuda')
        w = torch.as_tensor(weights,device='cuda')
        test = torch.as_tensor(scaler.transform(xt),dtype=torch.float32,device='cuda')
        net = torch.nn.Sequential(torch.nn.Linear(x.shape[1],config['width']),torch.nn.ReLU(),torch.nn.Dropout(config['dropout']),torch.nn.Linear(config['width'],9)).cuda()
        opt = torch.optim.AdamW(net.parameters(),lr=config['lr'],weight_decay=config['weight_decay'])
        amp = torch.amp.GradScaler('cuda')
        for _ in range(config['epochs']):
            guard.check()
            net.train(); opt.zero_grad(set_to_none=True)
            with torch.autocast('cuda',dtype=torch.float16):
                objective = (torch.nn.functional.cross_entropy(net(train),target,reduction='none')*w).mean()
            amp.scale(objective).backward(); amp.step(opt); amp.update()
        net.eval()
        with torch.no_grad(): result = net(test).softmax(-1).float().cpu().numpy()
        del net, opt, train, test, target, w
        torch.cuda.empty_cache()
        return result
    result = np.zeros((len(xt),9))
    if method == 'xgboost':
        import xgboost as xgb
        model = xgb.train({'device':'cuda','tree_method':'hist','objective':'multi:softprob','num_class':9,
                           'seed':seed,'nthread':2,**{k:v for k,v in config.items() if k!='rounds'}},
                          xgb.DMatrix(x,label=y,weight=weights),num_boost_round=config['rounds'])
        if not json.loads(model.save_config())['learner']['generic_param']['device'].startswith('cuda'):
            raise RuntimeError('GPU benchmark silently fell back to CPU')
        return model.predict(xgb.DMatrix(xt))
    if method == 'random_forest':
        model = RandomForestClassifier(n_estimators=200,n_jobs=2,random_state=seed,**config)
    else:
        scaler = StandardScaler().fit(x)
        x, xt = scaler.transform(x), scaler.transform(xt)
        model = LogisticRegression(max_iter=3000,random_state=seed,**config)
    model.fit(x,y,sample_weight=weights)
    result[:,model.classes_.astype(int)] = model.predict_proba(xt)
    return result


def run(args):
    from sklearn.metrics import average_precision_score, brier_score_loss
    if len(set(args.methods))!=len(args.methods) or len(set(args.seeds))!=len(args.seeds):
        raise ValueError('Model families and seeds must be unique')
    rows, groups = prepare()
    directory = args.output
    from pdm.experiment_provenance import fingerprint
    folds=list(partitions(rows,groups,args.protocol))
    signature = {'source_sha256':SOURCE_SHA256,'protocol':args.protocol,'methods':args.methods,'trials':args.trials,'seeds':args.seeds,
                 'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 'provenance':fingerprint(rows,groups,folds,args.methods)}
    directory.mkdir(parents=True,exist_ok=True)
    if (directory/'configuration.json').exists() and json.loads((directory/'configuration.json').read_text()) != signature:
        raise ValueError('Resume configuration differs; use a new output directory')
    atomic_json(directory/'configuration.json',signature)
    guard = ResourceGuard(directory)
    predictions = []
    with ExperimentLock(Path('artifacts/research-gpu.lock')):
        for method in args.methods:
            names = names_for(rows[0][0],method)
            x = np.asarray([vector(c,names) for c,_ in rows],dtype=np.float32)
            y = np.asarray([min(r,9)-1 for _,r in rows])
            ids = [c.tool_id for c,_ in rows]
            for fold,(train,test,key) in enumerate(folds):
                for seed in args.seeds:
                    path = directory/f'{method}-fold{fold}-seed{seed}.json'
                    if path.exists():
                        predictions.extend(json.loads(path.read_text())['predictions']); continue
                    start = time.perf_counter()
                    inner_groups = [groups[rows[i][0].tool_id] for i in train]
                    inner = list(GroupKFold(n_splits=min(3,len(set(inner_groups)))).split(train,groups=inner_groups))
                    trial_path = directory/f'{method}-fold{fold}-seed{seed}-trials.json'
                    trials = json.loads(trial_path.read_text()) if trial_path.exists() else []
                    for number,config in enumerate(candidates(method,args.trials)):
                        if number < len(trials): continue
                        out = np.zeros((len(train),9))
                        for ti,vi in inner:
                            a,b = np.asarray(train)[ti],np.asarray(train)[vi]
                            out[vi] = fit_predict(method,config,x[a],y[a],[ids[i] for i in a],x[b],seed,guard)
                        options = [(loss(y[train],calibrate(out,t),[ids[i] for i in train]),t) for t in (.5,1.,2.)]
                        value, temperature = min(options)
                        trials.append({'config':config,'temperature':temperature,'inner_balanced_log_loss':value})
                        atomic_json(trial_path,trials)
                    selected = min(trials,key=lambda v:v['inner_balanced_log_loss'])
                    probabilities = calibrate(fit_predict(method,selected['config'],x[train],y[train],[ids[i] for i in train],x[test],seed,guard),selected['temperature'])
                    scored = [{'method':method,'seed':seed,'tool_id':rows[i][0].tool_id,'cycle':rows[i][0].cycle,'remaining':rows[i][1],
                               'probabilities':p.tolist()} for i,p in zip(test,probabilities)]
                    atomic_json(path,{'selected':selected,'features':names,'training_tools':sorted({ids[i] for i in train}),
                                      'test_tools':sorted({ids[i] for i in test}),'seconds':time.perf_counter()-start,'predictions':scored})
                    predictions.extend(scored)
                    print(json.dumps({'completed':path.name,'seconds':time.perf_counter()-start}),flush=True)
        metrics = {}
        for method in args.methods:
            values = []
            for seed in args.seeds:
                selected = [p for p in predictions if p['method']==method and p['seed']==seed]
                target = np.asarray([p['remaining']<=5 for p in selected])
                scores = np.asarray([sum(p['probabilities'][:5]) for p in selected])
                values.append({'seed':seed,'n':len(selected),'positives':int(target.sum()),'average_precision':float(average_precision_score(target,scores)),
                               'brier':float(brier_score_loss(target,scores))})
            metrics[method] = values
        report = {**signature,'metrics':metrics,'interpretation':'Nested grouped development evidence on previously explored benchmark; no factory or superiority claim',
              'resume':'Completed folds/trials require identical data, splits, code and environment; interrupted trial restarts with same seed, without bitwise GPU determinism guarantee'}
        atomic_json(directory/'report.json',report)
        print(json.dumps(report,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--methods',nargs='+',default=['age_only','context','logistic','current_no_age','xgboost','random_forest','mlp'])
    parser.add_argument('--protocol',choices=['workpiece','recipe'],default='workpiece')
    parser.add_argument('--trials',type=int,default=20)
    parser.add_argument('--seeds',nargs='+',type=int,default=[17,29,43])
    parser.add_argument('--output',type=Path,default=Path('artifacts/gpu-benchmark-workpiece'))
    args = parser.parse_args()
    if not 1 <= args.trials <= 100: parser.error('Trials must be 1..100')
    run(args)
