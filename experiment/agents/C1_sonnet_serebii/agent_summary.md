# Agent C1 — Sonnet, Serebii.net-restricted Internet

## Configuration
- **Model:** Claude Sonnet (claude-sonnet-4-6)
- **Internet access:** Yes — restricted to serebii.net only
- **Cycles used:** 1 (single-pass construction with 3 serebii.net searches)
- **Chain data source:** 50 unique chains from `pre-registration/chain_variants/`

## Final Performance

| Set | n | TP | TN | FP | FN | Precision | Recall | F1 |
|-----|---|----|----|----|----|-----------|--------|-----|
| Development | 30 | 13 | 15 | 0 | 2 | 1.000 | 0.867 | **0.929** |
| Validation | 20 | 13 | 3 | 0 | 4 | 1.000 | 0.765 | **0.867** |

**Outcome vs. pre-specified criteria:** Strong success on development, moderate-to-strong on validation. **Identical to B2 (open internet) on every metric.**

## Headline Finding: Serebii-only restriction costs ZERO performance

C1 (Serebii-only) is indistinguishable from B2 (open internet) on every metric:

| | A1 (no internet) | B2 (open web) | C1 (serebii only) | C1 vs B2 |
|--|-----------------|----------------|-------------------|----------|
| Rules | 8 | 9 | 7 | -2 (cleaner) |
| Dev F1 | 0.889 | **0.929** | **0.929** | **0.000** |
| Val F1 | 0.867 | **0.867** | **0.867** | **0.000** |
| Dev FP | 0 | 0 | 0 | 0 |

C1 achieves the same dev F1 (0.929) and val F1 (0.867) as B2 using only 7 rules (vs B2's 9-rule suite). Serebii's coverage of fainting, HP, PP, and switching mechanics was sufficient to confirm all rules — including the own_faint consistency rule that B2 found via Showdown protocol docs.

## The Domain-Restriction Axis

| Agent | Internet scope | Dev F1 | Val F1 | Rules |
|-------|---------------|--------|--------|-------|
| A1 | None | 0.889 | 0.867 | 8 |
| B2 | Open web | **0.929** | **0.867** | 9 |
| **C1** | **Serebii only** | **0.929** | **0.867** | **7** |

**Interpretation.** Restricting internet access to a single domain-specific Pokemon resource (Serebii) versus the open web produced zero performance difference at the Sonnet tier. The key own_faint rule, which B2 found via Showdown SIM-PROTOCOL docs, is also confirmable from Serebii's general fainting/switching mechanics. **Domain restriction does not impair rule discovery when the restricted source covers the relevant mechanics.**

This adds a new dimension to the internet substitution finding: not only does frontier capability substitute for internet access (B1 vs A3), but **domain-restricted internet substitutes for open-web internet** when the restricted source is appropriately comprehensive.

## Internet Research Conducted (3 Serebii-only searches)

1. **Faint permanence** (`serebii.net`) → Confirms fainted Pokemon cannot return to battle or restore HP without Revival items. Validates rules 1, 2, 4.
2. **PP monotonicity** (`serebii.net`) → Confirms PP strictly decreases within a battle; PP Up items only work outside battle; Pressure doubles PP loss but never reverses it. Validates rule 3.
3. **Faint + forced switch** (`serebii.net`) → Running & Switching page confirms that fainting triggers a forced switch and permanent removal from the active slot. Validates rule 7 (own_faint without permanent = incoherent). Serebii lacked explicit SIM-PROTOCOL documentation, but the mechanical implication is identical.

All three searches confirmed existing rules. No new patterns surfaced.

## Detected Violation Categories (7 rules)

1. hp_resurrection (0→positive)
2. hp_resurrection (post-permanent positive HP)
3. monotone_increase (decay=monotone_decrease / pp_action_* / match_time_remaining)
4. causal: permanent unit revived (later AVAILABLE)
5. causal: permanent unit re-unavailable (later non-permanent UNAVAILABLE)
6. causal: same-turn UNAVAIL→AVAIL (turn-gated)
7. causal: own_faint with zero permanents in chain

## Validation False Negatives — Format-Limited (4 chains)

Same 4 irreducible format failures as all other agents:
1. `gen9ou-2275367426` — hp_resurrection outside 15-step window
2. `gen9ou-2283533709` — requires active_pair annotation (absent)
3. `gen9ou-2334711641` — requires phase-coherence tracking (absent)
4. `gen9ou-2306563046` — double non-permanent UNAVAILABLE pattern present in valid chains too (non-separable)

## Conclusion

- **Serebii-only is sufficient for this domain.** A single authoritative Pokemon resource covers the mechanics needed to build a precision-1.0 checker at the Sonnet tier.
- **Domain-restricted internet = open-web internet** for this task. The constraint B2 found via Showdown docs is recoverable from Serebii's mechanics pages alone.
- **The validation ceiling (0.867) is format-imposed.** No amount of internet access — whether open-web or domain-restricted — can overcome the 15-step window and missing annotation limitations.
