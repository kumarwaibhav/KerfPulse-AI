"""Causal, calendar-conditioned acquisition primitive for research evaluation.

Expected gains must come from a model trained on training-only cross-fitted
decisions. This module never reads unreleased vibration or future outcomes.
"""
from dataclasses import dataclass
import math


@dataclass
class AcquisitionState:
    eligible: int=0
    acquired: int=0


def choose_evidence(current, estimated_gain, inspection_offset, state, acquire_fused, budget=.25):
    if len(current)!=9 or any(not math.isfinite(p) or p<0 for p in current) or abs(sum(current)-1)>1e-5:
        raise ValueError('Expected nine normalized probabilities')
    if not math.isfinite(estimated_gain) or not 0<budget<=1:
        raise ValueError('Finite gain and budget in (0,1] required')
    next_eligible=state.eligible+1
    feasible=type(inspection_offset) is int and 1<=inspection_offset<=3
    quota=math.ceil(next_eligible*budget)
    requested=feasible and estimated_gain>0 and state.acquired<quota
    probability=list(current)
    if requested:
        # Optional measurements are fetched only after the cheap gate commits its request.
        probability=list(acquire_fused())
        if len(probability)!=9 or any(not math.isfinite(p) or p<0 for p in probability) or abs(sum(probability)-1)>1e-5:
            raise ValueError('Optional predictor returned invalid probabilities')
        state.acquired+=1
    state.eligible=next_eligible
    return {'probabilities':probability,'acquired':requested,'eligible':state.eligible,'acquired_total':state.acquired,'prefix_quota':quota,
            'reason':'positive_expected_decision_gain' if requested else 'no_feasible_break' if not feasible else 'budget_or_gain_deferred'}


def realized_decision_loss(probability, remaining, inspection_offset, inspection_cost=1., missed_window_cost=20.):
    """Training-only immediate decision-loss proxy, not avoided-failure ROI."""
    if type(inspection_offset) is not int or not 1<=inspection_offset<=3:
        raise ValueError('Unsupported calendar offset')
    if inspection_cost<=0 or missed_window_cost<=0: raise ValueError('Positive costs required')
    actionable=sum(probability[inspection_offset+1:inspection_offset+5])
    inspect=inspection_cost<=missed_window_cost*actionable
    observed_window=inspection_offset+2<=remaining<=inspection_offset+5
    return inspection_cost if inspect else missed_window_cost*int(observed_window)
