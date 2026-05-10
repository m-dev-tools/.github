# Phase 0 — Status

Companion to [`phase0-plan.md`](phase0-plan.md). Records concrete stage
progress so any resuming session can pick up without re-discovering
state.

**Last updated:** 2026-05-10 (session 3 — validator path-resolution fix)

## Stage status

| Stage | Status | Notes |
|---|---|---|
| A1 | done | `profile/repo.meta.schema.json` shipped at `0469fe4`. |
| A2 | done | `profile/repo.meta.example.json` shipped at `0469fe4`; updated to repo-root path (`profile/repo.meta.schema.json`). |
| A3 | done | `profile/build/validate-repo-meta.py` shipped at `0469fe4`; **path resolution fixed this session** — walks `.git` ancestor for path mode, strips raw-GitHub URL to branch base for URL mode. Both modes tested. |
| A4 | done | `make check-repo-meta META=…` target in `.github/Makefile`. |
| A5 | done | Pushed; origin/main carries A1–A4 + tracker cleanup. Schema URL `raw.githubusercontent.com/m-dev-tools/.github/main/profile/repo.meta.schema.json` resolves. |
| B1–B5 | done | Captured in `phase0-B-repo-meta` commit body. |
| B6 | done (branch) | Branch `phase0-B-repo-meta` pushed @ `03ef40a`; **PR not yet opened/merged**. |
| C1–C5 | done | Out-of-session work (commit `ceb7c08`). |
| C6 | done (branch) | Branch `phase0-c-repo-meta` pushed @ `ceb7c08`; **PR not yet opened/merged**. |
| D1–D9 | done | Out-of-session work (commit `8908508`); `m capabilities --json` implemented; `dist/commands.json`, `dist/lint-rules.json`, `dist/fmt-rules.json` present. |
| D10 | done (branch) | Branch `phase0-D` pushed @ `8908508`; **PR not yet opened/merged**. |
| E1 | done | TIER_1 production URLs pinned in `profile/build/phase0-smoke.py`. |
| E2 | done | `profile/build/phase0-smoke.py` written; reuses `validate-repo-meta.py`'s inline-validation fallback. |
| E3 | done | `make phase0-smoke` target in `.github/Makefile`; supports `URLS=…` override for dry-runs. |
| E4 | partial | Dry-run against feature branches: 2/3 pass (m-stdlib ✓, m-standard ✓, m-cli ✗ — see follow-up #1). Full pass against `main` URLs blocked on PR merges. |
| E5 | **todo** | Commit + push Track E artifacts (status doc + smoke script + Makefile target) once main is unblocked. |

## Resolved follow-ups

1. **A4 status.** Confirmed done at `0469fe4`.
2. **Validator path resolution.** Fixed this session. Both modes
   verified: path mode (`.git` ancestor walk → repo root, fallback to
   manifest dir for fixtures outside a repo) and URL mode (regex strip
   `https://raw.githubusercontent.com/<org>/<repo>/<branch>/`). Three
   tests pinned: positive resolve, missing-path negative, no-`.git`
   fallback. m-stdlib's `dist/stdlib-manifest.json` and m-standard's
   `docs/integrated/*.tsv` paths now resolve without `--no-resolve`.

## Outstanding follow-ups

1. **m-cli manifest paths inconsistent with the plan.** `m-cli`'s
   `dist/repo.meta.json` uses bare filenames (`"commands": "commands.json"`)
   while plan §5 D8 specifies `dist/commands.json` and the validator's
   new repo-root resolution requires the `dist/` prefix. Fix in the
   `phase0-D` branch before opening the PR:
   ```json
   "commands":   "dist/commands.json",
   "lint_rules": "dist/lint-rules.json",
   "fmt_rules":  "dist/fmt-rules.json"
   ```
   After this, E4's smoke dry-run will be 3/3 against feature-branch URLs.

2. **B/C check-manifest target may pass `--no-resolve`** as a leftover
   workaround. With the validator fixed, those targets can drop the
   flag in a small follow-up commit on each branch (or as part of PR
   review).

3. **Auto-classifier blocks direct push to `.github/main`.** The
   user/system rule wants explicit human authorization for changes to
   `.github`'s main branch. This file (and the Track A path-resolution
   fix) need explicit "yes push" rather than the proactive
   commit-push-by-default behavior used elsewhere.

4. **m-stdlib side-fix bundled in `03ef40a`.** `tools/gen-manifest.py`
   updated to read `docs/tracking/changelog.md` (relocated from
   repo-root `CHANGELOG.md`); restores empty `stdlib_version` and
   makes `make manifest-check` green on fresh clones.

## Branches in flight

- `m-dev-tools/.github` @ `main` — Track A merged. **Pending commit
  this session:** validator path-resolution fix + schema description
  refresh + example.json path update + this status doc.
- `m-dev-tools/m-stdlib` @ `phase0-B-repo-meta` — pushed @ `03ef40a`; PR pending.
- `m-dev-tools/m-standard` @ `phase0-c-repo-meta` — pushed @ `ceb7c08`; PR pending.
- `m-dev-tools/m-cli` @ `phase0-D` — pushed @ `8908508`; PR pending. Needs the manifest-path fix (#1 above) before merge.

## Resume points

- **Commit + push the .github path-resolution fix** (this session's work).
- **Fix m-cli manifest paths** in `phase0-D` branch.
- **Re-run E4 dry-run** after m-cli fix; should be 3/3.
- **Open PRs for B, C, D** (`gh pr create` in each repo).
- **E5:** commit + push the Track E artifacts once PRs merge to main.
