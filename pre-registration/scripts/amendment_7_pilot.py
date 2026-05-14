#!/usr/bin/env python3
"""
Task 2A: Amendment #7 Pilot — L18 L4 with max_tokens=2048.

Loads the first 5 flash_L18_L4 + first 5 pro_L18_L4 chain variants,
overrides max_tokens to 2048 (keeping thinking enabled), calls DeepSeek,
and classifies the pilot outcome:

  PASS                  : >=90% content populated AND mean content >=50 tokens
  RAISE_BUDGET          : 50-89% content populated OR mean content 20-50
  FUNDAMENTAL_FAILURE   : <50% content populated OR mean content <20

Outputs:
  amendment_7_pilot/raw_responses.ndjson
  amendment_7_pilot/pilot_summary.md

SPEC hash: dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8
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
PILOT_DIR.mkdir(exist_ok=True)

SPEC_HASH = "dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8"
PILOT_MAX_TOKENS = 2048


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
    """One API call with retry on 429/5xx."""
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

    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai package not installed")
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    # Load first 5 of each
    pilot_variants = []
    for model_subdir, prefix in [("deepseek-v4-flash", "flash"),
                                  ("deepseek-v4-pro", "pro")]:
        d = VARIANTS_DIR / model_subdir / f"{prefix}_L18_L4"
        files = sorted(d.glob("*.json"))[:5]
        for vf in files:
            with open(vf) as f:
                v = json.load(f)
            pilot_variants.append(v)

    print(f"Loaded {len(pilot_variants)} pilot variants "
          f"({sum(1 for v in pilot_variants if 'flash' in v['model'])} flash, "
          f"{sum(1 for v in pilot_variants if 'pro' in v['model'])} pro)")
    print(f"max_tokens override: {PILOT_MAX_TOKENS}")
    print()

    out_path = PILOT_DIR / "raw_responses.ndjson"
    records = []
    with open(out_path, "w") as fout:
        for i, v in enumerate(pilot_variants, 1):
            print(f"[{i}/{len(pilot_variants)}] {v['condition_id']} chain={v['chain_id'][:40]}")
            t0 = time.time()
            resp, err = call_api(client, v["api_params"]["model"],
                                 v["prompt_user"], PILOT_MAX_TOKENS)
            elapsed = time.time() - t0

            if err:
                rec = {
                    "condition_id": v["condition_id"],
                    "sample_id": v["chain_id"],
                    "model": v["model"],
                    "max_tokens_used": PILOT_MAX_TOKENS,
                    "amendment_7_pilot": True,
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
                    "max_tokens_used": PILOT_MAX_TOKENS,
                    "amendment_7_pilot": True,
                    "api_failure": False,
                    "api_error_code": None,
                    "content": content,
                    "reasoning_content": reasoning,
                    "finish_reason": finish,
                    "usage": usage,
                    "elapsed_seconds": round(elapsed, 2),
                    "spec_hash": SPEC_HASH,
                }
                content_tokens_est = len(content.split()) if content else 0
                print(f"  OK: finish={finish}, content_len={len(content)} chars, "
                      f"~{content_tokens_est} words, output_tokens={usage['output_tokens'] if usage else '?'} ({elapsed:.1f}s)")

            fout.write(json.dumps(rec) + "\n")
            fout.flush()
            records.append(rec)

    # Classify outcome
    n_total = len(records)
    n_api_failure = sum(1 for r in records if r["api_failure"])
    n_with_content = sum(1 for r in records
                         if not r["api_failure"] and r["content"] and len(r["content"]) > 0)
    pct_with_content = (n_with_content / n_total) * 100 if n_total else 0.0

    # Estimate content tokens for records with content
    # Content tokens ≈ usage.output_tokens minus reasoning_tokens, but DeepSeek doesn't split.
    # Use a word-based approximation: 1 token ≈ 0.75 words (English).
    content_tokens_list = []
    for r in records:
        if not r["api_failure"] and r["content"]:
            words = len(r["content"].split())
            est_tokens = round(words / 0.75)
            content_tokens_list.append(est_tokens)
    mean_content_tokens = (sum(content_tokens_list) / len(content_tokens_list)) if content_tokens_list else 0.0

    # Classification
    if pct_with_content >= 90 and mean_content_tokens >= 50:
        outcome = "PASS"
        outcome_detail = (
            "≥90% content populated and mean content ≥50 tokens. "
            "Proceed to Task 2B (full retest at max_tokens=2048)."
        )
    elif pct_with_content >= 50 or mean_content_tokens >= 20:
        outcome = "RAISE_BUDGET"
        outcome_detail = (
            f"{pct_with_content:.0f}% content populated, mean content {mean_content_tokens:.0f} tokens. "
            "Surface to user: consider raising max_tokens to 4096 before full retest."
        )
    else:
        outcome = "FUNDAMENTAL_FAILURE"
        outcome_detail = (
            f"{pct_with_content:.0f}% content populated, mean content {mean_content_tokens:.0f} tokens. "
            "STOP: L18 L4 may be fundamentally untestable; surface to user."
        )

    # Write pilot_summary.md
    lines = []
    lines.append("# Amendment #7 Pilot — L18 L4 Retest at max_tokens=2048")
    lines.append("")
    lines.append(f"**SPEC hash:** `{SPEC_HASH}`  ")
    lines.append("**Generated:** 2026-05-13  ")
    lines.append(f"**Pilot N:** {n_total} (5 flash + 5 pro, first 5 chain variants each)  ")
    lines.append(f"**max_tokens:** {PILOT_MAX_TOKENS}  ")
    lines.append("**thinking:** enabled  ")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Pilot Decision: " + f"**{outcome}**")
    lines.append("")
    lines.append(outcome_detail)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Aggregate Metrics")
    lines.append("")
    lines.append(f"- Total pilot calls: {n_total}")
    lines.append(f"- API failures: {n_api_failure}")
    lines.append(f"- Records with content populated: {n_with_content} ({pct_with_content:.0f}%)")
    lines.append(f"- Mean content tokens (word-based estimate): {mean_content_tokens:.0f}")
    if content_tokens_list:
        lines.append(f"- Content token range: {min(content_tokens_list)}–{max(content_tokens_list)}")
    n_finish_stop = sum(1 for r in records if not r["api_failure"] and r["finish_reason"] == "stop")
    n_finish_length = sum(1 for r in records if not r["api_failure"] and r["finish_reason"] == "length")
    lines.append(f"- finish_reason=stop: {n_finish_stop}")
    lines.append(f"- finish_reason=length: {n_finish_length}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Per-Record Detail")
    lines.append("")
    lines.append("| # | Condition | Chain | finish_reason | output_tokens | content_len (chars) | content tokens (est) | YES/NO/—? |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(records, 1):
        if r["api_failure"]:
            lines.append(f"| {i} | {r['condition_id']} | {r['sample_id'][:30]} | API_FAIL ({r['api_error_code']}) | — | — | — | — |")
            continue
        c = r["content"] or ""
        words = len(c.split())
        est = round(words / 0.75) if words else 0
        # Quick YES/NO detection
        c_upper = c.strip().upper()
        if c_upper.startswith("YES") or " YES" in c_upper[-20:]:
            verdict = "YES"
        elif c_upper.startswith("NO") or " NO" in c_upper[-20:]:
            verdict = "NO"
        elif c_upper:
            verdict = "(text, no clear verdict)"
        else:
            verdict = "(empty)"
        out_tok = r["usage"]["output_tokens"] if r["usage"] else "?"
        lines.append(f"| {i} | {r['condition_id']} | {r['sample_id'][:30]} | {r['finish_reason']} | {out_tok} | {len(c)} | {est} | {verdict} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Cost (Pilot)")
    lines.append("")
    total_input = sum(r["usage"]["input_tokens"] for r in records
                      if r["usage"])
    total_output = sum(r["usage"]["output_tokens"] for r in records
                       if r["usage"])
    # DeepSeek thinking-mode pricing: $16/M for thinking output, ~$0.27/M for input
    est_cost = (total_input * 0.27 / 1e6) + (total_output * 16.0 / 1e6)
    lines.append(f"- Total input tokens: {total_input}")
    lines.append(f"- Total output tokens (reasoning + content combined): {total_output}")
    lines.append(f"- Estimated cost: ${est_cost:.4f}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Sample Content (first 500 chars per record)")
    lines.append("")
    for i, r in enumerate(records, 1):
        if r["api_failure"]:
            continue
        lines.append(f"### Record {i} — {r['condition_id']} — {r['sample_id'][:40]}")
        lines.append("")
        lines.append("**Content:**")
        lines.append("```")
        c = r["content"] or "(empty)"
        lines.append(c[:500] + ("..." if len(c) > 500 else ""))
        lines.append("```")
        if r["reasoning_content"]:
            lines.append("**Reasoning (first 200 chars):**")
            lines.append("```")
            rc = r["reasoning_content"]
            lines.append(rc[:200] + ("..." if len(rc) > 200 else ""))
            lines.append("```")
        lines.append("")

    summary_path = PILOT_DIR / "pilot_summary.md"
    summary_path.write_text("\n".join(lines))

    print()
    print("=" * 60)
    print(f"PILOT OUTCOME: {outcome}")
    print(f"  Content populated: {n_with_content}/{n_total} ({pct_with_content:.0f}%)")
    print(f"  Mean content tokens: {mean_content_tokens:.0f}")
    print(f"  Estimated cost: ${est_cost:.4f}")
    print(f"  Raw responses: {out_path}")
    print(f"  Summary: {summary_path}")


if __name__ == "__main__":
    main()
