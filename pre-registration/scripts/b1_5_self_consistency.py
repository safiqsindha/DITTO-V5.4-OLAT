#!/usr/bin/env python3
"""
Priority B1.5 — Self-Consistency Baseline

20 chains (10 intact, 10 violated) from A3 selection (seed=42)
Conditions: L18 L3 at T=0 (baseline) and L18 L3 at T=0.7 with N=5 samples (majority vote)
Model: V4-Pro
Output: pre-registration/self_consistency/
"""

import csv
import json
import os
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
PREREGISTRATION = SCRIPT_DIR.parent
ENV_PATH = PREREGISTRATION.parent / ".env"
load_dotenv(ENV_PATH)

CHAIN_VARIANTS_DIR = PREREGISTRATION / "chain_variants" / "deepseek-v4-pro"
CHECKER_VERDICTS_CSV = PREREGISTRATION / "tool_augmentation_prep" / "checker_verdicts.csv"
OUT_DIR = PREREGISTRATION / "self_consistency"

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL = "deepseek-v4-pro"
MAX_TOKENS = 1024
N_SAMPLES = 5
SEED = 42

_RE_STRICT = re.compile(r'(?:Therefore,\s+)?[Tt]he answer is\s+(YES|NO)\b')
_RE_PERMISSIVE = re.compile(r'(?i)(?:answer is|answer:|conclusion:)\s*(yes|no)\b')
_RE_MD_STRIP = re.compile(r'[*_`]+')
_RE_LAST_TOKEN = re.compile(r'(YES|NO)\b[\s.,!?)\]]*$', re.IGNORECASE)


def parse_content(content):
    if not content:
        return None, 'unparseable'
    m = _RE_STRICT.search(content)
    if m:
        return m.group(1).upper(), 'strict'
    m = _RE_PERMISSIVE.search(content)
    if m:
        return m.group(1).upper(), 'permissive'
    stripped = _RE_MD_STRIP.sub('', content)
    m = _RE_PERMISSIVE.search(stripped)
    if m:
        return m.group(1).upper(), 'md_strip'
    tail = stripped[-200:]
    m = _RE_LAST_TOKEN.search(tail)
    if m:
        return m.group(1).upper(), 'last_token'
    return None, 'unparseable'


def build_client():
    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai package not installed")
        sys.exit(1)
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


def call_api(client, prompt, temperature):
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=MAX_TOKENS,
                extra_body={"thinking": {"type": "disabled"}},
            )
            return resp
        except Exception as exc:
            code = getattr(exc, 'status_code', None)
            if code in {429, 500, 502, 503, 504} and attempt < 2:
                wait = 5 * (2 ** attempt)
                print(f"  [retry] code={code}, sleeping {wait}s")
                time.sleep(wait)
                continue
            return None
    return None


def select_chains(all_chains, seed=42):
    """Select 10 intact + 10 violated using seed=42."""
    random.seed(seed)
    intact = [r for r in all_chains if r["GT_L3_symbolic"] == "False"]
    violated = [r for r in all_chains if r["GT_L3_symbolic"] == "True"]
    random.shuffle(intact)
    random.shuffle(violated)
    selected = intact[:10] + violated[:10]
    random.shuffle(selected)
    return selected


def get_l18_l3_prompt(chain_id):
    """Get the full L18 L3 prompt (CoT) for this chain."""
    path = CHAIN_VARIANTS_DIR / "pro_L18_L3" / f"{chain_id}.json"
    with open(path) as f:
        v = json.load(f)
    return v["prompt_user"], v.get("ground_truth", {})


