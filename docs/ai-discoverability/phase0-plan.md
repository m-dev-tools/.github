# Phase 0 Implementation Plan — Tier-1 Per-Repo Contract

**Parent plan:** [`AI-discoverability-plan.md`](AI-discoverability-plan.md)
**Phase 0 goal:** `m-cli`, `m-stdlib`, and `m-standard` each emit a validated
`dist/repo.meta.json`, ship an `AGENTS.md` with `CLAUDE.md` symlinked, and have
a working `make check-manifest` drift gate. The meta-repo ships the
`repo.meta.json` schema and a smoke test that proves all three repos chain
together.

**Phase 0 exit:** `make phase0-smoke` in `.github` is green — it fetches the
three `repo.meta.json` files, validates them, follows their `exposes`
pointers, and asserts every pointed-at payload parses cleanly.

---

## 1. Track Layout

Five tracks. Track A is a prerequisite for B/C/D. Track E integrates after
B/C/D finish.

```
┌────────────────────────────┐
│ Track A — schema + tooling │  (must finish before B/C/D start)
│ runs in .github            │
└────────────┬───────────────┘
             │
   ┌─────────┼─────────┐
   ▼         ▼         ▼
┌──────┐  ┌──────┐  ┌──────┐
│ B    │  │ C    │  │ D    │   parallel — different repos, no file overlap
│m-stdl│  │m-std │  │m-cli │
│  ib  │  │ ard  │  │      │
└──┬───┘  └──┬───┘  └──┬───┘
   │         │         │
   └─────────┼─────────┘
             ▼
┌────────────────────────────┐
│ Track E — integration smoke│  (waits until B/C/D are pushed)
│ runs in .github            │
└────────────────────────────┘
```

### Track index — callable names

| Track | Repo | Purpose | Blocked by | Stages |
|---|---|---|---|---|
| **A** | `.github` | Publish `repo.meta.schema.json` + validator | — | A1 → A5 |
| **B** | `m-stdlib` | Ship `dist/repo.meta.json` for stdlib | A5 | B1 → B6 |
| **C** | `m-standard` | Ship `dist/repo.meta.json` for language reference | A5 | C1 → C6 |
| **D** | `m-cli` | Ship `dist/repo.meta.json` + `m capabilities --json` | A5 | D1 → D10 |
| **E** | `.github` | Phase 0 smoke test wiring | B6 ∧ C6 ∧ D10 | E1 → E5 |

To call out work: `run A`, `run B3`, `run B through B4`, `run B+C+D in parallel`.

### Parallel safety guarantees

- **Different repos = different git histories.** B, C, D each operate in a
  separate clone. No file-level conflicts are possible across tracks.
- **Meta-repo (`.github`) is touched only by A and E,** and A finishes
  before E starts. No concurrent writes to `.github`.
- **Container/engine resources:** if two tracks run `m test` simultaneously
  against a Docker engine, they may collide on the default container name
  `m-test-engine`. Per-track override: set `M_TEST_ENGINE_CONTAINER=mte-<track>`
  before any `make engine-up` / `m test` invocation. Concrete:
  `B → mte-stdlib`, `C → mte-standard`, `D → mte-cli`.
- **Local virtualenvs:** each Python repo has its own `.venv/`. Direnv +
  `.envrc` per-repo prevents cross-contamination.
- **PyPI / npm caches:** shared, but read-mostly; no clash risk.
- **`m-cli` is the only Python repo where ongoing maintainer work is
  likely.** Before starting D, capture current branch state and surface any
  uncommitted changes before editing.

### Stage status conventions

Each stage is one of: `todo`, `doing`, `done`, `blocked`. A stage is `done`
only when its verification command exits 0.

---

## 2. Track A — Meta-Repo Schema and Tooling

Runs in `.github`. Small, single-session. Must complete before B/C/D start.

### A1 — Write `repo.meta.schema.json` v1

**Output:** `.github/profile/repo.meta.schema.json`

Required top-level fields: `id`, `repo`, `role`, `language`, `license`,
`agent_instructions`, `verified_on`, `exposes`, `verification_commands`.
Optional: `consumes`, `status`, `notes`.

`id` pattern: `^tool:[a-z0-9_-]+$` (Phase 0 only emits tool-level IDs;
finer-grained IDs come in Phase 1).

`exposes` is an object with string keys and string values; each value is a
relative path or absolute URL. No enforcement of which keys appear — each
repo declares what it owns.

`verified_on` is `YYYY-MM-DD`.

`verification_commands` is a non-empty array of strings.

