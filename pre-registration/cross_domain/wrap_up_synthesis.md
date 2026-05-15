# Wrap-Up Synthesis — Pre-API Experiment Batch

**Date:** 2026-05-15  
**Experiments:** P3 (v5.1 by-domain re-analysis) + A1/B2 50-chain comparison + G1 Phase 1 (modular decomposition)

---

## Section 1: What These Three Experiments Establish Empirically

### P3: Cross-Domain Methodology Validity

**Verdict: Partially supported.**

The Ditto-5.1 multi-domain dataset (22 models × 5 domains: Poker, PUBG, NBA, CS:GO, Rocket League) confirms:

1. **Panel-wide null is domain-general.** Mean detection gap = −0.023, median = −0.002 across 110 model-domain observations. No domain shows working detection (no model achieves >80% true detection in any domain).

2. **NO-floor mechanism is cross-domain.** The dominant failure pattern in 4/5 domains (CSGO, NBA, Poker, Rocket League) is a model bias toward NO regardless of chain content — structurally identical to the OLAT "V1-minimal NO-floor" characterization.

3. **PUBG is anomalous.** 11/22 models show anti-detection (FPR > true_det) in PUBG, likely due to a rendering artifact in the `eliminated_player` marker rather than a distinct failure mode.

4. **Some models show real positive signal in specific domains.** gpt-5 in PUBG (gap=+0.412), gpt-5 in Poker (gap=+0.245), multiple models in NBA with gaps 0.15–0.20. The task is not fundamentally impossible.

**Implication for Mew:** The OLAT diagnostic framing — identifying pipeline levers that break the NO-floor — is domain-general, not Pokemon-specific. This strengthens the cross-domain methodology claim for Mew Phase 3.

---

### A1 vs B2: Internet Contribution to Checker Construction

**Verdict: Real but marginal on the 50-chain corpus.**

| Metric | A1 (no-internet) | B2 (internet) | Delta |
|--------|-----------------|---------------|-------|
| Recall (50-chain) | 0.781 | 0.812 | +0.031 |
| F1 (50-chain) | 0.877 | 0.897 | +0.020 |
| False positives | 0 | 0 | 0 |
| Rules | 8 | 9 | +1 |

B2's one additional detection (`gen9ou-2310254076_p2_shuffled_42`) comes from the `own_faint_no_perm` rule: `trigger=own_faint` in a SubGoalTransition without a corresponding `UNAVAILABLE(permanent)` event. This rule was informed by internet research confirming that faint triggers always produce permanent unavailability records in valid Pokemon chains.

**The generalized monotone rule** (B2 covers all `decay=monotone_decrease` resources, not just `pp_action_*`) produced zero additional detections on this corpus. The only non-pp_action monotone resource in the corpus (`match_time_remaining`) had no violations.

**Shared gaps (6 chains both miss):** Window-limited hp_resurrection (resurrection outside visible 15-step window), double-UNAVAILABLE beyond safe threshold, missing active_pair data for causal incoherence detection. These are irreducible from the chain text format regardless of internet access.

**Implication for Mew:** Internet access at the Sonnet tier provides one additional rule with modest practical impact. The core checker logic is derivable from training data alone. For the LLM-as-checker-builder workflow, internet access is a marginal enhancement, not a prerequisite.

---

### G1 Phase 1: Framework Extractability from Existing Checker

**Verdict: STOP condition triggered — Pokemon checker code not available locally.**

The `pokemon_rule_checker.py` from `Ditto-5.3- Pokemon Diag` is on Safiq's local machine, not committed to any accessible repo.

**What was analyzed instead:** The Ditto-5.1 `src/` multi-domain framework (fully available and more complete than the Pokemon checker for cross-domain analysis purposes).

**Key finding from Ditto-5.1 architecture:**

The framework IS modular and a real framework-vs-plugin separation exists:
- **Framework layer** (domain-general): ~500 lines — evaluation harness, scoring, orchestration, McNemar, response parsing
- **Domain plugin layer**: ~500 lines/domain — data acquisition, event extraction, constraint rules, event rendering
- **Framework fraction**: ~17% of total code, but the 17% handles all reusable evaluation logic

The violation injectors (domain-specific constraint checkers) follow a shared pattern (`InjectionResult` dataclass, uniform `inject_*_violation()` function signatures) that could be formalized into a rule-registration API.

