# Project Ditto OLAT Design State Handoff

**Purpose:** This document captures the complete locked state of OLAT (One Lever At A Time) experimental design as of May 7, 2026, for handoff to a separate Claude session focused on operationalization and pre-registration drafting.

**Context for receiving Claude:** Project Ditto is an independent AI research program (Safiq Sindha + Myriam Sindha) studying constraint-reasoning detection in LLMs across game domains. The program has produced experiments v1–v5.1 with mixed results, culminating in a panel-wide null on v5.1's 22-model cross-provider replication. OLAT is the diagnostic experiment designed to identify which pipeline levers are responsible for v5.1's failure mode. This handoff captures the design state after ~3 weeks of careful methodology work, including 8 priority papers read with skeptical interrogation. Trust the locked decisions — they were arrived at deliberately and shouldn't be re-litigated without strong cause.

---

## Program State Summary

**Most recent experimental finding:** v5.1 panel-wide null (-0.067 log-odds, p=0.22) across 22 frontier models on Pokemon Showdown constraint detection. Three frontier models showed significant anti-detection (GPT-5, GPT-5.4-mini, Gemini 3 Flash Preview). One model showed pro-detection (GLM-5). Per-model intervention-response heterogeneity collapsed to zero — failure is structurally homogeneous, not idiosyncratic.

**v5.3 diagnostic finding:** Symbolic structural checker and LLM detection on Pokemon showed κ ≈ -0.001 — they're measuring different things. v1's LLM detection wasn't tracking the structural property the symbolic checker identifies. Open question: what was v1's LLM detection actually responding to?

**OLAT's role:** Diagnose which pipeline levers move the needle on V4-Flash for Pokemon constraint detection. Per-lever effect table feeds into Mew design (primary downstream path), program close-out characterization (secondary), and potential eval-adjacency commercial product (stretch).

---

## Decision Log — Recent Lever-Level Decisions

Confirmed in final design session before handoff (May 7-11, 2026). These decisions resolve ambiguities from earlier in the design process:

1. **Lever 2 (Field naming):** Test minimally at 2 levels (cryptic baseline vs semantic alternative). Reversed from initial skip recommendation per Sclar et al. literature analysis.
2. **Pre-OLAT verification n:** Confirmed at n=250 (within original 200-300 range).
3. **Lever 14 (Verification gates):** Folded into Lever 24 (Ground truth definition). Substantive overlap; ground truth testing now incorporates verification gate variations.
4. **Lever 5 (Selection criterion):** Confirmed 3 levels (random / difficulty-stratified / high cross-model variance).
5. **Pre-OLAT verification failure response:** Deferred to operationalization phase. To be specified during pre-registration drafting.
6. **Lever 10 (Adversarial chain construction):** **Cut.** Tests experimental design rather than model behavior. Chain construction locks at v5.1 baseline (single canonical violation type).
7. **Lever 13 (Abstraction taxonomy):** **Reduced to 2 levels** (all 8 abstractions vs 2-3 dominant). Substantive question retained; curve-shape question deferred.
8. **Lever 18 (CoT elicitation):** **Expanded to 4 levels** (none / "think step by step" / verification-style procedural / step-by-step structured list). Level 4 acts as interpretive anchor.

### Cross-model synthesis decisions (May 11, 2026)

After cross-model review across Claude, ChatGPT, and Gemini on 14 operationalization questions:

9. **Lever 11 (Cutoff position) REFRAMED:** Adopted Gemini's context-window ratio framing. Original chain-internal position framing didn't test Lost in the Middle's mechanism (chains are too short relative to V4-Flash's 1M token context window). New levels test position-in-prompt with distractor padding (5% / 50% / 95%).

10. **Lever 12 (Per-abstraction encoding) REFRAMED:** Adopted Gemini's structure-enforcement framing. New levels test free-form prose / format-restricting instructions / native function calling. This separates Tam et al.'s controversy (structure inherent vs prompt-enforced).

11. **Lever 19 (Strict grounding) REFRAMED:** Adopted Gemini's adversarial prover framing. Original off/standard/strict gradient risked triggering sycophantic over-refusal at Level 3. New Level 3 frames grounding as integrity verification under adversarial framing.

12. **All other levers (1, 2, 3, 4, 5, 9, 13, 15, 16, 17, 18, 24):** Locked at Claude+ChatGPT synthesis. Gemini's alternative framings considered but rejected as over-engineered, operationally infeasible, or testing different hypotheses than the diagnostic intent.

### Implementation review decisions (May 11, 2026)

After ChatGPT implementation review of locked operationalization summary:

13. **Global baseline configuration locked:** Single canonical defaults across all 17 levers, ≈ V1 setup with v5.1 baseline values. Eliminates baseline drift risk.

14. **Parser strategy locked:** Strict → permissive regex → first-token classification → log unparseable. Unparseable outputs excluded from primary analysis with sensitivity check including them.

15. **Five new risks documented:** Parse attrition bias, first-token over-rescue, prefix bias from truncation, distractor burden asymmetry, sampling-with-replacement leakage. Mitigations specified where applicable; remaining items documented as known limitations.

16. **Pre-OLAT verification response reclassified as blocker:** Originally deferred, but uncharacterized baseline behavior is reproducibility risk. Must be specified before pre-registration sign-off.

17. **Three cross-lever interactions documented as known limits:** Lever 1 × 11 (schema affects realized position), Lever 18 × 17 (CoT verbosity × strict format), Lever 24 × 5 (selection proxies derive from one ground truth universe).

