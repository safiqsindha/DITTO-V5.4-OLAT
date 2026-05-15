"""
Pokemon constraint chain symbolic checker.
Agent A1 — Sonnet, no internet. Final (Cycle 3 stable).

Detects violation classes from constraint chain text:

  hp_resurrection:
    (a) hp_unit_X goes from 0.0% to >0% in a later step
    (b) unit_X marked (permanent) UNAVAILABLE but hp_unit_X later appears >0%


  pp_monotone_violation:
    pp_action_X value increases between observations

  causal_incoherence:
    (a) unit acts (in active_pair) while UNAVAILABLE
    (b) unit marked (permanent) UNAVAILABLE later becomes AVAILABLE
    (c) unit marked (permanent) UNAVAILABLE, then marked UNAVAILABLE again
    (d) same unit goes UNAVAILABLE → AVAILABLE in the same turn
    (e) unit UNAVAILABLE → UNAVAILABLE within 2 steps (without AVAILABLE between)
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple


# ── parsers ──────────────────────────────────────────────────────────────────

_RESOURCE_RE  = re.compile(
    r"ResourceBudget:\s*([\w_]+)\s+at\s+([\d.]+)%"
)
_TOOL_AVAIL_RE = re.compile(
    r"ToolAvailability:\s*([\w_]+)\s+is\s+now\s+(AVAILABLE|UNAVAILABLE)"
    r"(?:\s*\(([\w_=]+)\))?"
)
_ACTIVE_RE = re.compile(
    r"active_pair:\s*own=([\w_]+)\s+opp=([\w_]+)"
)
_STEP_RE = re.compile(r"^Step\s+\d+\s+\(turn=\d+\):", re.MULTILINE)


def _parse_steps(chain_text: str) -> List[str]:
    """Split chain text into per-step blocks."""
    positions = [m.start() for m in _STEP_RE.finditer(chain_text)]
    if not positions:
        return [chain_text]
    blocks = []
    for i, pos in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(chain_text)
        blocks.append(chain_text[pos:end])
    return blocks


# ── rule checks ──────────────────────────────────────────────────────────────

def _check_hp_resurrection(steps: List[str]) -> List[str]:
    """
    hp_unit_X at 0.0% followed by hp_unit_X at >0.0% in a later step.
    """
    zeroed: set[str] = set()
    triggered = []
    for step in steps:
        for m in _RESOURCE_RE.finditer(step):
            name, pct_str = m.group(1), m.group(2)
            if not name.startswith("hp_unit"):
                continue
            pct = float(pct_str)
            if pct == 0.0:
                zeroed.add(name)
            elif name in zeroed and pct > 0.0:
                triggered.append(f"hp_resurrection:{name}")
    return ["hp_resurrection"] if triggered else []


def _check_pp_monotone(steps: List[str]) -> List[str]:
    """
    pp_action_X value increases between observations (PP should only decrease).
    """
    last_pct: dict[str, float] = {}
    triggered = []
    for step in steps:
        for m in _RESOURCE_RE.finditer(step):
            name, pct_str = m.group(1), m.group(2)
            if not name.startswith("pp_action"):
                continue
            pct = float(pct_str)
            if name in last_pct and pct > last_pct[name]:
                triggered.append(f"pp_monotone:{name}")
            last_pct[name] = pct
    return ["pp_monotone_violation"] if triggered else []


_STEP_TURN_RE = re.compile(r"Step\s+\d+\s+\(turn=(\d+)\)")


def _check_causal_incoherence(steps: List[str]) -> List[str]:
    """
    Causal incoherence sub-rules — see module docstring for full list.
    """
    availability: dict[str, str] = {}   # unit -> "AVAILABLE" | "UNAVAILABLE"
    permanent_unavail: set[str] = set()
    # track (step_index, turn) of most recent UNAVAILABLE per unit
    last_unavail_step: dict[str, Tuple[int, int]] = {}
    triggered = []

    for step_idx, step in enumerate(steps):
        # Parse current turn number
        turn_m = _STEP_TURN_RE.search(step)
        current_turn = int(turn_m.group(1)) if turn_m else -1

        # Collect all ToolAvailability events in this step, in order
        avail_events: List[Tuple[str, str, str]] = []  # (unit, status, qualifier)
        for m in _TOOL_AVAIL_RE.finditer(step):
            avail_events.append((m.group(1), m.group(2), m.group(3) or ""))

        for unit, status, qualifier in avail_events:
            if status == "UNAVAILABLE":
                if unit in permanent_unavail:
                    triggered.append(f"causal_incoherence:permanent_unit_re_unavailable:{unit}")

                # (f) UNAVAILABLE → UNAVAILABLE within 2 steps (non-permanent first)
                if unit in last_unavail_step:
                    prev_idx, _ = last_unavail_step[unit]
                    if availability.get(unit) == "UNAVAILABLE" and (step_idx - prev_idx) <= 2:
                        triggered.append(f"causal_incoherence:rapid_double_unavailable:{unit}")

                availability[unit] = "UNAVAILABLE"
                last_unavail_step[unit] = (step_idx, current_turn)
                if qualifier == "permanent":
                    permanent_unavail.add(unit)

            else:  # AVAILABLE
                if unit in permanent_unavail:
                    triggered.append(f"causal_incoherence:permanent_unit_revived:{unit}")

                # (d) same unit UNAVAILABLE → AVAILABLE in the same turn
                if (availability.get(unit) == "UNAVAILABLE"
                        and unit in last_unavail_step
                        and last_unavail_step[unit][1] == current_turn):
                    triggered.append(f"causal_incoherence:unavail_to_avail_same_turn:{unit}")

                availability[unit] = "AVAILABLE"

        # (a) Check active_pair: unit in pair while UNAVAILABLE
        ap = _ACTIVE_RE.search(step)
        if ap:
            for unit in (ap.group(1), ap.group(2)):
                if unit == "None":
                    continue
                if availability.get(unit) == "UNAVAILABLE":
                    triggered.append(f"causal_incoherence:active_while_unavailable:{unit}")

    return ["causal_incoherence"] if triggered else []



def _check_permanent_faint_resurrection(steps: List[str]) -> List[str]:
    """
    hp_unit_X appears at >0% after unit_X was marked (permanent) UNAVAILABLE.
    A fainted unit cannot have positive HP.
    """
    permanent_fainted: set[str] = set()
    triggered = []
    for step in steps:
        for m in _TOOL_AVAIL_RE.finditer(step):
            if m.group(2) == "UNAVAILABLE" and (m.group(3) or "") == "permanent":
                permanent_fainted.add(m.group(1))
        for m in _RESOURCE_RE.finditer(step):
            name, pct_str = m.group(1), m.group(2)
            if not name.startswith("hp_unit"):
                continue
            unit = name[len("hp_"):]  # "unit_X"
            if unit in permanent_fainted and float(pct_str) > 0.0:
                triggered.append(f"hp_resurrection:permanent_faint:{unit}")
    return ["hp_resurrection"] if triggered else []


# ── public API ────────────────────────────────────────────────────────────────

def check_chain(chain: dict) -> dict:
    """
    Args:
        chain: dict with at least "chain_text" or "prompt_user" key containing
               the constraint chain text.

    Returns:
        {"verdict": "YES" or "NO", "triggered_rules": [list of rule names]}
    """
    chain_text: str = chain.get("chain_text") or chain.get("prompt_user", "")

    steps = _parse_steps(chain_text)

    triggered_rules: List[str] = []
    triggered_rules.extend(_check_hp_resurrection(steps))
    triggered_rules.extend(_check_permanent_faint_resurrection(steps))
    triggered_rules.extend(_check_pp_monotone(steps))
    triggered_rules.extend(_check_causal_incoherence(steps))

    verdict = "YES" if triggered_rules else "NO"
    return {"verdict": verdict, "triggered_rules": triggered_rules}
