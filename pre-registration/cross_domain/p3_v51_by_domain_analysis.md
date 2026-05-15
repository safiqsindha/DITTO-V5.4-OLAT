# P3 — v5.1 By-Domain Re-Analysis

**Date:** 2026-05-15  
**Data source:** `https://github.com/safiqsindha/Ditto-5.1` (cloned locally)  
**Data file:** `RESULTS/v5_1/phase3_consolidated/per_cell_summary.csv` (110 rows: 22 models × 5 domains)

---

## Terminology Note

The Ditto-5.1 codebase uses **non-standard metric names** (confirmed by reading `scripts/consolidate_for_phase3.py`):

| Column name | What it actually measures | Standard name |
|---|---|---|
| `sensitivity` | P(model says NO \| violated chain) | False negative rate |
| `specificity` | P(model says YES \| clean chain) | False positive rate |
| `fp_rate` | P(model says NO \| clean chain) | True negative rate |

This document uses **standard epidemiological terms** throughout:
- **True detection rate** = 1 − `sensitivity` = P(model says YES \| violated chain)
- **False positive rate** = `specificity` = P(model says YES \| clean chain)
- **Detection gap** = true_detection_rate − false_positive_rate

---

## Experiment Context

Ditto-5.1 is a 22-model × 5-domain constraint detection experiment. For each domain, models are presented with:
- **Baseline chains:** intact game sequences, expected response NO (no violation)
- **Intervention chains:** chains with one planted constraint violation (domain-specific), expected response YES

Per-domain violations injected (from `src/harness/violation_injector.py`):
- **NBA:** actor with 7 fouls (over 6-foul ejection threshold) acts in a later event
- **PUBG:** eliminated player acts in a subsequent event
- **Poker:** folded player bets/raises in a subsequent event
- **CS:GO:** data ceiling — synthetic timestamp distribution prevents clean violation construction; violation injection may not be cleanly planted
- **Rocket League:** data ceiling — boost state tracking not available; violation injection may not be cleanly planted

This context matters for interpreting CSGO and RL detection results.

---

## Section 1: Per-Domain Summary

### Metrics table (22 models per domain)

| Domain | Med true_det | Med FPR | Med gap | NO-floor models | Good models (det>80%) | Neg-gap models | Failure mode |
|--------|-------------|---------|---------|-----------------|----------------------|----------------|--------------|
| CSGO | 0.051 | 0.074 | −0.004 | 13/22 | 0/22 | 2/22 | **NO-floor** |
| NBA | 0.144 | 0.155 | +0.012 | 9/22 | 0/22 | 4/22 | Mixed/partial |
| POKER | 0.154 | 0.168 | −0.007 | 10/22 | 0/22 | 6/22 | Mixed/partial |
| PUBG | 0.178 | 0.312 | −0.052 | 4/22 | 0/22 | 11/22 | **Mixed: NO-floor + anti-detection** |
| ROCKET LEAGUE | 0.148 | 0.217 | −0.006 | 8/22 | 0/22 | 7/22 | Mixed/partial |

**Panel-wide (22 models × 5 domains = 110 observations):**
- Mean true_det = 0.206, Mean FPR = 0.229, Mean gap = −0.023
- Median gap = −0.002
- Models with gap > +0.10: 11/110 (10.0%)
- Models with gap > +0.50: 0/110 (0.0%)
- Models with gap < −0.05: 30/110 (27.3%)
- **No model achieves >80% true detection in any domain**

---

### CS:GO (pure NO-floor)

**Median true_det = 0.051 | FPR = 0.074 | gap = −0.004**

13 of 22 models fall below 15% detection with <15% FPR — the clearest NO-floor pattern. Models almost universally say NO for both clean and violated CS:GO chains. The detection gap is essentially zero.

**Contextual note:** CS:GO violation injection was flagged as a "data ceiling" in the Ditto-5.1 codebase — synthetic timestamp distribution prevents clean intra-round violation construction. If the injected violations were weak or ambiguous, model failure to detect them may partly reflect violation quality rather than pure model failure. This ambiguity makes CSGO the least interpretable domain.

Best performing model: `qwen/qwen3.6-max-preview` (det=0.208, fpr=0.166, gap=+0.041) — marginal positive signal.

---

### NBA (mixed/partial, best performance domain)

**Median true_det = 0.144 | FPR = 0.155 | gap = +0.012**

9/22 models show near-zero detection (NO-floor-like). But the top 3 models show meaningful positive gaps:
- `gpt-5-mini`: det=0.470, fpr=0.276, gap=+0.194
- `claude-sonnet-4-6`: det=0.373, fpr=0.199, gap=+0.174  
- `gpt-5`: det=0.330, fpr=0.157, gap=+0.173

