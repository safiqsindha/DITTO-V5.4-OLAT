#!/usr/bin/env python3
"""
Task 1: Bimodal Quartile Analysis for L18 L2/L3 conditions.

Breaks down effect_size by output_tokens quartile for:
  flash_L18_L2, flash_L18_L3, pro_L18_L2, pro_L18_L3
across all three universes (L1, L2, L3).

Outputs:
  day_2/quartile_analysis/quartile_breakdown_full.csv
  day_2/quartile_analysis/bimodal_summary.md

SPEC hash: dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8
"""

import json
import csv
import os
import math
import random
import numpy as np
from pathlib import Path

SPEC_HASH = "dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8"

PROVENANCE_PATH = Path("/Users/safiqsindha/Desktop/Project Ditto/Ditto-5.4-OLAT/pre-registration/parser_provenance.ndjson")
DAY2_DIR = Path("/Users/safiqsindha/Desktop/Project Ditto/Ditto-5.4-OLAT/pre-registration/day_2")
OUT_DIR = DAY2_DIR / "quartile_analysis"
OUT_DIR.mkdir(exist_ok=True)

UNIVERSE_KEY = {
    "L1": "L1_shuffled_vs_real",
    "L2": "L2_planted_violations",
    "L3": "L3_symbolic_checker",
}

# Baseline gaps from the Day 2 effect tables (fixed, not re-computed)
BASELINE_GAPS = {
    ("flash", "L1"): 0.0,
    ("flash", "L2"): 0.0,
    ("flash", "L3"): 0.0,
    ("pro", "L1"): -0.0037,
    ("pro", "L2"): -0.0037,
    ("pro", "L3"): -0.0799,
}

TARGET_CONDITIONS = ["flash_L18_L2", "flash_L18_L3", "pro_L18_L2", "pro_L18_L3"]

# Seeds per SPEC §9 / Bootstrap convention
SEEDS = {"flash": 42, "pro": 43}

N_BOOT = 10_000

BIMODAL_THRESHOLD = 0.20  # |effect(Q1) - effect(Q4)| >= 0.20 AND opposite signs


def classify(effect, ci_lo, ci_hi):
    abs_e = abs(effect)
    ci_crosses_zero = ci_lo <= 0 <= ci_hi
    if abs_e >= 0.10:
        label = "Meaningful"
    elif abs_e >= 0.03:
        label = "Directional"
    else:
        label = "Null"
    if ci_crosses_zero and label != "Null":
        label += "(no_CI)"
    return label


def bca_ci(data, stat_fn, n_boot, seed, alpha=0.05):
    """BCa bootstrap CI. data is a list of records; stat_fn computes the statistic."""
    rng = random.Random(seed)
    n = len(data)
    if n == 0:
        return float("nan"), float("nan"), float("nan")

    observed = stat_fn(data)
    if math.isnan(observed):
        return observed, float("nan"), float("nan")

    # Bootstrap replicates
    boot_stats = []
    for _ in range(n_boot):
        sample = [data[rng.randint(0, n - 1)] for _ in range(n)]
        s = stat_fn(sample)
        if not math.isnan(s):
            boot_stats.append(s)

    if len(boot_stats) < 10:
        return observed, float("nan"), float("nan")

    boot_stats.sort()
    B = len(boot_stats)

    # Bias correction z0
    count_less = sum(1 for s in boot_stats if s < observed)
    if count_less == 0:
        count_less = 0.5
    elif count_less == B:
        count_less = B - 0.5
    z0 = _norm_ppf(count_less / B)

    # Jackknife acceleration
    jack_stats = []
    for i in range(n):
        leave_one_out = data[:i] + data[i + 1:]
        if leave_one_out:
            jack_stats.append(stat_fn(leave_one_out))
    jack_mean = sum(s for s in jack_stats if not math.isnan(s)) / max(1, sum(1 for s in jack_stats if not math.isnan(s)))
    diffs = [(jack_mean - s) for s in jack_stats if not math.isnan(s)]
    num = sum(d ** 3 for d in diffs)
    den = 6 * (sum(d ** 2 for d in diffs) ** 1.5)
    accel = num / den if abs(den) > 1e-12 else 0.0

    def adj_pct(alpha_side):
        z_a = _norm_ppf(alpha_side)
        z_adj = z0 + (z0 + z_a) / (1 - accel * (z0 + z_a))
        p = _norm_cdf(z_adj)
        p = max(0.001, min(0.999, p))
        return p

    lo_pct = adj_pct(alpha / 2)
    hi_pct = adj_pct(1 - alpha / 2)

    lo_idx = max(0, int(lo_pct * B) - 1)
    hi_idx = min(B - 1, int(hi_pct * B))
    return observed, boot_stats[lo_idx], boot_stats[hi_idx]


