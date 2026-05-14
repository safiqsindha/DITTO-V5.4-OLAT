# Project Ditto OLAT — Pre-Registration SPEC

**Version:** DRAFT — pending both-author signoff
**Date drafted:** 2026-05-11
**Authors:** Safiq Sindha, Myriam Sindha
**Status:** Awaiting resolution of open items (see Section 12) before sign-off

---

## 1. Program Context

Project Ditto is an independent AI research program studying constraint-reasoning detection in LLMs across competitive game domains. Experiments v1–v5.1 produced mixed results culminating in a panel-wide null (−0.067 log-odds, p=0.22) across 22 frontier models on Pokémon Showdown constraint detection, with v5.3 showing κ ≈ −0.001 between the symbolic structural checker and LLM detection — indicating they measure structurally different properties. OLAT (One Lever At A Time) is the diagnostic experiment designed to identify which specific pipeline levers are responsible for v5.1's failure mode. OLAT tests DeepSeek V4-Flash on 18 pipeline levers using a single-lever isolation design; the resulting per-lever effect table feeds into Mew design (primary downstream path), program close-out characterization, and potential eval-adjacency commercial product.

---

## 2. Subject Model

**Per Amendment #3 (2026-05-12, B3 decision):** Two subject models. Diagnostic evidence (Diag F/G/H/I) showed V4-Flash and V4-Pro operate in **different detection regimes** under CoT: V4-Flash produces strong-but-over-flagging detection (gap improves substantially via increased violation flagging, with a concomitant rise in false positives on intact chains); V4-Pro produces approximately balanced detection (more conservative; moderate true-positive rate with comparable specificity). This regime difference makes the cross-model comparison a substantive OLAT finding rather than a redundant replication. Running both doubles API spend (~$15–25 total) and produces capability-tier evidence on how lever effects propagate across detection regimes.

| Property | V4-Flash (primary, v5.1 panel continuity) | V4-Pro (secondary, capability-scaling) |
|---|---|---|
| API identifier | `deepseek-v4-flash` | `deepseek-v4-pro` |
| Base URL (standard) | `https://api.deepseek.com` | `https://api.deepseek.com` |
| Base URL (strict tool calling) | `https://api.deepseek.com/beta` | `https://api.deepseek.com/beta` |
| Architecture | 284B total params, 13B activated/token (MoE), 1M token context window | (Pro architecture details to be confirmed via API at execution time) |
| Attention | Hybrid CSA (4× compression, top-512 selection, 128-token sliding window) + HCA (128× compression). FP4 Lightning Indexer. | Same family; specifics confirmed at run-time |
| License | MIT | MIT |
| Release status | Preview (released 2026-04-24). Behavior may shift before GA. | Preview; behavior may shift before GA. |
| Migration deadline | `deepseek-chat` / `deepseek-reasoner` aliases retire 2026-07-24 at 15:59 UTC. SPEC references `deepseek-v4-flash` directly. | Same deadline applies. |
| MRCR 8-needle retrieval | ~0.82 through 256K tokens, decaying to 0.49 at 1M tokens | Higher capability tier expected; not measured at SPEC-time |
| Diagnostic role | V1-minimal baseline = rigid NO-floor (gap −1.000 at n=250, replicates v5.1 panel null). CoT shifts to **over-flagging detection regime**: large gap improvement via increased violation flagging plus increased false-positive rate on intact chains. | V1-minimal baseline = less-rigid NO-floor (gap −0.757 at n=250, YES_rate 13%; some attempts to reason within the 32-token cap). CoT shifts to **approximately balanced detection regime**: moderate true-positive and true-negative rates without the FP escalation seen on Flash. |

### Verified V4-Flash API behaviors (load-bearing)

- **Thinking mode:** `extra_body: {"thinking": {"type": "enabled"}}` or `reasoning_effort` parameter. When enabled, temperature / top_p / presence_penalty / frequency_penalty are **silently nullified** server-side. Setting `logprobs`/`top_logprobs` triggers 400 error.
- **Tool calling × thinking mode:** `reasoning_content` must be preserved and re-injected across sub-turns within a single user question when function calls intersect thinking mode.
- **Strict mode function calling:** Requires `/beta` endpoint, `"strict": true`, `"additionalProperties": false` on all object definitions, every property in `required`. Server rejects: `minLength`, `maxLength`, `minItems`, `maxItems`, `patternProperties`, numerical bounds.
- **JSON output mode:** `response_format: {"type": "json_object"}`. Mutually exclusive with tool calling.
- **Recommended sampling:** `temperature=1.0, top_p=1.0` for local deployments when thinking mode disabled.

---

## 2.5 Diagnostic Phase Findings (Pre-OLAT Verification + Diagnostics F/G/H/I/J)

The OLAT architecture incorporates findings from five diagnostic runs (~$5 total API spend) conducted 2026-05-11 through 2026-05-12. These findings established:

**Finding 1 — V1-minimal NO-floor across V4 family.**
Day -2 V4-Flash V1-minimal at k=15 produced gap=−1.000 (100% NO output, n=250, parser-confirmed under both v1 and v2 cascades). Day -2 V4-Pro V1-minimal produced gap=−0.757 (87% NO output, 13% YES, n=250). The floor is configurational (property of V1-minimal framing) rather than model-specific. This finding mechanistically explains v5.1's panel-wide null: 22 models all anchored to default-NO under V1-minimal framing.

**Finding 2 — CoT escapes the floor with model-specific regime.**
Diag F (V4-Flash + CoT) shows substantial gap improvement via increased violation flagging accompanied by elevated false-positive rate on intact chains. Detection regime: over-flagging. Diag H/I (V4-Pro + CoT) shows moderate gap movement with approximately balanced specificity/sensitivity. Detection regime: balanced. Both models break the floor with CoT but in qualitatively different ways.

**Finding 3 — Parser cascade is a substantive measurement instrument.**
Diag J showed v1 parser (3-stage) missed 60-90% of valid model responses on CoT conditions due to markdown-decorated answer formats (`**Answer:** YES`). v2 parser (4-stage with markdown tolerance and last-token scan) achieves 90-100% parsed_rate across all diagnostic configurations. The v1 → v2 transition produced gap-magnitude shifts up to 0.4+ on CoT conditions and sign changes on V4-Pro CoT measurements. Parser is therefore locked as a measurement instrument; future revisions are methodology amendments.

**Finding 4 — max_tokens empirical calibration.**
Diag I at max_tokens=4096 produced finish_reason=stop for all 40 responses across both models. Empirical max completion: 701 tokens (V4-Flash CoT) and 540 tokens (V4-Pro CoT). max_tokens=1024 provides ~30% headroom over observed max for both models without overshoot. Original 512-token cap (pre-Amendment-3) produced 90% truncation on V4-Flash CoT.

**Finding 5 — Cross-model baseline asymmetry.**
V4-Flash and V4-Pro show different baseline competences. V4-Flash is at absolute floor (0% violated detection). V4-Pro shows partial baseline competence (14% violated detection; 6 responses attempted reasoning within 32-token cap). Effect-size comparisons across the two models test "movement from per-model floor" rather than "trajectory toward shared endpoint."

**These five findings collectively shifted the OLAT design from "single-model lever-importance ranking" to "dual-model regime-characterization with parser-as-instrument and empirically-calibrated max_tokens." Amendments #1 (field coverage), #2 (Lever 8 reanchoring), and #3 (dual-model, parser v2, max_tokens, cross-model framing) implement these shifts.**

---

## 3. Domain

- **Domain:** Pokémon Showdown (HF dataset, no API needed)
- **Skill tier:** Mid-to-high (1500+ Elo or equivalent)
- **Ground truth baseline:** Shuffled-vs-real (v5.1 baseline, Lever 24 L1)

---

## 4. Experiment Parameters