The NBA violation (actor with 7 fouls acting) is clearly specified in the constraint context and directly verifiable from chain event data. This explains why some models show non-trivial detection. The foul-count violation requires counting across events, which distinguishes models with better sequential reasoning.

4/22 models show negative gap (anti-detection). Worst: `z-ai/glm-5` (det=0.315, fpr=0.606, gap=−0.291).

---

### Poker (mixed/partial, near-zero median gap)

**Median true_det = 0.154 | FPR = 0.168 | gap = −0.007**

10/22 models near zero detection. The poker violation (folded player acts) maps cleanly to a single rule clause. Top performance:
- `gpt-5`: det=0.482, fpr=0.237, gap=+0.245 (strongest single-domain positive signal)
- `gemini-2.5-flash`: det=0.221, fpr=0.133, gap=+0.088

6/22 models show negative gap. Worst: `z-ai/glm-5` (det=0.353, fpr=0.488, gap=−0.136).

---

### PUBG (most anomalous — anti-detection dominant)

**Median true_det = 0.178 | FPR = 0.312 | gap = −0.052**

PUBG is qualitatively different from the other four domains. Only 4/22 models show the clean NO-floor pattern, but 11/22 models show *negative* detection gaps. Models are more likely to flag clean PUBG chains as violated than to correctly identify actual violations. This is anti-detection — the inverse of the NO-floor pattern.

Two extreme cases:
- `x-ai/grok-4-fast`: det=0.041, fpr=0.864, gap=−0.823 — almost never detects the violation BUT flags 86% of clean chains. Near-perfect inverse detection.
- `z-ai/glm-5`: det=0.438, fpr=0.969, gap=−0.531 — flags 97% of clean chains as violated.

The PUBG violation (eliminated player acts) requires the model to recognize an actor marked `eliminated_player=<name>` in event context who subsequently generates an action. The `violation_injector.py` notes this marker is "surfaced explicitly so the 6-key context cap doesn't drop it." The anti-detection pattern may indicate some models flag the `eliminated_player` marker as a violation signal even in CLEAN chains (which may include benign marker presence), creating systematic false positives.

Best PUBG model: `gpt-5` (det=0.566, fpr=0.154, gap=+0.412) — the strongest single-model positive gap in the entire dataset.

---

### Rocket League (mixed/partial)

**Median true_det = 0.148 | FPR = 0.217 | gap = −0.006**

Rocket League injection was also flagged as a "data ceiling" in the codebase. 8/22 models near NO-floor. Some meaningful detection:
- `gemini-2.5-flash`: det=0.499, fpr=0.213, gap=+0.286
- `gemini-3.1-flash-lite-preview`: det=0.493, fpr=0.367, gap=+0.125

7/22 negative gap models. Worst: `kimi-k2.6` (det=0.150, fpr=0.375, gap=−0.226).

---

## Section 2: Cross-Domain Comparison

### Failure mode by domain

| Domain | Primary failure mode | Secondary | Notes |
|--------|---------------------|-----------|-------|
| CSGO | NO-floor (13/22) | Near-zero signal | Violation injection quality uncertain (data ceiling) |
| NBA | NO-floor (9/22) | Some models show real detection | Best-characterized violation; clearest positive signal |
| Poker | NO-floor (10/22) | Some models show real detection | Clean single-clause violation |
| PUBG | Anti-detection (11/22) | NO-floor (4/22) | Marker artifact may cause systematic FPs |
| Rocket League | NO-floor (8/22) + mixed | Anti-detection (7/22) | Violation injection quality uncertain |

### Domain-general findings

1. **No domain shows working detection (no model achieves >80% true detection in any domain).** This is the most important cross-domain finding: the near-zero-detection panel-wide null is not domain-specific.

2. **The NO-floor mechanism is domain-general but not universal.** It appears in varying degrees across all five domains (modal failure mode in 4/5 domains), consistent with the OLAT "V1-minimal NO-floor" characterization.

3. **PUBG is qualitatively different.** The anti-detection pattern (FPR > true_det for 11/22 models) does not appear in other domains at the same rate. This appears to be an artifact of how the PUBG violation is rendered (explicit `eliminated_player` marker that models may flag unconditionally) rather than a different causal failure mode.

4. **Best absolute performance:** gpt-5 in PUBG (det=0.566, gap=+0.412) and gpt-5 in Poker (det=0.482, gap=+0.245). NBA and RL also show positive signals in top models. These are real but modest detections — far short of what would be needed for production use.

