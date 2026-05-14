#!/usr/bin/env python3
"""
Amendment #7 Analysis — L18 L4 retest effect tables, sensitivities, summary.

Loads amendment_7/provenance.ndjson + baseline rows from parser_provenance.ndjson,
runs the full Day 2 analysis pipeline filtered to L18 L4 + baselines, and writes
parallel-product outputs to amendment_7/.

These outputs are NOT integrated into primary effect tables without both-author signoff.

SPEC hash: dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8
"""
import csv
import json
import sys
from pathlib import Path

# Import shared helpers from day2_analysis
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import day2_analysis as d2

ROOT = SCRIPT_DIR.parent
PROVENANCE_PRIMARY = ROOT / "parser_provenance.ndjson"
PROVENANCE_AMEND7 = ROOT / "amendment_7" / "provenance.ndjson"
ASSIGNMENTS_LOG = ROOT / "chain_condition_assignments.ndjson"
OUT_DIR = ROOT / "amendment_7"

SPEC_HASH = "dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8"


def main():
    # Load primary provenance (for baselines)
    primary = d2.load_ndjson(PROVENANCE_PRIMARY)
    amend7 = d2.load_ndjson(PROVENANCE_AMEND7)
    print(f"Loaded {len(primary)} primary records, {len(amend7)} amendment_7 records.")

    # Filter primary to baselines only; drop the original (failed) L18 L4 records
    primary_baselines = [r for r in primary
                         if r['condition_id'] in ('flash_baseline', 'pro_baseline')]
    print(f"Baseline records (Flash + Pro): {len(primary_baselines)}")

    # Combined provenance: baselines + amendment_7 L18 L4
    combined = primary_baselines + amend7
    print(f"Combined provenance: {len(combined)} records.")

    # Chain order: union of all chain_ids in combined provenance
    chain_ids = sorted({r['sample_id'] for r in combined})
    print(f"Unique chains: {len(chain_ids)}")

    # Build condition arrays
    cond_arrays = d2.build_condition_arrays(combined, chain_ids)
    print(f"Conditions: {sorted(k[1] for k in cond_arrays.keys())}")

    # Run analysis per universe
    all_rows = []
    for universe in d2.UNIVERSES:
        print(f"\n=== Universe {universe} ===")
        rows = d2.analyze_universe(universe, cond_arrays, chain_ids)
        all_rows.extend(rows)

    # Empirical Bayes shrinkage (within Flash/Pro × universe — only L18 L4 conditions here,
    # so shrinkage will be minimal/trivial with n=1 condition per group)
    all_rows = d2.apply_eb_shrinkage(all_rows)

    # Filter to L18 L4 + baselines for output
    output_rows = [r for r in all_rows
                   if r['is_baseline'] or
                   (r.get('lever_varied') == 18 and r.get('level_varied') == 'L4')]
    print(f"\nOutput rows: {len(output_rows)} (baselines + L18 L4 × 3 universes)")

    # Write effect tables per universe
    fieldnames = [
        'condition_id', 'model', 'universe', 'lever_varied', 'level_varied',
        'is_baseline', 'n_total', 'n_valid', 'n_api_fail',
        'n_violated_valid', 'n_intact_valid',
        'dr_violated', 'dr_intact', 'gap', 'gap_ci_lo', 'gap_ci_hi',
        'effect_size', 'effect_ci_lo', 'effect_ci_hi', 'effect_boot_std',
        'classification', 'ci_excludes_zero', 'cohens_h',
        'parse_failure_rate', 'api_failure_rate',
        'degenerate_variance', 'insufficient_n',
        'n_parsed_strict12', 'n_parsed_fallback34',
        's1_as_no_effect', 's1_classification',
        's2_as_random_effect', 's2_classification',
        's3_arcsine_effect', 's3_arcsine_gap_cond', 's3_arcsine_gap_base', 's3_classification',
        's4_parser_strict_effect', 's4_ci_lo', 's4_ci_hi', 's4_classification',
        's5_parse_fail_flagged', 's6_quartile_analysis',
        'robustness_concern', 'hidden_signal_candidate', 'effect_size_shrunken',
    ]

    for universe in d2.UNIVERSES:
        u_rows = [r for r in output_rows if r['universe'] == universe]
        path = OUT_DIR / f"effect_table_universe_{universe}.csv"
        with open(path, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            w.writeheader()
            for r in u_rows:
                w.writerow(r)
        print(f"  Wrote {path.name}: {len(u_rows)} rows")

    # Write a compact summary
    write_summary(output_rows, cond_arrays)
    print("\nDone.")


def write_summary(output_rows, cond_arrays):
    summary_path = OUT_DIR / "summary.md"
    lines = []
    lines.append("# Amendment #7 — L18 L4 Retest Summary")
    lines.append("")
    lines.append(f"**SPEC hash:** `{SPEC_HASH}`")
    lines.append("**Generated:** 2026-05-13")
    lines.append("**Retest config:** `max_tokens=4096`, `thinking: enabled`. Other params unchanged from original L18 L4.")
    lines.append("**Status:** Parallel product. NOT integrated into primary effect tables without both-author signoff.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Headline Effect Table (L18 L4)")
    lines.append("")

    l18l4_rows = [r for r in output_rows if not r['is_baseline']]
    lines.append("| Condition | Universe | n_valid | dr_violated | dr_intact | gap | effect_size | CI | Classification | Parse fail rate | API fail rate |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in sorted(l18l4_rows, key=lambda x: (x['condition_id'], x['universe'])):
        ci = (f"[{r['effect_ci_lo']}, {r['effect_ci_hi']}]"
              if r['effect_ci_lo'] is not None else "—")
        lines.append(
            f"| {r['condition_id']} | {r['universe']} | {r['n_valid']} | "
            f"{r['dr_violated']} | {r['dr_intact']} | {r['gap']} | "
            f"{r['effect_size']} | {ci} | {r['classification']} | "
            f"{r['parse_failure_rate']} | {r['api_failure_rate']} |"
        )
    lines.append("")

    lines.append("## Comparison to Original L18 L4 (max_tokens=64)")
    lines.append("")
    lines.append("Original L18 L4: all 100 records `Unknown` (0 parsed; `finish_reason=length`, content empty).")
    lines.append("")
    lines.append("Amendment #7 retest: see effect table above. The retest produces measurable effect sizes for the first time.")
    lines.append("")

    lines.append("## Comparison to L18 L2/L3 (existing primary results)")
    lines.append("")
    lines.append("From primary effect tables (Universe L3):")
    lines.append("")
    lines.append("| Condition | Effect | Classification |")
    lines.append("|---|---|---|")
    lines.append("| flash_L18_L2 | 0.217 | Meaningful |")
    lines.append("| flash_L18_L3 | 0.044 | Null |")
    lines.append("| pro_L18_L2 | 0.379 | Meaningful |")
    lines.append("| pro_L18_L3 | 0.354 | Meaningful |")
    for r in sorted(l18l4_rows, key=lambda x: x['condition_id']):
        if r['universe'] == 'L3':
            lines.append(f"| {r['condition_id']} | {r['effect_size']} | {r['classification']} |")
    lines.append("")

    # Sensitivities for L18 L4
    lines.append("## Sensitivity Analyses (L18 L4)")
    lines.append("")
    lines.append("| Condition | Universe | S1 (as_no) | S2 (as_random) | S3 (arcsine) | S4 (parser-strict) | S5 parse-fail flag | Robustness concern |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in sorted(l18l4_rows, key=lambda x: (x['condition_id'], x['universe'])):
        s4 = (f"{r['s4_parser_strict_effect']} ({r['s4_classification']})"
              if r['s4_parser_strict_effect'] is not None else "Unknown")
        lines.append(
            f"| {r['condition_id']} | {r['universe']} | "
            f"{r['s1_as_no_effect']} ({r['s1_classification']}) | "
            f"{r['s2_as_random_effect']} ({r['s2_classification']}) | "
            f"{r['s3_arcsine_effect']} ({r['s3_classification']}) | "
            f"{s4} | "
            f"{r['s5_parse_fail_flagged']} | "
            f"{r['robustness_concern']} |"
        )
    lines.append("")

    # YES-bias check (descriptive)
    lines.append("## YES-Bias Diagnostic")
    lines.append("")
    lines.append("Detection rate on intact vs. violated chains (Universe L3 — symbolic checker, the strictest ground truth):")
    lines.append("")
    lines.append("| Condition | dr_violated | dr_intact | Both ≥ 0.5? | Net YES rate |")
    lines.append("|---|---|---|---|---|")
    for r in sorted(l18l4_rows, key=lambda x: x['condition_id']):
        if r['universe'] != 'L3':
            continue
        drv = r['dr_violated'] or 0
        dri = r['dr_intact'] or 0
        both_high = "Yes — YES-biased" if (drv >= 0.5 and dri >= 0.5) else "No"
        # Net YES rate = weighted by n_violated_valid + n_intact_valid
        nv = r['n_violated_valid'] or 0
        ni = r['n_intact_valid'] or 0
        net = ((drv * nv + dri * ni) / (nv + ni)) if (nv + ni) > 0 else None
        lines.append(f"| {r['condition_id']} | {drv} | {dri} | {both_high} | {round(net, 3) if net is not None else 'n/a'} |")
    lines.append("")

    lines.append("## Operational Notes")
    lines.append("")
    lines.append("- All API calls used `max_tokens=4096` with `thinking: {type: enabled}`. Other parameters unchanged from original L18 L4 (temperature=0.0).")
    lines.append("- Parse path: 4-stage cascade on `content` field only (SPEC §8, Amendment #3). `reasoning_content` preserved for diagnostic but never parsed.")
    lines.append("- Bootstrap: BCa, 10K iterations; seed=42 (Flash), seed=43 (Pro). Same as Day 2 primary.")
    lines.append("- Six sensitivity analyses applied identically to primary. S6 (response-length quartile) is computed only for L18 L2/L3 — not applicable to L18 L4 because L4 is single-level. S4 may be vacuous for the same baseline-mismatch reason as L18 L2/L3.")
    lines.append("")
    lines.append("## Output Files")
    lines.append("")
    lines.append("- `effect_table_universe_L1.csv`, `..._L2.csv`, `..._L3.csv` — full effect tables (baselines + L18 L4)")
    lines.append("- `provenance.ndjson` — parsed records from the retest")
    lines.append("- `raw_responses.ndjson` — full API responses with reasoning_content")
    lines.append("- `summary.md` — this file")
    lines.append("- See also: `../amendments/amendment_7.md` for the methodology amendment document.")

    summary_path.write_text("\n".join(lines))
    print(f"  Wrote {summary_path.name}")


if __name__ == "__main__":
    main()
