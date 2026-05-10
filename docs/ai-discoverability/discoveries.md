---
kind: ai-discoverability-discovery-log
schema_version: "1"
---

# Discoveries

Use this file to record facts, gaps, mismatches, and design friction discovered
while implementing AI discoverability.

Discoveries are not automatically tasks. If a discovery requires work, create a
linked `REM-` item in [`remediation-backlog.md`](remediation-backlog.md).

## Discovery Index

| ID | Date | Repo | Impact | Summary | Next Action |
|---|---|---|---|---|---|
| DISC-001 | 2026-05-10 | .github | non-blocking | `tools.json` existed before this tracking scaffold and already had a discovery protocol | none |

## DISC-001: Existing Catalog Already Had Discovery Protocol

- Date: 2026-05-10
- Found during: tracking scaffold
- Repo: `.github`
- Impact: non-blocking
- Summary: `.github/profile/tools.json` already included a `discovery_protocol`; it was strengthened rather than duplicated.
- Evidence: `tools.json.discovery_protocol`
- Next action: none

## New Discovery Template

```md
## DISC-000: Short title

- Date: YYYY-MM-DD
- Found during: AI-000
- Repo:
- Impact: blocking | non-blocking | informational
- Summary:
- Evidence:
- Next action: REM-000 | ADR-000 | none
```

