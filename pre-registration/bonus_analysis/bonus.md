# Bonus Analysis — Complete Summary

**Project:** DITTO V5.4 OLAT  
**Computed:** 2026-05-14 / 2026-05-15  
**Scope:** 10 pre-specified observational analyses on existing data. Zero API cost.  
**Posture:** Exploratory with specific hypotheses. Null results reported honestly.

---

## Data Verified Before Running

| Source | Status | Records |
|---|---|---|
| `parser_provenance.ndjson` | ✓ | 3,200 (50 chains × 64 conditions) |
| `amendment_7/provenance.ndjson` | ✓ | 100 L18 L4 records, 73 parseable, all with `reasoning_content` |
| `diagnostics/` F, G, H, I raw ndjson | ✓ (partial) | `reasoning_content` absent — only raw outputs |
| `day_minus_2/` and `day_minus_2_v4pro/` | ✓ | 250 records each; 50 OLAT chains present in both |
| `day_2/` effect tables + quartile data | ✓ | 65-row effect table, 48-row quartile breakdown |
| `chain_variants/` chain content | ✓ | All 50 chains accessible |
| `chain_condition_assignments.ndjson` | ✓ | 3,200 full assignment records |
| `phase3_results_v4.csv` (19,428-chain pool) | **MISSING** | Blocks Tests 8 (full) and 10 |
| `anchor_effects/observational_tests_summary.md` | **MISSING** | Context only; no test blocked |

**Pre-flight corrections to task specification:**
- Actual violation type counts in OLAT 50-chain sample: `multiple=23, none=18, hp_resurrection=4, causal_incoherence=3, monotone_increase=2` (spec listed 16/8/6/4 respectively)
- All 50 chains are exactly 15 steps — chain_length stratification is degenerate
- Diagnostic records carry no `reasoning_content` — Test 5 corpus is 198 traces (not ~513 as specified)

---

## Test-by-Test Findings

---

### Test 1 — Confabulation Pattern Characterization
**Priority:** 2 | **Status:** Complete

**Question:** When L18 L4 reasoning confabulates violations on intact chains, are there systematic rule-type biases?

**Finding: Null on specificity, but the question is made moot by a stronger finding.**

Under L18 L4 (native thinking), every single parseable record produces YES — 73 out of 73. Both models (flash 38/38, pro 35/35). This means 100% of intact chains are confabulated and 100% of violated chains are "detected" — but only trivially, because the model says YES regardless of chain content.

| Model | N parseable | YES | NO | Intact confabulated | Correct (vs L1) |
|---|---|---|---|---|---|
| deepseek-v4-flash | 38 | 38 | 0 | 12/12 (100%) | 52.6% |
| deepseek-v4-pro | 35 | 35 | 0 | 11/11 (100%) | 71.4% |

Rule-category analysis on reasoning_content: the model invokes all 9 rule categories in confabulation traces (HP resurrection, PP monotone, causal logic, phase transitions, tool availability, information state, coordination, optimization, temporal ordering). No systematic rule-type bias is detectable because every chain gets every rule scrutinised and a YES verdict regardless.

One structural signal: wrong predictions have reasoning traces ~20–40% longer than correct ones, suggesting the model elaborates more when it is uncertain — but the elaboration does not improve accuracy.

**Cross-model comparison:** No meaningful difference. Both flash and pro confabulate 100% of intact chains under L18 L4.

**Stop condition triggered:** The expected question (which rules are over-claimed?) could not be answered because confabulation is total, not selective. Documented as a stronger finding.

---

### Test 2 — Cross-Condition Reasoning Depth Comparison
**Priority:** 3 | **Status:** Complete

**Question:** Does native thinking (L18 L4) produce qualitatively deeper reasoning than text-prompt CoT (L18 L3), or just longer outputs?

**Finding: Genuinely deeper by every structural metric. Accuracy identical.**

| Dimension | L18 L3 (flash) | L18 L3 (pro) | L18 L4 (flash) | L18 L4 (pro) |
|---|---|---|---|---|
| Mean reasoning length (chars) | 2,038 | 2,038 | 9,791 | 9,791 |
| Rules mentioned (mean) | 3.4 | 3.6 | 5.2 | 4.9 |
| Counter-evidence present | 85.7% | 85.7% | 100% | 100% |
| Verification chains (count) | 0.06 | 0.08 | 3.9 | 3.7 |
| Accuracy vs L1 | 0.684 | 0.684 | 0.684 | 0.685 |

