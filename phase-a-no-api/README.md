# Phase A — No-API Experiment Batch

**Date:** 2026-05-15  
**Status:** Complete  
**Total API cost:** $0  
**Estimated time:** 4–6 hours

All five tasks in the no-API batch are complete. This folder contains the outputs.
No API calls were required for any task in this batch.

---

## Summary of Tasks

| Task | Description | Status | Key Finding |
|------|-------------|--------|-------------|
| A1 | Deployment-time predictor analysis | ✅ Complete | AUC=0.907 with baseline pre-screen; AUC=0.564 without |
| A2 | PUBG anti-detection Phase 2A (code investigation) | ✅ Complete | Candidate marker identified: `eliminated_player` field |
| A3 | Self-consistency pre-work (sampling + test design) | ✅ Complete | 20-chain sample selected, experiment specified |
| A4 | Prompt robustness pre-work (variant design) | ✅ Complete | 4 variants designed, 20-chain sample selected |
| A5 | OLAT documentation audit + errata verification | ✅ Complete | All 3 errata confirmed applied; SPEC hash matches |

---

## Task A1: Deployment-Time Predictor Analysis

**Question:** Can a chain-features-only predictor achieve usable AUC (>0.70) for predicting
V4-Pro detection success, without evaluation-time features like ground truth labels?

**Method:** Split the 17 features from Test 6's RF model into deployment-time (available before
running detection) and evaluation-time (only available after running). Train logistic regression,
random forest, and gradient boosting on the deployment-time subset.

**Key results:**

| Predictor | AUC | Notes |
|-----------|-----|-------|
| Full-feature RF (Test 6 baseline) | 0.925 | Uses ground truth labels (circular for deployment) |
| **Deployment-time RF (condition + baseline)** | **0.907** | 9 features, no ground truth |
| Condition-only RF (no baseline run) | 0.564 | 7 features, barely above chance |

**Critical finding:** Two distinct deployment-time regimes:
1. **Condition config only:** AUC=0.564 — insufficient. `lever_num` dominates but provides
   limited discrimination without chain-level signal.
2. **Condition + baseline pre-screen:** AUC=0.907 — nearly matches the full-feature model.
   `flash_baseline_correct` is the top feature (0.327 importance), followed by `lever_num` (0.251).

**Mew implication:** Mew CANNOT predict detection success from condition configuration alone.
Mew CAN predict with high accuracy (85%+ precision) if a V1-minimal baseline pass is run on
each new chain first. The audit protocol should include a baseline pre-screen.

**Stop condition triggered:** AUC=0.907 effectively matches the full-feature model (gap=0.018).
Surface for both-author attention per pre-specified stop condition.

**Outputs:** `A1_deployment_predictor/deployment_predictor_analysis.md`, `results.json`

---

## Task A2: PUBG Anti-Detection Phase 2A (Marker Identification)

**Question:** P3 found 11 of 22 models showed anti-detection on PUBG specifically. What is the
specific marker causing this?

**Method:** Review PUBG chain construction from P3 analysis (which directly quotes
`violation_injector.py`) and G1 framework decomposition. Compare PUBG to other 4 domains.

**Source caveat:** The Ditto-5.1 codebase was analyzed in a prior session; this Phase 2A
relies on prior session outputs (P3 + G1 documents) rather than fresh code inspection.

**Candidate markers (ranked):**

1. **`eliminated_player` field in clean chains** (HIGH confidence) — The field is explicitly
   surfaced in the rendering to survive the 6-key context cap. Clean chains likely contain
   this field at the elimination event itself. Models may trigger YES on the marker's presence
   rather than on the sequence (marker + subsequent action).

2. **Rendering format amplifies the marker** (MEDIUM confidence) — Cannot confirm without
   direct code inspection; Phase 2B to verify.

3. **Temporal misreading of player status** (MEDIUM-LOW) — Models may misread active-then-eliminated
   sequence as a violation even without post-elimination action.

4. **6-key context cap creates symmetry** (LOW) — Does not explain PUBG-specific dominance.

**Phase 2B test modifications:**
- Modification A: Remove `eliminated_player` field from clean chains → expect FPR drop
- Modification B: Move marker to different position in violated chains
- Modification C: Replace `eliminated_player=<name>` with neutral field name

**Outputs:** `A2_pubg_artifact/phase_2a_marker_identification.md`

---

## Task A3: Self-Consistency Pre-Work

**Question:** Does majority voting (N=5 samples, T=0.7) on the best-performing CoT condition
(L18 L3) break the ~30% detection ceiling?

