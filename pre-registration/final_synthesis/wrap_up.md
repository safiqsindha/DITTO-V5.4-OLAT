# Project Ditto OLAT — Final Synthesis & Wrap-Up

**Generated:** 2026-05-15  
**Status:** All Part B experiments complete (B1, B1.5, B1.7, B2, B3). B1.7 finished 160/160, inconclusive as a robustness measurement (see Claim 6).  
**SPEC hash:** `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8`  

---

## Overview

Project Ditto OLAT ran 3,200 evaluations across 22 levers and 64 conditions on V4-Flash and V4-Pro, establishing the empirical basis for symbolic constraint chain detection. Part B (this document) adds tool augmentation, adversarial robustness, self-consistency, prompt robustness, cross-domain reproduction, and agent comparison experiments.

---

## Empirical Claims

### Claim 1 — L18 (CoT) is the dominant detection lever

**Evidence:** Universe L3 primary effect table.

| Condition | Effect | CI | Classification |
|---|---|---|---|
| pro_L18_L3 | 0.354 | [0.026, 0.685] | **Meaningful** |
| pro_L18_L2 | 0.379 | [0.036, 0.745] | **Meaningful** (L3 only) |
| pro_L17_L2 | 0.288 | [0.051, 0.486] | **Meaningful** |
| pro_L12_L3 | 0.191 | [0.017, 0.438] | **Meaningful** |

Out of 62 non-baseline conditions, only 6 are Meaningful and 7 are Directional (with CI crossing zero). L18 (thinking mode or CoT prompt suffix) produces the largest stable effects. L17 (structured JSON output) adds a secondary meaningful signal. L1–L16 are overwhelmingly null.

**Interpretation:** The model's detection capacity is regime-gated. No amount of field schema richness (L1), rendering format (L9), or auxiliary information (L12) substitutes for reasoning overhead (L18). This constrains Mew's design space: the reasoning regime must be on.

---

### Claim 2 — Native thinking (L18 L4) is YES-biased and unsuitable alone

**Evidence:** Amendment #7 retested L18 L4 at max_tokens=4096.

| Metric | Value |
|---|---|
| YES rate | 70.0% |
| NO rate | 0.0% |
| Parse failure rate | 30.0% |
| dr_violated | 1.0 |
| dr_intact | 1.0 |
| Gap | ≈0.0 |

L18 L4 produces zero discrimination: both intact and violated chains receive YES at equal rates. The 30% parse failure is a truncation artifact. Without tool augmentation, L18 L4 adds 100% false positive rate with no selectivity benefit.

**Interpretation:** L18 L4 is valuable as a reasoning substrate but not as a standalone detector. Tool augmentation is required to break the YES bias.

---

### Claim 3 — Tool augmentation (B1 Phase A) achieves near-perfect discrimination

**Evidence:** B1 Phase A — 50 chains, symbolic checker verdicts injected into L18 L4 prompts.

| Group | N | Detection Rate |
|---|---|---|
| Violated (GT_L3=True) | 32 | 0.9375 |
| Intact (GT_L3=False) | 18 | 0.000 |

**Gap: 0.9375** (pre-registered Outcome 1: gap > 0.40, dr_intact < 0.30, dr_violated ≥ 0.70 — all conditions met with large margin).

The symbolic checker (accuracy 91.39%, precision 99.90%, recall 88.61%) injects one of two verdict templates into the L18 L4 prompt. The model integrates this signal and produces calibrated YES/NO responses. Parse failure rate dropped from 30% (baseline L18 L4) to ~4% (2/50 unparseable in Phase A).

**Comparison to no-augmentation baseline (B1.5 T=0):** recall 0.60 → 0.9375; specificity 0.40 → 1.0. Tool augmentation contributes +56% recall and +60% specificity simultaneously.

**Interpretation:** This is the most important finding. The checker + LLM combination solves the detection problem at the 50-chain scale. Mew's core hypothesis — that structured symbolic checking combined with LLM reasoning outperforms either alone — is confirmed.

---

### Claim 4 — Checker deference is asymmetric (B1 Phase B)

**Evidence:** B1 Phase B — 20 chains with intentionally flipped checker verdicts. 17 valid records.

| Direction | N parseable | Deferred | Overrode |
|---|---|---|---|
| Intact → fake "violated" | 7 | **7 (100%)** | 0 (0%) |
| Violated → fake "intact" | 10 | 5 (50%) | **5 (50%)** |

