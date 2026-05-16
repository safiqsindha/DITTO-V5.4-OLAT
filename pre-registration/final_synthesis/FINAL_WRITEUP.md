# Project Ditto OLAT — Final Write-Up

**Symbolic-Augmented LLM Detection of Constraint Violations in Structured Game Logs**

**Date:** 2026-05-15
**SPEC hash (Amendment #6, locked):** `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8`
**Status:** Final draft. All experiments complete. B1.7 (prompt robustness) finished but is inconclusive as designed (§4.5) — it does not bear on the central augmentation result.

---

## Abstract

We ask whether a large language model can reliably detect rule violations in
structured Pokemon battle logs ("chains"), and what a deterministic symbolic
constraint checker contributes to that task. Across 3,200 pre-registered
evaluations spanning 22 pipeline levers, the best standalone prompting
configuration (chain-of-thought reasoning, `pro_L18_L3`) reaches a
detection gap of only 0.354 — far short of deployable. Injecting a symbolic
checker's verdict into the prompt raises the gap to **0.9375** (94% recall,
~100% specificity at 50-chain scale). However, an adversarial inversion
experiment shows the model **rubber-stamps false violation verdicts 100% of
the time** on genuinely intact chains, while overriding false "no violation"
verdicts only 50% of the time on genuinely violated chains. The augmented
system is therefore only as trustworthy as its checker's precision, which is
99.90% on this corpus. Self-consistency sampling does not substitute for the
checker (it trades recall for specificity at zero net gain), a PUBG-domain
detection artifact does not reproduce and does not contaminate the OLAT
corpus, and seven independent agents that built checkers from scratch all hit
an identical held-out F1 ceiling of 0.867 — a property of the chain format,
not of model capability. We conclude with **Mew**, a confidence-gated hybrid
architecture, and the empirical constraints that shape it.

---

## 1. Motivation

Constraint-violation detection in structured logs is a recurring need:
anti-cheat, audit, simulation validation, agent-trajectory checking. The naive
hypothesis is that a sufficiently capable LLM, given the log and the rules,
will simply find the violations. Project Ditto OLAT ("One-Lever-At-a-Time")
was designed to test that hypothesis rigorously and, when it fails, to
characterize *what* makes detection work — so that an architecture can be
built around the working mechanism rather than around hope.

The substrate is Pokemon Showdown battle chains. A chain is a serialized
sequence of battle events; a *violated* chain contains at least one event that
breaks a deterministic rule (HP resurrection from 0, PP increasing,
tool-availability after permanent unavailability, causally incoherent subgoal
transitions). The detection task is binary: does this chain contain a
violation, YES or NO.

---

## 2. Methods (summary)

All conditions, thresholds, and outcome taxonomies were pre-registered before
data collection; the locked SPEC hash appears in the header. Methodological
detail lives in the pre-registration tree (`pre-registration/`); this section
states only what is needed to read the results.

- **Models:** DeepSeek V4-Flash / V4-Pro for the primary lever screen and the
  Part B detection experiments; Claude Haiku / Sonnet / Opus 4.7 for the
  agentic checker-construction experiments.
- **Lever system:** 22 levers toggled one at a time. Lever 18 controls
  reasoning regime (L3 = textual chain-of-thought, L4 = native thinking mode);
  Lever 17 controls structured JSON output. Other levers cover field schema,
  rendering, and auxiliary information.
- **Symbolic checker:** a deterministic rule evaluator. On this corpus:
  accuracy 91.39%, **precision 99.90%**, recall 88.61%. Verdicts are
  pre-computed in `checker_verdicts.csv`.
- **Primary metric:** the *detection gap* = P(YES | violated) − P(YES | intact)
  = recall − (1 − specificity). Gap = 1.0 is perfect; gap = 0.0 is no
  discrimination.
- **Parsing:** a four-stage cascade (strict → permissive → markdown-strip →
  last-token). Unparseable responses are recorded as such and excluded from
  rate computations but retained as data.

