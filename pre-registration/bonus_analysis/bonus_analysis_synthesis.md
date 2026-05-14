# Bonus Analysis Synthesis

**Computed:** 2026-05-14  
**Tests completed:** 1, 2, 3, 4, 6, 7, 8, 9  
**Tests omitted:** 5, 10 (lower priority, not completed)

---

## 1. Setup Verification

### Data Available
- `parser_provenance.ndjson`: 3,200 records confirmed (50 chains × 64 conditions)
- `amendment_7/provenance.ndjson`: 100 records confirmed (73 parseable, reasoning_content populated)
- `day_minus_2/parser_provenance.ndjson`: 250 records, all 50 OLAT chains present, all flash verdicts = NO
- `day_minus_2_v4pro/parser_provenance.ndjson`: 250 records, all 50 OLAT chains present, 43 NO / 5 YES
- `day_2/quartile_analysis/quartile_breakdown_full.csv`: 48 rows (only 4 conditions: flash/pro × L18_L2/L18_L3)
- `chain_variants/{model}/{condition}/{chain_id}.json`: Accessible for all 50 chains
- `chain_condition_assignments.ndjson`: 3,200 records with full condition metadata

### Data Corrections Noted
- Violation type counts differ from task specification: actual counts are hp_resurrection=4, causal_incoherence=3, monotone_increase=2, multiple=23, none=18 (not 8/6/4/16 as specified)
- All 50 chains have uniform length (15 steps) — chain_length stratification is degenerate
- L18_L4 conditions have no parseable records in main provenance (in amendment_7 instead)
- In amendment_7, 100% of parseable records produce YES verdicts — a systematic L18_L4 YES-bias

### Data Missing
- `Ditto-5.3-Pokemon Diag/pokemon-v1-symbolic/outputs/phase3_results_v4.csv` — absent (Test 8 partial)
- `anchor_effects/observational_tests_summary.md` — absent (not needed for any test)
- Tests 5 and 10 were not completed (lower priority, limited available time)

---

## 2. Per-Test Summary

### Test 3: Chain Difficulty Stratification
All 50 OLAT chains are exactly 15 steps long, making chain_length stratification impossible. Difficulty is explained by violation type: intact chains achieve ~83% detection rate; violated chains cluster at 13–24% regardless of violation type. The 31/32 "blind spot" rate (both models below 40% DR) is the core finding — essentially all violated chains are systematically undetected. A proxy analysis using mean output tokens shows marginal signal (Q4 tokens: 31–36% DR vs Q1 tokens: 45–46%), partly confounded by intact-chain composition.

### Test 9: LLM-Checker Complementarity
The symbolic checker (L3) achieves 96% accuracy against L1 ground truth (precision=1.0, recall=0.941). When the LLM fails (1,832 instances), the checker is correct 94.7% of the time. When the checker fails (120 instances, only 2 chains), the LLM succeeds only 18.3% of the time. The relationship is strongly asymmetric: the checker is a far better fallback for LLM errors than vice versa. Under the 6 meaningful conditions, LLM coverage of checker failures rises to 66.7%, but this applies only to the 2 anomalous checker-wrong chains.

### Test 6: Detection Success Predictor
Random Forest achieves 84.7% accuracy (AUC=0.925) vs a 54.7% majority-class baseline. The top predictors are: (1) lever_num (23.3% importance — which experimental manipulation was applied), (2) chain_mean_output_tokens (19.6% — per-chain difficulty proxy), (3) record_output_tokens (10.7%), (4) is_intact (8.5%), (5) flash_baseline_correct (8.3%). The predictor confirms that condition choice dominates over chain properties as a predictor of success.

### Test 1: Confabulation Pattern Characterization
Under L18_L4 (native thinking), 100% of intact chains are confabulated — the model says YES to every chain regardless of violation status. Both flash (38/38) and pro (35/35) parseable records produce YES. The confabulation covers all 9 rule categories comprehensively and is accompanied by longer reasoning traces (wrong predictions: +40% longer). The L18_L4 condition introduces a YES-bias that completely eliminates specificity for intact chains.

