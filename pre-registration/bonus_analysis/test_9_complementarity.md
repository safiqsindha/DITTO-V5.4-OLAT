# Test 9: LLM-Checker Complementarity

**Status:** Complete  
**Priority:** 1  
**Computed:** 2026-05-14

---

## Setup

- **Symbolic checker verdict:** L3_symbolic_checker ground truth (True = violated)
- **Reference ground truth:** L1_shuffled_vs_real (True = shuffled/violated)
- **LLM verdict:** parsed_label (YES = violated, NO = intact)
- **Correct:** LLM verdict matches L1 ground truth

Analysis covers 50 OLAT chains × 64 conditions = 3,200 records. Records with parse_success=False are excluded from analysis.

---

## Symbolic Checker Accuracy

The symbolic checker (L3) agrees with the L1 ground truth on **48/50 chains (96%)**.

**Two chains where checker is wrong (L3 ≠ L1):**

| Chain | L1 | L3 | violation_type | LLM L1 DR |
|---|---|---|---|---|
| gen9ou-2286522581_p1_shuffled_1337 | True | False | none | 0.136 |
| gen9ou-2301379516_p1_shuffled_42 | True | False | none | 0.230 |

Both anomalies: chains with `_shuffled_` suffix (making L1=True by construction) but `violation_type='none'` and `L3_symbolic_checker=False`. These are chains that were shuffled at the step level but where the symbolic constraint checker found no violations in the shuffled sequence — the shuffle happened to not introduce detectable constraint violations per the checker's rules. Note that L2 (planted_violations) = True for both, confirming L1 is correct.

---

## Four-Way Agreement: Overall

Total evaluated: **3,016 chain-condition pairs** (3,200 - parse failures from L18_L4 conditions)

| Outcome | Count | Percentage |
|---|---|---|
| Both correct | 1,162 | 38.5% |
| LLM only correct | 22 | 0.7% |
| Checker only correct | 1,734 | 57.5% |
| Both wrong | 98 | 3.2% |

**Key finding:** The checker dominates. In 57.5% of cases, only the symbolic checker is correct — the LLM fails and the checker succeeds. In 38.5% of cases, both succeed (primarily intact chains where both agree on "no violation"). In only 0.7% of cases is the LLM correct when the checker is wrong.

---

## Complementarity Measures

**P(LLM correct | checker wrong):** How often does the LLM succeed when the checker fails?  
**P(checker correct | LLM wrong):** How often does the checker succeed when the LLM fails?

| Scope | P(LLM | chk_wrong) | P(chk | LLM_wrong) | chk_wrong N | LLM_wrong N |
|---|---|---|---|---|---|
| All conditions | 0.183 | 0.947 | 120 | 1,832 |
| Flash conditions | 0.115 | 0.944 | 60 | 912 |
| Pro conditions | 0.254 | 0.950 | 60 | 920 |

