"""
Task 2 — V4-Pro Day -2 Verification at n=250.

Identical configuration to V4-Flash Day -2 except the model: deepseek-v4-pro.
Uses the same 250 chains from verification_n250_sample.jsonl for direct
cross-model comparison. Parser is the v2 4-stage cascade (Amendment #3 spec).

Outputs (per user task spec):
  pre-registration/day_minus_2_v4pro/raw_responses.ndjson
  pre-registration/day_minus_2_v4pro/parser_provenance.ndjson
  pre-registration/day_minus_2_v4pro/verification_results.json
  pre-registration/day_minus_2_v4pro/day_minus_2_v4pro_log.txt
  pre-registration/day_minus_2_v4pro/scenario_evaluation.md
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

from openai import OpenAI, BadRequestError, RateLimitError

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = REPO_ROOT / ".env"
SAMPLE_PATH = REPO_ROOT / "pre-registration" / "day_minus_3" / "verification_n250_sample.jsonl"
OUT_DIR = REPO_ROOT / "pre-registration" / "day_minus_2_v4pro"

RAW_OUT = OUT_DIR / "raw_responses.ndjson"
PROVENANCE_OUT = OUT_DIR / "parser_provenance.ndjson"
RESULTS_OUT = OUT_DIR / "verification_results.json"
LOG_OUT = OUT_DIR / "day_minus_2_v4pro_log.txt"
SCENARIO_OUT = OUT_DIR / "scenario_evaluation.md"

# ---------------------------------------------------------------------------
# Config — identical to V4-Flash Day -2 except model
# ---------------------------------------------------------------------------
MODEL = "deepseek-v4-pro"
BASE_URL = "https://api.deepseek.com"   # NOT /beta
TEMPERATURE = 0.0
MAX_TOKENS = 32
CUTOFF_K = 15
PER_CALL_TIMEOUT_S = 120.0
MAX_WORKERS = 4

QUESTION_TEXT = "Does this battle chain contain any rule violations?"
OUTPUT_ANCHOR = "The answer is YES or NO."

# Pause thresholds per SPEC §6 / O6
S1_GAP_UPPER = 0.05
S2_GAP_LOWER = -0.05
S3_PARSE_FAIL = 0.05
S4_N_VALID_MIN = 200
S5_DEGEN = 0.95
S6_DETECTION = 0.80
S6_GAP_LOWER = 0.10

# Bootstrap
N_BOOTSTRAP = 2000
BOOTSTRAP_SEED = 1337

# ---------------------------------------------------------------------------
# v2 cascade (4-stage per Task 1 spec)
# ---------------------------------------------------------------------------
MD_DECOR = re.compile(r"[\*_`]+")
STRICT_RE = re.compile(r"(?:Therefore,\s+)?[Tt]he answer is\s+(YES|NO)\b", re.IGNORECASE)
PERMISSIVE_RE = re.compile(r"(?i)(answer is|answer:|conclusion:)\s*(yes|no)\b")
LAST_TOKEN_RE = re.compile(r"(?i)(YES|NO)\b[\s\.\,\!\?\)]*\s*$")
_STEP_BOUNDARY = re.compile(r"(Step \d+)")


def parse_v2(text):
    if not text:
        return None, "unparseable"
    s = text.strip()
    s_clean = MD_DECOR.sub("", s)
    if m := STRICT_RE.search(s_clean):
        return m.group(1).upper(), "strict"
    if m := PERMISSIVE_RE.search(s):
        return m.group(2).upper(), "permissive"
    if m := PERMISSIVE_RE.search(s_clean):
        return m.group(2).upper(), "md_strip"
    tail = s_clean[-200:].strip()
    if m := LAST_TOKEN_RE.search(tail):
        return m.group(1).upper(), "last_token"
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
    return f"{rendered_steps.rstrip()}\n\n{QUESTION_TEXT} {OUTPUT_ANCHOR}"


def load_env(env_path):
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and v and not os.environ.get(k, "").strip():
            os.environ[k] = v


def cohens_h(p1, p2):
    def phi(p):
        p = max(min(p, 1.0 - 1e-12), 1e-12)
        return 2.0 * math.asin(math.sqrt(p))
    return phi(p1) - phi(p2)


def bootstrap_ci(intact_correct, violated_correct, n_boot=N_BOOTSTRAP, seed=BOOTSTRAP_SEED):
    rng = random.Random(seed)
    ni, nv = len(intact_correct), len(violated_correct)
    if not ni or not nv:
        return (float("nan"), float("nan"))
    gaps = []
    for _ in range(n_boot):
        ir = [intact_correct[rng.randrange(ni)] for _ in range(ni)]
        vr = [violated_correct[rng.randrange(nv)] for _ in range(nv)]
        gaps.append(sum(vr)/nv - sum(ir)/ni)
    gaps.sort()
    return gaps[int(0.025 * n_boot)], gaps[int(0.975 * n_boot)]


def run_one(client, record):
    chain_path = Path(record["chain_path"])
    with chain_path.open() as f:
        chain = json.loads(f.readline())
    truncated = cutoff_rendered(chain["rendered"], CUTOFF_K)
    user_msg = build_user_prompt(truncated)
    t0 = time.monotonic()
    err = None
    text = ""
    served_model = None
    pt = ct = None
    finish_reason = None
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
        pt = r.usage.prompt_tokens
        ct = r.usage.completion_tokens
        finish_reason = r.choices[0].finish_reason
    except (BadRequestError, RateLimitError) as e:
        err = f"{type(e).__name__}: {e}"
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
    elapsed = time.monotonic() - t0
    parsed_label, parse_stage = parse_v2(text)
    gt_label = "YES" if record["ground_truth"] == "violated" else "NO"
    correct = (parsed_label == gt_label) if parsed_label is not None else None
    return {
        "chain_id": record["chain_id"],
        "ground_truth": record["ground_truth"],
        "ground_truth_label": gt_label,
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
        "finish_reason": finish_reason,
        "k_used": CUTOFF_K,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log_lines = []

    def log(msg):
        print(msg, flush=True)
        log_lines.append(msg)

    log("=" * 72)
    log("Task 2 — V4-Pro Day -2 Verification (n=250)")
    log("=" * 72)
    log(f"Model:        {MODEL}")
    log(f"Endpoint:     {BASE_URL}")
    log(f"Temperature:  {TEMPERATURE}")
    log(f"max_tokens:   {MAX_TOKENS}")
    log(f"cutoff k:     {CUTOFF_K}")
    log(f"thinking:     disabled")
    log(f"Parser:       v2 4-stage cascade (strict → permissive → md_strip → last_token)")
    log(f"Sample:       {SAMPLE_PATH}")
    log("=" * 72)

    load_env(ENV_PATH)
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        log("FAIL: DEEPSEEK_API_KEY missing")
        return 2
    log(f"Key prefix: {key[:8]}...")

    samples = [json.loads(l) for l in SAMPLE_PATH.open()]
    log(f"Loaded {len(samples)} chains: {sum(1 for s in samples if s['ground_truth']=='intact')} intact / {sum(1 for s in samples if s['ground_truth']=='violated')} violated")
    log("")

    client = OpenAI(api_key=key, base_url=BASE_URL, timeout=PER_CALL_TIMEOUT_S)

    t_start = time.monotonic()
    log("Starting parallel API calls...")
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(run_one, client, s): s for s in samples}
        completed = 0
        for fut in as_completed(futures):
            results.append(fut.result())
            completed += 1
            if completed % 25 == 0 or completed == len(samples):
                log(f"  Progress: {completed}/{len(samples)} ({time.monotonic()-t_start:.0f}s elapsed)")
    t_total = time.monotonic() - t_start
    log(f"All calls complete in {t_total:.1f}s ({t_total/len(results):.2f}s/call avg)")
    log("")

    # Persist raw
    with RAW_OUT.open("w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    log(f"Raw responses: {RAW_OUT.name}")
    with PROVENANCE_OUT.open("w") as f:
        for r in results:
            f.write(json.dumps({
                "chain_id": r["chain_id"],
                "parse_stage": r["parse_stage"],
                "parsed_label": r["parsed_label"],
                "ground_truth_label": r["ground_truth_label"],
                "correct": r["correct"],
                "raw_response_preview": r["raw_response"][:100],
            }) + "\n")
    log(f"Provenance:    {PROVENANCE_OUT.name}")
    log("")

    # Metrics
    n = len(results)
    errors = sum(1 for r in results if r["error"])
    unparseable = sum(1 for r in results if r["parse_stage"] == "unparseable")
    parse_fail_rate = unparseable / n
    n_valid = n - unparseable - errors

    stage_counts = Counter(r["parse_stage"] for r in results)
    intact_correct = [1 if r["correct"] else 0 for r in results if r["correct"] is not None and r["ground_truth"] == "intact"]
    violated_correct = [1 if r["correct"] else 0 for r in results if r["correct"] is not None and r["ground_truth"] == "violated"]
    det_intact = sum(intact_correct)/len(intact_correct) if intact_correct else float("nan")
    det_violated = sum(violated_correct)/len(violated_correct) if violated_correct else float("nan")
    gap = det_violated - det_intact if (intact_correct and violated_correct) else float("nan")
    h = cohens_h(det_violated, det_intact) if (intact_correct and violated_correct) else float("nan")
    ci_lo, ci_hi = bootstrap_ci(intact_correct, violated_correct)

    parsed = [r for r in results if r["parsed_label"] is not None]
    yes_rate = sum(1 for r in parsed if r["parsed_label"] == "YES")/len(parsed) if parsed else float("nan")
    no_rate = sum(1 for r in parsed if r["parsed_label"] == "NO")/len(parsed) if parsed else float("nan")

    cts = [r["completion_tokens"] for r in results if r["completion_tokens"]]
    mean_ct = sum(cts)/len(cts) if cts else float("nan")
    fr_dist = Counter(r["finish_reason"] for r in results)

    log("=" * 72)
    log("Verification Metrics (V4-Pro)")
    log("=" * 72)
    log(f"n_attempted:               {n}")
    log(f"n_valid:                   {n_valid}")
    log(f"errors:                    {errors}")
    log(f"unparseable:               {unparseable}")
    log(f"parse_failure_rate:        {parse_fail_rate:.4f}")
    log(f"")
    log(f"Parse stage breakdown:     {dict(stage_counts)}")
    log(f"finish_reason:             {dict(fr_dist)}")
    log(f"mean completion_tokens:    {mean_ct:.2f}")
    log(f"")
    log(f"n_intact:                  {len(intact_correct)}")
    log(f"n_violated:                {len(violated_correct)}")
    log(f"detection_rate_intact:     {det_intact:.4f}  ({sum(intact_correct)}/{len(intact_correct)})")
    log(f"detection_rate_violated:   {det_violated:.4f}  ({sum(violated_correct)}/{len(violated_correct)})")
    log(f"gap (SPEC):                {gap:+.4f}")
    log(f"Cohen's h:                 {h:+.4f}")
    log(f"95% bootstrap CI:          [{ci_lo:+.4f}, {ci_hi:+.4f}]")
    log(f"YES_rate (parsed):         {yes_rate:.4f}")
    log(f"NO_rate (parsed):          {no_rate:.4f}")

    # Scenario evaluation
    triggers = []
    if not math.isnan(gap):
        if gap > S1_GAP_UPPER:
            triggers.append(f"S1 (unexpected positive signal): gap={gap:+.4f} > +0.05")
        if gap < S2_GAP_LOWER:
            triggers.append(f"S2 (anti-detection): gap={gap:+.4f} < -0.05")
    if parse_fail_rate > S3_PARSE_FAIL:
        triggers.append(f"S3 (parse failure): {parse_fail_rate:.4f} > 0.05")
    if n_valid < S4_N_VALID_MIN:
        triggers.append(f"S4 (incomplete run): n_valid={n_valid} < 200")
    if not math.isnan(yes_rate):
        if yes_rate > S5_DEGEN or no_rate > S5_DEGEN:
            triggers.append(f"S5 (degenerate output): YES_rate={yes_rate:.4f}, NO_rate={no_rate:.4f}")
    if not math.isnan(det_violated) and not math.isnan(gap):
        if det_violated >= S6_DETECTION and gap >= S6_GAP_LOWER:
            triggers.append(f"S6 (V4-Pro organic competence): det_violated={det_violated:.4f} ≥ 0.80 AND gap={gap:+.4f} ≥ 0.10")

    log("")
    log("=" * 72)
    log("Scenario Classification (S1-S6)")
    log("=" * 72)
    if triggers:
        log("PAUSE triggered:")
        for t in triggers:
            log(f"  - {t}")
    else:
        log("No scenarios triggered. Proceed conditions met.")

    # Scenario evaluation markdown
    sm = [f"# Task 2 — V4-Pro Day −2 Scenario Evaluation\n",
          f"**Date:** 2026-05-12  •  **Cost:** ~$1–3  •  **n=250**\n",
          "## Metric snapshot\n",
          f"- parsed_rate: {1-parse_fail_rate:.4f}",
          f"- detection_rate_intact: {det_intact:.4f}",
          f"- detection_rate_violated: {det_violated:.4f}",
          f"- gap (SPEC): {gap:+.4f}",
          f"- 95% CI gap: [{ci_lo:+.4f}, {ci_hi:+.4f}]",
          f"- Cohen's h: {h:+.4f}",
          f"- YES_rate / NO_rate (parsed): {yes_rate:.4f} / {no_rate:.4f}",
          "",
          "## Per-scenario evaluation\n",
          "| Scenario | Threshold | Observed | Triggered? |",
          "|---|---|---|---|",
          f"| S1 Unexpected positive | gap > +0.05 | {gap:+.4f} | {'**YES**' if gap > S1_GAP_UPPER else 'no'} |",
          f"| S2 Anti-detection | gap < −0.05 | {gap:+.4f} | {'**YES**' if gap < S2_GAP_LOWER else 'no'} |",
          f"| S3 Parse failure | parse_fail > 0.05 | {parse_fail_rate:.4f} | {'**YES**' if parse_fail_rate > S3_PARSE_FAIL else 'no'} |",
          f"| S4 Incomplete | n_valid < 200 | {n_valid} | {'**YES**' if n_valid < S4_N_VALID_MIN else 'no'} |",
          f"| S5 Degenerate | YES or NO rate > 0.95 | YES={yes_rate:.4f}, NO={no_rate:.4f} | {'**YES**' if (yes_rate > S5_DEGEN or no_rate > S5_DEGEN) else 'no'} |",
          f"| S6 Organic competence | det_viol ≥ 0.80 AND gap ≥ 0.10 | det_viol={det_violated:.4f}, gap={gap:+.4f} | {'**YES**' if (det_violated >= S6_DETECTION and gap >= S6_GAP_LOWER) else 'no'} |",
          "",
          "## Interpretation\n"]
    if triggers:
        sm.append("**PAUSE triggered.** Both-author review required before Amendment #3 drafting / re-confirmation.")
        sm.append("\nTriggered scenarios:")
        for t in triggers:
            sm.append(f"- {t}")
    else:
        sm.append("**No scenarios triggered.** V4-Pro near-floor behavior at V1-minimal confirmed at full Day -2 sample size. Path 1 cross-model lock holds.")
    SCENARIO_OUT.write_text("\n".join(sm))
    log(f"\nScenario evaluation: {SCENARIO_OUT.name}")

    # Persist full results
    results_doc = {
        "task": "Task 2 — V4-Pro Day -2 Verification at n=250",
        "date": "2026-05-12",
        "config": {
            "model": MODEL,
            "endpoint": BASE_URL,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
            "cutoff_k": CUTOFF_K,
            "extra_body": {"thinking": {"type": "disabled"}},
            "parser": "v2 4-stage cascade",
        },
        "metrics": {
            "n_attempted": n,
            "n_valid": n_valid,
            "errors": errors,
            "unparseable": unparseable,
            "parse_failure_rate": parse_fail_rate,
            "parse_stage_breakdown": dict(stage_counts),
            "finish_reason_distribution": dict(fr_dist),
            "mean_completion_tokens": mean_ct,
            "n_intact": len(intact_correct),
            "n_violated": len(violated_correct),
            "detection_rate_intact_correctness": det_intact,
            "detection_rate_violated_correctness": det_violated,
            "gap_spec_convention": gap,
            "cohens_h": h,
            "ci_95_gap": [ci_lo, ci_hi],
            "yes_rate_parsed": yes_rate,
            "no_rate_parsed": no_rate,
        },
        "scenarios_triggered": triggers,
        "elapsed_s_total": round(t_total, 2),
    }
    RESULTS_OUT.write_text(json.dumps(results_doc, indent=2))
    LOG_OUT.write_text("\n".join(log_lines) + "\n")
    return 0 if not triggers else 3


if __name__ == "__main__":
    sys.exit(main())
