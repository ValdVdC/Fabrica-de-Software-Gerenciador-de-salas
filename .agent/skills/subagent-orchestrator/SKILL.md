---
name: subagent-orchestrator
description: >-
  Patterns and protocols for delegating tasks to ephemeral subagents, managing subagent
  boundaries, isolating noisy contexts, and synthesizing structured outputs. Use when
  spawning multiple subagents, running parallel audits, or delegating heavy research.
---

# Subagent Orchestrator

Architectural patterns for multi-agent delegation, isolating noisy research context, and ensuring deterministic collaboration.

## 1. When to Delegate to a Subagent

- **Heavy Codebase Exploration**: When surveying multiple folders or unfamiliar modules where dozens of file reads would overwhelm the primary agent's context.
- **Adversarial Analysis**: When auditing a completed pull request from antagonistic viewpoints (e.g. `adversary-breaker`, `adversary-security`, `adversary-compliance`).
- **Parallel Independent Investigations**: When comparing alternate algorithmic strategies (e.g. sequential vs parallel C implementations) simultaneously.

## 2. Delegation Boundaries and Roles

- **Single Responsibility**: Each spawned subagent must receive a tightly bounded prompt with a single clear deliverable.
- **Model Selection**:
  - `flash` / `flash_lite`: Routine search, file reading, linting, syntax checking.
  - `pro` / `inherit`: Complex reasoning, algorithmic planning, dialectical debates.
- **Inherited vs Isolated Workspace**: Use `Workspace: 'inherit'` when inspecting existing files, or `'branch'` only when performing experimental refactors.

## 3. Strict Contract for Subagent Reports

To prevent context contamination when the subagent replies, instruct the subagent to adhere to this terse response schema:

```markdown
## Summary
- [1-2 sentences summarizing findings]

## Specific Findings
- `path/to/file.ext:line` - Description of issue or insight.

## Recommended Action
- Concrete next step for primary agent.
```

- Subagents must never return long narrative chit-chat or redundant pleasantries.
- The parent agent synthesizes findings directly without copy-pasting subagent logs.