`additionalProperties: false` at every level.

**Verify:** `python3 -m json.tool .github/profile/repo.meta.schema.json`
parses; the schema itself validates as JSON Schema 2020-12 via
`check-jsonschema --schemafile <draft2020-meta> repo.meta.schema.json`.

### A2 — Write `repo.meta.example.json`

**Output:** `.github/profile/repo.meta.example.json`

A canonical example. Use a fictional repo (`tool:example-repo`) so the file is
unambiguously a template, not a real repo's manifest.

**Verify:** the example validates against the schema:
`check-jsonschema --schemafile profile/repo.meta.schema.json profile/repo.meta.example.json`.

### A3 — Write `validate-repo-meta.py`

**Output:** `.github/profile/build/validate-repo-meta.py`

Takes a path or URL. Loads it. Validates against
`repo.meta.schema.json`. Then fetches each `exposes.*` value (if URL) or
checks file existence (if path) and asserts it parses as JSON. Exits 0 on
success, prints structured errors on failure.

Zero third-party deps beyond `jsonschema` (already implied by A1). Use
`urllib` for fetches.

**Verify:**
```bash
python3 profile/build/validate-repo-meta.py profile/repo.meta.example.json
# → exits 0
```

### A4 — Add `make check-repo-meta` target

**Output:** added to `.github/Makefile`

```makefile
check-repo-meta:
	python3 profile/build/validate-repo-meta.py $(META)
```

Used downstream as: `make check-repo-meta META=<path-or-url>`.

**Verify:** `make check-repo-meta META=profile/repo.meta.example.json` is green.

### A5 — Commit and push

Single commit. Commit subject: `phase0-A: publish repo.meta.json schema v1`.

After push, the schema is reachable at
`https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/repo.meta.schema.json`,
which B/C/D will reference in their `$schema` field.

**Verify:** `curl -fsSL <raw URL>` returns the schema. Tracks B/C/D may now start.

---

## 3. Track B — `m-stdlib`

Runs in the `m-stdlib` repo. Smallest tier-1 track (the manifest already
exists; this is wrap-and-wire work).

### B1 — Audit current state

**Inputs read:** `README.md`, `Makefile`, `dist/`, `CLAUDE.md` or
`AGENTS.md` if present.

**Output:** a 1-paragraph audit note in the PR description that names:

- whether `dist/stdlib-manifest.json` is generated by `make manifest` (or
  equivalent) and whether that target exists today,
- whether `CLAUDE.md` exists and the canonical name to adopt,
- which CI workflow under `.github/workflows/` runs on every push.

**Verify:** audit note exists; no changes committed yet.

### B2 — Adopt `AGENTS.md` with `CLAUDE.md` symlink

If `CLAUDE.md` exists and `AGENTS.md` does not: `git mv CLAUDE.md AGENTS.md && ln -s AGENTS.md CLAUDE.md`.
If `AGENTS.md` already exists: leave it; ensure `CLAUDE.md` is a symlink to it.

`AGENTS.md` must contain these sections (add if missing):

- `## Setup` — exact commands to install
- `## Test` — exact commands to run tests
- `## Build / generate` — exact commands to regenerate `dist/`
- `## Verify` — list of `verification_commands` matching `repo.meta.json`
- `## Guardrails` — repo-specific don'ts (e.g., "do not edit `dist/` by hand")

**Verify:** `ls -la CLAUDE.md` shows symlink target `AGENTS.md`;
`grep -E '^## (Setup|Test|Build|Verify|Guardrails)' AGENTS.md` lists all five.

### B3 — Author `dist/repo.meta.json`

**Output:** `dist/repo.meta.json`

```json
{
  "$schema": "https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/repo.meta.schema.json",
  "id": "tool:m-stdlib",
  "repo": "https://github.com/m-dev-tools/m-stdlib",
  "role": "Pure-M runtime standard library — STD* modules",
  "language": ["m"],
  "license": "AGPL-3.0",
  "agent_instructions": "AGENTS.md",
  "verified_on": "<today YYYY-MM-DD>",
  "exposes": {
    "modules": "dist/stdlib-manifest.json"
  },
  "consumes": ["tool:m-test-engine"],
  "verification_commands": ["make manifest", "make test"]
}
```

**Verify:** validate against the published schema:
```bash
python3 <(curl -fsSL https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/build/validate-repo-meta.py) \
  dist/repo.meta.json
```

(Once Track E lands, this becomes `make check-manifest` locally.)

### B4 — Add `make check-manifest`

**Output:** Makefile target

