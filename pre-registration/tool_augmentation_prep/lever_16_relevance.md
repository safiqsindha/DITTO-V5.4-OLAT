# Task 2D — Lever 16 Relevance to Tool Augmentation Hypothesis

**Data source:** `day_2/effect_table_universe_L{1,2,3}.csv`
**Generated:** 2026-05-14

## Background

Lever 16 provides constraint context — the model receives rule descriptions (L2: natural-language; L3: predicate form) alongside the chain. This is structurally analogous to tool augmentation but provides only the *rules*, not per-chain analysis. Tool augmentation would additionally provide the symbolic checker's verdict on *this specific chain*.

If Lever 16 produces measurable improvement → providing rule context helps the model. Tool augmentation (rules + per-chain verdict) should help at least as much.

If Lever 16 produces null/degenerate effect → rules alone are insufficient. The model needs per-chain analysis. This supports the tool augmentation hypothesis that the *checker verdict* (not just the *rules*) is the key missing information.

## Effect Tables (Universe L1, L2, L3)

### Universe L1

| Condition | n_valid | dr_violated | dr_intact | gap | effect_size | classification |
|---|---|---|---|---|---|---|
| flash_baseline | 50 | 0.0 | 0.0 | 0.0 | 0.0 | Null |
| flash_L16_L2 | 50 | 0.0 | 0.0 | 0.0 | 0.0 | Null |
| flash_L16_L3 | 50 | 0.0 | 0.0 | 0.0 | 0.0 | Null |
| pro_baseline | 50 | 0.0588 | 0.0625 | -0.0037 | 0.0 | Null |
| pro_L16_L2 | 46 | 0.0 | 0.0 | 0.0 | 0.0037 | Null |
| pro_L16_L3 | 44 | 0.0 | 0.0 | 0.0 | 0.0037 | Null |

### Universe L2

| Condition | n_valid | dr_violated | dr_intact | gap | effect_size | classification |
|---|---|---|---|---|---|---|
| flash_baseline | 50 | 0.0 | 0.0 | 0.0 | 0.0 | Null |
| flash_L16_L2 | 50 | 0.0 | 0.0 | 0.0 | 0.0 | Null |
| flash_L16_L3 | 50 | 0.0 | 0.0 | 0.0 | 0.0 | Null |
| pro_baseline | 50 | 0.0588 | 0.0625 | -0.0037 | 0.0 | Null |
| pro_L16_L2 | 46 | 0.0 | 0.0 | 0.0 | 0.0037 | Null |
| pro_L16_L3 | 44 | 0.0 | 0.0 | 0.0 | 0.0037 | Null |

### Universe L3

| Condition | n_valid | dr_violated | dr_intact | gap | effect_size | classification |
|---|---|---|---|---|---|---|
| flash_baseline | 50 | 0.0 | 0.0 | 0.0 | 0.0 | Null |
| flash_L16_L2 | 50 | 0.0 | 0.0 | 0.0 | 0.0 | Null |
| flash_L16_L3 | 50 | 0.0 | 0.0 | 0.0 | 0.0 | Null |
| pro_baseline | 50 | 0.0312 | 0.1111 | -0.0799 | 0.0 | Null |
| pro_L16_L2 | 46 | 0.0 | 0.0 | 0.0 | 0.0799 | Directional(no_CI) |
| pro_L16_L3 | 44 | 0.0 | 0.0 | 0.0 | 0.0799 | Directional(no_CI) |

## Key Observations

### V4-Flash Lever 16

- flash_baseline (Universe L3): dr_violated=0.0, dr_intact=0.0, gap=0.0
- flash_L16_L2 (Universe L3): dr_violated=0.0, dr_intact=0.0, gap=0.0
- flash_L16_L3 (Universe L3): dr_violated=0.0, dr_intact=0.0, gap=0.0

All three Flash conditions are **fully degenerate (dr=0.0 for all chains)**. V4-Flash under V1-minimal framing produces a 100% NO floor regardless of whether constraint text is provided. Lever 16 has no measurable effect on Flash because Flash is already at the NO floor; there is nothing for Lever 16 to improve.

### V4-Pro Lever 16

- pro_baseline (Universe L3): dr_violated=0.0312, dr_intact=0.1111, gap=-0.0799, effect=0.0, class=Null
- pro_L16_L2 (Universe L3): dr_violated=0.0, dr_intact=0.0, gap=0.0, n_valid=46, class=Directional(no_CI)
- pro_L16_L3 (Universe L3): dr_violated=0.0, dr_intact=0.0, gap=0.0, n_valid=44, class=Directional(no_CI)

V4-Pro Lever 16 conditions are also **effectively degenerate**: dr_violated=0.0 and dr_intact=0.0 for L16_L2 and L16_L3, both classified as Directional(no_CI) with near-zero effects. These are four of the documented degenerate Pro conditions from Day 2. Adding NL or predicate-form constraint text does not lift Pro from the near-NO floor.

Note: n_valid is 46 (L16_L2) and 44 (L16_L3) vs 50 for baseline, indicating 4–6 parse failures introduced by the longer prompts. This is a minor robustness cost with no benefit.

## Implication for Tool Augmentation

Lever 16 provides the model with the constraint *rules* but not the per-chain *verdict*. Both Flash and Pro show null effect from Lever 16:

- Flash: degenerate at 0.0 both before and after adding rules
- Pro: near-zero both before and after adding rules

**Conclusion:** Rule descriptions alone do not help the model detect violations in V1-minimal framing. The model knows (or can be told) the rules but cannot apply them reliably to individual chains.

This **supports** the tool augmentation hypothesis: what the model lacks is not rule knowledge but per-chain analysis. The symbolic checker provides exactly that — a chain-specific verdict with the violated rule identified. Tool augmentation injects the missing component (chain analysis) that Lever 16 cannot provide.

**Caveat:** Lever 16 uses the same V1-minimal framing (no CoT) as the baseline. Tool augmentation will be tested under the same framing. If the model still cannot integrate checker output in V1-minimal mode, tool augmentation may need to be paired with a CoT-enabling condition (e.g., combined with L18 L3 or L18 L4) to be effective.

**Stop condition check:** The Lever 16 findings match the Day 2 documented classification of these conditions as degenerate. No inconsistency detected; stop condition not triggered.
