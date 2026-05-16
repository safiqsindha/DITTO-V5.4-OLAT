#!/usr/bin/env python3
"""
Priority B1.7 — Prompt Robustness Test

20 chains (10 intact, 10 violated), seed=43
4 prompt variants × 2 regimes × 20 chains = 160 API calls
Regimes: V1-minimal (L01_L1) and L18 L4 (thinking enabled, max_tokens=4096)
Output: pre-registration/prompt_robustness/
"""

import concurrent.futures
import csv
import json
import os
import random
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
PREREGISTRATION = SCRIPT_DIR.parent
ENV_PATH = PREREGISTRATION.parent / ".env"
load_dotenv(ENV_PATH)

CHAIN_VARIANTS_DIR = PREREGISTRATION / "chain_variants" / "deepseek-v4-pro"
CHECKER_VERDICTS_CSV = PREREGISTRATION / "tool_augmentation_prep" / "checker_verdicts.csv"
OUT_DIR = PREREGISTRATION / "prompt_robustness"

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL = "deepseek-v4-pro"
SEED = 43

_RE_STRICT = re.compile(r'(?:Therefore,\s+)?[Tt]he answer is\s+(YES|NO)\b')
_RE_PERMISSIVE = re.compile(r'(?i)(?:answer is|answer:|conclusion:)\s*(yes|no)\b')
_RE_MD_STRIP = re.compile(r'[*_`]+')
_RE_LAST_TOKEN = re.compile(r'(YES|NO)\b[\s.,!?)\]]*$', re.IGNORECASE)

# --- Variant definitions ---
# V0: Original OLAT prompt (L18 L3 CoT style)
# V1: Light paraphrase (same semantics, different wording)
# V2: Consistency framing (semantic inversion — YES means "consistent" = no violation)
# V3: Formatting perturbation (bullet points instead of paragraph)

VARIANT_QUESTIONS = {
    "V0": (
        "Does this battle chain contain any rule violations? "
        "Review the chain event by event. For each event, check whether it conforms "
        "to the rules of Pokemon battles. Identify any event that violates a rule. "
        "Therefore, the answer is YES or NO."
    ),
    "V1": (
        "Examine the sequence of battle events above. For each step, determine whether "
        "it follows the rules governing Pokemon battles. If any step breaks a rule, "
        "the answer is YES; otherwise, the answer is NO."
    ),
    "V2": (
        "Is this sequence of battle events internally consistent with the rules of "
        "Pokemon battles? Answer YES if all events are consistent, NO if any event "
        "violates a rule."
    ),
    "V3": (
        "Check the chain above for rule violations:\n"
        "- Go through each event one by one\n"
        "- Check if each event follows Pokemon battle rules\n"
        "- Identify any event that breaks a rule\n"
        "The answer is YES or NO."
    ),
}

# V2 requires semantic inversion: YES = no violation, NO = violation
# For scoring V2: parsed YES → treated as NO violation → correct if GT=False
# For scoring V2: parsed NO → treated as violation → correct if GT=True
VARIANT_INVERSION = {"V0": False, "V1": False, "V2": True, "V3": False}


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


def semantic_label(parsed_label, variant):
    """Apply semantic inversion for V2. Returns violation_detected: True/False."""
    if parsed_label is None:
        return None
    is_yes = (parsed_label == "YES")
    if VARIANT_INVERSION[variant]:
        # V2: YES = "consistent" = NO violation
        return not is_yes
    else:
        return is_yes


def build_client():
    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai package not installed")
        sys.exit(1)
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com", timeout=300)


def call_api(client, prompt, regime):
    """regime: 'v1_minimal' or 'l18_l4'"""
    if regime == "v1_minimal":
        kwargs = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 32,
            "extra_body": {"thinking": {"type": "disabled"}},
        }
    else:  # l18_l4
        kwargs = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 4096,
            "extra_body": {"thinking": {"type": "enabled"}},
        }
    for attempt in range(3):
        try:
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            future = executor.submit(client.chat.completions.create, **kwargs)
            try:
                resp = future.result(timeout=300)
            except concurrent.futures.TimeoutError:
                print(f"    [TIMEOUT] {regime} attempt {attempt+1} — skipping call")
                executor.shutdown(wait=False)
                return None
            executor.shutdown(wait=False)
            return resp
        except Exception as exc:
            code = getattr(exc, 'status_code', None)
            if code in {429, 500, 502, 503, 504} and attempt < 2:
                wait = 5 * (2 ** attempt)
                time.sleep(wait)
                continue
            return None
    return None


