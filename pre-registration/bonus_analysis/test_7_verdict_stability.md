# Test 7: Verdict Stability Analysis

**Status:** Complete  
**Priority:** 3  
**Computed:** 2026-05-14

---

## Setup

For each of 50 chains × 64 conditions in `parser_provenance.ndjson`:
- Collected all valid (parse_success=True) verdicts (YES/NO) per chain
- Computed YES rate per chain across all conditions
- Computed per-chain binary entropy: H = -p·log₂(p) - (1-p)·log₂(1-p)

Excluded: `flash_L18_L4` and `pro_L18_L4` (no valid parses in main provenance — those records are in amendment_7).

---

## Stability Classification

| Category | Threshold | N chains |
|---|---|---|
| Stable | entropy < 0.5 | 5 |
| Middle | 0.5 ≤ entropy ≤ 1.0 | 45 |
| Unstable | entropy > 1.0 | 0 |

**No chains are "unstable" (H > 1.0).** All chains fall below maximum entropy, and most fall in the middle range. This is because:
- All chains have YES rates between 0.082 and 0.300 (never near 0.5)
- Maximum entropy (H=1.0) requires p=0.5, which is never reached
- The models are biased toward NO — most chains see YES rates well below 50%

**Stable chains (H < 0.5):** 5 chains

| Category | Stable | Middle |
|---|---|---|
| Intact (violation_type=none) | 4 | 14 |
| Violated | 1 | 31 |

Stable intact chains: models consistently say NO (low YES rate → low entropy).  
The one stable violated chain: `gen9ou-2301944495_p1_shuffled_42` (H=0.409, YES rate=0.082) — so consistently rejected that it's nearly stable.

---

## YES Rate Distribution

| YES Rate Range | N chains | Intact | Violated |
|---|---|---|---|
| [0.0, 0.2) | 34 | 13 | 21 |
| [0.2, 0.4) | 16 | 5 | 11 |
| [0.4, 0.6) | 0 | 0 | 0 |
| [0.6, 0.8) | 0 | 0 | 0 |
| [0.8, 1.0) | 0 | 0 | 0 |

- **Minimum YES rate:** 0.082 (`gen9ou-2301944495_p1_shuffled_42`, vtype=multiple)
- **Maximum YES rate:** 0.300 (`gen9ou-2327376263_p1`, vtype=none — intact chain!)
- **Mean YES rate:** 0.177

**Critical observation:** No chain has YES rate above 0.30. The models are overwhelmingly biased toward NO. Even the most "detectable" violated chain produces YES in only 29% of conditions. The highest YES-rate chain is actually an *intact* chain (`gen9ou-2327376263_p1`), indicating some intact chains are slightly more prone to false-positive responses.

---

## Full Entropy Distribution

| Chain | YES Rate | Entropy | VType | L3 GT |
|---|---|---|---|---|
| gen9ou-2327376263_p1 | 0.300 | 0.881 | none | False |
| gen9ou-2310556760_p1_shuffled_7919 | 0.288 | 0.866 | multiple | True |
| gen9ou-2328038098_p2_shuffled_1337 | 0.262 | 0.830 | multiple | True |
| gen9ou-2320790123_p1_shuffled_1337 | 0.259 | 0.825 | multiple | True |
| gen9ou-2354144810_p2_shuffled_7919 | 0.246 | 0.805 | multiple | True |
| gen9ou-2283533709_p2_shuffled_1337 | 0.242 | 0.798 | multiple | True |
| gen9ou-2347015993_p1_shuffled_1337 | 0.237 | 0.791 | multiple | True |
| ... | ... | ... | ... | ... |
| gen9ou-2321486759_p2 | 0.102 | 0.474 | none | False |
| gen9ou-2273536349_p1 | 0.098 | 0.464 | none | False |
| gen9ou-2323855766_p2 | 0.098 | 0.464 | none | False |
| gen9ou-2348078225_p1 | 0.085 | 0.419 | none | False |
| gen9ou-2301944495_p1_shuffled_42 | 0.082 | 0.409 | multiple | True |

The five stable chains (H < 0.5) are four intact chains and one violated chain (`gen9ou-2301944495_p1_shuffled_42`).

---

## Entropy by Violation Type

| VType | Mean H | Max H | Min H | N |
|---|---|---|---|---|
| none (intact) | 0.628 | 0.881 | 0.419 | 18 |
| causal_incoherence | 0.613 | 0.687 | 0.514 | 3 |
| hp_resurrection | 0.674 | 0.741 | 0.567 | 4 |
| monotone_increase | 0.675 | 0.741 | 0.610 | 2 |
| multiple | 0.685 | 0.866 | 0.409 | 23 |

Entropy is surprisingly similar across violation types. The multiple category has the widest range (0.409–0.866) — some multiple-violation chains are nearly stable (models consistently reject them) while others are relatively variable. Intact chains have the lowest mean entropy (0.628) but also contain the highest-entropy chain (H=0.881).

---

## Cross-Condition Consistency

| Category | Count |
|---|---|
| Always YES (every condition) | 0 |
| Always NO (every condition) | 0 |
| Mixed | 50 |

Every chain receives at least one YES and at least one NO across the 62 analyzable conditions. No chain is perfectly consistent. This is expected given the wide variation in conditions (from near-random baselines to strong-signal L18_L3 conditions).

---

## Key Interpretation

1. **No true instability:** The absence of any chain with H > 1.0 means there are no chains where the model is genuinely confused (near 50/50). Instead, models lean heavily NO with some conditions pushing toward YES.

2. **Violated chains show slightly higher entropy than intact chains:** Mean entropy 0.685 vs 0.628. This is backward from what might be expected — violated chains "should" get more YES votes, but they primarily get NO votes with some YES votes under certain conditions, creating mild entropy. Intact chains also get mostly NO votes but slightly more consistently.

3. **The entire YES-rate range is [0.082, 0.300]:** This narrow, low range is the signature of a strong NO-bias. Even under the best conditions (L18_L3, L18_L2), many chains still receive NO in most conditions — the YES conditions are outnumbered by the NO conditions in the 64-condition design.

4. **Verdicts are semi-stable but not fixed:** All 50 chains are "mixed" (some YES, some NO conditions), meaning the models can be pushed toward YES under the right conditions, but the default is NO. Condition engineering is the primary lever for changing verdicts.

5. **The one stable violated chain** (`gen9ou-2301944495_p1_shuffled_42`, H=0.409) is also the worst-performing chain overall (overall DR = 0.082) — its stability comes from being consistently rejected across all conditions, which is wrong (it's a real violation).
