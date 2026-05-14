# Blocker #1 — Lever 1 Exact Field Lists

**Status:** RESOLVED — field schema derived from actual v1 pipeline code (translation.py, renderer.py, v4_runner.py, sample chain JSONL). O-A resolved: CoordinationDependency and OptimizationCriterion events ARE included in the v5.1 baseline LLM prompt (see O-A resolution below). L2 effective field count is ~18, not 12.

**Source files inspected:**
- `Ditto V1/src/translation.py` — defines the 6 abstract constraint event types and their fields
- `Ditto V1/src/renderer.py` — defines how each event type is rendered to the LLM; ALL 6 types in `_RENDERERS` dispatch table
- `Ditto V4/src/v4_runner.py` — reads `chain["rendered"]` directly; no event-type filtering
- `Ditto V4/data/v4_pokemon_chains/real/pokemon/gen9ou-2297404400_p2.jsonl` — sample chain confirming actual field values

---

## Chain Format Overview

The v1 Pokemon chain format uses an **abstract constraint language** — no Pokemon species names appear in rendered chains (domain-abstracted via translation layer). Events are typed with 6 concrete event classes. Unit labels are alphabetical (unit_A through unit_F). Move labels are positional (action_1 through action_4). PP values are normalized fractions (0.0–1.0).

**V1 validity filter (from RESULTS.md / build_chains.py):** Chains must have length 20–40 constraints, ≥ 2 SubGoalTransition, ≥ 1 ToolAvailability(unavailable), ≥ 10 ResourceBudget, non-decreasing timestamps, no consecutive duplicates.

**V1 task vs OLAT task:** V1 (Ditto V1 codebase) used a next-action prediction task. OLAT uses the V1 chain format for a violation detection (YES/NO) task introduced in the v3–v5 lineage. "V1 methodology" in OLAT means V1 chain format + V1 minimal setup, not V1's prediction task.

The chain JSONL file has this top-level structure:
```json
{
  "chain_id": "gen9ou-MATCHID_pN",
  "match_id": "gen9ou-MATCHID",
  "perspective": "p1" or "p2",
  "cutoff_k": 20,
  "constraints": [ ...event objects... ],
  "active_pair_by_step": [ [own_unit, opp_unit], ... ],
  "rendered": "..."
}
```

---

## L2 — Standard Schema (~18 fields, v5.1 baseline) — AUTHORITATIVE

**Derived from:** All 6 event types in translation.py + renderer.py rendering logic. Confirmed to match v5.1 prompt content via v4_runner.py inspection (reads `chain["rendered"]` directly — no event-type filtering).

The v5.1 baseline renders events from **all 6 constraint types**. The effective field count is ~18: 12 core fields from the 4 violation-relevant event types + 5 fields from CoordinationDependency and OptimizationCriterion + active_pair context. CoordinationDependency and OptimizationCriterion appear in every rendered chain even though EC-07 in the symbolic checker notes "No violation rules apply to them."

**The 4 core event types with their fields:**

| # | Field | Present in type(s) | Description |
|---|---|---|---|
| 1 | `type` | All | Event class name: `ResourceBudget` / `ToolAvailability` / `SubGoalTransition` / `InformationState` / `CoordinationDependency` / `OptimizationCriterion` |
| 2 | `timestamp` | All | Turn number (integer) |
| 3 | `resource` | ResourceBudget | Resource name: `hp_unit_X`, `pp_action_N_own/opp`, `match_time_remaining`, `status_unit_X`, `boost_STAT_unit_X` |
| 4 | `amount` | ResourceBudget | Normalized fraction 0.0–1.0. For boosts: magnitude/6. For status: severity (slp/frz=1.0, par/brn=0.5, psn/tox=0.3). |
| 5 | `decay` | ResourceBudget | Per-resource: HP=`"none"`, boost=`"none"`, status(most)=`"none"`, status(slp/tox)=`"monotone_decrease_if_turn_based"`, PP=`"monotone_decrease"`, time=`"monotone_decrease"` |
| 6 | `tool` | ToolAvailability | Unit label: `unit_A` through `unit_F` |
| 7 | `state` | ToolAvailability | `"available"` / `"unavailable"` |
| 8 | `recover_in` | ResourceBudget, ToolAvailability | Integer turns, `null` = permanent, `0` = benched |
| 9 | `from_phase` | SubGoalTransition | Phase string e.g. `"initial"`, `"vs_unit_B"`, `"forced_switch_required"` |
| 10 | `to_phase` | SubGoalTransition | New phase string |
| 11 | `trigger` | SubGoalTransition | `"opponent_switch"`, `"own_faint"`, etc. |
| 12 | `observable_added` | InformationState | List of newly revealed unit labels e.g. `["unit_B"]` |
| (+) | `observable_removed` | InformationState | List of removed items (usually empty) |
| (+) | `uncertainty` | InformationState | Float 0.0–1.0 (always 0.5 in practice) |

