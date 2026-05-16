#!/usr/bin/env python3
"""Test A3 (Opus no-internet) checker on development and validation sets."""

import json
from checker import ConstraintChecker


def load_chains(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def evaluate(chains, label):
    checker = ConstraintChecker()
    tp = tn = fp = fn = 0
    errors = []
    for c in chains:
        detected, vtype = checker.check_chain(c["chain_text"])
        violated = c["ground_truth"] == "YES"
        if violated and detected:
            tp += 1
        elif not violated and not detected:
            tn += 1
        elif not violated and detected:
            fp += 1
            errors.append(f"FP: {c['chain_id']} -> {vtype} (truth NO)")
        else:
            fn += 1
            errors.append(f"FN: {c['chain_id']} (truth YES / {c['violation_type']})")

    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0

    print(f"\n{'='*60}\n{label}\n{'='*60}")
    print(f"TP={tp} TN={tn} FP={fp} FN={fn}")
    print(f"Precision={p:.3f} Recall={r:.3f} F1={f1:.3f}")
    for e in errors:
        print(f"  {e}")
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn,
            "precision": p, "recall": r, "f1": f1}


if __name__ == "__main__":
    base = "/home/user/DITTO-V5.4-OLAT/experiment/chains"
    dev = load_chains(f"{base}/development_set.jsonl")
    val = load_chains(f"{base}/validation_set.jsonl")

    results = {
        "dev": evaluate(dev, "DEVELOPMENT SET"),
        "val": evaluate(val, "VALIDATION SET"),
    }
    with open("cycle_final_output.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved -> cycle_final_output.json")
