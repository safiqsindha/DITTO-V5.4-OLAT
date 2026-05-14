# Task 6: Sensitivity Analyses — 6 Meaningful Conditions (Universe L3)

**SPEC hash:** `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8`  
**Generated:** 2026-05-13  
**Per:** SPEC §9.2 — six sensitivity analyses reported alongside primary, do not override.

---

## Sensitivity Definitions

| ID | Name | Treatment |
|---|---|---|
| S1 | Unparseables-as-NO | Unparseable responses counted as NO |
| S2 | Unparseables-as-random | Unparseable responses counted as 0.5 (random) |
| S3 | Arcsine transformation | Cohen's h on arcsine-transformed rates (no BCa CI) |
| S4 | Parser-strict subset | Only responses parsed at stages 1–2 (strict/permissive) |
| S5 | Parse-failure audit | Parse failure rate ≥10% flags the condition |
| S6 | Response-length quartile | Gap by completion-token quartile of `usage.output_tokens` (L18 L2/L3 only). **Updated 2026-05-13: uses tokens (canonical methodological unit per SPEC §4), not character length. See `quartile_analysis/bimodal_summary.md` for the full reasoning-depth-threshold analysis.** |

---

## Results by Condition

### pro_L18_L2 (effect=0.379, Meaningful)

| Sensitivity | Result | Classification | Notes |
|---|---|---|---|
| Primary | 0.379 [0.036, 0.745] | **Meaningful** | |
| S1 as_no | 0.379 | **Meaningful** | No unparseables — identical to primary |
| S2 as_random | 0.379 | **Meaningful** | Same (no unparseables) |
| S3 arcsine | 0.933 | Meaningful(no_CI) | Cohen's h; no CI for arcsine sensitivity per SPEC |
| S4 parser_strict | Unknown (n=0) | Unknown | All 50 responses parsed via stages 3–4; S4 is vacuous |
| S5 parse_fail | 0.0% | Not flagged | |
| S6 quartile (L18, tokens) | Q1 (166–306): 0.280, Q2 (310–355): 0.080, Q3 (356–408): 0.524, Q4 (428–654): 0.258 | — | All-positive; Q3 highest. No valley. |

**Robustness assessment:** S1 and S2 identical (no unparseables). S3 corroborates direction. S4 is structurally unavailable (all responses use late cascade stages). S5 clean. S6 (completion-token quartiles) shows all-positive gaps across response-length quartiles; no reversal valley. `robustness_concern=False`.

**S4 note for all conditions:** Parser-strict (stages 1–2 only) is vacuous for conditions where models produce markdown-decorated responses parsed via md_strip or last_token. This is expected for CoT and structured-output conditions (Levers 17, 18) and is documented as parser-dependence characterization per Amendment #4 B3 / E1 — not a failure of the analysis.

---

### pro_L18_L3 (effect=0.354, Meaningful)

| Sensitivity | Result | Classification | Notes |
|---|---|---|---|
| Primary | 0.354 [0.026, 0.685] | **Meaningful** | |
| S1 as_no | 0.354 | **Meaningful** | No unparseables |
| S2 as_random | 0.354 | **Meaningful** | Same |
| S3 arcsine | 0.888 | Meaningful(no_CI) | |
| S4 parser_strict | Unknown (n=0) | Unknown | Vacuous — all stage 3–4 |
| S5 parse_fail | 0.0% | Not flagged | |
| S6 quartile (L18, tokens) | Q1 (296–423): 0.109, **Q2 (427–487): −0.365 (CI [−0.78, −0.06])**, Q3 (494–582): 1.080, Q4 (587–799): 0.455 | — | Valley-then-peak; Q2 reversed and statistically significant |

**Robustness assessment:** S1, S2, S3 all corroborate. S4 vacuous. S5 clean. **S6 (token-quartile, supersedes Day 2 character-length analysis) reveals a reasoning-depth threshold:** Q2 (response lengths ~427–487 tokens) shows a statistically significant **reversed effect** — every intact chain in this range answered YES (`dr_intact=1.0`) while violated chains dropped to `dr_violated=0.56`. Q3 (≥494 tokens) shows perfect separation. The overall positive effect (0.354) emerges because Q3 + Q4 dominate; the Q2 valley is washed out in the aggregate but is a real reasoning-depth phenomenon. See `quartile_analysis/bimodal_summary.md`. `robustness_concern=False` (the aggregate Meaningful classification holds), but the valley is a meaningful design constraint for Mew.

---

### pro_L17_L2 (effect=0.288, Meaningful)

| Sensitivity | Result | Classification | Notes |
|---|---|---|---|
| Primary | 0.288 [0.051, 0.486] | **Meaningful** | |
| S1 as_no | 0.288 | **Meaningful** | No unparseables |
| S2 as_random | 0.288 | **Meaningful** | Same |
| S3 arcsine | 0.801 | Meaningful(no_CI) | |
| S4 parser_strict | Unknown (n=0) | Unknown | 50/50 parsed at strict/permissive — but baseline S4 has n=0 (baseline uses late stages), making effect computation impossible |
| S5 parse_fail | 0.0% | Not flagged | |
| S6 quartile | N/A | — | L18 condition only |

**Robustness assessment:** S1, S2, S3 all corroborate. S4 vacuous (baseline n=0 under strict-only filter). S5 clean. `robustness_concern=False`. Most stable Meaningful finding in the set.

**Note on S4 for L17 conditions:** n_parsed_strict12=50/50 for pro_L17_L2 and pro_L17_L3 (all responses parsed at stages 1–2). However, the baseline (`pro_baseline`) uses stages 3–4 (markdown-decorated responses), producing n=0 in S4's strict-only filter for the baseline. Effect cannot be computed without a valid baseline. This is a structural limitation of S4 when baseline and condition use different parse paths — not a robustness concern.