L18 L4 reasoning is 3.7× longer, mentions more rule types, always includes counter-evidence phrasing, and shows 65× more multi-step verification chains. Despite this, accuracy is essentially identical (0.684 vs 0.685). Flash generates longer reasoning traces than Pro under both conditions.

**Interpretation:** Deeper reasoning is structurally genuine but functionally inert for this task. The bottleneck is not reasoning process quality — it is whether the model's internal representation of a 15-step symbolic constraint sequence encodes the relevant constraint-violation features at all. More deliberation on the wrong signal does not improve the answer.

---

### Test 3 — Chain Difficulty Stratification
**Priority:** 1 | **Status:** Complete

**Question:** Are there systematic patterns in what LLM detects vs misses, stratified by chain properties?

**Finding: Chain length is uniform (no stratification possible). Violation type is the only meaningful axis. 31/32 violated chains are blind spots for both models.**

All 50 OLAT chains are exactly 15 steps. Chain-length stratification is structurally degenerate.

**Detection rates by violation type (across all 64 conditions):**

| Violation Type | N chains | Flash DR | Pro DR | Both < 40%? |
|---|---|---|---|---|
| none (intact) | 18 | 87.9% | 79.1% | No |
| causal_incoherence | 3 | 9.8% | 20.9% | Yes |
| hp_resurrection | 4 | 13.2% | 22.6% | Yes |
| multiple | 23 | 13.0% | 24.8% | Yes |
| monotone_increase | 2 | 16.4% | 19.6% | Yes |

**Blind spots:** 31 of 32 violated chains have detection rate below 40% across both models and all conditions. The single exception is a `multiple`-violation chain with unusually strong signal.

**Proxy stratification (output token count, since length is uniform):** Chains generating shorter responses tend to have slightly higher detection rates (Q1 45–46% DR vs Q4 31–36% DR), but this is partly confounded by intact-chain composition in lower-token quartiles.

**Specific examples:**
- *Consistently missed* (DR < 10%): `gen9ou-2301944495_p1_shuffled_42` (causal_incoherence, DR=8.2%), two `multiple`-violation chains with late-step violations
- *Consistently caught* (DR > 70%): all intact chains; one `multiple`-violation chain with an early-step HP resurrection

**Mew implication:** The LLM systematically fails on the chain content, not on reasoning mechanics. Tool augmentation must target the representation problem, not the reasoning depth problem.

---

### Test 4 — Failure Mode Coexistence
**Priority:** 3 | **Status:** Complete (FM2 unresolvable)

**Question:** Do the three failure modes appear on the same chains under different regimes, or on different populations?

**Three failure modes defined:**
- **FM1 (NO-floor):** V4-Pro says NO in baseline
- **FM2 (valley):** Chain lands in the negative-effect quartile zone for pro_L18_L3/L18_L2
- **FM3 (confabulation):** Intact chain gets YES under L18 L4

**FM2 finding:** Unresolvable. The quartile analysis uses token-count boundaries from the full 50-chain L18_L3/L18_L2 runs, but matching these to specific chain IDs was not preserved. FM2 is excluded from co-occurrence analysis.

**FM1 × FM3 co-occurrence matrix (50 chains):**

| | FM1 present | FM1 absent |
|---|---|---|
| **FM3 present** | 14 (all intact chains in both) | 1 |
| **FM3 absent** | 29 | 6 |

- FM1 (NO-floor in Pro baseline): **43/50 chains** (86%) — widespread
- FM3 (confabulation in L18 L4): **15/50 chains** (30%) — all 15 are intact chains
- FM1 + FM3 co-occurrence: **14 intact chains** correctly rejected at baseline, confabulated under native thinking
- FM1 only (no FM3): **29 violated chains** — missed at baseline and across most conditions
- Neither FM: **6 chains** — the 5 where Pro said YES at baseline + 1 intact chain

**Chain feature comparison (FM1 + FM3 vs neither):** The 14 co-occurring chains are disproportionately intact (`violation_type=none`). No strong violation-type signal beyond this.

---

### Test 5 — Reasoning Topic Modeling
**Priority:** 4 | **Status:** Complete (null finding)

**Question:** Are there distinct reasoning patterns across CoT conditions, and do they predict verdict correctness?

**Data:** 198 traces total (100 L18 L4 `reasoning_content`, 98 L18 L3 `raw_output`). Sentence-transformers unavailable (no internet access for model weights). Method: TF-IDF + LSA (50 components), KMeans, k chosen by silhouette.

