# B1.7 — Surface Robustness (Variants 0, 1, 3)

Compares V0 (control), V1 (light paraphrase), V3 (formatting perturbation).

Same semantics — effects should persist if regime effects are robust.


## Regime: v1_minimal

| Variant | N | dr_intact | dr_violated | gap |
|---|---|---|---|---|
| V0 | 2 | 1.0 | None | None |
| V1 | 2 | 1.0 | None | None |
| V3 | 1 | 0.0 | None | None |

## Regime: l18_l4

| Variant | N | dr_intact | dr_violated | gap |
|---|---|---|---|---|
| V0 | 5 | None | 1.0 | None |
| V1 | 7 | 1.0 | 1.0 | 0.0 |
| V3 | 10 | 0.75 | 1.0 | 0.25 |

**Fragile** — gap range 0.250 ≥ 0.10 across V0/V1/V3
