from pdm.dataset import audit, load
from pdm.policy import PolicyState, decide, outcome
import pytest


def test_pinned_dataset_integrity():
    report = audit()
    assert report["eligible_pre_damage_cuts"] == 952
    assert report["tools"] == 14
    assert report["missing_ordinals"] == 21
    assert report["quarantined_rows"] == 2
    assert report["first_cut_damage_tools"] == [11]
    tool = load()[2]
    assert tool.cuts[33].status == "conflict"
    assert tool.cuts[-1].context == {}
    assert tool.cuts[-1].current == {}


def test_every_prefix_respects_release_cap():
    state = PolicyState()
    probability = [0, 0, 0.2, 0.2, 0.1, 0, 0, 0, 0.5]
    for cycle in range(1, 151):
        decision = decide(state, cycle, probability, probability, "decision")
        assert state.released <= state.eligible // 4
        if decision["slot"] is not None:
            assert decision["slot"] > cycle


def test_periodic_releases_every_fourth_accepted_cut():
    state = PolicyState()
    probability = [0, 0, 0, 0, 0, 0, 0, 0, 1]
    released = [cycle for cycle in range(1, 21)
                if decide(state, cycle, probability, probability, "periodic")["vibration_released"]]
    assert released == [4, 8, 12, 16, 20]


def test_inspection_boundaries_and_first_cut_failure():
    assert outcome(10, 5) == "timely"
    assert outcome(10, 8) == "timely"
    assert outcome(10, 9) == "late"
    assert outcome(10, 4) == "premature"
    assert outcome(1, None) == "no_inspection"


def test_future_slot_requires_two_to_five_cuts_of_lead():
    late = [0.0] * 9
    late[2] = 1.0  # decision after cut 1, damage 4, slot 3: one cut of lead
    assert decide(PolicyState(), 1, late, late, "current")["status"] == "monitor"
    timely = [0.0] * 9
    timely[5] = 1.0  # damage 7, slot 3: four cuts of lead
    assert decide(PolicyState(), 1, timely, timely, "current")["status"] == "inspect"


def test_retries_do_not_mint_release_quota():
    state = PolicyState()
    probability = [0.0] * 8 + [1.0]
    decide(state, 1, probability, probability, "periodic")
    with pytest.raises(ValueError, match="increase strictly"):
        decide(state, 1, probability, probability, "periodic")
    assert state.eligible == 1
    assert state.released == 0


def test_invalid_probability_does_not_change_state():
    state = PolicyState()
    with pytest.raises(ValueError, match="probability"):
        decide(state, 1, [float("nan")] * 9, [0.0] * 8 + [1.0], "current")
    assert state.last_cycle == 0
    assert state.eligible == 0


@pytest.mark.parametrize("interval", [1.0, True, 0, 4])
def test_invalid_interval_does_not_change_state(interval):
    state = PolicyState()
    probability = [0.0] * 8 + [1.0]
    with pytest.raises(ValueError, match="Inspection interval"):
        decide(state, 1, probability, probability, "current", slot_interval=interval)
    assert state.last_cycle == 0
    assert state.eligible == 0
