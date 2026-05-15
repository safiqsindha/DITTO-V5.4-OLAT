# G1 Phase 1 — Modular Checker Decomposition

**Date:** 2026-05-15

---

## STOP Condition: Primary Source Not Available

The G1 experiment description specified:
> Locate at `Ditto-5.3- Pokemon Diag/pokemon-v1-symbolic/detector/pokemon_rule_checker.py`

This file exists on Safiq's local machine at:
`/Users/safiqsindha/Desktop/Project Ditto/Ditto-5.3- Pokemon Diag/pokemon-v1-symbolic/detector/pokemon_rule_checker.py`

It is not committed to any accessible repository in this environment. The path is referenced by `pre-registration/scripts/day_minus_3_chain_pool.py` (line 25), confirming it exists, but the file itself is not available.

**Consequence:** Direct code decomposition of the Pokemon symbolic checker is not possible in this session.

**Substitution analysis:** Two partial sources ARE available:
1. The Ditto-5.1 `src/` directory, which contains the production multi-domain modular architecture (data pipelines, violation injectors, chain building, harness)
2. Inferences about the Pokemon checker's interface from `day_minus_3_chain_pool.py` and the OLAT data
3. The LLM-reconstructed checkers (A1 and B2) built in the LLMtoCriteria experiment, which independently re-derived most of the checker's logic

This document proceeds with the available sources, clearly flagging what is inferred vs directly observed.

---

## Section 1: Component Inventory (Ditto-5.1 Production Architecture)

The Ditto-5.1 `src/` directory is the most complete available example of a modular multi-domain checker framework. The architecture separates domain-specific and domain-general code clearly.

### Domain-General (Framework) Components

| Component | Location | Lines | Role |
|-----------|----------|-------|------|
| `BasePipeline` | `src/cells/base_pipeline.py:1–171` | 171 | Abstract base for all domain pipelines; defines `fetch()`, `parse()`, `extract_events()`, `run()`, `generate_mock_data()` interface |
| `EventStream` / `GameEvent` | `src/common/schema.py` | — | Normalized event sequence representation; domain-agnostic |
| `ChainCandidate` | `src/common/schema.py` | — | Chain with metadata; used by scoring and violation injection |
| `CellConfig` | `src/common/config.py` | — | Per-domain configuration container (cell_id, credentials, mock flag) |
| `score_chain` / `score_batch` | `src/harness/scoring.py:1–73` | 73 | Binary correct/incorrect scoring; domain-agnostic |
| `RunnerOrchestrator` | `src/harness/runner_orchestrator.py` | — | Orchestrates model evaluation across all domains; per-model budget kill-switch |
| `RunnerNative` / `RunnerOpenRouter` | `src/harness/runner_native.py`, `runner_openrouter.py` | — | Model API adapters; domain-agnostic |
| `McNemar` | `src/harness/mcnemar.py` | — | Paired significance testing; domain-agnostic |
| `parse_model_response` | `src/harness/prompts.py` | — | Strict→permissive→first-token response parser; domain-agnostic |
| `InjectionResult` dataclass | `src/harness/violation_injector.py:1–46` | 46 | Wraps an injected chain with violation metadata; domain-agnostic container |

### Domain-Specific Components

| Component | Location | Role |
|-----------|----------|------|
| `PokerPipeline` | `src/cells/poker/pipeline.py:1–497` | Fetches PHH dataset, parses .phh files, converts to EventStreams |
| `PokerExtractor` | `src/cells/poker/extractor.py` | Converts poker hand records to normalized GameEvent sequences |
| `NbaPipeline` + `NbaExtractor` | `src/cells/nba/` | NBA play-by-play acquisition and event normalization |
| `PubgPipeline` + `PubgExtractor` | `src/cells/pubg/` | PUBG match telemetry acquisition |
| `CsgoPipeline` + `CsgoExtractor` | `src/cells/csgo/` | CS:GO demo acquisition |
| `RocketLeaguePipeline` + extractor | `src/cells/rocket_league/` | Rocket League replay acquisition |
| `inject_nba_foul_violation` | `src/harness/violation_injector.py` | NBA-specific: bumps actor_foul_count to 7, keeps actor active |
| `inject_pubg_elimination_violation` | `src/harness/violation_injector.py` | PUBG-specific: marks player eliminated, keeps them acting |
| `inject_poker_folded_acts_violation` | `src/harness/violation_injector.py` | Poker-specific: makes folded player act |
| `inject_csgo_eliminated_acts_violation` | `src/harness/violation_injector.py` | CS:GO-specific: dead player acts post-elimination |
| Per-domain `generate_mock_data()` | Each pipeline subclass | Synthetic data for CI/testing; domain-specific event types and actors |
| Per-domain `format_event()` override | Cell prompt builders (referenced) | Domain-specific event rendering into natural language |