```makefile
check-manifest:
	$(MAKE) manifest                          # regenerate dist/stdlib-manifest.json
	git diff --exit-code dist/stdlib-manifest.json dist/repo.meta.json
```

The target asserts that `dist/` is up-to-date relative to source.

**Verify:** `make check-manifest` is green on a clean checkout.

### B5 — Wire `check-manifest` into CI

**Output:** edit to existing `.github/workflows/ci.yml`

Add a step under the existing test job:
```yaml
- name: Manifest drift gate
  run: make check-manifest
```

**Verify:** push a branch; CI passes. Push a deliberately corrupt
`stdlib-manifest.json`; CI fails. Revert.

### B6 — Commit and push

Single PR. Commit subject: `phase0-B: add repo.meta.json + manifest drift gate`.

**Verify:** PR is merged; `dist/repo.meta.json` is fetchable from raw URL.

---

## 4. Track C — `m-standard`

Runs in the `m-standard` repo. Same shape as Track B; the payloads
(`integrated/*`) already exist.

### C1 — Audit current state
Same as B1. Identify which `integrated/*.tsv` and `integrated/*.json`
artifacts exist and whether `make` regenerates them.

### C2 — Adopt `AGENTS.md`
Same protocol as B2. Required sections: Setup, Test, Build/generate, Verify,
Guardrails.

### C3 — Author `dist/repo.meta.json`

```json
{
  "$schema": "https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/repo.meta.schema.json",
  "id": "tool:m-standard",
  "repo": "https://github.com/m-dev-tools/m-standard",
  "role": "Machine-readable M language reference",
  "language": ["python"],
  "license": "AGPL-3.0",
  "agent_instructions": "AGENTS.md",
  "verified_on": "<today>",
  "exposes": {
    "grammar_surface":            "integrated/grammar-surface.json",
    "commands":                   "integrated/commands.tsv",
    "intrinsic_functions":        "integrated/intrinsic-functions.tsv",
    "intrinsic_special_variables":"integrated/intrinsic-special-variables.tsv",
    "operators":                  "integrated/operators.tsv",
    "errors":                     "integrated/errors.tsv",
    "pragmatic_standard":         "integrated/pragmatic-m-standard.json",
    "operational_standard":       "integrated/operational-m-standard.json",
    "va_sac_rules":               "integrated/va-sac-rules.tsv"
  },
  "verification_commands": ["make integrated", "make test"]
}
```

**Note:** the smoke test only requires each `exposes.*` path to parse as
JSON. TSVs are listed but the smoke test will skip non-JSON entries in
Phase 0; Phase 1 introduces per-kind schemas. To stay forward-compatible,
list them now.

### C4 — Add `make check-manifest`

```makefile
check-manifest:
	$(MAKE) integrated
	git diff --exit-code integrated/ dist/repo.meta.json
```

### C5 — Wire CI
Same as B5.

### C6 — Commit and push
Commit subject: `phase0-C: add repo.meta.json for m-standard`.

---

## 5. Track D — `m-cli`

Runs in the `m-cli` repo. Largest track: ships two new subcommands
(`m capabilities --json`, `m help --json`) plus the manifest wrap.

### D1 — Audit current state
Identify: how subcommands are registered (look in `src/m_cli/cli.py`); how
lint rules are registered (look in `src/m_cli/lint/rules.py`); how fmt
rules are registered. Confirm clean branch.

### D2 — Adopt `AGENTS.md`
`m-cli` already has a substantial `CLAUDE.md`. Rename to `AGENTS.md`,
symlink `CLAUDE.md → AGENTS.md`, ensure required sections exist (the
current content covers most; add a `## Verify` section if missing with
`make check`, `m doctor`).

### D3 — TDD: write the test for `m capabilities --json`

**Output:** `tests/test_capabilities.py`

Tests:

- `m capabilities --json` exits 0
- Output is valid JSON
- Top-level keys: `version`, `subcommands`
- `subcommands` is an object keyed by subcommand name
- Each subcommand entry has: `purpose`, `options` (list), `examples` (list)
- Specific subcommands (`fmt`, `lint`, `test`, `coverage`, `lsp`) are present

Confirm RED before D4.

### D4 — Implement `m capabilities --json`

**Output:** `src/m_cli/capabilities/cli.py` + wiring in `cli.py`

Reads the existing argparse subparsers tree and emits a structured JSON
view. Source of truth: the argparse registrations themselves. Do not
hand-curate.

**Verify:** D3 tests green; `m capabilities --json | python3 -m json.tool`
parses.

