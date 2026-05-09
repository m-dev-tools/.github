# m-dev-tools

Engine-neutral developer tooling for the **M (MUMPS)** programming language —
parser, language reference, runtime standard library, source-level toolchain,
and editor integrations. Designed to work for both **InterSystems IRIS** and
**YottaDB** developers maintaining modern (non-VistA) M code.

## Repositories

### Foundation

| Repo | What it is |
|---|---|
| [`tree-sitter-m`](https://github.com/m-dev-tools/tree-sitter-m)         | Tree-sitter grammar for M. 99.06% clean on the 39,330-routine VistA corpus. Bindings for Node, Rust, Python, Go. |
| [`m-standard`](https://github.com/m-dev-tools/m-standard)               | Citable, machine-readable M-language reference reconciling the ANSI standard, YottaDB docs, and InterSystems IRIS docs. |
| [`m-stdlib`](https://github.com/m-dev-tools/m-stdlib)                   | Pure-M (and selectively `$ZF`-bound) runtime standard library — assertions, JSON, regex, datetime, CSV, argparse, fixtures, mocks, logging, UUID, base64, and more. YottaDB-first; IRIS-portable where reasonable. |

### Toolchain

| Repo | What it is |
|---|---|
| [`m-cli`](https://github.com/m-dev-tools/m-cli)                         | The canonical `m <subcommand>` toolchain: `m fmt`, `m lint`, `m test`, `m coverage`, `m doc`, `m doctor`, `m new`, `m run`, `m build`, `m lsp`, `m plugins`, plus modernization rules (M-MOD-001..036, 7 lint profiles) and an entry-points-based plugin system for out-of-tree subcommands. |
| [`m-cli-extras`](https://github.com/m-dev-tools/m-cli-extras)           | Out-of-tree m-cli subcommand plugins. First plugin: `m corpus-stats` (file / line / label / parse-error counts across a directory of `.m` files). Pluggable bucket for niche, opinionated, or third-party-flavored utilities. |

### Test engine

| Repo | What it is |
|---|---|
| [`m-test-engine`](https://github.com/m-dev-tools/m-test-engine)         | Minimal YottaDB Docker container (`yottadb/yottadb-base:latest-master` + tail keep-alive) that backs `m test` and `m coverage` runtime. Bind-mounts `$PWD` as `/work`; `m-cli`'s `DockerEngine` transport dispatches via `docker exec`. Replaces vista-meta as the default engine for non-VistA work. |

### Editor support

| Repo | What it is |
|---|---|
| [`tree-sitter-m-vscode`](https://github.com/m-dev-tools/tree-sitter-m-vscode) | VS Code extension — syntax highlighting and language support powered by tree-sitter-m compiled to WASM. Recognises `.m`, `.mac`, `.int` files. Spawns m-cli's `m lsp` Language Server when m-cli is installed. |
| [`m-stdlib-vscode`](https://github.com/m-dev-tools/m-stdlib-vscode)     | VS Code extension — manifest-driven hover docs, goto-definition, and completion for the `m-stdlib` public surface. Ships a bundled `dist/stdlib-manifest.json` snapshot; works on a stock install with no other repo on disk. |

### Validation data

| Repo | What it is |
|---|---|
| [`m-modern-corpus`](https://github.com/m-dev-tools/m-modern-corpus)     | Snapshot collection of modern non-VistA M source from active open-source projects (EWD, mgsql, M-Web-Server, YDBOcto auxiliary, YDBTest). Default validation corpus for `m lint` rule profiles and parser regression gates. |

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

A typical first install of the `m` toolchain (Linux x86_64; pick the
matching wheel URL from the [tree-sitter-m
v0.1.1](https://github.com/m-dev-tools/tree-sitter-m/releases/tag/v0.1.1)
release for other platforms):

```bash
git clone https://github.com/m-dev-tools/m-cli
cd m-cli
uv sync --frozen --extra dev   # picks up the tree-sitter-m wheel from the
                               # GitHub release URL pinned in pyproject.toml
                               # — no sibling tree-sitter-m checkout required

# Verify
.venv/bin/m doctor
.venv/bin/m --help
```

For the test engine (replaces a host YottaDB install):

```bash
git clone https://github.com/m-dev-tools/m-test-engine
make -C m-test-engine up        # boots the YDB Docker container; m-cli
                                # auto-detects via DockerEngine
```

For runtime work on YottaDB, also clone [`m-stdlib`](https://github.com/m-dev-tools/m-stdlib).
For extra subcommands beyond core, install
[`m-cli-extras`](https://github.com/m-dev-tools/m-cli-extras) alongside
m-cli — its plugins register via the `m_cli.plugins` entry-point group
and surface as `m <name>` subcommands.

For VS Code, install the marketplace extensions (currently published under
the personal `rafael5` publisher; rebranding to a `m-dev-tools` Marketplace
publisher is on the roadmap).

## Licensing

Of the nine repos in the org, seven are **AGPL-3.0** (`tree-sitter-m`,
`m-standard`, `m-stdlib`, `m-cli`, `m-cli-extras`, `m-test-engine`,
plus this `.github` org-meta repo); the two VS Code extensions are
**MIT** to align with the broader extension ecosystem; `m-modern-corpus`
carries **per-subdirectory upstream licenses** (see its `LICENSES.md`).
A repo's own LICENSE file is the canonical statement; this README is
summary only.

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
