# Task 2B — Tool Augmentation Prompt Templates

**Generated:** 2026-05-14
**Status:** Design only. Do NOT run API experiments without both-author authorization.
**Purpose:** Three candidate prompt templates for the future tool augmentation experiment.
  Each template has a hypothesis, success/failure criteria, and example instantiations.

---

## Example Chains (used in instantiations below)

**Intact chain** (`gen9ou-2262855067_p1`, violation_type=none, GT all False):
```
Step 1 (turn=0):
  ToolAvailability: unit_A is now AVAILABLE
Step 2 (turn=0):
  SubGoalTransition: phase shifted from 'initial' to 'vs_unit_A' (trigger=opponent_switch)
Step 3 (turn=0):
  InformationState: added=[unit_A] removed=[none] uncertainty=0.50
Step 4 (turn=0):
  OptimizationCriterion: objective=weather_raindance weight_shift=weather_A
Step 5 (turn=1):
  ResourceBudget: pp_action_1_opp at 93.8% (decay=monotone_decrease)
Step 6 (turn=1):
  ResourceBudget: hp_unit_A at 50.0%
Step 7 (turn=1):
  ResourceBudget: pp_action_1_own at 93.8% (decay=monotone_decrease)
Step 8 (turn=1):
  CoordinationDependency: field_side_p2 depends on hazard_move:stickyweb -> expected_action=hazard_response
Step 9 (turn=1):
  OptimizationCriterion: objective=weather_raindance weight_shift=weather_A
Step 10 (turn=2):
  ToolAvailability: unit_A is now UNAVAILABLE (recover_in=0)
Step 11 (turn=2):
  ToolAvailability: unit_B is now AVAILABLE
Step 12 (turn=2):
  ResourceBudget: pp_action_1_opp at 87.5% (decay=monotone_decrease)
Step 13 (turn=2):
  ResourceBudget: hp_unit_B at 100.0%
Step 14 (turn=2):
  OptimizationCriterion: objective=weather_raindance weight_shift=weather_A
Step 15 (turn=3):
  ToolAvailability: unit_A is now UNAVAILABLE (recover_in=0)
```
Checker verdict text (intact):
```
VERDICT: NO VIOLATION
Rule checked: All resource budgets, tool availability transitions,
subgoal transitions, and coordination dependencies were self-consistent.
No monotone-decrease violations, HP-resurrection events, causal
incoherence, or conflicting state transitions detected.
```

**Violated chain** (`gen9ou-2260297169_p2_shuffled_1337`, violation_type=hp_resurrection, GT all True):
```
Step 1 (turn=0):
  ResourceBudget: hp_unit_B at 100.0%
Step 2 (turn=0):
  ResourceBudget: hp_unit_B at 100.0%
Step 3 (turn=0):
  SubGoalTransition: phase shifted from 'initial' to 'forced_switch_required' (trigger=own_faint)
Step 4 (turn=1):
  ResourceBudget: pp_action_2_opp at 93.8% (decay=monotone_decrease)
Step 5 (turn=1):
  CoordinationDependency: field_side_p2 depends on hazard_move:stealthrock -> expected_action=hazard_response
Step 6 (turn=1):
  ResourceBudget: hp_unit_A at 25.0%
Step 7 (turn=1):
  ResourceBudget: pp_action_1_opp at 81.2% (decay=monotone_decrease)
Step 8 (turn=1):
  ResourceBudget: hp_unit_A at 0.0%
Step 9 (turn=2):
  ResourceBudget: match_time_remaining at 91.7% (decay=monotone_decrease)
Step 10 (turn=2):
  ResourceBudget: hp_unit_A at 100.0%
Step 11 (turn=2):
  InformationState: added=[unit_A] removed=[none] uncertainty=0.50
Step 12 (turn=2):
  CoordinationDependency: field_side_p1 depends on hazard_type_B -> expected_action=hazard_response
Step 13 (turn=2):
  ResourceBudget: pp_action_1_own at 93.8% (decay=monotone_decrease)
Step 14 (turn=2):
  SubGoalTransition: phase shifted from 'initial' to 'vs_unit_A' (trigger=opponent_switch)
Step 15 (turn=2):
  ToolAvailability: unit_B is now UNAVAILABLE (recover_in=0)
```
Checker verdict text (violated, hp_resurrection):
```
VERDICT: VIOLATION DETECTED — HP RESURRECTION
Rule violated: ResourceBudget monotone constraint for HP.
A unit's HP dropped to 0% (faint) and later appeared at a higher
value (> 0%) without an intervening revival action. HP cannot increase
after reaching 0% under standard battle rules.
```