### Test 8: Symbolic Checker Characterization (Partial)
On 50 OLAT chains: recall=0.941, precision=1.000, FPR=0.000, accuracy=0.960. The checker achieves 100% recall on all true violation types (hp_resurrection, monotone_increase, causal_incoherence, multiple). The 2 missed chains are definitional anomalies — shuffled chains where the shuffling didn't introduce detectable constraint violations per the checker's rules. Full characterization requires the missing phase3_results_v4.csv.

### Test 7: Verdict Stability Analysis
No chain is "unstable" (H > 1.0). All YES rates fall in [0.082, 0.300] — well below the 0.5 threshold for maximum entropy. The strongest NO-bias chains are intact chains and one extremely hard violated chain (gen9ou-2301944495_p1_shuffled_42, YES rate=0.082). Violated chains have slightly higher entropy (mean H=0.685) than intact chains (0.628), but both groups are middle-range — the model can be pushed toward YES under good conditions but defaults to NO. No chain ever achieves YES rates above 0.30.

### Test 4: Failure Mode Coexistence
FM1 (NO-floor in V4-Pro baseline) affects 43/50 chains (86%). FM2 (valley quartile) is unresolvable due to token-count boundary mismatch with the 50-chain subset. FM3 (confabulation in L18_L4) affects 15/50 intact chains (30%). The 14 FM1+FM3 co-occurring chains are all intact chains — they are correctly rejected in simple conditions but confabulated under native thinking. Only 5 chains escape FM1 (the 5 where V4-Pro said YES in the anti-detection baseline).

### Test 2: Reasoning Depth Comparison
L18 L4 (native thinking) reasoning is 3.7× longer, achieves 100% counter-evidence usage (vs 85.7%), and shows 65× more logical chain patterns than L18 L3 (text-prompt CoT). Despite this, accuracy is identical: 0.684 (L18 L3) vs 0.685 (L18 L4). Deeper reasoning does not improve detection rates. Flash generates longer reasoning than Pro under both L18 L3 and L18 L4, but Pro achieves comparable or slightly better accuracy.

---

## 3. Cross-Test Synthesis: Tests 3, 6, 9 Together

Tests 3, 6, and 9 converge on a unified picture of why violation detection fails and what would be needed to fix it.

**Test 3** establishes that violated chains are systematically undetected (31/32 blind spots) across all conditions, with the primary differentiator being violation type (not chain length, not step count). The best conditions (L18_L3, L18_L2) improve detection rates from ~13% to ~30% for violated chains — but this is still far below adequate.

**Test 6** reveals that condition choice (lever_num importance = 0.233) is the dominant predictor of success — more important than any intrinsic chain property. The chain's "difficulty" (proxied by token output) is secondary (importance = 0.196). This means the model's failure is not fundamentally about the chains being hard — it's about the conditions not providing adequate signal. The right experimental manipulation (lever) matters more than the chain itself.

**Test 9** shows that the symbolic checker covers LLM failures 94.7% of the time. This creates a complementarity opportunity: wherever the LLM fails (which is most violated chains, under most conditions), the checker succeeds. But the checker's near-perfect performance means there are few cases where LLM adds value over the checker. The only domain where the LLM potentially adds value is on chains where the checker fails (the 2 anomalous boundary cases), and even there, only under the 6 meaningful conditions does the LLM coverage reach 66.7%.

