#!/usr/bin/env python3
"""
Priority B2 — PUBG Anti-Detection Reproduction Test

Tests whether the `eliminated_player` marker in PUBG chains causes the
anti-detection pattern identified in P3 (FPR > true detection rate).

Phase 1: Reproduce anti-detection on 20 original PUBG chain pairs (V4-Pro, V1-minimal)
Phase 2: Test 3 modifications:
  Mod 1 — Strip marker from clean chains (removes NOTE=Player_X_already_eliminated)
  Mod 2 — Move marker to different position in violated chains
  Mod 3 — Rename marker to neutral field name (STATUS=acting instead of NOTE=eliminated)

Output: pre-registration/pubg_artifact_investigation/
"""

import copy
import json
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
PREREGISTRATION = SCRIPT_DIR.parent
ENV_PATH = PREREGISTRATION.parent / ".env"
load_dotenv(ENV_PATH)

PUBG_EVENTS_DIR = Path("/Users/safiqsindha/Desktop/Project Ditto/Ditto V5.0/data/events/pubg")
V50_SRC = Path("/Users/safiqsindha/Desktop/Project Ditto/Ditto V5.0")
OUT_DIR = PREREGISTRATION / "pubg_artifact_investigation"

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL = "deepseek-v4-pro"
MAX_TOKENS = 32
N_PAIRS = 20

_RE_YES_NO = re.compile(r'\b(YES|NO)\b', re.IGNORECASE)


def parse_content(content):
    if not content:
        return None
    m = _RE_YES_NO.search(content)
    if m:
        return m.group(1).upper()
    return None


def build_client():
    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai package not installed")
        sys.exit(1)
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


def call_api(client, prompt):
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=MAX_TOKENS,
                extra_body={"thinking": {"type": "disabled"}},
            )
            return resp
        except Exception as exc:
            code = getattr(exc, 'status_code', None)
            if code in {429, 500, 502, 503, 504} and attempt < 2:
                time.sleep(5 * (2 ** attempt))
                continue
            return None
    return None


def load_pubg_chain_pairs(n=20):
    """Load PUBG event files and extract clean+adversarial chain pairs."""
    sys.path.insert(0, str(V50_SRC))
    from src.common.schema import GameEvent, ChainCandidate
    from src.harness.prompts import PUBGPromptBuilder
    from src.harness.violation_injector import inject_pubg_elimination_violation
    import hashlib, glob

    files = sorted(PUBG_EVENTS_DIR.glob("*.jsonl"))
    builder = PUBGPromptBuilder()
    pairs = []

    for fp in files:
        if len(pairs) >= n:
            break
        with open(fp) as fh:
            lines = fh.readlines()
        header = json.loads(lines[0])
        game_id = header["game_id"]

        all_events = []
        for i, line in enumerate(lines[1:]):
            try:
                e = json.loads(line)
            except Exception:
                continue
            if "event_type" not in e:
                continue
            all_events.append(GameEvent(
                timestamp=e.get("timestamp", 0.0),
                event_type=e["event_type"],
                actor=e.get("actor", ""),
                location_context=e.get("location_context", {}),
                raw_data_blob=e,
                cell="pubg",
                game_id=game_id,
                sequence_idx=i,
            ))

        action_events = [e for e in all_events if e.event_type != "position_commit"]
        if len(action_events) < 10:
            continue

        game_hash = hashlib.md5(game_id.encode()).hexdigest()[:16]
        for start in range(0, len(action_events) - 15, 8):
            if len(pairs) >= n:
                break
            segment = action_events[start:start + 20]
            sub_id = f"{game_hash}_sub{len(pairs):03d}"
            candidate = ChainCandidate(
                chain_id=sub_id,
                game_id=game_id,
                cell="pubg",
                events=segment,
            )
            result = inject_pubg_elimination_violation(candidate)
            if result:
                clean_chain = candidate
                adv_chain = result.chain
                clean_prompt = builder.build(clean_chain).baseline_prompt
                adv_prompt = builder.build(adv_chain).baseline_prompt
                pairs.append({
                    "chain_id": sub_id,
                    "game_id": game_id,
                    "clean_prompt": clean_prompt,
                    "adv_prompt": adv_prompt,
                    "violation_desc": result.violation_description,
                })

    print(f"Loaded {len(pairs)} PUBG chain pairs")
    return pairs, builder


