# M Tools — Gap Analysis and Remediation Strategy

> **Archived snapshot.** Imported verbatim from [`m-dev-tools/m-tools`](https://github.com/m-dev-tools/m-tools) — source commit [`16fe3f7`](https://github.com/m-dev-tools/m-tools/commit/16fe3f7dc6982070809cd1d8290d01fedc5905ac) (2026-04-27), before that repo was archived. Preserved as the original phased remediation roadmap that scoped what became `m-cli` and `m-stdlib`. **Not maintained.** For the *current* shape of the org, start at [`profile/README.md`](../../profile/README.md).

**Document type:** Strategic planning
**Scope:** Developer toolchain for the M (MUMPS) language
**Audience:** Developers building productivity tools for the M ecosystem
**Sibling document:** [`implementation.md`](https://github.com/m-dev-tools/m-tools/blob/main/docs/implementation.md) — what's actually shipped *(not rehosted; resolves to the archived m-tools repo, which remains read-only on GitHub)*

---

## Scope and portability

This document analyses the developer experience for the M (MUMPS) programming language. M itself is a portable, ISO-standardised language — implementations include InterSystems IRIS, YottaDB, GT.M, and historically others. The *toolchain* this analysis recommends (linters, formatters, AST tools, package managers) operates over `.m` source code and is portable in principle to any conformant M runtime.

In practice this project uses **YottaDB as the foundation runtime** for two reasons:

1. **YottaDB is open source under AGPL-3.0**, which makes it the most portable foundation for non-commercial / community tooling — anyone can install it and run the full toolchain end-to-end without licence negotiation. A toolchain bound to a closed-source runtime would be unreproducible for most contributors and unusable in CI without per-developer licensing. Open source means the toolchain is genuinely portable in the practical sense, not just the theoretical sense.
2. **YottaDB's command-line surface is mature and well-documented.** `mupip` (database management), `gde` (global directory editor), `lke` (lock examination), `dse` (database structure editor), and the `ydb` runtime — together with the `%XCMD` mechanism for one-shot M execution — give a concrete substrate to integrate with. These vendor tools are not wrapped or renamed by this project; they are used directly, with their own `--help` as canonical documentation.

Where this matters in the analysis: tool *recommendations* (e.g., "auto-formatter using `tree-sitter-m`") are M-portable. Tool *implementations* that touch a runtime (e.g., the test runner, coverage instrumentation, the trace tail) are YottaDB-bound today and would need a runtime-adapter layer to run against IRIS or other implementations. The shell-level naming convention reflects this split: portable analysis commands use `m <subcommand>`; runtime-bound commands use `ydb <subcommand>`. See [implementation.md](implementation.md) for the canonical command map and as-built status.

---

## Table of Contents

- [1. Introduction — The Problem](#1-introduction--the-problem)
- [2. Comprehensive Gap Analysis](#2-comprehensive-gap-analysis)
- [3. Strategic Recommendations](#3-strategic-recommendations)
  - [3.1 Tier 1 — Immediate (high impact, low effort)](#31-tier-1--immediate-high-impact-low-effort)
  - [3.2 Tier 2 — Short term (high impact, medium effort)](#32-tier-2--short-term-high-impact-medium-effort)
  - [3.3 Tier 3 — Medium term (medium impact, medium/high effort)](#33-tier-3--medium-term-medium-impact-mediumhigh-effort)
  - [3.4 Tier 4 — Long term / aspirational](#34-tier-4--long-term--aspirational)
- **[Addendum A: Technology-Optimal Remediation Strategy](#addendum-a-technology-optimal-remediation-strategy)**
  - [A.1 — The Foundation Problem: MUMPS Needs a Parser](#a1--the-foundation-problem-mumps-needs-a-parser)
  - [A.2 — Technology Selection Matrix](#a2--technology-selection-matrix)
  - [A.3 — The Database Layer: ZWR Format as Universal Interface](#a3--the-database-layer-zwr-format-as-universal-interface)
  - [A.4 — The Instrumentation Layer: Observability Without a Profiler](#a4--the-instrumentation-layer-observability-without-a-profiler)
  - [A.5 — Per-Gap Remediation (Major Gaps 🔴)](#a5--per-gap-remediation-major-gaps-)
  - [A.6 — Per-Gap Remediation (Moderate Gaps 🟡)](#a6--per-gap-remediation-moderate-gaps-)
- **[Addendum B: Prioritized Sequence of Remediation (Post-Parser)](#addendum-b-prioritized-sequence-of-remediation-post-parser)**
  - [B.1 — Sequencing Principles](#b1--sequencing-principles)
  - [B.2 — Phase 1: Canonicalise the Codebase](#b2--phase-1-canonicalise-the-codebase)
  - [B.3 — Phase 2: Catch Bugs Before Runtime](#b3--phase-2-catch-bugs-before-runtime)
  - [B.4 — Phase 3: Replace Approximations with Truth](#b4--phase-3-replace-approximations-with-truth)
  - [B.5 — Phase 4: Interactive Surfaces (No Parser Dep)](#b5--phase-4-interactive-surfaces-no-parser-dep)
  - [B.6 — Phase 5: Ecosystem Layer](#b6--phase-5-ecosystem-layer)
  - [B.7 — Cross-Cutting: Umbrella Dispatcher Rename](#b7--cross-cutting-umbrella-dispatcher-rename)
  - [B.8 — Sequence Summary](#b8--sequence-summary)
- **[Appendix B: Gold Standard — Top 5 Language Toolchains](#appendix-b-gold-standard--top-5-language-toolchains)**
  - [B.1 Python](#b1-python)
  - [B.2 JavaScript / TypeScript](#b2-javascript--typescript)
  - [B.3 Go](#b3-go)
  - [B.4 Rust](#b4-rust)
  - [B.5 Java](#b5-java)
- **[Appendix C: What Ships with YottaDB (Foundation Runtime)](#appendix-c-what-ships-with-yottadb-foundation-runtime)**
  - [C.1 Runtime and Interactive Tools](#c1-runtime-and-interactive-tools)
  - [C.2 MUPIP — Database Management Utility](#c2-mupip--database-management-utility)
  - [C.3 Auxiliary Utilities](#c3-auxiliary-utilities)
  - [C.4 MUMPS Intrinsic Debugging Commands](#c4-mumps-intrinsic-debugging-commands)
  - [C.5 Percent-Sign Utility Routines](#c5-percent-sign-utility-routines)

---

## 1. Introduction — The Problem

### Background

MUMPS (Massachusetts General Hospital Utility Multi-Programming System), now standardized as M, is a programming language and integrated hierarchical database that has been in continuous production use since 1966. It powers the majority of the world's large-scale healthcare IT infrastructure — Epic Systems, MEDITECH, the U.S. Department of Veterans Affairs' VistA system, and many others collectively manage hundreds of millions of patient records in MUMPS databases. M is implemented by several runtimes: InterSystems IRIS (commercial), YottaDB (open source, the foundation used here), GT.M (the open-source ancestor of YottaDB), and historically by several other vendors.

Despite this operational scale and longevity, the developer experience around M has received comparatively little investment in tooling. The language itself predates virtually every modern software development practice: unit testing, continuous integration, static analysis, code coverage, package management, and automated formatting all emerged decades after M was in widespread use. As a result, the ecosystem of developer productivity tools that mainstream language communities take for granted simply does not exist in the M world.

### The Core Problem

A developer arriving at an M codebase from Python, Go, JavaScript, Rust, or Java faces a jarring regression in developer experience. The gap is not merely cosmetic — it affects every stage of the development lifecycle:

**Edit:** No formatter exists. Code style is enforced only by convention and discipline. There is no equivalent of `black`, `gofmt`, or `prettier` to keep a codebase consistent without manual effort.

**Lint:** The only available static check is syntax validation (`zcompile`). There is no analysis of logic errors, unused variables, unreachable code, missing QUIT statements, undefined labels, or style violations. Python's `ruff`/`pylint`, Go's `golangci-lint`, and Rust's `clippy` all catch categories of bugs before runtime; M has nothing comparable.

**Test:** A test framework (`TESTRUN.m`) exists in this project, but the tooling around it is primitive. There is no way to run a single test case without running the entire suite, no coverage measurement, no test history, and no parallel execution. The `make watch` command reruns *all* tests on every file save — a workflow that degrades as the test suite grows.

**Debug:** M has built-in debugging commands (`ZBREAK`, `ZSTEP`, `ZSHOW`) but they are interactive and require entering the runtime manually. There is no scriptable debugger, no conditional breakpoint wrapper, and no integration with any IDE debugger protocol.

**Observe:** The integrated database is both a strength and an observability challenge. Globals are persistent and shared across processes, which makes it easy to accidentally carry test state between runs. There is no tool to snapshot the database state before a test, compare it after, or reliably reset it to a known fixture. The trace log (`^trace`) exists but cannot be tailed live.

**Integrate:** There are no pre-commit hooks, no CI pipeline script, no coverage gate, and no automated quality check that runs before code is committed or deployed.

### Why This Matters

The consequence of this tooling gap is not merely inconvenience. It means that:

1. **Bugs that would be caught automatically in other ecosystems reach manual testing** — or production. A Go developer's `go vet` or a Python developer's `mypy` catches entire categories of errors before a single test runs. In M, these categories are only caught when the faulty code path is manually exercised.

2. **The feedback loop is slower and more manual.** A Rust developer running `cargo watch -x test` gets sub-second feedback on every save. An M developer runs `make test`, waits for all 11 suites, and manually reads output. As the codebase grows, this degrades.

3. **Onboarding new developers is harder.** Modern languages have toolchains that enforce consistency and provide guardrails. M has neither, so new developers must learn conventions that are undocumented and unenforced.

4. **The barrier to contribution is higher.** Open-source projects with good tooling (formatters, lint gates, coverage requirements) attract more contributors because the bar for a "correct" contribution is clear and automatically checkable.

### The Strategic Opportunity

YottaDB's runtime is mature, performant, and POSIX-compliant. The runtime provides powerful hooks — `%XCMD` for one-shot execution, `$ZHOROLOG` for microsecond timing, `ZSHOW` for full process introspection, `mupip extract` for database export, and a straightforward routine compilation model. These are the building blocks of a complete developer toolchain. What is missing is the shell toolchain layer that assembles these primitives into a coherent, ergonomic developer experience comparable to what Python, Go, and Rust developers have. Because YottaDB is open source, every layer of this toolchain is reproducible without licence negotiation — a property no closed-source M runtime can offer.

This document surveys what currently exists, maps the complete gap against the toolchains of the five most popular programming languages (see [Appendix B](#appendix-b-gold-standard--top-5-language-toolchains) for the per-language reference tables), and proposes a prioritized roadmap of shell tools that can be built now using existing YottaDB capabilities.

---

## 2. Comprehensive Gap Analysis

This chapter maps every significant developer toolchain category against four reference points: what the gold standard provides (synthesized from the toolchains of Python, JavaScript/TypeScript, Go, Rust, and Java — see [Appendix B](#appendix-b-gold-standard--top-5-language-toolchains) for the per-language tables), what YottaDB ships with natively (see [Appendix C](#appendix-c-what-ships-with-yottadb-foundation-runtime)), what this project has built (see [implementation.md](implementation.md) for the live status), and the remaining gap with severity.

**Severity key:** 🔴 Major gap (daily pain) · 🟡 Moderate gap (occasional friction) · 🟢 Minor gap or N/A

**Status legend:** ✅ shipped (Tier 1–3) · 🟢 unblocked (parser foundation now exists in [`tree-sitter-m`](https://github.com/rafael5/tree-sitter-m); Tier 4 tool not yet built) · ⏸ deferred (no parser dep; awaiting demand) · 🟢/🟡/🔴 = original severity

| Category | Gold Standard | YDB Native | This Project | Original Sev | Status |
|----------|--------------|------------|--------------|--------------|--------|
| **Syntax check** | Per-file, fast, exit-code | `zcompile` via `%XCMD` | `ycheck` | 🟢 | ✅ shipped (with known exit-code bug — see TODO.md) |
| **Interactive REPL** | History, completion, multiline | `ydb` direct mode (bare) | `yeval` (single expression) | 🟡 | ⏸ Tier 4 (`yrepl` — needs prompt_toolkit) |
| **Lint — style** | Configurable style rules | Nothing | Nothing | 🔴 | 🟢 unblocked (tree-sitter-m AST visitor) |
| **Lint — logic** | Unused vars, unreachable code, missing returns | Nothing | Nothing | 🔴 | 🟢 unblocked (tree-sitter-m + CFG analysis) |
| **Lint — deep** | Data flow, type errors, null safety | Nothing | Nothing | 🔴 | 🟢 unblocked (tree-sitter-m + whole-program call graph) |
| **Auto-formatter** | Zero-config, deterministic | Nothing | Nothing | 🔴 | 🟢 unblocked (tree-sitter-m CST pretty-printer) |
| **Type checking** | Full static type analysis | N/A (untyped language) | N/A | 🟢 | N/A by language design |
| **Run all tests** | `make test` / `cargo test` | Nothing | `make test` | 🟢 | ✅ pre-existing |
| **Run one suite** | Select by name/path | Nothing | `ytest <suite>` | 🔴 | ✅ Tier 1 |
| **Run one test** | Select individual test case | Nothing | `ytest <suite> <label>` | 🔴 | ✅ Tier 1 |
| **Test watcher** | Smart — reruns only affected | Nothing | `ytest-watch-smart` | 🟡 | ✅ Tier 2 |
| **Test output** | Structured (TAP, JUnit XML) | Plain text | `ytap` (TAP-13) | 🟡 | ✅ Tier 3 |
| **Test history** | Pass/fail trends over time | Nothing | Nothing | 🟡 | ⏸ Tier 4 / future |
| **Coverage — line** | Which lines executed | Nothing | Nothing | 🔴 | 🟢 unblocked (tree-sitter-m identifies executable lines for source instrumentation) |
| **Coverage — branch** | Which branches taken | Nothing | Nothing | 🔴 | 🟢 unblocked (tree-sitter-m branch-aware injection) |
| **Coverage report** | HTML / lcov / badge | Nothing | `ycover` (label-entry, JSON or table) | 🔴 | ✅ Tier 3 (approximate) |
| **Benchmarking** | Repeatable, statistical | Nothing | `yperf` ($ZHOROLOG, μs precision) | 🟡 | ✅ Tier 3 |
| **Profiling** | Call graph, flame graph | `$ZHOROLOG` (manual) | Nothing | 🟡 | 🟢 unblocked (tree-sitter-m + source instrumentation share the coverage pipeline) |
| **Debugger — interactive** | Breakpoints, step, inspect | `ZBREAK`/`ZSTEP`/`ZSHOW` (manual) | Nothing | 🟡 | ⏸ Tier 4 (`ydebug`) |
| **Debugger — scriptable** | Conditional BPs, watchpoints | Nothing | Nothing | 🔴 | ⏸ Tier 4 |
| **Symbol introspection** | List functions/exports | `%RD` (compiled routines only) | `ywhat` | 🟡 | ✅ Tier 1 |
| **Documentation gen** | Extract comments → HTML/MD | Nothing | `ydoc` (Markdown) | 🟡 | ✅ Tier 3 |
| **Dependency mgmt** | Lockfile, versioned packages | Nothing | Nothing | 🔴 | ⏸ Tier 4 (manifest format to be designed in `m-standard`) |
| **DB export** | Dump state to portable format | `mupip extract`, `%GO` | `yexport` (json/zwr/raw) | 🟡 | ✅ Tier 2 |
| **DB import / fixture load** | Load known state for tests | `mupip load`, `%GI` | `yseed` (auto-detect format) | 🔴 | ✅ Tier 2 |
| **DB diff** | What changed between runs | Nothing | `ydiff` (+/-/~ markers) | 🔴 | ✅ Tier 2 |
| **DB state snapshot** | Before/after comparison | `mupip extract` (manual) | `ydiff before/after`, `ysnapshot` | 🔴 | ✅ Tier 2/3 |
| **DB global sizing** | Node counts, storage usage | `mupip size` | `yglobsize` (nodes + blocks) | 🟡 | ✅ Tier 2 |
| **DB reset / clean** | Wipe test globals reliably | `kill` in test teardown | `yclean` (named groups) | 🔴 | ✅ Tier 1 |
| **DB integrity check** | Verify database not corrupt | `mupip integ` | Nothing wired | 🟡 | ⏸ future |
| **Live log tail** | Stream output in real time | Nothing | `ylog` (poll + filter) | 🟡 | ✅ Tier 1 |
| **Pre-commit hooks** | Block bad commits | Nothing | `yhook install/run/uninstall` | 🟡 | ✅ Tier 1 |
| **CI pipeline** | One-command full check | Nothing | `yci`, `yci --report` | 🟡 | ✅ Tier 1 |
| **Environment check** | Verify full toolchain | Nothing | `make check-env` (minimal, but `yci` wraps it) | 🟡 | ✅ Tier 1 (via yci) |
| **Scaffolding** | New module/test template | Nothing | `ynew` (module + test + Makefile injection) | 🟡 | ✅ Tier 3 |
| **Security scan** | Dependency CVE check | Nothing | Nothing | 🟢 | N/A (no dependencies) |
| **Complexity metrics** | Cyclomatic complexity | Nothing | Nothing | 🟡 | 🟢 unblocked (tree-sitter-m AST visitor) |
| **Dead code detection** | Unused labels/variables | Nothing | Nothing | 🟡 | 🟢 unblocked (tree-sitter-m + reachability over call graph) |
| **Snapshot testing** | Compare output to baseline | Nothing | `ysnapshot create/check/update` | 🟡 | ✅ Tier 3 |
| **Parallel tests** | Run suites concurrently | Nothing | Nothing | 🟡 | ⏸ Tier 4 |
| **Test fixtures** | Composable, scoped test state | Nothing | `yseed` + `yclean` cover the foundation | 🔴 | ✅ Tier 1+2 |
| **Crash / lockup cleanup** | Recover from bad process exit | `mupip rundown`, `lke` | `yrundown` | 🟡 | ✅ Tier 2 |

**Original severity counts (still meaningful as a baseline):** 🔴 Major: 16 · 🟡 Moderate: 20 · 🟢 Minor/N/A: 4
**Closed by Tier 1–3:** 11 of 16 majors · 12 of 20 moderates · all 4 minors-or-N/A handled.
**Unblocked by `tree-sitter-m` v1.0** (parser foundation now ships — see [implementation.md → Parser-foundation status](implementation.md#41-parser-foundation-status-the-unlock-for-tier-4)): 4 of the 5 remaining majors (lint-style, lint-logic, lint-deep, auto-formatter) plus 4 moderates (profiling, complexity-metrics, dead-code, line/branch-coverage). Tools themselves are not yet built — they are downstream consumers of the parser.
**Still genuinely open (no parser dep, awaiting demand):** scriptable-debugger (DAP server), interactive-REPL (`yrepl` Phase 1 = `rlwrap ydb`), test-history (SQLite trend store), interactive-debugger, dependency-mgmt (manifest design in `m-standard`), DB-integrity (wrap `mupip integ`), parallel-tests (test-isolation refactor).

---

## 3. Strategic Recommendations

### Prioritization Criteria

Tools are ranked by the product of:
- **Daily friction:** How often does this gap cause pain in a normal edit-test-commit cycle?
- **Build effort:** How hard is this to build with existing YDB primitives?
- **Ecosystem unlock:** Does this tool enable other tools (e.g., fixture management enables reliable testing)?

---

### 3.1 Tier 1 — Immediate (high impact, low effort) — ✅ DONE 2026-04-25

All six shipped in the same session as the analysis itself. Each tool closes the original "Why Now" friction via shell-only implementation; no MUMPS-side changes were required for Tier 1.

| Tool | Closes Gap | Status |
|------|-----------|--------|
| **`ytest`** | Single suite / single test execution | ✅ |
| **`yclean`** | DB reset / test isolation | ✅ — 7 named groups (`tasks`, `trace`, `txn`, `idx`, `fixtures`, `demo`, `safe`) |
| **`ylog`** | Live trace tail | ✅ — polls `$$count^trace()` at 0.5s; supports `--n`, `--clear`, `--filter` |
| **`ywhat`** | Symbol introspection | ✅ — pure awk over column-1 lines |
| **`yhook`** | Pre-commit hooks | ✅ — refuses to overwrite a hand-written hook (marker line check) |
| **`yci`** | CI pipeline | ✅ — `--fast` and `--report` modes |

---

### 3.2 Tier 2 — Short term (high impact, medium effort) — ✅ DONE 2026-04-25

| Tool | Closes Gap | Implementation Note |
|------|-----------|---------------------|
| **`ydiff`** | DB diff / state change tracking | ✅ — chose flat `^ref=value` dumps + `diff -u` + awk to pair `-`/`+` lines into `~` change lines (simpler than parsing ZWR) |
| **`yexport`** | DB export | ✅ — three formats: `json` (via `exportJson^yutil`), `zwr` (`mupip extract`), `raw` (flat dump) |
| **`yseed`** | DB fixture loading | ✅ — auto-detects format; JSON path uses python3 to emit `set` commands and pipes them to `$YDB -direct` |
| **`ytest-watch-smart`** | Targeted test watcher | ✅ — pure-bash `stat -c %Y` polling (no `entr`/`inotifywait` dep); `<NAME>TST` convention mapping |
| **`yglobsize`** | Global size reporting | ✅ — exact node count via `count^yutil`; storage blocks via `mupip size` (with stderr→stdout redirect) |
| **`yrundown`** | Crash cleanup | ✅ — refuses to run if other YDB processes are alive; `--dry`, `--locks`, `--db` flags |

**New helper module:** [`routines/yutil.m`](../routines/yutil.m) — small MUMPS-side helpers (`count`, `dump`, `exportJson`, `bench`, `listGlobals`) since argless `FOR` loops fail through `%XCMD`'s wrapper. Shell tools call labels directly via `$YDB -run <label>^yutil <arg>`.

---

### 3.3 Tier 3 — Medium term (medium impact, medium/high effort) — ✅ DONE 2026-04-25

| Tool | Closes Gap | Implementation Note |
|------|-----------|---------------------|
| **`ydoc`** | Documentation generation | ✅ — pure awk; emits H2 per routine, H3 per label; skips `tXxx` test labels and `;@TEST` decorations |
| **`yperf`** | Benchmarking | ✅ — `bench^yutil` (3 warmups + N measurements with `$ZHOROLOG`); awk computes mean/median/p95/min/max/stddev/outliers |
| **`ynew`** | Scaffolding | ✅ — generates module + test + Makefile injection (python3 helper for the Makefile edit) |
| **`ycover`** | Coverage approximation | ✅ — ZBREAK at every label, run all suites in one YDB process, diff `^ycov` against discovered label set; reports per-routine % |
| **`ytap`** | TAP output | ✅ — awk transformer over `ytest` output; `1..N` plan emitted at end |
| **`ysnapshot`** | Snapshot testing | ✅ — `create`/`check`/`update`/`list`/`show`/`rm`; baselines in `fixtures/snapshots/<name>.txt` |

**Real test gaps surfaced by `ycover`** (current state, 69.1% coverage):
- `server.m` 0% (9 labels) — no test suite exists
- `taskscli.m` 0% (6 labels) — CLI exercised only via shell, not unit tests
- `trace.m` 0% (6 labels) — used as a side effect, never asserted on
- `ystate.m` 0% (3 labels) — has the known parse bug from TODO.md
- `yutil.m` 0% (5 labels) — new helper, no dedicated suite

---

### 3.4 Tier 4 — Long term / aspirational — 🟢 PARSER FOUNDATION SHIPPED 2026-04-26

The remaining tools all share one root prerequisite: **a real MUMPS parser**. Hand-rolled regex/awk approaches hit ceiling fast (postconditionals, dot blocks, naked references, indirection). The original strategic plan called for splitting the parser work into separate repos so the parser could mature on its own lifecycle — that work is now done.

| Project | Purpose | Status |
|---------|---------|--------|
| **[`m-standard`](https://github.com/rafael5/m-standard)** | Authoritative reference for the MUMPS language: integrated, citable, machine-readable spec layer reconciling AnnoStd (ISO 11756), YottaDB docs, IRIS docs, and VA SAC/XINDEX into a unified grammar-surface JSON. Also home to the dependency manifest format and any cross-cutting standards documents. | ✅ **v1.0 tagged** for AnnoStd + YottaDB scope; end-to-end pipeline green; all 9 validation gates passing in CI. v0.2 in progress for IRIS + SAC additions. |
| **[`tree-sitter-m`](https://github.com/rafael5/tree-sitter-m)** | The implementation layer. Production tree-sitter grammar generated from `m-standard`'s grammar-surface (949 keyword forms, schema-pinned). Bindings scaffolded for Node / Rust / Python / Go. **Note:** the original plan called for a "Lark phase 1, Tree-sitter phase 2" split under a single `m-grammar` repo. In practice, `tree-sitter-m` was built directly against `m-standard`'s grammar-surface and the Lark phase was skipped — the schema-pinned grammar-surface JSON gave enough structure that the iteration speed argument for Lark went away. | ✅ **v1.0 grammar work complete.** 99.06% clean on the full 39,330-routine VistA corpus; 100% of clinical packages. 10k-line synthesised routine parses in 78.6 ms. 110 corpus tests + 19 lib tests + 347/347 keyword-coverage triples all green. Remaining: publish bindings to npm/crates.io/PyPI/Go, AD-03 stamping integration, perf budget in CI. |
| **[`tree-sitter-m-vscode`](https://github.com/rafael5/tree-sitter-m-vscode)** | VS Code extension exercising the grammar end-to-end. Two-layer highlighting (TextMate cold-load + tree-sitter-m WASM semantic-tokens) demonstrates the editor-integration success criterion. | ✅ **v0.1 working.** `vsce package` produces a 1.27 MB `.vsix` bundling the parser WASM + web-tree-sitter runtime. Marketplace `vsce publish` gated only on a Personal Access Token from dev.azure.com. |

With the parser foundation in place, the Tier 4 tools become straightforward downstream consumers. The remaining work is on the *tools themselves*, not the prerequisite:

| Tool | Depends on | Status / Notes |
|------|-----------|----------------|
| **`yfmt`** (→ `m fmt`) | tree-sitter-m AST + pretty-printer | 🟢 Ready to build. Use lossless byte-range mode to preserve comments. |
| **`ylint-deep`** (→ `m lint --deep`) | tree-sitter-m AST + call graph | 🟢 Ready to build. Visitor pattern with rule predicates; configurable warning-set. |
| **`ylint-style`** / **`ylint-logic`** (→ `m lint --style` / `--logic`) | tree-sitter-m AST visitor | 🟢 Ready to build. Style + control-flow rules over the AST. |
| **`ycov-line` / `ycov-branch`** (→ `ydb cover --line` / `--branch`) | tree-sitter-m for instrumentation-point identification + `^ycov` global | 🟢 Ready to build. Replaces today's label-entry-only `ycover`. |
| **`ydebug`** (→ `ydb debug`) | YDB `ZBREAK`/`ZSTEP` + DAP server (no parser dep) | ⏸ No parser dep; deferred on demand. Wraps existing YDB primitives in a Debug Adapter Protocol server. |
| **`yrepl`** (→ `ydb repl`) | `prompt_toolkit` + tree-sitter-m (for completion) | ⏸ Phase 1 = `rlwrap ydb` (no parser dep, ships now); Phase 2 uses tree-sitter-m for tab-completion. |
| **`yparallel`** (→ `ydb test --parallel`) | Global-isolation conventions in test suites | ⏸ No parser dep; blocked on test-suite isolation discipline. |
| **`ydb-pkg`** (→ `m pkg`) | TOML manifest spec in `m-standard` + installer script | ⏸ Manifest format design pending in `m-standard`. |

**Decision (revised 2026-04-26):** the parser foundation is now shipped, so the strategic question shifts from *should we build a parser?* to *which downstream tools are worth building, in what order?* The natural sequencing follows daily friction: `yfmt` (zero current solution; canonicalises the codebase), then `ylint-style` + `ylint-logic` (catches bug categories before runtime), then `ycov-line` (replaces today's approximate `ycover`). `ylint-deep`, `ydebug`, `yrepl` Phase 2, and `ydb-pkg` are larger investments and can wait.

For the technology selection, parser hard problems, and the rationale for splitting into `m-standard` (spec) vs `tree-sitter-m` (impl), see [Addendum A](#addendum-a-technology-optimal-remediation-strategy).

---

## Addendum A: Technology-Optimal Remediation Strategy

This addendum provides a technology-first remediation plan for every Major (🔴) and Moderate (🟡) gap identified in the gap analysis. It is structured as an engineering specification: each section names specific libraries, parser technologies, and integration patterns. The goal is not a wish list but a buildable roadmap grounded in how comparable ecosystems have solved identical problems.

---

### A.1 — The Foundation Problem: MUMPS Needs a Parser

Almost every high-value gap in this analysis — linting, formatting, dead code detection, documentation generation, symbol introspection, complexity metrics, snapshot testing — shares a single prerequisite: the ability to transform MUMPS source text into a structured representation that a program can reason about. Regex-based approaches have been tried in MUMPS tooling for decades and consistently fail at the same boundaries: postconditional expressions embedded in commands, the distinction between a DO block's dot-notation and an argument list, naked references, and the interaction between `IF`/`ELSE` and the `$TEST` special variable. A proper parser is not a luxury; it is the foundation.

**The MUMPS Grammar's Hard Problems**

Any grammar for MUMPS must handle the following without ambiguity:

- **Column-1 labels.** A MUMPS source file is not free-form. A label must begin in column 1; everything indented is a command. This is a lexer-level concern — the tokenizer must be line-position-aware.
- **Postconditionals.** `DO:condition label` and `SET:condition var=val` attach conditions directly to commands and arguments, not as separate control structures. The grammar must represent these as optional decorated nodes on every command.
- **FOR variants.** `FOR i=1:1:10`, `FOR i=1,3,5`, and `FOR` (infinite loop with no argument) are three distinct syntactic forms with the same keyword.
- **Dot-block indentation.** MUMPS has no braces. `DO` blocks are delimited by leading dots: one dot for one level of nesting, two dots for two levels. This is whitespace-significant at the token level, not the grammar level.
- **String literal escaping.** The only escape sequence in MUMPS string literals is `""` (doubled quote) to represent a literal quote. Parsers that assume backslash escaping will silently misparse.
- **Extended indirection.** `@var` evaluates `var` as a name, and `@var@(subscript)` evaluates it as an array reference. The `@` operator is legal in argument positions across nearly every command.
- **DO/ELSE/IF interaction.** MUMPS `ELSE` does not attach to an `IF` syntactically; it tests `$TEST`, which is a global side effect modified by `IF`, `DO`, and certain other commands. A formatter that reformats `IF`/`ELSE` pairs without understanding this will silently break code.
- **Naked references.** `^(subscript)` reuses the last-used global name. This makes static data-flow analysis context-sensitive in a way that most languages do not have.

**Parser Technology Survey**

| Technology | Strengths | Weaknesses | Verdict |
|---|---|---|---|
| **ANTLR4** | Mature, generates parsers in Python/Java/Go/Rust/C#, large community, good error recovery, IDE grammar tooling | Java toolchain dependency, generated code is verbose, LL(*) has trouble with left-recursive grammars | Strong candidate |
| **Tree-sitter** | Incremental parsing, excellent IDE integration (Neovim/Helix/Emacs native), generates C with bindings to any language, handles error recovery gracefully | Grammar language is Rust-influenced DSL with a learning curve, less documentation than ANTLR | Best long-term choice |
| **Lark (Python PEG/Earley)** | Pure Python, EBNF grammar files, no code generation step, `lark.Token` trees are Pythonic, Earley handles ambiguous grammars | Slower than compiled parsers, Earley mode is O(n³) worst case, not suitable for IDE incremental use | Best for rapid prototyping |
| **pest.rs (Rust PEG)** | Extremely fast, safe memory model, excellent for CLI tools | Rust-only bindings, grammar in `.pest` DSL is less standard, high barrier for contributors | Good if Rust is already in stack |
| **flex/bison (lex/yacc)** | Decades of precedent, C output, small runtime | LALR(1) grammars are difficult to write and debug, C output requires C toolchain for every consumer language | Poor ergonomics for modern tooling |
| **Hand-written recursive descent** | Full control, can handle context-sensitive constructs like column-1 labels naturally | High maintenance cost, difficult for contributors, error messages require explicit effort | Acceptable only if grammar is small |

**Recommendation: Tree-sitter (Lark phase skipped in practice)**

The original recommendation was a two-phase path: Lark EBNF for the bootstrap, Tree-sitter for the long-term incremental/IDE-grade grammar. In practice the Lark phase was skipped. The grammar source-of-truth was extracted into `m-standard`'s schema-pinned `grammar-surface.json` (949 forms across the seven concept families), which gave enough structure that iterating directly in Tree-sitter's grammar DSL was viable from the start. `tools/build-grammar.js` in `tree-sitter-m` reads the grammar-surface and emits keyword tables, so grammar changes are driven by the spec-side data, not by hand-editing parser internals.

Tree-sitter's incremental parsing model is the prerequisite for IDE integration (the most valuable long-term unlock), and its C-with-bindings architecture means a single grammar can serve Python tooling, Neovim plugins, and GitHub's Linguist. [`tree-sitter-m`](https://github.com/rafael5/tree-sitter-m) is the published grammar; bindings for Node / Rust / Python / Go are scaffolded and locally green; publishing to package registries is the remaining release work. The VS Code demonstration ([`tree-sitter-m-vscode`](https://github.com/rafael5/tree-sitter-m-vscode)) exercises the WASM build path end-to-end.

**The single investment that unlocks everything.** With a working parse tree:
- A formatter is a pretty-printer over the AST
- A linter is a visitor over the AST with rule predicates
- Documentation generation reads doc comments adjacent to label nodes
- Dead code detection becomes a reachability problem on the call graph extracted from the AST
- Symbol introspection is a label-index over all parsed files
- IDE support (via Language Server Protocol) becomes a tree query problem

No other single investment has this leverage ratio.

**Project split (decided 2026-04-25, executed 2026-04-26):** This work lives outside `m-tools`. Three repos now exist:
- **[`m-standard`](https://github.com/rafael5/m-standard)** — the spec layer. Reconciled grammar-surface JSON + per-concept TSVs derived from AnnoStd (ISO 11756), YottaDB docs, IRIS docs, and VA SAC/XINDEX. Schema-pinned (`schema_version="1"`). v1.0 tagged for the AnnoStd + YottaDB scope; v0.2 in progress for IRIS + SAC additions. Also home to the dependency-manifest format for `ydb-pkg` (TBD).
- **[`tree-sitter-m`](https://github.com/rafael5/tree-sitter-m)** — the implementation layer. Production tree-sitter grammar generated from `m-standard`'s grammar-surface; 99.06% clean on the full 39,330-routine VistA corpus; Node / Rust / Python / Go bindings scaffolded. The original plan called for a `m-grammar` repo containing both Lark (phase 1) and Tree-sitter (phase 2); in practice the schema-pinned grammar-surface let us go straight to tree-sitter, so `m-grammar` collapsed into `tree-sitter-m` as a single repo.
- **[`tree-sitter-m-vscode`](https://github.com/rafael5/tree-sitter-m-vscode)** — sibling editor extension. Two-layer highlighting: TextMate grammar for cold-load + `DocumentSemanticTokensProvider` powered by `tree-sitter-m` compiled to WASM via `tree-sitter build --wasm --docker`. Demonstrates the editor-integration success criterion.

The Tier 4 tools (`yfmt`, `ylint-deep`, `ydoc-html`, `ycov-line`, `ydeadcode`, etc.) become downstream consumers of `tree-sitter-m`'s bindings. `m-tools` remains a pure shell-tools + MUMPS-library workspace; the parser project does not get folded back in.

---

### A.2 — Technology Selection Matrix

> **Updated 2026-04-26.** Where the original matrix said *Python + Lark/Tree-sitter*, the realised choice is *Python + `tree-sitter-m` Python binding*. The Lark phase from the original two-phase plan was skipped — see [A.1](#a1--the-foundation-problem-mumps-needs-a-parser).

| Gap | Severity | Recommended Technology |
|---|---|---|
| Lint — style | 🔴 | Python + tree-sitter-m AST visitor |
| Lint — logic | 🔴 | Python + tree-sitter-m + cfg-style analysis |
| Lint — deep (data flow) | 🔴 | Python + networkx call graph over tree-sitter-m AST |
| Auto-formatter | 🔴 | Python + tree-sitter-m CST printer (lossless mode) |
| Run one suite | 🔴 | Bash + pytest-style test discovery in yeval |
| Run one test | 🔴 | Bash + yeval argument parsing |
| Coverage — line | 🔴 | Python source instrumentation (tree-sitter-m identifies executable lines) + `^ycov` global |
| Coverage — branch | 🔴 | Python source instrumentation (tree-sitter-m branch-aware injection) |
| Coverage report | 🔴 | Python + rich / LCOV-format output |
| Debugger — scriptable | 🔴 | YDB ZBREAK hooks + expect/pexpect driver |
| Dependency management | 🔴 | Python + TOML manifest + ydb-pkg installer script |
| DB import / fixture load | 🔴 | Python ZWR processor + mupip load wrapper |
| DB diff | 🔴 | Python ZWR parser + unified diff |
| DB state snapshot | 🔴 | Python ZWR export wrapper |
| DB reset / clean | 🔴 | Python ZWR fixture restore |
| Test fixtures | 🔴 | Python ZWR fixture library + pytest-style fixture injection |
| Interactive REPL | 🟡 | Python + prompt_toolkit wrapping mumps process |
| Test watcher | 🟡 | Python + watchfiles + targeted yeval re-run |
| Test output | 🟡 | Python TAP/JUnit XML formatter over yeval output |
| Test history | 🟡 | Python SQLite store + trend reporter |
| Benchmarking | 🟡 | Python source instrumentation + time.perf_counter_ns wrapper |
| Profiling | 🟡 | Python source instrumentation + call-count aggregator |
| Symbol introspection | 🟡 | Python + tree-sitter-m label index |
| Documentation generation | 🟡 | Python + tree-sitter-m AST + Jinja2 HTML/Markdown output |
| DB export | 🟡 | Python ZWR wrapper + mupip extract |
| DB global sizing | 🟡 | Python ZWR parser + size aggregator |
| Live log tail | 🟡 | Python + rich.live + tail -F wrapper |
| Pre-commit hooks | 🟡 | pre-commit framework + ycheck as hook |
| CI pipeline | 🟡 | GitHub Actions / Gitea Actions YAML |
| Environment check | 🟡 | Python platform inspector script |
| Scaffolding | 🟡 | Python + Jinja2 template engine |
| Complexity metrics | 🟡 | Python + tree-sitter-m AST cyclomatic counter |
| Dead code detection | 🟡 | Python + networkx reachability over call graph |
| Snapshot testing | 🟡 | Python ZWR snapshot + diff assertion |
| Parallel tests | 🟡 | Python + concurrent.futures + isolated DB regions |
| Crash / lockup cleanup | 🟡 | Python + psutil + mupip rundown wrapper |

---

### A.3 — The Database Layer: ZWR Format as Universal Interface

Before addressing individual database-layer gaps, it is worth recognizing that YottaDB has already solved the hardest part of database tooling: it provides a textual export format that is both complete and trivially parseable. That format is ZWR (Z-WRite format), produced by `mupip extract` and consumed by `mupip load`.

**ZWR Format Description**

A ZWR file is a sequence of newline-terminated records. Each record is one of:

```
^global(sub1,sub2)="value"
^global(sub1,sub2,sub3)=$$VALUE$$hexencoded$$
%local="value"
```

Header lines begin with `;` and are comments. The format is:
- One node per line, always
- Global names begin with `^`, local names with `%` or alphanumeric
- Subscripts are comma-separated inside parentheses, string subscripts are double-quoted
- Values are either quoted strings (with `""` escaping) or `$$VALUE$$` hex-encoded binary blocks
- Subscript ordering matches M canonical ordering (numeric-before-string, lexicographic within strings)

This is, structurally, a sorted key-value dump with explicit hierarchy visible in the subscripts. Every line is self-contained.

**Why This Is a Gift for Tooling**

Most databases require either a binary dump format (requiring vendor tools to inspect) or a complex multi-table SQL dump (requiring schema knowledge to interpret). ZWR is neither. A Python script can process a multi-gigabyte ZWR file with a single-pass line iterator — no binary parsing, no schema introspection, no vendor library. Each line can be parsed with a small state machine that splits on the first `=` not inside quotes, then parses the subscript list.

This single property enables a Python ZWR processing library that becomes the foundation for all database-layer tooling:

- **DB diff**: Extract two snapshots, sort both, feed to `difflib.unified_diff`
- **DB export**: Wrap `mupip extract`, optionally filter by global prefix
- **DB import / fixture load**: Validate ZWR then call `mupip load`
- **DB state snapshot**: Timestamped `mupip extract` to a versioned directory
- **DB reset / clean**: `mupip load` from a known-good ZWR fixture
- **Test fixtures**: Curated ZWR files, one per test scenario, loaded before each test
- **Snapshot testing**: Capture ZWR after a test run, compare with committed baseline
- **Global sizing**: Parse ZWR, accumulate byte counts per top-level global name

**Recommended Python ZWR Library**

The library should be a single module, `yzwr.py`, with the following API surface:

- `parse_line(line: str) -> ZWRNode` — parses one ZWR record into a typed object
- `load_file(path: Path) -> Iterator[ZWRNode]` — streaming parser, handles arbitrarily large files
- `dump_nodes(nodes: Iterable[ZWRNode], path: Path)` — writes ZWR file
- `diff(a: Path, b: Path) -> str` — unified diff of two ZWR files
- `filter_prefix(nodes: Iterable[ZWRNode], prefix: str) -> Iterator[ZWRNode]` — subset by global name

The `ZWRNode` dataclass holds: `name: str`, `subscripts: list[str | int | float]`, `value: str`, `is_global: bool`, `raw: str`.

This library is ~200 lines of Python and unlocks six major gaps and three moderate gaps simultaneously.

---

### A.4 — The Instrumentation Layer: Observability Without a Profiler

Several gaps — coverage (line and branch), profiling, and benchmarking — require the ability to observe what code ran and how often. YottaDB provides no built-in profiler and no coverage instrumentation. However, MUMPS is a text-based language that can be pre-processed before execution, which makes source-level instrumentation practical and portable.

**Source Instrumentation vs Runtime Instrumentation**

Runtime instrumentation in YottaDB means inserting `ZBREAK` commands, which attach actions to specific labels or offsets. `ZBREAK label+offset^routine:"action"` runs `action` (an M expression) when execution reaches that point. This is powerful for interactive debugging but has serious limitations for automated tooling:

- ZBREAK actions are set programmatically in a running YDB session; there is no way to inject them from outside
- ZBREAK does not survive process restarts
- ZBREAK on every line of every routine has unmeasured overhead and adds fragility
- ZBREAK cannot easily instrument branch-level decisions

Source instrumentation is the alternative: a Python preprocessor reads each `.m` file, injects counter-increment statements into the source, writes modified `.m` files to a temporary directory, and runs the test suite against the modified source. After the suite completes, the counters (stored in a YDB global) are read back and converted into a coverage or profile report.

**The Instrumentation Pattern**

The preprocessor identifies instrumentation points by walking the parsed AST (using `tree-sitter-m` from A.1) or, as a simpler bootstrap, by line-level heuristics: every line that begins with a label, and every continuation line after a command that branches (`IF`, `FOR`, `DO`). At each point it injects:

```mumps
 $INCREMENT(^ycov(routineName,labelName,lineOffset))
```

`^ycov` is the instrumentation global. After the test run, reading `^ycov` with `$ORDER` loops gives the full execution frequency table. A Python script reads this table via `ydb_get` or by `mupip extract`-ing `^ycov` and parsing the ZWR output.

**Why Source Instrumentation is Practical**

- The modified `.m` source is valid MUMPS and runs in any standard YDB environment without configuration changes
- The instrumentation global survives across process boundaries, accumulating across all test processes in a parallel run
- The overhead is one integer increment per instrumented line — negligible for correctness testing, acceptable for coverage, and well-characterized for profiling
- Resetting instrumentation is a single `KILL ^ycov` before the test run
- The same mechanism serves three different consumers: coverage reporter, profiler, and benchmarking harness, differing only in which metrics they extract from `^ycov`

**Coverage vs Profiling Distinction**

Coverage asks: which lines were executed at all (binary)? Profiling asks: how many times was each line executed and in what proportion (quantitative)? The `^ycov` counter serves both: coverage is `$DATA(^ycov(r,l,o)) > 0`, profiling is the raw counter value. Branch coverage requires instrumenting both sides of conditional branches: inject a counter before the conditional and a counter at the first line of each branch body, then check that both were reached.

---

### A.5 — Per-Gap Remediation (Major Gaps 🔴)

---

#### Gap 1 — Lint: Style 🔴

**Domain Analysis**

Style linting is the enforcement of formatting and naming conventions at the syntactic level: indentation consistency, label naming conventions, command capitalization (MUMPS commands are case-insensitive; a codebase that mixes `SET` and `set` and `Set` is harder to read), line length, spacing around operators. Solving this requires recognizing syntactic structures — a regex over raw text cannot reliably distinguish a command keyword from a string value that happens to contain the same characters.

**Language/Technology Candidates**

| Option | Strengths | Weaknesses | Maturity |
|---|---|---|---|
| Python + `tree-sitter-m` AST visitor | Pythonic, easy rule addition, integrates with existing ycheck; **parser already exists** (99.06% on VistA corpus) | Requires the published Python binding (or a local install of `tree-sitter-m`) | High (tree-sitter Python bindings are mature) |
| Python + regex heuristics | No parser prerequisite, deployable now | Fragile at edge cases, false positives on strings containing keywords | Medium — superseded now that the parser exists |
| Rust + `tree-sitter-m` Rust binding | Fast, single binary; same grammar source-of-truth | Higher contributor barrier than Python | Medium |
| Go + `tree-sitter-m` Go binding | Single binary distribution | Less ergonomic AST walking than Python | Medium |
| JavaScript/Node + `tree-sitter-m` Node binding | Same grammar; trivial integration in editor extensions | Unexpected runtime dependency for a CLI MUMPS tool | Medium |

**Recommended Approach**

Python 3.11+ with the [`tree-sitter-m`](https://github.com/rafael5/tree-sitter-m) Python binding as the parse layer (the parser is already complete — 99.06% clean on the full 39,330-routine VistA corpus, 78.6 ms for a 10k-line synthesised routine). The rule engine is a visitor over the tree-sitter `Node` API: walk the tree with `tree.walk()` (or `node.children` recursion), match on `node.type`, and accumulate violations. Style rules should be configurable via a `ylint.toml` file (using Python's `tomllib` standard library). Output should use `rich` for terminal color and support `--format=json` for CI integration.

For per-keyword rules (e.g. command-keyword capitalization), use the metadata join exposed by `tree-sitter-m`'s `lib/stamp.js` (`canonical_name`, `matched_form`, `standard_status`) to drive checks against the canonical form, not by hand-listing keywords.

The rule set for style linting: command capitalization enforcement, consistent label casing (all-uppercase or CamelCase, not mixed), maximum line length (configurable, default 120), trailing whitespace, spacing after command keywords, dot-block indentation consistency.

**Precedent / Inspiration**

This mirrors `pylint`'s convention rules (C-prefixed messages) or ESLint's stylistic rules. The closest analogue is `rustfmt --check` in Rust: it does not modify files but exits non-zero if the file would be reformatted, enabling CI enforcement without auto-modification.

**Implementation Sketch**

1. Parse each `.m` file into a tree-sitter parse tree via the `tree-sitter-m` Python binding
2. Walk the tree with a `StyleVisitor` that checks each rule against relevant node types
3. Accumulate violations as `(file, line, col, rule_id, message)` tuples
4. Format and output; exit non-zero if any violations found
5. Suppression comments: `; ylint:disable=<rule_id>` on a line suppresses that rule for that line

**Integration Path**

`ycheck --style` calls the style linter on all `.m` files in the project. `make check` includes style checking. Pre-commit hook runs `ycheck --style --format=json` and fails the commit on violations.

---

#### Gap 2 — Lint: Logic 🔴

**Domain Analysis**

Logic linting detects semantic errors that are syntactically valid: variables SET but never READ, labels defined but never called, `QUIT` missing from a function that should return a value, unreachable code after unconditional `QUIT` or `GOTO`. These checks require understanding control flow, not just syntax. At minimum, a control-flow graph (CFG) per routine is needed. Full data-flow analysis (which variables are live at which points) requires a more sophisticated analysis — a def-use chain over the CFG.

**Language/Technology Candidates**

| Option | Strengths | Weaknesses | Maturity |
|---|---|---|---|
| Python + networkx CFG | networkx is mature, well-documented, pure Python | networkx graphs can be slow for very large routines | High |
| Python + custom CFG | Lightweight, no external dependency | More code to maintain | Medium |
| Clang-Tidy style (C++ AST) | Very mature model | Wrong language entirely for this project | N/A |
| Semgrep patterns | Easy rule authorship in YAML | Semgrep's MUMPS support is nonexistent | Low |
| Datalog (Soufflé) | Used by real static analyzers (CodeQL) | Extreme complexity overhead for a hobbyist tool | Low |

**Recommended Approach**

Python 3.11+ with `tree-sitter-m`'s parse tree converted to a CFG using `networkx.DiGraph`. Each routine becomes a directed graph where nodes are basic blocks (sequences of statements with no branches) and edges represent control transfers (`IF`, `FOR`, `DO`, `GOTO`, `QUIT`). Logic rules are then graph queries:

- **Unused variables**: SET nodes whose variable never appears as a read in any downstream node (def-use chain)
- **Unreachable code**: nodes with no incoming edges after the entry node
- **Missing QUIT**: routines that have a call-return usage pattern but lack a `QUIT expr` on all exit paths
- **Naked reference usage**: flag any `^(` as a warning unless it is inside a routine that explicitly sets the last-used global

**Precedent / Inspiration**

This is the equivalent of `go vet` in the Go ecosystem: a lightweight correctness checker that ships with the language toolchain and catches common mistakes without requiring full type inference. Go's `go vet` includes `unreachable`, `unusedresult`, and `lostcancel` checks, all implemented as AST/SSA passes over Go's own compiler IR.

**Implementation Sketch**

1. Parse `.m` files into AST (shared with style linter)
2. For each routine, build a CFG: label nodes as basic block headers, add edges for each branch target
3. Run a reachability analysis from the entry label to mark live blocks
4. Run a def-use pass: collect all `SET var` as definitions, all `$var` reads as uses; report variables defined but never used (excluding intentional dummy variables named `%` or `_`)
5. Check `QUIT` coverage: for routines invoked with `$$` (extrinsic function syntax), verify all paths reach `QUIT expr`

**Integration Path**

`ycheck --logic` runs logic linting. Violations include severity levels: ERROR for unreachable code and missing returns, WARN for unused variables. `make check` gates on zero ERRORs.

---

#### Gap 3 — Lint: Deep (Data Flow) 🔴

**Domain Analysis**

Deep linting goes beyond control flow to data flow: tracking where data values originate, how they transform, and where they are consumed. In MUMPS, this is particularly valuable for global variable data flow — tracking which routines write to which globals, which routines read from them, and whether there are routines that read a global path that is never written anywhere in the codebase (a potential runtime error source). This is a whole-program analysis, not per-routine.

**Language/Technology Candidates**

| Option | Strengths | Weaknesses | Maturity |
|---|---|---|---|
| Python + networkx (whole-program call/data graph) | Reuses CFG infrastructure from Gap 2 | Interprocedural analysis is significantly more complex | High (networkx), Low (MUMPS impl) |
| Soufflé Datalog | Purpose-built for program analysis, declarative rules | High operational complexity, separate toolchain | Medium |
| Python + custom taint analysis | Taint tracking is a well-understood pattern | Requires full inter-procedural call graph | Medium |
| Joern (code property graphs) | Used in security research | Java-based, no MUMPS support, heavyweight | Low |
| LLVM-based IR | Maximum power | Requires MUMPS→LLVM IR frontend, enormous effort | Research-grade |

**Recommended Approach**

Python 3.11+ with `networkx` for both the call graph and data flow graph. The analysis is structured as three passes:

1. **Call graph extraction**: Build a directed graph of `routine A calls routine B` by identifying `DO label^routine` and `$$label^routine()` patterns in the AST
2. **Global access extraction**: For each routine, extract the set of `{global_name: access_type}` where `access_type` is READ, WRITE, KILL, or LOCK
3. **Flow query layer**: The `ycheck --dataflow` command answers specific queries: "which routines write to `^patients`?", "which globals are read but never written?", "is `^tempwork` killed after every use path?"

The global access extraction is the novel part. It requires resolving extended indirection when possible (`@var` where `var` is a locally-set constant) and flagging as UNKNOWN when not.

**Precedent / Inspiration**

This mirrors TypeScript's whole-program type inference or Rust's borrow checker in intent (whole-program reasoning), but in implementation it is closer to a call graph analysis tool like `pycallgraph` or the inter-procedural analysis in `pyright`. The closest direct analogue is the `cargo-geiger` tool in Rust, which performs whole-crate analysis of unsafe usage patterns.

**Implementation Sketch**

1. Build call graph for entire project using AST from all `.m` files
2. Annotate each node with its global access set
3. Propagate annotations up the call graph (a routine that calls a routine that writes `^X` transitively writes `^X`)
4. Report: globals read but never written anywhere; globals written but never read anywhere; globals that cross routine boundaries without any documented interface

**Integration Path**

`ycheck --dataflow` for interactive use; `ycheck --dataflow --format=dot | dot -Tsvg > callgraph.svg` for visualization. Not included in `make check` by default (too slow for routine CI) but available as `make analyze`.

---

#### Gap 4 — Auto-Formatter 🔴

**Domain Analysis**

An auto-formatter transforms source code into a canonical style without changing its semantics. For MUMPS, the stakes are higher than for most languages: because `IF`/`ELSE` interact through `$TEST`, and because dot-block nesting is semantically significant whitespace, a formatter that makes incorrect assumptions will silently break code. This is a correctness-critical tool that must be grounded in a complete semantic model of MUMPS control flow, not just syntactic pretty-printing.

**Language/Technology Candidates**

| Option | Strengths | Weaknesses | Maturity |
|---|---|---|---|
| Python + `tree-sitter-m` (Python binding) | `node.text` over the byte-range tree gives lossless source reconstruction; **parser already exists** | Comment preservation requires explicit handling of trivia between named nodes | High |
| Python + line-level transformer | Simpler, no full parser required | Cannot reformat multi-line constructs | Low — superseded |
| Rust + `tree-sitter-m` (Rust binding) | Tree-sitter's `node.text()` enables lossless formatting; single binary | Higher contributor barrier than Python | Medium |
| Go + `tree-sitter-m` (Go binding) | Single-binary distribution | Less ergonomic AST walking | Medium |
| Haskell + Prettify/Pandoc-style | Algebraic pretty-printing is elegant | Extreme contributor barrier | Research |

**Recommended Approach**

Python 3.11+ with the [`tree-sitter-m`](https://github.com/rafael5/tree-sitter-m) Python binding. Tree-sitter's parse tree is naturally a CST: every byte of the input is covered by some node, and `node.text` (or `source[node.start_byte:node.end_byte]`) lets the formatter reconstruct trivia (comments, whitespace) that lives between named children. The key insight from tools like `rustfmt` and `prettier` is that a formatter must preserve comments and whitespace that carry meaning — tree-sitter's lossless byte-range model is exactly that property.

The formatter outputs canonical MUMPS: uppercase command keywords, single space after command keyword, postconditionals attached with no space (`SET:cond`), dot-blocks indented with exactly one dot plus one space per level, blank lines between top-level routines, and label names normalized to the project-configured convention.

**Precedent / Inspiration**

`rustfmt` in the Rust ecosystem works by parsing source to a full syntax tree (including trivia: comments and whitespace), reformatting using a width-aware layout algorithm (based on Philip Wadler's "A Prettier Printer"), and then emitting the formatted tree. The key lesson from `rustfmt` is that formatting must be idempotent (formatting a formatted file is a no-op) and that the formatter must be integrated with the parser — standalone regex-based formatters are always broken in edge cases.

**Implementation Sketch**

1. Parse `.m` file into a tree-sitter parse tree via the `tree-sitter-m` Python binding; keep the original `source: bytes` alongside the tree so trivia spans can be reconstructed via byte ranges
2. Walk the tree with a `Formatter` class that maintains indent level and line width
3. For each node type, emit the canonical form: commands as uppercase, spaces canonically placed
4. Preserve comment nodes in their original relative positions (before or after the statement they annotate)
5. Detect `IF`/`ELSE` pairs and emit them with a warning if the formatter cannot statically verify semantic equivalence (to avoid the `$TEST` trap)
6. Write output to stdout; use `--in-place` flag to overwrite; use `--check` for CI enforcement

**Integration Path**

`yfmt file.m` for single file. `yfmt --check` in `make check`. Pre-commit hook runs `yfmt --check` and fails if formatting differs. `make fmt` runs `yfmt --in-place` on all `.m` files.

---

> **Note on coverage:** This Addendum keeps per-gap entries only for the **unbuilt** tools — the strategic forward-looking content. Per-gap entries for Gaps 5, 6, 12–16 (Major) and 18, 19, 21, 23–31, 34, 36 (Moderate) covered tools that have since shipped; their as-built specifications live in [implementation.md §3](implementation.md#3-as-built-tool-specifications) and the per-tool deltas in [implementation.md §5.1](implementation.md#51-per-tool-delta-vs-original-spec). The remaining unbuilt-tool entries continue below: Gaps 7, 8, 10, 11 (Major) and Gaps 17, 20, 22, 32, 33, 35 (Moderate).

---

#### Gap 7 — Coverage: Line 🔴

**Domain Analysis**

Line coverage measures which source lines were executed during the test suite. For MUMPS, there is no built-in coverage facility. The solution is source instrumentation as described in A.4: inject counter increments before each executable line, run the suite, read the counters.

**Recommended Approach**

Python 3.11+ source instrumentor (`ycov.py`) that uses the [`tree-sitter-m`](https://github.com/rafael5/tree-sitter-m) Python binding to identify every executable line (every line with a command, not blank lines or comment-only lines), injects `$INCREMENT(^ycov("line",routine,linenum))` as the first statement on that line, writes instrumented `.m` files to a temporary directory (preserving the directory structure), runs `yeval` against the instrumented source, reads back `^ycov` via `mupip extract` into a ZWR file, and computes line coverage as `executed_lines / total_lines * 100`.

The parser is used to distinguish executable lines from label-only lines and comment-only lines, which must not be counted in the denominator. `tree-sitter-m`'s `line` / `label` / `comment` node types make this a direct query.

**Precedent / Inspiration**

`coverage.py` in Python uses the same source instrumentation approach. `gcov` in C/C++ instruments at the compiler IR level. The simpler `istanbul` (JavaScript) instruments source text, not AST, which produces false results for multi-statement lines — a lesson to take from.

**Implementation Sketch**

1. For each `.m` file, parse with `tree-sitter-m` to get line-type annotations (command line, label, comment, blank)
2. Inject `$INCREMENT(^ycov("L",routineName,lineNum))` as first statement on each command line
3. Write instrumented files to `/tmp/ycov_src/`
4. Set `ydb_routines` to point to `/tmp/ycov_src/` prepended to the normal path
5. Run `yeval`
6. `mupip extract /tmp/ycov.zwr` to get `^ycov` data
7. Parse ZWR, compute coverage per routine and project-wide
8. Output: per-routine table with line counts and coverage %; highlight uncovered lines

**Integration Path**

Replaces today's `ycover` (label-entry approximation). `make coverage` runs `ycov --report=term`. `make coverage-html` produces HTML report. CI posts coverage percentage as a check status.

---

#### Gap 8 — Coverage: Branch 🔴

**Domain Analysis**

Branch coverage measures whether both sides of every conditional were executed. In MUMPS, the relevant branching constructs are `IF condition` (true branch executed / false branch — fall through to `ELSE` or next command), postconditionals `CMD:condition` (command executed / skipped), and `FOR` loop entry/exit. Branch coverage requires more precise instrumentation than line coverage.

**Recommended Approach**

Extend `ycov.py` with branch instrumentation mode. For each `IF condition`, inject two counters: `^ycov("BT",routine,linenum)` (branch true — increment before the if-body) and `^ycov("BF",routine,linenum)` (branch false — inject before the `ELSE` body or, if no `ELSE`, inject via a `$INCREMENT(^ycov("BF",...))` into a synthetic `ELSE` block appended after the `IF`).

For postconditionals `CMD:cond`, the instrumentation is: inject `^ycov("PT",...)` before the command (executed only if condition is true) and `^ycov("PF",...)` as `DO:'cond $INCREMENT(^ycov("PF",...))` before the command.

**Implementation Sketch**

1. Extend the `tree-sitter-m` AST visitor to identify branch points (IF, ELSE, postconditionals, FOR bodies)
2. For each branch point, inject a pair of counters (true-side and false-side)
3. After test run, compute branch coverage: for each branch point, check if both sides have non-zero counts
4. Report as: `branch coverage: 45/60 branches covered (75%)`
5. Combine with line coverage report in the same output

**Integration Path**

`ycov --branch` adds branch coverage to the standard coverage report. `make coverage` runs both by default. The LCOV output can be fed to `genhtml` for HTML reporting.

---

#### Gap 10 — Debugger: Scriptable 🔴

**Domain Analysis**

YottaDB has an interactive debugger built into the environment: ZBREAK sets breakpoints, ZSHOW shows state, and the direct-mode prompt allows inspection. The gap is that none of this is scriptable — there is no programmatic API for setting breakpoints, stepping, and inspecting state from an external process. A scriptable debugger enables automated failure analysis: when a test fails, automatically attach a debugging session to replay the failure and capture the state at the point of error.

**Recommended Approach**

Python 3.11+ with `pexpect` as the immediate solution, targeting the DAP (Debug Adapter Protocol) as a long-term goal. The `pexpect` driver wraps a `yottadb` direct-mode session: it sends ZBREAK commands to set breakpoints, sends `DO label^routine` to start execution, waits for the breakpoint prompt, and then sends ZSHOW commands to inspect state. The output is captured and parsed by Python.

A `ydebug.py` script provides a scriptable interface: `ydebug.set_break("label", "routine")`, `ydebug.run("label", "routine")`, `ydebug.get_local("varname")`, `ydebug.get_global("^globalname", subscripts)`.

**Precedent / Inspiration**

`gdb` with Python scripting is the gold standard for scriptable debugging. `lldb` has an equivalent Python API. The long-term DAP implementation mirrors how `debugpy` (Python's VS Code debugger) works: a standalone process implementing the Debug Adapter Protocol.

**Implementation Sketch**

1. `pexpect.spawn('yottadb -direct')` starts a YDB direct-mode session
2. Send `ZBREAK label^routine` for each requested breakpoint
3. Send `DO entry^routine` to start execution
4. Wait for `%YDB-I-BPNTSET` and breakpoint hit prompts
5. At each breakpoint, send `ZSHOW "V"` to capture local variable state; parse the output
6. Provide `step()`, `continue_()`, `inspect_local()`, `inspect_global()` methods

**Integration Path**

`ydebug --script=replay_failure.py` runs a debugging script against a failing test. Future: `ytest --debug YTAUTH:TESTLOGIN` automatically attaches debugger on test failure and dumps variable state.

---

#### Gap 11 — Dependency Management 🔴

**Domain Analysis**

MUMPS has no package manager. Sharing code between projects requires manually copying `.m` files, with no version pinning, conflict resolution, or transitive dependency tracking. A dependency management system for MUMPS needs: a manifest format for declaring dependencies, a registry or source location for packages, a resolver that satisfies version constraints, and an installer that places `.m` files in the correct location in `ydb_routines`.

**Recommended Approach**

Python 3.11+ with a `ydb-pkg` (future `m pkg`) tool using TOML manifests. The manifest format (`ydb.toml`) specifies dependencies as git repository URLs with version tags or commit hashes — exactly the Go modules model, which deliberately avoids central registry lock-in. The `ydb-pkg install` command reads `ydb.toml`, clones or fetches each dependency, checks out the specified version, and copies the `.m` files to a local `vendor/` directory. The `ydb_routines` environment variable is updated to include `vendor/`.

A lockfile (`ydb.lock`) records the exact commit hash of each dependency at install time, enabling reproducible installs. The manifest format itself should be specified in `m-standard` (it is M-language metadata, not YDB-specific), and the installer can grow YDB-specific and IRIS-specific backends later.

**Precedent / Inspiration**

Go's module system (`go.mod` + `go.sum`) is the closest analogue: dependencies declared as URL + version, with a lockfile for reproducibility, no central registry required. `cargo` in Rust adds a central registry on top of the same model. For M, starting with the Go model is appropriate because the ecosystem is too small to justify a registry.

**Implementation Sketch**

1. `ydb.toml` format: `[dependencies]`, key = package name, value = `"git+https://github.com/user/repo@v1.2.3"`
2. `ydb-pkg install` reads manifest, resolves versions, clones to `vendor/<name>/`, copies `.m` files
3. `ydb-pkg update <name>` fetches latest tag matching the version constraint
4. `ydb-pkg lock` generates `ydb.lock` with exact commit hashes
5. Environment setup: `eval $(ydb-pkg env)` adds `vendor/` to `ydb_routines`

**Integration Path**

`make install` runs `ydb-pkg install`. `ydb_routines` in `.envrc` (direnv) includes the vendor path. CI runs `ydb-pkg install --frozen` (respects lockfile, fails if lockfile is stale).

---

### A.6 — Per-Gap Remediation (Moderate Gaps 🟡)

Per-gap entries for the still-unbuilt Moderate gaps. (See note at the start of A.5: shipped-tool entries are in [implementation.md](implementation.md).)

---

#### Gap 17 — Interactive REPL 🟡

**Domain Analysis**

The YottaDB direct-mode prompt is an interactive REPL, but it lacks the features that make REPLs productive: command history with search, tab completion for global names and labels, multi-line expression editing with proper continuation, and syntax highlighting. The gap is not the absence of a REPL but the absence of a good REPL.

**Recommended Approach**

Two phases. **Immediate**: `rlwrap yottadb -direct` already adds history and basic readline editing with zero new code. Document this and add `alias ymrepl='rlwrap yottadb -direct'` to environment setup. **Proper**: Python 3.11+ with `prompt_toolkit` wrapping a `pexpect`-driven YDB process. `prompt_toolkit` provides: history with `~/.ydb_history`, tab completion (complete global names from `$ORDER`, label names from the symbol index built by `tree-sitter-m`), multi-line input (detect incomplete expressions by counting unclosed parentheses and DO blocks), and syntax highlighting using a Pygments lexer for MUMPS.

**Precedent / Inspiration**

`pgcli` (PostgreSQL CLI replacement) and `mycli` (MySQL) both use `prompt_toolkit` to provide schema-aware completion, syntax highlighting, and history for database CLIs. `bpython` uses the same approach for Python. `ipython` is the reference implementation.

**Integration Path**

`yrepl` command launches the enhanced REPL. Falls back to `rlwrap yottadb -direct` if Python dependencies are not installed.

---

#### Gap 20 — Test History 🟡

**Domain Analysis**

Test history — tracking pass/fail/skip counts and timing trends across runs — enables identifying flaky tests, tracking coverage regression, and demonstrating progress over time. This requires persistent storage of test results and a reporting interface.

**Recommended Approach**

Python 3.11+ with SQLite (via the standard library `sqlite3` module). The `yhistory.py` tool maintains a `data/ydb/test_history.db` SQLite database. Each test run inserts one row per test: `(run_id, timestamp, routine, label, result, duration_ms, output)`. The `yhistory report` command shows trends: flaky tests (pass/fail in the last 10 runs), slowest tests, recent regressions.

**Implementation Sketch**

1. `ytest` appends results to `yhistory.db` after each run (TAP parse → SQLite insert)
2. Schema: `runs(id, timestamp, suite, duration)`, `results(run_id, test_id, result, duration_ms)`
3. `yhistory trend --last=30` shows a sparkline (using `rich.sparkline`) of pass rate over time
4. `yhistory flaky` lists tests with >10% failure rate in the last 50 runs
5. `yhistory compare run1 run2` shows which tests changed result between runs

**Integration Path**

History is written automatically by `ytest`. `make history` shows trend report. CI publishes history stats as job summaries.

---

#### Gap 22 — Profiling 🟡

**Domain Analysis**

Profiling identifies which routines and labels consume the most execution time or are called most frequently. Unlike benchmarking (which measures a specific operation), profiling measures the whole system under realistic load to find bottlenecks. As described in A.4, source instrumentation is the practical approach for MUMPS profiling.

**Recommended Approach**

Extend `ycov.py` (Gap 7) with a profiling mode that captures both call counts (via the `^ycov` instrumentation global) and wall-clock time (via `$ZHOROLOG` at label entry/exit). The profiler report shows: top 20 labels by call count, top 20 labels by total time, top 20 labels by time-per-call. This is a flat profile (not a call graph profile), which is appropriate for MUMPS given the complexity of building a full call graph profile.

For a more sophisticated sampling profiler (without source modification), the Python debugger driver from Gap 10 (`pexpect`-based) can periodically send ZSHOW commands to a running YDB process to capture the current execution label — this is the statistical sampling approach, equivalent to how `perf` and `py-spy` work.

**Implementation Sketch**

1. Instrumentation mode: inject `$INCREMENT(^yprof(label,routine))` at each label entry; also capture `$ZHOROLOG` value
2. Run routine under test N times
3. Read `^yprof` via ZWR export
4. Report: sorted by call count, then by total time
5. Sampling mode (alternative): `pexpect` driver sends `ZSHOW "S"` (stack trace) every 10ms; aggregate stack frames

**Integration Path**

`yprof --routine YTPERF^TESTQUERY` runs instrumented profiling. `yprof --sample --attach <pid>` runs sampling profiler against a running YDB process. `make profile` runs instrumented profiling on the benchmark suite.

---

#### Gap 32 — Complexity Metrics 🟡

**Domain Analysis**

Complexity metrics quantify the structural complexity of code: cyclomatic complexity (number of linearly independent paths through a routine), cognitive complexity (how difficult a routine is to understand), nesting depth (maximum dot-block nesting). High-complexity routines are candidates for refactoring. Computing these metrics requires parsing the control flow structure.

**Recommended Approach**

Python 3.11+ complexity visitor over the `tree-sitter-m` AST. Cyclomatic complexity (CC) for a MUMPS routine is: 1 + (number of `IF` statements) + (number of postconditionals) + (number of `FOR` loops) + (number of `DO:condition` calls). This is the standard McCabe formula applied to MUMPS control flow constructs. Cognitive complexity adds weighting for nesting depth.

Output: per-routine table sorted by complexity, with configurable thresholds (warn at CC > 10, error at CC > 20). Export as JSON for trend tracking.

**Precedent / Inspiration**

`radon` in Python computes McCabe complexity for Python code. `lizard` is a polyglot complexity analyzer. The key insight from `radon`: complexity should be tracked over time (regression detection) and integrated into code review.

**Implementation Sketch**

1. `tree-sitter-m` AST visitor `ComplexityVisitor` counts: `IF` nodes (+1 each), postconditional attributes (+1 each), `FOR` nodes (+1 each), `DO:cond` (+1 each), logical operators in conditions (`&`, `!` in M = `AND`/`OR`) (+1 each)
2. Track maximum nesting depth (dot-block depth)
3. `ycomplex` command reports per-routine CC, max nesting, total LOC
4. `--max-cc=15` fails if any routine exceeds threshold
5. History stored in SQLite for trend analysis

**Integration Path**

`ycomplex` command. `make complexity` runs and reports. `--max-cc` flag integrated into `ycheck`. Complexity trends shown alongside test history.

---

#### Gap 33 — Dead Code Detection 🟡

**Domain Analysis**

Dead code detection identifies code that can never be executed: labels that are defined but never called from anywhere in the codebase (unreachable labels), globals that are written but never read, and code after unconditional `QUIT` statements. This is a whole-program reachability analysis.

**Recommended Approach**

Python 3.11+ with `networkx` call graph analysis. The call graph is built by the data flow tool (Gap 3); dead code detection adds a reachability query: starting from known entry points (labels that are called from test entry points, from external interfaces, or marked with a `;;@export` doc annotation), traverse the call graph and collect all reachable labels. Any label not in the reachable set is potentially dead.

The "potentially" qualifier is important: MUMPS uses dynamic dispatch extensively (string-valued routine and label names, `DO @labelvar^@routinevar`), so static reachability analysis will have false positives. The tool should flag dynamic dispatch sites and annotate potentially-dead-but-dynamically-called labels separately.

**Precedent / Inspiration**

`cargo unused-features` and `clippy::dead_code` in Rust; `pylint`'s unused-import warnings in Python; `knip` in TypeScript. The key design lesson: dead code detection must have a clear notion of "entry points" (exported symbols), and everything reachable from entry points is live.

**Implementation Sketch**

1. Parse all `.m` files into AST; build call graph (from Gap 3)
2. Identify entry points: labels called from `yeval` test entry points, labels marked `;;@export`, labels in known framework hook positions
3. BFS/DFS from all entry points; mark all reachable labels as LIVE
4. Report all labels not marked LIVE as potentially DEAD
5. Flag any call sites that use string-valued routine/label names as DYNAMIC (cannot trace statically)

**Integration Path**

`ydead` command. `make dead-code` for project-wide analysis. Not in default `make check` (too many false positives from dynamic dispatch); run as `make analyze`.

---

#### Gap 35 — Parallel Tests 🟡

**Domain Analysis**

Running tests in parallel reduces total test suite time. For MUMPS/YottaDB, parallelism is constrained by database isolation: two parallel tests that write to the same global will interfere. The solution is either global namespace partitioning (each parallel worker uses a unique global prefix) or separate database files (each worker gets its own `ydb_gbldir` pointing to an isolated database).

**Recommended Approach**

Python 3.11+ with `concurrent.futures.ProcessPoolExecutor`, using the **separate database files** approach for isolation: each worker process gets a unique `ydb_gbldir` environment variable pointing to a copy of the baseline database in a temporary directory. Workers are pre-provisioned (one database copy per worker), and tests are distributed to workers in a queue. Results are collected and merged by the main process.

The worker count defaults to `min(cpu_count(), suite_count)`. For test suites that must share state (integration tests), they are pinned to a single worker using a `;;@serial` annotation.

**Precedent / Inspiration**

`pytest-xdist` in Python is the model: each worker gets an isolated environment, tests are distributed via a work queue, results are streamed back. The database-per-worker approach mirrors how Rails' `parallel_tests` gem creates a separate test database per worker.

**Implementation Sketch**

1. `ytest --parallel=4` provisions 4 worker environments: `cp -a $ydb_gbldir /tmp/ywrk_{0..3}/`
2. Distributes test list to a shared `multiprocessing.Queue`
3. Each worker pops tests from the queue, runs with its own `ydb_gbldir`, pushes results to results queue
4. Main process aggregates results, reports progress with `rich.progress`
5. On test failure, worker saves its database state for post-mortem debugging
6. Cleanup: removes worker database copies

**Integration Path**

`make test-parallel` runs with `--parallel=$(nproc)`. CI uses `--parallel=4`. Sequential mode (`make test`) is used for debugging.

---

*End of Addendum A*

---

## Addendum B: Prioritized Sequence of Remediation (Post-Parser)

This addendum was added 2026-04-27, after `tree-sitter-m` v1.0 shipped (99.06% clean on the 39,330-routine VistA corpus) and `m-standard` v1.0 was tagged. The strategic question is no longer *should we build a parser?* — it is *which downstream tools are worth building, in what order, now that the parser dependency is satisfied?*

The Tier 1–3 tools listed in Chapter 3 are already shipped. The remaining work is the Tier 4 backlog plus the umbrella-dispatcher rename. This addendum sequences that work into five phases ordered by daily friction, ecosystem unlock, and dependency depth.

---

### B.1 — Sequencing Principles

Three criteria drive the order:

1. **Daily friction first.** A tool that hurts every commit (no formatter) outranks a tool that hurts once a quarter (a debugger).
2. **Ecosystem unlock.** A tool that unblocks others (a formatter that lets a linter assume canonical layout) outranks a self-contained tool of equal friction.
3. **Risk-adjusted effort.** Tools with a clear analogue in another ecosystem (`yfmt` ≈ `gofmt`, `ylint` ≈ `clippy`) have lower implementation risk than novel work (a MUMPS-native package manager).

Two anti-principles also apply:

- **Do not bundle.** Each phase ships independently and is usable on its own. No phase blocks the next; a delay in Phase 3 must not stall Phase 4.
- **Do not perfect.** Each tool ships a usable v0.1 first. Coverage of edge cases (`ylint-deep`'s call-graph analysis, `ydebug`'s breakpoint expressions) matures over subsequent releases.

---

### B.2 — Phase 1: Canonicalise the Codebase

**Goal:** eliminate style debate and lock in a deterministic file layout that downstream tools can assume.

| Tool | Future name | Effort | Why now |
|------|-------------|--------|---------|
| **`yfmt`** | `m fmt` | Medium (2–3 weeks) | No current solution. Canonical formatting is the precondition for every later visitor — a linter that fights inconsistent indentation is a much harder linter. |

**Implementation:**
- Lossless byte-range pretty-printer over the `tree-sitter-m` AST (preserves comments, blank-line groupings, trailing-comment column alignment).
- Configuration: `m.toml` with style rules (label case, dot-block depth limits, max line length). Defaults match the "Lowercase Pythonic MUMPS" style in this project's CLAUDE.md.
- Idempotent: `m fmt | m fmt` produces no further change. Round-trip CI test runs the formatter twice and asserts byte-identical output.
- `--check` mode exits non-zero on any drift; wired into `yhook` and `yci`.

**Exit criteria for the phase:** `yfmt --check` passes on this repo and on a representative VistA package; the output is bytewise stable across two consecutive runs.

---

### B.3 — Phase 2: Catch Bugs Before Runtime

**Goal:** move bug categories from "found in test" to "found at edit time."

| Tool | Future name | Effort | Why now |
|------|-------------|--------|---------|
| **`ylint-style`** | `m lint --style` | Small (1–2 weeks) | AST visitor with rule predicates; rules are mostly mechanical. Builds the lint framework itself. |
| **`ylint-logic`** | `m lint --logic` | Medium (2–3 weeks) | Control-flow rules over the same framework: missing `QUIT`, unreachable code, undefined labels, unused locals. |

**Implementation:**
- Single binary, pluggable rule set. `m lint --style --logic` runs both groups; granular `--enable=R001,R012` for CI tuning.
- Lint configuration in the same `m.toml` as `yfmt`. Rule severity (`error` / `warning` / `off`) is per-project.
- Output formats: human (default), `--format=json` for editor integration, `--format=tap` for the existing `ytap` pipeline.
- `--fix` mode for mechanically rewritable rules (e.g., trailing whitespace, missing `QUIT` at the end of a routine).

**Why before `ylint-deep`:** the style + logic rules are local — they reason within a single function or routine. The deep variant needs a call graph and a symbol table that span the whole project, which is materially more work for a smaller marginal payoff. Ship the cheap, broad-coverage layer first.

**Exit criteria:** `m lint --style --logic` runs cleanly on this repo's existing routines (after the formatter pass), and surfaces ≥3 real bugs when run against a noisy VistA package as a smoke test.

---

### B.4 — Phase 3: Replace Approximations with Truth

**Goal:** retire the placeholder coverage tool with a parser-grounded replacement, and add the deeper analyses that need a call graph.

| Tool | Future name | Effort | Why now |
|------|-------------|--------|---------|
| **`ycov-line` / `ycov-branch`** | `ydb cover --line` / `--branch` | Medium (2–3 weeks) | Today's `ycover` reports label-entry coverage only — i.e., "did we enter this label?" not "did we execute every line in it?" The parser identifies real instrumentation points (statements + branches), and the existing `^ycov` global infrastructure is reused. |
| **`ylint-deep`** | `m lint --deep` | Large (4–6 weeks) | Builds a project-wide call graph and symbol table on top of the AST. Detects unused exports, dead labels, missing-routine references, and circular dependencies. |

**Implementation notes:**
- `ydb cover` keeps the existing `ZBREAK`-based runtime hook; the change is in instrumentation-point selection (now AST-driven) and in reporting (line + branch percentages, lcov export for IDE integration).
- `ylint-deep` shares the rule framework from Phase 2. New rule categories: `dead-code`, `unused-export`, `unresolved-call`, `cyclic-import`. The call graph itself becomes a reusable artifact (`m graph` could ship as a thin CLI over it later).

**Exit criteria:** `ydb cover --line` agrees with hand-instrumented spot checks on a small routine; `ylint-deep` correctly identifies the known dead labels in this repo's own `routines/`.

---

### B.5 — Phase 4: Interactive Surfaces (No Parser Dep)

These tools do not require the parser and were previously deferred only on demand. They can be picked up in parallel with Phase 2 or Phase 3 by a separate contributor.

| Tool | Future name | Effort | Notes |
|------|-------------|--------|-------|
| **`yrepl` Phase 1** | `ydb repl` | Small (≤1 week) | Wrap `ydb` direct mode with `rlwrap` or `prompt_toolkit` for history + multi-line editing. No parser dependency. |
| **`yparallel`** | `ydb test --parallel` | Medium (2 weeks) | Worker pool over isolated `ydb_gbldir` copies (see [A.6 → Parallel Test Execution](#a6--per-gap-remediation-moderate-gaps-)). Blocked only on per-suite isolation discipline in our existing tests. |
| **`ydebug`** | `ydb debug` | Large (3–4 weeks) | DAP server over YDB's `ZBREAK` / `ZSTEP` / `ZSHOW` primitives. Highest ceiling (full IDE step-debugging) but the lowest daily friction — a battery of `ZSHOW`s in direct mode covers most cases today. |
| **`yrepl` Phase 2** | `ydb repl` | Small follow-on | Adds tab-completion driven by `tree-sitter-m` (after Phase 1 ships). |

**Sequencing within the phase:** ship `yrepl` Phase 1 first — it is the smallest measurable win and unblocks REPL-driven exploration immediately. `yparallel` next, since it directly speeds up the existing test loop. `ydebug` last; it is the largest investment and the smallest delta over today's manual `ZBREAK` workflow.

---

### B.6 — Phase 5: Ecosystem Layer

| Tool | Future name | Effort | Status |
|------|-------------|--------|--------|
| **`ydb-pkg`** | `m pkg` | Large (6+ weeks) | Blocked on the manifest-format design in `m-standard`. Once the format is specified, the installer is a relatively small shell + Python tool over a declarative TOML registry. |
| **Bindings publishing** | (`tree-sitter-m`) | Small (≤1 week each) | Publish to npm / crates.io / PyPI / Go module proxy. Unblocks third-party tool authors. Tracked in `tree-sitter-m`'s STATUS, not in this document. |
| **AD-03 stamping** | (`tree-sitter-m`) | Small | Per `tree-sitter-m` STATUS — integrate the keyword-coverage stamping into the grammar release process. |

The package manager is intentionally last. The current toolchain assumes a single-repo / single-routine-set model, which has been adequate. Cross-project sharing of `.m` libraries is the genuine new capability that `ydb-pkg` unlocks, and the design ROI grows once a second project (e.g., a CLI on top of the parser) actually wants to depend on `m-tools`'s helpers.

---

### B.7 — Cross-Cutting: Umbrella Dispatcher Rename

The `m <subcommand>` / `ydb <subcommand>` rename (see [implementation.md → §1](implementation.md#1-canonical-command-map-m-help)) is independent of the per-tool work and can be done in any phase. Recommended timing: **after Phase 2 ships**, when the lint framework forces a config file to exist (`m.toml`) and the umbrella dispatcher gives the config a natural home.

The migration is mechanical: existing `y*` shell scripts become thin shims that dispatch to the umbrella. Old names remain functional indefinitely (no breakage); new documentation references the umbrella form.

---

### B.8 — Sequence Summary

| Phase | Tools | Approximate effort | Unblocks |
|-------|-------|--------------------|----------|
| **1** | `yfmt` | 2–3 weeks | Style debate ends; later visitors assume canonical layout |
| **2** | `ylint-style`, `ylint-logic` | 3–5 weeks | Bugs caught at edit time; lint framework reusable |
| **3** | `ycov-line`/`ycov-branch`, `ylint-deep` | 6–9 weeks | Real (not approximate) coverage; project-wide analyses |
| **4** | `yrepl` (P1+P2), `yparallel`, `ydebug` | 6–8 weeks | Interactive ergonomics; faster test loop |
| **5** | `ydb-pkg`, bindings publishing | 6+ weeks | Cross-project library sharing; third-party tool authors |
| **X-cut** | Umbrella dispatcher rename | 1 week | Coherent CLI surface; canonical config home |

**Critical-path summary:** the parser foundation is shipped, so no phase has a hard blocker on another. Phases 1 → 2 → 3 form the natural single-developer critical path (each builds on the previous AST + framework). Phase 4 is parallelisable. Phase 5 waits on `m-standard`'s manifest design and accepts a third-party-driven cadence.

---

*End of Addendum B*

---

## Appendix B: Gold Standard — Top 5 Language Toolchains

This appendix documents the toolchain available to developers in each of the five most widely used mainstream programming languages. These represent the lived experience of developers who would need to transition to or work alongside M code, and form the basis for the gold-standard column in [Chapter 2 — Comprehensive Gap Analysis](#2-comprehensive-gap-analysis).

---

### B.1 Python

Python's toolchain has matured significantly with the `ruff` era. The ecosystem prioritizes speed of feedback and comprehensive static analysis.

| Category | Tool(s) | Command | Notes |
|----------|---------|---------|-------|
| Runtime / REPL | `python`, `ipython`, `ptpython` | `python`, `ipython` | Full REPL with history, completion, multiline, magic commands |
| Syntax check | `py_compile`, `ruff` | `python -m py_compile f.py` | Instant; part of every linter |
| Linting (style) | `ruff`, `flake8`, `pycodestyle` | `ruff check .` | Rule-based; hundreds of configurable checks |
| Linting (logic) | `pylint`, `ruff` | `pylint src/` | Detects unused vars, unreachable code, missing returns |
| Type checking | `mypy`, `pyright` | `mypy src/` | Full static type analysis; catches type errors before runtime |
| Formatting | `ruff format`, `black`, `autopep8` | `ruff format .` | Zero-config; deterministic output |
| Test runner | `pytest`, `unittest` | `pytest` | Autodiscovers tests; rich output; plugins |
| Single test | `pytest` | `pytest tests/test_foo.py::test_bar` | Path + name selector |
| Test watcher | `pytest-watch`, `watchdog` | `ptw` | Reruns only affected tests on save |
| Coverage | `coverage.py`, `pytest-cov` | `pytest --cov=src` | Line + branch coverage; HTML report |
| Benchmarking | `pytest-benchmark`, `timeit` | `pytest --benchmark-only` | Repeatable, statistical results |
| Profiling | `cProfile`, `py-spy`, `line_profiler` | `py-spy record -o out.svg -- python f.py` | Flame graphs, line-level timing |
| Debugging | `pdb`, `ipdb`, `debugpy` | `python -m pdb script.py` | Breakpoints, step, inspect; IDE integration via DAP |
| Documentation | `pdoc`, `sphinx`, `mkdocs` | `pdoc src/mymodule` | Extracts docstrings; generates HTML |
| Dependency mgmt | `uv`, `pip`, `poetry`, `pipenv` | `uv add requests` | Lockfiles, virtual envs, reproducible installs |
| Build / tasks | `make`, `tox`, `nox`, `invoke` | `tox` | Multi-env test matrix; task automation |
| Import analysis | `isort`, `ruff` | `ruff check --select I` | Detect unused imports, sort order |
| Security scan | `bandit`, `safety` | `bandit -r src/` | Detects common security anti-patterns |
| Complexity | `radon`, `ruff` | `radon cc src/` | Cyclomatic complexity per function |
| Dead code | `vulture` | `vulture src/` | Unused functions, variables, imports |
| Fixture mgmt | `pytest fixtures`, `factory_boy` | `@pytest.fixture` decorator | Scoped, composable test state |
| Snapshot testing | `syrupy` | `assert result == snapshot` | Auto-update expected output |
| Pre-commit hooks | `pre-commit` | `pre-commit install` | Runs lint+format+type-check before every commit |
| CI script | `tox`, `nox`, GitHub Actions | `tox -e lint,type,test` | Full pipeline; matrix testing |
| Environment check | `tox`, `pyenv` | `python --version` | Version managers + lockfiles ensure reproducibility |
| Package publishing | `twine`, `flit`, `uv publish` | `uv publish` | Upload to PyPI |

---

### B.2 JavaScript / TypeScript

The JS/TS ecosystem has the broadest toolchain of any language, driven by the npm ecosystem's culture of small, composable packages.

| Category | Tool(s) | Command | Notes |
|----------|---------|---------|-------|
| Runtime / REPL | `node`, `ts-node`, `deno` | `node` | Readline REPL; `ts-node` for TypeScript |
| Syntax check | `tsc` | `tsc --noEmit` | TypeScript compiler; also catches type errors |
| Linting | `eslint`, `biome` | `eslint src/` | Pluggable; hundreds of rules; fixable violations |
| Type checking | `tsc`, `pyright` | `tsc --strict` | Full inference + structural typing |
| Formatting | `prettier`, `biome` | `prettier --write .` | Zero-config; opinionated; universal |
| Test runner | `jest`, `vitest`, `mocha` | `jest` | Autodiscovery; parallel; snapshots built-in |
| Single test | `jest`, `vitest` | `jest --testNamePattern "my test"` | Regex name or path filter |
| Test watcher | `jest`, `vitest` | `jest --watch` or `vitest --watch` | Interactive; runs only changed files |
| Coverage | `istanbul/nyc`, `c8`, `v8` | `jest --coverage` | Built into jest; HTML + lcov output |
| Benchmarking | `tinybench`, `benchmark.js` | (library-based) | Statistical microbenchmarks |
| Profiling | Node `--prof`, Chrome DevTools | `node --prof script.js` | V8 CPU profiler; flame graphs |
| Debugging | `node --inspect`, VS Code | `node --inspect-brk` | DAP protocol; full IDE integration |
| Documentation | `jsdoc`, `typedoc` | `typedoc src/` | Extracts JSDoc/TSDoc comments; HTML output |
| Dependency mgmt | `npm`, `yarn`, `pnpm` | `npm install` | `package-lock.json`; semantic versioning |
| Build | `webpack`, `vite`, `esbuild`, `rollup` | `vite build` | Bundling, tree-shaking, minification |
| Snapshot testing | `jest snapshots` | `expect(x).toMatchSnapshot()` | Auto-create + update expected output files |
| Fixture mgmt | `jest beforeEach/afterEach` | `beforeEach(() => setup())` | Scoped setup/teardown per test/suite |
| Mock/stub | `jest.mock()`, `sinon` | `jest.mock('./module')` | Module-level mocking; spy functions |
| Pre-commit hooks | `husky`, `lint-staged` | `npx husky install` | Run lint+format on staged files only |
| CI script | GitHub Actions, `npm run ci` | `npm run lint && npm test` | Standard `ci` script in `package.json` |
| Security scan | `npm audit`, `snyk` | `npm audit` | Dependency vulnerability scanning |
| Environment check | `nvm`, `volta`, `.nvmrc` | `node --version` | Version pinning per project |

---

### B.3 Go

Go's toolchain is the gold standard for batteries-included developer experience. Nearly everything ships with the language itself; third-party tools fill only the gaps.

| Category | Tool(s) | Command | Notes |
|----------|---------|---------|-------|
| Runtime / REPL | `gore`, `yaegi` | `gore` | No official REPL; `go run` for quick scripts |
| Syntax check | `go build` | `go build ./...` | Compile errors are syntax + type errors |
| Linting (vet) | `go vet` | `go vet ./...` | Ships with Go; catches common mistakes |
| Linting (full) | `golangci-lint`, `staticcheck` | `golangci-lint run` | Aggregates 50+ linters; industry standard |
| Type checking | built-in | `go build` | Types are checked at compile time — always |
| Formatting | `gofmt`, `goimports` | `gofmt -w .` | **Ships with Go**; canonical; non-negotiable in PRs |
| Test runner | `go test` | `go test ./...` | **Ships with Go**; parallel by default |
| Single test | `go test` | `go test -run TestName ./pkg/` | Regex name filter + package path |
| Test watcher | `gotestsum`, `air` | `gotestsum --watch` | `gotestsum` formats output; `--watch` reruns on change |
| Coverage | `go test -cover` | `go test -coverprofile=c.out ./...` | **Ships with Go**; HTML report via `go tool cover` |
| Benchmarking | `go test -bench` | `go test -bench=. -benchmem` | **Ships with Go**; ns/op + allocs/op |
| Profiling | `go tool pprof` | `go test -cpuprofile=cpu.out` | **Ships with Go**; flame graphs, heap profiles |
| Debugging | `dlv` (Delve) | `dlv test ./pkg/` | Full DAP debugger; breakpoints, stack, goroutines |
| Documentation | `godoc`, `pkgsite` | `godoc -http :6060` | Extracts doc comments; standard format |
| Dependency mgmt | `go mod` | `go mod tidy` | **Ships with Go**; lockfile (`go.sum`); reproducible |
| Build | `go build` | `go build -o bin/app` | **Ships with Go** |
| Race detector | `go test -race` | `go test -race ./...` | **Ships with Go**; detects data races at runtime |
| Fuzzing | `go test -fuzz` | `go test -fuzz=FuzzFn` | **Ships with Go** since 1.18 |
| Fixture mgmt | `testing.T`, `testcontainers` | `t.Cleanup(func(){...})` | `t.TempDir()`, `t.Cleanup()` built into stdlib |
| Pre-commit hooks | `golangci-lint` + `pre-commit` | `pre-commit run --all-files` | Standard practice; enforces `gofmt` + vet |
| CI script | `Makefile`, GitHub Actions | `make lint test` | `go vet + golangci-lint + go test` |
| Security scan | `gosec`, `govulncheck` | `govulncheck ./...` | **`govulncheck` ships with Go toolchain** |
| Complexity | `gocyclo`, `golangci-lint` | (via golangci-lint) | Cyclomatic complexity reporting |

> **Note:** Go is the benchmark for language-bundled tooling. `go test`, `go fmt`, `go vet`, `go doc`, `go mod`, `-race`, `-bench`, `-cover`, and `-fuzz` all ship with the standard `go` binary. Third-party tools are needed only for aggregated linting and the debugger.

---

### B.4 Rust

Rust's toolchain, delivered via `cargo`, is the closest to Go in terms of batteries-included quality and the most ergonomic for a compiled language.

| Category | Tool(s) | Command | Notes |
|----------|---------|---------|-------|
| Runtime / REPL | `evcxr` | `evcxr` | Third-party; reasonable quality |
| Syntax / compile | `cargo check` | `cargo check` | Type-checks without linking; very fast |
| Linting | `cargo clippy` | `cargo clippy -- -D warnings` | Ships in rustup; 700+ lints; highly actionable |
| Type checking | built-in | `cargo check` | Always; Rust's type system is the primary safety tool |
| Formatting | `rustfmt` | `cargo fmt` | Ships with rustup; canonical; enforced in most projects |
| Test runner | `cargo test` | `cargo test` | Ships with cargo; captures output; parallel |
| Single test | `cargo test` | `cargo test test_name` | String filter on test names |
| Test watcher | `cargo watch` | `cargo watch -x test` | Watches source; reruns on change |
| Coverage | `cargo tarpaulin`, `cargo llvm-cov` | `cargo tarpaulin` | LLVM-based; line + branch; lcov output |
| Benchmarking | `cargo bench`, `criterion` | `cargo bench` | `criterion` gives statistical analysis |
| Profiling | `cargo flamegraph`, `samply` | `cargo flamegraph` | Generates SVG flame graphs |
| Debugging | `rust-gdb`, `rust-lldb`, `CodeLLDB` | `rust-gdb target/debug/app` | IDE-integrated via DAP |
| Documentation | `cargo doc` | `cargo doc --open` | Extracts `///` doc comments; runs doctests |
| Dependency mgmt | `cargo` | `cargo add serde` | `Cargo.lock`; deterministic; audit-able |
| Build | `cargo build` | `cargo build --release` | Incremental; cross-compilation |
| Fixture mgmt | `rstest`, `proptest` | `#[rstest]` attribute | Parameterized tests; property-based testing |
| Fuzzing | `cargo fuzz` | `cargo fuzz run` | LibFuzzer integration |
| Security scan | `cargo audit` | `cargo audit` | Checks advisory database for vulnerable deps |
| Pre-commit hooks | `cargo fmt --check` + `cargo clippy` | (via `.pre-commit-config.yaml`) | Standard practice |
| CI script | GitHub Actions + `cargo` | `cargo fmt --check && cargo clippy && cargo test` | Standard three-step pipeline |

---

### B.5 Java

Java has the most mature and enterprise-focused toolchain, with build systems that can feel heavyweight but provide comprehensive lifecycle management.

| Category | Tool(s) | Command | Notes |
|----------|---------|---------|-------|
| Runtime / REPL | `jshell` | `jshell` | Ships with JDK since Java 9; reasonable REPL |
| Syntax / compile | `javac`, `maven`, `gradle` | `mvn compile` | Compilation is syntax + type checking |
| Linting (style) | `Checkstyle`, `PMD` | `mvn checkstyle:check` | Rule-based style enforcement; Google/Sun rules |
| Linting (logic) | `SpotBugs`, `PMD`, `Error Prone` | `mvn spotbugs:check` | Detects null dereferences, resource leaks, etc. |
| Type checking | built-in | `javac` | Strong static typing; checked at compile time |
| Formatting | `google-java-format`, `Spotless` | `mvn spotless:apply` | Plugin-driven; enforces Google Java style |
| Test runner | `JUnit 5`, `TestNG` | `mvn test` | Industry standard; rich annotations |
| Single test | `Maven Surefire` | `mvn test -Dtest=MyTest#myMethod` | Class + method filter |
| Test watcher | `JUnit Platform`, `fizzed-watcher` | (limited native support) | Less ergonomic than other ecosystems |
| Coverage | `JaCoCo` | `mvn jacoco:report` | Line + branch + complexity; HTML + XML |
| Benchmarking | `JMH` | (annotation-based) | JVM Microbenchmark Harness; industry standard |
| Profiling | `JProfiler`, `async-profiler`, `JFR` | `jfr print recording.jfr` | JFR ships with JDK; async-profiler is excellent |
| Debugging | `jdb`, IDE debuggers | `jdb` | JDWP protocol; universal IDE support |
| Documentation | `Javadoc` | `mvn javadoc:javadoc` | Ships with JDK; standard `/** */` format |
| Dependency mgmt | `Maven`, `Gradle` | `mvn dependency:tree` | `pom.xml` / `build.gradle`; central repository |
| Build | `Maven`, `Gradle`, `Bazel` | `mvn package` | Full lifecycle management |
| Fixture mgmt | `JUnit @BeforeEach`, `DBUnit` | `@BeforeEach void setup()` | Scoped; `@Nested` for grouping |
| Mock/stub | `Mockito`, `EasyMock` | `@Mock MyService svc` | Industry-standard mocking framework |
| Static analysis | `SonarQube`, `Error Prone` | `mvn sonar:sonar` | Enterprise-grade; technical debt tracking |
| Security scan | `OWASP Dependency-Check` | `mvn dependency-check:check` | CVE database scanning |
| Pre-commit hooks | `Maven enforcer`, `Checkstyle` | (via Maven lifecycle) | Bound to `validate` phase |
| CI script | `mvn verify` | `mvn clean verify` | Runs compile + test + check + package |

---

## Appendix C: What Ships with YottaDB (Foundation Runtime)

Before assessing gaps, it is important to inventory what YottaDB — the open-source M runtime used as this project's foundation — already provides. Many developers are unaware of the full scope of YottaDB's built-in utilities. These vendor tools are used directly throughout the toolchain; they are not wrapped or renamed.

### C.1 Runtime and Interactive Tools

| Tool | Invocation | Description |
|------|-----------|-------------|
| `ydb` / `mumps` | `$YDB_DIST/ydb` | Main runtime. Enters interactive direct-mode when invoked without `-run`. Accepts MUMPS commands interactively. |
| `%XCMD` | `ydb -run %XCMD "code"` | Execute a MUMPS code string and exit. The foundation of all shell wrappers. |
| Direct mode | `ydb` (interactive) | REPL-like mode: type MUMPS commands, see results. No history, no completion. |
| `ZCOMPILE` | `ydb -run %XCMD "zcompile \"file.m\""` | Compile a routine to object code (`.m` → `.o`). Reports syntax errors. Used by `ycheck`. |
| `ZLINK` | in-process | Dynamically load a compiled routine. Happens automatically on first call. |

### C.2 MUPIP — Database Management Utility

`mupip` is YottaDB's most powerful and underused utility. It operates on the database files directly and is the closest thing M has to a database administration toolkit.

| Subcommand | Description | Dev Relevance |
|-----------|-------------|---------------|
| `mupip extract` | Export globals to a portable text file (ZWR or GO format) | **High** — enables fixture export, backup before tests, diff between runs |
| `mupip load` | Import globals from ZWR/GO format | **High** — enables fixture loading, restoring known test state |
| `mupip integ` | Verify database file structural integrity | Medium — useful after crashes or unexpected exits |
| `mupip backup` | Backup live database to a file | Medium — snapshot before risky operations |
| `mupip restore` | Restore from a backup | Medium — reset to snapshot |
| `mupip size` | Report node counts and storage statistics for all globals | **High** — global size reporting; equivalent of `du` for the database |
| `mupip reorg` | Compact and reorganize database blocks | Low (maintenance) |
| `mupip rundown` | Clean up after crashed processes (remove stale locks, shared memory) | Medium — critical after crashes |
| `mupip journal` | Manage journal/WAL files | Low (operations) |
| `mupip set` | Modify database parameters (block size, extension size, etc.) | Low (setup) |
| `mupip trigger` | Manage YottaDB triggers (code that fires on global updates) | Medium — triggers are an advanced feature |
| `mupip freeze` | Freeze/unfreeze database updates | Low |
| `mupip replicate` | Configure primary/secondary replication | Low (operations) |

> **Key insight:** `mupip extract` and `mupip load` are the foundation of any fixture management system. They are already present but unused in most development workflows.

### C.3 Auxiliary Utilities

| Tool | Description |
|------|-------------|
| `gde` (Global Directory Editor) | Interactive tool to configure which globals live in which database files. Used at setup, rarely during development. |
| `lke` (Lock Examination) | Inspect and forcibly clear `LOCK` entries held by any process. Critical when a crashed process leaves locks held. |
| `dse` (Database Structure Editor) | Low-level block-by-level database editor. Dangerous — only for recovery scenarios. |

### C.4 MUMPS Intrinsic Debugging Commands

These commands are available within any MUMPS routine or interactive session:

| Command / Function | Description |
|-------------------|-------------|
| `ZSHOW "V"` | Print all local variables and their values |
| `ZSHOW "G"` | Print all global variable references |
| `ZSHOW "L"` | Print all currently held locks |
| `ZSHOW "D"` | Print all open devices |
| `ZSHOW "B"` | Print all ZBREAK breakpoints |
| `ZSHOW "S"` | Print the current call stack |
| `ZSHOW "A"` | Print everything above |
| `ZWRITE var` | Print a variable in MUMPS `SET` syntax (full subtree) |
| `ZPRINT label^routine` | Print source code of a label or entire routine |
| `ZBREAK label` | Set a breakpoint at a label |
| `ZBREAK label:"condition"` | Conditional breakpoint |
| `ZCONTINUE` | Resume execution after a ZBREAK halt |
| `ZSTEP INTO` | Step into the next line |
| `ZSTEP OVER` | Step over a DO call |
| `ZSTEP OUTOF` | Step out of current routine |
| `ZGOTO level:label` | Unwind stack to level and jump to label |
| `$STACK(n,"MCODE")` | Source code of call at stack level n |
| `$STACK(n,"PLACE")` | Routine+label+offset of call at stack level n |
| `$ZPOSITION` | Current routine and label+offset |
| `$ZTRAP` | YDB-specific error trap (alternative to `$ETRAP`) |

### C.5 Percent-Sign Utility Routines

These ship with YottaDB and live in `$YDB_DIST`:

| Routine | Description |
|---------|-------------|
| `%GO` | Export one or more globals to a file in GO (sequential) format |
| `%GI` | Import globals from a GO-format file |
| `%GSEL` | Interactive global name selection utility |
| `%RD` | Routine directory — list all compiled routines |
| `%RSEL` | Routine selector — interactive search through routines |
| `%ZDATE` | Date/time formatting utility |
| `%ZCRC` | CRC checksum computation |
| `%ZMVALID` | Validate that a string is a legal MUMPS variable name |
| `%XCMD` | Execute a command string (used by shell wrappers) |
| `%ZTRIGGER` | Trigger management interface |

---

*End of gap-analysis-and-remediation-strategy document.*
