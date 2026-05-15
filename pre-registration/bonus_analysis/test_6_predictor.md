# Test 6: Detection Success Predictor

**Status:** Complete  
**Priority:** 1  
**Computed:** 2026-05-14  
**Models saved:** `bonus_analysis/test_6_models/`

---

## Setup

**Target:** Binary — did V4-Pro produce a CORRECT verdict under L3_symbolic_checker ground truth?  
**Filter:** Pro model, parse_success=True records only  
**N records:** 1,499 (out of 1,600 pro records; 101 parse failures excluded)  
**Base rate:** 43.7% correct (655/1,499)

**Train/Test split:** 80/20, seed=42, stratified by condition_id  
- Train: 1,199 records  
- Test: 300 records  
- Test positive rate: 45.3%

---

## Feature Engineering

### Chain features (per sample_id):
- `is_intact`: 1 if violation_type='none', 0 otherwise
- `vtype_causal_incoherence`, `vtype_hp_resurrection`, `vtype_monotone_increase`, `vtype_multiple`, `vtype_none`: one-hot encoding
- `flash_baseline_correct`: did flash get it right in flash_baseline condition?
- `pro_baseline_correct`: did pro get it right in pro_baseline condition?
- `chain_mean_output_tokens`: mean output tokens across all conditions for this chain

### Condition features (per condition_id):
- `lever_num`: lever number (0 for baseline, 1–24 for experimental conditions)
- `level_num`: level 1–5 (L1=1 to L5=5)
- `thinking_enabled`: binary (only L18_L4 conditions)
- `function_calling`: binary
- `max_tokens`: maximum output tokens allowed
- `k_steps`: k parameter (steps shown to model)
- `cond_output_tok_p50`: median output tokens for this condition across all chains

### Per-record feature:
- `record_output_tokens`: actual output tokens for this specific record

Total features: 17

---

## Logistic Regression Results

| Metric | Value |
|---|---|
| Accuracy | 0.777 |
| F1 | 0.733 |
| AUC-ROC | 0.830 |

**Confusion matrix (test set, n=300):**
```
              Predicted NO  Predicted YES
Actual NO         141            23
Actual YES         44            92
```

**Coefficients (sorted by |coef|):**

| Feature | Coefficient |
|---|---|
| function_calling | +1.129 |
| pro_baseline_correct | +0.656 |
| is_intact | +0.619 |
| vtype_none | +0.619 |
| flash_baseline_correct | +0.619 |
| vtype_hp_resurrection | −0.269 |
| vtype_causal_incoherence | −0.247 |
| vtype_monotone_increase | −0.181 |
| level_num | −0.059 |
| vtype_multiple | −0.026 |

---

## Random Forest Results

| Metric | Value |
|---|---|
| Accuracy | **0.847** |
| F1 | **0.826** |
| AUC-ROC | **0.925** |

**Confusion matrix (test set, n=300):**
```
              Predicted NO  Predicted YES
Actual NO         145            19
Actual YES         27           109
```

**Top-10 Feature Importances:**

| Rank | Feature | Importance |
|---|---|---|
| 1 | lever_num | 0.2327 |
| 2 | chain_mean_output_tokens | 0.1964 |
| 3 | record_output_tokens | 0.1072 |
| 4 | is_intact | 0.0847 |
| 5 | flash_baseline_correct | 0.0828 |
| 6 | vtype_none | 0.0624 |
| 7 | function_calling | 0.0500 |
| 8 | pro_baseline_correct | 0.0455 |
| 9 | level_num | 0.0429 |
| 10 | cond_output_tok_p50 | 0.0267 |

---

## Baseline Comparison

| Classifier | Accuracy |
|---|---|
| Majority class (always predict dominant) | 0.547 |
| Logistic Regression | 0.777 |
| **Random Forest** | **0.847** |

Both classifiers substantially exceed the majority-class baseline (0.547). The Random Forest at 84.7% accuracy is well above the 65% characterization threshold.

---

## Feature Importance Analysis

### Best classifier accuracy: 0.847 — ABOVE 65% threshold

**Top 3 features by importance (Random Forest):**

1. **lever_num (0.233):** The lever number (which experimental manipulation was applied) is the single most important predictor. This makes sense — levers like L18 (CoT), L12 (structured output), and L17 (example-aware) dramatically improve performance. Baseline (lever=0) and most levers have near-random performance.

2. **chain_mean_output_tokens (0.196):** The mean output tokens a chain generates across all conditions is the second most important feature. Chains that generate more tokens are harder — they require more analysis, and the model tends to fail more often. This is a per-chain difficulty proxy (since actual chain_length is uniform at 15 steps).

3. **record_output_tokens (0.107):** The actual tokens generated for this specific record. Higher token output is associated with more reasoning, but also with confabulation (long wrong reasoning traces).

4. **is_intact + vtype_none (combined 0.147):** Intact chains are far easier to handle correctly.

5. **flash_baseline_correct (0.083):** Whether flash also gets this chain right at baseline. High cross-model consistency suggests a chain is intrinsically easy.

---

## Confidence vs Accuracy (Random Forest)

| Probability range | N | Accuracy |
|---|---|---|
| [0.00, 0.02) | 49 | 0.980 |
| [0.02, 0.06) | 37 | 0.946 |
| [0.06, 0.18) | 34 | 0.882 |
| [0.18, 0.32) | 28 | 0.750 |
| [0.32, 0.60) | 32 | 0.500 |
| [0.60, 0.79) | 30 | 0.700 |
| [0.79, 0.94) | 25 | 0.920 |
| [0.94, 0.99) | 33 | 0.909 |
| [0.99, 1.00) | 8 | 1.000 |

The calibration shows a U-shape: the model is well-calibrated at high and low confidence, but predictions in the [0.32, 0.60) range (near-chance) are genuinely uncertain (50% accuracy). When the RF is very confident (either very high or very low P), it is correct >90% of the time.

---

## Key Findings

1. **Condition choice dominates (lever_num importance = 0.233):** The experimental manipulation applied to a chain matters more than any intrinsic chain property. This validates the study design — lever selection is the primary driver of whether the model will succeed.

2. **Chain difficulty is real but secondary (token proxy importance = 0.196):** Per-chain difficulty (proxied by mean output token count) is the second most important feature, confirming that some chains are systematically harder regardless of condition.

3. **Baseline correctness predicts future correctness (flash/pro baseline combined ~0.128):** Whether a model gets a chain right under minimal conditions predicts whether it will succeed under augmented conditions. This is consistent with chains having intrinsic difficulty levels.

4. **Function calling (0.050):** Conditions with function calling enabled show improved performance — consistent with the structured output benefit seen in the main analyses.

5. **Thinking_enabled = 0.000:** The L18_L4 condition (thinking enabled) has no parseable records in the main provenance (records are in amendment_7 with different structure), so this feature contains no signal.

6. **Implications:** A simple prediction rule based on (a) which lever is applied + (b) whether the chain generates high token counts + (c) whether it's an intact chain explains most of the variance. A meta-predictor could pre-screen chains for difficulty and route harder chains to higher-intervention conditions.

---

## Limitations

- The L18_L4 condition is excluded (parse failures in main provenance)
- Only pro model records are used (target: L3 correctness)
- Chain features are limited since all chains have uniform 15-step length
- The high RF accuracy (0.847) may partially reflect that is_intact and lever_num together create nearly linearly separable conditions
- Models saved to: `bonus_analysis/test_6_models/logistic_regression.joblib` and `random_forest.joblib`
