# Multi-Agent Symbolic Checker Construction Experiment

## What This Is

This document describes a controlled empirical experiment to determine whether LLMs can
independently construct working symbolic constraint checkers from Pokemon battle telemetry
chains. The experiment answers six concrete questions about LLM-driven checker construction
across capability tiers, information access conditions, and workflow patterns — and connects
findings to Mew commercial positioning.

The experiment is fully pre-registered. Success criteria are fixed before any agent runs.
Interpretation follows results, not the other way around.

---

## Feasibility Assessment (This Environment)

Before executing, it is important to be clear about what can be done in this repo vs. what
requires external data or multi-session coordination.

### What is available here

- `pre-registration/chain_variants/` — 3,200 formatted constraint chains with ground truth
  labels across violation types: `none`, `multiple`, `hp_resurrection`, `causal_incoherence`,
  `monotone_increase`. These are in the exact text format the builder agents will process.
- `pre-registration/day_minus_3/chain_pool_inventory.json` — full inventory of the 19,428-chain
  pool, including violation type distribution and symbolic checker verdict counts.
- `pre-registration/scripts/` — existing Python infrastructure for chain handling and analysis.

### What is not in this repo

- The full 19,428-chain corpus (`Ditto V1/chains/real_v2` and `shuffled_v2`). These are
  referenced by path but not committed here.
- The existing Pokemon symbolic checker (`pokemon-v1-symbolic/`) and its verdict CSV
  (`phase3_results_v4.csv`). Required for the baseline performance measurement.

### What a single Claude Code session can and cannot do

| Task | Feasible here? | Notes |
|------|---------------|-------|
| Create `LLMtoCriteria.md` write-up | Yes | This document |
| Scaffold experiment directory structure | Yes | Full tree, all scripts |
| Write builder prompt template | Yes | Chain schema extractable from chain_variants |
| Write validation harness | Yes | Code complete; needs chain data to execute |
| Run Setup Task 1 (baseline) | No | Symbolic checker not in repo |
| Run Setup Task 2 (chain sets, full pool) | Partial | Can use 3,200 available chains for reduced-scale version; full 500-chain held-out set requires full corpus |
| Run Agent A1 (Sonnet, no-internet) | Yes | This session IS the Sonnet agent |
| Run Agent A2 (Haiku, no-internet) | No | Requires separate session with Haiku model |
| Run Agent B1 (Opus + internet) | No | Requires separate session with Opus model |
| Run Agents B2, B3 (Sonnet/Haiku + internet) | Partial | B2 feasible in this session with web tools; B3 needs Haiku session |
| Run Agent C1 (Sonnet, serebii-only) | Partial | Feasible if domain restriction enforced by prompt |
| Phase 2 validation | Partial | Code ready; requires chain data |
| Phase 3 synthesis | Yes (after data) | Once per-agent results exist |

**Bottom line:** The experiment framework can be fully built here. Execution requires either
(a) transferring chain data into this environment, or (b) coordinating builder runs across
separate model-specific sessions with shared output artifacts.

---

## Experiment Overview

Six (potentially eight) builder agents independently construct Pokemon symbolic checkers
from constraint chains. A separate validation instance measures performance against the
existing Pokemon checker as ground-truth benchmark. The experiment characterizes
LLM-driven checker construction across capability tiers, information access conditions,
and workflow patterns.

**Posture:** Controlled empirical experiment. Each agent operates in isolation. Validation
is fully separated from generation. Success criteria pre-specified. Results interpreted only
after all agents complete.

**Critical separation:** No builder agent has access to the existing Pokemon checker code,
symbolic checker output files, or any code in `pokemon-v1-symbolic/`. Builder agents work
only from provided constraint chain examples and rule category descriptions.

---

## Pre-Experiment Setup

### Setup Task 1: Verify Existing Checker Baseline

Confirm the existing Pokemon checker's performance on the held-out validation set.

