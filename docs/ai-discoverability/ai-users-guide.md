---
created: 2026-05-11
last_modified: 2026-05-11
revisions: 1
doc_type: [GUIDE]
lifecycle: active
owner: rmrich5
connections: [function]
title: "m-dev-tools — users guide"
---

# m-dev-tools — users guide

> The front door for **using** m-dev-tools, split between human
> developers (you, configuring an agent) and AI agents (the agent
> itself, reading this guide to understand what's available). If
> you're *extending* the framework rather than using it, the
> foundational reference is
> [`AI-discoverability-architecture.md`](AI-discoverability-architecture.md).

## Table of contents

- [1. What's available](#1-whats-available)
- [Part A — For humans (developers + teams)](#part-a--for-humans-developers--teams)
  - [A.1 Quickest path: install the MCP server in your IDE](#a1-quickest-path-install-the-mcp-server-in-your-ide)
  - [A.2 Alternative: direct catalog access (no MCP)](#a2-alternative-direct-catalog-access-no-mcp)
  - [A.3 Smoke-test the wiring](#a3-smoke-test-the-wiring)
  - [A.4 Troubleshooting](#a4-troubleshooting)
  - [A.5 Reporting issues](#a5-reporting-issues)
- [Part B — For AI agents (reading this to know what to do)](#part-b--for-ai-agents-reading-this-to-know-what-to-do)
  - [B.1 Tools you have access to](#b1-tools-you-have-access-to)
  - [B.2 Typed-ID grammar you'll see](#b2-typed-id-grammar-youll-see)
  - [B.3 Example session](#b3-example-session)
  - [B.4 What you will and will not do](#b4-what-you-will-and-will-not-do)
  - [B.5 If you don't have MCP support](#b5-if-you-dont-have-mcp-support)
- [3. Where to learn more (shared)](#3-where-to-learn-more-shared)

---

## 1. What's available

The org publishes three machine-readable artifacts at known URLs:

- **`llms.txt`** — < 40-line entry point (the standard
  [llmstxt.org](https://llmstxt.org/) format).
- **`tools.json`** — generated catalog of every repo, every
  exposes-URL, every consumes-edge.
- **`task_index.json`** — hand-curated mapping from plain-English
  intent (`"parse JSON in M"`) to typed IDs
  (`module:m-stdlib#STDJSON`).

Plus a thin **MCP server** (`m-dev-tools-mcp`) that wraps all three
behind three tools any MCP-capable agent can call: `route_intent`,
`describe`, `verify`. The server is published to the **official MCP
registry** at
[`registry.modelcontextprotocol.io`](https://registry.modelcontextprotocol.io/)
under the namespace `io.github.m-dev-tools/m-dev-tools-mcp` — so
MCP clients that browse the registry pick it up without
hand-rolling a config file.

Continuous-enforcement gates ([Phase 5
evidence](phases/phase5-evidence.md)) keep `verified_on` fresh, URLs
live, declared licenses honest, and schema changes documented — so
the agent isn't reading stale facts.

---

## Part A — For humans (developers + teams)

You're a developer who wants their AI assistant to give correct
answers about m-dev-tools without you supervising every step. This
part is about the wiring.

### A.1 Quickest path: install the MCP server in your IDE

Pick the option that matches the AI extension you're using.

#### Option 0 — PyPI (works for any MCP client that points at a binary on `$PATH`)

```bash
pip install m-dev-tools-mcp
# or with uv:
uv pip install m-dev-tools-mcp
```

Then point your client's MCP config at the `m-dev-tools-mcp`
executable. For Claude Code's `.mcp.json`:

```json
{
  "mcpServers": {
    "m-dev-tools": { "command": "m-dev-tools-mcp" }
  }
}
```

For Copilot Chat's `.vscode/mcp.json`:

```json
{
  "servers": {
    "m-dev-tools": { "type": "stdio", "command": "m-dev-tools-mcp" }
  }
}
```

This is the recommended path once `m-dev-tools-mcp` is on PyPI
(target: Phase 6 ship). Options 1–3 below all still work and are
the fallbacks when you'd rather not `pip install` into your
environment.

#### Option 1 — GitHub Copilot Chat (VS Code, agent mode)

Create `.vscode/mcp.json` at your workspace root:

```json
{
  "servers": {
    "m-dev-tools": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/m-dev-tools/m-dev-tools-mcp@v0.1.0",
        "m-dev-tools-mcp"
      ]
    }
  }
}
```

Open Copilot Chat → switch to **Agent** mode → the three tools
(`route_intent`, `describe`, `verify`) appear in the tool list.

#### Option 2 — Claude Code (anthropic.claude-code extension or terminal)

Create `.mcp.json` at your workspace root (or
`~/.config/claude/.mcp.json` for user-level):

```json
{
  "mcpServers": {
    "m-dev-tools": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/m-dev-tools/m-dev-tools-mcp@v0.1.0",
        "m-dev-tools-mcp"
      ]
    }
  }
}
```

Reload Claude Code. Ask `list your MCP tools` → expect
`route_intent`, `describe`, `verify`.

#### Option 3 — Any MCP-capable agent via the public registry

If your client supports the MCP registry directly (e.g. modern
Codex, Continue, Goose, …), point it at the registry entry:

```
io.github.m-dev-tools/m-dev-tools-mcp
```

The client fetches the server's `server.json` metadata from
`registry.modelcontextprotocol.io` and configures itself. No
hand-rolled `.mcp.json` needed.

#### Prerequisite — `uv` (provides `uvx`)

Required for Options 1 and 2. One-line install:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Option 3 (registry-driven) does not require `uv` on your machine —
the client decides how to launch the server.

#### Pin to a version

`@v0.1.0` is pinned to the released tag. Use `@main` to ride latest
(see [Releases](https://github.com/m-dev-tools/m-dev-tools-mcp/releases)
for what's in each tag).

### A.2 Alternative: direct catalog access (no MCP)

If your agent doesn't support MCP, point it at the three raw URLs
directly:

- `https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/llms.txt`
- `https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/tools.json`
- `https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/task_index.json`

The agent then walks the routing trail itself: find an intent row,
follow `primary` → `tools.<key>.<kind>_url`, fetch the manifest. The
8-step handshake in
[`AI-discoverability-architecture.md` §3.1](AI-discoverability-architecture.md#31-the-discovery-handshake--bidirectional-contract)
spells out the canonical sequence.

The MCP server is a thin wrapper over exactly this flow — it doesn't
have hidden behavior the raw catalog can't reproduce.

### A.3 Smoke-test the wiring

Don't want to open an agent just to find out the install is broken?
Shell the MCP server's CLI mode directly:

```bash
uvx --from "git+https://github.com/m-dev-tools/m-dev-tools-mcp@v0.1.0" \
    m-dev-tools-mcp --tool route_intent --query "parse JSON in M"
# expected: ["module:m-stdlib#STDJSON"]
```

Or clone and run the canned smoke:

```bash
git clone https://github.com/m-dev-tools/m-dev-tools-mcp
cd m-dev-tools-mcp
./examples/claude-code/smoke.sh
```

If either exits 0 with the typed ID, the server itself works; any
remaining issue is on the IDE-config side.

### A.4 Troubleshooting

| Symptom | Fix |
|---|---|
| `uvx: command not found` | Install `uv`: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Copilot Chat shows no `route_intent` tool | Confirm `.vscode/mcp.json` is in the workspace root, switch to **Agent** mode, restart VS Code |
| Claude Code "list your MCP tools" returns nothing | Confirm `.mcp.json` is in the workspace root or `~/.config/claude/`; reload Claude Code |
| Server crashes on launch | You're probably pinned to `@main` and HEAD landed broken. Pin to `@v0.1.0` (or a later release tag) |
| `route_intent` returns `[]` for everything | The catalog isn't reachable. Check internet; the server does live fetches over HTTPS, no offline mode |
| A tool returns a stale `verified_on` | The weekly cron in `.github`'s CI catches stale within 7 days. Don't want to wait? File an issue on the relevant repo |

### A.5 Reporting issues

- **MCP-server bugs** (wrong typed ID, server crashes on a query) →
  <https://github.com/m-dev-tools/m-dev-tools-mcp/issues>
- **Catalog bugs** (404'd `*_url`, wrong intent routing, missing
  recipe) →
  <https://github.com/m-dev-tools/.github/issues>
- **Per-repo bugs** (e.g. `STDJSON` behavior differs from the
  manifest) → file on the owning repo. `describe`'s response
  includes the repo URL — go straight there.

---

## Part B — For AI agents (reading this to know what to do)

You're an agent. A user just registered the `m-dev-tools` MCP server
or pointed you at the catalog directly. This part tells you what
you can call and what to do with it.

### B.1 Tools you have access to

If MCP is wired up (the common case — `.mcp.json` or registry
entry), you have three tools:

| Tool | Signature | Returns |
|---|---|---|
| `route_intent` | `(query: str) -> list[str]` | Typed IDs matching the intent. Example: `"parse JSON in M"` → `["module:m-stdlib#STDJSON"]`. First call when a user asks about M tooling. |
| `describe` | `(typed_id: str) -> dict` | Pointer-blob with `manifest_url`, `agent_instructions`, `verification_commands`. Supports `tool:` / `module:` / `cmd:` / `recipe:` kinds. **Returns URLs, never inlines payloads.** |
| `verify` | `(repo: str) -> list[str]` | Lists a repo's declared `verification_commands`. **Does not execute them** — see §B.4. |

The MCP framework gives you a JSON schema for each tool's parameters
on connect; you don't have to memorize the signatures from this
doc.

### B.2 Typed-ID grammar you'll see

Pattern:
`^(tool|cmd|module|rule|doc|data|workflow|task|recipe):[a-z0-9_-]+(#[A-Za-z0-9._-]+)?$`

| Kind | Example | What `describe` returns |
|---|---|---|
| `tool:` | `tool:m-cli` | The repo's `*_url` pointers + `agent_instructions` + `verification_commands` |
| `module:` | `module:m-stdlib#STDJSON` | The `manifest_url` for fetching signatures + worked examples; parent tool pointer |
| `cmd:` | `cmd:m-cli#test` | The `commands_url` (per-subcommand manifest) + parent tool |
| `recipe:` | `recipe:new-app-tdd-ci` | HTTPS + raw URLs of a mechanically-runnable recipe under `docs/recipes/` |

`rule:` / `doc:` / `data:` / `workflow:` / `task:` are valid in the
grammar but not currently handled by `describe`. If you encounter
one, return the typed ID to the user as a citation rather than
attempting to resolve it.

### B.3 Example session

User: *"How do I parse a JSON string in M into a tree?"*

```
call route_intent("parse JSON in M")
  → ["module:m-stdlib#STDJSON"]

call describe("module:m-stdlib#STDJSON")
  → { typed_id, symbol: "STDJSON",
      manifest_url: "…/m-stdlib/main/dist/stdlib-manifest.json",
      tool: { repo, agent_instructions, modules_url, … } }

fetch manifest_url (HTTP GET)
  → find parse^STDJSON signature + example

Compose answer:
  "Use `parse^STDJSON(jsonText, .tree)`. It populates `tree` with one
  node per JSON value; strings get the prefix \"s:\". Worked
  example from the manifest: …"
```

Key invariant: never guess the API surface. Every claim should be
grounded in a `manifest_url` you actually fetched.

### B.4 What you will and will not do

**Will:**

- Route plain-English intent to typed IDs (single `route_intent` call).
- Fetch real signatures + worked examples from per-repo manifests.
- Surface a repo's `verification_commands` so the user can decide to
  run them.
- Cite the manifest URL you used in your answer.

**Will not:**

- Execute commands on your own. `verify` *lists* what a repo
  declared; running them is the user's call.
- Fabricate APIs. If a symbol isn't in the manifest, say so rather
  than inventing one.
- Cache catalog state on disk. The MCP server keeps a 60-second
  in-process cache so a session amortizes fetches, but nothing hits
  the filesystem.

The `verify` "don't execute" choice is a security stance, not an
oversight — see
[phase4-plan.md §3 B5](phases/phase4-plan.md) for the rationale.

### B.5 If you don't have MCP support

Fetch the three raw catalog URLs and walk the 8-step handshake:

1. `GET …/profile/llms.txt`
2. `GET …/profile/tools.json`, validate against `tools.schema.json`
3. `GET …/profile/task_index.json`, find matching intent row
4. Take the row's `primary` typed ID, look it up in
   `tools.json` to get its `*_url`
5. `GET` that manifest URL
6. Read signature + example
7. Compose the answer
8. Cite the manifest URL

The MCP server does steps 1–6 for you and returns the manifest URL
ready to cite. The raw-catalog path is functionally identical, just
more round-trips.

---

## 3. Where to learn more (shared)

- [`AI-discoverability-architecture.md`](AI-discoverability-architecture.md)
  — the master architecture doc. First principles → three-layer
  design → component flow → growth playbook. Read this if you want
  to *extend* the framework.
- [`AI-discoverability-plan.md`](AI-discoverability-plan.md) — the
  original de-novo design plan with success criteria.
- [`AI-discoverability-guide.md`](AI-discoverability-guide.md) — the
  earlier user-facing intro; lighter weight than the architecture
  doc.
- [`phases/`](phases/) — five phase plans + matching evidence files
  (Phase 0 manifest contract → Phase 1 catalog-as-build-output →
  Phase 3 recipes + handshake → Phase 4 MCP server → Phase 5
  continuous enforcement). Each evidence doc cites the exit-gate
  output, so an agent can reproduce the framework's claims from
  history.
- [`m-dev-tools-mcp`](https://github.com/m-dev-tools/m-dev-tools-mcp)
  — the MCP server repo (the same repo `uvx` clones above). The
  `AGENTS.md` there has the per-tool contracts in more detail.
- [Official MCP registry entry](https://registry.modelcontextprotocol.io/)
  — search for `io.github.m-dev-tools/m-dev-tools-mcp`. The
  registry-driven install path (Option 3 above) reads from here.
