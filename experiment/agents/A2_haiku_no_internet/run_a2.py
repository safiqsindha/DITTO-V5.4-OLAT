#!/usr/bin/env python3
"""
A2 Agent: Haiku (claude-3-5-haiku-20241022), No Internet Access
Builds a symbolic checker for Pokemon constraint chains using iterative refinement.
"""

import json
import re
from pathlib import Path
from anthropic import Anthropic

client = Anthropic()

# Configuration
MODEL = "claude-3-5-haiku-20241022"
INTERNET_ACCESS = False
DEV_SET_PATH = Path("/home/user/DITTO-V5.4-OLAT/experiment/chains/development_set.jsonl")
VAL_SET_PATH = Path("/home/user/DITTO-V5.4-OLAT/experiment/chains/validation_set.jsonl")
WORKSPACE = Path("/home/user/DITTO-V5.4-OLAT/experiment/agents/A2_haiku_no_internet")

def load_chains(path):
    """Load chains from JSONL file."""
    chains = []
    with open(path) as f:
        for line in f:
            chains.append(json.loads(line))
    return chains

def count_violations(text):
    """Extract violation counts from response text."""
    matches = re.findall(r'(\w+)\s*:\s*(\d+)\s*(?:violation|detected)', text, re.IGNORECASE)
    return {k.lower(): int(v) for k, v in matches}

def format_dev_chains_for_analysis():
    """Format dev chains for the agent to analyze."""
    chains = load_chains(DEV_SET_PATH)
    formatted = []
    for i, chain in enumerate(chains, 1):
        formatted.append(f"Chain {i}: {chain['chain_id']}\nGround truth: {chain['ground_truth']}\nContent:\n{chain['chain_text']}\n")
    return "\n---\n".join(formatted)

def run_agent():
    """Run the Haiku agent with iterative refinement."""
    print(f"Starting A2 (Haiku, no internet) agent...")
    print(f"Model: {MODEL}")
    print(f"Internet access: {INTERNET_ACCESS}\n")

    conversation_history = []
    cycle = 0

    # Initial task
    system_prompt = """You are an expert at analyzing Pokemon Showdown battle constraint violations.
Your task is to build a symbolic constraint checker by analyzing example chains and identifying violation patterns.

You will work iteratively:
1. First, analyze provided development chains to understand violation patterns
2. Propose detection rules based on patterns you observe
3. I will test your rules and report results
4. You will refine rules based on feedback

Focus on precision (avoid false positives) and progressively improve recall.
Rules should detect physical impossibilities in the battle state.
"""

    dev_chains_text = format_dev_chains_for_analysis()

    initial_message = f"""Here are 30 development chains (15 intact, 15 violated) for you to analyze.

{dev_chains_text}

Please analyze these chains and identify the main violation patterns you see. For each pattern, propose a detection rule in Python that can check for it. Start with the clearest, highest-confidence patterns first.

Output your rules as a Python class method for each rule, following this format:
```python
def detect_rule_name(self, chain_dict):
    # Your detection logic
    return violation_detected  # boolean
```

Focus on rules that have zero false positives (never trigger on intact chains)."""

    conversation_history.append({
        "role": "user",
        "content": initial_message
    })

    print("Sending initial analysis request to Haiku...")
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=conversation_history
    )

    initial_response = response.content[0].text
    conversation_history.append({
        "role": "assistant",
        "content": initial_response
    })

    cycle += 1
    print(f"\nCycle {cycle} Response:\n{initial_response[:500]}...\n")

    # Save cycle output
    with open(WORKSPACE / f"cycle_{cycle}_output.json", "w") as f:
        json.dump({
            "cycle": cycle,
            "response_length": len(initial_response),
            "preview": initial_response[:200]
        }, f)

    # Iterative refinement loop (max 3 cycles for Haiku given context limits)
    for refine_cycle in range(2, 4):
        refinement_prompt = f"""Good start. Now let's refine these rules.

I will test your proposed rules on the development set and report which chains they correctly identify.

For this iteration:
1. Review the rules you proposed
2. Identify any potential issues (false positives on intact chains, false negatives on violated chains)
3. Refine the rules to improve them
4. Propose any new rules based on violation patterns you see that your current rules miss

Be conservative: it's better to have fewer high-confidence rules than many uncertain ones."""

        conversation_history.append({
            "role": "user",
            "content": refinement_prompt
        })

        print(f"Sending refinement request {refine_cycle - 1}...")
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=conversation_history
        )

        refine_response = response.content[0].text
        conversation_history.append({
            "role": "assistant",
            "content": refine_response
        })

        cycle = refine_cycle
        print(f"\nCycle {cycle} Response:\n{refine_response[:500]}...\n")

        # Save cycle output
        with open(WORKSPACE / f"cycle_{cycle}_output.json", "w") as f:
            json.dump({
                "cycle": cycle,
                "response_length": len(refine_response),
                "preview": refine_response[:200]
            }, f)

        # Check if agent wants to stop
        if "stable" in refine_response.lower() or "no further" in refine_response.lower():
            print(f"Agent indicates stability at cycle {cycle}")
            break

    print(f"\nA2 agent completed {cycle} cycles")

    # Extract final rules from conversation
    final_rules_prompt = """Now extract all your final detection rules into a single code block.
Format as a Python class with methods like `detect_violation_type(self, chain_dict)` for each violation type.
Make sure the code is valid Python and can be executed."""

    conversation_history.append({
        "role": "user",
        "content": final_rules_prompt
    })

    print("Extracting final rules...")
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=conversation_history
    )

    rules_response = response.content[0].text

    # Try to extract Python code from response
    code_match = re.search(r'```python\n(.*?)\n```', rules_response, re.DOTALL)
    if code_match:
        final_code = code_match.group(1)
    else:
        # Fallback: extract anything that looks like Python
        final_code = rules_response

    # Save final checker
    with open(WORKSPACE / "checker.py", "w") as f:
        f.write(final_code)

    print(f"Final checker saved to {WORKSPACE / 'checker.py'}")

    return conversation_history, final_code

if __name__ == "__main__":
    history, code = run_agent()
    print("\n✓ A2 agent run complete")