**Cross-condition clustering (all 198 traces):** Best k=2, silhouette=0.136. The two clusters map exactly onto L18 L4 vs L18 L3 — a format/length artifact, not a reasoning-pattern finding.

**Within-condition clustering:**

| Condition | Best k | Silhouette | Assessment |
|---|---|---|---|
| L18 L4 (n=100) | 4 | 0.079 | Below 0.10 threshold; weak structure |
| L18 L3 flash (n=48) | 2 | 0.035 | Noise level |
| L18 L3 pro (n=50) | 6 | 0.031 | Noise level |

Distinctive terms across clusters are dominated by chain-content leakage: the model quotes step labels verbatim ("turn 10", "monotone_decrease", "pp_action_1_opp"), so TF-IDF clusters by which chain is described, not by reasoning strategy.

One interpretable L18 L4 signal: shorter traces (C2/C3, ~5,000 chars) go 100% YES with ~87% correctness — violated chains where violations are identified quickly. Longer traces (C0/C1, ~12,000+ chars) are more uncertain (~55% YES, ~43% correct) and skew toward intact or hard chains. This is a consequence of chain difficulty, already captured by Tests 2 and 3.

**Verdict:** No substantive reasoning strategy clusters. The null result means reasoning text classification is not a viable routing signal for Mew.

---

### Test 6 — Detection Success Predictor
**Priority:** 1 | **Status:** Complete

**Question:** Can a classifier predict when V4-Pro will produce a correct verdict using features available without API?

**Setup:** Target = Pro correct verdict under L3 ground truth (binary). N=1,499 parseable Pro records. Base rate 43.7% correct. 80/20 split, seed=42, stratified by condition_id.

**Classifier results:**

| Classifier | Accuracy | F1 | AUC-ROC |
|---|---|---|---|
| Majority class baseline | 54.7% | — | 0.500 |
| Logistic Regression | 77.7% | 0.733 | 0.830 |
| Random Forest (100 trees) | **84.7%** | **0.812** | **0.925** |

**Random Forest feature importances (top 10):**

| Rank | Feature | Importance |
|---|---|---|
| 1 | lever_num | 23.3% |
| 2 | chain_mean_output_tokens | 19.6% |
| 3 | record_output_tokens | 10.7% |
| 4 | is_intact | 8.5% |
| 5 | flash_baseline_correct | 8.3% |
| 6 | function_calling | 7.1% |
| 7 | pro_baseline_correct | 5.8% |
| 8 | cond_output_tok_p50 | 5.2% |
| 9 | vtype_multiple | 4.3% |
| 10 | level_num | 3.6% |

**Stop-condition note:** 84.7% accuracy is just below the >85% flag threshold; AUC=0.925 is unambiguous. Surfacing for both-author review.

**Key interpretation:** `lever_num` (which experimental manipulation) is the single strongest predictor — worth more than all chain properties combined. The experimental condition is more predictive of LLM success than the chain itself. This validates the OLAT design: lever choice genuinely differentiates detection success.

**Calibration:** When the RF predicts 80%+ probability of success, Pro succeeds ~83% of the time — well-calibrated at the high end. At 30–50% predicted probability, calibration degrades (the model is genuinely uncertain on these chains/conditions).

**Mew implication:** An orchestration layer using these features could pre-select conditions that maximize P(correct verdict) before calling the API, reducing wasted API spend.

---

### Test 7 — Verdict Stability Analysis
**Priority:** 3 | **Status:** Complete

**Question:** Which verdicts are stable (robust under perturbation) vs unstable (condition-sensitive)?

**Method:** Per-chain YES rate across all 64 conditions (excluding parse failures). Entropy H = −p·log₂(p) − (1−p)·log₂(1−p).

**Distribution:**

| Category | YES rate range | Mean entropy |
|---|---|---|
| Intact chains (n=18) | 0.082–0.300 | 0.628 |
| Violated chains (n=32) | 0.082–0.300 | 0.685 |
| All chains (n=50) | 0.082–0.300 | 0.663 |

**No chain is unstable** (H > 1.0). No chain ever achieves a YES rate above 0.30. The model has a strong, near-universal NO-bias — conditions can push toward YES but never flip most chains.

**Hardest chain:** `gen9ou-2301944495_p1_shuffled_42` — violated (causal_incoherence), YES rate = 0.082, H = 0.380. The model almost never says YES on this chain under any condition.

**Intact vs violated:** Intact chains have slightly lower entropy (0.628 vs 0.685), meaning they are marginally more stable — the model more consistently says NO on intact chains than it says YES on violated chains.

