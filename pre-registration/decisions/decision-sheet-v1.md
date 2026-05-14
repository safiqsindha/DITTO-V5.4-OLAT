# Project Ditto OLAT — Both-Author Decision Sheet

**Purpose:** Resolve 5 open items requiring author input before pre-registration sign-off.
**Date prepared:** 2026-05-11
**Date resolved:** 2026-05-11
**Status:** ALL 5 ITEMS RESOLVED. Both-author signoff captured on this sheet. Resolutions applied to SPEC.md, artifacts, and BUILD_PLAN.md.

**SPEC hash before this sheet was applied:** `e7ba04e936ffe9b241d9b2375cb0a9efd1f7ef43b1adb0788da83f05215dc967`
**SPEC hash after this sheet was applied:** `4e18dab20be70f08a0bb528a56aa894bfd9a76095ce5450d5bbf408cfc187ff2`

## Final Resolutions Summary

| Item | Resolution |
|---|---|
| O3 | ACCEPTED with addendum: 8 abstractions split into 6 rule-bearing + 2 dimensional-only. Documented as feature, not defect. |
| O5 | ACCEPTED Interpretation A: Lever 18 testing implicitly holds Lever 15 at L2. Lever 15 L1 historical-framing footnote added. |
| O6 | ACCEPTED with one modification: S2/S4/S5 as drafted. S3 tightened from 0.20 to 0.05. |
| O7 | ACCEPTED Option A with explicit Day -3 chain pool check added to BUILD_PLAN.md. |
| O8 | REJECTED draft "L2 closing, L3 opening" — replaced with parallel L2/L3 user-turn opening to avoid position × content confound. |

**Author 1 signoff (all 5 items):** Safiq Sindha — 2026-05-11
**Author 2 signoff (all 5 items):** Myriam Sindha — 2026-05-11

**Item added after integration review (O2 conceptual coverage check, 2026-05-11):** Resolved 2026-05-12 via Amendment #1 to the pre-registration. **Option A** chosen — L1 expanded from 7 to 10 fields (added `recover_in`, `from_phase`, `to_phase`). L1 now covers all 9 active symbolic checker rules. See `signoff/signoff_block.md` Amendment Log. Full O2 detail retained in the "O2 — L1 Field Coverage Gaps" section at end of this sheet for historical record.

---

Each item below has the question, the evidence gathered, the resolution applied, and the both-author signoff captured.

---

## O3 — The 8 Abstraction Names

**Question:** What are the 8 abstraction dimensions used in Lever 12 (schema) and Lever 13 (taxonomy)?

**Evidence:**
- `translation.py` defines 6 event types: ResourceBudget, ToolAvailability, SubGoalTransition, InformationState, CoordinationDependency, OptimizationCriterion.
- `pokemon_rule_checker.py` EC-07 states CoordinationDependency and OptimizationCriterion have no violation rules.
- ResourceBudget carries 5 distinct resource sub-types: HP, PP, time, status, boost.
- The handoff says "8 abstractions" — never enumerated.

**Suggested resolution:**
The 8 are the violation-relevant resource categories:
1. ResourceBudget_HP
2. ResourceBudget_PP
3. ResourceBudget_time
4. ResourceBudget_status
5. ResourceBudget_boost
6. ToolAvailability
7. SubGoalTransition
8. InformationState

CoordinationDependency and OptimizationCriterion are excluded (EC-07: no rules apply).

**Caveat:** ResourceBudget_status and ResourceBudget_boost have `decay="none"` and are NOT covered by R1.

**Decision:** [x] Accept with documentation addendum (caveat reframed as feature)

**Addendum applied to SPEC:** Six of the eight abstractions are rule-bearing (ResourceBudget_HP, ResourceBudget_PP, ResourceBudget_time, ToolAvailability, SubGoalTransition, InformationState). Two are dimensional-only (ResourceBudget_status, ResourceBudget_boost). They appear in the schema for completeness of the abstraction space; they will not generate violation events in the test set; Lever 13 L2 naturally excludes them under either selection criterion. Documented feature, not defect.

**Author 1:** Safiq Sindha — 2026-05-11    **Author 2:** Myriam Sindha — 2026-05-11

---

## O5 — Lever 15 Framing for Lever 18 Testing

**Question:** When testing Lever 18 (CoT elicitation), is the global baseline Lever 15 (L1 = consistency rating 1–10) implicitly overridden to L2 (YES/NO violation detection)?

**Evidence:**
- Lever 18's locked output anchor is "The answer is YES/NO" — incompatible with a 1–10 rating.
- `Ditto V5.0/src/harness/prompts.py` `_CLASSIFY_QUESTION` confirms v5 used YES/NO violation detection framing, not a 1–10 rating.
- V1 (Ditto V1) used next-action prediction, not consistency rating — so "V1 baseline = consistency rating" is a pre-D-42 pilot framing that was never the production task.
- No v5.x version used a 1–10 scale.