### D5 — Emit `dist/commands.json` from `m capabilities`

**Output:** Makefile target `dist/commands.json:`

```makefile
dist/commands.json: src/m_cli/cli.py $(wildcard src/m_cli/**/cli.py)
	mkdir -p dist
	.venv/bin/m capabilities --json > $@
```

Plus a `manifest:` target that builds all `dist/*.json` files.

**Verify:** `make dist/commands.json && python3 -m json.tool dist/commands.json`.

### D6 — TDD + implement `m lint --list-rules --json`

**Output:** test in `tests/test_lint_list_rules.py`; flag in
`src/m_cli/lint/cli.py`.

Emits an array of objects: `id`, `severity`, `category`, `tags`, `profiles`,
`fixer_id` (or null), `description`. Source: the `Rule` registry.

`dist/lint-rules.json:` Makefile target that pipes this command's output.

### D7 — TDD + implement `m fmt --list-rules --json`

**Output:** test + flag + Makefile target. Same shape as D6 for the fmt
rule registry.

`dist/fmt-rules.json:` Makefile target.

### D8 — Author `dist/repo.meta.json`

```json
{
  "$schema": "https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/repo.meta.schema.json",
  "id": "tool:m-cli",
  "repo": "https://github.com/m-dev-tools/m-cli",
  "role": "Canonical M CLI — fmt / lint / test / coverage / watch / lsp / doc / new",
  "language": ["python"],
  "license": "AGPL-3.0",
  "agent_instructions": "AGENTS.md",
  "verified_on": "<today>",
  "exposes": {
    "commands":   "dist/commands.json",
    "lint_rules": "dist/lint-rules.json",
    "fmt_rules":  "dist/fmt-rules.json"
  },
  "consumes": ["tool:tree-sitter-m", "tool:m-standard", "tool:m-test-engine"],
  "verification_commands": ["make check", "m doctor"]
}
```

### D9 — Add `make check-manifest`

```makefile
check-manifest: dist/commands.json dist/lint-rules.json dist/fmt-rules.json
	git diff --exit-code dist/
```

Wire into existing `check` target's dependencies, or as a separate CI step.

### D10 — Commit and push
Single PR (or split: one PR per subcommand if reviews are heavy). Commit
subject for the main PR: `phase0-D: add capabilities + manifest drift gate`.

**Verify:** all three `dist/*.json` files fetchable from raw URLs after
merge.

---

## 6. Track E — Meta-Repo Integration Smoke

Runs in `.github` **after** B6, C6, and D10 are all merged.

### E1 — Pin the three published URLs

**Output:** edit `.github/profile/build/validate-repo-meta.py` (or add
`phase0-smoke.py` alongside) to know about the three production manifests:

```python
TIER_1 = [
    "https://raw.githubusercontent.com/m-dev-tools/m-stdlib/main/dist/repo.meta.json",
    "https://raw.githubusercontent.com/m-dev-tools/m-standard/main/dist/repo.meta.json",
    "https://raw.githubusercontent.com/m-dev-tools/m-cli/main/dist/repo.meta.json",
]
```

### E2 — Write `phase0-smoke.py`

**Output:** `.github/profile/build/phase0-smoke.py`

For each URL in `TIER_1`:

1. Fetch the `repo.meta.json`. Assert HTTP 200.
2. Validate against `repo.meta.schema.json`.
3. For each `exposes.*` URL: fetch. If the URL ends in `.json`, parse it.
   Otherwise (`.tsv` etc.) just assert HTTP 200 in Phase 0.
4. Assert `verified_on` is within 90 days.

Print a routing trail per repo and a final ✓/✗ summary. Exit non-zero on
any failure.

### E3 — Add `make phase0-smoke`

```makefile
phase0-smoke:
	python3 profile/build/phase0-smoke.py
```

### E4 — Run the smoke test

**Verify:** `make phase0-smoke` is green. This is Phase 0's exit criterion.

Capture the output as evidence:
```bash
make phase0-smoke | tee docs/phase0-evidence.txt
git add docs/phase0-evidence.txt
```

### E5 — Commit and push

Commit subject: `phase0-E: phase 0 smoke test green`.

Phase 0 is now complete. Phase 1 may start.

---

## 7. Stage Matrix — Single-Glance View

