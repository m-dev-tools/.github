---
created: 2026-05-11
last_modified: 2026-05-11
revisions: 0
doc_type: [GUIDE]
lifecycle: active
owner: rmrich5
connections: [function]
title: "m-dev-tools — AI user's guide"
---

# m-dev-tools — AI user's guide

> The front door for using `m-dev-tools` as an LLM-based agent or
> automated tool. Read this when you want an agent (Claude Code,
> Codex, Continue, …) to route plain-English questions about M
> tooling to the right repo without you hand-holding it.

If you're building the framework itself or extending its
enforcement coverage, the foundational reference is
[`AI-discoverability-architecture.md`](AI-discoverability-architecture.md).
This guide is the *consumer* counterpart: how to wire your agent in
and what it can do once you have.

---

## 1. What "AI-enabled" means here

The org publishes three machine-readable artifacts at known URLs:

- **`llms.txt`** — < 40-line entry point (the standard
  [llmstxt.org](https://llmstxt.org/) format).
- **`tools.json`** — generated catalog of every repo, every
  exposes-URL, every consumes-edge. One line per repo + pointer URLs
  to deeper manifests.
- **`task_index.json`** — hand-curated mapping from plain-English
  intent (`"parse JSON in M"`) to typed IDs (`module:m-stdlib#STDJSON`).

Plus a thin **MCP server** that wraps all three behind three tools
your agent can call directly: `route_intent`, `describe`, `verify`.

Continuous-enforcement gates ([Phase 5
evidence](phases/phase5-evidence.md)) keep `verified_on` fresh, URLs
live, declared licenses honest, and schema changes documented — so
the agent isn't reading stale facts.

## 2. Two install paths

Pick one based on how your agent loads tools.

### Path A — MCP (recommended)

Drop this into your project's `.mcp.json` (Claude Code, Codex,
Continue, any MCP-capable agent):

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

Pin to `@v0.1.0` for reproducibility, or `@main` to ride latest.

Confirm the server registered:

```bash
claude --print "list your MCP tools"
# expected: route_intent, describe, verify
```

Three tools become available:

| Tool | Signature | Returns |
|---|---|---|
| `route_intent` | `(query: str) -> list[str]` | Typed IDs matching the intent. Example: `"parse JSON in M"` → `["module:m-stdlib#STDJSON"]`. |
| `describe` | `(typed_id: str) -> dict` | Pointer-blob with `manifest_url`, `agent_instructions`, `verification_commands`. Supports `tool:` / `module:` / `cmd:` / `recipe:` kinds. Returns URLs the caller should fetch next — never inlines payloads. |
| `verify` | `(repo: str) -> list[str]` | Lists a repo's declared `verification_commands`. **Does not execute them** — that's your decision. |

### Path B — raw catalog (no MCP)

If your agent doesn't support MCP, point it at the three raw URLs
directly:

- `https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/llms.txt`
- `https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/tools.json`
- `https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/task_index.json`

The agent then walks the routing trail itself: find an intent row in
`task_index.json`, follow `primary` → `tools.<key>.<kind>_url`, fetch
the manifest. The 8-step handshake in
[`AI-discoverability-architecture.md` §3.1](AI-discoverability-architecture.md#31-the-discovery-handshake--bidirectional-contract)
spells out the canonical sequence.

The MCP server (Path A) is a thin wrapper over exactly this flow —
it doesn't have hidden behavior the raw catalog can't reproduce.

## 3. Example session — Claude Code

User opens a project that has the `.mcp.json` from §2.

```
> How do I parse a JSON string in M into a tree?

(Claude calls route_intent("parse JSON in M"))
→ ["module:m-stdlib#STDJSON"]

(Claude calls describe("module:m-stdlib#STDJSON"))
→ { typed_id, symbol: "STDJSON",
    manifest_url: "https://raw.githubusercontent.com/m-dev-tools/m-stdlib/main/dist/stdlib-manifest.json",
    tool: { typed_id: "tool:m-stdlib",
            repo: "https://github.com/m-dev-tools/m-stdlib",
            agent_instructions: "…/AGENTS.md",
            modules_url: "…/dist/stdlib-manifest.json" } }

(Claude fetches stdlib-manifest.json, finds parse^STDJSON's signature
+ worked example)

Claude: Use `parse^STDJSON(jsonText, .tree)`. It populates `tree`
with one node per JSON value; strings get the prefix "s:". Worked
example: …
```

The key invariant: Claude never guesses the API surface — every
claim is grounded in a manifest URL the agent actually fetched.

## 4. Example session — agent-free shell smoke

Don't want to open an agent? `examples/claude-code/smoke.sh` (in the
[m-dev-tools-mcp repo](https://github.com/m-dev-tools/m-dev-tools-mcp/tree/v0.1.0/examples/claude-code))
shells the same `route_intent` query through the MCP server's CLI
mode and asserts the canonical typed ID lands in the response:

```bash
git clone https://github.com/m-dev-tools/m-dev-tools-mcp
cd m-dev-tools-mcp
./examples/claude-code/smoke.sh
# → "module:m-stdlib#STDJSON"
```

Useful for CI or as a quick sanity check after install.

## 5. The four typed-ID kinds your agent will see

| Kind | Example | What it points at |
|---|---|---|
| `tool:` | `tool:m-cli` | A repo (m-cli, m-stdlib, …). `describe` returns the repo's `*_url` pointers + agent_instructions + verification_commands. |
| `module:` | `module:m-stdlib#STDJSON` | A symbol in a repo's manifest. `describe` resolves to the manifest URL for fetching signatures + examples. |
| `cmd:` | `cmd:m-cli#test` | An m-cli subcommand. `describe` returns `commands_url` (the per-subcommand manifest) + parent tool. |
| `recipe:` | `recipe:new-app-tdd-ci` | A mechanically-runnable workflow under `docs/recipes/`. `describe` returns the recipe's HTTPS + raw URLs. |

Other kinds (`rule:` / `doc:` / `data:` / `workflow:` / `task:`)
exist in the typed-ID grammar but `describe` currently handles the
four above. Adding a kind is a small change — file an issue if you
need it.

## 6. What the agent will and will not do

**Will:**

- Route from plain-English intent to typed IDs (single call).
- Fetch real signatures + worked examples from per-repo manifests.
- Surface a repo's `verification_commands` so you can decide to run
  them.

**Will not:**

- Execute commands on its own. `verify` *lists* what a repo declared;
  running them is your call.
- Fabricate APIs. If a symbol isn't in the manifest, the agent
  surfaces "I don't have a verified source for that" rather than
  guessing.
- Cache state on disk. The MCP server keeps a 60-second in-process
  cache so a Claude-Code interaction amortizes fetches, but nothing
  hits the filesystem.

The `verify` "don't execute" choice is a security stance, not an
oversight — see
[phase4-plan.md §3 B5](phases/phase4-plan.md) for the rationale.

## 7. Troubleshooting

**`uvx` not found.** Install [`uv`](https://docs.astral.sh/uv/) first:
`curl -LsSf https://astral.sh/uv/install.sh | sh`.

**`claude --print "list your MCP tools"` returns nothing.** Check
`.mcp.json` is in the repo root or your home `.config/claude/`
directory. Restart Claude Code after editing.

**The MCP server crashes on launch.** Pinning to `@main` picks up
breakage on first push. Pin to `@v0.1.0` (or the latest release tag —
see <https://github.com/m-dev-tools/m-dev-tools-mcp/releases>) for
stability.

**The catalog returns a stale `verified_on` for a tool.** The weekly
cron in `.github`'s CI catches that within 7 days. If you're not
willing to wait, file an issue on the relevant repo asking the
maintainer to re-run the verification commands + bump `verified_on`.

**Network unreachable on first call.** The MCP server has no offline
mode for live operation. The CLI flag `--offline` exists on each
gate but not on the server itself. Use the raw catalog (Path B) with
a local checkout if you genuinely need offline.

## 8. Where to learn more

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
  — the MCP server repo (the same repo `uvx` clones in Path A
  above). The `AGENTS.md` there has the per-tool contracts in more
  detail.

## 9. Reporting issues

The framework is CI-gated end-to-end, but bugs still happen. Report
them at:

- **MCP-server bugs** (a tool returns the wrong typed ID, the server
  crashes on a query) →
  <https://github.com/m-dev-tools/m-dev-tools-mcp/issues>
- **Catalog bugs** (a `*_url` 404s, an intent routes wrong, a recipe
  references a removed function) →
  <https://github.com/m-dev-tools/.github/issues>
- **Per-repo bugs** (e.g. m-stdlib STDJSON behavior differs from the
  manifest) → file on the owning repo. The MCP `describe` response
  includes the repo URL — go straight there.
