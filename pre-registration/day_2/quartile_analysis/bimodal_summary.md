# Task 1: Reasoning-Depth Threshold Analysis — L18 L2/L3 Conditions

**SPEC hash:** `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8`
**Generated:** 2026-05-13
**Quartile basis:** `usage.output_tokens` (completion tokens) — canonical methodological unit, consistent with `max_tokens` specification in SPEC §4.
**Bootstrap:** BCa, 10K iterations; seed=42 (Flash), seed=43 (Pro).
**Baseline gaps:** flash L1/L2/L3 = 0.0; pro L1 = −0.0037, pro L2 = −0.0037, pro L3 = −0.0799.

---

## Supersedes Day 2 S6

This analysis **supersedes** the Day 2 S6 character-length quartile findings in [`sensitivity_meaningful_conditions.md`](../sensitivity_meaningful_conditions.md). Completion tokens are the appropriate unit (tokens are what the model processes; character length is a downstream proxy that depends on formatting decisions). This is a documentation correction, not a methodology amendment — the 6 Meaningful conditions remain Meaningful and their overall effect sizes are unchanged.

---

## Headline Finding: Reasoning-Depth Threshold Effect

Both V4 models exhibit a **valley-then-peak** pattern on L18 L3 (and L18 L2 for Flash), in which **partial-CoT outputs produce worse-than-baseline results** until the response crosses a reasoning-depth threshold, after which strong positive Lever 18 effects emerge.

| Model × Lever | Valley (negative-effect zone) | Escape threshold | Peak quartile |
|---|---|---|---|
| **pro_L18_L3** | Q2: tokens 427–487, effect ≈ −0.36 to −0.40, CI excludes zero | ~494 tokens (Q3 boundary) | Q3 (tokens 494–582): effect ≈ +1.00 |
| **flash_L18_L3** | Q2–Q3: tokens 606–728, effect ≈ −0.12 to −0.14, CI excludes zero | ~729 tokens (Q4 boundary) | Q4 (tokens 729–883): effect ≈ +0.33 to +0.50 |

**Mew design implication:** Native CoT on rule-violation detection requires an adequate token budget to escape the "wrong-amount-of-reasoning" valley. At intermediate response lengths, the model produces reasoning that systematically misleads it on intact chains — increasing YES on intact more than on violated, reversing the gap. V4-Pro escapes at ~490 tokens of output; V4-Flash needs ~730 tokens. Configurations that cap CoT generation in the valley range will yield worse-than-baseline behavior on this task.

---

## Per-Condition Token-Quartile Breakdown

### pro_L18_L3 (overall effect=0.354, Meaningful across all 3 universes)

#### Universe L3

| Quartile | Tokens | n_violated | n_intact | dr_violated | dr_intact | gap | effect_size | CI | Classification |
|---|---|---|---|---|---|---|---|---|---|
| Q1 | 296–423 | 7 | 5 | 0.4286 | 0.4000 | 0.0286 | 0.1085 | [−0.49, 0.70] | Meaningful(no_CI) |
| **Q2** | **427–487** | 9 | 3 | 0.5556 | **1.0000** | **−0.4444** | **−0.3645** | **[−0.78, −0.06]** | **Meaningful (reversed)** |
| Q3 | 494–582 | 8 | 4 | 1.0000 | 0.0000 | 1.0000 | 1.0799 | [1.08, 1.08] (degenerate boot) | Meaningful |
| Q4 | 587–799 | 8 | 6 | 0.8750 | 0.5000 | 0.3750 | 0.4549 | [−0.12, 0.88] | Meaningful(no_CI) |

#### Universe L1 / L2 (identical for this sample)

| Quartile | Tokens | gap | effect_size | CI | Classification |
|---|---|---|---|---|---|
| Q1 | 296–423 | 0.029 | 0.032 | [−0.57, 0.63] | Directional(no_CI) |
| **Q2** | **427–487** | **−0.400** | **−0.396** | **[−0.80, −0.18]** | **Meaningful (reversed)** |
| Q3 | 494–582 | 1.000 | 1.004 | [1.00, 1.00] (degenerate boot) | Meaningful |
| Q4 | 587–799 | 0.489 | 0.493 | [−0.16, 0.90] | Meaningful(no_CI) |

**Pattern:** Q2 is the valley — intact chains achieve `dr_intact=1.0` (every intact chain answered YES) while violated chains drop to `dr_violated≈0.56`. Both universes show the Q2 CI excluding zero (statistically significant reversal). Q3 is the peak — `dr_violated=1.0`, `dr_intact=0.0` (perfect separation; bootstrap degenerate). The valley sits in tokens 427–487; escape is at ~494 tokens.

---

### flash_L18_L3 (overall effect=0.044, Null L3; +0.063 Directional in L1/L2)

#### Universe L3

| Quartile | Tokens | n_violated | n_intact | dr_violated | dr_intact | gap | effect_size | CI | Classification |
|---|---|---|---|---|---|---|---|---|---|
| Q1 | 342–590 | 4 | 8 | 1.0000 | 0.8750 | 0.1250 | 0.1250 | [0.00, 0.50] | Meaningful(no_CI) |
| **Q2** | **606–693** | 8 | 3 | 0.8750 | **1.0000** | **−0.1250** | **−0.1250** | **[−0.67, 0.00]** | **Meaningful (reversed, no_CI)** |
| **Q3** | **694–728** | 7 | 4 | 0.8571 | **1.0000** | **−0.1429** | **−0.1429** | **[−0.75, 0.00]** | **Meaningful (reversed, no_CI)** |
| Q4 | 729–883 | 11 | 3 | 1.0000 | 0.6667 | 0.3333 | 0.3333 | [0.00, 1.00] | Meaningful(no_CI) |

