# Task A4: Prompt Robustness Pre-Work — Variant Design

**Date:** 2026-05-15  
**Status:** Complete  
**API cost:** $0 (design only; API runs in Part B)

---

## Question

Do the V1-minimal NO-floor and L18 L4 confabulation effects survive paraphrase and formatting
perturbations? If they disappear under slight wording changes, the regime effects are
wording-specific rather than capability-level phenomena.

---

## Prompt Variants (4 total)

All variants test the same core question: "Does this chain contain a rule violation?"
with a YES/NO expected output. The variations probe sensitivity to surface form.

### Variant 0 — Control (original OLAT prompt)

**Regime: V1-minimal (L18 L1)**
```
Does this battle chain contain any rule violations? The answer is YES or NO.
```
*Anchor:* `The answer is YES` / `The answer is NO`

**Regime: L18 L4 (native thinking)**
```
Does this battle chain contain any rule violations? The answer is YES or NO.
```
*Note: Identical wording to V1-minimal; manipulation is in API parameter (thinking=enabled)*

---

### Variant 1 — Light Paraphrase

**Design intent:** Semantically equivalent but with different surface phrasing. Same question
structure (direct YES/NO), same anchor type, different word choices.

**Regime: V1-minimal**
```
Does this chain of battle events contain any violations of the rules? Answer YES or NO.
```
*Anchor:* `YES` / `NO` (parser should catch via last_token stage)

**Regime: L18 L3 (CoT condition — paraphrase test)**
```
Does this chain of battle events contain any violations of the rules? Review each event
and check for rule compliance. Answer YES or NO.
```
*Anchor:* `YES` / `NO`

**Changes from Variant 0:** "battle chain" → "chain of battle events"; "rule violations" →
"violations of the rules"; "The answer is YES or NO" → "Answer YES or NO".

---

### Variant 2 — Alternative Phrasing

**Design intent:** Different question framing that preserves the YES/NO response requirement
but uses a structurally different question form.

**Option A (consistency framing):**
```
Is this battle sequence internally consistent with the rules of the game?
Return YES if it is consistent, NO if any rule is broken.
```
*Anchor:* Parser catches trailing YES/NO

**Option B (binary detection framing):**
```
Analyze this sequence of battle events. Return YES if any rules are broken,
return NO if all events conform to valid battle rules.
```
*Anchor:* Parser catches trailing YES/NO

**Recommended:** Option B for V1-minimal (tests whether the "broken rules" framing vs
"violations" framing changes the floor behavior). Option A for L18 L4 (tests whether
the "consistency" framing changes confabulation).

---

### Variant 3 — Formatting Perturbation

**Design intent:** Same semantic content as Variant 0 but with different visual structure.
Bullet formatting instead of inline instructions.

**Regime: V1-minimal**
```
Review the battle chain below.
- Does it contain any rule violations?
- Answer YES or NO.

The answer is YES or NO.
```
*Anchor:* `The answer is YES` / `The answer is NO`

**Regime: L18 L3 (CoT condition — formatting test)**
```
Review the battle chain below.
- Go through each event in sequence.
- Check whether each event conforms to the rules of Pokemon battles.
- Identify any event that violates a rule.
- Answer YES if any rule is violated, NO if all events are valid.

Therefore, the answer is YES or NO.
```
*Anchor:* `Therefore, the answer is YES` / `Therefore, the answer is NO`

---

## Which Regimes to Test

### Primary: V1-minimal (L18 L1)
**Most important test.** The NO-floor (detection_rate_violated ≈ 0 across all conditions under
V1-minimal framing) is the foundational OLAT finding. If the NO-floor disappears under Variant 1
(light paraphrase), the floor is wording-specific — not a capability property. If it persists
across all variants, the floor is robust and the methodology claim is defensible.

### Secondary: L18 L3 (best CoT condition)
Tests whether the Meaningful effect (effect_size=0.354 in L3 universe for pro_L18_L3) survives
paraphrase. If the CoT effect disappears under paraphrase, it's prompt-specific.

