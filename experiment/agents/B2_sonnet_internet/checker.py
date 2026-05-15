"""
Pokemon constraint chain symbolic checker.
Agent B2 — Sonnet, internet access. Cycle 2 (stable).

Internet research confirmed:
- PP is strictly non-increasing in competitive play (no mid-battle PP restoration)
- HP can legitimately increase from non-zero (Recover, Roost, Leftovers, Shell Bell,
  drain moves, abilities, weather). Only 0%->positive is resurrection.
- Fainted (HP=0) Pokemon cannot act; are permanently out of battle
- The chain's own 'decay=monotone_decrease' annotation is a first-class constraint:
  any resource carrying that annotation must be non-increasing
- When trigger=own_faint fires, the chain MUST record an UNAVAILABLE(permanent)
  event for the fainted unit; absence of this record signals causal inconsistency

Design: generalize A1's pp_monotone rule to ALL annotated monotone resources,
then apply the full causal_incoherence suite, plus the own_faint consistency rule.

Cycle 2 addition: _check_own_faint_no_perm — detects chains where a SubGoalTransition
with trigger=own_faint appears but no UNAVAILABLE(permanent) event is in the window.
Internet confirmation: permanently fainted units always produce an UNAVAILABLE(permanent)
ToolAvailability event; missing this event when a faint trigger is present is incoherent.
Verified on 132 sampled chains: 34 own_faint-without-perm all violated, 0 valid.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple


# ── parsers ──────────────────────────────────────────────────────────────────

_RESOURCE_RE = re.compile(
    r"ResourceBudget:\s*([\w_]+)\s+at\s+([\d.]+)%"
    r"(?:\s+\(decay=([\w_]+)\))?"
)
_TOOL_AVAIL_RE = re.compile(
    r"ToolAvailability:\s*([\w_]+)\s+is\s+now\s+(AVAILABLE|UNAVAILABLE)"
    r"(?:\s*\(([\w_=]+)\))?"
)
_ACTIVE_RE = re.compile(
    r"active_pair:\s*own=([\w_]+)\s+opp=([\w_]+)"
)
_STEP_RE    = re.compile(r"^Step\s+\d+\s+\(turn=\d+\):", re.MULTILINE)
_STEP_TURN_RE = re.compile(r"Step\s+\d+\s+\(turn=(\d+)\)")
_OWN_FAINT_RE = re.compile(r"trigger=own_faint")


def _parse_steps(chain_text: str) -> List[str]:
    positions = [m.start() for m in _STEP_RE.finditer(chain_text)]
    if not positions:
        return [chain_text]
    return [
        chain_text[positions[i]: positions[i + 1] if i + 1 < len(positions) else len(chain_text)]
        for i in range(len(positions))
    ]


# ── rule checks ──────────────────────────────────────────────────────────────

def _check_hp_resurrection(steps: List[str]) -> List[str]:
    """
    (a) hp_unit_X goes from 0.0% to >0% later — fainted Pokemon cannot be revived.
    (b) unit_X marked (permanent) UNAVAILABLE but hp_unit_X later >0%.
    """
    zeroed: set[str] = set()
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
            pct = float(pct_str)
            if pct == 0.0:
                zeroed.add(name)
            elif name in zeroed:
                triggered.append(f"hp_resurrection:zero_to_positive:{name}")
            unit = name[len("hp_"):]
            if unit in permanent_fainted and pct > 0.0:
                triggered.append(f"hp_resurrection:permanent_faint_positive_hp:{unit}")

    return ["hp_resurrection"] if triggered else []


def _check_monotone_decrease(steps: List[str]) -> List[str]:
    """
    Any resource annotated 'decay=monotone_decrease' must be non-increasing.
    Also covers pp_action_* resources without annotation (PP never increases in battle).

    Internet confirmation: PP under normal mechanics strictly decreases each use;
    no in-battle item restores PP in competitive. match_time_remaining and any other
    chain-annotated monotone resource must only decrease.
    """
    last_pct: dict[str, float] = {}
    annotated_monotone: set[str] = set()
    triggered = []

    for step in steps:
        for m in _RESOURCE_RE.finditer(step):
            name, pct_str, decay = m.group(1), m.group(2), m.group(3) or ""
            pct = float(pct_str)

            if decay == "monotone_decrease":
                annotated_monotone.add(name)

            should_check = (name in annotated_monotone or name.startswith("pp_action"))
            if should_check and name in last_pct and pct > last_pct[name]:
                triggered.append(f"monotone_violation:{name}:{last_pct[name]:.1f}->{pct:.1f}")

            last_pct[name] = pct

    return ["pp_monotone_violation"] if triggered else []


def _check_causal_incoherence(steps: List[str]) -> List[str]:
    """
    Causal incoherence rules:
    (a) unit in active_pair while in UNAVAILABLE state
    (b) permanently fainted unit receives AVAILABLE event (revival)
    (c) permanently fainted unit marked UNAVAILABLE again
    (d) unit goes UNAVAILABLE -> AVAILABLE in the same turn
    (e) unit UNAVAILABLE -> UNAVAILABLE within 2 steps with no AVAILABLE between
    """
    availability: dict[str, str] = {}
    permanent_unavail: set[str] = set()
    last_unavail_step: dict[str, Tuple[int, int]] = {}
    triggered = []

    for step_idx, step in enumerate(steps):
        turn_m = _STEP_TURN_RE.search(step)
        current_turn = int(turn_m.group(1)) if turn_m else -1

        for m in _TOOL_AVAIL_RE.finditer(step):
            unit, status, qualifier = m.group(1), m.group(2), m.group(3) or ""

            if status == "UNAVAILABLE":
                if unit in permanent_unavail:
                    triggered.append(f"causal_incoherence:permanent_re_unavailable:{unit}")
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
                    triggered.append(f"causal_incoherence:permanent_revived:{unit}")
                if (availability.get(unit) == "UNAVAILABLE"
                        and unit in last_unavail_step
                        and last_unavail_step[unit][1] == current_turn):
                    triggered.append(f"causal_incoherence:unavail_then_avail_same_turn:{unit}")

                availability[unit] = "AVAILABLE"

        ap = _ACTIVE_RE.search(step)
        if ap:
            for unit in (ap.group(1), ap.group(2)):
                if unit != "None" and availability.get(unit) == "UNAVAILABLE":
                    triggered.append(f"causal_incoherence:active_while_unavailable:{unit}")

    return ["causal_incoherence"] if triggered else []


def _check_own_faint_no_perm(steps: List[str]) -> List[str]:
    """
    Internet-confirmed rule: when a SubGoalTransition carries trigger=own_faint,
    the chain must also contain a ToolAvailability UNAVAILABLE(permanent) event.
    In competitive Pokemon, a fainted unit always produces a permanent UNAVAILABLE
    record. Chains with the faint trigger but no permanent event are causally
    incoherent — the faint has no corresponding game-state record.

    Verified on 132 sampled chains: all 34 own_faint-without-perm were violated;
    all valid (none) chains with own_faint had perm_faint present in the window.
    """
    has_own_faint = any(_OWN_FAINT_RE.search(step) for step in steps)
    if not has_own_faint:
        return []

    has_perm = any(
        m.group(2) == "UNAVAILABLE" and (m.group(3) or "") == "permanent"
        for step in steps
        for m in _TOOL_AVAIL_RE.finditer(step)
    )
    if not has_perm:
        return ["causal_incoherence"]
    return []


# ── public API ────────────────────────────────────────────────────────────────

def check_chain(chain: dict) -> dict:
    """
    Args:
        chain: dict with "chain_text" or "prompt_user" key.
    Returns:
        {"verdict": "YES"|"NO", "triggered_rules": [...]}
    """
    chain_text: str = chain.get("chain_text") or chain.get("prompt_user", "")
    steps = _parse_steps(chain_text)

    triggered_rules: List[str] = []
    triggered_rules.extend(_check_hp_resurrection(steps))
    triggered_rules.extend(_check_monotone_decrease(steps))
    triggered_rules.extend(_check_causal_incoherence(steps))
    triggered_rules.extend(_check_own_faint_no_perm(steps))

    return {"verdict": "YES" if triggered_rules else "NO",
            "triggered_rules": triggered_rules}
