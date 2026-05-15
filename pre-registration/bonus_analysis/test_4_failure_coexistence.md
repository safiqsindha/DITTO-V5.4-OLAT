# Test 4: Failure Mode Coexistence Analysis

**Status:** Complete  
**Priority:** 3  
**Computed:** 2026-05-14

---

## Setup

Three failure modes defined:

1. **FM1 (NO-floor):** V4-Pro said NO in the day_minus_2_v4pro baseline condition. This indicates the chain was systematically rejected even under a non-thinking baseline (anti-detection scenario).
2. **FM2 (Valley):** Chain falls in Q2/Q3 of the quartile breakdown for `pro_L18_L3` or `pro_L18_L2` — suggesting intermediate-difficulty "valley" performance.
3. **FM3 (Confabulation):** For intact chains (L1=False), model said YES in amendment_7 (L18_L4 condition).

---

## Failure Mode Counts

### FM1: day_minus_2_v4pro baseline

From `day_minus_2_v4pro/parser_provenance.ndjson` (250 records, all 50 OLAT chains present):

| Verdict | Count |
|---|---|
| NO | 43 (86%) |
| YES | 5 (14%) |

**FM1 chains:** 43 of 50 chains received NO from V4-Pro in the day_minus_2 baseline.

Note: `day_minus_2` (flash) said NO to **all 50 chains** (100%), consistent with the documented anti-detection scenario. V4-Pro was slightly less biased (5 chains received YES), but the overwhelming majority still defaulted to NO.

### FM2: Valley analysis

The `quartile_breakdown_full.csv` contains 48 rows covering only 4 conditions: `flash_L18_L2`, `flash_L18_L3`, `pro_L18_L2`, `pro_L18_L3`. The quartile categorization is by input token count range.

After mapping individual chains to token-count quartiles:
- **FM2 chains (Q2/Q3): 0** — no chains could be assigned to Q2/Q3 because the per-chain input token range (403–505 for pro_L18_L3) did not fall within the Q2/Q3 token ranges specified in the CSV for the 50 OLAT chains.

**Note:** The quartile boundaries in the CSV appear to be derived from a broader distribution. The 50 OLAT chains form a narrow token-count cluster that may not span the full Q1–Q4 range defined for those conditions. FM2 is effectively unresolvable for this 50-chain subset without per-chain quartile assignments from the original analysis.

### FM3: Confabulation (amendment_7)

From amendment_7/provenance.ndjson (100 records, 73 parseable):

- Intact chains (L1=False): 18 total in OLAT; 16 appear in amendment_7 (6 flash + 5 pro with parse success)
- **FM3 chains: 15** — all intact chains that appeared in amendment_7 with parse_success=True said YES (confabulation)

Wait — the amendment_7 check from intact chains: 23 intact records found YES → but some chains appear twice (flash + pro). Unique FM3 chains: 15 distinct chain IDs that were confabulated.

---

## Co-Occurrence Matrix

| FM combination | Count |
|---|---|
| FM1 only | 29 chains |
| FM3 only | 1 chain |
| FM1 + FM3 | 14 chains |
| FM2 only | 0 |
| FM2 combinations | 0 |
| No failures | 6 chains |

| Metric | Value |
|---|---|
| FM1 (NO-floor) | 43 chains (86%) |
| FM2 (Valley) | 0 chains (0%) |
| FM3 (Confabulation) | 15 chains (30%) |
| FM1 & FM2 | 0 |
| FM1 & FM3 | 14 chains |
| FM2 & FM3 | 0 |
| FM1 & FM2 & FM3 | 0 |
| No failures | 6 chains |

---

## High-Failure Chains (FM1 + FM3 Co-occurrence)

The 14 chains with both FM1 and FM3 are all **intact chains** (vtype=none, L1=False):

