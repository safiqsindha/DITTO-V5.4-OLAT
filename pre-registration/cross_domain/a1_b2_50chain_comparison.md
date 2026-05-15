# A1 vs B2 — 50-Chain Baseline Comparison

**Generated:** 2026-05-15  
**Corpus:** 50 unique chain_ids (baseline condition, `lever_varied=None`, all `deepseek-v4-flash` model)  
**Ground truth field:** `L3_symbolic_checker` from `ground_truth` dict  
**Checkers:** A1 (`A1_sonnet_no_internet/checker.py`) vs B2 (`B2_sonnet_internet/checker.py`)

---

## Section 1: Performance Summary Table

| Metric | A1 (no-internet) | B2 (internet) |
|--------|----------------:|-------------:|
| N total | 50 | 50 |
| GT=YES (violated) | 32 | 32 |
| GT=NO (intact) | 18 | 18 |
| True Positives | 25 | 26 |
| True Negatives | 18 | 18 |
| False Positives | 0 | 0 |
| False Negatives | 7 | 6 |
| Precision | 1.000 | 1.000 |
| Recall | 0.781 (25/32) | 0.812 (26/32) |
| F1 | 0.877 | 0.897 |
| Accuracy | 0.860 (43/50) | 0.880 (44/50) |

Both checkers have perfect precision (zero false positives across 18 intact chains). B2 gains one
additional true positive over A1, raising recall from 0.781 to 0.812 and F1 from 0.877 to 0.897.

---

## Section 2: Agreement Matrix

| Agreement case | Count | Chain IDs |
|---|---:|---|
| Both correct | 43 | — (majority; all 18 intact chains + 25 violated chains) |
| A1 only correct | 0 | — |
| B2 only correct | 1 | `gen9ou-2310254076_p2_shuffled_42` |
| Both wrong | 6 | see below |

**Both-wrong chains (GT=YES, both checkers output NO):**

| chain_id | violation_type | A1 | B2 |
|---|---|---|---|
| gen9ou-2275367426_p2_shuffled_1337 | hp_resurrection | NO | NO |
| gen9ou-2283533709_p2_shuffled_1337 | multiple | NO | NO |
| gen9ou-2287639343_p2_shuffled_1337 | hp_resurrection | NO | NO |
| gen9ou-2306146403_p1_shuffled_1337 | multiple | NO | NO |
| gen9ou-2306563046_p2_shuffled_1337 | multiple | NO | NO |
| gen9ou-2334711641_p2_shuffled_7919 | causal_incoherence | NO | NO |

Notes on each missed chain:

- **gen9ou-2275367426** (`hp_resurrection`): `unit_B` goes UNAVAILABLE with `recover_in=0` (not `permanent`) in step 7, then `hp_unit_B` drops to 0% in step 15. The violation the symbolic checker annotated requires detecting that a non-zero HP unit transitions to UNAVAILABLE without being marked `permanent` — a pattern neither checker implements.
- **gen9ou-2283533709** (`multiple`): `trigger=own_faint` fires at step 7 and `unit_C` is marked UNAVAILABLE(`permanent`) at step 9 — i.e., the permanent record exists, so B2's `own_faint_no_perm` rule does not trigger. The remaining violations involve causal ordering (faint trigger precedes the corresponding permanent event by two steps within the same turn), a pattern not encoded in either checker.
- **gen9ou-2287639343** (`hp_resurrection`): `unit_A` UNAVAILABLE(`recover_in=0`) at step 2, then AVAILABLE at step 14 — recovery without the `permanent→revived` path; `hp_unit_C` sequence is 100%→0%→0% (monotone, no resurrection). Neither checker detects non-permanent UNAVAILABLE→AVAILABLE transitions as violations.
- **gen9ou-2306146403** (`multiple`): `unit_C` becomes UNAVAILABLE at step indices 1 and 6 (step numbers 2 and 7) without an AVAILABLE between — a `rapid_double_unavailable` gap. Both checkers' threshold `(step_idx - prev_idx) <= 2` is exceeded (diff = 5), so the rule does not fire.
- **gen9ou-2306563046** (`multiple`): `unit_A` UNAVAILABLE at step indices 1 and 9 (step numbers 2 and 10) without AVAILABLE between — same gap as above (diff = 8).
- **gen9ou-2334711641** (`causal_incoherence`): `unit_A` UNAVAILABLE(`recover_in=0`) at step 1, then `hp_unit_A at 75.0%` appears at step 12. Neither checker checks for positive HP on a unit currently in a non-permanent UNAVAILABLE state.

