"""
Day -3 chain pool inventory and pre-OLAT sample selection.

Reads the v5.1 Pokemon chain corpus and the symbolic checker verdicts,
builds the OLAT-eligible pool, performs the O7 paralysis filter check
(structurally a no-op given the symbolic checker taxonomy), and emits
the n=250 deterministic Lever 5 L1 random sample for Day -2 verification.

Outputs:
  pre-registration/day_minus_3/chain_pool_inventory.json
  pre-registration/day_minus_3/verification_n250_sample.jsonl
  pre-registration/day_minus_3/day_minus_3_log.txt
"""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DITTO_PARENT = REPO_ROOT.parent  # /Users/safiqsindha/Desktop/Project Ditto

CSV_PATH = DITTO_PARENT / "Ditto-5.3- Pokemon Diag" / "pokemon-v1-symbolic" / "outputs" / "phase3_results_v4.csv"
REAL_DIR = DITTO_PARENT / "Ditto V1" / "chains" / "real_v2"
SHUFFLED_DIR = DITTO_PARENT / "Ditto V1" / "chains" / "shuffled_v2"

OUT_DIR = REPO_ROOT / "pre-registration" / "day_minus_3"
INVENTORY_PATH = OUT_DIR / "chain_pool_inventory.json"
SAMPLE_PATH = OUT_DIR / "verification_n250_sample.jsonl"
LOG_PATH = OUT_DIR / "day_minus_3_log.txt"

# Pre-OLAT verification config
VERIFICATION_N = 250
LEVER_5_RANDOM_SEED = 42  # deterministic per OLAT plan

# O7 paralysis filter assertion: these violation_type tokens, if present in
# the corpus, would indicate paralysis-specific labeling. The symbolic
# checker taxonomy doesn't include any such type — this assertion is a
# guard that confirms the assumption.
PARALYSIS_LIKE_TOKENS = {"paralysis", "para_violation", "para", "fully_paralyzed"}

# Expected valid violation_type values per pokemon_rule_checker.py
EXPECTED_TYPES = {
    "none",
    "monotone_increase",
    "dead_unit_returns",
    "hp_resurrection",
    "faint_no_permanence",
    "double_availability",
    "causal_incoherence",
    "multiple",
}


def log(msg: str, log_lines: list[str]) -> None:
    print(msg)
    log_lines.append(msg)


def load_verdicts(csv_path: Path):
    """Yield (chain_id, violation_present, violation_type, excluded, exclusion_reason) tuples."""
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield (
                row["chain_id"],
                row["violation_present"].lower() == "true",
                row["violation_type"],
                row["excluded"].lower() == "true",
                row["exclusion_reason"],
            )


