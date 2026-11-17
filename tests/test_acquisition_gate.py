import math
import pytest
from pdm.acquisition_gate import AcquisitionState, choose_evidence, realized_decision_loss


def test_gate_never_reads_unrequested_evidence_and_respects_every_prefix():
    current=[0.]*8+[1.]
    def forbidden(): raise AssertionError('Unreleased vibration accessed')
    state=AcquisitionState()
    assert not choose_evidence(current,-1,1,state,forbidden)['acquired']
    assert not choose_evidence(current,1,4,state,forbidden)['acquired']
    requested=[]
    def measured_prediction(): requested.append(1); return current
    for _ in range(100):
        result=choose_evidence(current,1,1,state,measured_prediction)
        assert state.acquired<=math.ceil(state.eligible*.25)
    assert len(requested)==state.acquired


def test_inspection_gain_labels_use_correct_slot_window():
    near=[0.]*9;near[2]=1.
    quiet=[0.]*8+[1.]
    assert realized_decision_loss(near,3,1)==1
    assert realized_decision_loss(quiet,3,1)==20
    assert realized_decision_loss(quiet,2,1)==0
    with pytest.raises(ValueError): choose_evidence(quiet,float('nan'),1,AcquisitionState(),lambda:quiet)


def test_invalid_optional_evidence_does_not_advance_budget():
    state=AcquisitionState()
    quiet=[0.]*8+[1.]
    with pytest.raises(ValueError): choose_evidence(quiet,1,1,state,lambda:[float('nan')]*9)
    assert state==AcquisitionState()
