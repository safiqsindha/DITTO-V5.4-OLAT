# E3 — Rescue Inspection Set

Each item below is a response that the v1 parser missed but the v2 parser caught.
Goal: confirm that v2's classification matches the model's clear intent (not a liberal rescue).

Total rescued in corpus: **64**.  Sample size: 30 (stratified).

## #1  [F_flash_cot_512]  chain_id=gen9ou-2287639343_p2_shuffled_1337
- **Ground truth:** violated (expected label: YES)
- **v1 parser:** missed (unparseable)
- **v2 parser:** NO (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
 at 0% — consistent with permanent unavailability in step 8.  
- **Step 12 (turn=7):** PP decay — fine.  
- **Step 13 (turn=7):** hp_unit_C again at 0% — redundant but not a violation.  
- **Step 14 (turn=8):** unit_A becomes AVAILABLE — consistent with recover_in=0 from step 2.  
- **Step 15 (turn=8):** hp_unit_A at 100% — fine.

No contradictions or impossible sequences appear.  

**Answer:** NO
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #2  [F_flash_cot_512]  chain_id=gen9ou-2341946701_p1_shuffled_1337
- **Ground truth:** violated (expected label: YES)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
 at turn 0. A fainted Pokémon cannot become available again without a healing or revival event, and none is shown. This is a **rule violation**.

**Step 7–15:**  
Later steps show HP changes for unit_B (75% at turn 2) and unit_A (0% then available later), but the core problem is that unit_B was revived without any indicated cause.

**Conclusion:**  
Yes, there is a rule violation.

**Answer:** YES
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #3  [H_pro_cot_512]  chain_id=gen9ou-2338779384_p1
- **Ground truth:** intact (expected label: NO)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
tem’s semantics.  
- **Step 14**: `pp_action_2_own` at 93.8%, monotone decrease. Fine.  
- **Step 15**: `hp_unit_C` at 0%. This is **odd** because `unit_C` just became available in Step 13, and now its HP is 0% without any noted damage event.  

The main possible violation is the **HP of `unit_C` dropping to 0% without any recorded action or damage** between Step 13 and Step 15.  

**Answer:** YES
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #4  [I_flash_cot_4096]  chain_id=gen9ou-2273536349_p1
- **Ground truth:** intact (expected label: NO)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
er* unit_E is marked unavailable (recover_in=0). In standard battle logic, you cannot shift to a phase targeting a Pokémon that is already fainted/unavailable unless the opponent switches it in at that exact moment — but the unavailability is recorded first, then the phase shift. That order implies a violation of logical sequencing.

**Conclusion**: Yes, there is a rule violation.

**Answer:** YES
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #5  [I_pro_cot_4096]  chain_id=gen9ou-2272614714_p1
- **Ground truth:** intact (expected label: NO)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
rops to 50% even though the phase is `vs_unit_B` and unit_A is unavailable. This could be a violation if damage to an unavailable unit isn’t allowed.  
- **Step 14–15**: HP for unit_B is 100%, PP decays continue. No issue.  

The main potential violation is **damage to unit_A while it’s unavailable and not in the current phase**. That seems inconsistent with normal battle logic.  

**Answer:** YES
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #6  [F_flash_cot_512]  chain_id=gen9ou-2306563046_p2_shuffled_1337
- **Ground truth:** violated (expected label: YES)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
 
- But at turn 1, the phase was just set to `vs_unit_D` in step 3. Now it says it was `vs_unit_A` — that’s a contradiction.  
- This is a **rule violation**: the phase cannot be in two different states at the same turn without a valid transition in between.

**Step 5–15:**  
- The rest may be consistent, but the contradiction in step 4 is enough.

**Conclusion:**  
YES, there is a rule violation.
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #7  [I_flash_cot_4096]  chain_id=gen9ou-2321922786_p1
- **Ground truth:** intact (expected label: NO)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
formation about unit_C added.  
The immediate availability/unavailability of unit_B in the same turn is odd, but could be possible if it was used and fainted instantly. However, combined with the HP jump earlier, it suggests tracking inconsistency.

**Key violation:**  
The HP of unit_B jumping from 75% to 100% in the same turn without any recovery event is a clear rule violation.

**Answer:** YES
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #8  [I_flash_cot_4096]  chain_id=gen9ou-2276761872_p1
- **Ground truth:** intact (expected label: NO)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
 action being recorded, which is suspicious.
- **Step 14**: Unit B becomes permanently unavailable.
- **Step 15**: Phase shifts to `forced_switch_required` due to own faint.

The key issue:  
HP dropping from 75% to 0% in a single turn without any recorded attacks or actions between the drops is not logically possible under normal battle rules. This indicates a **rule violation**.

**Answer:** YES
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #9  [I_flash_cot_4096]  chain_id=gen9ou-2275367426_p2_shuffled_1337
- **Ground truth:** violated (expected label: YES)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
*  
`pp_action_1_own at 93.8%` — fine.

**Step 13 (turn=3):**  
`unit_A is now UNAVAILABLE` — fine.

**Step 14 (turn=3):**  
`phase shifted from 'initial' to 'vs_unit_A'` — fine.

**Step 15 (turn=3):**  
`hp_unit_B at 0.0%` — fine.

**Conclusion:**  
Yes, there are rule violations — specifically, units appearing in HP/availability steps before being added to the information state.

**Answer:** YES
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #10  [H_pro_cot_512]  chain_id=gen9ou-2276761872_p1
- **Ground truth:** intact (expected label: NO)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
ks aren’t allowed in one turn, but the sequence doesn’t specify that rule.

**Step 15**:  
- Phase shifts from `initial` to `forced_switch_required` with trigger `own_faint`.  
- However, the phase was already `vs_unit_A` earlier, not `initial`.  
This is a **state inconsistency** — the phase should not be `initial` at this point.

That inconsistency is a rule/logic violation.

**Answer**: **YES**
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #11  [I_flash_cot_4096]  chain_id=gen9ou-2327376263_p1
- **Ground truth:** intact (expected label: NO)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
milar, not stay in `forced_switch_required`. Staying in the same phase after a faint is a **rule violation** because the game state should allow a new switch-in, not remain in the same forced-switch state.  

**Step 14–15 (turn=8):**  
- `unit_D` becomes available. That’s fine, but the phase issue remains.  

**Conclusion:**  
The phase not changing after a faint is a violation.  

**Answer:** YES
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #12  [H_pro_cot_512]  chain_id=gen9ou-2272363626_p2_shuffled_7919
- **Ground truth:** violated (expected label: YES)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
 with the same name, but no revive event is shown. This is inconsistent.  

**Step 12–13:**  
- unit_C becomes available with 25% HP — possible if switching in.  

**Step 14–15:**  
- InformationState updates — normal.  

The main issue is **unit_B fainting in Step 8 and then being available with full HP in Step 10–11 without any revive action**. That breaks normal battle rules.  

**Answer:** YES
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #13  [H_pro_cot_512]  chain_id=gen9ou-2287788376_p1_shuffled_42
- **Ground truth:** violated (expected label: YES)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
l violations:**  
1. The `forced_switch_required` trigger is listed as `own_faint`, but the fainted unit (`unit_C`) appears to be the opponent’s.  
2. Multiple HP restorations occur without corresponding actions logged.  
3. `unit_A` becomes unavailable then available again without a clear switch action.  

Given these inconsistencies, the chain does contain rule violations.  

**Answer:** **YES**
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #14  [F_flash_cot_512]  chain_id=gen9ou-2291273479_p2_shuffled_1337
- **Ground truth:** violated (expected label: YES)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
nit_C` to `vs_unit_B` — but `unit_C` was permanently unavailable since turn 7, so being in `vs_unit_C` phase on turn 8 is inconsistent. This is another **violation**.

**Steps 11–15 (turn=9):** More faints and HP updates — but the earlier inconsistencies already indicate a problem.

**Conclusion:** There are rule violations (inconsistent phase transitions and availability timing).

**Answer:** YES
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #15  [H_pro_cot_512]  chain_id=gen9ou-2278537373_p1_shuffled_7919
- **Ground truth:** violated (expected label: YES)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
ty 0.50. This is plausible.  

**Step 14:**  
- status_unit_D at 50%. Could be a status condition like paralysis or sleep. No conflict.  

**Step 15:**  
- InformationState update again. Fine.  

The main issue is **Steps 10–11** where a fainted and permanently unavailable unit_B gets HP again. That breaks the rule that fainted Pokémon cannot be healed or used again in battle.  

**Answer:**  
YES
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #16  [F_flash_cot_512]  chain_id=gen9ou-2317659387_p2
- **Ground truth:** intact (expected label: NO)
- **v1 parser:** missed (unparseable)
- **v2 parser:** NO (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
hen at turn 2, unit B also becomes unavailable with `recover_in=0`. If the game rules require at least one unit to be available for the opponent to continue, having two units unavailable in a row without any recovery time could be a violation — but the chain doesn’t show any rule that prevents this sequence explicitly.

No direct contradiction with standard battle logic is visible.

**Answer**: NO
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #17  [I_pro_cot_4096]  chain_id=gen9ou-2320688421_p1_shuffled_42
- **Ground truth:** violated (expected label: YES)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
values are plausible.

**Step 13:**  
- Same optimization criterion, no issue.

**Step 14:**  
- Information state update — normal.

**Step 15:**  
- `unit_C` becomes AVAILABLE — could be a switch back in.

---

The clear violation is in **Steps 8–9**, where `unit_B` faints (`UNAVAILABLE, recover_in=0`) and then immediately becomes `AVAILABLE` in the same turn with no explanation.

**Answer:** YES
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #18  [H_pro_cot_512]  chain_id=gen9ou-2341946701_p1_shuffled_1337
- **Ground truth:** violated (expected label: YES)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
12**  
- `hp_unit_A at 0.0%` — Unit A faints.  

**Step 13–14**  
- `unit_A is now AVAILABLE` after fainting in Step 12 — Again, a fainted unit becoming available without revival is a violation.  

**Step 15**  
- `hp_unit_C at 50.0%` — This is fine.  

**Conclusion**: There are clear rule violations regarding fainted units becoming available again without any revival event.  

**Answer**: **YES**
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #19  [F_flash_cot_512]  chain_id=gen9ou-2327278602_p2
- **Ground truth:** intact (expected label: NO)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
unavailable (recover_in=0 again), unit B becomes available, PP update for opponent.

**Key issue**:  
In **Step 11** and **Step 12**, `hp_unit_B` changes from 75% to 100% in the same turn (turn=2) with no healing action or event recorded. This is inconsistent with normal resource tracking rules unless a heal occurred, which isn't listed.

**Conclusion**: There is a rule violation.

**Answer**: YES
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #20  [I_pro_cot_4096]  chain_id=gen9ou-2348078225_p1
- **Ground truth:** intact (expected label: NO)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
e to opponent switch — but if Unit_B fainted, the phase change should be due to own faint, not opponent switch.  

**Step 13**:  
- InformationState adds unit_C with uncertainty 0.50 — this is fine for a new opponent.  

**Step 14–15**:  
- Resource budgets and HP updates look normal.  

The inconsistency in Step 11 (Unit_B fainting without HP depletion) is a rule violation.  

**Answer**: **YES**
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #21  [H_pro_cot_512]  chain_id=gen9ou-2354144810_p2_shuffled_7919
- **Ground truth:** violated (expected label: YES)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
onent_switch.  
  - **Potential issue**: unit_A was just marked permanently unavailable, so switching back to 'vs_unit_A' seems contradictory—you can’t fight a permanently unavailable unit.

- **Step 15 (turn=2)**:  
  - hp_unit_A at 75% after being permanently unavailable also seems inconsistent.

The chain appears to have a logical inconsistency in **Step 14** given **Step 13**.

**Answer:** YES
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #22  [F_flash_cot_512]  chain_id=gen9ou-2330862666_p2
- **Ground truth:** intact (expected label: NO)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
ext turn, but "UNAVAILABLE" with 0 recovery is contradictory unless it means permanent removal.  
- Also, Step 5 and Step 7 show both own and opponent PP at exactly 93.8% for different actions, which is suspiciously identical but not impossible.

The most notable possible violation is the **recover_in=0** with UNAVAILABLE status, which is inconsistent with standard recovery logic.

**Answer:** YES
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #23  [F_flash_cot_512]  chain_id=gen9ou-2273536349_p1
- **Ground truth:** intact (expected label: NO)
- **v1 parser:** missed (unparseable)
- **v2 parser:** NO (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
ted (e.g., by a switch limit per certain number of turns, or by a rule that a Pokémon cannot switch out if it just switched in). However, the given log does not explicitly state any such rule being broken — it only logs what happened.

Since no explicit rule violation is described in the steps themselves, and the log appears internally consistent, there is **no violation** evident.

**Answer:** NO
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #24  [I_pro_cot_4096]  chain_id=gen9ou-2270600845_p1_shuffled_7919
- **Ground truth:** violated (expected label: YES)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
**  
- pp_action_2_own at 81.2% then 87.5% — **violation**, because monotone decrease means it should not increase.  
- hp_unit_C at 100% — fine.  
- pp_action_1_opp at 93.8% — fine.  

The two clear violations are:  
1. unit_B marked permanently unavailable but later available.  
2. pp_action_2_own increased under monotone decrease.  

So the answer is **YES**, there are rule violations.

**YES**
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #25  [I_flash_cot_4096]  chain_id=gen9ou-2320688421_p1_shuffled_42
- **Ground truth:** violated (expected label: YES)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
e and then available in the same turn. If the rule is that a unit must stay unavailable for at least one full turn after being marked unavailable (unless recover_in > 0), then this is a violation.

Given that `recover_in=0` is used, it implies immediate recovery, which contradicts the usual meaning of "unavailable."

**Conclusion:** YES, there is a rule violation (inconsistent availability logic).
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #26  [F_flash_cot_512]  chain_id=gen9ou-2278300586_p1
- **Ground truth:** intact (expected label: NO)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
s used twice in a row without a proper switch or recovery turn.

**Potential violation**: A unit becoming available and unavailable in the same turn without a clear action or switch in between, and the phase shift happening after the second unavailability, suggests a possible illegal double-action or incorrect sequencing.

Given this, the chain appears to contain a rule violation.

**Answer:** YES
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #27  [F_flash_cot_512]  chain_id=gen9ou-2276761872_p1
- **Ground truth:** intact (expected label: NO)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
shifts to forced_switch_required due to own faint — correct trigger.

**Key issue**:  
Having four HP drops for unit_B (75% → 50% → 25% → 0%) all in turn=2 implies multiple damaging actions in one turn without the opponent having a turn to act in between. This violates the typical turn structure where each side acts once per turn.

**Conclusion**: YES, there is a rule violation.  

**Answer**: YES
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #28  [F_flash_cot_512]  chain_id=gen9ou-2320688421_p1_shuffled_42
- **Ground truth:** violated (expected label: YES)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
recover_in=0, that usually means the unit is permanently gone (fainted) or cannot return immediately. Making it available again on the very next step without any recovery time or explanation is inconsistent.

- **Step 10–15**: No further contradictions, but the inconsistency in Step 8–9 remains.

**Conclusion**: There is a rule violation regarding unit_B’s availability transition.

**Answer:** YES
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #29  [F_flash_cot_512]  chain_id=gen9ou-2312002915_p2
- **Ground truth:** intact (expected label: NO)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
is inconsistent with the earlier `recover_in=0` which should mean immediate recovery.
- **Step 12**: Unit B becomes available. Fine.
- **Step 13–15**: PP and HP changes. HP goes from 50% to 75% without any healing action mentioned — that’s a violation unless healing is implied but not stated.

**Conclusion**: There are inconsistencies (recovery timing and unexplained HP increase).

**Answer:** YES
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**

## #30  [H_pro_cot_512]  chain_id=gen9ou-2275367426_p2_shuffled_1337
- **Ground truth:** violated (expected label: YES)
- **v1 parser:** missed (unparseable)
- **v2 parser:** YES (rescue stage: md_strip)
- **Response tail (last 400 chars):**
```
al issue:**  
- Step 8 says `unit_A` is AVAILABLE, but Step 1–3 already had `unit_A` taking damage, implying it was already in battle. If it was already active, it shouldn’t become “available” again unless it had been unavailable in between, which isn’t shown. This could be a sequencing/logic inconsistency.

Given that, there is a **rule violation** in the availability tracking.

**Answer:**  
YES
```
- **Manual verdict (☐ correct rescue / ☐ wrong rescue / ☐ ambiguous):**