**Suggested resolution (Interpretation A):**
Lever 15 is implicitly overridden to L2 (YES/NO violation detection: "Does this chain contain any rule violations?") whenever Lever 18 is the lever being tested. Documented as a Lever 18-specific baseline modification. The consistency-rating L1 is preserved as a level only when Lever 15 itself is the lever under test.

**Decision:** [x] Accept Interpretation A (option A1)

Lever 18 is preserved as a YES/NO-anchored lever; Lever 15 is implicitly held at L2 whenever Lever 18 is being tested. Lever 15 L1 (consistency rating) is preserved as a level only when Lever 15 is the lever under test. Historical-framing footnote added to SPEC Lever 15 section.

**Author 1:** Safiq Sindha — 2026-05-11    **Author 2:** Myriam Sindha — 2026-05-11

---

## O6 — Pre-OLAT Verification Pause Thresholds (S2–S5)

**Question:** What thresholds trigger a pause during the n=250 verification run?

**Current locked thresholds (from handoff):**
- S1: gap > +0.05 → PAUSE (unexpected positive signal)
- S6: detection on violated ≥ 0.80 AND gap ≥ 0.10 → PAUSE (V4-Flash organic competence)

**Suggested DRAFT thresholds for S2–S5:**

| Scenario | Threshold | Rationale |
|---|---|---|
| S2 Anti-detection | gap < −0.05 | Mirror of S1; symmetric tolerance for negative signal. |
| S3 Parse failure | parse_failure_rate > 0.20 | More than 50/250 unparseable means cascade is fragile for OLAT stress tests. |
| S4 Incomplete run | n_valid < 200 | 80% of attempted; below this, bootstrap CI too wide for reliable baseline (±5–7 pp at p≈0.5). |
| S5 Degenerate output | YES_rate > 0.95 OR NO_rate > 0.95 | Anchor dominance — would make all OLAT effects uninterpretable. |

**Decision:** [x] Accept S2, S4, S5 as drafted. **Modify S3:** tighten from 0.20 to 0.05.

**S3 modification rationale:** V1 is the simplest condition in the OLAT matrix. >5% parse failures on V1-on-V4-Flash indicates parser fragility that will compound under OLAT stress conditions. The 0.20 threshold describes catastrophic breakage; 0.05 is the appropriate "good enough for OLAT" gate.

**Author 1:** Safiq Sindha — 2026-05-11    **Author 2:** Myriam Sindha — 2026-05-11

---

## O7 — Paralysis Violation Framing in Lever 16

**Question:** How should Lever 16 L2/L3 handle paralysis, given it's probabilistic (25% chance of failing to act), not deterministic?

**Evidence:**
- Sleep and freeze are deterministic (act ≈ 0% while afflicted, with rare exceptions like Sleep Talk/Snore).
- Paralysis is probabilistic — a paralyzed unit can still act ~75% of the time legally.
- If "acted while paralyzed" is treated as a violation, the symbolic checker would produce false positives ~75% of the time on legitimate paralyzed-but-acting events.

**Three options:**

- **Option A (recommended):** Omit paralysis from L3 entirely. L2's text already hedges with "may be prevented from acting." No RULE_PARA in L3. If paralysis violations appear in the OLAT test set, they're either (a) not in the symbolic checker's rule set or (b) framed as "the move FAILED due to paralysis was rendered but should not have been" — narrow and rare. Treat as out-of-scope for this OLAT.

- **Option B:** Add RULE_PARA defined narrowly: "If status = paralysis and the chain renders a move-execution event marked as 'fully_paralyzed_failure', a subsequent successful move on the same turn is a violation." Requires the chain renderer to emit a paralysis-failure marker. Likely not present in current v5.1 chains.

- **Option C:** Drop paralysis mention from L2 entirely. Removes confound but reduces L2 ↔ L3 equivalence on a status category.

**Suggested resolution:** Option A. Leave L2's hedged wording, omit RULE_PARA from L3, document that paralysis-acted events are not classified as violations under either level. Confirm OLAT test set does not contain paralysis-only violations.

**Decision:** [x] A (omit from L3) **with explicit Day -3 chain pool check.**

**Day -3 confirmation step:** Filter v5.1 test set for chains where the only planted violation is paralysis. If count > 0, both authors choose between Option 1 (exclude — default) and Option 2 (retain with documented limitation — only if excluding drops violated set below ~50%). Both authors sign exclusion decision before Day -2. Step added to SPEC.md Section 17 and BUILD_PLAN.md.

**Author 1:** Safiq Sindha — 2026-05-11    **Author 2:** Myriam Sindha — 2026-05-11

