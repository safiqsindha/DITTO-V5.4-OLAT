"""
Diagnostic I — V4-Flash + V4-Pro at max_tokens=4096 with CoT.

n=20 per model from the same first 20 rows of the seeded sample (which is
the prefix of the n=50 used in F and H). Same prompt, just lifted ceiling.
Purpose: characterize the natural completion-length distribution of CoT
reasoning so we can size the OLAT max_tokens correctly. Will reveal whether
2048 is enough or 4096 is needed.

Cost estimate: <$1 total at 4096 tokens.
"""

from __future__ import annotations

import json
import os
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

N_DIAGNOSTIC = 20
MAX_TOKENS = 4096
CUTOFF_K = 15
TEMPERATURE = 0.0
BASE_URL = "https://api.deepseek.com"
PER_CALL_TIMEOUT_S = 240.0
MAX_WORKERS = 4
MODELS = ["deepseek-v4-flash", "deepseek-v4-pro"]

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


def run_one(client, model, record):
    chain_path = Path(record["chain_path"])
    with chain_path.open() as f:
        chain = json.loads(f.readline())
    truncated = cutoff_rendered(chain["rendered"], CUTOFF_K)
    user_msg = build_user_prompt(truncated)
    t0 = time.monotonic()
    try:
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": user_msg}],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            extra_body={"thinking": {"type": "disabled"}},
        )
        text = (r.choices[0].message.content or "").strip()
        finish_reason = r.choices[0].finish_reason
        served_model = getattr(r, "model", "?")
        ct = r.usage.completion_tokens
        err = None
    except Exception as e:
        text, finish_reason, served_model, ct, err = "", None, None, None, f"{type(e).__name__}: {e}"
    elapsed = time.monotonic() - t0
    parsed_label, parse_stage = parse_response(text)
    gt_label = "YES" if record["ground_truth"] == "violated" else "NO"
    correct = (parsed_label == gt_label) if parsed_label is not None else None
    return {
        "model": model,
        "chain_id": record["chain_id"],
        "ground_truth": record["ground_truth"],
        "ground_truth_label": gt_label,
        "kind": record["kind"],
        "raw_response": text,
        "parsed_label": parsed_label,
        "parse_stage": parse_stage,
        "correct": correct,
        "finish_reason": finish_reason,
        "completion_tokens": ct,
        "elapsed_s": round(elapsed, 2),
        "error": err,
        "served_model": served_model,
    }


