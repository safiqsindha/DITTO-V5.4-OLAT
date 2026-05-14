#!/usr/bin/env python3
"""
Diagnostics 1 and 4 — Amendment #7 parser sanity check + qualitative reasoning review.

Diagnostic 1 (parser sanity check):
  Spot-check 10 random parseable records from Amendment #7 retest.
  For each: dump raw_output (content field), parse_stage, parsed_label, ground_truth.
  Flag any record where content field does NOT contain the extracted verdict
  (parser-induced YES from content that says NO or is empty).

Diagnostic 4 (qualitative reasoning review):
  For all 73 parseable Amendment #7 records, examine reasoning_content and
  categorise into three buckets:
    A. Reasoning concludes violation found  → YES verdict aligns
    B. Reasoning concludes no violation     → YES verdict contradicts (danger zone)
    C. Reasoning ambiguous/incomplete       → unclear what model decided

No API calls. Read-only.
"""
import json
import random
import re
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROV_PATH = ROOT / "amendment_7" / "provenance.ndjson"

# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
records = []
with open(PROV_PATH) as f:
    for line in f:
        line = line.strip()
        if line:
            records.append(json.loads(line))

parseable = [r for r in records
             if r.get('parse_success') and not r.get('api_failure')]
unparseable = [r for r in records if not r.get('parse_success')]
api_fail = [r for r in records if r.get('api_failure')]

print(f"Total records in provenance.ndjson : {len(records)}")
print(f"  parseable (parse_success=True)   : {len(parseable)}")
print(f"  unparseable                      : {len(unparseable)}")
print(f"  api_failure                      : {len(api_fail)}")
print()

# ---------------------------------------------------------------------------
# Helper: does the raw content field itself contain the verdict?
# ---------------------------------------------------------------------------
_RE_STRICT     = re.compile(r'(?:Therefore,\s+)?[Tt]he answer is\s+(YES|NO)\b')
_RE_PERMISSIVE = re.compile(r'(?i)(?:answer is|answer:|conclusion:)\s*(yes|no)\b')
_RE_MD_STRIP   = re.compile(r'[*_`]+')
_RE_LAST_TOKEN = re.compile(r'(YES|NO)\b[\s.,!?)\]]*$', re.IGNORECASE)


def parse_content(content):
    """Replicate executor cascade; return (label, stage)."""
    if not content:
        return None, 'unparseable'
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


def content_agrees_with_verdict(raw_output, verdict):
    """
    Return True if we can find the verdict in the content through any parser stage.
    Return False if parsed_label is YES but content contains an explicit NO conclusion
    before the YES (sign of parser over-reach).
    """
    label, _ = parse_content(raw_output or '')
    return label == verdict


# ---------------------------------------------------------------------------
# DIAGNOSTIC 1 — 10 random parseable records
# ---------------------------------------------------------------------------
SEED = 42
rng = random.Random(SEED)
sample = rng.sample(parseable, min(10, len(parseable)))

print("=" * 72)
print("DIAGNOSTIC 1 — Parser Sanity Check (10 random parseable records)")
print("=" * 72)
print()

parser_induced_flags = []

