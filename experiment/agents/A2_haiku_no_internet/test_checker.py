#!/usr/bin/env python3
"""Test A2 checker on development and validation sets."""

import json
from pathlib import Path
from checker import ConstraintChecker

def load_chains(path):
    chains = []
    with open(path) as f:
        for line in f:
            chains.append(json.loads(line))
    return chains

def test_checker():
    checker = ConstraintChecker()
    dev_chains = load_chains("/home/user/DITTO-V5.4-OLAT/experiment/chains/development_set.jsonl")
    val_chains = load_chains("/home/user/DITTO-V5.4-OLAT/experiment/chains/validation_set.jsonl")

    print("=" * 60)
    print("DEVELOPMENT SET RESULTS")
    print("=" * 60)

    dev_tp, dev_tn, dev_fp, dev_fn = 0, 0, 0, 0
    dev_errors = []

    for chain in dev_chains:
        detected, violation_type = checker.check_chain(chain["chain_text"])
        is_violated = chain["ground_truth"] == "YES"

        if is_violated and detected:
            dev_tp += 1
        elif not is_violated and not detected:
            dev_tn += 1
        elif not is_violated and detected:
            dev_fp += 1
            dev_errors.append(f"FP: {chain['chain_id']} - predicted YES (type: {violation_type}), ground truth: NO")
        elif is_violated and not detected:
            dev_fn += 1
            dev_errors.append(f"FN: {chain['chain_id']} - predicted NO, ground truth: YES ({chain['violation_type']})")

    dev_precision = dev_tp / (dev_tp + dev_fp) if (dev_tp + dev_fp) > 0 else 0.0
    dev_recall = dev_tp / (dev_tp + dev_fn) if (dev_tp + dev_fn) > 0 else 0.0
    dev_f1 = 2 * (dev_precision * dev_recall) / (dev_precision + dev_recall) if (dev_precision + dev_recall) > 0 else 0.0

    print(f"TP: {dev_tp}, TN: {dev_tn}, FP: {dev_fp}, FN: {dev_fn}")
    print(f"Precision: {dev_precision:.3f}, Recall: {dev_recall:.3f}, F1: {dev_f1:.3f}")
    if dev_errors:
        print(f"\nErrors:")
        for err in dev_errors:
            print(f"  {err}")

    print("\n" + "=" * 60)
    print("VALIDATION SET RESULTS")
    print("=" * 60)

    val_tp, val_tn, val_fp, val_fn = 0, 0, 0, 0
    val_errors = []

    for chain in val_chains:
        detected, violation_type = checker.check_chain(chain["chain_text"])
        is_violated = chain["ground_truth"] == "YES"

        if is_violated and detected:
            val_tp += 1
        elif not is_violated and not detected:
            val_tn += 1
        elif not is_violated and detected:
            val_fp += 1
            val_errors.append(f"FP: {chain['chain_id']} - predicted YES, ground truth: NO")
        elif is_violated and not detected:
            val_fn += 1
            val_errors.append(f"FN: {chain['chain_id']} - predicted NO, ground truth: YES ({chain['violation_type']})")

    val_precision = val_tp / (val_tp + val_fp) if (val_tp + val_fp) > 0 else 0.0
    val_recall = val_tp / (val_tp + val_fn) if (val_tp + val_fn) > 0 else 0.0
    val_f1 = 2 * (val_precision * val_recall) / (val_precision + val_recall) if (val_precision + val_recall) > 0 else 0.0

    print(f"TP: {val_tp}, TN: {val_tn}, FP: {val_fp}, FN: {val_fn}")
    print(f"Precision: {val_precision:.3f}, Recall: {val_recall:.3f}, F1: {val_f1:.3f}")
    if val_errors:
        print(f"\nErrors:")
        for err in val_errors[:10]:  # Show first 10 errors
            print(f"  {err}")
        if len(val_errors) > 10:
            print(f"  ... and {len(val_errors) - 10} more")

    return {
        "dev": {"tp": dev_tp, "tn": dev_tn, "fp": dev_fp, "fn": dev_fn, "precision": dev_precision, "recall": dev_recall, "f1": dev_f1},
        "val": {"tp": val_tp, "tn": val_tn, "fp": val_fp, "fn": val_fn, "precision": val_precision, "recall": val_recall, "f1": val_f1}
    }

if __name__ == "__main__":
    results = test_checker()
    with open("/home/user/DITTO-V5.4-OLAT/experiment/agents/A2_haiku_no_internet/cycle_3_output.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to cycle_3_output.json")