def _norm_ppf(p):
    """Inverse normal CDF (Beasley-Springer-Moro approximation)."""
    p = max(1e-10, min(1 - 1e-10, p))
    if p == 0.5:
        return 0.0
    a = [0, -3.969683028665376e+01, 2.209460984245205e+02,
         -2.759285104469687e+02, 1.383577518672690e+02,
         -3.066479806614716e+01, 2.506628277459239e+00]
    b = [0, -5.447609879822406e+01, 1.615858368580409e+02,
         -1.556989798598866e+02, 6.680131188771972e+01, -1.328068155288572e+01]
    c = [0, -7.784894002430293e-03, -3.223964580411365e-01,
         -2.400758277161838e+00, -2.549732539343734e+00,
         4.374664141464968e+00, 2.938163982698783e+00]
    d = [0, 7.784695709041462e-03, 3.224671290700398e-01,
         2.445134137142996e+00, 3.754408661907416e+00]
    p_low = 0.02425
    p_high = 1 - p_low
    if p < p_low:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[1]*q+c[2])*q+c[3])*q+c[4])*q+c[5])*q+c[6]) / \
               ((((d[1]*q+d[2])*q+d[3])*q+d[4])*q+1)
    elif p <= p_high:
        q = p - 0.5
        r = q * q
        return (((((a[1]*r+a[2])*r+a[3])*r+a[4])*r+a[5])*r+a[6])*q / \
               (((((b[1]*r+b[2])*r+b[3])*r+b[4])*r+b[5])*r+1)
    else:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[1]*q+c[2])*q+c[3])*q+c[4])*q+c[5])*q+c[6]) / \
                ((((d[1]*q+d[2])*q+d[3])*q+d[4])*q+1)


def _norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def gap_stat(records, universe_key):
    """Compute gap = dr_violated - dr_intact for a list of records under given universe."""
    violated = [r for r in records if r["ground_truth"].get(universe_key) is True
                and r.get("parse_success") and not r.get("api_failure")]
    intact = [r for r in records if r["ground_truth"].get(universe_key) is False
              and r.get("parse_success") and not r.get("api_failure")]
    if not violated or not intact:
        return float("nan")
    dr_v = sum(1 for r in violated if r.get("parsed_label") == "YES") / len(violated)
    dr_i = sum(1 for r in intact if r.get("parsed_label") == "YES") / len(intact)
    return dr_v - dr_i


