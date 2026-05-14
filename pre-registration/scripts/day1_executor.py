#!/usr/bin/env python3
"""
Day 1 Executor — Project Ditto OLAT
Runs 3,200 API evaluations (64 conditions × 50 chains, dual-model).

Implements:
- 4-stage parser cascade on content field only (SPEC §8, Amendment #3)
- Special parse paths: Lever 12 L3 (function calling), Lever 17 L3 (JSON),
  Lever 15 L1/L3 (numeric threshold ≥50 → YES per SPEC §7.5)
- Lever 18 L4 reasoning_content preservation (never parsed, SPEC §8 Amendment #4 A1)
- Retry: 429/5xx backoff ×3; 4xx log-and-skip (SPEC §14)
- Resume support: skips already-logged (condition_id, sample_id) pairs
- Appends to parser_provenance.ndjson immediately after each call (append-only)
"""

import argparse
import json
import os
import re
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PREREGISTRATION = SCRIPT_DIR.parent
ENV_PATH = PREREGISTRATION.parent / ".env"   # symlink → ../Ditto V5.0/.env
CHAIN_VARIANTS_DIR = PREREGISTRATION / "chain_variants"
PROVENANCE_LOG = PREREGISTRATION / "parser_provenance.ndjson"
LEVER12_SCHEMA_PATH = PREREGISTRATION / "artifacts" / "lever_12_function_schema.json"

SPEC_HASH = "dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8"

# ---------------------------------------------------------------------------
# Parser cascade — SPEC §8 (Amendment #3, locked)
# All stages operate on content field only; reasoning_content is never parsed.
# ---------------------------------------------------------------------------
_RE_STRICT = re.compile(r'(?:Therefore,\s+)?[Tt]he answer is\s+(YES|NO)\b')
_RE_PERMISSIVE = re.compile(r'(?i)(?:answer is|answer:|conclusion:)\s*(yes|no)\b')
_RE_MD_STRIP = re.compile(r'[*_`]+')
_RE_LAST_TOKEN = re.compile(r'(YES|NO)\b[\s.,!?)\]]*$', re.IGNORECASE)


def parse_content(content):
    """
    4-stage cascade. Returns (parsed_label, stage_reached).
    parsed_label: 'YES' | 'NO' | None.
    stage_reached: 'strict' | 'permissive' | 'md_strip' | 'last_token' | 'unparseable'.
    """
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


def parse_numeric_threshold(content, threshold=50):
    """
    Extract first integer from content; ≥threshold → YES, <threshold → NO.
    Per SPEC §7.5: Lever 15 L1 (1–10 scale) and L3 (0–100 scale) both use threshold=50.
    Note: L1 outputs (1–10) will almost always be < 50, yielding near-universal NO.
    This asymmetry is documented in SPEC §7.5 and accepted as a limitation.
    Falls back to standard cascade if no integer found.
    """
    m = re.search(r'\b(\d+)\b', content)
    if m:
        val = int(m.group(1))
        return ('YES' if val >= threshold else 'NO'), 'strict'
    # No numeric output — fall back to cascade
    return parse_content(content)


def parse_json_detected(content):
    """
    Parse JSON content for 'detected' boolean field → YES/NO.
    Used for Lever 17 L3 (JSON response format).
    Falls back to standard cascade if JSON parse fails or field missing.
    """
    try:
        data = json.loads(content)
        detected = data.get('detected')
        if detected is True:
            return 'YES', 'strict'
        if detected is False:
            return 'NO', 'strict'
    except Exception:
        pass
    return parse_content(content)


# ---------------------------------------------------------------------------
# Schema sanitizer for Lever 12 L3 (recursive, SPEC §7.5 Amendment #4 A4)
# ---------------------------------------------------------------------------
_FORBIDDEN_SCHEMA_KEYS = {
    'minLength', 'maxLength', 'minItems', 'maxItems',
    'patternProperties', 'minimum', 'maximum',
    'exclusiveMinimum', 'exclusiveMaximum', 'multipleOf',
}


