# Phase 1 Implementation Plan — Org Routing Layer

**Parent plan:** [`AI-discoverability-plan.md`](AI-discoverability-plan.md) §7
**Phase 1 goal:** The org-level catalog (`profile/tools.json`) is **generated**,
not hand-edited. Hand-curated routing (intent → typed ID) is split into its
own source file (`profile/task_index.json`). Schemas enforce additive
discipline. `llms.txt` is strict llmstxt.org form. `make catalog &&
make validate-catalog` is green and runs in CI.

**Phase 1 exit:** `make catalog && make validate-catalog` in `.github` is
green; `tools.json` no longer contains hand-maintained subcommand / module /
rule lists — those facts are pulled at build time from each tier-1 repo's
`dist/repo.meta.json` and the payloads they expose. The set of hand-edited
routing files is exactly: `task_index.json` (intent map), `llms.txt` (AI
doorway), `README.md` (human overview), the two schemas, and the build/
validate scripts.

---

## 1. Track Layout

Four tracks, all in the meta-repo (`.github`). One repo, mostly sequential —
unlike Phase 0, which fanned out across tier-1 repos.

```
┌──────────────────────────────────────────────┐
│ Track A — Schema + task_index split          │  (foundation; must finish first)
│ runs in .github                              │
└────────────────┬─────────────────────────────┘
                 │
        ┌────────┴───────┐
        ▼                ▼
┌──────────────┐  ┌──────────────────────────┐
│ Track B      │  │ Track C — llms.txt       │   (independent of A/B —
│ catalog gen  │  │ migration to             │    can run in parallel)
│ + validator  │  │ llmstxt.org form         │
└──────┬───────┘  └────────────┬─────────────┘
       │                       │
       └──────────┬────────────┘
                  ▼
┌──────────────────────────────────────────────┐
│ Track D — Make targets + CI wiring           │   (integrates B and C;
│ runs in .github                              │    Phase 1 exit lives here)
└──────────────────────────────────────────────┘
```

### Track index — callable names

| Track | Repo | Purpose | Blocked by | Stages |
|---|---|---|---|---|
| **A** | `.github` | Tighten `tools.schema.json`; add `task_index.schema.json`; extract `task_index.json`; slim `tools.json` to summary shape | — | A1 → A7 |
| **B** | `.github` | Implement `build-catalog.py` + `validate-catalog.py` (TDD) | A7 | B1 → B6 |
| **C** | `.github` | Rewrite `profile/llms.txt` to strict llmstxt.org | — | C1 → C4 |
| **D** | `.github` | `make catalog` + `make validate-catalog` Makefile + CI workflow step | B6 ∧ C4 | D1 → D5 |

To call out work: `run A`, `run B3`, `run B through B4`, `run B+C in parallel`.

### Parallel safety guarantees

- **Tracks B and C touch different files** — B works in `profile/build/` and
  regenerates `profile/tools.json`; C rewrites `profile/llms.txt`. Two open
  PRs at the same time can't collide on a file.
- **Track A is the foundation** for B (which uses the new schemas to
  validate) and D (which runs the build chain). B and C can both start the
  moment A merges.
- **No cross-repo work in Phase 1.** Unlike Phase 0, no tier-1 repo needs
  touching. The tier-1 contract is already published; Phase 1 just builds
  the consumer.

### Stage status conventions

Same as Phase 0. Each stage is one of: `todo`, `doing`, `done`, `blocked`. A
stage is `done` only when its verification command exits 0.

---

## 2. Track A — Schema hardening + task_index split

Runs in `.github`. Single-session work; ~half-day.

### A1 — Audit `tools.json` shape

**Inputs read:** `profile/tools.json` (354 lines today),
`profile/tools.schema.json` (200 lines today).

**Output:** a 1-paragraph audit note in the PR description that names:

- the 10 top-level keys currently in `tools.json`
  (`$schema`, `description`, `discovery_protocol`, `kind`, `org`,
  `schema_version`, `task_index`, `tools`, `workflow`),
- which subset of `tools.*` entries are *summaries* (generatable from
  tier-1 manifests — counts, role, license, agent_instructions URL) vs
  *facts* (inlined subcommand lists, lint-rule lists, module lists — must
  move to pointer URLs),
