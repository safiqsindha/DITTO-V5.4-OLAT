"""
Day -2 — Pre-OLAT V1-on-Flash verification execution.

Runs n=250 API calls against deepseek-v4-flash with the V1-on-Flash baseline
prompt configuration per SPEC §6 and the global baseline in §5. Applies the
parser cascade per §8, computes detection_rate / gap / effect_size / 95%
bootstrap CI / parse_failure_rate / n_valid, and classifies the result
against the six S1-S6 verification scenarios.

LEVER 15 INTERPRETATION (documented 2026-05-12):
Per the O5 resolution principle (Lever 18 testing implicitly holds L15 at L2),
the pre-OLAT verification also uses Lever 15 L2 (YES/NO violation detection)
framing rather than the literal global baseline L15 L1 (consistency rating
1-10). Rationale: detection_rate, gap, Cohen's h, and the S5 pause threshold
(YES_rate > 0.95) are only defined for binary outputs. The L1 "consistency
rating" label refers to a pre-D-42 pilot framing and was never the production
task (V1 used next-action prediction; V5 used YES/NO). This interpretation
is surfaced in the Day -2 log for both-author review at Day -1.

Outputs:
  pre-registration/day_minus_2/parser_provenance.ndjson
  pre-registration/day_minus_2/raw_responses.ndjson
  pre-registration/day_minus_2/verification_results.json
  pre-registration/day_minus_2/day_minus_2_log.txt
"""

from __future__ import annotations

import json
import math
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    from openai import OpenAI, BadRequestError, RateLimitError
except ImportError:
    print("FAIL: openai package not installed.")
    sys.exit(2)

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = REPO_ROOT / ".env"
SAMPLE_PATH = REPO_ROOT / "pre-registration" / "day_minus_3" / "verification_n250_sample.jsonl"
OUT_DIR = REPO_ROOT / "pre-registration" / "day_minus_2"

PROVENANCE_PATH = OUT_DIR / "parser_provenance.ndjson"
RAW_PATH = OUT_DIR / "raw_responses.ndjson"
RESULTS_PATH = OUT_DIR / "verification_results.json"
LOG_PATH = OUT_DIR / "day_minus_2_log.txt"

# ---------------------------------------------------------------------------
# Global baseline configuration (SPEC §5 + §6)
# ---------------------------------------------------------------------------
MODEL = "deepseek-v4-flash"
BASE_URL = "https://api.deepseek.com"
TEMPERATURE = 0.0
MAX_TOKENS = 32                 # Lever 18 L1 baseline (32-token cap from V1)
CUTOFF_K = 15                   # Lever 8 L3 baseline per Amendment #2 (k=15)
PER_CALL_TIMEOUT_S = 60.0
MAX_WORKERS = 4                 # concurrency: gentle on rate limits

# Bootstrap config for 95% CI
N_BOOTSTRAP = 2000
BOOTSTRAP_SEED = 1337

# Pause thresholds per O6 (locked)
S1_THRESHOLD_GAP_UPPER = 0.05
S2_THRESHOLD_GAP_LOWER = -0.05
S3_THRESHOLD_PARSE_FAIL = 0.05
S4_THRESHOLD_N_VALID_MIN = 200
S5_THRESHOLD_DEGEN = 0.95
S6_THRESHOLD_DETECTION = 0.80
S6_THRESHOLD_GAP_LOWER = 0.10

# Lever 15 framing (per documented O5-style interpretation)
QUESTION_TEXT = "Does this battle chain contain any rule violations?"
OUTPUT_ANCHOR = "The answer is YES or NO."

# ---------------------------------------------------------------------------
# Parser cascade (SPEC §8)
# ---------------------------------------------------------------------------
STRICT_RE = re.compile(r"(?:Therefore,\s+)?[Tt]he answer is\s+(YES|NO)\b", re.IGNORECASE)
PERMISSIVE_RE = re.compile(r"(?i)(?:answer is|answer:|conclusion:)\s*(yes|no)\b")
FIRST_TOKEN_RE = re.compile(r"^\W*(YES|NO)\b", re.IGNORECASE)


def parse_response(text: str) -> tuple[str | None, str]:
    """Apply the four-stage parser cascade. Returns (label or None, stage_reached)."""
    if not text:
        return None, "unparseable"
    s = text.strip()
    m = STRICT_RE.search(s)
    if m:
        return m.group(1).upper(), "strict"
    m = PERMISSIVE_RE.search(s)
    if m:
        return m.group(1).upper(), "permissive"
    head = " ".join(s.split()[:10])
    m = FIRST_TOKEN_RE.search(head)
    if m:
        return m.group(1).upper(), "first_token"
    return None, "unparseable"


