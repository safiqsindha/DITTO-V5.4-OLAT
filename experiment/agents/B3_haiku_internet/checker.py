"""
B3 Checker: Haiku (3.5, standard thinking), WITH internet access - Final
Symbolic constraint violation detector for Pokemon battle chains.

Rules derived from analysis of 30 development chains, validated with web
research on Pokemon Showdown mechanics (Bulbapedia, Pokémon Showdown FAQ,
Smogon documentation).

Key findings from internet research:
  - Fainted Pokémon remain removed from active battle until next switch
    (permanent in-battle context)
  - Move PP strictly monotone-decreasing within single battle (confirmed
    via Showdown mechanics)
  - "trigger=own_faint" indicates forced switch mechanics

Design philosophy: rules fire only on physical/causal impossibilities.
FP-conservative approach: include only rules with zero false positives
on all 15 intact development chains.
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
        availability = {}    # unit -> [(step_idx, AVAILABLE|UNAVAILABLE, is_permanent)]
        permanent_units = set()
        permanent_step = {}  # unit -> step_idx of first permanent
        has_own_faint = False

        for idx, step in enumerate(steps):
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
                    availability.setdefault(unit, []).append((idx, state, is_perm))
                    if state == "UNAVAILABLE" and is_perm:
                        if unit not in permanent_units:
                            permanent_step[unit] = idx
                        permanent_units.add(unit)
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
            for sidx, state, _ in ev["availability"].get(unit, []):
                if sidx > pstep and state == "AVAILABLE":
                    return True
        return False

    def _own_faint_without_any_permanent(self, ev) -> bool:
        """
        A trigger=own_faint appears but the chain contains NO
        UNAVAILABLE(permanent) event anywhere.

        Reasoning: own_faint mechanics in Pokemon require a forced switch
        (the fainted unit must be permanently removed). A trigger=own_faint
        without any permanent UNAVAILABLE in the chain indicates missing
        or incoherent faint mechanics.
        """
        # Check if own_faint present but NO permanents anywhere
        if ev["has_own_faint"]:
            return len(ev["permanent_units"]) == 0
        return False
