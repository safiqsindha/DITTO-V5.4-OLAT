#!/usr/bin/env python3
"""
Day 0 Task 4 — Chain Variant Generator
SPEC hash: dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8
Amendment #6 (2026-05-13): 64 conditions × 50 chains = 3,200 variants.

Produces: pre-registration/chain_variants/<model>/<condition_id>/<chain_id>.json
"""

import json, csv, os, re, sys
from pathlib import Path

SPEC_HASH = "dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8"
GENERATED_DATE = "2026-05-13"

BASE = Path("/Users/safiqsindha/Desktop/Project Ditto")
OLAT_BASE = BASE / "Ditto-5.4-OLAT/pre-registration"
ASSIGNMENTS = OLAT_BASE / "chain_condition_assignments.ndjson"
VIOLATIONS_CSV = BASE / "Ditto-5.3- Pokemon Diag/pokemon-v1-symbolic/outputs/phase3_results_v4.csv"
OUT_DIR = OLAT_BASE / "chain_variants"

CHAIN_DIRS = [
    BASE / "Ditto V1/chains/real_v2",
    BASE / "Ditto V1/chains/shuffled_v2",
    BASE / "Ditto V4/data/v1_chains_mirror",
    BASE / "Ditto V1/chains/shuffled",
]

# ── Lever text constants ─────────────────────────────────────────────────────

LEVER16_L2 = (
    "Pokemon battles follow specific rules that govern what each Pokemon can and cannot do. "
    "Each move has a limited number of uses (PP); once a move's PP reaches zero, that move "
    "cannot be used again. A Pokemon that has fainted cannot take any action for the remainder "
    "of the battle. Each Pokemon can only use moves that belong to its specific moveset — "
    "moves from other Pokemon's movesets are not available. Certain status conditions also "
    "restrict what a Pokemon can do: a sleeping or frozen Pokemon cannot use moves, and a "
    "fully paralyzed Pokemon may be prevented from acting entirely."
)

LEVER16_L3 = (
    "RULE_PP: A move requires PP > 0 to be used. Using a move with PP = 0 is a violation.\n"
    "RULE_FAINT: A Pokemon with status = fainted cannot take any action. "
    "Any action by a fainted Pokemon is a violation.\n"
    "RULE_MOVESET: A Pokemon can only use moves in its moveset. "
    "Using a move not in the Pokemon's moveset is a violation.\n"
    "RULE_SLEEP: A Pokemon with status = sleep cannot use moves (except Sleep Talk or Snore). "
    "Using other moves while asleep is a violation.\n"
    "RULE_FREEZE: A Pokemon with status = freeze cannot use moves (except moves that thaw). "
    "Using other moves while frozen is a violation."
)

LEVER19_L2 = "Base your answer on the events shown in the chain."
LEVER19_L3 = (
    "You are reviewing a log that may contain injected errors or hallucinations from a "
    "secondary system. Verify the integrity of the sequence and determine whether any "
    "violations are present."
)

# Lever 15 question texts
Q_BASELINE = "Does this battle chain contain any rule violations? The answer is YES or NO."
Q_L15_L1 = "Rate how consistent this chain is on a scale of 1–10."
Q_L15_L3 = "What is the probability this chain contains a rule violation? Answer 0–100."

# Lever 18 full question+anchor texts (question already embedded in anchor text per artifacts)
Q_L18_L1 = "Does this battle chain contain any rule violations? The answer is YES or NO."
Q_L18_L2 = "Does this battle chain contain any rule violations? Think step by step before answering. Therefore, the answer is YES or NO."
Q_L18_L3 = (
    "Does this battle chain contain any rule violations? Review the chain event by event. "
    "For each event, check whether it conforms to the rules of Pokemon battles. "
    "Identify any event that violates a rule. Therefore, the answer is YES or NO."
)
Q_L18_L4 = "Does this battle chain contain any rule violations? The answer is YES or NO."

# Lever 17 output format additions
L17_L2_INSTRUCTION = " Respond in the format: Answer: YES or NO, Rule: <rule violated or none>."
L17_L3_INSTRUCTION = ' Respond in JSON: {"detected": true or false, "rule_violated": "<rule or null>"}.'

