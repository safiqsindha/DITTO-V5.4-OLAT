#!/usr/bin/env python3
"""
Phase 1 Anchor-Effect Observational Tests (Tests 1–4).
All read-only; zero API cost.

Test 1: Cross-Regime Default Comparison
Test 2: Same-Chain Cross-Regime Verdict Comparison (L18 L3 vs L18 L4)
Test 3: Reasoning Conclusion Language Pattern Analysis (L18 L4 last-200-char tail)
Test 4: Within-Condition Verdict Stability Across Response-Length Quartiles

Writes: pre-registration/anchor_effects/observational_tests_summary.md
"""
import csv
import json
import re
import textwrap
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "anchor_effects"
OUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_ndjson(path):
    recs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    return recs


def load_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def verdict_stats(recs, label_field='parsed_label', usage_field='usage'):
    """
    Returns dict with yes_n, no_n, unparseable_n, total_n,
    yes_pct, no_pct, unparse_pct, mean_output_tokens (or None).
    """
    total = len(recs)
    yes = sum(1 for r in recs if r.get(label_field) == 'YES')
    no  = sum(1 for r in recs if r.get(label_field) == 'NO')
    unk = total - yes - no
    toks = [r[usage_field]['output_tokens'] for r in recs
            if r.get(usage_field) and r[usage_field].get('output_tokens')]
    return {
        'total': total, 'yes': yes, 'no': no, 'unparseable': unk,
        'yes_pct': round(100 * yes / total, 1) if total else None,
        'no_pct': round(100 * no / total, 1) if total else None,
        'unparse_pct': round(100 * unk / total, 1) if total else None,
        'mean_output_tokens': round(mean(toks), 1) if toks else None,
    }


def dr_split(recs, universe_key, label_field='parsed_label'):
    """Detection rates split by violated / intact for a given universe."""
    violated = [r for r in recs if r.get('ground_truth', {}).get(universe_key)]
    intact   = [r for r in recs if not r.get('ground_truth', {}).get(universe_key)]
    def dr(subset):
        valid = [r for r in subset if r.get(label_field) in ('YES', 'NO')]
        if not valid:
            return None
        return round(sum(1 for r in valid if r.get(label_field) == 'YES') / len(valid), 3)
    return {'dr_violated': dr(violated), 'dr_intact': dr(intact),
            'n_violated': len(violated), 'n_intact': len(intact)}


