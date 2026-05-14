# Task 4: Lever 18 L4 (Native Thinking) — Diagnostic Report

**SPEC hash:** `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8`  
**Generated:** 2026-05-13  
**Conditions:** `flash_L18_L4` (50 records), `pro_L18_L4` (50 records)  
**Result:** All 100 records classified `Unknown` (0 parsed). This report diagnoses why.

---

## 1. Raw API Response Inspection

A sample of 6 records (3 Flash, 3 Pro) from the provenance log:

### Flash sample

| chain_id | content | reasoning_content (chars) | finish_reason | output_tokens |
|---|---|---|---|---|
| gen9ou-2260297169_p2_shuffled_1337 | EMPTY | 315 | **length** | 64 |
| gen9ou-2261012168_p1_shuffled_7919 | EMPTY | 346 | **length** | 64 |
| gen9ou-2262855067_p1 | EMPTY | 298 | **length** | 64 |

### Pro sample

| chain_id | content | reasoning_content (chars) | finish_reason | output_tokens |
|---|---|---|---|---|
| gen9ou-2260297169_p2_shuffled_1337 | EMPTY | 317 | **length** | 64 |
| gen9ou-2261012168_p1_shuffled_7919 | EMPTY | 313 | **length** | 64 |
| gen9ou-2262855067_p1 | EMPTY | 322 | **length** | 64 |

**Key observations:**
1. `content` is empty (zero bytes) for every record across both models
2. `reasoning_content` is populated (252–346 chars, ~65–90 tokens) for every record
3. `finish_reason = "length"` for every record — budget exhausted
4. `output_tokens = 64` for every record — exactly the `max_tokens` cap, no exceptions

---

## 2. Diagnostic I Comparison

Diagnostic I tested native thinking mode with `max_tokens=4096` on the same model family. Results from `diagnostic_I_summary.json`:

| Model | N | `max_tokens` | Records with content | Max completion tokens | Parsed at strict/permissive |
|---|---|---|---|---|---|
| V4-Flash | 20 | 4096 | ~3 | 701 | 3 (15%) |
| V4-Pro | 20 | 4096 | ~12 | 540+ | 12 (60%) |

In Diagnostic I, `raw_response` (content) IS populated. Flash produced 417–701 tokens of content per parsed record; Pro produced 284–540 tokens. The models do produce textual YES/NO answers in `content` when given sufficient token budget.

**Comparison to Day 1 L18 L4:**

| | Diagnostic I | Day 1 L18 L4 |
|---|---|---|
| `max_tokens` | 4096 | 64 |
| `content` field | Populated (~400–700 tokens for parseable) | **Empty (0 tokens)** |
| `reasoning_content` | Populated | Populated (~65–90 tokens) |
| `finish_reason` | `stop` | **`length`** |
| Parsed rate | 15–60% | **0%** |

---

## 3. Operationalization Gap Diagnosis

**Root cause: `max_tokens=64` consumes the total output token budget (reasoning + content combined), and the model allocates all 64 tokens to `reasoning_content` before producing any content.**

### Evidence

- Every record has `output_tokens=64` (exactly the cap) and `finish_reason=length`
- `reasoning_content` at ~65–90 tokens fills or slightly exceeds the budget
- `content` is empty in every record without exception

### What this tells us about DeepSeek's API

The SPEC intended `max_tokens=64` to apply to the **content field only**, with `reasoning_content` server-allocated separately (SPEC §7 table: `L4: 64 (on content) | thinking enabled; reasoning_content server-allocated separately`). This is consistent with Anthropic's extended thinking API, where thinking tokens have a separate budget from output tokens.

**However, DeepSeek V4-Flash/Pro's implementation applies `max_tokens` to the total output (reasoning + content combined).** The 64-token budget is consumed by the early portion of reasoning, and the model never reaches the content generation phase where it would produce a YES/NO verdict. Diagnostic I confirms that with 4096 tokens, content IS produced — the threshold where content begins appearing is well above 64 tokens (empirically: Flash needs ~400+ tokens to produce parseable content under thinking mode).