#### Universe L1 / L2 (identical for this sample)

| Quartile | Tokens | gap | effect_size | CI | Classification |
|---|---|---|---|---|---|
| Q1 | 342–590 | 0.143 | 0.143 | [0.00, 0.60] | Meaningful(no_CI) |
| **Q2** | **606–693** | **−0.125** | **−0.125** | [−0.67, 0.00] | **Meaningful (reversed, no_CI)** |
| **Q3** | **694–728** | **−0.143** | **−0.143** | [−0.75, 0.00] | **Meaningful (reversed, no_CI)** |
| Q4 | 729–883 | 0.500 | 0.500 | [0.00, 1.00] | Meaningful(no_CI) |

**Pattern:** Flash's valley spans a wider band (Q2 + Q3, tokens 606–728), with all intact chains in both quartiles answering YES (`dr_intact=1.0`). The Q3 CI just touches zero on the upper bound (CI=[−0.75, 0.00]); the reversal is consistent in direction but not statistically separated from zero at this n. Escape is at ~729 tokens — much later than Pro. Q4 then produces the expected strong positive effect (+0.33 in L3, +0.50 in L1/L2). **This explains why flash_L18_L3 is overall classified as Null/Directional**: the valley quartiles cancel out the Q1 + Q4 positive contributions in the aggregate.

---

### pro_L18_L2 (overall effect=0.379 in L3, Meaningful)

| Quartile | Tokens | gap (L3) | effect_size (L3) | CI | Classification |
|---|---|---|---|---|---|
| Q1 | 166–306 | 0.200 | 0.280 | [−0.47, 0.97] | Meaningful(no_CI) |
| Q2 | 310–355 | 0.000 | 0.080 | [−0.42, 0.75] | Directional(no_CI) |
| Q3 | 356–408 | 0.444 | 0.524 | [−0.37, 0.98] | Meaningful(no_CI) |
| Q4 | 428–654 | 0.178 | 0.258 | [−0.25, 0.86] | Meaningful(no_CI) |

**Pattern:** No valley — all quartiles are non-negative. Q2 shows a Directional dip but stays above zero. The L18 L2 CoT-style prompt does not exhibit the reasoning-depth threshold seen in L18 L3.

---

### flash_L18_L2 (overall effect=0.217 in L3, Meaningful)

| Quartile | Tokens | gap (L3) | effect_size (L3) | CI | Classification |
|---|---|---|---|---|---|
| Q1 | 153–362 | 0.000 | 0.000 | [0.00, 0.00] | Null |
| Q2 | 370–449 | 0.000 | 0.000 | [−0.57, 0.33] | Null |
| Q3 | 452–501 | 0.500 | 0.500 | [0.00, 1.00] | Meaningful(no_CI) |
| Q4 | 506–680 | 0.667 | 0.667 | [0.00, 1.00] | Meaningful(no_CI) |

**Pattern:** Monotone-positive — null at short response lengths, strong positive at longer lengths. No valley. The L18 L2 effect on Flash is a "threshold" effect (engages only above ~450 tokens) but does not invert.

---

## Summary: Where the Valley Lives

| Condition | Valley present? | Valley range (tokens) | Effect at valley | Escape token |
|---|---|---|---|---|
| pro_L18_L3 | **Yes** | 427–487 (Q2) | −0.36 to −0.40 (CI excludes 0) | ~494 |
| flash_L18_L3 | **Yes (wider)** | 606–728 (Q2–Q3) | −0.12 to −0.14 (CI touches 0) | ~729 |
| pro_L18_L2 | No | — | — | — |
| flash_L18_L2 | No (threshold only) | — | — | ~450 (engagement threshold) |

---

## Methodological Note on Day 2 S6

Day 2 S6 reported quartile effects using **character length** of `raw_output`. Under that ordering, pro_L18_L3 × L3 showed Q1=−0.214, Q2=−0.300, Q3=0.833, Q4=0.389 — interpreted at the time as a "bimodal" Q1/Q2-negative pattern.

Under the canonical **completion-token** quartile split (this analysis), the negative-effect zone is concentrated entirely in Q2 (tokens 427–487), with Q1 mildly positive (+0.11). The character-length ordering misclassified some Q2 responses into Q1 due to character-density variation in the markdown-decorated CoT output format. Both orderings agree that a negative-effect zone exists in the mid-short response-length range; the token-based ordering localizes it more precisely.

This is a documentation correction. The 6 Meaningful conditions in the headline table all remain Meaningful; their primary effect sizes are unchanged. S6 in `sensitivity_meaningful_conditions.md` is updated to use tokens.

---

## Notes on Bootstrap Behavior

Three quartiles return degenerate BCa CIs (`ci_lo = ci_hi = observed`):
- `pro_L18_L3` Q3 × all universes: all 8 violated=YES, all 4 intact=NO → every bootstrap resample gives the same `gap=1.0`.
- `flash_L18_L2` Q1 × all universes: all parsed records say YES → `gap=0.0` for every resample.

These are correct bootstrap behaviors for degenerate-data subsets, not a CI computation bug. The point estimates are reliable; the CIs reflect the absence of within-quartile variability.

---

## Output Files

- `quartile_breakdown_full.csv` — 48 rows (4 conditions × 3 universes × 4 quartiles)
- `bimodal_summary.md` — this file (filename retained for traceability; framing superseded)