---

## Section 3: B2 Unique Detections (B2=YES, A1=NO, GT=YES)

**Count: 1 chain**

### gen9ou-2310254076_p2_shuffled_42 (violation_type: multiple)

**B2 triggered rules:** `['causal_incoherence']` via `_check_own_faint_no_perm`  
**A1 triggered rules:** `[]`

**Mechanism:** Step 10 (turn=8) contains `SubGoalTransition: … (trigger=own_faint)`. This records that a player's own unit fainted. B2's `_check_own_faint_no_perm` rule (internet-confirmed) asserts that a faint trigger must be accompanied by a `ToolAvailability … UNAVAILABLE (permanent)` event anywhere in the chain. In this chain, the only `ToolAvailability` events are `unit_D UNAVAILABLE (recover_in=0)` at step 3 and `unit_C AVAILABLE` at step 8 — no permanent unavailability record exists. B2 therefore correctly flags this as causal incoherence.

A1 has no `own_faint_no_perm` rule and cannot detect this pattern.

**Chain evidence:**
```
Step 7  (turn=8): ResourceBudget: hp_unit_B at 0.0%          ← unit_B HP reaches zero
Step 10 (turn=8): SubGoalTransition: … (trigger=own_faint)   ← faint trigger fires
[no UNAVAILABLE(permanent) event anywhere in the 15-step chain]
```

---

## Section 4: A1 Unique Detections (A1=YES, B2=NO) — Including FP Analysis

**Count: 0 chains**

There are no chains where A1 is correct and B2 is not. A1 never makes a detection that B2 fails to also make. This is consistent with B2 being a strict superset of A1's detection capability on this corpus: every rule A1 fires, B2 also fires (or fires a co-equal rule), plus B2 has the additional `own_faint_no_perm` rule.

**False positive analysis:** Both checkers produce zero false positives across all 18 intact chains (GT=NO). Neither B2's generalized monotone rule nor its `own_faint_no_perm` rule triggered spuriously on any clean chain.

---

## Section 5: Cross-Rule Analysis — Which B2 Improvements Produced Real New Detections?

### B2 architectural improvement 1: Generalized monotone rule (`_check_monotone_decrease`)

A1's `_check_pp_monotone` only checks resources named `pp_action_*`. B2 generalizes to any resource annotated `decay=monotone_decrease` (e.g., `match_time_remaining`).

**Result on this corpus: 0 new detections.** All monotone violations present in the 50 baseline chains involved `pp_action_*` resources, which A1's rule already covers. B2's generalized rule and A1's narrow rule triggered on identical chains for monotone violations:

| chain_id | A1 monotone rule | B2 monotone rule |
|---|---|---|
| gen9ou-2261012168_p1_shuffled_7919 | `pp_monotone_violation` | `pp_monotone_violation` |
| gen9ou-2270600845_p1_shuffled_7919 | `pp_monotone_violation` | `pp_monotone_violation` |
| gen9ou-2272010071_p2_shuffled_7919 | `pp_monotone_violation` | `pp_monotone_violation` |
| gen9ou-2320109494_p1_shuffled_1337 | `pp_monotone_violation` | `pp_monotone_violation` |
| gen9ou-2353740572_p1_shuffled_42 | `pp_monotone_violation` | `pp_monotone_violation` |

No non-pp_action monotone violations appear in any of the 50 baseline chains.

### B2 architectural improvement 2: `own_faint_no_perm` consistency rule

**Result: 1 new detection** (`gen9ou-2310254076_p2_shuffled_42`, GT=YES). This is the sole source of B2's recall advantage. The rule encodes the internet-confirmed invariant that a `trigger=own_faint` SubGoalTransition must be accompanied by a `UNAVAILABLE(permanent)` ToolAvailability event. A1 does not implement this rule.

### Rule co-firing patterns (correct TP chains where A1 and B2 differ in rules fired)

Three additional chains show B2 firing `causal_incoherence` in addition to a rule A1 also fires — but both checkers already reached the correct YES verdict, so these are not new detections:

| chain_id | A1 rules | B2 rules |
|---|---|---|
| gen9ou-2260297169_p2_shuffled_1337 | `hp_resurrection` | `hp_resurrection`, `causal_incoherence` |
| gen9ou-2272010071_p2_shuffled_7919 | `pp_monotone_violation` | `pp_monotone_violation`, `causal_incoherence` |
| gen9ou-2272363626_p2_shuffled_7919 | `hp_resurrection` | `hp_resurrection`, `causal_incoherence` |

