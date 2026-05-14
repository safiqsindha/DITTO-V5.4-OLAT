# Amendment #7 — L18 L4 Retest Summary

**SPEC hash:** `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8`
**Generated:** 2026-05-13
**Retest config:** `max_tokens=4096`, `thinking: enabled`. Other params unchanged from original L18 L4.
**Status:** Parallel product. NOT integrated into primary effect tables without both-author signoff.

---

## Headline Effect Table (L18 L4)

| Condition | Universe | n_valid | dr_violated | dr_intact | gap | effect_size | CI | Classification | Parse fail rate | API fail rate |
|---|---|---|---|---|---|---|---|---|---|---|
| flash_L18_L4 | L1 | 38 | 1.0 | 1.0 | 0.0 | 0.0 | — | Null | 0.24 | 0.0 |
| flash_L18_L4 | L2 | 38 | 1.0 | 1.0 | 0.0 | 0.0 | — | Null | 0.24 | 0.0 |
| flash_L18_L4 | L3 | 38 | 1.0 | 1.0 | 0.0 | 0.0 | — | Null | 0.24 | 0.0 |
| pro_L18_L4 | L1 | 35 | 1.0 | 1.0 | 0.0 | 0.0037 | — | Null | 0.3 | 0.0 |
| pro_L18_L4 | L2 | 35 | 1.0 | 1.0 | 0.0 | 0.0037 | — | Null | 0.3 | 0.0 |
| pro_L18_L4 | L3 | 35 | 1.0 | 1.0 | 0.0 | 0.0799 | — | Directional(no_CI) | 0.3 | 0.0 |

## Comparison to Original L18 L4 (max_tokens=64)

Original L18 L4: all 100 records `Unknown` (0 parsed; `finish_reason=length`, content empty).

Amendment #7 retest: see effect table above. The retest produces measurable effect sizes for the first time.

## Comparison to L18 L2/L3 (existing primary results)

From primary effect tables (Universe L3):

| Condition | Effect | Classification |
|---|---|---|
| flash_L18_L2 | 0.217 | Meaningful |
| flash_L18_L3 | 0.044 | Null |
| pro_L18_L2 | 0.379 | Meaningful |
| pro_L18_L3 | 0.354 | Meaningful |
| flash_L18_L4 | 0.0 | Null |
| pro_L18_L4 | 0.0799 | Directional(no_CI) |

## Sensitivity Analyses (L18 L4)

| Condition | Universe | S1 (as_no) | S2 (as_random) | S3 (arcsine) | S4 (parser-strict) | S5 parse-fail flag | Robustness concern |
|---|---|---|---|---|---|---|---|
| flash_L18_L4 | L1 | 0.0147 (Null) | 0.0074 (Null) | 0.0 (Null) | Unknown | True | False |
| flash_L18_L4 | L2 | 0.0147 (Null) | 0.0074 (Null) | 0.0 (Null) | Unknown | True | False |
| flash_L18_L4 | L3 | 0.1458 (Directional) | 0.0729 (Null) | 0.0 (Null) | Unknown | True | False |
| pro_L18_L4 | L1 | 0.0221 (Null) | 0.0129 (Null) | 0.0154 (Null) | Unknown | True | False |
| pro_L18_L4 | L2 | 0.0221 (Null) | 0.0129 (Null) | 0.0154 (Null) | Unknown | True | False |
| pro_L18_L4 | L3 | 0.1319 (Directional) | 0.1059 (Directional) | 0.3243 (Meaningful(no_CI)) | Unknown | True | False |

## YES-Bias Diagnostic

Detection rate on intact vs. violated chains (Universe L3 — symbolic checker, the strictest ground truth):

| Condition | dr_violated | dr_intact | Both ≥ 0.5? | Net YES rate |
|---|---|---|---|---|
| flash_L18_L4 | 1.0 | 1.0 | Yes — YES-biased | 1.0 |
| pro_L18_L4 | 1.0 | 1.0 | Yes — YES-biased | 1.0 |

## Operational Notes

- All API calls used `max_tokens=4096` with `thinking: {type: enabled}`. Other parameters unchanged from original L18 L4 (temperature=0.0).
- Parse path: 4-stage cascade on `content` field only (SPEC §8, Amendment #3). `reasoning_content` preserved for diagnostic but never parsed.
- Bootstrap: BCa, 10K iterations; seed=42 (Flash), seed=43 (Pro). Same as Day 2 primary.
- Six sensitivity analyses applied identically to primary. S6 (response-length quartile) is computed only for L18 L2/L3 — not applicable to L18 L4 because L4 is single-level. S4 may be vacuous for the same baseline-mismatch reason as L18 L2/L3.

## Output Files

- `effect_table_universe_L1.csv`, `..._L2.csv`, `..._L3.csv` — full effect tables (baselines + L18 L4)
- `provenance.ndjson` — parsed records from the retest
- `raw_responses.ndjson` — full API responses with reasoning_content
- `summary.md` — this file
- See also: `../amendments/amendment_7.md` for the methodology amendment document.