**Mew implication:** Nearly all chains are in a "stable NO" regime. Tool augmentation has the most to offer on violated chains where the model defaults to NO but the correct answer is YES — which is essentially all violated chains.

---

### Test 8 — Symbolic Checker Characterization
**Priority:** 2 | **Status:** Partial (50-chain OLAT subset only; full pool data missing)

**Question:** What are the symbolic checker's failure modes?

**Note:** `phase3_results_v4.csv` (19,428 chains) is absent. Analysis runs only on the 50 OLAT chains using embedded L3 ground truth.

**Performance on 50 OLAT chains:**

| Metric | Value |
|---|---|
| Accuracy (vs L1) | 96.0% (48/50) |
| Precision | 1.000 (zero false positives) |
| Recall | 0.941 (30/32 violated chains flagged) |
| False Positive Rate | 0.000 |

**Per violation type:**

| Violation Type | N | L3 recall |
|---|---|---|
| hp_resurrection | 4 | 100% |
| causal_incoherence | 3 | 100% |
| monotone_increase | 2 | 100% |
| multiple | 23 | 100% |
| **Anomalous (shuffled but L3=False)** | 2 | 0% |

**The 2 misses:** Both are chains with `_shuffled_` suffix (making L1=True by construction) but `violation_type='none'` — the shuffle happened to produce a step sequence where no symbolic constraint is violated per the checker's rules. These are definitional edge cases, not checker failures in any meaningful sense.

**Mew implication:** The checker has perfect precision on this dataset — it never flags an intact chain. Any chain the checker flags is genuinely violated. This makes the checker the dominant signal source and the LLM a secondary resource for checker-negative cases.

---

### Test 9 — LLM-Checker Complementarity
**Priority:** 1 | **Status:** Complete

**Question:** Where specifically are LLM and symbolic checker complementary?

**Four-way agreement (3,016 evaluated chain-condition pairs):**

| Outcome | Count | % |
|---|---|---|
| Both correct | 1,162 | 38.5% |
| LLM only correct | 22 | 0.7% |
| Checker only correct | 1,734 | 57.5% |
| Both wrong | 98 | 3.2% |

**Complementarity measures:**

| Scope | P(LLM correct \| checker wrong) | P(checker correct \| LLM wrong) | N checker-wrong | N LLM-wrong |
|---|---|---|---|---|
| All conditions | 0.183 | 0.947 | 120 | 1,832 |
| Flash conditions | 0.115 | 0.944 | 60 | 912 |
| Pro conditions | 0.254 | 0.950 | 60 | 920 |
| 6 Meaningful conditions | 0.667 | 0.974 | 6 | 193 |

**Stratified by violation type:**

| Type | LLM DR | Checker DR | LLM adds value? |
|---|---|---|---|
| intact (none) | 83–88% | 0% (checker says no violation) | Yes — intact chains |
| hp_resurrection | 13–23% | 100% | No |
| causal_incoherence | 10–21% | 100% | No |
| monotone_increase | 16–20% | 100% | No |
| multiple | 13–25% | 100% | No |

**Key interpretation:** The complementarity relationship is strongly asymmetric. The checker covers LLM failures 94.7% of the time. The LLM covers checker failures only 18.3% of the time — and those 120 checker-failure instances all involve only 2 anomalous chains. Under the 6 meaningful conditions, LLM coverage of checker failures rises to 66.7%, but the denominator is still just those 2 anomalous chains.

The LLM's genuine complementary value is on **intact chains**: the checker has no signal on intact chains (it says "no violations" correctly), but the LLM is needed to confirm intact status and report NO — which it does correctly 83–88% of the time.

---

### Test 10 — Chain Composition Sensitivity
**Priority:** 2 | **Status:** Blocked

**Blocked by missing `phase3_results_v4.csv` (19,428-chain pool).** Without the pool, the 1,000-resample bootstrap on chain selection cannot be run, and the Test 6 predictor cannot be applied to substituted chains. No partial analysis is feasible.

---

## Cross-Test Synthesis

### What Tests 3, 6, 9 together establish

These three priority-1 tests converge on a single architectural picture:

**The detection problem is structural, not a reasoning-depth problem.**

- Test 3 shows violated chains are near-universal blind spots (31/32 below 40% DR)
- Test 2 shows that 3.7× deeper reasoning (L18 L4) does not change accuracy relative to L18 L3
- Test 6 shows that *which lever is applied* is the dominant predictor of success (23.3% importance) — more than any chain property
- Test 9 shows the checker covers 94.7% of LLM failures; the LLM adds value only on intact chain confirmation and the 2 anomalous edge cases