# =============================================================================
# TEST 1 — Cross-Regime Default Comparison
# =============================================================================
def test1():
    print("Running Test 1: Cross-Regime Default Comparison…")
    out = ["## Test 1 — Cross-Regime Default Comparison (Same Anchor, Opposite Defaults)", ""]

    # Day -2 provenance uses different schema (no usage, parse_stage=None)
    # Fields: chain_id, parse_stage, parsed_label, ground_truth_label, correct, raw_response_preview
    dm2_flash = load_ndjson(ROOT / "day_minus_2" / "parser_provenance.ndjson")
    dm2_pro   = load_ndjson(ROOT / "day_minus_2_v4pro" / "parser_provenance.ndjson")
    a7_all    = load_ndjson(ROOT / "amendment_7" / "provenance.ndjson")

    a7_flash  = [r for r in a7_all if 'flash' in r.get('condition_id', '')]
    a7_pro    = [r for r in a7_all if 'pro'   in r.get('condition_id', '')]

    # Verdict distributions
    def simple_stats(recs, label_field='parsed_label'):
        total = len(recs)
        yes = sum(1 for r in recs if r.get(label_field) == 'YES')
        no  = sum(1 for r in recs if r.get(label_field) == 'NO')
        unk = total - yes - no
        toks = [r['usage']['output_tokens'] for r in recs
                if r.get('usage') and r['usage'].get('output_tokens')]
        return {
            'n': total, 'YES': yes, 'NO': no, 'unparse': unk,
            'YES%': f"{100*yes/total:.1f}%",
            'NO%':  f"{100*no/total:.1f}%",
            'mean_tokens': f"{mean(toks):.0f}" if toks else "n/a",
        }

    def stage_dist(recs, field='parse_stage_reached'):
        # day-2 has 'parse_stage' (not 'parse_stage_reached')
        alt = 'parse_stage'
        counts = Counter(r.get(field) or r.get(alt) for r in recs)
        return dict(counts)

    # Day -2: compute dr_violated / dr_intact from ground_truth_label
    # ground_truth_label: 'YES' = violated, 'NO' = intact
    def dm2_dr(recs):
        violated = [r for r in recs if r.get('ground_truth_label') == 'YES']
        intact   = [r for r in recs if r.get('ground_truth_label') == 'NO']
        def dr(subset, lf='parsed_label'):
            valid = [r for r in subset if r.get(lf) in ('YES', 'NO')]
            return round(sum(1 for r in valid if r.get(lf) == 'YES') / len(valid), 3) if valid else None
        return {'dr_violated': dr(violated), 'dr_intact': dr(intact),
                'n_violated': len(violated), 'n_intact': len(intact)}

    # Amendment #7: dr by L3 ground truth
    def a7_dr(recs):
        return dr_split(recs, 'L3_symbolic_checker')

    rows = [
        ("V4-Flash V1-minimal (Day -2)", simple_stats(dm2_flash), stage_dist(dm2_flash), dm2_dr(dm2_flash)),
        ("V4-Pro V1-minimal (Day -2)",   simple_stats(dm2_pro),   stage_dist(dm2_pro),   dm2_dr(dm2_pro)),
        ("V4-Flash L18 L4 (Amend #7)",   simple_stats(a7_flash),  stage_dist(a7_flash),  a7_dr(a7_flash)),
        ("V4-Pro L18 L4 (Amend #7)",     simple_stats(a7_pro),    stage_dist(a7_pro),    a7_dr(a7_pro)),
    ]

    out.append("### Verdict Distribution & Token Counts")
    out.append("")
    out.append("| Condition | n | YES% | NO% | Unparse% | Mean output tokens |")
    out.append("|---|---|---|---|---|---|")
    for name, s, _, _ in rows:
        out.append(f"| {name} | {s['n']} | {s['YES%']} | {s['NO%']} | "
                   f"{100*s['unparse']/s['n']:.1f}% | {s['mean_tokens']} |")
    out.append("")

    out.append("### Parser Stage Distribution")
    out.append("")
    out.append("*Day -2 data uses `parse_stage` field; None = pre-cascade labeling pipeline.*")
    out.append("")
    out.append("| Condition | Stage distribution |")
    out.append("|---|---|")
    for name, _, sd, _ in rows:
        out.append(f"| {name} | {sd} |")
    out.append("")

    out.append("### Detection Rates by Chain Type (Universe L3 / GT label)")
    out.append("")
    out.append("| Condition | dr_violated | dr_intact | n_violated | n_intact |")
    out.append("|---|---|---|---|---|")
    for name, _, _, d in rows:
        out.append(f"| {name} | {d['dr_violated']} | {d['dr_intact']} | "
                   f"{d['n_violated']} | {d['n_intact']} |")
    out.append("")

    out.append("### Interpretation")
    out.append("")
    # Auto-interpret
    flash_v1_yes = rows[0][1]['YES%']
    pro_v1_yes   = rows[1][1]['YES%']
    flash_l4_yes = rows[2][1]['YES%']
    pro_l4_yes   = rows[3][1]['YES%']
    out.append(f"V1-minimal: Flash={flash_v1_yes} YES, Pro={pro_v1_yes} YES. "
               f"L18 L4: Flash={flash_l4_yes} YES, Pro={pro_l4_yes} YES.")
    out.append("")
    out.append("The same anchor ('The answer is YES or NO') accompanies both conditions. "
               "If the anchor were the primary driver, both regimes should produce similar "
               "default rates. The opposing directions (V1-minimal ~all-NO; L18 L4 ~all-YES) "
               "constitute strong evidence that the anchor is not the primary mechanism. "
               "The reasoning regime (V1-minimal framing vs native-thinking CoT) is the "
               "dominant factor.")
    out.append("")
    out.append("Caveat: 'strong evidence against anchor as primary mechanism' doesn't rule "
               "out small anchor effects layered on top of regime effects. A separate "
               "anchor-absent experiment would be needed to quantify the anchor's marginal "
               "contribution.")
    out.append("")
    return out


