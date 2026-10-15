# GSD Core — Workspace Workflow Rules

<!-- GSD Core v1.13.0 — Ported for Antigravity from open-gsd/gsd-core -->

## GSD Workflow Enforcement

Before making file changes, start work through a GSD skill so planning artifacts and execution context stay in sync.

**Entry points:**
- `gsd-quick` — for small fixes, doc updates, and ad-hoc tasks
- `gsd-debug` — for investigation and bug fixing  
- `gsd-execute-phase` — for planned phase work
- `gsd-new-project` — to initialize a new project with GSD structure

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.

## GSD Phase Loop

Every milestone repeats this 5-step loop, one phase at a time:

1. **Discuss** — capture implementation decisions before anything is planned
2. **Plan** — research, decompose, and verify the plan fits a fresh context window
3. **Execute** — run plans in parallel waves; each executor starts with a clean context
4. **Verify** — walk through what was built; diagnose and fix before declaring done
5. **Ship** — create the PR, archive the phase, repeat for the next milestone

## Context Rot Prevention

- Run all heavy research, planning, and execution in **fresh-context subagents**
- Keep the main session lean — use it for coordination only
- When approaching context limit, checkpoint your work and start a fresh session

## Key GSD Skills Available

| Skill | Purpose |
|---|---|
| `gsd-new-project` | Initialize project with GSD structure |
| `gsd-plan-phase` | Research and plan a phase |
| `gsd-execute-phase` | Execute planned work |
| `gsd-verify-work` | Verify completed work |
| `gsd-ship` | Create PR and archive phase |
| `gsd-quick` | Small ad-hoc tasks |
| `gsd-debug` | Investigation and debugging |
| `gsd-review` | Code review |
| `gsd-health` | Project health check |
| `ralph-loop` | Iterative fresh-context task execution |
