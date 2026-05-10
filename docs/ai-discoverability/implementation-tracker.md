---
kind: ai-discoverability-implementation-tracker
schema_version: "1"
status_values: [todo, doing, blocked, review, done, deferred, superseded]
---

# Implementation Tracker

This is the canonical task tracker for the AI discoverability project. Update
this file during every implementation session.

## Task Table

| ID | Phase | Workstream | Task | Owner Repo | Status | Blocks | Outputs | Verification |
|---|---|---|---|---|---|---|---|---|
| AI-001 | 1 | Catalog | Add typed stable IDs to top-level tools | .github | todo | | `tools.json` IDs | `make validate-catalog` |
| AI-002 | 1 | Catalog | Add typed stable IDs to m-cli subcommands | .github | todo | AI-001 | `cmd:m-cli#...` IDs | schema validation |
| AI-003 | 1 | Catalog | Add typed stable IDs to m-stdlib module summaries | .github | todo | AI-001 | `module:m-stdlib#...` IDs | schema validation |
| AI-004 | 1 | Catalog | Migrate `task_index.primary` and `see_also` to typed IDs | .github | todo | AI-001 AI-002 AI-003 | typed references | catalog resolver test |
| AI-005 | 1 | Schema | Tighten `tools.schema.json` for stable IDs | .github | todo | AI-001 | schema ID definitions | schema validation |
| AI-006 | 1 | Validation | Add catalog validation script | .github | todo | AI-005 | `validate-tools-json.py` | script exits 0 |
| AI-007 | 1 | Validation | Add catalog Makefile target | .github | todo | AI-006 | `make validate-catalog` | target exits 0 |
| AI-008 | 2 | Inventory | Audit all repos for AI instructions and metadata | .github | todo | | `repo-inventory.md` rows | manual review |
| AI-009 | 2 | Inventory | Assign maturity level M0-M5 to each repo | .github | todo | AI-008 | maturity table | manual review |
| AI-010 | 3 | m-cli | Add `m capabilities --json` design task | m-cli | todo | AI-008 | command metadata contract | m-cli tests |
| AI-011 | 3 | m-cli | Add `m help --json` design task | m-cli | todo | AI-008 | command help JSON | m-cli tests |
| AI-012 | 3 | m-stdlib | Confirm stdlib manifest has agent-ready module/API summaries | m-stdlib | todo | AI-008 | manifest gap list | manifest validation |
| AI-013 | 4 | Catalog generation | Design `build-tools-json.py` inputs and outputs | .github | todo | AI-008 AI-010 AI-012 | generator design | ADR or design note |
| AI-014 | 5 | Recipes | Add new-app TDD/CI recipe | .github | todo | | recipe doc | recipe walkthrough |
| AI-015 | 5 | Recipes | Add add-stdlib-module recipe | .github | todo | AI-012 | recipe doc | recipe walkthrough |
| AI-016 | 5 | Recipes | Add add-lint-rule recipe | .github | todo | AI-010 | recipe doc | recipe walkthrough |
| AI-017 | 6 | CI | Add catalog validation CI | .github | todo | AI-006 AI-007 | CI workflow | CI passes |
| AI-018 | 1 | Tracking | Add required lifecycle and commit protocol instructions | .github | done | | `how-to-track.md` lifecycle rules | `make validate-ai-tracking` |
| AI-019 | 1 | Tracking | Add AI tracking validation script | .github | done | | `scripts/validate-tracking.py` | `make validate-ai-tracking` |
| AI-020 | 1 | Tracking | Add Makefile target for tracking and catalog validation | .github | done | AI-019 | `Makefile` target | `make validate-ai-tracking` |

## How To Add A Task

1. Use the next unused `AI-` ID.
2. Pick a phase from `roadmap.md`.
3. Set status to `todo`.
4. Name the owner repo.
5. Add concrete outputs and verification.
6. Link any blocking `AI-`, `REM-`, or `ADR-` IDs.
