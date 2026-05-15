# Test 5: Reasoning Topic Modeling

**Status:** Complete (null finding)
**Priority:** 4
**Data sources:**
- `amendment_7/provenance.ndjson` — 100 L18 L4 records with `reasoning_content`
- `parser_provenance.ndjson` — 98 L18 L3 records with `raw_output` (CoT reasoning)
**Computed:** 2026-05-14
**Method:** TF-IDF (max 2,000 features, bigrams, sublinear_tf) + LSA (50 components) + KMeans (k by silhouette)

Note: `sentence-transformers/all-MiniLM-L6-v2` was unavailable (no internet access for model weights). TF-IDF + LSA is the embedding method. Results should be interpreted as a lower-bound on what semantic embeddings might reveal.

---

## Setup

| Source | N traces | Mean length | Range |
|---|---|---|---|
| L18 L4 (reasoning_content) | 100 | 9,791 chars | 4,744–17,089 |
| L18 L3 flash (raw_output) | 48 | 2,038 chars | 1,108–4,081 |
| L18 L3 pro (raw_output) | 50 | 2,038 chars | 1,170–4,412 |
| **Total** | **198** | **5,954 chars** | — |

Diagnostic records (F/G/H/I) had no `reasoning_content` — the specified ~440-record corpus was not available. The 198-record corpus used here is what exists on disk.

---

## Cross-Condition Clustering (L18 L3 + L18 L4 Together)

**Result: trivial separation artifact**

Best k=2, silhouette=0.136. The two clusters map exactly onto the two conditions:

| Cluster | N | Condition | YES rate | Correctness | Mean length |
|---|---|---|---|---|---|
| C0 | 100 | L18_L4 (100%) | 73.0% | 59.0% | 9,791 |
| C1 | 98 | L18_L3 (100%) | 76.5% | 68.4% | 2,038 |

The clustering finds format/length differences between conditions, not reasoning patterns. Cross-condition topic modeling on this corpus is uninformative.

---

## Within-Condition Clustering

### L18 L4 (native thinking, n=100)

Best k=4, silhouette=0.079 (below 0.1 threshold for meaningful structure).

| Cluster | N | YES% | Correct% | Mean len | Flash% | Intact% |
|---|---|---|---|---|---|---|
| C0 | 37 | 54.1% | 40.5% | 12,566 | 59.5% | 51.4% |
| C1 | 26 | 61.5% | 46.2% | 12,292 | 42.3% | 46.2% |
| C2 | 23 | 100.0% | 87.0% | 5,573 | 43.5% | 13.0% |
| C3 | 14 | 100.0% | 85.7% | 4,744 | 50.0% | 14.3% |

**Distinctive terms:**
- C0 (long traces, uncertain): "unavailable", "recover_in", "it", "that", "available" — heavy discussion of tool availability
- C1 (long traces, uncertain): "hazard", "opponent", "unit", "fainted", "hazard_response" — heavy discussion of hazard mechanics
- C2 (short traces, decisive YES): "step", "turn", "at", "from", "unavailable" — telegraphic step-by-step commentary
- C3 (short traces, decisive YES): "turn", "step", "monotone_decrease", "87", "decay" — focused resource tracking

**Pattern:** The dominant split is reasoning length and decisiveness. Shorter L18 L4 traces (C2, C3) go 100% YES with higher correctness — these appear to be violated chains where the model identifies violations quickly. Longer traces (C0, C1) are more uncertain (YES rates ~55-62%) and skew toward intact chains and lower correctness. This suggests longer deliberation is associated with harder/intact chains, not deeper reasoning.

**Medoid examples:**

C0 (long, uncertain): `gen9ou-2301379516_p1_shuffled_42` — *"We are given a sequence of steps from a battle log. Need to check if any rule violations occur... Need to infer the game rules. Possibly from a Pokémon-like game?"* [13,000 chars, YES, L1=True — anomalous checker-wrong chain]

C2 (short, decisive): `gen9ou-2310556760_p1_shuffled_7919` — *"We are asked: 'Does this battle chain contain any rule violations?' We need to analyze the sequence of steps..."* [5,573 chars, YES, L1=True — correctly detected]

### L18 L3 Flash (n=48)

Best k=2, silhouette=0.035 (noise-level structure).

| Cluster | N | YES% | Correct% | Mean len |
|---|---|---|---|---|
| C0 | 21 | 90.5% | 71.4% | 2,426 |
| C1 | 27 | 92.6% | 63.0% | 2,066 |

Distinctive terms are specific turn numbers ("turn 17", "turn 10", "turn 11") and unit names — indicating the clustering is picking up **which specific chain** is being discussed, not which reasoning strategy is being used. This is a chain-content leakage artifact: the model quotes the chain's step labels verbatim, so TF-IDF separates traces by which chain they describe, not how they reason.

### L18 L3 Pro (n=50)

Best k=6, silhouette=0.031 (noise). Clusters have correctness ranging from 50.0% to 85.7% but with n as small as 5. Distinctive terms are again stop-word level ("is", "step", "turn", "this") plus chain-content leakage. No interpretable reasoning patterns.

---

## Assessment: Null Finding

**The topic modeling does not reveal meaningful reasoning patterns.**

Three converging reasons:

1. **Silhouette scores are uniformly low** (0.031–0.079), all below the conventional 0.2 threshold for meaningful cluster structure. The embedding space has no strong cluster geometry.

2. **Distinctive terms are content artifacts, not reasoning strategies.** In L18 L3 traces, the model quotes chain steps verbatim (e.g., "turn 10", "pp_action_1_opp", "monotone_decrease"), so TF-IDF separates traces by which chain they describe rather than how the model reasons about it. The "clusters" are really chain-identity clusters.

3. **The one substantive L18 L4 pattern (length × decisiveness) is a consequence finding, not a reasoning-type finding.** Long traces correlate with harder chains (more intact, lower correctness); short traces correlate with easier violated chains. This is already captured by Test 3 (chain difficulty) and Test 2 (reasoning depth) — it adds no new structural insight.

**Would semantic embeddings (sentence-transformers) change this?** Possibly for the chain-content leakage issue — semantic embeddings would weight rule-reasoning phrases more than verbatim step labels. However, the fundamental problem (small N, chains quoted verbatim in reasoning traces) would persist. A negative or weak finding is the most likely outcome with better embeddings as well.

---

## Data Limitations vs Task Specification

The task specified ~440 diagnostic records + 73 L18 L4 records = ~513 traces. Actual available data: 198 traces. The diagnostic records (F/G/H/I) have no `reasoning_content` — this was not discovered until the battery began. With 513 traces, within-condition clustering might achieve stronger structure (more within-condition variation to detect). The null finding should be interpreted as:

> *With 198 traces and TF-IDF embeddings, no meaningful reasoning clusters are detectable. Whether richer data or better embeddings would change this is unknown.*

---

## Mew Implications

The null finding is itself informative: reasoning traces, as text, do not self-organize into distinct strategy clusters on this task. This means:

1. Reasoning style is not a reliable routing signal — Mew cannot use reasoning-pattern classification to decide which chains need which treatment.
2. The variation that exists (length × chain difficulty) is better captured by the structural features in Test 3 and Test 6 (chain features, lever choice) than by reasoning text analysis.
3. If reasoning-based routing is ever revisited, it would require semantic embeddings and more diverse reasoning traces (e.g., including non-L18 CoT conditions), not just L18 L3/L4.
