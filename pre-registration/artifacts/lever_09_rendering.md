# Blocker #2 — Lever 9 Exact Rendering Templates

**Status:** COMPLETE — templates drafted from handoff. Field names use L2 L1 cryptic baseline. Adjust field names if L2 corpus verification changes field list.

**Dependency:** Rendering templates use Lever 1 L2 field set (~12 fields). If corpus verification changes the L2 field list, update templates accordingly.

---

## Shared Policy: Lever 11 × Lever 16 Anchoring (Policy A)

When Lever 16 is at L2 or L3 (constraint context present), the constraint rules are **co-located immediately before the chain** in all rendering templates. The `{CONSTRAINT_CONTEXT}` block moves with the chain across all Lever 11 position conditions. Distractor padding surrounds the `{CONSTRAINT_CONTEXT + CHAIN}` bundle as a unit.

- When Lever 16 = L1 (no context): the `{CONSTRAINT_CONTEXT}` block is absent. The bundle is just the chain.
- When Lever 16 = L2/L3 and Lever 11 positions the chain at 5% / 50% / 95%: the rules immediately precede the chain in all three position conditions.

All three templates below include a `{CONSTRAINT_CONTEXT}` placeholder at the head of the chain block. Omit this block when Lever 16 = L1.

---

## Worked Example Chain

The following 5-turn chain (k=5) is used as the worked example across all three templates.

**Chain facts:**
- Player 1: Pikachu | Moveset: Thunderbolt, Quick Attack, Iron Tail, Volt Tackle
- Player 2: Blastoise | Moveset: Surf, Ice Beam, Flash Cannon, Aqua Jet
- Turn 5 violation: Pikachu uses Flamethrower — not in Pikachu's moveset (MOVESET_VIOLATION)

| Turn | Acting player | Pokemon | Move | Target | Damage | Target HP% remaining | Outcome | PP remaining | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | p1 | Pikachu | Thunderbolt | Blastoise | 65 | 35 | hit | 14 | none |
| 2 | p2 | Blastoise | Surf | Pikachu | 67 | 33 | hit | 14 | none |
| 3 | p1 | Pikachu | Quick Attack | Blastoise | 30 | 5 | hit | 29 | none |
| 4 | p2 | Blastoise | Ice Beam | Pikachu | 25 | 8 | hit | 9 | none |
| 5 | p1 | Pikachu | Flamethrower | Blastoise | 120 | 0 | faint | — | none |

---

## Template L1 — Multi-line Per Turn (v5.1 Baseline)

**Design intent:** Each turn rendered as a block of key-value lines, one field per line. Turns separated by blank line. This is the v5.1 baseline format.

**Delimiter conventions:**
- Field separator: `: ` (colon-space)
- Turn block separator: single blank line
- No explicit turn header line; `turn` field is the first line of each block
- Multi-entity events (e.g., a move that hits multiple targets): repeat the turn block once per target, incrementing a sub-index via `turn_part: 1`, `turn_part: 2`, etc.
- Null value handling: omit field entirely if value is null/not applicable (e.g., `dmg: 0` for status moves is written; `dmg` field omitted only if damage concept does not apply)
- Omitted field placeholders: field is omitted from block (not written as empty or N/A)
- Status field when no active status: `status: none`

**Policy A encoding:** `{CONSTRAINT_CONTEXT}` block (if present) appears immediately before the first turn block, separated by a blank line.

### Template L1 (with Policy A placeholder):

```
{CONSTRAINT_CONTEXT}

turn: 1
p: p1
poke: Pikachu
move: Thunderbolt
tgt_p: p2
tgt: Blastoise
dmg: 65
hp: 35
pp: 14
status: none
eff: super
result: hit

turn: 2
p: p2
poke: Blastoise
move: Surf
tgt_p: p1
tgt: Pikachu
dmg: 67
hp: 33
pp: 14
status: none
eff: neutral
result: hit

turn: 3
p: p1
poke: Pikachu
move: Quick_Attack
tgt_p: p2
tgt: Blastoise
dmg: 30
hp: 5
pp: 29
status: none
eff: neutral
result: hit

turn: 4
p: p2
poke: Blastoise
move: Ice_Beam
tgt_p: p1
tgt: Pikachu
dmg: 25
hp: 8
pp: 9
status: none
eff: neutral
result: hit

turn: 5
p: p1
poke: Pikachu
move: Flamethrower
tgt_p: p2
tgt: Blastoise
dmg: 120
hp: 0
pp: —
status: none
eff: neutral
result: faint
```

**Note on PP for violation turn:** When a move is not in the Pokemon's moveset, PP tracking is undefined. Render `pp: —` (literal dash) to indicate undefined/inapplicable. If the SPEC team prefers omitting the field entirely, note that omission policy should be consistent across all violation conditions.

---

## Template L2 — Single-Line Per Entity

**Design intent:** Each turn rendered as one line. All fields on a single line, pipe-delimited. Preserves turn order. One line = one acting entity's turn.

**Delimiter conventions:**
- Field separator within a turn: ` | ` (space-pipe-space)
- Field format: `key:value` (no space around colon)
- Turn separator: newline (each turn on its own line)
- Multi-entity events: render as multiple sequential lines with identical turn number and incrementing `sub` counter: `turn=5,sub=1 | ...` and `turn=5,sub=2 | ...`
- Null value handling: render `key:null`
- Omitted field placeholders: `key:—` (literal dash) for inapplicable fields (consistent with L1 policy)
- Multi-word values: use underscore to join (e.g., `Ice_Beam`, `Quick_Attack`)