def summarize(label, rows):
    parsed = [r for r in rows if r["parsed_label"] is not None]
    unp = [r for r in rows if r["parse_stage"] == "unparseable"]
    cts = [r["completion_tokens"] for r in rows if r["completion_tokens"]]
    parsed_cts = [r["completion_tokens"] for r in parsed]

    print(f"\n=== {label} ===")
    print(f"  n={len(rows)}  parsed={len(parsed)}  unparseable={len(unp)}")
    if cts:
        cts_sorted = sorted(cts)
        print(f"  completion_tokens (ALL): min={min(cts)}, max={max(cts)}, median={cts_sorted[len(cts)//2]}")
    if parsed_cts:
        pcts = sorted(parsed_cts)
        print(f"  completion_tokens (PARSED): min={min(parsed_cts)}, max={max(parsed_cts)}, "
              f"median={pcts[len(pcts)//2]}, p75={pcts[3*len(pcts)//4]}, p90={pcts[int(0.9*len(pcts))] if len(pcts)>=10 else pcts[-1]}")

    # finish_reason distribution
    fr = Counter(r["finish_reason"] for r in rows)
    print(f"  finish_reason: {dict(fr)}")
    print(f"  parse_stage:   {dict(Counter(r['parse_stage'] for r in rows))}")
    print(f"  label:         {dict(Counter(r['parsed_label'] for r in rows))}")

    # accuracy among parsed
    p_int_p = [r["correct"] for r in parsed if r["ground_truth"] == "intact"]
    p_vio_p = [r["correct"] for r in parsed if r["ground_truth"] == "violated"]
    if p_int_p:
        print(f"  det_rate_intact (parsed): {sum(p_int_p)/len(p_int_p):.3f} ({sum(p_int_p)}/{len(p_int_p)})")
    if p_vio_p:
        print(f"  det_rate_violated (parsed): {sum(p_vio_p)/len(p_vio_p):.3f} ({sum(p_vio_p)}/{len(p_vio_p)})")

    # responses near or at 4096
    if parsed_cts:
        hit_cap = sum(1 for c in parsed_cts if c >= 4090)
        print(f"  parsed responses near max_tokens cap (>=4090): {hit_cap}")
    return {"parsed_cts": parsed_cts, "all_cts": cts, "n_parsed": len(parsed), "n_unp": len(unp)}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    load_env(ENV_PATH)
    key = os.environ["DEEPSEEK_API_KEY"]
    print(f"=== Diagnostic I — unbounded CoT (max_tokens={MAX_TOKENS}, k={CUTOFF_K}, n={N_DIAGNOSTIC}) ===")
    print(f"Key prefix: {key[:8]}...")
    print(f"Models: {', '.join(MODELS)}")

    samples = []
    with SAMPLE_PATH.open() as f:
        for line in f:
            samples.append(json.loads(line))
    sub = samples[:N_DIAGNOSTIC]
    n_int = sum(1 for s in sub if s["ground_truth"] == "intact")
    print(f"Sample: {n_int} intact / {N_DIAGNOSTIC - n_int} violated")

    client = OpenAI(api_key=key, base_url=BASE_URL, timeout=PER_CALL_TIMEOUT_S)

    all_results = {m: [] for m in MODELS}
    for model in MODELS:
        print(f"\nRunning {model} (max_tokens={MAX_TOKENS})...")
        t0 = time.monotonic()
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futures = [ex.submit(run_one, client, model, s) for s in sub]
            for i, fut in enumerate(as_completed(futures), 1):
                all_results[model].append(fut.result())
                if i % 5 == 0 or i == len(sub):
                    print(f"  {i}/{len(sub)} (elapsed {time.monotonic()-t0:.1f}s)")
        print(f"  {model} complete in {time.monotonic()-t0:.1f}s")

    # Persist raw
    for model in MODELS:
        tag = model.replace("deepseek-v4-", "")
        raw_path = OUT_DIR / f"diagnostic_I_{tag}_raw.ndjson"
        with raw_path.open("w") as f:
            for r in all_results[model]:
                f.write(json.dumps(r) + "\n")
        print(f"Saved: {raw_path}")

    # Summarize
    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    summaries = {}
    for model in MODELS:
        summaries[model] = summarize(f"{model} + CoT @ max_tokens={MAX_TOKENS}", all_results[model])

    # Decision support output
    print("\n" + "=" * 72)
    print("max_tokens budget guidance")
    print("=" * 72)
    for model in MODELS:
        pcts = summaries[model]["parsed_cts"]
        if not pcts:
            print(f"  {model}: no parsed responses")
            continue
        max_p = max(pcts)
        print(f"  {model}: parsed max completion={max_p}")
        if max_p < 1024:
            print(f"    → 1024 is safe with headroom")
        elif max_p < 1500:
            print(f"    → 2048 is safe with comfortable margin")
        elif max_p < 2048:
            print(f"    → 2048 is borderline (no headroom); recommend 3072")
        elif max_p < 3072:
            print(f"    → 4096 is safe with margin; 2048 is insufficient")
        else:
            print(f"    → use 4096+ (longer reasoning observed)")

    # Save summary
    summary_doc = {
        "diagnostic": "I",
        "config": {"models": MODELS, "max_tokens": MAX_TOKENS, "k": CUTOFF_K, "n": N_DIAGNOSTIC},
        "per_model": {
            model: {
                "n": len(rows),
                "parsed": summaries[model]["n_parsed"],
                "unparseable": summaries[model]["n_unp"],
                "completion_tokens_all": summaries[model]["all_cts"],
                "completion_tokens_parsed": summaries[model]["parsed_cts"],
            }
            for model, rows in all_results.items()
        },
    }
    (OUT_DIR / "diagnostic_I_summary.json").write_text(json.dumps(summary_doc, indent=2))


if __name__ == "__main__":
    main()
