# OLAT Status Check — Pre-Session Inventory

**Generated:** 2026-05-15
**Branch:** `claude/amendment-7-diagnostics-PZxRq`
**Purpose:** Read-only inventory of OLAT pre-registration artifacts across all seven
  categories. Maps genuine open items, confirms complete work, and issues recommendations
  for work prioritization before Phase 3.

---

## Section 1 — Summary Table

| Category | Status | Open Items | Estimated Effort |
|---|---|---|---|
| 1. SPEC Integrity & Amendment Log | ⚠️ Partial | Amendment #7 not in log; log order non-sequential; no files for #1–6 | Low (documentation only) |
| 2. Amendment #7 Integration | 🔴 Blocked | Both-author signoff blank; Final Results Signoff blank | Requires both authors |
| 3. Effect Tables & Sensitivity Analyses | ⚠️ Partial | `sensitivity_analyses.json` s6_quartile still character-based | Medium (script update) |
| 4. Quartile / Length Analysis | ✅ Complete | None | — |
| 5. Anchor Effects (Phase 1) | ✅ Complete | Not yet referenced in primary summary docs | Low (cross-reference addition) |
| 6. Tool Augmentation Pre-Work (Phase 2) | ✅ Complete | `bonus_analysis/` and `experiment/` dirs absent (expected at this stage) | N/A (not yet due) |
| 7. Signoff & Final Documentation | 🔴 Blocked | Amendment #7 signoff empty; Final Results Signoff blank | Requires both authors |

---

## Section 2 — Genuine Open Items

### OPEN-1 [CRITICAL] Amendment #7 both-author signoff missing

