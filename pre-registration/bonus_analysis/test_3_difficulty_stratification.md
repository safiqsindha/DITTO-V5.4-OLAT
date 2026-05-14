# Test 3: Chain Difficulty Stratification

**Status:** Complete  
**Priority:** 1  
**Computed:** 2026-05-14

---

## Setup and Key Finding: Uniform Chain Length

All 50 OLAT chains have **exactly 15 steps** in the baseline condition. Chain length is not a differentiating feature in this dataset — the `chain_length` stratification is degenerate. The L08 lever family varies `k` (number of steps *shown* to the model), not the underlying chain length.

This finding does not invalidate the analysis; it simply means difficulty must be characterized by other dimensions.

---

## Chain Composition

| Category | Count |
|---|---|
| Total chains | 50 |
| Intact (violation_type = 'none') | 18 |
| Violated | 32 |

**Violated chain breakdown by violation_type:**

| Violation Type | Count |
|---|---|
| multiple | 23 |
| hp_resurrection | 4 |
| causal_incoherence | 3 |
| monotone_increase | 2 |

Note: The task specification listed hp_resurrection=8, causal_incoherence=6, monotone_increase=4, multiple=16 — these do not match the data. The actual counts from the 50 OLAT chains are above.

---

## Overall Detection Rates

| Subset | Flash DR | Pro DR |
|---|---|---|
| All 50 chains | 0.399 | 0.437 |
| Intact chains (18) | 0.879 | 0.791 |
| Violated chains (32) | 0.130 | 0.238 |

Interpretation: Both models are substantially better at correctly identifying intact chains than violated chains. Flash performs slightly better on intact chains; Pro performs better on violated chains. The overall gap between intact and violated detection rates is dramatic (>0.55 for both models), indicating the fundamental asymmetry in this task.

---

## Stratification by Violation Type

This is the primary differentiating dimension since chain_length is uniform.

| Violation Type | Flash DR | Pro DR | N (chains) |
|---|---|---|---|
| none (intact) | 0.879 | 0.791 | 18 |
| monotone_increase | 0.164 | 0.196 | 2 |
| hp_resurrection | 0.132 | 0.226 | 4 |
| multiple | 0.130 | 0.248 | 23 |
| causal_incoherence | 0.098 | 0.209 | 3 |

Key findings:
- **Intact chains** are the easiest to handle correctly (models default to "NO violation")
- **Causal_incoherence** is hardest for flash (DR=0.098) — the violation type that cannot be detected by scanning numeric values alone
- **Pro outperforms flash** on all violated violation types, with the largest gap on `multiple` (+0.118) and `hp_resurrection` (+0.094)
- All violated types cluster tightly in the 0.098–0.248 DR range — no clear gradation

---

## Earliest Violation Step (EVS) Analysis

EVS was computed from the L18_L1 condition prompts (15 steps, k=15) by scanning for HP-resurrection and PP-increase patterns.

- Violated chains: 32
- EVS successfully computed: 17 (hp_resurrection: 4/4, monotone_increase: 2/2, multiple with detectable signal: 11/23)
- No EVS possible: 15 (causal_incoherence: cannot detect from numeric scan; multiple without clear HP/PP signal)

**EVS distribution for chains with detected violations:**

| EVS | N chains | Mean DR |
|---|---|---|
| 5 | 2 | 0.236 |
| 7 | 2 | 0.198 |
| 8 | 2 | 0.177 |
| 10 | 3 | 0.164 |
| 11 | 2 | 0.165 |
| 12 | 1 | 0.148 |
| 13 | 2 | 0.193 |
| 14 | 2 | 0.179 |
| 15 | 1 | 0.180 |

**Trend:** Chains where violations occur earlier (steps 5–7) tend to have marginally higher detection rates than chains where violations occur late (steps 12–15), though the difference is small and the sample size is insufficient for strong conclusions. All EVS values fall in the range [5, 15], covering all steps of the 15-step chain.

All EVS=1 values found in the first pass were artifacts of the `chain_variants/{condition}` concatenated prompt structure and were discarded.

---

## Output Token Quartile Analysis (Proxy for Reasoning Difficulty)

Since chain_length is uniform, mean output tokens per chain (across all conditions) serves as a proxy for chain-induced reasoning burden.

| Token Quartile | Flash DR | Pro DR | N | Intact % |
|---|---|---|---|---|
| Q1 (simplest) | 0.454 | 0.464 | 13 | 46% |
| Q2 | 0.455 | 0.520 | 12 | 42% |
| Q3 | 0.379 | 0.407 | 12 | 33% |
| Q4 (most verbose) | 0.312 | 0.361 | 13 | 23% |