# Lever 2 field rename mapping (cryptic → descriptive)
LEVER2_RENAME = {
    "type": "event_type",
    "timestamp": "turn_number",
    "resource": "resource_name",
    "amount": "resource_fraction",
    "decay": "depletion_pattern",
    "tool": "unit_label",
    "state": "unit_status",
    "recover_in": "recovery_turns_remaining",
    "from_phase": "battle_phase_from",
    "to_phase": "battle_phase_to",
    "trigger": "transition_trigger",
    "observable_added": "revealed_units",
    "observable_removed": "concealed_units",
    "uncertainty": "observation_confidence",
    "role": "field_role",
    "dependency": "prerequisite_action",
    "expected_action": "required_response",
    "objective": "tactical_objective",
    "weight_shift": "priority_shift",
}

# Lever 1 field sets
L1_FIELDS = frozenset({"type", "timestamp", "resource", "amount", "decay",
                        "tool", "state", "recover_in", "from_phase", "to_phase"})
L3_EXTRA_FIELDS = frozenset({"role", "dependency", "expected_action", "objective",
                               "weight_shift", "observable_removed"})
# L3 also adds active_pair_own / active_pair_opp from active_pair_by_step

# Lever 13 abstraction sets
ALL_8_ABSTRACTIONS = [
    "ResourceBudget_HP", "ResourceBudget_PP", "ResourceBudget_time",
    "ResourceBudget_status", "ResourceBudget_boost",
    "ToolAvailability", "SubGoalTransition", "InformationState",
]
TOP_3_ABSTRACTIONS = ["ResourceBudget_HP", "SubGoalTransition", "ToolAvailability"]


# ── Chain loading ────────────────────────────────────────────────────────────

def load_chain(chain_id: str) -> dict:
    for d in CHAIN_DIRS:
        p = d / f"{chain_id}.jsonl"
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError(f"Chain not found: {chain_id}")


# ── cutoff_rendered (from Ditto V1/src/prompt_builder.py) ───────────────────

def cutoff_rendered(rendered: str, k: int) -> str:
    if k <= 0:
        return ""
    parts = re.split(r"(Step \d+)", rendered)
    steps = []
    i = 0
    while i < len(parts) and not re.fullmatch(r"Step \d+", parts[i]):
        i += 1
    while i + 1 < len(parts):
        header = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""
        if re.fullmatch(r"Step \d+", header):
            steps.append((header, body))
            i += 2
        else:
            i += 1
    selected = steps[:k]
    return "".join(h + b for h, b in selected)


# ── Lever 1: field schema filtering ─────────────────────────────────────────

def filter_constraint_fields(c: dict, level: str, step_idx: int,
                              active_pairs: list) -> dict:
    if level == "L2":
        return dict(c)
    if level == "L1":
        return {k: v for k, v in c.items() if k in L1_FIELDS}
    if level == "L3":
        filtered = dict(c)
        if step_idx < len(active_pairs):
            own, opp = active_pairs[step_idx]
            filtered["active_pair_own"] = own
            filtered["active_pair_opp"] = opp
        return filtered
    return dict(c)


# ── Lever 2: field renaming ──────────────────────────────────────────────────

def rename_fields(c: dict) -> dict:
    return {LEVER2_RENAME.get(k, k): v for k, v in c.items()}


# ── Lever 3: numerical encoding (semantic buckets) ───────────────────────────

def bucket_hp(v: float) -> str:
    if v == 0.0:
        return "Fainted"
    if v <= 0.25:
        return "Critical"
    if v <= 0.75:
        return "Hurt"
    return "Healthy"

def bucket_pp(v: float) -> str:
    if v == 0.0:
        return "Empty"
    if v <= 0.5:
        return "Low"
    return "Full"

def apply_lever3_to_constraint(c: dict) -> dict:
    c = dict(c)
    if c.get("type") == "ResourceBudget" and "amount" in c and "resource" in c:
        res = c["resource"]
        amt = c["amount"]
        if res.startswith("hp_unit_"):
            c["amount"] = bucket_hp(amt)
        elif res.startswith("pp_action_"):
            c["amount"] = bucket_pp(amt)
    return c


