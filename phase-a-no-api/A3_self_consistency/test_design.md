# Task A3: Self-Consistency Pre-Work — Test Design

**Date:** 2026-05-15  
**Status:** Complete  
**API cost:** $0 (design only; API runs in Part B)

---

## Question

Does majority voting (N=5 samples) on the best-performing prompt-level condition (L18 L3)
break the ~30% detection ceiling observed in the OLAT primary analysis?

Both reviewers identified self-consistency as the most obvious missing test. If majority voting
substantially improves recall, the detection ceiling is stochastic (not capability-limited).
If majority voting produces minimal change, the ceiling is capability-limited — the methodology
claim is ironclad.

---

## Chain Sample Selection (seed=42)

### Selection method
- Source: 50-chain OLAT corpus (`pre-registration/parser_provenance.ndjson`)
- Ground truth universe: L3 symbolic checker (primary)
- Corpus: 18 intact / 32 violated chains
- Target: 10 intact + 10 violated (stratified across violation types)
- Seed: 42 (applied to both intact and violated sampling independently)

### Selected 20 chains

**Intact (10 chains, L3_symbolic_checker=False):**

| Chain ID | Violation type |
|----------|---------------|
| gen9ou-2262855067_p1 | none |
| gen9ou-2272614714_p1 | none |
| gen9ou-2273536349_p1 | none |
| gen9ou-2276761872_p1 | none |
| gen9ou-2312002915_p2 | none |
| gen9ou-2321486759_p2 | none |
| gen9ou-2321922786_p1 | none |
| gen9ou-2327376263_p1 | none |
| gen9ou-2330862666_p2 | none |
| gen9ou-2348078225_p1 | none |

**Violated (10 chains, L3_symbolic_checker=True, stratified by type):**

| Chain ID | Violation type |
|----------|---------------|
| gen9ou-2270600845_p1_shuffled_7919 | monotone_increase |
| gen9ou-2272010071_p2_shuffled_7919 | multiple |
| gen9ou-2272363626_p2_shuffled_7919 | multiple |
| gen9ou-2287788376_p1_shuffled_42 | multiple |
| gen9ou-2291273479_p2_shuffled_1337 | multiple |
| gen9ou-2303002268_p2_shuffled_7919 | hp_resurrection |
| gen9ou-2334711641_p2_shuffled_7919 | causal_incoherence |
| gen9ou-2341946701_p1_shuffled_1337 | multiple |
| gen9ou-2347015993_p1_shuffled_1337 | multiple |
| gen9ou-2354144810_p2_shuffled_7919 | multiple |

**Violated allocation:** causal_incoherence=1, hp_resurrection=1, monotone_increase=1,
multiple=7. Proportional to corpus (3:4:2:23 → 10-slot allocation: 1:1:1:7).

**Note on `multiple` dominance:** 7 of 10 violated chains are `multiple` violation type —
reflecting the actual corpus distribution (23/32 = 72% of violated chains are `multiple`).
This is a documented feature of the OLAT corpus, not a selection bias.

---

## Experiment Configuration

### Primary condition: L18 L3 self-consistency test

| Parameter | Single-sample baseline | Majority-vote (N=5) |
|-----------|----------------------|---------------------|
| Condition | pro_L18_L3 | pro_L18_L3 (repeated 5×) |
| Temperature | T=0.0 (deterministic) | T=0.7 (standard self-consistency) |
| max_tokens | 1024 | 1024 |
| thinking | disabled | disabled |
| Model | V4-Pro | V4-Pro |
| Aggregation | N/A | Majority vote (YES if ≥3/5 samples say YES) |

**Why L18 L3?** The best-performing CoT condition in OLAT primary analysis:
`pro_L18_L3` achieved effect_size=0.354 in L3 universe — the highest among all Meaningful
conditions. Self-consistency testing the best available condition maximizes the chance of
observing a ceiling-breaking effect.

### Optional secondary condition: L18 L4 (native thinking) self-consistency

| Parameter | Single-sample | Majority-vote |
|-----------|--------------|---------------|
| Condition | pro_L18_L4 | pro_L18_L4 (repeated 5×) |
| Temperature | nullified server-side (thinking mode) | nullified server-side |
| max_tokens | 4096 | 4096 |
| thinking | enabled | enabled |

