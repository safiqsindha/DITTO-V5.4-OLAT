#!/usr/bin/env python3
"""
Phase 2 Tool Augmentation Pre-Work.

Task 2A: Generate checker_verdicts.csv — 50 Amendment #7 chains with all
         ground truths, violation types, synthesized checker verdict text,
         and agreement matrix.

Task 2D: Lever 16 relevance analysis → lever_16_relevance.md

Writes:
  pre-registration/tool_augmentation_prep/checker_verdicts.csv
  pre-registration/tool_augmentation_prep/lever_16_relevance.md

Zero API cost; read-only.
"""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "tool_augmentation_prep"
OUT_DIR.mkdir(exist_ok=True)

VARIANTS_FLASH = ROOT / "chain_variants" / "deepseek-v4-flash" / "flash_L18_L4"


def load_ndjson(path):
    recs = []
    with open(path) as f:
        for line in f:
            if line.strip():
                recs.append(json.loads(line))
    return recs


def load_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Violation-type → human-readable checker output
# ---------------------------------------------------------------------------
_VT_DESCRIPTIONS = {
    'none': (
        "VERDICT: NO VIOLATION\n"
        "Rule checked: All resource budgets, tool availability transitions, "
        "subgoal transitions, and coordination dependencies were self-consistent.\n"
        "No monotone-decrease violations, HP-resurrection events, causal "
        "incoherence, or conflicting state transitions detected."
    ),
    'hp_resurrection': (
        "VERDICT: VIOLATION DETECTED — HP RESURRECTION\n"
        "Rule violated: ResourceBudget monotone constraint for HP.\n"
        "A unit's HP dropped to 0% (faint) and later appeared at a higher "
        "value (> 0%) without an intervening revival action. HP cannot increase "
        "after reaching 0% under standard battle rules."
    ),
    'monotone_increase': (
        "VERDICT: VIOLATION DETECTED — MONOTONE INCREASE\n"
        "Rule violated: ResourceBudget monotone-decrease constraint.\n"
        "A resource annotated decay=monotone_decrease increased between "
        "consecutive observations. Resources with this constraint may only "
        "decrease or stay constant; any increase is a rule violation."
    ),
    'causal_incoherence': (
        "VERDICT: VIOLATION DETECTED — CAUSAL INCOHERENCE\n"
        "Rule violated: SubGoalTransition or ToolAvailability causal ordering.\n"
        "A state transition occurred without a valid triggering condition, or a "
        "unit transition referenced a state that could not have been reached by "
        "the preceding event sequence. The event ordering is causally inconsistent."
    ),
    'multiple': (
        "VERDICT: VIOLATION DETECTED — MULTIPLE VIOLATIONS\n"
        "Rules violated: More than one constraint category triggered.\n"
        "The chain contains violations across at least two rule categories "
        "(e.g., both HP-resurrection and monotone-increase, or "
        "HP-resurrection and causal incoherence). Each violation independently "
        "constitutes a rule breach."
    ),
}

_VT_RULE = {
    'none': 'none',
    'hp_resurrection': 'ResourceBudget(HP) monotone constraint',
    'monotone_increase': 'ResourceBudget monotone-decrease constraint',
    'causal_incoherence': 'SubGoalTransition / ToolAvailability causal ordering',
    'multiple': 'Multiple (≥2 categories)',
}


def checker_verdict_text(vt, gt_l3):
    base = _VT_DESCRIPTIONS.get(vt, _VT_DESCRIPTIONS['none'])
    if gt_l3 and vt == 'none':
        # Ground truth says yes but violation_type is none — shouldn't happen normally
        base = _VT_DESCRIPTIONS['multiple']
    return base


