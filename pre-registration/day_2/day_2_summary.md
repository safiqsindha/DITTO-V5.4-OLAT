# Day 2 Analysis Summary — Project Ditto OLAT

**SPEC hash:** `dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8`

## Completeness

- Provenance records: 3200
- Assignments: 3200
- Complete: YES
- API failures: 0
- Parse failures: 184
- Global parse fail rate: 0.0575

## Effect Table Summary (Universe L3 — symbolic checker as truth)

- Meaningful: 6
- Directional: 7
- Null: 43
- Total non-baseline conditions: 62

### Top Meaningful Effects (sorted by |effect_size|)

| Condition | Model | Effect | CI | Classification |
|---|---|---|---|---|
| pro_L18_L2 | deepseek-v4-pro | 0.3785 | [0.0357, 0.7454] | Meaningful |
| pro_L18_L3 | deepseek-v4-pro | 0.3542 | [0.0257, 0.6847] | Meaningful |
| pro_L17_L2 | deepseek-v4-pro | 0.2882 | [0.0514, 0.4857] | Meaningful |
| pro_L17_L3 | deepseek-v4-pro | 0.2431 | [0.0095, 0.51] | Meaningful |
| flash_L18_L2 | deepseek-v4-flash | 0.2167 | [0.0255, 0.5] | Meaningful |
| pro_L12_L3 | deepseek-v4-pro | 0.191 | [0.0174, 0.4375] | Meaningful |

## Cross-Model Deltas (Universe L3)

- Meaningful deltas (Flash vs Pro): 1 / 31

## Robustness Flags

- robustness_concern flagged: 0 conditions
- hidden_signal_candidate flagged: 0 conditions