# ── Lever 9 L2: single-line rendering ────────────────────────────────────────

def _fmt_val(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, list):
        return "[" + ",".join(str(x) for x in v) + "]"
    return str(v)

def render_L9_L2(constraints: list, active_pairs: list, k: int) -> str:
    lines = []
    for i, c in enumerate(constraints[:k]):
        parts = [f"step={i+1}", f"turn={c.get('timestamp',i)}"]
        for key, val in c.items():
            if key == "timestamp":
                continue
            parts.append(f"{key}:{_fmt_val(val)}")
        if i < len(active_pairs):
            own, opp = active_pairs[i]
            if own:
                parts.append(f"active_own:{own}")
        lines.append(" | ".join(parts))
    return "\n".join(lines)


# ── Lever 9 L3: entity-centric rendering ─────────────────────────────────────

def _entity_for_step(c: dict, step_idx: int, active_pairs: list) -> str:
    ctype = c.get("type", "")
    if ctype == "ToolAvailability":
        return c.get("tool", "own")
    if ctype == "ResourceBudget":
        res = c.get("resource", "")
        if res.startswith("hp_unit_") or res.startswith("status_unit_") or \
           res.startswith("boost_"):
            unit = res.split("_")[-1]
            return f"unit_{unit}" if not unit.startswith("unit_") else unit
        return "own"
    if ctype == "SubGoalTransition":
        return "own"
    if ctype == "InformationState":
        return "info"
    if ctype == "CoordinationDependency":
        return "own"
    if ctype == "OptimizationCriterion":
        return "own"
    return "own"

def render_L9_L3(constraints: list, active_pairs: list, k: int) -> str:
    groups: dict[str, list] = {}
    order: list[str] = []
    for i, c in enumerate(constraints[:k]):
        entity = _entity_for_step(c, i, active_pairs)
        if entity not in groups:
            groups[entity] = []
            order.append(entity)
        parts = [f"step={i+1}", f"turn={c.get('timestamp',i)}"]
        for key, val in c.items():
            if key == "timestamp":
                continue
            parts.append(f"{key}:{_fmt_val(val)}")
        groups[entity].append(" | ".join(parts))
    blocks = []
    for entity in order:
        header = f"=== {entity} ==="
        blocks.append(header + "\n" + "\n".join(groups[entity]))
    return "\n\n".join(blocks)


# ── Lever 4: derived state markers ───────────────────────────────────────────

def _compute_derived_state(constraints: list) -> list:
    """Compute cumulative derived state at each step."""
    hp_state = {}      # unit → current hp fraction
    pp_state = {}      # action → current pp fraction
    faint_set = set()  # permanently fainted units
    available = {}     # unit → bool
    use_counts = {}    # action → count of appearances
    last_used = {}     # action → step index

    states = []
    for i, c in enumerate(constraints):
        ctype = c.get("type", "")
        if ctype == "ResourceBudget":
            res = c.get("resource", "")
            amt = c.get("amount")
            if res.startswith("hp_unit_"):
                unit = res[len("hp_unit_"):]
                hp_state[unit] = amt
            elif res.startswith("pp_action_"):
                action = res
                if action not in use_counts:
                    use_counts[action] = 0
                use_counts[action] += 1
                last_used[action] = i + 1
                pp_state[action] = amt
        elif ctype == "ToolAvailability":
            unit = c.get("tool", "")
            st = c.get("state", "")
            recover_in = c.get("recover_in")
            if st == "unavailable" and recover_in is None:
                faint_set.add(unit)
            available[unit] = (st == "available")

        state_snap = {
            "hp_state": dict(hp_state),
            "pp_state": dict(pp_state),
            "faint_set": list(faint_set),
            "available": dict(available),
            "use_counts": dict(use_counts),
            "last_used": dict(last_used),
        }
        states.append(state_snap)
    return states

