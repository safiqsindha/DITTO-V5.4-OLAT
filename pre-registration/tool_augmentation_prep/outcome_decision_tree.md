# Task 2C — Tool Augmentation Experiment: Pre-Registered Outcome Decision Tree

**Generated:** 2026-05-14
**Status:** Pre-registration document. Locked before any API experiment runs.
**Purpose:** Maps every possible experimental outcome to an interpretation and
  next-step recommendation. Prevents post-hoc narrative construction.

**Baseline (Amendment #7 L18 L4 without tool augmentation):**
- dr_violated ≈ 1.0 (all parseable violated chains → YES)
- dr_intact ≈ 1.0 (all parseable intact chains → YES)
- gap ≈ 0.0 (YES-biased; no discrimination)
- Parse failure rate: ~27% (truncation at 4096 tokens)

**Metrics reported:** dr_violated, dr_intact, gap, effect_size, parse_failure_rate
  (all under Universe L3 primary; L1/L2 as sensitivity).

---

## Outcome 1 — Tool Augmentation Works (Strong Integration)

**Trigger conditions:**
- dr_intact drops from ~1.0 to < 0.30
- dr_violated stays ≥ 0.70
- gap > 0.40
- effect_size > 0.40 (Meaningful in OLAT classification)
- parse_failure_rate does not substantially increase vs baseline

**Interpretation:**
The model integrates checker output with chain analysis. Checker NO verdict
suppresses false positives on intact chains. Checker YES verdict reinforces
true positives on violated chains. The model is not rubber-stamping (which
would produce dr_intact ≈ checker's intact accuracy, not 0.0) — it is
actively using the checker as an evidence source.

**Mew implication:**
Tool augmentation is a viable architectural path. The symbolic checker
functions as a reliable oracle that the model can leverage. Mew's value
proposition is confirmed: structured rule-checking + LLM integration
outperforms either component alone.

**Next step:** Formalize the tool augmentation pipeline. Test on a held-out
chain set. Test robustness to checker errors (intentional adversarial flips).

---

## Outcome 2 — Partial Integration (Noisy)

**Trigger conditions:**
- dr_intact drops to 0.30–0.60 (partial suppression of false positives)
- dr_violated stays ≥ 0.60
- gap 0.10–0.40
- effect_size classified as Directional or Meaningful

**Interpretation:**
The model uses checker output but inconsistently. Some intact-chain
confabulations persist despite a clear checker NO verdict. Integration
is happening but is noisy: the model's YES-bias from the native-thinking
regime partially overrides the checker signal on a subset of chains.

**Mew implication:**
Tool augmentation is directionally correct but needs refinement. Possible
refinements: (a) Template B (verdict + reasoning) may improve over Template A;
(b) lower temperature or explicit instruction to trust the checker; (c) CoT
reasoning regime may amplify integration.

**Next step:** Run Template B if Template A produced this outcome. Compare
language patterns in reasoning_content between deferred vs. non-deferred cases.

---

## Outcome 3 — Tool Augmentation Fails (Model Ignores Checker)

**Trigger conditions:**
- dr_intact stays ≥ 0.80 (no meaningful suppression of false positives)
- dr_violated stays ≥ 0.80
- gap < 0.10
- effect_size ≈ 0.0 (Null in OLAT classification)

**Interpretation:**
The model ignores checker output. The YES-bias from the native-thinking
regime overwhelms the checker signal. In-prompt tool augmentation is
insufficient; the model's prior toward YES is stronger than the injected
evidence.

**Mew implication:**
In-prompt tool augmentation is not sufficient in V1-minimal / native-thinking
framing. Requires either: (a) fine-tuning to override the YES-bias regime;
(b) architectural integration (checker output as structured input, not text);
(c) different reasoning regime (e.g., text-prompt CoT) where the model is
more responsive to injected evidence.

**Next step:** Test tool augmentation in L18 L3 framing (text-prompt CoT,
which produces ~70–88% YES rate rather than 100%). If L18 L3 + augmentation
works but L18 L4 + augmentation fails, the framing regime is the bottleneck.

---

## Outcome 4 — Rubber-Stamping (Checker Deference Without Integration)

**Trigger conditions:**
- dr_intact ≈ checker accuracy on intact chains (expected: 0.0, since checker says
  NO on all intact chains in the L3-correct universe)
- dr_violated ≈ checker accuracy on violated chains (expected: ~1.0)
- gap ≈ checker gap (close to 1.0)
- Reasoning shows minimal engagement with chain content (flagged in qualitative review)

**Distinguishing from Outcome 1:**
Outcome 1 requires evidence that the model is reading the chain and not just
echoing the checker. Rubber-stamping is identified by:
(a) Consistency analysis: chains where checker is correct vs. a counterfactual
    where checker is intentionally wrong — rubber-stamping produces ~100% follow-rate
    regardless; integration produces selective disagreement.
(b) Reasoning content analysis: rubber-stamping reasoning uses checker language
    verbatim without independent chain analysis.

**Note:** Without a counterfactual (intentionally wrong checker) arm, Outcomes 1
and 4 are observationally indistinguishable from the primary experiment. A
follow-on experiment with adversarial checker verdicts is required to distinguish.
Flag this as a limitation in the initial analysis.

**Mew implication:**
If rubber-stamping, Mew adds no value over the symbolic checker alone. The LLM
layer is a cosmetic wrapper. This would suggest the symbolic checker output should
be exposed directly, not mediated through an LLM.

**Next step:** Run adversarial-checker arm (intentionally swap ~10 checker verdicts)
to measure follow-rate. If follow-rate > 90%, rubber-stamping is confirmed.

---

## Outcome 5 — Tool Augmentation Harms Detection (Confusion)

**Trigger conditions:**
- dr_violated drops below OLAT L18 L4 baseline (i.e., below ~1.0, meaningfully so)
- Specifically: dr_violated < 0.60
- This may be accompanied by dr_intact dropping (which is good) or staying high (which is worse)

**Interpretation:**
Injecting checker output causes the model to second-guess correct checker YES
verdicts on violated chains. The model produces arguments against the checker
and concludes NO on chains that are genuinely violated. The net effect is worse
than no augmentation.

**Why this might happen:**
- The checker verdict text is not persuasive enough on "hard" violated chains
  (e.g., multiple violations that are individually subtle)
- The model reads both the chain and the checker and finds ambiguity that the
  checker text doesn't resolve, defaulting to NO
- The "you may agree or disagree" framing (Template C) over-activates contrarianism

**Mew implication:**
Tool augmentation in its current form is harmful. The checker verdict text needs
to be more specific (step-level reasoning) before injection. Template B (with
step-by-step reasoning) is more likely to succeed than Templates A or C.

**Next step:** STOP current template. Revise checker verdict text to include
step-level justification before re-running.

---

## Outcome 6 — Mixed: dr_intact Improves but dr_violated Drops Symmetrically

**Trigger conditions:**
- dr_intact drops (false positives reduced)
- dr_violated also drops by similar magnitude
- gap ≈ 0.0 (no net improvement in discrimination)

**Interpretation:**
Tool augmentation shifts the model toward NO — it suppresses YES responses
broadly, including on violated chains. This is a calibration shift, not
improved discrimination. The model is now NO-biased for a different reason
(checker-following) rather than YES-biased (confabulation).

**Mew implication:**
Augmentation is changing the response mode but not improving detection.
The model is treating checker output as a strong prior that overrides its
own chain reading in both directions. Need to calibrate the strength of the
checker signal or frame it as additional evidence rather than authoritative verdict.

---

## Template-Specific Decision Matrix

| Outcome | Template A result | Recommended next template | Action |
|---|---|---|---|
| 1 (works strongly) | Confirmed | Run C to test rubber-stamp hypothesis | Proceed to pipeline formalization |
| 2 (partial) | Confirmed | Run B (reasoning injection) | Compare A vs B gap |
| 3 (fails) | Confirmed | Test in L18 L3 framing | Re-examine regime dependency |
| 4 (rubber-stamp) | Cannot confirm without adversarial arm | Run adversarial-checker arm | Report limitation |
| 5 (harms) | Confirmed | Revise checker text (step-level) | STOP current templates |
| 6 (calibration shift) | Confirmed | Run B to add reasoning context | Add step-level evidence |

---

## Statistical Thresholds

All thresholds are pre-registered at time of writing, before any API experiment runs.

| Metric | Threshold for "meaningful" | Notes |
|---|---|---|
| effect_size | ≥ 0.10 | OLAT Meaningful threshold |
| gap | ≥ 0.10 | Absolute difference in dr_violated − dr_intact |
| dr_intact reduction | ≥ 0.40 absolute drop from baseline | Baseline ~1.0; "improvement" requires ≤ 0.60 |
| dr_violated retention | ≥ 0.60 | Augmentation should not substantially harm detection |
| parse_failure_rate increase | ≤ 0.05 above baseline | Augmentation should not substantially increase truncation |

CI method: BCa bootstrap, 10K iterations, 95% CI (same as primary OLAT analysis).
Both-universe sensitivity: L1 and L2 as sensitivity checks; L3 as primary.

---

## Stop Conditions

1. **dr_violated < 0.40 in primary universe L3** → STOP immediately. Tool
   augmentation is actively harming detection on violated chains. Do not run
   remaining templates without both-author review.

2. **parse_failure_rate > 0.50** → STOP. Prompt length budget exceeded;
   augmented prompts are too long for the model's output window. Shorten
   checker verdict text before proceeding.

3. **API failure rate > 0.20** → STOP. Likely cost or rate-limit issue.
   Review API configuration before continuing.

4. **Qualitative review shows reasoning is blank or degenerate** → STOP.
   The augmented prompt format is not being processed correctly.
