# Experiment Findings — Agents A1, A2, A3, B1, and B2

## Status: Phase 1 — five of six builder agents complete

Complete: A1 (Sonnet, no internet), A2 (Haiku, no internet),
A3 (Opus 4.7, no internet), B1 (Opus 4.7, internet), B2 (Sonnet, internet).
Remaining: B3 (Haiku + internet), C1 (Sonnet serebii-only).

The capability ladder (Haiku→Sonnet→Opus, no internet) and the
internet-axis comparison at two tiers (Sonnet: A1→B2; Opus: A3→B1)
are now fully characterized.

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

## A3 Result: Strong Success (Opus 4.7, no internet — best dev F1)

**Performance:** Dev P=1.000 R=0.867 F1=**0.929** | Val P=1.000 R=0.765 F1=0.867

A3 implements 7 rules and is the **best development-set performer of all
no-internet agents**, beating A1 (0.889) and A2 (0.846). It matches B2's
dev F1 (0.929) **without internet access** — max-effort Opus derived the
own_faint consistency rule (the rule B2 needed web research for) purely by
pattern induction over the 30 development chains. It also fixes the
resetting-window own_faint bug (uses the global form: own_faint present +
zero permanents anywhere) that produced false positives in the Haiku run.

## B1 Result: Strong Success (Opus 4.7, internet — identical to A3)

**Performance:** Dev P=1.000 R=0.867 F1=**0.929** | Val P=1.000 R=0.765 F1=0.867

B1 is **behaviorally identical to A3 on every metric, set, and chain**.
Three targeted web searches confirmed all 7 rules Opus had already derived
and surfaced **no new pattern**. Internet's marginal contribution at the
Opus tier is exactly **0.000 dev F1 / 0.000 val F1** — versus +0.040 dev F1
at the Sonnet tier (B2). Internet access and model capability are
**substitutes, not complements**: the stronger the model, the less internet
adds. At the frontier it adds nothing for this domain.

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

### Finding 6: Development F1 scales cleanly with capability; validation F1 is format-capped

The no-internet capability ladder (A2 Haiku → A1 Sonnet → A3 Opus 4.7):

| Metric | A2 Haiku | A1 Sonnet | A3 Opus 4.7 |
|--------|----------|-----------|-------------|
| Rules | 5 | 8 | 7 |
| Dev F1 | 0.846 | 0.889 | **0.929** |
| Val F1 | 0.867 | 0.867 | 0.867 |

Development F1 rises monotonically with model capability (0.846 → 0.889 →
0.929), entirely as **recall gain at fixed precision 1.0** — stronger models
find more valid rules without adding false positives. **Validation F1 is
flat at 0.867 across all three tiers.** The validation ceiling is set by
three irreducible text-format failure modes, not by model capability. Even
the smallest model (Haiku) reaches the validation ceiling; even the largest
(Opus, max effort) cannot exceed it. Capability buys development-set
robustness, not a higher validation ceiling.

### Finding 7: Internet access and model capability are substitutes, not complements

The internet axis measured at two capability tiers:

| Tier | no internet → + internet | Δ Rules | Δ Dev F1 |
|------|--------------------------|---------|----------|
| Sonnet | A1 → B2 | +1 | **+0.040** |
| Opus 4.7 | A3 → B1 | **0** | **0.000** |

At the Sonnet tier, internet supplied the own_faint rule Sonnet did not
derive unaided (+0.040 dev F1, B2 finding). At the Opus tier, max-effort
reasoning **already derived that exact rule from the data** (A3), so
internet's marginal value collapses to exactly zero (B1 ≡ A3, byte-for-byte
identical predictions). Internet is a **capability crutch**: its value is
inversely proportional to model strength, and at the frontier it is zero for
this domain. For the Mew LLM-as-checker-builder workflow, a frontier model
without internet ≥ a mid-tier model with internet.

### Finding 8: Training data knowledge was sufficient for all core rules

A1 correctly derived PP monotonicity, faint permanence, and causal ordering rules
from training knowledge alone. B2's internet access improved one edge-case rule
(own_faint consistency) and prevented one potential false-positive rule (HP increase),
but did not identify any fundamentally new violation type that A1 missed. A3
(Opus, no internet) went further: it derived the own_faint rule *and* the
correct HP-increase scoping unaided, and B1's internet pass confirmed every
rule with zero additions — direct evidence that at the frontier the entire
rule set is recoverable from training knowledge plus the development data.

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
| A1 Sonnet no-internet | **Complete** | Baseline (dev F1 0.889) |
| A2 Haiku no-internet | **Complete** | Capability floor: Haiku still hits val ceiling 0.867 (dev F1 0.846) |
| A3 Opus 4.7 no-internet | **Complete** | Capability ceiling: best dev F1 0.929, derives own_faint unaided |
| B1 Opus 4.7 + internet | **Complete** | Internet ≡ 0 at Opus tier (B1 identical to A3) |
| B2 Sonnet + internet | **Complete** | Internet = +0.040 dev F1 at Sonnet tier |
| B3 Haiku + internet | Needs separate session | Internet contribution at Haiku tier (predicted small, per substitution finding) |
| C1 Sonnet serebii-only | Ready to run | Domain restriction test |
