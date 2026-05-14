"""
O4 — Lever 12 function-calling schema acceptance test.

Sends a single tool-required call to DeepSeek's /beta endpoint with the
lever_12_function_schema.json schema. Confirms three things in one shot:

  1. DEEPSEEK_API_KEY has /beta strict-mode access (no 401/403).
  2. The model name "deepseek-v4-flash" routes correctly (no 404).
  3. The strict-mode schema is accepted by the server (no 400).

Pass condition: HTTP 200 + the response contains a tool_call to
analyze_battle_chain whose JSON arguments parse and contain all 8
abstraction keys plus the four top-level required fields.

Run from the Ditto-5.4-OLAT directory:
    python pre-registration/scripts/o4_schema_acceptance_test.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

try:
    from openai import OpenAI, BadRequestError, AuthenticationError, NotFoundError
except ImportError:
    print("FAIL: openai package not installed. Run: pip install openai")
    sys.exit(2)


REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = REPO_ROOT / ".env"
SCHEMA_PATH = REPO_ROOT / "pre-registration" / "artifacts" / "lever_12_function_schema.json"

# Per SPEC Section 2: target the real model alias, not deepseek-chat / deepseek-reasoner.
MODEL = "deepseek-v4-flash"
BASE_URL = "https://api.deepseek.com/beta"

# Eight abstraction keys we expect to see in the tool_call response.
EXPECTED_ABSTRACTIONS = {
    "ResourceBudget_HP",
    "ResourceBudget_PP",
    "ResourceBudget_time",
    "ResourceBudget_status",
    "ResourceBudget_boost",
    "ToolAvailability",
    "SubGoalTransition",
    "InformationState",
}

# Minimal trivial chain — content doesn't matter, we only need the model
# to invoke the tool. The schema is what's being validated server-side.
TRIVIAL_CHAIN = """# Constraint chain (perspective=p1)
Step 1 (turn=1):
  ToolAvailability: unit_A is available
Step 2 (turn=1):
  ResourceBudget: resource=hp_unit_A amount=1.0 decay=none recover_in=None
Step 3 (turn=2):
  ResourceBudget: resource=pp_action_1_own amount=0.875 decay=monotone_decrease recover_in=None
