"""
Task 1 — Re-parse Day -2 V4-Flash raw responses with v2 4-stage cascade.

Zero API cost. Operates on pre-registration/day_minus_2/raw_responses.ndjson
(250 V4-Flash V1-minimal responses at k=15). Confirms whether the floor-effect
interpretation holds under the v2 parser cascade before Amendment #3 locks it.

Outputs (per user task spec):
  pre-registration/day_minus_2/reparse_v2/parser_provenance_v2.ndjson
  pre-registration/day_minus_2/reparse_v2/verification_results_v2.json
  pre-registration/day_minus_2/reparse_v2/comparison.md
"""

from __future__ import annotations

import json
import math
import random
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = REPO_ROOT / "pre-registration" / "day_minus_2" / "raw_responses.ndjson"
OUT_DIR = REPO_ROOT / "pre-registration" / "day_minus_2" / "reparse_v2"

PROVENANCE_OUT = OUT_DIR / "parser_provenance_v2.ndjson"
RESULTS_OUT = OUT_DIR / "verification_results_v2.json"
COMPARISON_OUT = OUT_DIR / "comparison.md"

# Reference: v1 metrics from the original Day -2 run for comparison
V1_METRICS = {
    "parsed_rate": 1.0000,
    "detection_rate_intact_correctness": 1.0000,  # SPEC convention: correctness rate
    "detection_rate_violated_correctness": 0.0000,
    "gap_spec_convention": -1.0000,
    "yes_rate": 0.0000,
    "no_rate": 1.0000,
    "parse_stage_breakdown": {"first_token": 250, "strict": 0, "permissive": 0, "unparseable": 0},
    "n_attempted": 250,
    "n_valid": 250,
}

# ---------------------------------------------------------------------------
# v2 4-stage cascade (matches Diagnostic J's P4)
# ---------------------------------------------------------------------------
MD_DECOR = re.compile(r"[\*_`]+")
STRICT_RE = re.compile(r"(?:Therefore,\s+)?[Tt]he answer is\s+(YES|NO)\b", re.IGNORECASE)
PERMISSIVE_RE = re.compile(r"(?i)(answer is|answer:|conclusion:)\s*(yes|no)\b")
LAST_TOKEN_RE = re.compile(r"(?i)(YES|NO)\b[\s\.\,\!\?\)]*\s*$")


def parse_v2(text: str) -> tuple[str | None, str]:
    """4-stage cascade per user task spec. Returns (label, stage)."""
    if not text:
        return None, "unparseable"
    s = text.strip()

    # Stage 1 — strict
    s_clean = MD_DECOR.sub("", s)
    if m := STRICT_RE.search(s_clean):
        return m.group(1).upper(), "strict"

    # Stage 2 — permissive (no markdown strip)
    if m := PERMISSIVE_RE.search(s):
        return m.group(2).upper(), "permissive"

    # Stage 3 — md_strip permissive
    if m := PERMISSIVE_RE.search(s_clean):
        return m.group(2).upper(), "md_strip"

    # Stage 4 — last_token
    tail = s_clean[-200:].strip()
    if m := LAST_TOKEN_RE.search(tail):
        return m.group(1).upper(), "last_token"

    return None, "unparseable"


def cohens_h(p1: float, p2: float) -> float:
    def phi(p):
        p = max(min(p, 1.0 - 1e-12), 1e-12)
        return 2.0 * math.asin(math.sqrt(p))
    return phi(p1) - phi(p2)


