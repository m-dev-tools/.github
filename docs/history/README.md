# Historical documents

---

## How the m-dev-tools ecosystem evolved

`m-tools` began as a single hub project: a `bin/` of 25 `y*` shell
scripts (`ycheck`, `ytest`, `ycover`, `ydiff`, …) that wrapped
YottaDB's command-line surface, plus a `routines/` tree of tutorial
M code, plus the strategic planning documents that drove everything
else. As the strategy materialised, each capability moved into a
dedicated repository:

1. **Strategy was codified first.** The four planning documents under
   [`docs/`](docs/) framed the problem: M had a real ISO standard and
   two production engines (IRIS, YottaDB), but no formatter, no
   linter, no test runner, no LSP, no package ecosystem — none of the
   "developer inner-loop" infrastructure mainstream languages take
   for granted. The
   [gap analysis](docs/gap-analysis-and-remediation-strategy.md)
   ranked the missing capabilities;
   [m-tool-gap-analysis.md](docs/m-tool-gap-analysis.md) §8 fixed
   the Tier 1 set; [m-tooling-tier1.md](docs/m-tooling-tier1.md)
   produced the focused execution plan; and
   [implementation.md](docs/implementation.md) defined the canonical
   `m <subcommand>` command map.

2. **The language reference came next.** Building tooling against an
   under-specified language doesn't work; every linter and formatter
   would re-invent its own keyword list and re-litigate which features
   were portable. The strategy called for a single citable reference,
   and that became
   [`m-standard`](https://github.com/m-dev-tools/m-standard) —
   the ANSI standard, YottaDB docs, IRIS docs, and VA SAC reconciled
   into one machine-readable artefact.

3. **The parser was generated mechanically from the reference.**
   With `m-standard` providing the grammar surface as JSON,
   [`tree-sitter-m`](https://github.com/m-dev-tools/tree-sitter-m)
   could be built without re-deriving the language by hand. It
   shipped clean enough on VistA (99.06%) to back every downstream
   tool.

4. **The CLI replaced the `y*` scripts.**
   [`m-cli`](https://github.com/m-dev-tools/m-cli) implemented the
   canonical `m <subcommand>` surface from
   [`docs/implementation.md`](docs/implementation.md):
   `m fmt` and `m lint` (engine-neutral, source-level),
   `m test` and `m coverage` (YottaDB-targeted, runtime-bound),
   `m watch` (the TDD inner loop), and the `m lsp` server that
   editors plug into. The Tier 1 set from
   [`docs/m-tooling-tier1.md`](docs/m-tooling-tier1.md) is fully
   shipped; Tier 2 quality gates and project-scaffolding subcommands
   layered on top.

5. **The runtime standard library landed once the toolchain
   supported it.** With `m fmt`, `m lint`, and `m test` in place,
   it became feasible to ship a versioned, conformance-tested,
   discoverable library —
   [`m-stdlib`](https://github.com/m-dev-tools/m-stdlib) — covering
   the gaps every M shop has historically filled with private
   `^XB*` / `^DI*` / `^%Z*` routines: assertions, JSON, regex,
   datetime, HTTP, crypto, and the rest. m-stdlib has architectural
   priority over m-cli: when both projects need a utility, it lands
   in m-stdlib first and m-cli imports.

6. **The test engine was extracted.** Originally `m-tools`' `Makefile`
   staged routines into the heavyweight
   [`vista-meta`](https://github.com/rafael5/vista-meta) container
   over SSH. For non-VistA M development that was overkill, so the
   minimal YottaDB container moved into
   [`m-test-engine`](https://github.com/m-dev-tools/m-test-engine) —
   `docker exec` replaces SSH staging, and consumer projects
   bind-mount their source at `/work`.

7. **Editor integration shipped last, on top of everything else.**
   [`tree-sitter-m-vscode`](https://github.com/m-dev-tools/tree-sitter-m-vscode)
   provides syntax highlighting via the WASM-compiled grammar and
   spawns `m lsp` for live tooling. Its companion
   [`m-stdlib-vscode`](https://github.com/m-dev-tools/m-stdlib-vscode)
   reads the m-stdlib manifest for hover, goto-def, and completion
   on STD\* symbols.

8. **A modern validation corpus was assembled.**
   [`m-modern-corpus`](https://github.com/m-dev-tools/m-modern-corpus)
   collects modern (post-2010, non-VistA) M source from active
   open-source projects, calibrating the `M-MOD-NN` rule track
   against contemporary idioms rather than legacy VA conventions.

---

## What's preserved here

- [`docs/gap-analysis-and-remediation-strategy.md`](docs/gap-analysis-and-remediation-strategy.md)
  — the original cross-engine gap analysis, the four-tier
  prioritisation, the technology-optimal remediation addenda, and
  the language-toolchain reference appendices.
- [`docs/m-tool-gap-analysis.md`](docs/m-tool-gap-analysis.md) —
  the §8 rank-ordered developer-impact analysis that fixed the
  Tier 1 set.
- [`docs/m-tooling-tier1.md`](docs/m-tooling-tier1.md) — the focused
  Tier 1 execution plan; still cited from the
  [m-cli README](https://github.com/m-dev-tools/m-cli).
- [`docs/implementation.md`](docs/implementation.md) — the original
  `m help` command map and as-built specs that `m-cli` realises.

These are kept verbatim so the ecosystem's design rationale stays
auditable: every choice the sibling repos make ultimately traces back
to a paragraph in one of these four documents.

---

## License

The historical documents under `docs/` are released under the same
terms as the rest of the `m-dev-tools` family — **AGPL-3.0** — to
match `m-cli`, `m-stdlib`, `m-standard`, `tree-sitter-m`, and
`m-test-engine`. The two VS Code extensions are independently MIT to
align with the broader extension ecosystem.
