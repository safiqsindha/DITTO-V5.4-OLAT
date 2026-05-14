# Test 8: Symbolic Checker Characterization (Partial)

**Status:** Partial — 50 OLAT chains only  
**Priority:** 2  
**Computed:** 2026-05-14

---

## Data Limitation Notice

**`phase3_results_v4.csv` (19,428-chain pool) is MISSING from disk.** This test cannot be completed on the full chain pool. The following analysis covers only the 50 OLAT chains used in the main experiment.

The 50-chain analysis is sufficient to characterize checker behavior on the experimental subset, but results cannot be generalized to the full symbolic checker evaluation without the missing file.

---

## Chain Composition

| Ground Truth | True (violated) | False (intact) |
|---|---|---|
| L1 (shuffled_vs_real) | 34 | 16 |
| L2 (planted_violations) | 34 | 16 |
| L3 (symbolic_checker) | 32 | 18 |

Note: L2 agrees perfectly with L1 for all 50 chains. L3 disagrees with L1 on 2 chains.

---

## Symbolic Checker Performance (vs L1 ground truth)

Treating L1 as the reference "true" ground truth and L3 as the checker's classification:

| Metric | Value |
|---|---|
| Accuracy | 0.960 (48/50) |
| Recall (TPR) | 0.941 (32/34) |
| Precision | 1.000 (32/32) |
| False Positive Rate | 0.000 (0/16) |

**Confusion matrix (L1 as truth, L3 as predicted):**

|  | L3=True | L3=False |
|---|---|---|
| L1=True (violated) | 32 (TP) | 2 (FN) |
| L1=False (intact) | 0 (FP) | 16 (TN) |

Key findings:
- **Perfect precision:** The checker never flags an intact chain as violated (zero false positives)
- **High recall:** The checker correctly identifies 32/34 violated chains (94.1%)
- **Two misses (FN):** Two chains are flagged violated by L1 but pass the checker

---

## Per Violation-Type Recall

| Violation Type | L1=True chains | L3=True (correct) | Recall |
|---|---|---|---|
| causal_incoherence | 3 | 3 | 1.000 |
| hp_resurrection | 4 | 4 | 1.000 |
| monotone_increase | 2 | 2 | 1.000 |
| multiple | 23 | 23 | 1.000 |
| none (anomalous) | 2 | 0 | 0.000 |

The checker achieves 100% recall on all violated violation types (causal_incoherence, hp_resurrection, monotone_increase, multiple). The two misses are in the **'none' anomaly category** — chains where `violation_type='none'` but `L1_shuffled_vs_real=True`.

---

## The Two Anomalous Chains

| Chain | violation_type | L1 | L2 | L3 | Notes |
|---|---|---|---|---|---|
| gen9ou-2286522581_p1_shuffled_1337 | none | True | True | **False** | Shuffled, but no constraint violation detectable |
| gen9ou-2301379516_p1_shuffled_42 | none | True | True | **False** | Shuffled, but no constraint violation detectable |

Both chains:
- Have `_shuffled_` in their ID (confirming shuffling occurred at step level → L1=True)
- Have `violation_type='none'` — the shuffling did not introduce a recognized violation type
- Have `L2_planted_violations=True` (experimental manipulation present)
- Have `L3_symbolic_checker=False` — the symbolic checker found no constraint violations

**Interpretation:** These are chains where step-level shuffling occurred but the resulting sequence happened to not violate any of the symbolic checker's rules. The checker is technically correct in its own logic (no detected constraint violation) but "wrong" relative to L1's ground truth (the sequence is shuffled, not real). This is a definitional boundary case, not a checker error — the L3 ground truth reflects a stricter definition of violation.

These two chains also have low LLM detection rates (0.136 and 0.230 vs L1), consistent with being genuinely hard to classify.

---

## L2 vs L1 Agreement

L2 agrees perfectly with L1 for all 50 chains (50/50 = 100%). This is expected — L2 (planted_violations) is essentially another label for the shuffled chains.

---

## Anomalous Ground Truth Combinations

| Chain | L1 | L2 | L3 | violation_type |
|---|---|---|---|---|
| gen9ou-2286522581_p1_shuffled_1337 | True | True | **False** | none |
| gen9ou-2301379516_p1_shuffled_42 | True | True | **False** | none |

Only these 2 chains have mismatched ground truths. All other 48 chains have L1=L2=L3.

---

## Implications for LLM-Checker Complementarity

Given the checker's near-perfect performance on this dataset (96% accuracy, 0% FPR):

- The checker outperforms the LLM substantially on violated chains (94.1% recall vs ~18% for both LLM models)
- The only cases where the checker fails are definitional boundary cases (shuffled-but-no-constraint-violation), not mechanical failures of the constraint logic
- For an ensemble detector, the checker should be the primary signal; the LLM adds value only on the rare boundary cases

---

## Summary

On the 50 OLAT chains:
- Symbolic checker recall: **0.941** (detects 94% of L1-violated chains)
- Symbolic checker FPR: **0.000** (zero false alarms on intact chains)  
- Symbolic checker accuracy: **0.960**
- The 2 missed chains are definitional anomalies, not checker failures

**The phase3_results_v4.csv (19,428-chain pool) is MISSING — this analysis cannot be extended to the full pool.** The statistics above are valid only for the 50 OLAT experimental chains and should not be extrapolated without additional data.