---

### pro_L17_L3 (effect=0.243, Meaningful)

| Sensitivity | Result | Classification | Notes |
|---|---|---|---|
| Primary | 0.243 [0.010, 0.510] | **Meaningful** | |
| S1 as_no | 0.243 | **Meaningful** | No unparseables |
| S2 as_random | 0.243 | **Meaningful** | Same |
| S3 arcsine | 0.822 | Meaningful(no_CI) | |
| S4 parser_strict | Unknown (n=0) | Unknown | Vacuous (same S4 baseline issue as L17 L2) |
| S5 parse_fail | 0.0% | Not flagged | |
| S6 quartile | N/A | — | L18 condition only |

**Robustness assessment:** Identical to pro_L17_L2 pattern. `robustness_concern=False`. Note: pro_L17_L3's primary CI [0.010, 0.510] just barely excludes zero — this is the narrowest Meaningful confirmation in the set. Effect magnitude is real but CI-boundary-sensitive.

---

### flash_L18_L2 (effect=0.217, Meaningful)

| Sensitivity | Result | Classification | Notes |
|---|---|---|---|
| Primary | 0.217 [0.026, 0.500] | **Meaningful** | |
| S1 as_no | 0.240 | **Meaningful** | Slight increase (5 unparseables treated as NO, boosting gap slightly) |
| S2 as_random | 0.215 | **Meaningful** | Near-identical |
| S3 arcsine | 0.680 | Meaningful(no_CI) | |
| S4 parser_strict | Unknown (n=0) | Unknown | flash_L18_L2 has n_parsed_strict12=11/46 (76% use stages 3–4) |
| S5 parse_fail | 8.0% | Not flagged (threshold 10%) | 4 parse failures — approaching threshold |
| S6 quartile (L18, tokens) | Q1 (153–362): 0.000, Q2 (370–449): 0.000, Q3 (452–501): 0.500, Q4 (506–680): 0.667 | — | Monotone-positive threshold; engages above ~450 tokens |

**Robustness assessment:** S1 and S2 both Meaningful and directionally consistent. S3 corroborates. S4 vacuous. S5 parse failure rate 8.0% — below 10% threshold but notable. S6 (token-quartile, supersedes Day 2 character-length analysis) shows a clean monotone-positive threshold: null at short response lengths (Q1/Q2 ≤ 449 tokens), strong positive at longer lengths (Q3/Q4 ≥ 452 tokens). No valley reversal — Flash's L18 L2 effect is a pure engagement threshold, not a reasoning-depth-trap pattern. `robustness_concern=False`.

---

### pro_L12_L3 (effect=0.191, Meaningful)

| Sensitivity | Result | Classification | Notes |
|---|---|---|---|
| Primary | 0.191 [0.017, 0.438] | **Meaningful** | |
| S1 as_no | 0.191 | **Meaningful** | No unparseables |
| S2 as_random | 0.191 | **Meaningful** | Same |
| S3 arcsine | 1.004 | Meaningful(no_CI) | Unusually high Cohen's h |
| S4 parser_strict | Unknown (n=0) | Unknown | n_parsed_strict12=50 (all permissive via regex) — S4 baseline issue |
| S5 parse_fail | 0.0% | Not flagged | All parsed via regex fallback; no parse failures |
| S6 quartile | N/A | — | L18 condition only |

**Robustness assessment:** S1, S2 identical (no unparseables). S3 shows unusually high Cohen's h (1.004), indicating large effect in arcsine space — consistent with sparse YES responses. S4 vacuous. S5 clean.

**Important caveat for pro_L12_L3:** All 50 records were parsed via regex fallback on truncated JSON arguments (implementation anomaly — see Day 2 summary). The function-calling condition's YES/NO labels come from `"violation_detected": true/false` extracted by regex from incomplete JSON. The parser-strict sensitivity (S4) is unavailable. Both authors should note that pro_L12_L3's Meaningful classification depends entirely on regex-parsed function-call responses, not on any text-based answer format. `robustness_concern=False` per the automated flag, but manual scrutiny warranted.

---

## Robustness Flag Summary

| Condition | robustness_concern | hidden_signal_candidate | Notes |
|---|---|---|---|
| pro_L18_L2 | False | False | S4 vacuous; S1/S2/S3 corroborate |
| pro_L18_L3 | False | False | S6 bimodal pattern worth noting |
| pro_L17_L2 | False | False | Most robust in set |
| pro_L17_L3 | False | False | CI boundary-sensitive |
| flash_L18_L2 | False | False | S5 near-threshold; S6 monotone |
| pro_L12_L3 | False | False | Regex-only; S4 vacuous |

No conditions trigger `robustness_concern` (primary Meaningful + ≥3/6 sensitivities Null). The 0-flag result from the primary analysis holds for the Meaningful subset specifically.

---

## S4 Structural Limitation (Cross-Condition)

Parser-strict sensitivity (S4) is **structurally unavailable** for all 6 Meaningful conditions. The root cause differs by condition type:

- **Lever 17, 18 (text output):** Condition responses parsed at stages 1–2, but the baseline responses use stages 3–4 (markdown-decorated). S4 cannot compute effect without a valid baseline.
- **Lever 12 L3 (function calling):** Condition responses parsed at 'permissive' (regex fallback), but this is coded as stage 2. However, the baseline has the same issue.

Per Amendment #4 B3/E1: S4 is labeled "parser-dependence characterization" — it measures whether findings hold when restricted to strict-parse responses. For CoT and structured-output conditions, this restriction is vacuous because the model's output format under those conditions systematically uses non-anchored phrasing. The S4 Unknown result correctly reflects this structural limitation.