Chains generating more tokens tend to have lower detection rates, partially because Q4 contains fewer intact chains (which inflate Q1/Q2 rates). Even so, pro's Q2 (0.520) vs Q4 (0.361) gap of 0.16 is notable.

---

## Per-Condition Detection Rates

Top-performing conditions (DR > 0.60):

| Condition | DR |
|---|---|
| flash_L18_L2 | 0.717 |
| pro_L12_L3 | 0.680 |
| pro_L18_L2 | 0.660 |
| pro_L18_L3 | 0.660 |
| pro_L11_L2 | 0.660 |
| flash_L12_L3 | 0.640 |
| flash_L18_L3 | 0.625 |

Most conditions cluster around 0.360 for flash (the baseline NO-bias rate: 18/50 intact chains × 1.0 + 32/50 violated × 0 ≈ 0.36). Flash improvements come mainly from L18 and L12 conditions. Pro improvements are more distributed.

Bottom conditions: `pro_L24_L2` (0.320), `flash_L15_L3` (0.280). L18_L4 (native thinking) has NaN DR in the main provenance — those records are in amendment_7.

---

## Blind Spots

**Definition:** Chains where both flash and pro achieve DR < 0.40 across all conditions.

- **31 out of 32 violated chains** are blind spots for both models
- 1 violated chain is not a blind spot (`gen9ou-2310556760_p1_shuffled_7919`, vtype=multiple, flash=0.161, pro=0.288 — barely misses threshold for pro)

Blind spot distribution by violation type:
- multiple: 22/23 (96%)
- hp_resurrection: 4/4 (100%)
- causal_incoherence: 3/3 (100%)
- monotone_increase: 2/2 (100%)

**No violated chain achieves detection rates above the blind-spot threshold for both models.** This is the core finding: the LLMs are systematically unable to detect actual violations in this constraint-chain format.

---

## Consistently Missed Chains (Bottom 5)

| Chain | Overall DR | Flash DR | Pro DR | VType | EVS |
|---|---|---|---|---|---|
| gen9ou-2301944495_p1_shuffled_42 | 0.082 | 0.100 | 0.065 | multiple | — |
| gen9ou-2334711641_p2_shuffled_7919 | 0.115 | 0.065 | 0.167 | causal_incoherence | — |
| gen9ou-2310254076_p2_shuffled_42 | 0.121 | 0.103 | 0.138 | multiple | — |
| gen9ou-2260297169_p2_shuffled_1337 | 0.133 | 0.100 | 0.167 | hp_resurrection | 10 |
| gen9ou-2306563046_p2_shuffled_1337 | 0.133 | 0.133 | 0.133 | multiple | — |

Notable: the absolute worst chain for Pro (`gen9ou-2301944495_p1_shuffled_42`) has DR=0.065 — the model correctly identifies the violation in only 6.5% of conditions. `gen9ou-2334711641_p2_shuffled_7919` (causal_incoherence) is the worst for flash (0.065).

---

## Consistently Caught Chains (Top 5 — all intact)

| Chain | Overall DR | Flash DR | Pro DR | VType |
|---|---|---|---|---|
| gen9ou-2348078225_p1 | 0.915 | 0.935 | 0.893 | none |
| gen9ou-2323855766_p2 | 0.902 | 0.933 | 0.871 | none |
| gen9ou-2273536349_p1 | 0.902 | 0.900 | 0.903 | none |
| gen9ou-2321486759_p2 | 0.898 | 0.897 | 0.900 | none |
| gen9ou-2330862666_p2 | 0.885 | 0.900 | 0.871 | none |

**All top-5 are intact chains.** This is not surprising — the dominant failure mode is correctly rejecting violations, not correctly accepting intact chains. Intact chains are "caught" (correctly identified as non-violated) ~88% of the time on average.

---

## Summary and Interpretation

1. **Chain length does not differentiate difficulty** — all chains are 15 steps. Difficulty is entirely explained by violation type and the specific violation mechanism.

2. **Violation type is the primary difficulty driver:** intact > monotone_increase ≈ hp_resurrection > multiple ≈ causal_incoherence. The bottom three types differ by only 0.035 in flash DR, suggesting the violated chains form a single "hard" cluster.

3. **EVS does not clearly predict difficulty** — the range is [5, 15] across violated chains, and there is no monotone relationship between step position and detection rate. Late-step violations (EVS=12–15) do appear slightly harder but the signal is weak given N=17.

4. **The 31/32 blind-spot rate is the critical finding**: essentially all violated chains are below the detection threshold for both models. The models are not partially solving the problem — they are near-systematically failing to flag genuine violations.

5. **Pro > Flash on violated chains** (0.238 vs 0.130 overall) while **Flash > Pro on intact chains** (0.879 vs 0.791). Pro achieves better recall; Flash achieves better precision (fewer false positives on intact chains).