for idx, rec in enumerate(sample, 1):
    raw = rec.get('raw_output') or ''
    stage = rec.get('parse_stage_reached', '?')
    label = rec.get('parsed_label', '?')
    gt = rec.get('ground_truth', {})
    cond = rec.get('condition_id', '?')
    chain = rec.get('sample_id', '?')
    model = rec.get('model', '?')
    finish = rec.get('finish_reason', '?')

    # Re-derive from raw_output independently to cross-check
    rederived_label, rederived_stage = parse_content(raw)

    # Flag if content does NOT produce the stored label
    mismatch = (rederived_label != label)
    # Also flag if content is empty/None but label is YES
    empty_content_yes = (not raw.strip()) and (label == 'YES')
    # Flag if content contains explicit NO but label is YES
    contains_explicit_no = bool(re.search(r'\bNO\b', raw, re.IGNORECASE)) and label == 'YES'
    # For last_token: show the tail that was searched
    tail_snippet = (raw[-200:] if len(raw) > 200 else raw) if stage == 'last_token' else None

    flag = mismatch or empty_content_yes

    print(f"[{idx}] {cond} | {chain[:45]}")
    print(f"     model        : {model}")
    print(f"     finish_reason: {finish}")
    print(f"     parse_stage  : {stage}")
    print(f"     stored_label : {label}")
    print(f"     rederived    : {rederived_label} (stage={rederived_stage})")
    print(f"     ground_truth : L1={gt.get('L1_shuffled_vs_real')} "
          f"L2={gt.get('L2_planted_violations')} "
          f"L3={gt.get('L3_symbolic_checker')}")
    print(f"     raw_output   : {repr(raw[:300])}")
    if tail_snippet and tail_snippet != raw:
        print(f"     last_200_tail: {repr(tail_snippet)}")
    if flag:
        print(f"     *** FLAG: label/content mismatch or empty-content YES ***")
        parser_induced_flags.append((idx, rec, 'label_mismatch' if mismatch else 'empty_content_yes'))
    if contains_explicit_no and label == 'YES':
        print(f"     *** NOTE: content contains 'NO' but label=YES — inspect manually ***")
    print()

if parser_induced_flags:
    print(">>> DIAGNOSTIC 1 RESULT: PARSER-INDUCED FLAGS FOUND — SEE ABOVE <<<")
    print(f"    {len(parser_induced_flags)} flagged record(s).")
else:
    print(">>> DIAGNOSTIC 1 RESULT: No parser-induced flags in 10-record sample. <<<")
    print("    All stored labels re-derive cleanly from raw_output via cascade.")
print()

# Stage distribution across all parseable records
from collections import Counter
stage_dist = Counter(r.get('parse_stage_reached') for r in parseable)
print("Stage distribution (all parseable):")
for stage, n in sorted(stage_dist.items(), key=lambda x: -x[1]):
    print(f"  {stage:15s}: {n}")
print()

# ---------------------------------------------------------------------------
# DIAGNOSTIC 4 — Qualitative reasoning review, all 73 parseable records
# ---------------------------------------------------------------------------
print("=" * 72)
print("DIAGNOSTIC 4 — Qualitative Reasoning Review (all parseable records)")
print("=" * 72)
print()

# Reasoning conclusion heuristics
_YES_SIGNALS = [
    re.compile(r'(?i)(?:answer is|therefore|conclusion[:\s]+|thus[,\s]+|so[,\s]+|hence[,\s]+)'
               r'[\s,]*(?:the\s+)?(?:answer\s+is\s+)?YES\b'),
    re.compile(r'(?i)\bthere(?:fore)?\s+(?:is|are)\s+(?:a\s+)?(?:rule\s+)?violation'),
    re.compile(r'(?i)\bconfirm(?:s|ed|ing)?\s+(?:a\s+)?(?:rule\s+)?violation'),
    re.compile(r'(?i)\bfinal\s+answer\s*[:\-–]\s*YES\b'),
    re.compile(r'(?i)\banswer\s*[:\-–]\s*YES\b'),
    re.compile(r'(?i)YES,?\s+there\s+(?:is|are)\s+(?:a\s+)?(?:rule\s+)?violation'),
    re.compile(r'(?i)\bthus,?\s+(?:the\s+)?answer\s+is\s+YES\b'),
]

_NO_SIGNALS = [
    re.compile(r'(?i)(?:answer is|therefore|conclusion[:\s]+|thus[,\s]+|so[,\s]+|hence[,\s]+)'
               r'[\s,]*(?:the\s+)?(?:answer\s+is\s+)?NO\b'),
    re.compile(r'(?i)\bno\s+(?:rule\s+)?violation(?:s)?\s+(?:found|detected|present|exist)'),
    re.compile(r'(?i)\bfinal\s+answer\s*[:\-–]\s*NO\b'),
    re.compile(r'(?i)\banswer\s*[:\-–]\s*NO\b'),
    re.compile(r'(?i)\bthere(?:fore)?\s+(?:are|is)\s+no\s+(?:rule\s+)?violation'),
    re.compile(r'(?i)NO,?\s+there\s+(?:are|is)\s+no\s+(?:rule\s+)?violation'),
]


