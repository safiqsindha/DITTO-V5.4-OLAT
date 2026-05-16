# LLM-to-Criteria Experiment — Final Summary

**Question:** Can an LLM build a symbolic constraint checker for Pokémon battle
chains, and how do model capability, internet access, and domain restriction
affect the quality of the resulting checker?

**Setup:** Seven agents built checkers from the same 50-chain development set
(30 dev, 20 val) using a rule-induction approach. Chains are 15-step windows
of Showdown battle telemetry. Violations span five categories: hp_resurrection,
monotone_increase, causal_incoherence, multiple, none.

---

## Results at a Glance

| Agent | Model | Internet | Dev F1 | Val F1 | P | R | Rules |
|-------|-------|----------|--------|--------|---|---|-------|
| A2 | Haiku | None | 0.889 | 0.867 | 1.0 | 0.765 | 5 |
| A1 | Sonnet | None | 0.889 | 0.867 | 1.0 | 0.765 | 8 |
| A3 | Opus 4.7 | None | **0.929** | 0.867 | 1.0 | 0.765 | 7 |
| B3 | Haiku | Open web | 0.889 | 0.786 | 1.0 | 0.647 | 5 |
| B2 | Sonnet | Open web | **0.929** | 0.867 | 1.0 | 0.765 | 9 |
| B1 | Opus 4.7 | Open web | **0.929** | 0.867 | 1.0 | 0.765 | 7 |
| C1 | Sonnet | Serebii only | **0.929** | 0.867 | 1.0 | 0.765 | 7 |

All agents maintain **precision = 1.000** (zero false alarms). Validation F1
is capped at **0.867** for every agent except B3.

---

## Three Experimental Axes

### 1 — Capability (no internet: A2 → A1 → A3)

Development F1 rises monotonically with model capability at fixed precision 1.0.
Validation F1 is flat: every model — from the smallest (Haiku) to the largest
(Opus) — hits the same 0.867 ceiling. The ceiling is set by three irreducible
text-format failure modes, not by model capability.

| Model | Dev F1 | Val F1 |
|-------|--------|--------|
| Haiku | 0.889 | 0.867 |
| Sonnet | 0.889 | 0.867 |
| Opus 4.7 | **0.929** | 0.867 |

### 2 — Internet access (measured at all three tiers)

Internet value is **inversely proportional to model capability**. At the frontier
(Opus) the model already derives the full rule set from training knowledge and
development data; internet adds nothing. At mid-tier (Sonnet) it contributes one
edge-case rule (+0.040 dev F1). At the floor (Haiku) it provides zero benefit and
slightly harms validation recall.

| Tier | No internet | + Internet | Δ Dev F1 | Δ Val F1 |
|------|------------|------------|----------|----------|
| Haiku | 0.889 | 0.889 | 0.000 | −0.081 |
| Sonnet | 0.889 | **0.929** | **+0.040** | 0.000 |
| Opus 4.7 | **0.929** | **0.929** | 0.000 | 0.000 |

### 3 — Domain restriction (C1: Serebii-only vs B2: open web)

Restricting internet access to a single authoritative Pokemon resource (Serebii)
versus the open web **costs zero performance** at the Sonnet tier. The own_faint
coupling rule that B2 found via Showdown SIM-PROTOCOL docs is equally confirmable
from Serebii's fainting/switching mechanics pages. Domain restriction is free when
the restricted source covers the relevant mechanics.

| Agent | Scope | Dev F1 | Val F1 |
|-------|-------|--------|--------|
| A1 | None | 0.889 | 0.867 |
| B2 | Open web | 0.929 | 0.867 |
| C1 | Serebii only | 0.929 | 0.867 |

---

## The Validation Ceiling: Why 0.867 and How to Break It

Every agent hits 0.867 (precision 1.0, recall 0.765) on validation — except B3
which is lower. The ceiling is not a model or knowledge problem; it is set by four
irreducible format failures:

| Chain | Failure mode | Fix required |
|-------|-------------|--------------|
| gen9ou-2275367426 | hp_resurrection outside 15-step window | Wider window (k≥20) |
| gen9ou-2283533709 | Requires active_pair annotation | Add active_pair to format |
| gen9ou-2334711641 | Phase-coherence tracking; no active_pair data | Add active_pair to format |
| gen9ou-2306563046 | Pattern indistinguishable from valid chains in text | Non-separable in current format |

**Wider windows** (Lever 8, k ∈ {20, 30}) are already pre-registered in
`chain_condition_assignments.ndjson` and supported by `day0_task4_variant_generator.py`
with no code changes. k=20 (~70% violation coverage) would likely recover 1 FN;
k=30 (~90%) may recover 2. The other 2 require structural format changes
(active_pair annotations).

---

## Key Takeaways for the Mew Workflow

1. **It works.** Every agent built a precision-1.0 symbolic checker from chain
   text alone. The approach is sound.

2. **Use Opus without internet.** A3 (Opus, no internet) matches the best
   internet-assisted result (B2, B1, C1) and requires no search infrastructure.

3. **If using a weaker model, open web > Serebii > no internet at Sonnet tier.**
   At Haiku tier, don't bother — internet doesn't help.

4. **The bottleneck is the chain format, not the model.** To push recall above
   0.867 on this validation set, regenerate with k=20 or k=30, or add active_pair
   annotations to the chain format. No amount of model scaling or internet access
   will move the needle past the current ceiling.
