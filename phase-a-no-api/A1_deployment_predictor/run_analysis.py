"""
Task A1: Deployment-Time Predictor Analysis
Question: Can a predictor using only deployment-time features (chain structure,
condition config) achieve usable AUC for predicting V4-Pro detection success?
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
from sklearn.calibration import calibration_curve
import joblib

REPO = Path(__file__).parent.parent.parent
PROV = REPO / "pre-registration/parser_provenance.ndjson"
FULL_RF = REPO / "pre-registration/bonus_analysis/test_6_models/random_forest.joblib"

# ─── Load data ────────────────────────────────────────────────────────────────
records = []
with open(PROV) as f:
    for line in f:
        records.append(json.loads(line.strip()))

df = pd.DataFrame(records)
df = df[df["model"] == "deepseek-v4-pro"].copy()
df = df[df["parse_success"] == True].copy()

# Ground truth: did V4-Pro produce the correct verdict under L3?
df["gt_l3"] = df["ground_truth"].apply(lambda g: g["L3_symbolic_checker"])
df["predicted_yes"] = df["parsed_label"] == "YES"
df["correct_l3"] = df["predicted_yes"] == df["gt_l3"]

# ─── Feature engineering ──────────────────────────────────────────────────────

# Per-chain features (computed across all records for that chain)
chain_stats = df.groupby("sample_id").agg(
    chain_mean_output_tokens=("usage", lambda x: np.mean([r["output_tokens"] for r in x])),
    is_intact=("violation_type", lambda x: int((x == "none").any())),
).reset_index()

# Violation type one-hot (use first occurrence per chain)
chain_vtype = df.groupby("sample_id")["violation_type"].first().reset_index()
for vt in ["causal_incoherence", "hp_resurrection", "monotone_increase", "multiple", "none"]:
    chain_vtype[f"vtype_{vt}"] = (chain_vtype["violation_type"] == vt).astype(int)
chain_vtype = chain_vtype.drop(columns=["violation_type"])

# Condition-level features
def parse_condition(cond_id):
    """Extract lever_num, level_num, and API parameter flags from condition_id."""
    if cond_id in ("flash_baseline", "pro_baseline"):
        return {"lever_num": 0, "level_num": 1, "thinking_enabled": 0,
                "function_calling": 0, "max_tokens": 32, "k_steps": 15}
    parts = cond_id.replace("flash_", "").replace("pro_", "")
    lever = int(parts.split("_L")[0][1:])
    level = int(parts.split("_L")[1])
    thinking = int(lever == 18 and level == 4)
    func_calling = int(lever == 12 and level == 3)
    max_tok = {(18, 2): 1024, (18, 3): 1024, (18, 4): 64, (12, 2): 128,
               (17, 2): 64, (17, 3): 128}.get((lever, level), 32)
    k = {1: 5, 2: 10, 4: 20, 5: 30}.get(level if lever == 8 else 99, 15)
    return {"lever_num": lever, "level_num": level, "thinking_enabled": thinking,
            "function_calling": func_calling, "max_tokens": max_tok, "k_steps": k}

cond_parsed = df["condition_id"].map(parse_condition).apply(pd.Series)
df = pd.concat([df.reset_index(drop=True), cond_parsed.reset_index(drop=True)], axis=1)

# Per-condition median output tokens (deployment-time: computed from historical runs of this condition)
cond_tok = df.groupby("condition_id").apply(
    lambda x: np.median([r["output_tokens"] for r in x["usage"]])
).reset_index()
cond_tok.columns = ["condition_id", "cond_output_tok_p50"]
df = df.merge(cond_tok, on="condition_id", how="left")

# Baseline correctness flags (available if you run baseline first)
baseline_rows = df[df["condition_id"] == "pro_baseline"][["sample_id", "correct_l3"]].copy()
baseline_rows.columns = ["sample_id", "pro_baseline_correct"]
flash_baseline = pd.DataFrame(records)
flash_baseline = flash_baseline[
    (flash_baseline["model"] == "deepseek-v4-flash") &
    (flash_baseline["condition_id"] == "flash_baseline") &
    (flash_baseline["parse_success"] == True)
].copy()
flash_baseline["gt_l3"] = flash_baseline["ground_truth"].apply(lambda g: g["L3_symbolic_checker"])
flash_baseline["predicted_yes"] = flash_baseline["parsed_label"] == "YES"
flash_baseline["flash_baseline_correct"] = flash_baseline["predicted_yes"] == flash_baseline["gt_l3"]
flash_baseline = flash_baseline[["sample_id", "flash_baseline_correct"]]

df = df.merge(baseline_rows, on="sample_id", how="left")
df = df.merge(flash_baseline, on="sample_id", how="left")
df = df.merge(chain_stats, on="sample_id", how="left")
df = df.merge(chain_vtype, on="sample_id", how="left")

# Per-record output tokens (NOT deployment-time — only available after running)
df["record_output_tokens"] = df["usage"].apply(lambda u: u["output_tokens"])

# ─── Feature split: deployment-time vs evaluation-time ───────────────────────

DEPLOYMENT_TIME_FEATURES = [
    # Condition config — known before any API call
    "lever_num",
    "level_num",
    "thinking_enabled",
    "function_calling",
    "max_tokens",
    "k_steps",
    "cond_output_tok_p50",      # historical median for this condition
    # Baseline correctness — available if baseline is run first (conditional)
    "pro_baseline_correct",
    "flash_baseline_correct",
]

EVAL_TIME_ONLY = [
    "record_output_tokens",     # actual tokens for this call (post-call)
    "chain_mean_output_tokens",  # mean across all conditions (requires all calls)
    "is_intact",                # ground truth!
    "vtype_causal_incoherence", # ground truth!
    "vtype_hp_resurrection",
    "vtype_monotone_increase",
    "vtype_multiple",
    "vtype_none",
]

FULL_FEATURE_SET = DEPLOYMENT_TIME_FEATURES + [
    "record_output_tokens",
    "chain_mean_output_tokens",
    "is_intact",
    "vtype_causal_incoherence",
    "vtype_hp_resurrection",
    "vtype_monotone_increase",
    "vtype_multiple",
    "vtype_none",
]

# Exclude baseline condition from modeling (it's used to compute baseline features)
df_model = df[~df["condition_id"].isin(["pro_baseline", "flash_baseline"])].copy()
df_model = df_model.dropna(subset=DEPLOYMENT_TIME_FEATURES + ["correct_l3"])
df_model[DEPLOYMENT_TIME_FEATURES] = df_model[DEPLOYMENT_TIME_FEATURES].fillna(0)
df_model["pro_baseline_correct"] = df_model["pro_baseline_correct"].astype(float).fillna(0)
df_model["flash_baseline_correct"] = df_model["flash_baseline_correct"].astype(float).fillna(0)

y = df_model["correct_l3"].astype(int)
X_deploy = df_model[DEPLOYMENT_TIME_FEATURES]

# Train / test split: stratified by condition (80/20, seed=42)
X_tr, X_te, y_tr, y_te = train_test_split(
    X_deploy, y, test_size=0.20, random_state=42, stratify=df_model["condition_id"]
)

# ─── Train deployment-time classifiers ────────────────────────────────────────
results = {}

lr = LogisticRegression(max_iter=1000, random_state=42)
lr.fit(X_tr, y_tr)
lr_probs = lr.predict_proba(X_te)[:, 1]
results["logistic_regression"] = {
    "auc": roc_auc_score(y_te, lr_probs),
    "accuracy": accuracy_score(y_te, lr.predict(X_te)),
    "f1": f1_score(y_te, lr.predict(X_te)),
}

rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_tr, y_tr)
rf_probs = rf.predict_proba(X_te)[:, 1]
results["random_forest"] = {
    "auc": roc_auc_score(y_te, rf_probs),
    "accuracy": accuracy_score(y_te, rf.predict(X_te)),
    "f1": f1_score(y_te, rf.predict(X_te)),
    "feature_importances": dict(zip(DEPLOYMENT_TIME_FEATURES, rf.feature_importances_)),
}

gb = GradientBoostingClassifier(n_estimators=100, random_state=42)
gb.fit(X_tr, y_tr)
gb_probs = gb.predict_proba(X_te)[:, 1]
results["gradient_boosting"] = {
    "auc": roc_auc_score(y_te, gb_probs),
    "accuracy": accuracy_score(y_te, gb.predict(X_te)),
    "f1": f1_score(y_te, gb.predict(X_te)),
}

# Calibration for best model (RF)
frac_pos, mean_pred = calibration_curve(y_te, rf_probs, n_bins=5)
results["random_forest"]["calibration"] = {
    "mean_predicted_proba": mean_pred.tolist(),
    "fraction_positives": frac_pos.tolist(),
}

# Threshold analysis for deployment predictor
thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]
threshold_analysis = {}
for t in thresholds:
    pred = (rf_probs >= t).astype(int)
    n_flagged = int(pred.sum())
    n_correct_flagged = int(((pred == 1) & (y_te.values == 1)).sum()) if n_flagged > 0 else 0
    # precision at threshold
    prec = n_correct_flagged / n_flagged if n_flagged > 0 else 0
    threshold_analysis[t] = {
        "n_flagged_as_likely_correct": n_flagged,
        "precision": round(prec, 3),
        "n_test_records": len(y_te),
    }
results["random_forest"]["threshold_analysis"] = threshold_analysis

# ─── Full-feature model AUC (Test 6 baseline comparison) ─────────────────────
try:
    full_rf = joblib.load(FULL_RF)
    full_feat_names = [
        "lever_num", "level_num", "thinking_enabled", "function_calling",
        "max_tokens", "k_steps", "cond_output_tok_p50",
        "record_output_tokens", "chain_mean_output_tokens",
        "is_intact", "flash_baseline_correct",
        "vtype_none", "vtype_causal_incoherence", "vtype_hp_resurrection",
        "vtype_monotone_increase", "vtype_multiple",
        "pro_baseline_correct",
    ]
    results["full_feature_rf_auc_from_test6"] = 0.925
    results["full_feature_comparison_note"] = (
        "Test 6 full-feature RF AUC=0.925 used 17 features including "
        "evaluation-time features (record_output_tokens, chain_mean_output_tokens, "
        "is_intact, vtype_*). Deployment-time predictor uses only the 9 condition "
        "and baseline-run features available before executing the detection call."
    )
except Exception as e:
    results["full_feature_rf_auc_from_test6"] = "load_error"

# ─── Save outputs ─────────────────────────────────────────────────────────────
out_dir = Path(__file__).parent
with open(out_dir / "results.json", "w") as f:
    json.dump(results, f, indent=2)

# Print summary
print("=" * 60)
print("DEPLOYMENT-TIME PREDICTOR RESULTS")
print("=" * 60)
print(f"\nTest 6 full-feature RF AUC:  0.925 (baseline)")
print(f"\nDeployment-time predictors (9 features, no ground truth):")
for name, r in results.items():
    if isinstance(r, dict) and "auc" in r:
        print(f"  {name:25s}  AUC={r['auc']:.3f}  Acc={r['accuracy']:.3f}  F1={r['f1']:.3f}")

print("\nRF feature importances (deployment-time features):")
for feat, imp in sorted(results["random_forest"]["feature_importances"].items(),
                         key=lambda x: -x[1]):
    print(f"  {feat:35s} {imp:.4f}")

print("\nRF calibration (mean_pred → frac_pos):")
for mp, fp in zip(results["random_forest"]["calibration"]["mean_predicted_proba"],
                  results["random_forest"]["calibration"]["fraction_positives"]):
    print(f"  predicted {mp:.2f} → actual {fp:.2f}")

print("\nRF threshold analysis:")
for t, ta in results["random_forest"]["threshold_analysis"].items():
    print(f"  threshold={t}  flagged={ta['n_flagged_as_likely_correct']}  precision={ta['precision']}")