**Sample selection (seed=42):**
- 10 intact chains (L3_symbolic_checker=False)
- 10 violated chains (stratified: 1 causal_incoherence, 1 hp_resurrection, 1 monotone_increase,
  7 multiple)
- Same chains used for both baseline (T=0) and majority-vote (T=0.7 × 5 samples)

**Experiment configuration:**
- Primary: pro_L18_L3, T=0.7, N=5 samples, majority vote (YES if ≥3/5)
- Control: pro_L18_L3, T=0.0, single sample (OLAT baseline)
- Optional: pro_L18_L4 with same self-consistency setup

**Pre-registered outcomes:**
- Outcome 1 (gain >0.10): Detection ceiling is stochastic; methodology claim needs nuance
- Outcome 2 (gain <0.05): Ceiling is capability-limited; methodology claim is ironclad
- Outcome 3 (reduction): Unusual; investigate parse failure rates first

**Ready for tomorrow:** Chain IDs selected, API parameters specified, outcome interpretations
pre-registered.

**Outputs:** `A3_self_consistency/test_design.md`

---

## Task A4: Prompt Robustness Pre-Work

**Question:** Do the V1-minimal NO-floor and L18 L4 confabulation effects survive paraphrase
and formatting perturbations?

**Sample selection (seed=43):**
- 10 intact chains, 10 violated chains (different from A3 sample — orthogonal design)

**Prompt variants:**
- Variant 0 (control): Original OLAT prompt
- Variant 1 (light paraphrase): Semantically equivalent with different surface phrasing
- Variant 2 (alternative phrasing): Different question framing (consistency vs violation)
- Variant 3 (formatting perturbation): Bullet format instead of inline

**Test regimes:**
- V1-minimal (most important — tests NO-floor robustness)
- L18 L3 (tests CoT effect robustness)
- Optional: L18 L4 (tests confabulation robustness)

**Critical note for Variant 2:** Consistency framing ("YES if consistent, NO if broken") inverts
the label convention. Must apply semantic inversion when computing detection rates.

**Pre-registered outcomes:**
- Outcome 1: Effects persist across all variants → regime effects robust
- Outcome 2: Survive paraphrase, break under format → effects are language-level
- Outcome 3: Break under Variant 1 → wording-specific (significant, requires writeup revision)

**Ready for tomorrow:** Variant text specified, sample selected, parser notes documented.

**Outputs:** `A4_prompt_robustness/variant_design.md`

---

## Task A5: OLAT Documentation Audit and Errata Application

**Question:** Are the three errata identified in the Day 0 completion report correctly applied?

**Errata reviewed:**
1. SPEC §7.5: Lever 15 conditions (L2, L3) → corrected to (L1, L3)
2. BUILD_PLAN Tasks 3, 4, 5: arithmetic 68 × 50 × 2 = 6,800 → corrected to 64 × 50 = 3,200
3. Lever 5 L2/L3: Documentation of data-unavailability dropout

**Audit finding:** All three errata were applied as part of Amendment #6 (2026-05-13),
signed by both authors. Current SPEC.md SHA-256 matches the Amendment #6 locked hash:
`dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8`

**Additional findings:**
- `artifacts/plumbing_schemas.md` has stale `first_token` in enum (should be `md_strip` /
  `last_token`). Documentation fix only; implementation is correct. Flagged for next review.
- Amendment #7 signoff rows in `signoff/signoff_block.md` are unsigned — both authors need
  to sign before Amendment #7 findings are integrated into primary tables.

**No methodology changes required.** The errata log serves as the audit confirmation record.

**Outputs:** `A5_errata/errata_log.md`

---

## Feeds Into Part B

| Part A output | Feeds into Part B task |
|---------------|----------------------|
| A1: deployment-time predictor results | Part B wrap-up synthesis §7 |
| A2: PUBG marker identification | B2: PUBG anti-detection reproduction test |
| A3: 20-chain sample + experiment design | B1.5: Self-consistency baseline API run |
| A4: Variant design + 20-chain sample | B1.7: Prompt robustness test API run |
| A5: Errata log + hash verification | B wrap-up synthesis §1 methodology provenance |

---

## Posture

All findings are pre-specified. No retroactive reclassification. Both-author signoff required
before integrating findings into primary OLAT results. Null findings are documented honestly.

The A1 stop condition (AUC effectively matches full model) has been surfaced and should be
reviewed by both authors. The A2 marker identification is provisional pending Phase 2B
confirmation.