"""

USER_PROMPT = (
    "Analyze the following battle chain for constraint violations. "
    "Call the analyze_battle_chain function with your assessment.\n\n"
    f"{TRIVIAL_CHAIN}"
)


def load_env(env_path: Path) -> None:
    """Load .env (handles symlinks). Mirrors the V5.0 / V5.1 load_env logic."""
    if not env_path.exists():
        print(f"FAIL: .env not found at {env_path}")
        sys.exit(2)
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and v and not os.environ.get(k, "").strip():
            os.environ[k] = v


def sanitize_schema(parameters: dict) -> dict:
    """
    Strip server-rejected keys per SPEC Section 2:
    minLength / maxLength / minItems / maxItems / patternProperties / numerical bounds.
    Defensive — our schema doesn't currently use these, but applied per the
    validation_notes contract in lever_12_function_schema.json.
    """
    REJECTED = {
        "minLength", "maxLength", "minItems", "maxItems",
        "patternProperties", "minimum", "maximum",
        "exclusiveMinimum", "exclusiveMaximum", "multipleOf",
    }

    def strip(obj):
        if isinstance(obj, dict):
            return {k: strip(v) for k, v in obj.items() if k not in REJECTED}
        if isinstance(obj, list):
            return [strip(item) for item in obj]
        return obj

    return strip(parameters)


def load_tools(schema_path: Path) -> list[dict]:
    """Load and sanitize the tools array from the schema file."""
    if not schema_path.exists():
        print(f"FAIL: schema not found at {schema_path}")
        sys.exit(2)

    raw = json.loads(schema_path.read_text())
    tools = raw.get("tools", [])
    if not tools:
        print("FAIL: schema file has no 'tools' array")
        sys.exit(2)

    sanitized = []
    for tool in tools:
        if tool.get("type") != "function":
            continue
        fn = dict(tool["function"])
        if "parameters" in fn:
            fn["parameters"] = sanitize_schema(fn["parameters"])
        sanitized.append({"type": "function", "function": fn})
    return sanitized


def main() -> int:
    print("=" * 70)
    print("O4 — Lever 12 schema acceptance test")
    print("=" * 70)
    print(f"Model:      {MODEL}")
    print(f"Endpoint:   {BASE_URL}")
    print(f"Schema:     {SCHEMA_PATH.relative_to(REPO_ROOT)}")
    print(f".env:       {ENV_PATH} (symlink → {os.readlink(ENV_PATH) if ENV_PATH.is_symlink() else 'direct file'})")
    print("-" * 70)

    load_env(ENV_PATH)
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        print("FAIL: DEEPSEEK_API_KEY not loaded from .env")
        return 2
    print(f"Key prefix: {key[:8]}... (length={len(key)})")

    tools = load_tools(SCHEMA_PATH)
    print(f"Tools loaded: {len(tools)} ({tools[0]['function']['name']})")

    client = OpenAI(api_key=key, base_url=BASE_URL, timeout=60.0)

    print("-" * 70)
    print("Sending request...")

    try:
        # Per SPEC Lever 12 L3 thinking-mode constraint (verified 2026-05-12):
        # deepseek-v4-flash on /beta defaults to thinking-mode enabled, which
        # the server refuses to combine with tool_choice='required'. Explicit
        # extra_body disables thinking and unblocks strict tool calling.
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": USER_PROMPT}],
            tools=tools,
            tool_choice="required",
            temperature=0.0,
            max_tokens=512,
            extra_body={"thinking": {"type": "disabled"}},
        )
    except AuthenticationError as e:
        print(f"FAIL: AuthenticationError (key invalid for /beta or revoked): {e}")
        return 1
    except NotFoundError as e:
        print(f"FAIL: NotFoundError (model '{MODEL}' not routable on this account): {e}")
        return 1
    except BadRequestError as e:
        print(f"FAIL: BadRequestError (server rejected schema or request): {e}")
        return 1
    except Exception as e:
        print(f"FAIL: unexpected error: {type(e).__name__}: {e}")
        return 1

    print("HTTP 200 received.")
    print("-" * 70)

    msg = response.choices[0].message
    tool_calls = getattr(msg, "tool_calls", None) or []
    if not tool_calls:
        print("FAIL: response contained no tool_calls.")
        print(f"Raw content: {msg.content!r}")
        return 1

    print(f"tool_calls returned: {len(tool_calls)}")
    call = tool_calls[0]
    if call.function.name != "analyze_battle_chain":
        print(f"FAIL: unexpected function name {call.function.name!r}")
        return 1

    try:
        args = json.loads(call.function.arguments)
    except json.JSONDecodeError as e:
        print(f"FAIL: tool arguments are not valid JSON: {e}")
        print(f"Raw arguments: {call.function.arguments!r}")
        return 1

    # Top-level required keys (per schema "required" list)
    required_top = {"violation_detected", "abstraction_assessments",
                    "primary_violation_abstraction", "supporting_evidence"}
    missing_top = required_top - set(args.keys())
    if missing_top:
        print(f"FAIL: missing top-level required keys: {missing_top}")
        return 1

    # All 8 abstraction keys present
    assessments = args.get("abstraction_assessments", {})
    if not isinstance(assessments, dict):
        print("FAIL: abstraction_assessments is not an object")
        return 1
    missing_abs = EXPECTED_ABSTRACTIONS - set(assessments.keys())
    extra_abs = set(assessments.keys()) - EXPECTED_ABSTRACTIONS
    if missing_abs:
        print(f"FAIL: missing abstraction keys: {missing_abs}")
        return 1
    if extra_abs:
        print(f"FAIL: unexpected abstraction keys: {extra_abs}")
        return 1

    # Each abstraction has the three nested required fields
    for name, body in assessments.items():
        for field in ("violated", "turn_index", "reasoning"):
            if field not in body:
                print(f"FAIL: abstraction '{name}' missing field '{field}'")
                return 1

    print("PASS — schema accepted and tool_call returned with all 8 abstractions populated.")
    print("-" * 70)
    print("Sample of returned assessment (ResourceBudget_HP):")
    print(json.dumps(assessments["ResourceBudget_HP"], indent=2))
    print("-" * 70)
    print(f"Usage: prompt_tokens={response.usage.prompt_tokens}, "
          f"completion_tokens={response.usage.completion_tokens}")
    print()
    print("O4 RESOLVED. Pre-registration cleared for final author signoff.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
