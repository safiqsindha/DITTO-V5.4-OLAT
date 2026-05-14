# Project Ditto OLAT — Build Plan

**Status:** Aligned with SPEC.md at hash `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8` (Amendment #6, 2026-05-13). All amendments #1–#6 signed by both authors. Days −3 and −2 complete. **Ready for Day 0 (chain variant preparation) post-vacation.**

---

## Prerequisites (Pre-Signoff)

- [x] **O1** — L2 field list — RESOLVED via codebase inspection; ~18 fields all 6 event types
- [x] **O2** — L1 minimal field set — RESOLVED Amendment #1 (Option A): L1 expanded to **10 fields** covering all 9 active symbolic checker rules
- [x] **O3** — 8 abstraction names — RESOLVED (decision-sheet-v1.md)
- [x] **O4** — Lever 12 schema `/beta` acceptance test — PASS 2026-05-12 (`pre-registration/scripts/o4_schema_acceptance_test.py`)
- [x] **O5** — Lever 15 framing for Lever 18 — RESOLVED Interpretation A (L15→L2 override)
- [x] **O6** — S2–S5 thresholds — RESOLVED (S3 tightened from 0.20 to 0.05; S2 + S5 later reinterpreted under Path 1 per Amendments #3 + #4)
- [x] **O7** — Paralysis framing — RESOLVED Option A; Day −3 chain pool check completed trivially (no paralysis taxonomy in symbolic checker)
- [x] **O8** — Lever 19 placement — RESOLVED (parallel L2/L3 at user-turn opening)
- [ ] **O9** — Lever 13 top-3 abstraction selection at execution time (Day 0 task; fallback rule fully specified in `artifacts/lever_13_fallback.md`)
- [ ] **Both-author signatures** on `signoff/signoff_block.md` Amendments #2, #3, #4, #5 against hash `0f7116…`

---

## Day −3 — Chain Pool Check ✅ COMPLETE (2026-05-12)

**Goal:** Confirm v5.1 corpus contains no paralysis-only violations (per O7 Option A).

**Result:** Symbolic checker taxonomy contains **no paralysis-related violation type**. The Day −3 paralysis filter is structurally a no-op for this corpus. 19,428 chains eligible; n=250 sample selected with `LEVER_5_RANDOM_SEED=42` (68 intact / 182 shuffled).

**Outputs:**
- `pre-registration/day_minus_3/chain_pool_inventory.json` — full pool inventory
- `pre-registration/day_minus_3/verification_n250_sample.jsonl` — sample for Day −2

---

## Day −2 — Pre-OLAT Verification ✅ COMPLETE for V4-Flash; V4-Pro CONFIRMED at n=250 via Task 2 (2026-05-12)

**Goal:** Establish empirical per-model V1-minimal baseline.

**Locked configuration (per SPEC §5 global baseline + Amendment #2 k=15 + Amendment #3 dual-model + Amendment #4 parser content scope + Amendment #1 L15 L2 baseline):**

| Parameter | Value |
|---|---|
| Models | `deepseek-v4-flash` AND `deepseek-v4-pro` |
| Endpoint | `https://api.deepseek.com` |
| `temperature` | 0.0 |
| `max_tokens` | 32 (L18 L1 baseline) |
| `cutoff_k` | 15 (L8 baseline post-Amendment #2) |
| `extra_body` | `{"thinking": {"type": "disabled"}}` |
| Lever 15 framing | L2 (YES/NO) — de facto baseline per B1 |
| Question text | `"Does this battle chain contain any rule violations?"` |
| Output anchor | `"The answer is YES or NO."` |
| Parser | v2 4-stage cascade (strict → permissive → md_strip → last_token), **content-only scope** per Amendment #4 A1 |
| Bootstrap | n_boot=10,000 BCa, seed=42 per SPEC §9.0 |
| Sample | `verification_n250_sample.jsonl` (68 intact / 182 shuffled) |

**Results (2026-05-12):**

| Model | gap | det_intact | det_violated | YES_rate | parsed_rate | Status |
|---|---|---|---|---|---|---|
| V4-Flash | −1.000 | 1.000 | 0.000 | 0.000 | 1.000 | Pre-Amendment-3 Task 1 (re-parse of original 250 under v2 cascade): identical to v1 |
| V4-Pro | −0.757 | 0.897 | 0.140 | 0.130 | 0.984 | Pre-Amendment-3 Task 2 (fresh n=250 run on V4-Pro) |

**Interpretation:** Path 1 (floor-effect baseline) confirmed across both V4 family members. S2 + S5 triggers on baseline runs are **expected** under Path 1 (per §6 reinterpretation) — they are floor characterization, not pathology. OLAT measures lever-induced movement off the per-model floor.

**Outputs:**
- `pre-registration/day_minus_2/raw_responses.ndjson` — V4-Flash k=15 raw
- `pre-registration/day_minus_2/reparse_v2/*` — v2 re-parse confirmation (Task 1)
- `pre-registration/day_minus_2_v4pro/*` — V4-Pro full Day −2 (Task 2)

---

## Day −1 — Final Pre-Registration Signoff

**Status:** SPEC is at hash `0f7116…`. Verify, then sign Amendments #2 through #5 on `signoff/signoff_block.md` (all four rows reference this same hash).

**Tasks:**
1. Run `shasum -a 256 pre-registration/SPEC.md` — must match `0f7116029842ef260352d7ed480b8bdfbb07bd4feab7ff75747df3618f1abae8`.
2. Both authors review final SPEC (recommend Myriam fresh Claude session).
3. Both authors sign Amendment #2, #3, #4, #5 rows in `signoff/signoff_block.md`.
4. Sign the Pre-OLAT Verification Results Record table with the metrics above.
5. **No OLAT conditions begin until signatures applied.**

If review surfaces methodology questions → Amendment #6 acceptable. Pre-registration discipline > amendment count.

---

## Day 0 — Chain Variant Preparation (Compute Only, No API)

**Goal:** Pre-compute deterministic chain variants for all 64 OLAT conditions (Amendment #6) × n=50 chains = 3,200 prompt/parameter records, ready for Day 1 batched execution.

**Procedure:** Follow the 11-step deterministic procedure in SPEC §17 (Day 0 procedure, Amendment #4 C2-inline). Summary:

1. Load chain per `chain_condition_assignments.ndjson` (seed=42, Lever 5 L1 random sample from 19,428-chain pool).
2. Apply Lever 1 field schema (L1=10 fields / L2=18 / L3=20).
3. Apply Lever 8 truncation (k ∈ **{5, 10, 15, 20, 30}** per Amendment #2; **k=15 baseline**).
4. Apply Lever 9 rendering template (L1 multi-line / L2 single-line / L3 entity-centric).
5. Apply Lever 4 marker annotations if ≠ L1.
6. Apply Lever 2 field renames if ≠ L1.
7. Apply Lever 3 numerical encoding if ≠ L1.
8. Compose prompt: Lever 19 (if ≠ L1) + Lever 16 (if ≠ L1) + chain + Lever 15 question + Lever 18 CoT instruction (if ≠ L1) + output anchor.
9. Set API parameters per condition: model (Flash or Pro), `temperature`, `max_tokens` (L18-dependent — see table below), `thinking` flag, `tools`/`tool_choice`, `response_format`.
10. Apply Lever 11 distractor padding (compute blocks; place per cutoff position).
11. Persist as `chain_variants/<model>/<condition>/<chain_id>.json` for Day 1.

**Lever-specific tasks:**

- **Lever 11 distractor verification (Amendment #4 A2 — MANDATORY):** All distractor candidate chains must pass `pokemon_rule_checker.py` violation-free pre-screen. Exclude any chain with `violation_present == True`. Distractor pool drawn exclusively from intact chains. Verification log: `pre-registration/day_0/distractor_pool_verification.csv`.
- **Lever 11 tokenizer (Amendment #4 A5):** Use `transformers.AutoTokenizer.from_pretrained("deepseek-ai/DeepSeek-V4-Flash")` for prompt sizing. Token count measured on assembled user-turn prompt only; system message tokens excluded from 200–250K target.
- **Lever 13 (O9):** Run `resolve_lever13_l2_abstractions()` once at Day 0 init. Log resolved top-3 + selection_method ("importance_score" or "corpus_frequency") in `chain_variants/<condition>/_metadata.json`.
- **Lever 24:** Prepare L1/L2/L3 ground truth labels per chain. Three independent universes per D7 — variants and labels generated for all three universes.

**Lever 18 max_tokens (Amendment #3, updated by Amendment #4 to add token caps):**

| Level | max_tokens (`content`) | Notes |
|---|---|---|
| L1 (baseline) | 32 | thinking disabled |
| L2 | **1024** (Amendment #3) | thinking disabled; Diag I shows empirical max ~701 |
| L3 | **1024** (Amendment #3) | thinking disabled |
| L4 | 64 (on content) | thinking enabled; `reasoning_content` server-allocated separately |

**Chain-condition assignment log:** `chain_condition_assignments.ndjson` written incrementally as Day 0 generates variants. Confirm 50 chains × 64 conditions = 3,200 records total.

**Estimated time:** 2–6 hours depending on Lever 11 distractor generation + verification.
**Estimated cost:** $0 (no API calls).

---

## Day 1 — Batched API Evaluations

**Goal:** Execute 3,200 API calls (64 conditions × n=50, dual-model).

**Pre-execution checklist:**

- [ ] Day 0 chain variants generated and verified (3,200 records in `chain_variants/`)
- [ ] Distractor pool verified violation-free (A2 mandatory)
- [ ] Signoff block signed at hash `0f7116…` (Amendments #2–#5 + verification record)
- [ ] Parser provenance log initialized (empty NDJSON file)
- [ ] Chain-condition assignment log finalized
- [ ] API key confirmed (`.env` symlink → `../Ditto V5.0/.env`; `DEEPSEEK_API_KEY` prefix `sk-105d6…`)
- [ ] V4-Flash AND V4-Pro both confirmed accessible via `client.models.list()`
- [ ] Lever 12 L3 schema sanitizer recursive enforcement verified (A4)

**Execution order:** Conditions can execute in any order. Recommended: run V4-Flash baseline + V4-Pro baseline first (verify pipeline end-to-end on 100 calls), then remaining 66 conditions × 2 models. Both models execute in parallel where rate limits allow.

**Per-condition task loop:**

1. Read pre-computed prompt and parameter set from `chain_variants/<model>/<condition>/<chain_id>.json`.
2. Submit API call. **Apply parser cascade on `content` field only** (Amendment #4 A1) — never parse `reasoning_content`.
3. On error (per SPEC §14 API failure handling):
   - HTTP 429: exponential backoff retry up to **3 attempts**, then log
   - HTTP 5xx: backoff retry up to 3, then log
   - HTTP 4xx (including schema rejection): log as `api_failure`, do not retry
   - Network/timeout: retry up to 3, then log
4. Write response to parser provenance log immediately (append-only).
5. Run 4-stage parser cascade (`strict → permissive → md_strip → last_token`) on `content`. Log `parse_stage_reached`.

**Special handling (per SPEC §7):**

- **Lever 11 L2/L3 (~200K-token prompts):** Confirm token count on assembled prompt before submission; flag if outside 200–250K range.
- **Lever 12 L3 (function calling):**
  - Use `/beta` endpoint
  - Apply recursive schema sanitizer (Amendment #4 A4): every nested object gets `additionalProperties: false`, every property listed in containing object's `required`, recursive stripping of length/bound constraints
  - Pass `extra_body={"thinking": {"type": "disabled"}}` (without this, server rejects `tool_choice="required"`)
  - Parse the function call payload's `detected` field directly per E2 — not the textual anchor
- **Lever 18 L4 (native thinking):**
  - Accept nullified temperature server-side
  - `reasoning_content` preserved in raw output for audit but **NOT parsed** (Amendment #4 A1)
  - Final classification must appear in `content` field
- **Lever 12 L3 × Lever 18 L4:** Preserve `reasoning_content` across tool sub-turns per verified API behavior. Per Amendment #4 A1, parser still operates on `content` only.

**Estimated time:** 4–12 hours batched (dual-model + rate limits).
**Estimated cost (Amendment #4 A5 breakdown):** ~$15–35 total. Lever 11 long-prompt conditions dominate (~$16); standard conditions ~$2; CoT conditions ~$1; reasoning L4 ~$0.5.

---

## Day 2 — Analysis: Per-Universe Effect Tables + Both-Author Review

**Goal:** Produce three independent OLAT effect tables (one per Lever 24 universe). Both authors review and sign off.

**Three-universe structure (Amendment #4 D7):** The 18-lever × 2-model effect-size matrix is computed independently for each Lever 24 universe (L1 shuffled-vs-real / L2 planted-violations / L3 symbolic-checker-as-truth). **No cross-universe aggregation in primary analysis.**

**Tasks per universe:**

1. **Verify log completeness:** `n_records` in parser provenance = `n_API_calls`. Reconcile orphan records against `chain_condition_assignments.ndjson`.
2. **Compute per-condition per-model:**
   - `detection_rate(intact)`, `detection_rate(violated)` — fractions correct per ground truth label
   - `gap` = detection_rate(violated) − detection_rate(intact) (SPEC §4 primary estimand)
   - `effect_size` = condition gap − baseline gap (SPEC §4 effect size definition)
   - `cohens_h`
   - **Bootstrap 95% BCa CI** on gap and effect size: `scipy.stats.bootstrap`, n_boot=10,000, seed=42 for V4-Flash / seed=43 for V4-Pro (per SPEC §9.0)
   - `parse_failure_rate`, `api_failure_rate`
3. **Compute cross-model capability-tier deltas** per lever: `effect_size_Flash − effect_size_Pro`. Bootstrap delta CI per SPEC §9.0 two-sample procedure (joint resampling of paired-difference distributions). Apply Amendment #4 C6 interpretation thresholds.
4. **Primary classification per decision rule × CI hierarchy** (Amendment #4 C5):
   1. Magnitude check: ≥0.10 → candidate Meaningful; 0.03–0.10 → Directional; <0.03 → Null (final).
   2. CI check: if 95% BCa CI excludes zero on appropriate side → classification confirmed. Otherwise downgrade one level.
   3. Final label governs downstream action.
5. **Sensitivity analyses** (SPEC §9.2 — six analyses reported alongside primary, do not override):
   - Unparseables-as-NO
   - Unparseables-as-random
   - Arcsine-transformed rates (method locked per E3)
   - Parser-strict subset (stage 1–2 only, **parser-dependence characterization** per B3 / E1, not a robustness check)
   - Per-condition parse_failure audit (flag conditions >10%)
   - Within-condition response-length quartile sub-analysis (L18 L2/L3 only)
6. **Multiple-comparison handling** (SPEC §9.1 / B4): no formal correction. Report both raw and **empirical-Bayes-shrunken** effect sizes for ranked table; raw rankings determine ordering, shrunken inform magnitude claims.
7. **Hierarchy and conflict resolution** (Amendment #4 B3): flag `robustness_concern=true` if primary Meaningful but ≥3/6 sensitivities Null; flag `hidden_signal_candidate=true` if primary Null but ≥3/6 sensitivities Meaningful. Primary classification retained for downstream action.
8. **Empty-cell handling** (SPEC §9.0): degenerate variance flagged; n_valid<25 → CI suppressed.
9. **Chain leakage audit** (Amendment #4 E5 / SPEC §11 assumption 12): report distribution of chain reuse counts; flag any chain in >20 conditions or top-5% concentration >40% of effect signal.

**Cross-universe reporting:** Three tables labeled by universe. Cross-universe patterns described qualitatively (e.g., "Lever 18 is Meaningful in all three universes") but **not aggregated into a master table.**

**Qualitative review:**
- Lever 18 L4: random sample of `reasoning_content` (n ≤ 20) for mechanism observations. Logged in parser provenance but not analyzed mechanistically.
- Per Amendment #4 D6 parser-as-instrument: report findings as "parser-mediated expressed detection behavior under v2 cascade," not as latent competence claims.

**Conditional follow-up triggers (SPEC §13):**
- Lever 8: if adjacent-level det(violated) diff ≥0.25 → cluster around cliff (per Amendment #4 C4)
- Lever 22: if T=0 vs T=0.5 diff ≥0.10 → sweep {0, 0.4, 0.7, 1.0}; also if mode-collapse at T=0 → test T=0.7+
- Other levers: no triggers pre-registered (Amendment #4 C1-defer)

**Final review:**
- Both authors independently review three effect tables.
- Discuss surprising findings.
- Sign final results block in `signoff/signoff_block.md`.

**If amendment triggered:** Follow Amendment Log process. Fresh signoff before any interpretation published.

---

## API Budget Estimate (Amendment #4 A5)

| Component | Calls | Est. cost |
|---|---|---|
| Pre-OLAT verification V4-Flash (already complete) | 250 | ~$0.50–1.50 (spent) |
| Pre-OLAT verification V4-Pro (already complete) | 250 | ~$1–3 (spent) |
| O4 schema acceptance test (already complete) | ~5 | ~$0.01 (spent) |
| Diagnostic phase F/G/H/I/J (already complete) | ~310 | ~$3 (spent) |
| **Standard 32-tok OLAT conditions** | ~2,800 (~1,400 per model) | ~$2.05 |
| **Lever 18 L2/L3 CoT conditions** | ~200 | ~$0.45 |
| **Lever 18 L4 thinking-enabled** | ~100 | ~$0.41 |
| **Lever 11 long-prompt conditions** | ~200 | ~$16.40 (dominates) |
| **OLAT subtotal** | **~3,200** | **~$19.31** |
| **Total program (diagnostic + OLAT)** | **~4,215** | **~$24** |

Range with ±50% uncertainty on Preview pricing: **$10–35 total**. Off-peak savings explicitly declined per author preference.

---

## Failure Mode Handling (Aligned with SPEC §6 + §14)

| Failure mode | Response |
|---|---|
| Day −2 verification S2/S5 triggered | **Expected under Path 1** per Amendment #4 D1. Floor characterization, not pathology. Document and proceed. |
| Day −2 verification S1/S3/S4/S6 triggered | Per `artifacts/verification_response.md`. Pause; both-author review; possible amendment. |
| API errors during Day 1 | Per SPEC §14: retry up to 3 attempts with exponential backoff (HTTP 429, 5xx, network/timeout); HTTP 4xx logged as `api_failure` without retry; schema rejection logged separately. Batch continues without termination. |
| `parse_failure_rate > 0.05` in any condition | Flag condition. Run sensitivity check. Report alongside effect sizes. Conditions with >10% combined parse + API failure flagged for inspection. |
| Lever 11 prompt exceeds API length limit | Switch to 100–150K token target. Document as plan deviation. Both-author signoff on deviation. |
| Lever 12 L3 schema rejected by DeepSeek | Debug schema sanitizer recursive enforcement (A4). If unresolvable, mark Lever 12 L3 as "deferred pending schema acceptance." Do not run partial schema. |
| V4-Flash or V4-Pro behavior shifts between Day −2 verification and Day 1 OLAT (Preview model risk) | Compare Day −2 baseline rate vs OLAT baseline-condition rate per model. If `|delta| > 0.05`, document as potential model drift confound. Run subset re-verification before proceeding. |
| Chain reuse concentration (Amendment #4 E5) | If any chain appears in >20 conditions OR top-5% contribute >40% of effect signal, run sensitivity excluding over-represented chains. |
| Empty cells (Amendment #4 B1/§9.0) | Degenerate variance (all-NO or all-YES): bootstrap CI=[point, point], flag `degenerate_variance=true`. n_valid<25: CI suppressed, flag `insufficient_n=true`. |

---

## Vacation Constraint

Target: Pre-registration signed before 2026-05-15. Execution during or after 2026-05-15–2026-05-29 as scheduling permits. **Do not compress pre-registration sign-off to meet deadline.** Amendment #5 has slipped the original timeline; this is the right tradeoff given the diagnostic and cross-model review findings.

---

## File Locations Reference

```
pre-registration/
├── SPEC.md                                                # locked at 0f7116…
├── BUILD_PLAN.md                                          # this file
├── signoff/signoff_block.md                               # Amendments #2–#5 awaiting signature
├── decisions/decision-sheet-v1.md                         # full resolution log
├── artifacts/                                             # 9 per-lever artifact files (locked)
├── scripts/
│   ├── o4_schema_acceptance_test.py                       # PASS verified
│   ├── day_minus_3_chain_pool.py                          # COMPLETE
│   ├── day_minus_2_verification.py                        # COMPLETE V4-Flash
│   ├── task1_reparse_day_minus_2.py                       # COMPLETE
│   ├── task2_day_minus_2_v4pro.py                         # COMPLETE V4-Pro
│   ├── diagnostic_F_cot_flash.py                          # COMPLETE
│   ├── diagnostic_G_v4pro_baseline.py                     # COMPLETE
│   ├── diagnostic_H_cot_v4pro.py                          # COMPLETE
│   ├── diagnostic_I_unbounded_cot.py                      # COMPLETE
│   ├── diagnostic_J_parser_sensitivity.py                 # COMPLETE
│   ├── reparse_diagnostics.py                             # COMPLETE
│   ├── step_distribution_check.py                         # COMPLETE
│   ├── day_0_chain_variants.py                            # TODO — Day 0 runner
│   ├── day_1_olat_batch.py                                # TODO — Day 1 dual-model runner
│   └── day_2_effect_table.py                              # TODO — Day 2 three-universe analysis
├── day_minus_3/                                           # populated
├── day_minus_2/                                           # populated (V4-Flash + reparse_v2)
├── day_minus_2_v4pro/                                     # populated
└── diagnostics/                                           # populated
```

External code dependency:
```
Ditto-5.3- Pokemon Diag/pokemon-v1-symbolic/detector/pokemon_rule_checker.py   # symbolic checker
Ditto V1/chains/real_v2/                                                       # 4,860 real chains
Ditto V1/chains/shuffled_v2/                                                   # 14,580 shuffled chains
Ditto-5.3- Pokemon Diag/pokemon-v1-symbolic/outputs/phase3_results_v4.csv     # checker verdicts
```
