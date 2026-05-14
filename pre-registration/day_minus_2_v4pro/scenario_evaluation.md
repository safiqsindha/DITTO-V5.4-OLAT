# Task 2 — V4-Pro Day −2 Scenario Evaluation

**Date:** 2026-05-12  •  **Cost:** ~$1–3  •  **n=250**

## Metric snapshot

- parsed_rate: 0.9840
- detection_rate_intact: 0.8971
- detection_rate_violated: 0.1404
- gap (SPEC): -0.7566
- 95% CI gap: [-0.8379, -0.6675]
- Cohen's h: -1.7201
- YES_rate / NO_rate (parsed): 0.1301 / 0.8699

## Per-scenario evaluation

| Scenario | Threshold | Observed | Triggered? |
|---|---|---|---|
| S1 Unexpected positive | gap > +0.05 | -0.7566 | no |
| S2 Anti-detection | gap < −0.05 | -0.7566 | **YES** |
| S3 Parse failure | parse_fail > 0.05 | 0.0160 | no |
| S4 Incomplete | n_valid < 200 | 246 | no |
| S5 Degenerate | YES or NO rate > 0.95 | YES=0.1301, NO=0.8699 | no |
| S6 Organic competence | det_viol ≥ 0.80 AND gap ≥ 0.10 | det_viol=0.1404, gap=-0.7566 | no |

## Interpretation

**PAUSE triggered.** Both-author review required before Amendment #3 drafting / re-confirmation.

Triggered scenarios:
- S2 (anti-detection): gap=-0.7566 < -0.05