**Note:** L18 L4 (Amendment #7) classifies as Null with 100% YES rate on parseable records.
Self-consistency for L18 L4 tests whether majority voting changes the confabulation pattern.
This is secondary — primary interest is L18 L3.

---

## API Parameters Per Condition

### L18 L3 single-sample baseline (T=0 control)
```json
{
  "model": "deepseek-v4-pro",
  "max_tokens": 1024,
  "temperature": 0.0,
  "extra_body": {"thinking": {"type": "disabled"}},
  "prompt": "[L18 L3 OLAT prompt per artifacts/lever_18_prompts.md]"
}
```

### L18 L3 majority-vote (T=0.7, N=5)
```json
{
  "model": "deepseek-v4-pro",
  "max_tokens": 1024,
  "temperature": 0.7,
  "extra_body": {"thinking": {"type": "disabled"}},
  "n_samples": 5,
  "aggregation": "majority_vote"
}
```

**Prompt template (L18 L3, from `artifacts/lever_18_prompts.md`):**

```
Does this battle chain contain any rule violations? Review the chain event by event.
For each event, check whether it conforms to the rules of Pokemon battles.
Identify any event that violates a rule. Therefore, the answer is YES or NO.
```

**Output anchor:** `Therefore, the answer is YES` / `Therefore, the answer is NO`

---

## Total API Calls

| Condition | Chains | Samples/chain | Total calls |
|-----------|--------|--------------|-------------|
| L18 L3 T=0.0 (baseline) | 20 | 1 | 20 |
| L18 L3 T=0.7 N=5 (majority vote) | 20 | 5 | 100 |
| L18 L4 T=N/A (optional) | 20 | 1 | 20 |
| L18 L4 T=0.7 N=5 (optional) | 20 | 5 | 100 |

**Primary experiment total:** 120 calls (20 baseline + 100 majority-vote)
**With optional L18 L4:** 240 calls

---

## Pre-Registered Outcome Interpretations

### Outcome 1: Majority vote substantially improves recall (>0.10 gain)

**Trigger:** `detection_rate_violated(majority_vote) − detection_rate_violated(T=0)` > 0.10
on the 10-chain violated set, L3 universe.

**Interpretation:** The detection ceiling is partly stochastic. Under deterministic inference
(T=0), the model is missing violations it could detect with additional samples. This implies:
1. The methodology ceiling is not purely capability-limited — it has a sampling component
2. Running N>1 samples per chain in production would improve recall
3. The OLAT primary analysis (single-sample, T=0) understates the model's detection potential
4. The "bottleneck is representational" claim in the writeup needs qualification

**Mew architectural implication if Outcome 1:** Self-consistency should be a standard component
of the Mew detection pipeline. The cost tradeoff (5× API calls for recall gains) needs explicit
customer-facing documentation.

---

### Outcome 2: Majority vote produces minimal change (<0.05 gain)

**Trigger:** `detection_rate_violated(majority_vote) − detection_rate_violated(T=0)` < 0.05.

**Interpretation:** The detection ceiling is capability-limited, not stochastic. With deterministic
inference already at the ceiling, adding samples at T=0.7 does not unlock additional correct
verdicts. This implies:
1. The ~30% detection ceiling is a stable property of the model's capability on this task format
2. The "bottleneck is representational, not reasoning depth" claim in the writeup is supported
3. The methodology ceiling claim is ironclad: no amount of resampling breaks through
4. Fine-tuning or structural changes (chain format, symbolic checker augmentation) are required
   for substantial recall improvement

**Mew architectural implication if Outcome 2:** Sampling budget should not be spent on majority
voting for detection. The engineering investment should go to structural improvements (chain
format, tool augmentation, fine-tuning).

---

### Outcome 3: Majority vote reduces recall (worse than single sample)

**Trigger:** `detection_rate_violated(majority_vote)` < `detection_rate_violated(T=0)`.

**Interpretation:** Unusual finding. Possible explanations:
1. T=0.7 increases noise such that some chains that produce consistent YES at T=0 now get mixed
   signals and a majority-NO outcome
2. The anchor `Therefore, the answer is YES/NO` interacts differently with non-zero temperature
3. Parse failure rate increases at T=0.7 (more creative outputs that miss the anchor format)

**Response if Outcome 3:** Investigate parse failure rates first. If parse failures are elevated
at T=0.7, the finding may be a parsing artifact rather than a genuine capability phenomenon.
Run sensitivity analysis with unparseables-as-NO vs unparseables-excluded.

---

## Execution Checklist (for tomorrow's API session)

- [ ] Load the 20 selected chain variants from `chain_variants/deepseek-v4-pro/pro_L18_L3/`
- [ ] Run single-sample baseline (T=0.0, n=1) on all 20 chains → 20 calls
- [ ] Run majority-vote experiment (T=0.7, n=5 calls per chain) on all 20 chains → 100 calls
- [ ] Apply 4-stage parser cascade per SPEC §8 to all 120 responses
- [ ] Compute `detection_rate_violated` and `detection_rate_intact` for each condition
- [ ] Compute gap and effect size vs OLAT primary analysis baseline
- [ ] Count majority votes per chain (YES count out of 5)
- [ ] Save raw responses to `self_consistency/raw_responses.ndjson`
- [ ] Check parse failure rate per condition before analyzing
- [ ] Optional: run L18 L4 conditions if budget allows

**Output files:**
- `pre-registration/self_consistency/raw_responses.ndjson` (120 records)
- `pre-registration/self_consistency/effect_table_self_consistency.csv`
- `pre-registration/self_consistency/summary.md`

**Cost estimate:** ~$0.50–1.50 (120 calls at L18 L3 lengths)
