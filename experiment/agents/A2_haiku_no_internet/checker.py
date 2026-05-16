"""
A2 Checker: Haiku (no internet) - Cycle 3 (Final)
Symbolic constraint violation detector for Pokemon battle chains.
"""

import re
from typing import Dict, List, Tuple, Any


class ConstraintChecker:
    """Detects violations in Pokemon battle constraint chains."""

    def __init__(self):
        self.violations = []

    def check_chain(self, chain_text: str) -> Tuple[bool, str]:
        """
        Main entry point. Returns (violation_detected, violation_type).
        """
        self.violations = []

        # Parse chain into steps
        steps = self._parse_chain(chain_text)
        if not steps:
            return False, "none"

        # Run all detection rules
        if self._detect_hp_resurrection_zero_to_positive(steps):
            return True, "hp_resurrection"
        if self._detect_hp_resurrection_permanent_faint(steps):
            return True, "hp_resurrection"
        if self._detect_pp_monotone_violation(steps):
            return True, "monotone_increase"
        if self._detect_causal_incoherence(steps):
            return True, "causal_incoherence"

        return False, "none"

    def _parse_chain(self, chain_text: str) -> List[Dict[str, Any]]:
        """Parse chain text into structured steps."""
        steps = []
        step_pattern = r"Step \d+\s*\(turn=(\d+)\):(.*?)(?=Step \d+|$)"

        for match in re.finditer(step_pattern, chain_text, re.DOTALL):
            turn = int(match.group(1))
            content = match.group(2).strip()

            step = {"turn": turn, "raw": content, "lines": content.split("\n")}
            steps.append(step)

        return steps

    def _detect_hp_resurrection_zero_to_positive(self, steps: List[Dict]) -> bool:
        """
        Detect when a unit's HP goes from 0.0% to >0%.
        This is a physical impossibility in a normal game.
        """
        hp_history = {}  # unit -> [(step_idx, hp_value)]

        for step_idx, step in enumerate(steps):
            for line in step["lines"]:
                # ResourceBudget: hp_unit_X at Y.Y%
                match = re.search(r"ResourceBudget:\s+hp_(unit_\w+)\s+at\s+([\d.]+)%", line)
                if match:
                    unit = match.group(1)
                    hp = float(match.group(2))

                    if unit not in hp_history:
                        hp_history[unit] = []
                    hp_history[unit].append((step_idx, hp))

                    # Check: if we previously saw 0.0%, and now we see > 0%, that's a violation
                    if len(hp_history[unit]) >= 2:
                        prev_hp = hp_history[unit][-2][1]
                        if prev_hp == 0.0 and hp > 0.0:
                            return True

        return False

    def _detect_hp_resurrection_permanent_faint(self, steps: List[Dict]) -> bool:
        """
        Detect when a unit marked UNAVAILABLE(permanent) later shows HP > 0%.
        A permanently fainted unit cannot have positive HP.
        """
        permanent_faint_units = set()

        for step in steps:
            for line in step["lines"]:
                # ToolAvailability: unit_X is now UNAVAILABLE (permanent)
                match = re.search(r"ToolAvailability:\s+(unit_\w+)\s+is now UNAVAILABLE\s*\(\s*permanent\s*\)", line)
                if match:
                    permanent_faint_units.add(match.group(1))

                # Check if a permanently fainted unit has HP > 0%
                match = re.search(r"ResourceBudget:\s+hp_(unit_\w+)\s+at\s+([\d.]+)%", line)
                if match:
                    unit = match.group(1)
                    hp = float(match.group(2))
                    if unit in permanent_faint_units and hp > 0.0:
                        return True

        return False

    def _detect_pp_monotone_violation(self, steps: List[Dict]) -> bool:
        """
        Detect when a resource marked decay=monotone_decrease increases.
        Also covers pp_action_* resources without explicit annotation.
        """
        resource_history = {}  # resource_name -> [(step_idx, value)]

        for step_idx, step in enumerate(steps):
            for line in step["lines"]:
                # ResourceBudget: resource_name at X.X% (decay=monotone_decrease)
                # Also: pp_action_* at X.X% with or without annotation
                match = re.search(r"ResourceBudget:\s+([\w_]+)\s+at\s+([\d.]+)%", line)
                if match:
                    resource = match.group(1)
                    value = float(match.group(2))

                    # Check if this is a monotone-decrease resource
                    is_monotone = "decay=monotone_decrease" in line or resource.startswith("pp_action_") or resource == "match_time_remaining"

                    if is_monotone:
                        if resource not in resource_history:
                            resource_history[resource] = []

                        # Check for increase violation
                        if resource_history[resource]:
                            prev_value = resource_history[resource][-1][1]
                            if value > prev_value:
                                return True

                        resource_history[resource].append((step_idx, value))

        return False

    def _detect_causal_incoherence(self, steps: List[Dict]) -> bool:
        """
        Detect causal ordering violations:
        1. A permanently fainted unit receives AVAILABLE event
        3. Unit goes UNAVAILABLE → AVAILABLE in same turn
        """
        permanent_faint_units = set()
        availability_history = {}  # unit -> [(step_idx, turn, event)]

        for step_idx, step in enumerate(steps):
            for line in step["lines"]:
                turn = step["turn"]

                # Track permanent faint
                match = re.search(r"ToolAvailability:\s+(unit_\w+)\s+is now UNAVAILABLE\s*\(\s*permanent\s*\)", line)
                if match:
                    unit = match.group(1)
                    permanent_faint_units.add(unit)

                # Rule 1: Permanently fainted unit receiving AVAILABLE
                match = re.search(r"ToolAvailability:\s+(unit_\w+)\s+is now AVAILABLE", line)
                if match:
                    unit = match.group(1)
                    if unit in permanent_faint_units:
                        return True

                # Track all availability changes for same-turn check
                match = re.search(r"ToolAvailability:\s+(unit_\w+)\s+is now (AVAILABLE|UNAVAILABLE)", line)
                if match:
                    unit = match.group(1)
                    event = match.group(2)
                    if unit not in availability_history:
                        availability_history[unit] = []
                    availability_history[unit].append((step_idx, turn, event))

        # Rule 3: Same-turn UNAVAIL → AVAIL
        for unit, history in availability_history.items():
            for i in range(len(history) - 1):
                step_i, turn_i, event_i = history[i]
                step_i_plus_1, turn_i_plus_1, event_i_plus_1 = history[i + 1]
                if turn_i == turn_i_plus_1 and event_i == "UNAVAILABLE" and event_i_plus_1 == "AVAILABLE":
                    return True

        return False
