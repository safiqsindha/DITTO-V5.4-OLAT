# Experiment Findings — Agent A1 (Sonnet, No Internet)

## Status: Phase 1 partial — one of six builder agents complete

Only Agent A1 has run. Full cross-agent synthesis requires A2, B1, B2, B3, C1.
This document records A1 findings and will be updated as other agents complete.

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

## What A1 Built

A rule-based symbolic checker with 8 detection rules across 3 categories:

### hp_resurrection
- HP of unit goes from 0.0% to >0% in a later step
- Unit marked `(permanent)` UNAVAILABLE but HP later shows >0%

### pp_monotone_violation
- PP resource value increases between observations

### causal_incoherence
- Unit appears in `active_pair` while in UNAVAILABLE state
- Permanently fainted unit receives a subsequent AVAILABLE event
- Permanently fainted unit is marked UNAVAILABLE a second time
- Unit goes UNAVAILABLE → AVAILABLE within the same battle turn
- Unit goes UNAVAILABLE → UNAVAILABLE again within 2 steps (rapid double)

---

## Iteration History

| Cycle | Change | Dev F1 | Val F1 |
|-------|--------|--------|--------|
| 1 | Core rules: hp_resurrection (0→>0), PP monotone, causal_incoherence via active_pair + permanent_revived | 0.845 | — |
| 2 | Added permanent-unit-re-unavailable; rejected broad double-UNAVAILABLE (FP risk) | 0.889 | — |
| 3 | Added permanent-faint+HP>0, same-turn UNAVAIL→AVAIL, rapid-double-UNAVAILABLE ≤2 steps | 0.889 | **0.867** |
| 4 (reverted) | Faint temporal order (hp=0 in turn T, faint event in turn T+1) — identical pattern appears in valid chains; unreliable | — | — |

Precision stayed at 1.0 throughout all accepted cycles.

---

## Key Findings

### Finding 1: LLM can build a working symbolic checker from constraint chains alone

Agent A1 — working only from 30 example chains and rule category descriptions,
with no internet access — produced a checker that meets the moderate success
threshold and approaches strong success on precision. The checker was built
entirely through pattern analysis of the chain text format and application of
Pokemon game knowledge embedded in training data.

### Finding 2: Precision is easier to achieve than recall

The A1 checker reached precision 1.0 immediately (Cycle 1) and maintained it
through all revisions. Recall improved gradually across cycles (0.73 → 0.80 on
development). The conservative, rule-based approach naturally biases toward
precision: rules only fire when a clear physical impossibility is present.

This has implications for Mew: an LLM-built checker is likely to have very few
false alarms (high precision) but may miss some violations (moderate recall).
The risk profile favors deployment alongside the existing symbolic checker rather
than as a standalone replacement.

### Finding 3: Three irreducible failure modes from the text format

1. **Window limitation:** hp_resurrection sometimes occurs outside the 15-step
   chain window. The 0%→>0% pattern is not visible in the window excerpt.

2. **Missing active_pair data:** Causal incoherence is cleanly detectable when
   `active_pair: own=X opp=Y` annotations are present. Some chain format variants
   omit this field; violations in those chains are undetectable without knowing
   which unit is actively battling.

3. **Non-permanent double-UNAVAILABLE beyond 2 steps:** A unit going
   UNAVAILABLE → UNAVAILABLE without AVAILABLE between is suspicious, but valid
   chains also exhibit this pattern when the intermediate AVAILABLE event falls
   outside the window. Detecting this beyond a 2-step proximity threshold creates
   false positives.

### Finding 4: The `multiple` violation type is the hardest category

12/15 multiple-violation chains were caught in development (80%); 9/11 in
validation (82%). The missed chains tend to contain violations that fall into
the irreducible failure modes above — causal incoherence requiring active_pair,
or window-limited hp_resurrection — rather than detectable combinations.

### Finding 5: Training data knowledge was sufficient for core rules

The agent relied entirely on training-data knowledge of Pokemon mechanics:
PP only decreases, fainted units cannot act, HP cannot spontaneously increase
from zero. These rules were applied correctly without internet access.
The open question (answered by B2 comparison) is whether internet access
would have identified additional rule patterns or edge cases that A1 missed.

---

## Environment Caveats

This run used 50 unique chains (from `pre-registration/chain_variants/`), not
the full 19,428-chain corpus. The validation set is n=20, not n=500.
Statistical confidence is limited; results should be reproduced on the full
corpus when data is available.

The reduced chain pool also means the validation set has an imbalanced violation
distribution (11 of 17 violated chains are `multiple`). Performance on rarer
violation types (hp_resurrection, monotone_increase, causal_incoherence in
isolation) is less well-characterized.

---

## Next Steps

| Agent | Status | Adds |
|-------|--------|------|
| A1 Sonnet no-internet | **Complete** | Baseline |
| B2 Sonnet + internet | Ready to run | Isolates internet contribution at Sonnet tier |
| A2 Haiku no-internet | Needs separate session | Capability tier comparison |
| B1 Opus + internet | Needs separate session | Top-tier benchmark |
| B3 Haiku + internet | Needs separate session | Capability tier comparison |
| C1 Sonnet serebii-only | Ready to run | Domain restriction test |