**Joint implication:** The detection problem is not simply "the model isn't reasoning deeply enough" (Test 2 shows deeper reasoning doesn't help). The problem is architectural — the chain representation (15-step symbolic constraint sequences) lacks the cues that LLMs rely on for pattern matching. A hybrid system using the symbolic checker as primary detector and the LLM as a secondary arbiter (under L18-class conditions) for ambiguous cases would substantially outperform either alone.

---

## 4. Architectural Implications

**Finding 1: The YES-bias problem is condition-specific, not universal.** L18_L4 produces 100% YES; baseline produces ~36% YES; L18_L3 produces ~66% YES on all chains combined. The model's bias is tunable through prompt engineering, not fixed.

**Finding 2: Native thinking mode (L18_L4) trades specificity for sensitivity.** It achieves near-100% sensitivity on violated chains but 0% specificity on intact chains (all intact chains confabulated). Text-prompt CoT (L18_L3) achieves ~88% specificity with ~25% sensitivity — a better operating point for practical use.

**Finding 3: Condition choice dominates chain properties.** The single most important predictor of detection success is which experimental lever is applied. This suggests the field of prompt engineering for constraint checking has large headroom — there is significant signal that better prompts could unlock.

**Finding 4: The checker + LLM ensemble is the right architecture.** Given that the checker has near-perfect precision and high recall, and the LLM's best conditions add marginal recall on the checker's blind spots, an ensemble should use: (1) symbolic checker as primary detector, (2) LLM under high-performance conditions (L18_L3 or L18_L2) as secondary check only for checker-negative chains.

**Finding 5: Per-chain difficulty is real but secondary.** Some chains are intrinsically harder (Test 6: chain_mean_output_tokens importance = 0.196; Test 3: some violated chains have DR<10%). These hard chains tend to be "multiple" violation type with late-step violations. Understanding what makes them hard (possibly more complex state tracking requirements) could guide chain difficulty stratification in future dataset design.

---

## 5. Unexpected Findings

**5.1 All chains have the same length (15 steps).** The task specification mentioned chain_length as a differentiating feature, but the OLAT dataset is uniform. The L08 lever varies k (steps *shown*), not the underlying chain length. This means one planned stratification dimension is structurally absent.

**5.2 L18_L4 is always YES.** The amendment_7 dataset shows 0/73 NO responses. This was not anticipated — the expectation was that thinking mode might improve accuracy. Instead, it produces a YES-bias that eliminates all specificity. This is a critical finding about the behavior of native thinking mode on this task type.

**5.3 The symbolic checker has perfect precision (zero FP) on the OLAT subset.** The checker flags no intact chain as violated. This makes the checker unusually trustworthy as a primary signal — any chain it flags is very likely genuinely violated.

**5.4 Two anomalous chains (violation_type='none' but L1=True).** These shuffled chains where the shuffle introduced no detectable constraint violation create definitional boundary cases. Both the LLM and checker tend to classify them as intact — arguably correctly, since the constraint logic finds no violations.

**5.5 Reasoning depth does not predict accuracy (Test 2).** L18_L4 reasoning is 3.7× longer with dramatically more logical structure than L18_L3, but accuracy is essentially identical (0.684 vs 0.685). This suggests the bottleneck is not reasoning process quality but something earlier: whether the model's internal representation of the constraint chain encodes the relevant features at all.

**5.6 Pro outperforms flash on violated chains but underperforms on intact chains.** Flash achieves higher specificity (79.1% intact DR); Pro achieves higher sensitivity (23.8% violated DR). These are different operating points on the same ROC curve, suggesting the two models have different default operating thresholds.

---

## File Index

| File | Test | Status |
|---|---|---|
| `test_1_confabulation_patterns.md` | Test 1 | Complete |
| `test_2_reasoning_depth.md` | Test 2 | Complete |
| `test_3_difficulty_stratification.md` | Test 3 | Complete |
| `test_4_failure_coexistence.md` | Test 4 | Complete |
| `test_6_predictor.md` | Test 6 | Complete |
| `test_7_verdict_stability.md` | Test 7 | Complete |
| `test_8_checker_characterization.md` | Test 8 | Partial (50 chains only) |
| `test_9_complementarity.md` | Test 9 | Complete |
| `test_6_models/logistic_regression.joblib` | Test 6 | Model file |
| `test_6_models/random_forest.joblib` | Test 6 | Model file |
| Tests 5, 10 | — | Not completed (lower priority) |
