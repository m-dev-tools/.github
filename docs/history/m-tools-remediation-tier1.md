# M Tools Remediation - Closing the Inner-Loop Gaps (Tier 1)


> **History**  For the *current* shape of the org, start at [`profile/README.md`](../../profile/README.md).

**Document type:** Strategic plan, scoped
**Scope:** The five Tier 1 developer-toolchain gaps in the M (MUMPS) ecosystem
**Audience:** Anyone planning, coordinating, or contributing to M-language tooling work
**Companion documents:**
- [m-tool-gap-analysis.md](m-tool-gap-analysis.md) — the broader cross-engine gap analysis (this doc focuses on its [§8 Tier 1](m-tool-gap-analysis.md#8-rank-ordered-developer-impact-where-to-invest-first))
- [gap-analysis-and-remediation-strategy.md](gap-analysis-and-remediation-strategy.md) — the wider phased remediation plan (this doc is the focused Tier 1 extract)

---

## Table of Contents

- [1. The Tier 1 gaps](#1-the-tier-1-gaps)
- [2. Foundation already in place](#2-foundation-already-in-place)
  - [2.1 `m-standard` — the language reference](#21-m-standard--the-language-reference)
  - [2.2 `tree-sitter-m` — the parser](#22-tree-sitter-m--the-parser)
  - [2.3 VistA — the corpus](#23-vista--the-corpus)
- [3. Strategy: incremental remediation](#3-strategy-incremental-remediation)
  - [3.1 Principles](#31-principles)
  - [3.2 The sequence](#32-the-sequence)
  - [3.3 What ships at each step](#33-what-ships-at-each-step)
  - [3.4 Portability across M implementations](#34-portability-across-m-implementations)
  - [3.5 Validation gates](#35-validation-gates)
  - [3.6 Out of scope (intentional)](#36-out-of-scope-intentional)
- [4. Why Tier 1 first](#4-why-tier-1-first)
- [5. Design decisions](#5-design-decisions)
  - [5.1 IRIS adapter ownership](#51-iris-adapter-ownership)
  - [5.2 `^XINDEX` integration](#52-xindex-integration)
  - [5.3 Performance baselining](#53-performance-baselining)
  - [5.4 Editor integration cadence](#54-editor-integration-cadence)
  - [5.5 Versioning across `m-standard` updates](#55-versioning-across-m-standard-updates)

---

## 1. The Tier 1 gaps

The [§8 ranking in m-tool-gap-analysis.md](m-tool-gap-analysis.md#8-rank-ordered-developer-impact-where-to-invest-first) identifies five Tier 1 capabilities — the development inner loop — that are **MAJOR common gaps** across both major M engines (IRIS, YottaDB) for pure MUMPS code. They are the **transformative** tools, validated in [§8.5](m-tool-gap-analysis.md#85-validation-empirical-grounding-for-the-ranking) against DORA / *Accelerate* research and the broader literature on developer productivity.

| # | Capability | Why it's Tier 1 |
|---|------------|-----------------|
| 1 | **Test runner** | Foundation. Without it, no quality activity is possible — refactoring is unsafe, CI has nothing to gate on, coverage cannot be measured. |
| 2 | **Linter (logic)** | Catches whole categories of bugs — unused vars, unreachable code, missing `QUIT`s, undefined labels — *at edit time*, before they reach a test or production. |
| 3 | **Formatter** | Eliminates style debate; enforces canonical layout that downstream tools (linters, AST analysers) can rely on. Runs invisibly on every save in mainstream languages. |
| 4 | **Single-test selection** | Without it, the test loop is "run all tests, scroll for the relevant failure." With it, the loop is sub-second. The difference compounds over a workday. |
| 5 | **Test watcher** | Auto-rerun on save; sub-second feedback. Once a developer has experienced this loop (Rust's `cargo watch`, Python's `pytest-watch`), going back is painful. |

These five are not five separable tools but a single integrated **inner loop**: edit → save → format → lint → run-affected-test → see result. Filling all five gaps closes the highest-leverage portion of the M developer-experience deficit; any one in isolation delivers a fraction of the value.

---

## 2. Foundation already in place

Tier 1 is feasible *now* because three pre-requisites are already shipped. These are not aspirations — they are tagged, tested, machine-readable artefacts that downstream tools can consume directly.

### 2.1 [`m-standard`](https://github.com/rafael5/m-standard) — the language reference

A machine-readable, vendor-neutral inventory of the M language surface, reconciled across the Annotated M Standard (ISO 11756), YottaDB documentation, IRIS documentation, and the VA SAC / XINDEX rule set:

- **949 keyword forms** (commands, intrinsic functions, intrinsic special variables, operators, pattern codes) with provenance flags (`in_anno`, `in_ydb`, `in_iris`).
- Three layered standards: **Pragmatic** (81 tokens — runs unmodified on both YDB and IRIS), **VA SAC-clean**, and **Operational** (58 tokens — Pragmatic ∩ SAC).
- A `grammar-surface.json` artefact purpose-built for parser generators and tools to consume.
- All sources offline-replicated; the build is byte-deterministic; **9 validation gates** passing on every CI run.

This is the **vocabulary** every Tier 1 tool needs: which tokens are valid, which are pragmatic, which are SAC-compliant, what provenance each carries.

### 2.2 [`tree-sitter-m`](https://github.com/rafael5/tree-sitter-m) — the parser

A production tree-sitter grammar for M, generated from `m-standard`'s grammar-surface JSON:

- **99.06% clean parse on the full 39,330-routine VistA corpus**; **100% on clinical packages**.
- 10,000-line synthesised routine parses in **78.6 ms**.
- 110 corpus tests + 19 lib tests + 347/347 keyword-coverage triples passing in CI.
- Bindings scaffolded for **Node / Rust / Python / Go**; publishing to npm / crates.io / PyPI / Go-modules in progress.

This is the **AST** every Tier 1 tool needs. A formatter walks it to produce canonical text. A linter visits its nodes with rule predicates. A test discoverer searches for `tXxx` test labels in it. Without this, every tool would have to re-implement an M parser from scratch — a multi-year effort that has been the historical blocker for M tooling.

### 2.3 VistA — the corpus

The U.S. Department of Veterans Affairs' VistA system — distributed publicly via [`WorldVistA/VistA-M`](https://github.com/WorldVistA/VistA-M) — is **~40,000 routines of pure ANSI MUMPS**, in active production use for decades. It is the **largest, most diverse open-source M codebase** in existence and the gold-standard real-world test corpus.

Every Tier 1 tool can be:

- **Built against it.** VistA exercises every hard-to-parse M idiom (dot-blocks, naked references, postconditionals, indirection, edge-case parameter passing). A tool that handles VistA handles real-world M.
- **Validated against it.** A formatter that doesn't round-trip cleanly on VistA isn't ready. A linter that produces 40,000 false positives isn't ready. A test discoverer that misses VistA's `tXxx` conventions isn't ready.
- **Demonstrated on it.** VistA is the showcase: *"this tool runs on the largest M codebase in production today."*

VistA is the difference between toy tooling and tooling proven at scale. `tree-sitter-m` already validates against it (39,330 routines, 99.06% clean); every Tier 1 tool inherits that validation harness.

---

## 3. Strategy: incremental remediation

### 3.1 Principles

1. **Build in dependency order.** A formatter unblocks the linter (linter rules can assume canonical layout). A test runner unblocks single-test selection and the watcher. Build prerequisites first.
2. **Ship each tool independently.** No tool waits for the next; each is usable on the day it's released.
3. **Validate against VistA on every release.** A Tier 1 tool that isn't tested on the 40,000-routine corpus is unfinished work.
4. **Build on YottaDB; design for portability.** YottaDB is AGPL-3.0 — fully open-source, fully reproducible CI, no licence negotiation, no per-developer seat costs. But the tools are **source-level**: they consume `.m` files via `tree-sitter-m`, not via any engine-specific interface. They run on any conformant M engine simply by running on the source.
5. **No engine lock-in in the binding choice.** Each tool exposes a stable CLI; engine integration is a thin shell wrapper. A Python user with `tree-sitter-m` Python bindings can run the formatter without YottaDB; an IRIS shop can run it the same way.

### 3.2 The sequence

| Step | Tool | Depends on | Notes |
|------|------|-----------|-------|
| 1 | **Formatter** (`m fmt`) | tree-sitter-m AST + lossless byte-range pretty-printer | Build first: every later tool benefits from canonical layout. **Idempotent** (`m fmt | m fmt` produces no further change). `--check` mode for CI. |
| 2 | **Linter — logic** (`m lint --logic`) | tree-sitter-m AST visitor + rule predicates | Catches missing `QUIT`, unreachable code, undefined labels, unused locals, naked-reference hazards. Pluggable rules; configurable via `m.toml`. JSON / TAP output for editor integration. |
| 3 | **Test runner** (`m test`) | YottaDB runtime + parser-aware `tXxx` test discovery | The project already ships [`ytest`](../bin/ytest); the strategic step is to make it **parser-aware** (test discovery via tree-sitter-m, not regex), portable across engines via thin adapters, and TAP-13 compliant out of the box. |
| 4 | **Single-test selection** | (folded into test runner) | `m test <suite> <label>`; `m test --pattern '...'`. Already prototyped in `ytest <suite> <label>`. |
| 5 | **Test watcher** (`m watch`) | Formatter + linter + test runner | Auto-rerun on save. Smart routing — recompile + test only the affected suites. The project already ships [`ytest-watch-smart`](../bin/ytest-watch-smart) as a foundation; the parser-aware version replaces stat-based polling with AST-derived dependency tracking. |

### 3.3 What ships at each step

**After Step 1 (formatter):**
- Every contributor in the M ecosystem can apply canonical layout to any `.m` file with a single command.
- VistA codebases can adopt a consistent style without manual re-indenting.
- Pre-commit hooks gain a meaningful `m fmt --check` gate.
- Code reviews stop arguing about whitespace.

**After Step 2 (linter — logic):**
- Whole categories of bugs caught at edit time, not at runtime.
- Pre-commit hook gains an `m lint --logic` gate.
- VistA-specific rule sets can be enabled via SAC compliance level (driven from `m-standard`'s SAC mappings).
- Editor integration via JSON output makes diagnostics first-class in VS Code, Vim, Emacs.

**After Step 3+4 (test runner with single-test selection):**
- Test discovery is parser-aware (no false-positive label detection).
- Tests run on any M engine via adapters; YottaDB is primary, IRIS adapter follows.
- `m test <suite> <label>` is the supported, documented invocation.
- TAP-13 output integrates with mainstream CI dashboards.

**After Step 5 (test watcher):**
- The full inner loop: edit → save → format → lint → run-affected-test → instant feedback.
- The first time the M ecosystem has the modern fast-feedback workflow that DORA / *Accelerate* research identifies as foundational.

### 3.4 Portability across M implementations

Each Tier 1 tool is **source-level by construction**:

| Tool | Engine touchpoint | Portability story |
|------|-------------------|-------------------|
| Formatter | None | Operates on `.m` text via tree-sitter-m. Engine-independent. |
| Linter (logic) | None | Operates on the AST. Engine-independent. |
| Test discovery | None | Parser-aware label scan. Engine-independent. |
| Test execution | Local M engine CLI | Pluggable adapter: YottaDB primary (`ydb -run ^TESTRUN`), IRIS via `iris session`, GT.M via `mumps -run`, etc. |
| Test watcher | Filesystem + test execution | Engine-independent orchestrator; only the test-execution adapter is engine-specific. |

The integration boundary with the engine is *only* the test-execution adapter — everything else operates on `.m` source files via the parser. This makes each tool **portable to IRIS-based VistA, GT.M, or any other conformant M engine** with **only a small adapter** for that engine's CLI. The bulk of the implementation is engine-neutral.

YottaDB is the primary build / development engine for two pragmatic reasons:

1. **Open-source reproducibility.** AGPL-3.0 means anyone can install, run, and contribute without licence negotiation. CI runs in any standard container.
2. **Mature C API.** `libyottadb.so` is a stable extensibility surface; foreign-language bindings (Go, Python, Rust, Node.js, Lua, Perl) make it straightforward to embed engine calls in tool implementations when needed (see [m-tool-gap-analysis.md §4.4](m-tool-gap-analysis.md#44-foreign-language-integration-embedded-language-vs-embedded-database) for the architecture rationale).

But "built on YottaDB" never means "locked to YottaDB." Each tool's parser-side work is engine-neutral; only the test-execution shim varies by engine.

### 3.5 Validation gates

Before any Tier 1 tool is considered production-ready, it must pass:

1. **VistA round-trip.** Runs cleanly on the full 40,000-routine [VistA-M](https://github.com/WorldVistA/VistA-M) corpus with no false-positive failures (formatter), no false-positive lints (linter), or no missed tests (discovery).
2. **Cross-engine smoke test.** The test runner adapters work on YottaDB (primary) and IRIS (`iris session` adapter); no engine-specific behaviours leak into the source-level tools.
3. **CI integration.** Each tool is wired into the project's own CI as a self-test (`make ci` runs the tool on the project's own routines). Dogfooding is the first acceptance test.
4. **Performance ceiling.** Each tool runs the full VistA corpus inside a documented budget — first-pass targets: formatter ≤ 60 s, linter ≤ 120 s on a current developer laptop. Performance-budgeting from day one prevents the "works on small examples but unusable at scale" failure mode.

### 3.6 Out of scope (intentional)

The Tier 1 plan does **not** cover:

- **Coverage** (line / branch) — Tier 2 in [§8](m-tool-gap-analysis.md#8-rank-ordered-developer-impact-where-to-invest-first).
- **Documentation generation** — Tier 3.
- **Dependency management** — Tier 3, blocked on a manifest-format design in `m-standard`.
- **IDE / DAP integration** — Tier 2; substantial engineering on its own.
- **IRIS ObjectScript (IOS) tooling** — out of scope; IOS is a separate language ([m-tool-gap-analysis.md §4.1.1](m-tool-gap-analysis.md#411-iris-objectscript-ios-what-it-is-and-why-it-isnt-ansi-standard-mumps)) with its own toolchain.

These are excluded to keep the Tier 1 plan focused. Each is sequenced separately in [gap-analysis-and-remediation-strategy.md → Addendum B](gap-analysis-and-remediation-strategy.md#addendum-b-prioritized-sequence-of-remediation-post-parser).

---

## 4. Why Tier 1 first

The case for Tier 1 primacy has three legs, all already established in the companion analysis:

**1. Empirical research on developer productivity.** [m-tool-gap-analysis.md §8.5](m-tool-gap-analysis.md#85-validation-empirical-grounding-for-the-ranking) cites primary sources:

- Forsgren, Humble & Kim (2018), *Accelerate*, identifies test automation as among the technical capabilities most strongly correlated with high software-delivery performance (DORA programme, 23,000+ respondents).
- Sadowski et al. (2018), [*"Lessons from Building Static Analysis Tools at Google"*](https://cacm.acm.org/research/lessons-from-building-static-analysis-tools-at-google/) (CACM 61(4)) — Tricorder static analysis prevents hundreds of bugs per day from entering Google's codebase.
- Vasilescu et al. (2015), [*"Quality and productivity outcomes relating to continuous integration in GitHub"*](https://web.cs.ucdavis.edu/~filkov/papers/pr_soc_lan.pdf) (FSE 2015) — CI users merge PRs significantly faster and find more bugs.
- Stack Overflow Annual Developer Survey: Ruff (84% admired) and Cargo (83% admired) — top-of-survey tools that bundle the Tier 1 capabilities.

**2. Cross-engine consolidation.** [§7 in m-tool-gap-analysis.md](m-tool-gap-analysis.md#7-consolidated-gap-analysis) shows that **all five Tier 1 capabilities are MAJOR common gaps** — both IRIS and YottaDB ship **None** for MUMPS code. **A single source-level tool, built on a shared parser foundation, fills the gap on every M engine simultaneously.** That economy of leverage is the strategic case for treating M as a portable language with portable tooling, not as a vendor-locked feature.

**3. The 40,000-routine VistA reality.** [§6.1 / §6.2](m-tool-gap-analysis.md#6-the-real-question-developer-experience-for-a-legacy-mumps-codebase) of m-tool-gap-analysis frames the real-world stakes: a VistA codebase has effectively zero benefit from IRIS's IOS-targeted tooling (the wrappers don't reach the MUMPS code) and effectively zero benefit from YottaDB's runtime-first investment (the developer-experience layer simply isn't there). Tier 1 is the work that closes the gap *for the actual M codebase that matters most*.

---

## 5. Design decisions

The five questions raised during initial planning now have working resolutions. They remain provisional — they may be revisited as work proceeds — but the project starts with these decisions in place.

### 5.1 IRIS adapter ownership

**Decision: defer indefinitely. Tier 1 ships without an IRIS adapter.**

InterSystems' demonstrated trajectory is to promote IRIS ObjectScript (IOS) as the developer-facing language and to scrub mention of MUMPS where possible — the 2018 Caché → IRIS rename was a marketing exercise, and IOS is a proprietary wrapper sitting *between* IRIS users and the MUMPS substrate. The vendor is not investing in MUMPS-side developer experience and has shown no interest in doing so. (See [m-tool-gap-analysis.md §1.2 naming history](m-tool-gap-analysis.md#naming-history-intersystems-mumps--caché-objectscript--iris-objectscript-ios) and [§4.1.3](m-tool-gap-analysis.md#413-iris-tooling-by-file-scope-and-language) for the evidence.)

Building and maintaining an IRIS adapter would require coordinating with a vendor whose strategic interests are misaligned with the goals of this work. The pragmatic choice is to invest the same effort in YottaDB and the source-level tooling — which ports automatically to any conformant M engine — and let an IRIS adapter remain a community contribution if one ever emerges. The source-level tools (formatter, linter, test discovery) are unaffected by this decision; they run on `.m` files via the parser, regardless of which engine the runtime side targets.

### 5.2 `^XINDEX` integration

**Decision: import the `^XINDEX` rule set as the linter's baseline; validate against XINDEX on the VistA corpus; then expand. Expose rule-family selection via a `--rules` toggle.**

Mechanics:

- The Tier 1 linter's first rule pack **replicates the XINDEX rule set**, mapping each XINDEX check to an `m lint` rule with stable IDs (e.g., `M-XINDX-001`, `M-XINDX-002`, …).
- Running `m lint --rules xindex` on the VistA corpus must reproduce XINDEX's findings — a hard validation gate ("if XINDEX flags it, we flag it; if XINDEX doesn't flag it, we don't").
- After parity, `m lint` extends with rules that XINDEX does not cover: parser-aware checks XINDEX cannot do (e.g., naked-reference hazards in nested dot blocks), modern lint categories (dead-code analysis, unused-locals), SAC compliance levels, and project-specific rules.
- A `--rules` toggle selects the rule family at invocation time:
  - `--rules xindex` — XINDEX-equivalent only (legacy compatibility mode)
  - `--rules sac` — VA SAC compliance set (driven from `m-standard`'s SAC mappings)
  - `--rules all` — everything the linter knows
  - `--rules <custom>` — per-project profiles defined in `m.toml`

**Rationale.** XINDEX's rule set encodes decades of accumulated VA / VistA experience about what to catch in M code. Replicating it gives the linter immediate credibility on the VistA corpus, makes the migration path frictionless ("disable `^XINDEX`, enable `m lint --rules xindex`, expect the same findings"), and provides a baseline from which to expand. The pattern of "absorb the predecessor, then extend" is well-precedented — ESLint absorbed JSHint / JSLint rules; Ruff absorbed flake8 / isort / pyupgrade.

### 5.3 Performance baselining

**Decision: TBD. Resolved by measurement once the tools exist.**

The 60 s / 120 s budgets in §3.5 are first-pass estimates. Empirical baselining will happen once each tool exists and can be measured against the 40,000-routine VistA corpus on representative hardware. If the budgets prove unrealistic, they will be revised based on actual measurements; the *requirement* of having a documented budget remains, even if the specific numbers change. Performance regressions versus the budget should be a CI-blocking event from the first release.

### 5.4 Editor integration cadence

**Decision: JSON and LSP-compatible output from the very first release of each tool. VS Code is the primary editor target.**

Mechanics:

- Each tool ships with a `--format=json` flag from the first release. The JSON output schema is documented and held stable across patch versions.
- An **LSP server** is developed alongside the tool implementation, not bolted on after. The LSP wrapper consumes the tool's own JSON output internally — so editor integration and CLI use share a single source of truth for diagnostics, formatting, and test results.
- A **VS Code extension** is the primary editor surface: linter diagnostics, format-on-save (`m fmt`), test-runner integration via the VS Code Test Explorer API. Vim / Emacs / JetBrains LSP clients work without additional effort once the LSP server exists.

**Rationale.** Adding LSP / IDE support after the fact is materially more expensive than designing for it upfront — it requires retrofitting tool internals to expose structured output and support partial / incremental computation. VS Code is the dominant editor in contemporary developer surveys ([Stack Overflow Developer Survey 2024](https://survey.stackoverflow.co/2024/) places it at the top), and it is the editor most likely to be installed by the M developers who would benefit from this work. Designing for VS Code first incidentally serves all other LSP-aware editors.

### 5.5 Versioning across `m-standard` updates

**Decision: each tool pins to a specific `m-standard` snapshot identified by the generation date of the `m-standard` artefact the tool was built against.**

Mechanics:

- Each tool's release manifest records the `m-standard` generation date (e.g., `m-standard@2025-01-15`).
- Upgrading a tool to a newer `m-standard` snapshot is a **deliberate operation at release time**, accompanied by regression tests against the VistA corpus to confirm no parsing or rule-evaluation drift.
- Tools do not float against a moving `m-standard` — that would compromise reproducibility (a `m fmt` run today must produce the same output as a `m fmt` run last year against the same source).

**Rationale.** Pinning by date is simpler than version-range constraints, and `m-standard`'s build is byte-deterministic — so a date is sufficient to identify an exact snapshot. Reproducibility is more important than being on the absolute newest grammar surface; users who need new tokens upgrade explicitly.

---

*End of m-tooling-tier1 document.*
