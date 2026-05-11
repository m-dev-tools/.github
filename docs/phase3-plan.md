# Phase 3 Implementation Plan — Recipes + Handshake Test (Layer 3)

**Parent plan:** [`AI-discoverability-plan.md`](AI-discoverability-plan.md) §7
**Phase 3 goal:** Agents (and the `test-discovery-protocol.py` script that
proxies for them) can complete the highest-value developer workflows by
*reading the org catalog* rather than by *guessing*. At least **4 of the 7
priority recipes** are written, executable, and CI-verified. The **discovery
handshake test** runs in CI on every push and on a weekly cron to catch
external link rot.

**Phase 3 exit:** running `profile/build/test-discovery-protocol.py` from a
fresh clone of `.github` completes the `new-app-tdd-ci` recipe top-to-bottom
(intent → typed ID → manifest pointer → actionable command sequence → green
run) with zero broken links, and CI on `.github/main` is green.

**Scope:** recipes are the **agent-facing** deliverable. They live under
[`.github/docs/recipes/`](recipes/) and reference typed IDs from the
generated `profile/tools.json` (Phase 1 deliverable). The handshake test
mechanically exercises §13 of [`AI-discoverability-guide.md`](AI-discoverability-guide.md)
and §7 of the parent plan.

**Not in scope:** the MCP server (Phase 4); continuous link-check / freshness
hardening on a weekly schedule (Phase 5 — Phase 3 link-checks at PR time only).

---

## 0. Blocking dependencies (must finish before Phase 3 starts)

