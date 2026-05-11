# m-dev-tools

**A suite of engine-neutral developer tools for the M (MUMPS) programming
language, built around a CI/CD-friendly, test-driven-development workflow.**
At the center sit two complementary projects:
[`m-stdlib`](https://github.com/m-dev-tools/m-stdlib), a pure-M runtime
**standard library** (assertions, fixtures, mocks, JSON, regex, HTTP,
crypto, logging, …) that gives every test the primitives it needs to be
expressive, isolated, and reproducible; and
[`m-cli`](https://github.com/m-dev-tools/m-cli), the
`m <subcommand>` **command-line toolchain** (`m fmt`, `m lint`, `m test`,
`m coverage`, `m watch`, `m lsp`, …) that makes the *red → green →
refactor* loop, pre-commit hooks, coverage gates, and CI pipelines a
first-class experience. Together with a real parser
([`tree-sitter-m`](https://github.com/m-dev-tools/tree-sitter-m)),
a citable language reference
([`m-standard`](https://github.com/m-dev-tools/m-standard)), a lightweight
containerized test engine
([`m-test-engine`](https://github.com/m-dev-tools/m-test-engine)), and
editor integrations, they form an end-to-end TDD stack that works
identically for **InterSystems IRIS** and **YottaDB** developers
maintaining modern (non-VistA) M code.

## For AI agents and automated tooling

**m-dev-tools is fully AI-enabled with an MCP endpoint.** The fastest path is to point any MCP-capable agent (Claude Code, Codex, Continue, …) at [`m-dev-tools-mcp`](https://github.com/m-dev-tools/m-dev-tools-mcp); drop this into your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "m-dev-tools": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/m-dev-tools/m-dev-tools-mcp@v0.1.0", "m-dev-tools-mcp"]
    }
  }
}
```

The server exposes three tools — `route_intent("parse JSON in M") → ["module:m-stdlib#STDJSON"]`, `describe(typed_id) → pointer-blob`, `verify(repo) → verification_commands` (lists, doesn't execute) — that walk the catalog for you and ground every claim in a manifest URL the agent actually fetched. No fabricated APIs.

**Full walkthrough:** [`docs/ai-discoverability/ai-users-guide.md`](../docs/ai-discoverability/ai-users-guide.md) — install paths, example sessions, troubleshooting, where to file bugs.

**Direct catalog access** (no MCP) is still supported — start at [`tools.json`](tools.json) (machine-readable catalog of every repo + every `*_url` pointer + `consumed_by` graph) and [`task_index.json`](task_index.json) (hand-curated intent → typed-ID routing). The 8-step discovery handshake in [`AI-discoverability-architecture.md`](../docs/ai-discoverability/AI-discoverability-architecture.md) spells out the canonical sequence. Four continuous-enforcement gates (freshness / link-check / license-reconcile / schema-version) keep the catalog honest — every PR + a weekly cron firing. See [`docs/ai-discoverability/`](../docs/ai-discoverability/) for the full framework.

Manifest pointers for symbol-level lookups:
- **m-stdlib API** → [`dist/stdlib-manifest.json`](https://raw.githubusercontent.com/m-dev-tools/m-stdlib/main/dist/stdlib-manifest.json)
- **M language surface** → [`integrated/grammar-surface.json`](https://raw.githubusercontent.com/m-dev-tools/m-standard/main/integrated/grammar-surface.json)

## Repositories

### Foundation

| Repo | What it is |
|---|---|
| [`tree-sitter-m`](https://github.com/m-dev-tools/tree-sitter-m)         | Tree-sitter grammar for M. 99.06% clean on the 39,330-routine VistA corpus. Bindings for Node, Rust, Python, Go. |
| [`m-standard`](https://github.com/m-dev-tools/m-standard)               | Citable, machine-readable M-language reference reconciling the ANSI standard, YottaDB docs, and InterSystems IRIS docs. |
| [`m-stdlib`](https://github.com/m-dev-tools/m-stdlib)                   | Pure-M (and selectively `$ZF`-bound) runtime standard library — assertions, JSON, regex, datetime, CSV, argparse, fixtures, mocks, logging, UUID, base64, HTTP, crypto, compression, and more. YottaDB-first; IRIS-portable where reasonable. |

### Toolchain

| Repo | What it is |
|---|---|
| [`m-cli`](https://github.com/m-dev-tools/m-cli)                         | The canonical `m <subcommand>` toolchain: `m fmt`, `m lint`, `m test`, `m coverage`, `m watch`, `m lsp`, `m doc`, `m doctor`, `m new`, `m run`, `m build`, `m ci init`, plus modernization rules (M-MOD-001..036, 8 lint profiles). |
| [`m-cli-extras`](https://github.com/m-dev-tools/m-cli-extras)           | Out-of-tree subcommands for `m-cli` (e.g. `m corpus-stats`), registered via the `m_cli.plugins` entry-point group. The bucket for niche utilities that shouldn't bloat core. |
| [`m-test-engine`](https://github.com/m-dev-tools/m-test-engine)         | Minimal YottaDB Docker container for `m-cli` and `m-stdlib` testing. The lightweight default for non-VistA M development — no SSH server, no FileMan, just an engine that `docker exec` can drive. |

### Editor support

| Repo | What it is |
|---|---|
| [`tree-sitter-m-vscode`](https://github.com/m-dev-tools/tree-sitter-m-vscode) | VS Code extension — syntax highlighting and language support powered by tree-sitter-m compiled to WASM. Spawns `m lsp` for live diagnostics, formatting, and Quick Fix code actions when m-cli is installed. |
| [`m-stdlib-vscode`](https://github.com/m-dev-tools/m-stdlib-vscode)     | VS Code extension — manifest-driven hover docs, goto-definition, and completion for the `m-stdlib` public surface. |

### Validation data

| Repo | What it is |
|---|---|
| [`m-modern-corpus`](https://github.com/m-dev-tools/m-modern-corpus)     | Snapshot collection of modern non-VistA M source from active open-source projects (EWD, mgsql, M-Web-Server, YDBOcto auxiliary, YDBTest). Used as a validation corpus for the parser and lint rules. |

### Historical root

| Where | What it is |
|---|---|
| [`.github/docs/history/`](../docs/history/) | Frozen in-org snapshots of the design documents that seeded the entire org — the original 2026 gap analysis, the Tier 1–4 strategy, and the `m <subcommand>` command map that produced everything above. Imported verbatim from the (now archived) [`m-tools`](https://github.com/m-dev-tools/m-tools) repo. Start here for the *why*. |

## How the pieces connect

```
                          ┌────────────────────────────────────┐
                          │   .github/docs/history/            │
                          │   (frozen snapshots from the       │
                          │    archived m-tools seed repo)     │
                          │   • original gap analysis          │
                          │   • Tier 1–4 strategy docs         │
                          └─────────────────┬──────────────────┘
                                            │ shaped
                                            ▼
   ════════════════════════════ FOUNDATION ════════════════════════════════

   ┌────────────────────────┐                  ┌──────────────────────────┐
   │      m-standard        │  grammar-surface │      tree-sitter-m       │
   │  citable M reference   │ ───────────────▶ │   parser → AST           │
   │  ANSI ⊕ YDB ⊕ IRIS ⊕   │      .json       │   99.06 % on VistA       │
   │  VA SAC, as TSV+JSON   │                  │   WASM · JS · Rust ·     │
   └────────────┬───────────┘                  │   Python · Go bindings   │
                │ TSVs                         └──────────────┬───────────┘
                │ (commands, ISVs, functions)                 │ AST
                │                                             │
   ════════════════════════════ TOOLCHAIN ═════════════════════════════════
                │                                             │
                ▼                                             ▼
   ┌────────────────────────────────────────────────────────────────────┐
   │                              m-cli                                 │
   │   m fmt    m lint    m test    m coverage    m watch    m lsp      │
   │   m doc    m new     m run     m build       m doctor   m ci       │
   └────┬─────────────────┬─────────────────────────────┬────────────────┘
        │ entry-points    │ docker exec                 │ manifest
        ▼                 ▼                             ▼
   ┌──────────────┐  ┌──────────────────┐  ┌─────────────────────────────┐
   │ m-cli-extras │  │  m-test-engine   │  │          m-stdlib           │
   │ out-of-tree  │  │ minimal YDB      │  │ pure-M runtime — STDJSON,   │
   │ plugins      │  │ Docker container │◀─│ STDREGEX, STDHTTP, STDFS,   │
   │ (corpus-     │  │ (`docker exec`,  │  │ STDASSERT, STDFIX, STDMOCK, │
   │ stats, …)    │  │  /work mount)    │  │ STDCRYPTO, STDLOG, … 32 mods│
   └──────────────┘  └──────────────────┘  └───────────────┬─────────────┘
                                                           │ stdlib-manifest.json
   ════════════════════════════ EDITORS ═══════════════════════════════════
                                                           │
   ┌──────────────────────────────┐         ┌──────────────▼───────────────┐
   │   tree-sitter-m-vscode       │         │      m-stdlib-vscode         │
   │ • WASM syntax highlighting   │         │ • hover docs                 │
   │ • spawns `m lsp` for live    │         │ • goto-definition            │
   │   diagnostics + Quick Fix    │         │ • completion for STD*        │
   │ • workspace smoke-report     │         │   symbols in .m files        │
   └──────────────────────┬───────┘         └──────────────────────────────┘
                          │ uses tree-sitter-m WASM
                          ▼
   ════════════════════════════ VALIDATION ════════════════════════════════

   ┌──────────────────────────────────────────────────────────────────────┐
   │                          m-modern-corpus                             │
   │  Snapshots of modern non-VistA M (EWD, mgsql, YDBOcto aux, YDBTest)  │
   │  — calibrates the parser's grammar gates and m-cli's M-MOD-NN rules  │
   │  against contemporary idioms rather than legacy VA conventions.      │
   └──────────────────────────────────────────────────────────────────────┘
```

**Reading the diagram from the top:**

1. [`m-standard`](https://github.com/m-dev-tools/m-standard) reconciles
   four authoritative M sources (the ANSI standard, YottaDB's docs,
   InterSystems IRIS's docs, and the VA SAC / XINDEX rule set) into a
   single citable reference. It emits `grammar-surface.json` and a
   family of TSVs.
2. [`tree-sitter-m`](https://github.com/m-dev-tools/tree-sitter-m) is
   **generated** from m-standard's grammar surface — one coupling
   point, pinned by `schema_version` — so the parser stays honest to
   the published reference.
3. [`m-cli`](https://github.com/m-dev-tools/m-cli) consumes both: the
   parser for AST-driven `m fmt` / `m lint` / `m test` / coverage /
   LSP, and the TSVs for keyword classification (every command,
   intrinsic function, and special variable in every profile).
4. **Three things plug into m-cli:**
   [`m-cli-extras`](https://github.com/m-dev-tools/m-cli-extras) via
   the `m_cli.plugins` entry-point group;
   [`m-test-engine`](https://github.com/m-dev-tools/m-test-engine) via
   `docker exec` (m-cli's `m test` and `m coverage` shell commands at
   the container, which bind-mounts the consumer's source at `/work`);
   and [`m-stdlib`](https://github.com/m-dev-tools/m-stdlib) via the
   manifest that `m doc` / `m search` / `m examples` / `m errors` read
   to surface the STD\* public surface.
5. **m-stdlib runs its own tests through the same engine** —
   m-test-engine is the shared YottaDB substrate for both the toolchain
   and the runtime library, so a working CI install for one project is
   automatically a working CI install for the other.
6. **Editors layer on top.** The
   [`tree-sitter-m-vscode`](https://github.com/m-dev-tools/tree-sitter-m-vscode)
   extension renders syntax via the parser's WASM build *and* spawns
   `m lsp` for live diagnostics / Quick Fix / hover / completion;
   [`m-stdlib-vscode`](https://github.com/m-dev-tools/m-stdlib-vscode)
   reads m-stdlib's manifest directly for STD\*-specific hover,
   goto-def, and completion.
7. [`m-modern-corpus`](https://github.com/m-dev-tools/m-modern-corpus)
   is the regression substrate for both the parser and the linter —
   the M-MOD-NN rule track was calibrated against this corpus so
   `m lint --rules=default` produces ~3 findings per routine on
   modern code rather than the ~57 the legacy XINDEX rules emit.

## Why this exists

M (MUMPS) is the language behind a great deal of healthcare and financial
infrastructure, but its modern developer tooling has historically lagged
behind mainstream languages. **`m-dev-tools`** provides the missing
source-level pieces — a real parser, a unified language reference, a
runtime standard library, and a `git`/`cargo`/`go`-style command-line
toolchain — engineered to be useful regardless of which M engine you run.

The toolchain is **engine-neutral at the source layer** (`m fmt` and
`m lint` care about M syntax, not a specific runtime), and **YottaDB-first
with IRIS portability** at the runtime layer (test runner, coverage,
stdlib).

## Getting started

A typical first install:

```bash
# Foundation: parser + toolchain
git clone https://github.com/m-dev-tools/tree-sitter-m
git clone https://github.com/m-dev-tools/m-cli
pip install ./tree-sitter-m   # order matters — m-cli's dep declaration
pip install ./m-cli           # needs the tree-sitter-m checkout present

# Verify
m doctor
m --help
```

For runtime work on YottaDB, also clone [`m-stdlib`](https://github.com/m-dev-tools/m-stdlib).
For VS Code, install the marketplace extensions (currently published under
the personal `rafael5` publisher; rebranding to a `m-dev-tools` Marketplace
publisher is on the roadmap).

## Licensing

Most repos are **AGPL-3.0**, the two VS Code extensions are **MIT** to
align with the broader extension ecosystem, and `m-modern-corpus` carries
**per-subdirectory upstream licenses** (see its `LICENSES.md`). A migrated
repo's license is the canonical statement; this README is summary only.

## Audience

Maintainers and tool authors working on:

- **IRIS** ObjectScript / Caché-derived M codebases (cooperative scope —
  IRIS extensions are documented as `iris-extension`, not "ANSI")
- **YottaDB** — the open-source M engine; default test target
- General-purpose M libraries that aim to work on either engine
- Editor and AI-assistant integrations that need a real M parser

VistA-specific code, FileMan, RPC infrastructure, and KIDS tooling live in
separate repositories under a different organization. `m-dev-tools` is
explicitly the **engine-neutral, modern-M** half of the ecosystem.
