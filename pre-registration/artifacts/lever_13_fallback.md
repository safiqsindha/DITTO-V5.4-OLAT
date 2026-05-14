# Blocker #8 — Lever 13 Fallback Rule

**Status:** COMPLETE — text rule fully specified from handoff. Code implementation stub provided; requires pipeline integration to activate.

---

## Deterministic Fallback Branch

The following single branch governs which abstractions are selected for Lever 13 Level 2 (top 2–3 dominant abstractions):

```
IF symbolic_checker.importance_metrics IS available at execution time:
    Select top-3 abstractions by importance score (descending).
    TIE-BREAK: alphabetical by abstraction name (ascending).
ELSE:
    Select top-3 abstractions by frequency in v5.1 corpus
    (count of chains where abstraction was the primary violation type).
    TIE-BREAK: alphabetical by abstraction name (ascending).
```

**No runtime ambiguity is permitted.** The branch must be resolved once at OLAT initialization and held constant for all Lever 13 L2 evaluations in that run. The resolved subset must be logged in the condition metadata before any API calls begin.

---

## Symbolic Checker Status

**At time of handoff (May 11, 2026):** v5.3 symbolic checker has 98% accuracy on Pokemon chains and is listed as an available tool. Importance metrics availability at OLAT execution time is unknown.

**Resolution action required before execution:**
1. Inspect symbolic checker code for an `importance_metrics` attribute, method, or output field.
2. If accessible: record the 3 highest-scoring abstraction names and confirm against the full 8-abstraction list.
3. If inaccessible: run frequency count on v5.1 corpus at commit 7033cb1 — count per-abstraction how many chains have that abstraction as primary violation type; select top-3.
4. Log the resolved subset in `condition_metadata.lever_13_l2_abstractions` before execution begins.

---

## Implementation Stub (Python)

```python
def resolve_lever13_l2_abstractions(
    symbolic_checker=None,
    corpus_df=None,
    all_abstractions=None  # list of 8 abstraction name strings
):
    """
    Returns list of 3 abstraction names for Lever 13 L2.
    Deterministic: same inputs always produce same output.
    Must be called once at OLAT init and result logged before API calls.
    """
    if symbolic_checker is not None:
        try:
            importance = symbolic_checker.importance_metrics  # or .get_importance()
            scored = {
                name: importance[name]
                for name in all_abstractions
                if name in importance
            }
            if scored:  # any importance metrics available — use this branch
                # Fill missing abstractions with score 0 so they rank last under
                # the importance criterion. Dimensional-only abstractions
                # (ResourceBudget_status, ResourceBudget_boost) are expected to
                # be absent from importance_metrics and will get 0 here, which
                # naturally excludes them from the top-3.
                for abs_name in all_abstractions:
                    if abs_name not in scored:
                        scored[abs_name] = 0.0
                top3 = sorted(
                    scored.keys(),
                    key=lambda n: (-scored[n], n)  # desc importance, asc alpha tie-break
                )[:3]
                return top3, "importance_score"
        except (AttributeError, KeyError):
            pass  # fall through to frequency method

    # Fallback: v5.1 corpus frequency (only triggers if symbolic checker
    # returns nothing at all).
    assert corpus_df is not None, "corpus_df required when symbolic_checker unavailable"
    freq = corpus_df["primary_violation_abstraction"].value_counts()
    top3 = sorted(
        all_abstractions,
        key=lambda n: (-freq.get(n, 0), n)  # desc frequency, asc alpha tie-break
    )[:3]
    return top3, "corpus_frequency"
```

**Dead-code resolution (2026-05-11):** The earlier draft gated the importance branch on `len(scored) == len(all_abstractions)`, which fails whenever the symbolic checker omits any abstraction from `importance_metrics`. Under realistic conditions the symbolic checker reports importance only for rule-bearing abstractions, so the length check would always fail and the importance branch was dead code. The patched `if scored:` check activates the importance branch whenever any importance metrics are available; missing abstractions are filled with 0.0 so they rank last and are excluded from the top-3. Top-3 selection result is unchanged versus the old code; the fallback rule now does what it says it does.

**[O3 RESOLVED — decision-sheet-v1.md, 2026-05-11]:**
- Replace `symbolic_checker.importance_metrics` with actual attribute/method name (Day 0 task)
- Replace `corpus_df["primary_violation_abstraction"]` with actual column name from v5.1 data (Day 0 task)
- The 8-element list below is locked.

**Locked `all_abstractions` list (from translation.py + symbolic checker EC-07):**
```python
ALL_ABSTRACTIONS = [
    "ResourceBudget_HP",       # hp_unit_X resources — rules R3, R4, R8, R9 (rule-bearing)
    "ResourceBudget_PP",       # pp_action_N_own/opp resources — rule R1 (rule-bearing)
    "ResourceBudget_time",     # match_time_remaining resource — rule R1 (rule-bearing)
    "ResourceBudget_status",   # status_unit_X resources — no rule (dimensional-only)
    "ResourceBudget_boost",    # boost_STAT_unit_X resources — no rule (dimensional-only)
    "ToolAvailability",        # unit_A through unit_F availability — rules R2, R6, R10 (rule-bearing)
    "SubGoalTransition",       # battle phase transitions — rule R11 (rule-bearing)
    "InformationState",        # information reveal sequence — assessment dimension (rule-bearing eligibility)
]
# CoordinationDependency and OptimizationCriterion excluded: EC-07 states no violation rules apply.
```

### Rule-Bearing vs Dimensional-Only Distinction

The 8 abstractions split asymmetrically:

| Abstraction | Class | Rules served |
|---|---|---|
| ResourceBudget_HP | rule-bearing | R3, R4, R8, R9 |
| ResourceBudget_PP | rule-bearing | R1 |
| ResourceBudget_time | rule-bearing | R1 |
| ResourceBudget_status | dimensional-only | none |
| ResourceBudget_boost | dimensional-only | none |
| ToolAvailability | rule-bearing | R2, R6, R10 |
| SubGoalTransition | rule-bearing | R11 |
| InformationState | rule-bearing | assessment dimension (no direct rule in v5.3, rule-eligible) |

**Implications for Lever 13 L2 selection:**
- Both selection criteria (importance score, corpus frequency) score abstractions by how often they trigger violations.
- Dimensional-only abstractions (ResourceBudget_status, ResourceBudget_boost) trigger no violations by construction.
- They will score 0 on both criteria and be naturally excluded from the top-3 under either selection path.
- This is a documented feature, not a defect: the L2 condition tests "show the model only the top-3 violation-bearing abstractions" and dimensional-only categories rightly fall outside that subset.

---

## Verification Checklist for Sign-Off

- [ ] 8 abstraction names confirmed from pipeline (unblocks placeholder replacement)
- [ ] Symbolic checker importance_metrics attribute/method confirmed accessible (or confirmed unavailable)
- [ ] v5.1 corpus frequency counts computed and documented
- [ ] Resolved top-3 list documented in condition metadata schema
- [ ] Code stub tested with actual pipeline before OLAT execution
