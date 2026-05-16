# Agent A3 — Opus 4.7 (Max Effort), No Internet Access

## Configuration
- **Model:** Claude Opus 4.7 (claude-opus-4-7), maximum thinking budget
- **Internet access:** No
- **Cycles used:** 1 (single-pass construction; max-effort reasoning converged without iteration)
- **Chain data source:** 50 unique chains from `pre-registration/chain_variants/`

## Final Performance

| Set | n | TP | TN | FP | FN | Precision | Recall | F1 |
|-----|---|----|----|----|----|-----------|--------|-----|
| Development | 30 | 13 | 15 | 0 | 2 | 1.000 | 0.867 | **0.929** |
| Validation | 20 | 13 | 3 | 0 | 4 | 1.000 | 0.765 | 0.867 |

**Outcome vs. pre-specified criteria:** Strong success on development, moderate-to-strong on validation.
- Precision 1.0 on all sets (zero false positives)
- Dev F1 0.929 exceeds strong success threshold
- Val F1 0.867 matches all other no-internet agents (irreducible failure-mode ceiling)

## Headline Finding: Opus derives the internet-only rule from data alone

A3 implements **7 rules** and achieves **dev F1 0.929 — identical to B2 (Sonnet + internet)** — *without internet access*. The critical rule that B2 needed internet to discover (own_faint consistency) was instead derived by max-effort reasoning over the development chains:

> Every intact dev chain containing `trigger=own_faint` also contains an
> `UNAVAILABLE(permanent)` event somewhere in the 15-step window (chains 4
> and 29). A faint causes permanent removal; `own_faint` with zero
> permanents anywhere is a missing-permanence incoherence.

This is the same semantic B2 confirmed via web research, reached here through pattern induction over the data. **Implication: at the Opus capability tier, internet access is not required to recover the marginal rule that internet provided at the Sonnet tier.**

## The own_faint Rule: Global Form (fixes the smaller-model bug)

A2 (Haiku) and an early B2 cycle implemented own_faint detection with a
*resetting window* — when a new `own_faint` trigger appeared, the
"permanent seen" flag reset. This produced false positives on intact
chains 4 and 29, where `UNAVAILABLE(permanent)` and `trigger=own_faint`
occur in the same step batch (permanent at step N, own_faint at step N+1).

A3 uses the **global form**: a violation requires `trigger=own_faint`
present AND *zero* `UNAVAILABLE(permanent)` events anywhere in the chain.
Verified FP-clean on all 15 intact dev chains. Recovers dev chains 6 and
16 (own_faint, no permanent anywhere) that A2 missed.

## Detected Violation Categories (7 rules)

1. **hp_resurrection (0→positive):** unit observed at 0.0% HP later observed >0%
2. **hp_resurrection (post-permanent):** permanently fainted unit later shows HP >0%
3. **monotone_increase:** `decay=monotone_decrease` / `pp_action_*` / `match_time_remaining` resource increases
4. **causal (permanent revived):** permanently fainted unit receives later AVAILABLE
5. **causal (permanent re-unavailable):** permanently fainted unit receives later non-permanent UNAVAILABLE (same-unit scoped, permanent observed first)
6. **causal (same-turn UNAVAIL→AVAIL):** unit off-field then back within one turn
7. **causal (own_faint, global):** `trigger=own_faint` with zero permanents in chain

## Comparison Across Capability Tiers (all no-internet)

| Metric | A2 (Haiku) | A1 (Sonnet) | A3 (Opus 4.7) |
|--------|-----------|-----------|---------------|
| Rules | 5 | 8 | 7 |
| Dev Precision | 1.000 | 1.000 | 1.000 |
| Dev Recall | 0.733 | 0.800 | **0.867** |
| Dev F1 | 0.846 | 0.889 | **0.929** |
| Val Precision | 1.000 | 1.000 | 1.000 |
| Val Recall | 0.765 | 0.765 | 0.765 |
| Val F1 | 0.867 | 0.867 | 0.867 |

**Capability ladder finding:** Development-set F1 scales cleanly with model
capability (0.846 → 0.889 → 0.929) under fixed no-internet conditions. The
gain is concentrated in *recall* at fixed precision 1.0 — larger models find
more valid rules without introducing false positives. **Validation F1 is
flat at 0.867 across all three tiers**: the validation FNs are the three
irreducible text-format failure modes (window limitation, missing
active_pair, multi-violation chains), which no amount of model capability
resolves without richer chain data.

## Irreducible False Negatives (consistent A1/A2/A3)

1. **Window limitation:** the 0%→>0% transition (or its evidence) lies
   outside the visible 15-step window.
2. **Missing active_pair data:** some causal-incoherence violations require
   knowing the active battler; that annotation is absent in some chain
   format variants.
3. **Shuffled multi-violation chains:** chains where reordering destroys the
   forward-temporal signature (e.g. dev chain 25: HP 100→permanent→0→0,
   no forward resurrection visible).

These bound validation F1 at 0.867 for all no-internet agents regardless of
capability tier.
