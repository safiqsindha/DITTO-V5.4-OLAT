"""
Expanded parser cascade — re-extracts YES/NO answers from existing diagnostic raw
responses, handling markdown decoration (**, *, _) and trailing answer patterns
the original parser missed.

Re-extracts across all diagnostic NDJSON files; reports the corrected detection
rates without spending any API budget.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DIAG_DIR = REPO_ROOT / "pre-registration" / "diagnostics"

# Strip markdown decoration before matching
MD_DECOR = re.compile(r"[\*_`]+")

# Stage 1 — strict: "the answer is YES/NO" (possibly preceded by Therefore,)
STRICT_RE = re.compile(r"(?:Therefore,\s+)?[Tt]he answer is\s+(YES|NO)\b", re.IGNORECASE)

# Stage 2 — permissive prefix forms
PERMISSIVE_RE = re.compile(
    r"(?i)(?:answer is|answer:|answer\s*:|conclusion:|conclusion\s*:|so:|so,|final\s+answer:?|verdict:?|"
    r"in\s+summary,?|in\s+conclusion,?|overall,?|hence,?|thus,?|therefore,?|"
    r"^|[\.\n!?]\s*)"
    r"\s*(?:\*{0,2}|_{0,2}|\"|')\s*(YES|NO)\s*(?:\*{0,2}|_{0,2}|\"|')\b"
)

# Stage 3 — last line / trailing answer (capture last clear yes/no at end of message)
LAST_TOKEN_RE = re.compile(
    r"(?i)(YES|NO)\b[\s\.\,\!\?\*\_\)]*\s*$"
)

# Stage 4 — first token
FIRST_TOKEN_RE = re.compile(r"^[\W\*\_]*(YES|NO)\b", re.IGNORECASE)


def parse_v2(text):
    """Expanded parser cascade. Returns (label, stage_name)."""
    if not text:
        return None, "unparseable"
    s = text.strip()

    # Stage 1 — strict (un-decorated)
    s_clean = MD_DECOR.sub("", s)
    if m := STRICT_RE.search(s_clean):
        return m.group(1).upper(), "strict"

    # Stage 2 — permissive with markdown tolerance
    if m := PERMISSIVE_RE.search(s):
        return m.group(1).upper(), "permissive"

    # Try the markdown-stripped version too
    if m := PERMISSIVE_RE.search(s_clean):
        return m.group(1).upper(), "permissive_clean"

    # Stage 3 — last-line scan: take last 200 chars, strip MD, look for trailing YES/NO
    tail = s_clean[-200:].strip()
    if m := LAST_TOKEN_RE.search(tail):
        return m.group(1).upper(), "last_token"

    # Stage 4 — first token
    head = " ".join(s.split()[:10])
    head_clean = MD_DECOR.sub("", head)
    if m := FIRST_TOKEN_RE.search(head_clean):
        return m.group(1).upper(), "first_token"

    return None, "unparseable"


def analyze_file(path, label):
    rows = [json.loads(l) for l in open(path)]
    new_results = []
    for r in rows:
        new_label, new_stage = parse_v2(r["raw_response"])
        gt_label = r["ground_truth_label"]
        new_correct = (new_label == gt_label) if new_label is not None else None
        new_results.append({**r, "v2_parsed_label": new_label, "v2_parse_stage": new_stage, "v2_correct": new_correct})

    parsed_v1 = sum(1 for r in rows if r["parsed_label"] is not None)
    parsed_v2 = sum(1 for r in new_results if r["v2_parsed_label"] is not None)
    v1_intact_p = [r["correct"] for r in rows if r["correct"] is not None and r["ground_truth"] == "intact"]
    v1_violated_p = [r["correct"] for r in rows if r["correct"] is not None and r["ground_truth"] == "violated"]
    v2_intact_p = [r["v2_correct"] for r in new_results if r["v2_correct"] is not None and r["ground_truth"] == "intact"]
    v2_violated_p = [r["v2_correct"] for r in new_results if r["v2_correct"] is not None and r["ground_truth"] == "violated"]
    stages = Counter(r["v2_parse_stage"] for r in new_results)
    labels = Counter(r["v2_parsed_label"] for r in new_results)

    print(f"\n{'='*72}")
    print(f"{label}  (n={len(rows)})")
    print(f"{'='*72}")
    print(f"  parsed (v1 → v2):  {parsed_v1} → {parsed_v2}   (delta: +{parsed_v2 - parsed_v1})")
    print(f"  v2 stages:         {dict(stages)}")
    print(f"  v2 labels:         {dict(labels)}")

    def fmt(correct):
        if not correct:
            return "n=0"
        return f"{sum(correct)/len(correct):.3f} ({sum(correct)}/{len(correct)})"
    print(f"  intact detection:")
    print(f"    v1: {fmt(v1_intact_p)}")
    print(f"    v2: {fmt(v2_intact_p)}")
    print(f"  violated detection:")
    print(f"    v1: {fmt(v1_violated_p)}")
    print(f"    v2: {fmt(v2_violated_p)}")

    if v2_intact_p and v2_violated_p:
        gap_v2 = sum(v2_violated_p)/len(v2_violated_p) - sum(v2_intact_p)/len(v2_intact_p)
        print(f"  v2 gap:            {gap_v2:+.4f}")
    return new_results


def main():
    files = [
        (DIAG_DIR / "diagnostic_F_cot_flash_raw.ndjson", "Diag F  — V4-Flash + CoT @ 512"),
        (DIAG_DIR / "diagnostic_G_v4pro_baseline_raw.ndjson", "Diag G  — V4-Pro + V1-minimal @ 32"),
        (DIAG_DIR / "diagnostic_H_cot_v4pro_raw.ndjson", "Diag H  — V4-Pro + CoT @ 512"),
        (DIAG_DIR / "diagnostic_I_flash_raw.ndjson", "Diag I  — V4-Flash + CoT @ 4096"),
        (DIAG_DIR / "diagnostic_I_pro_raw.ndjson", "Diag I  — V4-Pro + CoT @ 4096"),
    ]
    for path, label in files:
        if path.exists():
            analyze_file(path, label)


if __name__ == "__main__":
    main()
