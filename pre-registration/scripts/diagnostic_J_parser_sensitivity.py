"""
Diagnostic J — Parser sensitivity analysis on existing raw response corpus.

Three experiments, zero API cost:
  E1: Parser cascade depth comparison (P1...P5)
  E2: Parser strictness sensitivity (S1 exact / S2 flexible / S3 relaxed)
  E3: Per-stage rescue inspection set (30 v1-missed-but-v2-caught samples)

Operates on the ~440 raw responses preserved across Day -2 (k=15), Diag F, G, H,
and Diag I (Flash + Pro). Each response has ground truth labeled via chain_id.

Outputs to pre-registration/diagnostics/parser_sensitivity/:
  E1_cascade_depth.json + markdown table
  E2_strictness.json   + markdown table
  E3_rescue_inspection.md  (human-readable for manual labeling)
  diagnostic_J_summary.md
"""

from __future__ import annotations

import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DIAG_DIR = REPO_ROOT / "pre-registration" / "diagnostics"
DAY_M2_DIR = REPO_ROOT / "pre-registration" / "day_minus_2"
OUT_DIR = DIAG_DIR / "parser_sensitivity"

DATASETS = [
    # (file_path, config_label, model, cot_flag, max_tokens)
    (DAY_M2_DIR / "raw_responses.ndjson",                          "day-2_flash_v1min_32",  "v4-flash", False, 32),
    (DIAG_DIR / "diagnostic_F_cot_flash_raw.ndjson",                "F_flash_cot_512",        "v4-flash", True,  512),
    (DIAG_DIR / "diagnostic_G_v4pro_baseline_raw.ndjson",           "G_pro_v1min_32",         "v4-pro",   False, 32),
    (DIAG_DIR / "diagnostic_H_cot_v4pro_raw.ndjson",                "H_pro_cot_512",          "v4-pro",   True,  512),
    (DIAG_DIR / "diagnostic_I_flash_raw.ndjson",                    "I_flash_cot_4096",       "v4-flash", True,  4096),
    (DIAG_DIR / "diagnostic_I_pro_raw.ndjson",                      "I_pro_cot_4096",         "v4-pro",   True,  4096),
]


# ---------------------------------------------------------------------------
# Parser implementations
# ---------------------------------------------------------------------------

MD_DECOR = re.compile(r"[\*_`]+")


# E1 Cascade stages
def _strict_match(s):
    pat = re.compile(r"(?:Therefore,\s+)?[Tt]he answer is\s+(YES|NO)\b", re.IGNORECASE)
    if m := pat.search(s):
        return m.group(1).upper()
    return None


def _permissive_match(s):
    pat = re.compile(r"(?i)(?:answer is|answer:|conclusion:)\s*(yes|no)\b")
    if m := pat.search(s):
        return m.group(1).upper()
    return None


def _markdown_strip_match(s):
    # Strip markdown decoration, then try permissive
    s_clean = MD_DECOR.sub("", s)
    return _permissive_match(s_clean)


def _last_token_match(s):
    # Last 200 chars, strip decoration, look for trailing yes/no
    s_clean = MD_DECOR.sub("", s)
    tail = s_clean[-200:].strip()
    pat = re.compile(r"(?i)(YES|NO)\b[\s\.\,\!\?\)]*\s*$")
    if m := pat.search(tail):
        return m.group(1).upper()
    return None


def _first_token_match(s):
    head_clean = MD_DECOR.sub("", " ".join(s.split()[:10]))
    pat = re.compile(r"^[\W]*(YES|NO)\b", re.IGNORECASE)
    if m := pat.search(head_clean):
        return m.group(1).upper()
    return None


# E1 cascade variants (each variant = a list of stages tried in order)
CASCADES = {
    "P1_strict_only": [("strict", _strict_match)],
    "P2_strict_permissive": [
        ("strict", _strict_match),
        ("permissive", _permissive_match),
    ],
    "P3_v2_md_tolerant": [
        ("strict", _strict_match),
        ("permissive", _permissive_match),
        ("md_strip", _markdown_strip_match),
    ],
    "P4_plus_last_token": [
        ("strict", _strict_match),
        ("permissive", _permissive_match),
        ("md_strip", _markdown_strip_match),
        ("last_token", _last_token_match),
    ],
    "P5_plus_first_token": [
        ("strict", _strict_match),
        ("permissive", _permissive_match),
        ("md_strip", _markdown_strip_match),
        ("last_token", _last_token_match),
        ("first_token", _first_token_match),
    ],
}


