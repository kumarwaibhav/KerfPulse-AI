import numpy as np
import pytest
from pdm.research_evaluation import validate_rows, paired_interval
from pdm.gpu_benchmark import prepare


def test_prediction_validation_rejects_duplicate_and_wrong_target():
    observations,_=prepare()
    cut,remaining=observations[0]
    row={'tool_id':cut.tool_id,'cycle':cut.cycle,'remaining':remaining,'probabilities':[1/9]*9}
    expected={(cut.tool_id,cut.cycle):remaining}
    validate_rows([row],expected)
    with pytest.raises(ValueError):validate_rows([row,row],expected)
    with pytest.raises(ValueError):validate_rows([{**row,'remaining':remaining+1}],expected)
    with pytest.raises(ValueError):validate_rows([{**row,'probabilities':[float('nan')]*9}],expected)


def test_paired_cluster_interval_identical_models_is_zero():
    observations,groups=prepare()
    labels=np.array([r<=5 for _,r in observations])
    clusters=np.array([groups[c.tool_id] for c,_ in observations])
    # Mathematical prediction fixture, never substituted for sensor measurements.
    scores=np.linspace(.01,.8,len(labels))
    result=paired_interval(labels,[scores],[scores],clusters,repeats=25)
    assert result['ap_delta_95_interval']==[0.,0.]
    assert result['valid_replicates']>0
