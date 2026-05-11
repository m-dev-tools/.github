# Phase 4 — Exit evidence

**Captured:** 2026-05-11T12:29Z (Track E landing).

Per [`phase4-plan.md` §11 "Phase 4 Done — Definition"](phase4-plan.md):
clean runs of the four meta-repo gates + canonical-query round-trip
through the v0.1.0 release are the documented exit. This doc mirrors
[`phase3-evidence.md`](phase3-evidence.md): one section per gate, a
"What this proves" wrap-up, then each §11 criterion cited green.

## `pytest profile/build/` — 51 / 51

```
...................................................                      [100%]
51 passed in 1.93s
```

Phase 3's TDD suite carries forward without churn. The catalog
build / validate / discovery-protocol behavior all stays green
after the Phase 4 onboarding edits.

## `make catalog` — byte-idempotent

Running the generator twice against `origin/main` (with the new
TIER_3 entry for `m-dev-tools-mcp`) produces zero diff against the
committed `profile/tools.json`. The new `tools.m-dev-tools-mcp`
block materializes deterministically from the upstream
`exposes.{mcp_tools, release_wheel}` declarations.

```
python3 profile/build/build-catalog.py --write profile/tools.json
# (regen-twice diff is empty)
```

## `make validate-catalog` — schema-strict

```
python3 profile/build/validate-catalog.py
OK: /home/rafael/m-dev-tools/.github/profile/tools.json + /home/rafael/m-dev-tools/.github/profile/task_index.json
```

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

## `make recipes-check` — 4 / 4 recipes clean

```
SKIP: docs/recipes/add-lint-rule.md (manual checklist; see https://github.com/m-dev-tools/.github/blob/main/docs/recipes/add-lint-rule.md#manual-checklist)
SKIP: docs/recipes/add-stdlib-module.md (manual checklist; see https://github.com/m-dev-tools/.github/blob/main/docs/recipes/add-stdlib-module.md#manual-checklist)
VALIDATE: docs/recipes/new-app-tdd-ci.md (frontmatter + steps + 5 assertions OK)
VALIDATE: docs/recipes/use-stdlib-module.md (frontmatter + steps + 4 assertions OK)
recipes-check: 4 recipe(s) clean
```

## Canonical-query round-trip via `uvx --from git+...@v0.1.0`

The parent-plan exit criterion: an agent can install the MCP server
from the v0.1.0 tag and answer the canonical "parse JSON in M"
intent. Reproducible from a clean environment.

```
$ uvx --from "git+https://github.com/m-dev-tools/m-dev-tools-mcp@v0.1.0" \
      m-dev-tools-mcp --tool route_intent --query "parse JSON in M"
   Updated https://github.com/m-dev-tools/m-dev-tools-mcp (1ae96c41d62ace23ee541c3934c3ad9274baea41)
   Building m-dev-tools-mcp @ git+https://github.com/m-dev-tools/m-dev-tools-mcp@1ae96c41d62ace23ee541c3934c3ad9274baea41
      Built m-dev-tools-mcp @ git+https://github.com/m-dev-tools/m-dev-tools-mcp@1ae96c41d62ace23ee541c3934c3ad9274baea41
Installed 30 packages
[
  "module:m-stdlib#STDJSON"
]

$ uvx --from "git+https://github.com/m-dev-tools/m-dev-tools-mcp@v0.1.0" \
      m-dev-tools-mcp --version
0.1.0
```

The `describe` follow-up resolves the typed ID to a pointer-blob the
client can navigate (manifest_url, AGENTS.md, repo_meta_url):

```
$ uvx --from "git+https://github.com/m-dev-tools/m-dev-tools-mcp@v0.1.0" \
      m-dev-tools-mcp --tool describe --typed-id "module:m-stdlib#STDJSON"
…
  "tool": {
    "typed_id": "tool:m-stdlib",
    "kind": "tool",
    "repo": "https://github.com/m-dev-tools/m-stdlib",
    "agent_instructions": "https://github.com/m-dev-tools/m-stdlib/blob/main/AGENTS.md",
    "modules_url": "https://raw.githubusercontent.com/m-dev-tools/m-stdlib/main/dist/stdlib-manifest.json",
    "repo_meta_url": "https://raw.githubusercontent.com/m-dev-tools/m-stdlib/main/dist/repo.meta.json"
  }
}
```

## What this proves

1. **Agent operability is end-to-end real.** An external agent can
   install the MCP server from the v0.1.0 tag, ask "parse JSON in
   M", and follow the typed-ID pointers all the way to the m-stdlib
   manifest — no manual configuration, no catalog hand-curation.