- Load checker from `Ditto-5.3- Pokemon Diag/pokemon-v1-symbolic/`
- Run on chain corpus, capturing per-chain verdicts
- Measure: precision, recall, F1, per-rule-category accuracy
- Document in `experiment/baseline_performance.md`

**Stop condition:** If baseline diverges substantially from documented 96% accuracy /
precision 1.0 / recall 0.94 on the 50-chain OLAT sample, stop and surface — this would
indicate baseline drift affecting experiment interpretation.

### Setup Task 2: Construct Development and Validation Chain Sets

Source: 19,428-chain pool with symbolic checker verdicts as ground truth.

**Development set** (provided to builder agents):
- 30 chains: 15 intact, 15 violated
- Violated chains include diverse violation types (all major rule categories represented)
- Seed=42

**Validation set** (held out, used by validation instance only):
- 500 chains: stratified by violation type to match pool distribution
- Disjoint from development set
- Seed=84

**Iteration test set** (agent self-testing):
- 10 chains randomly selected from the 30 development chains
- Agents may run their checker against this set during construction
- Agents cannot access ground truth for the other 20 development chains
- Mimics realistic Mew workflow: human validates small subset, LLM iterates

**Persist:**
- `experiment/chains/development_set.jsonl`
- `experiment/chains/iteration_test_set.jsonl`
- `experiment/chains/validation_set.jsonl`

**Reduced-scale fallback (if full corpus unavailable):**
Use the 3,200 chains in `chain_variants/` with stratified sampling:
- Development: 30 chains (same proportions)
- Iteration test: 10 chains (subset of development)
- Validation: 200 chains (reduced from 500; power is lower but direction of findings remains interpretable)

### Setup Task 3: Builder Prompt Template

A single shared prompt all six builders receive, varying only in model identity and tool
configuration.

```
You are building a symbolic constraint checker for Pokemon battle telemetry.

TASK:
Build a Python module that takes a constraint chain (Pokemon battle log in
structured JSON format) and returns:
- verdict: "YES" if any rule violation is detected, "NO" otherwise
- triggered_rules: list of rule categories that fired (if any)

The module's main function should have signature:
def check_chain(chain: dict) -> dict:
    """
    Returns: {"verdict": "YES" or "NO", "triggered_rules": [list of rule names]}
    """

CONSTRAINT CHAIN FORMAT:
[insert chain schema documentation here — field names, types, structure]

RULE CATEGORIES TO CHECK (9 categories):
1. HP resurrection: HP increase patterns that violate game mechanics
2. PP monotone violation: PP values that don't decrease monotonically per move
3. Causal incoherence: Actions taken when Pokemon should not be able to act
4. Phase transition violation: Turn ordering or game phase violations
5. Tool availability: Use of unavailable tools (items, abilities, etc.)
6. Information state violation: Decisions based on information not yet revealed
7. Coordination violation: Multi-Pokemon coordination issues
8. Optimization violation: Statistically anomalous suboptimal play
9. Temporal ordering: Events occurring out of temporal sequence

You will receive 30 example chains with ground truth labels (15 intact, 15
violated, mixed violation types).

You may iteratively refine your checker by:
1. Writing initial code
2. Running on the iteration_test_set (10 chains, ground truth provided)
3. Reviewing failures, revising code
4. Repeating up to 5 iteration cycles

CONSTRAINTS:
- Maximum 5 iteration cycles
- Maximum 4096 tokens per response
- Must produce executable Python code by final cycle
- Code must handle the chain schema exactly as provided
- Do not access any existing checker code

DELIVERABLES:
1. Final Python module: checker.py
2. Brief design rationale (one paragraph)
3. Self-assessment: which rule categories are you most/least confident about?

Begin.
```

The chain schema documentation is extracted from `pre-registration/chain_variants/`. The
actual chain format uses a text-structured step sequence:

