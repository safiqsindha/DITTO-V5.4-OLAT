# Agent B1 — Opus 4.7 (Max Effort), Internet Access

## Configuration
- **Model:** Claude Opus 4.7 (claude-opus-4-7), maximum thinking budget
- **Internet access:** Yes (3 targeted searches; see `search_log.jsonl`)
- **Cycles used:** 1 (single-pass construction + internet confirmation pass)
- **Chain data source:** 50 unique chains from `pre-registration/chain_variants/`

## Final Performance

| Set | n | TP | TN | FP | FN | Precision | Recall | F1 |
|-----|---|----|----|----|----|-----------|--------|-----|
| Development | 30 | 13 | 15 | 0 | 2 | 1.000 | 0.867 | **0.929** |
| Validation | 20 | 13 | 3 | 0 | 4 | 1.000 | 0.765 | 0.867 |

**Outcome vs. pre-specified criteria:** Strong success on development, moderate-to-strong on validation. Identical to A3 (Opus, no internet) on every metric, every set, every chain.

## Headline Finding: Internet contributes ZERO at the Opus tier

B1 (Opus + internet) is **byte-for-byte identical in behavior to A3 (Opus, no internet)**:

| | A3 (no internet) | B1 (+ internet) | Delta |
|--|------------------|-----------------|-------|
| Rules | 7 | 7 | **0** |
| Dev F1 | 0.929 | 0.929 | **0.000** |
| Val F1 | 0.867 | 0.867 | **0.000** |
| Dev FP | 0 | 0 | 0 |
| Per-chain predictions | — | identical | — |

Three targeted web searches (Bulbapedia fainting mechanics, Pokémon Showdown SIM-PROTOCOL, Smogon PP/healing rules) **confirmed every rule** Opus had already derived from the 30 development chains — and surfaced **no new violation pattern**.

## The Key Comparison: Internet Value Collapses With Capability

| Tier | Agent (no net) → Agent (+ net) | Δ Rules | Δ Dev F1 | Internet's marginal value |
|------|-------------------------------|---------|----------|---------------------------|
| Sonnet | A1 → B2 | +1 (own_faint) | **+0.040** | Real but marginal |
| Opus 4.7 | A3 → B1 | **0** | **0.000** | **None** |

**Interpretation.** At the Sonnet tier, internet research supplied one rule (own_faint consistency) that Sonnet did not derive unaided — worth +0.040 development F1 (B2 finding). At the Opus tier, max-effort reasoning *already derived that exact rule from the data* (A3), so internet's marginal contribution drops to exactly zero. Internet access and model capability are **substitutes, not complements**, for this task: the stronger the model, the less internet adds. Frontier reasoning subsumes the knowledge a weaker model must look up.

## Internet Research Conducted (3 searches)

1. **Faint permanence** → "a fainted Pokémon cannot return to battle or restore HP during the battle." Confirms rules 1, 2, 4, 5.
2. **PP monotonicity & HP healing** → "during a single battle, PP can only decrease"; HP *can* increase from non-zero via Recover/Roost. Confirms rule 3; confirms the 0→positive scoping of rule 1 is necessary (a generic "any HP increase" rule would false-positive on healing).
3. **Forced switch / recall** → "any Pokémon that faints must also be recalled." Confirms rule 7 (own_faint with no permanent = incoherent).

All three confirmed existing rules. None produced a rule change or addition. Notably, search #2 confirmed the *same* false-positive-prevention insight (HP-up-from-nonzero is legal) that B2 credited internet for at the Sonnet tier — but A3 had already encoded the correct scoping without it.

## Detected Violation Categories (7 rules — identical to A3)

1. hp_resurrection (0→positive)
2. hp_resurrection (post-permanent positive HP)
3. monotone_increase (decay=monotone_decrease / pp_action_* / match_time_remaining)
4. causal: permanent unit revived (later AVAILABLE)
5. causal: permanent unit re-unavailable (later non-permanent UNAVAILABLE, same-unit scoped)
6. causal: same-turn UNAVAIL→AVAIL
7. causal: own_faint with zero permanents in chain (global form)

## Validation False Negatives — Irreducible, Internet Cannot Help (4 chains)

Internet research specifically investigated whether external knowledge could recover any of the 4 validation FNs. It cannot — all four are **chain-format limitations, not knowledge gaps**:

1. `gen9ou-2275367426` (hp_resurrection): shuffle places the 0%→positive evidence such that no forward 0→positive transition is observable in text order.
2. `gen9ou-2283533709` (multiple): violation requires active_pair / phase-coherence tracking; that annotation is absent.
3. `gen9ou-2334711641` (causal_incoherence): phase references `vs_unit_A` after unit_A went UNAVAILABLE — requires active_pair data not present.
4. `gen9ou-2306563046` (multiple): double non-permanent UNAVAILABLE without intervening AVAILABLE — but **validation intact chain `gen9ou-2327278602` (NO) exhibits the same pattern** (unit_A UNAVAILABLE at steps 7 and 13, no AVAILABLE between), so any rule catching #4 would false-positive on a valid chain. Genuinely non-separable from this text format.

This reproduces the B2 conclusion ("three irreducible failure modes, unchanged by internet access") and confirms it holds at the Opus tier: the 0.867 validation ceiling is imposed by the 15-step text format, not by model capability or internet access.

## Conclusion for the Mew LLM-as-checker-builder workflow

- **Frontier model, no internet, is sufficient.** Opus 4.7 unaided reaches the same checker quality (dev F1 0.929) that Sonnet reached only *with* internet, and matches Opus-with-internet exactly.
- **Internet is a capability crutch, not a capability multiplier.** Its value is inversely proportional to model strength; at the frontier it is zero for this domain.
- **The 0.867 validation ceiling is a data-format problem.** Closing it requires richer chains (wider window, `active_pair` annotation), not better models or web access.