def make_mod1_strip_marker(clean_prompt):
    """Mod 1: Strip NOTE=Player_X_already_eliminated from clean chain."""
    lines = clean_prompt.split("\n")
    clean_lines = []
    for line in lines:
        # Remove NOTE=... segments from the line
        cleaned = re.sub(r'NOTE=\w+_already_eliminated,?\s*', '', line)
        cleaned = re.sub(r',\s*NOTE=\w+_already_eliminated', '', cleaned)
        clean_lines.append(cleaned)
    return "\n".join(clean_lines)


def make_mod2_move_marker(adv_prompt):
    """Mod 2: Move NOTE= marker to a different (non-elimination-relevant) position.
    Instead of appearing on post-elimination events, move it to the first event."""
    lines = adv_prompt.split("\n")
    # Find NOTE lines and move all NOTE content to line 1
    note_texts = []
    cleaned_lines = []
    for line in lines:
        notes = re.findall(r'NOTE=\w+_already_eliminated', line)
        note_texts.extend(notes)
        cleaned = re.sub(r'NOTE=\w+_already_eliminated,?\s*', '', line)
        cleaned = re.sub(r',\s*NOTE=\w+_already_eliminated', '', cleaned)
        cleaned_lines.append(cleaned)
    # Add note to first non-header line
    if note_texts and len(cleaned_lines) > 2:
        note_str = ", ".join(note_texts[:1])  # just the first note
        # Find first event line (has "t=" pattern)
        for idx, line in enumerate(cleaned_lines):
            if "t=" in line and "|" in line:
                cleaned_lines[idx] = line.rstrip() + f", {note_str}"
                break
    return "\n".join(cleaned_lines)


def make_mod3_rename_marker(adv_prompt):
    """Mod 3: Rename NOTE=Player_X_already_eliminated to STATUS=Player_X_acting."""
    result = re.sub(
        r'NOTE=(\w+)_already_eliminated',
        r'STATUS=\1_currently_acting',
        adv_prompt
    )
    result = re.sub(
        r'ELIMINATES=(\w+)',
        r'TAGGED=\1',
        result
    )
    return result


def run_condition(client, pairs, condition_name, prompt_fn, is_violated):
    """Run API calls for one condition."""
    out_path = OUT_DIR / "raw_responses.ndjson"
    done = set()
    if out_path.exists():
        with open(out_path) as f:
            for line in f:
                r = json.loads(line)
                done.add((r["chain_id"], r["condition"], r.get("is_violated", False)))

    results = []
    with open(out_path, "a") as fout:
        for i, pair in enumerate(pairs):
            key = (pair["chain_id"], condition_name, is_violated)
            if key in done:
                continue

            prompt = prompt_fn(pair)
            print(f"  [{i+1}/{len(pairs)}] {pair['chain_id']} [{condition_name}]")

            t0 = time.time()
            resp = call_api(client, prompt)
            elapsed = round(time.time() - t0, 2)

            if resp is None:
                rec = {
                    "chain_id": pair["chain_id"], "condition": condition_name,
                    "is_violated": is_violated,
                    "api_failure": True, "content": None, "parsed_label": None,
                    "elapsed": elapsed,
                }
            else:
                content = getattr(resp.choices[0].message, "content", "") or ""
                parsed = parse_content(content)
                usage = None
                if hasattr(resp, "usage") and resp.usage:
                    usage = {"input_tokens": resp.usage.prompt_tokens,
                             "output_tokens": resp.usage.completion_tokens}
                # V5.1 semantics: "Is this consistent?" → YES=consistent=no violation, NO=violation
                # So NO = detection, YES = no detection (or false positive)
                # But actually we need to check the question used
                # builder.format_question → "Is the sequence of events above consistent with..."
                # YES = consistent = clean, NO = not consistent = violation detected
                violation_flagged = (parsed == "NO")  # NO = "not consistent" = violation found
                rec = {
                    "chain_id": pair["chain_id"], "condition": condition_name,
                    "is_violated": is_violated,
                    "api_failure": False, "content": content, "parsed_label": parsed,
                    "violation_flagged": violation_flagged,
                    "usage": usage, "elapsed": elapsed,
                }
                print(f"    parsed={parsed} violation_flagged={violation_flagged}")

            fout.write(json.dumps(rec) + "\n")
            fout.flush()
            results.append(rec)
            time.sleep(0.4)

    return results