**Total core fields: 12** (excluding observable_removed and uncertainty which are near-constant). Including all InformationState fields: 14. Including CoordinationDependency and OptimizationCriterion fields (present in v5.1 baseline): **~18 effective fields**. Treat 18 as the correct count for L2 (v5.1 baseline).

**CoordinationDependency fields (informational, not violation-relevant):**
- `role`: e.g. `"field_side_p1"`
- `dependency`: e.g. `"hazard_type_A"` (Stealth Rock), `"hazard_type_B"` (Spikes)
- `expected_action`: `"hazard_response"`

**OptimizationCriterion fields (informational, not violation-relevant):**
- `objective`: e.g. `"weather_raindance"`, `"field_electricterrain"`
- `weight_shift`: e.g. `"weather_A"`, `"terrain_A"`

**[O-A — RESOLVED]:** CoordinationDependency and OptimizationCriterion events ARE included in the v5.1 baseline LLM prompt. Evidence from codebase inspection:
- `renderer.py` `_RENDERERS` dispatch table includes both types (lines 95–96)
- `render_chain()` iterates ALL constraints in the list with no type filtering
- `v4_runner.py` line 124: `rendered: str = chain["rendered"]` — reads pre-computed `rendered` field directly
- `cutoff_rendered()` truncates to k steps only — no event-type filtering
Therefore L2 effective field count is ~18 (not 12). Update references to L2 "~12 fields" to "~18 fields".

---

## L1 — Minimal Schema (10 fields) — LOCKED per O2 Option A (Amendment #1, 2026-05-12)

**Derived from:** Violation-detection requirements in `pokemon_rule_checker.py`. L1 contains every field required for any of the 9 active symbolic checker rules (R1, R2, R3, R4, R6, R8, R9, R10, R11) to fire.

**O2 Option A rationale:** Per the O2 conceptual coverage check (below), the original 7-field L1 could not detect R2, R4, R9, R10, or R11. Expanding to 10 fields by adding `recover_in`, `from_phase`, and `to_phase` closes the coverage gap so that Lever 1's effect-size measurement compares "fewer descriptive fields" (10 → 18 → 20) rather than "fewer detectable violation types" — preserving the single-variable manipulation principle.

| # | Field | Event type | Violation rule served |
|---|---|---|---|
| 1 | `type` | All | Event dispatch |
| 2 | `timestamp` | All | Temporal ordering for all rules |
| 3 | `resource` | ResourceBudget | R1 (pp/time — monotone_decrease resources only), R3/R4/R8/R9 (hp resources) |
| 4 | `amount` | ResourceBudget | R1, R3, R4, R8, R9 |
| 5 | `decay` | ResourceBudget | R1 — identifies monotone_decrease resources (PP and match_time_remaining only; HP/boost have decay="none") |
| 6 | `tool` | ToolAvailability | R2, R6, R8, R10 |
| 7 | `state` | ToolAvailability | R2, R6, R10 |
| 8 | `recover_in` | ResourceBudget, ToolAvailability | R2 (None = permanent faint), R4 (permanence marker), R9 (permanent-faint set), R10 (None vs not-None) |
| 9 | `from_phase` | SubGoalTransition | R11 — initial-phase re-entry check |
| 10 | `to_phase` | SubGoalTransition | R11 — `vs_` prefix detection |

**Fields included:** type, timestamp, resource, amount, decay, tool, state, recover_in, from_phase, to_phase = **10 fields**

**Fields excluded in L1:** trigger (informational, not violation-relevant per R11 logic at pokemon_rule_checker.py:475–481), observable_added, observable_removed, uncertainty, role, dependency, expected_action, objective, weight_shift, active_pair_own, active_pair_opp

**Violation coverage for L1 (10 fields) — all rules detectable:**

| Violation type | Detectable from L1? | Notes |
|---|---|---|
| `monotone_increase` (R1) | ✓ YES | resource, amount, decay all present |
| `dead_unit_returns` (R2) | ✓ YES | tool, state, recover_in all present |
| `hp_resurrection` (R3/R8/R9) | ✓ YES | resource, amount, recover_in (for R9 permanent-faint set) all present |
| `faint_no_permanence` (R4) | ✓ YES | resource, amount, tool, state, recover_in all present |
| `double_availability` (R6) | ✓ YES | tool, state |
| `causal_incoherence` (R10) | ✓ YES | resource, amount, tool, state, recover_in all present |
| `causal_incoherence` (R11) | ✓ YES | from_phase, to_phase present |

**Coverage summary:** L1 covers all 9 active symbolic checker rules. No violation type is structurally undetectable under L1.

---

## Symbolic Checker Rule Coverage Analysis (O2 Conceptual Coverage Check)

**Status:** DRAFT — coverage gaps identified. Awaiting both-author decision before O2 can be closed.

Conducted 2026-05-11 per O2 conceptual coverage check protocol. Mapped each of the 9 active symbolic checker rules (R1, R2, R3, R4, R6, R8, R9, R10, R11) against the current L1 field set (type, timestamp, resource, amount, decay, tool, state).

**Per-rule field requirements (from pokemon_rule_checker.py source):**

