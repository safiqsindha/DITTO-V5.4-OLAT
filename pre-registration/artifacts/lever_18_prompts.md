# Blocker #5 — Lever 18 Exact Prompt Text

**Status:** RESOLVED — Lever 15 baseline override locked per O5 (decision-sheet-v1.md, 2026-05-11).

---

## Lever 15 Baseline Override (Locked)

**Resolution (O5 Option A1):** When Lever 18 is the lever being tested at any level (L1, L2, L3, or L4), Lever 15 is implicitly held at **L2 (YES/NO violation detection)** rather than its global baseline L1 (consistency rating 1–10). This override is required because the locked Lever 18 output anchor mandates a YES/NO classification, which is incompatible with a 1–10 rating output format. Lever 15 L1 (consistency rating) is preserved as a level *only* when Lever 15 itself is the lever under test.

**Question text used in all Lever 18 levels:** "Does this battle chain contain any rule violations?"

**Historical context:** The Lever 15 L1 "Consistency rating" label reflects a pre-D-42 pilot framing from early program development. Ditto V1 production used next-action prediction; V5.0 used YES/NO violation detection (`_CLASSIFY_QUESTION` in `Ditto V5.0/src/harness/prompts.py`). Lever 15 L1 tests the original pilot wording as a historical methodology variant, not as the actual V1 production task. This documentation aligns the SPEC with program history surfaced during codebase inspection.

---

## Shared Parameters Across All Four Levels

| Parameter | Value |
|---|---|
| Lever 15 framing (locked override) | L2 — violation detection YES/NO |
| Question text | "Does this battle chain contain any rule violations?" |
| Thinking mode L1–L3 | `thinking: {"type": "disabled"}` |
| Thinking mode L4 | `thinking: {"type": "enabled"}`, `reasoning_effort: "high"` |
| Lever 22 (temperature) baseline | T=0.0 (L1–L3 deterministic) |

---

## Level 1 — No CoT (Baseline)

**API parameters:**
- `thinking: {"type": "disabled"}`
- `max_tokens: 32`

**Prompt text (user turn):**

> Does this battle chain contain any rule violations? The answer is YES or NO.

**Output anchor:** `The answer is YES` / `The answer is NO`

**Notes:**
- 32-token cap matches v5.1 baseline exactly.
- No chain-of-thought instruction. Model produces direct binary answer.
- "The answer is YES or NO" at end of question functions as both directive and parser anchor.
- Documented baseline modification from v5.1: v5.1 did not require an explicit output anchor. The anchor is a OLAT addition to support cross-level parser consistency. Pre-OLAT verification (n=250) characterizes whether this anchor shifts the baseline detection rate.

---

## Level 2 — "Think Step by Step"