B2 detects additional incoherence signals in these chains, but they do not affect the correctness outcome.

---

## Section 6: Implication for Internet Contribution Claim

### Summary

On the 50-chain baseline corpus, B2's internet-informed improvements yield:

- **1 additional true positive** (recall +0.031, F1 +0.020) from the `own_faint_no_perm` rule
- **0 additional true positives** from the generalized monotone rule
- **0 false positives** introduced by either improvement

### Interpretation

The internet contribution claim rests on a small but genuine empirical foundation. B2 correctly detects one chain that A1 cannot, and the improvement is cleanly attributable to a single internet-confirmed rule (`_check_own_faint_no_perm`). The rule's premise — that a `trigger=own_faint` event without a corresponding `UNAVAILABLE(permanent)` record is causally incoherent — is valid and produces no spurious detections on intact chains.

However, the overall magnitude of the improvement is modest:
- The recall gap is 1/32 = 3.1 percentage points.
- The generalized monotone rule (B2's other architectural addition) produces no new detections on this corpus, because no baseline chain contained a non-`pp_action` monotone violation.
- Six chains remain missed by both checkers, representing shared gaps in detection coverage: non-permanent fainted units with positive HP, double-UNAVAILABLE events outside the 2-step window, and causal ordering violations that neither checker's rule set encodes.

### Shared gap patterns (neither checker detects these)

| Gap pattern | Missed chains | Count |
|---|---|---|
| Non-permanent UNAVAILABLE unit with positive HP (later) | gen9ou-2334711641 | 1 |
| Non-permanent UNAVAILABLE→UNAVAILABLE outside 2-step window | gen9ou-2306146403, gen9ou-2306563046 | 2 |
| Non-permanent UNAVAILABLE→AVAILABLE (faint without permanent marking) | gen9ou-2275367426, gen9ou-2287639343 | 2 |
| Causal ordering / semantic shuffle (no symbolic signal in text) | gen9ou-2283533709 | 1 |

### Conclusion

B2's internet research produces a real but small improvement over A1 on the full 50-chain corpus: +1 true positive, same false positive rate. The improvement is entirely attributable to the `own_faint_no_perm` rule, not the generalized monotone rule. The dominant remaining failure mode — shared by both checkers — is the inability to detect violations involving non-permanent unit unavailability and violations whose symbolic signals are spread across more than 2 steps without the specific trigger patterns the checkers implement.

---

## Appendix: Full Per-Chain Results

| chain_id | GT | vtype | A1 | B2 | A1 rules | B2 rules |
|---|---|---|---|---|---|---|
| gen9ou-2260297169_p2_shuffled_1337 | YES | hp_resurrection | YES | YES | hp_resurrection | hp_resurrection, causal_incoherence |
| gen9ou-2261012168_p1_shuffled_7919 | YES | causal_incoherence | YES | YES | pp_monotone_violation | pp_monotone_violation |
| gen9ou-2262855067_p1 | NO | none | NO | NO | — | — |
| gen9ou-2270600845_p1_shuffled_7919 | YES | monotone_increase | YES | YES | pp_monotone_violation, causal_incoherence | pp_monotone_violation, causal_incoherence |
| gen9ou-2272010071_p2_shuffled_7919 | YES | multiple | YES | YES | pp_monotone_violation | pp_monotone_violation, causal_incoherence |
| gen9ou-2272252150_p1_shuffled_1337 | YES | multiple | YES | YES | causal_incoherence | causal_incoherence |
| gen9ou-2272363626_p2_shuffled_7919 | YES | multiple | YES | YES | hp_resurrection | hp_resurrection, causal_incoherence |
| gen9ou-2272614714_p1 | NO | none | NO | NO | — | — |
| gen9ou-2272614714_p1_shuffled_1337 | YES | multiple | YES | YES | hp_resurrection | hp_resurrection |
| gen9ou-2273536349_p1 | NO | none | NO | NO | — | — |
| gen9ou-2275367426_p2_shuffled_1337 | YES | hp_resurrection | **NO** | **NO** | — | — |
| gen9ou-2276761872_p1 | NO | none | NO | NO | — | — |
| gen9ou-2278300586_p1 | NO | none | NO | NO | — | — |
| gen9ou-2278537373_p1_shuffled_7919 | YES | multiple | YES | YES | hp_resurrection ×2 | hp_resurrection |
| gen9ou-2283533709_p2_shuffled_1337 | YES | multiple | **NO** | **NO** | — | — |
| gen9ou-2286522581_p1_shuffled_1337 | NO | none | NO | NO | — | — |
| gen9ou-2287639343_p2_shuffled_1337 | YES | hp_resurrection | **NO** | **NO** | — | — |
| gen9ou-2287788376_p1_shuffled_42 | YES | multiple | YES | YES | hp_resurrection, causal_incoherence | hp_resurrection, causal_incoherence |
| gen9ou-2287824764_p1 | NO | none | NO | NO | — | — |
| gen9ou-2291273479_p2_shuffled_1337 | YES | multiple | YES | YES | hp_resurrection, causal_incoherence | hp_resurrection, causal_incoherence |
| gen9ou-2301379516_p1_shuffled_42 | NO | none | NO | NO | — | — |
| gen9ou-2301944495_p1_shuffled_42 | YES | multiple | YES | YES | causal_incoherence | causal_incoherence |
| gen9ou-2303002268_p2_shuffled_7919 | YES | hp_resurrection | YES | YES | hp_resurrection | hp_resurrection |
| gen9ou-2306146403_p1_shuffled_1337 | YES | multiple | **NO** | **NO** | — | — |
| gen9ou-2306563046_p2_shuffled_1337 | YES | multiple | **NO** | **NO** | — | — |
| gen9ou-2310254076_p2_shuffled_42 | YES | multiple | **NO** | **YES** | — | causal_incoherence |
| gen9ou-2310556760_p1_shuffled_7919 | YES | multiple | YES | YES | causal_incoherence | causal_incoherence |
| gen9ou-2312002915_p2 | NO | none | NO | NO | — | — |
| gen9ou-2317659387_p2 | NO | none | NO | NO | — | — |
| gen9ou-2320109494_p1_shuffled_1337 | YES | monotone_increase | YES | YES | pp_monotone_violation | pp_monotone_violation |
| gen9ou-2320688421_p1_shuffled_42 | YES | causal_incoherence | YES | YES | causal_incoherence | causal_incoherence |
| gen9ou-2320790123_p1_shuffled_1337 | YES | multiple | YES | YES | causal_incoherence | causal_incoherence |
| gen9ou-2321486759_p2 | NO | none | NO | NO | — | — |
| gen9ou-2321922786_p1 | NO | none | NO | NO | — | — |
| gen9ou-2323855766_p2 | NO | none | NO | NO | — | — |
| gen9ou-2326066086_p2_shuffled_42 | YES | multiple | YES | YES | hp_resurrection ×2, causal_incoherence | hp_resurrection, causal_incoherence |
| gen9ou-2327278602_p2 | NO | none | NO | NO | — | — |
| gen9ou-2327376263_p1 | NO | none | NO | NO | — | — |
| gen9ou-2328038098_p2_shuffled_1337 | YES | multiple | YES | YES | hp_resurrection | hp_resurrection |
| gen9ou-2330862666_p2 | NO | none | NO | NO | — | — |
| gen9ou-2334711641_p2_shuffled_7919 | YES | causal_incoherence | **NO** | **NO** | — | — |
| gen9ou-2338779384_p1 | NO | none | NO | NO | — | — |
| gen9ou-2341946701_p1_shuffled_1337 | YES | multiple | YES | YES | hp_resurrection | hp_resurrection |
| gen9ou-2343591826_p1_shuffled_1337 | YES | multiple | YES | YES | hp_resurrection | hp_resurrection |
| gen9ou-2343602002_p1_shuffled_7919 | YES | multiple | YES | YES | hp_resurrection ×2, causal_incoherence | hp_resurrection, causal_incoherence |
| gen9ou-2345018884_p1_shuffled_7919 | YES | multiple | YES | YES | hp_resurrection ×2 | hp_resurrection |
| gen9ou-2347015993_p1_shuffled_1337 | YES | multiple | YES | YES | hp_resurrection | hp_resurrection |
| gen9ou-2348078225_p1 | NO | none | NO | NO | — | — |
| gen9ou-2353740572_p1_shuffled_42 | YES | multiple | YES | YES | pp_monotone_violation | pp_monotone_violation |
| gen9ou-2354144810_p2_shuffled_7919 | YES | multiple | YES | YES | hp_resurrection ×2, causal_incoherence | hp_resurrection, causal_incoherence |

Bold **NO** / **YES** cells indicate non-agreement with ground truth. The single bold **YES** in the B2 column for `gen9ou-2310254076` is B2's unique correct detection.