| Upstream phase | What Phase 3 needs from it | Status as of 2026-05-11 |
|---|---|---|
| **Phase 1** (org routing layer) | Generated `profile/tools.json` with `*_url` pointers, `profile/task_index.json` as the intent map, strict `llms.txt` | ✅ **CLOSED 2026-05-10** — A/B/C/D all merged (PRs #10/#11/#12/#16). `make catalog && make validate-catalog` green in CI on every push. `make catalog` byte-idempotent against `origin/main`. |
| **Phase 2** (tier-2 repos `repo.meta.json`) | Recipes #6 (`investigate-failure`) and #7 (`add-editor-support`) reach into `tree-sitter-m`; their manifests must be in the catalog | ✅ **CLOSED 2026-05-10** — all 3 tier-2 + all 3 tier-3 repos onboarded the same day. `tools.json` carries **9 manifest-bearing entries** (m-tools the only archived holdout, rehosted under `docs/history/` per PR #17). |

**Phase 3 launch state — both blockers resolved as of 2026-05-11.** All five
tracks (A → B+C+D → E) are unblocked. Recipes 6 and 7 (originally Phase-2-
and Phase-4-blocked) are unblocked at the data layer; recipe 7's tier-3
VS Code-extension specifics may still want the MCP server (Phase 4) before
end-to-end CI-verifiable, so it remains a post-exit follow-up per §1.

Verification commands (re-runnable to confirm the launch state hasn't
regressed):

```bash
cd .github
make catalog && make validate-catalog && make phase0-smoke
# Note: local validate-catalog needs a Python with `jsonschema` installed;
# CI installs it via the workflow step. Locally: pip install jsonschema or
# use the m-standard venv: /home/rafael/m-dev-tools/m-standard/.venv/bin/python.
pytest profile/build/   # 26/26 expected
```

---

## 1. Track Layout

Five tracks. Track A is a prerequisite for B/C/D. Track E integrates after
B/C/D finish.

```
┌─────────────────────────────────────────────┐
│ Track A — recipe schema + frontmatter spec  │  (must finish before B/C/D start)
│ runs in .github                             │
└─────────────────┬───────────────────────────┘
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ B       │ │ C       │ │ D       │   parallel — different files, no overlap
   │ recipes │ │handshake│ │ CI +    │
   │ 1–4     │ │  test   │ │recipe   │
   │         │ │ (TDD)   │ │ runner  │
   └────┬────┘ └────┬────┘ └────┬────┘
        │           │           │
        └───────────┼───────────┘
                    ▼
   ┌─────────────────────────────────────────┐
   │ Track E — Phase 3 smoke + evidence      │  (waits until B+C+D done)
   │ runs in .github                         │
   └─────────────────────────────────────────┘
```

### Track index — callable names

| Track | Repo | Purpose | Blocked by | Stages |
|---|---|---|---|---|
| **A** | `.github` | `recipe.schema.json` + frontmatter contract; create `docs/recipes/` | Phase 1 D5 | A1 → A5 |
| **B** | `.github` | Author recipes 1–4 (the four required for exit) | A5 | B1 → B5 |
| **C** | `.github` | TDD-build `test-discovery-protocol.py` | A5 | C1 → C5 |
| **D** | `.github` | `make recipes-check` + `make handshake` + CI wiring | B5 ∧ C5 | D1 → D4 |
| **E** | `.github` | Smoke + evidence file + close-out PR | D4 | E1 → E3 |

Recipes 5–7 (`add-m-cli-command`, `investigate-failure`, `add-editor-support`)
are **post-exit follow-ups** — they round out the "all 7" set but are not
gating. Recipe 6 is blocked by Phase 2 (needs tier-2 manifests); recipe 7 is
blocked by Phase 4 (editor extension manifests). Track these as separate
issues, not Phase 3 stages.

To call out work: `run A`, `run B3`, `run B through B4`, `run B+C in parallel`.

### Parallel safety guarantees

- **Tracks B and C touch different files.** B writes Markdown under
  `docs/recipes/`; C writes Python under `profile/build/`. No collision.
- **Track A is the only one that touches `recipe.schema.json`.** Once A5
  lands, B and C consume the schema without modifying it.
- **Track D edits `Makefile` and `.github/.github/workflows/ci.yml`.** No
  other track writes to those files in Phase 3.
- **No cross-repo work in Phase 3 itself.** Recipes *invoke* tier-1 repos
  (`m new`, `m test`, etc.) as black boxes; they don't modify them.
- **Container/engine resources.** Recipes that exercise `m test` against
  Docker may collide on the default `m-test-engine` container name when
  multiple recipes run in parallel in CI. Each recipe declares
  `M_TEST_ENGINE_CONTAINER=mte-recipe-<slug>` in its setup block so two CI
  runners on the same host don't fight.

### Stage status conventions

Same as Phase 0 / Phase 1. Each stage is one of: `todo`, `doing`, `done`,
`blocked`. A stage is `done` only when its verification command exits 0.

---

## 2. Track A — Recipe schema + directory layout

Runs in `.github`. Single-session work; ~half-day.

### A1 — Audit existing recipe-shaped content

**Inputs read:** `profile/tools.json` `workflow` block (if any survives from
Phase 1's slimming — likely empty by now); the seven recipes listed in
parent plan §5.1.

**Output:** a 1-paragraph audit note in the PR description listing:

- Whether any of the seven recipes already exist anywhere in the org
  (`m-cli/docs/`, `m-stdlib/docs/`, `.github/docs/`) — if so, the new
  `docs/recipes/<slug>.md` either lifts or supersedes them.
- Which recipes are tier-1-only (1–5) vs tier-2-dependent (6) vs tier-3-
  dependent (7).
- The set of typed IDs each recipe is expected to reference (from
  `task_index.json` and `tools.json`).

**Verify:** audit note exists in PR body before A2 begins.

### A2 — Draft `profile/recipe.schema.json`

**Output:** new `profile/recipe.schema.json` — JSON Schema 2020-12.

Models recipe frontmatter (the YAML block at the top of every
`docs/recipes/<slug>.md`). Required fields:

| Field | Type | Notes |
|---|---|---|
| `id` | string | Typed ID, `^recipe:[a-z0-9_-]+$`. Matches §4.4 of parent plan. |
| `title` | string | Human-readable, ≤ 70 chars. |
| `intent` | string | Plain-English statement of what the recipe achieves. Matches one entry in `task_index.json`. |
| `touches` | array of typed IDs | Typed IDs the recipe references (`tool:m-cli`, `cmd:m-cli#test`, `module:m-stdlib#STDJSON`, etc.). The handshake test resolves these. |
| `prereqs` | array of typed IDs | Other recipes / tools that must succeed first. May be empty. |
| `verified_on` | string (ISO date) | Last date the recipe was run end-to-end and produced the documented result. |
| `ci_verifiable` | boolean | `true` if the recipe's commands can run unattended in CI. `false` requires a `manual_checklist_url` field. |

**Verify:**
```bash
check-jsonschema --schemafile <draft2020-meta> profile/recipe.schema.json
```

### A3 — Create `docs/recipes/` directory + README

**Output:** new `docs/recipes/README.md` describing the recipe contract,
the seven priority recipes, and the CI gate.

A `.gitkeep` is not needed because `README.md` populates the directory.

**Verify:** `ls docs/recipes/` shows `README.md`; `make check-docs-prose` is
green (README.md is `.md`, allowed).

### A4 — Add `task_index.json` entries for the seven intents

**Output:** edit to `profile/task_index.json` (the file split out in Phase 1
Track A4). Add one row per recipe linking intent → `recipe:<slug>` typed ID.

```json
{
  "intent": "scaffold a new M project with TDD and CI",
  "primary": "recipe:new-app-tdd-ci",
  "also": ["cmd:m-cli#new", "cmd:m-cli#ci-init"]
}
```

**Verify:** `make validate-catalog` is green after the edit.

### A5 — Commit and push

Single PR. Commit subject: `phase3-A: recipe schema + docs/recipes/ scaffold`.

**Verify:** PR merged; `recipe.schema.json` reachable via raw URL.

---

## 3. Track B — Author recipes 1–4

Runs in `.github`. Blocked by A5. Largest track by Markdown volume; smallest
by code volume (zero code).

Recipes are **executable, not stubs**. Each is one Markdown file under
`docs/recipes/` with the A2 frontmatter on top and a body that lists exact
commands and expected outputs. A recipe is "done" only when running its
commands top-to-bottom on a fresh clone produces the documented result.

### B1 — Recipe 1: `new-app-tdd-ci.md`

**Output:** `docs/recipes/new-app-tdd-ci.md`

End-to-end toolchain smoke. Verifies that the four-headed inner loop (`m new`
→ `m test` → `m fmt --check` → `m lint --error-on=error` → `m coverage
--min-percent=85`) works against a clean clone.

Body sections:

1. **Frontmatter** (per A2 schema).
2. **Prerequisites** — m-cli installed; `m doctor` green.
3. **Commands** — exact, copy-paste-able:

   ```bash
   m new fetcher
   cd fetcher
   m test                         # expected: green
   m fmt --check                  # expected: no diff
   m lint --error-on=error        # expected: zero findings
   m coverage --min-percent=85    # expected: ≥ 85%
   ```

4. **Expected outputs** — verbatim final-line excerpts from each command.
5. **Failure triage** — one paragraph linking to `recipe:investigate-failure`.

**Verify:** run the recipe top-to-bottom on a fresh `mktemp -d` directory;
all five commands exit 0.

### B2 — Recipe 2: `use-stdlib-module.md`

**Output:** `docs/recipes/use-stdlib-module.md`

Agent-facing: how to look up a `STD*` API, find an example, and call it
from M code. Worked example: parse JSON via `STDJSON`.

Body:

1. **Frontmatter** — `touches: [module:m-stdlib#STDJSON, cmd:m-cli#test]`.
2. **Lookup path** — fetch `tools.json` → resolve `module:m-stdlib#STDJSON`
   → follow `manifest_url` → find `STDJSON` entry → read `signature` +
   `example` fields.
3. **Worked example** — a 10-line `.m` routine that calls `parse^STDJSON`
   and tests the result via `^STDASSERT`.
4. **Verification** — `m test FILE.m` is green.

**Verify:** the worked example runs green in `mktemp -d`.

### B3 — Recipe 3: `add-stdlib-module.md`

**Output:** `docs/recipes/add-stdlib-module.md`

Repo-side recipe (TDD for STD\* modules). Steps:

1. Open issue in `m-stdlib` proposing the module.
2. Write `<MODULE>TST.m` first; confirm RED.
3. Implement `<MODULE>.m`.
4. Run `m test`; confirm green.
5. Run `m coverage --min-percent=85`.
6. Regenerate `dist/repo.meta.json` via `make manifest`; confirm
   `make check-manifest` is green.
7. PR with squash-merge.

**Verify:** dry-run the recipe against a throwaway module name; confirm
each step is executable.

### B4 — Recipe 4: `add-lint-rule.md`

**Output:** `docs/recipes/add-lint-rule.md`

Repo-side recipe for `m-cli`. Mirrors B3's TDD shape but for a single
`register(Rule(...))` block in `src/m_cli/lint/rules.py` (XINDEX track) or
`src/m_cli/lint/_modern.py` (M-MOD track). Includes regeneration of
`dist/lint-rules.json` and the `make check-manifest` drift gate.

**Verify:** dry-run against a throwaway rule ID; confirm each step works.

### B5 — Commit and push

One or two PRs (recipes 1–2 ship first for review; 3–4 follow). Commit
subject for the main PR: `phase3-B: recipes 1–4 (new-app, use-stdlib,
add-stdlib, add-lint-rule)`.

**Verify:** PRs merged; all four `.md` files exist under `docs/recipes/`
with valid frontmatter (validated by Track D's CI step).

---

## 4. Track C — Discovery handshake test

Runs in `.github`. Blocked by A5. TDD. The single check that proves the
discovery system works end-to-end.

### C1 — TDD: tests for `test-discovery-protocol.py`

**Output:** `profile/build/test_discovery_protocol.py` (pytest)

Fixtures: a frozen snapshot of `tools.json` + `task_index.json` + one tier-1
`repo.meta.json` + one `exposes` payload. Drive each step of the handshake
against the fixtures, then against the live URLs.

Test cases:

- Intent "parse JSON in M" resolves to `module:m-stdlib#STDJSON`.
- The pointed-at manifest URL fetches; the module entry has `signature` +
  `example` fields.
- A broken link in `llms.txt` causes the script to exit non-zero.
- A schema violation in `tools.json` causes the script to exit non-zero.
- A typed ID with the wrong grammar fails the `typedID` regex.

Confirm RED before C2.

### C2 — Implement `test-discovery-protocol.py`

**Output:** `profile/build/test-discovery-protocol.py`

Steps (per parent plan §5.2):

```python
1. Fetch llms.txt → parses, all links resolve.
2. Fetch tools.json → validates against tools.schema.json.
3. Match a sample intent against task_index ("parse JSON in M").
4. Resolve the primary typed ID through tools.json.
5. Fetch the pointed-at manifest (e.g. stdlib-manifest.json).
6. Find STDJSON in the manifest → assert it has signature + example.
7. Print the routing trail; fail on any broken link or schema violation.
```

The script accepts `--offline` (use bundled fixtures) and `--live` (default;
hit raw GitHub URLs). CI runs `--live`; local dev defaults to `--live` but
falls back to `--offline` if network is unavailable (warn, don't fail).

**Verify:** C1 tests green; `python3 profile/build/test-discovery-protocol.py`
exits 0 against current `main`.

### C3 — Recipe runner (lightweight)

**Output:** `profile/build/run-recipe.py`

Reads a recipe Markdown file, validates frontmatter against
`recipe.schema.json`, extracts the command block, and shells out to each
command in a `mktemp -d` directory. Pipes stdout/stderr; asserts exit 0;
diffs against the recipe's documented "expected output" excerpt.

Used in Track D's CI step to gate every PR on the four required recipes.

**Verify:** `python3 profile/build/run-recipe.py docs/recipes/new-app-tdd-ci.md`
exits 0.

### C4 — Determinism + idempotency check

Run the handshake test twice in a row; assert the routing trail printed on
the second run is byte-identical to the first (modulo timestamps). Then
artificially corrupt one tier-1 `repo.meta.json` payload in a fixture;
assert the handshake test fails with a specific exit code (not just non-zero).

**Verify:** both checks pass.

### C5 — Commit and push

One PR. Commit subject: `phase3-C: test-discovery-protocol + run-recipe
(TDD)`.

**Verify:** PR merged; `profile/build/` contains both scripts + tests.

---

## 5. Track D — Make targets + CI wiring

Runs in `.github`. Blocked by B5 (recipes 1–4 exist) and C5 (scripts exist).

### D1 — Add `make recipes-check` target

**Output:** addition to `.github/Makefile`.

```makefile
recipes-check:
	@for r in docs/recipes/*.md; do \
	  python3 profile/build/run-recipe.py "$$r" || exit 1; \
	done
```

Runs the recipe runner over every Markdown file under `docs/recipes/`. If
any recipe fails (broken command, exit-code mismatch, output diff), the
target fails.

**Verify:** `make recipes-check` is green against the four recipes from
Track B.

### D2 — Add `make handshake` target

**Output:** addition to `.github/Makefile`.

```makefile
handshake:
	python3 profile/build/test-discovery-protocol.py --live
```

**Verify:** `make handshake` is green against current `main`.

### D3 — Wire into CI

**Output:** edit to `.github/.github/workflows/ci.yml`.

Add two new steps after the Phase 1 catalog gates:

```yaml
- name: Run discovery handshake
  run: make handshake
- name: Run recipes (executable docs)
  run: make recipes-check
```

Add a weekly scheduled trigger so the handshake runs on a cron to catch
external link rot between PRs (the lightweight version of Phase 5's
freshness gate — Phase 3 ships only the daily/PR-time check, not the full
weekly health report):

```yaml
on:
  push:
  pull_request:
  schedule:
    - cron: '0 12 * * 1'   # Mondays 12:00 UTC — weekly link-check
```

**Verify:** push a branch; CI passes. Push a deliberately broken recipe
(typo in `m new` invocation); CI fails. Revert.

### D4 — Commit and merge

Single PR. Commit subject: `phase3-D: make recipes-check + handshake wired
into CI`.

**Verify:** PR merged; CI green on `main`.

---

## 6. Track E — Phase 3 smoke + evidence

Runs in `.github`. Blocked by D4.

### E1 — Phase 3 smoke

**Output:** evidence file `docs/phase3-evidence.txt`.

```bash
make catalog && make validate-catalog && make handshake && make recipes-check \
  | tee docs/phase3-evidence.txt
```

**Verify:** all four targets exit 0; evidence file captures the routing
trail printed by `make handshake` and the per-recipe pass lines from
`make recipes-check`.

### E2 — Update `phase3-status.md`

**Output:** `docs/phase3-status.md` (analogous to `phase0-status.md`).

Single file recording stage-by-stage status, blockers resolved, and a
"Next" section pointing at Phase 4 (MCP server). Mark Phase 3 closed when
all stages in §7's matrix are `done`.

**Verify:** doc exists; every stage in §7 is marked `done`.

### E3 — Close-out PR

Single PR. Commit subject: `phase3-E: smoke + evidence; Phase 3 closed`.

**Verify:** PR merged; `phase3-evidence.txt` and `phase3-status.md` on
`main`; Phase 4 unblocked.

---

## 7. Stage Matrix — Single-Glance View

| Stage | Repo | Blocked by | Verification |
|---|---|---|---|
| A1 | .github | Phase 1 D5 | audit note in PR body |
| A2 | .github | A1 | `recipe.schema.json` validates as JSON Schema 2020-12 |
| A3 | .github | A2 | `docs/recipes/README.md` exists; `check-docs-prose` green |
| A4 | .github | A3 | `make validate-catalog` green after `task_index.json` edit |
| A5 | .github | A4 | PR merged; `recipe.schema.json` reachable via raw URL |
| B1 | .github | A5 | recipe 1 runs green on fresh `mktemp -d` |
| B2 | .github | A5 | recipe 2 runs green on fresh `mktemp -d` |
| B3 | .github | A5 | recipe 3 dry-run against throwaway module |
| B4 | .github | A5 | recipe 4 dry-run against throwaway rule ID |
| B5 | .github | B1, B2, B3, B4 | PR merged; four `.md` files under `docs/recipes/` |
| C1 | .github | A5 | RED tests |
| C2 | .github | C1 | C1 tests green |
| C3 | .github | C2 | `run-recipe.py` exits 0 on recipe 1 |
| C4 | .github | C3 | determinism + corruption checks pass |
| C5 | .github | C4 | PR merged; both scripts + tests under `profile/build/` |
| D1 | .github | B5, C5 | `make recipes-check` exits 0 |
| D2 | .github | B5, C5 | `make handshake` exits 0 |
| D3 | .github | D1, D2 | CI green on branch; negative test fails |
| D4 | .github | D3 | PR merged; CI green on `main` |
| E1 | .github | D4 | `phase3-evidence.txt` captures clean run |
| E2 | .github | E1 | `phase3-status.md` exists; all stages `done` |
| E3 | .github | E2 | PR merged; Phase 4 unblocked |

---

## 8. Calling Convention

Same shape as phase0/phase1.

- **`run A`** — execute Track A end-to-end.
- **`run B`** — execute Track B end-to-end (only after A5).
- **`run B2`** — execute only stage B2.
- **`run B through B4`** — B1, B2, B3, B4 in sequence.
- **`run B+C in parallel`** — spawn two independent sessions; different
  files, no collision risk.
- **`resume C from C3`** — continue from a checkpoint; assumes C1–C2 done.

A Claude session given a track callout should:

1. Read this document.
2. Confirm the blocking stage(s) are `done` per `phase3-status.md`.
3. Execute its stages in order.
4. Run the verification command at the end of each stage; halt on failure.
5. Report the final state when the track (or named substage) completes.

Do **not** advance a stage whose verification didn't exit 0. Halt and report.

### Recommended order

If executing single-threaded:

1. **A** (foundation — schema + directory).
2. **B and C in parallel** (B = recipes; C = handshake test).
3. **D** (Make + CI wiring; integrates B and C).
4. **E** (smoke + evidence; close-out).

If you can only ship part of Phase 3, ship **A + recipe 1 (`new-app-tdd-ci`)
+ Track C + Track D**. That alone delivers the §13 success criterion (an
agent can run the most important recipe end-to-end and the handshake test
gates CI). The other three recipes can ship as follow-up PRs without
re-opening Phase 3.

---

## 9. Risk Notes

- **Recipes are documentation that runs.** A recipe that lints clean in
  Markdown review but breaks against current tier-1 CLIs is silently broken
  until CI runs. Mitigation: Track D's `make recipes-check` runs the recipe
  body in a `mktemp -d` on every PR, not just at recipe-authoring time.
- **Tier-1 CLI surface drift breaks recipes.** If `m new`, `m test`, etc.
  rename flags or change exit-code semantics, recipes break. Mitigation:
  `verified_on` in recipe frontmatter must be updated whenever the recipe
  is re-run; CI's recipe gate makes that recurrence automatic.
- **External link rot.** Recipes reference raw-GitHub URLs that can rot if
  a tier-1 repo renames a file. Phase 3 gates against this at PR time and
  weekly via cron; the full freshness report (badged on the README) is
  Phase 5.
- **Network in CI.** Both `make handshake` and `make recipes-check` need
  network. GitHub Actions has network; local dev usually does. Document
  the `--offline` flag for `test-discovery-protocol.py` so local
  development without network can still validate the schema-bound parts.
- **Container collision in CI.** Recipes 1 and 3 may both shell out to
  `m test` against Docker. If a CI runner reuses host state across jobs,
  `m-test-engine` container-name collisions could surface. Mitigation:
  each recipe sets `M_TEST_ENGINE_CONTAINER=mte-recipe-<slug>` in its
  setup block; the `m-cli` engine resolver already respects that env var.
- **Phase 2 soft-blocker for recipes 6–7.** Recipe 6 (`investigate-
  failure`) shows how to use tree-sitter-m parser output; recipe 7
  (`add-editor-support`) touches the VS Code extension manifest. Both
  reference tier-2/tier-3 typed IDs not yet in the catalog. Defer to
  follow-up PRs, not Phase 3.
- **Schema-changelog discipline.** Adding `recipe.schema.json` is an
  *additive* change to the org-level schema set. No `schema_compat` bump
  needed, but a row in `schema-changelog.md` (Phase 1 deliverable, lands
  before Phase 3 starts) documenting the new schema is required.

---

## 10. Phase 3 Done — Definition

Phase 3 is done when **all** of these are true:

1. `profile/recipe.schema.json` exists and validates against JSON Schema
   2020-12.
2. `docs/recipes/` contains at least **4** `.md` files (recipes 1–4) with
   valid frontmatter that validates against `recipe.schema.json`.
3. `profile/build/test-discovery-protocol.py` exists, is TDD-covered, and
   exits 0 against live `main` URLs.
4. `profile/build/run-recipe.py` exists, is TDD-covered, and exits 0 on
   each of recipes 1–4.
5. `make handshake` and `make recipes-check` are real Make targets that
   delegate to the scripts above.
6. `.github/.github/workflows/ci.yml` runs both targets on every push/PR
   AND on a weekly cron schedule.
7. CI is green on `.github/main`.
8. `docs/phase3-evidence.txt` captures a clean run of `make catalog &&
   make validate-catalog && make handshake && make recipes-check` and is
   committed to `main`.
9. `docs/phase3-status.md` shows every stage in §7's matrix marked `done`.
10. `task_index.json` contains intent rows pointing at `recipe:*` typed IDs
    for at least the four shipped recipes.

When all ten are true, Phase 4 (tier-3 repos + MCP server) is unblocked.
Recipes 5–7 may continue to land as independent PRs without re-opening
Phase 3.