- the current 6 categories under `task_index` (`_comment`, `history`,
  `infra`, `language`, `lib`, `workflow`),
- whether any inlined field has no equivalent `exposes.*` pointer in the
  tier-1 manifests (those become Phase 1 follow-ups, not blockers).

**Verify:** audit note exists in the PR body before A2 begins.

### A2 — Tighten `tools.schema.json`

**Output:** `profile/tools.schema.json` v2

Changes:

- `additionalProperties: false` at every object level (currently absent or
  partial).
- A single `typedID` regex `^(tool|cmd|module|rule|doc|data|workflow|task|recipe):[a-z0-9_-]+(#[A-Za-z0-9._-]+)?$`
  hoisted into `$defs` and referenced everywhere a typed ID appears
  (parent plan §4.4).
- Drop `task_index` from this schema entirely — it lives in
  `task_index.schema.json` after A3.
- Each `tools.*` entry's `exposes` is **string-only** (URLs / paths) —
  no inline objects allowed.
- Split version metadata into `schema_compat: integer` (only bumps on
  breaking changes) and `schema_version: string` (display) per parent
  plan §4.5.

**Verify:**
```bash
check-jsonschema --schemafile <draft2020-meta> profile/tools.schema.json
```

### A3 — Add `task_index.schema.json`

**Output:** `profile/task_index.schema.json`

Single new schema. Models intent → typed ID maps. Required leaf fields:
`intent` (string), `primary` (typed ID). Optional: `also` (array of typed
IDs).

**Verify:** schema parses + a small synthetic `task_index.json` fixture
validates against it.

### A4 — Extract `task_index.json`

**Output:** `profile/task_index.json`

Lift the entire `task_index` block out of current `tools.json` into its own
file. Add `$schema` pointing at `task_index.schema.json`. Preserve every
existing intent mapping verbatim (no curation changes in this PR — that's a
separate concern).

**Verify:**
```bash
check-jsonschema --schemafile profile/task_index.schema.json profile/task_index.json
```

### A5 — Slim `tools.json` to summary shape

**Output:** `profile/tools.json` (interim — will be regenerated by Track B's
build script later, but should validate cleanly now)

- Remove the `task_index` block (now in `task_index.json`).
- Replace each inlined facts block in `tools.*` with a pointer URL field
  (`commands_url`, `modules_url`, `lint_rules_url`, etc.) whose value
  resolves to the corresponding raw-GitHub URL of the tier-1 manifest's
  `exposes.*` payload.
- Keep: `org`, per-tool `repo`, `role`, `license`, `agent_instructions`,
  `verified_on`, summary counts (number of commands / modules / rules).
- Add `$schema` pointing at the tightened `tools.schema.json`.

**Verify:**
```bash
check-jsonschema --schemafile profile/tools.schema.json profile/tools.json
```

### A6 — Verify whole-tree consistency

**Verify:**
```bash
python3 -m json.tool profile/tools.json >/dev/null
python3 -m json.tool profile/task_index.json >/dev/null
python3 -m json.tool profile/tools.schema.json >/dev/null
python3 -m json.tool profile/task_index.schema.json >/dev/null
check-jsonschema --schemafile profile/tools.schema.json profile/tools.json
check-jsonschema --schemafile profile/task_index.schema.json profile/task_index.json
```

All exit 0.

### A7 — Commit and push

Single PR. Commit subject: `phase1-A: schema tightening + task_index split`.

**Verify:** PR is merged; raw URLs for the new schema files resolve.

---

## 3. Track B — Catalog builder + validator scripts

Runs in `.github`. TDD. Blocked by A7 (schemas must be in place).

### B1 — TDD: tests for `validate-catalog.py`

**Output:** `profile/build/test_validate_catalog.py` (pytest)

Fixtures: valid `tools.json` + `task_index.json` pair; a `tools.json` with
an unknown top-level key (must fail under `additionalProperties: false`); a
`task_index.json` row with a malformed typed ID (must fail under the
typedID regex).

Confirm RED before B2.

### B2 — Implement `validate-catalog.py`

**Output:** `profile/build/validate-catalog.py`