def compute_metrics(condition_name):
    out_path = OUT_DIR / "raw_responses.ndjson"
    recs = []
    with open(out_path) as f:
        for line in f:
            r = json.loads(line)
            if r["condition"] == condition_name and not r.get("api_failure"):
                recs.append(r)

    clean = [r for r in recs if not r["is_violated"]]
    violated = [r for r in recs if r["is_violated"]]

    def flagged_rate(subset):
        if not subset:
            return None
        return round(sum(1 for r in subset if r.get("violation_flagged")) / len(subset), 4)

    fpr = flagged_rate(clean)
    tpr = flagged_rate(violated)
    gap = round(tpr - fpr, 4) if fpr is not None and tpr is not None else None

    return {
        "condition": condition_name,
        "n_clean": len(clean), "n_violated": len(violated),
        "fpr": fpr, "tpr": tpr, "gap": gap,
        "anti_detection": (fpr is not None and tpr is not None and fpr > tpr),
    }


def write_cross_domain_check(metrics_list):
    path = OUT_DIR / "cross_domain_check.md"
    marker_counts = {}
    # Count NOTE= markers across OLAT chain variants
    olat_variants_dir = PREREGISTRATION / "chain_variants" / "deepseek-v4-pro"
    import glob as g
    olat_files = g.glob(str(olat_variants_dir / "pro_L01_L1" / "*.json"))
    note_count = 0
    for fp in olat_files:
        with open(fp) as f:
            v = json.load(f)
        if "NOTE=" in v.get("prompt_user", "") or "already_eliminated" in v.get("prompt_user", ""):
            note_count += 1

    lines = [
        "# B2 — Cross-Domain Marker Check\n",
        f"**NOTE= / already_eliminated marker in OLAT Pokemon chains:** "
        f"{note_count}/{len(olat_files)} files\n",
        "If note_count=0, the PUBG marker is domain-specific and not contaminating other domains.\n",
        "If note_count>0, the marker pattern may appear in cross-domain chains (requires investigation).\n",
    ]
    path.write_text("\n".join(lines) + "\n")
    print(f"  Wrote {path}")


