#!/usr/bin/env python3
"""Debug specific chains."""

import json
from checker import ConstraintChecker

def load_chains():
    chains = []
    with open("/home/user/DITTO-V5.4-OLAT/experiment/chains/development_set.jsonl") as f:
        for line in f:
            chains.append(json.loads(line))
    return chains

# Find the FP chains
chains = load_chains()
fp_chains = ["gen9ou-2348078225_p1", "gen9ou-2276761872_p1"]

for chain_id in fp_chains:
    chain = next((c for c in chains if c["chain_id"] == chain_id), None)
    if chain:
        print(f"\n=== {chain_id} ===")
        print(f"Ground truth: {chain['ground_truth']}")
        print(f"Content:\n{chain['chain_text'][:500]}...")

        # Debug each rule
        checker = ConstraintChecker()
        steps = checker._parse_chain(chain['chain_text'])

        print(f"Steps: {len(steps)}")

        # Check each rule manually
        print(f"  HP 0→positive: {checker._detect_hp_resurrection_zero_to_positive(steps)}")
        print(f"  HP permanent+positive: {checker._detect_hp_resurrection_permanent_faint(steps)}")
        print(f"  PP monotone: {checker._detect_pp_monotone_violation(steps)}")
        print(f"  Causal incoherence: {checker._detect_causal_incoherence(steps)}")

        detected, violation_type = checker.check_chain(chain['chain_text'])
        print(f"Overall: Detected: {detected}, Type: {violation_type}")