Loads `tools.json` and `task_index.json`, validates each against its
schema. Then merges them (`tools_json["task_index"] = task_index_json`) and
re-validates the composite against a third "merged" schema (or
`unevaluatedProperties: false` over the union — pick whichever is simpler
to express). Exits 0 / non-zero with structured errors.

**Verify:** B1 tests green; `make validate-catalog` (added in D1) is green
against current state.

### B3 — TDD: tests for `build-catalog.py`

**Output:** `profile/build/test_build_catalog.py`

Fixtures: three synthetic tier-1 `repo.meta.json` payloads (one minimal,
one rich, one with extra `exposes` keys). Test that build-catalog emits a
deterministic `tools.json` slice, sorted keys, no inlined facts, all
`*_url` pointers resolvable against the fixture base URL.

Confirm RED before B4.

### B4 — Implement `build-catalog.py`

**Output:** `profile/build/build-catalog.py`

```
For each url in TIER_1:
  fetch repo.meta.json
  validate against repo.meta.schema.json
  for each exposes[kind] -> url:
    HEAD it (don't fetch the full payload)
    optionally fetch for summary counts (modules, commands, rules)
  emit a summary entry under tools[id]:
    repo, role, license, agent_instructions, verified_on
    a summary count where cheap to compute
    a *_url pointer for each exposed payload
Merge with profile/task_index.json (read fresh)
Emit deterministically (sorted keys, 2-space indent)
Write to profile/tools.json
```

**Verify:** B3 tests green; running against live `TIER_1` produces a
`tools.json` identical to the slim version produced in A5 (modulo summary
counts and `verified_on` timestamps now sourced from live manifests). Diff
the two; reconcile.

### B5 — Determinism + freshness check

Run `make catalog` twice in a row; assert byte-identical output. Then
artificially advance one tier-1 repo's `verified_on` in a local fixture;
assert that change reflects in the regenerated `tools.json`.

**Verify:** both checks pass.

### B6 — Commit and push

Single PR (or two if B1-B2 and B3-B4 ship separately for review). Commit
subject for the main PR: `phase1-B: build-catalog + validate-catalog (TDD)`.

**Verify:** PR is merged; `profile/build/` contains both scripts + their
tests; `tools.json` on `main` reflects build output.

---

## 4. Track C — `llms.txt` migration

Runs in `.github`. Small. Independent of A/B — can ship anytime.

### C1 — Audit current `llms.txt` against llmstxt.org spec