```
Step N (turn=T):
  ResourceBudget: <resource_name> at <pct>% (decay=<decay_type>)
  SubGoalTransition: phase shifted from '<from>' to '<to>'
  CoordinationDependency: ? depends on ? -> expected_action=?
  InformationState: added=[<tokens>] removed=[<tokens>] uncertainty=<0.0-1.0>
  ToolAvailability: <unit> is now UNAVAILABLE (recover_in=<n>)
```

Key fields that matter for rule checking:
- `ResourceBudget` with `decay=none` and increasing `hp_unit_*` values → HP resurrection
- `ResourceBudget` with `pp_action_*` values not monotone decreasing → PP violation
- `ToolAvailability: UNAVAILABLE` followed by action from that unit → causal incoherence
- `SubGoalTransition` ordering inconsistencies → phase transition violation
- `InformationState` with low uncertainty but decisive action → information state violation

### Setup Task 4: Agent Tool Configurations

| Agent | Model | Internet | Notes |
|-------|-------|----------|-------|
| A1 | Sonnet | None | Standard code execution only |
| A2 | Haiku | None | Standard code execution only |
| B1 | Opus | General | Web search + URL fetch, all domains |
| B2 | Sonnet | General | Web search + URL fetch, all domains |
| B3 | Haiku | General | Web search + URL fetch, all domains |
| C1 | Sonnet | Restricted | serebii.net only; all other domains blocked |

For all internet-enabled agents: log every search query and every URL fetched with
timestamp. This generates the search domain data for cross-agent analysis.

Note on domain restriction: if the sandbox enforces domain restriction via prompt
instruction only rather than at the tool level, document this limitation. Empirical
strength weakens for Group C, but the comparison remains informative.

### Setup Task 5: Optional Additional Agents

**Agent D1 (Sonnet + validation feedback, no internet):** Same as A1 but receives
validation feedback from a separate validator instance after each iteration cycle.
Validator runs checker on a 20-chain subset and returns failure descriptions without
revealing chain content. Tests whether mid-construction feedback improves checker quality.

**Agent E1 (Sonnet pair, collaborative, no internet):** Two Sonnet instances collaborate —
one proposes rule logic, the other implements code. Tests whether multi-agent collaboration
improves construction quality.

Run D1 and E1 only if Phase 1 results from the six core agents are inconclusive and
additional dimensions would clarify.

---

## Experiment Execution

### Phase 1: Independent Builder Runs

For each builder agent (A1, A2, B1, B2, B3, C1):

1. Initialize with shared builder prompt
2. Provide `development_set.jsonl` (30 chains with ground truth)
3. Provide `iteration_test_set.jsonl` reference (10-chain self-test subset)
4. Allow up to 5 iteration cycles
5. Log all agent outputs per cycle:
   - Generated code (full text)
   - Reasoning content (if available)
   - Self-test results (which chains classified correctly/incorrectly)
   - Search queries and URLs visited (Groups B and C only)
6. Capture final deliverables:
   - `final_checker.py`
   - Design rationale paragraph
   - Self-assessment

Run each agent in complete isolation. No agent has access to any other agent's outputs,
intermediate code, or search history.

**Persistence per agent:**
- `experiment/agents/{agent_id}/cycle_{N}_output.json`
- `experiment/agents/{agent_id}/final_checker.py`
- `experiment/agents/{agent_id}/search_log.jsonl` (queries and URLs; empty for no-internet)
- `experiment/agents/{agent_id}/agent_summary.md` (cycles used, tokens, rationale)

### Phase 2: Validation

After all six builder agents complete, a separated validation instance runs with no
exposure to builder agent context. The validator has access only to final code artifacts.

The validation instance:

1. Loads each `final_checker.py`
2. Loads `validation_set.jsonl` (500 chains, held out)
3. For each builder checker:
   - Runs on all 500 validation chains
   - Computes: precision, recall, F1, per-rule-category accuracy
   - Compares each per-chain verdict to symbolic checker ground truth
   - Identifies systematic failure patterns
