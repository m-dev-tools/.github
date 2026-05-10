---
kind: ai-discoverability-decision-log
schema_version: "1"
---

# Decisions

Use this file as a lightweight ADR log. Add an entry whenever the project makes
a durable architecture, schema, ownership, or workflow decision.

## Decision Index

| ID | Date | Title | Status | Related |
|---|---|---|---|---|
| ADR-001 | 2026-05-10 | Use `.github/profile/tools.json` as the org-level machine-readable catalog | accepted | AI-001 |
| ADR-002 | 2026-05-10 | Use repo-local metadata as source of truth and generate the org catalog | proposed | AI-013 |

## ADR-001: Use `tools.json` As The Org Catalog

- Date: 2026-05-10
- Status: accepted
- Related: AI-001

### Context

AI agents need a single machine-readable entrypoint that maps user intent to
repos, commands, manifests, and workflows.

### Decision

Use `.github/profile/tools.json` as the org-level machine-readable catalog.
Keep `.github/profile/README.md` as the human overview and
`.github/profile/llms.txt` as the compact AI reading order.

### Consequences

- `tools.json` must remain parseable and schema-validated.
- Detailed inventory should eventually be generated from repo-local metadata.

## ADR-002: Generate The Org Catalog From Repo-Local Metadata

- Date: 2026-05-10
- Status: proposed
- Related: AI-013

### Context

As `m-stdlib` expands and `m-cli` gains commands, hand-maintaining all details
in the org catalog will drift.

### Decision

Treat repo-local manifests and capability JSON as source of truth. Generate the
org catalog from those inputs.

### Consequences

- Each repo needs a local metadata contract.
- The `.github` repo needs a catalog generator and validation checks.

## New Decision Template

```md
## ADR-000: Title

- Date: YYYY-MM-DD
- Status: proposed | accepted | superseded
- Related: AI-000, DISC-000, REM-000

### Context

### Decision

### Consequences
```

