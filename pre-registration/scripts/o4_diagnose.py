"""
O4 diagnostic — characterize DeepSeek account access.

Surfaces:
  1. Which model names are listed on the account.
  2. Whether deepseek-v4-flash actually responds (or silently routes to reasoner).
  3. Whether tool_choice='auto' (looser) works where 'required' fails.
  4. Whether a plain (no-tools) call to deepseek-v4-flash succeeds.

This is read-only diagnostic — no methodology decision is being made here.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from openai import OpenAI, BadRequestError, AuthenticationError, NotFoundError

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = REPO_ROOT / ".env"
SCHEMA_PATH = REPO_ROOT / "pre-registration" / "artifacts" / "lever_12_function_schema.json"

BASE_URL_BETA = "https://api.deepseek.com/beta"
BASE_URL_STD = "https://api.deepseek.com"


def load_env(env_path: Path) -> None:
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and v and not os.environ.get(k, "").strip():
            os.environ[k] = v


def banner(s):
    print("\n" + "=" * 70)
    print(s)
    print("=" * 70)


def try_call(label, client, **kwargs):
    print(f"\n--- {label} ---")
    try:
        r = client.chat.completions.create(**kwargs)
        msg = r.choices[0].message
        tcs = getattr(msg, "tool_calls", None) or []
        # Some DeepSeek model names appear in the response object's `model` field
        # showing what was actually used server-side.
        served_model = getattr(r, "model", "?")
        content = (msg.content or "")[:120]
        print(f"OK | served_model={served_model} | tool_calls={len(tcs)} | content_preview={content!r}")
        return True
    except (BadRequestError, NotFoundError, AuthenticationError) as e:
        print(f"FAIL | {type(e).__name__}: {e}")
    except Exception as e:
        print(f"ERR  | {type(e).__name__}: {e}")
    return False


def main():
    load_env(ENV_PATH)
    key = os.environ["DEEPSEEK_API_KEY"]

    # ------------------------------------------------------------------
    # 1. List available models on the account (uses standard endpoint)
    # ------------------------------------------------------------------
    banner("1) Models listed for this account")
    client_std = OpenAI(api_key=key, base_url=BASE_URL_STD, timeout=30.0)
    try:
        models = client_std.models.list()
        for m in models.data:
            print(f"  - {m.id}")
    except Exception as e:
        print(f"FAIL | {type(e).__name__}: {e}")

    # ------------------------------------------------------------------
    # 2. Plain call to deepseek-v4-flash on /beta — does the alias route?
    # ------------------------------------------------------------------
    banner("2) Plain text call (no tools) on /beta")
    client_beta = OpenAI(api_key=key, base_url=BASE_URL_BETA, timeout=30.0)
    for model in ("deepseek-v4-flash", "deepseek-chat", "deepseek-reasoner"):
        try_call(
            f"model={model}, no tools",
            client_beta,
            model=model,
            messages=[{"role": "user", "content": "Reply with exactly: PONG"}],
            max_tokens=10,
            temperature=0.0,
        )

    # ------------------------------------------------------------------
    # 3. Tool call with tool_choice='auto' on deepseek-v4-flash
    # ------------------------------------------------------------------
    banner("3) Strict-mode tools, tool_choice='auto'")
    schema = json.loads(SCHEMA_PATH.read_text())
    tools = []
    for t in schema.get("tools", []):
        if t.get("type") == "function":
            tools.append(t)

    minimal_chain = (
        "Step 1 (turn=1): ToolAvailability: unit_A is available\n"
        "Step 2 (turn=1): ResourceBudget: resource=hp_unit_A amount=1.0 decay=none recover_in=None"
    )

    for model in ("deepseek-v4-flash", "deepseek-chat"):
        try_call(
            f"model={model}, tool_choice=auto, strict=true in schema",
            client_beta,
            model=model,
            messages=[{
                "role": "user",
                "content": f"Analyze this chain and call the analyze_battle_chain tool.\n\n{minimal_chain}",
            }],
            tools=tools,
            tool_choice="auto",
            max_tokens=512,
            temperature=0.0,
        )

    # ------------------------------------------------------------------
    # 4. Tool call with tool_choice='required' on deepseek-chat (control)
    # ------------------------------------------------------------------
    banner("4) Strict-mode tools, tool_choice='required' on deepseek-chat (control)")
    try_call(
        "model=deepseek-chat, tool_choice=required",
        client_beta,
        model="deepseek-chat",
        messages=[{
            "role": "user",
            "content": f"Analyze this chain.\n\n{minimal_chain}",
        }],
        tools=tools,
        tool_choice="required",
        max_tokens=512,
        temperature=0.0,
    )

    print("\nDiagnostic complete.")


if __name__ == "__main__":
    main()
