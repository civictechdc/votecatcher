# Agent Self-Learning

VoteCatcher uses a hybrid self-learning loop. `AGENTS.md` stays concise, while durable project-specific lessons live in `docs/agents/`.

## When To Propose A Learning Update

At task end, propose a learning update when you discovered a durable project-specific rule, pitfall, command, convention, or stale instruction.

Use a strict filter.

Keep:
- Durable project knowledge likely useful across future sessions.
- Repeated pitfalls or commands that are easy to forget.
- Corrections to stale agent instructions.
- Team-specific conventions not obvious from code.

Skip:
- Task trivia.
- Temporary state.
- One-off debugging notes.
- Generic coding advice.
- Personal preferences that are not project conventions.

## Required Workflow

Before editing learning docs:

1. Ask the user first.
2. Create a separate branch named `agents/<short-topic>`.
3. Open a separate PR for the AGENTS/docs-agent update.
4. Do not mix self-learning changes into feature branches.

## Where Lessons Go

- `AGENTS.md` - only high-level routing and mandatory contracts.
- `docs/agents/*.md` - detailed agent-only guidance.
- `README.md` or `docs/development/*.md` - human-facing project behavior.
