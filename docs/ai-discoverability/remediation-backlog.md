---
kind: ai-discoverability-remediation-backlog
schema_version: "1"
status_values: [todo, doing, blocked, review, done, deferred, superseded]
---

# Remediation Backlog

Use this file for concrete follow-up work discovered while implementing the AI
discoverability project.

Remediation items differ from main `AI-` tasks: they usually originate from a
discovery and may be done now, deferred, or promoted into the main tracker.

## Backlog

| ID | Source | Repo | Problem | Proposed Fix | Status | Required For |
|---|---|---|---|---|---|---|
| REM-001 | DISC-001 | .github | No full JSON Schema validation command exists yet | Add `validate-tools-json.py` and `make validate-catalog` | todo | AI-006 AI-007 |

## How To Use

1. Create a `REM-` row when a discovery implies concrete work.
2. Set status to `todo` unless the work is immediately in progress.
3. Link the originating `DISC-` ID.
4. Link the `AI-` task or phase that requires the remediation.
5. Promote to `implementation-tracker.md` if it becomes core phase work.