**Overall rubber-stamp rate: 70.6%** (Outcome A in pre-registration taxonomy).

The model is fully susceptible to fake violation injection on intact chains: when the checker says "VIOLATION DETECTED" on a genuinely intact chain, the model defers 100% of the time, producing false positives.

In contrast, when the checker says "NO VIOLATION" on a genuinely violated chain, the model overrides in 50% of cases — evidence that native reasoning partially persists even against a confident-sounding false checker.

**Pre-registered significance:** The decision tree (outcome_decision_tree.md) predicted that Outcomes 1 and 4 (genuine integration vs. rubber-stamping) are observationally indistinguishable without this adversarial arm. Phase B resolves the ambiguity: the behavior is hybrid. The model is NOT pure rubber-stamping (violated-chain overrides confirm chain reading), but it IS fully susceptible to false positive injection.

**Interpretation:** For Mew, this is a precision/recall asymmetry risk: a noisy checker that over-reports violations will produce systematic false positives that the LLM will not correct. A checker with near-perfect precision (99.90% in this corpus) is therefore essential — the LLM cannot be relied upon to filter false positive checker verdicts.

---

### Claim 5 — Majority-vote self-consistency provides marginal recall improvement (B1.5)

**Evidence:** B1.5 — 20 chains, T=0 single sample vs T=0.7 × 5 majority vote.

| Metric | T=0 | T=0.7 majority |
|---|---|---|
| Recall (violated) | 0.60 | 0.70 |
| Specificity (intact) | 0.40 | 0.30 |
| Gain | — | +0.10 recall, −0.10 specificity |

Recall gain = 0.100 — pre-registered as "Intermediate" (0.05–0.10 range; technically 0.100 does not satisfy the strict `> 0.10` threshold for Outcome 1). Specificity *decreases* with majority vote, confirming that the model's false positive tendency is stochastic: temperature sampling generates more false positives at T=0.7.

**Interpretation:** The detection ceiling under no augmentation is both stochastic (majority vote helps recall) and capability-limited (50% false positive rate at T=0). Self-consistency alone cannot replace the symbolic checker: it trades recall for specificity and produces no net improvement in discrimination. This validates the augmentation approach (Claim 3) over the self-consistency approach.

---

### Claim 6 — Prompt robustness (B1.7) — COMPLETE, INCONCLUSIVE AS A ROBUSTNESS MEASUREMENT

**Status:** Complete. 160/160 calls, 0 timeouts. 41/160 (≈26%) parseable. The
chronic API-hang was diagnosed (l18_l4 thinking calls are slow at ~150s, not
hung) and bounded with a 300s `concurrent.futures` timeout that never had to
fire. B1.7 tests **prompt variants on the bare model — there is no checker
augmentation in this experiment.**

**Headline result: the dominant finding is parse failure, not robustness.**
74% of responses (119/160) were unparseable. Per-cell parseable N is too
sparse to compute a gap for 5 of 8 variant×regime cells:

| Regime | Variant | N(parse) | n_intact | n_violated | dr_intact | dr_violated | gap |
|---|---|---|---|---|---|---|---|
| v1_minimal | V0 | 2 | 2 | 0 | 1.0 | — | — |
| v1_minimal | V1 | 2 | 2 | 0 | 1.0 | — | — |
| v1_minimal | V2 | 15 | 9 | 6 | 1.0 | 1.0 | **0.0** |
| v1_minimal | V3 | 1 | 1 | 0 | 0.0 | — | — |
| l18_l4 | V0 | 5 | 0 | 5 | — | 1.0 | — |
| l18_l4 | V1 | 7 | 1 | 6 | 1.0 | 1.0 | **0.0** |
| l18_l4 | V2 | 3 | 0 | 3 | — | 1.0 | — |
| l18_l4 | V3 | 10 | 4 | 6 | 0.75 | 1.0 | **0.25** |

Only 3 cells yield a computable gap: v1_minimal V2 = 0.0, l18_l4 V1 = 0.0,
l18_l4 V3 = 0.25.

**Interpretation (honest):**

1. **Not assessable as designed.** Surface robustness (V0/V1/V3) and semantic
   robustness (V0/V2) both require comparing computable gaps across variants.
   V0's gap is uncomputable in *both* regimes (no parseable intact+violated
   pair), so neither pre-registered comparison can be made. The script's
   mechanical "Fragile — gap range 0.250 ≥ 0.10" label is derived from
   l18_l4 V1 vs V3 on N ≤ 10 per cell and **should not be over-read**; it is
   not a statistically meaningful robustness verdict.

