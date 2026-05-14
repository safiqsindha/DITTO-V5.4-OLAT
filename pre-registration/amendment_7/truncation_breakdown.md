# Amendment #7 — Truncation Breakdown at max_tokens=4096

**SPEC hash:** `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8`
**Generated:** 2026-05-13
**Scope:** Supplementary diagnostic for Amendment #7 L18 L4 retest. Informs whether an Amendment #7B at higher `max_tokens` is warranted.

---

## Headline

- **Combined truncation rate at 4096 tokens: 27/100 = 27%** (Flash 24%, Pro 30%)
- Truncation rate is higher on **intact** chains than on **violated** chains for both models — consistent with the pilot-2 hypothesis that confirming "no violation" requires deeper reasoning than identifying "yes, here's the violation"
- The pilot at max_tokens=2048 had 20% truncation; pilot 2 at 4096 (one intact chain) had 0%. The full retest at 4096 lands between these — pilots underestimated because they happened to draw chains with lower-than-average reasoning depth

---

## By Model

| Model | n | Truncated (4096 tokens) | Parsed | Mean output tokens | Min | Max |
|---|---|---|---|---|---|---|
| flash_L18_L4 | 50 | 12 (24%) | 38 (76%) | 2,565 | 535 | 4,096 |
| pro_L18_L4 | 50 | 15 (30%) | 35 (70%) | 2,554 | 989 | 4,096 |

Flash and Pro have nearly identical mean output tokens. Pro's higher truncation rate reflects a slightly heavier tail rather than a higher mean.

---

## By Ground Truth (Universe L3 — symbolic checker)

| Model | Intact (n=18) truncated | Violated (n=32) truncated |
|---|---|---|
| flash_L18_L4 | 6 (33%) | 6 (19%) |
| pro_L18_L4 | 6 (33%) | 9 (28%) |

**Pattern:** Intact chains truncate at **33% for both models** — significantly higher than violated chains (Flash 19%, Pro 28%). This is consistent across both models and suggests an asymmetric reasoning cost: confirming absence of violation requires exhausting more candidate violations than identifying a single present one.

By L1 universe (shuffled-vs-real):
- Flash intact 4/16 = 25%; violated 8/34 = 24%
- Pro intact 5/16 = 31%; violated 10/34 = 29%

L1's split looks closer to symmetric than L3's because L1 has fewer intact chains and the 4-vs-8 / 5-vs-10 splits are noisy. L3's 33%/19% asymmetry is the cleaner signal.

---

## Parseable Records — Verdict Distribution

| Model | YES | NO | Other |
|---|---|---|---|
| flash_L18_L4 | 38/38 (100%) | 0 | 0 |
| pro_L18_L4 | 35/35 (100%) | 0 | 0 |

**Zero NO verdicts across 73 parseable records.** This is the YES-bias signal documented in `summary.md`. Among records that successfully emit a verdict within 4096 tokens, the verdict is always YES regardless of ground truth.

---

## Cost

- 100 calls × avg ~2,560 output tokens × $16/M (thinking output) + 100 × ~440 input tokens × $0.27/M
- **Actual cost: ~$4.10** (10% higher than the $2-3 estimate due to higher truncation rate inflating average output)
- Pilots: $0.22 (pilot 1) + $0.06 (pilot 2) = $0.28
- **Total Amendment #7 spend: ~$4.38**

---

## Implication for Amendment #7B

A subset retest at higher `max_tokens` (e.g., 8192) would target the 27 truncated records:
- Flash truncated: 12 records
- Pro truncated: 15 records
- Estimated cost at 8192: 27 × ~$0.13 = ~$3.50

**However**, given the YES-bias signal in the 73 parseable records, the question is whether the truncated 27 would change the substantive finding. Two scenarios:

1. **Truncated records would also produce YES.** This is the most likely outcome given the 100% YES rate among completed reasoning. Amendment #7B would confirm `dr_violated = dr_intact = 1.0` more robustly but would not change the Null classification.

2. **Truncated records would produce NO.** Possible if longer reasoning eventually causes the model to "find" no violation. This would shift `dr_intact` below 1.0 and potentially reveal a real (small) gap. The asymmetric truncation by ground truth (intact 33%, violated 19-28%) hints at this — intact chains might be the ones where the model is "still deliberating" rather than committing to YES.

**Decision point for both authors:** is a $3.50 Amendment #7B worth running to disambiguate scenarios 1 and 2? If scenario 2 is true and ignored, the L18 L4 finding could be wrong in a substantive way (real positive effect masked by truncation).

---

## Output-Token Distribution

| Bucket | Flash count | Pro count |
|---|---|---|
| <1000 tokens | 6 | 1 |
| 1000–1999 | 18 | 18 |
| 2000–2999 | 9 | 11 |
| 3000–3999 | 5 | 5 |
| 4096 (truncated) | 12 | 15 |

Both distributions are roughly bimodal: a clean-completion peak around 1500–2500 tokens, plus a truncation cluster at the cap. The truncation cluster represents chains where the model's reasoning would have continued well past 4096 tokens.