| Rule | Required fields | Present in L1 (7 fields)? | Gap |
|---|---|---|---|
| R1 — monotone_increase | type, timestamp, resource, amount, decay | ✅ Yes | — |
| R2 — dead_unit_returns | type, timestamp, tool, state, **recover_in** | ❌ recover_in missing | recover_in |
| R3 — hp_resurrection | type, timestamp, resource, amount | ✅ Yes | — |
| R4 — faint_no_permanence | type, timestamp, resource, amount, tool, state, **recover_in** | ❌ recover_in missing | recover_in |
| R6 — double_availability | type, timestamp, tool, state | ✅ Yes | — |
| R8 — available_while_zeroed | type, timestamp, resource, amount, tool, state | ✅ Yes | — |
| R9 — positive_hp_perm_faint | type, timestamp, resource, amount, tool, state, **recover_in** | ❌ recover_in missing | recover_in |
| R10 — hp_zero_temp_switch | type, timestamp, resource, amount, tool, state, **recover_in** | ❌ recover_in missing | recover_in |
| R11 — initial_phase_reentry | type, timestamp, **from_phase**, **to_phase**, **trigger** | ❌ All three missing | from_phase, to_phase, trigger |

**Source-line evidence (pokemon_rule_checker.py):**
- Line 145 — `_permanent_faint()`: `event.get("recover_in") is None` → R2, R4, R9 all depend on this helper
- Line 153 — `_switch_out()`: `event.get("recover_in") is not None` → R10 directly
- Line 475–477 — R11: reads `from_phase`, `to_phase`, `trigger` from SubGoalTransition events

**Coverage gaps under current 7-field L1:**

| Gap | Affects | Violation types not detectable |
|---|---|---|
| `recover_in` | R2, R4, R9, R10 | `dead_unit_returns`, `faint_no_permanence`, `hp_resurrection` (R9 variant), `causal_incoherence` (R10 variant) |
| `from_phase`, `to_phase`, `trigger` | R11 | `causal_incoherence` (R11 variant) |

Combined: under current L1, **5 of 9 rules cannot fire** (R2, R4, R9, R10, R11). The violation-type strings `dead_unit_returns`, `faint_no_permanence`, and `causal_incoherence` would never be reported under L1, even when those violations are objectively present in the chain.

**This is a real coverage gap. Surfaced as a new decision sheet item (see `decisions/decision-sheet-v1.md`, Item O2). Both authors must resolve before O2 can be closed and final signoff proceeds.**

---

## L3 — Extended Schema (15–20 fields)

**Derived from:** L2 + all fields from all 6 event types + chain-level metadata.

L3 includes everything in L2, plus:

| # | Field | Event type | Notes |
|---|---|---|---|
| 13 | `role` | CoordinationDependency | Hazard side identifier |
| 14 | `dependency` | CoordinationDependency | Hazard type (e.g. hazard_type_A = Stealth Rock) |
| 15 | `expected_action` | CoordinationDependency | Always `"hazard_response"` |
| 16 | `objective` | OptimizationCriterion | Weather/terrain label (e.g. `"weather_raindance"`) |
| 17 | `weight_shift` | OptimizationCriterion | Abstracted label (e.g. `"weather_A"`) |
| 18 | `active_pair_own` | Chain-level | Own-side active unit label at this step |
| 19 | `active_pair_opp` | Chain-level | Opp-side active unit label at this step |
| 20 | `observable_removed` | InformationState | Currently always empty |

**Total L3 fields: 20** (including the 12 L2 fields + 8 extended fields above)

---

## Violation Type Taxonomy (from pokemon_rule_checker.py)

The v5.3 symbolic checker (98% accuracy) produces these 6 distinct violation type strings:

| Violation type string | Rules | Description |
|---|---|---|
| `monotone_increase` | R1 | A `monotone_decrease` resource increased |
| `dead_unit_returns` | R2 | Permanently fainted unit becomes AVAILABLE |
| `hp_resurrection` | R3, R8, R9 | HP positive after 0; available while zeroed; permanently fainted has HP |
| `faint_no_permanence` | R4 | HP=0 but no permanent-faint marker follows |
| `double_availability` | R6 | Unit becomes AVAILABLE twice without intervening UNAVAILABLE |
| `causal_incoherence` | R10, R11 | HP=0 unit temp-switched-out; initial-phase re-entry after battle started |
| `multiple` | multiple | Multiple distinct violation types in same chain (meta-type) |

---

## Verification Checklist for Sign-Off

- [x] O-A resolved: CoordinationDependency and OptimizationCriterion ARE in v5.1 LLM prompt — confirmed from renderer.py _RENDERERS table + v4_runner.py chain["rendered"] direct read
- [ ] L2 field count (~18) confirmed by both authors at sign-off
- [ ] L1 field count confirmed: 7 fields or 8 (adding recover_in) or 10 (adding SubGoalTransition)
- [ ] Violation types in OLAT test set enumerated — confirm which of the 6 types appear and whether L1 covers them
- [ ] active_pair_by_step rendering in L3 confirmed (per-step vs chain-level)
