# Agent A1 — Sonnet, No Internet

## Configuration
- **Model:** Claude Sonnet (claude-sonnet-4-6)
- **Internet access:** None
- **Cycles used:** 3 (Cycle 4 attempted and reverted)
- **Chain data source:** 50 unique chains from `pre-registration/chain_variants/`
  (reduced-scale; full 19,428-chain corpus not available in this environment)

## Final Performance

| Set | n | TP | TN | FP | FN | Precision | Recall | F1 |
|-----|---|----|----|----|----|-----------|--------|-----|
| Iteration test | 10 | 4 | 5 | 0 | 1 | 1.000 | 0.800 | 0.889 |
| Development | 30 | 12 | 15 | 0 | 3 | 1.000 | 0.800 | 0.889 |
| Validation | 20 | 13 | 3 | 0 | 4 | 1.000 | 0.765 | 0.867 |

**Outcome vs. pre-specified criteria:** Moderate-to-strong success.
- Precision 1.0 exceeds the strong success threshold (>0.85)
- Recall 0.765 sits between moderate (>0.60) and strong (>0.80) success thresholds
- No false positives across any test set

## Design Rationale

The checker works by parsing constraint chain text into step blocks, then
applying a set of deterministic rules derived from analysis of the chain format.
The structure is rule-based rather than statistical because the constraint chain
representation is highly structured and the violation types correspond directly
to observable symbolic patterns (HP values, PP values, ToolAvailability event
sequences). Rule-based detection offers perfect precision when rules are correctly
specified — each rule fires only when a genuine physical impossibility is present.

Detected violation categories:
1. **hp_resurrection (direct):** HP of a unit rises from 0.0% to >0% in a later step
2. **hp_resurrection (permanent faint):** A unit marked (permanent) UNAVAILABLE
   later shows HP > 0% (permanently fainted unit cannot have positive HP)
3. **pp_monotone_violation:** A PP resource value increases between observations
   (PP can only decrease in normal gameplay)
4. **causal_incoherence (active_pair):** A unit in the active_pair is in UNAVAILABLE state
5. **causal_incoherence (permanent revived):** A permanently fainted unit receives
   a subsequent AVAILABLE event
6. **causal_incoherence (permanent re-unavailable):** A permanently fainted unit
   is marked UNAVAILABLE again
7. **causal_incoherence (same-turn UNAVAIL→AVAIL):** A unit goes off-field and
   returns to the field within the same battle turn — impossible in standard mechanics
8. **causal_incoherence (rapid double-UNAVAILABLE):** A unit in UNAVAILABLE state
   is marked UNAVAILABLE again within 2 steps, with no intervening AVAILABLE event

## Self-Assessment

**Most confident:**
- PP monotone violation (100% accuracy across all sets) — perfectly detectable from
  value sequence with no ambiguity
- HP resurrection from 0% (high accuracy) — clear pattern, few edge cases
- None/intact chains (100% — zero false positives) — conservative rules by design

**Moderately confident:**
- Multiple violations containing hp_resurrection or PP monotone components —
  these are caught via the component rules
- Causal incoherence with active_pair data — highly reliable when the format
  includes active_pair annotations

**Least confident:**
- Causal incoherence without active_pair data — depends on ToolAvailability event
  sequences only; some violations require knowing which unit is actively battling,
  which is only encoded in the active_pair field (present in some chain formats, not all)
- hp_resurrection in chains where the resurrection happens outside the observed
  15-step window — inherently undetectable from the window alone
- Multiple violation chains that combine detectable + undetectable violations —
  if the only violation in the window is undetectable (e.g., active_pair needed),
  the chain is missed

## Irreducible False Negatives

Three types of violations cannot be detected reliably from the 15-step text format:

1. **Window limitation for hp_resurrection:** Some chains show HP going 0%→>0%
   only in the full chain, but the 15-step window captures only one end of the pattern.

2. **Causal incoherence via active_own/active_pair:** Some violations are only
   visible when you know which unit is currently the active battler. The text format
   sometimes includes `active_pair: own=X opp=Y` (detectable) but sometimes omits
   it (undetectable).

3. **Double UNAVAILABLE beyond 2-step threshold:** Some chains show a unit going
   UNAVAILABLE → UNAVAILABLE with a gap larger than 2 steps. Flagging this creates
   false positives on valid chains where the intermediate AVAILABLE event falls
   outside the chain window.

## Iteration Log Summary

| Cycle | Key Change | Dev F1 | Val F1 | Decision |
|-------|-----------|--------|--------|----------|
| 1 | Initial rules: hp_resurrection, PP, causal_incoherence (active_pair + permanent_revived) | 0.845 | — | Keep |
| 2 | Added permanent-unit-re-unavailable; tested+rejected broad double-UNAVAILABLE | 0.889 | — | Keep |
| 3 | Added permanent-faint+HP>0, same-turn UNAVAIL→AVAIL, rapid double-UNAVAILABLE ≤2 steps | 0.889 | 0.867 | Keep (FINAL) |
| 4 | Added faint temporal order (hp=0 in turn T, faint event in turn T+1); REVERTED — same pattern appears in valid chains | — | — | Reverted |
