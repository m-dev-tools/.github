# Phase 0 — Status

Companion to [`phase0-plan.md`](phase0-plan.md). Records concrete stage
progress.

**Last updated:** 2026-05-10 (Phase 0 closed — all PRs merged, smoke green on `main`)

## ✅ Phase 0 complete

`make phase0-smoke` green against `main` URLs. All twelve cross-repo
`exposes` pointers (2 m-stdlib + 7 m-standard + 3 m-cli) resolve and
parse. The Phase 0 exit criterion is met.

## Stage status

| Stage | Status | Notes |
|---|---|---|
| A1 | done | `profile/repo.meta.schema.json` shipped at `0469fe4`. |
| A2 | done | `profile/repo.meta.example.json` shipped at `0469fe4`. |
| A3 | done | `profile/build/validate-repo-meta.py` shipped at `0469fe4`; path resolution fixed at `e8be174` (walks `.git` ancestor / strips raw URL to branch base). |
| A4 | done | `make check-repo-meta META=…` target in `.github/Makefile` at `0469fe4`. |
| A5 | done | `.github/main` carries A1–A4 + tracker cleanup + validator fix. Schema URL `raw.githubusercontent.com/m-dev-tools/.github/main/profile/repo.meta.schema.json` resolves. |
| B1–B5 | done | Captured in `phase0-B-repo-meta` commit body. |
| B6 | **merged** | PR #2 squash-merged to m-stdlib `main`. Branch deleted on origin. |
| C1–C5 | done | Captured in `phase0-c-repo-meta` commit body. |
| C6 | **merged** | PR #5 squash-merged to m-standard `main`. Branch deleted on origin. |
| D1–D9 | done | Captured in `phase0-D` commit bodies (commands/lint-rules/fmt-rules introspection + drift gate + AGENTS.md adoption). |
| D10 | **merged** | PR #8 squash-merged to m-cli `main`. Branch deleted on origin. Three commits squashed: `8908508` (capabilities) + `f516e76` (drift-gate gotchas) + `aa52ae8` (repo-root path convention). |
| E1 | done | TIER_1 production URLs pinned in `profile/build/phase0-smoke.py`. |
| E2 | done | `profile/build/phase0-smoke.py` written; reuses `validate-repo-meta.py`'s validation logic. |
| E3 | done | `make phase0-smoke` target in `.github/Makefile`; `URLS=…` override supported. |
| E4 | **done** | **3/3 PASS** against `main` URLs (the production target). Feature-branch dry-run was 3/3 pre-merge. |
| E5 | done | Track E artifacts committed at `.github` `7f60dcd`. |

## Resolved follow-ups

1. **A4 status.** Confirmed done at `0469fe4`.
2. **Validator path resolution.** Fixed at `e8be174`. Both modes
   verified with positive, negative, and no-`.git`-fallback tests.
3. **m-cli manifest path convention.** Fixed at m-cli `aa52ae8`
   (folded into the squashed PR #8 merge commit on m-cli `main`).
4. **m-stdlib `tools/gen-manifest.py` changelog drift.** Bundled
   into the Track B squashed commit on m-stdlib `main`.
5. **Drift-gate gotchas surfaced on m-cli PR #8** (plugin-leak from
   maintainer's venv; argparse `required` cross-version variance).
   Captured in m-cli `f516e76` and in
   `~/claude/memory/feedback_manifest_drift_gotchas.md` for future
   manifest-drift work.

## Outstanding follow-ups (Phase 0 cleanup, non-blocking)

1. **Local feature branches still exist** in each repo's local clone
   even though origin deleted them. Optional cleanup:
   ```bash
   cd m-stdlib && git checkout main && git pull && git branch -D phase0-B-repo-meta
   cd m-standard && git checkout main && git pull && git branch -D phase0-c-repo-meta
   cd m-cli && git checkout main && git pull && git branch -D phase0-D
   ```

## Next

Phase 1 — org routing layer. See
[`AI-discoverability-plan.md`](AI-discoverability-plan.md) §7 Phase 1:

- `repo.meta.schema.json` already exists (lands in this phase
  formally, but already in production from Phase 0).
- Tighten `tools.schema.json`: typed-ID regex,
  `additionalProperties: false`, `task_index` inner schema.
- Write `profile/build/build-catalog.py` — reads each tier-1
  `dist/repo.meta.json` from the catalog's TIER_1 list, follows
  `exposes` pointers, emits summary into a regenerated
  `profile/tools.json`.
- Split out `profile/task_index.json` from `tools.json` as the only
  hand-curated routing source.
- Migrate `llms.txt` to strict llmstxt.org format.
- Wire `make catalog`, `make validate-catalog`, and CI.

Phase 1 exit: `make catalog && make validate-catalog` green;
`tools.json` no longer contains hand-maintained subcommand /
module / rule lists.