def classify_chain_id(chain_id: str) -> tuple[str, str]:
    """
    Classify chain by id pattern.
    Returns (real_or_shuffled, match_id) where match_id strips the shuffle suffix.
    Real format:     gen9ou-<numeric>_<p1|p2>
    Shuffled format: gen9ou-<numeric>_<p1|p2>_shuffled_<seed>
    """
    if "_shuffled_" in chain_id:
        match_id = chain_id.split("_shuffled_", 1)[0]
        return "shuffled", match_id
    return "real", chain_id


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log_lines: list[str] = []

    log("=" * 72, log_lines)
    log("Day -3 — Chain Pool Inventory & Verification Sample Selection", log_lines)
    log("=" * 72, log_lines)

    # ------------------------------------------------------------------
    # 1. Verify source files exist
    # ------------------------------------------------------------------
    for p in (CSV_PATH, REAL_DIR, SHUFFLED_DIR):
        if not p.exists():
            log(f"FAIL: source missing: {p}", log_lines)
            return 2
    log(f"Verdicts CSV:    {CSV_PATH}", log_lines)
    log(f"Real chains:     {REAL_DIR}", log_lines)
    log(f"Shuffled chains: {SHUFFLED_DIR}", log_lines)
    log("", log_lines)

    # ------------------------------------------------------------------
    # 2. Load all verdicts
    # ------------------------------------------------------------------
    verdicts = list(load_verdicts(CSV_PATH))
    log(f"Total verdicts loaded: {len(verdicts)}", log_lines)

    # ------------------------------------------------------------------
    # 3. Filter to OLAT-eligible pool
    #    Eligible = not excluded by the symbolic checker
    # ------------------------------------------------------------------
    eligible = [v for v in verdicts if not v[3]]
    excluded = [v for v in verdicts if v[3]]
    log(f"  Eligible (not excluded): {len(eligible)}", log_lines)
    log(f"  Excluded:                {len(excluded)}", log_lines)

    if excluded:
        ex_reasons = Counter(v[4] for v in excluded)
        for reason, count in ex_reasons.most_common():
            log(f"    Excluded reason '{reason}': {count}", log_lines)
    log("", log_lines)

    # ------------------------------------------------------------------
    # 4. Tabulate violation_type distribution
    # ------------------------------------------------------------------
    type_dist = Counter(v[2] for v in eligible)
    log("Violation type distribution (eligible pool):", log_lines)
    for vt, count in type_dist.most_common():
        log(f"  {vt:<25} {count:>6}", log_lines)
    log("", log_lines)

    # ------------------------------------------------------------------
    # 5. O7 paralysis filter check (structural guard)
    # ------------------------------------------------------------------
    paralysis_hits = [vt for vt in type_dist.keys() if any(tok in vt.lower() for tok in PARALYSIS_LIKE_TOKENS)]
    if paralysis_hits:
        log(f"WARNING (O7): unexpected paralysis-like violation_type values found: {paralysis_hits}", log_lines)
        log("Both authors should review chain-pool exclusion before Day -2.", log_lines)
        return 1
    log("O7 paralysis filter: PASS — no paralysis-related violation_type in eligible pool.", log_lines)
    log("  (Symbolic checker taxonomy contains no PARA rule; assertion is structural.)", log_lines)
    log("", log_lines)

    # ------------------------------------------------------------------
    # 6. Validate violation_type taxonomy
    # ------------------------------------------------------------------
    unknown_types = set(type_dist.keys()) - EXPECTED_TYPES
    if unknown_types:
        log(f"WARNING: unexpected violation_type values: {unknown_types}", log_lines)
        log("Both authors should review before Day -2.", log_lines)
        return 1
    log(f"Violation taxonomy: PASS — all {len(type_dist)} types in expected set.", log_lines)
    log("", log_lines)

    # ------------------------------------------------------------------
    # 7. Real vs shuffled split (ground truth for Lever 24 L1)
    # ------------------------------------------------------------------
    real_eligible = [v for v in eligible if classify_chain_id(v[0])[0] == "real"]
    shuf_eligible = [v for v in eligible if classify_chain_id(v[0])[0] == "shuffled"]
    log(f"Ground truth split (Lever 24 L1 — chain_id pattern):", log_lines)
    log(f"  Real (ground truth NO violation):     {len(real_eligible)}", log_lines)
    log(f"  Shuffled (ground truth YES violation): {len(shuf_eligible)}", log_lines)
    log("", log_lines)

    # Note the false-negative shuffled chains (shuffled but symbolic checker
    # missed the violation — these have ground_truth=YES but checker says NO).
    fn_shuf = [v for v in shuf_eligible if v[2] == "none"]
    log(f"  Of shuffled chains, {len(fn_shuf)} have checker verdict='none'", log_lines)
    log(f"  (false negatives from checker's ~88.6% recall; ground truth from chain_id stands)", log_lines)
    log("", log_lines)

    # ------------------------------------------------------------------
    # 8. Verify chain files exist for a quick sample
    # ------------------------------------------------------------------
    log("Spot-checking file existence (10 random chain_ids)...", log_lines)
    rng_check = random.Random(0)
    sample_check = rng_check.sample(eligible, min(10, len(eligible)))
    missing = []
    for chain_id, _, _, _, _ in sample_check:
        cls, _ = classify_chain_id(chain_id)
        d = REAL_DIR if cls == "real" else SHUFFLED_DIR
        f = d / f"{chain_id}.jsonl"
        if not f.exists():
            missing.append(str(f))
    if missing:
        log(f"WARNING: {len(missing)}/10 chain files missing on disk:", log_lines)
        for m in missing[:5]:
            log(f"  - {m}", log_lines)
        return 1
    log("  All 10 spot-check files exist.", log_lines)
    log("", log_lines)

    # ------------------------------------------------------------------
    # 9. Lever 5 L1 random selection for Day -2 verification (n=250)
    #    Per SPEC §6: random selection from v5.1 pool, deterministic seed.
    # ------------------------------------------------------------------
    rng = random.Random(LEVER_5_RANDOM_SEED)
    sample_records = rng.sample(eligible, VERIFICATION_N)
    log(f"Lever 5 L1 random sample: n={VERIFICATION_N}, seed={LEVER_5_RANDOM_SEED}", log_lines)

    sample_real = sum(1 for v in sample_records if classify_chain_id(v[0])[0] == "real")
    sample_shuf = VERIFICATION_N - sample_real
    log(f"  Sample composition: {sample_real} real / {sample_shuf} shuffled", log_lines)

    sample_type_dist = Counter(v[2] for v in sample_records)
    log("  Sample violation_type distribution:", log_lines)
    for vt, count in sample_type_dist.most_common():
        log(f"    {vt:<25} {count:>4}", log_lines)
    log("", log_lines)

    # ------------------------------------------------------------------
    # 10. Write sample JSONL
    # ------------------------------------------------------------------
    with SAMPLE_PATH.open("w") as f:
        for chain_id, vio_present, vio_type, _, _ in sample_records:
            cls, match_id = classify_chain_id(chain_id)
            ground_truth = "violated" if cls == "shuffled" else "intact"
            f.write(json.dumps({
                "chain_id": chain_id,
                "ground_truth": ground_truth,
                "ground_truth_basis": "chain_id_pattern_lever_24_l1",
                "match_id": match_id,
                "kind": cls,
                "symbolic_checker_violation_present": vio_present,
                "symbolic_checker_violation_type": vio_type,
                "chain_path": str((REAL_DIR if cls == "real" else SHUFFLED_DIR) / f"{chain_id}.jsonl"),
            }) + "\n")
    log(f"Wrote sample: {SAMPLE_PATH}", log_lines)

    # ------------------------------------------------------------------
    # 11. Write inventory summary JSON
    # ------------------------------------------------------------------
    inventory = {
        "generated": "2026-05-12",
        "spec_hash": "9ab2e9484fe8837d687a952d132fa07ca771fc37bcd5e5774f1adee91ebefe6c",
        "sources": {
            "verdicts_csv": str(CSV_PATH),
            "real_chains_dir": str(REAL_DIR),
            "shuffled_chains_dir": str(SHUFFLED_DIR),
        },
        "totals": {
            "verdicts_loaded": len(verdicts),
            "eligible": len(eligible),
            "excluded": len(excluded),
            "real_eligible": len(real_eligible),
            "shuffled_eligible": len(shuf_eligible),
        },
        "violation_type_distribution": dict(type_dist),
        "o7_paralysis_filter": {
            "result": "PASS",
            "note": "No paralysis-related violation_type in eligible pool. Symbolic checker has no PARA rule; assertion is structural.",
            "paralysis_like_tokens_searched": sorted(PARALYSIS_LIKE_TOKENS),
        },
        "lever_5_l1_sample": {
            "n": VERIFICATION_N,
            "seed": LEVER_5_RANDOM_SEED,
            "real_count": sample_real,
            "shuffled_count": sample_shuf,
            "violation_type_distribution": dict(sample_type_dist),
            "sample_path": str(SAMPLE_PATH),
        },
        "checker_recall_caveat": {
            "false_negative_shuffled_chains": len(fn_shuf),
            "note": "Ground truth for Lever 24 L1 derives from chain_id pattern, not symbolic checker verdict. These FNs are still 'violated' ground truth.",
        },
    }
    INVENTORY_PATH.write_text(json.dumps(inventory, indent=2))
    log(f"Wrote inventory: {INVENTORY_PATH}", log_lines)

    log("", log_lines)
    log("Day -3 complete. Status: PASS.", log_lines)
    log(f"  - Eligible pool: {len(eligible)} chains", log_lines)
    log(f"  - O7 paralysis filter: PASS (structural)", log_lines)
    log(f"  - Verification n=250 sample ready at {SAMPLE_PATH.name}", log_lines)

    LOG_PATH.write_text("\n".join(log_lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