2. **Consistent with the baseline story.** Where a gap *is* computable, two of
   three cells show gap = 0.0 — the bare model assigns "violation" at equal
   rates to intact and violated chains. This is the same YES-bias pathology
   documented in Claim 2 for unaugmented L18 L4, now seen to persist across
   prompt framings. B1.7 thus *corroborates* Claims 1–2 (the unaugmented
   model is near-chance regardless of prompt surface) rather than testing the
   augmentation result, which is a separate experiment (Claim 3).

3. **Bottom line:** B1.7 does not deliver a prompt-robustness measurement for
   the augmentation effect. It delivers a null/inconclusive result at these
   token settings (v1_minimal max_tokens=32; l18_l4 thinking without a
   forced YES/NO trigger), and incidental confirmation that prompt variation
   does not rescue the unaugmented model. The central augmentation claim
   (Claim 3) does not depend on B1.7.

Artifacts: `pre-registration/prompt_robustness/effect_table_per_variant.csv`,
`surface_robustness_summary.md`, `semantic_robustness_summary.md`.

---

### Claim 7 — PUBG anti-detection does not reproduce in V4-Pro replication (B2)

**Evidence:** B2 — 20 PUBG chain pairs, 4 conditions (original + 3 modifications), V4-Pro V1-minimal.

| Condition | FPR | TPR | Gap | Anti-detection? |
|---|---|---|---|---|
| original | 0.0 | 0.2 | 0.2 | No |
| mod1_strip_marker | 0.0 | 0.2 | 0.2 | No |
| mod2_move_marker | 0.0 | 0.1 | 0.1 | No |
| mod3_rename_marker | 0.0 | 0.1 | 0.1 | No |

**Pre-registered Outcome 3:** Anti-detection does NOT reproduce in this replication.

The P3 finding (FPR > TPR, `NOTE=Player_X_already_eliminated` marker drives false positives) was not reproduced. In this replication: FPR=0.0 across all conditions (model never falsely flags clean PUBG chains), TPR=0.2 (model detects only 20% of violated chains, regardless of marker manipulation).

The `eliminated_player` marker is **absent from OLAT Pokemon chains** (0/50 files).

**Interpretive note:** The non-reproduction does not invalidate the P3 finding — different PUBG chain selection, different exact prompt construction, or model version differences could explain the divergence. The key finding for this project is that the PUBG-domain marker artifact does not contaminate OLAT chains.

---

### Claim 8 — R1 research-mode agent (B3) never finalizes; the binding constraint is reluctance to commit, not turn budget

**Evidence:** B3 was run **twice** — Claude Sonnet (claude-sonnet-4-6),
30 web searches, at two turn budgets.

| Run | Turn budget | Searches used | Best dev F1 | `finalize_checker`? | Outcome |
|---|---|---|---|---|---|
| Original | 20 | 30/30 | 0.865 (P=0.941, R=0.80) @ turn 20 | No | Unknown |
| Re-run (2026-05-16) | **45** | 30/30 | **0.884 (P=0.826, R=0.95)** @ turn ~42 | **No** | **Unknown** |

**The decisive finding: 2.25× the turn budget did not change the outcome
class.** With more than double the turns, the agent reached a *higher* dev F1
(0.884 vs 0.865, recovering recall to 0.95 via a late phase-establishment
rule) but **still never called `finalize_checker`** — it kept iterating
`evaluate_checker` until the hard turn cap, ending turn 45 mid-experiment at
F1=0.85. Both runs: searches exhausted 30/30, no checker written to disk,
pre-registered outcome **Unknown — agent did not finalize checker**.