def classify_reasoning(reasoning_content):
    """
    Returns (bucket, evidence) where bucket is 'YES_aligns', 'NO_contradicts', 'ambiguous'.
    evidence is a short snippet of the matching signal.
    """
    if not reasoning_content or not reasoning_content.strip():
        return 'ambiguous', '[empty reasoning]'

    text = reasoning_content

    # Check final 800 chars first (conclusion is usually at the end)
    tail = text[-800:]

    yes_hits = []
    no_hits = []

    for pat in _YES_SIGNALS:
        m = pat.search(tail)
        if m:
            yes_hits.append(m.group(0)[:80])
    for pat in _NO_SIGNALS:
        m = pat.search(tail)
        if m:
            no_hits.append(m.group(0)[:80])

    # If no signal in tail, check full text
    if not yes_hits and not no_hits:
        for pat in _YES_SIGNALS:
            m = pat.search(text)
            if m:
                yes_hits.append(m.group(0)[:80])
        for pat in _NO_SIGNALS:
            m = pat.search(text)
            if m:
                no_hits.append(m.group(0)[:80])

    # Also look for bare final YES/NO at end of reasoning.
    # Exclude "YES or NO" / "YES or no" patterns — those are format instructions,
    # not answer conclusions.
    bare = re.search(r'(YES|NO)[\s.,]*$', tail.strip(), re.IGNORECASE)
    if bare:
        # Context window of 20 chars before the match
        ctx_before = tail.strip()[max(0, bare.start()-20):bare.start()]
        is_format_instruction = bool(re.search(r'(?i)yes\s+or\s*$', ctx_before))
        if not is_format_instruction:
            val = bare.group(1).upper()
            if val == 'YES':
                yes_hits.append(f'[bare final: {bare.group(0)[:30]}]')
            else:
                no_hits.append(f'[bare final: {bare.group(0)[:30]}]')

    # Add bare-final to positional hits so it participates in the tie-break
    bare_pos = None
    bare_m = re.search(r'(YES|NO)[\s.,]*$', tail.strip(), re.IGNORECASE)
    if bare_m:
        bare_pos = bare_m.start()

    if yes_hits and not no_hits:
        return 'YES_aligns', yes_hits[0]
    if no_hits and not yes_hits:
        # If the bare final is YES, YES wins regardless of mid-sentence NO
        if bare_m and bare_m.group(1).upper() == 'YES':
            return 'YES_aligns', f'[bare-final overrides mid-sentence NO] {bare_m.group(0)[:30]}'
        return 'NO_contradicts', no_hits[0]
    if yes_hits and no_hits:
        # Both found — check which appears later (include bare_final position)
        yes_positions = [m.start() for p in _YES_SIGNALS
                         for m in [p.search(tail)] if m]
        if bare_m and bare_m.group(1).upper() == 'YES':
            yes_positions.append(bare_pos)
        no_positions = [m.start() for p in _NO_SIGNALS
                        for m in [p.search(tail)] if m]
        if bare_m and bare_m.group(1).upper() == 'NO':
            no_positions.append(bare_pos)
        last_yes = max(yes_positions, default=-1)
        last_no = max(no_positions, default=-1)
        if last_yes > last_no:
            return 'YES_aligns', f'[both signals; YES later] {yes_hits[0]}'
        elif last_no > last_yes:
            return 'NO_contradicts', f'[both signals; NO later] {no_hits[0]}'
        else:
            return 'ambiguous', f'[conflicting: YES={yes_hits[0]} / NO={no_hits[0]}]'
    # Only bare final, no named-pattern hits
    if bare_m:
        if bare_m.group(1).upper() == 'YES':
            return 'YES_aligns', f'[bare final only] {bare_m.group(0)[:30]}'
        else:
            return 'NO_contradicts', f'[bare final only] {bare_m.group(0)[:30]}'
    return 'ambiguous', '[no conclusive signal found]'


buckets = {'YES_aligns': [], 'NO_contradicts': [], 'ambiguous': []}

for rec in parseable:
    reasoning = rec.get('reasoning_content') or ''
    bucket, evidence = classify_reasoning(reasoning)
    buckets[bucket].append((rec, evidence))