### Why `reasoning_content` is populated

The model begins reasoning immediately upon receiving the prompt. The `reasoning_content` captures tokens 1–64 of the model's output. At token 64, the API cuts off generation, producing `finish_reason=length`. The model had not yet reached a conclusion — the reasoning snippets show the model mid-analysis (e.g., "Let's parse each step... Step 1: ...") without any conclusion statement.

### SPEC design intent vs. implementation reality

| Aspect | SPEC intent | Observed behavior |
|---|---|---|
| `max_tokens` scope | Content only; reasoning separately allocated | Total output (reasoning + content) |
| Content at `max_tokens=64` | YES/NO verdict + anchor | Empty (model never reaches content phase) |
| Reasoning at `max_tokens=64` | Server-allocated separately | Truncated at 64 tokens, mid-reasoning |
| `finish_reason` | `stop` (model completes) | `length` (budget exhausted) |

---

## 4. Content vs. Reasoning Token Attribution

The `usage.output_tokens=64` in every record represents the total budget consumed, not content tokens only. Since `content` is empty, all 64 tokens went to `reasoning_content`. This means:

- 0 content tokens per record
- ~64 reasoning tokens per record (slightly less than 64 due to how the tokenizer counts)
- No content output to parse

---

## 5. Minimum Token Budget Estimate

From Diagnostic I:
- Flash: minimum observed completion_tokens for a parseable response = 404 tokens
- Pro: minimum observed = ~280 tokens

A conservative estimate: `max_tokens=512` would likely produce parseable content for most Pro records and some Flash records. `max_tokens=1024` (the budget used for L18 L2/L3) would provide adequate headroom based on empirical max of 701 tokens observed in Diagnostic I.

---

## 6. Summary Diagnosis

| Question | Answer |
|---|---|
| Is `content` empty? | Yes — all 100 records |
| Is `reasoning_content` populated? | Yes — all 100 records (252–346 chars) |
| Why is `content` empty? | `max_tokens=64` exhausted by reasoning before content phase |
| Is this a parser bug? | No — the parser-cascade-on-content rule is correctly applied |
| Is this an API call error? | No — API calls succeed (200 OK, no `api_failure`) |
| Is this a model bug? | No — model is actively reasoning; it's a token-budget design mismatch |
| What would fix it? | Raise `max_tokens` for L18 L4 to ≥512 (or ≥1024 to match L18 L2/L3) |
| Does DeepSeek separate reasoning from content token budgets? | No — contrary to SPEC assumption |

---

## 7. Recommendation for Both-Author Decision

**The L18 L4 operationalization is incompatible with DeepSeek's actual API behavior under `max_tokens=64`.** All 100 records are structurally unmeasurable: the model reasons but cannot output a verdict within the allotted budget.

**Options for both-author review:**

**A. Amendment #7 — Rerun L18 L4 with increased max_tokens**  
Raise `max_tokens` to 1024 for L18 L4 (matching L18 L2/L3 budget). Cost ~$0.41 additional (100 calls × ~1000 tokens average). Produces comparable CoT L4 data. Requires Amendment #7 sign-off before execution.

**B. Accept L18 L4 as untestable in current configuration**  
Classify all 100 records as structural measurement failures. Report as a program limitation: "Lever 18 L4 (native thinking) could not be measured because DeepSeek applies `max_tokens` to total output rather than content alone, contrary to SPEC assumption. A retest with higher token budget is deferred to future work." No amendment needed; OLAT findings stand without L18 L4.

**C. Hybrid: accept L18 L4 as untestable but document for Mew**  
Same as B, plus document the finding for Mew design: native thinking at current SPEC configuration is incompatible with the YES/NO output framing. Mew should test native thinking with a higher content budget or a different answer extraction method.

**This decision belongs to both authors.** The diagnostic confirms the mechanism. Do not run L18 L4 again without an Amendment #7 sign-off.