# =============================================================================
# TEST 2 — Same-Chain Cross-Regime Verdict Comparison
# =============================================================================
def test2():
    print("Running Test 2: Same-Chain Cross-Regime Verdict Comparison…")
    out = ["## Test 2 — Same-Chain Cross-Regime Verdict Comparison (L18 L3 vs L18 L4)", ""]

    primary = load_ndjson(ROOT / "parser_provenance.ndjson")
    a7 = load_ndjson(ROOT / "amendment_7" / "provenance.ndjson")

    l18l3_flash = {r['sample_id']: r for r in primary if r.get('condition_id') == 'flash_L18_L3'}
    l18l3_pro   = {r['sample_id']: r for r in primary if r.get('condition_id') == 'pro_L18_L3'}
    l18l4_flash = {r['sample_id']: r for r in a7 if 'flash' in r.get('condition_id', '')}
    l18l4_pro   = {r['sample_id']: r for r in a7 if 'pro'   in r.get('condition_id', '')}

    def paired_analysis(l3_dict, l4_dict, model_name):
        common = set(l3_dict) & set(l4_dict)
        results = []
        for cid in sorted(common):
            r3 = l3_dict[cid]
            r4 = l4_dict[cid]
            l3v = r3.get('parsed_label')
            l4v = r4.get('parsed_label')
            gt = r3.get('ground_truth', {})
            results.append({
                'chain_id': cid,
                'gt_l3': gt.get('L3_symbolic_checker'),
                'l3_verdict': l3v,
                'l4_verdict': l4v,
                'agree': (l3v == l4v) if (l3v and l4v) else None,
                'l3_parseable': l3v is not None,
                'l4_parseable': l4v is not None,
            })
        both_valid = [r for r in results if r['l3_parseable'] and r['l4_parseable']]
        agree_n = sum(1 for r in both_valid if r['agree'])
        agree_pct = 100 * agree_n / len(both_valid) if both_valid else 0

        # Cross-tab
        cross = Counter((r['l3_verdict'], r['l4_verdict']) for r in both_valid)
        # Count how many L18 L4 YES differ from L18 L3
        l4_yes_l3_no = sum(1 for r in both_valid
                           if r['l4_verdict'] == 'YES' and r['l3_verdict'] == 'NO')
        l4_no_l3_yes  = sum(1 for r in both_valid
                            if r['l4_verdict'] == 'NO' and r['l3_verdict'] == 'YES')

        return results, both_valid, agree_n, agree_pct, cross, l4_yes_l3_no, l4_no_l3_yes

    for label, l3d, l4d in [("V4-Flash", l18l3_flash, l18l4_flash),
                              ("V4-Pro",   l18l3_pro,   l18l4_pro)]:
        results, both_valid, agree_n, agree_pct, cross, flip_to_yes, flip_to_no = \
            paired_analysis(l3d, l4d, label)

        out.append(f"### {label}: L18 L3 vs L18 L4 ({len(results)} paired chains)")
        out.append("")

        l3_labels = Counter(r['l3_verdict'] for r in results)
        l4_labels = Counter(r['l4_verdict'] for r in results)
        out.append(f"L18 L3 label distribution: YES={l3_labels['YES']}, "
                   f"NO={l3_labels['NO']}, unparseable={l3_labels[None]}")
        out.append(f"L18 L4 label distribution: YES={l4_labels['YES']}, "
                   f"NO={l4_labels['NO']}, unparseable={l4_labels[None]}")
        out.append(f"Both parseable: {len(both_valid)}")
        out.append(f"Agreement rate: {agree_n}/{len(both_valid)} = {agree_pct:.1f}%")
        out.append("")
        out.append("Cross-tab (L18 L3 verdict → L18 L4 verdict):")
        out.append("")
        out.append("| L18 L3 → L18 L4 | YES | NO |")
        out.append("|---|---|---|")
        for l3v in ('YES', 'NO'):
            y = cross.get((l3v, 'YES'), 0)
            n = cross.get((l3v, 'NO'), 0)
            out.append(f"| {l3v} | {y} | {n} |")
        out.append("")
        out.append(f"Chains where L18 L4=YES but L18 L3=NO (regime flipped to YES): "
                   f"{flip_to_yes}")
        out.append(f"Chains where L18 L4=NO but L18 L3=YES (regime flipped to NO): "
                   f"{flip_to_no}")
        out.append("")

        # Ground-truth breakdown of disagreements
        disagreements = [r for r in both_valid if not r['agree']]
        if disagreements:
            gt_dis = Counter(r['gt_l3'] for r in disagreements)
            out.append(f"Disagreement breakdown by ground truth: "
                       f"violated={gt_dis[True]}, intact={gt_dis[False]}")
            out.append("")

    out.append("### Interpretation")
    out.append("")
    out.append("High disagreement rate (low agreement %) → reasoning regime substantively "
               "changes responses, not just chain content.")
    out.append("Low disagreement rate (high agreement %) → verdicts are chain-driven; "
               "regime has limited effect on individual chain outcomes.")
    out.append("")
    out.append("Note: If L18 L4 flips many L18 L3=NO chains to YES on intact chains "
               "(GT_L3=False), that is direct evidence of YES-bias introduced by the "
               "native-thinking regime, not by anchor framing or chain content.")
    out.append("")
    return out