**File:** `pre-registration/amendments/amendment_7.md`, `pre-registration/signoff/signoff_block.md`
**Evidence:** `amendment_7.md` signoff block reads `[ ] [ ]`. Amendment #7 is absent from
the Amendment Log in `signoff_block.md` (which lists #1, #2, #5, #6, #4, #3 in that order).
**Why it matters:** Both-author signoff is required before (a) merging Amendment #7 results
into primary effect tables, (b) citing L18 L4 results in the final write-up. The integration
block is in force.
**Action needed:** Both authors review `amendment_7.md`, check signoff boxes, and add
Amendment #7 to the Amendment Log in `signoff_block.md`.
**Effort:** < 30 minutes (review only; retest is already complete).
**Priority:** CRITICAL — blocks all downstream integration.

---

### OPEN-2 [CRITICAL] Final Results Signoff blank

**File:** `pre-registration/signoff/signoff_block.md`
**Evidence:** Final Results section has all checkboxes empty and signature lines blank.
This is expected at current project stage (Phase 2 pre-work, not final analysis), but must
be tracked as a required completion item.
**Why it matters:** Cannot publish or submit until both authors sign off on final results.
**Action needed:** Defer until Phase 3 analysis is complete; then schedule both-author sign-off
session.
**Effort:** Coordination required.
**Priority:** CRITICAL (future gate), not blocking current work.

---

### OPEN-3 [IMPORTANT] `sensitivity_analyses.json` s6_quartile data is stale (character-based)

**File:** `pre-registration/day_2/sensitivity_analyses.json`
**Evidence:** s6_quartile boundaries for Meaningful conditions read as character ranges
(~1146–2145 characters). The authoritative analysis has been superseded by
`pre-registration/day_2/quartile_analysis/bimodal_summary.md`, which uses
completion-token boundaries (e.g., pro_L18_L3 Q2: 427–487 tokens). The JSON file was not
updated when the token-based analysis was computed.
**Why it matters:** Any downstream code or document that reads s6_quartile from
`sensitivity_analyses.json` will use wrong units (characters ≠ tokens). This is a
correctness risk if Phase 3 scripts import from that field.
**Action needed:** Either (a) update s6_quartile in `sensitivity_analyses.json` with
token-based values from `quartile_breakdown_full.csv`, or (b) add a deprecation notice in
the JSON and direct readers to `bimodal_summary.md`. Option (b) is lower risk.
**Effort:** ~1 hour (update script or add deprecation comment to 192 affected entries).
**Priority:** IMPORTANT — must resolve before Phase 3 scripts consume this field.

---

### OPEN-4 [IMPORTANT] BUILD_PLAN arithmetic errata (Flag 1) unfixed

**File:** `pre-registration/BUILD_PLAN.md` (specific line TBD; flagged in
`pre-registration/day_0/day_0_completion_report.md` as Flag 1)
**Evidence:** `day_0_completion_report.md` documents an arithmetic error in the BUILD_PLAN
cost/token estimate. The errata note is captured inline in the completion report but the
error is not corrected in `BUILD_PLAN.md` itself. Grep confirms no correction annotation
in `BUILD_PLAN.md`.
**Why it matters:** BUILD_PLAN.md is a pre-registration artifact. An uncorrected arithmetic
error in a locked document is a credibility risk. The Day 0 report flags this as an errata
but does not assign a correction action.
**Action needed:** Add inline `[ERRATA: ...]` annotation to the affected line in
`BUILD_PLAN.md`, documenting the correct value and cross-referencing `day_0_completion_report.md`.
**Effort:** < 15 minutes.
**Priority:** IMPORTANT — pre-registration credibility.

---

### OPEN-5 [IMPORTANT] Amendment #7 not in Amendment Log; log order non-sequential

**File:** `pre-registration/signoff/signoff_block.md` (Amendment Log section)
**Evidence:** Log lists: #1, #2, #5, #6, #4, #3 (non-sequential). Amendment #7 is absent.
The amendment file `pre-registration/amendments/amendment_7.md` exists but is not cross-
referenced in the log.
**Why it matters:** Non-sequential ordering suggests amendments were logged out-of-order.
Missing #7 entry means the log is incomplete. Both weaken the pre-registration record.
**Action needed:** (a) Add Amendment #7 entry to the log. (b) Optionally add a footnote
explaining the non-sequential ordering (likely due to retroactive documentation of #3 and #4).
**Effort:** < 15 minutes.
**Priority:** IMPORTANT — pre-registration completeness.

---

### OPEN-6 [LOW] Anchor effects not cross-referenced in primary summary documents

**File:** `pre-registration/anchor_effects/observational_tests_summary.md` (exists, complete)
**Evidence:** The observational tests summary was generated in this session and contains all
4 Phase 1 tests with full synthesis. However, the primary OLAT results documents (e.g.,
`day_2/cross_universe_comparison.md`) do not reference or cite it.
**Why it matters:** The anchor-effect finding (regime, not anchor, is the primary verdict
driver) is a cross-cutting insight that should be visible from the primary results.
**Action needed:** Add a brief cross-reference note in `cross_universe_comparison.md` pointing
to `anchor_effects/observational_tests_summary.md` for the anchor-effect analysis.
**Effort:** < 15 minutes.
**Priority:** LOW — documentation hygiene.

---

### OPEN-7 [LOW] No separate amendment files for Amendments #1–6

**Files:** `pre-registration/amendments/` (contains only `amendment_7.md`)
**Evidence:** Amendments #1–6 are documented in the Amendment Log within `signoff_block.md`
as one-line entries only. No standalone amendment files exist for them.
**Why it matters:** Low — the Amendment Log entries provide sufficient traceability for
amendments that are already signed off. This is a documentation completeness note, not a
correctness issue.
**Action needed:** Optional: create stub files `amendment_1.md` through `amendment_6.md`
that expand on the log entries. Not required for pre-registration validity.
**Effort:** ~1–2 hours (research + write). Low value.
**Priority:** LOW — optional.

---

## Section 3 — Already-Complete Items

**SPEC hash locked:** `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8`
(Amendment #6 lock confirmed in `signoff_block.md`; hash file at `pre-registration/spec_hash.txt`). ✓

**Effect tables (all 3 universes):** `day_2/effect_table_universe_L{1,2,3}.csv` each contain
65 rows (64 conditions + header). L18_L4 correctly shows `class=Unknown`, `n_valid=0`,
blank dr/gap — confirmed not integrated. ✓

**Degenerate variance flags:** `sensitivity_analyses.json` correctly marks `degenerate_variance=True`
for 4 Pro conditions (L15_L1/L3, L16_L2/L3). ✓

**L18_L4 parse failure flagged:** `sensitivity_analyses.json` entries for L18_L4 show
`primary_classification=Unknown` and `s5_parse_fail_flagged=True`. ✓

**Cross-universe comparison:** `day_2/cross_universe_comparison.md` is complete and thorough;
documents universe identity, effective independence, and sensitivity check results. ✓

**Valley-then-peak analysis:** `day_2/quartile_analysis/bimodal_summary.md` exists with
correct token-based boundaries and valley-then-peak framing. pro_L18_L3 Q2 valley
(427–487 tokens, effect ≈ −0.36 to −0.40, escape ~494 tokens) and flash_L18_L3 valley
(Q2–Q3, 606–728 tokens, escape ~729 tokens) fully documented. ✓

**Diagnostic 1 (parser sanity):** `pre-registration/scripts/diagnostic_1_and_4.py` runs
10-record spot-check; result: 0 parser-induced YES flags. Parser operates only on `content`
field; with `thinking: enabled`, `content` receives bare answer token only. ✓

**Diagnostic 4 (reasoning categorization):** Same script; result: 73/73 Bucket A
(reasoning→YES aligns with parsed YES), 0 Bucket B, 0 Bucket C. YES-bias confirmed as
genuine model behavior, not parser artifact. ✓

**Amendment #7 retest complete:** 73/100 parseable (27 truncated at 4096 tokens),
all 73 parsed as YES, gap=0.0, `class=Unknown`. Root cause confirmed: DeepSeek applies
`max_tokens` to total output (reasoning + content), not content-only. ✓

**Phase 1 anchor tests (all 4):** `pre-registration/anchor_effects/observational_tests_summary.md`
contains Tests 1–4 + synthesis. Key finding: regime (not anchor) is primary verdict driver;
anchor matched reasoning language ~41% of cases (partial cognitive framing influence). ✓

**Phase 2 — checker_verdicts.csv:** `pre-registration/tool_augmentation_prep/checker_verdicts.csv`
generated for all 50 Amendment #7 chains. Distribution: 32 all_agree_YES, 16 all_agree_NO,
2 two_YES_one_NO. ✓

**Phase 2 — prompt templates:** `pre-registration/tool_augmentation_prep/prompt_templates.md`
contains Templates A, B, C with hypotheses, success/failure patterns, and example
instantiations. ✓

**Phase 2 — outcome decision tree:** `pre-registration/tool_augmentation_prep/outcome_decision_tree.md`
pre-registers 6 outcomes with trigger conditions, interpretations, Mew implications, and
next steps. Stop conditions pre-registered. ✓

**Phase 2 — Lever 16 relevance:** `pre-registration/tool_augmentation_prep/lever_16_relevance.md`
documents that rules alone (Lever 16) show null effect on both Flash and Pro; supports
tool augmentation hypothesis. ✓

**Day 2 scripts:** All analysis scripts present in `pre-registration/scripts/`. ✓

---

## Section 4 — Recommendations

### Before Phase 3 (requires action this session or next)

**R1 [BLOCKS INTEGRATION] — Get both-author signoff on Amendment #7.**
Until both authors sign `amendment_7.md` and add #7 to the Amendment Log, L18_L4 results
cannot be cited or integrated. Schedule a synchronous sign-off. Estimated time: < 30 min
(retest data is already complete and reviewed).

**R2 [CORRECTNESS RISK] — Update or deprecate `sensitivity_analyses.json` s6_quartile.**
Phase 3 analysis scripts must not import the character-based quartile boundaries. Preferred
fix: add a `"s6_quartile_deprecated": true` flag and a `"s6_quartile_note"` field pointing
to `quartile_breakdown_full.csv`, then update any Phase 3 code to read from the CSV.
Alternatively, run an update pass to write token-based values into the JSON.

**R3 [CREDIBILITY] — Fix BUILD_PLAN arithmetic errata in-place.**
Add `[ERRATA: ...]` annotation to the relevant line in `BUILD_PLAN.md`. This is a 15-minute
fix that closes Flag 1 from `day_0_completion_report.md`.

**R4 [COMPLETENESS] — Add Amendment #7 to Amendment Log; note non-sequential ordering.**
Update the Amendment Log in `signoff_block.md`. Add a brief parenthetical explaining the
non-sequential numbering if necessary.

### Can wait until Phase 3 drafting

**R5** — Add cross-reference from `cross_universe_comparison.md` to
`anchor_effects/observational_tests_summary.md` (OPEN-6). Low effort, low urgency.

**R6** — Decide whether to create stub files for Amendments #1–6 (OPEN-7). Optional;
current log entries are sufficient for pre-registration traceability.

### Requires both-author review (cannot be completed unilaterally)

**R7** — Amendment #7 signoff (see R1 above).

**R8** — Final Results Signoff (OPEN-2). Not yet due; schedule after Phase 3 analysis
and write-up are complete.

**R9** — Any decision to update `sensitivity_analyses.json` s6_quartile values should be
reviewed by both authors before committing, as it modifies a pre-registration artifact.

---

## Appendix — File Locations Verified

| Artifact | Path | Verified |
|---|---|---|
| SPEC hash | `pre-registration/spec_hash.txt` | ✓ |
| Amendment #7 file | `pre-registration/amendments/amendment_7.md` | ✓ |
| Signoff block | `pre-registration/signoff/signoff_block.md` | ✓ |
| Effect tables (L1/L2/L3) | `pre-registration/day_2/effect_table_universe_L{1,2,3}.csv` | ✓ |
| Sensitivity analyses JSON | `pre-registration/day_2/sensitivity_analyses.json` | ✓ |
| Cross-universe comparison | `pre-registration/day_2/cross_universe_comparison.md` | ✓ |
| Valley-then-peak analysis | `pre-registration/day_2/quartile_analysis/bimodal_summary.md` | ✓ |
| Quartile breakdown CSV | `pre-registration/day_2/quartile_analysis/quartile_breakdown_full.csv` | ✓ |
| Diagnostic script | `pre-registration/scripts/diagnostic_1_and_4.py` | ✓ |
| Phase 1 anchor tests | `pre-registration/scripts/phase1_anchor_tests.py` | ✓ |
| Phase 2 prep script | `pre-registration/scripts/phase2_prep.py` | ✓ |
| Anchor tests summary | `pre-registration/anchor_effects/observational_tests_summary.md` | ✓ |
| Checker verdicts CSV | `pre-registration/tool_augmentation_prep/checker_verdicts.csv` | ✓ |
| Prompt templates | `pre-registration/tool_augmentation_prep/prompt_templates.md` | ✓ |
| Outcome decision tree | `pre-registration/tool_augmentation_prep/outcome_decision_tree.md` | ✓ |
| Lever 16 relevance | `pre-registration/tool_augmentation_prep/lever_16_relevance.md` | ✓ |
| Day 0 completion report | `pre-registration/day_0/day_0_completion_report.md` | ✓ |
| BUILD_PLAN | `pre-registration/BUILD_PLAN.md` | ✓ (errata unfixed) |
| bonus_analysis/ | `pre-registration/bonus_analysis/` | ✗ ABSENT |
| experiment/ | `pre-registration/experiment/` | ✗ ABSENT (not yet due) |