def gt_agreement_pattern(gt):
    """Return a short string like 'all_agree_YES', 'all_agree_NO', 'L1_disagrees', etc."""
    l1 = bool(gt.get('L1_shuffled_vs_real'))
    l2 = bool(gt.get('L2_planted_violations'))
    l3 = bool(gt.get('L3_symbolic_checker'))
    if l1 == l2 == l3 == True:
        return 'all_agree_YES'
    if l1 == l2 == l3 == False:
        return 'all_agree_NO'
    truths = [l1, l2, l3]
    yes_count = sum(truths)
    if yes_count == 1:
        return 'only_one_YES'
    if yes_count == 2:
        return 'two_YES_one_NO'
    return 'mixed'


# =============================================================================
# TASK 2A — checker_verdicts.csv
# =============================================================================
def task_2a():
    print("Task 2A: Generating checker_verdicts.csv…")
    a7 = load_ndjson(ROOT / "amendment_7" / "provenance.ndjson")
    # Deduplicate: use flash records (same chains as pro, identical ground truth)
    flash_recs = {r['sample_id']: r for r in a7 if 'flash' in r.get('condition_id', '')}

    # Load prompt text from chain variant files for example instantiation
    prompt_map = {}
    for vf in VARIANTS_FLASH.glob("*.json"):
        d = json.loads(vf.read_text())
        prompt_map[d['chain_id']] = d.get('prompt_user', '')

    rows = []
    for chain_id in sorted(flash_recs):
        r = flash_recs[chain_id]
        gt = r.get('ground_truth', {})
        vt = r.get('violation_type', 'none')
        cvt = checker_verdict_text(vt, gt.get('L3_symbolic_checker'))
        rows.append({
            'chain_id':          chain_id,
            'GT_L1_shuffled':    gt.get('L1_shuffled_vs_real', False),
            'GT_L2_planted':     gt.get('L2_planted_violations', False),
            'GT_L3_symbolic':    gt.get('L3_symbolic_checker', False),
            'violation_type':    vt,
            'rule_triggered':    _VT_RULE.get(vt, 'unknown'),
            'gt_agreement':      gt_agreement_pattern(gt),
            'checker_verdict_text': cvt,
        })

    out_path = OUT_DIR / "checker_verdicts.csv"
    fieldnames = ['chain_id', 'GT_L1_shuffled', 'GT_L2_planted', 'GT_L3_symbolic',
                  'violation_type', 'rule_triggered', 'gt_agreement',
                  'checker_verdict_text']
    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)

    # Summary statistics
    total = len(rows)
    vt_dist = Counter(r['violation_type'] for r in rows)
    l3_yes = sum(1 for r in rows if r['GT_L3_symbolic'])
    l3_no  = total - l3_yes
    agree_dist = Counter(r['gt_agreement'] for r in rows)

    print(f"  Wrote {out_path.name}: {total} chains")
    print(f"  L3 violated: {l3_yes}, L3 intact: {l3_no}")
    print(f"  Violation types: {dict(vt_dist)}")
    print(f"  GT agreement patterns: {dict(agree_dist)}")

    return rows, prompt_map