def analyze_quartile(records, universe_key, baseline_gap, model_key, quartile_label):
    """Compute all metrics for a single quartile block."""
    uk = universe_key
    valid = [r for r in records if not r.get("api_failure")]
    violated = [r for r in valid if r["ground_truth"].get(uk) is True]
    intact = [r for r in valid if r["ground_truth"].get(uk) is False]
    parsed_violated = [r for r in violated if r.get("parse_success")]
    parsed_intact = [r for r in intact if r.get("parse_success")]

    n_total = len(records)
    n_valid = len(valid)
    n_violated = len(violated)
    n_intact = len(intact)
    n_parsed_violated = len(parsed_violated)
    n_parsed_intact = len(parsed_intact)

    if not parsed_violated or not parsed_intact:
        return {
            "n_total": n_total, "n_valid": n_valid,
            "n_violated": n_violated, "n_intact": n_intact,
            "n_parsed_violated": n_parsed_violated, "n_parsed_intact": n_parsed_intact,
            "dr_violated": float("nan"), "dr_intact": float("nan"),
            "gap": float("nan"), "effect_size": float("nan"),
            "ci_lo": float("nan"), "ci_hi": float("nan"),
            "classification": "Unknown",
            "parse_failure_rate": float("nan"),
        }

    dr_v = sum(1 for r in parsed_violated if r.get("parsed_label") == "YES") / len(parsed_violated)
    dr_i = sum(1 for r in parsed_intact if r.get("parsed_label") == "YES") / len(parsed_intact)
    gap = dr_v - dr_i
    effect_size = gap - baseline_gap

    # BCa CI on effect_size via bootstrapping the gap
    seed = SEEDS[model_key]

    def stat_fn(boot_records):
        boot_v = [r for r in boot_records if r["ground_truth"].get(uk) is True and r.get("parse_success")]
        boot_i = [r for r in boot_records if r["ground_truth"].get(uk) is False and r.get("parse_success")]
        if not boot_v or not boot_i:
            return float("nan")
        bdr_v = sum(1 for r in boot_v if r.get("parsed_label") == "YES") / len(boot_v)
        bdr_i = sum(1 for r in boot_i if r.get("parsed_label") == "YES") / len(boot_i)
        return (bdr_v - bdr_i) - baseline_gap

    obs, ci_lo, ci_hi = bca_ci(valid, stat_fn, N_BOOT, seed)
    classification = classify(effect_size, ci_lo, ci_hi)

    # Parse failure rate
    n_parse_fail = sum(1 for r in valid if not r.get("api_failure") and not r.get("parse_success"))
    parse_failure_rate = n_parse_fail / n_valid if n_valid > 0 else float("nan")

    return {
        "n_total": n_total, "n_valid": n_valid,
        "n_violated": n_violated, "n_intact": n_intact,
        "n_parsed_violated": n_parsed_violated, "n_parsed_intact": n_parsed_intact,
        "dr_violated": round(dr_v, 4), "dr_intact": round(dr_i, 4),
        "gap": round(gap, 4), "effect_size": round(effect_size, 4),
        "ci_lo": round(ci_lo, 4) if not math.isnan(ci_lo) else float("nan"),
        "ci_hi": round(ci_hi, 4) if not math.isnan(ci_hi) else float("nan"),
        "classification": classification,
        "parse_failure_rate": round(parse_failure_rate, 4),
    }