def apply_lever4_L2_annotation(c: dict, step_idx: int, derived_states: list) -> str:
    """Sparse natural-language inline annotation appended to step text."""
    notes = []
    ctype = c.get("type", "")
    if step_idx == 0 or step_idx >= len(derived_states):
        return ""
    prev = derived_states[step_idx - 1]

    if ctype == "ResourceBudget":
        res = c.get("resource", "")
        amt = c.get("amount")
        if res.startswith("pp_action_"):
            count = prev["use_counts"].get(res, 0)
            if count > 0:
                notes.append(f"this is use #{count + 1} of {res}")
            if amt is not None and amt <= 0.0:
                notes.append(f"{res} has reached zero PP")
        if res.startswith("hp_unit_"):
            unit = res[len("hp_unit_"):]
            if amt is not None and amt <= 0.0:
                notes.append(f"{unit} has fainted")
    elif ctype == "ToolAvailability":
        unit = c.get("tool", "")
        st = c.get("state", "")
        recover_in = c.get("recover_in")
        if st == "unavailable" and recover_in is None:
            notes.append(f"{unit} has permanently fainted")
        elif st == "available" and unit in prev["faint_set"]:
            notes.append(f"WARNING: {unit} was previously fainted but is now available")

    if notes:
        return " (" + "; ".join(notes) + ")"
    return ""

def apply_lever4_L3_annotation(c: dict, step_idx: int, derived_states: list) -> str:
    """Dense prescriptive structured annotation."""
    if step_idx >= len(derived_states):
        return ""
    snap = derived_states[step_idx]
    ctype = c.get("type", "")

    parts = []
    if ctype == "ResourceBudget":
        res = c.get("resource", "")
        if res.startswith("pp_action_"):
            count = snap["use_counts"].get(res, 0)
            last = snap["last_used"].get(res, step_idx + 1)
            amt = snap["pp_state"].get(res, 1.0)
            parts.append(f"pp_remaining={amt:.1%}")
            parts.append(f"total_uses={count}")
            parts.append(f"last_seen_step={last}")
        if res.startswith("hp_unit_"):
            unit = res[len("hp_unit_"):]
            fainted = unit in snap["faint_set"]
            parts.append(f"hp_fraction={c.get('amount',0):.3f}")
            parts.append(f"fainted={fainted}")
    elif ctype == "ToolAvailability":
        unit = c.get("tool", "")
        avail = snap["available"].get(unit, False)
        perm_faint = unit in snap["faint_set"]
        parts.append(f"available={avail}")
        parts.append(f"permanently_fainted={perm_faint}")

    if parts:
        return " [" + ", ".join(parts) + "]"
    return ""


# ── Render constraint to text line (for Lever 9 L1 custom field filtering) ──

def render_constraint_L1_format(c: dict, step_num: int) -> str:
    """Render a single constraint event in L1 (multi-line per step) format."""
    ctype = c.get("type", "unknown")
    ts = c.get("timestamp", "?")
    header = f"Step {step_num} (turn={ts}):\n"
    fields = {k: v for k, v in c.items() if k not in ("type", "timestamp")}

    if ctype == "SubGoalTransition":
        from_p = fields.get("from_phase", "?")
        to_p = fields.get("to_phase", "?")
        trig = fields.get("trigger", "")
        body = f"  SubGoalTransition: phase shifted from '{from_p}' to '{to_p}'"
        if trig:
            body += f" (trigger={trig})"
    elif ctype == "InformationState":
        added = fields.get("observable_added", [])
        removed = fields.get("observable_removed", [])
        unc = fields.get("uncertainty", 0.5)
        added_str = "[" + ",".join(added) + "]" if added else "[none]"
        removed_str = "[" + ",".join(removed) + "]" if removed else "[none]"
        body = f"  InformationState: added={added_str} removed={removed_str} uncertainty={unc:.2f}"
    elif ctype == "ToolAvailability":
        tool = fields.get("tool", "?")
        state = fields.get("state", "?")
        recover_in = fields.get("recover_in")
        if state == "unavailable":
            ri_str = "(permanent)" if recover_in is None else f"(recover_in={recover_in})"
        else:
            ri_str = ""
        body = f"  ToolAvailability: {tool} is now {state.upper()}"
        if ri_str:
            body += f" {ri_str}"
    elif ctype == "ResourceBudget":
        resource = fields.get("resource", "?")
        amount = fields.get("amount", 0)
        decay = fields.get("decay", "")
        amt_str = f"{amount * 100:.1f}%" if isinstance(amount, float) else str(amount)
        body = f"  ResourceBudget: {resource} at {amt_str} (decay={decay})"
    elif ctype == "CoordinationDependency":
        role = fields.get("role", "?")
        dep = fields.get("dependency", "?")
        exp = fields.get("expected_action", "?")
        body = f"  CoordinationDependency: {role} depends on {dep} -> expected_action={exp}"
    elif ctype == "OptimizationCriterion":
        obj = fields.get("objective", "?")
        ws = fields.get("weight_shift", "?")
        body = f"  OptimizationCriterion: objective={obj} weight_shift={ws}"
    else:
        body = f"  {ctype}: " + " ".join(f"{k}={v}" for k, v in fields.items())

    # Extra L3 fields
    if "active_pair_own" in c:
        body += f"\n  active_pair: own={c['active_pair_own']} opp={c.get('active_pair_opp','?')}"

    return header + body + "\n"