# ---------------------------------------------------------------------------
# V1 chain truncation logic (copied from Ditto V1/src/prompt_builder.py)
# ---------------------------------------------------------------------------
_STEP_BOUNDARY = re.compile(r"(Step \d+)")


def cutoff_rendered(rendered: str, k: int) -> str:
    """First k steps of a rendered chain string."""
    if k <= 0:
        return ""
    parts = _STEP_BOUNDARY.split(rendered)
    steps: list[tuple[str, str]] = []
    i = 0
    while i < len(parts) and not _STEP_BOUNDARY.fullmatch(parts[i]):
        i += 1
    while i + 1 < len(parts):
        header = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""
        if _STEP_BOUNDARY.fullmatch(header):
            steps.append((header, body))
            i += 2
        else:
            i += 1
    selected = steps[:k]
    return "".join(header + body for header, body in selected)


def build_user_prompt(rendered_steps: str) -> str:
    """V1-on-Flash baseline prompt for pre-OLAT verification."""
    return f"{rendered_steps.rstrip()}\n\n{QUESTION_TEXT} {OUTPUT_ANCHOR}"


# ---------------------------------------------------------------------------
# Env loader
# ---------------------------------------------------------------------------
def load_env(env_path: Path) -> None:
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and v and not os.environ.get(k, "").strip():
            os.environ[k] = v


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------
def cohens_h(p1: float, p2: float) -> float:
    """Cohen's h effect size for difference between two proportions."""
    def phi(p):
        # clip to avoid asin domain issues
        p = max(min(p, 1.0 - 1e-12), 1e-12)
        return 2.0 * math.asin(math.sqrt(p))
    return phi(p1) - phi(p2)


def bootstrap_ci_gap(
    intact_correct: list[int],
    violated_correct: list[int],
    n_boot: int,
    seed: int,
) -> tuple[float, float]:
    """95% bootstrap CI for gap = violated_rate - intact_rate."""
    rng = random.Random(seed)
    gaps = []
    n_i, n_v = len(intact_correct), len(violated_correct)
    if n_i == 0 or n_v == 0:
        return (float("nan"), float("nan"))
    for _ in range(n_boot):
        i_resample = [intact_correct[rng.randrange(n_i)] for _ in range(n_i)]
        v_resample = [violated_correct[rng.randrange(n_v)] for _ in range(n_v)]
        p_i = sum(i_resample) / n_i
        p_v = sum(v_resample) / n_v
        gaps.append(p_v - p_i)
    gaps.sort()
    lo = gaps[int(0.025 * n_boot)]
    hi = gaps[int(0.975 * n_boot)]
    return lo, hi