def get_chain_text(chain_id, regime):
    """Get chain text (steps only) for the given regime."""
    if regime == "v1_minimal":
        # Use L01_L1 variant (minimal field schema, v1_minimal condition)
        path = CHAIN_VARIANTS_DIR / "pro_L01_L1" / f"{chain_id}.json"
    else:
        # Use L18_L3 variant for chain text (standard field schema)
        path = CHAIN_VARIANTS_DIR / "pro_L18_L3" / f"{chain_id}.json"

    with open(path) as f:
        v = json.load(f)
    prompt_user = v["prompt_user"]
    # Strip question
    for marker in ["\nDoes this battle chain", "\nExamine the sequence", "\nIs this sequence"]:
        if marker in prompt_user:
            return prompt_user[:prompt_user.index(marker)].strip()
    return prompt_user.strip()


def build_prompt(chain_text, variant):
    return f"{chain_text}\n\n{VARIANT_QUESTIONS[variant]}"


def select_chains(all_chains, seed=43):
    random.seed(seed)
    intact = [r for r in all_chains if r["GT_L3_symbolic"] == "False"]
    violated = [r for r in all_chains if r["GT_L3_symbolic"] == "True"]
    random.shuffle(intact)
    random.shuffle(violated)
    return intact[:10] + violated[:10]


def run_all(client, chains):
    out_path = OUT_DIR / "raw_responses.ndjson"
    done = set()
    if out_path.exists():
        with open(out_path) as f:
            for line in f:
                r = json.loads(line)
                done.add((r["chain_id"], r["variant"], r["regime"]))

    regimes = ["v1_minimal", "l18_l4"]
    variants = ["V0", "V1", "V2", "V3"]
    total = len(chains) * len(variants) * len(regimes)
    print(f"Planned: {total} calls ({len(chains)} chains × {len(variants)} variants × {len(regimes)} regimes)")
    print(f"Already done: {len(done)}")

    count = 0
    with open(out_path, "a") as fout:
        for chain_row in chains:
            chain_id = chain_row["chain_id"]
            gt_violated = chain_row["GT_L3_symbolic"] == "True"

            for regime in regimes:
                chain_text = get_chain_text(chain_id, regime)
                for variant in variants:
                    key = (chain_id, variant, regime)
                    if key in done:
                        continue
                    count += 1
                    print(f"  [{count}/{total}] {chain_id} {variant} {regime}")

                    prompt = build_prompt(chain_text, variant)
                    t0 = time.time()
                    resp = call_api(client, prompt, regime)
                    elapsed = round(time.time() - t0, 2)

                    rec = _make_record(chain_id, gt_violated, variant, regime, resp, elapsed)
                    fout.write(json.dumps(rec) + "\n")
                    fout.flush()
                    time.sleep(0.4)


def _make_record(chain_id, gt_violated, variant, regime, resp, elapsed):
    base = {
        "chain_id": chain_id, "gt_l3_symbolic": gt_violated,
        "variant": variant, "regime": regime,
        "semantic_inverted": VARIANT_INVERSION[variant],
    }
    if resp is None:
        return {**base, "api_failure": True, "content": None,
                "parsed_label": None, "parse_stage": "api_failure",
                "violation_detected": None, "elapsed": elapsed}
    choice = resp.choices[0]
    content = getattr(choice.message, "content", "") or ""
    finish_reason = getattr(choice, "finish_reason", None)
    usage = None
    if hasattr(resp, "usage") and resp.usage:
        usage = {"input_tokens": resp.usage.prompt_tokens,
                 "output_tokens": resp.usage.completion_tokens}
    parsed_label, parse_stage = parse_content(content)
    violation_detected = semantic_label(parsed_label, variant)
    correct = (violation_detected == gt_violated) if violation_detected is not None else None
    return {**base, "api_failure": False, "content": content,
            "parsed_label": parsed_label, "parse_stage": parse_stage,
            "violation_detected": violation_detected, "correct": correct,
            "finish_reason": finish_reason, "usage": usage, "elapsed": elapsed}


