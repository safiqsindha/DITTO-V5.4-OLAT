"""
B1 Checker: Opus 4.7 (max effort, WITH internet) - Final
Symbolic constraint violation detector for Pokemon battle chains.

Rules derived from analysis of 30 development chains + training knowledge,
then independently CONFIRMED via 3 targeted web searches (Bulbapedia,
Pokemon Showdown SIM-PROTOCOL, Smogon):

  - Faint = permanent removal; a fainted Pokemon cannot return or restore
    HP within the same battle  -> confirms rules 1, 2, 4, 5
  - Move PP can only decrease within a battle, never increase
    -> confirms rule 3
  - HP CAN legitimately increase from a non-zero value via healing moves
    (Recover, Roost, etc.) -> confirms the 0->positive scoping of rule 1
    is correct and necessary to avoid false positives
  - "Any Pokemon that faints must also be recalled" (permanent)
    -> confirms rule 7 (own_faint with no permanent = incoherent)

Net effect of internet at the Opus tier: ZERO new rules, ZERO rule
changes. Every rule Opus derived from data in the no-internet run (A3)
was confirmed correct; internet found nothing additional. (Contrast:
at the Sonnet tier, internet gave B2 one extra rule, +0.040 dev F1.)

Design philosophy: rules fire only on physical/causal impossibilities.
Precision is prioritized; every rule is verified FP-clean on all 15
intact development chains before inclusion.
"""

import re
from typing import Dict, List, Tuple, Any