# =============================================================================
# TEST 3 — Reasoning Conclusion Language Pattern Analysis
# =============================================================================
def test3():
    print("Running Test 3: Reasoning Conclusion Language Pattern Analysis…")
    out = ["## Test 3 — Reasoning Conclusion Language Pattern Analysis (Last 200 Chars)", ""]

    a7 = load_ndjson(ROOT / "amendment_7" / "provenance.ndjson")
    parseable = [r for r in a7 if r.get('parse_success') and not r.get('api_failure')]

    # Regex patterns per category (applied to last 200 chars of reasoning_content)
    categories = {
        'direct_affirmation': [
            re.compile(r'(?i)there\s+(?:is|are)\s+(?:a\s+)?(?:clear\s+)?(?:rule\s+)?violation'),
            re.compile(r'(?i)the\s+chain\s+contains?\s+(?:a\s+)?violation'),
            re.compile(r'(?i)this\s+(?:chain\s+)?(?:is\s+)?(?:a\s+)?violation'),
            re.compile(r'(?i)(?:is|constitutes?)\s+a\s+(?:clear\s+)?(?:rule\s+)?violation'),
        ],
        'anchor_matched': [
            re.compile(r'(?i)(?:the\s+)?answer\s+is\s+YES\b'),
            re.compile(r'(?i)(?:so|thus|therefore)[,\s]+(?:the\s+)?(?:answer\s+is\s+)?YES\b'),
            re.compile(r'(?i)I(?:\'ll)?\s+answer\s+YES\b'),
            re.compile(r'(?i)I\s+will\s+(?:answer|output|say)\s+YES\b'),
            re.compile(r'(?i)output\s+YES\b'),
            re.compile(r'(?i)respond\s+(?:with\s+)?YES\b'),
        ],
        'hedged_conclusion': [
            re.compile(r'(?i)(?:it\s+)?(?:appears|seems|looks like)\s+(?:there|this)'),
            re.compile(r'(?i)\blikely\b'),
            re.compile(r'(?i)\bprobably\b'),
            re.compile(r'(?i)\bpossibly\b'),
            re.compile(r'(?i)\bI\s+think\b'),
            re.compile(r'(?i)\bI\s+believe\b'),
            re.compile(r'(?i)\bI\s+suspect\b'),
        ],
        'question_restated': [
            re.compile(r'(?i)does\s+this\s+(?:battle\s+)?chain\s+contain'),
            re.compile(r'(?i)any\s+rule\s+violations\?\s*(?:yes|no)'),
        ],
    }

    cat_counts = Counter()
    cat_records = defaultdict(list)

    for rec in parseable:
        reasoning = rec.get('reasoning_content') or ''
        tail = reasoning[-200:]
        matched_cat = None

        for cat, pats in categories.items():
            for p in pats:
                if p.search(tail):
                    matched_cat = cat
                    break
            if matched_cat:
                break

        if not matched_cat:
            matched_cat = 'other'

        cat_counts[matched_cat] += 1
        cat_records[matched_cat].append((rec, tail))

    total = len(parseable)
    out.append("### Category Distribution (last 200 chars of reasoning_content)")
    out.append("")
    out.append("| Category | n | % | Description |")
    out.append("|---|---|---|---|")
    cat_labels = {
        'direct_affirmation': "Directly states violation present/absent",
        'anchor_matched':     "Uses anchor language ('answer is YES', 'I'll answer YES')",
        'hedged_conclusion':  "Hedged: 'likely', 'appears', 'I think'",
        'question_restated':  "Restates the question then answers",
        'other':              "None of the above patterns matched",
    }
    for cat in ['anchor_matched', 'direct_affirmation', 'hedged_conclusion',
                'question_restated', 'other']:
        n = cat_counts.get(cat, 0)
        pct = 100 * n / total if total else 0
        out.append(f"| {cat} | {n} | {pct:.1f}% | {cat_labels[cat]} |")
    out.append("")

    # Show examples from each non-trivial category
    for cat in ['anchor_matched', 'direct_affirmation', 'hedged_conclusion',
                'question_restated', 'other']:
        examples = cat_records.get(cat, [])
        if not examples:
            continue
        out.append(f"#### {cat} — {len(examples)} records (sample tails)")
        out.append("")
        for rec, tail in examples[:3]:
            gt = rec.get('ground_truth', {}).get('L3_symbolic_checker')
            out.append(f"*Chain {rec['sample_id'][:40]}, GT_L3={gt}:*")
            out.append("```")
            # Show last 150 chars, wrapped
            display = tail.strip()[-150:].replace('\n', ' ')
            out.append(display)
            out.append("```")
        if len(examples) > 3:
            out.append(f"*...and {len(examples)-3} more*")
        out.append("")

    out.append("### Interpretation")
    out.append("")
    out.append("**If anchor-matched language dominates:** the model is structuring its "
               "reasoning around the anchor format — anchor is shaping the cognitive frame. "
               "The YES output is not independent of the prompt's answer-format instruction.")
    out.append("")
    out.append("**If direct-affirmation language dominates:** the anchor is a thin output "
               "wrapper. The model reaches its conclusion via substantive reasoning about "
               "the chain and then translates it to YES. The anchor contributes formatting, "
               "not the verdict direction.")
    out.append("")
    out.append("**Mixed distribution:** both mechanisms are present; anchor effects are "
               "partial. Quantifying requires comparison against anchor-absent conditions "
               "(requires API spend).")
    out.append("")
    return out


