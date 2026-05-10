---
kind: ai-discoverability-schema-changelog
schema_version: "1"
---

# Schema Changelog

Use this file to track changes to machine-readable contracts:

- `.github/profile/tools.json`,
- `.github/profile/tools.schema.json`,
- future repo-local `tool.meta.json` files,
- generated catalog outputs,
- stable ID formats,
- manifest contracts consumed by the org catalog.

## Changelog

| ID | Date | Contract | Change | Compatibility | Related |
|---|---|---|---|---|---|
| SCH-001 | 2026-05-10 | `tools.json` | Added `$schema` pointer to `tools.schema.json` | additive | AI-005 |
| SCH-002 | 2026-05-10 | `tools.schema.json` | Added initial schema for required top-level catalog structure | additive | AI-005 |

## Compatibility Values

| Value | Meaning |
|---|---|
| additive | Existing consumers should continue working |
| breaking | Existing consumers must update |
| clarification | Contract meaning clarified without structural change |
| deprecated | Old field or shape remains but should be phased out |

## New Entry Template

```md
| SCH-000 | YYYY-MM-DD | contract | change | additive | AI-000 |
```

