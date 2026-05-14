# Blocker #9 — Evaluation Plumbing Schemas

**Status:** COMPLETE — schemas locked from handoff. Example records provided.

---

## Schema 1 — Parser Provenance Log

**Purpose:** Track which parse stage successfully extracted a YES/NO classification for each sample. Required for parse attrition audit (Documented Assumption #8). Supports sensitivity check that excludes fallback-stage-rescued samples.

**One record per API call response.**

### Schema definition

```json
{
  "condition_id": "string",
  "sample_id": "string",
  "parse_stage_reached": "strict | permissive | first_token | unparseable",
  "parse_success": "boolean",
  "fallback_used": "boolean",
  "raw_output": "string"
}
```

### Field definitions

| Field | Type | Description |
|---|---|---|
| `condition_id` | string | Identifier for the OLAT condition. Format: `lever_{N}_L{level}`, e.g., `lever_09_L2`. Baseline condition: `baseline`. |
| `sample_id` | string | Unique identifier for the chain evaluated. Format: `chain_{corpus_id}_{run_index}`, e.g., `chain_0042_01`. Must be consistent with chain-condition assignment log (Schema 2). |
| `parse_stage_reached` | enum string | The stage at which parsing terminated. Values: `strict` (primary regex matched), `permissive` (secondary regex matched), `first_token` (first-token classification applied), `unparseable` (all stages failed). |
| `parse_success` | boolean | True if a YES/NO classification was extracted (stages 1–3). False if `parse_stage_reached = unparseable`. |
| `fallback_used` | boolean | True if `parse_stage_reached` is `first_token` (any stage beyond strict). False if `parse_stage_reached` is `strict`. Note: `permissive` stage counts as fallback for this flag. |
| `raw_output` | string | The full `content` field from the API response, unmodified. For Lever 18 L4, `raw_output` contains only the `content` field (not `reasoning_content`). `reasoning_content` is stored separately (see implementation note). |

**Implementation note for Lever 18 L4:** When Lever 18 L4 (native thinking) is active, `raw_output` should contain `content` only. Store `reasoning_content` in a separate field `reasoning_content` appended to the record (not in the locked schema, but tracked for qualitative review).

**Implementation note for Lever 12 L3:** When Lever 12 L3 (function calling) is active, `raw_output` contains the tool call result payload (the function call arguments JSON), not a text completion. Parser operates on the structured payload; `parse_stage_reached` will typically be `strict` if the schema validates or `unparseable` if the payload is malformed.

### Example records

**Example 1 — strict parse success:**
```json
{
  "condition_id": "lever_18_L2",
  "sample_id": "chain_0042_01",
  "parse_stage_reached": "strict",
  "parse_success": true,
  "fallback_used": false,
  "raw_output": "Let me review this chain step by step. Turn 1: Pikachu uses Thunderbolt... Turn 5: Pikachu uses Flamethrower — Flamethrower is not in Pikachu's moveset. Therefore, the answer is YES."
}
```

**Example 2 — first-token fallback:**
```json
{
  "condition_id": "lever_09_L3",
  "sample_id": "chain_0108_01",
  "parse_stage_reached": "first_token",
  "parse_success": true,
  "fallback_used": true,
  "raw_output": "YES, the chain contains a violation in turn 3."
}
```

**Example 3 — unparseable:**
```json
{
  "condition_id": "lever_12_L2",
  "sample_id": "chain_0217_01",
  "parse_stage_reached": "unparseable",
  "parse_success": false,
  "fallback_used": false,
  "raw_output": "The battle chain appears to follow standard Pokemon mechanics throughout all five turns with no apparent irregularities in move selection or execution."
}
```

---

## Schema 2 — Chain-Condition Assignment Log

**Purpose:** Track which chains appear in which conditions to support post-hoc leakage assessment (Documented Assumption #12). Sampling with replacement across conditions creates dependence structure; this log enables auditing.

**One record per (chain, condition) assignment.**

### Schema definition

```json
{
  "chain_id": "string",
  "condition_id": "string",
  "sequence_position": "integer",
  "sampling_method": "without_replacement_within | with_replacement_across"
}
```

### Field definitions

| Field | Type | Description |
|---|---|---|
| `chain_id` | string | Unique identifier for the chain from the corpus. Format: `chain_{corpus_id}`, e.g., `chain_0042`. Matches the `chain_` prefix in `sample_id` from Schema 1. |
| `condition_id` | string | Identifier for the OLAT condition. Same format as Schema 1 `condition_id`. |
| `sequence_position` | integer | Position of this chain in the ordered evaluation sequence for this condition (1-based). Used for temporal ordering if any mid-run API issues arise. |
| `sampling_method` | enum string | Sampling method governing this chain-condition assignment. `without_replacement_within` = this chain appears exactly once within this condition (standard within-condition design). `with_replacement_across` = this chain may appear in multiple conditions (expected; documents the cross-condition dependence structure). |

**Note:** Every record in Schema 2 should correspond to a record in Schema 1 (same `condition_id` + `sample_id` where `sample_id`'s `chain_` prefix matches `chain_id`). Orphan records in either direction indicate a pipeline tracking failure.

### Example records

**Example 1 — chain appearing in one condition:**
```json
{
  "chain_id": "chain_0042",
  "condition_id": "lever_09_L2",
  "sequence_position": 17,
  "sampling_method": "without_replacement_within"
}
```

**Example 2 — same chain in a second condition (with-replacement-across documented):**
```json
{
  "chain_id": "chain_0042",
  "condition_id": "lever_18_L3",
  "sequence_position": 33,
  "sampling_method": "with_replacement_across"
}
```

**Example 3 — baseline condition:**
```json
{
  "chain_id": "chain_0108",
  "condition_id": "baseline",
  "sequence_position": 1,
  "sampling_method": "without_replacement_within"
}
```

---

## Storage and Format

Both schemas should be stored as newline-delimited JSON (NDJSON) for streaming writes during evaluation:
- `parser_provenance.ndjson` — one JSON object per line
- `chain_condition_assignments.ndjson` — one JSON object per line

Both files are append-only during the evaluation run. Do not overwrite; append.

---

## Verification Checklist for Sign-Off

- [ ] `condition_id` format confirmed and enumerated for all ~36 OLAT conditions before run
- [ ] `chain_id` format confirmed against v5.1 corpus chain identifiers
- [ ] Pipeline writes both log files on every API call (not batched post-hoc)
- [ ] Schema 1 × Schema 2 join confirmed on (condition_id, chain_id) before analysis
- [ ] `reasoning_content` storage for Lever 18 L4 implemented separately from locked `raw_output` field