5. **Panel-wide null confirmed:** Mean gap = −0.023, median = −0.002. The null is robust across all domains and is not an artifact of any single domain dominating the aggregate.

---

## Section 3: Does the OLAT Failure Mode Framework Apply Cross-Domain?

### OLAT framework summary

The OLAT diagnostic identified "V1-minimal NO-floor" as the primary mechanism for the v5.1 panel-wide null: models presented with minimal instructions respond NO regardless of chain content. The OLAT experiment was designed to diagnose which pipeline levers (chain format, instructions, CoT elicitation, etc.) can break this floor.

### Cross-domain application

**Verdict: Partially supported, with one domain-specific anomaly.**

**Supported:** The NO-floor pattern is present across all five domains. In CSGO, NBA, Poker, and Rocket League, the dominant failure mode (NO-floor or mixed) is consistent with the OLAT framework's V1-minimal characterization. Models defaulting to NO across both baseline and intervention conditions is structurally identical in all these domains.

**Anomaly (PUBG):** The anti-detection pattern in PUBG (FPR > true_det for 11/22 models) is NOT explained by the NO-floor mechanism. It suggests a domain-specific confound: the explicit `eliminated_player` marker in PUBG's rendered chain may trigger unconditional YES responses from some models regardless of whether the marker is actually in the violation condition. This is a PUBG rendering artifact, not a general model failure mode.

**Implication:** The OLAT framework's "pipeline lever" approach is domain-general for the NO-floor component. Levers that help models break out of default-NO (better instructions, CoT, constraint text clarity) should generalize across domains. However, each domain may have domain-specific confounds (like PUBG's marker artifact) that require domain-specific attention.

---

## Section 4: Implications for the Larger Mew Project

### What P3 establishes

1. **Cross-domain null is real.** The near-zero detection finding from v5.1 is robust across all five domains tested. This is not domain-specific.

2. **OLAT's V1-minimal NO-floor mechanism is cross-domain.** Models defaulting to NO is the dominant failure pattern in 4/5 domains. This strengthens the OLAT framing as a domain-general diagnostic, not Pokemon-specific.

3. **Some models show positive signal in some domains.** gpt-5, gemini-2.5-flash, and certain others achieve meaningful detection gaps (>0.15) in specific domains. This shows the task is not fundamentally impossible — the framework can work when the violation is well-specified and the model has sufficient reasoning capability.

4. **Domain structure matters.** Cleanly specified, single-clause violations (Poker, PUBG) produce higher peak detection than structurally ambiguous domains (CSGO, RL). This supports the constraint chain + explicit violation specification approach that the Mew framework builds on.

### Implications for Mew methodology claim

If the Mew framing is "the same constraint-chain + symbolic checker methodology generalizes across domains," the P3 data is **partially supportive**:
- The failure mode (NO-floor) IS domain-general, confirming the diagnostic methodology applies cross-domain
- But successful detection is sparse and domain-specific, not yet showing general methodological success
- The path to cross-domain success is the same as the OLAT diagnostic path: identify and fix the pipeline levers that break the NO-floor, domain by domain

**Specific evidence statement:** "v5.1 multi-domain results confirm the V1-minimal NO-floor failure mode is domain-general across Poker, PUBG, NBA, CS:GO, and Rocket League (panel-wide median detection gap = −0.002). This supports applying the OLAT diagnostic methodology cross-domain. However, working detection remains sparse and below production thresholds in all five domains tested."

---

## Methodology Notes and Caveats

1. **Variable name inversion.** The Ditto-5.1 codebase uses `sensitivity` and `specificity` in inverted senses relative to epidemiological convention. All analyses here use the standard definitions (documented above).

2. **CSGO and RL violation injection quality.** Both domains are noted as "data ceiling" cases in the violation injector code. If injected violations are weak, some measured "failures to detect" may reflect genuine non-violating chains rather than model failure. Results for these two domains should be interpreted with more caution than NBA/Poker/PUBG.

3. **PUBG anti-detection likely confounded.** The `eliminated_player` marker may be present in clean chains in ways that trigger false positives. This domain-specific rendering artifact makes PUBG's failure mode classification less reliable.

4. **Missing the specific "v5.1 panel-wide null" Pokemon result.** The OLAT handoff characterizes v5.1 as "Pokemon Showdown constraint detection." This Ditto-5.1 repository contains a multi-domain experiment, not a Pokemon experiment. The numeric characterization in the handoff (gap = −0.067 log-odds, p=0.22) may refer to either an earlier Pokemon-only run or the same data analyzed via McNemar log-odds rather than the raw probability gap used here. The panel-wide null finding is consistent in direction (near-zero or negative gap) across both characterizations.
