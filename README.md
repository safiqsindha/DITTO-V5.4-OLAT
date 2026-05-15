# DITTO V5.4 — OLAT (One Lever At A Time)

Pre-registered experimental study measuring how 24 prompting/inference levers ("Levers")
affect a model's ability to detect rule violations in Pokémon battle chains.

**SPEC hash (locked, Amendment #6):** `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8`
**Models evaluated:** DeepSeek V4-Flash, V4-Pro
**Scale:** 3,200 API evaluations (64 conditions × 50 chains, dual-model)

---

## Study design

Each model is evaluated on 50 chains (sampled with `seed=42` from a pool of 19,428).
For each of 24 Levers, one or more levels (L1–L5) is run against the same chain set.
Ground truth is assessed under three universes:

| Universe | Definition | Intact/Violated split (n=50) |
|---|---|---|
| **L1** (shuffled-vs-real) | Was the chain shuffled? | 16 / 34 |
| **L2** (planted violations) | Does the chain contain a planted rule violation? | 16 / 34 |
| **L3** (symbolic checker) | Does a symbolic rule checker flag a violation? | 18 / 32 |

For this 50-chain draw, L1 and L2 are identical (every chain labeled violated in L1 is
also labeled violated in L2), so effective independent universes = 2.

Detection rate `dr = P(YES | chain)`. Gap convention (Convention B):
```
gap = dr_violated − dr_intact          (TPR − FPR, both inside the condition)
effect_size = gap(condition) − gap(baseline)
```

Classification thresholds:

| |effect_size| | Label |
|---|---|
| ≥ 0.10 | Meaningful |
| 0.03–0.10 | Directional |
| < 0.03 | Null |

If the 95% BCa bootstrap CI crosses zero, the label is downgraded one level.

---

## Methodology

- **Parser:** 4-stage cascade on the model's `content` field (strict → permissive → md_strip → last_token). `reasoning_content` is preserved but never parsed (SPEC §8, Amendment #3).
- **Bootstrap:** BCa with 10,000 iterations and jackknife acceleration. Seeds: 42 (Flash), 43 (Pro).
- **Six sensitivity analyses per condition (SPEC §9.2):** S1 unparseables-as-NO; S2 unparseables-as-random; S3 arcsine-transformed gap; S4 parser-strict subset; S5 parse-failure audit (≥10% flagged); S6 response-length quartile (L18 L2/L3 only, now token-based — see Day 2 quartile analysis).
- **Robustness flags:** `robustness_concern` if Meaningful primary + ≥3/6 sensitivities Null; `hidden_signal_candidate` if Null primary + ≥3/6 sensitivities Meaningful.
- **Empirical Bayes shrinkage:** prior mean = 0, prior variance = median observed bootstrap variance across levers.

---

## Repository layout

```
pre-registration/
├── SPEC.md                              # locked pre-registration spec
├── BUILD_PLAN.md                        # execution plan
├── parser_provenance.ndjson             # all 3,200 parsed records
├── chain_condition_assignments.ndjson   # which chains assigned to which conditions
├── chain_variants/                      # generated prompt variants per condition
├── day_0/                               # chain pool generation
├── day_minus_2/, day_minus_2_v4pro/     # ground-truth verification (V4-Flash, V4-Pro)
├── day_minus_3/                         # chain pool pre-build
├── day_2/                               # primary analysis
│   ├── effect_table_universe_L{1,2,3}.csv
│   ├── cross_model_deltas.csv
│   ├── sensitivity_analyses.json
│   ├── day_2_summary.md
│   ├── cross_universe_comparison.md
│   ├── chain_composition_note.md
│   ├── convention_and_degenerate_clarification.md
│   ├── l18_l4_diagnosis.md
│   ├── l18_l4_qualitative_review.md
│   ├── sensitivity_meaningful_conditions.md
│   ├── post_day2_validation_status.md
│   └── quartile_analysis/               # token-based S6, supersedes char-length
│       ├── quartile_breakdown_full.csv
│       └── bimodal_summary.md
├── amendment_7_pilot/                   # pilots @ max_tokens 2048 + 4096
├── amendment_7/                         # full L18 L4 retest output (parallel product)
├── amendments/
│   └── amendment_7.md                   # methodology amendment (DRAFT)
├── diagnostics/                         # exploratory + diagnostic runs (Diagnostic I, etc.)
├── decisions/                           # decision sheet
├── scripts/                             # all executor + analysis scripts
└── bonus_analysis/                      # post-primary observational battery (zero API)
    ├── bonus.md                         # full per-test summary (start here)
    ├── bonus_analysis_synthesis.md      # cross-test synthesis + Mew implications
    ├── test_1_confabulation_patterns.md
    ├── test_2_reasoning_depth.md
    ├── test_3_difficulty_stratification.md
    ├── test_4_failure_coexistence.md
    ├── test_5_reasoning_clusters.md
    ├── test_6_predictor.md
    ├── test_6_models/                   # serialized RF + LR classifiers (joblib)
    ├── test_7_verdict_stability.md
    ├── test_8_checker_characterization.md
    └── test_9_complementarity.md
```

---

## Headline findings (Universe L3, primary)

**6 Meaningful conditions** (effect ≥ 0.10, CI excludes zero):

| Condition | Effect | CI | Universes Meaningful in |
|---|---|---|---|
| pro_L17_L2 | 0.288 | [0.051, 0.486] | All 3 (most robust) |
| pro_L17_L3 | 0.243 | [0.010, 0.510] | All 3 (CI boundary-sensitive) |
| pro_L18_L3 | 0.354 | [0.026, 0.685] | All 3 |
| pro_L18_L2 | 0.379 | [0.036, 0.745] | L3 only |
| flash_L18_L2 | 0.217 | [0.026, 0.500] | L3 only |
| pro_L12_L3 | 0.191 | [0.017, 0.438] | L3 only |

**Reasoning-depth threshold effect** (token-quartile analysis, supersedes Day 2 S6 character-length):
Both V4 models exhibit a *valley-then-peak* pattern on L18 L3. At intermediate response lengths,
partial chain-of-thought produces **worse-than-baseline** results — intact chains over-trigger YES
relative to violated chains.

- **V4-Pro** valley: 427–487 tokens (effect ≈ −0.36, CI [−0.78, −0.06]); escape at ~494 tokens.
- **V4-Flash** valley: 606–728 tokens (effect ≈ −0.14, CI touches 0); escape at ~729 tokens.

This is a Mew design constraint: configurations that cap CoT generation inside the valley range
will yield worse-than-baseline behavior on rule-violation detection.

---

## Amendment #7 — L18 L4 (Native Thinking) retest

The original L18 L4 run (`max_tokens=64`) produced 100/100 `Unknown`. Root cause: DeepSeek's
API applies `max_tokens` to total output (`reasoning_content` + `content`), not content-only
as the SPEC assumed. The 64-token budget was entirely consumed by reasoning before any verdict
could be emitted.

**Amendment #7** retested L18 L4 at `max_tokens=4096` (other parameters unchanged). The full
retest is complete (100 calls; cost ~$4.10).

**Headline:** L18 L4 classifies as **Null in all 3 universes for both models**, with
`dr_violated = dr_intact = 1.0` on parseable records. **73/73 parseable verdicts are YES, 0
are NO** — a model YES-bias under native thinking, not a detection capability. 27% of
records truncated at 4096 tokens (Flash 24%, Pro 30%); intact chains truncate at 33% vs.
19–28% on violated, hinting at asymmetric reasoning cost.

The retest output is written to `pre-registration/amendment_7/` as a *parallel product* — not
merged into primary effect tables without both-author signoff. See
[`pre-registration/amendment_7/summary.md`](pre-registration/amendment_7/summary.md) for the
effect tables and [`pre-registration/amendment_7/truncation_breakdown.md`](pre-registration/amendment_7/truncation_breakdown.md)
for the truncation diagnostic. Methodology amendment doc:
[`pre-registration/amendments/amendment_7.md`](pre-registration/amendments/amendment_7.md).

---

## Bonus Analysis

Post-primary observational analysis battery. Zero API cost — all findings from records already on disk.
10 pre-specified tests covering confabulation patterns, reasoning depth, chain difficulty, failure mode
coexistence, topic modeling, a detection-success predictor (ML), verdict stability, symbolic checker
characterization, LLM-checker complementarity, and composition sensitivity.

**9 of 10 tests complete.** Test 10 (composition sensitivity) is blocked by a missing pool data file
(`phase3_results_v4.csv`). Test 5 (topic modeling) produced a null finding.

**Top findings:**

| Finding | Source |
|---|---|
| All 50 OLAT chains are exactly 15 steps — chain-length stratification is degenerate | Test 3 |
| 31/32 violated chains are blind spots for both models (<40% DR across all conditions) | Test 3 |
| Symbolic checker: precision=1.0, recall=0.941 on OLAT subset | Tests 8, 9 |
| Checker covers 94.7% of LLM failures; LLM covers only 18.3% of checker failures | Test 9 |
| Random Forest predictor: 84.7% accuracy, AUC=0.925; top feature = lever choice | Test 6 |
| L18 L4 (native thinking) produces YES on 100% of parseable records — no specificity | Tests 1, 2 |
| Deeper reasoning (3.7× longer, L18 L4) does not improve accuracy vs L18 L3 | Test 2 |
| No chain achieves YES rate above 0.30 across all 64 conditions — strong NO-bias floor | Test 7 |

**Architecture implication:** A checker-primary + LLM-secondary ensemble under L18-class conditions
outperforms either alone. The bottleneck is representational (the chain format lacks LLM pattern-
matching hooks), not reasoning depth. Condition choice (lever) matters more than chain properties.

See [`pre-registration/bonus_analysis/bonus.md`](pre-registration/bonus_analysis/bonus.md) for the
full per-test summary and [`pre-registration/bonus_analysis/bonus_analysis_synthesis.md`](pre-registration/bonus_analysis/bonus_analysis_synthesis.md)
for cross-test synthesis and Mew architectural implications.

---

## Reproducing the analysis

```bash
# Requires DEEPSEEK_API_KEY in ../.env (path resolved by scripts at runtime)
python3 pre-registration/scripts/day1_executor.py --dry-run    # pre-flight + cost estimate
python3 pre-registration/scripts/day1_executor.py              # full Day 1 run
python3 pre-registration/scripts/day2_analysis.py              # rebuild Day 2 effect tables
python3 pre-registration/scripts/quartile_analysis.py          # token-quartile breakdown
```

All scripts are append-only with resume support (`parser_provenance.ndjson` keyed by
`(condition_id, sample_id)`).

---

## Status

| Phase | Status |
|---|---|
| Day −3 chain pool generation | Complete |
| Day −2 ground-truth verification (Flash) | Complete |
| Day −2 ground-truth verification (Pro) | Complete |
| Day 1 executor (3,200 evaluations) | Complete |
| Day 2 analysis (effect tables, sensitivities, EB shrinkage, deltas) | Complete |
| Day 2 post-validation (6 tasks) | Complete |
| Quartile analysis (token-based, supersedes Day 2 S6 char-length) | Complete |
| Amendment #7 pilots (max_tokens 2048, 4096) | Complete |
| Amendment #7 full retest (100 calls at max_tokens=4096) | Complete |
| Amendment #7B (subset retest at 8192, optional) | Pending decision |
| Bonus analysis battery (10 observational tests, zero API) | Complete (9/10; Test 10 blocked) |
| Both-author signoff | Pending |

---

## Pre-registration provenance

This study was pre-registered before any data collection. The SPEC has been locked since
Amendment #6 (hash `dbae94d…`). All deviations from the locked SPEC are recorded in
`pre-registration/amendments/`. The Amendment #7 retest is the only post-Day-1 methodology
change; all other Day 2 outputs use the original locked SPEC.

---

## License

Research artifacts, no commercial license declared. Contact repo owner for use beyond
academic citation.
