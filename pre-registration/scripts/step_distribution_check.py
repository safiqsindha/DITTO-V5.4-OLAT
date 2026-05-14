"""
Step-distribution check for the Day -2 verification sample.

For each violated chain in the n=250 sample, look up violation_step from
phase3_results_v4.csv and tabulate the distribution. Specifically:

  - What fraction of violations occur at step <= k for each k in {3, 5, 8, 12, 20}?
  - At which k does cumulative coverage cross 50%, 80%, 95%?

If most violations occur beyond step 5, the k=5 Lever 8 baseline cannot show
them to the model — explaining the degenerate-NO output on Day -2.

This is read-only analysis: no API calls, no chain file reads (CSV only).
"""

from __future__ import annotations

import csv
import json
import statistics
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DITTO_PARENT = REPO_ROOT.parent
CSV_PATH = DITTO_PARENT / "Ditto-5.3- Pokemon Diag" / "pokemon-v1-symbolic" / "outputs" / "phase3_results_v4.csv"
SAMPLE_PATH = REPO_ROOT / "pre-registration" / "day_minus_3" / "verification_n250_sample.jsonl"
OUT_PATH = REPO_ROOT / "pre-registration" / "day_minus_2" / "step_distribution_analysis.json"

OLAT_K_LEVELS = [3, 5, 8, 12, 20]


