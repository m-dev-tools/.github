---
kind: ai-discoverability-recipe
schema_version: "1"
status: stub
primary: workflow:tdd_inner_loop
---

# Recipe: New M App With TDD And CI

Use this recipe when a user asks an AI agent to create a new M application using
the m-dev-tools stack.

## Intended Flow

1. Read `.github/profile/llms.txt`.
2. Resolve `workflow:tdd_inner_loop` in `.github/profile/tools.json`.
3. Use `m-cli` as the primary tool.
4. Scaffold with `m new`.
5. Write a failing test first.
6. Implement using `m-stdlib` primitives.
7. Verify with `m test`, `m fmt --check`, `m lint`, and `m coverage`.
8. Add CI with `m ci init`.

## Stub Status

This recipe is a placeholder. Fill in exact commands and examples during Phase
5.

