from pdm.experiment_provenance import fingerprint
from pdm.gpu_benchmark import prepare, partitions


def test_provenance_changes_for_labels_and_partitions():
    rows,groups=prepare()
    folds=list(partitions(rows,groups,'workpiece'))
    initial=fingerprint(rows,groups,folds,['age_only'])
    changed=rows.copy();changed[0]=(rows[0][0],rows[0][1]+1)
    assert fingerprint(changed,groups,folds,['age_only'])['observations_sha256']!=initial['observations_sha256']
    assert fingerprint(rows,groups,folds[::-1],['age_only'])['partitions_sha256']!=initial['partitions_sha256']
    assert len(initial['code'])>=7
    assert initial['features']['age_only']==['NumberOfCycle']