| Parameter | Value |
|---|---|
| Sample size per condition | n=50 chains |
| Total conditions | ~36 (see Section 7) |
| Total evaluations | **3,200** (Amendment #6: dual-model 1,600 V4-Flash + 1,600 V4-Pro; 64 conditions × n=50 per §7.5 after Lever 5 L2/L3 dropout) |
| Estimated API cost | **~$15–35** (Amendment #4 recomputation; Lever 5 dropout saves ~$0.15, negligible against the ~$16 Lever 11 driver) |

**API cost estimate breakdown (Amendment #4, 2026-05-12):**

Pricing assumptions (V4-Flash and V4-Pro are Preview; production pricing not yet finalized — assumptions approximated from V3-era DeepSeek tiers at peak hours, cache-miss):
- V4-Flash: ~$0.27/M input tokens, ~$1.10/M output tokens
- V4-Pro: ~$0.55/M input tokens, ~$2.19/M output tokens
- Off-peak discount not applied (declined per author preference)

Per-condition-class breakdown (per model; dual-model doubles):

| Class | Calls (per model) | Input tokens (each) | Output tokens (each) | V4-Flash cost | V4-Pro cost |
|---|---|---|---|---|---|
| Standard 32-tok conditions (most levers) | ~1,400 | ~1,775 | ~1.5 | ~$0.67 | ~$1.37 |
| Lever 18 L2/L3 (CoT, max_tokens=1024) | 100 | ~1,775 | ~500 | ~$0.11 | ~$0.21 |
| Lever 18 L4 (reasoning_content unbounded) | 50 | ~1,775 | ~2,050 | ~$0.13 | ~$0.28 |
| Lever 11 long-prompt (~200K input) | 100 | ~200,000 | ~1.5 | ~$5.40 | ~$11.00 |
| **Per-model subtotal** | **~1,650** | | | **~$6.31** | **~$12.86** |

**Dual-model total: ~$19.17.** Range with ±50% uncertainty (Preview-pricing variance + cache-rate sensitivity + actual response-length distribution): **$10–35**.

**Cost drivers:** Lever 11 long-prompt conditions dominate (~$16 of total). Verify actual Preview pricing before Day 1 execution; off-peak window 16:30–00:30 UTC offers ~50% reduction if author preference changes.
| Statistical analysis | Paired effect size + bootstrap 95% CI + qualitative direction |
| No significance testing | No p-values; no NHST |
| Primary estimand | **Gap** = detection_rate(violated) − detection_rate(intact), per condition per model |
| Effect size | **(condition gap) − (baseline gap)**, per lever per model (primary OLAT output) |
| Secondary estimands | Detection_rate(violated) and detection_rate(intact) reported separately for interpretive decomposition |
| Cross-model output | **Capability-tier delta** = effect_size_Flash − effect_size_Pro, per lever |
| Tie-breaking when secondary diverges from primary | Primary estimand governs classification; secondary estimands provide diagnostic context but do not override classification |
| Output format | Per-lever effect table ranked by magnitude |
| Pipeline stages | 9 (data source → structuring → chain selection → chain construction → T value creation → prompt construction → LLM analysis → validation/ground truth → post review) |

---

## 5. Global Baseline Configuration

When testing any single lever, all other levers are held at the following defaults. Effectively ≈ V1 setup with v5.1 baseline values. Baseline is the V1 original setup: consistency-rating framing (pre-D-42 pivot), original chains from Pokémon Showdown HF dataset, pre-amendment SPEC (no v3-era changes), 32-token output cap.

**Note on "V1 methodology":** V1 (Ditto V1 codebase) used a **next-action prediction task** ("propose the next action for your side at step K+1"), not a consistency rating or violation detection task. "V1 methodology" in this SPEC refers specifically to V1's **chain format** (abstract constraint language from translation.py: 6 event types, unit_A–F labeling, action_1–4 labeling, pre-rendered JSONL) and **minimal setup** (cryptic names, 32-token cap, T=0.0, random selection, no CoT). The violation detection question framing (YES/NO) was introduced in the v3–v5 lineage. The "consistency-rating framing" (Lever 15 L1) refers to a pre-D-42 pilot design, not the V1 production task.

| Lever | Default when not being tested |
|---|---|
| 1 (Field schema) | L2 Standard (v5.1 baseline schema, ~18 fields — all 6 event types rendered) |
| 2 (Field naming) | L1 Cryptic (raw Showdown export format) |
| 3 (Numerical encoding) | L1 Raw values |
| 4 (Derived state markers) | L1 No markers |
| 5 (Selection criterion) | L1 Random selection from v5.1 pool |
| 8 (Chain length k) | k=15 (Amendment #2 baseline — median of {5,10,15,20,30}; anchored to empirical violation-step median of 14) |
| 9 (Chain rendering format) | L1 v5.1 multi-line per turn |
| 11 (Cutoff position) | L1 First 5% of prompt (chain at start) |
| 12 (Per-abstraction encoding) | L1 Free-form prose |
| 13 (Abstraction taxonomy) | L1 All 8 abstractions |
| 15 (Question phrasing) | **L2 YES/NO violation detection (de facto baseline).** L1 Consistency rating is reserved as a level only when Lever 15 itself is the lever under test. The Lever 18 baseline override is the SPEC's load-bearing example: any condition that requires a YES/NO classification format implicitly holds Lever 15 at L2. (Per Amendment #4 clarification.) |
| 16 (Constraint context content) | L1 No context |
| 17 (Output format demand) | L1 Binary YES/NO free-form |
| 18 (CoT elicitation) | L1 No CoT |
| 19 (Strict-grounding) | L1 No grounding instruction |
| 22 (Temperature) | L1 T=0.0 |
| 24 (Ground truth definition) | L1 Shuffled-vs-real (v5.1 baseline) |

**Footnote on Lever 15 baseline (Amendment #4 clarification):** The "L1 Consistency rating" baseline label reflects pre-D-42 program history. In actual SPEC execution, every non-Lever-15 condition uses L2 (YES/NO violation detection) because the locked output anchor and parser cascade assume YES/NO classification. L1 is operative only when Lever 15 is the lever under test and the SPEC accepts the resulting parser/scoring asymmetry (1-10 rating output thresholded to binary). Pre-Amendment-3 Tasks 1 and 2 (Day -2 verification on both V4-Flash and V4-Pro) used Lever 15 at L2 — confirming this is the de facto baseline.

---

## 6. Pre-OLAT Verification Protocol

**Floor-effect baseline locked per Amendment #3 (2026-05-12).** The Day −2 verification at k=15 produced 100% NO output on V4-Flash V1-minimal (gap=−1.000). This finding was **confirmed under the v2 4-stage parser cascade** (Pre-Amendment-3 Task 1, 2026-05-12): re-parsing the original 250 V4-Flash raw responses produced identical metrics (parsed_rate=1.000, gap=−1.000, 0 rescues, 0 reclassifications). The 100% NO finding is parser-confirmed, not a parser artifact — the floor is genuine model behavior under V1-minimal framing. The full V4-Pro Day −2 verification at n=250 (Pre-Amendment-3 Task 2, 2026-05-12) produced gap=−0.757 with 95% CI [−0.838, −0.668], YES_rate=0.130, parsed_rate=0.984; consistent with the n=50 Diag G result (8% YES) and confirming V4-Pro's less-rigid-but-still-strong-floor behavior. **Path 1 (floor-effect baseline) holds across both V4 family members.** Detection-rate metrics, gap, and Cohen's h are computed against the per-model empirical floor; OLAT measures which levers move each model off its floor and how the regime differs across capability tier.

### S2 Handling Under Path 1 (Amendment #3 — Option (ii))

The S2 trigger (gap < −0.05) fires when baseline detection is meaningfully worse than chance. Under Path 1, the per-model baseline is **expected** to fire S2 — this is floor characterization, not pathology. S2's purpose during Day −2 was to catch unexpected baseline behavior; Path 1 confirms the strongly-negative baseline is the expected V1-minimal characterization across V4-Flash (gap=−1.000) and V4-Pro (gap=−0.757). The S2 trigger on Day −2 V4-Pro is documented and accepted; no methodology amendment follows from it.

**Anti-detection scenarios in OLAT proper:** Individual OLAT conditions are evaluated against per-model baseline gap via standard effect-size analysis. A condition producing detection meaningfully worse than per-model baseline surfaces as a negative effect size in the OLAT effect-size table — no separate S2 trigger applies post-baseline. S1, S3, S4, S6 retain their original Day-−2 semantics; S2 and S5 are reinterpreted under Path 1 (see below).

**S5 reinterpretation under Path 1 (Amendment #4 — parallel to S2):** S5 (degenerate output: YES_rate > 0.95 OR NO_rate > 0.95) was written pre-Path-1 to catch unexpected anchor dominance. Under Path 1, V4-Flash baseline produces 100% NO output by design (the rigid NO-floor) and V4-Pro baseline produces 87% NO output. The V4-Flash baseline triggers S5 literally, but this is expected floor characterization, not anchor pathology. S5's purpose during Day -2 was to catch unexpected anchor effects; Path 1 reframes the strongly-skewed NO distribution as expected V1-minimal baseline behavior. S5 trigger on Day -2 baseline runs is documented and accepted; no methodology amendment follows from it. S5 retains its original semantics for OLAT proper — a non-baseline OLAT condition producing >0.95 YES or NO rate would still warrant pause.



**Run:** V1-on-Flash, n=250 chains, executed before OLAT proper.
**Outputs:** detection rate, gap, effect size, 95% bootstrap CI, parse failure rate, n_valid.
**Signoff requirement:** Both authors review and sign off on verification results before any OLAT conditions begin.

### Verification Scenarios

See `artifacts/verification_response.md` for full per-scenario specification. All six thresholds locked per O6 (decision-sheet-v1.md):

| Scenario | Trigger | Response |
|---|---|---|
| S1 — Unexpected positive signal | gap > +0.05 | PAUSE + both-author review + amendment |
| S2 — Unexpected anti-detection | gap < −0.05 | PAUSE + CI check + possible amendment |
| S3 — High parse failure rate | parse_failure_rate > 0.05 | PAUSE + failure taxonomy + parser fix |
| S4 — Incomplete run | n_valid < 200 | PAUSE + diagnose API/refusal cause |
| S5 — Degenerate output distribution | YES_rate > 0.95 OR NO_rate > 0.95 | PAUSE + anchor investigation |
| S6 — V4-Flash organic competence | detection_rate ≥ 0.80 AND gap ≥ 0.10 | PAUSE + formal amendment (Path A/B/C) |

**S3 rationale (tightened per O6):** V1 is the simplest condition in the entire OLAT matrix. >5% parse failures on V1-on-V4-Flash indicates parser fragility that will compound under OLAT stress conditions (Lever 12 L3, Lever 17 L3, Lever 18 L2/L3/L4). The original 0.20 threshold describes catastrophic breakage; 0.05 describes "good enough for OLAT."

---

## 7. Lever Operationalization

### 7.1 OLAT-Scale Levers (full 3+ levels)

#### Lever 1 — Field Schema
- **L1 (Minimal):** 10 violation-relevant fields (type, timestamp, resource, amount, decay, tool, state, recover_in, from_phase, to_phase). Covers all 9 active symbolic checker rules. See `artifacts/lever_01_field_schemas.md` for exact field list.
- **L2 (Standard, baseline):** ~18 fields — all 6 event types as rendered in v5.1 baseline (CoordinationDependency and OptimizationCriterion included). See `artifacts/lever_01_field_schemas.md`.
- **L3 (Extended):** 20 fields with derived properties (L2 + active_pair_by_step). See `artifacts/lever_01_field_schemas.md`.
- **Prediction:** Monotonic effect (direction uncertain); magnitude uncertain.
- **[RESOLVED — CONFIRM AT SIGN-OFF]:** L2 field schema derived from codebase inspection of translation.py, renderer.py, and v4_runner.py. All 6 event types rendered in v5.1 baseline prompt (confirmed: v4_runner.py reads chain["rendered"] with no event-type filtering). Effective L2 field count is ~18. See `artifacts/lever_01_field_schemas.md` for authoritative field list.

#### Lever 4 — Derived State Markers
- **L1 (baseline):** No markers. Chain renders raw events only.
- **L2:** Sparse natural-language inline annotations. Example: "Player_1 uses Thunderbolt (this is Player_1's fourth use of Thunderbolt this match)."
- **L3:** Dense prescriptive structured annotations. Example: "Player_1 uses Thunderbolt [PP_remaining=4, status=normal, last_used_turn=12, total_uses_this_match=4]."
- **Documented limitation and Mew application rule (Amendment #4):** L2 and L3 confound annotation style (natural vs prescriptive) with density (sparse vs dense). If Lever 4 effects are Meaningful, the directional interpretation cannot disentangle these two dimensions. **Mew design application rule:** A positive Lever 4 result is implemented in Mew as the specific operationalization tested (e.g., if L2 outperforms L1 by ≥0.10, Mew adopts L2's exact "sparse natural-language" template, not a derived "use natural language and sparsity" abstract principle). Isolating the natural-vs-prescriptive vs sparse-vs-dense contribution requires follow-up testing outside OLAT.
- **Prediction:** Markers move the needle; sparse natural-language hypothesized to outperform dense prescriptive (per Teaching Claude Why).

#### Lever 5 — Selection Criterion
- **L1 (baseline):** Random selection from v5.1 chain pool.
- **L2:** [DEFERRED per Amendment #6 — data unavailable] Originally: Difficulty-stratified by mean detection rate across 22 v5.1 models. Not executable: v5.1 22-model panel was run on NBA / Rocket League / CSGO / PUBG / Poker, not Pokemon. No per-chain Pokemon detection data exists at 22-model panel breadth.
- **L3:** [DEFERRED per Amendment #6 — data unavailable] Originally: High cross-model variance from v5.1 panel. Same data-availability blocker as L2.
- **Prediction:** N/A — L2 and L3 not executed in this OLAT.
- **Data-availability dropout rationale (Amendment #6):** Verified 2026-05-13 via cross-version search (Ditto V1 through V5.1 Final + V5.2 + V5.3). The V5.1 Final phase3_consolidated panel (81,460 rows, 22 models) covered only non-Pokemon cells. V5.2 d_1_4 has partial 2-model Pokemon data (Haiku + Sonnet on 1,200 chains, 600 overlap with OLAT pool) — too thin for 5-bucket stratification or meaningful variance ranking, and binary variance gives only 2 cross-model bins rather than the 22-model-panel-scale L3 envisioned. The SPEC's prior endogeneity note (Amendment #5 D3) flagged Lever 5 as low-confidence under v5.1 panel contamination; the data-availability gap is the structural surfacing of that endogeneity. Building a fresh 22-model Pokemon panel was considered and rejected — under V1-minimal framing (panel-faithful), most models would produce NO-floor responses (per Path 1), reproducing the contamination at higher cost. A CoT-framed panel would resolve the floor issue but redefine what Lever 5 measures, which is out of scope for this OLAT. Lever 5 retains only L1 (random selection) as executable; L2 and L3 are deferred pending a future panel build, which would warrant fresh pre-registration as a separate study.
- **Endogeneity note (Amendment #5 D3, retained for record):** Lever 5 L2 (difficulty-stratified) and L3 (high-variance) derive from v5.1 panel detection statistics. The v5.1 regime is now understood to be heavily contaminated by V1-minimal NO-floor behavior (per Diagnostic Findings Section 2.5). "Difficulty" and "cross-model variance" in this lever therefore measure sensitivity to *historically observed detectability under the v5.1 regime*, not intrinsic chain difficulty independent of the failure mode OLAT is diagnosing. The Amendment #6 data-availability dropout is the operational consequence of this endogeneity becoming structurally unresolvable.

#### Lever 8 — Chain Length k
- **L1:** k=5
- **L2:** k=10
- **L3:** k=15 (baseline)
- **L4:** k=20
- **L5:** k=30
- **Level anchoring (Amendment #2, 2026-05-12):** Levels reanchored to the empirical violation-step distribution in the v5.1 corpus. Per the Day -2 step-distribution check (see `day_minus_2/step_distribution_analysis.json`), violation_step in the n=250 sample has median=14, mean=17.8, p25=11, p75=24.5. Baseline at k=15 sits at the median (~50% of violations in-frame); k=5 anchors the floor (~4% visibility); k=30 captures the long tail (~90%+ visibility). Linear-ish spacing on the relevant operating range, not log-spaced as originally drafted — log-spacing centered well below the violation distribution and produced near-zero baseline detection at k=5 (Day -2 first run, deprecated). The new spacing is methodology-motivated: each level corresponds to a meaningful coverage band of the violation distribution.
- **Prediction (Amendment #4 — narrowed interpretation, supersedes saturation-curve framing from Amendment #2):** Detection rate is expected to follow a saturation curve in k. At k=5 (floor), detection_rate ≈ NO-bias rate (near zero on violated chains since violations are rarely in-frame). At k=10–15 the rate climbs as median-depth violations become visible. By k=20–30 the rate plateaus as the tail of late-step violations comes into frame. The empirical question is the *shape* of the saturation curve, characterizing **effective utilization of visible violation evidence** (not "reasoning depth" — k simultaneously changes visibility, compression ratio, recency, and distractor-to-signal proportion, so a cliff cannot be cleanly attributed to a single mechanism). Either shape carries diagnostic information about how the model processes evidence as it becomes available.
- **Conditional follow-up:** If a sharp cliff is observed between two adjacent levels → cluster around identified cliff range. If gradual monotonic saturation → no follow-up.

#### Lever 9 — Chain Rendering Format
- **L1 (baseline):** v5.1 multi-line per turn. See `artifacts/lever_09_rendering.md`.
- **L2:** Single-line per entity. See `artifacts/lever_09_rendering.md`.
- **L3:** Entity-centric grouping. See `artifacts/lever_09_rendering.md`.
- **Policy A (Lever 11 × Lever 16):** When Lever 16 ≠ L1, constraint rules co-locate immediately before chain. Distractor padding surrounds {rules + chain} bundle.
- **Prediction:** Entity-centric formats outperform time-centric (per adjacent literature on sequential reasoning).

#### Lever 12 — Per-Abstraction Encoding Format
- **L1 (baseline):** Free-form prose. Unconstrained natural-language abstraction encoding.
- **L2:** Format-restricting instructions (FRI). Prompt requests JSON: `response_format: {"type": "json_object"}` + system instruction mandating JSON output. max_tokens = 128.
- **L3:** Native function calling. `/beta` endpoint, `strict: true`, schema per `artifacts/lever_12_function_schema.json`.
- **L3 × L17 override:** When testing L3, Lever 17 baseline overridden from free-form YES/NO to boolean JSON response (API-level incompatibility).
- **L3 × L18 L4:** `reasoning_content` preserved across sub-turns per verified API requirement.
- **L3 thinking-mode constraint (verified 2026-05-12 via O4 diagnostic):** Lever 12 L3 calls must pass `extra_body={"thinking": {"type": "disabled"}}` on the `/beta` endpoint. Without this, `deepseek-v4-flash` defaults to thinking-mode enabled, and the server rejects `tool_choice="required"` with the error `'deepseek-reasoner does not support this tool_choice'`. Benign in the OLAT matrix because Lever 18 baseline (L1) already disables thinking; documented here as an explicit prerequisite for any condition that activates Lever 12 L3.
- **Schema sanitizer recursion (Amendment #4):** The schema sanitizer must recursively enforce DeepSeek strict mode requirements on all nested objects and arrays:
  - Every nested object: `additionalProperties: false`
  - Every property at every nesting depth listed in its containing object's `required` array
  - Recursive stripping of `minLength`, `maxLength`, `minItems`, `maxItems`, `patternProperties`, and numerical bounds from nested definitions
  - Verification: schema sanitizer outputs the post-sanitization JSON for inspection during O4 schema acceptance test
- **[LOCKED per O3]:** The 8 abstractions are: ResourceBudget_HP, ResourceBudget_PP, ResourceBudget_time, ResourceBudget_status, ResourceBudget_boost, ToolAvailability, SubGoalTransition, InformationState. See `artifacts/lever_12_function_schema.json`.
- **Rule-bearing vs dimensional-only distinction:** Six of the eight abstractions (ResourceBudget_HP, ResourceBudget_PP, ResourceBudget_time, ToolAvailability, SubGoalTransition, InformationState) are rule-bearing — symbolic checker rules exist for these dimensions. Two (ResourceBudget_status, ResourceBudget_boost) are assessment dimensions without violation rules. They appear in the Lever 12 function calling schema for completeness of the abstraction space. They will not generate violation events in the test set, and Lever 13 L2 (top-3 by importance or frequency) will naturally exclude them under either selection criterion. This is a documented feature, not a defect.

#### Lever 13 — Abstraction Taxonomy
- **L1 (baseline):** All 8 abstractions.
- **L2:** Top-3 dominant abstractions (locked at exactly 3 per Amendment #4). Selection per deterministic rule: if symbolic checker importance metrics available → top-3 by importance score; else → top-3 by v5.1 corpus frequency. Alphabetical tie-break. See `artifacts/lever_13_fallback.md`.
- **[LOCKED per O3]:** 8-abstraction list locked (see Lever 12 above). Alphabetical tie-break rule fully specified in `artifacts/lever_13_fallback.md`.
- **Selection asymmetry note:** Of the 8 abstractions, ResourceBudget_status and ResourceBudget_boost are dimensional-only (no symbolic checker rules apply). Under either selection criterion (importance score or corpus frequency), these score 0 and are naturally excluded from the top-3. The L2 condition therefore tests "show the model only the top-3 rule-bearing abstractions," which is the intended manipulation. See `artifacts/lever_13_fallback.md` for the rule-bearing vs dimensional-only table.

#### Lever 15 — Question Phrasing
- **L1 (baseline):** Consistency rating — "Rate how consistent this chain is on a scale of 1–10."
- **L2:** Violation detection — "Does this chain contain any rule violations? Answer YES or NO."
- **L3:** Scaled likelihood — "What is the probability this chain contains a rule violation? Answer 0–100."
- **Output parsing:** L3 scaled outputs thresholded to binary for cross-level effect size computation. Threshold: ≥50 → YES; <50 → NO.
- **L1 thresholding asymmetry (Amendment #4 — documented limitation):** Lever 15 L1 (consistency rating 1-10) is the only lever level requiring a continuous-to-binary output transformation (thresholded at ≥50 → YES, <50 → NO). All other lever levels produce natively binary outputs that the parser cascade handles uniformly. If Lever 15 L1 shows an effect relative to L2 or L3, the effect cannot be cleanly attributed to "the consistency rating prompt produces different model behavior" versus "the thresholding boundary at 50 creates classification artifacts." This asymmetry is accepted as a documented limitation rather than mitigated, because alternative approaches (e.g., calibrating the threshold per model) would introduce post-hoc analyst discretion. Effect-size measurements on Lever 15 should be reported with this asymmetry explicitly flagged in interpretation.
- **Footnote on L1 historical framing (per O5):** The Lever 15 L1 label "Consistency rating (v1 baseline)" reflects a pre-D-42 pilot framing from early program development. Ditto V1 production (Ditto V1 codebase, `prompt_builder.py`) used next-action prediction, and V5.0 (`_CLASSIFY_QUESTION` in `Ditto V5.0/src/harness/prompts.py`) used YES/NO violation detection. The L1 framing tests the original pilot wording as a historical methodology variant, not as the actual V1 production task. This documentation aligns the SPEC with the actual program history surfaced during codebase inspection.

#### Lever 16 — Constraint Context Content
- **L1 (baseline):** No constraint context.
- **L2:** Generic natural language paragraph. Exact text: see `artifacts/lever_16_constraint_text.md`.
- **L3:** Structured rules in predicate form (RULE_PP, RULE_FAINT, RULE_MOVESET, RULE_SLEEP, RULE_FREEZE). Exact text: see `artifacts/lever_16_constraint_text.md`.
- **Policy A:** L2 and L3 text co-located immediately before chain (see above).
- **Paralysis omission (locked per O7 Option A):** Paralysis is omitted from L3 (no RULE_PARA) because the mechanic is probabilistic (~25% block chance), not deterministic — a paralyzed-but-acting event is usually legal. L2 retains its hedged "may be prevented from acting" wording. A **Day -3 chain pool check** filters paralysis-only violations from the OLAT test set before pre-OLAT verification execution (see Section 17 / BUILD_PLAN.md).
- **Prediction (Amendment #4 — magnitude-bounded):** L2 > L3 > L1 ordering predicted on gap improvement, with each pairwise difference ≥0.05 in gap to count as confirmation. Smaller orderings count as null. Falsifiable if L3 > L2 in gap, or if all pairwise differences < 0.05.
- **Cross-model prediction:** V4-Flash gap improvement on L2 vs L1 predicted larger than V4-Pro gap improvement on L2 vs L1 (capability-tier interpretation: V4-Flash benefits more from explicit constraint context because its over-flagging regime is more correctable). Magnitude threshold: capability-tier delta ≥0.15 required to confirm differential effect.

#### Lever 18 — CoT Elicitation
- **L1 (baseline):** No CoT. `thinking: disabled`. max_tokens=32. Prompt: see `artifacts/lever_18_prompts.md`.
- **L2:** "Think step by step." `thinking: disabled`. **max_tokens=1024** (Amendment #3, raised from 512). Prompt: see `artifacts/lever_18_prompts.md`.
- **L3:** Verification-style procedural. `thinking: disabled`. **max_tokens=1024** (Amendment #3, raised from 512). Prompt: see `artifacts/lever_18_prompts.md`.
- **max_tokens rationale (Amendment #3, verified via Diag I 2026-05-12):** Diagnostic I at max_tokens=4096 produced finish_reason=stop for all 40 responses across both V4-Flash and V4-Pro. Empirical max completion observed: 701 (Flash) and 540 (Pro). 1024 provides ~30% headroom over the observed max for both models without overshoot.
- **L4:** Native thinking mode. `thinking: enabled`. max_tokens=64 on content; reasoning_content unbounded. Prompt: see `artifacts/lever_18_prompts.md`.
- **Output anchor (all levels):** L1/L4: "The answer is YES/NO". L2/L3: "Therefore, the answer is YES/NO."
- **Documented baseline modification:** Per-level max_tokens modifies v5.1's uniform 32-token cap. Within-Lever 18 comparisons valid; cross-lever comparisons involving Lever 17 must account for cap variation.
- **Lever 18 baseline override (locked per O5):** When Lever 18 is the lever being tested at any level (L1, L2, L3, or L4), Lever 15 is implicitly held at L2 (YES/NO violation detection) rather than its global baseline L1 (consistency rating). This override is required because the locked Lever 18 output anchor mandates a YES/NO classification, which is incompatible with a 1–10 rating output format. Lever 15 L1 (consistency rating) is preserved as a level *only* when Lever 15 itself is the lever under test. See `artifacts/lever_18_prompts.md`.
- **Pre-registered cross-model predictions (Amendment #4 — magnitude-bounded, falsifiable; supersedes earlier B3a directional draft):**
  - **V4-Flash L1 → L2 gap improvement:** Predicted ≥+0.30 (grounded in Diag F gap +0.58 and Diag I gap +0.88; OLAT n=50 expected to tighten range). Falsifiable if observed improvement <+0.10.
  - **V4-Pro L1 → L2 gap movement:** Predicted in range −0.10 to +0.20 (grounded in Diag H gap +0.05 and Diag I gap −0.05). Falsifiable if movement >+0.30 or <−0.20.
  - **Cross-model regime difference:** Capability-tier delta on Lever 18 L2 predicted ≥+0.20 (V4-Flash improves more from CoT than V4-Pro). Falsifiable if delta <+0.10 or reverses sign.
- **Cross-model interpretation rule (Amendment #4):** If V4-Flash L2 gap exceeds V4-Pro L2 gap by ≥0.20, capability-tier model has not yet "outgrown" over-flagging regime. If V4-Pro L2 gap exceeds V4-Flash by ≥0.10, higher-tier model converts CoT into a more discriminating instrument. Differences <0.10 in either direction interpreted as "regime difference not detected at this sample size."
- **Regime terminology (Amendment #4 — operational/descriptive):** Terms like "over-flagging regime" (V4-Flash) and "balanced regime" (V4-Pro) are **operational shorthand** for the patterns observed across n=50 diagnostic conditions. They are not claims about stable latent behavioral modes. Given small per-condition n and parser dependence, these descriptions are phenomenological characterizations of expressed detection behavior under specific framings, not mechanistic constructs. OLAT effect-size measurements may produce regime shifts, regime stability, or regime variability — all are valid empirical outcomes within this descriptive frame.

#### Lever 19 — Strict-Grounding Instruction
- **L1 (baseline):** No grounding instruction.
- **L2:** "Base your answer on the events shown in the chain."
- **L3:** "You are reviewing a log that may contain injected errors or hallucinations from a secondary system. Verify the integrity of the sequence and determine whether any violations are present."
- **Placement (locked per O8):** Both L2 and L3 are placed at user-turn opening, before the chain (and before the Lever 16 constraint context if present). Parallel placement isolates the text content effect from any position effect.
- **Documented limitation (per O8):** L2 reads slightly less naturally at user-turn opening than it would as a closing reminder. This naturalness cost is accepted as a deliberate design choice — confounding text content with position would corrupt Lever 19's effect-size measurement.
- See `artifacts/lever_19_adversarial.md` for prompt templates and Lever 16 interaction check.
- **Prediction (Amendment #4 — replaces unfalsifiable strict-citation comparator):** L3 (adversarial framing) is predicted to produce higher false-positive rate on intact chains than L1 (no grounding) due to the model "searching harder" for violations. Falsifiable if L3 specificity ≥ L1 specificity, OR if effect direction reverses for V4-Pro vs V4-Flash. L2 (grounding reminder) is predicted to fall between L1 and L3 on specificity. Quantitative threshold: ≥0.10 difference in detection_rate_intact between L3 and L1 required to confirm prediction.

#### Lever 24 — Ground Truth Definition
- **L1 (baseline):** Shuffled-vs-real (v5.1 baseline).
- **L2:** Planted-violations (v3 era).
- **L3:** Symbolic-checker-as-truth (v5.3 contribution).
- **Note:** Each ground truth definition is its own evaluation universe. No cross-universe aggregation in primary analysis.
- **Prediction:** L1 and L3 will diverge substantially (per v5.3 κ ≈ −0.001 finding).
- **Evaluation universe structure (Amendment #4 — three independent tables):** Each ground truth definition (L1 shuffled-vs-real, L2 planted-violations, L3 symbolic-checker-as-truth) generates an **independent OLAT effect-size table**. The 18-lever × 2-model effect-size matrix is computed three times, once per ground truth universe. Cross-universe aggregation is prohibited in the primary analysis.
- **Per-universe operations:** Within each universe, primary analysis, sensitivity analyses, and capability-tier delta calculations are all performed independently. Baseline gaps are recomputed per universe (a chain is intact-or-violated relative to that universe's ground truth definition).
- **Reporting structure:** Final OLAT outputs include three effect-size tables labeled by universe. Cross-universe patterns (e.g., "Lever 18 is Meaningful in all three universes") are described qualitatively in the analysis writeup but not aggregated into a "master table."
- **Rationale:** Each ground truth definition reflects a different operational concept of "violation." Aggregating across them would dilute lever-specific findings that may matter under one ground truth but not another, and would obscure the v5.3 finding (κ ≈ −0.001) that symbolic and prompted ground truths measure structurally different properties.

### 7.2 Minimally-Tested Levers

#### Lever 2 — Field Naming
- **L1 (baseline):** Cryptic abbreviations matching raw Showdown export format.
- **L2:** Full descriptive semantic names throughout (all fields renamed).
- **Rationale:** Partial renaming introduces confound; full rename tests Sclar et al. naming sensitivity cleanly.

#### Lever 3 — Numerical Encoding
- **L1 (baseline):** Raw numerical values.
- **L2:** Semantic buckets. HP: Healthy >75% / Hurt 25–75% / Critical <25% / Fainted 0. PP: Full / Low / Empty. Type multipliers: Super effective / Neutral / Resisted / Immune.

#### Lever 11 — Cutoff Position
- **L1 (baseline):** Chain at first 5% of prompt.
- **L2:** Chain at 50% mark.
- **L3:** Chain at final 5%.
- **Total prompt length:** ~200–250K tokens.
- **Distractor content (verification required):** Unrelated Pokémon Showdown battles, **verified 100% violation-free via symbolic checker pre-screen**. Day 0 chain variant preparation must run all distractor candidates through `pokemon_rule_checker.py` and exclude any chain where the symbolic checker reports any rule violation. The distractor pool is therefore drawn exclusively from intact chains.
- **Rationale:** If distractor padding natively contains rule violations, the model may detect a violation in the padding rather than the target chain, inflating false-positive rate on intact-target conditions and confounding Lever 11's positional effect with distractor contamination.
- **Tokenizer specification (Amendment #4):** Token counts for Lever 11 prompt sizing computed using DeepSeek V4-Flash tokenizer (accessed via `transformers.AutoTokenizer.from_pretrained("deepseek-ai/DeepSeek-V4-Flash")`). Token count is measured on the **assembled user-turn prompt** (post-rendering, including Lever 9 chain format, Lever 16 constraint context if present, and distractor padding) — system message tokens are excluded from the 200-250K target. For Lever 18 L4 conditions, `reasoning_content` budget is server-allocated separately and does not count against the prompt token budget. Total prompt token count logged per condition for sensitivity audit.
- **Policy A:** Rules travel with chain (co-located bundle). See operationalization notes above.
- **Prediction:** U-shape with L2 worst if Lost in the Middle propagates; null if hybrid attention mitigates.

#### Lever 17 — Output Format Demand
- **L1 (baseline):** Binary YES/NO free-form. max_tokens=32.
- **L2:** Loose structure ("Answer: YES, Rule: respawn"). max_tokens=64.
- **L3:** Strict JSON (`{"detected": true, "rule_violated": "respawn"}`). max_tokens=128. `response_format: {"type": "json_object"}` required.
- **Documented baseline modification:** L2/L3 caps expand from v5.1's uniform 32 to prevent finish_reason="length" truncation. L1 preserves v5.1 baseline.

#### Lever 22 — Temperature
- **L1 (baseline):** T=0.0.
- **L2:** T=0.5.
- **CRITICAL:** All Lever 22 evaluations execute with `thinking: {"type": "disabled"}` explicitly set.
- **Conditional follow-up:** If effect ≥ 0.10 → sweep {0.0, 0.4, 0.7, 1.0}. If CoT × temperature interaction in downstream analysis → test T=0.0 and T=1.0 separately.

### 7.3 Locked at Baseline (Not Tested)
- **Lever 20 (Few-shot exemplars):** 0-shot. Locked to avoid few-shot formatting confound per Sclar et al.
- **Lever 21 (Model choice):** V4-Flash.
- **Lever 23 (Samples per chain):** k=1. Locked per Wang et al. self-consistency curves.

### 7.4 Cut from OLAT
- **Lever 10 (Adversarial chain construction):** Cut. Tests experimental design, not model behavior. Chain construction locks at v5.1 baseline (single canonical violation type).
- **Lever 14 (Verification gates):** Folded into Lever 24.

### 7.5 Total OLAT Conditions

**Per Amendment #6 (2026-05-13):** Lever 5 L2 and L3 dropped due to data-availability (see §7.1 Lever 5 dropout rationale). Lever 15 (L2, L3) corrected to (L1, L3) — typo correction reflecting Amendment #4 B1's L2 baseline lock. Net change: 4 conditions removed (Lever 5 L2/L3 × 2 models); Lever 15 conditions re-labeled (no count change). Totals: 34 → 32 per model, 68 → 64 dual-model, 3,400 → 3,200 evaluations.

| Category | Per-model conditions | Dual-model total |
|---|---|---|
| 12 OLAT-scale levers (varied levels; Lever 5 contributes 0 post-Amendment #6) | 24 non-baseline | 48 |
| 5 minimally-tested levers (~2 levels each) | 7 non-baseline | 14 |
| 1 shared baseline | 1 | 2 |
| **Total** | **32 conditions** | **64 conditions** |

Per-lever condition breakdown:

**OLAT-scale (§7.1):**
- Lever 1 (Field Schema): 2 non-baseline (L1, L3)
- Lever 4 (Derived State Markers): 2 non-baseline (L2, L3)
- Lever 5 (Selection Criterion): **0 non-baseline — L2/L3 deferred per Amendment #6 data-availability dropout**
- Lever 8 (Chain Length k): 4 non-baseline (L1, L2, L4, L5)
- Lever 9 (Rendering Format): 2 non-baseline (L2, L3)
- Lever 12 (Per-Abstraction Encoding): 2 non-baseline (L2, L3)
- Lever 13 (Abstraction Taxonomy): 1 non-baseline (L2)
- Lever 15 (Question Phrasing): 2 non-baseline **(L1, L3)** — corrected from (L2, L3) per Amendment #6; L2 is the baseline, so L1 and L3 are the non-baseline conditions tested against it
- Lever 16 (Constraint Context): 2 non-baseline (L2, L3)
- Lever 18 (CoT Elicitation): 3 non-baseline (L2, L3, L4)
- Lever 19 (Strict-Grounding): 2 non-baseline (L2, L3)
- Lever 24 (Ground Truth): 2 non-baseline (L2, L3)
- **Subtotal:** 24 non-baseline (was 26 pre-Amendment-6)

**Minimally-tested (§7.2):**
- Lever 2 (Field Naming): 1 non-baseline (L2)
- Lever 3 (Numerical Encoding): 1 non-baseline (L2)
- Lever 11 (Cutoff Position): 2 non-baseline (L2, L3)
- Lever 17 (Output Format Demand): 2 non-baseline (L2, L3)
- Lever 22 (Temperature): 1 non-baseline (L2)
- **Subtotal:** 7 non-baseline

**Total evaluations:** 64 conditions × n=50 = **3,200 evaluations** (Amendment #6)

---

## 8. Parser Strategy

**Per Amendment #3 (2026-05-12, Diag J + Pre-Amendment-3 Task 1 validation):** **4-stage cascade** applied in sequential precedence order — strict regex first, then progressively relaxed; the first stage to match wins. The cascade adds markdown tolerance (Stage 3) and last-token scan (Stage 4) on top of the original strict+permissive pattern. Empirical parsed_rate on the 440-response diagnostic corpus rises from 10–93% (legacy 3-stage) to 93–100% (Amendment #3 4-stage), with per-config gap measurements stabilizing once parsed_rate exceeds ~80%. The first_token fallback used in the pre-Amendment-3 SPEC was dropped because Diag J showed it adds <1% rescue beyond Stage 4 (last_token) and is therefore dead weight.

### Parser Scope (locked, Amendment #4)

**All parser cascade stages operate exclusively on the `content` field returned by the API.** The `reasoning_content` field (populated only when `thinking: enabled`, i.e., Lever 18 L4) is **never parsed** by any cascade stage. Concatenation of `reasoning_content` with `content` is explicitly prohibited.

This locks the parser's input space to the model's terminal verdict output, excluding intermediate reasoning trace content. Without this lock:
- Stage 4 (last_token) 200-character scan could bleed into `reasoning_content` if `content` is short
- Stages 1-3 regex matches in `reasoning_content` could override a contradictory verdict in `content`
- Two implementers could produce different parser inputs from the same API response

For Lever 18 L4 conditions, this means: the model's final classification must appear in `content` (not in `reasoning_content`), and any rationale text in `reasoning_content` is discarded for analysis purposes (though logged in parser provenance for audit).

**Sequential precedence (each stage tried only if all earlier stages fail):**

1. **Strict** — regex `(?:Therefore,\s+)?[Tt]he answer is\s+(YES|NO)\b` (case-insensitive) applied to `content`. Matches the locked output anchor exactly. Strictest stage; intended to catch well-formed Lever 18 L1 and L4 outputs.
2. **Permissive** — regex `(?i)(answer is|answer:|conclusion:)\s*(yes|no)\b` applied to `content`. Catches answers in formats like `Answer: YES` or `Conclusion: NO` without leading "The".
3. **md_strip** — strip markdown decoration `[*_\`]+` from `content`, then re-run the permissive regex. Catches CoT-produced responses like `**Answer:** YES` and `**Answer**: **YES**`. Without this stage, Diag J showed CoT parsed_rate stalled at 10–60% across the diagnostic corpus.
4. **last_token** — strip markdown, scan the last 200 characters of `content` for trailing `(YES|NO)\b` followed only by whitespace, punctuation, or closing brackets. Catches terse V1-minimal responses (`"NO."`, `"YES"`) and verbose responses where the final line is just `**NO**`. Pre-Amendment-3 Task 1 confirmed this stage catches all 250 V4-Flash Day −2 V1-minimal responses with zero classification changes vs the dropped first_token stage.
5. **Unparseable** — log and exclude from primary analysis.

Unparseable outputs excluded from primary analysis. Sensitivity check includes them (treating as NO or as random 50/50). Parse provenance logged per sample per `artifacts/plumbing_schemas.md` Schema 1, recording which cascade stage produced the parse.

### Parser as Instrument (locked, not a lever)

**The parser cascade above is the canonical measurement instrument for OLAT, not a manipulation under test.** Diagnostic J showed parser variation (v1 → v2) can produce gap-magnitude shifts of 0.4+ on CoT-bearing conditions. Allowing the parser to vary at experiment time would confound lever effects with instrument effects. The 4-stage cascade is therefore locked: any future revision to the parser is a methodology amendment requiring fresh both-author signoff and a new SPEC hash. Per-stage rescue rates and stage-mix distributions are recorded in parser provenance for sensitivity analysis but are not OLAT outputs.

**Construct framing (Amendment #4 — language tightening):** OLAT measures **parser-mediated expressed detection behavior** under the locked 4-stage cascade, not latent internal detection competence. Diagnostic J showed parser variation (v1 → v2) can produce gap-magnitude shifts of 0.4+ and sign reversals on CoT conditions — meaning the measured construct changed materially when the instrument changed. Downstream interpretive language must distinguish:
- "V4-Flash detects violations at rate X under CoT with locked parser cascade v2" — what the SPEC measures
- "V4-Flash detects violations at rate X under CoT" — interpretation drift; collapses parser to invisible
- "V4-Flash has detection competence X" — over-claims; mistakes expressed behavior for latent capability

Reports of OLAT findings must preserve the first framing; the second and third are downstream drift that the SPEC does not license.

---

## 9. Decision Rules for Results

| Effect magnitude | Interpretation | Downstream action |
|---|---|---|
| ≥ 0.10 absolute change in detection rate | Meaningful | Include in Mew design |
| 0.03–0.10 | Directional | File for future testing |
| < 0.03 | Null | Skip in subsequent work |

**Decision rule × CI hierarchy (Amendment #4 formalization):** The classification rule is applied in strict order:

1. **Magnitude check:** Compute |condition gap − baseline gap|. If ≥0.10, candidate classification = Meaningful. If 0.03-0.10, candidate = Directional. If <0.03, classification = Null (final).
2. **CI check (for candidate Meaningful or Directional only):** If bootstrap 95% BCa CI excludes zero on the appropriate side (positive CI for positive effects, negative CI for negative effects), classification confirmed. If CI crosses zero, classification downgraded by one level (Meaningful → Directional; Directional → Null).
3. **Final classification:** Resulting label after Steps 1-2 governs downstream action.

This hierarchy is deterministic — two analysts applying it to identical raw data produce identical classifications. Sensitivity analyses (Section 9.2) do not enter this hierarchy; they are reported separately.

### 9.0 Bootstrap Methodology Specification (Amendment #4)

All bootstrap confidence intervals in OLAT analysis use the following locked specification:

**For intra-model paired effect sizes** (condition gap − baseline gap, same model):
- Method: Paired bootstrap of difference scores
- Implementation: `scipy.stats.bootstrap` with `method='BCa'` (bias-corrected and accelerated)
- Resample count: 10,000 iterations
- Resample unit: chain-level (chain index pairs preserved across condition and baseline)
- Seed: fixed at 42 for reproducibility across runs
- Stratification: none (paired structure handles correlation)

**For cross-model effect-size deltas** ((Flash condition gap − Flash baseline gap) − (Pro condition gap − Pro baseline gap)):
- Method: Two-sample independent bootstrap of paired-difference distributions
- Step 1: Compute paired difference distribution per model (10,000 iterations each, seed=42 for Flash, seed=43 for Pro)
- Step 2: Compute difference between the two distributions (joint resampling: for each iteration, draw paired-difference from Flash distribution minus paired-difference from Pro distribution)
- Resulting 95% BCa CI on cross-model delta
- This procedure correctly propagates the variance from both models' independent samples while preserving paired structure within each model

**For absolute detection rate differences** (e.g., V4-Flash detection_intact under Lever 16 L2 vs L1):
- Method: Paired bootstrap of difference scores (same as intra-model effect size method above)

**Empty-cell handling:**
- Conditions producing zero variance (all-NO or all-YES outputs after parser exclusions): bootstrap reports point estimate with CI=[point, point]; flagged in analysis output with `degenerate_variance=true`
- Conditions with n_valid < 25 after parser exclusions: effect size reported but bootstrap CI suppressed; flagged with `insufficient_n=true`

**Variance estimation libraries:** SciPy 1.11+ for BCa implementation. Specific function signatures and parameter values logged in analysis provenance.

### 9.1 Statistical Power for Decision Rules

At n=50 per condition with paired bootstrap 95% CI on gap, the minimum detectable effect at 80% power varies by baseline rate due to ceiling/floor compression. Power calculations for the locked decision thresholds:

| Baseline rate | Detectable effect (≥0.10 threshold) | Detectable effect (0.03-0.10 threshold) | Power for direction at 0.03 |
|---|---|---|---|
| 0.50 (chance) | Adequate (≥80%) | Marginal (~60%) | Low (~40%) |
| 0.14 (V4-Pro V1-min) | Adequate for movement to >0.30 | Marginal for movement to 0.20-0.30 | Low |
| 0.00 (V4-Flash V1-min) | Adequate for any movement >0 | Conservative | n/a (one-sided) |

**Implications:**
- 0.03-0.10 "directional" band: Confidence intervals at n=50 will frequently overlap zero. Pre-registered handling: directional effects reported with bootstrap CI bounds; if CI crosses zero, classification reclassified as null per Diag J finding that small-sample gaps can be artifactual.
- ≥0.10 "meaningful" band: Adequate power for detection at all baseline rates.
- **Multiple comparison handling (Amendment #4 sharpened):** 18 levers × 2 models = 36 primary effect estimates. No formal multiple-comparison correction applied (consistent with pre-registration design specifying effect-size estimation rather than NHST). However, the following narrative guardrails apply:
  - Under chance, ~2 of 36 effect estimates would fall in the 0.03-0.10 directional band by chance alone. Directional findings on a single lever × model cell should not be treated as robust without convergent evidence (e.g., directional in both models, or supported by sensitivity analyses).
  - Ranked effect tables suffer from winner's curse: the top-ranked lever's effect size is the maximum of 36 noisy estimates, systematically inflated relative to its true effect.
  - **Empirical Bayes shrinkage applied to ranked tables:** Effect sizes in the ranked table are reported as both raw and shrunken estimates. Shrunken estimates use the empirical Bayes method (`scipy.stats.norm` posterior under prior mean=0, prior variance=median observed variance across levers). The raw rankings determine ordering; the shrunken estimates inform the magnitude claims for Mew design.
  - Mew design decisions prioritize levers ranked Meaningful in **both models** when both were tested; single-model Meaningful classifications are weighted lower in Mew prioritization.

**Power for cross-model comparisons:** Detecting differential effects (V4-Flash effect minus V4-Pro effect) at the lever level requires both effects to be precisely estimated. At n=50 per cell, cross-model differential effects of ≥0.15 are detectable; smaller differentials should be reported as descriptive comparisons rather than tested differences.

### 9.2 Pre-Registered Sensitivity Analyses

Primary analysis: parser unparseables excluded; raw detection rates; bootstrap BCa 95% CI; effect size = (condition gap − baseline gap).

Pre-registered sensitivity analyses (all reported alongside primary):

1. **Unparseables-as-NO:** Treat parser-unparseable outputs as NO. Reports lower-bound estimate of YES detection.
2. **Unparseables-as-random:** Treat parser-unparseables as 50/50 random. Reports neutral assumption estimate.
3. **Variance-stabilizing transformation:** Apply arcsine transformation to rates near 0/1 boundaries. Reports effect sizes corrected for ceiling/floor compression.
   - Method locked at arcsine (Amendment #4). Logit considered but rejected because arcsine handles exact boundary values (0.0 and 1.0) without infinity, which is relevant given V4-Flash's 0% baseline floor. Variance-stabilizing transformation applied to detection rates only; gap and effect-size are computed on raw rates, with sensitivity reported as transformed estimates alongside primary raw estimates.
4. **Fallback-stage-rescued exclusion (parser-dependence characterization, not robustness check):** Exclude samples that parsed only via cascade stages 3 (md_strip) or 4 (last_token). Reports "parser-strict effect size" computed only on stage 1-2 parses. **Interpretation:** This sensitivity is not a robustness check on the primary effect; it characterizes whether the primary effect is driven by anchor-conforming outputs (stages 1-2) or by markdown-decorated or terminally-positioned outputs (stages 3-4). A divergence between primary and parser-strict effect sizes indicates parser-dependence in the measured signal, not signal unreliability per se. **Effective n asymmetry note:** This exclusion disproportionately affects CoT conditions (Lever 18 L2/L3/L4), where stage 3-4 rescues dominate. The parser-strict effect size for CoT conditions is computed on a substantially smaller subsample than for V1-minimal conditions; CI widths reflect this and should not be compared directly across conditions.
5. **Per-condition parse_failure_rate audit:** Report parse_failure_rate per condition. Flag conditions with >10% failure for closer inspection.
6. **Within-condition response-length sensitivity:** For Lever 18 L2/L3, sub-analyze by response length quartile to characterize whether longer reasoning produces different effects.

Sensitivity analyses are reported in the OLAT effect-size table as additional columns; primary effect size is the headline metric.

**Hierarchy and conflict resolution (Amendment #4):** The primary analysis classification (Meaningful / Directional / Null) governs downstream Mew design decisions. Sensitivity analyses are diagnostic — they characterize robustness but do not override the primary classification. Specifically:

- If primary analysis classifies a lever as Meaningful but ≥3 of 6 sensitivity analyses produce Null, the lever is flagged as `robustness_concern=true` in the effect table but retains Meaningful classification for downstream action.
- If primary analysis classifies a lever as Null but ≥3 of 6 sensitivity analyses produce Meaningful, the lever is flagged as `hidden_signal_candidate=true` but retains Null classification for downstream action (no retroactive promotion).
- Sensitivity #4 (rescue exclusion) is interpreted specifically as a parser-dependence characterization, not a robustness check: it measures whether the OLAT effect is driven by Stage 1-2 parses or by Stage 3-4 rescues. Results reported separately as "parser-strict effect size" alongside primary.

This hierarchy prevents retroactive sensitivity-driven reclassification while preserving sensitivity as audit material.

### 9.3 Cross-Model Baseline Asymmetry (Amendment #3 interpretation framing)

V4-Flash and V4-Pro show different baseline behaviors under V1-minimal:
- **V4-Flash:** at absolute floor (0% violated detection; gap = −1.000)
- **V4-Pro:** partial baseline competence (14% violated detection; gap = −0.757)

Effect-size comparisons across the two models are **descriptive regime comparisons** — they test "how much each lever moves the model from its own baseline" rather than "how much each lever moves toward the same target" or "how capability scales." Cross-model lever effects are interpreted as **differential movement from per-model floors**, not as trajectories toward a shared endpoint, and not as isolating capability-tier as a causal variable. V4-Flash and V4-Pro differ simultaneously in baseline floor severity, spontaneous reasoning behavior under token constraints, and likely instruction-following priors — these factors are confounded with capability tier in any cross-model comparison.

**Practical consequence for the OLAT effect table:** Each model receives its own column of effect sizes computed against its own baseline. Cross-model rows report (V4-Flash effect, V4-Pro effect, capability-tier delta). The capability-tier delta is itself a substantive output — it characterizes how lever effects propagate across the two models tested — and should not be conflated with intra-model effect magnitude.

The decision-rule thresholds above (≥0.10 meaningful, 0.03–0.10 directional, <0.03 null) apply independently to each model's effect table; thresholds are not pooled across models.

**Capability-tier delta interpretation thresholds (Amendment #4):**

- Delta ≥0.20: "Strong capability-tier effect" — lever effect substantially differs between V4-Flash and V4-Pro
- Delta 0.10-0.20: "Moderate capability-tier effect"
- Delta 0.03-0.10: "Weak capability-tier difference" — descriptive only, not interpreted as capability-driven
- Delta <0.03: "Capability-tier invariant" — lever effect generalizes across capability tier

Cross-model delta confidence intervals are reported alongside point estimates per the bootstrap protocol in Section 9.0. Delta interpretation requires both the magnitude threshold AND CI exclusion of zero (same hierarchy as intra-model effect classification).

**Honest caveat:** Cross-model deltas are descriptive regime comparisons. They cannot cleanly isolate "capability scaling" from baseline-response elasticity differences (V4-Flash and V4-Pro differ in baseline floor severity, spontaneous reasoning behavior under token constraint, and likely instruction-following priors). The delta characterizes how lever effects propagate across the two models tested; it does not isolate a single underlying mechanism.

---

## 10. Cross-Lever Interactions

### Resolved through design ordering
- **Lever 9 × Lever 11:** Context-window ratio computed after Lever 9 rendering (token count varies by format).
- **Lever 12 × Lever 17 (Amendment #4 precedence rule):** Distinct parsers per output type. Lever 12 L3 (function calling) and Lever 17 L1 (free-form YES/NO) are API-incompatible; Lever 17 baseline overridden when testing Lever 12 L3. **Prompt-schema conflict resolution:** When prompt text anchor (e.g., "Therefore, the answer is YES/NO") conflicts with schema-required output shape (e.g., boolean `detected` field), schema-valid output supersedes textual anchor semantics. Parser cascade for Lever 12 L3 conditions parses the function call payload's `detected` field directly, not the textual anchor.
- **Lever 16 × Lever 19:** L3 of Lever 19 does not introduce rule knowledge absent at Lever 16 L1. Verified in `artifacts/lever_19_adversarial.md`.

### Resolved via V4-Flash API behavior
- **Lever 22 × Lever 18 (CRITICAL):** All Lever 22 evaluations execute with `thinking: disabled`. Lever 18 L4 accepts nullified temperature.
- **Lever 12 × Lever 18 (CRITICAL):** `reasoning_content` preserved across sub-turns when Lever 12 L3 × Lever 18 L4 active.
- **Lever 17 × Lever 18:** JSON validation (Lever 17 L3) operates on `content` field only; `reasoning_content` excluded.

### Documented as known interactions
- **Lever 1 × Lever 11:** Schema changes token count → realized context ratio drifts across schema conditions. **Mitigation:** Compute realized ratio after Lever 1 schema applied; log per condition.
- **Lever 18 × Lever 17:** Reasoning verbosity vs output format compliance; no direct collision, interpretation requires distinguishing `reasoning_content` from `content`.
- **Lever 24 × Lever 5:** Selection proxies derive from v5.1 shuffled-vs-real ground truth. Difficulty "by one ground truth" ≠ difficulty "by another." Documented limitation.
- **Lever 1 × Lever 4:** Marker availability depends on field schema. Both levers tested independently at each other's baseline.
- **Lever 15 × Lever 17 × Lever 18:** Response channel shape varies. Parser strategy and threshold mappings provide unified handling.
- **Lever 24 × all:** Each ground truth definition is its own evaluation universe. No cross-universe aggregation.

---

## 11. Documented Assumptions

1. Results may not transfer to other models. V4-Flash is sub-frontier; Haiku, GPT-5, etc. may show different lever sensitivities (Sclar et al. 2024 supports cross-model format-preference variability).
2. Results may not transfer to other domains. Pokémon is the most-trained-on game in the program; PUBG, NBA, CSGO, RL may show different patterns.
3. Pokémon's training-data saturation may inflate baseline detection rates relative to less-saturated domains.
4. OLAT cannot detect interactions between levers; only main effects.
5. Compute-only levers can be tested cheaply (Stages 1–3, 8–9 mostly). API-bound levers limit scope (Stages 4–7).
6. Evaluation-awareness as potential confound (per Anthropic NLA work, May 2026). Frontier models in v5.1 panel may have responded differently because they recognized test context.
7. V4-Flash baseline under V1 methodology is established empirically by pre-OLAT verification run. Lever effects are perturbations from this empirically-established baseline.
8. **Parse attrition bias may be condition-specific.** Malformed outputs are unlikely random — some lever combinations inherently induce more parse failures. **Mitigation:** Track parse failure rate per condition. Report alongside main effect sizes.
9. **First-token fallback may over-rescue malformed outputs.** "No violations found" → classified as NO (potentially correct). Log fallback provenance. Sensitivity check excludes fallback-rescued samples.
10. **Chain length truncation introduces prefix bias.** Truncating to first k events overrepresents early-turn violations. Per the Day -2 step-distribution check, the v5.1 corpus violation_step has median=14 with a long right tail (max=40). Lever 8 levels reanchored per Amendment #2 to span this empirical range: {5, 10, 15, 20, 30}. The k=5 floor visibility (~4%) and k=30 ceiling (~90%+) frame the saturation curve. Documented as a deliberate sampling design, not a bias to mitigate.
11. **50K–250K fixed prompt creates uneven distractor burden.** Short chains receive proportionally more distractor padding. Documented known interaction — acceptable for diagnostic intent.
12. **Sampling with replacement across conditions creates dependence structure.** Chain-condition assignment logged for post-hoc leakage assessment per `artifacts/plumbing_schemas.md`. **Post-hoc audit threshold (Amendment #4):** Distribution of chain reuse counts (how many conditions each chain appears in) reported alongside primary OLAT results. Flag for closer inspection: any single chain appearing in >20 conditions (out of 68), or top-5% of chains by reuse count contributing >40% of any condition's effect-size signal. If concentration patterns are flagged, sensitivity analysis re-runs effect-size estimates excluding over-represented chains.
13. **Ceiling/floor compression on detection rates near 0 or 1.** **Mitigation:** Primary effects on raw rates; sensitivity check applies variance-stabilizing transformation (arcsine, per Amendment #4 method lock) for rates near bounds. Both reported.

---

## 12. Open Items (Must Be Resolved Before Sign-Off)

| # | Item | Artifact | Status | Blocked by |
|---|---|---|---|---|
| O1 | L2 exact field list (Lever 1) | lever_01_field_schemas.md | RESOLVED — ~18-field schema from codebase inspection. O-A also resolved (see below). Both authors confirm ~18 count before sign-off. | Both-author confirmation |
| O2 | L1 minimal field set violation coverage | lever_01_field_schemas.md | RESOLVED per Amendment #1 (2026-05-12) — Option A: L1 expanded to 10 fields covering all 9 active symbolic checker rules. | — |
| O3 | 8 abstraction names | lever_12_function_schema.json, lever_13_fallback.md | RESOLVED per decision-sheet-v1.md — 8 names locked, rule-bearing vs dimensional-only documented. | — |
| O4 | Lever 12 schema acceptance test | lever_12_function_schema.json | OPEN | DeepSeek /beta endpoint test |
| O5 | Lever 15 question framing for Lever 18 testing | lever_18_prompts.md | RESOLVED per decision-sheet-v1.md — Interpretation A locked: Lever 18 implicitly holds Lever 15 at L2. | — |
| O6 | Verification scenarios S2–S5 thresholds | verification_response.md | RESOLVED per decision-sheet-v1.md — S2/S4/S5 accepted as drafted; S3 tightened from 0.20 to 0.05. | — |
| O7 | Lever 16 paralysis violation framing | lever_16_constraint_text.md | RESOLVED per decision-sheet-v1.md — Option A: paralysis omitted from L3, L2 hedged wording retained, Day -3 chain pool check added. | — |
| O8 | Lever 19 L2/L3 placement (system vs user turn) | lever_19_adversarial.md | RESOLVED per decision-sheet-v1.md — both at parallel user-turn opening. | — |
| O9 | Lever 13 top-3 abstraction selection run | lever_13_fallback.md | OPEN — requires execution; fallback rule fully specified, pending symbolic checker access | Symbolic checker + corpus access |
| O-A | CoordinationDependency/OptimizationCriterion in v5.1 LLM prompt | lever_01_field_schemas.md | RESOLVED — YES, both types ARE included. renderer.py _RENDERERS table includes both; v4_runner.py reads chain["rendered"] with no event-type filtering. L2 effective field count = ~18. | — |

---

## 13. Conditional Follow-Up Triggers (Pre-Registered)

### Lever 8 (Chain Length) — Amendment #4 quantitative threshold

- **Trigger (sharp cliff):** Adjacent-level detection_rate(violated) difference ≥0.25 between any two adjacent levels in {k=5, k=10, k=15, k=20, k=30}
- **Trigger (gradual saturation):** All adjacent-level differences <0.25 with monotonic increase
- **Response (cliff):** Follow-up with cluster around identified cliff range (e.g., if k=10→k=15 shows the cliff, run {11, 12, 13, 14})
- **Response (gradual):** No follow-up; report saturation curve shape descriptively
- **Falsifiability:** "Reasoning depth" interpretation is exploratory — the prediction tests whether a sharp cliff exists, not what it means. The presence or absence of a cliff is the falsifiable claim.

### Lever 22 (Temperature)
- **Trigger:** Effect ≥ 0.10 detection rate change between T=0 and T=0.5
- **Response:** Sweep full range {0.0, 0.4, 0.7, 1.0}
- **Additional trigger:** CoT × temperature interaction in downstream analysis → test T=0.0 and T=1.0 separately
- **Additional trigger:** V4-Flash mode-collapse at T=0 → test T=0.7+ regardless of main effect

### Other levers (Amendment #4 — C1-defer)

No conditional follow-up triggers pre-registered for other levers. Follow-up analyses on OLAT effect-table findings (Lever 18 over-flagging confirmation, Lever 16 cross-model differential effects, Lever 12 function-calling vs FRI divergence, etc.) will be specified in post-execution analysis amendments if needed. The post-OLAT roadmap conversation will identify which follow-ups warrant fresh both-author signoff against new hypotheses grounded in the effect table.

---

## 14. Evaluation Plumbing

See `artifacts/plumbing_schemas.md` for:
- Parser provenance log schema (one record per API call)
- Chain-condition assignment log schema (one record per chain-condition pair)

Both logs are append-only NDJSON files written during evaluation.

**API failure handling (Amendment #4):** All API failures during Day 1 execution are caught, recorded in parser provenance with `parse_stage_reached="api_failure"`, `parse_success=false`, and `raw_output=<error message>`. The batch continues without termination. Failure categories logged include:
- HTTP 4xx (client errors — invalid schema, malformed request, etc.)
- HTTP 429 (rate limit — retry with exponential backoff up to 3 attempts, then log as failure)
- HTTP 5xx (server errors — retry with backoff up to 3 attempts, then log)
- Network/timeout errors (retry up to 3 attempts, then log)
- Schema validation rejections on Lever 12 L3 (logged separately for post-execution audit)

Per-condition failure rate is reported alongside parse failure rate in the OLAT effect table. Conditions with >10% combined failure rate are flagged for closer inspection.

---

## 15. Structure-Enforcement Layer Disambiguation

Each condition in the OLAT matrix must be annotated with all five API parameters to ensure reproducibility from the SPEC alone and prevent hidden compound manipulations.

**Required per-condition annotation:**
1. `prompt_text` — full user turn text (with anchor and Policy A co-location applied)
2. `response_format` — `{"type": "text"}` (default) or `{"type": "json_object"}` (Lever 17 L3, Lever 12 L2)
3. `tools` — `null` (default) or function definition array (Lever 12 L3)
4. `thinking` — `{"type": "disabled"}` (default) or `{"type": "enabled"}` (Lever 18 L4 only)
5. `max_tokens` — per-lever per-level value as specified

**Concrete layer assignments:**
- **Prompt instruction layer:** Lever 17 L1/L2/L3 text prompt
- **API response mode layer:** `response_format` parameter (Lever 17 L3, Lever 12 L2)
- **Tool-calling schema layer:** `tools` parameter (Lever 12 L3 only)

No condition should leave layer assignments ambiguous.

---

## 16. Downstream Framing

- **Primary:** OLAT per-lever effect table specifies which levers Mew should handle deliberately vs hold at OLAT-baseline values.
- **Secondary:** Close out Ditto program with methodology characterization.
- **Stretch:** Eval-adjacency commercial product (regime-sensitivity audit, routing-invariance check).

---

## 17. Logistics

- **Hosting:** Local desktop folder.
- **Signoff:** Both-author signoff captured locally before any API calls.
- **Amendments:** Any mid-flight amendment requires fresh both-author signoff before resuming.
- **Pre-registration deadline target:** Before 2026-05-15 (pre-vacation).
- **Execution:** On or after 2026-05-15; can execute during vacation if sequencing permits.

### Execution sequencing (high-level — full details in BUILD_PLAN.md)

- **Day -3 — Chain pool check.** Filter v5.1 test set for chains where the only planted violation is paralysis-related. If count > 0, both authors decide between Option 1 (exclude) and Option 2 (retain with documented limitation). Default = exclude unless excluding drops the violated set below ~50% of chains. Both authors sign the exclusion decision before Day -2 begins. See `artifacts/lever_16_constraint_text.md` for the full procedure.
- **Day -2 — Pre-OLAT verification execution.** V1-on-Flash, n=250. See `artifacts/verification_response.md` for the six pause scenarios.
- **Day -1 — Verification review and pre-registration signoff.**
- **Day 0 — Chain variant preparation (compute only, no API).** See "Day 0 procedure" below.
- **Day 1 — Batched OLAT API evaluations.**
- **Day 2 — Analysis and final results signoff.**

### Day 0 procedure (Amendment #4 — C2-inline)

Chain variant preparation is **deterministic**. For each of the 68 dual-model conditions, the baseline chain selected per Lever 5 L1 random sample is transformed by applying the lever-specific operationalization locked in §7. No condition-time decisions are made; every variant is the mechanical output of the SPEC operationalization applied to a chain.

**Procedure (executed once per condition × n=50 chain assignments):**

1. **Load the chain** from the OLAT pool (per `chain_condition_assignments.ndjson` from Day −3 sampling, seeded with `LEVER_5_RANDOM_SEED=42`).
2. **Apply Lever 1** field schema (L1 / L2 / L3 per condition) — filter chain `constraints[]` to the field set defined in `artifacts/lever_01_field_schemas.md`.
3. **Apply Lever 8** truncation — `cutoff_rendered(rendered, k)` for the condition's k value.
4. **Apply Lever 9** rendering template (L1 multi-line / L2 single-line / L3 entity-centric per `artifacts/lever_09_rendering.md`).
5. **Apply Lever 4** state marker annotations if Lever 4 ≠ L1.
6. **Apply Lever 2** field renames if Lever 2 ≠ L1.
7. **Apply Lever 3** numerical encoding transformations if Lever 3 ≠ L1.
8. **Compose prompt** — concatenate (Lever 19 grounding text if ≠ L1) + (Lever 16 constraint context if ≠ L1) + rendered chain + (Lever 15 question text) + (Lever 18 CoT instruction if ≠ L1) + (output anchor).
9. **Set API parameters per condition** — model (V4-Flash or V4-Pro), `temperature` (Lever 22), `max_tokens` (Lever 18 level), `thinking` flag (Lever 18 L4 enables), `tools`/`tool_choice` (Lever 12 L3), `response_format` (Lever 12 L2 / Lever 17 L3).
10. **Apply Lever 11** distractor padding (compute distractor blocks to reach target prompt length; place per condition's cutoff position).
11. **Persist** the constructed prompt and parameter set to `chain_variants/<condition>/<chain_id>.json` for Day 1 batched execution.

Determinism is enforced by single-seed initialization at Day 0 start, no random branching inside the procedure, and a `chain_variants` checkpoint that Day 1 reads (so Day 1 cannot accidentally re-randomize). Detailed implementation lives in BUILD_PLAN.md Day 0 section and the chain-prep script. Cross-model conditions share the same chain pool and lever variants; only the model name and per-model API params differ.

---

## Appendix A — Literature Verification Status

| Paper | Citation | Status for OLAT |
|---|---|---|
| Mind Your Step | Liu et al. 2025, ICML | Adjacent context; effect size 2–3× larger than theirs |
| Lost in the Middle | Liu et al. 2024, TACL | Substantially mitigated in V4-era hybrid attention |
| Fluid Benchmarking | Hu et al. 2025, OpenReview | Requires multi-model panel; use simpler proxies |
| Sclar et al. | 2024, ICLR | Directly applicable; supports format-level testing |
| Temperature paper | arXiv:2604.08563 | Single-model test (Grok-4.1); partial applicability |
| Same Task More Tokens | Levy et al. 2024, ACL | Prior holds; Lever 8 levels reanchored to empirical violation-step distribution per Amendment #2 (linear-ish spacing across the operating range, not log) |
| Tam (Let Me Speak Freely) | 2024, EMNLP | Hybrid task regime; finding contested; 32-token cap attenuates |
| Wei (CoT foundational) | 2022, NeurIPS | Doesn't cover task; reasoning-as-interference interpretation supported |

---

*SHA-256 hash: [COMPUTED AT SIGN-OFF — see signoff/signoff_block.md]*
