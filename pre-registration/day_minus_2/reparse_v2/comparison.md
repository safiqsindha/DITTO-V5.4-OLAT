# Task 1 — Day −2 V4-Flash v1 vs v2 Parser Comparison

**Date:** 2026-05-12  •  **Cost:** $0  •  **Input:** `raw_responses.ndjson`

**Config:** V4-Flash, V1-minimal, k=15, max_tokens=32, n=250

## Side-by-side metrics

| Metric | v1 parser (original Day −2) | v2 4-stage cascade |
|---|---|---|
| parsed_rate | 1.0000 | 1.0000 |
| YES_rate (parsed) | 0.0000 | 0.0000 |
| NO_rate (parsed) | 1.0000 | 1.0000 |
| detection_rate_intact (correctness) | 1.0000 | 1.0000 |
| detection_rate_violated (correctness) | 0.0000 | 0.0000 |
| **gap (SPEC: violated − intact)** | **-1.0000** | **-1.0000** |
| Δgap (v2 − v1) | — | +0.0000 |

## Parse stage breakdown

| Stage | v1 | v2 |
|---|---|---|
| strict | 0 | 0 |
| permissive | 0 | 0 |
| md_strip (v2-only) | — | 0 |
| last_token (v2-only) | — | 250 |
| first_token (v1-only) | 250 | — |
| unparseable | 0 | 0 |

## v1→v2 deltas

- Rescued by v2 (v1 missed): 0
- Classification differs: 0

## Stop-condition evaluation

- **parsed_rate < 0.95?** 1.0000 — NO (passes)
- **|Δgap| > 0.10?** |+0.0000| — NO (passes)
- **YES_rate > 0.05?** 0.0000 — NO (passes)

## Interpretation

**Floor-effect interpretation CONFIRMED under v2 parser.** Path 1 lock holds. Proceed to Task 2.