**API parameters:**
- `thinking: {"type": "disabled"}`
- `max_tokens: 1024` (Amendment #3, 2026-05-12; raised from 512)

**Prompt text (user turn):**

> Does this battle chain contain any rule violations? Think step by step before answering. Therefore, the answer is YES or NO.

**Output anchor:** `Therefore, the answer is YES` / `Therefore, the answer is NO`

**Notes:**
- Standard CoT per Wei et al. prompt-induced reasoning.
- Parsing handled by Amendment #3 5-stage cascade (see SPEC §8). Strict regex matches `(Therefore,\s+)?[Tt]he answer is (YES|NO)`; markdown-tolerant and last-token stages catch CoT-decorated answers like `**Answer:** YES`.
- 1024-token cap accommodates verbalized CoT trace of 5–15 steps. Empirically observed max completion: 701 tokens (Flash) and 540 tokens (Pro) at max_tokens=4096; 1024 gives ~30% headroom.
- Directive force: "Think step by step" is imperative, same grammatical strength as L3's procedural instruction.
- Reasoning lives in `content` field. No `reasoning_content` field in L2 (thinking mode disabled).

---

## Level 3 — Verification-Style Procedural

**API parameters:**
- `thinking: {"type": "disabled"}`
- `max_tokens: 1024` (Amendment #3, 2026-05-12; raised from 512)

**Prompt text (user turn):**

> Does this battle chain contain any rule violations? Review the chain event by event. For each event, check whether it conforms to the rules of Pokemon battles. Identify any event that violates a rule. Therefore, the answer is YES or NO.

**Output anchor:** `Therefore, the answer is YES` / `Therefore, the answer is NO`

**Notes:**
- Procedural instruction specifying a review process without mandating verbalized reasoning output.
- Design intent: tests Mind Your Step's verbal overshadowing hypothesis — does procedural instruction without explicit "think step by step" verbalization directive produce different behavior than L2?
- Directive force control: "Review... For each event, check... Identify..." is imperative in the same register as L2's "Think step by step." Both are procedural commands of equivalent assertiveness.
- "Therefore" anchor is identical to L2 for parser consistency.
- 512-token cap same as L2.

---

## Level 4 — Native Thinking Mode

**API parameters:**
- `thinking: {"type": "enabled"}` (via `extra_body: {"thinking": {"type": "enabled"}}` or `reasoning_effort: "high"`)
- `max_tokens: 64` (on `content` field only; `reasoning_content` is unbounded by API design)
- Temperature/top_p/penalties: **silently nullified by V4-Flash server** when thinking mode enabled — do not attempt to set these for L4 evaluations

**Prompt text (user turn):**

> Does this battle chain contain any rule violations? The answer is YES or NO.

**Output anchor:** `The answer is YES` / `The answer is NO` (in `content` field)

**Notes:**
- Prompt text is identical to L1. The manipulation is at the API parameter level (thinking mode), not prompt content.
- The L4 prompt text intentionally contains no explicit CoT instruction in the user message. Native thinking mode channels deliberation into `reasoning_content` (separate field) rather than `content`.
- Parser reads `content` field only for final answer. `reasoning_content` is preserved for qualitative review but excluded from binary classification.
- 64-token cap on `content` is sufficient for "The answer is YES/NO" plus minor context (e.g., "The answer is YES. The chain contains a moveset violation in turn 5.").
- Documented baseline modification: Lever 22 temperature baseline is effectively undefined for L4 (nullified server-side). Accept this for L4; within-lever comparisons of L4 vs L1–L3 include this confound as a documented limitation.
- **Lever 12 × Lever 18 L4 interaction:** When L4 intersects Lever 12 L3 (function calling), `reasoning_content` must be preserved and re-injected across tool sub-turns within a single user question. Dialogue manager implements this; see lever_12_function_schema.json for details.

---

## Parser Strategy (All Levels)

Applied in order; first successful parse terminates the chain:

1. **Strict parse:** regex `(Therefore, )?[Tt]he answer is (YES|NO)` — catches well-formed outputs across all four levels.
2. **Permissive parse:** regex `(?i)(answer is|answer:|conclusion:)\s*(yes|no)` — catches minor anchor variations.
3. **First-token classification:** scan first 10 tokens of `content` field for `YES` or `NO` as first substantive token.
   - Risk: semantic inversion — "No, the chain appears valid" would be classified NO (correct), but "No violations" could be classified as NO when the chain IS valid. Log all first-token rescues for sensitivity check.
4. **Log as unparseable** if all three fail. Exclude from primary analysis; include in sensitivity check.

Parser provenance is logged per sample. See plumbing_schemas.md for schema.

---

## Directive Force Control Note

| Level | CoT instruction | Imperative register |
|---|---|---|
| L1 | None | Declarative question only |
| L2 | "Think step by step before answering." | Imperative sentence, action: cognitive process |
| L3 | "Review the chain event by event. For each event, check... Identify..." | Imperative sequence, action: procedural review |
| L4 | None (identical to L1 in user message) | Declarative question only |

L2 and L3 both use imperative directives of similar grammatical force. L1 and L4 are both declarative. The cognitive demand of L3's procedural instruction is higher than L2's, but the directive register is controlled to be equivalent.

---

## Verification Checklist for Sign-Off

- [x] Lever 15 question framing incompatibility resolved — Interpretation A locked per O5 (decision-sheet-v1.md)
- [ ] L4 prompt confirmed to produce valid V4-Flash function calls when Lever 12 L3 is active
- [ ] Parser regex tested against representative V4-Flash outputs from pre-OLAT verification run
- [ ] 512-token cap for L2/L3 confirmed as sufficient (review average output length in pre-OLAT verification)
- [ ] L4 qualitative review protocol confirmed (who reviews reasoning_content, what they record)
