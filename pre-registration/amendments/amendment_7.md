# Amendment #7 — Lever 18 L4 Retest with Raised Token Budget

**SPEC parent hash:** `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8` (locked at Amendment #6)
**Author(s):** Safiq Sindha (SS), Myriam Sindha (MS)
**Status:** SIGNED OFF — both authors approved 2026-05-16 (retest complete; YES-bias finding accepted)
**Generated:** 2026-05-13
**Retest completed:** 2026-05-13 22:16 PT (100/100 records, cost ~$4.10)

---

## 1. Problem Statement

The Day 1 execution of Lever 18 L4 (Native Thinking, both V4-Flash and V4-Pro) produced 100/100 `Unknown` records (0 parseable). Diagnostic investigation ([`day_2/l18_l4_diagnosis.md`](../day_2/l18_l4_diagnosis.md)) identified the root cause:

- SPEC §7 specifies `L4: 64 (on content) | thinking enabled; reasoning_content server-allocated separately`.
- DeepSeek's V4-Flash/Pro API, contrary to that assumption, applies `max_tokens` to **total output** (`reasoning_content` + `content` combined).
- All 100 records had `output_tokens=64` (exactly the cap), `finish_reason=length`, and empty `content`. The model's reasoning consumed the entire 64-token budget before any verdict could be emitted.

This is an operationalization gap between SPEC and the actual API, not a model defect, not a parser bug, and not a data quality issue.

---

## 2. What Changed

| Aspect | Original SPEC | Amendment #7 |
|---|---|---|
| `max_tokens` for L18 L4 | 64 | **4096** |
| `thinking` | enabled | enabled (unchanged) |
| Temperature | 0.0 | 0.0 (unchanged) |
| Chain set | 50 chains per model | same 50 chains (no resampling) |
| Parser | 4-stage cascade on `content` (SPEC §8, Amendment #3) | unchanged |
| Bootstrap | BCa 10K, seed=42 (Flash) / 43 (Pro) | unchanged |
| Universes | L1, L2, L3 | unchanged |
| Models | V4-Flash, V4-Pro | unchanged |

**No methodological change to ground truth, sensitivity analyses, classification thresholds, or any other condition.** Only the `max_tokens` parameter for the L18 L4 condition is changed, and only because the original value was incompatible with the actual DeepSeek API behavior.

---

## 3. Rationale for 4096 Tokens

Determined empirically via two pilots:

**Pilot 1** (`pre-registration/amendment_7_pilot/pilot_summary.md`):
- 10 calls (5 Flash + 5 Pro) at `max_tokens=2048`
- 8/10 (80%) produced parseable YES verdicts
- 2/10 (20%) truncated at exactly 2048 tokens — both on the same intact chain (`gen9ou-2262855067_p1`)
- Cost: $0.22
- Mechanical classification: `RAISE_BUDGET`

**Pilot 2** (`pre-registration/amendment_7_pilot/pilot2_summary.md`):
- 2 calls (1 Flash + 1 Pro) on the truncated chain at `max_tokens=4096`
- 2/2 (100%) completed with parseable YES verdicts
- Flash: 2,354 output tokens (74% headroom)
- Pro: 1,401 output tokens (66% headroom)
- Cost: $0.06

4096 tokens gives Flash ~74% headroom over its worst observed case and aligns with the SPEC §7 cost estimate band for L18 L4 ($0.41 estimate; observed pilot avg suggests $2–3 for full retest).

---

## 4. Cost Impact

| | Original | Amendment #7 |
|---|---|---|
| Calls | 100 | 100 (same 50 chains × 2 models) |
| Cost (estimated) | $0.41 | $2–3 (empirically informed from pilot 1 + 2) |
| Cumulative budget impact | within SPEC §7 ceiling of $6.50 for L18 L4 | within ceiling |

Pilot 1 + Pilot 2 combined: $0.28 already spent on diagnostic + threshold confirmation.

---

## 4a. Retest Outcome (added 2026-05-13 22:16 PT)

| Metric | Flash | Pro |
|---|---|---|
| Records | 50 | 50 |
| Truncated at 4096 tokens | 12 (24%) | 15 (30%) |
| Parseable | 38 (76%) | 35 (70%) |
| Verdicts YES | 38 (100%) | 35 (100%) |
| Verdicts NO | 0 | 0 |
| Mean output tokens (all) | 2,565 | 2,554 |

**Classification (Universe L3):** flash_L18_L4 = Null, pro_L18_L4 = Directional(no_CI) (effect=0.0799 is the same baseline-subtraction artifact seen on the four degenerate Pro conditions — `gap=0.0` minus baseline_gap `−0.0799`).

**Substantive finding:** the model classifies all chains as containing violations under native thinking. `dr_violated = dr_intact = 1.0` on parseable records. This is **YES-bias under native thinking**, not a detection-capability effect.

**Asymmetric truncation:** intact chains truncate at 33% in both models vs. 19% (Flash) / 28% (Pro) on violated chains. This hints that intact-chain reasoning extends beyond 4096 tokens — possibly because confirming "no violation" requires exhausting all candidates rather than identifying one. An Amendment #7B at `max_tokens=8192` would disambiguate whether the truncated 27 would shift any `dr_intact` below 1.0.

**Pilot vs. full-run divergence note:** Pilot 1 (n=10 at 2048) had 20% truncation; pilot 2 (n=2 at 4096, intact chain) had 0%. Both underestimated. The full retest at 4096 lands at 27% truncation overall, with the asymmetric intact-vs-violated pattern visible only at the full sample.

---

## 5. Scope of Results

**The amendment retest produces a parallel-product set of outputs**, written to `pre-registration/amendment_7/`:

- `provenance.ndjson` — 100 parsed records in the same schema as `parser_provenance.ndjson`
- `raw_responses.ndjson` — full API responses including `reasoning_content`
- `effect_table_universe_L1.csv`, `..._L2.csv`, `..._L3.csv` — effect tables for L18 L4 (Flash + Pro) under all three Lever 24 universes, computed via the same BCa bootstrap + 6 sensitivities used in Day 2 primary
- `summary.md` — headline effect table + comparison to L18 L2/L3 + YES-bias diagnostic

**These outputs are NOT merged into the primary parser_provenance or primary effect tables without both-author signoff.** The merge step is intentionally deferred so that:

1. Both authors can independently validate the retest outcome before it enters the headline finding set.
2. Any decision about how to characterize L18 L4 in the final write-up (Meaningful, Null, biased, etc.) is made with both authors' input — the retest may reveal a YES-bias pattern that warrants a different framing than a simple Meaningful/Null classification.

If both authors approve, the merge is a single append from `amendment_7/provenance.ndjson` into `parser_provenance.ndjson` plus a re-run of `day2_analysis.py` against the updated primary log.

---

## 6. What This Does Not Cover

- **Same operationalization gap may exist for other thinking-enabled conditions.** No other OLAT condition uses `thinking: enabled` at content-only `max_tokens`, so this amendment is scoped narrowly to L18 L4. Future Mew design should specify thinking budgets in DeepSeek-native terms (total-output cap) rather than assuming content-only allocation.
- **Other L18 levels (L1, L2, L3) are unaffected.** They did not use thinking-enabled mode under the original SPEC and require no retest.
- **No change to the locked SPEC §9 classification thresholds.** Meaningful / Directional / Null thresholds and the `robustness_concern` / `hidden_signal_candidate` flag logic are unchanged.

---

## 7. Decision Authority

This amendment is **methodology amendment territory** — it changes a parameter (`max_tokens`) that affects how a condition is measured. Per project convention, both authors must sign off before:

1. Merging Amendment #7 results into primary effect tables.
2. Citing L18 L4 results in the final write-up.

The amendment is **not** a SPEC hash change. The parent SPEC (hash `dbae94d…`) remains the locked reference. Amendment #7 documents a single parameter override for one condition (L18 L4) with explicit rationale and empirical pilot evidence.

---

## 8. Signoff Block

```
Author 1 signoff:    [x] Safiq Sindha (SS)   Date: 2026-05-16   Notes: Retest reviewed; root cause (total-output max_tokens) and YES-bias finding accepted. L18 L4 = Null/biased.
Author 2 signoff:    [x] Myriam Sindha (MS)  Date: 2026-05-16   Notes: Concur. YES-bias under native thinking confirmed; classification stands.
Merged to primary:   [ ]   Date: __________   By:    ____________________   (signoff complete — merge into primary tables is now UNBLOCKED but not yet performed; separate explicit step)
```

---

## 9. Cross-References

- **Root-cause diagnostic:** [`day_2/l18_l4_diagnosis.md`](../day_2/l18_l4_diagnosis.md)
- **Qualitative review of original failure:** [`day_2/l18_l4_qualitative_review.md`](../day_2/l18_l4_qualitative_review.md)
- **Pilot 1 (2048 tokens):** [`amendment_7_pilot/pilot_summary.md`](../amendment_7_pilot/pilot_summary.md)
- **Pilot 2 (4096 tokens, intact-chain edge case):** [`amendment_7_pilot/pilot2_summary.md`](../amendment_7_pilot/pilot2_summary.md)
- **Retest results:** [`amendment_7/summary.md`](../amendment_7/summary.md)
- **Executor script:** [`scripts/amendment_7_executor.py`](../scripts/amendment_7_executor.py)
- **Analysis script:** [`scripts/amendment_7_analysis.py`](../scripts/amendment_7_analysis.py)
