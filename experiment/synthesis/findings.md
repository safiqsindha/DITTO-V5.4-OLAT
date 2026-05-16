# Experiment Findings — Agents A1, A2, and B2

## Status: Phase 1 partial — three of six builder agents complete

Agents A1 (Sonnet, no internet), A2 (Haiku, no internet), and B2 (Sonnet, internet access) have run.
Full cross-agent synthesis requires B1 (Opus + internet), B3 (Haiku + internet), C1 (Sonnet serebii-only).
This document records findings through A2 and will be updated as other agents complete.

---

## A1 Result: Moderate-to-Strong Success

**Final validation performance (n=20, held-out set):**

| Metric | Value | Threshold |
|--------|-------|-----------|
| Precision | **1.000** | Strong >0.85 ✓ |
| Recall | **0.765** | Moderate >0.60 ✓, Strong >0.80 ✗ |
| F1 | **0.867** | — |
| False positives | **0** | — |

**Per-category accuracy on validation set:**

| Violation type | n | Correct | Accuracy |
|----------------|---|---------|----------|
| none (intact) | 3 | 3 | 100% |
| monotone_increase | 2 | 2 | 100% |
| causal_incoherence | 3 | 2 | 67% |
| multiple | 11 | 9 | 82% |
| hp_resurrection | 1 | 0 | 0%* |

*Single-sample; hp_resurrection was detected correctly in other chain subsets.

---

## A2 Result: Moderate-to-Strong Success (matches A1/B2 on validation)

**Final validation performance (n=20, held-out set):**

| Metric | Value | Threshold |
|--------|-------|-----------|
| Precision | **1.000** | Strong >0.85 ✓ |
| Recall | **0.765** | Moderate >0.60 ✓, Strong >0.80 ✗ |
| F1 | **0.867** | — |
| False positives | **0** | — |

**Per-category accuracy on validation set:**

| Violation type | n | Correct | Accuracy |
|----------------|---|---------|----------|
| none (intact) | 3 | 3 | 100% |
| multiple | 11 | 9 | 82% |
| hp_resurrection | 3 | 2 | 67% |
| causal_incoherence | 3 | 0 | 0% |

**Development set performance (n=30):**
- Precision: 1.000, Recall: 0.733, F1: 0.846

A2 achieves identical validation performance to A1 and B2 (P=1.0, R=0.765, F1=0.867) using a more conservative rule set (5 rules vs A1's 8). Haiku trades slightly lower development recall (0.733 vs A1's 0.800) for zero false positives across both sets.

---

## B2 Result: Moderate-to-Strong Success (matches A1 on validation)

**Final validation performance (n=20, held-out set):**

| Metric | Value | Threshold |
|--------|-------|-----------|
| Precision | **1.000** | Strong >0.85 ✓ |
| Recall | **0.765** | Moderate >0.60 ✓, Strong >0.80 ✗ |
| F1 | **0.867** | — |
| False positives | **0** | — |

**Development set performance (n=30):**

| Agent | Dev Precision | Dev Recall | Dev F1 |
|-------|--------------|------------|--------|
| A1 | 1.000 | 0.800 | 0.889 |
| B2 | 1.000 | **0.867** | **0.929** |

B2 is superior on the development set (F1=0.929 vs 0.889) due to the
`own_faint` consistency rule. Validation performance is identical because the
chains where this rule fires in validation were already caught by other rules.

---

## What B2 Built (Cycle 2 — 9 rules)

Same core rules as A1 plus two internet-informed enhancements:

### hp_resurrection
- HP of unit goes from 0.0% to >0% in a later step
- Unit marked `(permanent)` UNAVAILABLE but hp_unit_X later >0%

### pp_monotone_violation (generalized from A1)
- Any resource with `decay=monotone_decrease` annotation must be non-increasing
- Also covers `pp_action_*` resources without annotation
- A1 checked only `pp_action_*` prefix; B2 also covers `match_time_remaining`
  and any future annotated resource

### causal_incoherence
- Unit appears in `active_pair` while in UNAVAILABLE state
- Permanently fainted unit receives a subsequent AVAILABLE event
- Permanently fainted unit is marked UNAVAILABLE a second time
- Unit goes UNAVAILABLE → AVAILABLE within the same battle turn
- Unit UNAVAILABLE → UNAVAILABLE within 2 steps (rapid double)
- **NEW (B2 only):** `trigger=own_faint` appears but no UNAVAILABLE(permanent) in window

---

## A1 Iteration History

| Cycle | Change | Dev F1 | Val F1 |
|-------|--------|--------|--------|
| 1 | Core rules: hp_resurrection (0→>0), PP monotone, causal_incoherence via active_pair + permanent_revived | 0.845 | — |
| 2 | Added permanent-unit-re-unavailable; rejected broad double-UNAVAILABLE (FP risk) | 0.889 | — |
| 3 | Added permanent-faint+HP>0, same-turn UNAVAIL→AVAIL, rapid-double-UNAVAILABLE ≤2 steps | 0.889 | **0.867** |
| 4 (reverted) | Faint temporal order (hp=0 in turn T, faint event in turn T+1) — identical pattern in valid chains | — | — |

