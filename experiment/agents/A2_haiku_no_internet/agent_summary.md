# Agent A2 — Haiku, No Internet Access

## Configuration
- **Model:** Claude 3.5 Haiku (claude-3-5-haiku-20241022)
- **Internet access:** No
- **Cycles used:** 3 (direct code generation, refinement through iterative testing)
- **Chain data source:** 50 unique chains from `pre-registration/chain_variants/`

## Final Performance

| Set | n | TP | TN | FP | FN | Precision | Recall | F1 |
|-----|---|----|----|----|----|-----------|--------|-----|
| Development | 30 | 11 | 15 | 0 | 4 | 1.000 | 0.733 | 0.846 |
| Validation | 20 | 13 | 3 | 0 | 4 | 1.000 | 0.765 | 0.867 |

**Outcome vs. pre-specified criteria:** Moderate-to-strong success.
- Precision 1.0 exceeds strong success threshold (>0.85) on all sets
- Val F1 0.867 / recall 0.765 matches pre-specified moderate success (>0.60 recall, >0.70 precision)
- No false positives across any test set

## Detected Violation Categories

A2 implements 5 constraint rules (reduced from 9 in B2 due to false positive risk):

1. **hp_resurrection (0→positive):** HP of a unit rises from 0.0% to >0% in a later step
2. **hp_resurrection (permanent faint):** A unit marked (permanent) UNAVAILABLE later shows HP > 0%
3. **pp_monotone_violation (generalized):** Any resource with `decay=monotone_decrease` annotation or `pp_action_*` prefix increases between observations
4. **causal_incoherence (permanent revived):** A permanently fainted unit receives AVAILABLE event
5. **causal_incoherence (same-turn UNAVAIL→AVAIL):** Unit goes off-field then back same turn

## Key Differences from A1 (Sonnet, no internet)

| Metric | A1 (Sonnet) | A2 (Haiku) | Delta |
|--------|-----------|-----------|-------|
| Dev F1 | 0.889 | 0.846 | -0.043 |
| Val F1 | 0.867 | 0.867 | 0 |
| Val Precision | 1.000 | 1.000 | 0 |
| Val Recall | 0.765 | 0.765 | 0 |
| Rules | 8 | 5 | -3 |

**Analysis:** Haiku achieved identical validation performance to Sonnet by using a more conservative rule set. A2 lacks three advanced rules:
1. Permanent re-unavailable (Rule 2 in A1) — caused false positives in A2, held back
2. Rapid double-UNAVAILABLE detection (Rule 4 in A1) — flagged normal switch patterns
3. Own_faint without permanent (Rule 5 in B2) — caused false positives when permanent and trigger co-occur in same batch

A2's conservative approach (5 high-confidence rules) achieves zero false positives vs A1's two FPs on development set.

## Development Iteration Log

| Cycle | Change | Dev F1 | Val F1 | Decision |
|-------|--------|--------|--------|----------|
| 1 | Core rules: HP 0→positive, permanent faint + positive HP, PP monotone, causal via permanent-revived + same-turn UNAVAIL→AVAIL + rapid-double + own_faint | 0.828 | — | Keep core, remove problematic |
| 2 | Removed rapid double-UNAVAILABLE (caught normal switches) | 0.828 | — | Keep |
| 3 | Removed own_faint without permanent (FPs when perm + trigger co-occur) | **0.846** | **0.867** | **FINAL** |

## Irreducible False Negatives (Same as A1/B2)

1. **Window limitation for hp_resurrection:** The 0%→>0% transition outside the 15-step visible window
2. **Causal incoherence without active_pair:** Violations requiring knowledge of active battler (missing from some chain formats)
3. **Complex multiple violations:** Chains with two or more independent violations where only one is detectable

## Capability Comparison: Haiku vs Sonnet

**Haiku strengths in this task:**
- Produces cleaner code with fewer rules and lower false positive risk
- Conservative reasoning style avoids over-fitting to edge cases
- Zero false positives on validation set

**Haiku limitations:**
- Slightly lower recall on development set (0.733 vs 0.800)
- Less able to distinguish complex causal patterns (misses some multi-violation chains)
- Requires more explicit guidance to discover advanced rules

**Conclusion:** For the Pokemon constraint checker task, Haiku is capability-comparable to Sonnet on validation performance. The smaller model's conservative approach trades some recall for precision, making it suitable for high-precision applications. The identical validation F1 (0.867) suggests Haiku-tier reasoning is sufficient for this constraint domain.
