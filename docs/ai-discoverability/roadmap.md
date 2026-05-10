---
kind: ai-discoverability-roadmap
schema_version: "1"
status: draft
---

# Roadmap

This file tracks the phase-level plan for the AI discoverability project. Keep
this strategic. Put day-to-day work in
[`implementation-tracker.md`](implementation-tracker.md).

## Phase Summary

| Phase | Name | Goal | Status | Exit Criteria |
|---|---|---|---|---|
| 0 | Completed foundation | Establish initial root catalog, schema, and AI entrypoint | done | `llms.txt`, `tools.json`, and `tools.schema.json` exist and parse |
| 1 | Catalog stabilization | Make the current manual catalog reliable and addressable | todo | Stable IDs exist and schema validates them |
| 2 | Repo inventory | Audit every repo for metadata maturity and missing contracts | todo | Every repo has an inventory row and maturity level |
| 3 | Self-describing repos | Move source-of-truth metadata into owning repos | todo | Core repos expose machine-readable metadata |
| 4 | Generated org catalog | Generate `tools.json` from repo-local metadata | todo | `make catalog` regenerates deterministic catalog output |
| 5 | Agent recipes | Make common AI workflows explicit and executable | todo | Recipes exist and link to commands, manifests, and checks |
| 6 | Drift-proofing and release | Add CI checks and release criteria | todo | CI catches stale metadata and schema violations |

## Current Phase

Current phase: **Phase 1: Catalog stabilization**

Primary focus:

- add typed stable IDs,
- validate IDs in schema,
- add catalog validation script,
- add a `make validate-catalog` target.

## Phase Detail Template

Use this template when expanding a phase.

```md
## Phase N: Name

- Goal:
- Starts when:
- Ends when:
- Primary files:
- Main tasks:
- Risks:
- Exit criteria:
```