4. Aggregates results:
   - Performance comparison table across all six agents
   - Per-rule-category performance breakdown
   - Cross-agent agreement analysis
   - Search behavior analysis (Groups B and C)

**Persistence:**
- `experiment/validation/per_agent_performance.json`
- `experiment/validation/cross_agent_comparison.md`
- `experiment/validation/per_rule_breakdown.csv`
- `experiment/validation/disagreement_analysis.md`

### Phase 3: Cross-Agent Synthesis

After validation completes, cross-agent analysis answers the six experimental questions:

**Question 1: Can LLMs build working symbolic checkers from constraint chains?**
Aggregate result across all six agents. "Working" = precision >0.7 AND recall >0.6.
Count agents reaching this threshold.

**Question 2: Does internet access help, and by how much?**
Compare matched-capability pairs:
- A1 (Sonnet, no internet) vs B2 (Sonnet + internet)
- A2 (Haiku, no internet) vs B3 (Haiku + internet)

Compute performance delta per pair.

**Question 3: Does capability tier matter?**
Compare within Group B (all with internet):
- B1 (Opus) vs B2 (Sonnet) vs B3 (Haiku)

Compute performance ordering.

**Question 4: Does domain restriction preserve quality?**
Compare:
- C1 (serebii.net only) vs B2 (general internet, matched capability)
- C1 vs A1 (no internet, matched capability)

**Question 5: What sources do LLMs consult?**
Analyze search logs from Groups B and C:
- Distribution of consulted domains per agent
- Most cited sources
- For Group C: was serebii.net sufficient? Were non-allowed domains attempted?
- Query patterns by intent: rule lookup, implementation lookup, edge case clarification,
  schema understanding

**Question 6: Are there systematic failure patterns?**
Cross-agent failure analysis:
- Which rule categories did all agents handle well?
- Which were systematically difficult?
- Are failures correlated across agents (hard rule categories) or independent
  (agent-specific weaknesses)?

**Persistence:**
- `experiment/synthesis/findings.md`
- `experiment/synthesis/mew_implications.md`

---

## Pre-Specified Success Criteria

These thresholds are fixed before any agent runs. They cannot be adjusted after seeing results.

| Outcome | Threshold | Interpretation |
|---------|-----------|----------------|
| Strong success | Multiple agents: precision >0.85 AND recall >0.80 | LLMs substantially replace expert checker construction |
| Moderate success | Multiple agents: precision >0.7 AND recall >0.6 | LLMs produce useful first drafts requiring human refinement |
| Weak success | At most 1-2 agents at moderate threshold; high variance | High-variance construction; requires agent selection and oversight |
| Failure | No agent reaches moderate threshold | LLM-driven construction not viable with current methodology |

---

## Internet Behavior Analysis (Groups B and C)

For agents with internet access, search log analysis specifically extracts:

1. **Domain frequency:** Top 10 domains by visit count per agent
2. **Authoritative source usage:** Frequency of consulting Pokemon Showdown rules,
   Bulbapedia, Smogon, serebii.net
3. **Code resource usage:** Did agents consult code repositories (GitHub, GitLab)?
   Did they find existing Pokemon checkers? If yes, note as contamination concern.
4. **Query patterns by intent:**
   - Rule lookups ("what are Pokemon HP rules")
   - Implementation lookups ("python parse pokemon battle log")
   - Edge case clarification ("does X count as Y in Pokemon")
   - Schema understanding ("pokemon showdown protocol format")
5. **For Group C (serebii.net restricted):** Was the agent able to find all needed
   information? Were there non-allowed domain access attempts? Did the agent express
   limitations from the restriction?

---

## Stop Conditions