def analyze_results(chains):
    out_path = OUT_DIR / "raw_responses.ndjson"
    all_recs = []
    with open(out_path) as f:
        for line in f:
            all_recs.append(json.loads(line))

    regimes = ["v1_minimal", "l18_l4"]
    variants = ["V0", "V1", "V2", "V3"]

    # Per-variant, per-regime detection rates
    results = {}
    for regime in regimes:
        for variant in variants:
            recs = [r for r in all_recs if r["regime"] == regime and r["variant"] == variant
                    and not r.get("api_failure") and r.get("violation_detected") is not None]
            intact = [r for r in recs if not r["gt_l3_symbolic"]]
            violated = [r for r in recs if r["gt_l3_symbolic"]]

            def dr(subset):
                if not subset:
                    return None
                return round(sum(1 for r in subset if r["violation_detected"]) / len(subset), 4)

            results[(regime, variant)] = {
                "regime": regime, "variant": variant, "n": len(recs),
                "n_intact": len(intact), "n_violated": len(violated),
                "dr_intact": dr(intact), "dr_violated": dr(violated),
                "gap": round(dr(violated) - dr(intact), 4)
                       if dr(intact) is not None and dr(violated) is not None else None,
            }

    return results


def write_effect_table(results):
    path = OUT_DIR / "effect_table_per_variant.csv"
    rows = list(results.values())
    if rows:
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    print(f"  Wrote {path}")


def write_surface_robustness(results):
    """V0 vs V1 vs V3 (same semantics) per regime."""
    path = OUT_DIR / "surface_robustness_summary.md"
    lines = [
        "# B1.7 — Surface Robustness (Variants 0, 1, 3)\n",
        "Compares V0 (control), V1 (light paraphrase), V3 (formatting perturbation).\n",
        "Same semantics — effects should persist if regime effects are robust.\n",
    ]
    for regime in ["v1_minimal", "l18_l4"]:
        lines.append(f"\n## Regime: {regime}\n")
        lines.append("| Variant | N | dr_intact | dr_violated | gap |")
        lines.append("|---|---|---|---|---|")
        for v in ["V0", "V1", "V3"]:
            r = results.get((regime, v), {})
            lines.append(
                f"| {v} | {r.get('n','?')} | {r.get('dr_intact','?')} | "
                f"{r.get('dr_violated','?')} | {r.get('gap','?')} |"
            )
        # Assess robustness
        gaps = [results.get((regime, v), {}).get("gap") for v in ["V0", "V1", "V3"]
                if results.get((regime, v), {}).get("gap") is not None]
        if gaps:
            gap_range = max(gaps) - min(gaps)
            if gap_range < 0.10:
                lines.append(f"\n**Robust** — gap range {gap_range:.3f} < 0.10 across V0/V1/V3")
            else:
                lines.append(f"\n**Fragile** — gap range {gap_range:.3f} ≥ 0.10 across V0/V1/V3")

    path.write_text("\n".join(lines) + "\n")
    print(f"  Wrote {path}")


def write_semantic_robustness(results):
    """V0 vs V2 (with inversion)."""
    path = OUT_DIR / "semantic_robustness_summary.md"
    lines = [
        "# B1.7 — Semantic Robustness (Variant 0 vs Variant 2)\n",
        "V2 uses consistency framing (YES=consistent=no violation).\n",
        "Semantic inversion applied: V2 YES → violation_detected=False.\n",
    ]
    for regime in ["v1_minimal", "l18_l4"]:
        lines.append(f"\n## Regime: {regime}\n")
        lines.append("| Variant | N | dr_intact | dr_violated | gap |")
        lines.append("|---|---|---|---|---|")
        for v in ["V0", "V2"]:
            r = results.get((regime, v), {})
            lines.append(
                f"| {v} | {r.get('n','?')} | {r.get('dr_intact','?')} | "
                f"{r.get('dr_violated','?')} | {r.get('gap','?')} |"
            )
        r0 = results.get((regime, "V0"), {})
        r2 = results.get((regime, "V2"), {})
        g0 = r0.get("gap")
        g2 = r2.get("gap")
        if g0 is not None and g2 is not None:
            delta = abs(g0 - g2)
            if delta < 0.10:
                lines.append(f"\n**Semantically robust** — gap delta {delta:.3f} < 0.10")
            else:
                lines.append(f"\n**Semantic framing matters** — gap delta {delta:.3f} ≥ 0.10")

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
    print(f"Selected {len(chains)} chains: {intact_cnt} intact, {violated_cnt} violated (seed=43)")

    client = build_client()
    run_all(client, chains)

    results = analyze_results(chains)
    write_effect_table(results)
    write_surface_robustness(results)
    write_semantic_robustness(results)

    print("\n=== B1.7 Complete ===")
    # Print summary table
    for regime in ["v1_minimal", "l18_l4"]:
        print(f"\n  Regime: {regime}")
        for v in ["V0", "V1", "V2", "V3"]:
            r = results.get((regime, v), {})
            print(f"    {v}: dr_intact={r.get('dr_intact')}, "
                  f"dr_violated={r.get('dr_violated')}, gap={r.get('gap')}")


if __name__ == "__main__":
    main()