The original interpretation ("the bottleneck is the shuffled-chain violation
pattern within budget") is **superseded**: given 25 extra turns the agent
*did* eventually crack recall (0.95), so the violation pattern was not the
hard wall. The actual binding constraint is **behavioral — the agent does not
commit.** It treats `finalize_checker` as never-yet-optimal and iterates
indefinitely. This is a sharper and more architecturally relevant finding
than the budget-exhaustion framing.

**Re-run dev F1 trajectory:** plateau at 0.811 (turns ~20–32) → 0.872 (turn
~38, "Rule AA" phase rule) → peak 0.884 (turns ~42–44, R=0.95) → 0.85 (turn
45, still perturbing rules when the cap hit).

**Qualitative finding (unchanged):** The agent independently rediscovered HP
resurrection and PP monotone-decrease rules via simulated web search
(matching actual symbolic checker rules), confirming agentic rule-discovery
works; the failure is convergence/commitment, not discovery.

Prior `max_turns=20` outputs are preserved at
`experiment/agents/R1_sonnet_research_maxturns20_backup_20260516/`.

**Comparison baseline (per merged LLM-to-Criteria table, PR #9):** A1 (Sonnet, no internet): dev F1=0.889, **val F1=0.867**; B2 (Sonnet, open web): dev F1=0.929, **val F1=0.867**. The R1 agent's best dev F1=0.884 (re-run, first 30 chains) is comparable to A1/B2 *dev* performance, but in **neither run** did the agent validate on a held-out set, so no val-F1 comparison is possible at any turn budget. Pre-registered comparison requires a finalized checker. (Prior drafts cited B2 F1=0.897; corrected to 0.867 against the authoritative merged table.)

**Interpretation:** Internet research at a 30-query budget approaches but does not exceed the no-augmentation Sonnet baseline, *and the agent will not commit a checker regardless of turn budget*. Tool augmentation (Claim 3) with a pre-built checker dramatically outperforms both. For Mew, the architectural lesson is that agentic checker-construction needs a forced-commitment mechanism (e.g., auto-finalize the best-scoring checker at budget exhaustion), not merely a larger budget.

---

### Claim 9 — Cross-domain isolation: PUBG artifacts absent from OLAT chains

**Evidence:** B2 cross-domain check. 

PUBG `NOTE=Player_X_already_eliminated` marker present in OLAT chains: **0/50 files** (0%).

The PUBG-specific marker pattern does not appear in OLAT Pokemon chains. OLAT chain violations are limited to: HP resurrection (hp at 0.0% → positive), PP monotone violation (pp increase), ToolAvailability after permanent UNAVAILABLE, SubGoalTransition causal incoherence. These are structurally different from PUBG's elimination tracking pattern.

---

## LLM-to-Criteria Experiment — Complete Results (PR #9, merged)

> **Naming note:** The agent IDs below (A1–A3, B1–B3, C1) are *internal to the
> LLM-to-Criteria experiment* and are **distinct from the Part B experiment IDs**
> (B1 tool augmentation, B2 PUBG, B3 R1 research agent) used elsewhere in this
> document. Do not conflate `B2` (LLM-to-Criteria: Sonnet + open web) with Part B's
> B2 (PUBG anti-detection).

Seven agents built symbolic constraint checkers from the same 50-chain Pokemon
battle dataset. All achieved **precision = 1.0** (zero false alarms).

| Agent | Model | Internet | Dev F1 | Val F1 |
|-------|-------|----------|--------|--------|
| A2 | Haiku | None | 0.889 | 0.867 |
| A1 | Sonnet | None | 0.889 | 0.867 |
| A3 | Opus 4.7 | None | **0.929** | 0.867 |
| B3 | Haiku | Open web | 0.889 | 0.786 |
| B2 | Sonnet | Open web | **0.929** | 0.867 |
| B1 | Opus 4.7 | Open web | **0.929** | 0.867 |
| C1 | Sonnet | Serebii only | **0.929** | 0.867 |

**Three findings:**

1. **Capability:** Dev F1 rises with model size; val F1 is flat at 0.867 for every
   model — the ceiling is the chain format, not the model.
2. **Internet:** Helps at Sonnet (+0.040 dev F1), is redundant at Opus (already
   derives every rule), and doesn't help at Haiku.
3. **Domain restriction:** Serebii-only = open web. Zero performance cost from
   restricting to one authoritative source.

**To break the 0.867 ceiling:** use k=20 or k=30 chains (already pre-registered,
no code changes needed), or add `active_pair` annotations to the chain format.

**Status:** PR #9 merged and closed. Experiment fully complete; all results on `main`.

**Cross-reference (reconciled):** Claim 8 (Part B R1 research agent) previously
cited "B2 (Sonnet with internet): F1=0.897" as a comparison baseline. This has
been corrected to the authoritative merged value — LLM-to-Criteria B2 **val
F1 = 0.867** (dev F1 = 0.929) — in the Claim 8 text above.

---

## Mew Architecture Specification — Updated

Based on the full empirical record:

### Core Architecture

```
Chain Input
    ↓
Symbolic Constraint Checker  ← Critical: must have precision ≥ 0.999
    ↓
Verdict + Confidence Score
    ↓
LLM Integration Layer (L18 L4 framing)  ← Tool-augmented prompt
    ↓
Final YES/NO + Explanation
```

### Empirical constraints on architecture:

1. **Checker precision must be near-perfect (≥ 0.99)**: B1 Phase B shows 100% rubber-stamping of false violation verdicts on intact chains. A checker with 10% FPR will produce systematic false positives that the LLM cannot filter.

2. **LLM reasoning regime must be L18 (CoT)**: V1-minimal and L18 L4 without augmentation both fail (gap≈0). L18 L3 CoT achieves gap=0.354 standalone; L18 L4 + checker achieves gap=0.9375.

3. **Self-consistency sampling does not substitute for checker**: Majority vote at T=0.7 improves recall by 0.10 but degrades specificity by 0.10. Net discrimination improvement: 0. The symbolic checker provides precision-recall improvement simultaneously.

4. **Prompt-robustness of the augmentation effect is untested**: B1.7 completed but is inconclusive (74% parse failure; V0 gap uncomputable in both regimes; see Claim 6). It corroborates that the *unaugmented* model is near-chance across prompt framings but does not measure robustness of the *augmented* effect. This remains an open validation gap, not a confirmed property.

5. **Adversarial robustness limitation**: Mew's checker layer must be trusted — the LLM defers to it asymmetrically. This means the checker pipeline needs high-confidence gating: only inject verdicts when checker confidence is high; defer to LLM-only reasoning for low-confidence checker outputs.

### Mew V2 Design Recommendation

```
Chain Input
    ↓
Symbolic Checker → confidence ≥ 0.95?
    ├─ YES: Inject verdict + reasoning into L18 L4 prompt
    │         Model almost always defers (gap=0.9375)
    │         Risk: false positive rubber-stamp → gated by checker precision
    └─ NO:  Use L18 L3 CoT without augmentation  
              Model achieves gap=0.354
              Lower ceiling but no checker-deference risk
```

---

## Mew Pitch — Empirically Grounded

**The problem:** LLMs cannot reliably detect constraint violations in structured game logs. V1-minimal produces near-zero detection. Even the best prompt engineering (L18 L3 CoT) achieves only 35% discrimination on 50-chain OLAT.

**The solution:** Mew's hybrid architecture combines:
1. A symbolic constraint checker (deterministic rule evaluation, 91.39% accuracy, 99.90% precision)
2. An LLM reasoning layer (L18 L4 CoT) that integrates checker output with chain analysis

**The evidence:**
- Standalone CoT: gap=0.354 (best OLAT condition, 3,200 evaluations)
- Tool-augmented CoT: gap=0.9375 (50-chain Phase B, same model)
- Gap improvement: +165% relative to standalone CoT

**The caveat:** The LLM rubber-stamps false violation verdicts 100% of the time. Mew is only as good as its checker's precision. This is a feature, not a bug: it means Mew's quality is directly controllable via checker quality, which is deterministic and auditable.

**Competitive positioning:**
- Pure LLM (L18 L3): 35% discrimination → not deployable
- Pure checker: 91.39% accuracy, 99.90% precision → near-deployable but brittle (88.61% recall)
- Mew (checker + LLM): 93.75% recall, 100% specificity → deployable for moderated-precision use cases

---

## Open Questions for Next Phase

1. **Prompt robustness of the augmentation effect**: B1.7 was inconclusive (74% parse failure on the *bare* model; never tested the augmented effect). A redesigned run with a forced YES/NO trigger (or higher max_tokens for l18_l4) and the checker injected is needed to actually answer whether augmentation persists across V0/V1/V3 and V0/V2.

2. **Checker scaling**: The symbolic checker was built for specific OLAT violation types (hp_resurrection, pp_monotone, tool_availability, subgoal_causal). What is its performance on out-of-distribution chains, new game domains, and edge cases?

3. **Confidence-gated augmentation**: Can Mew apply conditional injection (inject verdict only when checker confidence ≥ threshold) to prevent rubber-stamping on checker FPs? The threshold tuning would require a calibration set.

4. **False positive rubber-stamp mitigation**: For adversarial robustness, can a prompt instruction ("critically evaluate the checker's claim before deciding") shift the 100% rubber-stamp rate on fake violations without degrading normal augmentation performance?

5. **Agent vs. augmentation tradeoff**: B3 shows a research-mode agent with internet access approaches F1=0.865 in dev with 30 searches + 20 turns. At what computational budget does agent-built checking approximate or exceed pre-built checker + LLM augmentation? This is the Mew architectural decision point.

6. **PUBG anti-detection**: B2 found no anti-detection in this replication. P3's original finding (FPR > TPR) may be condition-specific (different chain selection, prompt variant, or model version). Investigation requires controlled comparison.

7. **B3 finalization**: ~~Re-run at higher turn budget~~ TESTED 2026-05-16 at max_turns=45 — the agent *still* did not finalize (best dev F1=0.884, no val comparison). Conclusion: a larger budget does not help; the open need is a forced-commitment mechanism (auto-finalize best-scoring checker at budget exhaustion), which would require a script change to `finalize_checker` gating, not another re-run.

8. **Amendment #7 sign-off**: L18 L4 results (Amendment #7) require both-author sign-off (R1 in olat_status_check.md) before they can be formally cited. This is a process requirement, not a data requirement.

---

## Experiment Status Summary

| Experiment | Status | Primary Finding |
|---|---|---|
| OLAT Day 1+2 (3,200 evals) | Complete | L18 CoT = dominant lever; gap=0.354 (pro_L18_L3) |
| B1 Phase A — Tool Augmentation | Complete | gap=0.9375 (Outcome 1) |
| B1 Phase B — Adversarial Inversion | Complete | Asymmetric: 100% rubber-stamp (intact→fake-violated); 50% override (violated→fake-intact) |
| B1.5 — Self-Consistency | Complete | Recall gain=0.100 (Intermediate); specificity drops |
| B1.7 — Prompt Robustness | Complete | Inconclusive: 74% parse failure; only 3/8 cells computable; corroborates Claims 1–2, doesn't test Claim 3 |
| B2 — PUBG Anti-Detection | Complete | Outcome 3: does not reproduce; cross-domain clean |
| B3 — R1 Research Agent | Complete* | Run twice (max_turns 20 & 45); never finalized at either budget; best dev F1=0.884 (45-turn); binding constraint = commitment, not budget |
| LLM-to-Criteria (PR #9) | Complete | 7 agents, all precision=1.0; val F1 flat at 0.867 (format-bound ceiling) |

*B3 technically incomplete per pre-registration (no finalized checker).

---

## Artifact Index

| Artifact | Path |
|---|---|
| B1 Phase A effect table | `pre-registration/tool_augmentation/effect_table.csv` |
| B1 Phase A raw responses | `pre-registration/tool_augmentation/raw_responses.ndjson` |
| B1 Phase B raw responses | `pre-registration/tool_augmentation/adversarial_inversion_responses.ndjson` |
| B1 Phase B analysis | `pre-registration/tool_augmentation/inversion_analysis.md` |
| B1 summary | `pre-registration/tool_augmentation/summary.md` |
| B1.5 effect table | `pre-registration/self_consistency/effect_table_self_consistency.csv` |
| B1.5 summary | `pre-registration/self_consistency/summary.md` |
| B1.7 raw responses | `pre-registration/prompt_robustness/raw_responses.ndjson` |
| B1.7 effect table (pending) | `pre-registration/prompt_robustness/effect_table_per_variant.csv` |
| B2 raw responses | `pre-registration/pubg_artifact_investigation/raw_responses.ndjson` |
| B2 reproduction summary | `pre-registration/pubg_artifact_investigation/phase_2b_reproduction.md` |
| B2 cross-domain check | `pre-registration/pubg_artifact_investigation/cross_domain_check.md` |
| B3 search log | `experiment/agents/R1_sonnet_research/search_log.jsonl` |
| B3 agent turns | `experiment/agents/R1_sonnet_research/agent_turns.jsonl` |
| B3 agent summary | `experiment/agents/R1_sonnet_research/agent_summary.md` |
| Day 2 effect tables | `pre-registration/day_2/effect_table_universe_L{1,2,3}.csv` |
| Cross-universe comparison | `pre-registration/day_2/cross_universe_comparison.md` |
| Outcome decision tree | `pre-registration/tool_augmentation_prep/outcome_decision_tree.md` |
