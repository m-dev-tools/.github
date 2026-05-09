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
| [`m-cli`](https://github.com/m-dev-tools/m-cli)                         | The canonical `m <subcommand>` toolchain: `m fmt`, `m lint`, `m test`, `m coverage`, `m doc`, `m doctor`, `m new`, `m run`, `m build`, `m lsp`, plus modernization rules (M-MOD-001..036, 7 lint profiles). |

### Editor support

| Repo | What it is |
|---|---|
| [`tree-sitter-m-vscode`](https://github.com/m-dev-tools/tree-sitter-m-vscode) | VS Code extension — syntax highlighting and language support powered by tree-sitter-m compiled to WASM. Recognises `.m`, `.mac`, `.int` files. |
| [`m-stdlib-vscode`](https://github.com/m-dev-tools/m-stdlib-vscode)     | VS Code extension — manifest-driven hover docs, goto-definition, and completion for the `m-stdlib` public surface. |

### Validation data

| Repo | What it is |
|---|---|
| [`m-modern-corpus`](https://github.com/m-dev-tools/m-modern-corpus)     | Snapshot collection of modern non-VistA M source from active open-source projects (EWD, mgsql, M-Web-Server, YDBOcto auxiliary, YDBTest). Used as a validation corpus for the parser and lint rules. |

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
