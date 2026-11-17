from pdm.gpu_benchmark import prepare, partitions, names_for, candidates
import pytest


def test_group_splits_and_age_ablation():
    rows, groups = prepare()
    seen = []
    for train, test, _ in partitions(rows, groups, 'workpiece'):
        assert {groups[rows[i][0].tool_id] for i in train}.isdisjoint({groups[rows[i][0].tool_id] for i in test})
        seen.extend(test)
    assert sorted(seen) == list(range(len(rows)))
    assert names_for(rows[0][0], 'age_only') == ['NumberOfCycle']
    assert 'NumberOfCycle' not in names_for(rows[0][0], 'current_no_age')
    assert len(candidates('xgboost',20)) == 20
    assert len({str(c) for c in candidates('xgboost',20)}) == 20


def test_search_space_limits_fail_instead_of_looping_forever():
    for method,count in [('random_forest',49),('xgboost',82),('mlp',82),('logistic',0)]:
        with pytest.raises(ValueError):candidates(method,count)
