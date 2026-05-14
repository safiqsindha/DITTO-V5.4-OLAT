#!/usr/bin/env python3
"""
Task 2A.2: Second pilot — confirm intact-chain edge case at max_tokens=4096.

The first pilot at 2048 tokens truncated 2/10 calls, both on the same chain:
  gen9ou-2262855067_p1 (the only non-shuffled / likely-intact chain in pilot 1).

This second pilot reruns just that chain on both Flash and Pro at 4096 tokens.

Outputs:
  amendment_7_pilot/raw_responses_pilot2.ndjson
  amendment_7_pilot/pilot2_summary.md
"""
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path("/Users/safiqsindha/Desktop/Project Ditto/Ditto-5.4-OLAT/pre-registration")
ENV_PATH = ROOT.parent / ".env"
VARIANTS_DIR = ROOT / "chain_variants"
PILOT_DIR = ROOT / "amendment_7_pilot"

SPEC_HASH = "dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8"
PILOT2_MAX_TOKENS = 4096
TARGET_CHAIN = "gen9ou-2262855067_p1"


def load_env():
    if ENV_PATH.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(ENV_PATH)
        except ImportError:
            with open(ENV_PATH) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, _, v = line.partition('=')
                        os.environ.setdefault(k.strip(), v.strip().strip('"\''))
    return os.environ.get('DEEPSEEK_API_KEY')


def call_api(client, model, prompt, max_tokens):
    retries = 3
    backoff = 5.0
    for attempt in range(retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=max_tokens,
                extra_body={"thinking": {"type": "enabled"}},
            )
            return resp, None
        except Exception as exc:
            code = getattr(exc, "status_code", None)
            if code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(backoff * (2 ** attempt))
                continue
            return None, str(code if code is not None else type(exc).__name__)
    return None, "max_retries_exceeded"