def main():
    # Load CSV verdicts, keyed by chain_id
    verdicts = {}
    with CSV_PATH.open() as f:
        for row in csv.DictReader(f):
            verdicts[row["chain_id"]] = row

    # Load n=250 sample
    sample = []
    with SAMPLE_PATH.open() as f:
        for line in f:
            sample.append(json.loads(line))

    # ----------------------------------------------------------------
    # Pull violation_step for sample chains that have violations
    # ----------------------------------------------------------------
    sample_violated = [s for s in sample if s["ground_truth"] == "violated"]
    sample_intact = [s for s in sample if s["ground_truth"] == "intact"]

    # For violated chains, get the symbolic checker's reported violation_step.
    # Note: false-negative shuffled chains have violation_step blank.
    steps_for_violated = []
    blanks = 0
    for s in sample_violated:
        v = verdicts.get(s["chain_id"], {})
        step_str = v.get("violation_step", "").strip()
        if step_str:
            try:
                steps_for_violated.append(int(step_str))
            except ValueError:
                blanks += 1
        else:
            blanks += 1

    print("=" * 72)
    print("Step-Distribution Check — Sample n=250")
    print("=" * 72)
    print(f"Sample composition: {len(sample_violated)} violated, {len(sample_intact)} intact")
    print(f"Violated chains with reported violation_step: {len(steps_for_violated)}")
    print(f"Violated chains with blank/missing step:      {blanks}")
    print(f"  (Blank means symbolic checker found no violation despite shuffled chain_id —")
    print(f"   these are false-negatives from the checker's 88.6% recall. They still")
    print(f"   contribute to 'violated' ground truth but their violation step is unknown.)")
    print()

    if not steps_for_violated:
        print("No violated chains have step data. Cannot analyze.")
        return

    # ----------------------------------------------------------------
    # Distribution stats
    # ----------------------------------------------------------------
    step_counts = Counter(steps_for_violated)
    mn = min(steps_for_violated)
    mx = max(steps_for_violated)
    med = statistics.median(steps_for_violated)
    mean = statistics.mean(steps_for_violated)
    p25, p75 = statistics.quantiles(steps_for_violated, n=4)[0], statistics.quantiles(steps_for_violated, n=4)[2]

    print(f"Violation step (among {len(steps_for_violated)} step-labeled violated chains):")
    print(f"  min={mn}  max={mx}  median={med:.1f}  mean={mean:.2f}  p25={p25:.1f}  p75={p75:.1f}")
    print()

    # ----------------------------------------------------------------
    # Coverage at each Lever 8 k level
    # ----------------------------------------------------------------
    n = len(steps_for_violated)
    print("Cumulative violation visibility at each Lever 8 level:")
    print(f"  (violation_step <= k means the violation is in-frame at that k)")
    print()
    print(f"  {'k':>3}  {'visible':>10}  {'fraction':>10}  {'invisible':>10}")
    print(f"  {'-':>3}  {'-':>10}  {'-':>10}  {'-':>10}")
    coverage = {}
    for k in OLAT_K_LEVELS:
        visible = sum(1 for s in steps_for_violated if s <= k)
        frac = visible / n
        coverage[k] = {"visible": visible, "fraction": frac, "invisible": n - visible}
        print(f"  {k:>3}  {visible:>10}  {frac:>9.1%}  {n - visible:>10}")
    print()

    # ----------------------------------------------------------------
    # Quantile crossings
    # ----------------------------------------------------------------
    sorted_steps = sorted(steps_for_violated)
    quantile_targets = [0.50, 0.80, 0.95]
    print("Quantile crossings (smallest k that covers the given fraction):")
    for q in quantile_targets:
        # The k at index floor(q*n) - 1
        idx = max(0, min(n - 1, int(q * n) - 1))
        k_needed = sorted_steps[idx]
        print(f"  {int(q*100):>3}% of violations visible by step {k_needed}")
    print()

    # ----------------------------------------------------------------
    # By violation type
    # ----------------------------------------------------------------
    by_type = {}
    for s in sample_violated:
        v = verdicts.get(s["chain_id"], {})
        vt = v.get("violation_type", "unknown")
        step_str = v.get("violation_step", "").strip()
        if step_str:
            try:
                by_type.setdefault(vt, []).append(int(step_str))
            except ValueError:
                pass

    print("Per-violation-type step statistics:")
    print(f"  {'type':<22}  {'n':>4}  {'min':>4}  {'median':>6}  {'mean':>6}  {'max':>4}  {'visible@k=5':>11}")
    type_summary = {}
    for vt in sorted(by_type.keys()):
        steps = by_type[vt]
        vis_at_5 = sum(1 for s in steps if s <= 5)
        type_summary[vt] = {
            "n": len(steps),
            "min": min(steps),
            "median": statistics.median(steps),
            "mean": statistics.mean(steps),
            "max": max(steps),
            "visible_at_k5": vis_at_5,
            "visible_at_k5_fraction": vis_at_5 / len(steps),
        }
        print(f"  {vt:<22}  {len(steps):>4}  {min(steps):>4}  {statistics.median(steps):>6.1f}  "
              f"{statistics.mean(steps):>6.2f}  {max(steps):>4}  "
              f"{vis_at_5}/{len(steps)} ({vis_at_5/len(steps):.0%})")
    print()

    # ----------------------------------------------------------------
    # Interpretation
    # ----------------------------------------------------------------
    visible_at_5 = coverage[5]["fraction"]
    visible_at_20 = coverage[20]["fraction"]
    print("=" * 72)
    print("Interpretation")
    print("=" * 72)
    if visible_at_5 < 0.50:
        print(f"FINDING: At k=5, only {visible_at_5:.1%} of violations are in-frame.")
        print(f"This is consistent with Hypothesis 1 — the k=5 baseline does not show")
        print(f"the model where the violations are. The degenerate-NO output is a")
        print(f"rational response given the truncated input.")
    elif visible_at_5 < 0.80:
        print(f"FINDING: At k=5, {visible_at_5:.1%} of violations are in-frame.")
        print(f"Partial visibility — k=5 may be marginally informative but still")
        print(f"insufficient for most chains. Suggests the gap is mostly Hypothesis 1.")
    else:
        print(f"FINDING: At k=5, {visible_at_5:.1%} of violations are in-frame.")
        print(f"Most violations ARE visible at k=5. The degenerate-NO output cannot")
        print(f"be explained by k=5 alone. V4-Flash framing/prior issue (Hypothesis 2-4)")
        print(f"more likely.")
    print()
    print(f"Comparison: at k=20, {visible_at_20:.1%} of violations are in-frame.")

    # ----------------------------------------------------------------
    # Persist
    # ----------------------------------------------------------------
    output = {
        "generated": "2026-05-12",
        "sample_size": {
            "total": len(sample),
            "violated": len(sample_violated),
            "intact": len(sample_intact),
            "violated_with_step_data": len(steps_for_violated),
            "violated_blank_step": blanks,
        },
        "overall_step_stats": {
            "min": mn, "max": mx, "median": med, "mean": mean, "p25": p25, "p75": p75,
        },
        "coverage_by_k": coverage,
        "by_violation_type": type_summary,
    }
    OUT_PATH.write_text(json.dumps(output, indent=2))
    print(f"\nAnalysis saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