def main():
    # Load provenance
    records = []
    with open(PROVENANCE_PATH) as f:
        for line in f:
            records.append(json.loads(line))

    print(f"Loaded {len(records)} provenance records.")

    # Filter to target conditions
    cond_records = {c: [r for r in records if r["condition_id"] == c]
                    for c in TARGET_CONDITIONS}
    for c, recs in cond_records.items():
        print(f"  {c}: {len(recs)} records")

    csv_rows = []
    bimodal_flags = {}  # (cond, universe) -> {Q1_effect, Q4_effect, is_bimodal}
    qualitative_samples = {}  # (cond, universe) -> {Q1: [...], Q4: [...]}

    for cond in TARGET_CONDITIONS:
        model_key = "flash" if cond.startswith("flash") else "pro"
        recs = cond_records[cond]

        # Sort by output_tokens
        recs_sorted = sorted(recs, key=lambda r: r.get("usage", {}).get("output_tokens", 0))
        token_vals = [r.get("usage", {}).get("output_tokens", 0) for r in recs_sorted]
        n = len(recs_sorted)

        # Quartile boundaries (indices)
        q_size = n // 4
        q_bounds_idx = [0, q_size, 2 * q_size, 3 * q_size, n]
        # Make sure last quartile picks up remainder
        q_bounds_idx[4] = n

        quartile_recs = []
        for q in range(4):
            start = q_bounds_idx[q]
            end = q_bounds_idx[q + 1]
            q_recs = recs_sorted[start:end]
            tok_min = token_vals[start] if start < n else 0
            tok_max = token_vals[end - 1] if end - 1 < n else 0
            quartile_recs.append((q + 1, tok_min, tok_max, q_recs))

        print(f"\n{cond} quartile token ranges:")
        for q_num, tok_min, tok_max, q_recs in quartile_recs:
            print(f"  Q{q_num}: tokens {tok_min}–{tok_max}, n={len(q_recs)}")

        for universe in ["L1", "L2", "L3"]:
            uk = UNIVERSE_KEY[universe]
            baseline_gap = BASELINE_GAPS[(model_key, universe)]

            q_effects = {}
            for q_num, tok_min, tok_max, q_recs in quartile_recs:
                metrics = analyze_quartile(q_recs, uk, baseline_gap, model_key, f"Q{q_num}")

                row = {
                    "condition_id": cond,
                    "model": model_key,
                    "universe": universe,
                    "quartile": f"Q{q_num}",
                    "token_min": tok_min,
                    "token_max": tok_max,
                    **metrics,
                    "baseline_gap": round(baseline_gap, 4),
                }
                csv_rows.append(row)
                q_effects[f"Q{q_num}"] = metrics["effect_size"]

            # Bimodal flag
            q1_e = q_effects.get("Q1", float("nan"))
            q4_e = q_effects.get("Q4", float("nan"))
            if not math.isnan(q1_e) and not math.isnan(q4_e):
                diff = abs(q1_e - q4_e)
                opposite = (q1_e < 0 < q4_e) or (q4_e < 0 < q1_e)
                is_bimodal = diff >= BIMODAL_THRESHOLD and opposite
            else:
                diff = float("nan")
                opposite = False
                is_bimodal = False

            bimodal_flags[(cond, universe)] = {
                "Q1_effect": q1_e, "Q4_effect": q4_e,
                "diff": diff, "opposite_signs": opposite,
                "is_bimodal": is_bimodal,
            }
            if is_bimodal:
                print(f"  ** BIMODAL: {cond} × {universe}: Q1={q1_e:.3f}, Q4={q4_e:.3f}, diff={diff:.3f}")

            # Collect qualitative samples for bimodal conditions
            if is_bimodal:
                uk_val = UNIVERSE_KEY[universe]
                q1_recs = quartile_recs[0][3]
                q4_recs = quartile_recs[3][3]
                seed = SEEDS[model_key]
                rng = random.Random(seed + 1)  # +1 to avoid collision with bootstrap

                def sample3(pool):
                    valid_pool = [r for r in pool if not r.get("api_failure") and r.get("parse_success")]
                    if not valid_pool:
                        valid_pool = pool
                    rng.shuffle(valid_pool)
                    return valid_pool[:3]

                qualitative_samples[(cond, universe)] = {
                    "Q1": sample3(q1_recs[:]),
                    "Q4": sample3(q4_recs[:]),
                }

    # Write CSV
    csv_path = OUT_DIR / "quartile_breakdown_full.csv"
    fieldnames = [
        "condition_id", "model", "universe", "quartile",
        "token_min", "token_max",
        "n_total", "n_valid", "n_violated", "n_intact",
        "n_parsed_violated", "n_parsed_intact",
        "dr_violated", "dr_intact", "gap", "baseline_gap",
        "effect_size", "ci_lo", "ci_hi",
        "classification", "parse_failure_rate",
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in csv_rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    print(f"\nWrote {len(csv_rows)} rows to {csv_path}")

    # Write bimodal summary markdown
    write_bimodal_summary(csv_rows, bimodal_flags, qualitative_samples, quartile_recs_all=None)


def write_bimodal_summary(csv_rows, bimodal_flags, qualitative_samples, quartile_recs_all):
    lines = []
    lines.append("# Task 1: Bimodal Quartile Analysis — L18 L2/L3 Conditions")
    lines.append("")
    lines.append(f"**SPEC hash:** `{SPEC_HASH}`  ")
    lines.append("**Generated:** 2026-05-13  ")
    lines.append("**Quartile basis:** `usage.output_tokens` (completion tokens), NOT character length  ")
    lines.append("**Bootstrap:** BCa, 10K iterations; seed=42 (Flash), seed=43 (Pro)  ")
    lines.append("**Bimodal criterion:** |effect(Q1) − effect(Q4)| ≥ 0.20 AND opposite signs  ")
    lines.append("**Baseline gaps:** flash L1/L2/L3 = 0.0; pro L1 = −0.0037, pro L2 = −0.0037, pro L3 = −0.0799  ")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary table of bimodal flags
    lines.append("## Bimodal Flag Summary")
    lines.append("")
    lines.append("| Condition | Universe | Q1 effect | Q4 effect | |diff| | Opposite signs | Bimodal? |")
    lines.append("|---|---|---|---|---|---|---|")
    for cond in TARGET_CONDITIONS:
        for universe in ["L1", "L2", "L3"]:
            bf = bimodal_flags.get((cond, universe), {})
            q1_e = bf.get("Q1_effect", float("nan"))
            q4_e = bf.get("Q4_effect", float("nan"))
            diff = bf.get("diff", float("nan"))
            opp = bf.get("opposite_signs", False)
            bim = bf.get("is_bimodal", False)
            q1_s = f"{q1_e:.3f}" if not math.isnan(q1_e) else "nan"
            q4_s = f"{q4_e:.3f}" if not math.isnan(q4_e) else "nan"
            diff_s = f"{diff:.3f}" if not math.isnan(diff) else "nan"
            bim_s = "**YES**" if bim else "No"
            lines.append(f"| {cond} | {universe} | {q1_s} | {q4_s} | {diff_s} | {'Yes' if opp else 'No'} | {bim_s} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Per-condition × universe breakdown tables
    lines.append("## Per-Condition Quartile Breakdown")
    lines.append("")

    # Reorganize csv_rows by (cond, universe)
    from collections import defaultdict
    by_cond_univ = defaultdict(list)
    for row in csv_rows:
        by_cond_univ[(row["condition_id"], row["universe"])].append(row)

    for cond in TARGET_CONDITIONS:
        lines.append(f"### {cond}")
        lines.append("")
        for universe in ["L1", "L2", "L3"]:
            rows = by_cond_univ.get((cond, universe), [])
            bf = bimodal_flags.get((cond, universe), {})
            bim_label = " ← **BIMODAL**" if bf.get("is_bimodal") else ""
            lines.append(f"#### Universe {universe}{bim_label}")
            lines.append("")
            lines.append("| Quartile | Tokens | n_violated | n_intact | dr_violated | dr_intact | gap | effect_size | CI | Classification |")
            lines.append("|---|---|---|---|---|---|---|---|---|---|")
            for row in rows:
                q = row["quartile"]
                tok = f"{row['token_min']}–{row['token_max']}"
                nv = row["n_parsed_violated"]
                ni = row["n_parsed_intact"]
                drv = row["dr_violated"]
                dri = row["dr_intact"]
                gap = row["gap"]
                eff = row["effect_size"]
                ci_lo = row["ci_lo"]
                ci_hi = row["ci_hi"]
                ci_s = f"[{ci_lo}, {ci_hi}]" if ci_lo != "" and ci_hi != "" else "—"
                cls = row["classification"]
                lines.append(f"| {q} | {tok} | {nv} | {ni} | {drv} | {dri} | {gap} | {eff} | {ci_s} | {cls} |")
            lines.append("")

            if bf.get("is_bimodal"):
                lines.append(f"**Bimodal pattern detected:** Q1={bf['Q1_effect']:.3f}, Q4={bf['Q4_effect']:.3f}. Shorter responses show {'negative' if bf['Q1_effect'] < 0 else 'positive'} gap; longer responses show {'positive' if bf['Q4_effect'] > 0 else 'negative'} gap.")
                lines.append("")

    # Qualitative review for bimodal conditions
    bimodal_conds = [(c, u) for (c, u), bf in bimodal_flags.items() if bf.get("is_bimodal")]
    if bimodal_conds:
        lines.append("---")
        lines.append("")
        lines.append("## Qualitative Review — Bimodal Conditions")
        lines.append("")
        lines.append("3 Q1 records (shortest responses) + 3 Q4 records (longest responses) per bimodal condition.")
        lines.append("")

        for cond, universe in sorted(bimodal_conds):
            lines.append(f"### {cond} × Universe {universe}")
            lines.append("")
            samples = qualitative_samples.get((cond, universe), {})
            for q_label in ["Q1", "Q4"]:
                q_samples = samples.get(q_label, [])
                lines.append(f"#### {q_label} Records (shortest responses)" if q_label == "Q1" else f"#### {q_label} Records (longest responses)")
                lines.append("")
                if not q_samples:
                    lines.append("*(no valid samples)*")
                    lines.append("")
                    continue
                for i, r in enumerate(q_samples, 1):
                    tok = r.get("usage", {}).get("output_tokens", "?")
                    label = r.get("parsed_label", "?")
                    gt = r.get("ground_truth", {}).get(UNIVERSE_KEY[universe], "?")
                    gt_label = "violated" if gt is True else "intact" if gt is False else str(gt)
                    raw = str(r.get("raw_output", ""))[:300].replace("\n", " ")
                    lines.append(f"**Record {i}** — chain={r.get('sample_id', '?')[:40]}, tokens={tok}, label={label}, ground_truth={gt_label}")
                    lines.append(f"> {raw}{'...' if len(str(r.get('raw_output', ''))) > 300 else ''}")
                    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Replication Check: pro_L18_L3 × L3 Bimodal Pattern")
    lines.append("")
    lines.append("Day 2 S6 used **character length** quartiles; this analysis uses **completion tokens**.")
    lines.append("Day 2 S6 values: Q1=−0.214, Q2=−0.300, Q3=0.833, Q4=0.389")

    # Find pro_L18_L3 × L3 rows
    pro_l18_l3_rows = [r for r in csv_rows if r["condition_id"] == "pro_L18_L3" and r["universe"] == "L3"]
    lines.append("")
    lines.append("Completion-token quartile values:")
    for row in pro_l18_l3_rows:
        lines.append(f"- {row['quartile']}: effect={row['effect_size']} (tokens {row['token_min']}–{row['token_max']})")

    bf_check = bimodal_flags.get(("pro_L18_L3", "L3"), {})
    replicates = bf_check.get("is_bimodal", False)
    lines.append("")
    if replicates:
        lines.append("**Bimodal pattern REPLICATES** under completion-token quartile split.")
    else:
        lines.append("**Bimodal pattern does NOT replicate** under completion-token quartile split. This discrepancy requires both-author attention — the Day 2 S6 character-length finding may not hold under token-based quartiles.")

    out_path = Path("/Users/safiqsindha/Desktop/Project Ditto/Ditto-5.4-OLAT/pre-registration/day_2/quartile_analysis/bimodal_summary.md")
    out_path.write_text("\n".join(lines))
    print(f"Wrote bimodal summary to {out_path}")


if __name__ == "__main__":
    main()
