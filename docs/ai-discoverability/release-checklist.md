---
kind: ai-discoverability-release-checklist
schema_version: "1"
---

# Release Checklist

Use this checklist before closing a phase or publishing a visible update to the
AI discoverability system.

## Phase Completion Checklist

| Check | Status | Notes |
|---|---|---|
| Roadmap phase exit criteria reviewed | todo | |
| `implementation-tracker.md` statuses updated | todo | |
| Blocking discoveries triaged | todo | |
| Required remediation items completed or deferred | todo | |
| Decisions recorded in `decisions.md` | todo | |
| Schema changes recorded in `schema-changelog.md` | todo | |
| `tools.json` parses | todo | |
| `tools.schema.json` parses | todo | |
| Catalog validation command passes | todo | |
| Root `llms.txt` still points to current files | todo | |
| README links still work | todo | |

## Validation Commands

Run these from the repository root when available:

```bash
python3 -m json.tool .github/profile/tools.json >/tmp/tools-json-check
python3 -m json.tool .github/profile/tools.schema.json >/tmp/tools-schema-check
```

Future commands:

```bash
make validate-catalog
make catalog
git diff --exit-code .github/profile/tools.json
```