print(f"Category distribution across {len(parseable)} parseable records:")
print(f"  A. Reasoning concludes violation (YES aligns)  : {len(buckets['YES_aligns'])}")
print(f"  B. Reasoning concludes no violation (contradicts): {len(buckets['NO_contradicts'])}")
print(f"  C. Ambiguous/incomplete reasoning               : {len(buckets['ambiguous'])}")
print()

# --- Bucket B detail (the dangerous ones) ---
if buckets['NO_contradicts']:
    print("=" * 72)
    print(f"BUCKET B — Reasoning says NO but verdict=YES ({len(buckets['NO_contradicts'])} records)")
    print("(These are the parser/model integrity concern)")
    print("=" * 72)
    for rec, evidence in buckets['NO_contradicts']:
        gt = rec.get('ground_truth', {})
        reasoning = rec.get('reasoning_content') or ''
        tail = reasoning[-600:]
        print(f"\n  Chain    : {rec['sample_id']}")
        print(f"  Model    : {rec['model']}")
        print(f"  GT L3    : {gt.get('L3_symbolic_checker')}")
        print(f"  Verdict  : {rec.get('parsed_label')} (stage={rec.get('parse_stage_reached')})")
        print(f"  Evidence : {evidence}")
        print(f"  Reasoning tail (last 600 chars):")
        for line in textwrap.wrap(tail, width=68, initial_indent='    ', subsequent_indent='    '):
            print(line)
    print()
else:
    print(">>> DIAGNOSTIC 4: No Bucket B records found (no reasoning→NO contradictions). <<<")
    print()

# --- Bucket C detail (ambiguous) ---
if buckets['ambiguous']:
    print("=" * 72)
    print(f"BUCKET C — Ambiguous reasoning ({len(buckets['ambiguous'])} records)")
    print("=" * 72)
    for rec, evidence in buckets['ambiguous']:
        gt = rec.get('ground_truth', {})
        reasoning = rec.get('reasoning_content') or ''
        tail = reasoning[-400:]
        print(f"\n  Chain    : {rec['sample_id']}")
        print(f"  Model    : {rec['model']}")
        print(f"  GT L3    : {gt.get('L3_symbolic_checker')}")
        print(f"  Verdict  : {rec.get('parsed_label')} (stage={rec.get('parse_stage_reached')})")
        print(f"  Note     : {evidence}")
        print(f"  Reasoning tail (last 400 chars):")
        for line in textwrap.wrap(tail, width=68, initial_indent='    ', subsequent_indent='    '):
            print(line)
    print()

# --- Bucket A summary (aligning YES) ---
print("=" * 72)
print(f"BUCKET A — Reasoning aligns with YES verdict ({len(buckets['YES_aligns'])} records)")
print("(Showing first evidence snippet per record)")
print("=" * 72)
for rec, evidence in buckets['YES_aligns'][:10]:
    gt = rec.get('ground_truth', {})
    print(f"  {rec['sample_id'][:45]:45s} GT_L3={gt.get('L3_symbolic_checker')}  ev={evidence[:60]}")
if len(buckets['YES_aligns']) > 10:
    print(f"  ... and {len(buckets['YES_aligns']) - 10} more (all YES_aligns)")
print()

# --- Cross-tab: GT_L3 vs bucket ---
print("=" * 72)
print("Cross-tab: Ground Truth L3 × Reasoning Bucket")
print("=" * 72)
cross = Counter()
for bucket, recs in buckets.items():
    for rec, _ in recs:
        gt_l3 = rec.get('ground_truth', {}).get('L3_symbolic_checker')
        cross[(gt_l3, bucket)] += 1

print(f"{'GT_L3':8s}  {'A(YES_aligns)':15s}  {'B(NO_contrad)':15s}  {'C(ambiguous)':12s}")
for gt_val in [True, False]:
    a = cross.get((gt_val, 'YES_aligns'), 0)
    b = cross.get((gt_val, 'NO_contradicts'), 0)
    c = cross.get((gt_val, 'ambiguous'), 0)
    print(f"{str(gt_val):8s}  {a:15d}  {b:15d}  {c:12d}")
print()

print("Done.")
