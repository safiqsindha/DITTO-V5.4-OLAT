# B1 — Tool Augmentation Summary

## Phase B1.A — Standard Tool Augmentation

| Group | N | Detection Rate |
|---|---|---|
| All intact (GT_L3=False) | 18 | 0.0 |
| All violated (GT_L3=True) | 32 | 0.9375 |
| Test-9 FN chains | 2 | 0.0 |

**Gap (violated DR − intact DR):** 0.9375

## Outcome Classification

**Outcome 1: Tool augmentation works — gap>0.40, dr_intact<0.30, dr_violated≥0.70**

## Phase B1.B — Adversarial Inversion

- N valid: 17
- Deferred to flipped: 12 (70.6%)
- Overrode flipped: 5 (29.4%)
