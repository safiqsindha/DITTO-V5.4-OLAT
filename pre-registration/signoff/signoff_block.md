# Project Ditto OLAT — Signoff Block

---

## Pre-Registration Signoff

**SPEC SHA-256:** `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8`

**Hash history:**
- `b5cbfdb5d5c6a3cfd068f5509e456c4d8b3c77c8890596c09cfa6266c4f3909b` — original signoff 2026-05-12
- `9ab2e9484fe8837d687a952d132fa07ca771fc37bcd5e5774f1adee91ebefe6c` — Amendment #1 (O2 Option A — L1 to 10 fields), 2026-05-12
- `7a465951906491e595e3679b29a75cabcb5cd3c3eb1ff86485ca9d98a6bcff06` — Amendment #2 (Lever 8 reanchor + saturation prediction), 2026-05-12
- `a9db72457db930a91d0871826cf5a91a947390affec776c22e4109ca60aa5538` — Amendment #3 interim (5-stage cascade), superseded
- `6dd1917c680443a330a9d3182e3b3a85bdaee5262a6215d440e5366cb48c11bd` — Amendment #3 mid-refinement, superseded
- `527d7c94ceed6a1fa300e2c1fe12192270a9b44821e5a1da9cb54ab7cf407a52` — Amendment #3 finalized (8-item dual-model + parser scope), 2026-05-12
- `c376c6ee622cd79db2b91ad682e38ce62c2feb9af7ab5be3af38b9c3a7944fc2` — Amendment #4 interim (A1-A5 + B1-B2 applied), superseded same-day
- `f84ac646b051661bd2a5b75116783536270005e8dc1a453f13644f4c90f831e1` — Amendment #4 (completeness improvements pre cross-model review), 2026-05-12
- `0f7116029842ef260352d7ed480b8bdfbb07bd4feab7ff75747df3618f1abae8` — Amendment #5 (cross-model review integration), 2026-05-12
- **`dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8`** — Amendment #6 (Lever 5 L2/L3 data-availability dropout + Lever 15 §7.5 typo correction), 2026-05-13 (current)

This hash covers the SPEC.md file as of the moment both authors sign below. Any modification to SPEC.md after this signature requires a new hash and a fresh signoff (see Amendment Log below).

**Verify hash before signing:**
```
shasum -a 256 pre-registration/SPEC.md
```
Expected output must match the hash above exactly.

---

### Author 1 Signoff

**Name:** Safiq Sindha
**Date:** 5/12
**Signature / initials:** SS
**Notes / reservations:** Hash look good. Signing off on Ammendment 5.

---

### Author 2 Signoff

**Name:** Myriam Sindha
**Date:** 5/12
**Signature / initials:** MS
**Notes / reservations:** Signing off on Ammendment 5.

---

## Pre-OLAT Verification Results Record

*Filled in 2026-05-12 after Pre-Amendment-3 Tasks 1 and 2. Dual-model verification per Amendment #3 B3.*

| Metric | V4-Flash (Task 1 — Day-2 raw re-parsed under v2 cascade) | V4-Pro (Task 2 — fresh n=250 under v2 cascade) |
|---|---|---|
| Run date | 2026-05-12 (re-parse) | 2026-05-12 |
| n_attempted | 250 | 250 |
| n_valid | 250 | 246 |
| detection_rate_violated | 0.0000 (0/182) | 0.1404 (25/178) |
| detection_rate_intact | 1.0000 (68/68) | 0.8971 (61/68) |
| gap (SPEC: violated − intact) | −1.0000 | −0.7566 |
| Cohen's h | −3.1416 | −1.7201 |
| 95% bootstrap CI (n_boot=2000) | [−1.0000, −1.0000] (degenerate) | [−0.8379, −0.6675] |
| parse_failure_rate | 0.0000 | 0.0160 |
| parse_stage_breakdown | strict: 0% / permissive: 0% / md_strip: 0% / last_token: 100% / unparseable: 0% | strict: 1.2% / permissive: 0% / md_strip: 0% / last_token: 97.2% / unparseable: 1.6% |
| API access date | 2026-05-12 | 2026-05-12 |
| Routing target (served_model) | `deepseek-v4-flash` | `deepseek-v4-pro` |
| Scenario triggered (S1–S6) | S2 (gap < −0.05) + S5 (NO_rate > 0.95) — **expected under Path 1 per Amendment #3 + #4 D1**, not pathology | S2 (gap < −0.05) — **expected under Path 1**, not pathology |
| Anchor effect on baseline | "The answer is YES or NO." anchor is the locked OLAT modification; baseline is the floor-effect baseline characterized in §6 |