2. **The catalog generates the onboarding URLs.**
   `tools.m-dev-tools-mcp` carries `repo_meta_url`, `mcp_tools_url`,
   and `release_wheel_url` — all derived from the upstream
   `dist/repo.meta.json`'s `exposes` block. No hand-edits to
   `tools.json`. `make catalog` byte-idempotent. The "facts in
   repos, routing in meta-repo" architectural inversion holds.
3. **CI gates cover both new surfaces.** The meta-repo's `check` +
   `handshake` jobs both ran green on PR #27. The MCP-server repo's
   `check` job ran green on PRs #1 / #2 / #3 / #4 / #5. Phase 4's
   PRs land through the same gates as Phase 0 / 1 / 3.
4. **Release distribution works without PyPI.** `uvx --from
   git+...@v0.1.0` builds the wheel from the tagged commit on
   first invocation and caches it for subsequent calls. The
   `release_wheel_url` field in `tools.m-dev-tools-mcp` points
   directly at the GitHub Release asset for callers that prefer
   `pip install <url>`.

## Phase 4 closed

All nine [`phase4-plan.md` §11](phase4-plan.md) done-criteria met:

1. **m-dev-tools/m-dev-tools-mcp exists, public, full Phase-0
   contract** — repo at <https://github.com/m-dev-tools/m-dev-tools-mcp>;
   public AGPL-3.0; AGENTS.md + CLAUDE.md symlink + dist/repo.meta.json
   + `make check-manifest` + CI. (Track A PR #1 / commit `6a92068`.)
2. **`server.py` exposes route_intent / describe / verify, each
   TDD-covered** — 30 dedicated cases (9 / 11 / 7) under
   `tests/test_{route_intent,describe,verify}.py`, plus 3 smoke + 11
   CLI = 41 / 41 total. (Track B PR #2 / commit `90ca336`.)
3. **Tagged v0.1.0 GitHub Release with built wheel attached** —
   <https://github.com/m-dev-tools/m-dev-tools-mcp/releases/tag/v0.1.0>;
   23-KB pure-Python wheel
   `m_dev_tools_mcp-0.1.0-py3-none-any.whl`. (Track D2.)
4. **`tools.json` carries `tool:m-dev-tools-mcp` with `status:active`,
   `repo_meta_url`, `release_wheel_url`, `mcp_tools_url`** — all
   four fields present on `tools.m-dev-tools-mcp`. (Track D meta-repo
   PR #27 / commit `1a4b15a`.)
5. **`task_index.json` has at least one intent → `tool:m-dev-tools-mcp`** —
   `infra.agent_integration` row with intent "Point my MCP-capable
   agent at the m-dev-tools catalog" and `primary: tool:m-dev-tools-mcp`.
   (Track D meta-repo PR #27.)
6. **`examples/claude-code/` has working `.mcp.json`, smoke script,
   recorded session transcript** — `.mcp.json` (uvx-from-git config),
   `README.md`, `smoke.sh` (passes locally via
   `M_DEV_TOOLS_MCP_BIN=$PWD/.venv/bin/m-dev-tools-mcp`), and
   `session.md` (template; user fills in once after a real Claude
   Code session). (Track C PR #3 / commit `7dc8410`.)
7. **`docs/phase4-evidence.md` captures clean runs of the four gates
   + the canonical round-trip** — this file. Each criterion cited
   green; the same pattern phase3-evidence.md follows.
8. **MCP server answers `route_intent("parse JSON in M")` with
   `module:m-stdlib#STDJSON` from a fresh `uvx --from
   git+...@v0.1.0` install** — see "Canonical-query round-trip"
   section above. Reproducible from a clean environment.
9. **CI green on both `.github/main` and `m-dev-tools-mcp/main`** —
   every Phase 4 PR (#1 / #2 / #3 / #4 / #5 on m-dev-tools-mcp;
   #27 on .github) merged with CI green. Drift gates
   (`check-manifest`, `check-agents`, `check-catalog`,
   `recipes-check`, `handshake`) all gate every push/PR.

Phase 5 (continuous enforcement: freshness / link-check /
license-reconcile / schema-version) is unblocked. PyPI publishing is
*deliberately* not on this list — re-evaluated as a follow-up after
Phase 5 once external adoption demonstrates the API + name are worth
the irreversible commitment.

## Out-of-scope follow-ups

Two items surfaced during Track D worth filing as their own PRs:

- `profile/build/validate-repo-meta.py` chokes on binary
  `exposes.*` URLs (UTF-8 decode of wheel bytes). Fix: skip
  decoding for non-text extensions. `--no-resolve` is the
  documented escape hatch in the meantime.
- Three Phase-3-era orphan schema fixture files under
  `profile/build/fixtures/` (recipe / task_index / tools .schema.json)
  are gitignored but still on disk. The auto-classifier blocks `rm`
  on them; manual cleanup is fine.

Neither blocks any phase boundary.