# ---------------------------------------------------------------------------
# Per-chain runner
# ---------------------------------------------------------------------------
def run_one(client, record: dict, log_lock) -> dict:
    chain_path = Path(record["chain_path"])
    with chain_path.open() as f:
        chain = json.loads(f.readline())
    rendered = chain["rendered"]
    truncated = cutoff_rendered(rendered, CUTOFF_K)
    user_msg = build_user_prompt(truncated)
    t0 = time.monotonic()
    err = None
    text = ""
    try:
        r = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": user_msg}],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            extra_body={"thinking": {"type": "disabled"}},
        )
        text = (r.choices[0].message.content or "").strip()
        served_model = getattr(r, "model", "?")
        prompt_tokens = r.usage.prompt_tokens
        completion_tokens = r.usage.completion_tokens
    except (BadRequestError, RateLimitError) as e:
        err = f"{type(e).__name__}: {e}"
        served_model = None
        prompt_tokens = completion_tokens = None
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        served_model = None
        prompt_tokens = completion_tokens = None
    elapsed = time.monotonic() - t0

    parsed_label, parse_stage = parse_response(text)
    ground_truth = record["ground_truth"]  # "violated" or "intact"
    ground_truth_label = "YES" if ground_truth == "violated" else "NO"
    correct = (parsed_label == ground_truth_label) if parsed_label is not None else None

    return {
        "chain_id": record["chain_id"],
        "ground_truth": ground_truth,
        "ground_truth_label": ground_truth_label,
        "kind": record["kind"],
        "raw_response": text,
        "parsed_label": parsed_label,
        "parse_stage": parse_stage,
        "correct": correct,
        "elapsed_s": round(elapsed, 2),
        "error": err,
        "served_model": served_model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "k_used": CUTOFF_K,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log_lines: list[str] = []

    def log(msg: str):
        print(msg, flush=True)
        log_lines.append(msg)

    log("=" * 72)
    log("Day -2 — Pre-OLAT V1-on-Flash Verification")
    log("=" * 72)
    log(f"Model:        {MODEL}")
    log(f"Endpoint:     {BASE_URL}")
    log(f"Temperature:  {TEMPERATURE}")
    log(f"max_tokens:   {MAX_TOKENS}  (Lever 18 L1 = V1 32-token cap)")
    log(f"cutoff k:     {CUTOFF_K}    (Lever 8 L2 baseline)")
    log(f"thinking:     disabled (extra_body, per Lever 12 L3 constraint)")
    log(f"Sample:       {SAMPLE_PATH}")
    log("")
    log("Lever 15 interpretation: L2 (YES/NO) — see Day -2 docstring for rationale.")
    log(f"Question:     {QUESTION_TEXT!r}")
    log(f"Anchor:       {OUTPUT_ANCHOR!r}")
    log("=" * 72)

    if not SAMPLE_PATH.exists():
        log(f"FAIL: sample missing: {SAMPLE_PATH}")
        return 2

    load_env(ENV_PATH)
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        log("FAIL: DEEPSEEK_API_KEY not loaded.")
        return 2
    log(f"Key prefix: {key[:8]}... (length={len(key)})")

    sample_records = []
    with SAMPLE_PATH.open() as f:
        for line in f:
            sample_records.append(json.loads(line))
    log(f"Sample loaded: {len(sample_records)} chains")
    log("")

    client = OpenAI(api_key=key, base_url=BASE_URL, timeout=PER_CALL_TIMEOUT_S)

    log_lock = None  # placeholder for future locking
    results = []
    t_start = time.monotonic()
    log("Starting parallel API calls...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(run_one, client, rec, log_lock): rec for rec in sample_records}
        completed = 0
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            completed += 1
            if completed % 25 == 0 or completed == len(sample_records):
                log(f"  Progress: {completed}/{len(sample_records)}")

    t_total = time.monotonic() - t_start
    log(f"All calls complete in {t_total:.1f}s ({t_total/len(results):.2f}s/call avg)")
    log("")

    # --- Persist raw + provenance ---
    with RAW_PATH.open("w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    log(f"Raw responses written:    {RAW_PATH}")
    with PROVENANCE_PATH.open("w") as f:
        for r in results:
            f.write(json.dumps({
                "chain_id": r["chain_id"],
                "parse_stage": r["parse_stage"],
                "parsed_label": r["parsed_label"],
                "ground_truth_label": r["ground_truth_label"],
                "correct": r["correct"],
                "raw_response_preview": r["raw_response"][:100],
            }) + "\n")
    log(f"Parser provenance written: {PROVENANCE_PATH}")
    log("")

    # --- Compute metrics ---
    n_attempted = len(results)
    error_count = sum(1 for r in results if r["error"])
    unparseable = sum(1 for r in results if r["parse_stage"] == "unparseable")
    parse_failure_rate = unparseable / n_attempted
    n_valid = n_attempted - unparseable - error_count

    by_stage = {}
    for r in results:
        by_stage[r["parse_stage"]] = by_stage.get(r["parse_stage"], 0) + 1

    intact_correct = [r["correct"] for r in results if r["correct"] is not None and r["ground_truth"] == "intact"]
    violated_correct = [r["correct"] for r in results if r["correct"] is not None and r["ground_truth"] == "violated"]

    n_intact = len(intact_correct)
    n_violated = len(violated_correct)
    detection_intact = (sum(intact_correct) / n_intact) if n_intact else float("nan")
    detection_violated = (sum(violated_correct) / n_violated) if n_violated else float("nan")
    gap = detection_violated - detection_intact if (n_intact and n_violated) else float("nan")
    h = cohens_h(detection_violated, detection_intact) if (n_intact and n_violated) else float("nan")
    ci_lo, ci_hi = bootstrap_ci_gap(intact_correct, violated_correct, N_BOOTSTRAP, BOOTSTRAP_SEED)

    # YES/NO rate among parseable responses
    parsed = [r for r in results if r["parsed_label"] is not None]
    yes_rate = sum(1 for r in parsed if r["parsed_label"] == "YES") / len(parsed) if parsed else float("nan")
    no_rate = sum(1 for r in parsed if r["parsed_label"] == "NO") / len(parsed) if parsed else float("nan")

    log("=" * 72)
    log("Verification Metrics")
    log("=" * 72)
    log(f"n_attempted:               {n_attempted}")
    log(f"n_valid (parseable+no_err): {n_valid}")
    log(f"errors:                    {error_count}")
    log(f"unparseable:               {unparseable}")
    log(f"parse_failure_rate:        {parse_failure_rate:.4f}")
    log(f"")
    log(f"Parse stage breakdown:")
    for stage in ("strict", "permissive", "first_token", "unparseable"):
        count = by_stage.get(stage, 0)
        log(f"  {stage:<12}  {count:>4}  ({100*count/n_attempted:5.1f}%)")
    log(f"")
    log(f"n_intact:                  {n_intact}")
    log(f"n_violated:                {n_violated}")
    log(f"detection_rate_intact:     {detection_intact:.4f}")
    log(f"detection_rate_violated:   {detection_violated:.4f}")
    log(f"gap (violated - intact):   {gap:+.4f}")
    log(f"Cohen's h:                 {h:+.4f}")
    log(f"95% bootstrap CI of gap:   [{ci_lo:+.4f}, {ci_hi:+.4f}]  (n_boot={N_BOOTSTRAP}, seed={BOOTSTRAP_SEED})")
    log(f"")
    log(f"YES_rate:                  {yes_rate:.4f}")
    log(f"NO_rate:                   {no_rate:.4f}")

    # --- Scenario classification ---
    log("")
    log("=" * 72)
    log("Scenario Classification (S1-S6)")
    log("=" * 72)
    triggers = []
    if not math.isnan(gap):
        if gap > S1_THRESHOLD_GAP_UPPER:
            triggers.append("S1 (unexpected positive signal): gap > +0.05")
        if gap < S2_THRESHOLD_GAP_LOWER:
            triggers.append("S2 (anti-detection): gap < -0.05")
    if parse_failure_rate > S3_THRESHOLD_PARSE_FAIL:
        triggers.append(f"S3 (parse failure): {parse_failure_rate:.4f} > 0.05")
    if n_valid < S4_THRESHOLD_N_VALID_MIN:
        triggers.append(f"S4 (incomplete run): n_valid {n_valid} < 200")
    if not math.isnan(yes_rate):
        if yes_rate > S5_THRESHOLD_DEGEN or no_rate > S5_THRESHOLD_DEGEN:
            triggers.append("S5 (degenerate output)")
    if not math.isnan(detection_violated) and not math.isnan(gap):
        if detection_violated >= S6_THRESHOLD_DETECTION and gap >= S6_THRESHOLD_GAP_LOWER:
            triggers.append("S6 (V4-Flash organic competence): detection>=0.80 AND gap>=0.10")

    if triggers:
        log("PAUSE triggered:")
        for t in triggers:
            log(f"  - {t}")
        log("Both-author review required before Day -1 signoff.")
        proceed = False
    else:
        log("No scenarios triggered.")
        log(f"  Proceed conditions: parse_failure_rate ({parse_failure_rate:.4f}) <= 0.05 ✓")
        log(f"                      n_valid ({n_valid}) >= 200 ✓")
        log("Result is interpretable. Awaiting both-author signoff at Day -1.")
        proceed = True

    # --- Persist results ---
    results_doc = {
        "generated": "2026-05-12",
        "spec_hash": "9ab2e9484fe8837d687a952d132fa07ca771fc37bcd5e5774f1adee91ebefe6c",
        "config": {
            "model": MODEL,
            "endpoint": BASE_URL,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
            "cutoff_k": CUTOFF_K,
            "extra_body": {"thinking": {"type": "disabled"}},
            "lever_15_interpretation": "L2 (YES/NO) — see day_minus_2.py docstring",
            "question_text": QUESTION_TEXT,
            "output_anchor": OUTPUT_ANCHOR,
        },
        "metrics": {
            "n_attempted": n_attempted,
            "n_valid": n_valid,
            "errors": error_count,
            "unparseable": unparseable,
            "parse_failure_rate": parse_failure_rate,
            "parse_stage_breakdown": by_stage,
            "n_intact": n_intact,
            "n_violated": n_violated,
            "detection_rate_intact": detection_intact,
            "detection_rate_violated": detection_violated,
            "gap": gap,
            "cohens_h": h,
            "ci_95_gap": [ci_lo, ci_hi],
            "yes_rate_among_parsed": yes_rate,
            "no_rate_among_parsed": no_rate,
        },
        "scenarios_triggered": triggers,
        "proceed_recommendation": proceed,
        "elapsed_s_total": round(t_total, 2),
    }
    RESULTS_PATH.write_text(json.dumps(results_doc, indent=2))
    log("")
    log(f"Results written:           {RESULTS_PATH}")

    LOG_PATH.write_text("\n".join(log_lines) + "\n")
    return 0 if proceed else 3


if __name__ == "__main__":
    sys.exit(main())