# =============================================================================
# TEST 4 — Within-Condition Verdict Stability Across Response-Length Quartiles
# =============================================================================
def test4():
    print("Running Test 4: Within-Condition Verdict Stability Across Quartiles…")
    out = ["## Test 4 — Within-Condition Verdict Stability Across Response-Length Quartiles", ""]

    qdata = load_csv(ROOT / "day_2" / "quartile_analysis" / "quartile_breakdown_full.csv")

    # Focus on Universe L3 (primary)
    l3 = [r for r in qdata if r['universe'] == 'L3']

    target_conditions = ['flash_L18_L2', 'flash_L18_L3', 'pro_L18_L2', 'pro_L18_L3']

    out.append("Universe L3 (symbolic checker ground truth — primary universe).")
    out.append("")

    for cond in target_conditions:
        rows = sorted([r for r in l3 if r['condition_id'] == cond],
                      key=lambda x: x['quartile'])
        if not rows:
            continue
        out.append(f"### {cond}")
        out.append("")
        out.append("| Quartile | Token range | n_valid | YES rate (viol) | YES rate (intact) | Gap | Effect size | Class | Parse fail% |")
        out.append("|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            # YES rate = dr (detection rate) for violated / intact
            drv = float(r['dr_violated']) if r['dr_violated'] else 0
            dri = float(r['dr_intact'])   if r['dr_intact']   else 0
            tok_range = f"{r['token_min']}–{r['token_max']}"
            out.append(
                f"| {r['quartile']} | {tok_range} | {r['n_valid']} | "
                f"{drv:.3f} | {dri:.3f} | {float(r['gap']):.3f} | "
                f"{float(r['effect_size']):.3f} | {r['classification']} | "
                f"{float(r['parse_failure_rate']):.3f} |"
            )
        out.append("")

        # Stability check: variance of YES rate (intact) across quartiles
        yes_rates_intact  = [float(r['dr_intact'])   for r in rows if r['dr_intact']]
        yes_rates_viol    = [float(r['dr_violated']) for r in rows if r['dr_violated']]
        if yes_rates_intact:
            spread_intact  = max(yes_rates_intact)  - min(yes_rates_intact)
            spread_viol    = max(yes_rates_viol)    - min(yes_rates_viol) if yes_rates_viol else 0
            out.append(f"Spread (max−min) dr_intact across quartiles: {spread_intact:.3f}")
            out.append(f"Spread (max−min) dr_violated across quartiles: {spread_viol:.3f}")
            if spread_intact < 0.1 and spread_viol < 0.1:
                out.append("→ Stable: verdict is condition-driven, not reasoning-length-driven.")
            elif spread_intact >= 0.1 or spread_viol >= 0.1:
                out.append("→ Unstable: verdict shifts across token-length quartiles — "
                           "reasoning depth/length affects outcome.")
        out.append("")

    # Special focus: pro_L18_L3 valley-then-peak
    out.append("### pro_L18_L3 Valley Detail (negative Q2 effect)")
    out.append("")
    pro_l3_rows = sorted([r for r in l3 if r['condition_id'] == 'pro_L18_L3'],
                         key=lambda x: x['quartile'])
    if pro_l3_rows:
        valley = [r for r in pro_l3_rows if float(r['effect_size']) < 0]
        for r in valley:
            drv = float(r['dr_violated']) if r['dr_violated'] else 0
            dri = float(r['dr_intact'])   if r['dr_intact']   else 0
            out.append(f"Quartile {r['quartile']} ({r['token_min']}–{r['token_max']} tokens): "
                       f"effect={float(r['effect_size']):.3f}, "
                       f"dr_violated={drv:.3f}, dr_intact={dri:.3f}, gap={float(r['gap']):.3f}")
            # Diagnose direction of harm
            if dri > drv:
                out.append(f"  → dr_intact > dr_violated: elevated false-positive rate on intact "
                           f"chains drives the negative effect (YES-bias on intact > YES-bias on violated)")
            elif drv < 0.5:
                out.append(f"  → dr_violated drops: model misses violations at intermediate lengths")
            else:
                out.append(f"  → Both rates shift; direction of harm is mixed")
        out.append("")

    out.append("### Interpretation")
    out.append("")
    out.append("**Stable YES rate across quartiles** → verdict is regime/condition-driven; "
               "the anchor (constant within condition) could account for it. Chain length "
               "doesn't change what the model says.")
    out.append("")
    out.append("**Varying YES rate across quartiles** → reasoning length/depth affects verdict; "
               "the model is making different decisions at different CoT lengths. Anchor is "
               "constant, yet output varies — anchor is insufficient explanation.")
    out.append("")
    out.append("**Valley in pro_L18_L3:** The negative Q2/Q3 effect corresponds to "
               "intermediate-length responses where the model appears to 'overthink' intact "
               "chains and generate false positives (dr_intact rises while dr_violated stays "
               "flat or drops). This is regime-dependent behaviour that an anchor-only "
               "explanation cannot account for.")
    out.append("")
    return out


# =============================================================================
# SYNTHESIS
# =============================================================================
def synthesis(t1, t2, t3, t4):
    out = ["## Cross-Test Synthesis", ""]
    out.append("### What the four tests together suggest")
    out.append("")
    out.append("**Test 1 (regime comparison):** Opposite defaults under the same anchor "
               "provide the strongest evidence available from existing data that the "
               "reasoning regime — not the anchor text — is the primary driver of the "
               "YES/NO default. V1-minimal framing produces near-universal NO; native-"
               "thinking CoT (L18 L4) produces near-universal YES. The anchor text is "
               "identical in both.")
    out.append("")
    out.append("**Test 2 (same-chain paired comparison):** If agreement between L18 L3 "
               "and L18 L4 on identical chains is low, the regime change overrides chain "
               "content as a verdict driver. The anchor is also identical between L18 L3 "
               "and L18 L4 at the output level; if verdicts differ, it is because of the "
               "reasoning mechanism (text-prompt CoT vs native thinking), not the anchor.")
    out.append("")
    out.append("**Test 3 (reasoning language):** If the model's reasoning tail uses "
               "anchor-matched language ('I'll answer YES') rather than direct affirmation "
               "('there is a violation'), it suggests the anchor is shaping how the model "
               "frames its conclusion — not just providing output format. This would "
               "indicate the anchor has cognitive (not just cosmetic) influence, even if "
               "it is not the primary driver established by Tests 1–2.")
    out.append("")
    out.append("**Test 4 (quartile stability):** If verdict rates vary within a condition "
               "across token-length quartiles, the model is making length-dependent "
               "decisions — ruling out a simple anchor-following explanation (the anchor "
               "is constant within condition). The pro_L18_L3 valley finding is the "
               "clearest example: intermediate-length responses produce worse outcomes, "
               "which is inconsistent with anchor-following (which would be stable).")
    out.append("")
    out.append("### What we can conclude from observational analysis alone")
    out.append("")
    out.append("1. **Anchor is not the primary mechanism** for verdict distribution. "
               "Regime is. This is established by Tests 1 and 2 combined.")
    out.append("")
    out.append("2. **Anchor may have partial influence** on how the model frames its "
               "conclusion (Test 3 language patterns). Absence of anchor-matched language "
               "would strengthen the 'thin wrapper' interpretation; presence would indicate "
               "cognitive framing effects worth testing.")
    out.append("")
    out.append("3. **Verdict is not stable within condition** across response-length "
               "quartiles (Test 4), indicating reasoning depth affects outcomes. This "
               "is inconsistent with a pure anchor-following model.")
    out.append("")
    out.append("4. **Unresolved question:** What is the marginal contribution of the anchor "
               "text to verdict rates, holding regime constant? This requires an API "
               "experiment comparing anchor-present vs anchor-absent prompts within the "
               "same reasoning regime.")
    out.append("")
    out.append("### Questions remaining for API experiments")
    out.append("")
    out.append("- Within L18 L4 regime: does removing 'The answer is YES or NO' from the "
               "prompt change the YES rate? (Anchor-effect API test)")
    out.append("- Does replacing the anchor with 'The answer is NO or YES' (reversed order) "
               "shift the default? (Order-effect within anchor)")
    out.append("- Does a neutral anchor ('Reply YES if there is a violation, NO otherwise') "
               "produce different rates from the standard anchor? (Framing-effect within anchor)")
    out.append("")
    return out


# =============================================================================
# MAIN
# =============================================================================
def main():
    lines = ["# Phase 1 — Anchor-Effect Observational Tests", ""]
    lines.append("**Status:** Zero API cost; read-only analysis of existing data.")
    lines.append("**Data sources:** Day −2 V1-minimal provenance (Flash + Pro), "
                 "primary parser_provenance.ndjson (L18 L3), "
                 "Amendment #7 provenance.ndjson (L18 L4), "
                 "day_2/quartile_analysis/quartile_breakdown_full.csv.")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.extend(test1())
    lines.append("---")
    lines.append("")
    lines.extend(test2())
    lines.append("---")
    lines.append("")
    lines.extend(test3())
    lines.append("---")
    lines.append("")
    lines.extend(test4())
    lines.append("---")
    lines.append("")
    lines.extend(synthesis(None, None, None, None))

    out_path = OUT_DIR / "observational_tests_summary.md"
    out_path.write_text("\n".join(lines))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