def run_cascade(cascade, text):
    if not text:
        return None, "unparseable"
    s = text.strip()
    for stage_name, fn in cascade:
        if (label := fn(s)) is not None:
            return label, stage_name
    return None, "unparseable"


# E2 strictness — single-regex variants (no cascade)
def _s1_anchor_exact(s):
    pat = re.compile(r"Therefore, the answer is (YES|NO)")
    return pat.search(s).group(1) if pat.search(s) else None


def _s2_anchor_flexible(s):
    pat = re.compile(r"(?:Therefore,?\s+)?[Tt]he\s+answer\s+(?:is\s+)?(YES|NO)", re.IGNORECASE)
    s_clean = MD_DECOR.sub("", s)
    m = pat.search(s_clean)
    return m.group(1).upper() if m else None


def _s3_anchor_relaxed(s):
    """Any sentence containing 'answer' within 40 chars of 'yes' or 'no'."""
    s_clean = MD_DECOR.sub("", s).lower()
    # Find every occurrence of 'answer', look in window after it
    answers = []
    for m in re.finditer(r"answer", s_clean):
        window = s_clean[m.start():m.start() + 60]
        if (ym := re.search(r"\byes\b", window)):
            answers.append(("YES", m.start() + ym.start()))
        if (nm := re.search(r"\bno\b", window)):
            answers.append(("NO", m.start() + nm.start()))
    if not answers:
        return None
    # Take the LAST one (most likely to be the final answer)
    answers.sort(key=lambda x: x[1])
    return answers[-1][0]


