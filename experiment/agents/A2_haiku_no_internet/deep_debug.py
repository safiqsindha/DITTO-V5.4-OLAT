#!/usr/bin/env python3
"""Deep debug of causal incoherence rule."""

import json
import re

def parse_chain(chain_text):
    steps = []
    step_pattern = r"Step \d+\s*\(turn=(\d+)\):(.*?)(?=Step \d+|$)"
    for match in re.finditer(step_pattern, chain_text, re.DOTALL):
        turn = int(match.group(1))
        content = match.group(2).strip()
        step = {"turn": turn, "raw": content, "lines": content.split("\n")}
        steps.append(step)
    return steps

def debug_causal(chain_text, chain_id):
    steps = parse_chain(chain_text)
    print(f"\n=== {chain_id} ===")
    print(f"Total steps: {len(steps)}")

    permanent_faint_units = set()
    availability_history = {}
    has_own_faint = False
    own_faint_window_has_permanent = False

    for step_idx, step in enumerate(steps):
        print(f"\nStep {step_idx+1} (turn {step['turn']}):")
        for line in step["lines"]:
            # Track permanent faint
            match = re.search(r"ToolAvailability:\s+(unit_\w+)\s+is now UNAVAILABLE\s*\(\s*permanent\s*\)", line)
            if match:
                unit = match.group(1)
                permanent_faint_units.add(unit)
                own_faint_window_has_permanent = True
                print(f"  PERMANENT FAINT: {unit}")

            # Rule 1: Permanently fainted unit receiving AVAILABLE
            match = re.search(r"ToolAvailability:\s+(unit_\w+)\s+is now AVAILABLE", line)
            if match:
                unit = match.group(1)
                if unit in permanent_faint_units:
                    print(f"  RULE 1 VIOLATION: {unit} became AVAILABLE after permanent faint!")
                    return "Rule 1"
                else:
                    print(f"  AVAILABLE: {unit}")

            # Track all availability changes
            match = re.search(r"ToolAvailability:\s+(unit_\w+)\s+is now (AVAILABLE|UNAVAILABLE)", line)
            if match:
                unit = match.group(1)
                event = match.group(2)
                if unit not in availability_history:
                    availability_history[unit] = []
                availability_history[unit].append((step_idx, step['turn'], event))
                if "permanent" not in line and "recover_in" not in line:
                    print(f"    Tracked: {unit} -> {event}")

            # Track own_faint
            if "trigger=own_faint" in line:
                has_own_faint = True
                own_faint_window_has_permanent = False
                print(f"  TRIGGER own_faint")

    print(f"\nPermanent faint units: {permanent_faint_units}")
    print(f"Has own_faint: {has_own_faint}, window_has_permanent: {own_faint_window_has_permanent}")

    # Rule 3: Same-turn UNAVAIL → AVAIL
    print(f"\nChecking Rule 3 (same-turn UNAVAIL→AVAIL)...")
    for unit, history in availability_history.items():
        print(f"  {unit}: {history}")
        for i in range(len(history) - 1):
            step_i, turn_i, event_i = history[i]
            step_i_plus_1, turn_i_plus_1, event_i_plus_1 = history[i + 1]
            if turn_i == turn_i_plus_1 and event_i == "UNAVAILABLE" and event_i_plus_1 == "AVAILABLE":
                print(f"    RULE 3 VIOLATION: {unit} went UNAVAIL→AVAIL in turn {turn_i}")
                return "Rule 3"

    # Rule 5: own_faint without permanent
    print(f"\nChecking Rule 5 (own_faint without permanent)...")
    if has_own_faint and not own_faint_window_has_permanent:
        print(f"  RULE 5 VIOLATION")
        return "Rule 5"

    return None

# Load chains
chains = []
with open("/home/user/DITTO-V5.4-OLAT/experiment/chains/development_set.jsonl") as f:
    for line in f:
        chains.append(json.loads(line))

for chain_id in ["gen9ou-2348078225_p1", "gen9ou-2276761872_p1"]:
    chain = next((c for c in chains if c["chain_id"] == chain_id), None)
    if chain:
        result = debug_causal(chain['chain_text'], chain_id)
        print(f"\nFiring rule: {result}")