---

## 3. The baseline problem

The lever screen (3,200 evaluations, 62 non-baseline conditions) establishes
the ceiling of prompt engineering alone.

| Condition | Gap | 95% CI | Class |
|---|---|---|---|
| pro_L18_L3 | 0.354 | [0.026, 0.685] | Meaningful |
| pro_L18_L2 | 0.379 | [0.036, 0.745] | Meaningful (L3-only) |
| pro_L17_L2 | 0.288 | [0.051, 0.486] | Meaningful |
| pro_L12_L3 | 0.191 | [0.017, 0.438] | Meaningful |

Only 6 of 62 conditions are Meaningful and 7 Directional; the remaining 49 are
null. **Reasoning regime (Lever 18) is the dominant lever** — no amount of
field-schema richness, rendering format, or auxiliary information substitutes
for reasoning overhead. Detection capacity is regime-gated.

Worse, the strongest reasoning regime is unusable alone. Native thinking mode
(`L18 L4`, max_tokens 4096, Amendment #7 retest) is **YES-biased**: 70% YES,
0% NO, 30% parse failure, dr_violated = dr_intact = 1.0, **gap ≈ 0.0**. It
calls everything a violation. Prompting alone hits a hard ceiling around
gap = 0.35 and collapses entirely under native thinking.

---

## 4. Results

### 4.1 Tool augmentation breaks the ceiling (B1 Phase A)

Injecting the symbolic checker's verdict into the `L18 L4` prompt, 50 chains:

| Group | N | Detection rate |
|---|---|---|
| Violated | 32 | **0.9375** |
| Intact | 18 | **0.000** |

**Gap = 0.9375.** This satisfies pre-registered Outcome 1 (gap > 0.40,
dr_intact < 0.30, dr_violated ≥ 0.70) with large margin. The YES-bias of
standalone `L18 L4` is broken: parse failure falls from 30% to ~4%. Relative
to the no-augmentation baseline (§4.3, T=0): recall 0.60 → 0.94, specificity
0.40 → ~1.0 — both improve **simultaneously**. This is the central positive
result: checker + LLM solves the detection problem at this scale where neither
component alone does.

### 4.2 The model defers to the checker asymmetrically (B1 Phase B)

To distinguish genuine integration from rubber-stamping, we flipped checker
verdicts on 20 chains (17 parseable).

| Manipulation | N | Deferred to fake verdict | Overrode |
|---|---|---|---|
| Intact chain + fake "VIOLATION" | 7 | **7 (100%)** | 0 |
| Violated chain + fake "no violation" | 10 | 5 (50%) | 5 (50%) |

Overall rubber-stamp rate 70.6% (pre-registered Outcome A). The behavior is
**hybrid**: the model is fully susceptible to false-positive injection
(100% deference when told an intact chain is violated) but retains partial
independent judgment against false negatives (50% override when told a
violated chain is clean). The pre-registered decision tree predicted that
genuine integration and rubber-stamping are observationally indistinguishable
without this adversarial arm; Phase B resolves the ambiguity.

**Consequence:** the augmented system inherits the checker's false-positive
rate without filtering it. A checker with 10% FPR would inject systematic
false positives the LLM would not catch. The 99.90% checker precision on this
corpus is the *enabling condition* for the §4.1 result, not an incidental
property.

### 4.3 Self-consistency is not a substitute (B1.5)

Without augmentation, 20 chains, T=0 single sample vs T=0.7 × 5 majority vote:

| Metric | T=0 | T=0.7 majority | Δ |
|---|---|---|---|
| Recall | 0.60 | 0.70 | +0.10 |
| Specificity | 0.40 | 0.30 | −0.10 |

Recall gain 0.100 — pre-registered "Intermediate" (does not clear the strict
> 0.10 Outcome-1 threshold). Specificity *decreases*: temperature sampling
manufactures additional false positives. Net discrimination improvement: zero.
Sampling trades one error for the other; the symbolic checker improves both at
once (§4.1). This is the negative control that isolates the checker's
contribution.

### 4.4 PUBG anti-detection does not reproduce; cross-domain is clean (B2)

The prior P3 finding — a `NOTE=Player_X_already_eliminated` marker driving
false positives, FPR > TPR — was retested on 20 PUBG chain pairs across 4
marker conditions (original, strip, move, rename).

| Condition | FPR | TPR | Gap |
|---|---|---|---|
| original | 0.0 | 0.2 | 0.2 |
| strip_marker | 0.0 | 0.2 | 0.2 |
| move_marker | 0.0 | 0.1 | 0.1 |
| rename_marker | 0.0 | 0.1 | 0.1 |

Pre-registered Outcome 3: **anti-detection does not reproduce** (FPR = 0.0
throughout; the model never falsely flags clean PUBG chains). Non-reproduction
does not invalidate P3 — chain selection, prompt construction, or model
version could explain divergence — but it removes P3 as a threat. Critically,
the PUBG marker appears in **0 / 50 OLAT chains**: the artifact is
domain-isolated and does not contaminate the Pokemon results.

### 4.5 Prompt robustness (B1.7) — inconclusive as designed

B1.7 ran 20 chains × 4 prompt variants × 2 regimes (160 calls; 0 API
timeouts). It tests prompt variants **on the bare model — there is no checker
augmentation in this experiment.** The dominant outcome is parse failure:
**119/160 (74%) responses were unparseable**, leaving per-cell parseable N too
sparse to compute a detection gap for 5 of 8 variant×regime cells.

| Regime | Variant | N(parse) | dr_intact | dr_violated | gap |
|---|---|---|---|---|---|
| v1_minimal | V0 | 2 | 1.0 | — | — |
| v1_minimal | V1 | 2 | 1.0 | — | — |
| v1_minimal | V2 | 15 | 1.0 | 1.0 | **0.0** |
| v1_minimal | V3 | 1 | 0.0 | — | — |
| l18_l4 | V0 | 5 | — | 1.0 | — |
| l18_l4 | V1 | 7 | 1.0 | 1.0 | **0.0** |
| l18_l4 | V2 | 3 | — | 1.0 | — |
| l18_l4 | V3 | 10 | 0.75 | 1.0 | **0.25** |

The pre-registered comparisons (surface: V0 vs V1 vs V3; semantic: V0 vs V2)
both require V0's gap, which is uncomputable in **both** regimes — so neither
comparison can be made. The analysis script's mechanical "Fragile" label
(gap range 0.25) is derived from l18_l4 V1 vs V3 at N ≤ 10 and is not a
statistically meaningful verdict. Of the three computable cells, two show
gap = 0.0 — the bare model assigns "violation" at equal rates to intact and
violated chains, the same YES-bias pathology documented in §3 for unaugmented
`L18 L4`, now seen to persist across prompt framings.

**Conclusion:** B1.7 does not measure prompt-robustness of the augmentation
effect (it never augmented). It returns a null/inconclusive result at these
token settings and incidentally corroborates §3 — prompt variation does not
rescue the unaugmented model. The central augmentation claim (§4.1) is a
separate experiment and does not depend on B1.7. Whether augmentation is
prompt-robust remains an **open validation gap** (§7.1), not a confirmed
property.

### 4.6 Agentic checker construction hits a format-bound ceiling (B3 + LLM-to-Criteria)

Two complementary experiments asked whether an agent can *build* the checker
rather than be handed it.

**B3 (R1 research agent):** Claude Sonnet, 30 simulated web searches, run at
**two turn budgets** (20 and 45). The agent independently rediscovered the
HP-resurrection and PP-monotone rules but in **neither run** called
`finalize_checker`: 20-turn run reached dev F1 = 0.865 (P = 0.941, R = 0.80);
the 45-turn re-run reached a *higher* dev F1 = 0.884 (P = 0.826, R = 0.95) by
recovering recall late, then kept perturbing rules until the cap. Pre-registered
outcome at both budgets: **Unknown — no finalized checker.** The decisive
result is that **2.25× the turn budget did not change the outcome class** —
the binding constraint is not the budget or the violation pattern (given more
turns the agent did crack recall) but a **behavioral reluctance to commit**:
the agent treats finalization as never-yet-optimal and iterates indefinitely.
Prior 20-turn outputs preserved at
`experiment/agents/R1_sonnet_research_maxturns20_backup_20260516/`.

**LLM-to-Criteria (PR #9, merged):** seven agents built checkers from the same
50-chain dataset under varied model size and internet access. All achieved
**precision = 1.0** (zero false alarms).

> **Naming note:** these agent IDs (A1–A3, B1–B3, C1) are internal to the
> LLM-to-Criteria experiment and are **distinct** from the Part B experiment
> IDs (B1 tool augmentation, B2 PUBG, B3 R1 agent).

| Agent | Model | Internet | Dev F1 | Val F1 |
|---|---|---|---|---|
| A2 | Haiku | None | 0.889 | 0.867 |
| A1 | Sonnet | None | 0.889 | 0.867 |
| A3 | Opus 4.7 | None | **0.929** | 0.867 |
| B3 | Haiku | Open web | 0.889 | 0.786 |
| B2 | Sonnet | Open web | **0.929** | 0.867 |
| B1 | Opus 4.7 | Open web | **0.929** | 0.867 |
| C1 | Sonnet | Serebii only | **0.929** | 0.867 |

Three findings: (1) **Capability** — dev F1 rises with model size but val F1 is
**flat at 0.867 for every model**; the ceiling is the chain format, not the
model. (2) **Internet** — helps Sonnet (+0.040 dev F1), is redundant at Opus
(already derives every rule), no help at Haiku. (3) **Domain restriction** —
Serebii-only equals open web; zero cost from restricting to one authoritative
source. To break 0.867: use k = 20 or k = 30 chains (pre-registered, no code
change) or add `active_pair` annotations to the chain format.

The synthesis across §4.6: a pre-built checker handed to the LLM (gap = 0.9375,
§4.1) dramatically outperforms agentic self-discovery at realistic budgets
(val F1 ≤ 0.867, or unfinalized).

---

## 5. The Mew architecture

The empirical record constrains the design space tightly enough to specify an
architecture rather than speculate one.

```
Chain input
   │
   ▼
Symbolic constraint checker     ← precision ≥ 0.99 is load-bearing (§4.2)
   │
   ▼
Confidence ≥ τ ?
   ├── yes → inject verdict + reasoning into L18 L4 prompt
   │          model defers, gap ≈ 0.94 (§4.1)
   │          residual risk: false-positive rubber-stamp, bounded by checker precision
   └── no  → L18 L3 CoT, no augmentation
              gap ≈ 0.35 (§3), lower ceiling but no deference risk
   │
   ▼
YES / NO + explanation
```

**Empirical constraints baked into the design:**

1. **Checker precision must be near-perfect.** §4.2: 100% rubber-stamp of
   false violations. Mew's quality is upper-bounded by, and directly
   controllable through, checker precision — which is deterministic and
   auditable. This is presented as a feature: quality is a knob, not a hope.
2. **Reasoning regime must be L18.** Non-reasoning and unaugmented native
   thinking both yield gap ≈ 0 (§3).
3. **No sampling shortcut.** Self-consistency yields zero net discrimination
   gain (§4.3); it cannot replace the checker.
4. **Confidence gating is necessary, not optional.** Because deference is
   asymmetric and total on false positives, low-confidence checker outputs
   must fall back to unaugmented reasoning rather than be injected.

**Competitive positioning:**

| Approach | Performance | Verdict |
|---|---|---|
| Pure LLM (best CoT) | gap 0.354 | Not deployable |
| Pure symbolic checker | P 99.90%, R 88.61% | Near-deployable, brittle recall |
| **Mew (checker + gated LLM)** | **R 93.75%, spec ~100%** | **Deployable (moderated-precision)** |

---

## 6. Limitations and threats to validity

- **Scale.** §4.1–4.3 are 20–50-chain experiments. The gap = 0.9375 result is
  strong but small-sample; CI width is not yet characterized at this scale.
- **Prompt-robustness untested.** B1.7 (§4.5) completed but is inconclusive:
  74% parse failure left V0's gap uncomputable, so neither pre-registered
  comparison could be made, and the experiment never augmented. Robustness of
  the augmentation effect is an open validation gap, not a confirmed property.
- **B3 unfinalized.** The agentic baseline lacks a held-out comparison; only
  dev F1 is available, so the agent-vs-augmentation tradeoff is bounded, not
  measured.
- **Single corpus / single domain for the core result.** Checker precision of
  99.90% is corpus-specific; out-of-distribution and new-domain behavior is
  untested (open question §7.2).
- **Model-version sensitivity.** The PUBG non-reproduction (§4.4) is itself
  evidence that findings can be version- or selection-sensitive.
- **Process gate.** L18 L4 / Amendment #7 results require both-author sign-off
  before formal external citation; this is a process, not a data, dependency.

---

## 7. Open questions

1. **Prompt-robustness of augmentation** — B1.7 was inconclusive (tested the
   bare model, 74% parse failure). A redesign with a forced YES/NO trigger (or
   higher l18_l4 max_tokens) *and the checker injected* is needed to actually
   answer whether augmentation persists across V0/V1/V3 and V0/V2.
2. **Checker scaling** — performance on OOD chains, new domains, edge cases.
3. **Confidence-gated injection** — calibrating τ to suppress rubber-stamping
   on checker false positives requires a calibration set.
4. **Rubber-stamp mitigation** — can a "critically evaluate the checker's
   claim" instruction shift the 100% false-positive deference without
   degrading normal augmentation?
5. **Agent-vs-augmentation crossover** — at what compute budget does
   agent-built checking match pre-built checker + LLM? (B3 + LLM-to-Criteria
   bound this but do not locate the crossover.)
6. **Breaking the 0.867 ceiling** — k = 20/30 chains or `active_pair`
   annotations; pre-registered, no code change.
7. **B3 forced commitment** — re-running at a higher budget was tested
   (max_turns = 45, 2026-05-16) and did *not* help: the agent still never
   finalized. The remaining open need is a script-level forced-commitment
   mechanism (auto-finalize the best-scoring checker at budget exhaustion) to
   obtain a clean val-set comparison; a larger budget alone is not the answer.

---

## 8. Conclusion

Prompting alone cannot reliably detect constraint violations in structured
game logs (gap ≤ 0.35; native thinking collapses to gap ≈ 0). A deterministic
symbolic checker injected into the prompt solves the task (gap = 0.9375) by
contributing precision *and* recall simultaneously where sampling contributes
neither. The price is total deference to the checker on false positives, which
makes checker precision the single load-bearing parameter — and, because that
precision is deterministic and auditable, makes system quality a controllable
knob rather than an emergent hope. Independent agents building checkers from
scratch converge on an identical format-bound ceiling well below the augmented
system. The recommended architecture, Mew, is a confidence-gated hybrid that
injects high-confidence checker verdicts and falls back to unaugmented
reasoning otherwise. One secondary experiment (prompt robustness) returned
inconclusive and leaves the robustness of the augmentation effect an open
validation gap; it does not bear on the central result.

---

*Artifact index, per-experiment raw data, and the working synthesis are in
`pre-registration/final_synthesis/wrap_up.md` and the `pre-registration/`
subtree.*