| Stage | Repo | Blocked by | Verification |
|---|---|---|---|
| A1 | .github | — | schema parses as JSON Schema |
| A2 | .github | A1 | example validates against A1 |
| A3 | .github | A1 | example validation script exits 0 |
| A4 | .github | A3 | `make check-repo-meta META=…example.json` |
| A5 | .github | A4 | raw URL `curl -fsSL` returns schema |
| B1 | m-stdlib | A5 | audit note written |
| B2 | m-stdlib | B1 | `ls -la CLAUDE.md` symlink to AGENTS.md |
| B3 | m-stdlib | B2 | validator script exits 0 |
| B4 | m-stdlib | B3 | `make check-manifest` exits 0 |
| B5 | m-stdlib | B4 | CI green on PR branch |
| B6 | m-stdlib | B5 | PR merged; raw URL returns repo.meta.json |
| C1–C6 | m-standard | A5 | parallel to B; same verifications |
| D1 | m-cli | A5 | audit note |
| D2 | m-cli | D1 | symlink |
| D3 | m-cli | D2 | RED test |
| D4 | m-cli | D3 | D3 test green |
| D5 | m-cli | D4 | `dist/commands.json` parses |
| D6 | m-cli | D4 | `dist/lint-rules.json` parses |
| D7 | m-cli | D4 | `dist/fmt-rules.json` parses |
| D8 | m-cli | D5, D6, D7 | validator script exits 0 |
| D9 | m-cli | D8 | `make check-manifest` exits 0 |
| D10 | m-cli | D9 | PR merged; all raw URLs return |
| E1 | .github | B6, C6, D10 | URLs pinned |
| E2 | .github | E1 | script written |
| E3 | .github | E2 | target wired |
| E4 | .github | E3 | `make phase0-smoke` green |
| E5 | .github | E4 | committed; evidence captured |

---

## 8. Calling Convention

To direct a Claude session at a specific slice of work:

- **`run A`** — execute Track A end-to-end.
- **`run B`** — execute Track B end-to-end (only after A5).
- **`run B3`** — execute only stage B3.
- **`run B through B4`** — B1, B2, B3, B4 in sequence.
- **`run B+C+D in parallel`** — spawn three independent sessions; one per
  track. Each gets its own track letter and operates in its own repo.
- **`resume D from D6`** — continue from a checkpoint; assumes D1–D5 done.

A Claude session given a track callout should:

1. Read this document.
2. Confirm the blocking stage(s) are `done`.
3. Execute its stages in order.
4. Run the verification command at the end of each stage; halt on failure.
5. Report the final state when the track (or named substage) completes.

Do **not** advance a stage whose verification didn't exit 0. Halt and report.

---

## 9. Risk Notes

- **Schema iteration after publish.** If A5 ships and B/C/D discover a
  required field is missing, that's an additive change. Bump
  `repo.meta.schema.json` minor version, update example, no `schema_compat`
  bump. Re-run any track's verification after the schema bump.
- **`m-cli` ongoing maintainer work.** D2 renames `CLAUDE.md` →
  `AGENTS.md`. Any open PR that touches `CLAUDE.md` will conflict. Mitigate
  by checking open PRs before D2 and either merging them first or rebasing
  after D2.
- **`dist/` already in `.gitignore`?** Several repos may currently
  `.gitignore` `dist/`. Phase 0 requires `dist/repo.meta.json` and the
  payload files to be committed. Each track's stage 3 must remove `dist/`
  from `.gitignore` (or add explicit `!dist/repo.meta.json` etc.) — verify
  during the audit stage.
- **Engine container name collisions.** If B and D run `m test` in
  parallel against Docker, override `M_TEST_ENGINE_CONTAINER` per track as
  noted in §1.
- **Phase 0 does not validate `exposes.*` content schemas.** Only that the
  pointed-at files exist and (for `.json`) parse. Per-kind schemas land in
  Phase 1.

---

## 10. Phase 0 Done — Definition

Phase 0 is done when **all** of these are true:

1. `https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/repo.meta.schema.json` returns the v1 schema.
2. `https://raw.githubusercontent.com/m-dev-tools/m-stdlib/main/dist/repo.meta.json` returns a valid manifest.
3. `https://raw.githubusercontent.com/m-dev-tools/m-standard/main/dist/repo.meta.json` returns a valid manifest.
4. `https://raw.githubusercontent.com/m-dev-tools/m-cli/main/dist/repo.meta.json` returns a valid manifest.
5. `m capabilities --json` is a working command in `m-cli`.
6. Each tier-1 repo has `AGENTS.md` with `CLAUDE.md` symlinked to it.
7. Each tier-1 repo has a green `make check-manifest` and that target runs in CI.
8. `make phase0-smoke` in `.github` is green and the evidence file is committed.

Phase 1 — org routing layer — starts the next session after Phase 0 is done.
