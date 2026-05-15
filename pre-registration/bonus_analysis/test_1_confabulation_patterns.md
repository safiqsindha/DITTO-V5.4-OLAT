# Test 1: Confabulation Pattern Characterization

**Status:** Complete  
**Priority:** 2  
**Data source:** `amendment_7/provenance.ndjson` (100 records, 73 parse_success=True)  
**Computed:** 2026-05-14

---

## Setup

**Critical preliminary finding:** In the amendment_7 (L18_L4 / native thinking mode) dataset, **every single parseable record produces a YES verdict**. Of 73 parseable records, 73 say YES — 0 say NO. This is a fundamental bias of the L18_L4 condition in this dataset.

| Model | N records | YES | NO |
|---|---|---|---|
| deepseek-v4-flash | 38 | 38 | 0 |
| deepseek-v4-pro | 35 | 35 | 0 |

This means:
- **Every intact chain (L1=False) is a confabulation** — the model says YES even though the chain has no violation
- **Every violated chain is "correctly detected"** — but only trivially, since the model says YES to everything

---

## Confabulation Rate

| Category | N |
|---|---|
| Intact chains (L1=False) | 23 |
| Confabulations (intact, model says YES) | **23 (100%)** |
| Violated chains (L1=True) | 50 |
| Correct detections (violated, model says YES) | 50 (100%) |

The confabulation rate is **100%** — the L18_L4 condition produces YES for every chain regardless of whether violations exist. This is not subtle confabulation; it is systematic over-triggering.

---

## Overall Accuracy (vs L1 ground truth)

| Model | Correct | N | Accuracy |
|---|---|---|---|
| Overall | 50 | 73 | 0.685 |
| deepseek-v4-flash | 26 | 38 | 0.684 |
| deepseek-v4-pro | 24 | 35 | 0.686 |

The 0.685 accuracy equals the fraction of violated chains in the dataset (50/73 = 0.685) — exactly the expected accuracy of a model that always says YES. The accuracy is driven entirely by the base rate of violated chains.

---

## Rule Categories in Confabulating Reasoning

For the 23 intact chains where the model confabulates (says YES), reasoning content was analyzed for rule category mentions.

### Confabulation category frequencies:

| Rule Category | Frequency (confab) | Frequency (correct rejections) |
|---|---|---|
| HP/health | 23/23 (100%) | 0/0 (N/A) |
| PP/resource | 23/23 (100%) | 0/0 (N/A) |
| Temporal | 23/23 (100%) | 0/0 (N/A) |
| Tool/availability | 23/23 (100%) | 0/0 (N/A) |
| Phase/transition | 23/23 (100%) | 0/0 (N/A) |
| Causal/logic | 22/23 (96%) | 0/0 (N/A) |
| Information state | 22/23 (96%) | 0/0 (N/A) |
| Coordination | 10/23 (44%) | 0/0 (N/A) |
| Optimization | 7/23 (30%) | 0/0 (N/A) |

**There are no "correct rejections" to compare against** — the model never rejects. Every intact chain is confabulated, so we cannot measure which rule categories distinguish confabulations from correct rejections.

The model discusses all rule categories comprehensively in every reasoning trace. This is not selective confabulation (citing a specific spurious rule) — it is comprehensive confabulation (reasoning about all possible violations and finding something to flag in every chain).

---

## Per-Model Confabulation Patterns

### deepseek-v4-flash (L18_L4):
- Intact chains: 12 | Confabulations: 12 | Rate: **100%**
- Rule categories in confabulations (n=12):
  - HP/health, PP/resource, Temporal, Tool/availability, Phase/transition: 12/12 (100%)
  - Information state: 12/12 (100%)
  - Causal/logic: 11/12 (92%)
  - Coordination: 7/12 (58%)
  - Optimization: 4/12 (33%)