**Inputs read:** `profile/llms.txt` (49 lines today),
[llmstxt.org spec](https://llmstxt.org/).

**Output:** a 1-paragraph audit note in the PR description naming which
sections of the current file conform vs. drift from the spec. Specifically:

- Does the file have a single H1 with the project name?
- Is there a single-paragraph blockquote `> ...` summary?
- Are subsequent sections `## Title` with bulleted link lists?
- Are any required sections missing? Any non-spec sections present?

**Verify:** audit note exists.

### C2 — Rewrite to strict llmstxt.org form

**Output:** `profile/llms.txt`

Follow the template in parent plan §4.6:

```markdown
# m-dev-tools

> Engine-neutral M (MUMPS) developer tools — TDD/CI/lint/fmt/test/coverage
> across YottaDB and InterSystems IRIS. Modeled on Go/Rust/Python toolchains.

## Start here

- [Org catalog (machine-readable)](...): intent → repo routing
- [Schema](...): contract for tools.json
- [Org README](...): human overview

## Core repositories

- [m-cli](...): canonical `m` CLI surface
- [m-stdlib](...): runtime standard library
- [m-standard](...): language reference data
- [tree-sitter-m](...): parser

## Guardrails

- Do not invent STD* APIs or `m` commands; route the gap to the owning repo.
- Use `m-stdlib` before adding helper logic elsewhere.
- For language semantics, query `m-standard`'s TSVs/JSON, not memory.
```

Forty lines max. Anything longer lives in `README.md` or `tools.json`.

### C3 — Link-check

**Verify:** every URL in the new `llms.txt` returns HTTP 200 via `curl -fsSL
-o /dev/null` (or equivalent). Zero broken links.

### C4 — Commit and push

Single PR. Commit subject: `phase1-C: rewrite llms.txt to strict llmstxt.org form`.

**Verify:** PR merged.

---

## 5. Track D — Make targets + CI wiring

Runs in `.github`. Blocked by B6 (build/validate scripts) and C4 (so the
link-check step has a known-clean `llms.txt` to gate on).

### D1 — Add `make catalog` target

**Output:** addition to `.github/Makefile`

```makefile
catalog:
	python3 profile/build/build-catalog.py
```

By default writes back to `profile/tools.json`. Idempotent — running twice
in a row produces no diff. The CI workflow will run `make catalog` then
`git diff --exit-code profile/tools.json` to fail on drift (same pattern as
each tier-1 repo's `check-manifest`).

**Verify:** `make catalog && git diff --exit-code profile/tools.json` is
green.

### D2 — Add `make validate-catalog` target

**Output:** addition to `.github/Makefile`

```makefile
validate-catalog:
	python3 profile/build/validate-catalog.py
```

Replaces the current target (which only runs `python3 -m json.tool`). The
new target invokes the full jsonschema validator from B2.

**Verify:** `make validate-catalog` is green.

### D3 — Wire into CI

**Output:** edit to `.github/.github/workflows/ci.yml` (the workflow added
in Phase-0 cleanup, currently runs `validate-catalog` + `check-docs-prose`).

Add two new steps:

```yaml
- name: Regenerate catalog (drift gate)
  run: |
    make catalog
    git diff --exit-code profile/tools.json profile/task_index.json
- name: Validate catalog
  run: make validate-catalog
```

`Validate catalog` already exists in the workflow but invokes the old
`python -m json.tool` form; this stage replaces it with the new
schema-strict validator.

**Verify:** push a branch; CI passes. Push a deliberately corrupt
`tools.json` (e.g. invalid typed ID); CI fails. Revert.

### D4 — Phase 1 smoke

**Output:** evidence file

```bash
make catalog && make validate-catalog | tee docs/phase1-evidence.txt
git add docs/phase1-evidence.txt
```

**Verify:** evidence captures both targets exiting 0.

### D5 — Commit and merge

Single PR. Commit subject: `phase1-D: make catalog + validate-catalog wired into CI`.

Phase 1 is now complete. Phase 2 may start.

---

## 6. Stage Matrix — Single-Glance View

| Stage | Repo | Blocked by | Verification |
|---|---|---|---|
| A1 | .github | — | audit note in PR body |
| A2 | .github | A1 | `tools.schema.json` validates as JSON Schema |
| A3 | .github | A1 | `task_index.schema.json` validates as JSON Schema |
| A4 | .github | A3 | `task_index.json` validates against A3 schema |
| A5 | .github | A2, A4 | `tools.json` validates against A2 schema |
| A6 | .github | A5 | all four files parse + validate |
| A7 | .github | A6 | PR merged; raw URLs resolve |
| B1 | .github | A7 | RED tests |
| B2 | .github | B1 | B1 tests green |
| B3 | .github | B2 | RED tests |
| B4 | .github | B3 | B3 tests green |
| B5 | .github | B4 | determinism + freshness checks pass |
| B6 | .github | B5 | PR merged; generated `tools.json` on main |
| C1 | .github | — | audit note in PR body |
| C2 | .github | C1 | new `llms.txt` ≤ 40 lines, strict form |
| C3 | .github | C2 | all URLs HTTP 200 |
| C4 | .github | C3 | PR merged |
| D1 | .github | B6 | `make catalog` deterministic |
| D2 | .github | B6 | `make validate-catalog` exits 0 |
| D3 | .github | D1, D2, C4 | CI green on branch; negative test fails |
| D4 | .github | D3 | evidence file captured |
| D5 | .github | D4 | PR merged |

---

## 7. Calling Convention

To direct a Claude session at a specific slice of work:

- **`run A`** — execute Track A end-to-end.
- **`run B`** — execute Track B end-to-end (only after A7).
- **`run B3`** — execute only stage B3.
- **`run B through B4`** — B1, B2, B3, B4 in sequence.
- **`run B+C in parallel`** — spawn two independent sessions; one per
  track. Different files, no collision risk.
- **`resume B from B3`** — continue from a checkpoint; assumes B1–B2 done.

A Claude session given a track callout should:

1. Read this document.
2. Confirm the blocking stage(s) are `done`.
3. Execute its stages in order.
4. Run the verification command at the end of each stage; halt on failure.
5. Report the final state when the track (or named substage) completes.

Do **not** advance a stage whose verification didn't exit 0. Halt and report.

### Recommended order

If executing single-threaded:

1. **A** (foundation — schema + data split).
2. **B and C in parallel** (B = build/validate machinery; C = llms.txt rewrite).
3. **D** (Make + CI wiring; pulls B and C together).

If you can only ship part of Phase 1, ship **A and D-minus-the-CI-bit**
first — that gets `task_index.json` separated from `tools.json` and the
schemas tightened, which is the largest single source of catalog drift.
Phase 1 then becomes "ship the generator" rather than "ship the entire
routing layer," and partial value lands sooner.

---

## 8. Risk Notes

- **Schema tightening may reject the current `tools.json`.** Track A
  intentionally re-shapes `tools.json` in the same PR (A5) so the
  tightened schema and the data match at landing time. If an outside
  consumer is reading `tools.json` and expects the old inlined
  subcommand/module/rule fields, this is a breaking change for them —
  but Phase 0's Phase-0-done definition says no external consumer
  exists yet beyond the smoke test. Audit during A1 to confirm.
- **`build-catalog.py` needs network at build time.** It fetches tier-1
  `repo.meta.json` from raw GitHub URLs. CI has network; local dev
  usually does. Offline dev breaks `make catalog` — acceptable trade
  (Phase 0 took the same posture with manifest validation).
- **Race between Track D and a tier-1 manifest update.** If a tier-1
  repo bumps its `verified_on` between Track B6 and Track D5, the
  generated `tools.json` will differ from what B6 committed and Track
  D's drift gate may flag it. Mitigation: run `make catalog` as the
  first step in D1, immediately followed by the commit, before any
  other work that could race. (This is the same race the per-tier-1
  `check-manifest` faces; same mitigation.)
- **`llms.txt` link rot is the silent failure mode.** C3 link-checks
  at PR time but won't catch later rot. Phase 5 (per parent plan)
  adds `make check-links` on a weekly schedule — defer until then.
- **Schema-changelog discipline.** Parent plan §6.3 calls for a
  `schema-changelog.md` row whenever `tools.schema.json` or
  `repo.meta.schema.json` changes non-additively. Track A's tightening
  IS non-additive (drops `task_index` and inlined facts blocks). The
  PR description for A7 should treat that as a `schema_compat: 1 → 2`
  bump and add a changelog row — the changelog doesn't exist yet
  (Phase 5 spec), so create it in A7 with one row.
- **Drift between `tools.json` and tier-1 manifests during B build.**
  If `build-catalog.py` is invoked between two of the three tier-1
  repos updating their `dist/repo.meta.json`, the generated catalog
  will reflect a transient mixed state. CI catches this on the next
  push; for now, accept the brief inconsistency window.

---

## 9. Phase 1 Done — Definition

Phase 1 is done when **all** of these are true:

1. `profile/tools.schema.json` carries `additionalProperties: false` at
   every level and a typed-ID regex enforced wherever a typed ID
   appears.
2. `profile/task_index.schema.json` exists and validates against JSON
   Schema 2020-12.
3. `profile/task_index.json` is the **only** hand-curated routing
   source; lifted out of `tools.json`.
4. `profile/tools.json` carries **no** inlined subcommand / module /
   lint-rule lists; every per-repo entry references a tier-1
   `dist/<kind>.json` via `*_url` pointers.
5. `profile/build/build-catalog.py` and
   `profile/build/validate-catalog.py` exist and are TDD-covered.
6. `profile/llms.txt` is strict llmstxt.org form, ≤ 40 lines, all URLs
   HTTP 200.
7. `make catalog` is idempotent (running twice produces no diff against
   committed `tools.json`).
8. `make validate-catalog` invokes the real jsonschema validator (not
   `python -m json.tool`).
9. CI (`.github/.github/workflows/ci.yml`) runs both targets on every
   push/PR and gates on green.
10. `docs/phase1-evidence.txt` captures a clean run of both targets and
    is committed to `main`.

Phase 2 — tier-2 repos onboarding (`tree-sitter-m`, `m-test-engine`,
`m-modern-corpus`) — starts the next session after Phase 1 is done.
