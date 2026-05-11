# m-dev-tools recipes

CI-verifiable, end-to-end developer workflows for the m-dev-tools stack.
Each recipe is one Markdown file under this directory with YAML
frontmatter (schema: [`profile/recipe.schema.json`](../../profile/recipe.schema.json))
and a body that runs top-to-bottom on a fresh clone.

A recipe is "done" only when running its commands in order on a clean
machine produces the documented result. The Phase-3 discovery handshake
test (`profile/build/test-discovery-protocol.py`, landing in Phase-3
Track C) executes each `ci_verifiable: true` recipe and gates on its
success.

## What a recipe looks like

```markdown
---
id: recipe:new-app-tdd-ci
title: Scaffold a new M project with TDD + CI in 60 seconds
intent: Start a new M project with TDD and CI scaffolding
touches:
  - cmd:m-cli#new
  - cmd:m-cli#test
  - cmd:m-cli#fmt
  - cmd:m-cli#lint
  - cmd:m-cli#coverage
  - cmd:m-cli#ci
  - tool:m-test-engine
  - module:m-stdlib#STDASSERT
prereqs: []
verified_on: 2026-05-11
ci_verifiable: true
tier: tier-1
---

# Scaffold a new M project with TDD + CI

…recipe body: step-by-step shell commands, expected outputs, link to the
exit assertion…
```

Frontmatter contract:

| Field | Required? | Notes |
|---|---|---|
| `id` | yes | Typed `recipe:<slug>`. Slug matches filename (`new-app-tdd-ci` → `new-app-tdd-ci.md`). |
| `title` | yes | ≤ 70 chars. |
| `intent` | yes | Matches at least one entry in [`profile/task_index.json`](../../profile/task_index.json). |
| `touches` | yes (≥1) | Typed IDs the recipe references. The handshake test resolves each through `tools.json`. |
| `prereqs` | no | Other recipe / tool typed-IDs that must succeed first. |
| `verified_on` | yes | ISO date the recipe was last run end-to-end. Phase-5 freshness gate rejects > 90 days old. |
| `ci_verifiable` | yes | `true` if commands run unattended in CI. `false` requires `manual_checklist_url`. |
| `manual_checklist_url` | conditional | Required iff `ci_verifiable: false`. |
| `tier` | no | `tier-1` / `tier-2` / `tier-3`. Determines which Phase ships the recipe (recipes 1–5 are tier-1; #6 is tier-2; #7 is tier-3). |
| `notes` | no | Free-text, not consumed mechanically. |

## The seven priority recipes

Per [`AI-discoverability-plan.md` §5.1](../AI-discoverability-plan.md) and
the [Phase-3 implementation plan](../phase3-plan.md):

| # | Slug | Tier | Phase-3 status | What it proves |
|---|---|---|---|---|
| 1 | `new-app-tdd-ci` | tier-1 | gating (Track B) | Whole-stack scaffold → red test → green → CI passes |
| 2 | `use-stdlib-module` | tier-1 | gating (Track B) | Agent looks up `parse^STDJSON` and calls it correctly |
| 3 | `add-stdlib-module` | tier-1 | gating (Track B) | Author a new STD* module with TDD; manifest regenerates |
| 4 | `add-lint-rule` | tier-1 | gating (Track B) | Ship a new `M-MOD-*` rule with fixer linkage; cliff falls right |
| 5 | `add-m-cli-command` | tier-1 | buffer (Track B if budget allows) | New subcommand registered; `m capabilities --json` picks it up |
| 6 | `investigate-failure` | tier-2 | **post-exit** | Standard triage path when `m test` is red |
| 7 | `add-editor-support` | tier-3 | **post-exit** | Extend the VS Code extensions with a new file association / setting |

Phase-3 exit per [`phase3-plan.md`](../phase3-plan.md): at least **4 of
the 7** are written + executable + CI-verified. Recipes 1–4 are the
exit set; #5 is buffer; #6 + #7 land after Phase 3 closes.

## CI gate (Phase-3 Track D)

`make recipes-check` runs from `.github`'s working tree on every
push/PR. For each `*.md` under this directory:

1. Validate frontmatter against `recipe.schema.json`.
2. Assert every typed ID in `touches` and `prereqs` resolves through
   `tools.json` + `task_index.json`.
3. Assert `intent` matches at least one entry in `task_index.json`.
4. If `ci_verifiable: true`, exec the body's command block in a fresh
   environment and assert exit 0 + expected output.
5. Link-check every URL in the body (HEAD; HTTP 200 required).

The handshake test (`profile/build/test-discovery-protocol.py`) drives
the whole chain end-to-end: pick an intent → resolve to typed ID →
follow to recipe → run recipe → assert exit code.

## Authoring a new recipe

1. Pick the slug — must match an existing `intent` in
   `task_index.json` (or add one via the same PR).
2. Write `docs/recipes/<slug>.md` with the frontmatter above.
3. Run `make recipes-check` locally — fixture-level validation only;
   the CI step does the full exec.
4. Bump `verified_on` to today on every edit. If the body changes,
   re-run the command sequence top-to-bottom and confirm before
   bumping.
5. Open a PR. The recipe joins the catalog on merge.

## Naming + slug conventions

- Slug pattern: `^[a-z0-9_-]+$` (matches the typedID regex's slug
  group).
- Slug → filename → typed `recipe:<slug>` ID are 1:1.
- One H1 in the body: same text as `title` is conventional but not
  enforced.
- Section headers under `## Setup` / `## Steps` / `## Verify` /
  `## Cleanup` are the recommended shape; not yet schema-enforced.

## What this directory is NOT

- A general documentation tree. That's [`../`](../) — for plans,
  guides, and history.
- A test corpus. That's `m-modern-corpus` (and, by reach, the VistA
  corpus surfaced via `tree-sitter-m`).
- A tutorial. Recipes are mechanically-runnable; tutorials are prose
  that explains why. The user-facing guide lives in
  [`../AI-discoverability-guide.md`](../AI-discoverability-guide.md).