**Policy A encoding:** `{CONSTRAINT_CONTEXT}` block (if present) appears as a single prefixed block on its own line before turn=1, using `RULE: ` prefix per line. Blank line separates the context block from the chain.

### Template L2 (with Policy A placeholder):

```
{CONSTRAINT_CONTEXT}

turn=1 | p:p1 | poke:Pikachu | move:Thunderbolt | tgt_p:p2 | tgt:Blastoise | dmg:65 | hp:35 | pp:14 | status:none | eff:super | result:hit
turn=2 | p:p2 | poke:Blastoise | move:Surf | tgt_p:p1 | tgt:Pikachu | dmg:67 | hp:33 | pp:14 | status:none | eff:neutral | result:hit
turn=3 | p:p1 | poke:Pikachu | move:Quick_Attack | tgt_p:p2 | tgt:Blastoise | dmg:30 | hp:5 | pp:29 | status:none | eff:neutral | result:hit
turn=4 | p:p2 | poke:Blastoise | move:Ice_Beam | tgt_p:p1 | tgt:Pikachu | dmg:25 | hp:8 | pp:9 | status:none | eff:neutral | result:hit
turn=5 | p:p1 | poke:Pikachu | move:Flamethrower | tgt_p:p2 | tgt:Blastoise | dmg:120 | hp:0 | pp:— | status:none | eff:neutral | result:faint
```

---

## Template L3 — Entity-Centric Grouping

**Design intent:** All events for Player 1's active Pokemon grouped together as a block, then all events for Player 2's active Pokemon. Within each entity block, events appear in chronological turn order. This breaks the turn-interleaved order of L1/L2.

**Delimiter conventions:**
- Entity block header: `=== {player}: {pokemon} ===` (triple-equals, space, player ID, colon-space, Pokemon name)
- Events within a block: single-line per-event format matching L2 syntax (for field encoding consistency)
- Entity block separator: single blank line
- Turn order within entity block: ascending (chronological within that entity's events)
- Multi-entity events: render the event in the block of the **acting** entity only; note target inline via `tgt:` and `tgt_p:` fields
- Null value handling: `key:null` consistent with L2
- Omitted field placeholders: `key:—` consistent with L1/L2
- Entity ordering: P1 block first, P2 block second (consistent with chain data ordering)

**Policy A encoding:** `{CONSTRAINT_CONTEXT}` block (if present) appears before the P1 entity block, separated by a blank line. Rules are not repeated inside each entity block.

### Template L3 (with Policy A placeholder):

```
{CONSTRAINT_CONTEXT}

=== p1: Pikachu ===
turn=1 | move:Thunderbolt | tgt_p:p2 | tgt:Blastoise | dmg:65 | tgt_hp:35 | pp:14 | status:none | eff:super | result:hit
turn=3 | move:Quick_Attack | tgt_p:p2 | tgt:Blastoise | dmg:30 | tgt_hp:5 | pp:29 | status:none | eff:neutral | result:hit
turn=5 | move:Flamethrower | tgt_p:p2 | tgt:Blastoise | dmg:120 | tgt_hp:0 | pp:— | status:none | eff:neutral | result:faint

=== p2: Blastoise ===
turn=2 | move:Surf | tgt_p:p1 | tgt:Pikachu | dmg:67 | tgt_hp:33 | pp:14 | status:none | eff:neutral | result:hit
turn=4 | move:Ice_Beam | tgt_p:p1 | tgt:Pikachu | dmg:25 | tgt_hp:8 | pp:9 | status:none | eff:neutral | result:hit
```

**Note on `hp` vs `tgt_hp` in L3:** In L1/L2, `hp` refers to the target's remaining HP after the move. In L3, the acting entity's turn block does not contain the acting entity's own HP as a primary field (the acting Pokemon's HP is only relevant if they are also targeted). Rename `hp` to `tgt_hp` in L3 to make the reference explicit. Confirm this renaming is acceptable before sign-off.

---

## Cross-Template Consistency Check

| Property | L1 | L2 | L3 |
|---|---|---|---|
| Turn order preserved | ✓ | ✓ | ✗ (entity-grouped) |
| All 12 L2 fields present | ✓ | ✓ | ✓ (10 shown; `p` field implicit in entity block header in L3) |
| Multi-entity event handling | Repeat block w/ sub-index | Repeat line w/ sub counter | Render in acting entity's block only |
| Null encoding | Omit field | `key:null` | `key:null` |
| Inapplicable field placeholder | `key: —` | `key:—` | `key:—` |
| Policy A rule co-location | Before turn 1 block | Before turn=1 line | Before P1 entity block |
| L1 baseline (no context) | Block absent | Block absent | Block absent |

---

## Verification Checklist for Sign-Off

- [ ] L1 field names confirmed against v5.1 corpus cryptic export keys (Blocker #1 dependency)
- [ ] Multi-entity event rendering tested on at least one multi-hit chain from v5.1 corpus
- [ ] `tgt_hp` rename in L3 confirmed (or reverted to `hp` with note)
- [ ] Policy A co-location confirmed: both authors agree on rule block format for L2/L3 of Lever 16
- [ ] Worked example renders correctly in actual pipeline rendering function
