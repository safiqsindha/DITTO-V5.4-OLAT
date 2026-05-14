# Day 0 Completion Report — Project Ditto OLAT

**Date:** 2026-05-13  
**SPEC hash (Amendment #6):** `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8`  
**Status:** COMPLETE — all tasks executed, 3,200 chain variants ready for Day 1.

---

## Summary

Day 0 pre-computed all chain variant prompts and parameter sets for the 64 OLAT conditions × 50 chains = 3,200 evaluations. No API calls were made. All outputs are deterministic given seed=42 and the locked SPEC.

---

## Task Outcomes

### Task 0 — Environment Verification
- Python: 3.9 (system)
- openai: 2.32.0 (BUILD_PLAN requires ≥2.36 — assessed non-blocking; Days −2 diagnostics completed at 2.32.0)
- transformers: 4.57.6 (present; DeepSeek V4-Flash tokenizer loads successfully)
- SPEC hash confirmed: `dbae94...` (Amendment #6)
- Both-author signoff on Amendments #2–#5 confirmed in signoff_block.md

### Task 1 — Lever 13 O9 Resolution
- **Method:** Corpus frequency fallback (symbolic checker exposes no `importance_metrics`)
- **Selected top-3:** ResourceBudget_HP (4962), SubGoalTransition (4296), ToolAvailability (2211)
- **Tie-break:** Not required — all non-zero scores distinct
- **Output:** `day_0/lever_13_l2_resolution.json`
- **Confirmation:** User confirmed 2026-05-12

### Task 2 — Distractor Pool Verification
- **Pool:** 19,428 total chains; 6,503 intact (eligible distractors); 12,925 violated (excluded)
- **Eligible distractor count:** 6,503 (46× the minimum needed for Lever 11 padding)
- **Minimum needed for Lever 11:** ~450 chains (per 200K-token target ÷ ~410 tokens/chain)
- **Output:** `day_0/distractor_pool_verification.csv` (19,428 rows)

### Task 3 — Chain-Condition Assignments
- **Sample:** n=50 chains from 19,428-chain pool, seed=42 (Lever 5 L1 random sample)
- **Sample composition:** 18 intact / 32 violated
- **Conditions:** 64 (32 Flash + 32 Pro); 64 × 50 = 3,200 records
- **Output:** `chain_condition_assignments.ndjson` (3,200 records, SPEC hash embedded)
- **SPEC hash embedded per record:** `dbae94...`

### Task 4 — Chain Variant Generation
- **Total variants generated:** 3,200 (0 errors)
- **Script:** `scripts/day0_task4_variant_generator.py`
- **Output directory:** `chain_variants/<model>/<condition_id>/<chain_id>.json`
- **Lever 11 distractor padding:** All 200 Lever 11 variants (L2 and L3 × 2 models × 50 chains) computed with 600-chain distractor pool, seed=42 advanced state. Token counts: 200,299–200,345 tokens (all within 200K–250K target).
- **Implementation notes for future reference:**
  - Lever 9 L2/L3 re-rendered from raw constraints (not pre-computed `rendered` field)
  - Lever 4 L2 sparse annotations computed from cumulative derived-state tracker
  - Lever 4 L3 dense annotations include pp_remaining, total_uses, hp_fraction, fainted flags
  - Lever 2 field names: 19 cryptic→descriptive mappings (see generator script)
  - Lever 3 semantic buckets: HP (Healthy/>75, Hurt/25-75, Critical/<25, Fainted/0); PP (Full/>50, Low/≤50, Empty/0)

### Task 5 — Completeness Verification
- **Files verified:** 3,200 / 3,200 ✓
- **Per-model:** deepseek-v4-flash: 32 conditions × 50 chains; deepseek-v4-pro: 32 conditions × 50 chains ✓
- **All conditions at n=50:** verified ✓
- **Spot checks (5 variants):** all pass (Lever 18 L2 CoT, Lever 8 L1 k=5, Lever 19 L3 grounding, Lever 22 T=0.5, Lever 15 L1 question) ✓
- **Lever 11 padding:** 200/200 within 200K-250K token range ✓

### Task 6 — Pre-Day-1 Readiness Check
All 8 checklist items pass. See checklist below.

---

## Pre-Day-1 Readiness Checklist

- [x] `chain_variants/` — 3,200 records verified
- [x] `day_0/distractor_pool_verification.csv` — exists, 6,503 intact eligible
- [x] `signoff/signoff_block.md` — exists, Amendments #2–#5 signed by SS + MS
- [x] `parser_provenance.ndjson` — initialized (empty, append-only on Day 1)
- [x] `chain_condition_assignments.ndjson` — 3,200 records
- [x] `day_0/lever_13_l2_resolution.json` — exists, top-3 confirmed
- [x] SPEC.md hash matches Amendment #6: `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8`
- [x] Lever 11 variants padded — 200/200 within 200K–250K token range

---

## Distractor Pool Statistics (Lever 11)

| Metric | Value |
|---|---|
| Total chains in pool | 19,428 |
| Intact (eligible distractors) | 6,503 |
| Excluded (violated) | 12,925 |
| OLAT target chains excluded | 50 |
| Distractor candidates | 6,453 |
| Chains selected for padding | 600 (seed=42, advanced state) |
| Chains loaded (with rendered field) | 600 |
| Target prompt length | 200K–250K tokens |
| Actual token range (L11 variants) | 200,299–200,345 tokens |
| Position L2 (50% mark) | ~223 before / ~177 after target |
| Position L3 (95% mark) | ~423 before / ~23 after target |

---

## Lever 11 Token Budget Details

| Component | Tokens |
|---|---|
| Average distractor chain (k=15) | ~410 |
| Separator (`\n\n---\n\n`) | 2 |
| Target chain + question (k=15) | ~462 |
| Total (L11 L2 variant) | ~200,300 |

---

## Documentation Errata (to fix post-Day-0, no methodology change)

**Flag 1 — BUILD_PLAN arithmetic error:**  
Tasks 3, 4, and 5 state "68 × 50 × 2 = 6,800" — incorrectly multiplies the model dimension twice. Correct: 68 × 50 = 3,400 (pre-Amendment-6) → now 64 × 50 = 3,200 (Amendment-6). BUILD_PLAN tasks should be updated to read "64 conditions × n=50 chains = 3,200 records."

**Flag 2 — SPEC §7.5 Lever 15 typo (pre-Amendment-6):**  
Prior SPEC listed Lever 15 non-baseline conditions as "(L2, L3)" — L2 is the baseline, so the non-baseline conditions are L1 and L3. Corrected in Amendment #6. BUILD_PLAN day prompt also references this errata, to be cleaned up as non-methodology documentation fix.

---

## Anomalies and Notes

1. **openai version 2.32.0 < required 2.36:** Day −2 diagnostics completed at 2.32.0 without issue. Monitored; not blocking Day 1 unless a specific 2.36 feature is invoked.
2. **Lever 24 ground truth divergence observed:** In the OLAT sample, some shuffled chains have `L1_shuffled_vs_real=True` but `L3_symbolic_checker=False` — shuffling did not create a symbolic violation in those chains. This is expected and is exactly the measurement that Lever 24 tests.
3. **Lever 11 uses same distractor set for all target chains in a condition:** The 600 distractor chains are used as uniform padding for all 50 target chains in a Lever 11 condition. The model evaluates the target chain (not the distractors). Different target chains are positioned at different offsets within the same distractor corpus.
4. **plumbing_schemas.md enum inconsistency:** Schema 1 `parse_stage_reached` enum still uses old value `first_token` instead of Amendment #3 values `md_strip` / `last_token`. This is documentation errata only — implementation uses Amendment #3 4-stage cascade per SPEC §8.

---

## Outputs Summary

| Artifact | Path | Records |
|---|---|---|
| Chain-condition assignments | `chain_condition_assignments.ndjson` | 3,200 |
| Chain variants (all conditions) | `chain_variants/` | 3,200 files |
| Distractor pool verification | `day_0/distractor_pool_verification.csv` | 19,428 |
| Lever 13 resolution | `day_0/lever_13_l2_resolution.json` | 1 |
| Parser provenance (initialized) | `parser_provenance.ndjson` | 0 (empty) |

**Day 0 complete. Ready for Day 1 batched API evaluations.**
