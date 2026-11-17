"""Validate grouped predictions and report paired cluster uncertainty.

Seed repetitions do not create independent machines. Bootstrap intervals here
describe development evidence from few connected workpiece clusters only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss
from pdm.gpu_benchmark import prepare
from pdm.research_runtime import atomic_json


def validate_rows(rows,expected):
    seen=set()
    for row in rows:
        key=(row['tool_id'],row['cycle'])
        if key in seen or key not in expected:raise ValueError('Duplicate or unexpected prediction identity')
        seen.add(key)
        if row['remaining']!=expected[key]:raise ValueError('Prediction target differs from verified source')
        p=np.asarray(row['probabilities'],dtype=float)
        if p.shape!=(9,) or not np.isfinite(p).all() or (p<0).any() or (p>1).any() or abs(p.sum()-1)>1e-5:
            raise ValueError('Invalid horizon probabilities')
    if seen!=set(expected):raise ValueError('Incomplete held-out cohort')


def paired_interval(labels,candidate,baseline,clusters,repeats=1000,seed=17):
    labels=np.asarray(labels,dtype=bool);clusters=np.asarray(clusters)
    unique=np.unique(clusters);indexes={key:np.flatnonzero(clusters==key) for key in unique}
    rng=np.random.default_rng(seed);differences=[]
    for _ in range(repeats):
        draw=np.concatenate([indexes[key] for key in rng.choice(unique,size=len(unique),replace=True)])
        if not labels[draw].any():continue
        deltas=[average_precision_score(labels[draw],np.asarray(a)[draw])-average_precision_score(labels[draw],np.asarray(b)[draw])
                for a,b in zip(candidate,baseline)]
        differences.append(float(np.mean(deltas)))
    return {'ap_delta_95_interval':np.percentile(differences,[2.5,97.5]).tolist() if differences else None,
            'valid_replicates':len(differences),'requested_replicates':repeats,'clusters':len(unique),
            'interpretation':'Paired connected-workpiece bootstrap, conditional development evidence; seeds averaged within each replicate'}


def evaluate(directory,repeats=1000):
    directory=Path(directory)
    report=json.loads((directory/'report.json').read_text())
    observations,groups=prepare()
    expected={(c.tool_id,c.cycle):remaining for c,remaining in observations}
    keys=sorted(expected);labels=np.asarray([expected[key]<=5 for key in keys])
    cluster_ids=np.asarray([groups[key[0]] for key in keys])
    cube={};metrics={}
    for method in report['methods']:
        cube[method]=[];metrics[method]=[]
        for seed in report['seeds']:
            rows=[]
            paths=list(directory.glob(f'{method}-fold*-seed{seed}.json'))
            for path in paths:
                fold=json.loads(path.read_text())
                a={groups[t] for t in fold['training_tools']};b={groups[t] for t in fold['test_tools']}
                if a & b:raise ValueError('Linked workpiece leakage in fold manifest')
                for row in fold['predictions']:
                    if row['method']!=method or row['seed']!=seed or row['tool_id'] not in fold['test_tools']:
                        raise ValueError('Prediction identity disagrees with fold manifest')
                rows.extend(fold['predictions'])
            validate_rows(rows,expected)
            by_key={(r['tool_id'],r['cycle']):r for r in rows}
            scores=np.clip(np.asarray([sum(by_key[key]['probabilities'][:5]) for key in keys]),0,1)
            cube[method].append(scores)
            calculated={'seed':seed,'average_precision':float(average_precision_score(labels,scores)),
                        'brier':float(brier_score_loss(labels,scores))}
            saved=next(r for r in report['metrics'][method] if r['seed']==seed)
            if any(abs(saved[k]-calculated[k])>1e-7 for k in ('average_precision','brier')):
                raise ValueError('Saved metrics disagree with complete verified predictions')
            metrics[method].append(calculated)
    if 'logistic' not in cube:raise ValueError('Matched logistic comparator required')
    summary={}
    for method,values in metrics.items():
        ap=[v['average_precision'] for v in values];brier=[v['brier'] for v in values]
        summary[method]={'average_precision_mean':float(np.mean(ap)),'average_precision_seed_range':[min(ap),max(ap)],
                         'brier_mean':float(np.mean(brier)),'per_seed':values,
                         'paired_vs_logistic':paired_interval(labels,cube[method],cube['logistic'],cluster_ids,repeats)}
    result={'n':len(keys),'positive_cuts':int(labels.sum()),'positive_rate':float(labels.mean()),'seeds':report['seeds'],
            'input_report_sha256':hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
            'analysis_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'methods':summary,
            'qualification':'Previously explored single-machine development data. No independent confirmation, plant-validity or superiority claim.'}
    atomic_json(directory/'comparison-analysis.json',result)
    lines=['# Expanded grouped model comparison','','All held-out identities, source targets and linked-workpiece splits were validated before analysis.',
           f"Cohort: {len(keys)} eligible cuts, {int(labels.sum())} positives, {len(np.unique(cluster_ids))} connected-workpiece clusters. Seeds: {report['seeds']}.",'',
           '| Method | Mean AP | AP seed range | Mean Brier | Paired AP delta vs logistic, bootstrap 95% |',
           '|---|---:|---|---:|---|']
    for method,value in summary.items():
        interval=value['paired_vs_logistic']['ap_delta_95_interval']
        lines.append(f"| {method} | {value['average_precision_mean']:.4f} | {value['average_precision_seed_range'][0]:.4f}–{value['average_precision_seed_range'][1]:.4f} | {value['brier_mean']:.4f} | {interval} |")
    lines += ['','Intervals are paired connected-workpiece bootstrap approximations on few clusters, conditional on fitted models. They are not independent-machine confirmation or a guarantee under domain shift. Seeds are repeated optimization runs on the same data, not independent samples. Inspection utility must be assessed separately.']
    (directory/'comparison-analysis.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({m:{k:v[k] for k in ('average_precision_mean','brier_mean')} for m,v in summary.items()},indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--replicates',type=int,default=1000)
    args=parser.parse_args()
    if not 25<=args.replicates<=10000:parser.error('Use 25..10000 replicates')
    evaluate(args.directory,args.replicates)
