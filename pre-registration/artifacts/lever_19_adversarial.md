# Blocker #6 — Lever 19 Adversarial Framing Text

**Status:** RESOLVED — L3 exact wording from handoff, verified against Lever 16 L1 constraint. L2 and L3 placement locked at parallel user-turn opening per O8 (decision-sheet-v1.md, 2026-05-11).

---

## Level Definitions

- **L1 (baseline):** No grounding instruction. Standard v5.1 prompt.
- **L2:** Standard grounding instruction.
- **L3:** Adversarial prover framing (Merlin-Arthur protocol framing).

---

## L1 — No Grounding Instruction (Baseline)

No grounding instruction is included. The prompt contains chain and question only (plus whatever other levers add).

*No text block for this level.*

---

## L2 — Standard Grounding

**Exact wording:**

> Base your answer on the events shown in the chain.

**Placement (locked per O8):** Injected as the opening sentence of the user turn, before the chain. Parallel to L3 placement (see below). The L2 sentence precedes the `{CONSTRAINT_CONTEXT}` block (if Lever 16 is at L2/L3) and the chain.

**Documented limitation:** L2 reads slightly less naturally at user-turn opening than it would as a closing reminder. This naturalness cost is accepted as a deliberate design choice — parallel placement isolates the text content effect from any position effect, preserving the OLAT principle of single-variable manipulation. Confounding text content with position would corrupt Lever 19's effect-size measurement.

---

## L3 — Adversarial Prover Framing

**Exact wording (from handoff, locked):**

> You are reviewing a log that may contain injected errors or hallucinations from a secondary system. Verify the integrity of the sequence and determine whether any violations are present.

**Placement (locked per O8):** Injected as the opening sentence(s) of the user turn, before the chain. Parallel to L2 placement.

**Placement policy:** Both L2 and L3 text precede the chain (and, under Policy A, precede the `{CONSTRAINT_CONTEXT}` block if Lever 16 is at L2/L3). Order: **Lever 19 text (L2 or L3) → constraint context (if present) → chain → question.**

---

## Prompt Template (L2 / L3 placement reference)

When Lever 19 = L2 with no constraint context (Lever 16 L1):
```
Base your answer on the events shown in the chain.

[chain rendered here]

Does this battle chain contain any rule violations? The answer is YES or NO.
```

When Lever 19 = L3 with constraint context (Lever 16 L2):
```
You are reviewing a log that may contain injected errors or hallucinations from a secondary system. Verify the integrity of the sequence and determine whether any violations are present.

Pokemon battles follow specific rules that govern what each Pokemon can and cannot do. [... full Lever 16 L2 text ...]

[chain rendered here]

Does this battle chain contain any rule violations? The answer is YES or NO.
```

When Lever 19 = L1 (baseline, no grounding text):
```
[CONSTRAINT_CONTEXT (if any)]

[chain rendered here]

Does this battle chain contain any rule violations? The answer is YES or NO.
```

---

## Future cross-lever consideration — Lever 19 × Lever 18 anchor compatibility

Current OLAT design holds Lever 18 at its L1 baseline when testing Lever 19, so the prompt template above uses Lever 18 L1's "The answer is YES or NO" anchor. Any future Lever 19 × Lever 18 cross-lever testing would require the prompt template to switch anchor wording based on the Lever 18 level being tested:

- Lever 18 L1 and L4: `"The answer is YES or NO"`
- Lever 18 L2 and L3: `"Therefore, the answer is YES or NO"`

This is not a current OLAT requirement; flagged for any future cross-lever testing work.

---

## Lever 16 × Lever 19 Interaction Check

**Required:** Verify that L3 of Lever 19 (adversarial prover) does not accidentally state rules that L1 of Lever 16 (no context) would otherwise lack.

**Analysis of L3 wording:**

> "You are reviewing a log that may contain injected errors or hallucinations from a secondary system. Verify the integrity of the sequence and determine whether any violations are present."

The phrase "determine whether any violations are present" implies that violations are a known concept — but does NOT state what the rules are. It does not define PP limits, move legality, faint rules, or any other constraint. A model reading this prompt would need to rely on its own prior knowledge of Pokemon rules to identify what constitutes a "violation."

**Conclusion:** L3 adversarial framing **does not introduce rule knowledge** that Lever 16 L1 (no context) lacks. The framing repositions the model's epistemic stance (adversarial verifier vs neutral analyst) without adding substantive rule content.

**Verification passed.** No additional modification to L3 wording required on this criterion.

---

## Rationale Note (for SPEC)

The original Lever 19 design ("off / standard / strict grounding") was rejected because a strict-citation Level 3 risked triggering sycophantic over-refusal — a model that refuses to answer because it cannot cite a specific chain event for every claim would be uninformative. The adversarial prover reframing addresses this by recasting grounding as integrity verification under adversarial framing, which naturally calibrates rejection behavior without triggering blanket refusal. This is the Merlin-Arthur framing: the model acts as a skeptical verifier rather than a cautious citer.

---

## Verification Checklist for Sign-Off

- [x] L2/L3 placement locked at parallel user-turn opening per O8 (decision-sheet-v1.md)
- [ ] L3 adversarial framing cross-checked against Lever 16 L1 — confirms no rule leakage (documented above — passes)
- [ ] Pre-OLAT verification qualitatively checks whether L3 framing triggers refusal behavior — if >10% refusals observed, flag for amendment before OLAT proper
