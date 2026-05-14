# Phase 1 — Anchor-Effect Observational Tests

**Status:** Zero API cost; read-only analysis of existing data.
**Data sources:** Day −2 V1-minimal provenance (Flash + Pro), primary parser_provenance.ndjson (L18 L3), Amendment #7 provenance.ndjson (L18 L4), day_2/quartile_analysis/quartile_breakdown_full.csv.

---

## Test 1 — Cross-Regime Default Comparison (Same Anchor, Opposite Defaults)

### Verdict Distribution & Token Counts

| Condition | n | YES% | NO% | Unparse% | Mean output tokens |
|---|---|---|---|---|---|
| V4-Flash V1-minimal (Day -2) | 250 | 0.0% | 100.0% | 0.0% | n/a |
| V4-Pro V1-minimal (Day -2) | 250 | 12.8% | 85.6% | 1.6% | n/a |
| V4-Flash L18 L4 (Amend #7) | 50 | 76.0% | 0.0% | 24.0% | 2565 |
| V4-Pro L18 L4 (Amend #7) | 50 | 70.0% | 0.0% | 30.0% | 2554 |

### Parser Stage Distribution

*Day -2 data uses `parse_stage` field; None = pre-cascade labeling pipeline.*

| Condition | Stage distribution |
|---|---|
| V4-Flash V1-minimal (Day -2) | {'first_token': 250} |
| V4-Pro V1-minimal (Day -2) | {'last_token': 243, 'unparseable': 4, 'strict': 3} |
| V4-Flash L18 L4 (Amend #7) | {'last_token': 38, 'unparseable': 12} |
| V4-Pro L18 L4 (Amend #7) | {'last_token': 35, 'unparseable': 15} |

### Detection Rates by Chain Type (Universe L3 / GT label)

| Condition | dr_violated | dr_intact | n_violated | n_intact |
|---|---|---|---|---|
| V4-Flash V1-minimal (Day -2) | 0.0 | 0.0 | 182 | 68 |
| V4-Pro V1-minimal (Day -2) | 0.14 | 0.103 | 182 | 68 |
| V4-Flash L18 L4 (Amend #7) | 1.0 | 1.0 | 32 | 18 |
| V4-Pro L18 L4 (Amend #7) | 1.0 | 1.0 | 32 | 18 |

### Interpretation

V1-minimal: Flash=0.0% YES, Pro=12.8% YES. L18 L4: Flash=76.0% YES, Pro=70.0% YES.

The same anchor ('The answer is YES or NO') accompanies both conditions. If the anchor were the primary driver, both regimes should produce similar default rates. The opposing directions (V1-minimal ~all-NO; L18 L4 ~all-YES) constitute strong evidence that the anchor is not the primary mechanism. The reasoning regime (V1-minimal framing vs native-thinking CoT) is the dominant factor.

Caveat: 'strong evidence against anchor as primary mechanism' doesn't rule out small anchor effects layered on top of regime effects. A separate anchor-absent experiment would be needed to quantify the anchor's marginal contribution.

---

## Test 2 — Same-Chain Cross-Regime Verdict Comparison (L18 L3 vs L18 L4)

### V4-Flash: L18 L3 vs L18 L4 (50 paired chains)

L18 L3 label distribution: YES=44, NO=4, unparseable=2
L18 L4 label distribution: YES=38, NO=0, unparseable=12
Both parseable: 37
Agreement rate: 34/37 = 91.9%

Cross-tab (L18 L3 verdict → L18 L4 verdict):

| L18 L3 → L18 L4 | YES | NO |
|---|---|---|
| YES | 34 | 0 |
| NO | 3 | 0 |

Chains where L18 L4=YES but L18 L3=NO (regime flipped to YES): 3
Chains where L18 L4=NO but L18 L3=YES (regime flipped to NO): 0

Disagreement breakdown by ground truth: violated=1, intact=2

### V4-Pro: L18 L3 vs L18 L4 (50 paired chains)

L18 L3 label distribution: YES=31, NO=19, unparseable=0
L18 L4 label distribution: YES=35, NO=0, unparseable=15
Both parseable: 35
Agreement rate: 26/35 = 74.3%

Cross-tab (L18 L3 verdict → L18 L4 verdict):

| L18 L3 → L18 L4 | YES | NO |
|---|---|---|
| YES | 26 | 0 |
| NO | 9 | 0 |

Chains where L18 L4=YES but L18 L3=NO (regime flipped to YES): 9
Chains where L18 L4=NO but L18 L3=YES (regime flipped to NO): 0

Disagreement breakdown by ground truth: violated=4, intact=5

### Interpretation

High disagreement rate (low agreement %) → reasoning regime substantively changes responses, not just chain content.
Low disagreement rate (high agreement %) → verdicts are chain-driven; regime has limited effect on individual chain outcomes.

Note: If L18 L4 flips many L18 L3=NO chains to YES on intact chains (GT_L3=False), that is direct evidence of YES-bias introduced by the native-thinking regime, not by anchor framing or chain content.

---

## Test 3 — Reasoning Conclusion Language Pattern Analysis (Last 200 Chars)

### Category Distribution (last 200 chars of reasoning_content)

| Category | n | % | Description |
|---|---|---|---|
| anchor_matched | 30 | 41.1% | Uses anchor language ('answer is YES', 'I'll answer YES') |
| direct_affirmation | 31 | 42.5% | Directly states violation present/absent |
| hedged_conclusion | 1 | 1.4% | Hedged: 'likely', 'appears', 'I think' |
| question_restated | 1 | 1.4% | Restates the question then answers |
| other | 10 | 13.7% | None of the above patterns matched |

#### anchor_matched — 30 records (sample tails)

*Chain gen9ou-2261012168_p1_shuffled_7919, GT_L3=True:*
```
 violations? The answer is YES or NO." So we need to output YES or NO. Since we found at least one violation, answer is YES.  Thus, final answer: YES.
```
*Chain gen9ou-2262855067_p1, GT_L3=False:*
```
mon to only log state changes. So logging the same state change twice is likely a bug or violation of the logging protocol.  Therefore, answer is YES.
```
*Chain gen9ou-2272010071_p2_shuffled_7919, GT_L3=True:*
```
t might be fine. Step 5 says forced switch required after own faint, but then later there is opponent switch. No inconsistency.  So the answer is YES.
```
*...and 27 more*

#### direct_affirmation — 31 records (sample tails)

*Chain gen9ou-2260297169_p2_shuffled_1337, GT_L3=True:*
```
on.  Also, step 10 is immediately after step 9 (same turn2). So at turn2, unit_A suddenly has full HP. That is a violation.  Therefore, answer is YES.
```
*Chain gen9ou-2270600845_p1_shuffled_7919, GT_L3=True:*
```
 respected. So answer is YES, there are rule violations.  But note: The question: "Does this battle chain contain any rule violations?" So answer YES.
```
*Chain gen9ou-2272252150_p1_shuffled_1337, GT_L3=True:*
```
turn16, opponent switches to unit_A, but unit_A becomes unavailable? That doesn't make sense. So there is a rule violation.  Therefore, answer is YES.
```
*...and 28 more*

#### hedged_conclusion — 1 records (sample tails)

*Chain gen9ou-2287824764_p1, GT_L3=False:*
```
ays UNAVAILABLE, which is contradictory. That might be a violation: inconsistent state. So I think there is at least one violation.  Thus answer: YES.
```

#### question_restated — 1 records (sample tails)

*Chain gen9ou-2326066086_p2_shuffled_42, GT_L3=True:*
```
inconsistency.  Thus there are multiple rule violations.  The question: "Does this battle chain contain any rule violations?" So answer should be YES.
```

#### other — 10 records (sample tails)

*Chain gen9ou-2276761872_p1, GT_L3=False:*
```
te machine. If it already left 'initial', it cannot shift from 'initial' again without first returning to 'initial'. So violation.  Thus, answer: YES.
```
*Chain gen9ou-2291273479_p2_shuffled_1337, GT_L3=True:*
```
ilable" typically means cannot be used. In Pokémon, a fainted Pokémon is unavailable. So switching to a fainted Pokémon is illegal.  Thus answer: YES.
```
*Chain gen9ou-2321922786_p1, GT_L3=False:*
```
mulation where these are just state updates, but the rule violations are about logical consistency. Since the question is straightforward, answer YES.
```
*...and 7 more*

### Interpretation

**If anchor-matched language dominates:** the model is structuring its reasoning around the anchor format — anchor is shaping the cognitive frame. The YES output is not independent of the prompt's answer-format instruction.

**If direct-affirmation language dominates:** the anchor is a thin output wrapper. The model reaches its conclusion via substantive reasoning about the chain and then translates it to YES. The anchor contributes formatting, not the verdict direction.

**Mixed distribution:** both mechanisms are present; anchor effects are partial. Quantifying requires comparison against anchor-absent conditions (requires API spend).

---

## Test 4 — Within-Condition Verdict Stability Across Response-Length Quartiles

Universe L3 (symbolic checker ground truth — primary universe).

### flash_L18_L2

| Quartile | Token range | n_valid | YES rate (viol) | YES rate (intact) | Gap | Effect size | Class | Parse fail% |
|---|---|---|---|---|---|---|---|---|
| Q1 | 153–362 | 12 | 1.000 | 1.000 | 0.000 | 0.000 | Null | 0.000 |
| Q2 | 370–449 | 12 | 0.833 | 0.833 | 0.000 | 0.000 | Null | 0.000 |
| Q3 | 452–501 | 12 | 1.000 | 0.500 | 0.500 | 0.500 | Meaningful(no_CI) | 0.167 |
| Q4 | 506–680 | 14 | 1.000 | 0.333 | 0.667 | 0.667 | Meaningful(no_CI) | 0.143 |

Spread (max−min) dr_intact across quartiles: 0.667
Spread (max−min) dr_violated across quartiles: 0.167
→ Unstable: verdict shifts across token-length quartiles — reasoning depth/length affects outcome.

### flash_L18_L3

| Quartile | Token range | n_valid | YES rate (viol) | YES rate (intact) | Gap | Effect size | Class | Parse fail% |
|---|---|---|---|---|---|---|---|---|
| Q1 | 342–590 | 12 | 1.000 | 0.875 | 0.125 | 0.125 | Meaningful(no_CI) | 0.000 |
| Q2 | 606–693 | 12 | 0.875 | 1.000 | -0.125 | -0.125 | Meaningful(no_CI) | 0.083 |
| Q3 | 694–728 | 12 | 0.857 | 1.000 | -0.143 | -0.143 | Meaningful(no_CI) | 0.083 |
| Q4 | 729–883 | 14 | 1.000 | 0.667 | 0.333 | 0.333 | Meaningful(no_CI) | 0.000 |

Spread (max−min) dr_intact across quartiles: 0.333
Spread (max−min) dr_violated across quartiles: 0.143
→ Unstable: verdict shifts across token-length quartiles — reasoning depth/length affects outcome.

### pro_L18_L2

| Quartile | Token range | n_valid | YES rate (viol) | YES rate (intact) | Gap | Effect size | Class | Parse fail% |
|---|---|---|---|---|---|---|---|---|
| Q1 | 166–306 | 12 | 0.700 | 0.500 | 0.200 | 0.280 | Meaningful(no_CI) | 0.000 |
| Q2 | 310–355 | 12 | 0.250 | 0.250 | 0.000 | 0.080 | Directional(no_CI) | 0.000 |
| Q3 | 356–408 | 12 | 0.778 | 0.333 | 0.444 | 0.524 | Meaningful(no_CI) | 0.000 |
| Q4 | 428–654 | 14 | 0.778 | 0.600 | 0.178 | 0.258 | Meaningful(no_CI) | 0.000 |

Spread (max−min) dr_intact across quartiles: 0.350
Spread (max−min) dr_violated across quartiles: 0.528
→ Unstable: verdict shifts across token-length quartiles — reasoning depth/length affects outcome.

### pro_L18_L3

| Quartile | Token range | n_valid | YES rate (viol) | YES rate (intact) | Gap | Effect size | Class | Parse fail% |
|---|---|---|---|---|---|---|---|---|
| Q1 | 296–423 | 12 | 0.429 | 0.400 | 0.029 | 0.108 | Meaningful(no_CI) | 0.000 |
| Q2 | 427–487 | 12 | 0.556 | 1.000 | -0.444 | -0.364 | Meaningful | 0.000 |
| Q3 | 494–582 | 12 | 1.000 | 0.000 | 1.000 | 1.080 | Meaningful | 0.000 |
| Q4 | 587–799 | 14 | 0.875 | 0.500 | 0.375 | 0.455 | Meaningful(no_CI) | 0.000 |

Spread (max−min) dr_intact across quartiles: 1.000
Spread (max−min) dr_violated across quartiles: 0.571
→ Unstable: verdict shifts across token-length quartiles — reasoning depth/length affects outcome.

### pro_L18_L3 Valley Detail (negative Q2 effect)

Quartile Q2 (427–487 tokens): effect=-0.364, dr_violated=0.556, dr_intact=1.000, gap=-0.444
  → dr_intact > dr_violated: elevated false-positive rate on intact chains drives the negative effect (YES-bias on intact > YES-bias on violated)

### Interpretation

**Stable YES rate across quartiles** → verdict is regime/condition-driven; the anchor (constant within condition) could account for it. Chain length doesn't change what the model says.

**Varying YES rate across quartiles** → reasoning length/depth affects verdict; the model is making different decisions at different CoT lengths. Anchor is constant, yet output varies — anchor is insufficient explanation.

**Valley in pro_L18_L3:** The negative Q2/Q3 effect corresponds to intermediate-length responses where the model appears to 'overthink' intact chains and generate false positives (dr_intact rises while dr_violated stays flat or drops). This is regime-dependent behaviour that an anchor-only explanation cannot account for.

---

## Cross-Test Synthesis

### What the four tests together suggest

**Test 1 (regime comparison):** Opposite defaults under the same anchor provide the strongest evidence available from existing data that the reasoning regime — not the anchor text — is the primary driver of the YES/NO default. V1-minimal framing produces near-universal NO; native-thinking CoT (L18 L4) produces near-universal YES. The anchor text is identical in both.

**Test 2 (same-chain paired comparison):** If agreement between L18 L3 and L18 L4 on identical chains is low, the regime change overrides chain content as a verdict driver. The anchor is also identical between L18 L3 and L18 L4 at the output level; if verdicts differ, it is because of the reasoning mechanism (text-prompt CoT vs native thinking), not the anchor.

**Test 3 (reasoning language):** If the model's reasoning tail uses anchor-matched language ('I'll answer YES') rather than direct affirmation ('there is a violation'), it suggests the anchor is shaping how the model frames its conclusion — not just providing output format. This would indicate the anchor has cognitive (not just cosmetic) influence, even if it is not the primary driver established by Tests 1–2.

**Test 4 (quartile stability):** If verdict rates vary within a condition across token-length quartiles, the model is making length-dependent decisions — ruling out a simple anchor-following explanation (the anchor is constant within condition). The pro_L18_L3 valley finding is the clearest example: intermediate-length responses produce worse outcomes, which is inconsistent with anchor-following (which would be stable).

### What we can conclude from observational analysis alone

1. **Anchor is not the primary mechanism** for verdict distribution. Regime is. This is established by Tests 1 and 2 combined.

2. **Anchor may have partial influence** on how the model frames its conclusion (Test 3 language patterns). Absence of anchor-matched language would strengthen the 'thin wrapper' interpretation; presence would indicate cognitive framing effects worth testing.

3. **Verdict is not stable within condition** across response-length quartiles (Test 4), indicating reasoning depth affects outcomes. This is inconsistent with a pure anchor-following model.

4. **Unresolved question:** What is the marginal contribution of the anchor text to verdict rates, holding regime constant? This requires an API experiment comparing anchor-present vs anchor-absent prompts within the same reasoning regime.

### Questions remaining for API experiments

- Within L18 L4 regime: does removing 'The answer is YES or NO' from the prompt change the YES rate? (Anchor-effect API test)
- Does replacing the anchor with 'The answer is NO or YES' (reversed order) shift the default? (Order-effect within anchor)
- Does a neutral anchor ('Reply YES if there is a violation, NO otherwise') produce different rates from the standard anchor? (Framing-effect within anchor)