# ── Main rendering pipeline ──────────────────────────────────────────────────

def render_chain_for_condition(chain: dict, cond: dict) -> str:
    """Return the rendered chain text for a given condition."""
    lever = cond["lever_varied"]
    level = cond["level_varied"]
    k = cond["k"]
    constraints_raw = chain["constraints"]
    active_pairs = chain.get("active_pair_by_step", [])

    # Determine Lever 1 level (field schema)
    l1_level = "L2"  # baseline
    if lever == 1:
        l1_level = level

    # Determine Lever 9 level (rendering format)
    l9_level = "L1"  # baseline
    if lever == 9:
        l9_level = level

    # Determine Lever 2 active (field renaming)
    do_lever2 = (lever == 2 and level == "L2")

    # Determine Lever 3 active (numerical encoding)
    do_lever3 = (lever == 3 and level == "L2")

    # Determine Lever 4 active (state markers)
    l4_level = "L1"  # baseline
    if lever == 4:
        l4_level = level

    # For baseline Lever 9 L1 with baseline Lever 1 L2: use pre-computed rendered
    if l9_level == "L1" and l1_level == "L2" and not do_lever2 and not do_lever3 and l4_level == "L1":
        rendered = chain.get("rendered", "")
        return cutoff_rendered(rendered, k)

    # Custom rendering path
    # Step 1: compute derived state if Lever 4 needed
    derived_states = None
    if l4_level in ("L2", "L3"):
        derived_states = _compute_derived_state(constraints_raw)

    # Step 2: apply Lever 1 field filtering and Lever 3 bucketing
    constraints = []
    for i, c_raw in enumerate(constraints_raw[:k]):
        c = filter_constraint_fields(c_raw, l1_level, i, active_pairs)
        if do_lever3:
            c = apply_lever3_to_constraint(c)
        constraints.append(c)

    # Step 3: render per Lever 9 format
    if l9_level == "L1":
        # Re-render in L1 multi-line format
        preamble = f"# Constraint chain (perspective={chain.get('perspective','?')})\n"
        step_texts = []
        for i, c in enumerate(constraints):
            step_text = render_constraint_L1_format(c, i + 1)
            if l4_level == "L2" and derived_states:
                ann = apply_lever4_L2_annotation(c, i, derived_states)
                if ann:
                    step_text = step_text.rstrip("\n") + ann + "\n"
            elif l4_level == "L3" and derived_states:
                ann = apply_lever4_L3_annotation(c, i, derived_states)
                if ann:
                    step_text = step_text.rstrip("\n") + ann + "\n"
            step_texts.append(step_text)
        chain_text = preamble + "".join(step_texts)
    elif l9_level == "L2":
        lines = []
        for i, c in enumerate(constraints):
            if do_lever2:
                c = rename_fields(c)
            parts = [f"step={i+1}", f"turn={c.pop('timestamp', c.pop('turn_number', i))}"]
            for key, val in c.items():
                parts.append(f"{key}:{_fmt_val(val)}")
            if i < len(active_pairs):
                own, _ = active_pairs[i]
                if own:
                    parts.append(f"active_own:{own}")
            line = " | ".join(parts)
            if l4_level == "L2" and derived_states:
                ann = apply_lever4_L2_annotation(constraints_raw[i] if i < len(constraints_raw) else c,
                                                  i, derived_states)
                line += ann
            elif l4_level == "L3" and derived_states:
                ann = apply_lever4_L3_annotation(constraints_raw[i] if i < len(constraints_raw) else c,
                                                  i, derived_states)
                line += ann
            lines.append(line)
        chain_text = "\n".join(lines)
    elif l9_level == "L3":
        groups: dict[str, list] = {}
        order: list[str] = []
        for i, c in enumerate(constraints):
            if do_lever2:
                c_disp = rename_fields(dict(c))
            else:
                c_disp = dict(c)
            entity = _entity_for_step(constraints_raw[i] if i < len(constraints_raw) else c,
                                      i, active_pairs)
            if entity not in groups:
                groups[entity] = []
                order.append(entity)
            parts = [f"step={i+1}", f"turn={c_disp.pop('timestamp', c_disp.pop('turn_number', i))}"]
            for key, val in c_disp.items():
                parts.append(f"{key}:{_fmt_val(val)}")
            line = " | ".join(parts)
            if l4_level == "L2" and derived_states:
                ann = apply_lever4_L2_annotation(constraints_raw[i] if i < len(constraints_raw) else c,
                                                  i, derived_states)
                line += ann
            elif l4_level == "L3" and derived_states:
                ann = apply_lever4_L3_annotation(constraints_raw[i] if i < len(constraints_raw) else c,
                                                  i, derived_states)
                line += ann
            groups[entity].append(line)
        blocks = []
        for entity in order:
            header = f"=== {entity} ==="
            blocks.append(header + "\n" + "\n".join(groups[entity]))
        chain_text = "\n\n".join(blocks)
    else:
        chain_text = ""

    return chain_text


