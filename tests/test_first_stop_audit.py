import pytest
from pdm.first_stop_audit import prefix_quota,timely_slots


def test_floor_prefix_quota_and_invalid_counts():
    assert [prefix_quota(n) for n in range(9)]==[0,0,0,0,1,1,1,1,2]
    for value in (-1,True,1.5):
        with pytest.raises(ValueError):prefix_quota(value)


def test_only_recorded_cuts_create_future_opportunities():
    assert timely_slots(50,[42,43,44,45,46,47])==[45,48]
    assert timely_slots(50,[42])==[45]
    assert timely_slots(50,[33])==[]
    assert timely_slots(1,[])==[]
    assert timely_slots(50,[])==[]  # unsupported/no observations has no invented opportunity
    for cycles in ([50],[43,43],[True]):
        with pytest.raises(ValueError):timely_slots(50,cycles)


def test_saved_real_experiment_retains_unknown_acquisition_timing(tmp_path):
    from pathlib import Path
    from pdm.first_stop_audit import audit
    directory=Path('artifacts/acquisition-regret-development-v1')
    if not (directory/'report.json').exists():pytest.skip('Historical experiment not acquired/reproduced')
    result=audit(directory,tmp_path/'audit.json')
    assert result['supported_cuts']==375 and result['unsupported_cuts']==577
    assert result['coverage']=={'supported':5,'unsupported_recipe':8,'no_pre_damage_observation':1}
    tool=next(t for t in result['tools'] if t['tool_id']==9)
    assert tool['attainable_timely_slots']==[147]
    assert tool['policies']['regret_gate']['total_acquisitions']==29
    assert tool['policies']['regret_gate']['acquisitions_before_first_decision'] is None
    assert tool['policies']['current']['acquisitions_before_first_decision']==0