**Stop and surface during Phase 1 if:**
- Any agent appears to have located the existing Pokemon checker code (search log shows
  visits to the project's GitHub if public). Fatal contamination for the blinded condition.
- An agent's checker fails to execute at all by cycle 3 (indicates setup error).
- An agent encounters errors suggesting tool configuration problems.

**Stop and surface during Phase 2 if:**
- Validation reveals baseline performance substantially different from expectations.
- One or more builder checkers achieve near-perfect performance, raising contamination
  concerns.
- Per-rule-category analysis shows extreme variance suggesting inconsistent interpretation
  across agents.

**Stop and surface during Phase 3 if:**
- Findings contradict existing OLAT analysis (e.g., complementarity patterns inconsistent
  with Test 9 findings).
- Search log analysis reveals behaviors warranting ethical or methodological review.

---

## Output Structure

```
experiment/
├── baseline_performance.md
├── chains/
│   ├── development_set.jsonl        (30 chains)
│   ├── iteration_test_set.jsonl     (10 chains, subset of development)
│   └── validation_set.jsonl         (500 chains, held out)
├── agents/
│   ├── A1_sonnet_no_internet/
│   │   ├── cycle_1_output.json
│   │   ├── cycle_2_output.json
│   │   ├── ...
│   │   ├── final_checker.py
│   │   ├── search_log.jsonl         (empty for no-internet agents)
│   │   └── agent_summary.md
│   ├── A2_haiku_no_internet/
│   ├── B1_opus_internet/
│   ├── B2_sonnet_internet/
│   ├── B3_haiku_internet/
│   └── C1_sonnet_serebii_only/
├── validation/
│   ├── per_agent_performance.json
│   ├── cross_agent_comparison.md
│   ├── per_rule_breakdown.csv
│   └── disagreement_analysis.md
└── synthesis/
    ├── findings.md
    └── mew_implications.md
```

---

## Effort Estimate

| Phase | Estimated Duration |
|-------|--------------------|
| Setup (Tasks 1–4) | 1–2 hours |
| Phase 1 (six builder agents, up to 5 cycles each) | 6–10 hours |
| Phase 2 (validation) | 2–3 hours |
| Phase 3 (synthesis) | 2–3 hours |
| **Total** | **11–18 hours** |

---

## Empirical Questions and What This Establishes

| Question | Method | Output |
|----------|--------|--------|
| Can LLMs build working symbolic checkers from constraint chains? | Pass/fail per agent vs. moderate-success threshold | Count of working checkers |
| What is the contribution of training-data knowledge vs. internet access? | Matched-capability pairs A1/B2, A2/B3 | Performance delta at two tiers |
| How does capability tier scale? | Within-Group-B comparison (Opus/Sonnet/Haiku) | Three-point ordering |
| Can the workflow operate under regulated-industry source restrictions? | C1 vs B2, C1 vs A1 | Quality preserved or degraded |
| What documentation does an LLM consult when building a domain checker? | Search log analysis, Groups B and C | Domain distribution, query patterns |
| What are systematic failure modes in LLM-driven checker construction? | Per-rule-category accuracy across all agents | Correlated vs. independent failures |

---

## Mew Commercial Pitch Implications

Pre-specified interpretation framework — determined before any results are seen:

**If strong success:** "LLM-driven rapid cross-domain expansion is empirically validated.
Demonstrated workflow for building production-quality checkers in hours."

**If moderate success:** "Mew accelerates checker construction with LLM-human collaboration.
Empirical effort estimate: [hours per domain based on observed iteration counts]."

**If weak success or failure:** Mew pitch reverts to methodology focus. Cross-domain
expansion claims are softened. Empirical lesson: LLM-driven construction is more limited
than the original pitch implied.

The Mew commercial framing follows the empirical result, not the other way around.

---

## Posture for Execution

- **Experimental discipline:** No agent sees another agent's output. Validation runs
  separated. Success criteria fixed before results.
- **Honest reporting:** If results are weak or null, report that clearly.
- **Contamination vigilance:** If any agent locates the existing checker code, flag
  immediately — this is fatal for the blinded condition.
- **Failure is informative:** All outcome levels are informative for Mew positioning.
  The experiment is valuable regardless of which outcome occurs.