def bootstrap_bca_ci(values_a: list[int], values_b: list[int], n_boot: int = 2000, seed: int = 1337):
    """95% percentile bootstrap CI on gap = mean(b) - mean(a)."""
    rng = random.Random(seed)
    na, nb = len(values_a), len(values_b)
    if not na or not nb:
        return (float("nan"), float("nan"))
    gaps = []
    for _ in range(n_boot):
        a_resample = [values_a[rng.randrange(na)] for _ in range(na)]
        b_resample = [values_b[rng.randrange(nb)] for _ in range(nb)]
        gaps.append(sum(b_resample)/nb - sum(a_resample)/na)
    gaps.sort()
    return gaps[int(0.025 * n_boot)], gaps[int(0.975 * n_boot)]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not RAW_PATH.exists():
        print(f"FAIL: {RAW_PATH} not found")
        return 2

    rows = [json.loads(l) for l in RAW_PATH.open()]
    print(f"Loaded {len(rows)} raw responses from {RAW_PATH.name}")

    # Re-parse with v2
    reparsed = []
    for r in rows:
        v2_label, v2_stage = parse_v2(r["raw_response"])
        gt_label = r["ground_truth_label"]
        v2_correct = (v2_label == gt_label) if v2_label is not None else None
        reparsed.append({
            "sample_id": r["chain_id"],
            "ground_truth": r["ground_truth"],
            "ground_truth_label": gt_label,
            "raw_output_preview": r["raw_response"][:100],
            "v1_parse_stage": r["parse_stage"],
            "v1_parsed_label": r["parsed_label"],
            "v1_correct": r["correct"],
            "v2_parse_stage": v2_stage,
            "v2_parsed_label": v2_label,
            "v2_correct": v2_correct,
        })

    # Write parser provenance
    with PROVENANCE_OUT.open("w") as f:
        for r in reparsed:
            f.write(json.dumps(r) + "\n")
    print(f"Provenance written: {PROVENANCE_OUT.name}")

    # ----------------------------------------------------------------
    # Aggregate metrics (SPEC convention)
    # ----------------------------------------------------------------
    n = len(reparsed)
    parsed = [r for r in reparsed if r["v2_parsed_label"] is not None]
    intact = [r for r in reparsed if r["ground_truth"] == "intact"]
    violated = [r for r in reparsed if r["ground_truth"] == "violated"]
    intact_parsed = [r for r in intact if r["v2_parsed_label"] is not None]
    violated_parsed = [r for r in violated if r["v2_parsed_label"] is not None]

    intact_correct = [1 if r["v2_correct"] else 0 for r in intact_parsed]
    violated_correct = [1 if r["v2_correct"] else 0 for r in violated_parsed]

    det_intact_correctness = sum(intact_correct) / len(intact_correct) if intact_correct else float("nan")
    det_violated_correctness = sum(violated_correct) / len(violated_correct) if violated_correct else float("nan")
    gap_spec = det_violated_correctness - det_intact_correctness
    h = cohens_h(det_violated_correctness, det_intact_correctness)
    ci_lo, ci_hi = bootstrap_bca_ci(intact_correct, violated_correct)

    yes_count = sum(1 for r in parsed if r["v2_parsed_label"] == "YES")
    no_count = sum(1 for r in parsed if r["v2_parsed_label"] == "NO")
    yes_rate = yes_count / len(parsed) if parsed else float("nan")
    no_rate = no_count / len(parsed) if parsed else float("nan")

    stage_counts = Counter(r["v2_parse_stage"] for r in reparsed)
    parsed_rate = len(parsed) / n
    parsed_rate_intact = len(intact_parsed) / len(intact) if intact else float("nan")
    parsed_rate_violated = len(violated_parsed) / len(violated) if violated else float("nan")

    # Per-stage rescues vs v1
    rescued_v2 = [r for r in reparsed if r["v1_parsed_label"] is None and r["v2_parsed_label"] is not None]
    differed = [r for r in reparsed if r["v1_parsed_label"] is not None and r["v2_parsed_label"] is not None and r["v1_parsed_label"] != r["v2_parsed_label"]]

    print(f"\n=== Task 1 — v2 re-parse results ===")
    print(f"n_attempted:               {n}")
    print(f"parsed_rate (v2):          {parsed_rate:.4f}  (intact: {parsed_rate_intact:.4f}, violated: {parsed_rate_violated:.4f})")
    print(f"parse_stage_breakdown:     {dict(stage_counts)}")
    print(f"yes_rate (parsed):         {yes_rate:.4f}")
    print(f"no_rate (parsed):          {no_rate:.4f}")
    print(f"detection_rate_intact (correctness):     {det_intact_correctness:.4f}  ({sum(intact_correct)}/{len(intact_correct)})")
    print(f"detection_rate_violated (correctness):   {det_violated_correctness:.4f}  ({sum(violated_correct)}/{len(violated_correct)})")
    print(f"gap (SPEC: violated - intact):           {gap_spec:+.4f}")
    print(f"Cohen's h:                               {h:+.4f}")
    print(f"95% bootstrap CI on gap:                 [{ci_lo:+.4f}, {ci_hi:+.4f}]")
    print(f"")
    print(f"v1→v2 deltas:")
    print(f"  rescued by v2 (v1 missed): {len(rescued_v2)}")
    print(f"  classification differs:     {len(differed)}")

    results = {
        "task": "Task 1 — re-parse Day -2 V4-Flash with v2 4-stage cascade",
        "date": "2026-05-12",
        "input": str(RAW_PATH),
        "config_reference": "V4-Flash, V1-minimal, k=15, max_tokens=32, thinking=disabled (matches Day -2 Amendment #2 baseline)",
        "v2_cascade_stages": ["strict", "permissive", "md_strip", "last_token", "unparseable"],
        "n_attempted": n,
        "parsed_rate_overall": parsed_rate,
        "parsed_rate_intact": parsed_rate_intact,
        "parsed_rate_violated": parsed_rate_violated,
        "parse_stage_breakdown": dict(stage_counts),
        "yes_count": yes_count,
        "no_count": no_count,
        "yes_rate_parsed": yes_rate,
        "no_rate_parsed": no_rate,
        "n_intact": len(intact),
        "n_violated": len(violated),
        "n_intact_parsed": len(intact_parsed),
        "n_violated_parsed": len(violated_parsed),
        "detection_rate_intact_correctness": det_intact_correctness,
        "detection_rate_violated_correctness": det_violated_correctness,
        "gap_spec_convention": gap_spec,
        "gap_alt_convention_intact_minus_violated": -gap_spec,
        "cohens_h": h,
        "ci_95_gap_spec": [ci_lo, ci_hi],
        "v1_v2_deltas": {
            "rescued_by_v2": len(rescued_v2),
            "classification_differs": len(differed),
        },
    }
    RESULTS_OUT.write_text(json.dumps(results, indent=2))
    print(f"\nResults written: {RESULTS_OUT.name}")

    # ----------------------------------------------------------------
    # Comparison markdown
    # ----------------------------------------------------------------
    md = [f"# Task 1 — Day −2 V4-Flash v1 vs v2 Parser Comparison\n",
          f"**Date:** 2026-05-12  •  **Cost:** $0  •  **Input:** `{RAW_PATH.name}`\n",
          f"**Config:** V4-Flash, V1-minimal, k=15, max_tokens=32, n=250\n",
          "## Side-by-side metrics\n",
          "| Metric | v1 parser (original Day −2) | v2 4-stage cascade |",
          "|---|---|---|",
          f"| parsed_rate | {V1_METRICS['parsed_rate']:.4f} | {parsed_rate:.4f} |",
          f"| YES_rate (parsed) | {V1_METRICS['yes_rate']:.4f} | {yes_rate:.4f} |",
          f"| NO_rate (parsed) | {V1_METRICS['no_rate']:.4f} | {no_rate:.4f} |",
          f"| detection_rate_intact (correctness) | {V1_METRICS['detection_rate_intact_correctness']:.4f} | {det_intact_correctness:.4f} |",
          f"| detection_rate_violated (correctness) | {V1_METRICS['detection_rate_violated_correctness']:.4f} | {det_violated_correctness:.4f} |",
          f"| **gap (SPEC: violated − intact)** | **{V1_METRICS['gap_spec_convention']:+.4f}** | **{gap_spec:+.4f}** |",
          f"| Δgap (v2 − v1) | — | {(gap_spec - V1_METRICS['gap_spec_convention']):+.4f} |",
          "",
          "## Parse stage breakdown\n",
          "| Stage | v1 | v2 |",
          "|---|---|---|",
          f"| strict | {V1_METRICS['parse_stage_breakdown'].get('strict', 0)} | {stage_counts.get('strict', 0)} |",
          f"| permissive | {V1_METRICS['parse_stage_breakdown'].get('permissive', 0)} | {stage_counts.get('permissive', 0)} |",
          f"| md_strip (v2-only) | — | {stage_counts.get('md_strip', 0)} |",
          f"| last_token (v2-only) | — | {stage_counts.get('last_token', 0)} |",
          f"| first_token (v1-only) | {V1_METRICS['parse_stage_breakdown'].get('first_token', 0)} | — |",
          f"| unparseable | {V1_METRICS['parse_stage_breakdown'].get('unparseable', 0)} | {stage_counts.get('unparseable', 0)} |",
          "",
          "## v1→v2 deltas\n",
          f"- Rescued by v2 (v1 missed): {len(rescued_v2)}",
          f"- Classification differs: {len(differed)}",
          "",
          "## Stop-condition evaluation\n",
          f"- **parsed_rate < 0.95?** {parsed_rate:.4f} — {'YES → STOP' if parsed_rate < 0.95 else 'NO (passes)'}",
          f"- **|Δgap| > 0.10?** |{(gap_spec - V1_METRICS['gap_spec_convention']):+.4f}| — {'YES → STOP' if abs(gap_spec - V1_METRICS['gap_spec_convention']) > 0.10 else 'NO (passes)'}",
          f"- **YES_rate > 0.05?** {yes_rate:.4f} — {'YES → SURFACE (Path 1 may need reconsidering)' if yes_rate > 0.05 else 'NO (passes)'}",
          "",
          "## Interpretation\n"]

    if parsed_rate >= 0.95 and abs(gap_spec - V1_METRICS["gap_spec_convention"]) <= 0.10 and yes_rate <= 0.05:
        md.append("**Floor-effect interpretation CONFIRMED under v2 parser.** Path 1 lock holds. Proceed to Task 2.")
        path1_status = "confirmed"
    else:
        md.append("**Unexpected finding surfaced.** Surface to user for both-author review before proceeding to Task 2.")
        path1_status = "needs-review"

    COMPARISON_OUT.write_text("\n".join(md))
    print(f"Comparison written: {COMPARISON_OUT.name}")
    print(f"\nPath 1 status: {path1_status.upper()}")
    return 0 if path1_status == "confirmed" else 3


if __name__ == "__main__":
    sys.exit(main())