### deepseek-v4-pro (L18_L4):
- Intact chains: 11 | Confabulations: 11 | Rate: **100%**
- Rule categories in confabulations (n=11):
  - HP/health, PP/resource, Temporal, Tool/availability, Phase/transition: 11/11 (100%)
  - Causal/logic: 11/11 (100%)
  - Information state: 10/11 (91%)
  - Coordination: 3/11 (27%)
  - Optimization: 3/11 (27%)

Both models are near-identical in confabulation pattern: they mention almost every rule category in every trace. The primary difference is that Pro mentions Coordination/Optimization less than Flash.

---

## Overall Rule Category Frequency (all 73 records)

| Rule Category | Frequency |
|---|---|
| HP/health | 73/73 (100%) |
| PP/resource | 73/73 (100%) |
| Temporal | 73/73 (100%) |
| Tool/availability | 73/73 (100%) |
| Causal/logic | 69/73 (95%) |
| Phase/transition | 66/73 (90%) |
| Information state | 65/73 (89%) |
| Coordination | 26/73 (36%) |
| Optimization | 16/73 (22%) |

The top 4 categories (HP/health, PP/resource, Temporal, Tool/availability) appear in 100% of traces, regardless of correctness. This confirms the model is comprehensively reasoning about all dimensions in every chain — not selectively targeting the specific violation type.

---

## Reasoning Length Analysis

| Model | Correct reasoning length (mean chars) | Wrong reasoning length (mean chars) |
|---|---|---|
| deepseek-v4-flash | 7,200 | 10,084 |
| deepseek-v4-pro | 6,569 | 8,016 |

Incorrect predictions (which for intact chains = confabulations) generate **longer reasoning** than correct predictions. Longer reasoning in L18_L4 is associated with more confabulation — the model "reasons itself into" a YES verdict through extended exploration.

---

## Confabulation Examples

All confabulations involve intact chains (L1=False, L3=False). Representative patterns:

**gen9ou-2262855067_p1** (flash and pro, vtype=none):
- Both models claim violations across: Causal/logic, Coordination, HP/health, Information state, Optimization, PP/resource, Phase/transition, Temporal, Tool/availability
- The chain is genuinely intact — no constraint violations exist

**gen9ou-2273536349_p1** (flash and pro, vtype=none):
- Both models cite: Causal/logic, HP/health, Information state, PP/resource, Phase/transition, Temporal, Tool/availability
- This chain has the highest overall detection rate (0.902) in the main analysis — it's consistently identified as intact by non-thinking models

Pattern: The native thinking (L18_L4) mode causes models to over-analyze and find spurious violations in genuinely clean chains, while the same chains are correctly identified as intact under text-prompt conditions (L18_L3 and other conditions).

---

## Comparison: L18_L4 vs Other Conditions

From Test 7 (Verdict Stability), the main provenance analysis shows intact chains achieve DR=0.879 (flash) and 0.791 (pro) under non-thinking conditions. Under L18_L4 (amendment_7), all intact chains receive YES — the thinking mode dramatically increases false positive rates for intact chains.

This is a concrete architectural finding: **native thinking mode trades false negatives (missed violations) for false positives (confabulated violations) on intact chains.**

---

## Summary

1. **100% confabulation rate under L18_L4:** Every intact chain is confabulated. The native thinking mode introduces a systematic YES-bias that eliminates any ability to correctly identify intact chains in this dataset.

2. **No selective bias in rule citations:** Both models cite all rule categories comprehensively in every trace. Confabulation is not driven by specific rule fixation — it is global overconfidence.

3. **Longer reasoning = worse outcomes:** Wrong predictions (confabulations) generate reasoning traces 20–40% longer than correct predictions, suggesting that extended reasoning leads to confabulation rather than correctness.

4. **Pro and Flash are nearly identical:** The confabulation pattern is model-agnostic; both DeepSeek variants exhibit the same behavior at near-identical rates.

5. **Methodological note:** The confabulation analysis here is limited to L18_L4 (amendment_7 data). Other conditions cannot be analyzed this way because they lack reasoning_content in the main provenance. The 100% YES rate in L18_L4 may reflect a temperature or prompt configuration specific to this condition.