Interpretation: The relationship is highly asymmetric. When the LLM fails (1,832 instances), the checker is correct 94.7% of the time — the checker reliably covers LLM failures. When the checker fails (only 120 instances — because it's wrong on 2 chains × 64 conditions = 128 max), the LLM succeeds only 18.3% of the time. **The checker is a better fallback for LLM errors than the LLM is for checker errors.**

The 120 "checker wrong" instances correspond to the 2 anomalous chains × ~60 conditions each.

---

## Complementarity by Violation Type

| Violation Type | Both% | LLM only% | Chk only% | Both wrong% | P(LLM|chk_wrong) | P(chk|LLM_wrong) |
|---|---|---|---|---|---|---|
| causal_incoherence | 15.3% | 0.0% | 84.7% | 0.0% | 0.000 | 1.000 |
| hp_resurrection | 17.9% | 0.0% | 82.1% | 0.0% | 0.000 | 1.000 |
| monotone_increase | 18.0% | 0.0% | 82.0% | 0.0% | 0.000 | 1.000 |
| multiple | 18.8% | 0.0% | 81.2% | 0.0% | 0.000 | 1.000 |
| none (intact) | 74.5% | 2.0% | 14.5% | 9.0% | 0.183 | 0.616 |

For violated violation types (causal_incoherence, hp_resurrection, monotone_increase, multiple): the symbolic checker is **perfectly correct** (L3=True matches L1=True), while the LLM is correct only ~16–19% of the time. P(LLM|chk_wrong) = 0.000 for all violated types — the checker never fails on violated chains in this dataset.

For intact chains: the checker is correct (L3=False = L1=False) but occasionally the LLM says YES (false positive / confabulation — 9.0% both-wrong rate). Here P(chk|LLM_wrong) = 0.616, meaning when the LLM confabulates on an intact chain, the checker is only right 61.6% of the time (because some intact chains with LLM=YES correspond to the 2 anomalous chains where L3=False incorrectly).

---

## Complementarity by Chain Difficulty

Chains sorted by LLM detection rate (vs L1), then split into quartiles:

| Quartile | DR range | Both% | LLM only% | Chk only% | Both wrong% | P(LLM|chk_wrong) |
|---|---|---|---|---|---|---|
| Q1 (easy, high DR) | 0.77–0.92 | 85.2% | 0.0% | 14.8% | 0.0% | 0.000 |
| Q4 (hard, low DR) | 0.08–0.15 | 12.2% | 1.1% | 79.6% | 7.1% | 0.136 |

Easy chains: mostly intact chains where both succeed. Hard chains: LLM fails 87.8% of the time; checker covers ~80% of total cases. The "both wrong" rate rises to 7.1% for hard chains — these are primarily the 2 anomalous checker-wrong chains.

---

## Meaningful Conditions vs All Conditions

Meaningful conditions: `pro_L18_L2`, `pro_L18_L3`, `pro_L17_L2`, `pro_L17_L3`, `flash_L18_L2`, `pro_L12_L3`

| Scope | P(LLM | chk_wrong) | P(chk | LLM_wrong) |
|---|---|---|
| Meaningful (6 conds) | **0.667** | 0.963 |
| Non-meaningful (58 conds) | 0.130 | 0.945 |

Under meaningful conditions, P(LLM|chk_wrong) rises to 0.667 — the LLM is substantially more likely to correctly identify the 2 anomalous checker-wrong chains under these conditions. This is because the 6 meaningful conditions are the highest-performing conditions overall, and for the 2 anomalous chains (L1=True, L3=False), the LLM is more likely to say YES under good conditions.

---

## L18 L3 vs L18 L4 Complementarity

| Condition | P(LLM | chk_wrong) | P(chk | LLM_wrong) | LLM_wrong N |
|---|---|---|---|---|
| L18 L3 (flash_L18_L3, pro_L18_L3) | 1.000 | 1.000 | 31 |
| L18 L4 (flash_L18_L4, pro_L18_L4) | 0.000 | 0.000 | 0 |

**L18_L4 result (0.000 for both):** The L18_L4 condition has no parseable records in the main `parser_provenance.ndjson` — it returns NaN. The amendment_7 records use L1 ground truth for scoring and have different chain coverage. With 0 LLM-wrong instances in the L1 framework for L18_L4, the complementarity measure is undefined.

**L18_L3 result (1.000 / 1.000):** Under L18_L3 conditions, P(LLM|chk_wrong)=1.0 because for the 2 anomalous checker-wrong chains, the LLM correctly says YES (both chains are violated per L1). P(chk|LLM_wrong)=1.0 because whenever L18_L3 LLM is wrong, the checker is correct (those are violated chains the LLM misses).

---

## Per-Condition Four-Way Breakdown (Selected Conditions)

| Condition | Both% | LLM only% | Chk only% | Both wrong% | N |
|---|---|---|---|---|---|
| flash_baseline | 32.0% | 0.0% | 64.0% | 4.0% | 50 |
| pro_baseline | 32.0% | 2.0% | 64.0% | 2.0% | 50 |
| flash_L18_L3 | 62.5% | 4.2% | 33.3% | 0.0% | 48 |
| pro_L18_L3 | 66.0% | 4.0% | 30.0% | 0.0% | 50 |
| flash_L18_L2 | 69.6% | 2.2% | 26.1% | 2.2% | 46 |
| pro_L18_L2 | 64.0% | 2.0% | 32.0% | 2.0% | 50 |
| flash_L12_L3 | 64.0% | 4.0% | 32.0% | 0.0% | 50 |
| pro_L12_L3 | 68.0% | 4.0% | 28.0% | 0.0% | 50 |
| pro_L17_L2 | 52.0% | 2.0% | 44.0% | 2.0% | 50 |
| pro_L17_L3 | 46.0% | 2.0% | 50.0% | 2.0% | 50 |

At baseline conditions (32% both correct), 64% of cases are checker-only — the LLM is consistently wrong while the checker is right. The best conditions (`flash_L18_L2`, `pro_L12_L3`) bring "both correct" to ~64–70% by improving LLM performance, while "checker only" drops to 26–32%.

---

## Summary

1. **Massive asymmetry:** The symbolic checker covers LLM failures 94.7% of the time; the LLM covers checker failures only 18.3% of the time. These are not complementary peers — the checker is the dominant accurate signal.

2. **Near-zero LLM complementarity for violated chains:** For all violated violation types, P(LLM|chk_wrong) = 0.000 — the checker is never wrong on violated chains (in this 50-chain subset), so the LLM never gets to demonstrate its value on checker failures.

3. **Meaningful conditions improve LLM's share:** Under the 6 meaningful conditions, P(LLM|chk_wrong) rises to 0.667, reflecting higher overall LLM performance that catches more of the 2 anomalous chains.

4. **L18_L4 comparison was methodologically blocked:** No parseable L18_L4 records exist in the main provenance file; the amendment_7 records have different scoring. The comparison is not directly computable from available data.

5. **Architectural implication:** An ensemble that uses symbolic checker as primary detector and LLM only as a secondary check on checker-negative outcomes (where false negatives are known) would capture substantially more violations than either alone — but the LLM would need to be under high-performance conditions (e.g., L18_L2 or L18_L3) to provide meaningful additional coverage.