# ── Prompt composition ───────────────────────────────────────────────────────

def compose_prompt(chain_text: str, cond: dict) -> str:
    """Compose full user-turn prompt per SPEC §17 step 8 ordering:
    Lever 19 → Lever 16 → chain → Lever 15 question → Lever 18 CoT → anchor.
    """
    lever = cond["lever_varied"]
    level = cond["level_varied"]

    # Lever 19 grounding (user-turn opening)
    l19_text = ""
    if lever == 19:
        if level == "L2":
            l19_text = LEVER19_L2
        elif level == "L3":
            l19_text = LEVER19_L3

    # Lever 16 constraint context (co-located before chain)
    l16_text = ""
    if lever == 16:
        if level == "L2":
            l16_text = LEVER16_L2
        elif level == "L3":
            l16_text = LEVER16_L3

    # Lever 15 question phrasing
    l15_text = Q_BASELINE  # default = L2 (violation detection YES/NO)
    if lever == 15:
        if level == "L1":
            l15_text = Q_L15_L1
        elif level == "L3":
            l15_text = Q_L15_L3

    # Lever 18 CoT — overrides the question+anchor text
    if lever == 18:
        if level == "L1":
            l15_text = Q_L18_L1
        elif level == "L2":
            l15_text = Q_L18_L2
        elif level == "L3":
            l15_text = Q_L18_L3
        elif level == "L4":
            l15_text = Q_L18_L4

    # Lever 17 output format — appends to question
    if lever == 17:
        if level == "L2":
            l15_text = Q_BASELINE + L17_L2_INSTRUCTION
        elif level == "L3":
            l15_text = Q_BASELINE + L17_L3_INSTRUCTION

    # Assemble
    parts = []
    if l19_text:
        parts.append(l19_text)
    if l16_text:
        parts.append(l16_text)
    parts.append(chain_text.strip())
    parts.append(l15_text)

    return "\n\n".join(parts)


# ── API params ───────────────────────────────────────────────────────────────

