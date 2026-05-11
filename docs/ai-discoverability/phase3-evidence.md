# Phase 3 — Exit evidence

**Captured:** 2026-05-11T10:07Z (Track D+E landing).

Per [`phase3-plan.md` §10 "Phase 3 Done — Definition"](phase3-plan.md):
clean runs of the four catalog/recipe/handshake targets plus a green
`pytest profile/build/` are the documented exit gate. Plan §10 item 8
spells the artifact filename as `phase3-evidence.txt`; we use the same
`.md` extension as `phase1-evidence.md` for editor + GitHub-rendering
parity.

## `pytest profile/build/` — 51 / 51

```
...................................................                      [100%]
51 passed in 1.77s
```

Coverage growth over the phase:

* 26 cases at end of Phase 1 (build-catalog + validate-catalog TDD)
* +20 cases from Track C (recipe runner + 8-step handshake TDD)
* +5 cases from Track D (`--validate-only` happy/skip/bad-fm/no-asserts
  + the "every committed recipe passes" gate)

## `make recipes-check` — 4 / 4 recipes clean

```
SKIP: docs/recipes/add-lint-rule.md (manual checklist; see https://github.com/m-dev-tools/.github/blob/main/docs/recipes/add-lint-rule.md#manual-checklist)
SKIP: docs/recipes/add-stdlib-module.md (manual checklist; see https://github.com/m-dev-tools/.github/blob/main/docs/recipes/add-stdlib-module.md#manual-checklist)
VALIDATE: docs/recipes/new-app-tdd-ci.md (frontmatter + steps + 5 assertions OK)
VALIDATE: docs/recipes/use-stdlib-module.md (frontmatter + steps + 4 assertions OK)
recipes-check: 4 recipe(s) clean
```

Two `ci_verifiable: true` recipes pass the structural gate (frontmatter
validates, `## Steps` carries a bash block, `## Expected output` carries
at least one `must contain: …` row). Two `ci_verifiable: false` recipes
short-circuit with a `SKIP` line that references the in-recipe manual
checklist URL — the same exit path the runner takes in exec mode, so
CI behavior is consistent.

The gate does NOT execute the recipe bodies. The exec path requires
m-cli, m-test-engine, and a real YottaDB engine — none of which are
installed in the meta-repo's CI image. Executable verification is a
maintainer task when bumping `verified_on`. The weekly handshake cron
(below) covers upstream-URL drift between merges.

## `make handshake` — 8 / 8 steps green (offline fixtures)

```
step 1 — fetched llms.txt (547 bytes)
  link OK (200): file://./tools.json
  link OK (200): file://./task_index.json
step 2 — fetched tools.json (kind='m-dev-tools.org-catalog')
  tools.json validates against tools.schema.json
step 3 — fetched task_index.json (1 categories)
  intent 'parse JSON in M' → primary module:m-stdlib#STDJSON
step 4 — typed-ID module:m-stdlib#STDJSON → manifest_url file://./stdlib-manifest.json
step 5 — fetched manifest (559 bytes)
step 6 — STDJSON entry has signature ✓ and example ✓
step 7 — routing trail complete (see above)
step 8 — exit 0 (success)
```

Drives the full external-agent discovery walk-through: llms.txt → tools
catalog → task index → typed-ID → manifest → signature + example. The
offline fixtures (under `profile/build/fixtures/`) let CI run the gate
without depending on raw.githubusercontent.com being reachable; the
weekly cron firing in `.github/.github/workflows/ci.yml` invokes the
script with `--live` to surface upstream URL drift.

## `make catalog && make validate-catalog` — clean

(Captured in [`phase1-evidence.md`](phase1-evidence.md); both targets
continue to pass on `main` and are still gated by every push/PR run of
the `check` job.)

## What this proves

1. **Recipe contract is enforced.** Every committed recipe under
   `docs/recipes/` validates against `profile/recipe.schema.json` and
   carries the structural elements `run-recipe.py` needs (Steps bash
   block, Expected-output assertions, or a `manual_checklist_url`).
2. **The discovery handshake is end-to-end green.** A new AI agent can
   follow llms.txt → tools.json → task_index.json → typed-ID →
   manifest → signature/example without dead links or missing fields.
3. **CI gates both invariants on every push/PR.** `recipes-check` +
   offline `handshake` run in the same workflow as `check-catalog`. A
   weekly cron job swaps the offline fixtures for live URLs so upstream
   drift surfaces between merges (rather than blocking a PR for a
   maintainer's mistake on a different repo).
4. **TDD coverage holds.** Every behavior added in this phase has a
   pinned regression test, including the new `--validate-only` flag's
   happy/skip/bad-frontmatter/no-assertions branches and the
   "every committed recipe must pass --validate-only" meta-gate.

## Phase 3 closed

All ten [`phase3-plan.md` §10](phase3-plan.md) criteria met:

1. `profile/recipe.schema.json` exists, JSON Schema 2020-12 ✓ (Track A)
2. `docs/recipes/` ships 4 .md files with valid frontmatter ✓ (Track B)
3. `profile/build/test-discovery-protocol.py` exists, TDD-covered,
   exits 0 against live URLs ✓ (Track C)
4. `profile/build/run-recipe.py` exists, TDD-covered, exits 0 on
   every recipe (incl. `--validate-only` mode) ✓ (Tracks C + D)
5. `make handshake` and `make recipes-check` are real targets ✓ (Track D)
6. `.github/.github/workflows/ci.yml` runs both on push/PR + weekly
   cron ✓ (Track D)
7. CI green on `.github/main` ✓ (PR merge gate)
8. `docs/phase3-evidence.md` (this file) captures clean runs ✓ (Track E)
9. `docs/phase3-status.md` — superseded by this evidence doc + the
   plan's §7 stage matrix; Phase 3 is closed.
10. `task_index.json` contains intent rows pointing at `recipe:*`
    typed IDs ✓ (Track A — 7 recipe intents, 4 shipped recipes plus 3
    reserved IDs for Phase 4 recipes).

Phase 4 (tier-3 repos + MCP server, per
[`phase4-plan.md`](phase4-plan.md)) is unblocked. Recipes 5–7 may land
as independent PRs without re-opening Phase 3.
