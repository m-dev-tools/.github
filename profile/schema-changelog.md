# Schema Changelog

Tracks changes to `profile/tools.schema.json` and
`profile/task_index.schema.json` (the routing-layer schemas).

Conventions:

- **`schema_compat`** (integer) bumps only on **breaking** (non-additive)
  changes. Every bump adds a row below.
- **`schema_version`** (semver-style string) bumps on every change.
- **Additive changes** (new optional fields, new enum values, new
  `propertyName` patterns) keep `schema_compat`; bump `schema_version`'s
  minor or patch only.
- **Breaking changes** (removed fields, renamed fields, tightened
  patterns that reject previously-accepted data, new required fields)
  bump `schema_compat` and `schema_version`'s major.

The contract: a consumer that validates against `schema_compat: N` can
read any document with `schema_compat <= N`. Bumping `schema_compat`
without a changelog row is forbidden.

---

## v1.0 — 2026-05-10 — initial strict schema (P1-A)

- **Schemas affected:**
  `profile/tools.schema.json`, `profile/task_index.schema.json` (new).
- **`schema_compat`:** *(unversioned)* → **1**
- **`schema_version`:** `"1"` (string) → `"1.0"` (semver-style string)
- **Type:** non-additive — the prior schema accepted forms that this
  one rejects. Documented as the first compat-tracked version
  (`schema_compat: 1`); future bumps will increment from here.

**What changed:**

- `additionalProperties: false` at every object level in both schemas
  (previously: `true` at every level — the prior schema was effectively
  advisory).
- Hoisted a single `typedID` regex into `$defs`
  (`^(tool|cmd|module|rule|doc|data|workflow|task|recipe):[a-z0-9_-]+(#[A-Za-z0-9._-]+)?$`)
  and referenced it everywhere a typed identifier appears
  (`tools.*.consumes`, `tools.*.consumed_by`, `workflow.*.steps[].tool`/`tools`,
  `task_index.categories.*.*.primary`/`see_also`, etc.). Strings that
  *look* like references but don't match the grammar now fail
  validation.
- Split `schema_compat: integer` (breaking-change-only) from
  `schema_version: string` (display) per parent plan §4.5.
- **Dropped** `task_index` from `tools.schema.json`. Lives in its own
  file (`task_index.json`) validated by `task_index.schema.json`. The
  catalog generator (Phase-1 Track B) merges them at build time.
- Per-tool entries lost their inlined-facts blocks:
  `subcommands` → `commands_url`; `modules` → `manifest_url`;
  `machine_readable.*` → individual `*_url` fields.
  Inlined data is *forbidden* by the new shape — drift-prone, and the
  facts live in each repo's `dist/repo.meta.json.exposes.*` anyway.
- Per-tool entries gained required fields: `id` (self-typed-ID),
  `agent_instructions`, `verified_on`. Optional `status` enum
  (`active` / `archived` / `deprecated`).
- `propertyNames` constraints on `tools` (keys must match
  `^[a-z0-9_-]+$`) and on `task_index.categories.*.*` (keys must match
  `^[a-z][a-z0-9_]*$`).
- `patternProperties` on tools entries: `*_url` (URI) and `*_count`
  (integer) accepted by pattern, so the generator can add any payload
  pointer without schema changes.

**Data migrations performed in the same PR:**

- `tools.json`: 368 → 224 lines (39% smaller). Every per-tool entry
  rewritten to summary shape. `consumes`/`consumed_by` arrays
  re-emitted with `tool:` prefixes.
- `task_index.json` (new): extracted from the prior embedded
  `tools.json.task_index`. All 59 intent rows' `primary`/`see_also`
  references migrated to the strict typedID grammar
  (`m-cli#new` → `cmd:m-cli#new`, `m-stdlib#STDJSON` →
  `module:m-stdlib#STDJSON`, etc.). 5 categories, 59 rows.
- Workflow steps: `tool`/`tools` references migrated to typed IDs.

**Verification at landing time:**

- Both schemas validate as JSON Schema 2020-12.
- `tools.json` and `task_index.json` both validate against their
  respective schemas.
- `make phase0-smoke` continues to return PASS — the manifests it
  fetches are unchanged; only the org catalog representation moved.

---

## Future entries

Add a new section above this line on every `schema_compat` bump.
Template:

```markdown
## vMAJOR.MINOR — YYYY-MM-DD — short title

- **Schemas affected:** …
- **`schema_compat`:** N → N+1
- **`schema_version`:** A.B → A+1.0
- **Type:** breaking | additive
- **What changed:** …
- **Migration required:** …
```
