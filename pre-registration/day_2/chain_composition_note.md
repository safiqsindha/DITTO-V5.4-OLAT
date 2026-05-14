# Task 3: Chain Composition Note

**SPEC hash:** `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8`  
**Generated:** 2026-05-13

---

## OLAT Sample Composition (n=50, seed=42)

The 50-chain OLAT sample was drawn from the 19,428-chain pool using seed=42 random sampling (Lever 5 L1 procedure, SPEC §17 Step 1). Ground truth labels vary by universe because each universe defines "violation" differently.

| Universe | Definition | Intact | Violated | Note |
|---|---|---|---|---|
| L1 (shuffled-vs-real) | Is chain shuffled? | 16 | 34 | 32/64 split |
| L2 (planted violations) | Does chain contain a planted violation? | 16 | 34 | Identical to L1 for this sample |
| L3 (symbolic checker) | Does checker flag a rule violation? | 18 | 32 | 36/64 split |

**L1 and L2 are identical for this sample.** All 34 chains labeled violated in L1 are also labeled violated in L2 (and vice versa). This is a property of the specific 50-chain draw — L1 and L2 ground truth definitions coincide for this corpus sample.

---

## Day −2 Composition for Reference

Day −2 verification used n=250 chains (seed=42, Lever 5 L1 procedure):

| Universe | Intact | Violated |
|---|---|---|
| Structural (shuffled-vs-real) | 68 | 182 |

Note: Day −2 used only one ground-truth universe (shuffled-vs-real). The 27%/73% intact/violated split in the larger n=250 sample reflects the underlying pool composition (~33% intact in the eligible 6,503 distractor pool).

---

## Was the 18/32 Split Intentional?

The OLAT 18/32 split (L3) and 16/34 split (L1/L2) were **not deliberate stratification** — they emerged from seed=42 random sampling from the 19,428-chain pool.

The pool contains:
- 6,503 intact chains (33.5%)
- 12,925 violated chains (66.5%)

A random n=50 sample from this pool is expected to contain approximately 17 intact and 33 violated chains. The observed 16–18 intact / 32–34 violated range is consistent with this expectation. No stratification rule was applied.

---

## CI Width Implications

With n=18 intact chains (L3 universe), each single YES response shifts `dr_intact` by 1/18 ≈ 5.6%. With n=16 intact chains (L1/L2 universe), each single YES shifts `dr_intact` by 1/16 = 6.25%.

This is why several conditions are Meaningful in L3 but only Directional in L1/L2: the slightly larger intact group in L3 (18 vs 16) provides marginally tighter confidence intervals. This is not an artifact — it correctly reflects the different statistical power available under each universe's ground truth assignment.

The intact-group size is the primary source of CI uncertainty for these conditions. A larger n would help all three universes equally.

---

## Recommendation for Both-Author Review

The 18/32 and 16/34 splits are emergent from random sampling and consistent with the pool's base rate. No documentation amendment is needed. The CI-width sensitivity noted for several Meaningful conditions (flash_L18_L2, pro_L12_L3, pro_L18_L2) is properly attributed to the small intact-group sample size rather than to any procedural anomaly.