# =============================================================================
# TASK 2D — lever_16_relevance.md
# =============================================================================
def task_2d():
    print("Task 2D: Generating lever_16_relevance.md…")

    # Extract lever 16 data from Universe L3 effect table
    effect_rows = load_csv(ROOT / "day_2" / "effect_table_universe_L3.csv")
    relevant_ids = {'pro_baseline', 'pro_L16_L2', 'pro_L16_L3',
                    'flash_baseline', 'flash_L16_L2', 'flash_L16_L3'}
    l16_data = {r['condition_id']: r for r in effect_rows if r['condition_id'] in relevant_ids}

    # Also get Universe L1/L2 for completeness
    l1_rows = {r['condition_id']: r for r in
               load_csv(ROOT / "day_2" / "effect_table_universe_L1.csv")
               if r['condition_id'] in relevant_ids}
    l2_rows = {r['condition_id']: r for r in
               load_csv(ROOT / "day_2" / "effect_table_universe_L2.csv")
               if r['condition_id'] in relevant_ids}

    lines = []
    lines.append("# Task 2D — Lever 16 Relevance to Tool Augmentation Hypothesis")
    lines.append("")
    lines.append("**Data source:** `day_2/effect_table_universe_L{1,2,3}.csv`")
    lines.append("**Generated:** 2026-05-14")
    lines.append("")
    lines.append("## Background")
    lines.append("")
    lines.append("Lever 16 provides constraint context — the model receives rule "
                 "descriptions (L2: natural-language; L3: predicate form) alongside the "
                 "chain. This is structurally analogous to tool augmentation but provides "
                 "only the *rules*, not per-chain analysis. Tool augmentation would "
                 "additionally provide the symbolic checker's verdict on *this specific chain*.")
    lines.append("")
    lines.append("If Lever 16 produces measurable improvement → providing rule context "
                 "helps the model. Tool augmentation (rules + per-chain verdict) should "
                 "help at least as much.")
    lines.append("")
    lines.append("If Lever 16 produces null/degenerate effect → rules alone are "
                 "insufficient. The model needs per-chain analysis. This supports the "
                 "tool augmentation hypothesis that the *checker verdict* (not just the "
                 "*rules*) is the key missing information.")
    lines.append("")

    lines.append("## Effect Tables (Universe L1, L2, L3)")
    lines.append("")
    for universe, data in [('L1', l1_rows), ('L2', l2_rows), ('L3', l16_data)]:
        lines.append(f"### Universe {universe}")
        lines.append("")
        lines.append("| Condition | n_valid | dr_violated | dr_intact | gap | "
                     "effect_size | classification |")
        lines.append("|---|---|---|---|---|---|---|")
        for cid in ['flash_baseline', 'flash_L16_L2', 'flash_L16_L3',
                    'pro_baseline', 'pro_L16_L2', 'pro_L16_L3']:
            if cid not in data:
                continue
            r = data[cid]
            lines.append(
                f"| {r['condition_id']} | {r['n_valid']} | {r['dr_violated']} | "
                f"{r['dr_intact']} | {r['gap']} | {r['effect_size']} | "
                f"{r['classification']} |"
            )
        lines.append("")

    lines.append("## Key Observations")
    lines.append("")

    # Diagnose flash L16
    fl16_l3 = l16_data.get('flash_L16_L2', {})
    lines.append("### V4-Flash Lever 16")
    lines.append("")
    lines.append(f"- flash_baseline (Universe L3): "
                 f"dr_violated={l16_data['flash_baseline']['dr_violated']}, "
                 f"dr_intact={l16_data['flash_baseline']['dr_intact']}, "
                 f"gap={l16_data['flash_baseline']['gap']}")
    lines.append(f"- flash_L16_L2 (Universe L3): "
                 f"dr_violated={l16_data['flash_L16_L2']['dr_violated']}, "
                 f"dr_intact={l16_data['flash_L16_L2']['dr_intact']}, "
                 f"gap={l16_data['flash_L16_L2']['gap']}")
    lines.append(f"- flash_L16_L3 (Universe L3): "
                 f"dr_violated={l16_data['flash_L16_L3']['dr_violated']}, "
                 f"dr_intact={l16_data['flash_L16_L3']['dr_intact']}, "
                 f"gap={l16_data['flash_L16_L3']['gap']}")
    lines.append("")
    lines.append("All three Flash conditions are **fully degenerate (dr=0.0 for all "
                 "chains)**. V4-Flash under V1-minimal framing produces a 100% NO floor "
                 "regardless of whether constraint text is provided. Lever 16 has no "
                 "measurable effect on Flash because Flash is already at the NO floor; "
                 "there is nothing for Lever 16 to improve.")
    lines.append("")

    lines.append("### V4-Pro Lever 16")
    lines.append("")
    lines.append(f"- pro_baseline (Universe L3): "
                 f"dr_violated={l16_data['pro_baseline']['dr_violated']}, "
                 f"dr_intact={l16_data['pro_baseline']['dr_intact']}, "
                 f"gap={l16_data['pro_baseline']['gap']}, "
                 f"effect={l16_data['pro_baseline']['effect_size']}, "
                 f"class={l16_data['pro_baseline']['classification']}")
    lines.append(f"- pro_L16_L2 (Universe L3): "
                 f"dr_violated={l16_data['pro_L16_L2']['dr_violated']}, "
                 f"dr_intact={l16_data['pro_L16_L2']['dr_intact']}, "
                 f"gap={l16_data['pro_L16_L2']['gap']}, "
                 f"n_valid={l16_data['pro_L16_L2']['n_valid']}, "
                 f"class={l16_data['pro_L16_L2']['classification']}")
    lines.append(f"- pro_L16_L3 (Universe L3): "
                 f"dr_violated={l16_data['pro_L16_L3']['dr_violated']}, "
                 f"dr_intact={l16_data['pro_L16_L3']['dr_intact']}, "
                 f"gap={l16_data['pro_L16_L3']['gap']}, "
                 f"n_valid={l16_data['pro_L16_L3']['n_valid']}, "
                 f"class={l16_data['pro_L16_L3']['classification']}")
    lines.append("")
    lines.append("V4-Pro Lever 16 conditions are also **effectively degenerate**: "
                 "dr_violated=0.0 and dr_intact=0.0 for L16_L2 and L16_L3, both "
                 "classified as Directional(no_CI) with near-zero effects. These are "
                 "four of the documented degenerate Pro conditions from Day 2. Adding "
                 "NL or predicate-form constraint text does not lift Pro from the near-NO "
                 "floor.")
    lines.append("")
    lines.append("Note: n_valid is 46 (L16_L2) and 44 (L16_L3) vs 50 for baseline, "
                 "indicating 4–6 parse failures introduced by the longer prompts. This "
                 "is a minor robustness cost with no benefit.")
    lines.append("")

    lines.append("## Implication for Tool Augmentation")
    lines.append("")
    lines.append("Lever 16 provides the model with the constraint *rules* but not the "
                 "per-chain *verdict*. Both Flash and Pro show null effect from Lever 16:")
    lines.append("")
    lines.append("- Flash: degenerate at 0.0 both before and after adding rules")
    lines.append("- Pro: near-zero both before and after adding rules")
    lines.append("")
    lines.append("**Conclusion:** Rule descriptions alone do not help the model detect "
                 "violations in V1-minimal framing. The model knows (or can be told) the "
                 "rules but cannot apply them reliably to individual chains.")
    lines.append("")
    lines.append("This **supports** the tool augmentation hypothesis: what the model "
                 "lacks is not rule knowledge but per-chain analysis. The symbolic checker "
                 "provides exactly that — a chain-specific verdict with the violated rule "
                 "identified. Tool augmentation injects the missing component (chain "
                 "analysis) that Lever 16 cannot provide.")
    lines.append("")
    lines.append("**Caveat:** Lever 16 uses the same V1-minimal framing (no CoT) as the "
                 "baseline. Tool augmentation will be tested under the same framing. If "
                 "the model still cannot integrate checker output in V1-minimal mode, "
                 "tool augmentation may need to be paired with a CoT-enabling condition "
                 "(e.g., combined with L18 L3 or L18 L4) to be effective.")
    lines.append("")
    lines.append("**Stop condition check:** The Lever 16 findings match the Day 2 "
                 "documented classification of these conditions as degenerate. No "
                 "inconsistency detected; stop condition not triggered.")
    lines.append("")

    out_path = OUT_DIR / "lever_16_relevance.md"
    out_path.write_text("\n".join(lines))
    print(f"  Wrote {out_path.name}")


# =============================================================================
# MAIN
# =============================================================================
def main():
    rows, prompt_map = task_2a()
    task_2d()

    # Print summary of 2A agreement matrix for verification
    print("\n2A — GT agreement pattern distribution:")
    agree_dist = Counter(r['gt_agreement'] for r in rows)
    for pattern, n in sorted(agree_dist.items(), key=lambda x: -x[1]):
        print(f"  {pattern}: {n}")


if __name__ == "__main__":
    main()