### Optional: L18 L4 (native thinking confabulation)
Tests whether the 100% YES-bias found in Amendment #7 survives paraphrase. If confabulation
disappears when phrasing changes, it was an artifact of the specific anchor+thinking mode
combination.

---

## Sample Chain Selection (seed=43)

**Note:** Different seed from A3 to ensure orthogonality between self-consistency and prompt
robustness samples. Some chain overlap with A3 is acceptable (chains are used differently).

### Selected 20 chains

**Intact (10 chains, L3_symbolic_checker=False):**

| Chain ID |
|----------|
| gen9ou-2272614714_p1 |
| gen9ou-2278300586_p1 |
| gen9ou-2286522581_p1_shuffled_1337 |
| gen9ou-2301379516_p1_shuffled_42 |
| gen9ou-2317659387_p2 |
| gen9ou-2321486759_p2 |
| gen9ou-2321922786_p1 |
| gen9ou-2327376263_p1 |
| gen9ou-2338779384_p1 |
| gen9ou-2348078225_p1 |

**Violated (10 chains, L3_symbolic_checker=True, stratified by type):**

| Chain ID | Violation type |
|----------|---------------|
| gen9ou-2260297169_p2_shuffled_1337 | hp_resurrection |
| gen9ou-2283533709_p2_shuffled_1337 | multiple |
| gen9ou-2310254076_p2_shuffled_42 | multiple |
| gen9ou-2310556760_p1_shuffled_7919 | multiple |
| gen9ou-2320109494_p1_shuffled_1337 | monotone_increase |
| gen9ou-2320790123_p1_shuffled_1337 | multiple |
| gen9ou-2334711641_p2_shuffled_7919 | causal_incoherence |
| gen9ou-2343591826_p1_shuffled_1337 | multiple |
| gen9ou-2343602002_p1_shuffled_7919 | multiple |
| gen9ou-2345018884_p1_shuffled_7919 | multiple |

**Violated allocation:** causal_incoherence=1, hp_resurrection=1, monotone_increase=1, multiple=7
(proportional to corpus distribution: 3:4:2:23 → 10-slot allocation).

---

## Pre-Registered Outcome Interpretations

### Primary test: V1-minimal NO-floor robustness

**Reference metric:** `detection_rate_violated` under V1-minimal Variant 0 (expected ≈ 0.0–0.13
per OLAT primary finding).

#### Outcome 1: NO-floor and effects persist across all variants

**Trigger:** `detection_rate_violated` under each variant is within ±0.10 of Variant 0.

**Interpretation:** Regime effects are robust to surface phrasing. The NO-floor is a capability
property of the model under minimal instruction, not an artifact of the specific OLAT wording.
The methodology claim is defensible without qualification.

**Writeup implication:** Add supporting sentence: "The V1-minimal NO-floor was verified to
persist under 3 prompt surface perturbations (light paraphrase, alternative phrasing, formatting
change), ruling out wording-specificity as a confound."

---

#### Outcome 2: Effects survive paraphrase (Variants 1-2) but break under formatting change (Variant 3)

**Trigger:** Variants 1-2 stay within ±0.10 of Variant 0; Variant 3 diverges by >0.10.

**Interpretation:** The NO-floor is robust to semantic rephrasing but sensitive to visual
formatting structure. This is a methodologically interesting finding:
- The floor is not about specific vocabulary
- The floor MAY be about structural parsing of the prompt (the model responds to prompt format,
  not just question content)
- Mew audit prompts should use consistent visual format with OLAT validation prompts

**Writeup implication:** "The V1-minimal NO-floor survived paraphrase but was sensitive to
formatting perturbation. Format consistency is a design constraint for Mew audit prompts."

---

#### Outcome 3: Effects break under Variant 1 (light paraphrase)

**Trigger:** `detection_rate_violated` under Variant 1 is >0.15 higher than under Variant 0
(i.e., paraphrase breaks the floor).

**Interpretation:** The NO-floor is wording-specific — it is an artifact of the specific OLAT
prompt phrasing, not a general capability property. This is a significant finding requiring
writeup revision.