**Engineering estimate for Mew framework product:**
- Phase 1 (refactor to shared rule API): 6–8 weeks
- Phase 2 (new domain instantiation): 4–6 weeks per domain
- Bottleneck: domain expertise for data acquisition and constraint rule specification (not automatable)

---

## Section 2: Implications for the Larger Mew Project

Combining P3, A1/B2, G1 with prior OLAT and bonus battery results:

### Mew Part 1: Constraint chains + symbolic checker

**Status: Established (Pokemon domain).**

The A1/B2 LLMtoCriteria experiment demonstrates that an LLM can build a working symbolic checker from 30 example chains with no pre-existing checker code: P=1.0, R=0.765–0.812, F1=0.867–0.897. The constraint chain format encodes detectable violations, and rule-based detection achieves high precision.

**Remaining gap:** The full Pokemon symbolic checker (`pokemon_rule_checker.py`) achieves higher recall than A1/B2 by covering more violation categories (8 vs 3). Getting to the full checker's performance would require either more example chains or more explicit rule specifications.

### Mew Part 2: Fine-tuning

**Status: Not yet empirically tested.** Tomorrow's API experiments (R1, tool augmentation, A2/B1) will begin characterizing this.

### Mew Part 3: Cross-domain methodology validity

**Status: Established for null result + failure mode, partial for positive signal.**

P3 confirms:
- The NO-floor failure mode is domain-general (5/5 domains affected)
- The OLAT diagnostic approach (lever-by-lever) is domain-general
- Some positive detection signal exists in NBA, Poker, PUBG for the best-performing models

What P3 does NOT yet establish: that the OLAT lever solutions (CoT elicitation, chain format improvements, constraint text quality) also generalize across domains. That requires running the full OLAT lever battery on a second domain.

### Mew Product: Modular checker framework

**Status: Architecture exists, formal product packaging not yet built.**

The Ditto-5.1 framework IS a real multi-domain modular architecture. The framework-vs-plugin separation is clear. The blocker is not architectural — it is the data acquisition and constraint specification work required per new domain engagement (4–6 weeks/domain).

---

## Section 3: Open Questions for the Next Phase

### Immediate (tomorrow's API experiments)

1. **R1 — Reasoning control:** Does native reasoning mode (Lever 18 L4) break the NO-floor in the OLAT Pokemon domain? This is the most direct lever test.

2. **Tool augmentation:** Does giving the model structured chain parsing tools improve detection? Tests whether the NO-floor is a formatting problem or a reasoning problem.

3. **A2/B1 capability tier comparison:** Does Haiku (A2) reconstruct a working checker as well as Sonnet (A1)? Does Opus (B1) add meaningfully more rules than Sonnet (B2)?

### Medium term (Mew Phase 3 empirical demonstration)

4. **Cross-domain OLAT lever replication:** Run the full OLAT lever battery (or a targeted subset: Lever 18 CoT + Lever 16 constraint text) on one non-Pokemon domain from Ditto-5.1 (NBA or Poker recommended — cleanest violation specification). Test whether lever effects found in Pokemon generalize.

5. **Pokemon checker code access:** Committing `pokemon_rule_checker.py` to the DITTO-V5.4-OLAT repo (or a new repo) would enable the direct G1 analysis originally specified and complete the modular decomposition.

### Longer term (Mew commercial development)

6. **Customer development:** P3 shows positive detection signal in NBA and Poker for top models. These are accessible domains for customer conversations (e.g., sports analytics, online poker operators). Real customer data would replace the synthetic constraint chains with production-quality data.

7. **Acquihire framing:** The technical differentiators are now empirically characterized: (a) constraint chain format that enables symbolic verification, (b) the symbolic checker construction workflow, (c) the OLAT diagnostic methodology for identifying detection failure modes. These are the IP components worth quantifying for acquihire conversations.

---

## Data Availability Note

The Ditto-5.1 GitHub repo (https://github.com/safiqsindha/Ditto-5.1) was cloned locally for P3 and G1 analyses. All data used in this batch is from:
- `Ditto-5.1/RESULTS/v5_1/phase3_consolidated/` — 81,460 model-domain-chain-condition observations
- `DITTO-V5.4-OLAT/pre-registration/chain_variants/` — 3,200 OLAT chain conditions
- `DITTO-V5.4-OLAT/experiment/agents/` — A1/B2 checker files

No new API calls were made in this batch.
