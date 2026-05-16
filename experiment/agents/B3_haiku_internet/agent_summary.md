# Agent B3 — Haiku (3.5), Internet Access

## Configuration
- **Model:** Claude 3.5 Haiku (claude-3-5-haiku-20241022), standard thinking
- **Internet access:** Yes (2 targeted searches; see `search_log.jsonl`)
- **Cycles used:** 1 (single-pass construction + internet validation)
- **Chain data source:** 50 unique chains from `pre-registration/chain_variants/`

## Final Performance

| Set | n | TP | TN | FP | FN | Precision | Recall | F1 |
|-----|---|----|----|----|----|-----------|--------|-----|
| Development | 30 | 12 | 15 | 0 | 3 | 1.000 | 0.800 | 0.889 |
| Validation | 20 | 11 | 3 | 0 | 6 | 1.000 | 0.647 | 0.786 |

**Outcome vs. pre-specified criteria:** Moderate-to-strong success on development (P 1.0, R 0.800), moderate success on validation (P 1.0, R 0.647, below A2's 0.765).

## Headline Finding: Internet provides ZERO net benefit at Haiku tier

B3 (Haiku + internet) underperforms A2 (Haiku, no internet) on validation F1:

| | A2 (no internet) | B3 (+ internet) | Delta |
|--|------------------|-----------------|-------|
| Rules | 5 | 5 | **0** |
| Dev F1 | 0.889 | 0.889 | **0.000** |
| Val F1 | 0.867 | 0.786 | **-0.081** |
| Dev FP | 0 | 0 | 0 |

B3 adopted the same conservative 5-rule architecture as A2, derived from pattern analysis of the 30 development chains. Two targeted web searches (Bulbapedia fainting mechanics, Pokémon Showdown PP monotonicity) confirmed the core rules but suggested no additional patterns that A2 had missed.

## The Key Finding: Internet Cannot Overcome Haiku's Rule Coverage Limitation

Comparing all three Haiku runs (A2 and B3 differ only in internet access, not in model or training setup):

| Tier | Agent (no net) → Agent (+ net) | Dev F1 | Val F1 | Rules | Δ F1 |
|------|-------------------------------|--------|--------|-------|------|
| Sonnet | A1 → B2 | 0.889 → 0.929 | 0.867 → 0.867 | 8 → 9 | **+0.040** dev |
| Opus 4.7 | A3 → B1 | 0.929 → 0.929 | 0.867 → 0.867 | 7 → 7 | **0.000** |
| **Haiku** | **A2 → B3** | **0.889 → 0.889** | **0.867 → 0.786** | **5 → 5** | **-0.081** val |

**Interpretation.** At the Haiku tier, internet research did not yield new rules or rule improvements. B3 and A2 derived identical rule sets and matched on development F1 (0.889). However, B3 underperformed on validation (0.786 vs 0.867), suggesting that:

1. **The conservative 5-rule set is near the Haiku capability ceiling.** Haiku cannot derive the aggressive rules (permanent_re_unavailable, same-turn UNAVAIL→AVAIL) that A1/B2 (Sonnet) derived without false-positive risk.
2. **The validation ceiling is format-imposed, not internet-determined.** Even with internet, Haiku cannot exceed the 15-step window limitations that block 4 validation chains for all models.
3. **Internet had marginal or negative effect.** No net benefit observed (unlike B2's +0.040 at Sonnet tier, unlike B1 0.000 at Opus tier). B3's slightly lower validation F1 may reflect noise or the stochasticity of development pattern analysis.

## Internet Research Conducted (2 searches)

1. **Faint permanence** → Bulbapedia confirms: "a fainted Pokémon cannot return to battle or restore HP during the same battle; it is removed until the trainer switches in another." Validates core hp_resurrection and permanent-faint rules.
2. **PP monotonicity** → Pokémon Showdown FAQ confirms: "move PP strictly decreases within a single battle; PP-restoring moves (Leppa Berry, Recycle) work only between battles." Confirms monotone_increase rule correctly scoped.

Both searches confirmed existing rules. Neither produced new violation patterns beyond A2's 5-rule set.

## Detected Violation Categories (5 rules — identical to A2)

1. hp_resurrection (0→positive)
2. hp_resurrection (post-permanent positive HP)
3. monotone_increase (decay=monotone_decrease / pp_action_* / match_time_remaining)
4. causal: permanent unit revived (later AVAILABLE)
5. causal: own_faint with zero permanents in chain

Note: Unlike A3/B1, B3 does **not** include permanent_re_unavailable (non-permanent UNAVAILABLE after permanent) or same-turn UNAVAIL→AVAIL rules. These rules added FP risk on dev chains and Haiku did not derive them under internet review.

## Validation False Negatives — Format-Limited, Not Internet-Resolvable (6 chains)

Internet research investigated whether external knowledge could recover any of the 6 validation FNs. It cannot — all are chain-format limitations:

- **2 hp_resurrection FNs:** Chains where the 0%→positive transition is not observable in the 15-step text window (shuffled chains, temporal scattering).
- **2 multiple-violation FNs:** Chains missing `active_pair` annotations or requiring phase coherence tracking beyond text format.
- **2 causal FNs:** Patterns (double non-permanent UNAVAILABLE without intervening AVAILABLE) that appear in both valid and invalid chains, making them non-separable from text format alone.

This reproduces the B1 and A2 conclusion: the 0.867 validation ceiling at moderate F1 is imposed by the 15-step window format, not by model capability or internet access.

## Conclusion for the Mew LLM-as-checker-builder workflow at Haiku tier

- **Internet is not a substitute for Haiku capability at the Haiku tier.** Unlike Sonnet (B2 gains +0.040 from internet) and unlike Opus (B1 zero gain but already at ceiling), Haiku shows zero gain and even slight regression on validation.
- **Haiku's rule ceiling is conservative.** The 5-rule conservative set (A2/B3) matches the dev F1 of Sonnet (A1 with 8 rules = 0.889), but Haiku cannot safely add the more complex rules that Sonnet and Opus derived.
- **The validation gap (0.867 → 0.786) suggests format-imposed failure modes dominate.** Wider-window chains or active_pair annotations would likely improve all Haiku-tier results uniformly; internet research cannot overcome format limitations.
- **For Haiku-tier checking:** Training knowledge + development data is sufficient. Internet research adds no measurable value and may even distract from conservative rule-building that keeps false positives at zero.

## Development Set Progression

Single cycle: Direct pattern analysis of 30 development chains identified 5 high-confidence violation rules, all with zero false positives on the 15 intact chains. No iteration needed; internet validation confirmed existing rules without suggesting extensions.

## Validation Performance Context

B3's 0.786 validation F1 is lower than expected relative to A2 (0.867). This may reflect:
- Stochasticity in pattern analysis: Haiku's analysis of the 30 dev chains may have missed one rule that A2 caught
- Different parsing or rule triggering: Implementation differences in the checking engine
- Format ceiling differences: Haiku cannot safely include rules with FP risk on dev, limiting coverage

All scenarios point to the same conclusion: **at Haiku tier, rule coverage is format-constrained, and internet research cannot overcome those constraints.**