---

## Section 2: Architectural Summary

```
Framework layer (domain-general):
┌──────────────────────────────────────────────────────────┐
│  BasePipeline (abstract)                                 │
│    fetch() → parse() → extract_events() → EventStream   │
│                                                          │
│  ChainBuilder (wraps EventStream → ChainCandidate)       │
│  ViolationInjector (InjectionResult dataclass + per-     │
│    domain inject_*() functions — domain-specific but     │
│    domain-general pattern)                               │
│                                                          │
│  RunnerOrchestrator → RunnerNative / RunnerOpenRouter    │
│  PromptBuilder (formats chain + instructions for model)  │
│  parse_model_response() → binary label                   │
│  Scorer (correct/incorrect per chain)                    │
│  McNemar (paired significance test)                      │
└──────────────────────────────────────────────────────────┘

Domain plugin layer (per-cell):
┌─────────┐  ┌─────┐  ┌──────┐  ┌───────┐  ┌────────────────┐
│  Poker  │  │ NBA │  │ PUBG │  │ CS:GO │  │ Rocket League  │
│Pipeline │  │     │  │      │  │       │  │                │
│Extractor│  │     │  │      │  │       │  │                │
│MockData │  │     │  │      │  │       │  │                │
└─────────┘  └─────┘  └──────┘  └───────┘  └────────────────┘
```

**Framework code (domain-general):** ~500 lines across BasePipeline, schema, scoring, orchestrator, McNemar, response parser.

**Domain plugin code (domain-specific):** ~500 lines per domain (pipeline + extractor + mock data). For 5 domains: ~2,500 lines.

**Framework fraction:** ~500/(500+2500) ≈ **17% framework, 83% domain-specific**. This ratio is expected: data acquisition from real-world APIs is inherently domain-specific. The core EVALUATION logic (chain building → prompt → parse → score → McNemar) is 100% reusable.

---

## Section 3: Pokemon Checker Interface (Inferred)

The Pokemon symbolic checker is not available, but its interface is inferable from OLAT artifacts:

### What can be inferred

**From `day_minus_3_chain_pool.py`:**
- Input: CSV at `outputs/phase3_results_v4.csv`; one row per chain
- Output fields include: `chain_id`, `violation_type`, ground truth labels
- Violation type taxonomy (8 categories):
  - `none` — intact chain, no violation
  - `monotone_increase` — PP or similar resource increases (should only decrease)
  - `dead_unit_returns` — unit marked out-of-battle reappears
  - `hp_resurrection` — HP goes from 0% to >0% 
  - `faint_no_permanence` — faint event without permanent UNAVAILABLE
  - `double_availability` — unit becomes AVAILABLE twice without UNAVAILABLE between
  - `causal_incoherence` — logical ordering violation in battle events
  - `multiple` — two or more of the above coexist

**From the LLMtoCriteria A1/B2 reconstruction:**
A1 (independently derived, no access to checker code) successfully reconstructed:
- `hp_resurrection` rule (0%→>0%, permanent faint + positive HP) ✓
- `monotone_increase` / `pp_monotone_violation` rule ✓
- `causal_incoherence` rule (5 sub-rules) ✓
- A1 missed: `dead_unit_returns`, `faint_no_permanence`, `double_availability` (or these were renamed in checker)

B2 added: `own_faint_no_perm` rule (trigger=own_faint without UNAVAILABLE permanent), which may correspond to the checker's `faint_no_permanence` category.

**Checker architecture (inferred):** The checker processes constraint chain text, applies rule functions per violation category, and returns a verdict + violation_type label. Structure is likely similar to A1/B2 checkers: rule functions + public `check_chain()` API.

---

## Section 4: Cross-Domain Instantiation Specification

For a new domain (example: **financial transactions**), the checkers framework would need:

### What the domain plugin must provide

1. **Data pipeline** (`BasePipeline` subclass):
   - `fetch()`: acquire transaction records (API, CSV, database)
   - `parse()`: normalize to structured dicts
   - `extract_events()`: convert to `EventStream` (transaction = event, account = actor)
   - `generate_mock_data()`: synthetic transactions for testing

2. **Domain-specific constraint rules** (analogous to violation_injector):
   - Identify 3–6 verifiable constraints in the domain
   - Example financial constraints: "account balance cannot go negative," "frozen account cannot transact," "transaction amount ≤ account limit"
   - Each constraint → one `inject_*_violation()` function
   - Each constraint → one detection rule in the symbolic checker

3. **Event rendering** (prompt builder):
   - `format_event()`: converts GameEvent to natural language for LLM prompt
   - Domain-specific field names (e.g., `debit_amount`, `account_id` instead of Pokemon field names)

4. **Constraint context text** (Lever 16 equivalent):
   - 6–10 sentences describing the domain's rules in natural language
   - Rules must map 1:1 to the injected violations

### What can be reused as-is

- `BasePipeline` abstract class (unchanged)
- `ChainCandidate` / `EventStream` / `GameEvent` schema (unchanged)
- `RunnerOrchestrator`, `RunnerNative`, `RunnerOpenRouter` (unchanged)
- `parse_model_response()` strict→permissive→first-token parser (unchanged)
- `score_chain()`, `score_batch()` (unchanged)
- `McNemar` significance test (unchanged)
- `InjectionResult` dataclass (unchanged)

### Rough code estimate

| Component | New code (lines) | Reused code (lines) |
|-----------|-----------------|---------------------|
| Data pipeline (fetch/parse/extract) | ~300 | 0 |
| Mock data generator | ~50 | ~171 (BasePipeline) |
| Constraint rules / violation injectors | ~150 (per 5 rules) | 0 |
| Event renderer / prompt builder | ~100 | ~50 (base prompt) |
| Config / cell registration | ~30 | ~50 (CellConfig) |
| **Total new** | **~630** | **~440 reused** |

New code ≈ 59% of domain-specific code, reused ≈ 41%. The evaluation pipeline (orchestrator, scoring, statistics) requires zero new code.

---

## Section 5: Implications for Mew Architecture

### Is the existing checker modular enough to extract a framework?

**Yes, with qualifications.**

The Ditto-5.1 architecture IS a working multi-domain framework: 5 domains were evaluated with the same harness, the same scoring logic, and the same McNemar test. The framework-vs-plugin separation is clean.

**Qualifications:**
1. **The violation injectors (checker logic) are domain-specific, not a shared checker engine.** Each domain has custom `inject_*()` functions rather than a shared rule-registration system. For a "framework product," this would need to be generalized into a rule-registration API.

2. **The Pokemon symbolic checker (Ditto-5.3) is a separate codebase** with a different output format (CSV with 8-category taxonomy) vs Ditto-5.1's violation injection approach. Integrating them would require reconciling two independent architectures.

3. **Data acquisition is the bulk of domain-specific work** (~300 lines per domain for fetch/parse). For Mew as a commercial product, this data acquisition layer would need to be either customer-provided or built per customer engagement.

### Realistic engineering effort

To extract a "Mew checker framework" product:
- **Phase 1 (6–8 weeks):** Refactor Ditto-5.1 violation injectors into a shared rule-registration API. Add the Pokemon domain as a sixth cell. Standardize output format (verdict + violation_type + confidence).
- **Phase 2 (4–6 weeks per new domain):** Build domain plugin (data pipeline + constraint rules + event renderer) for first customer domain. This is the "template" that demonstrates the framework.
- **Phase 3 (ongoing):** Framework stabilization and documentation as each new domain tests it.

**Bottleneck:** Data acquisition and constraint rule specification are not automatable — they require domain expertise per engagement. This is the core of the service delivery model.

### Foundation for next steps

The G1 decomposition provides the input to the next empirical step: building a checker for one new domain using the framework, then measuring whether the OLAT lever findings (CoT elicitation, constraint text quality, chain format) generalize to that new domain. Poker, PUBG, and NBA are already available in Ditto-5.1 — these could serve as within-experiment validation of framework generalizability.