---

## Template A — Minimal Verdict Injection

### Template structure

```
[chain rendered per OLAT baseline]

A symbolic constraint checker analyzed this chain. The checker reports:
[checker_verdict_text]

Does this battle chain contain any rule violations? The answer is YES or NO.
```

### Hypothesis

The model defers to the checker verdict. Providing a plain verdict (YES/NO + rule category)
is sufficient for the model to output the correct answer. The model functions as a
thin wrapper around the checker output.

### Success pattern
- dr_intact drops from ~1.0 to < 0.30 (model correctly says NO on intact chains
  because checker says NO)
- dr_violated stays ≥ 0.70 (model correctly says YES on violated chains because
  checker says YES)
- Gap > 0.40; effect size substantial

### Failure pattern
- dr_intact stays near 1.0 (model ignores checker NO verdict and hallucinates violations)
- dr_violated drops (model second-guesses checker YES verdict)
- Both degrade (checker output causes confusion)

### Example instantiation — intact chain

```
Step 1 (turn=0):
  ToolAvailability: unit_A is now AVAILABLE
Step 2 (turn=0):
  SubGoalTransition: phase shifted from 'initial' to 'vs_unit_A' (trigger=opponent_switch)
[... full chain as above ...]
Step 15 (turn=3):
  ToolAvailability: unit_A is now UNAVAILABLE (recover_in=0)

A symbolic constraint checker analyzed this chain. The checker reports:
VERDICT: NO VIOLATION
Rule checked: All resource budgets, tool availability transitions,
subgoal transitions, and coordination dependencies were self-consistent.
No monotone-decrease violations, HP-resurrection events, causal
incoherence, or conflicting state transitions detected.

Does this battle chain contain any rule violations? The answer is YES or NO.
```
**Expected output if template works:** NO

### Example instantiation — violated chain

```
Step 1 (turn=0):
  ResourceBudget: hp_unit_B at 100.0%
[... full chain as above ...]
Step 15 (turn=2):
  ToolAvailability: unit_B is now UNAVAILABLE (recover_in=0)

A symbolic constraint checker analyzed this chain. The checker reports:
VERDICT: VIOLATION DETECTED — HP RESURRECTION
Rule violated: ResourceBudget monotone constraint for HP.
A unit's HP dropped to 0% (faint) and later appeared at a higher
value (> 0%) without an intervening revival action. HP cannot increase
after reaching 0% under standard battle rules.

Does this battle chain contain any rule violations? The answer is YES or NO.
```
**Expected output if template works:** YES

---

## Template B — Verdict + Reasoning Injection

### Template structure

```
[chain rendered per OLAT baseline]

A symbolic constraint checker analyzed this chain step by step.
Checker analysis:
[checker_verdict_text]
[checker_reasoning_text]

Considering both the chain and the symbolic checker's analysis,
does this battle chain contain any rule violations? The answer is YES or NO.
```

**Note on checker_reasoning_text:** The OLAT symbolic checker stores `violation_type`
but not step-by-step reasoning text. For this experiment, the reasoning text would
be synthesized from `violation_type` + the relevant step numbers extracted from the
prompt. This synthesis needs to be formalized before the experiment runs.
Placeholder format:
```
Checker step-by-step: [Rule category] detected at Step [N] (turn=[T]).
Specifically: [one-sentence description of the rule breach].
```

### Hypothesis

The model integrates checker reasoning with its own chain reading. Seeing both the
verdict and the justification allows the model to validate (or override) the checker.
Integration is richer than Template A's pure deference.

### Success pattern
- Same as Template A for correctly-checked chains
- Additionally: if checker is occasionally wrong (which it may be for edge cases),
  the model corrects the checker rather than blindly deferring
- Gap ≥ Template A gap, or gap ≈ Template A with higher stability

