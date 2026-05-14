"""
Diagnostic F — Does Lever 18 L2 CoT break V4-Flash off the NO-floor?

Config: n=50 from existing seeded sample, k=15, model=deepseek-v4-flash,
prompt = chain + "Think step by step before answering. Therefore, the
answer is YES or NO.", max_tokens=512 (Lever 18 L2).

Compared against the Day -2 baseline (k=15, max_tokens=32, no CoT, 100% NO),
this isolates the Lever 18 effect on the floor.
"""

from __future__ import annotations

import json
import math
import os
import random
import re
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = REPO_ROOT / ".env"
SAMPLE_PATH = REPO_ROOT / "pre-registration" / "day_minus_3" / "verification_n250_sample.jsonl"
OUT_DIR = REPO_ROOT / "pre-registration" / "diagnostics"

DIAG_NAME = "F_cot_flash"
N_DIAGNOSTIC = 50
MODEL = "deepseek-v4-flash"
BASE_URL = "https://api.deepseek.com"
TEMPERATURE = 0.0
MAX_TOKENS = 512                # Lever 18 L2 cap
CUTOFF_K = 15
PER_CALL_TIMEOUT_S = 120.0
MAX_WORKERS = 4

QUESTION_TEXT = "Does this battle chain contain any rule violations?"
COT_INSTRUCTION = "Think step by step before answering."
OUTPUT_ANCHOR = "Therefore, the answer is YES or NO."

STRICT_RE = re.compile(r"(?:Therefore,\s+)?[Tt]he answer is\s+(YES|NO)\b", re.IGNORECASE)
PERMISSIVE_RE = re.compile(r"(?i)(?:answer is|answer:|conclusion:)\s*(yes|no)\b")
FIRST_TOKEN_RE = re.compile(r"^\W*(YES|NO)\b", re.IGNORECASE)
_STEP_BOUNDARY = re.compile(r"(Step \d+)")


def parse_response(text):
    if not text:
        return None, "unparseable"
    s = text.strip()
    if m := STRICT_RE.search(s):
        return m.group(1).upper(), "strict"
    if m := PERMISSIVE_RE.search(s):
        return m.group(1).upper(), "permissive"
    head = " ".join(s.split()[:10])
    if m := FIRST_TOKEN_RE.search(head):
        return m.group(1).upper(), "first_token"
    return None, "unparseable"


def cutoff_rendered(rendered, k):
    if k <= 0:
        return ""
    parts = _STEP_BOUNDARY.split(rendered)
    steps = []
    i = 0
    while i < len(parts) and not _STEP_BOUNDARY.fullmatch(parts[i]):
        i += 1
    while i + 1 < len(parts):
        if _STEP_BOUNDARY.fullmatch(parts[i]):
            steps.append((parts[i], parts[i + 1]))
            i += 2
        else:
            i += 1
    return "".join(h + b for h, b in steps[:k])


def build_user_prompt(rendered_steps):
    return f"{rendered_steps.rstrip()}\n\n{QUESTION_TEXT} {COT_INSTRUCTION} {OUTPUT_ANCHOR}"


def load_env(env_path):
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and v and not os.environ.get(k, "").strip():
            os.environ[k] = v