18. **Six items confirmed as pre-registration blockers:** Lever 1 field lists, Lever 9 rendering templates, Lever 12 function calling schema, Lever 16 rule/context text, Lever 18 prompt text, Lever 19 adversarial framing text. Plus Pre-OLAT verification responses (#16). Total ~5-7 hours focused drafting work before sign-off.

### V4-Flash verification and Gemini synthesis (May 11, 2026)

After Gemini deep research output and V4-Flash documentation verification via web research:

19. **V4-Flash confirmed real and accessible.** Released April 24, 2026, model identifier `deepseek-v4-flash`, MIT licensed, hybrid CSA+HCA attention, 1M context. Preview status (behavior may shift before GA). Migration deadline: `deepseek-chat`/`deepseek-reasoner` aliases retire July 24, 2026. Architectural specs verified from Hugging Face model card and NVIDIA developer blog; 27%/10% efficiency figures re-attributed to V4-Pro vs V3.2 specifically (not V4-Flash).

20. **Lever 11 prompt length cap revised to 200-250K tokens** (from initial 50K). Based on verified V4-Flash MRCR retrieval decay: 0.82 at 256K → 0.49 at 1M. Capping below 250K stresses attention while remaining within saturated retrieval threshold, preserving positional effect-size measurement integrity.

21. **Lever 22 × Lever 18 API interaction locked.** All Lever 22 evaluations must execute with `thinking: {"type": "disabled"}` because V4-Flash silently nullifies temperature/top_p/penalties when thinking mode enabled. Verified against DeepSeek API documentation.

22. **Lever 18 restructured to separate prompt-induced CoT from native thinking.** L1-L3 use text-prompt CoT with `thinking: disabled`. L4 uses native thinking mode (`thinking: enabled`, `reasoning_effort: high`). Separation isolates prompt-induced reasoning scaffolding from architecture-native deliberation.

23. **Lever 17 max_tokens revised to per-level policy.** L1: 32 tokens (v5.1 baseline). L2: 64. L3: 128 (prevents JSON truncation). Documented baseline modification preserves L1 v5.1 baseline-matching while preventing structured output truncation in L2/L3.

24. **Lever 12 strict-mode API specifics locked.** L3 uses `/beta` endpoint, `"strict": true`, `additionalProperties: false`, all properties in `required`. Schema sanitizer required to strip unsupported parameters (minLength, maxLength, patternProperties, numerical bounds). Verified against DeepSeek strict-mode documentation.

25. **Pre-OLAT verification Scenario 6 added.** If V4-Flash baseline organically outperforms v4.5/v5.1 cohort (detection ≥0.80, gap ≥0.10), pause for both-author review. Formal amendment required — no auto-rollback. Preserves pre-registration discipline.

26. **`reasoning_content` preservation locked for Lever 12 × Lever 18.** When function calling intersects native thinking mode, dialogue manager must preserve and re-inject `reasoning_content` across sub-turns within a single user question. Verified API requirement.

27. **Three implementation gaps closed (May 11, 2026):**
   - **Lever 18 max_tokens LOCKED:** L1=32, L2/L3=512, L4=64 on content + unbounded reasoning_content. 512 chosen over 1024-2048 to constrain runaway hallucination while allowing 5-10 step reasoning traces matching task complexity. Documented baseline modification from v5.1's uniform 32-token cap; effect-size comparisons within Lever 18 remain valid.
   - **Lever 11 × Lever 16 anchoring LOCKED at Policy A:** Rules travel with chain (co-located). Cleanest isolation of position effect; anchoring rules separately would confound position with cross-context retrieval. When Lever 16 is at L1 baseline (no context), the bundle is just chain — consistent across positions.
   - **Lever 18 output anchor LOCKED at Option 1:** All four levels mandate explicit output anchor. L1/L4: "The answer is YES/NO". L2/L3: "Therefore, the answer is YES/NO". Parser strategy uses anchor as primary regex match. Documented baseline modification; pre-OLAT verification (n=250) characterizes anchor's effect on baseline detection rate.

28. **Cross-model synthesis phase formally closed.** Three rounds completed:
   - Round 1 (design): Claude + ChatGPT + Gemini operationalization of 14 open questions
   - Round 2 (implementation): ChatGPT implementation review with risk identification
   - Round 3 (verification): Gemini deep research + web-research verification of V4-Flash specifics + ChatGPT closing synthesis confirming readiness
   
   Architecture is locked. Remaining work is implementation-level freezing (SPEC drafting), not methodological reopening. Receiving Claude session should act as Formatting and Operationalization Assistant for the 7 blockers + watch item, not as Methodology Co-Designer.

These decisions reduced total levers being varied from ~19 to 18, and total OLAT conditions to ~36.

---

## Fully Locked Decisions

### Subject and domain
- **Subject model:** DeepSeek V4-Flash
  - **API model identifier:** `deepseek-v4-flash`
  - **Base URL:** `https://api.deepseek.com` (standard); `https://api.deepseek.com/beta` for strict-mode tool calling
  - **Architecture:** 284B total params, 13B activated per token (MoE), 1M token context window
  - **Attention:** Hybrid CSA (Compressed Sparse Attention with 4× compression, top-512 selection, 128-token sliding window) + HCA (Heavily Compressed Attention with 128× compression). FP4 Lightning Indexer.
  - **License:** MIT
  - **Release status:** Preview (released April 24, 2026). Behavior may shift before GA — record access date and routing target for reproducibility.
  - **Migration deadline:** `deepseek-chat` and `deepseek-reasoner` aliases retire July 24, 2026 at 15:59 UTC. Pre-registration references `deepseek-v4-flash` directly to avoid breakage.
  - **MRCR 8-needle retrieval:** ~0.82 through 256K tokens, decaying to 0.49 at 1M tokens for V4-Flash specifically (V4-Pro retains 0.59 at 1M). This decay drives the Lever 11 prompt length cap (see operationalization notes).
  - **Efficiency figures (re-attributed):** The 27% FLOPs / 10% KV cache figures from earlier handoff drafts are V4-Pro vs V3.2 specifically, not V4-Flash specific. The hybrid attention design carries to Flash but exact percentages differ.
- **Domain:** Pokemon Showdown (HF dataset, no API needed)
- **Skill tier:** mid-to-high (1500+ Elo or equivalent)

### Verified V4-Flash API behaviors (load-bearing for OLAT)

Confirmed against DeepSeek API documentation (May 11, 2026):

- **Thinking mode:** Enabled via `extra_body: {"thinking": {"type": "enabled"}}` or `reasoning_effort` parameter (Non-think / Think High / Think Max). When enabled, **temperature, top_p, presence_penalty, frequency_penalty are silently nullified** by the server. Setting `logprobs`/`top_logprobs` triggers a 400 error. Critical for Lever 22.
- **Tool calling × thinking mode:** When tool calls intersect thinking mode, `reasoning_content` must be preserved and re-injected across sub-turns within a single user question. Between user questions, clearing `reasoning_content` is recommended for bandwidth. Critical for Lever 12 × Lever 18.
- **Strict mode function calling:** Requires `/beta` endpoint, `"strict": true` in function definition, `"additionalProperties": false` on all object definitions, every property explicitly listed in `required` array. Server rejects schemas with `minLength`, `maxLength`, `minItems`, `maxItems`, `patternProperties`, numerical bounds.
- **JSON output mode:** `response_format: {"type": "json_object"}`. JSON mode and tool calling are mutually exclusive.
- **Recommended sampling for local deployments:** `temperature=1.0, top_p=1.0` per DeepSeek docs (when thinking mode disabled).

### Baseline configuration
- **Baseline methodology:** V1 original setup
  - Consistency-rating framing (pre-D-42 pivot)
  - Original chains from Pokemon Showdown HF dataset
  - Pre-amendment SPEC (no v3-era SPEC v1.1 changes like ResourceBudget in ACTIONABLE_TYPES, phase_ prefix strip)
  - 32-token output cap
- **Pre-OLAT verification run:** V1-on-Flash, n=250 chains, before OLAT proper
  - Outputs: detection rate, gap, effect size, 95% bootstrap CI
  - Cost: ~$1-3, time ~2-4 hours
  - Both authors sign off before OLAT design is finalized
  - If verification produces unexpectedly positive signal (gap > 0.05): pause and reconsider — V1-on-V4-Flash should be approximately null per v4.5 result
  - **Scenario 6 (added per Gemini catch):** If verification yields unexpectedly high detection rate (e.g., ≥0.80) with positive signal gap ≥ 0.10, V4-Flash may organically outperform the v4.5/v5.1 cohorts due to its optimized structured-data and logical-coding capabilities. Testing manipulation levers against an already-competent baseline compresses observable variance and creates artificial ceiling effects. **Response: pause for both-author review.** Formal amendment required — either (a) accept ceiling-limited OLAT with documented variance compression, (b) integrate Lever 5 (Selection Criterion) to systematically sample higher-difficulty chains until baseline returns to ~0.5 (constitutes scope amendment requiring sign-off), or (c) declare OLAT premise compromised and reconsider program direction. **Auto-rollback rejected** as breaking pre-registration discipline.

### Experiment parameters
- **Sample size per OLAT condition:** n=50
- **Statistical analysis:** paired effect size + bootstrap 95% CI + qualitative direction (no significance testing, no p-values)
- **Output format:** per-lever effect table ranked by magnitude
- **Pipeline structure:** 9 stages (data source, structuring, chain selection, chain construction, T value creation, prompt construction, LLM analysis, validation/ground truth, post review)

### Decision rules for results interpretation
- **Lever effect ≥ 0.10 absolute change in detection rate:** meaningful, worth follow-up in Mew design
- **Lever effect 0.03-0.10:** directional, file for future testing
- **Lever effect < 0.03:** null, skip in subsequent work

### Execution sequencing
- **Day 1:** Prepare all chain variants (compute only, no API)
- **Day 2:** Run batched API evaluations
- **Day 3:** Parse outputs, compute effect-size table, both-author review

### Logistics
- **Hosting:** Local folder on desktop hosts the test
- **Signoff:** Both-author signoff captured locally before any API calls
- **Amendments:** Any mid-flight amendment requires fresh signoff before resuming

### Downstream framing
- **Primary:** OLAT informs Mew design — per-lever effect table specifies which levers Mew should handle deliberately vs hold at OLAT-baseline values
- **Secondary:** Close out program with Ditto methodology characterization
- **Stretch:** Eval-adjacency commercial product (regime-sensitivity audit, routing-invariance check)

---

## Global Baseline Configuration

When testing a single lever, every other lever is held at this baseline. Effectively ≈ V1 setup with v5.1 baseline values across all levers.

| Lever | Default value when not being tested |
|---|---|
| 1 (Field schema) | L2 Standard (v5.1 baseline schema, ~12 fields) |
| 2 (Field naming) | L1 Cryptic (matching raw Showdown export format) |
| 3 (Numerical encoding) | L1 Raw values |
| 4 (Derived state markers) | L1 No markers |
| 5 (Selection criterion) | L1 Random selection from v5.1 pool |
| 8 (Chain length k) | k=5 (median of {3,5,8,12,20}) |
| 9 (Chain rendering format) | L1 v5.1 multi-line per turn |
| 11 (Cutoff position) | L1 First 5% of prompt (chain at start) |
| 12 (Per-abstraction encoding) | L1 Free-form prose |
| 13 (Abstraction taxonomy) | L1 All 8 abstractions |
| 15 (Question phrasing) | L1 Consistency rating (v1 baseline) |
| 16 (Constraint context content) | L1 No context |
| 17 (Output format demand) | L1 Binary YES/NO free-form |
| 18 (CoT elicitation) | L1 No CoT |
| 19 (Strict-grounding) | L1 No grounding instruction |
| 22 (Temperature) | L1 T=0.0 |
| 24 (Ground truth definition) | L1 Shuffled-vs-real (v5.1 baseline) |

---

## Documented Assumptions (Pre-Registered)

1. Results may not transfer to other models. V4-Flash is sub-frontier; Haiku, GPT-5, etc. may show different lever sensitivities. (Sclar et al. 2024 supports cross-model format-preference variability.)
2. Results may not transfer to other domains. Pokemon is the most-trained-on game in the program; PUBG, NBA, CSGO, RL may show different patterns.
3. Pokemon's training-data saturation may inflate baseline detection rates relative to less-saturated domains.
4. OLAT cannot detect interactions between levers; only main effects.
5. Compute-only levers can be tested cheaply (Stages 1-3, 8-9 mostly). API-bound levers limit scope (Stages 4-7).
6. Evaluation-awareness as potential confound (per Anthropic NLA work, May 2026). Frontier models in v5.1 panel may have responded differently because they recognized test context.
7. V4-Flash baseline under V1 methodology is established empirically by pre-OLAT verification run. Lever effects are perturbations from this empirically-established baseline.

### Risks identified during implementation review (added May 11, 2026)

8. **Parse attrition bias may be condition-specific.** Malformed outputs are unlikely to be random — some lever levels (particularly Levers 17/18/12 combinations) inherently induce more parse failures. Excluding unparseable outputs may itself become part of the measured effect. **Mitigation:** Track parse failure rate per condition and parser fallback stage reached per sample. Report alongside main effect sizes.

9. **First-token classification fallback may over-rescue malformed outputs.** Outputs like "No, the chain appears valid" could be misclassified as YES by naive first-token parsing, creating semantic inversion. **Mitigation:** Log fallback-stage provenance per sample. Sensitivity check excluding fallback-stage-rescued samples.

10. **Chain length truncation introduces prefix bias.** Truncating chains longer than k to first k events systematically excludes later violations and overrepresents early-turn violations. **Documented as known sampling bias** rather than mitigated — the Lever 8 design varies both length and which events are present.

11. **50K fixed prompt creates uneven distractor burden.** Short chains receive proportionally more distractor padding; long chains receive proportionally less. "Relative position" and "context burden" are not perfectly separable. **Documented as known interaction** — acceptable since the diagnostic intent is testing position-in-context, not isolating it from context burden.

12. **Sampling with replacement across conditions creates dependence structure.** Same chains may appear across multiple conditions, creating non-independence. **Documented as known dependence structure.** Track chain-condition assignment to support post-hoc leakage assessment.

13. **Ceiling/floor compression on detection rates near 0 or 1.** Effect sizes are bounded — a manipulation pushing detection from 0.02 to 0.04 looks like a 0.02 effect but the underlying mechanism could be substantial. **Mitigation:** Primary effects computed on raw rates; sensitivity check applies variance-stabilizing transformation (arcsine or logit) on rates close to bounds. Both reported.

---

## Lever Subset (18 levers being varied)

### OLAT-scale levers (test at full design — 3 levels for most, 5 levels for chain length)

| # | Lever | Levels | Stage | Operationalization Status |
|---|---|---|---|---|
| 1 | Field schema | 3 | 2 (Structuring) | Variants to be written |
| 4 | Derived state markers | 3 | 2 (Structuring) | Variants to be written |
| 5 | Selection criterion | 3 | 3 (Chain selection) | **Confirmed 3 levels.** See operationalization notes below |
| 8 | Chain length k | 5 | 4 (Chain construction) | **Locked levels:** {3, 5, 8, 12, 20} log-spaced |
| 9 | Chain rendering format | 3 | 4 (Chain construction) | See operationalization notes below |
| 12 | Per-abstraction encoding format | 3 | 5 (T value creation) | Variants to be written |
| 13 | Abstraction taxonomy used | 2 | 5 (T value creation) | **Reduced to 2 levels:** all 8 abstractions vs 2-3 dominant abstractions |
| 15 | Question phrasing | 3 | 6 (Prompt construction) | Variants to be written |
| 16 | Constraint context content | 3 | 6 (Prompt construction) | See operationalization notes below |
| 18 | CoT elicitation | 4 | 6 (Prompt construction) | **Locked at 4 levels:** none / "think step by step" / verification-style procedural / step-by-step structured list |
| 19 | Strict-grounding instruction | 3 | 6 (Prompt construction) | Variants to be written |
| 24 | Ground truth definition | 3 | 8 (Validation) | **Includes Lever 14 verification-gates folded in.** Variants to be written |

### Minimally-tested levers (2-3 levels each, lighter verification)

| # | Lever | Levels | Stage | Operationalization Status |
|---|---|---|---|---|
| 2 | Field naming | 2 | 2 (Structuring) | **Confirmed test minimally:** cryptic baseline vs semantic alternative |
| 3 | Numerical encoding | 2 | 2 (Structuring) | raw vs bucketed |
| 11 | Cutoff position | 3 | 4 (Chain construction) | start / middle / end |
| 17 | Output format demand | 3 | 6 (Prompt construction) | **Locked:** Free-form binary / loose structure / strict JSON |
| 22 | Temperature | 2 | 7 (LLM analysis) | **Locked:** T=0.0 / T=0.5 |

### Locked at baseline (no testing, single value)

- **Lever 20 (Few-shot exemplars):** Locked at 0-shot to match v5.1 baseline. Avoids few-shot formatting confound per Sclar et al.
- **Lever 21 (Model choice):** Locked at V4-Flash.
- **Lever 23 (Number of samples per chain):** Locked at k=1 (single-shot) to match v5.1 budget per Wang et al. self-consistency curves.

### Cut from OLAT (with rationale)

These levers were considered as candidates but explicitly cut from the OLAT working set:

- **Lever 10 (Adversarial chain construction):** **Cut.** Tests how violations are planted (type/position/severity). Most "experimental design" of the candidate levers rather than testing model behavior. v5.1 violations were already constructed deliberately. Cutting locks chain construction at v5.1 baseline (single canonical violation type, position determined by chain semantics). If OLAT shows methodology-sensitive results across other levers, adversarial construction becomes natural follow-up work — not part of diagnostic OLAT.

- **Lever 14 (Verification gates):** **Folded into Lever 24 (Ground truth definition).** Overlapping substantively — both concern symbolic-vs-LLM validation. Lever 24 now incorporates verification gate variations as part of ground truth testing.

### Skipped levers (not tested, classification justified)

- **Lever 6 (Match-level filters):** Skip. Standard data hygiene; not a methodological variable.
- **Lever 7 (Stratification):** Skip. Standard statistical methodology.
- **Lever 25 (Symbolic verifier integration):** Folded into Lever 24 (Ground truth definition).
- **Lever 26 (Parse strategy):** Skip. Engineering convention.
- **Lever 27 (Effect size metric):** Skip. Detection rate + gap locked as primary metric.
- **Lever 28 (Statistical test):** Skip. McNemar paired binary locked.

### Total OLAT conditions

- 12 OLAT-scale levers (most at 3 levels, one at 5 levels for chain length, one at 4 levels for CoT, one at 2 levels for taxonomy) = ~27 non-baseline conditions
- 5 minimally-tested levers (avg 2.5 levels) = ~8 non-baseline conditions
- 1 shared baseline
- **Total: ~36 OLAT conditions**

At n=50 chains per condition: ~1,800 evaluations. On V4-Flash batched: ~$2-4 total API spend. Cheap.

---

## Conditional Follow-Up Patterns (Pre-Registered)

Two levers have explicit follow-up triggers if main OLAT shows specific patterns:

### Lever 8 (Chain length k) — conditional follow-up

If main OLAT shows abrupt change between two adjacent levels (e.g., k=8 performs well, k=12 collapses), trigger follow-up with **Option B (Cluster around expected threshold):**
- Levels clustered around identified cliff range, e.g., {7, 8, 9, 10, 11, 12}
- Characterizes cliff width

If main OLAT shows monotonic decay or null across {3, 5, 8, 12, 20}: no follow-up needed.

**Documented alternative not chosen:** Option C (Two-phase: locate cliff with {3, 8, 20}, then cluster). Skipped because it breaks one-lever-at-a-time discipline.

### Lever 22 (Temperature) — conditional follow-up

If main OLAT shows meaningful effect (≥0.10 detection rate change) between T=0 and T=0.5, trigger follow-up sweeping full temperature range per Temperature paper:
- Levels: {0.0, 0.4, 0.7, 1.0}

If CoT (Lever 18) shows interaction with temperature in downstream analysis, the extremes (T=0.0 and T=1.0) may need separate testing per Temperature paper finding that CoT preferred extremes.

If V4-Flash shows mode-collapse or repetition patterns at T=0, T=0.7+ may be needed even without main effect trigger.

**CRITICAL API-level lock:** All Lever 22 evaluations must execute with `thinking: {"type": "disabled"}` explicitly set. V4-Flash silently nullifies temperature, top_p, presence_penalty, and frequency_penalty when thinking mode is enabled — the server does not error, parameters are ignored. Failure to disable thinking mode would cause the temperature sweep to measure noise rather than the intended sampling distribution change.

---

## Operationalization Notes for Specific Levers

These have specific framing that should carry forward to the SPEC. All decisions reflect cross-model synthesis (Claude + ChatGPT + Gemini) completed May 11, 2026.

### Lever 1 (Field schema)
- **Locked:** 3 levels — Minimal / Standard / Extended
  - Level 1 (Minimal): 5-7 core fields (player, move, target, damage, outcome)
  - Level 2 (Standard): v5.1 baseline schema (~12 fields)
  - Level 3 (Extended): 15-20 fields including derived properties (effectiveness multipliers, status flags)
- **Pre-registered prediction:** monotonic effect (more fields helps or hurts directionally); magnitude uncertain
- **Documented assumption:** Minimal set must contain all truly essential fields (violation-relevant fields) — to be validated during operationalization

### Lever 2 (Field naming)
- **Locked:** 2 levels — Rename all fields
  - Level 1 (baseline): Cryptic abbreviations matching raw Showdown export format
  - Level 2: Full descriptive semantic names throughout
- **Rationale:** Partial renaming introduces confound between renamed and unrenamed fields. Full rename is cleanest test of Sclar et al.'s naming sensitivity finding.

### Lever 3 (Numerical encoding)
- **Locked:** 2 levels — Raw vs semantic buckets
  - Level 1 (baseline): Raw numerical values
  - Level 2: Semantic buckets aligned with game mechanics (HP: Healthy >75% / Hurt 25-75% / Critical <25% / Fainted 0; PP: Full / Low / Empty; Type multipliers: Super effective / Neutral / Resisted / Immune)
- **Rationale:** Semantic anchoring per Razeghi et al. on pretraining frequency.

### Lever 4 (Derived state markers)
- **Locked:** 3 levels — No / Sparse natural-language / Dense prescriptive
  - Level 1: No markers. Chain renders raw events only.
  - Level 2: Sparse natural-language. Inline annotations in discursive style. E.g., "Player_1 uses Thunderbolt (this is Player_1's fourth use of Thunderbolt this match)."
  - Level 3: Dense prescriptive. Structured annotations. E.g., "Player_1 uses Thunderbolt [PP_remaining=4, status=normal, last_used_turn=12, total_uses_this_match=4]."
- **Documented limitation:** Levels 2 and 3 confound style (natural vs prescriptive) with density (sparse vs dense). Combined effect tested; isolated effects deferred to follow-up.
- **Pre-registered prediction:** markers move the needle (direction unknown); sparse natural-language hypothesized to outperform dense prescriptive per Teaching Claude Why.

### Lever 5 (Selection criterion)
- **Cannot use full IRT** — Fluid Benchmarking requires multi-model panel, infeasible for single-V4-Flash OLAT
- **Locked:** 3 levels — Use simpler difficulty-stratification proxies on v5.1 panel data
  - Level 1 (baseline): Random selection from v5.1 chain pool
  - Level 2: Difficulty-stratified selection. Bucket chains by mean detection rate across 22 v5.1 models; sample evenly across difficulty buckets (e.g., 0-0.2, 0.2-0.4, 0.4-0.6, 0.6-0.8, 0.8-1.0)
  - Level 3: High cross-model variance selection. Chains with highest variance in detection rate across 22 v5.1 models (most discriminating per Fluid Benchmarking concept)
- **Pre-registered prediction:** difficulty-stratified selection produces lower variance OLAT estimates than random; effect size on detection rates uncertain.

### Lever 9 (Chain rendering format)
- **Locked:** 3 levels
  - Level 1 (baseline): v5.1 multi-line per turn format
  - Level 2: Single-line per entity format
  - Level 3: Entity-centric grouping (all events for entity 1, then entity 2, etc.)
- **Pre-registered prediction:** entity-centric formats outperform time-centric per adjacent literature on sequential reasoning representation

### Lever 11 (Cutoff position) — REFRAMED per Gemini synthesis
- **Original framing rejected:** Defining position by event index within a 5-20 event chain doesn't test Lost in the Middle's mechanism, because the entire chain occupies a small fraction of V4-Flash's 1M token context window. The model can effortlessly process the isolated chain.
- **Locked reframing:** Test position by **context-window ratio** with distractor padding
  - Level 1: Chain placed in first 5% of total utilized prompt tokens (padding follows chain)
  - Level 2: Chain placed at 50% mark, surrounded by dense distractor tokens before and after to artificially inflate relative context position
  - Level 3: Chain placed in final 5% (padding precedes chain)
- **Total prompt length target locked: ~200-250K tokens** (revised upward from initial 50K based on V4-Flash MRCR retrieval decay verification). Rationale: V4-Flash MRCR 8-needle retrieval holds ~0.82 through 256K tokens and decays to 0.49 at 1M tokens. Capping below 250K stresses attention sufficiently to test position effects while remaining safely within the saturated retrieval threshold, preserving positional effect-size measurement integrity. Pushing toward 1M would confound position effects with CSA-induced retrieval collapse.
- **Distractor content locked:** Unrelated Pokemon Showdown content (other battles, different matchups). Documented rationale: other content types (generic text, repeated chain content) would be too easy to parse or differentiate, confounding position effects with content novelty.
- **Lever 11 × Lever 16 anchoring policy LOCKED (Policy A — rules travel with chain):** When Lever 16 is at L2 or L3 (constraint context present), the rules are co-located with the chain in all Lever 11 conditions. Distractor padding surrounds the {rules + chain} bundle, not the chain alone.
  - When chain is at 5%: rules immediately adjacent (also at ~5%), distractors fill 5-100%
  - When chain is at 50%: rules immediately adjacent to chain at ~50%, distractors fill 0-50% and 50-100%
  - When chain is at 95%: rules immediately adjacent (also at ~95%), distractors fill 0-95%
  - **Rationale:** Cleanest isolation of Lever 11's position effect. Anchoring rules separately would confound position with cross-context retrieval, mixing Lever 11 and Lever 16 effects. When Lever 16 is at L1 baseline (no context), the bundle is just chain — consistent across positions.
- **Pre-registered prediction:** If Lost in the Middle propagates to V4-Flash's hybrid attention architecture, expect U-shape with Level 2 worst. If hybrid attention mitigates, expect null across positions.

### Lever 12 (Per-abstraction encoding format) — REFRAMED per Gemini synthesis
- **Original framing rejected:** Structured vs Natural vs Hybrid conflates *what* the data looks like with *how* the model is instructed to produce it.
- **Locked reframing:** Test by structure enforcement mechanism
  - Level 1 (baseline): Free-form prose. Unconstrained natural-language abstraction encoding.
  - Level 2: Format-restricting instructions (FRI). Prompt explicitly requests structured format (e.g., "Output as JSON: {...}") via `response_format: {"type": "json_object"}` parameter with system instruction mandating JSON output.
  - Level 3: Native function calling. Use V4-Flash API's function-calling parameter via `/beta` endpoint with `"strict": true`.
- **Rationale:** Tam et al.'s controversy is partly about whether structured outputs are inherently bad or just bad when forced via prompts. Function-calling tier directly tests this.
- **V4-Flash API specifics (verified):**
  - L3 requires `/beta` endpoint (`https://api.deepseek.com/beta`) with `"strict": true` in function definition
  - JSON schema must include `"additionalProperties": false` on all object definitions
  - Every property must be listed in `required` array (even nominally optional ones)
  - Server rejects schemas containing `minLength`, `maxLength`, `minItems`, `maxItems`, `patternProperties`, numerical bounds
  - Test harness needs dedicated schema sanitizer to strip unsupported parameters before API submission
  - L2 and L3 are mutually exclusive at API level (JSON mode and tool calling cannot be combined in single request)
- **L3 × L18 interaction:** When function calling intersects thinking mode (Lever 18 L2/L3/L4), `reasoning_content` must be preserved and re-injected across sub-turns within a single user question. Dialogue manager must not strip `reasoning_content` between tool result and follow-up.
- **L3 × L17 interaction:** Function calling enforces structured payload via API tool definition; Lever 17 L1 (free-form YES/NO) is incompatible with Lever 12 L3 (function calling). When testing Lever 12 L3, Lever 17 baseline is overridden to demand boolean return within validated JSON schema payload.

### Lever 13 (Abstraction taxonomy used)
- **Locked:** 2 levels
  - Level 1 (baseline): All 8 abstractions
  - Level 2: Top 2-3 dominant abstractions selected by symbolic checker importance metrics
- **Operationalization detail:** Symbolic checker importance metrics needed. If unavailable, fallback to Option A (most frequent in v5.1 data).
- **Documented limitation:** Selecting only 2-3 abstractions may miss subtle violation patterns. Verify chosen subset covers all known violation types during operationalization.

### Lever 15 (Question phrasing)
- **Locked:** 3 levels — Methodology-aligned
  - Level 1 (baseline): Consistency rating (v1 baseline) — "Rate how consistent this chain is on a scale of 1-10"
  - Level 2: Violation detection (v5 D-42 pivot) — "Does this chain contain any rule violations? Answer YES or NO"
  - Level 3: Scaled likelihood — "What is the probability this chain contains a rule violation? Answer 0-100"
- **Output parsing note:** Different response formats (scale vs yes/no vs percentage) require consistent comparison logic. Thresholding scaled outputs to binary detection for cross-level effect size calculation.
- **Pre-registered prediction:** Question phrasing produces meaningful effect (per v5 D-42 pivot evidence); direction depends on which framing V4-Flash handles best.

### Lever 16 (Constraint context content)
- Teaching Claude Why finding reinforces: natural-language framing > rigid structured rules for generalization
- **Locked:** 3 levels
  - Level 1 (baseline): No constraint context. Just chain and question.
  - Level 2: Generic paragraph in natural language. E.g., "Pokemon battles follow specific rules. Each Pokemon has limited PP per move, can only act when not fainted, and cannot use moves that don't exist in their moveset."
  - Level 3: Structured rules in predicate form. E.g., "RULE_1: PP > 0 required for move usage. RULE_2: status != fainted required for action. RULE_3: move in moveset required for usage."
- **Pre-registered prediction:** natural-language framing (Level 2) outperforms structured rules (Level 3); both outperform no context (Level 1)

### Lever 17 (Output format demand)
- Tam et al. monotonicity hierarchy: free-form > loose structure > strict JSON for reasoning tasks
- Hybrid task regime (your task has both reasoning and classification elements)
- **Locked:** 3 levels
  - Level 1 (baseline): Binary YES/NO free-form
  - Level 2: Loose structure ("Answer: YES, Rule: respawn")
  - Level 3: Strict JSON (`{"detected": true, "rule_violated": "respawn"}`)
- **max_tokens policy (revised per Gemini catch):** 
  - L1: max_tokens = 32 (matches v5.1 baseline; sufficient for YES/NO)
  - L2: max_tokens = 64 (room for loose structured response)
  - L3: max_tokens = 128 (sufficient for well-formed JSON object with bracket closure)
  - **Documented baseline modification:** Original 32-token cap is preserved for L1 to match v5.1 baseline. L2/L3 expand cap because uniform 32 would trigger `finish_reason="length"` truncation errors for structured outputs, crippling those conditions. Per-level cap accepted over uniform 128 to preserve L1 baseline-matching with v5.1.
- **JSON output mechanism for L3:** Set `response_format: {"type": "json_object"}` with system instruction mandating JSON. Failure to set the API parameter causes the model to occasionally append markdown code blocks (e.g., ` ```json `), breaking automated regex parsing downstream.
- **Output parsing:** L3 final JSON validation operates exclusively against `message.content` field. When Lever 18 (CoT) is also enabled in thinking mode, `reasoning_content` resides separately and is not part of JSON constraint evaluation — parser ignores `reasoning_content` for L3 validity check.

### Lever 18 (CoT elicitation)
- Your -4 to -5 log-odds CoT degradation finding is contrary to Wei et al. baseline but not directly covered by Mind Your Step
- **Locked at 4 levels:**
  - Level 1 (baseline): No CoT. Direct answer to YES/NO question. Implement as `thinking: {"type": "disabled"}` to prevent native thinking mode from activating.
  - Level 2: "Think step by step" instruction. Standard CoT framing per Wei et al. Use text-prompt CoT without enabling native thinking mode (`thinking: disabled`).
  - Level 3: Verification-style procedural. Process instruction without forced verbalization. Tests Mind Your Step's verbal overshadowing hypothesis — does procedural instruction without explicit reasoning trace produce different behavior than verbal CoT? Use text-prompt without native thinking mode (`thinking: disabled`).
  - Level 4: Native thinking mode. Enable via `extra_body: {"thinking": {"type": "enabled"}}` or `reasoning_effort: "high"`. Captures V4-Flash's optimized continuous-space deliberation channel. Reasoning trace in `reasoning_content` field separate from `content`.
- **Critical design decision:** Levels 1-3 use text-prompt CoT framings (with thinking mode disabled) to test prompt-induced reasoning scaffolding. Level 4 uses the native API thinking parameter to test V4-Flash's optimized deliberation channel. This separation isolates prompt-induced CoT from architecture-native deliberation.
- **API behavior locks:**
  - L1/L2/L3 evaluations execute with `thinking: {"type": "disabled"}` to ensure prompt-level CoT manipulation is what's tested (and to keep temperature controllable when this lever is at baseline for Lever 22 testing)
  - L4 evaluations execute with `thinking: enabled` — accept that temperature/top_p/penalties are nullified for this level
  - For L4, `reasoning_content` from each turn is preserved within the same user question if tool calls occur (Lever 12 interaction). Between user questions, `reasoning_content` can be cleared for bandwidth.
- **max_tokens policy (LOCKED):**
  - L1: 32 tokens (matches v5.1 baseline exactly)
  - L2: 512 tokens (accommodates verbalized "think step by step" CoT)
  - L3: 512 tokens (accommodates verification-style procedural reasoning)
  - L4: 64 tokens on `content` field; `reasoning_content` unbounded by API design
  - **Documented baseline modification:** Per-level cap is a deliberate methodological modification from v5.1's uniform 32-token cap. Effect-size comparisons within Lever 18 remain valid (all CoT levels compared against each other). Cross-lever comparisons that aggregate Lever 17 effects across Lever 18 levels must account for the cap variation.
  - **Rationale for 512 over 1024-2048:** Sufficient for reasonable CoT length on this task (5-20 event chains with rule violations) while constraining runaway hallucination. Leaves room for ~5-10 step reasoning traces matching task complexity.
- **Output anchor (LOCKED):** All Lever 18 levels mandate explicit output anchor for parser consistency.
  - L1 anchor: `"The answer is YES"` or `"The answer is NO"` (fits within 32-token cap)
  - L2/L3 anchor: `"Therefore, the answer is YES"` or `"Therefore, the answer is NO"` (appears after CoT reasoning)
  - L4 anchor: `"The answer is YES"` or `"The answer is NO"` in `content` field (reasoning lives in `reasoning_content`)
  - **Documented baseline modification:** v5.1 baseline did not require an output anchor. Adding the anchor for OLAT Lever 18 testing is a deliberate methodological modification. Pre-OLAT verification (n=250) tests with anchor included to characterize baseline shift. If anchor materially changes baseline detection rate, the shift is documented but does not invalidate Lever 18 comparisons (anchor is constant across all four levels).
  - **Parser strategy:**
    1. Strict parse: regex `(Therefore, )?[Tt]he answer is (YES|NO)` (catches well-formed outputs across all levels)
    2. Permissive parse: regex `(answer is|answer:|conclusion:)\s*(yes|no)` case-insensitive (catches minor variations)
    3. First-token classification: look for YES/NO in first 10 tokens of `content` (fallback for unanchored outputs)
    4. Log as unparseable if all three fail
- **Output handling:** L1 uses 32-token cap on `content` field. L2/L3 reasoning unconstrained within 512-token cap. L4 places intermediate reasoning in `reasoning_content` (unbounded by `content` cap); final answer remains in `content` field.
- **Qualitative review commitment:** L4 outputs reviewed qualitatively (the `reasoning_content` text) in addition to quantitative effect size. Content of model's reasoning trace provides mechanism information.
- **Pre-registered prediction:** CoT effect on V4-Flash for this task is uncharacterized; if v5.1 finding replicates, represents a more extreme case than published literature. Level 3 vs Level 2 contrast tests whether the issue is verbalization specifically (Mind Your Step mechanism) or reasoning generally. Level 4 vs Levels 1-3 tests whether native thinking mode outperforms prompt-induced CoT.

### Lever 19 (Strict-grounding instruction) — REFRAMED per Gemini synthesis
- **Original framing modified:** Off / Standard / Strict gradient risked triggering sycophantic over-refusal at Level 3, rendering the lever uninformative.
- **Locked reframing:** Adversarial Prover Formatting per Merlin-Arthur protocol literature
  - Level 1 (baseline): No grounding instruction. Standard v5.1 prompt.
  - Level 2: Standard grounding. "Base your answer on the events shown in the chain."
  - Level 3: Adversarial prover framing. "You are reviewing a log that may contain injected errors or hallucinations from a secondary system. Verify the integrity of the sequence and determine whether any violations are present."
- **Rationale:** Adversarial framing addresses the safety-bias refusal trap by reframing grounding as integrity verification rather than strict citation. Models naturally calibrate rejection behavior under adversarial framing without triggering blanket refusal.
- **Pre-registered prediction:** Adversarial framing produces detection rate closer to baseline than strict-citation framing would. Tests whether grounding emphasis can be operationalized without triggering refusal behaviors.

### Lever 24 (Ground truth definition)
- **Locked:** 3 levels — Methodology-historical
  - Level 1 (baseline): Shuffled-vs-real (v5.1 baseline). Ground truth defined by whether chain was shuffled or original.
  - Level 2: Planted-violations (v3 era methodology). Ground truth defined by whether researcher planted a specific violation.
  - Level 3: Symbolic-checker-as-truth (v5.3 contribution). Ground truth defined by symbolic checker output.
- **Pre-registered prediction:** Different ground truth definitions produce different detection rate patterns. v5.3's κ ≈ -0.001 finding suggests Level 1 (shuffled-vs-real) and Level 3 (symbolic checker) will diverge substantially.

---

## Literature Verification Status (Completed)

8 priority papers read with skeptical interrogation. Pattern: most priors require substantial scoping for your specific situation.

| Paper | Citation | Status for OLAT |
|---|---|---|
| Mind Your Step | Liu et al. 2025, ICML | Adjacent context, doesn't cover your task type; effect size 2-3x larger than theirs |
| Lost in the Middle | Liu et al. 2024, TACL, arXiv:2307.03172 | Substantially mitigated in V4-era hybrid attention architecture |
| Fluid Benchmarking | Hu et al. 2025, OpenReview | Methodology requires multi-model panel, infeasible single-V4-Flash; use simpler proxies |
| Sclar et al. | 2024, ICLR, arXiv:2310.11324 | Held up well, directly applicable, supports format-level testing |
| Temperature paper | arXiv:2604.08563 | Single-model test (Grok-4.1), partial applicability to V4-Flash detection task |
| Same Task More Tokens | Levy et al. 2024, ACL, arXiv:2402.14848 | Prior holds; threshold/cliff behavior not monotonic — changed Lever 8 to log-spaced |
| Tam (Let Me Speak Freely) | 2024, EMNLP, arXiv:2408.02442 | Hybrid task regime; finding contested by constrained-decoding researchers; 32-token cap attenuates |
| Wei (CoT foundational) | 2022, NeurIPS, arXiv:2201.11903 | Doesn't cover your task; pattern of "reasoning tokens can be interference" supports modern interpretation |

**Anthropic blog posts filed for context (not OLAT-load-bearing):**
- NLA (May 7, 2026): Evaluation-awareness as confound for v5.1 interpretation; filed for Phase 3 / parallel exploration
- Teaching Claude Why (May 8, 2026): Pretraining-style formatting generalizes better; reinforces Lever 16 prediction; useful for Mew design (data quality > volume)

**Lower-priority papers NOT read** (judged unnecessary given pattern detection): Wang et al. (self-consistency), Razeghi et al. (numerical), Webson & Pavlick (question phrasing), Min et al. (in-context learning), Brown et al. (few-shot).

---

## Pre-Registration Blockers (Must Be Frozen Before Sign-Off)

These items define the actual experimental manipulations and must be frozen before pre-registration sign-off. Without them, the manipulations are not fully specified.

### Text/schema artifacts to freeze (6 items)

1. **Lever 1 exact field lists** — specify L1 (5-7 fields), L2 (~12 fields v5.1 baseline), L3 (15-20 fields) from v5.1 corpus
2. **Lever 9 exact rendering templates** — delimiter conventions, entity ordering, line break policy, multi-entity event rendering, null value handling, omitted field placeholders for L1/L2/L3. **Lever 11 × Lever 16 anchoring policy is locked at Policy A** (rules travel with chain); templates must encode this.
3. **Lever 12 function-calling schema** — JSON schema definition for L3 native function calling; verify against existing pipeline via Claude Code. Schema sanitizer must strip unsupported parameters (minLength, maxLength, patternProperties, numerical bounds) and enforce `additionalProperties: false` + all properties in `required`.
4. **Lever 16 exact rule/context text** — L2 paragraph text and L3 predicate rules with violation type → rule expression coverage table. Equivalence between L2 and L3 must be verified (same rules, different format). Templates must support Policy A co-location with chain (rules immediately adjacent to chain regardless of chain position).
5. **Lever 18 exact prompt text** — L2 "think step by step" wording, L3 verification-style procedural wording, L4 native thinking mode framing. Controlled for directive force across levels. **Output anchor locked across all levels:** L1/L4 use "The answer is YES/NO"; L2/L3 use "Therefore, the answer is YES/NO". **Per-level max_tokens locked:** L1=32, L2/L3=512, L4=64 on content + unbounded reasoning_content.
6. **Lever 19 exact adversarial framing text** — L3 adversarial prover instruction wording

### Procedural specifications to freeze (3 items)

7. **Pre-OLAT verification response specification** — what specific outcomes trigger pause vs proceed for the 6 documented scenarios. Each scenario needs explicit proceed/pause threshold:
   - Scenario 1 (unexpected positive signal): gap > 0.05 triggers pause
   - Scenarios 2-5 (the existing failure scenarios): explicit thresholds needed
   - Scenario 6 (V4-Flash organic competence): detection ≥0.80 AND gap ≥0.10 triggers pause + amendment (locked)

8. **Lever 13 fallback rule** — explicit deterministic branch for symbolic checker importance metrics availability. SPEC must lock as single branch: "If symbolic checker importance metrics are available at execution time, use top-3 by importance. If unavailable, use top-3 by v5.1 corpus frequency. Alphabetical tie-break on abstraction name." No runtime ambiguity permitted.

9. **Evaluation plumbing field definitions** — exact schemas for:
   - Parser provenance logging: `{condition_id, sample_id, parse_stage_reached, parse_success, fallback_used, raw_output}` — required for parse attrition audit
   - Chain-condition assignment tracking: `{chain_id, condition_id, sequence_position, sampling_method}` — required for leakage audit

**Total estimated drafting time:** 5-8 hours of focused work.

---

## Watch Item for SPEC Drafting

**Structure-enforcement × output-format layer disambiguation.** The handoff anticipates the big incompatibilities (Lever 12 L3 × Lever 17 L1 mutual exclusion, Lever 18 × Lever 17 max_tokens collision). But the SPEC must make explicit *which layer is being measured* in each condition:

- **Prompt instruction layer:** Lever 17 L1/L2/L3 (binary YES/NO, loose structure, strict JSON via text prompt with `response_format`)
- **API response mode layer:** `response_format: {"type": "json_object"}` parameter
- **Tool-calling schema layer:** Lever 12 L3 via `/beta` endpoint with `strict: true`

These three layers are partially orthogonal but not fully independent. The SPEC must annotate each condition with which layer is the manipulation target, and which layers are at baseline.

**Concrete example of the risk:** A condition labeled "Lever 17 L3 (strict JSON)" could be implemented at the prompt-instruction layer (text prompt requests JSON) or the API-response-mode layer (`response_format` parameter set). Without disambiguation, the same nominal condition could be implemented two different ways across the test matrix, creating a hidden compound manipulation.

**Resolution rule for SPEC:** Every condition row in the OLAT matrix should explicitly list:
- Prompt text used (with anchoring policy applied)
- `response_format` parameter value
- `tools` parameter value (function definitions if any)
- `thinking` parameter value
- `max_tokens` parameter value

This makes each condition reproducible from the SPEC alone and forces explicit disambiguation of which layer is being manipulated.

## Cross-Lever Interactions

Documented interactions where lever testing may produce confounded results:

### Resolved through ordering or design

- **Lever 9 × Lever 11:** Context-window ratio for Lever 11 computed after Lever 9 rendering (token count varies by rendering format).
- **Lever 12 × Lever 17:** Parser must distinguish failure modes between function-call payloads (Lever 12 L3) and strict JSON text completions (Lever 17 L3). Distinct parsers per output type. Lever 12 L3 (function calling) and Lever 17 L1 (free-form YES/NO) are API-incompatible; when testing Lever 12 L3, Lever 17 baseline is overridden to boolean JSON response.
- **Lever 16 × Lever 19:** Verify L3 of Lever 19 (adversarial prover) doesn't accidentally state rules that L1 of Lever 16 (no context) would otherwise lack. Independent inspection during operationalization.

### Resolved via V4-Flash API behavior (verified May 11, 2026)

- **Lever 22 × Lever 18 (CRITICAL):** V4-Flash silently nullifies temperature/top_p/penalties when thinking mode enabled. **Resolution:** All Lever 22 evaluations execute with `thinking: {"type": "disabled"}` explicitly set. When testing Lever 18, L1-L3 use `thinking: disabled` (prompt-induced CoT only); L4 uses `thinking: enabled` (native thinking mode). When Lever 22 is at baseline (T=0) and Lever 18 is being tested at L4, accept that temperature is effectively non-deterministic.
- **Lever 12 × Lever 18 (CRITICAL):** Function calling × thinking mode requires `reasoning_content` preservation across sub-turns within a single user question. **Resolution:** Dialogue manager hard-codes preservation of `reasoning_content` field when Lever 12 L3 (function calling) intersects Lever 18 L4 (native thinking). Between user questions, clearing `reasoning_content` is recommended for bandwidth but not required for correctness.
- **Lever 17 × Lever 18:** JSON validation (Lever 17 L3) operates on `message.content` field only. When Lever 18 L4 is active, `reasoning_content` resides separately and is not subject to JSON constraint evaluation.

### Documented as known interactions (not fully isolated)

- **Lever 1 × Lever 11:** Schema changes token count, which affects realized context ratio. Realized position may drift across schema conditions even with fixed nominal ratios. **Mitigation:** Compute realized context ratio after Lever 1's schema is applied; log per-condition realized positions.
- **Lever 18 × Lever 17:** Reasoning-heavy CoT prompts (L4 native thinking) may produce verbose `reasoning_content`. Strict output formatting (Lever 17 L3 JSON) is enforced on `content` field separately, so no direct collision, but interpretation requires distinguishing reasoning trace verbosity from final output format compliance.
- **Lever 24 × Lever 5:** Difficulty stratification and variance proxies derive from v5.1's shuffled-vs-real ground truth. Chains "difficult" under one ground truth may not be difficult under symbolic-checker truth. Documented as known limitation; selection proxies are uniform across ground-truth conditions by design.
- **Lever 1 × Lever 4:** Marker availability depends on field schema. When testing Lever 4, schema is at baseline. When testing Lever 1, markers are at baseline. Cross-effects deferred to follow-up.
- **Lever 15 × Lever 17 × Lever 18:** Response channel shape varies. Parser strategy and threshold mappings provide unified handling.
- **Lever 24 × all analyses:** Each ground truth definition is its own evaluation universe. Cross-lever comparisons within each universe; no cross-universe aggregation.

## Remaining Work to OLAT Execution

### Pre-registration sign-off requirements (5-7 hours focused work)

**Blockers must be frozen** (see Pre-Registration Blockers section above):
- 6 lever-level text/schema artifacts
- 1 verification response specification

### Implementation-stage operationalization (acceptable to defer)

These are operational infrastructure rather than manipulation definitions:

1. **Lever 5 data processing pipeline** — v5.1 raw data archive at commit 7033cb1 processing for difficulty stratification and cross-model variance proxies
2. **Lever 13 importance metric extraction** — symbolic checker importance metrics, with fallback to v5.1 corpus frequency
3. **Parser provenance tracking** — implement logging of fallback-stage reached per sample (added per ChatGPT review)
4. **Chain-condition assignment tracking** — log which chains appear in which conditions for post-hoc leakage assessment (added per ChatGPT review)

### Pre-registration drafting (4-6 hours)

- SPEC document combining all locked decisions
- Lever-by-lever operationalization with exact variants
- Pre-registered predictions and conditional follow-up triggers
- Documented assumptions (now 13 items)
- Decision rules for results
- Both-author signoff blocks

### Execution (2-4 days)

- Pre-OLAT verification run: 1-2 hours execution + analysis
- Main OLAT execution: 1-2 days batched
- Analysis and effect-size table: 1-2 days

### Total realistic timeline

- 1-2 weeks of focused work from current state to OLAT results
- Vacation 5/15-5/29 is constraint
- **Recommended sequencing:** Lock pre-registration before vacation, execute after

---

## Tools and Resources Available

- Frozen prompt corpus from v5.1
- Per-cell data pipelines (PUBG, NBA, CSGO, RL, Poker, Pokemon — Pokemon being primary)
- Chain construction and translation infrastructure
- Violation injectors
- Statistical analysis pipeline (paired McNemar, Bonferroni, BH-FDR, bootstrap CI)
- Decision log discipline (D-44 from v5)
- scripts/reasoning_control_experiment.py
- v5.3 symbolic checker (98% accuracy on Pokemon chains) — available for Lever 24 ground truth comparison
- Local desktop folder for test hosting
- v5.1 raw data archive at commit 7033cb1 — usable for Lever 5 difficulty stratification

---

## Posture for Receiving Claude

**What to do:**
- Help operationalize the lever variants (write specific prompt text, format specifications)
- Help draft the pre-registration document structure
- Flag inconsistencies or gaps in the locked design
- Push back if proposed operationalizations don't match what's locked above
- Respect the literature analysis pattern — the priors are calibrated, don't re-borrow them wholesale

**What NOT to do:**
- Don't re-litigate locked decisions without strong cause
- Don't introduce new levers or change lever counts without explicit user direction
- Don't override conditional follow-up patterns
- Don't soften the decision rules or sample size requirements
- Don't invent literature citations — what's verified is documented above; treat anything else as needing verification

**Authorship discipline:**
- Both authors (Safiq + Myriam) sign off on pre-registration before API calls
- Synthesis writing is reserved for Safiq and Myriam, not Claude
- Internal documents may credit Claude infrastructure; public artifacts do not credit AI co-authorship

**The 5/15-5/29 vacation context:** Aim for pre-registration locked before 5/15. Execution can happen during or after vacation as scheduling permits. Don't push for compressed timeline if it sacrifices the pre-registration discipline that's been carefully built.