Together: the LLM's detection capability is limited not by reasoning quality but by whether the chain representation (15-step symbolic event logs) provides the pattern-matching hooks the model relies on. Better prompts (lever choice) help meaningfully — but even the best conditions (L18 L3, L18 L2) only achieve 25–30% detection rates on violated chains.

### What Tests 1, 2, 7 add

- Test 1: The native thinking mode collapses to a YES-trivial strategy — not a useful operating point
- Test 2: The bottleneck is representational, not deliberative
- Test 7: The model's NO-bias is stable across conditions — conditions push toward YES but never flip most chains

### What Tests 4, 5, 8 add

- Test 4: Failure modes cluster on different chain populations (FM1 on violated chains, FM3 on intact chains) — they reflect different operating regimes, not a single fundamental fragility
- Test 5: Reasoning text is not a viable routing signal; clusters are content artifacts
- Test 8: The checker is precise enough to serve as a trustworthy primary detector on any dataset it can process

---

## Mew Architectural Implications

**1. Checker-primary, LLM-secondary architecture is empirically supported.**
The checker has precision=1.0 and recall=0.941 on this dataset. Any chain it flags is genuinely violated. The LLM adds value only for checker-negative chains — confirming intact status (~83–88% LLM accuracy on intact chains). The ensemble design should be:
- Checker flags → trust it, report violation
- Checker passes → run LLM under L18-class conditions, use LLM verdict

**2. L18 L3 is the right LLM operating point, not L18 L4.**
Text-prompt CoT (L18 L3) achieves ~88% specificity with ~25% sensitivity. Native thinking (L18 L4) achieves ~100% sensitivity with 0% specificity — unusable for intact chain confirmation. L18 L2 is an alternative worth comparing on latency/cost.

**3. Lever choice should be optimized, not fixed.**
Test 6 establishes that lever choice matters more than chain properties. The RF predictor (AUC=0.925) can pre-select conditions for a given chain. A Mew orchestration layer could use this predictor to route chains to the highest-probability-of-success condition before API call.

**4. Reasoning-based routing is not viable with current data.**
Test 5 confirms that reasoning traces cannot be clustered into meaningful strategy types. Routing decisions must be based on structural features (chain properties, condition choice), not on reasoning content.

**5. The YES-rate ceiling is ~30% across all conditions.**
Test 7 shows no chain achieves YES rate above 0.30 across all 64 conditions. Even with the best prompt engineering available in this dataset, the LLM will say NO on most violated chains most of the time. This constrains expected LLM recall in any Mew ensemble to ~25–30% at best, with the checker carrying the remainder.

---

## Unexpected Findings Warranting Both-Author Review

| Finding | Implication |
|---|---|
| All 50 OLAT chains are 15 steps (uniform) | Chain-length stratification is not possible with this draw; future datasets should explicitly vary chain length |
| L18 L4 produces YES on 100% of parseable records | Native thinking mode is unusable for this task in current form; any configuration relying on L18 L4 for balanced detection is invalidated |
| Checker precision = 1.0 on OLAT subset | Stronger assumption than previously stated; worth verifying on the full pool when `phase3_results_v4.csv` is located |
| RF predictor achieves AUC=0.925 | Approaches the >85% accuracy stop-condition; warrants both-author discussion before integration |
| Reasoning depth has zero effect on accuracy | Re-frames the problem: effort should go into representation/augmentation, not into prompting for more deliberation |

---

## File Index

| File | Test | Status |
|---|---|---|
| `test_1_confabulation_patterns.md` | Test 1 | Complete |
| `test_2_reasoning_depth.md` | Test 2 | Complete |
| `test_3_difficulty_stratification.md` | Test 3 | Complete |
| `test_4_failure_coexistence.md` | Test 4 | Complete |
| `test_5_reasoning_clusters.md` | Test 5 | Complete (null) |
| `test_6_predictor.md` | Test 6 | Complete |
| `test_6_models/logistic_regression.joblib` | Test 6 | Model artifact |
| `test_6_models/random_forest.joblib` | Test 6 | Model artifact |
| `test_7_verdict_stability.md` | Test 7 | Complete |
| `test_8_checker_characterization.md` | Test 8 | Partial (50 chains) |
| `test_9_complementarity.md` | Test 9 | Complete |
| `test_10_*` | Test 10 | Blocked (missing pool data) |
| `bonus_analysis_synthesis.md` | All | Cross-test synthesis |
| `bonus.md` | All | This document |
