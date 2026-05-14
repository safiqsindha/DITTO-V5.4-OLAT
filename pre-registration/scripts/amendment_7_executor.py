#!/usr/bin/env python3
"""
Task 2B: Amendment #7 Full L18 L4 Retest at max_tokens=4096.

Reruns all 50 flash_L18_L4 + 50 pro_L18_L4 chain variants at max_tokens=4096
with thinking enabled. Uses the same 50 chains as the original L18 L4 run.

Writes to a SEPARATE provenance file. NOT integrated into primary parser_provenance.ndjson
without both-author signoff.

Outputs:
  amendment_7/raw_responses.ndjson    -- full API responses (resume-friendly)
  amendment_7/provenance.ndjson       -- parsed records in same schema as parser_provenance.ndjson

SPEC hash: dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8
"""
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path("/Users/safiqsindha/Desktop/Project Ditto/Ditto-5.4-OLAT/pre-registration")
ENV_PATH = ROOT.parent / ".env"
VARIANTS_DIR = ROOT / "chain_variants"
OUT_DIR = ROOT / "amendment_7"
OUT_DIR.mkdir(exist_ok=True)

RAW_PATH = OUT_DIR / "raw_responses.ndjson"
PROV_PATH = OUT_DIR / "provenance.ndjson"

SPEC_HASH = "dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8"
MAX_TOKENS = 4096

# Parser cascade (copied verbatim from day1_executor.py — content field only)
_RE_STRICT = re.compile(r'(?:Therefore,\s+)?[Tt]he answer is\s+(YES|NO)\b')
_RE_PERMISSIVE = re.compile(r'(?i)(?:answer is|answer:|conclusion:)\s*(yes|no)\b')
_RE_MD_STRIP = re.compile(r'[*_`]+')
_RE_LAST_TOKEN = re.compile(r'(YES|NO)\b[\s.,!?)\]]*$', re.IGNORECASE)


def parse_content(content):
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


def load_completed():
    completed = set()
    if PROV_PATH.exists():
        with open(PROV_PATH) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rec = json.loads(line)
                        completed.add((rec['condition_id'], rec['sample_id']))
                    except Exception:
                        pass
    return completed


_RETRY_CODES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_BACKOFF = 5.0


def call_api(client, model, prompt, max_tokens):
    for attempt in range(_MAX_RETRIES + 1):
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
            is_retryable = (code in _RETRY_CODES) or (code is None)
            if is_retryable and attempt < _MAX_RETRIES:
                wait = _BACKOFF * (2 ** attempt)
                print(f"    [retry {attempt+1}/{_MAX_RETRIES}] code={code} — sleeping {wait:.0f}s")
                time.sleep(wait)
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

    # Load all L18 L4 variants
    variants = []
    for model_subdir, prefix in [("deepseek-v4-flash", "flash"),
                                  ("deepseek-v4-pro", "pro")]:
        d = VARIANTS_DIR / model_subdir / f"{prefix}_L18_L4"
        for vf in sorted(d.glob("*.json")):
            with open(vf) as f:
                variants.append(json.load(f))

    completed = load_completed()
    pending = [v for v in variants if (v['condition_id'], v['chain_id']) not in completed]

    print(f"Total variants: {len(variants)} (flash: {sum(1 for v in variants if 'flash' in v['condition_id'])}, "
          f"pro: {sum(1 for v in variants if 'pro' in v['condition_id'])})")
    print(f"Already completed: {len(completed)}")
    print(f"Pending: {len(pending)}")
    print(f"max_tokens: {MAX_TOKENS}")
    print(f"thinking: enabled")
    print()

    if not pending:
        print("All complete. Exiting.")
        return

    raw_f = open(RAW_PATH, "a")
    prov_f = open(PROV_PATH, "a")

    t_start = time.time()
    for i, v in enumerate(pending, 1):
        cond_id = v['condition_id']
        chain_id = v['chain_id']
        print(f"[{i}/{len(pending)}] {cond_id} {chain_id[:35]}", end=" ", flush=True)

        t0 = time.time()
        resp, err = call_api(client, v["api_params"]["model"], v["prompt_user"], MAX_TOKENS)
        elapsed = time.time() - t0

        if err:
            print(f"FAIL ({err}, {elapsed:.1f}s)")
            raw_rec = {
                "condition_id": cond_id, "sample_id": chain_id, "model": v["model"],
                "max_tokens_used": MAX_TOKENS, "amendment_7": True,
                "api_failure": True, "api_error_code": err,
                "content": None, "reasoning_content": None,
                "finish_reason": None, "usage": None,
                "elapsed_seconds": round(elapsed, 2), "spec_hash": SPEC_HASH,
            }
            prov_rec = {
                "condition_id": cond_id, "sample_id": chain_id, "model": v["model"],
                "lever_varied": v.get("lever_varied"), "level_varied": v.get("level_varied"),
                "ground_truth": v.get("ground_truth"), "violation_type": v.get("violation_type"),
                "spec_hash": SPEC_HASH,
                "parse_stage_reached": "api_failure", "parse_success": False,
                "fallback_used": False, "parsed_label": None,
                "raw_output": None, "reasoning_content": None,
                "finish_reason": None, "usage": None,
                "api_failure": True, "api_error_code": err,
                "amendment_7": True, "max_tokens_used": MAX_TOKENS,
            }
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
            parsed_label, stage = parse_content(content)

            print(f"finish={finish} out_tok={usage['output_tokens'] if usage else '?'} "
                  f"verdict={parsed_label or 'unparseable'} ({elapsed:.1f}s)")

            raw_rec = {
                "condition_id": cond_id, "sample_id": chain_id, "model": v["model"],
                "max_tokens_used": MAX_TOKENS, "amendment_7": True,
                "api_failure": False, "api_error_code": None,
                "content": content, "reasoning_content": reasoning,
                "finish_reason": finish, "usage": usage,
                "elapsed_seconds": round(elapsed, 2), "spec_hash": SPEC_HASH,
            }
            prov_rec = {
                "condition_id": cond_id, "sample_id": chain_id, "model": v["model"],
                "lever_varied": v.get("lever_varied"), "level_varied": v.get("level_varied"),
                "ground_truth": v.get("ground_truth"), "violation_type": v.get("violation_type"),
                "spec_hash": SPEC_HASH,
                "parse_stage_reached": stage,
                "parse_success": parsed_label is not None,
                "fallback_used": stage in ("permissive", "md_strip", "last_token"),
                "parsed_label": parsed_label,
                "raw_output": content,
                "reasoning_content": reasoning,
                "finish_reason": finish,
                "usage": usage,
                "api_failure": False,
                "api_error_code": None,
                "amendment_7": True,
                "max_tokens_used": MAX_TOKENS,
            }

        raw_f.write(json.dumps(raw_rec) + "\n")
        raw_f.flush()
        prov_f.write(json.dumps(prov_rec) + "\n")
        prov_f.flush()

    raw_f.close()
    prov_f.close()

    total_elapsed = time.time() - t_start
    print()
    print(f"Done. Wrote {len(pending)} new records in {total_elapsed/60:.1f} min.")
    print(f"  Raw: {RAW_PATH}")
    print(f"  Provenance: {PROV_PATH}")


if __name__ == "__main__":
    main()
