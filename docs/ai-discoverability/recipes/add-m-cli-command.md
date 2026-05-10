---
kind: ai-discoverability-recipe
schema_version: "1"
status: stub
primary: tool:m-cli
---

# Recipe: Add An m-cli Command

Use this recipe when a user asks an AI agent to add a new `m` subcommand.

## Intended Flow

1. Read `m-cli` README and `CLAUDE.md`.
2. Check existing `m` subcommands in `tools.json`.
3. Add command tests first.
4. Implement the command using existing m-cli patterns.
5. Expose command metadata through future `m capabilities --json`.
6. Update catalog generation inputs.
7. Verify with m-cli test, lint, type, and catalog checks.

## Stub Status

This recipe is a placeholder. Fill in exact repo-local commands during Phase 5.

