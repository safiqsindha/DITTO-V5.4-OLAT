# Task 2: dr_intact / dr_violated Convention and Degenerate Condition Clarification

**SPEC hash:** `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8`  
**Generated:** 2026-05-13

---

## 1. Definitional Convention

The Day 2 outputs use **Convention B** throughout:

- **`dr_violated`** = fraction of violated chains where the model said **YES** (true-positive rate)
- **`dr_intact`** = fraction of intact chains where the model said **YES** (false-positive rate)
- **`gap`** = `dr_violated − dr_intact`

This is the SPEC §4 primary estimand: `gap = detection_rate(violated) − detection_rate(intact)`. Under Convention B, a positive gap means the model flags violated chains more than intact chains — the expected direction if the model detects violations. Convention A (dr_intact = "rate of correct intact classification" = rate of NO on intact) is the complement: Convention A's dr_intact = 1 − Convention B's dr_intact.

The gap formula is the same under both conventions (the 1's cancel), but the detection-rate columns themselves differ. **Day 2 CSVs use Convention B (YES-rate on each group).**

A perfect detector has `dr_violated = 1.0, dr_intact = 0.0, gap = 1.0`.  
A floor model (always NO) has `dr_violated = 0.0, dr_intact = 0.0, gap = 0.0`.  
An anti-detection model (always YES on intact, always NO on violated) has `dr_violated = 0.0, dr_intact = 1.0, gap = -1.0`.

---

## 2. Four Degenerate Pro Conditions — Response Distributions

The four conditions flagged as `degenerate_variance=True` in the Day 2 effect tables are:  
`pro_L15_L1`, `pro_L15_L3`, `pro_L16_L2`, `pro_L16_L3`

Ground truth labels are per Universe L3 (symbolic checker). Intact = n=18 chains; Violated = n=32 chains (for these conditions after parse filtering).

### pro_L15_L1 (Lever 15 L1 — numeric 1-10 probability scale, Pro model)

| Group | n | YES | NO | Unparseable | API fail |
|---|---|---|---|---|---|
| Intact (symbolic checker) | 18 | 0 | 18 | 0 | 0 |
| Violated (symbolic checker) | 32 | 0 | 31 | 1 | 0 |

**Pattern: FLOOR** — model said NO to all parseable responses across both intact and violated chains. One violated chain produced unparseable output.

### pro_L15_L3 (Lever 15 L3 — numeric 0-100 probability scale, Pro model)

| Group | n | YES | NO | Unparseable | API fail |
|---|---|---|---|---|---|
| Intact | 18 | 0 | 15 | 3 | 0 |
| Violated | 32 | 0 | 29 | 3 | 0 |

**Pattern: FLOOR** — all parseable responses were NO. 6 total unparseable responses (model output prose without a numeric value or YES/NO).

### pro_L16_L2 (Lever 16 L2 — role framing L2, Pro model)

| Group | n | YES | NO | Unparseable | API fail |
|---|---|---|---|---|---|
| Intact | 18 | 0 | 17 | 1 | 0 |
| Violated | 32 | 0 | 29 | 3 | 0 |

**Pattern: FLOOR** — all parseable responses were NO. 4 total unparseable.

### pro_L16_L3 (Lever 16 L3 — role framing L3, Pro model)

| Group | n | YES | NO | Unparseable | API fail |
|---|---|---|---|---|---|
| Intact | 18 | 0 | 17 | 1 | 0 |
| Violated | 32 | 0 | 27 | 5 | 0 |

**Pattern: FLOOR** — all parseable responses were NO. 6 total unparseable.

---

## 3. Classification

All four conditions are **Floor pattern**: the Pro model produced 0% YES response on both intact and violated chains under these lever conditions. This is the expected V1-minimal floor behavior — the same floor observed in Day −2 verification (V4-Flash gap = −1.000, V4-Pro gap = −0.757). These conditions failed to move the Pro model off the floor.

**Not** anti-detection pattern: anti-detection requires YES on intact and NO on violated (dr_intact > dr_violated, gap < 0). None of the four conditions show any YES responses at all.

---

## 4. Interpretation of the effect_size = 0.0799 Artifact

All four conditions show `effect_size = 0.0799` in the CSV despite `gap = 0.0`. This is a computational artifact:

`effect_size = gap(condition) − gap(baseline)`

The Pro baseline (`pro_baseline`) has `gap = -0.0799` (i.e., the baseline model says YES slightly more often on intact chains than violated chains — a mild negative gap from the Day −2 verification data showing Pro responds to ~13% of prompts with YES, more on intact than violated at baseline). The condition gap is exactly 0.0. Therefore:

`effect_size = 0.0 − (−0.0799) = 0.0799`

This is not a real signal. It means: "these lever conditions produced the same floor behavior as not applying any lever at all." The 0.0799 value reflects only baseline gap variability, not lever-induced movement. The `degenerate_variance=True` flag and `Directional(no_CI)` classification correctly mark these as computational artifacts rather than findings.

---

## 5. Appropriate Classification

The `Directional(no_CI)` label is a reasonable flag under the pre-registered classification rules (Amendment #4 C5):
- |effect_size| = 0.0799 is in the Directional range (0.03–0.10)
- BCa CI is unavailable because the bootstrap distribution is degenerate (all bootstrap gap samples for the condition = 0.0, making z0 = ppf(0) = −∞)
- The `degenerate_variance=True` flag marks this as a computational edge case

Per SPEC §9.0: "degenerate variance (all-NO or all-YES): bootstrap CI=[point, point], flag `degenerate_variance=true`." These conditions satisfy that criterion.

**Recommended interpretation for both-author review:** These four conditions confirm that Levers 15 and 16 (numeric probability scale and role framing) did not move the Pro model off the NO-floor. The effect_size = 0.0799 is a baseline subtraction artifact, not a lever effect. No amendment or reclassification is needed; the `degenerate_variance` flag provides the correct documentation.