---

## O8 — Lever 19 L2 Placement (System Prompt vs User Turn)

**Question:** Should Lever 19 L2 grounding instruction ("Base your answer on the events shown in the chain.") go in the system prompt or the user turn?

**Evidence:**
- L3 (adversarial framing) is already locked to user turn, opening sentence(s), before the chain.
- Consistency requires L2 and L3 to share placement so the manipulation is purely textual, not positional.
- V1 codebase places task-specific instructions in the user turn; the system prompt is reserved for high-level role framing.

**Suggested resolution:**
User turn, **final sentence after the chain and before the question.** This way L2 reads as a closing reminder ("…events shown above. Base your answer on the events shown in the chain. Does this chain contain any rule violations?"). L3 stays at user-turn opening as locked. Placement is consistent at the user-turn level, differing only in opening-vs-closing position, which is a deliberate design choice (L2 = reminder, L3 = framing prelude).

**Alternative:** Both L2 and L3 at user-turn opening (parallel placement). Cleaner but L2 reads less naturally there.

**Decision:** [x] L2 opening (parallel to L3) — **rejecting the original "L2 closing" recommendation.**

**Rejection rationale:** The drafted recommendation creates a position × content confound. Lever 19 L2 vs L3 would differ in both text content (grounding reminder vs adversarial framing) AND position (closing vs opening). The whole point of OLAT is isolating single-variable effects. The "L2 reads more naturally as a closing reminder" rationale is subjective and doesn't justify confounding the lever's effect size with position. Naturalness cost at user-turn opening is accepted as a deliberate design tradeoff.

**Author 1:** Safiq Sindha — 2026-05-11    **Author 2:** Myriam Sindha — 2026-05-11

---

## Sign-Off Summary

All 5 items resolved 2026-05-11. Both-author signoff captured per-item above.

**Application status:**

1. [x] Resolutions applied to relevant artifacts and SPEC.md (2026-05-11)
2. [x] SPEC SHA-256 recomputed — see `signoff/signoff_block.md`
3. [x] `signoff/signoff_block.md` updated with new hash
4. [ ] Run O4 (DeepSeek `/beta` schema acceptance test) — see `.env` setup
5. [ ] Sign `signoff/signoff_block.md` — both authors final signoff on locked pre-registration
6. O9 (Lever 13 top-3 selection) executes at Day 0; no sign-off blocker.

**Decisions complete (both authors):** 2026-05-11 (5 original items). One additional item (O2) surfaced during integration review — see below.

---

## O2 — L1 Field Coverage Gaps (surfaced 2026-05-11 during integration review)

**Question:** Does the current L1 minimal field set (7 fields: type, timestamp, resource, amount, decay, tool, state) cover all symbolic checker rules?

**Coverage check result (per `artifacts/lever_01_field_schemas.md` O2 section):**

| Rule | Status under L1 (7 fields) |
|---|---|
| R1 — monotone_increase | ✅ Detectable |
| R2 — dead_unit_returns | ❌ Needs `recover_in` |
| R3 — hp_resurrection | ✅ Detectable |
| R4 — faint_no_permanence | ❌ Needs `recover_in` |
| R6 — double_availability | ✅ Detectable |
| R8 — available_while_zeroed | ✅ Detectable |
| R9 — positive_hp_perm_faint | ❌ Needs `recover_in` |
| R10 — hp_zero_temp_switch | ❌ Needs `recover_in` |
| R11 — initial_phase_reentry | ❌ Needs `from_phase`, `to_phase`, `trigger` |

**Net impact under current L1:** 5 of 9 rules cannot fire. Violation-type strings `dead_unit_returns`, `faint_no_permanence`, and `causal_incoherence` (both R10 and R11 variants) would never be reported, regardless of whether those violations are objectively present in the chain. This makes L1 vs L2 vs L3 detection-rate gaps difficult to interpret if the test set contains chains with these violation types.

**Decision options for both authors:**

- **Option A — Expand L1 to 10 fields:** Add `recover_in`, `from_phase`, `to_phase` (and `trigger` is redundant once from/to are present — R11 only needs from_phase to detect the violation; trigger is informational). Result: L1 covers all 9 rules. Cost: L1 is no longer the strict "minimal" schema; the L1→L2 step shrinks (10→18 fields rather than 7→18).
- **Option B — Expand L1 to 8 fields:** Add `recover_in` only. Result: L1 covers R1, R2, R3, R4, R6, R8, R9, R10 — i.e., 8 of 9 rules. R11 (initial-phase re-entry) remains undetectable under L1. Cost: documented limitation that R11-type violations are invisible to L1; sensitivity check at analysis time excludes R11-classified chains.
- **Option C — Keep L1 at 7 fields:** No change. Document as known limitation that L1 cannot detect R2, R4, R9, R10, R11. The Lever 1 effect-size measurement compares L1's detection rate (which sees only R1/R3/R6/R8 violations) against L2/L3's broader coverage. Interpretation must account for this asymmetry.
- **Option D — Filter test set to L1-coverable violations only:** Exclude chains where the only violation type is R2, R4, R9, R10, or R11. L1 stays at 7 fields. Cost: shrinks test set; may bias toward easier violations.