def run_calls(client, chains):
    """Run all calls: single-sample T=0 and 5-sample T=0.7 for each chain."""
    out_path = OUT_DIR / "raw_responses.ndjson"
    done = set()  # (chain_id, temperature, sample_idx)
    if out_path.exists():
        with open(out_path) as f:
            for line in f:
                r = json.loads(line)
                done.add((r["chain_id"], r["temperature"], r["sample_idx"]))

    total_planned = len(chains) * (1 + N_SAMPLES)
    print(f"Planned: {total_planned} API calls ({len(chains)} chains × (1 + {N_SAMPLES}))")
    print(f"Already done: {len(done)}")

    count = 0
    with open(out_path, "a") as fout:
        for chain_row in chains:
            chain_id = chain_row["chain_id"]
            gt_violated = chain_row["GT_L3_symbolic"] == "True"
            prompt, gt_dict = get_l18_l3_prompt(chain_id)

            # Single-sample T=0 baseline
            key0 = (chain_id, 0.0, 0)
            if key0 not in done:
                count += 1
                print(f"  [{count}/{total_planned}] {chain_id} T=0 s0")
                t0 = time.time()
                resp = call_api(client, prompt, 0.0)
                elapsed = round(time.time() - t0, 2)
                rec = _make_record(chain_id, gt_violated, 0.0, 0, resp, elapsed)
                fout.write(json.dumps(rec) + "\n")
                fout.flush()
                time.sleep(0.3)

            # 5 samples T=0.7
            for si in range(N_SAMPLES):
                key_si = (chain_id, 0.7, si)
                if key_si not in done:
                    count += 1
                    print(f"  [{count}/{total_planned}] {chain_id} T=0.7 s{si}")
                    t0 = time.time()
                    resp = call_api(client, prompt, 0.7)
                    elapsed = round(time.time() - t0, 2)
                    rec = _make_record(chain_id, gt_violated, 0.7, si, resp, elapsed)
                    fout.write(json.dumps(rec) + "\n")
                    fout.flush()
                    time.sleep(0.3)


def _make_record(chain_id, gt_violated, temperature, sample_idx, resp, elapsed):
    if resp is None:
        return {
            "chain_id": chain_id, "gt_l3_symbolic": gt_violated,
            "temperature": temperature, "sample_idx": sample_idx,
            "api_failure": True, "content": None,
            "parsed_label": None, "parse_stage": "api_failure",
            "elapsed": elapsed,
        }
    choice = resp.choices[0]
    content = getattr(choice.message, "content", "") or ""
    finish_reason = getattr(choice, "finish_reason", None)
    usage = None
    if hasattr(resp, "usage") and resp.usage:
        usage = {
            "input_tokens": resp.usage.prompt_tokens,
            "output_tokens": resp.usage.completion_tokens,
        }
    parsed_label, parse_stage = parse_content(content)
    return {
        "chain_id": chain_id, "gt_l3_symbolic": gt_violated,
        "temperature": temperature, "sample_idx": sample_idx,
        "api_failure": False, "content": content,
        "parsed_label": parsed_label, "parse_stage": parse_stage,
        "finish_reason": finish_reason, "usage": usage, "elapsed": elapsed,
    }


def analyze_results(chains):
    out_path = OUT_DIR / "raw_responses.ndjson"
    all_recs = []
    with open(out_path) as f:
        for line in f:
            all_recs.append(json.loads(line))

    chain_ids = {r["chain_id"] for r in all_recs}
    rows = []
    for chain_row in chains:
        chain_id = chain_row["chain_id"]
        gt_violated = chain_row["GT_L3_symbolic"] == "True"

        # Single-sample T=0
        t0_recs = [r for r in all_recs if r["chain_id"] == chain_id
                   and r["temperature"] == 0.0 and not r["api_failure"]]
        t0_label = t0_recs[0]["parsed_label"] if t0_recs else None

        # 5-sample T=0.7 majority vote
        t07_recs = [r for r in all_recs if r["chain_id"] == chain_id
                    and r["temperature"] == 0.7 and not r["api_failure"]]
        t07_labels = [r["parsed_label"] for r in t07_recs if r["parsed_label"]]
        if t07_labels:
            votes = Counter(t07_labels)
            majority_label = votes.most_common(1)[0][0]
            majority_pct = votes.most_common(1)[0][1] / len(t07_labels)
        else:
            majority_label = None
            majority_pct = None

        rows.append({
            "chain_id": chain_id,
            "gt_l3_symbolic": gt_violated,
            "t0_single_label": t0_label,
            "t07_n_samples": len(t07_labels),
            "t07_votes_yes": t07_labels.count("YES"),
            "t07_votes_no": t07_labels.count("NO"),
            "t07_majority_label": majority_label,
            "t07_majority_pct": round(majority_pct, 3) if majority_pct else None,
            "t0_correct": (t0_label == "YES") == gt_violated if t0_label else None,
            "t07_correct": (majority_label == "YES") == gt_violated if majority_label else None,
        })

    # Compute aggregate metrics
    intact = [r for r in rows if not r["gt_l3_symbolic"]]
    violated = [r for r in rows if r["gt_l3_symbolic"]]

    def recall(recs, key):
        valid = [r for r in recs if r[key] is not None]
        if not valid:
            return None
        return round(sum(1 for r in valid if r[key]) / len(valid), 4)

    metrics = {
        "n_intact": len(intact),
        "n_violated": len(violated),
        "t0_recall_violated": recall(violated, "t0_correct"),
        "t07_recall_violated": recall(violated, "t07_correct"),
        "t0_specificity_intact": recall(intact, "t0_correct"),
        "t07_specificity_intact": recall(intact, "t07_correct"),
    }

    recall_gain = None
    if metrics["t0_recall_violated"] is not None and metrics["t07_recall_violated"] is not None:
        recall_gain = round(metrics["t07_recall_violated"] - metrics["t0_recall_violated"], 4)
    metrics["recall_gain_majority_vote"] = recall_gain

    return rows, metrics


