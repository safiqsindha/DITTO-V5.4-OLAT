# OLAT Documentation Errata Log

**Date:** 2026-05-15  
**Prepared by:** Phase A no-API audit  
**Status:** All three errata confirmed applied — no pending corrections

---

## Audit Summary

Task A5 audited three documented errata against current SPEC.md, BUILD_PLAN.md, and
signoff_block.md. All three were applied as part of Amendment #6 (2026-05-13). The current
SPEC.md SHA-256 matches the Amendment #6 locked hash exactly.

**SHA-256 verification (run 2026-05-15):**
```
shasum -a 256 pre-registration/SPEC.md
dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8
```
Expected: `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8` ✓ **MATCH**

The hash is unchanged from Amendment #6. No errata modifications were made to SPEC.md after
Amendment #6 signing.

---

## Errata #1 — SPEC §7.5 Lever 15 Typo

**Erratum:** Lever 15 non-baseline conditions were listed as (L2, L3) in §7.5, but L2 is the
baseline. The correct non-baseline conditions are (L1, L3).

**Source of erratum:** Day 0 completion report `day_0/day_0_completion_report.md` §Documentation
Errata Flag 2: "Prior SPEC listed Lever 15 non-baseline conditions as (L2, L3) — L2 is the
baseline, so the non-baseline conditions are L1 and L3."

**Resolution status:** APPLIED in Amendment #6 (2026-05-13). The Amendment #6 log entry in
`signoff/signoff_block.md` explicitly documents this correction:
> "(B) Lever 15 §7.5 typo correction. Lever 15 non-baseline conditions corrected from (L2, L3)
> to (L1, L3)."

**Verification:** SPEC §7.5 per-lever breakdown currently reads:
> "Lever 15 (Question Phrasing): 2 non-baseline **(L1, L3)** — corrected from (L2, L3) per
> Amendment #6; L2 is the baseline, so L1 and L3 are the non-baseline conditions tested
> against it"

**No further action required.** ✓

---

## Errata #2 — BUILD_PLAN Arithmetic Error

**Erratum:** Tasks 3, 4, and 5 in BUILD_PLAN.md stated "68 × 50 × 2 = 6,800" — incorrectly
multiplying the model dimension twice. Correct figure: 64 conditions × n=50 chains = 3,200
records (post-Amendment #6; pre-Amendment #6: 68 × 50 = 3,400).

**Source of erratum:** Day 0 completion report §Documentation Errata Flag 1:
> "Tasks 3, 4, and 5 state '68 × 50 × 2 = 6,800' — incorrectly multiplies the model dimension
> twice. Correct: 68 × 50 = 3,400 (pre-Amendment-6) → now 64 × 50 = 3,200 (Amendment-6)."

**Resolution status:** APPLIED. The BUILD_PLAN.md Day 0 section currently contains:
> "[ERRATA FLAG 1 — RESOLVED] `day_0/day_0_completion_report.md` flagged that an earlier
> draft of this section stated '68 × 50 × 2 = 6,800' (incorrectly multiplying the model
> dimension twice). Current text reflects the correct figure: 64 conditions × n=50 chains =
> 3,200 records (post-Amendment-6). No methodology change."

**Verification:** BUILD_PLAN.md Day 0 Goal line: "3,200 prompt/parameter records" ✓
BUILD_PLAN.md Day 1 checklist: "3,200 API calls (64 conditions × n=50, dual-model)" ✓
BUILD_PLAN.md API Budget table: "OLAT subtotal: ~3,200" ✓

**No further action required.** ✓

---

## Errata #3 — Lever 5 L2/L3 Documentation (Data Unavailability)

**Erratum:** SPEC §7.1 Lever 5 originally specified L2 (difficulty-stratified) and L3
(high cross-model variance) as executable conditions. These conditions were not tested due
to v5.1 panel data being unavailable for the Pokemon domain.

**Source of erratum:** Day 0 completion report §Documentation Errata: "Lever 5 L2 and L3
weren't tested due to v5.1 panel data unavailability."

**Resolution status:** APPLIED in Amendment #6 (2026-05-13). SPEC §7.1 Lever 5 currently
documents:
> "L2: [DEFERRED per Amendment #6 — data unavailable] Originally: Difficulty-stratified by
> mean detection rate across 22 v5.1 models. Not executable: v5.1 22-model panel was run on
> NBA / Rocket League / CSGO / PUBG / Poker, not Pokemon."
>
> "L3: [DEFERRED per Amendment #6 — data unavailable] Originally: High cross-model variance
> from v5.1 panel. Same data-availability blocker as L2."

SPEC §4 includes in the Total evaluations note: "(Amendment #6: dual-model 1,600 V4-Flash +
1,600 V4-Pro; 64 conditions × n=50 per §7.5 after Lever 5 L2/L3 dropout)"

SPEC §7.5 includes: "Lever 5 (Selection Criterion): **0 non-baseline — L2/L3 deferred per
Amendment #6 data-availability dropout**"

**Implication for OLAT effect tables:** Lever 5 row in effect tables will have null entries
for L2 and L3 conditions (these were not run). This is documented explicitly in §7.5 and in
the dropout rationale.

**No further action required.** ✓

---

## Additional Documentation Notes Found During Audit

**Note A — plumbing_schemas.md enum inconsistency (Day 0, §Anomaly 4):**
`artifacts/plumbing_schemas.md` Schema 1 `parse_stage_reached` enum still uses old value
`first_token` from the pre-Amendment-3 3-stage cascade rather than Amendment #3 values
`md_strip` / `last_token`. This is documentation errata only — the implementation uses the
correct 4-stage cascade. The actual parser_provenance.ndjson records use `last_token` and
`md_strip` correctly (verified: all 3,200 records use correct stage labels). The schema
documentation is inconsistent but not load-bearing.

**Action:** Update `artifacts/plumbing_schemas.md` enum to replace `first_token` with
`md_strip` and `last_token`. Requires no methodology amendment; documentation fix only.
**Both-author awareness: Not required.** Flag in next documentation review.

**Note B — Amendment #7 signoff pending:**
`signoff/signoff_block.md` Amendment #7 row shows unsigned entries (`[ ]`) for both authors.
Amendment #7 (L18 L4 max_tokens 64 → 4096) retest outputs are in `amendment_7/` pending
both-author signoff before integration into primary tables.
**Action:** Ensure both authors sign Amendment #7 signoff rows before integrating Amendment #7
findings into primary OLAT effect tables. This is a process requirement, not a documentation
errata.

---

## Signoff Block Update Recommendation

The current `signoff/signoff_block.md` Amendment Log documents Amendment #6 covering both the
Lever 5 dropout and the Lever 15 §7.5 typo correction, signed by both authors (SS + MS, 2026-05-13).

No additional signoff block entry is required for this A5 audit — the errata were properly
documented and signed under Amendment #6. This errata_log.md serves as the comprehensive
audit confirmation that:
1. All three errata were identified and applied
2. The SPEC hash is unchanged from Amendment #6 (confirming no post-signoff modifications)
3. The audit found no undocumented corrections to the locked SPEC

**For the writeup:** This errata log should be referenced in any methodology appendix as
evidence that documentation corrections were tracked and verified separately from methodology
amendments.
