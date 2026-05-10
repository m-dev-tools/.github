---
kind: ai-discoverability-index
schema_version: "1"
status: active
canonical_tracker: implementation-tracker.md
---

# AI Discoverability Project

This directory tracks the cross-repo project to make the `m-dev-tools`
organization maximally discoverable, computable, and usable by AI coding
agents.

Start here when planning or reviewing the AI discoverability work. For the full
architecture, read [`../AI-discoverability-guide.md`](../AI-discoverability-guide.md).
For day-to-day tracking rules, read [`how-to-track.md`](how-to-track.md).

## Tracking Files

| File | Purpose | Update Cadence |
|---|---|---|
| [`how-to-track.md`](how-to-track.md) | Operating instructions for humans and AI agents using this tracking system | Whenever the process changes |
| [`roadmap.md`](roadmap.md) | Phase-level plan and exit criteria | At phase boundaries |
| [`implementation-tracker.md`](implementation-tracker.md) | Canonical task tracker for implementation work | Every work session |
| [`repo-inventory.md`](repo-inventory.md) | Per-repo metadata maturity and gaps | After each repo audit |
| [`decisions.md`](decisions.md) | Lightweight ADR log for durable choices | Whenever architecture changes |
| [`discoveries.md`](discoveries.md) | Findings made during implementation | Whenever new facts or gaps are found |
| [`remediation-backlog.md`](remediation-backlog.md) | Follow-up fixes discovered while implementing | Whenever discoveries imply work |
| [`schema-changelog.md`](schema-changelog.md) | Changes to metadata contracts and schemas | Whenever schemas/catalog contracts change |
| [`release-checklist.md`](release-checklist.md) | Phase completion checklist | Before closing a phase |

## Recipes

Workflow recipes live in [`recipes/`](recipes/). These are executable,
AI-friendly guides for common work:

- new application with TDD/CI,
- adding an `m-stdlib` module,
- adding an `m-cli` command,
- adding a lint rule,
- adding editor support.

## Status Values

Use only these task statuses:

```text
todo
doing
blocked
review
done
deferred
superseded
```

## ID Prefixes

Use stable IDs so work can be cross-linked.

| Prefix | Meaning | Example |
|---|---|---|
| `AI-` | Main implementation task | `AI-001` |
| `DISC-` | Discovery or finding | `DISC-001` |
| `REM-` | Remediation backlog item | `REM-001` |
| `ADR-` | Architecture decision record | `ADR-001` |
| `SCH-` | Schema/catalog contract change | `SCH-001` |

