# Phase 4 Implementation Plan — `m-dev-tools-mcp` MCP server

**Parent plan:** [`AI-discoverability-plan.md`](AI-discoverability-plan.md) §7
**Phase 4 goal:** Ship `m-dev-tools-mcp` — a thin MCP server that wraps the
org catalog as a first-class protocol surface — as a GitHub-Release wheel
(not PyPI; see [parent plan §5.3](AI-discoverability-plan.md#53-mcp-server)
for the deferral rationale). At least one MCP client (Claude Code) is
demonstrated end-to-end answering `route_intent("parse JSON in M")` with
`module:m-stdlib#STDJSON`.

**Phase 4 exit:** an MCP client configured against `m-dev-tools-mcp`
(installed via `pip install <release-wheel-url>` or `uvx --from git+...@v<X.Y>`)
returns `module:m-stdlib#STDJSON` for the canonical intent query and
returns a resolvable pointer-blob for `describe("module:m-stdlib#STDJSON")`.
The server's repo is onboarded to the Phase-0 contract and listed in
`profile/tools.json` as `tool:m-dev-tools-mcp` with `status: active`.

**Scope.** Building a new tier-3 repo (`m-dev-tools-mcp`) that exposes three
MCP tools (`route_intent`, `describe`, `verify`) over a thin Python wrapper
of `tools.json` + `task_index.json` + the discovery-handshake logic from
Phase 3. The server reads the catalog from `origin/main` raw-GitHub URLs
(network at call time) and ships as ~150 LOC of single-file Python plus a
TDD test suite.

**Not in scope:**

- **PyPI publishing.** Deferred per parent plan §5.3 and PR #18 until
  external adoption demonstrates the API surface + name are worth the
  irreversible commitment (PyPI names are permanent; bad versions are
  yank-only). Re-evaluated as a follow-up after Phase 5.
- **Tier-3 repo onboarding.** All three tier-3 repos (`m-cli-extras`,
  `tree-sitter-m-vscode`, `m-stdlib-vscode`) already ship the Phase-0
  contract — landed in PR #13 (2026-05-10).
- **Multi-client integration matrix.** Phase 4 ships with Claude Code as
  the reference client. Codex / Continue / other MCP-capable agents are
  documented as "should work" but are not gating on Phase 4 exit — they're
  follow-up integration smoke.
- **Continuous freshness / link-check / license-reconcile.** Those are
  Phase 5 cross-cutting investments (parent plan §6.2 + §6.3).

---

## 0. Blocking dependencies (must finish before Phase 4 starts)

| Upstream phase | What Phase 4 needs from it | Status as of 2026-05-11 |
|---|---|---|
| **Phase 1** (org routing layer) | Stable `profile/tools.json` + `profile/task_index.json` schemas; both schema-validated in CI. The MCP server consumes both as its source of truth. | ✅ **CLOSED 2026-05-10** — `make catalog && make validate-catalog` green in CI; `make catalog` byte-idempotent against `origin/main`. |
| **Phase 2** (tier-2 + tier-3 manifests) | `tools.json` has manifest-bearing entries for every repo the MCP server's `describe` and `verify` tools might be asked about. | ✅ **CLOSED 2026-05-10** — all 9 active repos onboarded; `tools.json` carries `repo_meta_url` + `verification_commands`-resolvable pointers for each. |
| **Phase 3** (recipes + handshake test) | `profile/build/test-discovery-protocol.py` is the reference implementation of the routing trail. The MCP server's `route_intent` and `describe` reuse its lookup helpers (importable: `match_intent`, `parse_typed_id`, `resolve_module_manifest_url`, `find_module_entry`, `entry_has_signature_and_example`, `fetch`). | ✅ **CLOSED 2026-05-11** — see [`phase3-evidence.md`](phase3-evidence.md). PR wave (in merge order): #19 (§0 blockers); #20 (Track A — `recipe.schema.json` + `docs/recipes/README.md` + 7 task_index recipe intents); #22 (Track C — `test-discovery-protocol.py` + `run-recipe.py` with TDD); #23 (Track B — 4 shipped recipes); #24 (Tracks D+E — `make recipes-check` + `make handshake` + CI on push/PR + Monday-14:00-UTC cron + evidence). 51/51 pytest cases. |

All three upstream phases are now closed. Phase 4 is fully unblocked:
Tracks A (repo scaffold) and D (catalog onboarding) were independent of
Phase 3 from the start; Track B's prior wait on Phase 3 C2 is resolved —
the importable lookup helpers it consumes are on `.github/main` at
`profile/build/test-discovery-protocol.py`. Track C (client-integration
smoke) still consumes Tracks B + D and runs last.

Verification commands (re-runnable to confirm the launch state hasn't
regressed):

```bash
cd .github
make catalog && make validate-catalog && make phase0-smoke
# Phase 3 handshake — Track B's lookup logic delegates to this script:
make handshake                                       # offline fixtures
python3 profile/build/test-discovery-protocol.py --live  # live URLs
make recipes-check                                   # recipe structural gate
```

---

## 1. Track Layout

Five tracks. Track A is a prerequisite for B/C/D. Track E integrates after
B/C/D finish.

```
┌─────────────────────────────────────────────┐
│ Track A — new m-dev-tools-mcp repo scaffold │  (must finish before B/C/D start)
│ runs in m-dev-tools-mcp                     │
└─────────────────┬───────────────────────────┘
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ B       │ │ C       │ │ D       │   parallel — different files / repos
   │ MCP     │ │ Claude  │ │ release │
   │ tools   │ │ Code    │ │ +       │
   │ (TDD)   │ │ smoke   │ │ catalog │
   └────┬────┘ └────┬────┘ └────┬────┘
        │           │           │
        └───────────┼───────────┘
                    ▼
   ┌─────────────────────────────────────────┐
   │ Track E — Phase 4 smoke + evidence      │  (waits until B+C+D done)
   │ runs in .github                         │
   └─────────────────────────────────────────┘
```

### Track index — callable names

| Track | Repo | Purpose | Blocked by | Stages |
|---|---|---|---|---|
| **A** | `m-dev-tools-mcp` (new) | Scaffold new repo with Phase-0 contract: AGENTS.md, dist/repo.meta.json, Makefile, MCP SDK skeleton, TDD harness | — | A1 → A7 |
| **B** | `m-dev-tools-mcp` | TDD-build the three MCP tools (`route_intent`, `describe`, `verify`) — reuses Phase 3's discovery helpers | A7 | B1 → B6 |
| **C** | `m-dev-tools-mcp` | Claude Code integration smoke — `.mcp.json` config + end-to-end intent → typed-ID round-trip | B6 | C1 → C4 |
| **D** | `.github` + `m-dev-tools-mcp` | Cut v0.1.0 GitHub Release with attached wheel; onboard `tool:m-dev-tools-mcp` to `profile/tools.json` | B6 | D1 → D5 |
| **E** | `.github` | Phase 4 smoke + evidence + close-out PR | C4 ∧ D5 | E1 → E3 |

To call out work: `run A`, `run B3`, `run B through B4`, `run B+D in
parallel` (after B6: the only legal parallel pair pre-merge is C and D,
since both consume B).

### Parallel safety guarantees

- **New repo = no file-overlap risk.** Tracks A and B both operate inside
  the new `m-dev-tools-mcp` clone — same repo, but A finishes before B
  starts, so no concurrent writes.
- **Track D edits `.github/profile/tools.json` + a per-build script.** No
  other track touches those files in Phase 4.
- **Track C writes to user-config files** (Claude Code MCP config), not to
  any shared org file. CI runs Track C against a fixture-only config.
- **No cross-repo work in Phase 4 *during* tracks B and C.** Tracks A and
  D are the only ones that cross repo boundaries (A creates a repo;
  D edits `.github` to catalog it).
- **PyPI namespace untouched.** Per the parent plan deferral; Track D
  ships a GitHub Release, not a `twine upload`. No name registration.

### Stage status conventions

Same as Phase 0 / Phase 1 / Phase 3. Each stage is one of: `todo`, `doing`,
`done`, `blocked`. A stage is `done` only when its verification command
exits 0.

### What Phase 3 already shipped that Phase 4 consumes

Track B (MCP tools) and Track E (smoke + evidence) lean on Phase 3
artifacts that already live on `.github/main`. Track B should `import`
from them rather than reimplement the routing trail.

| Phase 3 artifact | Location | Phase 4 use |
|---|---|---|
| Discovery-handshake helpers | `profile/build/test-discovery-protocol.py` (functions `match_intent`, `parse_typed_id`, `resolve_module_manifest_url`, `find_module_entry`, `entry_has_signature_and_example`, `fetch`, `extract_llms_links`) | Track B's `route_intent` / `describe` import these directly; no reimplementation. |
| Offline catalog fixtures | `profile/build/fixtures/` — `llms.txt`, `tools.json`, `task_index.json`, `stdlib-manifest.json`, `repo.meta.json` | Track B's TDD fixtures (B1 / B3 / B5) — copy or symlink into the MCP repo's `tests/fixtures/` so the unit tests don't hit raw-GitHub. |
| Recipe schema + 4 shipped recipes | `profile/recipe.schema.json` + `docs/recipes/{new-app-tdd-ci,use-stdlib-module,add-stdlib-module,add-lint-rule}.md` | Track B's `describe("recipe:new-app-tdd-ci")` — the typed ID resolves through `task_index.json`'s `recipes` category (committed as part of PR #20). |
| `make handshake` + `make recipes-check` | `.github/Makefile` | Track E's E1 evidence script already invokes both; no Make changes needed in this phase. |
| Recipe runner with `--validate-only` | `profile/build/run-recipe.py` (PR #24) | Pattern reference for any "validate without executing" MCP tool surface Track B might add later (not in current scope). |

### Out-of-scope Phase 3 follow-ups noted (do not address in Phase 4)

- `run-recipe.py`'s minimal YAML parser does not handle `>` block scalars
  or `[]` inline empty arrays. The four shipped recipes work around this.
  Phase 4 does not parse recipe YAML — the MCP server reads
  `task_index.json` for routing — so this limitation does not bite here.
- Three orphan schema fixture files (`recipe.schema.json`,
  `task_index.schema.json`, `tools.schema.json`) remain untracked under
  `profile/build/fixtures/`. Track B should copy only the five tracked
  fixtures listed above when seeding its `tests/fixtures/`.

---

## 2. Track A — `m-dev-tools-mcp` repo scaffold

Runs in the (to-be-created) `m-dev-tools-mcp` repo. Single-session work;
~half-day.

### A1 — Create the repo on GitHub

**Output:** new repository `m-dev-tools/m-dev-tools-mcp` (AGPL-3.0, public).

Description (single sentence, mirrors the org-default tagline shape):
"MCP server for the m-dev-tools org catalog — exposes `route_intent`,
`describe`, and `verify` as first-class agent tools."

**Verify:** `gh repo view m-dev-tools/m-dev-tools-mcp --json url,visibility,license`
returns the expected metadata.

### A2 — Bootstrap Python package skeleton

**Output:** initial commit on `main` with:

```
m-dev-tools-mcp/
├── AGENTS.md
├── CLAUDE.md → AGENTS.md (symlink)
├── LICENSE
├── Makefile
├── pyproject.toml
├── README.md
├── dist/
│   └── (generated; .gitignore'd except repo.meta.json)
├── src/
│   └── m_dev_tools_mcp/
│       ├── __init__.py
│       ├── __main__.py        # entry point
│       └── server.py          # MCP server scaffold; tool stubs only
└── tests/
    ├── __init__.py
    └── test_smoke.py          # imports the module, no behavior yet
```

Tooling defaults match the org convention (Python 3.12, `uv`, `ruff`, `mypy`,
`pytest`).

**Verify:** `make install && make test` is green (smoke test is a no-op).

### A3 — Ship `AGENTS.md` (canonical) + symlink

**Output:** `AGENTS.md` + `CLAUDE.md` → `AGENTS.md`.

Contents follow the m-cli / m-stdlib AGENTS.md skeleton: setup, test,
verify, project conventions, library API surface. Lists the three MCP tools
as the public surface.

**Verify:** `make check-agents` (added in A5) is green.

### A4 — Ship `dist/repo.meta.json`

**Output:** `dist/repo.meta.json` validated by the org-level schema.

```json
{
  "$schema": "https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/repo.meta.schema.json",
  "id": "tool:m-dev-tools-mcp",
  "repo": "https://github.com/m-dev-tools/m-dev-tools-mcp",
  "role": "MCP server wrapping the m-dev-tools org catalog as route_intent / describe / verify tools",
  "language": ["python"],
  "license": "AGPL-3.0",
  "agent_instructions": "AGENTS.md",
  "verified_on": "2026-05-11",
  "exposes": {
    "tools": "dist/mcp-tools.json"
  },
  "consumes": ["tool:m-cli", "tool:m-stdlib", "tool:m-standard"],
  "verification_commands": ["make check", "make smoke"]
}
```

`exposes.tools` points at a manifest of the three MCP tools' names +
signatures, regenerated from `server.py` introspection (the analogue of
m-cli's `commands.json`).

**Verify:** `make check-repo-meta META=dist/repo.meta.json` from the
`.github` Makefile is green against the repo's `dist/repo.meta.json`.

### A5 — Wire `make check-manifest` drift gate

**Output:** Makefile target that regenerates `dist/mcp-tools.json` from
`server.py` introspection (reads each `@mcp.tool` decorator, extracts
name + docstring + parameter schema), diffs against the committed copy,
fails on diff. Same pattern as m-cli's manifest drift gate.

Also wires `make check-agents` (assert `AGENTS.md` exists + has required
sections).

**Verify:** `make check-manifest && make check-agents` is green.

### A6 — Wire CI

**Output:** `.github/workflows/ci.yml` running `make check`
(lint + mypy + test + check-manifest + check-agents). Triggers on push +
pull_request.

**Verify:** CI is green on the initial commit.

### A7 — Commit, push, merge initial scaffold

Single PR (the initial-commit PR — `main` is empty until this lands).
Commit subject: `phase4-A: scaffold m-dev-tools-mcp (Phase-0 contract + CI)`.

**Verify:** PR merged; `main` carries the skeleton; CI green; the repo's
`repo_meta_url` resolves at the raw-GitHub URL.

---

## 3. Track B — Implement the three MCP tools

Runs in `m-dev-tools-mcp`. Blocked by A7 (need the scaffold). Phase 3
closed 2026-05-11 so the discovery helpers Track B imports are already
on `.github/main`.

TDD throughout — write each test, confirm RED, implement, confirm GREEN.

### B1 — TDD: `route_intent(query)` tests

**Output:** `tests/test_route_intent.py` (pytest).

Fixtures: copy Phase 3's bundled fixture set —
`profile/build/fixtures/{llms.txt, tools.json, task_index.json,
stdlib-manifest.json, repo.meta.json}` — into `tests/fixtures/` so the
unit tests don't hit raw-GitHub. Track C's smoke script (separate from
unit tests) is the path that exercises live fetches. Test cases:

- Exact intent string match: `route_intent("Parse JSON in M")` returns
  `["module:m-stdlib#STDJSON"]` (or whatever the live `task_index.json`
  says).
- Fuzzy match: `route_intent("json parsing")` returns the same with
  similarity rank.
- Empty query: returns `[]`.
- Catalog network failure: graceful error, structured error type, no
  silent fallback.
- `see_also` entries surface in the result list after `primary`.

Confirm RED before B2.

### B2 — Implement `route_intent`

**Output:** `src/m_dev_tools_mcp/server.py` — `route_intent` tool. The
exact-match path delegates to Phase 3's `match_intent` (vendored or
imported from `.github`'s `test-discovery-protocol.py` — see the
"What Phase 3 already shipped" subsection of §1). The fuzzy-rank path
is the only new logic Phase 4 writes for this tool.

```python
from m_dev_tools_mcp._discovery import match_intent  # vendored from .github

@mcp.tool
def route_intent(query: str) -> list[str]:
    """Return typed IDs matching the plain-English intent."""
    ti = _fetch_task_index()                 # cached fetch from origin/main
    exact = match_intent(query, ti)          # Phase-3 helper
    if exact:
        return [exact]
    return _fuzzy_rank(query, ti)            # Phase-4 fuzzy fallback
```

Fuzzy match: case-folded substring against `intent` strings + lightweight
token overlap. No external NLP deps — keeps the single-file constraint
intact. Vendoring (vs `pip install` from the meta-repo) keeps the MCP
server's dependency graph at `mcp` + stdlib only.

**Verify:** B1 tests green; `route_intent("parse JSON in M")` returns
`["module:m-stdlib#STDJSON"]` against the live catalog.

### B3 — TDD: `describe(typed_id)` tests

**Output:** `tests/test_describe.py`.

Fixtures: same frozen catalog as B1. Test cases:

- `describe("module:m-stdlib#STDJSON")` returns a dict with `repo`,
  `manifest_url`, `agent_instructions`, `verification_commands`.
- `describe("cmd:m-cli#test")` resolves to the m-cli entry + drills
  into `commands_url` to surface the per-subcommand description.
- `describe("tool:m-cli")` returns the top-level tool entry.
- `describe("recipe:new-app-tdd-ci")` resolves through `task_index.json`'s
  `recipes` category (shipped in PR #20) to the actual recipe at
  `docs/recipes/new-app-tdd-ci.md` (shipped in PR #23). Confirm the
  returned blob carries the recipe's HTTPS URL + raw-GitHub URL — both
  are typical client follow-up reads.
- `describe("invalid-id")` returns a structured error, not a crash.
- Typed-ID grammar mismatch: rejected before catalog lookup.

Confirm RED before B4.

### B4 — Implement `describe`

**Output:** `src/m_dev_tools_mcp/server.py` — `describe` tool.

Walks the catalog: parses the typed ID via Phase 3's `parse_typed_id`,
looks up the appropriate slice of `tools.json` (using
`resolve_module_manifest_url` for `module:` IDs), follows `exposes.*`
pointers for `cmd:` / `rule:` IDs, returns a JSON blob with the pointer
URLs the caller should read next. Does **not** inline the underlying
payloads — keeps the catalog's "pointers, not facts" invariant.

`recipe:` IDs are the new code path Phase 4 writes: a single lookup
into `task_index.json`'s `recipes` category, returning the recipe's
HTTPS + raw URLs. No Phase 3 helper covers this since recipes weren't
in the routing trail at handshake-design time.

**Verify:** B3 tests green; `describe("module:m-stdlib#STDJSON")` includes
the m-stdlib manifest URL and the AGENTS.md URL.

### B5 — TDD + implement `verify(repo)`

**Output:** `tests/test_verify.py` + the implementation.

Test cases:

- `verify("m-cli")` resolves `tool:m-cli` → reads its `verification_commands`
  array from `dist/repo.meta.json` → returns the list (does NOT execute
  them — that's a client concern).
- `verify("nonexistent-repo")` returns a structured error.
- `verify` with a typed ID instead of a bare repo name: accepted (typed ID
  form is the documented contract; bare repo name is sugar).

Note: per the parent plan §5.3 the original spec said "verify runs
verification_commands and returns status." That's a security-sensitive
choice — running arbitrary commands from a catalog blob is exactly the
prompt-injection vector MCP servers are warned about. Phase 4 ships
`verify` as **command-listing only**; actually executing the commands is
the **client's** responsibility (the agent, with the user's consent).
Documented in AGENTS.md.

**Verify:** B5 tests green; `verify("m-cli")` returns
`["make check", "m doctor"]` (or whatever m-cli's repo.meta.json says).

### B6 — Regenerate manifest + ship

**Output:** `dist/mcp-tools.json` regenerated; `make check-manifest` green;
PR merged.

Commit subject: `phase4-B: implement route_intent + describe + verify (TDD)`.

**Verify:** PR merged on `m-dev-tools-mcp` `main`; CI green; manifest
drift gate green.

---

## 4. Track C — Claude Code integration smoke

Runs in `m-dev-tools-mcp`. Blocked by B6 (the tools must exist before a
client can call them).

### C1 — Author `.mcp.json` fixture

**Output:** `examples/claude-code/.mcp.json`

```json
{
  "mcpServers": {
    "m-dev-tools-mcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/m-dev-tools/m-dev-tools-mcp@main", "m-dev-tools-mcp"]
    }
  }
}
```

Plus a `README.md` in `examples/claude-code/` documenting the two install
paths (release wheel + uvx-from-git) and pointing Codex / Continue users at
their respective config locations with the same JSON shape.

**Verify:** the example MCP config validates as JSON (pre-commit hook
already covers this).

### C2 — Smoke script

**Output:** `examples/claude-code/smoke.sh` — shells the MCP server's
`route_intent` tool with the canonical query and asserts the response.

```bash
#!/usr/bin/env bash
set -euo pipefail
RESULT=$(uvx --from git+https://github.com/m-dev-tools/m-dev-tools-mcp@main \
  m-dev-tools-mcp --tool route_intent --query "parse JSON in M")
echo "$RESULT" | grep -q '"module:m-stdlib#STDJSON"'
```

The `--tool` / `--query` CLI surface is added in Track B as a thin
non-MCP path for smoke-testing without an MCP client.

**Verify:** running the smoke script locally exits 0 and prints
`module:m-stdlib#STDJSON`.

### C3 — Manual Claude Code session

One person installs the MCP server, opens Claude Code, points it at the
config, asks "How do I parse JSON in M?", confirms Claude responds via
the MCP server's `route_intent` (visible in the session trace). Captures
a screenshot or transcript in `examples/claude-code/session.md`.

**Verify:** transcript exists; `route_intent` was the routing step (not
Claude guessing from training data).

### C4 — Commit + push the examples

Single PR. Commit subject: `phase4-C: Claude Code integration smoke +
example config`.

**Verify:** PR merged; `examples/claude-code/` is on `main`.

---

## 5. Track D — GitHub Release + catalog onboarding

Runs in `m-dev-tools-mcp` and `.github`. Blocked by B6 (need a working
server to release).

### D1 — Build the wheel

**Output:** `dist/m_dev_tools_mcp-0.1.0-py3-none-any.whl` produced by
`uv build`.

Pinned to Python 3.10+ (matches MCP-SDK floor). Pure Python; no compiled
extensions.

**Verify:** `pip install dist/m_dev_tools_mcp-0.1.0-py3-none-any.whl` into
a fresh `mktemp -d` venv works; `m-dev-tools-mcp --version` prints `0.1.0`.

### D2 — Tag + GitHub Release

**Output:** `v0.1.0` annotated tag on `m-dev-tools-mcp` `main`; a GitHub
Release attached with the wheel as a downloadable asset.

```bash
gh release create v0.1.0 dist/m_dev_tools_mcp-0.1.0-py3-none-any.whl \
  --title "v0.1.0 — initial MCP server" \
  --notes "First MCP-server release. Three tools: route_intent, describe, verify. Install via 'pip install <release-asset-url>' or 'uvx --from git+...@v0.1.0 m-dev-tools-mcp'."
```

**Verify:** the release URL resolves; `pip install` against the asset URL
into a fresh venv works.

### D3 — Onboard `tool:m-dev-tools-mcp` to `tools.json`

**Output:** edit to `.github/profile/tools.json` adding the
`m-dev-tools-mcp` entry under `tools`:

```json
"m-dev-tools-mcp": {
  "id": "tool:m-dev-tools-mcp",
  "repo": "https://github.com/m-dev-tools/m-dev-tools-mcp",
  "role": "MCP server — exposes route_intent / describe / verify over the org catalog",
  "language": "python",
  "license": "AGPL-3.0",
  "agent_instructions": "https://github.com/m-dev-tools/m-dev-tools-mcp/blob/main/AGENTS.md",
  "verified_on": "2026-05-11",
  "status": "active",
  "repo_meta_url":   "https://raw.githubusercontent.com/m-dev-tools/m-dev-tools-mcp/main/dist/repo.meta.json",
  "mcp_tools_url":   "https://raw.githubusercontent.com/m-dev-tools/m-dev-tools-mcp/main/dist/mcp-tools.json",
  "release_wheel_url": "https://github.com/m-dev-tools/m-dev-tools-mcp/releases/download/v0.1.0/m_dev_tools_mcp-0.1.0-py3-none-any.whl",
  "consumes": ["tool:m-cli", "tool:m-stdlib", "tool:m-standard"]
}
```

Add task_index intents under a new `mcp` category (or under `infra`):

```json
"agent_integration": {
  "intent": "Point my MCP-capable agent at the m-dev-tools catalog",
  "primary": "tool:m-dev-tools-mcp",
  "doc": "https://github.com/m-dev-tools/m-dev-tools-mcp/blob/main/examples/claude-code/README.md"
}
```

**Verify:** `make catalog && make validate-catalog && make phase0-smoke`
all green.

### D4 — Update README + llms.txt

**Output:** edits to `.github/profile/README.md` (add an "MCP server" row
under the appropriate table) and `.github/profile/llms.txt` (add the MCP
binary as an entry under "Core repositories" or a new "Agent integration"
section).

Keep `llms.txt` under 40 lines (parent plan §4.6).

**Verify:** `make catalog` byte-idempotent after edits; `llms.txt` link-check
passes against the new release URL.

### D5 — Commit + merge

Single PR (or two — one in `m-dev-tools-mcp` for release prep, one in
`.github` for catalog onboarding). Commit subject for the `.github` PR:
`phase4-D: onboard tool:m-dev-tools-mcp + first GitHub Release wheel`.

**Verify:** PR merged on `.github` `main`; catalog generates clean;
`describe("tool:m-dev-tools-mcp")` works (when called against the live
catalog) — self-referential smoke that proves D3's entry is reachable.

---

## 6. Track E — Phase 4 smoke + evidence

Runs in `.github`. Blocked by C4 and D5.

Follows the Phase 1 / Phase 3 convention: a single
`docs/phase4-evidence.md` file (no separate `phase4-status.md`). The
stage-by-stage roll-up is folded into the evidence doc; phase0's split
status/plan layout was an early convention that did not carry forward.

### E1 — Phase 4 smoke

**Output:** evidence file `docs/phase4-evidence.md`.

```bash
make catalog && make validate-catalog && make handshake && make recipes-check \
  && python3 - <<'PY' | tee -a docs/phase4-evidence.md
import subprocess
out = subprocess.check_output([
  "uvx", "--from",
  "git+https://github.com/m-dev-tools/m-dev-tools-mcp@v0.1.0",
  "m-dev-tools-mcp", "--tool", "route_intent",
  "--query", "parse JSON in M",
], text=True)
assert "module:m-stdlib#STDJSON" in out, f"unexpected: {out!r}"
print("PHASE4-EXIT OK:", out.strip())
PY
```

The terminal output is post-processed by hand into Markdown sections
mirroring `phase3-evidence.md` (one section per gate; a "What this
proves" wrap-up; a "Phase 4 closed" roll-up that walks each §11
done-criterion).

**Verify:** all targets exit 0; evidence captures the canonical-query
round-trip; every §11 done-criterion is cited green in the doc.

### E2 — Close-out PR

Single PR. Commit subject: `phase4-E: smoke + evidence; Phase 4 closed`.

**Verify:** PR merged; `phase4-evidence.md` on `main`; Phase 5 unblocked.

---

## 7. Stage Matrix — Single-Glance View

| Stage | Repo | Blocked by | Verification |
|---|---|---|---|
| A1 | `m-dev-tools-mcp` (new) | — | `gh repo view` returns expected metadata |
| A2 | `m-dev-tools-mcp` | A1 | `make install && make test` green (no-op smoke) |
| A3 | `m-dev-tools-mcp` | A2 | `make check-agents` green |
| A4 | `m-dev-tools-mcp` | A3 | `.github` `make check-repo-meta META=…` green |
| A5 | `m-dev-tools-mcp` | A4 | `make check-manifest && make check-agents` green |
| A6 | `m-dev-tools-mcp` | A5 | initial CI run green |
| A7 | `m-dev-tools-mcp` | A6 | PR merged; `repo_meta_url` resolves |
| B1 | `m-dev-tools-mcp` | A7 | RED tests |
| B2 | `m-dev-tools-mcp` | B1 | B1 tests green; live-catalog round-trip works |
| B3 | `m-dev-tools-mcp` | B2 | RED tests |
| B4 | `m-dev-tools-mcp` | B3 | B3 tests green; pointer-blob includes manifest URL |
| B5 | `m-dev-tools-mcp` | B4 | TDD green; `verify("m-cli")` returns command list (no exec) |
| B6 | `m-dev-tools-mcp` | B5 | PR merged; manifest drift gate green |
| C1 | `m-dev-tools-mcp` | B6 | example `.mcp.json` validates as JSON |
| C2 | `m-dev-tools-mcp` | C1 | `smoke.sh` exits 0; output contains the typed ID |
| C3 | `m-dev-tools-mcp` | C2 | manual session transcript exists |
| C4 | `m-dev-tools-mcp` | C3 | PR merged; `examples/claude-code/` on `main` |
| D1 | `m-dev-tools-mcp` | B6 | wheel builds; pip-installs into a fresh venv |
| D2 | `m-dev-tools-mcp` | D1 | GitHub Release tag exists; wheel asset downloadable |
| D3 | `.github` | D2 | `make catalog && make validate-catalog && make phase0-smoke` green |
| D4 | `.github` | D3 | `make catalog` byte-idempotent after README + llms.txt edits |
| D5 | `.github` | D4 | PR merged; `describe("tool:m-dev-tools-mcp")` reachable on live catalog |
| E1 | `.github` | C4 ∧ D5 | `phase4-evidence.md` captures canonical-query round-trip + every §11 done-criterion cited green |
| E2 | `.github` | E1 | PR merged; Phase 5 unblocked |

---

## 8. Calling Convention

Same shape as phase0/phase1/phase3.

- **`run A`** — execute Track A end-to-end.
- **`run B`** — execute Track B end-to-end (only after A7 and Phase 3 C2).
- **`run B3`** — execute only stage B3.
- **`run B through B4`** — B1, B2, B3, B4 in sequence.
- **`run C+D in parallel`** — spawn two independent sessions; different
  files, no collision risk (only legal parallel pair after B6).
- **`resume D from D3`** — continue from a checkpoint; assumes D1–D2 done.

A Claude session given a track callout should:

1. Read this document.
2. Confirm the blocking stage(s) are `done` per `phase4-status.md`.
3. Execute its stages in order.
4. Run the verification command at the end of each stage; halt on failure.
5. Report the final state when the track (or named substage) completes.

Do **not** advance a stage whose verification didn't exit 0. Halt and report.

### Recommended order

If executing single-threaded:

1. **A** (foundation — scaffold the new repo).
2. **B** (implement the three tools; the most code-heavy track).
3. **C and D in parallel** (C = Claude Code smoke; D = release + catalog).
4. **E** (smoke + evidence; close-out).

If you can only ship part of Phase 4, ship **A + B + C** and defer D
(release + catalog onboarding) as a follow-up PR. That gets the MCP
server *callable* by Claude Code via `uvx --from git+...@main`, which
satisfies the parent plan's success criterion #3 (an agent can use the
MCP server) without the release ceremony. D5's catalog onboarding closes
the loop but is not gating on agents being able to *use* the server.

---

## 9. Risk Notes

- **MCP SDK API surface is still volatile.** The Anthropic MCP Python
  SDK is in active development; minor versions can shift the
  `@tool` decorator surface. Mitigation: pin the SDK version in
  `pyproject.toml`; gate upgrades behind explicit version bumps in
  follow-up PRs, not in Phase 4 itself.
- **`verify` execution-vs-listing ambiguity.** Parent plan §5.3 says
  "verify runs verification_commands and returns status." Phase 4 ships
  command-*listing* only — see B5 rationale. This narrows the security
  surface (no arbitrary-command execution from a catalog blob the user
  didn't author). If a future caller wants execution, they wrap
  `verify` client-side. Document in AGENTS.md so future sessions don't
  silently re-widen the contract.
- **PyPI namespace squatting.** Deferring PyPI publishing means
  someone else could register `m-dev-tools-mcp` on PyPI first.
  Mitigation: reserve the name *without publishing a useful version* —
  upload a `0.0.0` placeholder that just `print()s` "Use the GitHub
  release wheel; this PyPI package is a placeholder." This is the only
  permissible PyPI interaction in Phase 4. Track it as a separate D4-bis
  follow-up if name-reservation is wanted; otherwise accept the squat
  risk and document in §5.3 of the parent plan that namespace defense
  is out of scope.
- **Catalog fetch over network at call time.** Each MCP-tool invocation
  hits raw-GitHub. Latency: ~100–300ms per request. Acceptable for
  agent use; document in AGENTS.md that the server is not designed for
  high-frequency programmatic calls. Mitigation: cache the catalog
  in-memory for 60s within a single server process.
- **Vendored Phase 3 helper drift.** Track B vendors (or imports) a
  small set of pure functions from `.github`'s
  `test-discovery-protocol.py` (`match_intent`, `parse_typed_id`,
  `resolve_module_manifest_url`, `find_module_entry`,
  `entry_has_signature_and_example`, `fetch`). If the upstream signature
  changes, vendored copies drift silently. Mitigation: the MCP server's
  TDD suite pins the function behaviors (input/output contracts) on
  fixtures copied from `profile/build/fixtures/`. A future upstream
  rename surfaces as a red unit test, not a runtime failure in a Claude
  Code session. Track B's PR body must spell out the vendoring decision
  so a future maintainer doesn't `pip install` the meta-repo to fix
  drift (the meta-repo is not a Python package — it's a GitHub `.github`
  org-meta repo). Per §5.3 of the parent plan: pointers, not facts —
  vendoring small pure functions is the canonical exception.
- **`m-cli-extras` plugin-leak in the manifest drift gate.** Phase-0
  onboarding for tier-3 repos surfaced this gotcha — a maintainer's
  local venv can introduce phantom entry points that fail
  `check-manifest` in CI but not locally. Captured in m-cli `f516e76`.
  Mitigation: the new `m-dev-tools-mcp` manifest covers only
  `@mcp.tool`-decorated functions in its own source tree, not
  entry points from arbitrary installed packages. Document in
  `make check-manifest`'s comment.
- **MCP-client config drift.** Claude Desktop, Claude Code, Codex,
  and Continue each have slightly different MCP-config formats.
  Phase 4 ships Claude Code config only; the others are documented
  as "should work with the same JSON shape" but unverified. If a
  future user reports breakage in Codex or Continue, that becomes a
  Phase 5 follow-up or its own dedicated PR.

---

## 10. Suggested Gantt

```
                 W1  W2  W3  W4  W5  W6  W7  W8  W9
m-dev-tools-mcp repo (A)    █████
mcp tools (B)                    █████████████
Claude Code smoke (C)                         ████████
release + catalog (D)                         ████████
Phase 4 smoke (E)                                     ████
phase 3 (closed 2026-05-11) ✅ — all helpers on .github/main
```

- A is one week. B is two-to-three weeks (TDD across three tools).
- C and D run in parallel once B lands.
- E is one week (smoke + evidence + close-out PR).
- Total Phase 4 elapsed: ~6 weeks single-threaded; ~5 weeks with one
  parallel pair.

Phase 4 ships inside one quarter, well within the parent plan's "ship
inside two quarters" budget for the agent-operability layer.

---

## 11. Phase 4 Done — Definition

Phase 4 is done when **all** of these are true:

1. The `m-dev-tools/m-dev-tools-mcp` repo exists, is public, and ships
   the full Phase-0 contract (`AGENTS.md` + `dist/repo.meta.json` +
   `make check-manifest` + CI).
2. `src/m_dev_tools_mcp/server.py` exposes three MCP tools:
   `route_intent`, `describe`, `verify` — each TDD-covered.
3. A tagged `v0.1.0` GitHub Release exists with a built Python wheel
   attached.
4. `.github/profile/tools.json` carries `tool:m-dev-tools-mcp` with
   `status: active`, a `repo_meta_url`, a `release_wheel_url`, and an
   `mcp_tools_url` pointing at the per-server manifest.
5. `.github/profile/task_index.json` carries at least one intent row
   pointing at `tool:m-dev-tools-mcp` (e.g. "point my MCP-capable agent
   at the m-dev-tools catalog").
6. `examples/claude-code/` in the MCP-server repo contains a working
   `.mcp.json`, a smoke script, and a recorded session transcript.
7. `docs/phase4-evidence.md` in `.github` captures a clean run of
   `make catalog && make validate-catalog && make handshake &&
   make recipes-check` *plus* the canonical `route_intent` round-trip,
   with each criterion in this list cited green (same pattern as
   `phase3-evidence.md`).
8. The MCP server answers `route_intent("parse JSON in M")` with
   `module:m-stdlib#STDJSON` from a fresh `uvx --from git+...@v0.1.0`
   install — the parent-plan exit criterion, reproducible from a
   clean environment.
9. CI is green on both `.github/main` and `m-dev-tools-mcp/main`.

When all nine are true, Phase 5 (continuous enforcement hardening) is
unblocked. PyPI publishing is *deliberately* not on this list — it's
re-evaluated as a follow-up after Phase 5 once external adoption
demonstrates the API + name are worth the irreversible commitment.