def write_effect_table(rows, metrics):
    path = OUT_DIR / "effect_table_self_consistency.csv"
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {path}")


def write_summary(rows, metrics):
    path = OUT_DIR / "summary.md"
    gain = metrics.get("recall_gain_majority_vote")
    if gain is not None:
        if gain > 0.10:
            outcome = "Outcome 1: Majority vote substantially improves recall (>0.10 gain) → ceiling is partly stochastic"
        elif abs(gain) < 0.05:
            outcome = "Outcome 2: Majority vote produces minimal change (<0.05 gain) → ceiling is capability-limited"
        elif gain < -0.05:
            outcome = "Outcome 3: Majority vote reduces recall → investigate parse failures"
        else:
            outcome = f"Intermediate: recall gain = {gain:.3f} (0.05–0.10 range)"
    else:
        outcome = "Unknown — insufficient data"

    lines = [
        "# B1.5 — Self-Consistency Baseline Summary\n",
        "## Aggregate Metrics\n",
        f"| Metric | Value |",
        f"|---|---|",
        f"| N intact | {metrics['n_intact']} |",
        f"| N violated | {metrics['n_violated']} |",
        f"| T=0 recall (violated) | {metrics['t0_recall_violated']} |",
        f"| T=0.7 majority-vote recall (violated) | {metrics['t07_recall_violated']} |",
        f"| Recall gain from majority vote | {gain} |",
        f"| T=0 specificity (intact) | {metrics['t0_specificity_intact']} |",
        f"| T=0.7 majority specificity (intact) | {metrics['t07_specificity_intact']} |",
        f"\n## Pre-Registered Outcome: **{outcome}**\n",
        "## Interpretation\n",
    ]
    if gain is not None and gain > 0.10:
        lines.append(
            "The ceiling is partly stochastic — the model has the capability to detect more "
            "violations but doesn't reliably do so in a single forward pass. Majority vote "
            "over multiple samples recovers this latent signal. This suggests ensemble "
            "methods could improve recall without additional prompt engineering."
        )
    elif gain is not None and abs(gain) < 0.05:
        lines.append(
            "The detection ceiling is capability-limited, not stochastic. Multiple samples "
            "at T=0.7 do not improve recall over a single T=0 sample. The bottleneck is "
            "representational — the model lacks the chain-pattern-matching needed to detect "
            "violations regardless of sampling strategy."
        )
    path.write_text("\n".join(lines) + "\n")
    print(f"  Wrote {path}")


def main():
    if not DEEPSEEK_API_KEY:
        print("ERROR: DEEPSEEK_API_KEY not set")
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(CHECKER_VERDICTS_CSV) as f:
        all_chains = list(csv.DictReader(f))

    chains = select_chains(all_chains, seed=SEED)
    intact_cnt = sum(1 for r in chains if r["GT_L3_symbolic"] == "False")
    violated_cnt = sum(1 for r in chains if r["GT_L3_symbolic"] == "True")
    print(f"Selected {len(chains)} chains: {intact_cnt} intact, {violated_cnt} violated (seed=42)")

    client = build_client()
    run_calls(client, chains)

    rows, metrics = analyze_results(chains)
    write_effect_table(rows, metrics)
    write_summary(rows, metrics)

    print("\n=== B1.5 Complete ===")
    print(f"Recall gain (majority vote): {metrics.get('recall_gain_majority_vote')}")


if __name__ == "__main__":
    main()