### Failure pattern
- Rubber-stamping: model outputs checker verdict verbatim regardless of chain content
  (dr_violated ≈ dr_intact ≈ checker's accuracy on that split — no model value added)
- Confusion: reasoning injection causes the model to argue against the checker on
  violated chains, lowering dr_violated

### Example instantiation — intact chain

```
[... full chain ...]

A symbolic constraint checker analyzed this chain step by step.
Checker analysis:
VERDICT: NO VIOLATION
Rule checked: All resource budgets, tool availability transitions,
subgoal transitions, and coordination dependencies were self-consistent.
No monotone-decrease violations, HP-resurrection events, causal
incoherence, or conflicting state transitions detected.
Checker step-by-step: Reviewed all 15 steps. ResourceBudget fields with
decay=monotone_decrease decreased monotonically (pp_action_1_opp: 93.8%→87.5%).
ToolAvailability transitions are consistent (unit_A: AVAILABLE→UNAVAILABLE,
unit_B: ∅→AVAILABLE). No HP-resurrection events. No repeated-unavailability
anomaly (Step 15 unit_A re-declares UNAVAILABLE; this is redundant but not
a state reversal). SubGoalTransition from 'initial' is triggered once, correctly.

Considering both the chain and the symbolic checker's analysis,
does this battle chain contain any rule violations? The answer is YES or NO.
```
**Expected output if template works:** NO

### Example instantiation — violated chain

```
[... full chain ...]

A symbolic constraint checker analyzed this chain step by step.
Checker analysis:
VERDICT: VIOLATION DETECTED — HP RESURRECTION
Rule violated: ResourceBudget monotone constraint for HP.
A unit's HP dropped to 0% (faint) and later appeared at a higher
value (> 0%) without an intervening revival action. HP cannot increase
after reaching 0% under standard battle rules.
Checker step-by-step: At Step 8 (turn=1), hp_unit_A reaches 0.0% (faint).
At Step 10 (turn=2), hp_unit_A is reported at 100.0%. This is an increase
from 0% to 100% with no revival action in the intervening steps (Steps 8–9).
This violates the HP monotone constraint: a fainted unit cannot regain HP
without explicit revival.

Considering both the chain and the symbolic checker's analysis,
does this battle chain contain any rule violations? The answer is YES or NO.
```
**Expected output if template works:** YES

---

## Template C — Verdict as Evidence to Evaluate

### Template structure

```
[chain rendered per OLAT baseline]

A symbolic constraint checker examined this chain and produced the following analysis:
[checker_verdict_text]

You may agree with or disagree with the checker. Evaluate the chain and the
checker's analysis together. Does this battle chain contain any rule violations?
The answer is YES or NO.
```

### Hypothesis

The model performs critical evaluation rather than deference. The "you may agree or
disagree" instruction activates independent reasoning. This tests whether the model
can function as a validator of the checker rather than a follower.

### Success pattern
- On chains where checker is correct (all 50 in this experiment): same success as A/B
- On chains where checker might be wrong (edge cases, post-hoc analysis): model
  overrides checker correctly
- This template's value is most apparent in a follow-on experiment where some
  checker verdicts are intentionally flipped (adversarial injection)

### Failure pattern
- Model always defers despite the instruction (rubber-stamping)
- Model always disagrees with checker (reflexive contrarianism)
- Model contradicts correct checker verdicts, lowering gap below Templates A/B

### Example instantiation — intact chain

```
[... full chain ...]

A symbolic constraint checker examined this chain and produced the following analysis:
VERDICT: NO VIOLATION
Rule checked: All resource budgets, tool availability transitions,
subgoal transitions, and coordination dependencies were self-consistent.
No monotone-decrease violations, HP-resurrection events, causal
incoherence, or conflicting state transitions detected.

You may agree with or disagree with the checker. Evaluate the chain and the
checker's analysis together. Does this battle chain contain any rule violations?
The answer is YES or NO.
```
**Expected output if template works:** NO (agrees with checker on intact chain)

### Example instantiation — violated chain

```
[... full chain ...]

A symbolic constraint checker examined this chain and produced the following analysis:
VERDICT: VIOLATION DETECTED — HP RESURRECTION
Rule violated: ResourceBudget monotone constraint for HP.
A unit's HP dropped to 0% (faint) and later appeared at a higher
value (> 0%) without an intervening revival action. HP cannot increase
after reaching 0% under standard battle rules.

You may agree with or disagree with the checker. Evaluate the chain and the
checker's analysis together. Does this battle chain contain any rule violations?
The answer is YES or NO.
```
**Expected output if template works:** YES (agrees with checker on violated chain)

---

## Template Selection Guidance

| Template | Tests | Best if | Risk |
|---|---|---|---|
| A | Pure deference | Checker accuracy alone is sufficient | Rubber-stamping; no model reasoning |
| B | Integration | Reasoning context improves reliability | Reasoning text synthesis adds complexity |
| C | Critical evaluation | Model should validate checker, not blindly follow | May introduce contrarianism |

**Recommended run order:** A → C → B (ascending complexity; A establishes baseline,
C tests independence, B tests richest integration).

**Recommended n per template:** 50 chains × 2 models = 100 calls per template.
Total experiment: 300 calls at ~$X (TBD based on max_tokens budget).

**Both-author sign-off required before any API calls.**