def run_one(client, record):
    chain_path = Path(record["chain_path"])
    with chain_path.open() as f:
        chain = json.loads(f.readline())
    truncated = cutoff_rendered(chain["rendered"], CUTOFF_K)
    user_msg = build_user_prompt(truncated)
    t0 = time.monotonic()
    try:
        r = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": user_msg}],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            extra_body={"thinking": {"type": "disabled"}},
        )
        text = (r.choices[0].message.content or "").strip()
        served_model = getattr(r, "model", "?")
        pt, ct = r.usage.prompt_tokens, r.usage.completion_tokens
        err = None
    except Exception as e:
        text = ""
        served_model = None
        pt = ct = None
        err = f"{type(e).__name__}: {e}"
    elapsed = time.monotonic() - t0
    parsed_label, parse_stage = parse_response(text)
    ground_truth_label = "YES" if record["ground_truth"] == "violated" else "NO"
    correct = (parsed_label == ground_truth_label) if parsed_label is not None else None
    return {
        "chain_id": record["chain_id"],
        "ground_truth": record["ground_truth"],
        "ground_truth_label": ground_truth_label,
        "kind": record["kind"],
        "raw_response": text,
        "parsed_label": parsed_label,
        "parse_stage": parse_stage,
        "correct": correct,
        "elapsed_s": round(elapsed, 2),
        "error": err,
        "served_model": served_model,
        "prompt_tokens": pt,
        "completion_tokens": ct,
        "k_used": CUTOFF_K,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"=== Diagnostic {DIAG_NAME} ===")
    print(f"Model:       {MODEL}")
    print(f"k:           {CUTOFF_K}")
    print(f"max_tokens:  {MAX_TOKENS} (Lever 18 L2)")
    print(f"n:           {N_DIAGNOSTIC}")
    print(f"Prompt:      chain + '{QUESTION_TEXT} {COT_INSTRUCTION} {OUTPUT_ANCHOR}'")
    print()

    load_env(ENV_PATH)
    key = os.environ["DEEPSEEK_API_KEY"]
    print(f"Key prefix: {key[:8]}...")

    samples = []
    with SAMPLE_PATH.open() as f:
        for line in f:
            samples.append(json.loads(line))
    sub = samples[:N_DIAGNOSTIC]
    real = sum(1 for s in sub if s["ground_truth"] == "intact")
    violated = N_DIAGNOSTIC - real
    print(f"Sample: {real} intact / {violated} violated")
    print()

    client = OpenAI(api_key=key, base_url=BASE_URL, timeout=PER_CALL_TIMEOUT_S)
    t0 = time.monotonic()
    results = []
    print("Running...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(run_one, client, s) for s in sub]
        for i, fut in enumerate(as_completed(futures), 1):
            results.append(fut.result())
            if i % 10 == 0 or i == len(sub):
                print(f"  {i}/{len(sub)}")
    elapsed = time.monotonic() - t0
    print(f"Complete in {elapsed:.1f}s")
    print()

    # Save raw
    raw_path = OUT_DIR / f"diagnostic_{DIAG_NAME}_raw.ndjson"
    with raw_path.open("w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    # Metrics
    intact_correct = [r["correct"] for r in results if r["correct"] is not None and r["ground_truth"] == "intact"]
    violated_correct = [r["correct"] for r in results if r["correct"] is not None and r["ground_truth"] == "violated"]
    parsed = [r for r in results if r["parsed_label"] is not None]
    yes_rate = sum(1 for r in parsed if r["parsed_label"] == "YES") / len(parsed) if parsed else 0
    no_rate = sum(1 for r in parsed if r["parsed_label"] == "NO") / len(parsed) if parsed else 0
    unparseable = sum(1 for r in results if r["parse_stage"] == "unparseable")
    by_stage = Counter(r["parse_stage"] for r in results)
    by_label = Counter(r["parsed_label"] for r in results)
    p_intact = sum(intact_correct) / len(intact_correct) if intact_correct else float("nan")
    p_violated = sum(violated_correct) / len(violated_correct) if violated_correct else float("nan")
    gap = p_violated - p_intact if (intact_correct and violated_correct) else float("nan")
    mean_ct = sum(r["completion_tokens"] for r in results if r["completion_tokens"]) / max(1, sum(1 for r in results if r["completion_tokens"]))

    print("=== Results ===")
    print(f"unparseable:              {unparseable}/{len(results)}")
    print(f"parse stage breakdown:    {dict(by_stage)}")
    print(f"label breakdown:          {dict(by_label)}")
    print(f"YES_rate / NO_rate:       {yes_rate:.3f} / {no_rate:.3f}")
    print(f"detection_rate_intact:    {p_intact:.4f}")
    print(f"detection_rate_violated:  {p_violated:.4f}")
    print(f"gap:                      {gap:+.4f}")
    print(f"mean completion_tokens:   {mean_ct:.1f}")
    print()
    print(f"Raw responses saved: {raw_path}")

    # Summary
    summary = {
        "diagnostic": DIAG_NAME,
        "config": {
            "model": MODEL, "k": CUTOFF_K, "max_tokens": MAX_TOKENS, "n": N_DIAGNOSTIC,
            "lever_18_level": "L2 (think step by step)",
        },
        "metrics": {
            "yes_rate": yes_rate, "no_rate": no_rate,
            "detection_rate_intact": p_intact, "detection_rate_violated": p_violated, "gap": gap,
            "unparseable": unparseable,
            "parse_stages": dict(by_stage),
            "label_breakdown": dict(by_label),
            "mean_completion_tokens": mean_ct,
        },
        "elapsed_s": round(elapsed, 1),
    }
    (OUT_DIR / f"diagnostic_{DIAG_NAME}_summary.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
