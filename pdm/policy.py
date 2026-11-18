"""Causal optional-feature release and first-inspection scoring."""

from dataclasses import dataclass
import math


@dataclass
class PolicyState:
    eligible: int = 0
    released: int = 0
    first_slot: int | None = None
    last_cycle: int = 0


def decide(state, cycle, current, fused, policy, slot_interval=3, threshold=0.5):
    if policy not in ("current", "periodic", "decision", "fused"):
        raise ValueError("Unknown release policy")
    if isinstance(cycle, bool) or not isinstance(cycle, int) or cycle <= state.last_cycle:
        raise ValueError("Cycle ordinal must increase strictly within a run")
    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("Threshold must be a finite probability")
    if isinstance(slot_interval, bool) or not isinstance(slot_interval, int) or slot_interval not in (1, 2, 3):
        raise ValueError("Inspection interval must be 1, 2 or 3 cuts for this forecast horizon")
    if len(current) != 9 or len(fused) != 9:
        raise ValueError("Expected remaining-cut classes 1 through 8 and greater than 8")
    for values in (current, fused):
        if any(not math.isfinite(value) or value < 0 or value > 1 for value in values):
            raise ValueError("Invalid probability values")
        if not math.isclose(sum(values), 1, abs_tol=1e-6):
            raise ValueError("Probabilities must sum to one")
    state.last_cycle = cycle
    state.eligible += 1
    slot = (cycle // slot_interval + 1) * slot_interval
    # A prediction made after a completed cut can affect only a future break.
    offsets = list(range(slot - cycle + 2, slot - cycle + 6))
    actionable = sum(current[offset - 1] for offset in offsets)
    quota = state.eligible // 4
    wanted = policy == "fused" or (policy == "periodic" and state.eligible % 4 == 0)
    if policy == "decision":
        wanted = abs(actionable - threshold) <= 0.2
    release = wanted and (policy == "fused" or state.released < quota)
    probability = fused if release else current
    state.released += int(release)
    actionable = sum(probability[offset - 1] for offset in offsets)
    status = "monitor"
    if not offsets:
        status = "no_feasible_slot"
    elif policy == "decision" and wanted and not release:
        status = "deferred"
    elif actionable >= threshold:
        status = "inspect"
        if state.first_slot is None:
            state.first_slot = slot
    return {"status": status, "risk": sum(probability[:5]), "actionable_risk": actionable,
            "slot": slot if status == "inspect" else None, "vibration_released": release,
            "eligible": state.eligible, "released": state.released, "quota": quota}


def outcome(damage_cycle, first_slot):
    if first_slot is None:
        return "no_inspection"
    lead = damage_cycle - first_slot
    if lead > 5:
        return "premature"
    return "timely" if lead >= 2 else "late"