STRICTNESS = {
    "S1_anchor_exact": _s1_anchor_exact,
    "S2_anchor_flexible": _s2_anchor_flexible,
    "S3_anchor_relaxed": _s3_anchor_relaxed,
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_all():
    """Load every response, tagging by config_label."""
    all_rows = []
    for path, config, model, cot, max_t in DATASETS:
        if not path.exists():
            print(f"WARN missing: {path}")
            continue
        for line in path.open():
            r = json.loads(line)
            r["_config"] = config
            r["_model"] = model
            r["_cot"] = cot
            r["_max_tokens"] = max_t
            # Normalize ground_truth fields
            if "ground_truth_label" not in r:
                r["ground_truth_label"] = "YES" if r["ground_truth"] == "violated" else "NO"
            all_rows.append(r)
    return all_rows


# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------

def compute_metrics(rows, parsed_labels):
    """Compute parsed_rate, det_intact, det_violated, gap given a list of (row, parsed_label)."""
    n = len(rows)
    parsed = [(r, p) for r, p in zip(rows, parsed_labels) if p is not None]
    parsed_rate = len(parsed) / n if n else 0.0

    intact_correct = [1 if p == r["ground_truth_label"] else 0 for r, p in parsed if r["ground_truth"] == "intact"]
    violated_correct = [1 if p == r["ground_truth_label"] else 0 for r, p in parsed if r["ground_truth"] == "violated"]

    det_intact = (sum(intact_correct) / len(intact_correct)) if intact_correct else None
    det_violated = (sum(violated_correct) / len(violated_correct)) if violated_correct else None
    gap = (det_violated - det_intact) if (det_intact is not None and det_violated is not None) else None

    return {
        "n": n,
        "n_parsed": len(parsed),
        "parsed_rate": parsed_rate,
        "n_intact_parsed": len(intact_correct),
        "n_violated_parsed": len(violated_correct),
        "det_intact": det_intact,
        "det_violated": det_violated,
        "gap": gap,
    }


# ---------------------------------------------------------------------------
# E1 — Cascade depth
# ---------------------------------------------------------------------------

def experiment_1(all_rows):
    print("\n" + "=" * 72)
    print("E1 — Parser cascade depth comparison")
    print("=" * 72)

    configs = sorted({r["_config"] for r in all_rows})

    e1_results = {}
    for cascade_name, cascade in CASCADES.items():
        e1_results[cascade_name] = {}
        # Parse every row with this cascade
        parsed_labels = [run_cascade(cascade, r["raw_response"])[0] for r in all_rows]
        e1_results[cascade_name]["overall"] = compute_metrics(all_rows, parsed_labels)
        # Per-config slice
        for cfg in configs:
            sub_idx = [i for i, r in enumerate(all_rows) if r["_config"] == cfg]
            sub_rows = [all_rows[i] for i in sub_idx]
            sub_labels = [parsed_labels[i] for i in sub_idx]
            e1_results[cascade_name][cfg] = compute_metrics(sub_rows, sub_labels)

    # Print overall + per-config table
    print(f"\n{'Cascade':<24} {'parsed%':>8} {'n_par':>6} {'det_int':>8} {'det_vio':>8} {'gap':>8}")
    print("-" * 72)
    for cascade_name in CASCADES:
        m = e1_results[cascade_name]["overall"]
        det_i = f"{m['det_intact']:.3f}" if m['det_intact'] is not None else "n/a"
        det_v = f"{m['det_violated']:.3f}" if m['det_violated'] is not None else "n/a"
        gap = f"{m['gap']:+.3f}" if m['gap'] is not None else "n/a"
        print(f"{cascade_name:<24} {m['parsed_rate']:>7.1%} {m['n_parsed']:>6} {det_i:>8} {det_v:>8} {gap:>8}")

    # Per-config breakdown
    print(f"\nPer-config parsed_rate by cascade:")
    print(f"  {'config':<30} " + " ".join(f"{c:>10}" for c in CASCADES))
    for cfg in configs:
        row = f"  {cfg:<30} "
        for cn in CASCADES:
            pr = e1_results[cn][cfg]["parsed_rate"]
            row += f" {pr:>9.1%}"
        print(row)

    # Per-config gap by cascade (only CoT configs since V1-min is uniform)
    print(f"\nPer-config gap by cascade:")
    print(f"  {'config':<30} " + " ".join(f"{c:>10}" for c in CASCADES))
    for cfg in configs:
        row = f"  {cfg:<30} "
        for cn in CASCADES:
            g = e1_results[cn][cfg]["gap"]
            row += f" {g:>+9.3f}" if g is not None else f" {'n/a':>10}"
        print(row)

    return e1_results


# ---------------------------------------------------------------------------
# E2 — Strictness sensitivity
# ---------------------------------------------------------------------------

def experiment_2(all_rows):
    print("\n" + "=" * 72)
    print("E2 — Parser strictness sensitivity (single-regex, no cascade)")
    print("=" * 72)

    configs = sorted({r["_config"] for r in all_rows})
    e2_results = {}

    for s_name, fn in STRICTNESS.items():
        e2_results[s_name] = {}
        parsed_labels = [fn(r["raw_response"]) for r in all_rows]
        e2_results[s_name]["overall"] = compute_metrics(all_rows, parsed_labels)
        for cfg in configs:
            sub_idx = [i for i, r in enumerate(all_rows) if r["_config"] == cfg]
            sub_rows = [all_rows[i] for i in sub_idx]
            sub_labels = [parsed_labels[i] for i in sub_idx]
            e2_results[s_name][cfg] = compute_metrics(sub_rows, sub_labels)

    print(f"\n{'Strictness':<24} {'parsed%':>8} {'n_par':>6} {'det_int':>8} {'det_vio':>8} {'gap':>8}")
    print("-" * 72)
    for s_name in STRICTNESS:
        m = e2_results[s_name]["overall"]
        det_i = f"{m['det_intact']:.3f}" if m['det_intact'] is not None else "n/a"
        det_v = f"{m['det_violated']:.3f}" if m['det_violated'] is not None else "n/a"
        gap = f"{m['gap']:+.3f}" if m['gap'] is not None else "n/a"
        print(f"{s_name:<24} {m['parsed_rate']:>7.1%} {m['n_parsed']:>6} {det_i:>8} {det_v:>8} {gap:>8}")

    print(f"\nPer-config parsed_rate by strictness:")
    print(f"  {'config':<30} " + " ".join(f"{c:>16}" for c in STRICTNESS))
    for cfg in configs:
        row = f"  {cfg:<30} "
        for sn in STRICTNESS:
            pr = e2_results[sn][cfg]["parsed_rate"]
            row += f" {pr:>15.1%}"
        print(row)

    return e2_results


# ---------------------------------------------------------------------------
# E3 — Rescue inspection set
# ---------------------------------------------------------------------------

def experiment_3(all_rows):
    """Find responses v1 missed but v2 caught; sample 30 for manual review."""
    print("\n" + "=" * 72)
    print("E3 — Rescue inspection set (v1-missed, v2-caught)")
    print("=" * 72)

    v1_cascade = CASCADES["P2_strict_permissive"]
    v2_cascade = CASCADES["P3_v2_md_tolerant"]

    rescued = []
    for r in all_rows:
        v1_label, _ = run_cascade(v1_cascade, r["raw_response"])
        v2_label, v2_stage = run_cascade(v2_cascade, r["raw_response"])
        if v1_label is None and v2_label is not None:
            rescued.append({
                **r,
                "v1_label": v1_label,
                "v2_label": v2_label,
                "v2_stage": v2_stage,
            })

    print(f"\nTotal rescued (v1 missed, v2 caught): {len(rescued)}")
    print(f"  v2 label distribution: {Counter(r['v2_label'] for r in rescued)}")
    print(f"  v2 stage distribution: {Counter(r['v2_stage'] for r in rescued)}")

    # Sample 30 stratified by config (proportional)
    by_cfg = defaultdict(list)
    for r in rescued:
        by_cfg[r["_config"]].append(r)
    print(f"\n  By config:")
    for cfg, lst in by_cfg.items():
        print(f"    {cfg}: {len(lst)} rescued")

    # Stratified sample of 30
    sample_target = 30
    total = sum(len(v) for v in by_cfg.values())
    sampled = []
    rng = random.Random(42)
    for cfg, lst in by_cfg.items():
        n_take = max(1, round(sample_target * len(lst) / total)) if total else 0
        if lst:
            sampled.extend(rng.sample(lst, min(n_take, len(lst))))
    # Cap at sample_target if we over-sampled due to rounding
    rng.shuffle(sampled)
    sampled = sampled[:sample_target]

    inspection_md = ["# E3 — Rescue Inspection Set\n",
                     "Each item below is a response that the v1 parser missed but the v2 parser caught.",
                     "Goal: confirm that v2's classification matches the model's clear intent (not a liberal rescue).\n",
                     f"Total rescued in corpus: **{len(rescued)}**.  Sample size: {len(sampled)} (stratified).",
                     ""]
    for i, r in enumerate(sampled, 1):
        inspection_md.append(f"## #{i}  [{r['_config']}]  chain_id={r['chain_id']}")
        inspection_md.append(f"- **Ground truth:** {r['ground_truth']} (expected label: {r['ground_truth_label']})")
        inspection_md.append(f"- **v1 parser:** missed (unparseable)")
        inspection_md.append(f"- **v2 parser:** {r['v2_label']} (rescue stage: {r['v2_stage']})")
        # Tail
        tail = r["raw_response"][-400:]
        inspection_md.append(f"- **Response tail (last 400 chars):**\n```\n{tail}\n```")
        inspection_md.append(f"- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**")
        inspection_md.append("")

    return rescued, sampled, "\n".join(inspection_md)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_rows = load_all()
    print(f"Loaded {len(all_rows)} raw responses across {len({r['_config'] for r in all_rows})} configs")

    e1 = experiment_1(all_rows)
    e2 = experiment_2(all_rows)
    rescued, sampled, inspection_md = experiment_3(all_rows)

    (OUT_DIR / "E1_cascade_depth.json").write_text(json.dumps(e1, indent=2, default=str))
    (OUT_DIR / "E2_strictness.json").write_text(json.dumps(e2, indent=2, default=str))
    (OUT_DIR / "E3_rescue_inspection.md").write_text(inspection_md)
    (OUT_DIR / "E3_rescue_full_list.json").write_text(json.dumps(rescued, indent=2, default=str))

    print(f"\nOutputs written to {OUT_DIR}/")
    for p in sorted(OUT_DIR.glob("*")):
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