**Response if Outcome 3:**
1. Do NOT retroactively reclassify OLAT findings — document as a robustness limitation
2. Add explicit disclaimer to writeup: "The V1-minimal NO-floor was observed to be
   wording-specific — varying the prompt phrasing substantially changed detection rates."
3. Surface for both-author review before any publications
4. This finding changes the Mew implication: detection behavior is highly prompt-sensitive,
   making prompt engineering a core engineering requirement (not just a calibration detail)

---

### Secondary test: L18 L3 CoT effect robustness

**Reference metric:** `gap = detection_rate_violated − detection_rate_intact` under L18 L3
Variant 0 (expected: gap ≈ 0.354 from OLAT primary analysis).

#### Outcome A: CoT effect (gap) persists across variants (±0.10)

**Interpretation:** The Meaningful L18 L3 effect is robust to prompt surface variation.
The effect is a property of CoT instruction + detection task, not the specific OLAT phrasing.

#### Outcome B: CoT effect disappears under paraphrase (gap drops below 0.10)

**Interpretation:** The L18 L3 effect is prompt-specific. Requires writeup qualification and
both-author review. May affect Mew's use of the L18 L3 condition as a primary detection protocol.

---

## Execution Checklist (for tomorrow's API session)

**Input:** 20 selected chains × 4 prompt variants × 2 test regimes (V1-minimal + L18 L3)
= **160 API calls** (primary; add ~80 if L18 L4 optional included)

- [ ] Construct 4 variant prompts per chain per condition (no API — text substitution)
- [ ] Run all 160 calls: 20 chains × 4 variants × 2 regimes
- [ ] Apply 4-stage parser cascade to each response
- [ ] Compute per-variant detection_rate_violated and detection_rate_intact
- [ ] Compute gap per variant
- [ ] Compare Variant 1-3 gaps to Variant 0 gaps
- [ ] Check parse failure rates per variant (critical: formatting variants may produce higher failure rates)
- [ ] Save raw responses to `prompt_robustness/raw_responses.ndjson`
- [ ] Apply pre-registered outcome classification

**Output files:**
- `pre-registration/prompt_robustness/raw_responses.ndjson` (160 records)
- `pre-registration/prompt_robustness/effect_table_per_variant.csv`
- `pre-registration/prompt_robustness/robustness_summary.md`

**Cost estimate:** ~$0.30–1.00 (160 calls, mixed V1-minimal at 32 tokens and L18 L3 at 1024 tokens)

---

## Parser Notes for Variant Responses

Variant 0 uses the locked OLAT anchor (`The answer is YES/NO` or `Therefore, the answer is YES/NO`)
which the 4-stage cascade is designed for.

Variants 1-3 use different anchor forms — this will likely DECREASE Stage 1-2 parse success and
INCREASE Stage 3-4 rescues. Consequences:
- Higher unparse rate is expected and acceptable for robustness testing
- Parser provenance records stage for each response (needed for sensitivity analysis)
- Primary analysis excludes unparseables; sensitivity analysis includes them (as-NO, as-random)
- Compare parse failure rates across variants — a high failure rate in Variant 3 (formatting)
  may itself be evidence of prompt sensitivity

**Recommended parser extension for variants:**
- Stage 1 (Strict): original OLAT anchors
- Stage 2 (Permissive): `(answer is|answer:|conclusion:)\s*(yes|no)` — catches "Answer YES"
- Stage 3 (md_strip + permissive): catches markdown-decorated answers
- Stage 4 (last_token): catches trailing YES/NO
- For Variant 2 (consistency framing): "YES if it is consistent" needs to be handled carefully
  — "is consistent" maps to NO_violation which is the REVERSE of the YES label. Flag this
  explicitly and apply semantic inversion before scoring.

**Critical for Variant 2 Option A:** "Return YES if consistent, NO if any rule is broken" —
this inverts the label convention relative to OLAT (where YES=violated). Must apply label
inversion when computing detection rates for Variant 2A. Document in analysis.
