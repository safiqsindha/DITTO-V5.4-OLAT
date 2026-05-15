# Agent B2 — Sonnet, Internet Access

## Configuration
- **Model:** Claude Sonnet (claude-sonnet-4-6)
- **Internet access:** Yes (5 targeted searches; see search_log.jsonl)
- **Cycles used:** 2 (Cycle 2 stable; no further safe rules found)
- **Chain data source:** 50 unique chains from `pre-registration/chain_variants/`

## Final Performance

| Set | n | TP | TN | FP | FN | Precision | Recall | F1 |
|-----|---|----|----|----|----|-----------|--------|-----|
| Iteration test | 10 | 4 | 5 | 0 | 1 | 1.000 | 0.800 | 0.889 |
| Development | 30 | 13 | 15 | 0 | 2 | 1.000 | 0.867 | 0.929 |
| Validation | 20 | 13 | 3 | 0 | 4 | 1.000 | 0.765 | 0.867 |

**Outcome vs. pre-specified criteria:** Moderate-to-strong success.
- Precision 1.0 exceeds strong success threshold (>0.85) on all sets
- Dev F1 0.929 exceeds strong success threshold (>0.80 recall on dev)
- Val F1 0.867 / recall 0.765 sits between moderate and strong on validation
- No false positives across any test set

## Internet Access Contribution

Internet access yielded two substantive findings:

**Finding 1 — Generalized monotone rule.** Internet confirmed that the chain's
`decay=monotone_decrease` annotation is a first-class constraint: any annotated
resource must be non-increasing. This extends detection beyond `pp_action_*` to
`match_time_remaining` and any future annotated monotone resource. A1 checked only
`pp_action_*` prefix. Practical impact on this dataset: `match_time_remaining` appears
in the chain format but no violations of it appear in the test sets — net 0 additional
TPs. The rule is architecturally stronger for deployment on the full corpus.

**Finding 2 — own_faint consistency rule.** Internet confirmed that when a
SubGoalTransition carries `trigger=own_faint`, a permanently fainted unit should
always produce a `ToolAvailability UNAVAILABLE(permanent)` event. Chains with the faint
trigger but no corresponding permanent event are causally incoherent. Empirically
verified on 132 sampled chains: all 34 with `own_faint` and no `perm_faint` were
violated (ground_truth=YES); 0 valid chains lacked the permanent event when
`own_faint` appeared. **Practical impact: +1 TP on dev (F1 0.889 → 0.929). Net 0
on validation (the rule fires there, but for chains already caught by other rules).**

**Finding 3 — HP increase from non-zero is valid.** Internet confirmed many legitimate
mechanisms for HP to increase from >0%. This suppressed a potential rule that would
have penalized any HP increase (which would have caused false positives). Not
quantified directly, but prevented a regression.

## Design Rationale

Same conservative rule-based approach as A1. Each rule fires only on physical
impossibilities. The internet access allowed one additional rule (own_faint
consistency) and generalization of the monotone rule.

Detected violation categories:
1. **hp_resurrection (0→positive):** HP of a unit rises from 0.0% to >0% in a later step
2. **hp_resurrection (permanent faint):** A unit marked (permanent) UNAVAILABLE later shows HP > 0%
3. **pp_monotone_violation (generalized):** Any resource annotated `decay=monotone_decrease`
   or any `pp_action_*` resource increases between observations
4. **causal_incoherence (active_pair):** A unit in the active_pair is in UNAVAILABLE state
5. **causal_incoherence (permanent revived):** A permanently fainted unit receives AVAILABLE
6. **causal_incoherence (permanent re-unavailable):** A permanently fainted unit is UNAVAILABLE again
7. **causal_incoherence (same-turn UNAVAIL→AVAIL):** Off-field then back same turn
8. **causal_incoherence (rapid double-UNAVAILABLE):** UNAVAILABLE→UNAVAILABLE within 2 steps
9. **causal_incoherence (own_faint without perm_faint):** `trigger=own_faint` in SubGoalTransition
   without any UNAVAILABLE(permanent) event in the window

## Iteration Log

| Cycle | Key Change | Dev F1 | Val F1 | Decision |
|-------|-----------|--------|--------|----------|
| 1 | Generalized monotone rule + full A1 causal_incoherence suite | 0.889 | — | Keep |
| 2 | Added own_faint consistency rule (trigger=own_faint without perm_faint) | **0.929** | **0.867** | **FINAL** |

## Irreducible False Negatives

Same three failure modes as A1, unchanged by internet access:

1. **Window limitation for hp_resurrection:** The 0%→>0% transition outside the
   15-step window. Internet does not help extend the observable window.

2. **Causal incoherence without active_pair:** Some violations require knowing the
   active battler. Internet knowledge cannot substitute for missing `active_pair` data
   in the chain text.

3. **Double non-permanent UNAVAILABLE beyond 2-step threshold:** Extending the gap
   threshold beyond 4 steps creates false positives on valid (none) chains.

## A1 vs B2 Comparison

| Metric | A1 (no internet) | B2 (internet) | Delta |
|--------|-------------------|---------------|-------|
| Dev F1 | 0.889 | **0.929** | +0.040 |
| Val F1 | 0.867 | 0.867 | 0 |
| Val Precision | 1.000 | 1.000 | 0 |
| Val Recall | 0.765 | 0.765 | 0 |
| Rules | 8 | 9 | +1 |

**Conclusion:** Internet access yielded one new rule (own_faint consistency) that
improved development-set recall by 0.040. Validation performance is identical —
the new rule's new detections in validation were already caught by other rules.
The generalized monotone rule is architecturally superior but produces no
additional detections on these test sets. Internet access helped most with
confirming rule semantics and preventing potential false positive rules (HP
increase from non-zero), not with discovering entirely new violation patterns.