def write_reproduction_summary(metrics_list):
    path = OUT_DIR / "phase_2b_reproduction.md"
    lines = [
        "# B2 — PUBG Anti-Detection Reproduction Test\n",
        "## Results by Condition\n",
        "| Condition | N_clean | N_violated | FPR | TPR | Gap | Anti-detection? |",
        "|---|---|---|---|---|---|---|",
    ]
    for m in metrics_list:
        anti = "YES" if m["anti_detection"] else "no"
        lines.append(
            f"| {m['condition']} | {m['n_clean']} | {m['n_violated']} | "
            f"{m['fpr']} | {m['tpr']} | {m['gap']} | {anti} |"
        )

    lines.append("\n## Interpretation\n")
    orig = next((m for m in metrics_list if m["condition"] == "original"), None)
    mod1 = next((m for m in metrics_list if m["condition"] == "mod1_strip_marker"), None)
    mod2 = next((m for m in metrics_list if m["condition"] == "mod2_move_marker"), None)
    mod3 = next((m for m in metrics_list if m["condition"] == "mod3_rename_marker"), None)

    if orig:
        if orig["anti_detection"]:
            lines.append(f"**Original reproduces anti-detection** (FPR={orig['fpr']} > TPR={orig['tpr']})")
        else:
            lines.append(f"**Original does NOT show anti-detection** (FPR={orig['fpr']}, TPR={orig['tpr']})")

    if orig and mod1:
        if orig["anti_detection"] and not mod1["anti_detection"]:
            lines.append("**Mod 1 (strip marker) eliminates anti-detection** → marker contributes to FPR")
        elif not orig["anti_detection"] and not mod1["anti_detection"]:
            lines.append("No change from stripping marker — marker not causal")

    if orig and mod3:
        if orig["anti_detection"] and not mod3["anti_detection"]:
            lines.append("**Mod 3 (rename marker) eliminates anti-detection** → specific marker text is causal")
        elif orig["anti_detection"] and mod3["anti_detection"]:
            lines.append("Renaming marker doesn't help → not a keyword-matching artifact")

    # Overall outcome
    if orig and orig["anti_detection"]:
        if mod1 and not mod1["anti_detection"]:
            outcome = "Outcome 1: Anti-detection reproduces AND disappears after mod → marker is causal"
        else:
            outcome = "Outcome 2: Anti-detection reproduces but survives mods → marker not the cause"
    elif orig and not orig["anti_detection"]:
        outcome = "Outcome 3: Anti-detection does NOT reproduce in this replication"
    else:
        outcome = "Unknown — insufficient data"

    lines.append(f"\n**Pre-registered Outcome: {outcome}**")
    path.write_text("\n".join(lines) + "\n")
    print(f"  Wrote {path}")


def main():
    if not DEEPSEEK_API_KEY:
        print("ERROR: DEEPSEEK_API_KEY not set")
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading PUBG chain pairs...")
    pairs, builder = load_pubg_chain_pairs(N_PAIRS)
    if len(pairs) < N_PAIRS:
        print(f"WARNING: Only {len(pairs)} pairs available (needed {N_PAIRS})")

    client = build_client()
    metrics_list = []

    # Phase 1: Original chains (clean + violated)
    print("\n=== Phase 1: Original PUBG chains ===")
    run_condition(client, pairs, "original",
                  lambda p: p["clean_prompt"], is_violated=False)
    run_condition(client, pairs, "original",
                  lambda p: p["adv_prompt"], is_violated=True)
    metrics_list.append(compute_metrics("original"))

    # Phase 2: Modifications
    print("\n=== Phase 2a: Mod 1 — Strip marker from clean chains ===")
    run_condition(client, pairs, "mod1_strip_marker",
                  lambda p: make_mod1_strip_marker(p["clean_prompt"]), is_violated=False)
    run_condition(client, pairs, "mod1_strip_marker",
                  lambda p: p["adv_prompt"], is_violated=True)
    metrics_list.append(compute_metrics("mod1_strip_marker"))

    print("\n=== Phase 2b: Mod 2 — Move marker position in violated chains ===")
    run_condition(client, pairs, "mod2_move_marker",
                  lambda p: p["clean_prompt"], is_violated=False)
    run_condition(client, pairs, "mod2_move_marker",
                  lambda p: make_mod2_move_marker(p["adv_prompt"]), is_violated=True)
    metrics_list.append(compute_metrics("mod2_move_marker"))

    print("\n=== Phase 2c: Mod 3 — Rename marker to neutral field name ===")
    run_condition(client, pairs, "mod3_rename_marker",
                  lambda p: p["clean_prompt"], is_violated=False)
    run_condition(client, pairs, "mod3_rename_marker",
                  lambda p: make_mod3_rename_marker(p["adv_prompt"]), is_violated=True)
    metrics_list.append(compute_metrics("mod3_rename_marker"))

    write_reproduction_summary(metrics_list)
    write_cross_domain_check(metrics_list)

    print("\n=== B2 Complete ===")
    for m in metrics_list:
        print(f"  {m['condition']}: FPR={m['fpr']}, TPR={m['tpr']}, gap={m['gap']}, "
              f"anti_det={m['anti_detection']}")


if __name__ == "__main__":
    main()
