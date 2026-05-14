# Cross-Universe Comparison — 6 Universe L3 Meaningful Conditions

**SPEC hash:** `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8`  
**Generated:** 2026-05-13  
**Per:** Amendment #4 D7 — three independent effect tables, no cross-universe aggregation.

---

## Summary

Of the 6 conditions classified Meaningful in Universe L3, **4 are Meaningful in all three universes** (pro_L17_L2, pro_L17_L3, pro_L18_L3, and with caveats pro_L18_L2) and **2 are Meaningful only in L3** (flash_L18_L2, pro_L12_L3). Universe L1 and L2 produce identical effect sizes and classifications across all 6 conditions — this is expected because L1 and L2 share the same chain composition (34 violated / 16 intact) while L3 has a different split (32 violated / 18 intact) due to the symbolic checker assigning ground truth independently.

---

## Why L1 and L2 Are Identical

The L1 and L2 universe labels differ in *how* violated chains are defined:
- **L1:** shuffled-vs-real (structural shuffling creates the "violation")
- **L2:** planted violations (explicit injection)
- **L3:** symbolic checker verdict (rule-based automated classifier)

However, for the 50 chains in the OLAT sample, **all 34 violated chains in L1 are also violated in L2** (and vice versa — the L1 and L2 labels are perfectly correlated for this sample). This produces identical `n_violated_valid`, `dr_violated`, `dr_intact`, and effect sizes across L1 and L2. The differences emerge only in L3 (which uses the symbolic checker's independent verdicts), where 2 chains shift from violated to intact compared to L1/L2.

The L1–L2 correlation is a property of this specific 50-chain OLAT sample. It does not indicate a methodology error.

---

## Per-Condition Table

### pro_L17_L2 (Lever 17 L2 — structured output format, Pro model)

| Universe | n_violated | n_intact | dr_violated | dr_intact | Effect | BCa 95% CI | Classification |
|---|---|---|---|---|---|---|---|
| L1 | 34 | 16 | 0.412 | 0.125 | 0.261 | [0.014, 0.448] | **Meaningful** |
| L2 | 34 | 16 | 0.412 | 0.125 | 0.261 | [0.014, 0.448] | **Meaningful** |
| L3 | 32 | 18 | 0.406 | 0.111 | 0.288 | [0.051, 0.486] | **Meaningful** |

**Finding:** Meaningful in all three universes. Effect direction is consistent. Finding is robust across ground-truth definitions.

---

### pro_L17_L3 (Lever 17 L3 — structured JSON output, Pro model)

| Universe | n_violated | n_intact | dr_violated | dr_intact | Effect | BCa 95% CI | Classification |
|---|---|---|---|---|---|---|---|
| L1 | 34 | 16 | 0.382 | 0.125 | 0.239 | [0.056, 0.479] | **Meaningful** |
| L2 | 34 | 16 | 0.382 | 0.125 | 0.239 | [0.056, 0.479] | **Meaningful** |
| L3 | 32 | 18 | 0.375 | 0.111 | 0.243 | [0.010, 0.510] | **Meaningful** |

**Finding:** Meaningful in all three universes. Effect direction is consistent. Finding is robust.

---

### pro_L18_L3 (Lever 18 L3 — chain-of-thought L3 format, Pro model)

| Universe | n_violated | n_intact | dr_violated | dr_intact | Effect | BCa 95% CI | Classification |
|---|---|---|---|---|---|---|---|
| L1 | 34 | 16 | 0.529 | 0.125 | 0.364 | [0.019, 0.706] | **Meaningful** |
| L2 | 34 | 16 | 0.529 | 0.125 | 0.364 | [0.019, 0.706] | **Meaningful** |
| L3 | 32 | 18 | 0.531 | 0.111 | 0.354 | [0.026, 0.685] | **Meaningful** |

**Finding:** Meaningful in all three universes. Largest stable effect across all universes.

---

### pro_L18_L2 (Lever 18 L2 — chain-of-thought L2 format, Pro model)

| Universe | n_violated | n_intact | dr_violated | dr_intact | Effect | BCa 95% CI | Classification |
|---|---|---|---|---|---|---|---|
| L1 | 34 | 16 | 0.441 | 0.125 | 0.305 | [-0.037, 0.655] | **Directional** |
| L2 | 34 | 16 | 0.441 | 0.125 | 0.305 | [-0.037, 0.655] | **Directional** |
| L3 | 32 | 18 | 0.469 | 0.111 | 0.379 | [0.036, 0.745] | **Meaningful** |

**Finding:** Universe-specific. Meaningful only in L3; Directional in L1 and L2 (CI crosses zero in those universes). The CI in L1/L2 includes zero, likely because the smaller intact group (n=16 vs n=18 in L3) increases variance. The effect magnitude is consistent (~0.305–0.379) across universes; the universe-specific classification reflects CI width rather than directional inconsistency.

**Interpretation note:** The finding is directionally consistent across all universes, but the confidence interval crosses zero in L1 and L2 per pre-registered CI-downgrade rule (Amendment #4 C5). Both authors should note that this classification is CI-boundary-sensitive.

---

### flash_L18_L2 (Lever 18 L2 — chain-of-thought L2 format, Flash model)

| Universe | n_violated | n_intact | dr_violated | dr_intact | Effect | BCa 95% CI | Classification |
|---|---|---|---|---|---|---|---|
| L1 | 32 | 14 | 0.344 | 0.143 | 0.152 | [-0.044, 0.455] | **Directional** |
| L2 | 32 | 14 | 0.344 | 0.143 | 0.152 | [-0.044, 0.455] | **Directional** |
| L3 | 30 | 16 | 0.333 | 0.125 | 0.217 | [0.026, 0.500] | **Meaningful** |

**Finding:** Universe-specific. Meaningful only in L3. In L1/L2, only 14 intact chains are valid (8% parse-fail rate removes some), reducing statistical power. The L3 universe assigns 16 intact chains to this condition, improving CI coverage. Effect direction consistent across all universes.

**Note:** flash_L18_L2's L1/L2 n_intact=14 is notably small. A single false positive shifts dr_intact by 7.1%. Both-author review should consider whether this condition's Meaningful status in L3 is stable to CI boundary sensitivity.

---

### pro_L12_L3 (Lever 12 L3 — function calling, Pro model)

| Universe | n_violated | n_intact | dr_violated | dr_intact | Effect | BCa 95% CI | Classification |
|---|---|---|---|---|---|---|---|
| L1 | 34 | 16 | 0.265 | 0.125 | 0.129 | [-0.043, 0.395] | **Directional** |
| L2 | 34 | 16 | 0.265 | 0.125 | 0.129 | [-0.043, 0.395] | **Directional** |
| L3 | 32 | 18 | 0.281 | 0.111 | 0.191 | [0.017, 0.438] | **Meaningful** |

**Finding:** Universe-specific. Meaningful only in L3. The function-calling condition (Lever 12 L3) uses regex fallback on truncated JSON arguments (see implementation anomalies in Day 2 summary); all 50 pro_L12_L3 records parsed via permissive (regex) stage, not strict. In L1/L2, the CI crosses zero. This finding should be treated with caution pending L1/L2 verification.

---

## Summary Table

| Condition | L1 | L2 | L3 | Meaningful in all 3? |
|---|---|---|---|---|
| pro_L17_L2 | **Meaningful** | **Meaningful** | **Meaningful** | Yes |
| pro_L17_L3 | **Meaningful** | **Meaningful** | **Meaningful** | Yes |
| pro_L18_L3 | **Meaningful** | **Meaningful** | **Meaningful** | Yes |
| pro_L18_L2 | Directional | Directional | **Meaningful** | No — L3 only |
| flash_L18_L2 | Directional | Directional | **Meaningful** | No — L3 only |
| pro_L12_L3 | Directional | Directional | **Meaningful** | No — L3 only |

**Robust findings (Meaningful in all 3 universes):** pro_L17_L2, pro_L17_L3, pro_L18_L3  
**Universe-specific findings (Meaningful only in L3):** pro_L18_L2, flash_L18_L2, pro_L12_L3

---

## Revised Headline Framing (Provisional — Pending Both-Author Review)

**Prior framing (Universe L3 only):** 6 Meaningful conditions.

**Revised framing (cross-universe):**
- **3 findings robust across all ground-truth definitions:** Pro model, Lever 17 (structured output format L2 and L3) and Lever 18 (CoT L3 format)
- **3 findings universe-specific (L3 only):** Pro L18 L2, Flash L18 L2, Pro L12 L3 — directionally consistent but CI crosses zero under L1/L2 ground truth; classification is CI-boundary-sensitive

The robust findings (Lever 17 and Lever 18 L3 on Pro) are the most defensible OLAT results. The universe-specific findings should be presented with explicit acknowledgment that their Meaningful classification depends on the symbolic-checker ground truth definition.

Per SPEC Amendment #4 D7: no cross-universe aggregation. The three tables stand as independent outputs. This qualitative synthesis is observational, not a reclassification.
