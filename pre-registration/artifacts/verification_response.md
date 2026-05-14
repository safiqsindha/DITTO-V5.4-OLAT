# Blocker #7 — Pre-OLAT Verification Response Specification

**Status:** RESOLVED — all six scenarios locked per O6 (decision-sheet-v1.md, 2026-05-11). S1 and S6 locked from handoff. S2, S4, S5 accepted as drafted. **S3 tightened from 0.20 to 0.05** per cross-model review rationale.

**Run parameters:** n=250 chains, V1-on-Flash (V1 methodology on V4-Flash), before OLAT proper.
**Outputs:** detection rate, gap (detection_rate_violated_chains − detection_rate_intact_chains), effect size (Cohen's h or equivalent), 95% bootstrap CI.
**Expected baseline:** approximately null (gap near 0.0), per v4.5 result and v5.1 panel null.

---

## Decision Framework

After the n=250 verification run, both authors independently review the four outputs and classify the result against the six scenarios below. Scenario classification is mutual; if authors disagree, treat as pause until resolved.

**Proceed condition (all of the following must hold):**
- None of the pause thresholds in S1–S6 are triggered
- Parse failure rate ≤ 5%
- n_valid ≥ 200 (≥ 200 chains successfully parsed)
- Both authors agree the result is interpretable

**Pause condition:** Any single scenario threshold triggered. See per-scenario response.

---

## Scenario 1 — Unexpected Positive Signal

**Definition:** The verification run shows a meaningful positive detection signal on V1 methodology applied to V4-Flash.

**Threshold (LOCKED):** `gap > 0.05`

**Rationale:** V1-on-V4-Flash should be approximately null per v4.5 result. A positive gap above 0.05 suggests V4-Flash responds differently to V1 methodology than the v4.5 cohort in a direction that would inflate OLAT lever effects.

**Trigger:** gap > 0.05 (i.e., detection rate on violated chains exceeds detection rate on intact chains by more than 5 percentage points)

**Response:**
1. **PAUSE.** Do not begin OLAT conditions.
2. Both-author review required. Review prompt: Is this positive signal real or a parse artifact? Check parse provenance logs.
3. If real: reconsider whether V1 baseline is appropriate for OLAT, or whether OLAT should use a different baseline condition. Amendment required.
4. If artifact: fix parser, re-run verification. Fresh signoff required.
5. **Amendment process:** Document finding, draft amendment to baseline configuration, both-author signoff on amendment before OLAT execution.

---

## Scenario 2 — Unexpected Strong Anti-Detection Signal

**[LOCKED per O6, reinterpreted per Amendment #3 Option (ii) — 2026-05-12]**

**Status post-Amendment-#3:** S2's pre-OLAT firing is **expected under Path 1** as floor characterization, not pathology. The Day −2 V4-Flash run (gap=−1.000) and Day −2 V4-Pro run (gap=−0.757) both trigger S2, and both are accepted as the empirical baselines per Path 1. No methodology amendment follows from S2 firing on Day −2.

Anti-detection in OLAT proper is handled via per-model effect-size analysis: a condition producing detection meaningfully worse than per-model baseline gap surfaces as a negative effect size in the OLAT effect table. No separate S2 trigger applies post-baseline.

The remainder of this section describes S2's pre-Amendment-3 original semantics for historical record.

---


**Definition:** The verification run shows a strong negative detection signal — the model performs substantially worse than chance on violated chains.

**Threshold (DRAFT):** `gap < −0.05`

**Rationale:** A strong negative gap (anti-detection) would mean V4-Flash is systematically worse than random on V1 methodology, suggesting the model has learned to classify violated chains as intact. This would compress OLAT lever effects toward a floor and make improvements hard to measure.

**Trigger:** gap < −0.05

**Response:**
1. **PAUSE.** Do not begin OLAT conditions.
2. Both-author review. Distinguish: (a) active anti-detection bias vs (b) near-chance with noisy negative estimate.
3. Compute 95% CI. If CI includes 0.0: anti-detection not confirmed; treat as null baseline and proceed with documentation.
4. If CI excludes 0.0 from below: confirmed anti-detection. Both authors decide whether to (a) proceed with OLAT with documented floor constraint or (b) amend methodology.
5. **Amendment process:** Same as S1.

---

## Scenario 3 — High Parse Failure Rate

**[LOCKED per O6 — tightened to 0.05]**

**Definition:** A substantial fraction of the n=250 outputs cannot be parsed into YES/NO by the full parser cascade (strict → permissive → first-token → unparseable).

**Threshold (LOCKED):** `parse_failure_rate > 0.05` (i.e., more than 12 of 250 outputs logged as "unparseable" after all four cascade stages)

**Rationale (O6):** V1 is the simplest condition in the entire OLAT matrix. If V1-on-V4-Flash produces more than 5% parse failures, the parser strategy is not robust enough for OLAT stress conditions (Lever 12 L3, Lever 17 L3, Lever 18 L2/L3/L4). The original 0.20 threshold describes "is the pipeline catastrophically broken" rather than "is the pipeline good enough to run OLAT on." OLAT testing on a flaky parser produces uninterpretable effect sizes.

**Trigger:** parse_failure_rate > 0.05 (unparseable / n_attempted)

**Response:**
1. **PAUSE.** Do not begin OLAT conditions.
2. Inspect unparseable outputs. Categorize failure mode: (a) anchor missing, (b) anchor format variation, (c) model refusal, (d) truncation at 32-token cap, (e) other.
3. If (d) truncation: the 32-token cap may be too tight even for simple YES/NO with anchor. Evaluate extending L1 cap to 64. Amendment required.
4. If (a) or (b): tighten anchor wording or add to permissive regex. Re-run verification with amended parser. Fresh signoff.
5. If (c) refusal: characterize refusal pattern. May indicate Lever 19-adjacent behavior. Document.
6. **Amendment process:** Document failure taxonomy, amend parser or prompt, re-run, fresh signoff.

---

## Scenario 4 — Incomplete Run / API Errors

**[LOCKED per O6]**

**Definition:** The verification run does not complete with sufficient valid responses for a reliable estimate.

**Threshold (DRAFT):** `n_valid < 200` (fewer than 200 successfully completed and parseable API calls out of 250 attempted)

**Rationale:** Fewer than 200 valid responses means the bootstrap CI will be too wide for reliable baseline characterization. The 250 target was chosen to yield a reliable estimate (±5–7 pp at 95% CI for a rate near 0.5).

**Trigger:** n_valid < 200

**Response:**
1. **PAUSE.** Do not begin OLAT conditions.
2. Diagnose failure mode: (a) API rate limiting, (b) network errors, (c) model refusals counted as missing, (d) budget exhausted.
3. If (a) or (b): retry with backoff. API-level fix, not methodology amendment.
4. If (c): refusals are valid responses — recheck parsing logic. If refusals are parsing as "unparseable," this is a parser issue, not a response count issue.
5. Re-run with fixes. Fresh signoff on re-run results before OLAT.
6. **No amendment required** if the run completes with ≥200 valid responses after fix.

---

## Scenario 5 — Output Anchor Dominates / Degenerate Output Distribution

**[LOCKED per O6]**

**Definition:** The model produces an essentially constant output regardless of chain content, indicating the output anchor (or some other prompt property) is driving responses rather than chain evaluation.

**Threshold (DRAFT):** `YES_rate > 0.95` OR `NO_rate > 0.95` on the n_valid responses (more than 95% of responses have the same class label)

**Rationale:** If the model is anchored to always say YES or always say NO, the detection rate estimate is meaningless. OLAT lever effects measured against this baseline would be uninterpretable. The pre-OLAT verification (n=250) is specifically designed to detect this before OLAT begins.

**Trigger:** (YES_count / n_valid > 0.95) OR (NO_count / n_valid > 0.95)

**Response:**
1. **PAUSE.** Do not begin OLAT conditions.
2. Inspect response distribution. Check whether the dominant response is YES (false positive bias) or NO (false negative bias / blanket refusal).
3. If YES always: model may be interpreting the anchor phrase as the answer rather than using it as a template. Test without anchor on 20 chains. If removing anchor restores variance, the anchor wording is the issue.
4. If NO always: model may be refusing to make a positive detection claim. Check whether Lever 19 L1 (no grounding) combined with the YES/NO frame suppresses positive responses.
5. Amendment: revise anchor wording or question framing. Both-author signoff required.

---

## Scenario 6 — V4-Flash Organic Competence

**Definition:** V4-Flash baseline organically outperforms the v4.5/v5.1 cohort on the detection task, suggesting the model is already competent at constraint detection under V1 methodology.

**Threshold (LOCKED):** `detection_rate_on_violated_chains ≥ 0.80` AND `gap ≥ 0.10`

**Rationale (from handoff):** If V4-Flash is already highly competent at the task under V1 methodology, testing manipulation levers against this baseline compresses observable variance and creates artificial ceiling effects. OLAT is designed to find which levers move the needle from a near-null baseline — a near-ceiling baseline changes the measurement regime.

**Trigger:** Both conditions must hold simultaneously:
- Detection rate on violated chains ≥ 0.80
- Gap (detection_violated − detection_intact) ≥ 0.10

**Response:**
1. **PAUSE.** Do not begin OLAT conditions.
2. Both-author review. **Formal amendment required** — one of three paths:
   - **Path A:** Accept ceiling-limited OLAT with documented variance compression. OLAT proceeds but predictions and interpretations are amended to reflect that upward lever effects are near-impossible.
   - **Path B:** Integrate Lever 5 (Selection Criterion) to systematically sample higher-difficulty chains until baseline returns to ~0.5. **This constitutes a scope amendment requiring fresh signoff.** Do not auto-execute.
   - **Path C:** Declare OLAT premise compromised and reconsider program direction. Consult downstream framing (Mew design, characterization) before deciding.
3. **Auto-rollback rejected.** No automatic change to baseline or methodology is permitted without fresh both-author signoff. Pre-registration discipline is preserved.
4. **Amendment process:** Document finding, select path, both authors sign amended pre-registration before any OLAT API calls.

---

## Proceed Response

If none of S1–S6 triggers and all proceed conditions hold:

1. Both authors confirm result in writing (signoff_block.md).
2. Record: detection rate, gap, effect size, 95% CI, parse failure rate, n_valid.
3. Lock these values as the empirically-established V4-Flash baseline for OLAT.
4. Begin OLAT condition preparation (Day 0 per BUILD_PLAN.md).

---

## Verification Checklist for Sign-Off

- [x] S2 threshold (gap < −0.05) confirmed by both authors per O6
- [x] S3 threshold (parse_failure_rate > 0.05 — tightened from 0.20) confirmed by both authors per O6
- [x] S4 threshold (n_valid < 200) confirmed by both authors per O6
- [x] S5 threshold (YES_rate or NO_rate > 0.95) confirmed by both authors per O6
- [x] All six scenarios reviewed for completeness against known failure modes per O6
- [ ] Both-author signoff on this specification (final pre-registration signoff)