class ConstraintChecker:
    """Detects violations in Pokemon battle constraint chains."""

    def check_chain(self, chain_text: str) -> Tuple[bool, str]:
        """Main entry point. Returns (violation_detected, violation_type)."""
        steps = self._parse_chain(chain_text)
        if not steps:
            return False, "none"

        events = self._extract_events(steps)

        if self._hp_resurrection_zero_to_positive(events):
            return True, "hp_resurrection"
        if self._hp_positive_after_permanent_faint(events):
            return True, "hp_resurrection"
        if self._monotone_increase(events):
            return True, "monotone_increase"
        if self._permanent_revived(events):
            return True, "causal_incoherence"
        if self._permanent_re_unavailable(events):
            return True, "causal_incoherence"
        if self._same_turn_unavail_then_avail(events):
            return True, "causal_incoherence"
        if self._own_faint_without_any_permanent(events):
            return True, "causal_incoherence"

        return False, "none"

    # ---------- parsing ----------

    def _parse_chain(self, chain_text: str) -> List[Dict[str, Any]]:
        steps = []
        pattern = r"Step \d+\s*\(turn=(\d+)\):(.*?)(?=Step \d+|$)"
        for m in re.finditer(pattern, chain_text, re.DOTALL):
            steps.append({
                "turn": int(m.group(1)),
                "lines": [ln.strip() for ln in m.group(2).strip().split("\n") if ln.strip()],
            })
        return steps

    def _extract_events(self, steps: List[Dict]) -> Dict[str, Any]:
        """Single pass: build normalized event structures."""
        hp_obs = {}          # unit -> [(step_idx, hp)]
        resource_obs = {}    # resource -> [(step_idx, value)]
        availability = {}    # unit -> [(step_idx, turn, AVAILABLE|UNAVAILABLE, is_permanent)]
        permanent_units = set()
        permanent_step = {}  # unit -> step_idx of first permanent
        has_own_faint = False
        any_permanent = False

        for idx, step in enumerate(steps):
            turn = step["turn"]
            for line in step["lines"]:
                m = re.search(r"ResourceBudget:\s+hp_(unit_\w+)\s+at\s+([\d.]+)%", line)
                if m:
                    hp_obs.setdefault(m.group(1), []).append((idx, float(m.group(2))))
                    continue

                m = re.search(r"ResourceBudget:\s+([\w_]+)\s+at\s+([\d.]+)%", line)
                if m:
                    name, val = m.group(1), float(m.group(2))
                    monotone = ("decay=monotone_decrease" in line
                                or name.startswith("pp_action_")
                                or name == "match_time_remaining")
                    if monotone:
                        resource_obs.setdefault(name, []).append((idx, val))
                    continue

                m = re.search(r"ToolAvailability:\s+(unit_\w+)\s+is now (AVAILABLE|UNAVAILABLE)(.*)", line)
                if m:
                    unit, state, tail = m.group(1), m.group(2), m.group(3)
                    is_perm = "permanent" in tail
                    availability.setdefault(unit, []).append((idx, turn, state, is_perm))
                    if state == "UNAVAILABLE" and is_perm:
                        if unit not in permanent_units:
                            permanent_step[unit] = idx
                        permanent_units.add(unit)
                        any_permanent = True
                    continue

                if "trigger=own_faint" in line:
                    has_own_faint = True

        return {
            "hp_obs": hp_obs,
            "resource_obs": resource_obs,
            "availability": availability,
            "permanent_units": permanent_units,
            "permanent_step": permanent_step,
            "has_own_faint": has_own_faint,
            "any_permanent": any_permanent,
        }

    # ---------- rules ----------

    def _hp_resurrection_zero_to_positive(self, ev) -> bool:
        """A unit observed at HP 0.0% later observed at HP > 0%."""
        for unit, obs in ev["hp_obs"].items():
            seen_zero = False
            for _, hp in obs:
                if hp == 0.0:
                    seen_zero = True
                elif seen_zero and hp > 0.0:
                    return True
        return False

    def _hp_positive_after_permanent_faint(self, ev) -> bool:
        """A permanently fainted unit later shows HP > 0%."""
        for unit in ev["permanent_units"]:
            pstep = ev["permanent_step"][unit]
            for sidx, hp in ev["hp_obs"].get(unit, []):
                if sidx > pstep and hp > 0.0:
                    return True
        return False

    def _monotone_increase(self, ev) -> bool:
        """A monotone-decrease resource increases between observations."""
        for name, obs in ev["resource_obs"].items():
            for i in range(1, len(obs)):
                if obs[i][1] > obs[i - 1][1]:
                    return True
        return False

    def _permanent_revived(self, ev) -> bool:
        """A permanently fainted unit receives a later AVAILABLE event."""
        for unit in ev["permanent_units"]:
            pstep = ev["permanent_step"][unit]
            for sidx, _, state, _ in ev["availability"].get(unit, []):
                if sidx > pstep and state == "AVAILABLE":
                    return True
        return False

    def _permanent_re_unavailable(self, ev) -> bool:
        """A permanently fainted unit receives a later non-permanent UNAVAILABLE."""
        for unit in ev["permanent_units"]:
            pstep = ev["permanent_step"][unit]
            for sidx, _, state, is_perm in ev["availability"].get(unit, []):
                if sidx > pstep and state == "UNAVAILABLE" and not is_perm:
                    return True
        return False

    def _same_turn_unavail_then_avail(self, ev) -> bool:
        """Same unit goes UNAVAILABLE then AVAILABLE within one turn."""
        for unit, hist in ev["availability"].items():
            for i in range(len(hist) - 1):
                _, t0, s0, _ = hist[i]
                _, t1, s1, _ = hist[i + 1]
                if t0 == t1 and s0 == "UNAVAILABLE" and s1 == "AVAILABLE":
                    return True
        return False

    def _own_faint_without_any_permanent(self, ev) -> bool:
        """
        A trigger=own_faint appears but the chain contains NO
        UNAVAILABLE(permanent) event anywhere.

        Reasoning (no internet, derived from dev data): a faint causes
        permanent removal of the fainted unit. Every intact dev chain
        with trigger=own_faint also contains a permanent UNAVAILABLE
        event somewhere in the 15-step window. own_faint with zero
        permanents anywhere is a missing-permanence incoherence.

        This is the GLOBAL form of the rule (fixes the resetting-window
        bug that produced false positives in smaller-model runs where
        permanent and own_faint co-occurred in the same step batch).
        """
        return ev["has_own_faint"] and not ev["any_permanent"]