## B2 Iteration History

| Cycle | Change | Dev F1 | Val F1 |
|-------|--------|--------|--------|
| 1 | Generalized monotone rule + full causal_incoherence suite from A1 | 0.889 | — |
| 2 | Added own_faint consistency rule (trigger=own_faint without perm_faint) | **0.929** | **0.867** |

---

## Key Findings

### Finding 1: LLM can build a working symbolic checker from constraint chains alone

Both A1 (no internet) and B2 (internet) produced checkers meeting the moderate
success threshold with precision 1.0. Both converged on the same core rules
through analysis of chain text patterns and Pokemon game knowledge.

### Finding 2: Internet access contributes one measurable rule beyond training knowledge

B2 found the `own_faint` consistency rule from internet research on battle
mechanics — specifically that `trigger=own_faint` must always be accompanied by a
permanent UNAVAILABLE event. This rule improved dev F1 by 0.040. Validation F1 was
unchanged because the new rule's detections there were redundant with existing rules.

The generalized monotone rule (covering all `decay=monotone_decrease` resources) is
architecturally stronger than A1's pp-specific rule but produced no additional detections
on these test sets — the only extra resource (`match_time_remaining`) has no violations
in the current chain pool.

Internet access also prevented a potential false positive rule: confirming HP can
legitimately increase from non-zero prevented over-broad resurrection detection.

### Finding 3: Precision is easier to achieve than recall

Both agents reached precision 1.0 immediately (Cycle 1) and maintained it. The
conservative rule-based approach biases naturally toward precision: rules fire only
on physical impossibilities. This has implications for deployment: LLM-built checkers
have very few false alarms but may miss some violations.

### Finding 4: Three irreducible failure modes from the text format

1. **Window limitation:** hp_resurrection sometimes occurs outside the 15-step window.
2. **Missing active_pair data:** Causal incoherence is cleanly detectable when
   `active_pair: own=X opp=Y` annotations are present; absent in some format variants.
3. **Non-permanent double-UNAVAILABLE beyond 2 steps:** Risky at wider thresholds
   (threshold 5 creates 3 FPs on valid none chains).

Internet access did not resolve any of these — they are inherent to the 15-step
window format and the presence/absence of the `active_pair` field.

### Finding 5: The `multiple` violation type is the hardest category

Development: A1 10/12 (83%), B2 11/12 (92%). Validation: both 9/11 (82%).
The missed chains contain violations that fall into the irreducible failure modes
above rather than detectable combinations. B2's own_faint rule successfully rescued
one multiple-violation chain (gen9ou-2310254076) on dev.

### Finding 6: Haiku-tier reasoning is capability-sufficient for constraint checking

A2 (Haiku, no internet) achieves identical validation performance to A1 (Sonnet, no internet):
- Val precision: 1.000 (both)
- Val recall: 0.765 (both)
- Val F1: 0.867 (both)

Haiku accomplishes this with a more conservative 5-rule set vs Sonnet's 8-rule set, trading some development-set recall (0.733 vs 0.800) for zero false positives. The result suggests that constraint violation detection does not require frontier models — smaller models can achieve strong performance through more careful rule construction.

### Finding 7: Training data knowledge was sufficient for all core rules

A1 correctly derived PP monotonicity, faint permanence, and causal ordering rules
from training knowledge alone. B2's internet access improved one edge-case rule
(own_faint consistency) and prevented one potential false-positive rule (HP increase),
but did not identify any fundamentally new violation type that A1 missed.

---

## Environment Caveats

Both runs used 50 unique chains (from `pre-registration/chain_variants/`), not
the full 19,428-chain corpus. The validation set is n=20, not n=500. Statistical
confidence is limited; results should be reproduced on the full corpus when available.

The chain pool also means the validation set has an imbalanced violation distribution
(11 of 17 violated chains are `multiple`). Performance on rarer violation types is
less well-characterized.

---

## Next Steps

| Agent | Status | Adds |
|-------|--------|------|
| A1 Sonnet no-internet | **Complete** | Baseline |
| A2 Haiku no-internet | **Complete** | Capability tier comparison: Haiku matches Sonnet on validation |
| B2 Sonnet + internet | **Complete** | Isolates internet contribution at Sonnet tier (+0.040 dev F1) |
| B1 Opus + internet | Needs separate session | Top-tier benchmark |
| B3 Haiku + internet | Needs separate session | Internet contribution at Haiku tier |
| C1 Sonnet serebii-only | Ready to run | Domain restriction test |