**My analysis (surfacing, not deciding):**

Option A is methodologically cleanest — L1 becomes a true "all rules covered, just fewer descriptive fields" baseline, and the L1→L2→L3 sequence becomes a coverage-depth comparison rather than a rule-availability one. Option B is the next-cleanest if R11 violations are rare in the test set. Options C and D both confound Lever 1's effect-size measurement with rule-coverage asymmetry — measuring "fewer fields" but actually measuring "fewer detectable violation types," which is a different manipulation.

**Decision:**

[x] Option A (10 fields) &nbsp;&nbsp;&nbsp; [ ] Option B (8 fields) &nbsp;&nbsp;&nbsp; [ ] Option C (keep 7, document) &nbsp;&nbsp;&nbsp; [ ] Option D (filter test set) &nbsp;&nbsp;&nbsp; [ ] Other: _______

**Author 1:** Safiq Sindha — 2026-05-12    **Author 2:** Myriam Sindha — 2026-05-12

Applied as Amendment #1 to the pre-registration. New SPEC SHA-256: `9ab2e9484fe8837d687a952d132fa07ca771fc37bcd5e5774f1adee91ebefe6c`. Previous signed hash `b5cbfdb5d5c6a3cfd068f5509e456c4d8b3c77c8890596c09cfa6266c4f3909b` superseded.

---

**Status of pre-signoff blockers as of 2026-05-12 (post-Amendment #1):**

- [x] Item 1 (Lever 13 dead-code patch) — applied 2026-05-11
- [x] Item 2 (Lever 19 cross-lever anchor note) — applied 2026-05-11
- [x] Item 3 (O2 coverage check) — Option A chosen, applied as Amendment #1 on 2026-05-12
- [x] O4 (DeepSeek `/beta` schema acceptance test) — PASS on 2026-05-12
- [ ] Both-author re-signature on `signoff/signoff_block.md` at new hash `9ab2e948…ebefe6c` (Amendment #1 row)
- [x] Item 3 (O2 coverage check) — **gaps surfaced; awaiting both-author resolution**
- [ ] O4 (DeepSeek `/beta` schema acceptance test) — also outstanding
- [ ] Both-author final signoff on `signoff/signoff_block.md`

Per posture reminder: STOP and surface. Not deciding unilaterally on which fields to add or which violations to exclude.

---

## Cross-Model Review Resolution (2026-05-12)

ChatGPT, Gemini Pro, and Gemini Deep Research reviewed the SPEC at hash `f84ac646…`. Convergent findings adopted; hallucinated Gemini Deep Research specifics (V4-Pro 1.6T/49B parameter counts, "Think Max 200K minimum," multi-turn state hydration concerns, CSA "10% KV cache" claim) discarded.

**Resolution applied as Amendment #5** (labeled "Amendment #4" in user spec): 29 substantive SPEC changes spanning parser scope, bootstrap methodology, falsifiable prediction magnitudes, capability-tier thresholds, regime-descriptive language, and chain-leakage audit. See `signoff/signoff_block.md` Amendment Log row 5 for the full enumeration.

**Author 1:** Safiq Sindha — 2026-05-12    **Author 2:** Myriam Sindha — 2026-05-12

New SPEC SHA-256: `0f7116029842ef260352d7ed480b8bdfbb07bd4feab7ff75747df3618f1abae8`. Previous hash `f84ac646…f831e1` superseded.

**Items discarded from cross-model review (for record):**
- Gemini Deep Research: V4-Pro 1.6T/49B parameter counts (hallucinated)
- Gemini Deep Research: "Think Max 200K token minimum" requirement (hallucinated API behavior)
- Gemini Deep Research: Multi-turn state hydration concerns (not applicable to OLAT's single-shot design)
- Gemini Deep Research: CSA "10% of KV cache" mechanism (cited without verification, conflicts with handoff)

**Items considered but not adopted as primary:**
- Empirical Bayes shrinkage adopted as supplementary reporting (B4 narrative guardrail) rather than as primary ranking method, because OLAT design specifies effect-size estimation; raw and shrunken estimates both reported.
- Lever 8 mechanistic interpretation narrowed (D4) rather than expanded — k changes multiple things simultaneously; cliff attribution is single-mechanism agnostic.
