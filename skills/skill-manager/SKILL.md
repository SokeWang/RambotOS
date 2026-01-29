---
name: skill-manager
description: The Meta-Skill that allows RAMBOT to create, manage, and evolve new capabilities.
allowed-tools: [propose_skill, acquire_skill, enhance_skill]
---

# Skill Manager (Meta-Skill)

This is RAMBOT's core evolutionary engine. It enables the agent to write its own tools, creating a self-improving feedback loop.

## Capabilities

1.  **Skill Acquisition**: Creates entirely new skill packages (folders with logic + instructions).
2.  **Skill Enhancement**: Updates existing packages with new features while preserving old ones.

## Instructions

### When to use
*   Use this skill **IMMEDIATELY** when the user asks for something you cannot currently do.
*   **DO NOT** say "I cannot do that." Say "I will acquire that skill."
*   **ALWAYS** check if an existing tool can be extended before proposing a new one.

### Workflow
1.  **Analysis**: Call `propose_skill(requirement="...")` first. This will check all existing tools and skills to see if any can be enhanced.
2.  **Approval**: The system will **FORCE INTERRUPT** here. Wait for the user to say "Yes".
3.  **Execution**:
    *   If the proposal says "ACQUIRE": Call `acquire_skill`.
    *   If the proposal says "ENHANCE": Call `enhance_skill`.

## Examples

*   **User**: "Check the weather." (And you don't have a weather tool)
    *   **Action**: `propose_skill(requirement="Check weather in cities")`
*   **User**: "Add history to the crypto tool." (And you have `crypto-price`)
    *   **Action**: `propose_skill(requirement="Add historical price lookup to crypto-price")`