**Verification proceed decision (per locked Amendment #3 + #4 thresholds):**
- [x] All proceed conditions met: n_valid ≥ 200 (Flash 250, Pro 246) ✓ | parse_failure_rate ≤ 0.05 (Flash 0.000, Pro 0.016) ✓ | S2 + S5 firing on baseline expected under Path 1; not blocking
- [x] Both authors agree result is interpretable as the empirical V1-minimal floor characterization across V4 family
- [x] Path 1 (floor-effect baseline) confirmed across both V4-Flash and V4-Pro

**Author 1 verification signoff:** Safiq Sindha (SS) Date: 2026-05-12

**Author 2 verification signoff:** Myriam Sindha (MS) Date: 2026-05-12

---

## Final Results Signoff

*To be filled in after OLAT execution and analysis (Day 2).*

**Results file location:** _______________
**Effect table signed:** [ ] Yes

**Both authors confirm:**
- [ ] Effect table reviewed independently
- [ ] Parse failure rates reported alongside effect sizes
- [ ] Sensitivity checks completed (include-unparseable and exclude-first-token)
- [ ] Lever 18 L4 reasoning_content qualitative review completed
- [ ] Surprising findings documented

**Author 1 results signoff:** _______________ Date: _______________

**Author 2 results signoff:** _______________ Date: _______________

---

## Amendment Log

*Record any amendments to the pre-registration here. Each amendment requires both-author signoff and a new SPEC hash.*

| # | Date | Amendment description | New SPEC SHA-256 | Author 1 | Author 2 |
|---|---|---|---|---|---|
| 1 | 2026-05-12 | **O2 Option A — L1 expanded to 10 fields.** Add `recover_in`, `from_phase`, `to_phase` to the L1 minimal schema so it covers all 9 active symbolic checker rules. Closes O2 coverage gap. Affects SPEC §7.1 Lever 1 description and §12 open items table. Removes the deferred-to-Day-3 risk for O2 path (a). Hash verified by Author 1 via `shasum -a 256` on 2026-05-12. | `9ab2e9484fe8837d687a952d132fa07ca771fc37bcd5e5774f1adee91ebefe6c` | Safiq Sindha (SS) — 2026-05-12 | Myriam Sindha (MS) — 2026-05-12 |
| 2 | 2026-05-12 | **Lever 8 reanchor + saturation-curve prediction.** Triggered by Day -2 first-run finding (S2 + S5 triggered, degenerate-NO output) and confirmed by step-distribution check showing only 3.6% of violations visible at k=5 (median violation_step=14, p75=24.5 in v5.1 corpus). Levels changed from {3, 5, 8, 12, 20} to **{5, 10, 15, 20, 30}**. Baseline shifts from L2(k=5) to **L3(k=15)**. Prediction reframed from "monotonic in k" to **saturation-curve in k** (floor at k=5, climb through median, plateau at k=20–30). Affects SPEC §5 global baseline table, §7.1 Lever 8, §11 assumption #10, §13 conditional follow-up, Appendix A Same Task More Tokens citation. Day -2 verification re-run required at new baseline. | `7a465951906491e595e3679b29a75cabcb5cd3c3eb1ff86485ca9d98a6bcff06` | Safiq Sindha (SS) — 2026-05-12 | Myriam Sindha (MS) — 2026-05-12 |
| 5 | 2026-05-12 | **Cross-model review integration (labeled "Amendment #4" in user spec).** Closes the cross-model review phase. Integrates convergent ChatGPT + Gemini Pro feedback; selectively adopts substantive Gemini Deep Research items; discards hallucinated specifics (V4-Pro parameter counts, "Think Max" requirement, multi-turn state hydration, CSA mechanism). 29 substantive changes across SPEC. **Section A (parser/implementation):** A1 parser scope locked to `content` field only (excludes `reasoning_content`); A2 distractor padding 100% violation-free pre-screen required; A3 API failure handling spec in §14; A4 recursive schema sanitizer enforcement for Lever 12 L3; A5 DeepSeek V4-Flash tokenizer locked for Lever 11 sizing. **Section B (bootstrap/analysis):** B1 §9.0 bootstrap methodology spec (10K BCa iterations, paired intra-model, two-sample cross-model deltas, empty-cell handling); B2 estimand hierarchy in §4 (gap → effect size → cross-model delta); B3 sensitivity hierarchy with parser-dependence reframing of #4 and conflict resolution rules; B4 multiple-comparison sharpened with empirical Bayes shrinkage. **Section C (falsifiability):** C1 Lever 19 prediction replaced with falsifiable specificity threshold; C2 Lever 16 magnitude-bounded ≥0.05 pairwise + ≥0.15 cross-model; C3 Lever 18 magnitude-bounded supersedes B3a directional draft (Flash ≥+0.30, Pro range −0.10 to +0.20, cross-model delta ≥+0.20); C4 Lever 8 ≥0.25 adjacent-level cliff threshold; C5 decision rule × CI hierarchy formalized in §9; C6 capability-tier delta interpretation thresholds in §9.3. **Section D (framing):** D1 S5 reinterpretation under Path 1 (parallel to S2); D2 cross-model descriptive language (regime comparison, not capability isolation); D3 Lever 5 endogeneity note; D4 Lever 8 narrowed to "effective utilization" not "reasoning depth"; D5 Lever 18 regime terminology operational/descriptive; D6 parser-as-instrument construct tightening (3 levels of interpretive drift documented); D7 Lever 24 three-table evaluation universe structure; D8 Lever 15 L1 thresholding asymmetry documented; D9 Lever 4 Mew application rule. **Section E (implementation):** E1 Sensitivity #4 reframed as parser-dependence characterization (included with B3); E2 Lever 12/Lever 17 prompt-schema precedence; E3 arcsine method locked (logit rejected); E5 chain leakage audit threshold (>20 conditions or top-5% concentration). | `0f7116029842ef260352d7ed480b8bdfbb07bd4feab7ff75747df3618f1abae8` | Safiq Sindha (SS) — 2026-05-12 | Myriam Sindha (MS) — 2026-05-12 |
| 6 | 2026-05-13 | **Lever 5 L2/L3 data-availability dropout + Lever 15 §7.5 typo correction.** Two changes bundled. **(A) Lever 5 L2/L3 dropped (Option A).** Cross-version data search confirmed no per-chain Pokemon detection data exists at 22-model panel breadth: V5.1 Final phase3_consolidated panel covered NBA / Rocket League / CSGO / PUBG / Poker — not Pokemon. V5.2 d_1_4 has partial 2-model Pokemon data (Haiku + Sonnet, 1,200 chains, 600 overlap with OLAT pool) — too thin for 5-bucket stratification or meaningful variance ranking. Building a fresh 22-model panel was considered and rejected (V1-minimal would reproduce floor contamination; CoT framing redefines Lever 5). The SPEC's Amendment #5 D3 endogeneity note prefigured this dropout; Amendment #6 operationalizes it. Lever 5 retains only L1 (random selection); L2 and L3 marked DEFERRED pending future panel build (out of OLAT scope). **(B) Lever 15 §7.5 typo correction.** Lever 15 non-baseline conditions corrected from (L2, L3) to (L1, L3). Amendment #4 B1 set Lever 15 baseline = L2 (YES/NO violation detection); §7.5's per-lever breakdown lagged that update and listed L2 as a non-baseline condition (which would have produced effect_size=0 by construction against the L2 baseline). The correct non-baseline conditions are L1 (consistency rating) and L3 (scaled likelihood). No methodology change; counts unaffected. **Combined effect on totals:** 12 OLAT-scale non-baseline drops from 26 → 24; per-model conditions 34 → 32; dual-model 68 → 64; total evaluations 3,400 → 3,200; cost saving ~$0.15 (negligible). Affects SPEC §4 (totals row), §7.1 Lever 5 (DEFERRED notation + dropout rationale), §7.5 (totals table + per-lever breakdown for Lever 5 and Lever 15). | `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8` | Safiq Sindha (SS) — 2026-05-13 | Myriam Sindha (MS) — 2026-05-13 |
| 4 | 2026-05-12 | **Completeness improvements for cross-model review.** No methodology changes; additions and clarifications surface design rationale for external reviewers. **A1** — New §2.5 Diagnostic Phase Findings (5 findings citing Diag F/G/H/I/J + Pre-Amendment-3 Tasks 1/2). **A2** — New §9.1 Statistical Power for Decision Rules (power table by baseline rate + multiple-comparison handling + cross-model differential power). **A3** — New §9.2 Pre-Registered Sensitivity Analyses (6 sensitivity checks reported alongside primary). **A4** — §7.5 Total OLAT Conditions rewritten with exact counts: 12 OLAT-scale levers (26 non-baseline conditions) + 5 minimally-tested levers (7 non-baseline) + 1 baseline = 34 per model × 2 models = **68 conditions, 3,400 evaluations**. **A5** — §4 API cost recomputed at ~$15–35 with explicit pricing assumptions; Lever 11 long-prompt dominates cost. **B1** — Lever 15 baseline in §5 clarified: L2 (YES/NO) is the de facto baseline; L1 (consistency rating) is reserved only when Lever 15 is the lever under test. **B2** — Lever 13 L2 in §7.1 locked at exactly top-3 (was "top 2–3"). **B3a** — Lever 18 cross-model predictions softened from magnitude ranges to directional regime claims (over-flagging vs balanced). **C1-defer** — §13 conditional follow-up triggers extended with deferral sentence covering other levers (no triggers pre-registered; post-execution amendments if needed). **C2-inline** — §17 Day 0 procedure added inline (11-step deterministic chain-variant preparation). Affects SPEC §2.5 (new), §4, §5, §7.1, §7.5, §9.1 (new), §9.2 (new), §13, §17. | `f84ac646b051661bd2a5b75116783536270005e8dc1a453f13644f4c90f831e1` | Safiq Sindha (SS) — 2026-05-12 | Myriam Sindha (MS) — 2026-05-12 |
| 7 | 2026-05-13 | **Lever 18 L4 max_tokens raised 64 → 4096 (operationalization gap correction).** Root cause: DeepSeek applies `max_tokens` to total output (`reasoning_content` + `content` combined), not to `content`-only as SPEC §7 assumed. Day 1 produced 0/100 parseable L18 L4 records (all `finish_reason=length`, `content` empty at the 64-token cap). Two pilots confirmed 4096 sufficient (Flash headroom 74%, Pro 66% over worst observed case). Retest (2026-05-13): 100 calls, 73/100 parseable, all 73 → YES, gap=0.0, YES-bias confirmed. Classification: Null (both models). Asymmetric truncation: intact chains truncate at 33% vs. 19–28% for violated (intact reasoning exceeds budget more often). Retest outputs in `amendment_7/`; NOT merged into primary tables pending both-author signoff. No SPEC hash change; parent hash `dbae94d…` unchanged. See `amendments/amendment_7.md` for full rationale. | `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8` (unchanged — parameter override only) | [ ] | [ ] |
| 3 | 2026-05-12 | **Floor-effect baseline lock + dual-model + max_tokens 1024 + 4-stage parser cascade + S2 reinterpretation + cross-model asymmetry framing + cross-model predictions + parser-as-instrument lock.** Full 8-item scope: **(1)** L18 L2/L3 max_tokens raised 512 → 1024 (Diag I evidence: max completion 701 Flash / 540 Pro at 4096 ceiling, all finish_reason=stop). **(2)** Parser cascade upgraded from legacy 3-stage (strict → permissive → first_token) to 4-stage v2 (strict → permissive → md_strip → last_token); first_token dropped as redundant (<1% rescue beyond last_token per Diag J + Task 1). **(3)** V4-Pro added as co-primary subject alongside V4-Flash; total evaluations doubles to ~3,600; budget rises to ~$15–25. **(4)** V4-Pro Day −2 baseline locked at gap=−0.757 (n=250 per Pre-Amendment-3 Task 2). V4-Flash baseline gap=−1.000 reconfirmed under v2 cascade per Task 1. **(5)** S2 trigger documented as Path-1-expected; per-model effect-size analysis handles anti-detection post-baseline. **(6)** Cross-model baseline asymmetry documented as interpretation framing in §9 — effect sizes measure "movement from per-model floor," not "trajectory toward shared endpoint." **(7)** Pre-registered predictions updated with cross-model claims grounded in diagnostic data: Lever 18 produces large gap improvement on Flash via over-flagging regime, smaller gap change on Pro because Pro's CoT regime is already balanced; Lever 16 expected to reduce Flash's FP rate more than Pro's. **(8)** Parser cascade locked as canonical measurement instrument — any future revision is a methodology amendment requiring fresh signoff. Affects SPEC §2 Subject Model, §4 Experiment Parameters, §6 Pre-OLAT Verification Protocol, §7.1 Lever 18 & Lever 16, §8 Parser Strategy, §9 Decision Rules, plus artifact `verification_response.md` (S2 reinterpretation note). | `527d7c94ceed6a1fa300e2c1fe12192270a9b44821e5a1da9cb54ab7cf407a52` | Safiq Sindha (SS) — 2026-05-12 | Myriam Sindha (MS) — 2026-05-12 |

---

## Open Items Resolved at Signoff

*Document how each open item from SPEC.md Section 12 was resolved before signing.*

| Item | Resolution |
|---|---|
| O1 — L2 field list | RESOLVED via codebase inspection (translation.py, renderer.py, v4_runner.py). L2 = ~18 fields (all 6 event types rendered in v5.1 baseline). See `artifacts/lever_01_field_schemas.md`. |
| O2 — L1 violation coverage | RESOLVED per Amendment #1 (2026-05-12) — Option A: L1 expanded from 7 to 10 fields (added `recover_in`, `from_phase`, `to_phase`). Covers all 9 active symbolic checker rules. Day -3 chain pool check no longer needed for O2 coverage purposes. See Amendment Log above. |
| O3 — 8 abstraction names | RESOLVED per `decisions/decision-sheet-v1.md` — 8 names locked. 6 rule-bearing + 2 dimensional-only documented as feature. |
| O4 — Lever 12 schema acceptance | RESOLVED — DeepSeek `/beta` acceptance test PASS on 2026-05-12. HTTP 200; `tool_calls=1`; all 8 abstractions populated; served_model=`deepseek-v4-flash`; prompt_tokens=1775, completion_tokens=444. Run via `pre-registration/scripts/o4_schema_acceptance_test.py` with locked config (model=deepseek-v4-flash, strict=true, tool_choice=required, extra_body={"thinking":{"type":"disabled"}}). |
| O5 — Lever 15 / Lever 18 question framing | RESOLVED per `decisions/decision-sheet-v1.md` — Interpretation A locked: Lever 18 implicitly holds Lever 15 at L2. Historical-framing footnote added. |
| O6 — S2–S5 verification thresholds | RESOLVED per `decisions/decision-sheet-v1.md` — S2/S4/S5 accepted as drafted; S3 tightened from 0.20 to 0.05. |
| O7 — Paralysis violation framing | RESOLVED per `decisions/decision-sheet-v1.md` — Option A: paralysis omitted from L3, L2 hedged wording retained, Day -3 chain pool check added. |
| O8 — Lever 19 placement | RESOLVED per `decisions/decision-sheet-v1.md` — parallel L2/L3 user-turn opening. |
| O9 — Lever 13 top-3 selection | OPEN — Day 0 task; fallback rule fully specified. Not a signoff blocker. |
| O-A — CoordDep/OptCrit in v5.1 prompt | RESOLVED via codebase inspection — both event types included in rendered chain. L2 field count = ~18. |
