---
kind: ai-discoverability-tracking-guide
schema_version: "1"
status_values: [todo, doing, blocked, review, done, deferred, superseded]
canonical_tracker: implementation-tracker.md
---

# How To Track AI Discoverability Work

This file explains how humans and AI agents should use the tracking system in
this directory. The project is cross-repo by nature: implementing it will
surface gaps, stale docs, missing metadata, and refactoring needs across the
`m-dev-tools` suite. The tracking system exists so those discoveries improve
the plan without derailing it.

## First Read Order

When starting a work session, read these files in order:

1. [`README.md`](README.md) for the directory map.
2. [`roadmap.md`](roadmap.md) for current phase and priorities.
3. [`implementation-tracker.md`](implementation-tracker.md) for active tasks.
4. [`repo-inventory.md`](repo-inventory.md) when the task touches a repo.
5. [`discoveries.md`](discoveries.md) and
   [`remediation-backlog.md`](remediation-backlog.md) for known caveats.

For architecture background, read
[`../AI-discoverability-guide.md`](../AI-discoverability-guide.md).

## Core Rule

Keep one canonical implementation task in
[`implementation-tracker.md`](implementation-tracker.md). Use the other files to
explain context, decisions, discoveries, and follow-up work.

Do not hide work only in chat, issues, or commit messages. If it changes the AI
discoverability project, put it in this directory.

## Status Values

Use only these statuses in tracking tables:

| Status | Meaning |
|---|---|
| `todo` | Not started |
| `doing` | Actively in progress |
| `blocked` | Cannot proceed until another task, decision, or external dependency is resolved |
| `review` | Implemented and waiting for review or validation |
| `done` | Complete and verified |
| `deferred` | Valid work, intentionally postponed |
| `superseded` | Replaced by a newer task or decision |

Avoid ambiguous phrases such as "mostly done", "WIP-ish", or "probably fine".

## Stable IDs

Use these ID families:

| Prefix | File | Purpose |
|---|---|---|
| `AI-` | `implementation-tracker.md` | Main implementation work |
| `DISC-` | `discoveries.md` | Findings discovered during work |
| `REM-` | `remediation-backlog.md` | Concrete remediation tasks |
| `ADR-` | `decisions.md` | Durable decisions |
| `SCH-` | `schema-changelog.md` | Schema or metadata contract changes |

IDs are never reused. If a task is replaced, mark it `superseded` and link to
the new ID.

## Work Session Protocol

At the start of a work session:

1. Pick or create one `AI-` task.
2. Set its status to `doing`.
3. Confirm the task has an owner repo, outputs, and verification command.
4. Check whether it is blocked by any `REM-`, `DISC-`, or `ADR-` entry.

During the work session:

1. Log new facts in `discoveries.md`.
2. Create `REM-` items for concrete follow-up work.
3. Add an `ADR-` if the work changes architecture or policy.
4. Add an `SCH-` entry if schemas, stable IDs, or catalog contracts change.
5. Keep `implementation-tracker.md` updated.

At the end of a work session:

1. Update task status.
2. Record outputs produced.
3. Record verification run or explain why verification was not run.
4. Add any next task IDs.

## Discovery Triage

When implementation reveals a gap, use this decision flow:

1. If it blocks the current phase, create a `REM-` item and link it from the
   active `AI-` task.
2. If it does not block the current phase, log it in
   `remediation-backlog.md` and keep moving.
3. If it changes the design, record an `ADR-`.
4. If it changes metadata contracts, update `schema-changelog.md`.

Discovery entry template:

```md
## DISC-000: Short title

- Date: YYYY-MM-DD
- Found during: AI-000
- Repo: repo-name
- Impact: blocking | non-blocking | informational
- Summary:
- Evidence:
- Next action: REM-000 | ADR-000 | none
```

Remediation row template:

```md
| REM-000 | DISC-000 | repo-name | Problem | Proposed fix | todo | AI-000 |
```

## Main Task Table Rules

Every row in `implementation-tracker.md` should include:

- `ID`
- `Phase`
- `Workstream`
- `Task`
- `Owner Repo`
- `Status`
- `Blocks`
- `Outputs`
- `Verification`

The `Verification` column should name a command, schema validation, generated
file check, or explicit manual review.

Good:

```md
| AI-010 | 2 | m-cli | Add `m capabilities --json` | m-cli | todo | | JSON command metadata | pytest + schema fixture |
```

Weak:

```md
| AI-010 | 2 | m-cli | Improve CLI docs | m-cli | WIP | | better docs | check it |
```

## Repo Maturity Levels

Use these levels in `repo-inventory.md`:

| Level | Meaning |
|---|---|
| `M0` | Prose only |
| `M1` | Has local AI instructions |
| `M2` | Has machine-readable metadata |
| `M3` | Metadata is schema-validated |
| `M4` | Org catalog generated from metadata |
| `M5` | CI prevents metadata drift |

## AI-Friendly Writing Rules

- Prefer tables with stable columns.
- Prefer controlled statuses.
- Link IDs explicitly.
- Keep one fact per row.
- Put verification commands in backticks.
- Record unknowns as unknowns.
- Do not invent missing APIs, commands, or metadata. Create a discovery or
  remediation item instead.

## Relationship To Root Catalog

The tracking system manages the project that produces and maintains:

- `.github/profile/llms.txt`,
- `.github/profile/tools.json`,
- `.github/profile/tools.schema.json`,
- future generated indexes such as `AI-INDEX.md`.

The root catalog is for AI consumption. This directory is for project
management and implementation history.