def build_api_params(cond: dict) -> dict:
    lever = cond["lever_varied"]
    level = cond["level_varied"]
    model = cond["model"]
    max_tokens = cond["max_tokens"]
    temperature = cond["temperature"]
    thinking_enabled = cond["thinking_enabled"]
    function_calling = cond["function_calling"]

    # Lever 17 max_tokens override
    if lever == 17:
        if level == "L2":
            max_tokens = 64
        elif level == "L3":
            max_tokens = 128

    # Lever 12 L2 max_tokens
    if lever == 12 and level == "L2":
        max_tokens = 128

    params = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "thinking": {"type": "enabled" if thinking_enabled else "disabled"},
    }

    if function_calling:
        params["function_calling"] = True
        params["endpoint_suffix"] = "/beta"
        params["tool_choice"] = "required"

    if lever == 12 and level == "L2":
        params["response_format"] = {"type": "json_object"}

    if lever == 17 and level == "L3":
        params["response_format"] = {"type": "json_object"}

    return params


# ── Ground truth ─────────────────────────────────────────────────────────────

def ground_truth_L1(chain_id: str) -> bool:
    """L1: shuffled-vs-real. Violated = shuffled chain (has _shuffled_ in ID)."""
    return "_shuffled_" in chain_id

def ground_truth_L3(chain_id: str, violations_map: dict) -> bool:
    """L3: symbolic-checker-as-truth. Violated = violation_present in phase3_results_v4.csv."""
    return violations_map.get(chain_id, False)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    # Load violations map
    violations_map = {}
    with open(VIOLATIONS_CSV) as f:
        for row in csv.DictReader(f):
            violations_map[row["chain_id"]] = row["violation_present"].strip().lower() == "true"
    print(f"Loaded {len(violations_map)} violation records.")

    # Load assignments (unique condition × chain pairs)
    assignments = []
    seen = set()
    with open(ASSIGNMENTS) as f:
        for line in f:
            r = json.loads(line)
            key = (r["condition_id"], r["chain_id"])
            if key not in seen:
                assignments.append(r)
                seen.add(key)
    print(f"Loaded {len(assignments)} unique condition-chain assignments.")

    # Generate variants
    n_written = 0
    n_errors = 0
    for rec in assignments:
        cid = rec["condition_id"]
        chain_id = rec["chain_id"]
        model = rec["model"]

        out_path = OUT_DIR / model / cid / f"{chain_id}.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            chain = load_chain(chain_id)
        except FileNotFoundError as e:
            print(f"ERROR: {e}")
            n_errors += 1
            continue

        chain_text = render_chain_for_condition(chain, rec)
        prompt_user = compose_prompt(chain_text, rec)
        api_params = build_api_params(rec)

        # Ground truths
        gt_L1 = ground_truth_L1(chain_id)
        gt_L3 = ground_truth_L3(chain_id, violations_map)
        # L2 (planted-violations): same as L1 for this corpus
        # (shuffled chains = planted violations; real chains = no planted violation)
        gt_L2 = gt_L1

        variant = {
            "condition_id": cid,
            "model": model,
            "chain_id": chain_id,
            "lever_varied": rec["lever_varied"],
            "level_varied": rec["level_varied"],
            "lever": rec["lever"],
            "level": rec["level"],
            "k": rec["k"],
            "prompt_user": prompt_user,
            "api_params": api_params,
            "ground_truth": {
                "L1_shuffled_vs_real": gt_L1,
                "L2_planted_violations": gt_L2,
                "L3_symbolic_checker": gt_L3,
            },
            "violation_type": rec.get("violation_type", ""),
            "assignment_index": rec.get("assignment_index", -1),
            "spec_hash": SPEC_HASH,
            "generated_date": GENERATED_DATE,
        }

        # Lever 11: distractor padding not pre-computed (requires tokenizer);
        # flag for Lever 11 preprocessing script.
        if rec["lever_varied"] == 11:
            variant["distractor_padding_required"] = True
            variant["distractor_target_tokens"] = "200000-250000"
            variant["distractor_position"] = "L2_midpoint" if rec["level_varied"] == "L2" else "L3_end"

        out_path.write_text(json.dumps(variant, indent=2))
        n_written += 1

        if n_written % 200 == 0:
            print(f"  {n_written} / {len(assignments)} written...")

    print(f"\nDone. Written: {n_written}. Errors: {n_errors}.")
    return n_errors


if __name__ == "__main__":
    sys.exit(main())
