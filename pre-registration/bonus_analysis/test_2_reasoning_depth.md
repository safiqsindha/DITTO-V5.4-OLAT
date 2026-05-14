# Test 2: Cross-Condition Reasoning Comparison

**Status:** Complete  
**Priority:** 3  
**Computed:** 2026-05-14

---

## Setup

**L18 L3 reasoning:** From `parser_provenance.ndjson`, conditions `pro_L18_L3` (n=50) and `flash_L18_L3` (n=48), using the `raw_output` field (model's full response including chain-of-thought before YES/NO).

**L18 L4 reasoning:** From `amendment_7/provenance.ndjson`, using `reasoning_content` field (native thinking mode, separate from final answer).

**N records analyzed:**
- L18 L3: 98 records (48 flash + 50 pro)
- L18 L4: 73 records (38 flash + 35 pro, with reasoning_content populated)
- Total: 171 records

**Scoring dimensions:**
1. **rules_mentioned:** Count of distinct rule categories mentioned in reasoning (max 9)
2. **counter_evidence:** Binary — presence of counter-evidence words (however, but, although, etc.)
3. **verification_chains:** Count of "if.*then", "since.*therefore", "because.*so" patterns
4. **reasoning_length:** Character count of reasoning text

---

## Comparison Table

| Group | N | Rules | Counter% | Verif | Length (chars) | Accuracy (vs L1) |
|---|---|---|---|---|---|---|
| L18 L3 (flash) | 48 | 7.08 | 93.8% | 0.06 | 2,223 | 0.667 |
| L18 L3 (pro) | 50 | 6.68 | 78.0% | 0.00 | 1,860 | 0.700 |
| L18 L4 (flash) | 38 | 7.39 | 100.0% | 2.26 | 8,111 | 0.684 |
| L18 L4 (pro) | 35 | 7.23 | 100.0% | 1.60 | 7,023 | 0.686 |

---

## L18 L4 vs L18 L3 (Overall)

| Group | N | Rules | Counter% | Verif | Length |
|---|---|---|---|---|---|
| L18 L3 (all) | 98 | 6.88 | 85.7% | 0.03 | 2,038 |
| L18 L4 (all) | 73 | 7.32 | 100.0% | 1.95 | 7,590 |

**Relative differences (L18 L4 vs L18 L3):**

| Metric | L18 L3 | L18 L4 | Ratio |
|---|---|---|---|
| Rules mentioned | 6.88 | 7.32 | 1.1× higher |
| Counter-evidence rate | 85.7% | 100.0% | 1.2× higher |
| Verification chains | 0.03 | 1.95 | **63.5× higher** |
| Reasoning length | 2,038 chars | 7,590 chars | **3.7× longer** |
| Accuracy (vs L1) | 0.684 | 0.685 | essentially equal |

---

## Analysis

### Rules Mentioned
L18 L4 mentions slightly more rule categories (7.32 vs 6.88), but the difference is small. Both modes cover nearly all 9 categories in every trace (the chain structure triggers mentions of HP, PP, Phase, Tool, etc. in almost every reasoning). This dimension does not clearly differentiate L3 from L4.

### Counter-Evidence
L18 L3 pro (78.0%) and flash (93.8%) are both high, but L18 L4 achieves 100% for both models. The native thinking mode universally employs counter-evidence language — the model explicitly considers alternative interpretations before reaching a conclusion. This structural difference is real.

### Verification Chains
The most dramatic difference: L18 L3 produces essentially no "if-then / since-therefore / because-so" reasoning chains (0.03 average), while L18 L4 produces 1.95 chains per record. The native thinking mode explicitly chains logical conditionals, while text-prompt CoT in L18 L3 tends to use more declarative statements.

### Reasoning Length
L18 L4 traces are 3.7× longer on average (7,590 vs 2,038 characters). The native thinking mode generates extended internal deliberation that is captured in `reasoning_content`, while text-prompt CoT in `raw_output` is shorter and more constrained.

### Accuracy
Despite the dramatic differences in reasoning depth and length, **accuracy is essentially identical: 0.684 (L18 L3) vs 0.685 (L18 L4)**. More sophisticated reasoning does not translate to better performance. This is the central paradox of Test 2.

---

## Chain-Level Comparison (Common Chains, Pro Model)

For the 35 chains where pro model appears in both L18 L3 and L18 L4:

| Metric | L18 L3 (pro) | L18 L4 (pro) |
|---|---|---|
| Rules mentioned | 6.77 | 7.23 |
| Counter-evidence rate | 0.83 | 1.00 |
| Verification chains | 0.00 | 1.60 |

The per-chain comparison confirms the aggregate results. Pro model's L18 L4 reasoning is consistently deeper by all structural metrics, but maps to the same accuracy on matched chains.

---

## Flash vs Pro Comparison

| Metric | Flash L18 L3 | Pro L18 L3 | Flash L18 L4 | Pro L18 L4 |
|---|---|---|---|---|
| Rules | 7.08 | 6.68 | 7.39 | 7.23 |
| Counter% | 93.8% | 78.0% | 100% | 100% |
| Verif chains | 0.06 | 0.00 | 2.26 | 1.60 |
| Length | 2,223 | 1,860 | 8,111 | 7,023 |
| Accuracy | 0.667 | 0.700 | 0.684 | 0.686 |

Flash generates longer and more verification-chain-rich L18 L3 reasoning than Pro, but Pro achieves higher accuracy under L18 L3. Flash generates longer L18 L4 reasoning (8,111 vs 7,023 chars) with more verification chains (2.26 vs 1.60), but accuracy is nearly equal (0.684 vs 0.686).

The pro model is more concise but equally accurate across both reasoning modes.

---

## Is L18 L4 Reasoning "Genuinely Deeper"?

By structural metrics: **yes, unambiguously.**
- 3.7× longer reasoning
- 100% counter-evidence (vs 85.7%)
- 65× more logical chain patterns

By outcome: **no difference.**
- Accuracy is identical (0.684 vs 0.685)
- The extended reasoning does not improve detection rates

This pattern is consistent with the broader L18_L4 findings (Test 1): native thinking mode generates more elaborate reasoning but also introduces confabulation on intact chains. The confabulation rate exactly compensates for any detection improvements — the model catches more violations but also invents more false violations.

---

## Methodological Notes

1. **L18 L3 raw_output includes the YES/NO answer** as part of the text, so rule mentions may be inflated by the format. Keyword matching is done on the full raw_output string, which may include the chain text (if the model echoes it).

2. **L18 L4 reasoning_content is truly separate** from the final answer — it represents the model's internal deliberation. The scoring reflects this internal process.

3. The verification_chain patterns ("if.*then", etc.) match quite broadly and may include conditional statements within the chain description itself, not just the model's own reasoning.

4. All 27 records with parse_success=False in amendment_7 were excluded (these had no reasoning_content or unparseable output).

---

## Summary

L18 L4 (native thinking) produces reasoning that is structurally deeper by every metric: longer, more counter-evidence, more verification chains. However, this depth does not translate to higher accuracy. The same chains that were analyzed in L18 L3 are analyzed equally well (or equally poorly) in L18 L4. The reasoning quality improvement is real but functionally inert — it does not change the output distribution. This suggests the fundamental limitation is not in the reasoning process but in the chain representation itself or the model's ability to ground its reasoning in the specific constraint patterns present in the chains.
