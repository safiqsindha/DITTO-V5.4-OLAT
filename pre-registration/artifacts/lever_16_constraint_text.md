# Blocker #4 — Lever 16 Exact Rule/Context Text

**Status:** RESOLVED — paralysis framing locked per O7 Option A (decision-sheet-v1.md, 2026-05-11). L3 omits RULE_PARA. L2 retains hedged paralysis wording. Day -3 chain pool check required before pre-OLAT verification execution to confirm no paralysis-only violations in the test set.

---

## Level Definitions

- **L1 (baseline):** No constraint context. Chain and question only.
- **L2:** Generic paragraph in natural language.
- **L3:** Structured rules in predicate form.

**Equivalence requirement:** Every violation type in the v5.1 test set must map to a corresponding rule expression in both L2 and L3. L2 and L3 encode the same constraints — different format, same coverage.

**Policy A co-location:** When Lever 11 is being tested, L2 and L3 text is co-located immediately before the rendered chain as a bundle. See lever_09_rendering.md for placement syntax in each rendering template.

---

## L1 — No Context (Baseline)

No constraint text is included in the prompt. The chain and question appear alone.

*No text block for this level.*

---

## L2 — Generic Natural Language Paragraph

**Exact wording:**

> Pokemon battles follow specific rules that govern what each Pokemon can and cannot do. Each move has a limited number of uses (PP); once a move's PP reaches zero, that move cannot be used again. A Pokemon that has fainted cannot take any action for the remainder of the battle. Each Pokemon can only use moves that belong to its specific moveset — moves from other Pokemon's movesets are not available. Certain status conditions also restrict what a Pokemon can do: a sleeping or frozen Pokemon cannot use moves, and a fully paralyzed Pokemon may be prevented from acting entirely.

**Formatting for prompt injection:** Insert as a single paragraph with no leading label or header. Precedes the chain block directly (Policy A: moves with the chain for Lever 11 testing).

**Word count:** ~100 words.

---

## L3 — Structured Rules in Predicate Form

**Exact wording:**

```
RULE_PP: A move requires PP > 0 to be used. Using a move with PP = 0 is a violation.
RULE_FAINT: A Pokemon with status = fainted cannot take any action. Any action by a fainted Pokemon is a violation.
RULE_MOVESET: A Pokemon can only use moves in its moveset. Using a move not in the Pokemon's moveset is a violation.
RULE_SLEEP: A Pokemon with status = sleep cannot use moves (except Sleep Talk or Snore). Using other moves while asleep is a violation.
RULE_FREEZE: A Pokemon with status = freeze cannot use moves (except moves that thaw). Using other moves while frozen is a violation.
```

**Formatting for prompt injection:** Each rule on its own line, no blank lines between rules, no trailing punctuation variation. Precedes the chain block directly (Policy A). No header label (e.g., do not prepend "Rules:" or "Constraints:").

---

## Violation Type → Rule Coverage Table

**Status of violation type list:** [REQUIRES V5.1 TEST SET ENUMERATION — confirm all violation types present in the OLAT chain corpus before sign-off]

| Violation type | Violation code | L2 coverage | L3 rule | Notes |
|---|---|---|---|---|
| PP exhaustion | PP_EXHAUSTION | ✓ "once a move's PP reaches zero, that move cannot be used again" | RULE_PP | Covered in both |
| Fainted Pokemon acts | FAINT_ACTION | ✓ "A Pokemon that has fainted cannot take any action" | RULE_FAINT | Covered in both |
| Move not in moveset | MOVESET_VIOLATION | ✓ "Each Pokemon can only use moves that belong to its specific moveset" | RULE_MOVESET | Covered in both |
| Action while asleep | SLEEP_VIOLATION | ✓ "a sleeping...Pokemon cannot use moves" | RULE_SLEEP | L2 mentions Sleep Talk/Snore exception implicitly; L3 makes it explicit |
| Action while frozen | FREEZE_VIOLATION | ✓ "a frozen Pokemon cannot use moves" | RULE_FREEZE | Covered in both |
| Action while fully paralyzed | PARA_VIOLATION | ⚠️ HEDGED — L2 says "may be prevented from acting" (probabilistic framing, not absolute rule) | ❌ NO RULE_PARA — omitted per O7 Option A | **Resolution (O7):** Paralysis is omitted from L3 entirely. L2's hedged wording is retained. Pre-OLAT Day -3 chain pool check confirms no paralysis-only violations exist in the test set. If any are found, default response is exclusion (see below). |
| [ADDITIONAL TYPES] | [REQUIRES TEST SET] | — | — | [REQUIRES V5.1 VIOLATION TYPE ENUMERATION] |

**Paralysis framing — resolution (O7 Option A):** Paralysis is probabilistic in Pokemon mechanics (~75% successful action, ~25% blocked). L2 retains its hedged "may be prevented from acting" wording. L3 omits RULE_PARA entirely — no deterministic predicate rule can express the 25% probability mechanic without false positives on legitimate paralyzed-but-acting events.

**Day -3 chain pool check (mandatory before pre-OLAT verification):**

1. Filter the v5.1 test set for chains where the only planted violation is paralysis-related ("acted while paralyzed" with no other rule violation present).
2. If count > 0, flag for review.
3. **Response options:**
   - **Default — Option 1:** Exclude paralysis-only chains from the OLAT test set. Document the exclusion in the chain-condition assignment log.
   - **Option 2:** Retain them and document as a known limitation. These chains will produce uninterpretable results under L3 predicate framing (no RULE_PARA to match against).
   - **Fallback:** If excluding reduces the test set below required minimum (n_violated < ~50% of chains), use Option 2 and document.
4. Both authors sign off on the exclusion decision before Day -2 verification execution.

---

## L2/L3 Equivalence Verification

For each covered violation type, verify that L2's natural language framing and L3's predicate rule capture the same constraint boundary. The table above documents coverage; equivalence check is:

1. For each row where both L2 and L3 are ✓: confirm both rules have the same triggering condition
2. For each row where L2 ✓ but L3 ❌: draft the missing L3 rule or escalate
3. For each row marked PARTIAL: resolve framing before sign-off

**Current equivalence gaps:**
- PARA_VIOLATION: L2 is probabilistic framing, L3 has no rule → resolved per O7 Option A. Day -3 chain pool check filters paralysis-only chains from the test set; equivalence gap is structurally removed before evaluation runs.

---

## Verification Checklist for Sign-Off

- [ ] v5.1 test set violation types enumerated and added to coverage table
- [ ] All violation types have both L2 coverage and L3 rule (or deliberate exclusion documented)
- [x] Paralysis framing resolved per O7 Option A (decision-sheet-v1.md): L3 omits RULE_PARA, L2 retains hedged wording, Day -3 chain pool check enforces exclusion if needed
- [ ] Day -3 chain pool check executed and signed off (Day -3 task, not pre-signoff)
- [ ] Policy A placement tested in actual prompt construction pipeline
- [ ] Both authors confirm rule text is accurate to Pokemon game mechanics for the relevant competitive format
