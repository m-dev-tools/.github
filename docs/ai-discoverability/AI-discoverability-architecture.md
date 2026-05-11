# AI-discoverability architecture — m-dev-tools

> The foundational document for how the m-dev-tools org makes itself
> discoverable to LLM-based agents and MCP clients. Reading it
> end-to-end gives a human or an agent enough to extend the framework
> safely: adding a new repo, a new tool, a new manifest kind.

**Audience.** A human or an agent that needs to change anything about
how m-dev-tools surfaces itself to AI consumers. If you're just
*consuming* the catalog as an agent, the [llms.txt](https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/llms.txt)
entry-point and the org-side [tools.json](https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/tools.json) /
[task_index.json](https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/task_index.json)
are sufficient — you don't need this doc.

**Status.** Master architecture document. Supersedes (but does not
replace) the earlier
[AI-discoverability-guide.md](AI-discoverability-guide.md) and
[AI-discoverability-plan.md](AI-discoverability-plan.md). Both remain
authoritative as historical-rationale references; this doc is the
single place to learn how the pieces *currently* fit together.

---

## Table of contents

1. [First principles — what LLMs and MCP clients actually need](#1-first-principles)
2. [The design — three-layer architecture](#2-the-design--three-layer-architecture)
3. [The implementation — component flow](#3-the-implementation--component-flow)
4. [How to extend (growth playbook)](#4-how-to-extend--growth-playbook)
5. [Operational invariants — the CI gates that hold it all together](#5-operational-invariants)
6. [Where to read more](#6-where-to-read-more)

---

## 1. First principles

### 1.1 What LLM-based agents need to discover a codebase

LLMs are not "smart filesystems." They are prediction engines whose
behaviour degrades fast when they fabricate identifiers, follow stale
links, or rely on memorized training-cutoff snapshots. To direct an
agent at a codebase reliably, you have to give it:

- **A small, predictable entry point.** Not "browse our docs" — a
  single file, < 40 lines, that lists every onward link the agent
  will need. (The de-facto standard is
  [llmstxt.org](https://llmstxt.org/)'s `llms.txt`.)
- **A machine-readable catalog** of the repos, modules, commands,
  rules, recipes, etc. the agent might be asked about — keyed by
  predictable, typed identifiers.
- **A typed-identifier grammar** so the agent has a finite, schema-
  validatable language for *referring* to anything in the catalog
  (vs. "the JSON parsing thing in the M library"). Our grammar:
  `^(tool|cmd|module|rule|doc|data|workflow|task|recipe):[a-z0-9_-]+(#[A-Za-z0-9._-]+)?$`.
- **Pointers, not facts.** The catalog should say "fetch
  `https://…/dist/commands.json` to see m-cli's subcommands" rather
  than inlining the subcommand list itself. Inlined facts drift
  silently; pointer URLs either resolve or 404 (which CI can gate).
- **Per-unit manifests with signatures + examples.** When the agent
  drills into `module:m-stdlib#STDJSON`, it needs to see the exact
  function signature, the parameter contract, and at least one
  worked example. Without an example the agent will fabricate one.
- **Recipes — executable, tested workflows** for common tasks
  ("scaffold a new M project", "add a stdlib module"). A recipe is
  not a tutorial; it's a Markdown file with YAML frontmatter, a
  `## Steps` bash block, and `## Expected output` assertions that
  CI can verify.
- **Link integrity gates.** Every pointer in the catalog must have a
  CI step that confirms it still resolves. Otherwise the catalog
  rots toward "mostly broken".
- **Per-repo agent instructions (`AGENTS.md`).** Org-level prose
  ("we prefer TDD", "write the manifest test first") doesn't scale.
  Each repo carries its own `AGENTS.md` that overrides the org
  defaults where applicable.

### 1.2 What MCP clients need on top of discovery

The [Model Context Protocol](https://modelcontextprotocol.io/) is the
emerging standard for letting agents call typed tools over a stdio
transport. For us to be MCP-native, we need:

- **A small set of *stable* MCP tools** the agent can call. Renaming
  or repurposing a tool is a contract break; new tools get added in
  their own PR with their own TDD coverage.
- **Structured I/O** — each tool's parameters declared with
  type annotations the framework turns into JSON Schema. The agent
  reads the schema once and never guesses at argument shapes.
- **A predictable error surface.** When a call can't succeed (typed
  ID malformed, tool not found, …), the failure carries a stable
  string code the agent can switch on. No free-form exception text.
- **A frictionless install path** that doesn't require the agent's
  operator to babysit. We support `pip install m-dev-tools-mcp`
  (PyPI), `pip install <release-wheel-url>` (GitHub Release wheel),
  and `uvx --from git+…@<tag>` (pin to a release tag, install on
  demand) — three channels with overlapping reach. PyPI is the
  channel of choice for the official MCP registry listing (per
  [`AI-discoverability-plan.md` §5.3 + Phase 6](AI-discoverability-plan.md#53-mcp-server-m-dev-tools-mcp)).
- **Pointer-blob responses.** The MCP tools never inline catalog
  payloads. `describe("module:m-stdlib#STDJSON")` returns a dict of
  URLs to fetch next — same "pointers, not facts" invariant as the
  catalog itself.

### 1.3 The architectural inversion that follows

The old approach — `tools.json` as a hand-maintained registry — had
one fatal failure mode: drift. Every repo that grew a new subcommand,
shipped a new module, or changed its license, had to remember to
update a file in a *different* repo. The new approach inverts that:

> **Each repo owns its facts.** Each repo emits
> `dist/repo.meta.json` describing its own surface. The org meta-repo
> *generates* `tools.json` from those manifests via
> `profile/build/build-catalog.py`. Hand-edits to `tools.json` are
> erased on the next regen. The drift gate ensures CI never lets a
> stale `tools.json` ship.

Everything in this doc follows from that inversion plus the seven
first-principles bullets in §1.1.

---

## 2. The design — three-layer architecture

The framework decomposes cleanly into three layers, dependency-ordered
bottom-up. Higher layers consume — but never write to — lower layers'
artifacts.

```
+-----------------------------------------------------------------+
| LAYER 3 — Agent operability                                     |
|                                                                 |
|   What an external agent (Claude Code, Codex, Continue, ...)    |
|   actually calls. Every call here ultimately resolves into a    |
|   Layer-2 lookup, which resolves into a Layer-1 fetch.          |
|                                                                 |
|   * m-dev-tools-mcp (FastMCP server, 3 tools)                   |
|       - route_intent(query) -> typed-IDs                        |
|       - describe(typed_id) -> pointer-blob                      |
|       - verify(repo) -> verification_commands (no exec)         |
|   * docs/recipes/*.md (mechanically-runnable workflows)         |
|   * profile/build/test-discovery-protocol.py (8-step handshake) |
+-----------------------------------------------------------------+
                            ^
                            | reads / fetches
                            |
+-----------------------------------------------------------------+
| LAYER 2 — Org routing (generated catalog)                       |
|                                                                 |
|   What the meta-repo (`.github`) publishes as the single        |
|   authoritative routing layer. Hand-edits to tools.json are     |
|   illegal and erased; hand-edits to task_index.json are the     |
|   only allowed curation.                                        |
|                                                                 |
|   * profile/llms.txt (< 40 lines, llmstxt.org form)             |
|   * profile/tools.json (generated, byte-deterministic)          |
|   * profile/task_index.json (intent -> typed-ID, hand-curated)  |
|   * profile/{tools,task_index,repo.meta,recipe}.schema.json     |
|   * profile/build/{build,validate}-catalog.py                   |
+-----------------------------------------------------------------+
                            ^
                            | regenerates from
                            |
+-----------------------------------------------------------------+
| LAYER 1 — Repo-local facts                                      |
|                                                                 |
|   Each onboarded repo emits its own machine-readable surface.   |
|   The schema lives in the meta-repo                             |
|   (profile/repo.meta.schema.json); each repo's CI re-validates  |
|   on every push via `make check-manifest`.                      |
|                                                                 |
|   Per repo:                                                     |
|   * AGENTS.md + CLAUDE.md (symlink)                             |
|   * dist/repo.meta.json (validates against org schema)          |
|   * dist/<exposes_kind>.json (whatever the repo declares it     |
|     owns — e.g. m-cli/dist/commands.json,                       |
|     m-stdlib/dist/stdlib-manifest.json,                         |
|     m-dev-tools-mcp/dist/mcp-tools.json)                        |
|   * Makefile target `check-manifest` (regen + git-diff)         |
|   * .github/workflows/ci.yml runs make check on push/PR         |
+-----------------------------------------------------------------+
```

**Currently onboarded:** 10 manifest-bearing repos (tier-1 + tier-2 +
tier-3). The exact list lives in
[`profile/build/build-catalog.py`](../../profile/build/build-catalog.py)
as `TIER_1 + TIER_2 + TIER_3`. Adding a new repo is one line there
(plus the per-repo work — see §4.1).

Why bottom-up matters: a change at Layer 1 (a new module, a renamed
command) flows up automatically. The repo regenerates its dist
manifest, the meta-repo's `make catalog` picks up the change, Layer 3
agents see the new entry. No coordination, no cross-repo PR dance.

---

## 3. The implementation — component flow

This is what happens when an external agent asks Claude Code (or any
MCP-capable client) "how do I parse JSON in M?":

```
+---------------------------+
| User prompts agent:       |
| "How do I parse JSON in M?"|
+-------------+-------------+
              |
              v
+---------------------------+
| Agent (Claude Code, ...)   |
| Loaded llms.txt at startup,|
| sees m-dev-tools-mcp tools |
+-------------+-------------+
              |
              | route_intent("parse JSON in M")
              v
+--------------------------------------------+
| m-dev-tools-mcp (stdio MCP server)         |
|                                            |
|   route_intent_impl + 60s in-memory cache  |
|   match_intent() helper [vendored from     |
|                          Phase 3]          |
+--------+-------------------------+---------+
         |                         |
         | fetch                   | fetch
         v                         v
+---------------+         +---------------------+
| tools.json    |         | task_index.json     |
| (generated)   |         | (hand-curated)      |
+-------+-------+         +----------+----------+
        |                            |
        | byte-idempotent regen      |
        v                            |
+-----------------------------+       |
| profile/build/              |       |
|   build-catalog.py          |       |
+-----+-----------------------+       |
      |                               |
      | fetches each TIER_N           |
      v repo.meta.json                |
                                      |
+-----------------------------+       |
| Per-repo dist/repo.meta.json|       |
|   * exposes.<kind>: URL     |       |
|   * consumes: [typed-IDs]   |       |
|   * verification_commands   |       |
|   * agent_instructions      |       |
+--------------+--------------+       |
               |                      |
               +---- agent receives <--+
                     route_intent's
                     result and may
                     follow with
                     describe(typed_id)
                     which traverses
                     the same fetch
                     chain.
```

The two response paths Layer 3 supports:

- **`route_intent(query: str) -> list[str]`** — returns
  `[primary, *see_also]` typed-IDs that match the query. Uses
  exact-string match first, then keyword overlap with a
  leading-keyword bonus. The vendored `match_intent` helper lives
  in [`m-dev-tools-mcp/src/m_dev_tools_mcp/_discovery.py`](https://github.com/m-dev-tools/m-dev-tools-mcp/blob/main/src/m_dev_tools_mcp/_discovery.py)
  (copy-of-truth from
  [`profile/build/test-discovery-protocol.py`](../../profile/build/test-discovery-protocol.py);
  see §4.3).

- **`describe(typed_id: str) -> dict`** — returns a pointer-blob with
  the URLs the agent should fetch next. Supports `tool:` / `module:`
  / `cmd:` / `recipe:` kinds. Never inlines payloads — preserves the
  "pointers, not facts" invariant end-to-end.

- **`verify(repo: str) -> list[str]`** — lists the repo's declared
  `verification_commands`. **Does not execute them.** Executing
  catalog-derived commands is the agent's decision (with user
  consent); listing them is ours.

### 3.1 The discovery handshake — bidirectional contract

[`profile/build/test-discovery-protocol.py`](../../profile/build/test-discovery-protocol.py)
is the executable specification of how an agent walks the catalog
end-to-end. It runs as `make handshake` on every push/PR. The eight
steps:

```
step 1 -- fetch llms.txt; assert each link returns 200
step 2 -- fetch tools.json; validate against tools.schema.json
step 3 -- fetch task_index.json; assert canonical intent resolves
step 4 -- resolve module:m-stdlib#STDJSON via tools.json
step 5 -- fetch the resolved manifest_url
step 6 -- assert the symbol entry has signature + example
step 7 -- print the routing trail (audit log)
step 8 -- exit 0
```

Any change to Layer 1 or Layer 2 that breaks any of those eight steps
fails CI before merge. Phase 3 also wired a weekly cron firing
`test-discovery-protocol.py --live` against the public URLs to surface
upstream drift between merges (e.g., a renamed dist field that the
local CI fixtures don't catch).

---

## 4. How to extend — growth playbook

The framework is designed for incremental growth. Each scenario below
is a maintainer-runnable workflow, not a freeform refactor.

### 4.1 Add a new repo to the org catalog

1. Author `dist/repo.meta.json` in the new repo. Required fields:
   `id`, `repo`, `role`, `language`, `license`, `agent_instructions`,
   `verified_on`, `exposes`, `verification_commands`. Validate
   against the meta-repo's schema via
   `make check-repo-meta META=path/to/repo.meta.json`.
2. Author `AGENTS.md` (org-aware prose: setup / test / verify /
   guardrails / layout) and symlink `CLAUDE.md -> AGENTS.md`.
3. Wire `make check-manifest` (regen the per-repo dist manifest →
   `git diff --exit-code`).
4. Wire `.github/workflows/ci.yml` to run `make check`.
5. Open PR on the new repo; merge once CI green.
6. On `.github`: add the raw repo.meta.json URL to the appropriate
   `TIER_N` list in
   [`profile/build/build-catalog.py`](../../profile/build/build-catalog.py).
   Run `make catalog && make validate-catalog && make phase0-smoke`;
   commit the regenerated `tools.json`. Optionally add a
   `task_index.json` intent for the new repo.

The new entry materializes deterministically — no hand-edits to
`tools.json` are required.

### 4.2 Add a new tool / module / command to an existing repo

1. Add the source in the owning repo.
2. Regenerate the relevant `dist/<exposes_kind>.json` via the repo's
   `make manifest` (or equivalent).
3. `make check-manifest` must stay clean.
4. PR + merge.
5. The catalog stays unchanged unless `dist/repo.meta.json` itself
   changes (e.g., a brand-new `exposes` kind). Otherwise the agent
   reads the new entry via the same pointer URL it already had.

### 4.3 Add a new MCP tool

1. Author a new `@server.tool()` in
   [`m-dev-tools-mcp/src/m_dev_tools_mcp/server.py`](https://github.com/m-dev-tools/m-dev-tools-mcp/blob/main/src/m_dev_tools_mcp/server.py).
2. Write TDD coverage in `tests/test_<tool>.py` (red → green; pure
   `*_impl` function + thin `*_through_cache` MCP wrapper).
3. Update `tests/test_smoke.py`'s "exactly three tools" assertion if
   the tool set is changing (an additive change requires a plan
   amendment — see [`AGENTS.md`](https://github.com/m-dev-tools/m-dev-tools-mcp/blob/main/AGENTS.md)
   guardrail "Three MCP tools, no more").
4. `make manifest` regen → `make check-manifest` clean.
5. PR + merge.

### 4.4 Add a new manifest kind / `exposes` key

The org schema (`profile/repo.meta.schema.json`)'s `exposes` map is
`additionalProperties: { type: string }` — accepts any kind, the
generator translates it as `<kind>_url` in `tools.json`. So:

1. Pick a kind name (`commands` / `rules` / `lint_rules` /
   `mcp_tools` / `release_wheel` / ...).
2. Add it to the owning repo's `dist/repo.meta.json` under `exposes`.
3. The next `make catalog` on `.github` regenerates the org catalog
   with a `<kind>_url` field on that tool's entry.

If the value is an absolute URL (e.g., a GitHub Release asset), the
generator passes it through verbatim. If it's a path relative to the
repo root, the generator resolves it against the raw-content prefix.

### 4.5 Add a new recipe

1. Author `docs/recipes/<slug>.md` with YAML frontmatter (`id`,
   `title`, `intent`, `touches`, `verified_on`, `ci_verifiable`).
2. Include a `## Steps` bash-fenced block and a
   `## Expected output` section with at least one
   `must contain: <substring>` assertion.
3. If `ci_verifiable: false`, also include a `manual_checklist_url`.
4. Add an intent row under `task_index.json`'s `recipes` category
   pointing at `recipe:<slug>`.
5. `make recipes-check` must stay clean (structural validation only —
   the M toolchain isn't installed in CI; full executable
   verification is a maintainer task when bumping `verified_on`).

### 4.6 Ship the MCP server through a new distribution channel

The MCP server (`m-dev-tools-mcp`) is currently distributed through
four channels:

1. **PyPI** — `pip install m-dev-tools-mcp`. Primary channel; what
   the MCP registry's `server.json` declares.
2. **GitHub Release wheel** — `pip install <release-url>`. Backup
   for environments that can't reach PyPI.
3. **`uvx --from git+...@<tag>`** — source-build pinned to a tag or
   commit. Useful for pre-release testing.
4. **Public MCP registry** at
   [`registry.modelcontextprotocol.io`](https://registry.modelcontextprotocol.io/)
   under the namespace `io.github.m-dev-tools/m-dev-tools-mcp`.
   Registry-aware clients (Codex, Continue, Goose, …) discover the
   server without a hand-written `.mcp.json`.

To add a new channel (a VS Code extension bundling the server, a
Homebrew tap, …):

1. Decide whether the channel is worth the recurring maintenance.
   The MCP registry is one PR per release tag via the
   `mcp-publisher` CLI; a VS Code extension carries the maintenance
   cost of the entire marketplace surface.
2. Add the install path to the
   [`docs/ai-discoverability/ai-users-guide.md`](ai-users-guide.md)
   "For humans" section under §A.1.
3. If the channel exposes a new pointer URL (e.g. a Marketplace
   listing), add it as an `exposes` field on
   `m-dev-tools-mcp/dist/repo.meta.json` — the catalog's
   `build-catalog.py` will surface it as a `<kind>_url` on the
   `tools.m-dev-tools-mcp` entry on the next `make catalog`.
4. If the channel needs versioned releases, wire the publish step
   into `m-dev-tools-mcp/.github/workflows/release.yml` so every
   `v*` tag fires it.

The registry-listing step uses `mcp-publisher login github`
(browser OAuth) and `mcp-publisher publish` — these require a real
human at a browser, so document the steps for the maintainer rather
than expecting CI to do it (GitHub OIDC auth in
`mcp-publisher login github-oidc` mode is the CI-friendly path for
later automation).

---

## 5. Operational invariants

The framework holds together because every architectural promise has
a CI gate that breaks the build if it's violated. The gates:

```
On every push / pull request:

  make check-manifest      Per repo: regenerated dist/*.json equals
                           the committed copy. Catches hand-edits
                           and stale generators.

  make check-agents        AGENTS.md exists; CLAUDE.md is a symlink
                           to it. Enforces single-source-of-truth
                           for agent instructions.

  make check-docs-prose    docs/ holds only markdown + image files.
                           Generated artifacts belong elsewhere.

  make check-catalog       (.github only) Regenerated tools.json
                           equals the committed copy.

  make validate-catalog    (.github only) tools.json + task_index.json
                           validate against their JSON schemas.

  make recipes-check       (.github only) Every recipe under
                           docs/recipes/ passes --validate-only:
                           frontmatter clean + Steps block + at
                           least one must-contain assertion.

  make handshake           (.github only) 8-step discovery walk
                           through (offline fixtures).

Weekly (Monday 14:00 UTC, .github cron):

  test-discovery-protocol.py --live
                           Same 8 steps against the public URLs.
                           Surfaces upstream drift between merges.
```

Together those nine gates make every Layer-1 fact, every Layer-2
generated payload, and every Layer-3 protocol surface verifiable
without running M code in CI.

---

## 6. Where to read more

### Design + planning history

- [AI-discoverability-guide.md](AI-discoverability-guide.md) —
  user-facing intro; first attempt at framing the problem.
- [AI-discoverability-plan.md](AI-discoverability-plan.md) — the
  de-novo design plan. Canonical reference for the three-layer
  decomposition, the success criteria, and the architectural
  inversion vs. hand-maintained `tools.json`.

### Phase plans + exit evidence

Each phase landed with a plan + an evidence file capturing the
exit-gate output (the evidence files document what was true on
landing day; current state can drift). All under [`phases/`](phases/):

- Phase 0 — manifest contract: [`phases/phase0-plan.md`](phases/phase0-plan.md),
  [`phases/phase0-status.md`](phases/phase0-status.md).
- Phase 1 — catalog as build output: [`phases/phase1-plan.md`](phases/phase1-plan.md),
  [`phases/phase1-evidence.md`](phases/phase1-evidence.md).
- Phase 3 — recipes + handshake: [`phases/phase3-plan.md`](phases/phase3-plan.md),
  [`phases/phase3-evidence.md`](phases/phase3-evidence.md).
- Phase 4 — MCP server: [`phases/phase4-plan.md`](phases/phase4-plan.md),
  [`phases/phase4-evidence.md`](phases/phase4-evidence.md).

Phase 2 (tier-2 + tier-3 onboarding) folded into the Phase 1 wave —
same Phase-0 contract, applied to six more repos.

### The framework itself

- [`profile/tools.json`](../../profile/tools.json) — the generated
  org catalog.
- [`profile/task_index.json`](../../profile/task_index.json) —
  hand-curated intent → typed-ID routing.
- [`profile/llms.txt`](../../profile/llms.txt) — the entry-point
  file (cap 40 lines).
- [`profile/repo.meta.schema.json`](../../profile/repo.meta.schema.json)
  — the per-repo manifest contract.
- [`profile/tools.schema.json`](../../profile/tools.schema.json) —
  the org catalog contract.
- [`profile/task_index.schema.json`](../../profile/task_index.schema.json)
  — the intent-routing contract.
- [`profile/recipe.schema.json`](../../profile/recipe.schema.json) —
  the recipe-frontmatter contract.
- [`profile/build/`](../../profile/build/) — `build-catalog.py`,
  `validate-catalog.py`, `validate-repo-meta.py`, `phase0-smoke.py`,
  `test-discovery-protocol.py`, `run-recipe.py`.
- [`docs/recipes/`](../recipes/) — mechanically-runnable Markdown
  recipes.
- [`m-dev-tools-mcp`](https://github.com/m-dev-tools/m-dev-tools-mcp)
  — the MCP server repo. v0.1.0 wheel attached to the
  [v0.1.0 release](https://github.com/m-dev-tools/m-dev-tools-mcp/releases/tag/v0.1.0);
  also published to the
  [official MCP registry](https://registry.modelcontextprotocol.io/)
  as `io.github.m-dev-tools/m-dev-tools-mcp` (Phase 6).
- [`docs/ai-discoverability/ai-users-guide.md`](ai-users-guide.md)
  — the consumer-facing front door (Part A for human developers,
  Part B for AI agents). Read this if you're using the framework
  rather than extending it.

### Phase 5 — closed 2026-05-11

Continuous enforcement hardening. Plan at
[`phases/phase5-plan.md`](phases/phase5-plan.md), exit evidence at
[`phases/phase5-evidence.md`](phases/phase5-evidence.md). All five
tracks landed (A freshness, B link-check + B0 binary-URL fix, C
license-reconcile, D schema-version policing, E this close-out).
Every architectural promise in the framework now has an automated
watchdog; human discipline is no longer the load-bearing path.

The operational loop is complete. Future phases — if any — address
*growth* scenarios (more repos, more tools, more catalog kinds)
rather than enforcement coverage.
