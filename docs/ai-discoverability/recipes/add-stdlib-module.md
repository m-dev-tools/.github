---
kind: ai-discoverability-recipe
schema_version: "1"
status: stub
primary: tool:m-stdlib
---

# Recipe: Add An m-stdlib Module Or API

Use this recipe when a user asks an AI agent to add runtime library
functionality to `m-stdlib`.

## Intended Flow

1. Read `m-stdlib` README and local agent instructions.
2. Check `dist/stdlib-manifest.json` for existing APIs.
3. If the API is absent, add tests first.
4. Implement the STD* routine or label.
5. Regenerate the stdlib manifest.
6. Verify local tests and manifest drift checks.
7. Ensure the org catalog can summarize the new module/API.

## Stub Status

This recipe is a placeholder. Fill in exact repo-local commands during Phase 5.

