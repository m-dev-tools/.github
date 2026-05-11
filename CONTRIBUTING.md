# Contributing to m-dev-tools

Thanks for considering a contribution to the **m-dev-tools** org. This
file is the org-level default — individual repos may add their own
`CONTRIBUTING.md` with repo-specific detail, but the dev loop below
applies to every repo in the org unless that repo says otherwise.

If you're looking for the org overview, repo list, and "why this
exists," see the [landing page](https://github.com/m-dev-tools).

## Prerequisites

By stack:

| Working on… | You need… |
|---|---|
| `m-cli`, `m-stdlib`, `m-standard`, `m-test-engine` | **Python 3.12** + [`uv`](https://docs.astral.sh/uv/) |
| Test/coverage paths in `m-cli` or `m-stdlib` | **Docker** (the simplest engine path) — *or* a local YottaDB install |
| `tree-sitter-m`                          | **Node.js 22** + a C compiler |
| `tree-sitter-m-vscode`, `m-stdlib-vscode` | **Node.js ≥ 18** + **VS Code ≥ 1.85** |
| `m-modern-corpus`                        | nothing — it's a data repo |

You do **not** need a VistA install, the `vista-meta` repo, or a
sibling `tree-sitter-m/` checkout to develop on any m-dev-tools repo.
Closing those dependencies is what the org's "self-contained" sprint
shipped — see the bar below.

## The self-contained dev loop

### Python toolchain repos (`m-cli`, `m-stdlib`)

```bash
git clone https://github.com/m-dev-tools/<repo>
cd <repo>
make install              # uv sync --extra dev + pre-commit hooks
make engine-up            # boots the YottaDB engine via m-test-engine (Docker)
make test                 # full test suite
make engine-down          # tear down when finished
```

`make engine-up` is the new (2026-05) entry point — it delegates to
the [`m-test-engine`](https://github.com/m-dev-tools/m-test-engine)
Docker compose, giving you a running YottaDB without VistA. If you
already have YottaDB installed locally, set `M_CLI_ENGINE=local` and
skip `engine-up` entirely. Auto-detection picks the right transport
when you don't override.

### `m-cli`'s engine transports

`m-cli` ships three engine transports; the one used at runtime is
selected by the `M_CLI_ENGINE` env var (or auto-detected):

| Transport | When to use | How it runs M code |
|---|---|---|
| `local`  | YottaDB is installed natively | direct `ydb -run …` subprocess |
| `docker` | you ran `make engine-up` | `docker exec <container> ydb -run …` |
| `ssh`    | maintainer with vista-meta running | SSH into the vista-meta container |

If none is set explicitly, `detect_engine()` picks: `ssh` if
`~/data/vista-meta/conn.env` exists (legacy maintainer path),
otherwise `docker` if a `m-test-engine` container is running,
otherwise `local`.

### Whole-corpus regression gates

Some `m-cli` targets run lint or round-trip checks across an entire
M corpus. They take a `CORPUS=` flag (env-var fallback) so you don't
need any specific repo on disk:

```bash
make lint-vista                                          # default: m-modern-corpus
make lint-vista CORPUS=$HOME/path/to/some/Packages       # override
```

The default points at
[`m-modern-corpus`](https://github.com/m-dev-tools/m-modern-corpus)
(in the org). VistA-specific gates have moved into `Makefile.vista`
and only activate when the maintainer points `CORPUS` at a VistA
checkout.

### Parser repo (`tree-sitter-m`)

```bash
git clone https://github.com/m-dev-tools/tree-sitter-m
cd tree-sitter-m
npm ci
npm test                              # corpus + lib + coverage gate
```

For the Python binding specifically: install from a tagged release's
prebuilt wheel (no C toolchain needed):

```bash
pip install tree-sitter \
  https://github.com/m-dev-tools/tree-sitter-m/releases/download/v0.1.0/tree_sitter_m-0.1.0-cp310-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
```

(Wheels for linux x64/arm64, macOS x64/arm64, and Windows x64 are
attached to every release; pick the one matching your platform. See
that repo's `RELEASE.md` §5.5 for the full URL set and uv pinning
template.)

### VS Code extensions

Both extensions follow the same loop — see each repo's own
[`CONTRIBUTING.md`](https://github.com/m-dev-tools/tree-sitter-m-vscode/blob/main/CONTRIBUTING.md)
for the full development, packaging, and publishing details.

## The "self-contained" bar

The 2026-05 sprint set this success criterion:

> A fresh clone of any `m-dev-tools` repo on a stock developer
> machine with Docker installed (no VistA, no `vista-meta`, no
> `rafael5` sibling checkouts) runs its own `make check` and
> produces a green result.

If your contribution breaks that bar (adds a hardcoded path to a
non-org repo, requires a VistA install, depends on a sibling
checkout that can't come from the org), call it out in your PR
description so reviewers can decide whether the trade-off is worth
it.

## Filing issues

- **Parse-tree wrong** for some routine → file at
  [`tree-sitter-m`](https://github.com/m-dev-tools/tree-sitter-m/issues).
- **Lint false positive / negative** → file at
  [`m-cli`](https://github.com/m-dev-tools/m-cli/issues), and
  include the routine plus the rule ID.
- **Standard-library / runtime question** → file at
  [`m-stdlib`](https://github.com/m-dev-tools/m-stdlib/issues).
- **Language-reference data wrong** (a command, ISV, or function
  classified incorrectly) → file at
  [`m-standard`](https://github.com/m-dev-tools/m-standard/issues).

For cross-repo or org-level discussion, file at
[`m-dev-tools/.github`](https://github.com/m-dev-tools/.github/issues).

## Pull request flow

1. Open an issue first for anything beyond a small fix — ensures the
   change matches roadmap / scope.
2. Branch off `main` (default across every repo in the org).
3. Add tests **before** implementation. Every repo follows the same
   TDD rule: write the test, confirm it fails, implement, confirm it
   passes.
4. Run the local gate (`make check`, or the repo's equivalent)
   before pushing.
5. PR description should: link the issue, explain the *why*, and
   note any new dependency / friction-bar implication.

## Code style

- **Python**: `ruff` (format + lint) + `mypy`, line length 88-100
  (per-repo). No `print()` in library code — use `logging`.
- **M (MUMPS)**: pythonic-lower formatting (lower-case canonical
  command names — `set X=1`, not `S X=1`); `m fmt` enforces it.
- **TypeScript / Node**: per-repo (mostly Biome).
- **No mocks unless unavoidable** — prefer real fixtures and fakes.

## Layout conventions

Each repo in the org follows a uniform top-level layout. The rule that
matters across all of them:

**`docs/` holds only human-readable prose** (`.md`, `.markdown`, images,
`.gitkeep`). Technical artifacts — generated data, output, metadata,
copy-paste examples, scaffolding templates — live elsewhere:

| Path | Contents | Where it applies |
|---|---|---|
| `docs/` | Prose: specs, guides, ADRs, plans, build logs | every repo |
| `dist/` | Published machine-readable contract files (Phase 0 `repo.meta.json` + the `exposes.*` payloads it references) | tier-1 repos (`m-cli`, `m-stdlib`, `m-standard`) |
| `examples/` | Worked-example artifacts (demo source, copy-paste config presets) | `m-cli`, `m-stdlib` |
| `templates/` | Project scaffolds | `m-stdlib` |
| `scripts/` | Shell helpers (seed/unseed, bench drivers) | `m-cli`, `m-stdlib` |
| `tools/` | Generator scripts (manifest, skill, doctests, validators) | tier-1 generally |
| Domain-specific top-level dirs (e.g. `integrated/`, `per-source/`, `schemas/`, `sources/`, `mappings/` in `m-standard`) | Pipeline layers, source replicas, schemas | repo-specific |

The rule is enforced per-repo by `make check-docs-prose` (CI gate).
Anything non-prose landing under `docs/` fails the build with a pointer
to the right directory above. Each tier-1 repo's `AGENTS.md` carries a
"Layout conventions" section that specializes this table for its own
top-level layout.

## Licensing

Most repos are **AGPL-3.0** (`tree-sitter-m`, `m-standard`,
`m-stdlib`, `m-cli`, `m-test-engine`); the two VS Code extensions
are **MIT**; `m-modern-corpus` carries per-subdirectory upstream
licenses. By contributing, you agree your contributions are
licensed under the same terms as the repo you're contributing to.