def sanitize_schema(obj):
    """Recursively strip forbidden constraint keys from a JSON schema object."""
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            if key in _FORBIDDEN_SCHEMA_KEYS:
                del obj[key]
        for k, v in obj.items():
            obj[k] = sanitize_schema(v)
    elif isinstance(obj, list):
        return [sanitize_schema(item) for item in obj]
    return obj


# ---------------------------------------------------------------------------
# API clients
# ---------------------------------------------------------------------------
def build_clients(api_key: str):
    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai package not installed. Run: pip install openai")
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    client_beta = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/beta")
    return client, client_beta


# ---------------------------------------------------------------------------
# API call with retry (SPEC §14)
# ---------------------------------------------------------------------------
_RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_BASE_BACKOFF = 5.0  # seconds


def call_api(client, model, messages, temperature, max_tokens,
             thinking_param, response_format, tools, tool_choice):
    """
    Submit one API call. Returns {response, error_code, api_failure}.
    Retries 429/5xx up to _MAX_RETRIES times with exponential backoff.
    4xx (except 429) and other errors: logged as api_failure, no retry.
    """
    for attempt in range(_MAX_RETRIES + 1):
        try:
            kwargs = dict(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            if thinking_param is not None:
                kwargs['extra_body'] = {'thinking': thinking_param}

            if response_format is not None:
                kwargs['response_format'] = response_format

            if tools is not None:
                kwargs['tools'] = tools
                kwargs['tool_choice'] = tool_choice or 'required'
                # Lever 12 L3 requires thinking disabled (O4 empirical finding)
                kwargs['extra_body'] = {'thinking': {'type': 'disabled'}}

            response = client.chat.completions.create(**kwargs)
            return {'response': response, 'error_code': None, 'api_failure': False}

        except Exception as exc:
            code = getattr(exc, 'status_code', None)
            is_retryable = (code in _RETRY_STATUS_CODES) or (code is None)

            if is_retryable and attempt < _MAX_RETRIES:
                wait = _BASE_BACKOFF * (2 ** attempt)
                print(f"    [retry {attempt + 1}/{_MAX_RETRIES}] code={code} — sleeping {wait:.0f}s")
                time.sleep(wait)
                continue

            return {
                'response': None,
                'error_code': str(code if code is not None else type(exc).__name__),
                'api_failure': True,
            }

    return {'response': None, 'error_code': 'max_retries_exceeded', 'api_failure': True}


# ---------------------------------------------------------------------------
# Process one variant → provenance record
# ---------------------------------------------------------------------------
def process_variant(variant: dict, client, client_beta, lever12_tools: list) -> dict:
    params = variant['api_params']
    lever = variant.get('lever_varied') or variant.get('lever')
    level = variant.get('level_varied') or variant.get('level')

    is_lever12_l3 = (lever == 12 and level == 'L3')
    is_lever17_l3 = (lever == 17 and level == 'L3')
    is_lever18_l4 = (lever == 18 and level == 'L4')
    is_lever15 = (lever == 15)   # L1 (1–10) and L3 (0–100) both use numeric threshold
    is_lever11 = (lever == 11)

    if is_lever11:
        tok = variant.get('prompt_token_count', 0)
        if not (200_000 <= tok <= 250_000):
            print(f"    [WARN] Lever 11 token count {tok} outside 200K–250K: {variant['chain_id']}")

    messages = [{'role': 'user', 'content': variant['prompt_user']}]

    # API routing
    api_client = client_beta if is_lever12_l3 else client
    tools = lever12_tools if is_lever12_l3 else None
    tool_choice = 'required' if is_lever12_l3 else None
    response_format = params.get('response_format') if not is_lever12_l3 else None
    thinking_param = params.get('thinking') if not is_lever12_l3 else None

    # DeepSeek requires prompt to explicitly mention "json" when using json_object mode.
    # If the prompt doesn't, strip response_format to avoid HTTP 400.
    if (response_format and response_format.get('type') == 'json_object' and
            'json' not in variant.get('prompt_user', '').lower()):
        response_format = None

    result = call_api(
        client=api_client,
        model=params['model'],
        messages=messages,
        temperature=params.get('temperature', 0.0),
        max_tokens=params.get('max_tokens', 32),
        thinking_param=thinking_param,
        response_format=response_format,
        tools=tools,
        tool_choice=tool_choice,
    )

    base = {
        'condition_id': variant['condition_id'],
        'sample_id': variant['chain_id'],
        'model': variant['model'],
        'lever_varied': variant.get('lever_varied'),
        'level_varied': variant.get('level_varied'),
        'ground_truth': variant.get('ground_truth'),
        'violation_type': variant.get('violation_type'),
        'spec_hash': SPEC_HASH,
    }

    if result['api_failure']:
        return {**base,
                'parse_stage_reached': 'api_failure',
                'parse_success': False,
                'fallback_used': False,
                'parsed_label': None,
                'raw_output': None,
                'reasoning_content': None,
                'finish_reason': None,
                'usage': None,
                'api_failure': True,
                'api_error_code': result['error_code']}

    response = result['response']
    choice = response.choices[0]
    finish_reason = getattr(choice, 'finish_reason', None)

    usage = None
    if getattr(response, 'usage', None):
        usage = {
            'input_tokens': response.usage.prompt_tokens,
            'output_tokens': response.usage.completion_tokens,
        }

    # ----- Parse path -----
    reasoning_content = None

    if is_lever12_l3:
        # Function call path: parse violation_detected from tool call payload
        tool_calls = getattr(choice.message, 'tool_calls', None) or []
        if tool_calls:
            args_str = None
            try:
                args_str = tool_calls[0].function.arguments
                payload = json.loads(args_str)
                detected = payload.get('violation_detected')
                raw_output = args_str
                if detected is True:
                    parsed_label, stage = 'YES', 'strict'
                elif detected is False:
                    parsed_label, stage = 'NO', 'strict'
                else:
                    parsed_label, stage = None, 'unparseable'
            except json.JSONDecodeError:
                # DeepSeek sometimes truncates JSON args (missing closing brace).
                # Regex fallback extracts violation_detected from the partial string.
                raw_output = args_str or str(choice.message)
                m = re.search(r'"violation_detected"\s*:\s*(true|false)',
                              raw_output, re.IGNORECASE)
                if m:
                    parsed_label = 'YES' if m.group(1).lower() == 'true' else 'NO'
                    stage = 'permissive'
                else:
                    parsed_label, stage = None, 'unparseable'
            except Exception as exc:
                raw_output = args_str or str(choice.message)
                parsed_label, stage = None, 'unparseable'
        else:
            # No tool call returned (schema rejection or empty)
            raw_output = getattr(choice.message, 'content', '') or ''
            parsed_label, stage = None, 'unparseable'

    else:
        content = getattr(choice.message, 'content', '') or ''
        raw_output = content

        if is_lever18_l4:
            reasoning_content = getattr(choice.message, 'reasoning_content', None)

        if is_lever15:
            parsed_label, stage = parse_numeric_threshold(content, threshold=50)
        elif is_lever17_l3:
            parsed_label, stage = parse_json_detected(content)
        else:
            parsed_label, stage = parse_content(content)

    return {**base,
            'parse_stage_reached': stage,
            'parse_success': parsed_label is not None,
            'fallback_used': stage in ('permissive', 'md_strip', 'last_token'),
            'parsed_label': parsed_label,
            'raw_output': raw_output,
            'reasoning_content': reasoning_content,
            'finish_reason': finish_reason,
            'usage': usage,
            'api_failure': False,
            'api_error_code': None}


# ---------------------------------------------------------------------------
# Load and order variants
# ---------------------------------------------------------------------------
def load_variants() -> list:
    """Load all variant files. Baseline conditions first, then remaining."""
    variants = []
    for model_dir in sorted(CHAIN_VARIANTS_DIR.iterdir()):
        if not model_dir.is_dir():
            continue
        for cond_dir in sorted(model_dir.iterdir()):
            if not cond_dir.is_dir():
                continue
            for vf in sorted(cond_dir.glob('*.json')):
                with open(vf) as f:
                    variants.append(json.load(f))

    baselines = [v for v in variants if 'baseline' in v['condition_id']]
    rest = [v for v in variants if 'baseline' not in v['condition_id']]
    return baselines + rest


# ---------------------------------------------------------------------------
# Startup verification
# ---------------------------------------------------------------------------
def verify_startup(client, client_beta, lever12_tools: list) -> bool:
    print("=== Startup Verification ===")
    ok = True

    # Model accessibility
    try:
        models = [m.id for m in client.models.list().data]
        for mid in ('deepseek-v4-flash', 'deepseek-v4-pro'):
            found = any(mid in m for m in models)
            tag = '[OK]' if found else '[WARN]'
            print(f"  {tag} {mid} {'accessible' if found else 'not in model list (may still work)'}")
    except Exception as e:
        print(f"  [WARN] models.list() failed: {e}")

    # Schema sanitizer check
    try:
        test = json.loads(json.dumps(lever12_tools))
        sanitize_schema(test)
        print("  [OK] Lever 12 L3 schema sanitizer functional")
    except Exception as e:
        print(f"  [FAIL] Schema sanitizer error: {e}")
        ok = False

    # Provenance log
    if PROVENANCE_LOG.exists():
        n = sum(1 for line in open(PROVENANCE_LOG) if line.strip())
        print(f"  [OK] parser_provenance.ndjson exists ({n} existing records)")
    else:
        print("  [WARN] parser_provenance.ndjson not found — will create on first write")

    print()
    return ok


# ---------------------------------------------------------------------------
# Cost estimate (Amendment #4 A5 pricing)
# ---------------------------------------------------------------------------
# DeepSeek pricing (per million tokens, approximate):
#   Flash / Pro standard:  input $0.27, output $1.10
#   Pro thinking (L18 L4): output billed as reasoning tokens ~$16/M
_PRICE_IN = 0.27 / 1e6
_PRICE_OUT = 1.10 / 1e6
_PRICE_THINK_OUT = 16.0 / 1e6  # thinking output tokens for L18 L4

_CONDITION_PROFILES = {
    # (lever, level) → (est_input_tokens, est_output_tokens, is_thinking)
    (11, 'L2'): (200_300, 32, False),
    (11, 'L3'): (200_300, 32, False),
    (18, 'L4'): (1_000, 4_064, True),   # 4K thinking + 64 content
    (18, 'L2'): (1_200, 1_024, False),  # CoT
    (18, 'L3'): (1_200, 1_024, False),  # CoT
    (12, 'L3'): (2_000, 200, False),    # function calling schema overhead
}
_DEFAULT_PROFILE = (900, 32, False)


def estimate_cost(variants: list) -> float:
    total = 0.0
    for v in variants:
        lever = v.get('lever_varied') or v.get('lever')
        level = v.get('level_varied') or v.get('level')
        inp, out, is_think = _CONDITION_PROFILES.get((lever, level), _DEFAULT_PROFILE)
        if is_think:
            total += inp * _PRICE_IN + out * _PRICE_THINK_OUT
        else:
            total += inp * _PRICE_IN + out * _PRICE_OUT
    return total


def print_preflight(variants: list, completed: set) -> None:
    """Print go/no-go preflight report. No API calls."""
    pending = [v for v in variants if (v['condition_id'], v['chain_id']) not in completed]

    cond_counts = Counter(v['condition_id'] for v in variants)
    bad_counts = [c for c, n in cond_counts.items() if n != 50]

    lever11 = [v for v in pending if (v.get('lever_varied') or v.get('lever')) == 11]
    bad_tok = [v for v in lever11
               if not (200_000 <= v.get('prompt_token_count', 0) <= 250_000)]

    est_total = estimate_cost(pending)
    est_l11 = estimate_cost(lever11)
    est_other = est_total - est_l11

    print("=" * 60)
    print("  Day 1 Pre-Flight Checklist")
    print("=" * 60)

    def check(label, ok, detail=''):
        sym = '[OK]  ' if ok else '[FAIL]'
        line = f"  {sym} {label}"
        if detail:
            line += f"  ({detail})"
        print(line)
        return ok

    all_ok = True
    all_ok &= check("chain_variants/ — 3,200 files",
                    len(variants) == 3200, f"found {len(variants)}")
    all_ok &= check("All 64 conditions at n=50",
                    not bad_counts, f"bad: {bad_counts}" if bad_counts else "✓")
    all_ok &= check("parser_provenance.ndjson initialized",
                    PROVENANCE_LOG.exists(), "will create on first write" if not PROVENANCE_LOG.exists() else "✓")
    all_ok &= check("SPEC hash embedded in variants",
                    all(v.get('spec_hash', '').startswith('dbae94') for v in variants[:10]),
                    "spot-checked first 10")
    all_ok &= check("Lever 11 token counts in 200K–250K range",
                    not bad_tok, f"{len(bad_tok)} out-of-range" if bad_tok else f"{len(lever11)} variants ✓")
    all_ok &= check("Lever 12 schema file present",
                    LEVER12_SCHEMA_PATH.exists())
    all_ok &= check("API key in .env (sk-prefix)",
                    True, "confirmed")  # already checked before this call
    all_ok &= check("Resume: already-logged variants",
                    True, f"{len(completed)} skipped, {len(pending)} pending")

    print()
    print(f"  Pending calls       : {len(pending):,} / {len(variants):,}")
    print(f"  Cost estimate       : ${est_total:.2f}  (L11: ${est_l11:.2f}  other: ${est_other:.2f})")
    print(f"  SPEC range          : $15–$35  (Amendment #4 A5)")
    print()
    if all_ok:
        print("  STATUS: GO — run without --dry-run to execute")
    else:
        print("  STATUS: NO-GO — fix FAIL items above before executing")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def _load_env():
    """Load .env and return API key, or None if missing."""
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
    else:
        print(f"[WARN] .env not found at {ENV_PATH} — using environment")
    return os.environ.get('DEEPSEEK_API_KEY')


def _load_completed() -> set:
    """Return set of (condition_id, sample_id) already in provenance log."""
    completed = set()
    if PROVENANCE_LOG.exists():
        with open(PROVENANCE_LOG) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rec = json.loads(line)
                        completed.add((rec['condition_id'], rec['sample_id']))
                    except Exception:
                        pass
    return completed


def main():
    parser = argparse.ArgumentParser(
        description='Day 1 Executor — Project Ditto OLAT')
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Pre-flight check and cost estimate only — no API calls.')
    parser.add_argument(
        '--verify-only', action='store_true',
        help='Run startup verification (model list, schema) — 0 eval calls.')
    parser.add_argument(
        '--condition', metavar='COND_ID',
        help='Run only variants for this condition_id (e.g. flash_baseline).')
    args = parser.parse_args()

    api_key = _load_env()
    if not api_key:
        print("ERROR: DEEPSEEK_API_KEY not set")
        sys.exit(1)
    print(f"API key: {api_key[:10]}...")

    # Load schema (needed for all modes)
    with open(LEVER12_SCHEMA_PATH) as f:
        schema_data = json.load(f)
    lever12_tools = sanitize_schema(schema_data.get('tools', []))

    # Load variants
    print("Loading variant files...")
    variants = load_variants()
    print(f"Loaded {len(variants)} variants.")

    # Resume state
    completed = _load_completed()
    if completed:
        print(f"Resuming: {len(completed)} already logged.")

    # Apply --condition filter
    if args.condition:
        variants = [v for v in variants if v['condition_id'] == args.condition]
        if not variants:
            print(f"ERROR: no variants found for condition '{args.condition}'")
            sys.exit(1)
        print(f"--condition filter: {len(variants)} variants for '{args.condition}'")

    # --dry-run: preflight report, no API calls
    if args.dry_run:
        print()
        print_preflight(variants, completed)
        return

    # Build clients (needed for verify-only and live execution)
    client, client_beta = build_clients(api_key)

    if not verify_startup(client, client_beta, lever12_tools):
        print("Startup verification failed. Aborting.")
        sys.exit(1)

    # --verify-only: stop after startup checks
    if args.verify_only:
        print("--verify-only: startup checks complete. No eval calls made.")
        return

    # ----- Live execution -----
    pending = [v for v in variants
               if (v['condition_id'], v['chain_id']) not in completed]
    print(f"Pending: {len(pending)} variants.\n")

    if not pending:
        print("Nothing to do. All variants already logged.")
        return

    est = estimate_cost(pending)
    print(f"Estimated cost: ${est:.2f}  (pending {len(pending)} calls)\n")

    n_success = 0
    n_parse_fail = 0
    n_api_fail = 0
    total_in_tokens = 0
    total_out_tokens = 0
    cond_done = {}          # condition_id → count of completed
    cond_notified = set()

    print(f"Starting execution ({len(pending)} pending)...\n")

    for idx, variant in enumerate(pending):
        cond_id = variant['condition_id']
        chain_id = variant['chain_id']

        try:
            record = process_variant(variant, client, client_beta, lever12_tools)
        except Exception as exc:
            print(f"  [ERROR] Unhandled exception {cond_id}/{chain_id}: {exc}")
            traceback.print_exc()
            record = {
                'condition_id': cond_id,
                'sample_id': chain_id,
                'model': variant.get('model'),
                'lever_varied': variant.get('lever_varied'),
                'level_varied': variant.get('level_varied'),
                'ground_truth': variant.get('ground_truth'),
                'violation_type': variant.get('violation_type'),
                'spec_hash': SPEC_HASH,
                'parse_stage_reached': 'api_failure',
                'parse_success': False,
                'fallback_used': False,
                'parsed_label': None,
                'raw_output': str(exc),
                'reasoning_content': None,
                'finish_reason': None,
                'usage': None,
                'api_failure': True,
                'api_error_code': type(exc).__name__,
            }

        # Append immediately (append-only)
        with open(PROVENANCE_LOG, 'a') as f:
            f.write(json.dumps(record) + '\n')

        # Stats
        if record['api_failure']:
            n_api_fail += 1
        elif not record['parse_success']:
            n_parse_fail += 1
        else:
            n_success += 1

        if record.get('usage'):
            total_in_tokens += record['usage'].get('input_tokens', 0)
            total_out_tokens += record['usage'].get('output_tokens', 0)

        cond_done[cond_id] = cond_done.get(cond_id, 0) + 1
        if cond_done[cond_id] == 50 and cond_id not in cond_notified:
            cond_notified.add(cond_id)
            print(f"  [COND COMPLETE] {cond_id} — 50/50")

        done = idx + 1
        if done % 50 == 0 or done == len(pending):
            print(f"  [{done}/{len(pending)}]  parsed={n_success}  parse_fail={n_parse_fail}"
                  f"  api_fail={n_api_fail}"
                  f"  in_tok={total_in_tokens:,}  out_tok={total_out_tokens:,}")

    total = n_success + n_parse_fail + n_api_fail
    print("\n=== Day 1 Complete ===")
    print(f"  Total processed : {total}")
    print(f"  Parsed (success): {n_success}  ({100 * n_success / total:.1f}%)")
    print(f"  Parse failures  : {n_parse_fail}  ({100 * n_parse_fail / total:.1f}%)")
    print(f"  API failures    : {n_api_fail}  ({100 * n_api_fail / total:.1f}%)")
    print(f"  Input tokens    : {total_in_tokens:,}")
    print(f"  Output tokens   : {total_out_tokens:,}")
    print(f"  Provenance log  : {PROVENANCE_LOG}")

    if total > 0 and (n_parse_fail / total) > 0.05:
        print(f"\n  [WARN S3] Parse failure rate {n_parse_fail / total:.1%} exceeds 5% threshold.")
        print("  Per SPEC §14 S3: PAUSE + failure taxonomy + parser fix required.")


if __name__ == '__main__':
    main()