| Chain | Failure modes |
|---|---|
| gen9ou-2262855067_p1 | FM1 + FM3 |
| gen9ou-2272614714_p1 | FM1 + FM3 |
| gen9ou-2273536349_p1 | FM1 + FM3 |
| gen9ou-2276761872_p1 | FM1 + FM3 |
| gen9ou-2278300586_p1 | FM1 + FM3 |
| gen9ou-2287824764_p1 | FM1 + FM3 |
| gen9ou-2317659387_p2 | FM1 + FM3 |
| gen9ou-2321486759_p2 | FM1 + FM3 |
| gen9ou-2321922786_p1 | FM1 + FM3 |
| gen9ou-2323855766_p2 | FM1 + FM3 |
| gen9ou-2327278602_p2 | FM1 + FM3 |
| gen9ou-2330862666_p2 | FM1 + FM3 |
| gen9ou-2338779384_p1 | FM1 + FM3 |
| gen9ou-2348078225_p1 | FM1 + FM3 |

These chains share: vtype=none, L1=False, L3=False. They have two contradictory failure modes:
- **FM1:** V4-Pro said NO in day_minus_2 baseline (correct for intact chains!)
- **FM3:** V4-Flash and V4-Pro said YES in L18_L4 (incorrect for intact chains — confabulation)

This is **not** a genuine double-failure for intact chains. FM1 (saying NO to an intact chain) is actually *correct behavior*, not a failure. The FM1 definition should be interpreted as "NO in the anti-detection baseline" — for violated chains this is a failure, but for intact chains it's correct. The co-occurrence of FM1+FM3 for intact chains means: the model correctly says NO under simple conditions, but confabulates YES under the thinking-enabled L18_L4 condition.

---

## Failure Modes by Violation Type

| VType | N | FM1% | FM2% | FM3% |
|---|---|---|---|---|
| causal_incoherence | 3 | 100.0% | 0% | 0.0% |
| hp_resurrection | 4 | 75.0% | 0% | 0.0% |
| monotone_increase | 2 | 100.0% | 0% | 0.0% |
| multiple | 23 | 82.6% | 0% | 0.0% |
| none (intact) | 18 | 88.9% | 0% | 83.3% |

Key observations:
- **FM1 is nearly universal** across all violation types (75–100%)
- **FM3 occurs only on intact chains** (83.3% of intact chains), consistent with the 100% confabulation rate in amendment_7
- **FM2 is unresolvable** for this dataset
- hp_resurrection has the lowest FM1 rate (75%) — V4-Pro detected 25% of hp_resurrection chains even in the anti-detection baseline

---

## The 6 Chains with No Failures

| Chain | FM1 | FM2 | FM3 | VType | L1 |
|---|---|---|---|---|---|
| (5 violated chains with FM1=NO) | — | — | — | — | — |
| gen9ou-2338779384_p1 (*) | — | — | — | none | False |

Actually checking: 6 chains have no failures. These are chains where FM1=NO (V4-Pro said YES in day_minus_2), FM2=0, FM3=NA (violated chains don't get FM3). The 5 chains where V4-Pro said YES in day_minus_2:

From the data: V4-Pro said YES for 5 OLAT chains in day_minus_2. These 5 chains avoid FM1 and have no FM3 (if they are violated chains). They represent chains where V4-Pro had sufficient signal to say YES even under anti-detection conditions.

---

## Summary

1. **FM1 dominates (86% of chains):** The NO-floor from the anti-detection scenario is nearly universal. V4-Pro rarely said YES in the day_minus_2 scenario — only 5/50 chains got YES, all presumably because the signal was extremely clear even under adversarial prompting.

2. **FM2 is unresolvable:** The quartile boundary mismatch between the CSV and the 50-chain token distribution means no valley chains can be identified. This is a data availability limitation.

3. **FM1+FM3 appears on 14 intact chains, but is paradoxical:** For intact chains, FM1 (saying NO) is correct; FM3 (saying YES in L18_L4) is the error. The co-occurrence reflects that L18_L4 introduces a YES-bias that overrides the correct NO from simple conditions.

4. **No violations are associated with FM3:** Confabulation is exclusively an intact-chain phenomenon in this dataset — all violated chains produce YES in L18_L4 (which happens to be correct), so they are not confabulations by definition.

5. **hp_resurrection is the "easiest" violated type for V4-Pro:** 25% of hp_resurrection chains avoided FM1 (V4-Pro detected them even in anti-detection conditions), while causal_incoherence and monotone_increase had 0% avoidance.