def main():
    api_key = load_env()
    if not api_key:
        print("ERROR: DEEPSEEK_API_KEY not set")
        sys.exit(1)

    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    # Load just the target chain for flash + pro
    pilot_variants = []
    for model_subdir, prefix in [("deepseek-v4-flash", "flash"),
                                  ("deepseek-v4-pro", "pro")]:
        vf = VARIANTS_DIR / model_subdir / f"{prefix}_L18_L4" / f"{TARGET_CHAIN}.json"
        with open(vf) as f:
            v = json.load(f)
        pilot_variants.append(v)

    print(f"Loaded {len(pilot_variants)} pilot-2 variants (target chain: {TARGET_CHAIN})")
    print(f"max_tokens override: {PILOT2_MAX_TOKENS}")
    print()

    out_path = PILOT_DIR / "raw_responses_pilot2.ndjson"
    records = []
    with open(out_path, "w") as fout:
        for i, v in enumerate(pilot_variants, 1):
            print(f"[{i}/{len(pilot_variants)}] {v['condition_id']} chain={v['chain_id']}")
            t0 = time.time()
            resp, err = call_api(client, v["api_params"]["model"],
                                 v["prompt_user"], PILOT2_MAX_TOKENS)
            elapsed = time.time() - t0

            if err:
                rec = {
                    "condition_id": v["condition_id"],
                    "sample_id": v["chain_id"],
                    "model": v["model"],
                    "max_tokens_used": PILOT2_MAX_TOKENS,
                    "amendment_7_pilot2": True,
                    "api_failure": True,
                    "api_error_code": err,
                    "content": None,
                    "reasoning_content": None,
                    "finish_reason": None,
                    "usage": None,
                    "elapsed_seconds": round(elapsed, 2),
                    "spec_hash": SPEC_HASH,
                }
                print(f"  FAIL: {err} ({elapsed:.1f}s)")
            else:
                choice = resp.choices[0]
                content = getattr(choice.message, "content", "") or ""
                reasoning = getattr(choice.message, "reasoning_content", None)
                finish = getattr(choice, "finish_reason", None)
                usage = None
                if getattr(resp, "usage", None):
                    usage = {
                        "input_tokens": resp.usage.prompt_tokens,
                        "output_tokens": resp.usage.completion_tokens,
                    }
                rec = {
                    "condition_id": v["condition_id"],
                    "sample_id": v["chain_id"],
                    "model": v["model"],
                    "max_tokens_used": PILOT2_MAX_TOKENS,
                    "amendment_7_pilot2": True,
                    "api_failure": False,
                    "api_error_code": None,
                    "content": content,
                    "reasoning_content": reasoning,
                    "finish_reason": finish,
                    "usage": usage,
                    "elapsed_seconds": round(elapsed, 2),
                    "spec_hash": SPEC_HASH,
                }
                print(f"  OK: finish={finish}, content='{content[:30]}', "
                      f"output_tokens={usage['output_tokens'] if usage else '?'}, "
                      f"reasoning_len={len(reasoning) if reasoning else 0} chars ({elapsed:.1f}s)")

            fout.write(json.dumps(rec) + "\n")
            fout.flush()
            records.append(rec)

    # Classify
    n_total = len(records)
    n_with_content = sum(1 for r in records
                         if not r["api_failure"] and r["content"] and len(r["content"]) > 0)
    n_finish_stop = sum(1 for r in records if not r["api_failure"] and r["finish_reason"] == "stop")
    n_finish_length = sum(1 for r in records if not r["api_failure"] and r["finish_reason"] == "length")

    if n_with_content == n_total and n_finish_stop == n_total:
        outcome = "PASS"
        outcome_detail = (
            f"All {n_total} calls completed with parseable verdicts at max_tokens=4096. "
            "Authorize Task 2B (full retest at 4096)."
        )
    elif n_with_content >= 1:
        outcome = "PARTIAL"
        outcome_detail = (
            f"{n_with_content}/{n_total} parseable. Some intact-chain edge cases remain truncated at 4096. "
            "Surface to user before full retest."
        )
    else:
        outcome = "FAIL"
        outcome_detail = (
            f"Both calls still truncated at 4096 tokens. "
            "Intact-chain reasoning under L18 L4 may exceed any reasonable token budget."
        )

    # Cost
    total_input = sum(r["usage"]["input_tokens"] for r in records if r["usage"])
    total_output = sum(r["usage"]["output_tokens"] for r in records if r["usage"])
    est_cost = (total_input * 0.27 / 1e6) + (total_output * 16.0 / 1e6)

    # Write summary
    lines = []
    lines.append("# Amendment #7 Pilot 2 — Intact-Chain Edge Case at max_tokens=4096")
    lines.append("")
    lines.append(f"**SPEC hash:** `{SPEC_HASH}`")
    lines.append("**Generated:** 2026-05-13")
    lines.append(f"**Target chain:** `{TARGET_CHAIN}` (the chain that truncated for both Flash and Pro at max_tokens=2048 in pilot 1)")
    lines.append(f"**max_tokens:** {PILOT2_MAX_TOKENS}")
    lines.append("**thinking:** enabled")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"## Pilot 2 Decision: **{outcome}**")
    lines.append("")
    lines.append(outcome_detail)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Per-Record Detail")
    lines.append("")
    lines.append("| # | Condition | finish_reason | output_tokens | content | reasoning_len (chars) | elapsed (s) |")
    lines.append("|---|---|---|---|---|---|---|")
    for i, r in enumerate(records, 1):
        if r["api_failure"]:
            lines.append(f"| {i} | {r['condition_id']} | API_FAIL ({r['api_error_code']}) | — | — | — | {r['elapsed_seconds']} |")
            continue
        c = (r["content"] or "")[:40]
        rl = len(r["reasoning_content"]) if r["reasoning_content"] else 0
        out_tok = r["usage"]["output_tokens"] if r["usage"] else "?"
        lines.append(f"| {i} | {r['condition_id']} | {r['finish_reason']} | {out_tok} | `{c}` | {rl} | {r['elapsed_seconds']} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Cost")
    lines.append("")
    lines.append(f"- Total input tokens: {total_input}")
    lines.append(f"- Total output tokens (reasoning + content): {total_output}")
    lines.append(f"- Estimated cost: ${est_cost:.4f}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Full Content")
    lines.append("")
    for i, r in enumerate(records, 1):
        if r["api_failure"]:
            continue
        lines.append(f"### Record {i} — {r['condition_id']}")
        lines.append("")
        lines.append(f"**Content** (verdict — parseable: {'YES' if r['content'] else 'NO'}):")
        lines.append("```")
        lines.append(r["content"] or "(empty)")
        lines.append("```")
        if r["reasoning_content"]:
            lines.append(f"**Reasoning ({len(r['reasoning_content'])} chars, first 600):**")
            lines.append("```")
            lines.append(r["reasoning_content"][:600] + ("..." if len(r["reasoning_content"]) > 600 else ""))
            lines.append("```")
            if len(r["reasoning_content"]) > 600:
                lines.append(f"**Reasoning (last 400 chars):**")
                lines.append("```")
                lines.append("..." + r["reasoning_content"][-400:])
                lines.append("```")
        lines.append("")

    summary_path = PILOT_DIR / "pilot2_summary.md"
    summary_path.write_text("\n".join(lines))

    print()
    print("=" * 60)
    print(f"PILOT 2 OUTCOME: {outcome}")
    print(f"  Parseable: {n_with_content}/{n_total}")
    print(f"  finish_reason=stop: {n_finish_stop}")
    print(f"  finish_reason=length: {n_finish_length}")
    print(f"  Estimated cost: ${est_cost:.4f}")
    print(f"  Raw: {out_path}")
    print(f"  Summary: {summary_path}")


if __name__ == "__main__":
    main()
