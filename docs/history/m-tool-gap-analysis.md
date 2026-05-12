# M Tools — Gap Analysis (Vendor-Neutral)

> **Archived snapshot.** Imported verbatim from [`m-tools`](https://github.com/rafael5/m-tools) — source commit [`16fe3f7`](https://github.com/rafael5/m-tools/commit/16fe3f7dc6982070809cd1d8290d01fedc5905ac) (2026-04-27), at the point that repo seeded the rest of the m-dev-tools org (it has since been moved out of the org back to its original author's account). Preserved for the design rationale behind the m-dev-tools ecosystem (Go/Rust/Python toolchain analogy that drove `m-cli`'s CLI ergonomics). **Not maintained.** For the *current* shape of the org, start at [`profile/README.md`](../../profile/README.md).

**Document type:** Reference / strategic planning
**Scope:** Developer toolchain for the M (MUMPS) programming language across all current implementations
**Audience:** Anyone evaluating, building for, or contributing to the M ecosystem
**Companion document:** [gap-analysis-and-remediation-strategy.md](gap-analysis-and-remediation-strategy.md) — the YottaDB-bound remediation roadmap that consumes this analysis

---

## Table of Contents

- [1. Introduction](#1-introduction)
  - [1.1 What is M, and why does its toolchain matter?](#11-what-is-m-and-why-does-its-toolchain-matter)
  - [1.2 The two main current implementations](#12-the-two-main-current-implementations)
  - [1.3 What "M tools" means in this document](#13-what-m-tools-means-in-this-document)
- [2. The Gold Standard — Top 5 Language Toolchains](#2-the-gold-standard--top-5-language-toolchains)
  - [2.1 Python](#21-python)
  - [2.2 JavaScript / TypeScript](#22-javascript--typescript)
  - [2.3 Go](#23-go)
  - [2.4 Rust](#24-rust)
  - [2.5 Java](#25-java)
- [3. The M Language Surface Across Implementations](#3-the-m-language-surface-across-implementations)
  - [3.1 Concept-by-concept reconciliation](#31-concept-by-concept-reconciliation)
  - [3.2 What's portable vs what isn't](#32-whats-portable-vs-what-isnt)
  - [3.3 Multi-vendor extensions (non-ANSI but in both engines)](#33-multi-vendor-extensions-non-ansi-but-in-both-engines)
- [4. The M Development Toolchain Across Implementations](#4-the-m-development-toolchain-across-implementations)
  - [4.1 InterSystems IRIS](#41-intersystems-iris)
    - [4.1.1 IRIS ObjectScript (IOS): what it is, and why it isn't ANSI standard MUMPS](#411-iris-objectscript-ios-what-it-is-and-why-it-isnt-ansi-standard-mumps)
    - [4.1.2 File extensions in IRIS source code](#412-file-extensions-in-iris-source-code)
    - [4.1.3 IRIS tooling, by file scope and language](#413-iris-tooling-by-file-scope-and-language)
  - [4.2 YottaDB](#42-yottadb)
  - [4.3 Common across both engines](#43-common-across-both-engines)
  - [4.4 Foreign-language integration: "embedded language" vs "embedded database"](#44-foreign-language-integration-embedded-language-vs-embedded-database)
  - [4.5 Polyglot routines vs C-API separation: a quality / maintainability analysis](#45-polyglot-routines-vs-c-api-separation-a-quality--maintainability-analysis)
- [5. Summary Table: MUMPS-vs-MUMPS — Gold Standard, IRIS, YottaDB, VA/Community](#5-summary-table-mumps-vs-mumps--gold-standard-iris-yottadb-vacommunity)
  - [5.1 Where both engines fall short of the gold standard](#51-where-both-engines-fall-short-of-the-gold-standard)
  - [5.2 Where the engines diverge most sharply](#52-where-the-engines-diverge-most-sharply)
  - [5.3 What the MUMPS-only matrix reveals](#53-what-the-mumps-only-matrix-reveals)
- [6. The Real Question: Developer Experience for a Legacy MUMPS Codebase](#6-the-real-question-developer-experience-for-a-legacy-mumps-codebase)
  - [6.1 The IRIS-based VistA scenario](#61-the-iris-based-vista-scenario)
  - [6.2 The YottaDB-based VistA scenario](#62-the-yottadb-based-vista-scenario)
  - [6.3 Side-by-side summary](#63-side-by-side-summary)
  - [6.4 The bottom line](#64-the-bottom-line)
- [7. Consolidated Gap Analysis](#7-consolidated-gap-analysis)
- [8. Rank-Ordered Developer Impact: Where to Invest First](#8-rank-ordered-developer-impact-where-to-invest-first)

---

## 1. Introduction

### 1.1 What is M, and why does its toolchain matter?

M (originally MUMPS — Massachusetts General Hospital Utility Multi-Programming System, ANSI X11.1, ISO 11756) is a high-level programming language with an integrated hierarchical key-value database. It has been in continuous production use since 1966 and underpins a disproportionate share of the world's healthcare IT — Epic Systems, MEDITECH, the U.S. Department of Veterans Affairs' VistA system, and others collectively store hundreds of millions of patient records in M databases.

Despite that operational footprint, the developer experience around M has received comparatively little tooling investment. Most modern software-development practices — unit testing, continuous integration, static analysis, code coverage, package management, automated formatting — emerged after M was already in widespread production use. As a result, the productivity tools that mainstream language communities take for granted are largely absent in the M world.

This document inventories the gap. It is deliberately **vendor-neutral**: it begins from the language standard and the cross-vendor reality, not from any single implementation's strengths or limitations. The companion document, [gap-analysis-and-remediation-strategy.md](gap-analysis-and-remediation-strategy.md), is the YottaDB-bound remediation strategy that builds on this analysis.

### 1.2 The two main current implementations

M is a standardised language with multiple historical and current implementations. Two implementations are in active production today and are the focus of this analysis:

| Implementation | Vendor | Licence | Notes |
|----------------|--------|---------|-------|
| **InterSystems IRIS** | InterSystems Corporation | Commercial / proprietary | The current product, branded as **IRIS** since 2018. *(See the **Naming history** note below the table.)* The runtime is MUMPS at its core. The primary developer-facing language is **IRIS ObjectScript (IOS)** — a proprietary superset of MUMPS that adds object-oriented classes, methods, embedded SQL, and embedded Python (see [§4.1.1](#411-iris-objectscript-ios-what-it-is-and-why-it-isnt-ansi-standard-mumps)). IOS is **not** ANSI standard MUMPS, and most IRIS tooling targets IOS classes (`.cls`) rather than `.m` MUMPS routines. |
| **YottaDB** | YottaDB LLC | AGPL-3.0 (open source) | A 2017 fork of FIS GT.M (the open-source M implementation that traces back to the same Massachusetts General codebase). M-only at its core; richer extensibility comes via a stable C API (`libyottadb`) that other languages bind to. |

Other implementations — FIS GT.M (the YottaDB ancestor, now in maintenance), MiniM, M21, Reference Standard M (RSM), MUMPS V1 — exist but are either retired, niche, or maintained on a different cadence; they are not covered in detail here.

#### Naming history: InterSystems MUMPS → Caché ObjectScript → IRIS ObjectScript (IOS)

InterSystems' technology has been continuously evolved for several decades; its **branding** has been changed twice in that time. Distinguishing the technology from the marketing layers is important for an accurate gap analysis:

1. **InterSystems MUMPS (ISM)** — late 1970s through the 1990s. A pure ANSI MUMPS implementation, more or less.
2. **Caché ObjectScript (COS)** — late 1990s onward. InterSystems built an object-oriented layer on top of ISM's MUMPS runtime — adding classes, methods, properties, embedded SQL, and a class-compilation phase — and named the resulting language **Caché ObjectScript**, abbreviated **COS**. The product itself was branded **Caché**. The MUMPS runtime remained underneath; COS code compiles down to MUMPS-shaped intermediate routines that the routine compiler then turns into object code.
3. **IRIS / "ObjectScript"** — 2018 onward. InterSystems rebranded the product from **Caché** to **IRIS**. *This was a marketing rename, not a technology change* — the engine, the class-compilation pipeline, and the language itself were all carried over. InterSystems scrubbed most mentions of "Caché" from its website and product surfaces, and now refers to the language simply as **"ObjectScript"** (without the "Caché" prefix). Technically, however, today's "ObjectScript" is **the same Caché ObjectScript** with the brand name removed.

For clarity in this document — and to disambiguate from Apple's iOS (which is an unrelated mobile operating system) — we use the term **IRIS ObjectScript (IOS)** when referring to InterSystems' current language. **IOS = Caché ObjectScript with the "Caché" prefix scrubbed.** Where context calls for it, we also use **COS** to refer to the historically-cumulative language (the pre- and post-rename forms are functionally equivalent), or just **ObjectScript** when the modifier doesn't add information.

**The MUMPS runtime under IOS is still MUMPS.** This is what the §5 matrix scores on: the IRIS column tracks what's available to a developer writing pure `.m` or pure-MUMPS `.mac` routines on IRIS — i.e., the developer who is not opting into the IOS class layer. IOS-specific tooling (the class compiler, `%UnitTest`, Documatic, IPM, etc.) is out of scope for the MUMPS-vs-MUMPS comparison; see [§4.1.1](#411-iris-objectscript-ios-what-it-is-and-why-it-isnt-ansi-standard-mumps).

### 1.3 What "M tools" means in this document

Two related things are inventoried below:

1. **The language surface** — commands, intrinsic functions, intrinsic special variables (ISVs), operators, and pattern codes that an M program can use. This is the input to any source-level tool (parser, linter, formatter, AST-based analyser) and is necessarily implementation-aware: a tool that promises portability has to know which features each engine implements.
2. **The development toolchain** — the editors, debuggers, test runners, linters, formatters, profilers, package managers, CI integrations, and other utilities that surround the language. This is where the gap against mainstream languages is most acute.

The data in [§3](#3-the-m-language-surface-across-implementations) is grounded in [`m-standard`](https://github.com/rafael5/m-standard), an integrated machine-readable reference that reconciles four primary sources (the Annotated M Standard / ISO 11756, the YottaDB documentation, the IRIS documentation, and the VA SAC / XINDEX rule set) into a unified data layer. All cross-engine counts cited below trace back to that reconciliation.

---

## 2. The Gold Standard — Top 5 Language Toolchains

The following tables document the toolchain available to developers in each of the five most widely used mainstream programming languages today. They establish the gold-standard reference against which the M ecosystem is measured in [§5](#5-summary-table-gold-standard-vs-iris-vs-yottadb).

These are the lived experience of developers who would need to transition to or work alongside M code. The tables are deliberately uniform in shape so they can be compared directly.

---

### 2.1 Python

Python's toolchain has matured significantly with the `ruff` era. The ecosystem prioritises speed of feedback and comprehensive static analysis.

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

### 2.2 JavaScript / TypeScript

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

### 2.3 Go

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

> **Note:** Go is the benchmark for language-bundled tooling. `go test`, `go fmt`, `go vet`, `go doc`, `go mod`, `-race`, `-bench`, `-cover`, and `-fuzz` all ship with the standard `go` binary.

---

### 2.4 Rust

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

### 2.5 Java

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

## 3. The M Language Surface Across Implementations

Before discussing toolchains, it is necessary to understand what the language itself looks like across implementations. A formatter, linter, or AST analyser has to know which features each engine implements; otherwise it cannot make portability claims.

The numbers in this section are drawn directly from [`m-standard`](https://github.com/rafael5/m-standard), which reconciles the Annotated M Standard (ISO 11756 / ANSI X11.1-1995), the YottaDB documentation tree, and the InterSystems IRIS documentation site into a unified per-concept inventory.

### 3.1 Concept-by-concept reconciliation

| Concept | Total catalogued | In ANSI standard | YottaDB implements | IRIS implements | Implemented by **both** |
|---------|------------------|------------------|--------------------|-----------------|-------------------------|
| **Commands** | 82 | 40 | 50 | 47 | 29 |
| **Intrinsic functions** | 159 | 28 | 60 | 119 | 26 |
| **Intrinsic special variables (ISVs)** | 82 | 17 | 65 | 42 | 26 |
| **Operators** | 17 | 16 | 17 | 16 | 16 |
| **Pattern codes** | 7 | 7 | 7 | 7 | 7 |

Two observations follow from the table:

1. **The ANSI core is small, and full coverage is partial in both engines.** Of the 40 ANSI commands, neither YottaDB nor IRIS implements all of them — 14 ANSI commands (mostly the `ASTART`/`ASTOP`/`AUNBLOCK`/`ASSIGN` async-event family) are absent in both. Conformance is "ANSI minus a few legacy bits, plus a large layer of extensions."
2. **IRIS extends the function library far more aggressively than YottaDB.** IRIS ships 93 intrinsic functions that YottaDB does not — `$BIT`, `$LISTBUILD`, `$LISTGET`, `$ZF`, `$ZHEX`, the `$WCHAR` family, and many more. YottaDB extends primarily through ISVs (39 YDB-only ISVs vs. 16 IRIS-only) and through its C-API.

### 3.2 What's portable vs what isn't

`m-standard` defines three layered standards beyond raw counts:

| Standard | Definition | Count |
|----------|------------|-------|
| **Pragmatic** | Token implemented by both YottaDB and IRIS | 81 |
| **VA SAC-clean** | Token permitted by VA Standards & Conventions / XINDEX | 65 rules / 171 per-name flags |
| **Operational** | Pragmatic ∩ SAC-clean — i.e., what runs unmodified on both engines AND passes the VA's static-analysis rules | 58 |

For a developer whose code must run on both engines, the language surface is roughly the **81 pragmatic** tokens. For a VistA developer it shrinks to **58 operational** tokens. The remaining ANSI commands — the parts of the standard that no engine implements — are dead surface that no portable program can use.

### 3.3 Multi-vendor extensions (non-ANSI but in both engines)

A small set of `Z*` tokens originated outside ANSI but were picked up by both major engines. These are de-facto cross-vendor extensions:

| Concept | Tokens implemented by YDB and IRIS but not in ANSI |
|---------|----------------------------------------------------|
| Commands | `ZBREAK`, `ZKILL`, `ZPRINT`, `ZWRITE` |
| Intrinsic functions | `$INCREMENT`, `$ZCONVERT`, `$ZDATE`, `$ZSEARCH`, `$ZWIDTH` |
| Intrinsic special variables | `$X`, `$Y`, `$ZA`, `$ZB`, `$ZEOF`, `$ZERROR`, `$ZHOROLOG`, `$ZIO`, `$ZJOB`, `$ZMODE`, `$ZTRAP`, `$ZVERSION` |

These are useful for a portability-minded toolchain because they expand the practical pragmatic surface from 81 to ~102 tokens — still well short of ANSI + every extension, but enough to cover most non-trivial diagnostic and I/O code.

---

## 4. The M Development Toolchain Across Implementations

This chapter inventories what each implementation provides for **developing** M code (as distinct from running it). The structure mirrors §2's gold-standard categories so the comparison in §5 can be a direct row-by-row match.

### 4.1 InterSystems IRIS

IRIS sits at the commercial end of the spectrum. Tooling is comprehensive but largely proprietary, web/IDE-centric, and gated by licensing. Crucially for an M-portability analysis, **most IRIS tooling targets IRIS ObjectScript / IOS classes (`.cls`) — not pure MUMPS routines (`.m`).** Before listing the tooling, the next two subsections establish what IOS actually is and how it relates to ANSI MUMPS (note: IOS = IRIS ObjectScript = the language formerly branded as Caché ObjectScript / COS; see the [naming history](#naming-history-intersystems-mumps--caché-objectscript--iris-objectscript-ios) above), then enumerate the file types you will encounter in an IRIS source tree.

#### 4.1.1 IRIS ObjectScript (IOS): what it is, and why it isn't ANSI standard MUMPS

**IRIS ObjectScript (IOS)** — historically and technically still **Caché ObjectScript (COS)**, see the [naming history](#naming-history-intersystems-mumps--caché-objectscript--iris-objectscript-ios) above — is InterSystems' primary programming language. It is **not** ANSI standard MUMPS. It is a proprietary superset built on top of MUMPS that adds object orientation, embedded SQL, embedded Python, and a class-compilation phase. Pure ANSI MUMPS code runs under IOS (every ANSI command is also legal IOS) — but IOS code does **not** run on a pure ANSI MUMPS engine such as YottaDB.

The terms **IOS**, **Caché ObjectScript**, **COS**, and (when InterSystems is the speaker) plain **ObjectScript** all refer to the same language. We use **IOS** in this document to disambiguate from Apple's iOS and to make the IRIS-attachment explicit.

**What ObjectScript adds beyond ANSI MUMPS:**

| Feature | ObjectScript example | Why it isn't ANSI MUMPS |
|---------|----------------------|-------------------------|
| **Classes** | `Class Pkg.Foo Extends %Persistent { Property X As %Integer; Method Bar() {...} }` | ANSI MUMPS has no class concept. Defined in `.cls` files, compiled by the class compiler. |
| **Method dispatch syntax** | `set obj=##class(Pkg.Foo).%New()`, `do obj.Bar()`, `set y=obj.X`, `..Property` | The `obj.Method(args)` form lexically overlaps MUMPS dot-blocks (where a leading-dot line introduces a nested DO scope). The grammar disambiguates by context — but the disambiguation rules themselves are non-ANSI. |
| **Embedded SQL** | `&sql(SELECT ID INTO :id FROM Pkg.Foo WHERE X=:val)` | The `&sql(...)` form is an ObjectScript-only construct that compiles to a prepared SQL plan. ANSI MUMPS has no SQL layer at all. |
| **Embedded Python** | `Method M [Language=python] { ... Python code ... }` (since IRIS 2021.1) | Method-level language switching is an ObjectScript extension. ANSI MUMPS executes only MUMPS. |
| **Macros** | `#include %occInclude`, `#define $$$Foo expr`, `$$$Foo` | Pre-processed before the routine compiler sees the code. ANSI MUMPS has no macro pre-processor. |
| **Class-scoped operators** | `$this`, `..Property`, `##super(...)`, `##class(...)`, `%this` | Tokens unique to the class-compilation model. None exist in ANSI. |
| **Property / parameter typing** | `Property X As %Integer (MAXVAL=100)` | ANSI MUMPS is untyped — every value is a string until coerced. ObjectScript's class properties carry compile-time type metadata. |

**How ObjectScript compiles internally:**

```
.cls source (ObjectScript class)
        │
        │   class compiler
        ▼
.int file (intermediate routine — generated, MUMPS-shaped code)
        │
        │   routine compiler  (also runs on hand-written .mac and .m)
        ▼
object code  (executed by the IRIS runtime)
```

A `.cls` file is **compiled into one or more `.int` (intermediate) routines** by the class compiler. Those `.int` routines look superficially like MUMPS but use ObjectScript-specific tokens (`$this`, `&sql`, `..Property`, etc.) that a pure-ANSI parser cannot accept. The `.int` routines are then run through the routine compiler to produce object code. A hand-written `.mac` (macro routine) or `.m` (ANSI routine) skips the class compiler — it goes straight through the macro pre-processor (for `.mac`) and into the routine compiler.

This means ObjectScript is, in effect, **a higher-level language that transpiles down to a MUMPS-flavoured intermediate form**, and then to object code. It is not "MUMPS with extensions" in the same sense that GNU C is "ISO C with extensions" — it is a separate language with its own grammar, semantics, and compilation pipeline that happens to share a runtime with MUMPS.

**Why ObjectScript is not part of the ANSI standard:**

1. **The standard pre-dates the OO additions.** ANSI X11.1-1995 / ISO 11756 defines MUMPS as a procedural, untyped language with hierarchical key-value globals. The standard has not been revised to incorporate classes, methods, embedded SQL, or macros. ObjectScript is InterSystems-proprietary; the ANSI committee did not adopt it.
2. **The grammars are incompatible.** A pure-ANSI MUMPS parser cannot parse a typical `.cls` file. The `Class`, `Property`, `Method`, `Parameter`, `Index`, and `Storage` keywords — and the `&sql(...)`, `&js<>...`, `##class(...)`, `..Property`, `$this` tokens — have no ANSI definition.
3. **The compilation model is different.** ANSI MUMPS is routine-based: the `.m` file is the unit of compilation. ObjectScript adds a class-compilation phase that generates `.int` routines from `.cls` definitions. The class layer has no ANSI counterpart.
4. **Embedded SQL and embedded Python are out of scope for ANSI MUMPS.** They are first-class in ObjectScript but have no place in the ANSI grammar or runtime model.

**Bottom line:** ObjectScript is a different language built on top of MUMPS. For the rest of this document, "MUMPS code" means ANSI-flavoured M (`.m` source, or `.mac` source restricted to ANSI features) that runs on any conformant engine. "ObjectScript code" means IRIS-extended code (`.cls` classes, or `.mac` routines using ObjectScript tokens) that runs only on IRIS. **A tool that handles ObjectScript does not necessarily handle MUMPS, and vice versa.**

#### 4.1.2 File extensions in IRIS source code

| Extension | Contents | Language | Notes |
|-----------|----------|----------|-------|
| `.cls` | ObjectScript class definition | ObjectScript | Compiled by the class compiler. Generates `.int` routines. **Not parseable as ANSI MUMPS.** |
| `.mac` | Macro routine — most common form of routine code | ObjectScript or MUMPS | Can use plain MUMPS or ObjectScript routine syntax. Macros (`$$$Foo`) are expanded before compilation. The bulk of "routine-layer" IRIS code lives here. |
| `.int` | Intermediate routine — post-macro-expansion | ObjectScript or MUMPS | Auto-generated from `.cls` (always) and `.mac` (after macro expansion). Editable but not the canonical source-of-truth. |
| `.inc` | Macro / include definitions | ObjectScript | `#define $$$Foo expr`, included by `.mac` and `.cls` via `#include`. |
| `.m` | ANSI MUMPS routine | MUMPS (ANSI) | Recognised on import; **stored internally as a MAC routine.** Rarely the source-of-truth in IRIS-native projects. |
| `.bas`, `.mvb`, `.mvi` | Caché Basic / MultiValue Basic | Basic | Legacy. Out of scope here. |
| `.csp` | Caché Server Pages | Mixed (HTML + ObjectScript) | Server-side templating; legacy. |
| `.dfi`, `.lut`, `.pivot` | DeepSee / Analytics artefacts | XML metadata | Out of scope for source-code analysis. |
| `.xml`, `.gof` | Export bundle formats | Wrapper | Used for source-control export and database import/export, not as direct edit targets. |

In a typical IRIS-native project, source code is overwhelmingly `.cls` (ObjectScript classes) plus some `.mac` (routines, usually with ObjectScript tokens). **Pure `.m` ANSI MUMPS files are uncommon** — they appear mainly in projects that maintain cross-engine portability with YottaDB or in legacy VistA imports.

#### 4.1.3 IRIS tooling, by file scope and language

The table annotates each IRIS tool with **three** orthogonal axes — the file scope (which IRIS source format it touches), and whether the tool genuinely supports MUMPS code, IOS code, or both. **File scope and language are not the same thing:** a `.mac` routine is a *container*, not a *language*. The same `.mac` slot can hold either pure ANSI MUMPS or hand-written IOS, and importing a `.m` file into IRIS produces a MAC routine without changing the source language one byte. A tool that "operates on `.mac` files" may or may not actually understand MUMPS — it depends on whether the tool requires IOS constructs (`$this`, `..Property`, `&sql(...)`, `##class()`, `///` doc comments, `$$$Foo` macros) to do useful work.

**File scope** — what kind of source format does the tool ingest?
- **`.cls`** — IOS class file
- **`.mac/.int`** — routine-layer file (any language)
- **`.m`** — ANSI MUMPS native source
- **engine** — operates on compiled bytecode, the database, or the engine itself

**Language columns** — does the tool genuinely support each language?
- <span style="color:#22863a;font-weight:bold">✔</span> — yes, the tool supports this language. (Where support is degraded for one language vs the other, the Notes column elaborates.)
- <span style="color:#cb2431;font-weight:bold">✘</span> — no, the tool does not meaningfully support this language (or no tool exists in this row).

**IOS = IRIS ObjectScript** (formerly Caché ObjectScript / COS); see [§4.1.1](#411-iris-objectscript-ios-what-it-is-and-why-it-isnt-ansi-standard-mumps) for the language definition. The IOS column comes first, since IOS is the engine's primary developer-facing language; MUMPS is second to make the IOS-vs-MUMPS asymmetry visible at a glance.

| Category | What ships with IRIS | File scope | IOS | MUMPS | Notes |
|----------|----------------------|------------|:---:|:-----:|-------|
| Runtime / REPL | `iris session`, `iris terminal` | `.mac/.int`, engine | <span style="color:#22863a;font-weight:bold">✔</span> | <span style="color:#22863a;font-weight:bold">✔</span> | Interactive prompt accepts either IOS or MUMPS commands; limited history. |
| IDE | **VS Code ObjectScript extension** | `.cls`, `.mac/.int`, `.inc` | <span style="color:#22863a;font-weight:bold">✔</span> | <span style="color:#cb2431;font-weight:bold">✘</span> | **By definition an IOS extension** — the IntelliSense, completion, navigation, refactoring, and class-aware features all target IOS. `.m` files can be opened, but the extension provides no MUMPS-aware features for them; the experience is a bare text editor. (InterSystems Studio, the now-deprecated Windows-only IDE, had the same posture.) |
| Class compiler | `$SYSTEM.OBJ.Compile`, `##class(%SYSTEM.OBJ).Compile` | `.cls` only | <span style="color:#22863a;font-weight:bold">✔</span> | <span style="color:#cb2431;font-weight:bold">✘</span> | Compiles classes into `.int` routines. **Cannot run on `.m` files** — there is no class to compile. |
| Routine compiler | Implicit on first reference | `.mac/.int`, `.m` | <span style="color:#22863a;font-weight:bold">✔</span> | <span style="color:#22863a;font-weight:bold">✔</span> | Compiles whatever routine code is loaded — IOS or MUMPS — to object code. Reports MUMPS-level syntax errors. Language-neutral within the MUMPS family. |
| Linting | VS Code extension diagnostics | `.cls`, `.mac` | <span style="color:#22863a;font-weight:bold">✔</span> | <span style="color:#cb2431;font-weight:bold">✘</span> | Surfaces class-compile errors and IOS-only checks; no MUMPS-aware linting. (`^XINDEX` is **not** IRIS-shipped — it is a VA-provided community package; see [§4.3](#43-common-across-both-engines).) |
| Formatting | **None official** | — | <span style="color:#cb2431;font-weight:bold">✘</span> | <span style="color:#cb2431;font-weight:bold">✘</span> | No `gofmt`/`prettier` analogue at any layer or for any language. |
| Test runner | **`%UnitTest`** framework | `.cls` only | <span style="color:#22863a;font-weight:bold">✔</span> | <span style="color:#cb2431;font-weight:bold">✘</span> | Requires extending `%UnitTest.TestCase` (an IOS class). **Cannot test a `.m` routine directly** — only via a class wrapper that calls into the routine. |
| Coverage | `%UnitTest.Coverage` (line-level) | `.mac/.int` (instrumented) | <span style="color:#22863a;font-weight:bold">✔</span> | <span style="color:#22863a;font-weight:bold">✔</span> | Instruments compiled routines regardless of source language. The instrumentation sees compiled bytecode, not source — it does not care whether the routine was originally IOS or MUMPS. **Driver, however, must be a `%UnitTest` class** (IOS). |
| Benchmarking | **None standardised** | — | <span style="color:#cb2431;font-weight:bold">✘</span> | <span style="color:#cb2431;font-weight:bold">✘</span> | Ad-hoc `$ZHOROLOG`. |
| Profiling | **`^%SYS.MONLBL`** (line-by-line); `^pButtons` / `^SystemPerformance` | `.mac/.int`, engine | <span style="color:#22863a;font-weight:bold">✔</span> | <span style="color:#22863a;font-weight:bold">✔</span> | Profiles compiled routines. Language-neutral: runs equally well over a hand-written MUMPS routine, an imported `.m`, or an `.int` generated from `.cls`. |
| Debugging — terminal | `ZBREAK`, `ZSTEP`, `ZSHOW` | engine | <span style="color:#22863a;font-weight:bold">✔</span> | <span style="color:#22863a;font-weight:bold">✔</span> | Pure runtime primitives. Work on any compiled routine regardless of source language. |
| Debugging — IDE | Studio debugger, VS Code debugger via DAP | `.cls`, `.mac/.int`, `.m` | <span style="color:#22863a;font-weight:bold">✔</span> | <span style="color:#22863a;font-weight:bold">✔</span> | Underlying step/breakpoint mechanics are engine-level, but UI affordances (variable inspection, expression evaluation, source mapping) are tuned for IOS classes. Pure MUMPS works in degraded form. |
| Documentation | **Documatic**, `class.View()` | `.cls` only | <span style="color:#22863a;font-weight:bold">✔</span> | <span style="color:#cb2431;font-weight:bold">✘</span> | Requires `///` doc comments **and** class-level metadata. **No documentation generator exists for MUMPS routine code at all**, regardless of file scope. |
| Dependency mgmt | **IPM** (InterSystems Package Manager, formerly **ZPM**) | `.cls`-centric | <span style="color:#22863a;font-weight:bold">✔</span> | <span style="color:#cb2431;font-weight:bold">✘</span> | `module.xml` manifest treats classes as the unit of distribution. A MUMPS-only project has no natural manifest unit. |
| Build / tasks | `$SYSTEM.OBJ.LoadDir`, `Installer.cls`, Makefile around `iris session` | `.cls`, `.mac/.int` | <span style="color:#22863a;font-weight:bold">✔</span> | <span style="color:#cb2431;font-weight:bold">✘</span> | The IRIS build / install pattern is **`Installer.cls`** — by definition a class-based, IOS-only construct. There is no MUMPS-routine-shaped equivalent. Raw `iris session` invocations can be wrapped in a Makefile to load `.m` files manually, but that is a hand-rolled bypass of the IRIS build model, not first-class MUMPS support. |
| Source control | `%Studio.SourceControl.*`; community git integrations | `.cls`, `.mac/.int` | <span style="color:#22863a;font-weight:bold">✔</span> | <span style="color:#cb2431;font-weight:bold">✘</span> | **IRIS stores all routines and classes inside its proprietary database (in a global), *not* on the filesystem.** This is the single most consequential workflow detail in the IRIS column. Source control therefore requires an explicit **export → filesystem → git → import** round-trip on every iteration: the developer edits inside IRIS, exports to `.cls` / `.mac` / `.m` text, commits to git, and on the consuming side imports the text back into the IRIS database before the code can run. There is **no filesystem-resident development model** comparable to Python, Go, Rust, or YottaDB (where `.m` source files on disk *are* the routines). The export/import dance is a serious productivity drag for both languages, but it is **worse for MUMPS**: the `%Studio.SourceControl.*` hooks and the VS Code extension's server-side editing are designed around IOS classes, leaving MUMPS-routine round-trips largely manual. Day-to-day MUMPS development on IRIS effectively reduces to: dump routines from the global → version-control on git → re-load to the global to test. |
| Pre-commit hooks | **None standardised** | — | <span style="color:#cb2431;font-weight:bold">✘</span> | <span style="color:#cb2431;font-weight:bold">✘</span> | Ad-hoc. |
| CI script | Docker image + `iris session` | `.cls`, `.mac/.int` | <span style="color:#22863a;font-weight:bold">✔</span> | <span style="color:#22863a;font-weight:bold">✔</span> | Official Docker images make CI feasible regardless of source language. The harness inside (class compile, `%UnitTest`) is IOS-shaped. |
| Snapshot testing | **None standardised** | — | <span style="color:#cb2431;font-weight:bold">✘</span> | <span style="color:#cb2431;font-weight:bold">✘</span> | Ad-hoc within `%UnitTest`. |
| Foreign-language API | **Native API** (.NET, Java, Python, Node.js) + embedded Python | `.cls`, engine | <span style="color:#22863a;font-weight:bold">✔</span> | <span style="color:#cb2431;font-weight:bold">✘</span> | Native API calls dispatch through IOS methods; embedded Python lives inside IOS methods. **Not callable from a pure `.m` routine.** |
| System administration | **System Management Portal (SMP)** | engine | <span style="color:#22863a;font-weight:bold">✔</span> | <span style="color:#22863a;font-weight:bold">✔</span> | Web admin UI: namespaces, users, journal, replication. Independent of source language. |
| Database export / import | `$SYSTEM.OBJ.Export/Import`, journal replication | engine | <span style="color:#22863a;font-weight:bold">✔</span> | <span style="color:#22863a;font-weight:bold">✔</span> | Container/engine level. Bundles whichever routines and classes exist in the namespace. |
| Embedded SQL | `&sql(...)` blocks | `.cls` only | <span style="color:#22863a;font-weight:bold">✔</span> | <span style="color:#cb2431;font-weight:bold">✘</span> | IOS-only construct. Cannot appear in an ANSI MUMPS routine. |
| Containerised deployment | Official Docker images, Kubernetes kits | engine | <span style="color:#22863a;font-weight:bold">✔</span> | <span style="color:#22863a;font-weight:bold">✔</span> | Engine-level packaging. |

**Key observation about IRIS tooling and language:**

- **Language-aware tooling in IRIS is overwhelmingly ObjectScript-targeted.** The class compiler, `%UnitTest`, Documatic, IPM, Studio's smart features, the VS Code extension's IntelliSense, the Native API, embedded Python, and embedded SQL all require ObjectScript constructs to be useful.
- **`^XINDEX` does not ship with IRIS at all.** It is a VistA Toolkit routine (pure M source, from the VA's Kernel package) that happens to be present in any IRIS-based VistA installation because VistA itself brings it. The same routine runs identically on YottaDB. It is the closest thing to a MUMPS-aware linter in the M ecosystem today, but it is a VistA artefact, not a vendor tool of either engine.
- **The remainder are engine-level**: the routine compiler, `^%SYS.MONLBL`, `%UnitTest.Coverage`'s instrumentation, `ZBREAK`/`ZSHOW`/`ZSTEP`, journal export/import, and SMP. These are language-neutral because they operate below the language layer (compiled bytecode, the database, or the running process). They work on a 40,000-routine VistA codebase as readily as on an ObjectScript application — but they tell you nothing about the source language and provide no source-language-aware guidance.

The MAC-routine container does not magically transform MUMPS code into ObjectScript. Importing a `.m` routine into IRIS produces a MAC routine slot that holds *MUMPS code*, and tools that genuinely understand MUMPS (essentially `^XINDEX` only, and only when VistA — or a standalone Toolkit install — is present) treat it as MUMPS. Tools that require ObjectScript constructs simply have nothing to do with that routine.

**The IRIS toolchain in one sentence:** comprehensive, IDE-centric, gated by commercial licensing, and **ObjectScript-targeted at the language layer** — strong for class-based development, language-neutral at the engine layer (profiler, admin UI, journal), and offering **no first-party MUMPS-aware tooling at all** (the `^XINDEX` static analyser, often cited in this context, is a VistA Toolkit routine — not an InterSystems tool).

### 4.2 YottaDB

YottaDB sits at the open-source end. The runtime is feature-complete and POSIX-compliant; the **C API (`libyottadb.so`)** is the principal extensibility surface, and most non-M language support comes through bindings on top of it. There is no first-party IDE.

The table below mirrors the format of [§4.1.3 (IRIS tooling)](#413-iris-tooling-by-file-scope-and-language) so the two engines can be compared row-by-row. Because YottaDB is **MUMPS-only** — there is no IOS-equivalent layer to score separately — the language column is just **MUMPS**.

**File scope** — what kind of source format or runtime layer does the tool touch?
- **`.m`** — ANSI MUMPS routine source
- **engine** — operates on compiled bytecode, the database, or the engine itself
- **bindings** — operates via the C API with host-language bindings (`libyottadb.so`)
- **—** — no tool exists in this category

**MUMPS column** — does the tool genuinely support MUMPS code?
- <span style="color:#22863a;font-weight:bold">✔</span> — yes, the tool supports MUMPS code (or is engine-level / language-neutral and applies to MUMPS).
- <span style="color:#cb2431;font-weight:bold">✘</span> — no first-party tool exists. (Community-supplied tools — `^XINDEX`, `%ut`, KIDS — are inventoried in [§4.3](#43-common-across-both-engines), not here.)

| Category | What ships with YottaDB | File scope | MUMPS | Notes |
|----------|-------------------------|------------|:-----:|-------|
| Runtime / REPL | `ydb` direct mode; `ydb -run %XCMD "code"` | engine | <span style="color:#22863a;font-weight:bold">✔</span> | REPL is bare: no history, no completion, no multi-line editing. `%XCMD` is the foundation of all shell wrappers. |
| Syntax check / routine compiler | `ZCOMPILE` via `%XCMD` | `.m` | <span style="color:#22863a;font-weight:bold">✔</span> | Compile-only; reports syntax errors. No type system. |
| Linting | **None** | — | <span style="color:#cb2431;font-weight:bold">✘</span> | No analogue to `ruff` / `clippy`. (`^XINDEX` is community-supplied — see [§4.3](#43-common-across-both-engines).) |
| Formatting | **None** | — | <span style="color:#cb2431;font-weight:bold">✘</span> | No `gofmt` analogue. |
| Test runner | **None first-party** | — | <span style="color:#cb2431;font-weight:bold">✘</span> | OSEHRA `%ut` (M-Unit) is the de-facto community framework — see [§4.3](#43-common-across-both-engines). |
| Coverage | **None first-party** | — | <span style="color:#cb2431;font-weight:bold">✘</span> | `ZBREAK`-based community implementations exist; nothing canonical. |
| Benchmarking | `$ZHOROLOG` primitive only | engine | <span style="color:#cb2431;font-weight:bold">✘</span> | A microsecond timer is available; no `criterion`-style harness. |
| Profiling | **None integrated** | — | <span style="color:#cb2431;font-weight:bold">✘</span> | No analogue to IRIS's `^%SYS.MONLBL`. Some signals derivable from journals / triggers. |
| Debugging — terminal | `ZBREAK`, `ZSTEP INTO/OVER/OUTOF`, `ZSHOW "V/G/L/S/A"`, `ZWRITE`, `ZPRINT`, `ZCONTINUE`, `ZGOTO`, `$STACK`, `$ZPOSITION` | engine | <span style="color:#22863a;font-weight:bold">✔</span> | Powerful but interactive and manual. |
| Debugging — IDE / DAP | **None** | — | <span style="color:#cb2431;font-weight:bold">✘</span> | No first-party IDE or DAP server. |
| Documentation | **None integrated** | — | <span style="color:#cb2431;font-weight:bold">✘</span> | Comments in source; no `godoc` analogue ships with YDB. |
| Dependency mgmt | **None** | — | <span style="color:#cb2431;font-weight:bold">✘</span> | No package manager. Source is shipped as `.m` files manually. (KIDS is community-supplied — see [§4.3](#43-common-across-both-engines).) |
| Build / tasks | **None integrated** | — | <span style="color:#cb2431;font-weight:bold">✘</span> | No build system. Teams roll their own with `make` + `ydb -run`. |
| Source control | Plain git on the routine directory | `.m` | <span style="color:#22863a;font-weight:bold">✔</span> | **Filesystem-resident:** `.m` source files on disk *are* the routines. No export / import dance — git just works on the routine directory. **Direct contrast with IRIS**, where routines live inside the database and source control requires an export → git → import round-trip on every iteration (see [§4.1.3 source-control row](#413-iris-tooling-by-file-scope-and-language)). |
| Pre-commit hooks | **None integrated** | — | <span style="color:#cb2431;font-weight:bold">✘</span> | Standard git hooks are usable; nothing M-aware. |
| CI script | **None integrated** | — | <span style="color:#cb2431;font-weight:bold">✘</span> | Standard CI runners over `make` + `ydb -run`. |
| Snapshot testing | **None** | — | <span style="color:#cb2431;font-weight:bold">✘</span> | Ad-hoc. |
| Foreign-language API | **`libyottadb.so` C API** + bindings: Go (official), Python (official), Node.js (community), Rust (community), Lua (community), Perl (community) | engine + bindings | <span style="color:#22863a;font-weight:bold">✔</span> | Stable C API is the major extensibility win. Calls are bidirectional: M ↔ host language. See [§4.4](#44-foreign-language-integration-embedded-language-vs-embedded-database). |
| Database management | **`mupip`** (extract / load / size / integ / backup / restore / rundown / journal / set / trigger / freeze / replicate) | engine | <span style="color:#22863a;font-weight:bold">✔</span> | The single most powerful and underused YDB utility. `mupip extract` / `load` are the foundation of any fixture management system. |
| Global directory | **`gde`** | engine | <span style="color:#22863a;font-weight:bold">✔</span> | Configures which globals live in which database files. |
| Lock examination | **`lke`** | engine | <span style="color:#22863a;font-weight:bold">✔</span> | Inspect and forcibly clear `LOCK` entries from crashed processes. |
| Database structure / recovery | **`dse`** | engine | <span style="color:#22863a;font-weight:bold">✔</span> | Block-level recovery editor. Dangerous; recovery scenarios only. |
| Utility routines | **`%GO`**, **`%GI`**, **`%GSEL`**, **`%RD`**, **`%RSEL`**, **`%ZDATE`**, **`%ZCRC`**, **`%ZMVALID`**, **`%XCMD`**, **`%ZTRIGGER`** | engine | <span style="color:#22863a;font-weight:bold">✔</span> | Ship inside `$YDB_DIST`. Cover global I/O, routine listing, date/time, CRC, identifier validation, trigger management. |
| SQL | **Octo** (separate package) | separate runtime | <span style="color:#cb2431;font-weight:bold">✘</span> | A SQL-on-YottaDB layer — *not part of the core distribution*. Roughly comparable in surface to IRIS's embedded SQL but sits as a separate runtime. |
| Containerised deployment | Community Docker images; YottaDB AWS / GCP marketplace listings | engine | <span style="color:#22863a;font-weight:bold">✔</span> | Adequate; less polished than IRIS's official kits. |
| System administration — web UI | **YDBGUI** ([gitlab.com/YottaDB/UI/YDBGUI](https://gitlab.com/YottaDB/UI/YDBGUI)) — Vue.js front-end on an **M backend**, served by the **YDB Web Server** plugin. Companion projects: **YDBGDEGUI** (Global Directory Editor GUI) and **YDBAdminOpsGUI** (admin / ops dashboard). | engine | <span style="color:#22863a;font-weight:bold">✔</span> | Shipped with YottaDB r1.36 (2022). Dashboard, real-time process / global statistics, database admin and monitor surfaces. Younger and narrower in scope than IRIS's SMP, but actively developed. The fact that the backend is itself written in M is a deliberate "M-first" architectural choice. |
| System administration — shell | `mupip`, `gde`, `lke`, `dse`, environment variables, `.envrc`-style setup | engine | <span style="color:#22863a;font-weight:bold">✔</span> | Composable POSIX surface; fully scriptable. Unfamiliar to non-Unix admins, which is what motivated YDBGUI. |

**The YottaDB toolchain in one sentence:** mature, open-source, runtime-first, and POSIX-composable — strong on the engine / database / admin layer (mupip, gde, lke, dse, YDBGUI, the C API), with **filesystem-resident routines** that play naturally with standard git and POSIX tooling — but most developer-experience layers (linter, formatter, IDE, test runner, coverage, docs, package manager) are simply absent and have to be built or sourced from the community.

### 4.3 Common across both engines

A handful of capabilities are consistently available either because they come from the M language itself or because they ship as third-party / community / VistA-provided M source that runs on any conformant engine:

**From the M language itself**

- **Interactive direct mode** with manual breakpoints (`ZBREAK`) and inspection (`ZSHOW`, `ZWRITE`).
- **Microsecond timing** via `$ZHOROLOG` — sufficient for hand-rolled benchmarks.
- **Trigger primitives** (`MUPIP TRIGGER` in YDB, `%CSP.UI`-managed triggers in IRIS) for instrumentation patterns that don't require a separate profiler.
- **Plain-text routine source** that any text editor or CI runner can handle, even without M-aware tooling.
- **A stable, decades-old language standard** — code written against the ANSI / pragmatic core ports between engines without rewrites.

**From the VA / VistA ecosystem (not vendor-shipped)**

- **`^XINDEX`** — the VistA Toolkit static analyser (the 17 `XINDX*` routines from the VA Kernel package, in `WorldVistA/VistA-M`). Pure M source; runs identically on YottaDB and IRIS. The closest thing to a MUMPS-aware linter that exists today: it understands ANSI MUMPS, enforces the VA Standards & Conventions (SAC) rule set, and rejects ObjectScript-only constructs as non-conformant. Bundled with any VistA deployment; can also be installed standalone.
- **OSEHRA `%ut`** (M-Unit) — the de-facto community testing framework for pure MUMPS routines. Pure M source; runs on either engine.

**From the OSS community (cross-engine)**

- **OSEHRA / WorldVistA tooling** — additional M-source utilities for code archaeology, indentation, and routine inspection. Quality varies; not vendor-supported.

---

### 4.4 Foreign-language integration: "embedded language" vs "embedded database"

The §4.1 and §4.2 tables list foreign-language integration as a single row, but the two engines take **architecturally inverse approaches** that deserve a closer look. InterSystems markets IRIS's runtime hosting of Python (since 2021.1) under the label **"Embedded Python"**. YottaDB ships a stable C API (`libyottadb.so`) with first-party bindings for Python and Go, plus community bindings for Rust, Node.js, Lua, and Perl. Both put the foreign language and the M engine in the same OS process. Neither pays IPC or serialisation overhead. **They are not the same thing.**

#### "Embedded" is a technical term of art, not marketing

Embedding a language interpreter into a host program is a well-established architectural pattern with decades of precedent: Tcl was designed for embedding in the late 1980s; Lua's defining design property is that it is embedded into host applications; CPython's C API explicitly distinguishes [embedding](https://docs.python.org/3/extending/embedding.html) from extending; V8 is embedded in Chrome, Node.js, and Deno; SQLite is the canonical embedded database. The term is not marketing.

**Definition (technical):** *an embedded runtime is one that is loaded as a library into another program's address space, runs under that program's process and threading control, and exposes an API the host can use to evaluate code, call functions, and exchange data.* The host owns the lifecycle; the embedded runtime is the guest.

#### The architectural inversion

The difference between the two integration models is **which side is the host**:

| Aspect | IRIS Embedded Python | YottaDB C-API integration |
|--------|---------------------|---------------------------|
| Host process | IRIS server | The user's Python (or Rust, Go, Lua, …) program |
| Embedded runtime | CPython, loaded into the IRIS process | YottaDB, loaded as `libyottadb.so` into the user's program |
| Who owns lifecycle, threading, scheduling | IRIS | The host language's program |
| Inline source-file integration | Python in `.cls` methods (`[Language=python]`); SQL via `&sql(...)` | None — host language has its own source files; M routines invoked via `ydb_ci()` (call-in) |
| Cross-language call mechanism | ObjectScript ↔ Python proxy layer | Direct C FFI: `ydb_set_s`, `ydb_get_s`, `ydb_subscript_next_s`, etc. |
| Foreign-language package ecosystem | Operates inside an IRIS-managed environment | Normal PyPI / crates.io / npm / Go module proxy |
| Tooling for the foreign language | pdb, pip, IDE debug all IRIS-mediated; unusual for a Python developer | Host's normal tooling works unchanged |
| Threading model | IRIS owns threads; Python GIL applies | Host owns threads; YDB calls are thread-safe |
| Licence posture | Commercial IRIS licence required | AGPL-3.0 on YDB; host language unconstrained |
| Foreign-language coverage | Python only (+ SQL, JavaScript via CSP) | Any C-FFI-capable language — currently 10+ ecosystems |
| Foreign object persistence | Python objects can BE IRIS objects (auto-mapped to globals via class storage) | Host objects are not persisted — globals are a separate, deliberate API surface |

Both architectures have decades of precedent in other systems:

- **IRIS's model** — a database server that hosts a foreign-language interpreter — is the same shape as **PostgreSQL's PL/Python**, **Oracle's Java stored procedures**, and **SQL Server's CLR integration**. The database drives.
- **YottaDB's model** — the database as a library linked into the host program — is the same shape as **SQLite**, **RocksDB**, **LevelDB**, **LMDB**, and **DuckDB**. These are routinely described as *embedded databases*. The host language drives.

So **both models embed something in something else**. IRIS embeds a language inside the database; YottaDB embeds the database inside a language. The labels "Embedded Python" (IRIS) and "C-API bindings" (YDB) describe these inverse architectures.

#### A terminology test

The conventional **`X-on-Y`** idiom for software stacks names the data foundation last: *Python-on-Postgres*, *Rails-on-Postgres*, *Django-on-MySQL*. The application is `X`; the database is `Y`.

- **YottaDB's model fits this idiom cleanly.** A Python application using YottaDB as its data layer is **Python-on-YDB**. Same for **Rust-on-YDB**, **Go-on-YDB**, **Node-on-YDB**, **Lua-on-YDB**. The host language is the application; YDB is the data foundation. Stack idiom works.
- **IRIS's model breaks the idiom.** IRIS is not a database that Python applications run on top of — IRIS is a host runtime that *encapsulates* Python as an embedded guest interpreter. Neither *Python-on-IRIS* nor *IRIS-on-Python* captures the relationship correctly. The natural phrasing is **"IRIS encapsulating Python"** (or *"Python embedded in IRIS"*, *"IRIS hosting Python"*).

The fact that `X-on-Y` works for one model and not the other is itself diagnostic of the architectural inversion. Stack idioms describe relationships of dependency-on-foundation; encapsulation idioms describe relationships of host-and-guest. The two models are different *shapes*, not just different orientations of the same shape, and the language we naturally reach for reflects that.

#### Performance

Both models are in-process and avoid IPC / serialisation. For pure compute, neither has an architectural advantage. The dominant cost is **cross-language call overhead** (typically sub-microsecond per call on modern hardware), and that cost is comparable in both models. Workloads that respect the "do bulk work on one side of the boundary, then cross" rule perform well in either model; chatty workloads suffer in both.

What dominates real workloads differs:

- **Python-on-YDB:** a typical hot loop traverses an M global from Python (`for sub in ydb.subscripts("^Patient", []): …`). Each iteration crosses the FFI boundary once. Performance is dominated by *number of round-trips*, which binding authors can amortise by exposing bulk / iterator APIs.
- **IRIS Embedded Python:** a typical hot loop iterates over an ObjectScript class's properties (`for prop in obj.Properties: …`). Each iteration crosses the proxy layer once. Performance is dominated by the proxy-cache hit rate.

Neither architecture is faster in the abstract; the question is whether your workload's natural API shape lines up with the model's strengths.

#### Implications for portability

When evaluating whether code is "portable" between IRIS and YottaDB:

- **A `.cls` file using Embedded Python or `&sql(...)`** is not portable — both the class layer and the embedded constructs are ObjectScript-specific.
- **A `.m` file plus a Python program that calls into it via `libyottadb`** is portable *in spirit* — the M code runs on either engine, and the Python program could in principle call IRIS via the Native API instead. The two paths use different APIs (and different licences), but the M source itself is unchanged.
- **A `.m` file containing only ANSI / pragmatic MUMPS** runs on either engine; the question of which language hosts it is orthogonal.

This asymmetry is what the §5 matrix's "Embedded other language" row captures: IRIS's `.cls` ⬤ entry reflects inline foreign code in source files; YottaDB's ◯ entry reflects that you cannot write Python directly inside a `.m` file. But the equivalent capability — *calling Python from M, or calling M from Python* — exists on both engines via different mechanisms, and that broader capability is what the "Foreign-language API" row tracks.

---

### 4.5 Polyglot routines vs C-API separation: a quality / maintainability analysis

§4.4 establishes that the two integration architectures put the foreign language and the M engine in the same OS process and have comparable runtime performance. The substantive question is therefore not *which is faster?* but **what happens to the foreign-language code over the project's lifetime**: how it is reviewed, tested, refactored, deployed, debugged, and handed off to new contributors. That is what determines whether a system is good to work on five years from now.

This subsection compares the two models on the dimensions that matter to developers and maintainers — code quality, efficiency, maintainability, and integration with modern CI/CD lifecycles.

#### The two models, concretely

**Polyglot routine (IRIS):** ObjectScript class with embedded Python and embedded SQL in the same `.cls` file:

```objectscript
Class MyApp.Patients Extends %Persistent {
  Property ID As %Integer;

  ClassMethod Process(id As %Integer) As %Status [Language = python] {
    import pandas as pd
    df = pd.read_sql("SELECT * FROM Patients WHERE ID = ?", iris.connect(), params=[id])
    # ... pandas operations ...
  }

  Method Save() As %Status {
    &sql(INSERT INTO Patients VALUES (:..ID))
    quit $$$OK
  }
}
```

Three grammars — ObjectScript, Python, embedded SQL — in one file.

**C-API separation (YottaDB):** pure M on one side, pure Python project on the other, joined by a stable C ABI:

```mumps
; routines/patients.m
patients ;
process(id)
  set rec=$get(^Patient(id))
  quit rec
```

```python
# patient_service/main.py — separate project, normal layout
import yottadb
import pandas as pd

def process(patient_id: int) -> dict:
    record = yottadb.get(("^Patient", str(patient_id)))
    df = pd.DataFrame([record])
    return df.to_dict()
```

Two languages, two source trees, joined by the YDB C-API.

#### Comparison matrix

**Symbol convention** (cell-by-cell, scoring each side independently): <span style="color:#22863a;font-weight:bold">✔</span> = capability present and works as expected for that side · <span style="color:#cb2431;font-weight:bold">✘</span> = capability absent or materially degraded for that side. A row with <span style="color:#22863a;font-weight:bold">✔</span>/<span style="color:#22863a;font-weight:bold">✔</span> means both architectures handle the dimension well; a row with <span style="color:#22863a;font-weight:bold">✔</span>/<span style="color:#cb2431;font-weight:bold">✘</span> or <span style="color:#cb2431;font-weight:bold">✘</span>/<span style="color:#22863a;font-weight:bold">✔</span> shows a substantive split.

| Dimension | C-API separation (YDB) | Polyglot (IRIS) |
|-----------|------------------------|-----------------|
| **Linter / formatter for foreign code** | <span style="color:#22863a;font-weight:bold">✔</span> Full — Python lives in `.py`; standard tools work without modification | <span style="color:#cb2431;font-weight:bold">✘</span> None — `ruff`, `black`, `mypy`, `pylint` cannot read `.cls` files; embedded Python is invisible to its own ecosystem |
| **Type checker for foreign code** | <span style="color:#22863a;font-weight:bold">✔</span> Full — `mypy --strict` works; binding types (e.g., `yottadb-rs`'s typed `Result<T, E>`) carry contracts across the boundary | <span style="color:#cb2431;font-weight:bold">✘</span> Effectively absent — `mypy` / `pyright` don't see embedded Python; OS↔Python seam errors surface only at runtime |
| **Test framework for foreign code** | <span style="color:#22863a;font-weight:bold">✔</span> Native — `pytest` / `cargo test` / `go test`, with mocked or real YDB calls | <span style="color:#cb2431;font-weight:bold">✘</span> `%UnitTest` only — testing embedded Python in isolation requires either (a) wrapping in an OS test class or (b) extracting to `.py` (which defeats the polyglot integration) |
| **Code review (PRs)** | <span style="color:#22863a;font-weight:bold">✔</span> Single-language PRs; each can be reviewed by domain experts | <span style="color:#cb2431;font-weight:bold">✘</span> Multi-grammar diffs; reviewer context-switches between OS, Python, and SQL |
| **Refactoring tools** | <span style="color:#22863a;font-weight:bold">✔</span> Full — `gopls rename`, `rust-analyzer rename`, PyCharm refactor all work normally | <span style="color:#cb2431;font-weight:bold">✘</span> None — PyCharm / VS Code Python extensions can't refactor inside `.cls`; ObjectScript-specific tools don't understand Python |
| **IDE / completion / navigation** | <span style="color:#22863a;font-weight:bold">✔</span> Full — each language gets its native IDE support | <span style="color:#cb2431;font-weight:bold">✘</span> Degraded — Studio and the VS Code ObjectScript extension treat embedded Python as opaque text inside a class |
| **Dependency management** | <span style="color:#22863a;font-weight:bold">✔</span> Standard — `pip` / `uv` / `poetry` / `cargo` / `go mod` with lockfiles | <span style="color:#cb2431;font-weight:bold">✘</span> IRIS-managed Python environment; not the standard PyPI flow; conflicts with system Python / virtualenvs |
| **CI / CD** | <span style="color:#22863a;font-weight:bold">✔</span> Standard — `pytest` in a 50 MB Python container, `cargo test` in `rust:slim`; M-side runs separately in YDB | <span style="color:#cb2431;font-weight:bold">✘</span> Requires an IRIS container (commercial; ~GB image) to compile and test the class; pipelines are IRIS-specific |
| **Documentation** | <span style="color:#22863a;font-weight:bold">✔</span> Full — Sphinx / mkdocs / `pdoc` for Python, `godoc` for Go, `rustdoc` for Rust | <span style="color:#cb2431;font-weight:bold">✘</span> Documatic extracts OS class headers and `///` comments; embedded Python is invisible to it |
| **Static analysis (security, complexity, dead code)** | <span style="color:#22863a;font-weight:bold">✔</span> Full — `bandit`, `gosec`, `cargo-audit` operate on each side as designed | <span style="color:#cb2431;font-weight:bold">✘</span> None across the OS / Python boundary; foreign-language tools don't see embedded code |
| **Debugger** | <span style="color:#22863a;font-weight:bold">✔</span> Native — host language's debugger (`pdb`, `dlv`, `rust-lldb`) works on the host code; M-side via `ZBREAK` is separate but well-defined | <span style="color:#cb2431;font-weight:bold">✘</span> Studio / VS Code debug ObjectScript; stepping into embedded Python is awkward; Python frames render as IRIS-managed proxies |
| **Versioning** | <span style="color:#22863a;font-weight:bold">✔</span> M and host language evolve independently | <span style="color:#cb2431;font-weight:bold">✘</span> A `.cls` file with embedded Python is a single unit; updating the Python revs the class; backward-compat is awkward |
| **Hiring pool** | <span style="color:#22863a;font-weight:bold">✔</span> Large — anyone fluent in the host language can contribute to that side; M expertise remains needed for the M side, but is bounded | <span style="color:#cb2431;font-weight:bold">✘</span> Small — needs OS class developers + IRIS-specific Python proxy expertise (and shrinking) |
| **Onboarding** | <span style="color:#22863a;font-weight:bold">✔</span> A Python developer can learn "this is how I call the M database" and ship code without learning ObjectScript | <span style="color:#cb2431;font-weight:bold">✘</span> New developer must learn OS class system, embedded Python conventions, IRIS-specific Python proxy semantics, embedded SQL |
| **Vendor lock-in** | <span style="color:#22863a;font-weight:bold">✔</span> Low — the C ABI is a stable, portable contract | <span style="color:#cb2431;font-weight:bold">✘</span> High — code commits to the IRIS class layer and IRIS-specific Python integration |
| **Initial prototype velocity** | <span style="color:#cb2431;font-weight:bold">✘</span> Slower bootstrap — two trees, two test runners, two CI jobs | <span style="color:#22863a;font-weight:bold">✔</span> Faster — everything in one file; class-compile feedback is fast |
| **Steady-state development velocity** | <span style="color:#22863a;font-weight:bold">✔</span> Faster — each language uses its native (and, in Python / Rust / Go, very mature) tooling | <span style="color:#cb2431;font-weight:bold">✘</span> Slower — degraded tooling on the foreign language compounds over time |
| **Runtime performance** | <span style="color:#22863a;font-weight:bold">✔</span> In-process when host loads `libyottadb.so`; ~µs per FFI call. Comparable. | <span style="color:#22863a;font-weight:bold">✔</span> In-process; ~µs per OS↔Python proxy call |

**Tally:** of 18 dimensions, the C-API model wins 16, the polyglot model wins 1 (initial prototype velocity), and 1 is a tie (runtime performance). The single polyglot win is a transient advantage that disappears once the project crosses a low size threshold; the 16 C-API wins compound over the project lifetime.

#### The CI / CD lifecycle dimension

This is where the gap between the two models is sharpest. Modern host-language ecosystems assume:

- Linters and formatters on every commit (`ruff check`, `cargo fmt --check`)
- Type checkers in CI (`mypy --strict`, `tsc --noEmit`)
- Test suites in fast, ephemeral containers (`pytest` in 50 MB images, `cargo test` in `rust:slim`)
- Lockfiles guaranteeing reproducible builds (`uv.lock`, `Cargo.lock`, `go.sum`)
- Pre-commit hooks blocking bad commits before review
- Coverage tracked over time (Codecov, Coveralls)
- Static analysis (`bandit`, `gosec`, `cargo-audit`) on every PR
- Documentation auto-generated and deployed (`mkdocs gh-deploy`, `cargo doc`)

**In the polyglot model, none of this applies to the embedded foreign-language code.** The Python inside a `.cls` method is opaque to `ruff`, invisible to `mypy`, untestable by `pytest`, undocumented by Sphinx, uncovered by `pytest-cov`, and unreachable by every other tool the Python ecosystem has built over the past decade. The IRIS class compiler and `%UnitTest` are the only validation — and they were not designed to be a Python toolchain.

**In the C-API model, every modern host-language tool applies as-is.** The Python side is a normal Python project; the Rust side is a normal Cargo crate. The M side has weak tooling (the gap motivating this entire document), but the weak M tooling **does not drag down the host language**. Each language gets the best available for its ecosystem.

#### The Inner Platform Effect

The polyglot model exhibits what software-engineering literature calls the [**Inner Platform Effect**](https://en.wikipedia.org/wiki/Inner-platform_effect): IRIS effectively reinvents a multi-language tooling stack inside its own walls.

| Mainstream tool / capability | IRIS-internal reinvention | Why it falls short |
|------------------------------|---------------------------|--------------------|
| `ruff` / `mypy` / `pylint` | IRIS class compiler + runtime errors for embedded Python | Class compiler validates ObjectScript; embedded Python is just text until it executes |
| `pytest` | `%UnitTest` (ObjectScript class-based) | Cannot test embedded Python in isolation; can only test through OS wrappers |
| Sphinx / `pdoc` | Documatic | OS-classes only; embedded Python is invisible to documentation extraction |
| `pip` / `uv` | IRIS-managed Python environment | Not standard PyPI; lockfiles, virtualenvs, and reproducible installs are second-class |
| `pdb` / IDE Python debug | IRIS Studio / VS Code debugger | Stepping into Python from OS is awkward; Python frames render as IRIS-managed proxies |
| GitHub Actions matrices | IRIS-container-based CI | Commercial container required; per-PR cost is materially higher |

Each reinvention is necessarily weaker than the original it shadows, because the original has decades of community investment that no single vendor can match per-language. The C-API model avoids this entirely by **not** trying to host a Python lifecycle inside the database — it just exposes a C ABI and lets `pip` / `uv` / `pytest` / `mypy` do what they already do well.

#### When polyglot is legitimately the right call

The polyglot model has narrow but real use cases:

- **Genuinely small snippets.** A single `&sql(SELECT ID FROM Foo WHERE X=:val)` inside a method is more readable than dispatching to a separate SQL file. The line where this stops being true is roughly when the foreign code grows past one screen.
- **Stored-procedure-style logic.** Where the foreign code is logically a stored procedure that runs close to the data and never needs to evolve independently, polyglot has lower ceremony.
- **Incremental modernisation.** A team with decades of ObjectScript that wants to introduce Python without uprooting structure may reasonably start polyglot before separating out.
- **Single-developer or very small projects.** Where the velocity cost of two source trees outweighs the long-term maintenance benefit, polyglot can win on net.

These cases are bounded. Once a project has multiple developers, a non-trivial Python / Rust / Go component, or any expectation of long-term maintenance, the polyglot model's costs compound while the C-API model's costs amortise.

#### Recommendation

For systems of any non-trivial scale, **the C-API separation model is materially better on every dimension that matters for long-term maintenance**: code quality, testing, refactoring, CI/CD, hiring, documentation, and lock-in. Runtime performance is roughly a wash. The polyglot model wins only on initial-prototype velocity and on a small class of snippet-sized foreign code — both temporary or bounded advantages.

The deeper observation: **good software engineering separates concerns by domain, and language is one of the most important domain boundaries.** Each language has its own conventions, tooling, experts, and ecosystem. Mixing languages in one file fights all of these; separating them lets each part be excellent at what it does. The C-API approach respects this boundary; the polyglot approach fights it.

For an M codebase being modernised today, the question "polyglot or C-API?" reduces to: *do we want to reinvent the Python (or Rust, or Go) tooling stack inside our walls, or use the tooling that already exists outside them?* Phrased that way, the answer is rarely in doubt.

---

## 5. Summary Table: MUMPS-vs-MUMPS — Gold Standard, IRIS, YottaDB, VA/Community

**This is a MUMPS-vs-MUMPS comparison.** It scores each engine on what's available to a developer writing **pure ANSI / pragmatic MUMPS code** — `.m` routines, or pure-MUMPS `.mac` routines on IRIS that contain no ObjectScript constructs. ObjectScript classes (`.cls`) are deliberately **out of scope**: ObjectScript is a separate language built on top of the runtime ([§4.1.1](#411-objectscript-what-it-is-and-why-it-isnt-ansi-standard-mumps)), and a `%UnitTest` class or Documatic comment doesn't help a developer writing MUMPS. Tools that target ObjectScript belong in a different comparison.

The columns are:

1. **Gold Standard** — the consensus capability mainstream-language developers expect (synthesised across Python, JS/TS, Go, Rust, Java; see [§2](#2-the-gold-standard--top-5-language-toolchains)).
2. **IRIS (MUMPS routine)** — what's available to a developer writing `.m` or pure-MUMPS `.mac` files on IRIS, with no class wrapping.
3. **YottaDB (`.m`)** — what's available to a developer writing `.m` files on YottaDB.
4. **VA / Community packages** — pure-M source artefacts that supplement *either* engine equally (`^XINDEX`, KIDS, `%ut` / M-Unit, OSEHRA / WorldVistA tools; see [§4.3](#43-common-across-both-engines)). These are not vendor-shipped — they are M-language packages distributed by the VA, OSEHRA, WorldVistA, and similar communities. **This column is informational, not scored.** It lists what community / VA add-ons exist where they exist, and carries a descriptive note where they don't. **There are no scoring labels in this column** (no Full / Basic / Minimal / None) — absence of a community package is not an implementation gap, so it is not scored. See the scoping caveat below.

> **Scoping caveat.** *None of the tooling in the table below — neither the IRIS or YottaDB engine entries, nor the VA / Community packages — has been formally scoped against the gold-standard tools in §2 for actual functionality, depth, or feature parity.* This document identifies the **presence or absence** of an analogous capability; it does not measure how close that capability comes to (for example) `ruff`'s rule set, `pytest`'s discovery, or `cargo`'s dependency resolution. The Full / Basic tag on the IRIS and YottaDB columns reflects relative engine-shipping maturity (e.g., IRIS's profiler is much more developed than YDB's REPL); it is **not** a comparison against the gold standard. The VA / Community column drops Full / Basic entirely because community packages have not been benchmarked against peer tools at all. *Quantifying these gaps and measuring the remaining distance to gold-standard parity is a follow-on project; the purpose of **this** analysis is to identify the gaps in the first place.*

#### A note on "OS-class wrappers" (and why they don't help the underlying MUMPS code)

Several IRIS-column cells in the matrix below note that a capability is available *only via an OS-class wrapper*. This is shorthand for a specific pattern: writing an ObjectScript class file (`.cls`) that extends an IRIS framework class (e.g., `%UnitTest.TestCase`) and whose methods do nothing but call into pure MUMPS routines via the `$$label^routine` syntax. Concretely:

```objectscript
/// Test class — pure scaffolding around a MUMPS routine
Class MyApp.Tests.PatientServiceTest Extends %UnitTest.TestCase {
  Method TestProcess() {
    set result = $$process^patientService(123)
    do $$$AssertEquals(result.status, "OK")
  }
}
```

The class is **scaffolding, not logic** — it exists solely so IRIS's class-based tooling (`%UnitTest`, `%UnitTest.Coverage`, Documatic, IPM) has something to dispatch on. The underlying MUMPS routine (`patientService.m`) is unchanged.

**What this gives you:** access to IRIS's test discovery, test reporting, line-coverage instrumentation, and class-based packaging — all hanging off the wrapper class.

**What this does *not* give you:**

- **No MUMPS-language awareness.** The test framework sees pass/fail returned from a class method; it has no understanding of MUMPS syntax, control flow, or idioms. A test that calls `$$process^patientService` is opaque to the framework as a unit; it cannot tell you anything about the routine's quality.
- **No improvement to the underlying MUMPS code.** Linting, formatting, complexity analysis, dead-code detection, documentation extraction, and refactoring of the MUMPS routines themselves are entirely unaffected. The wrapper class is a façade, not an analyser. The MUMPS code remains as opaque after wrapping as before.
- **No MUMPS-side refactoring support.** Refactoring tools (rename, extract method, find references) operate on the class, not the routine. Renaming a label inside `patientService.m` will silently break every wrapper that calls `$$oldlabel^patientService`, and no IRIS-side tool will catch it.

**What this *forces*:**

- Test code, fixture code, documentation, and dependency manifests must all be expressed in **ObjectScript class syntax** — pulling MUMPS development into the OS class hierarchy and the OS toolchain.
- The wrapper layer is itself a maintenance burden: every MUMPS entry point that needs testing or coverage requires a parallel class method, and the two must be kept in sync by hand.
- The team's tooling investment goes into the wrapper layer (not the MUMPS routines), which compounds IRIS lock-in: the wrappers are non-portable to YottaDB, even though the MUMPS routines they call are portable.

**Implication for a legacy MUMPS codebase.** A 40,000-routine VistA codebase has **effectively zero benefit** from this tooling pattern. To get *partial* coverage of those routines under IRIS's class-based test framework, a team would need to author and maintain tens of thousands of wrapper class files — a multi-year, non-MUMPS-improving effort whose only product is permission to use IRIS's tools on a fraction of the surface. The underlying 40,000 routines remain unlinted, unformatted, undocumented at the language layer, and unaffected by IRIS's developer-experience investment, **regardless of how thorough the wrapper layer becomes**.

**Wrapping doesn't manage MUMPS code; it manages ObjectScript code that happens to call MUMPS.** OS-wrapping is a **severe and serious blocker of MUMPS-side code management**, not a partial fill of the MUMPS-tooling gap. Test code, fixture code, documentation, and dependency manifests are all forced into ObjectScript class syntax. Refactoring tools, code review, and lifecycle automation operate on the wrapper classes, not the underlying routines. The team's tooling investment goes into the wrappers, and the underlying MUMPS routines remain opaque to every OS-tier tool that touches them.

The structural consequence: the IRIS column in the matrix below is scored **None** everywhere the supposed capability is gated by an OS-class wrapper. By the table's MUMPS-only scope (see preface), **"capability available only via an OS-class wrapper" is equivalent to "capability not available to MUMPS code"** — wrapping is scored as **None**, never as Basic or Minimal.

**Legend.** The whole table is MUMPS-only by scope (see preface). The IRIS and YottaDB columns are scored on whether the **implementation ships this functionality**, using bold-text labels (no symbols). The VA / Community column is *informational* — it carries descriptive notes only, not scoring labels. Licensing posture is captured separately in [§1.2](#12-the-two-main-current-implementations) and [§5.2](#52-where-the-engines-diverge-most-sharply).

**For the IRIS and YottaDB columns** (four-level scoring):

- **Full** — the implementation ships a mature, comprehensive equivalent.
- **Basic** — the implementation ships something usable but minimal; works, but well below the gold standard.
- **Minimal** — the implementation provides only a primitive (e.g., `$ZHOROLOG` for benchmarking, bare `ydb` direct-mode for REPL); below "Basic" but not entirely absent.
- **None** — the implementation does NOT ship this functionality, *or* the underlying capability exists but only via an **OS-class wrapper** (see the OS-class-wrapper note above). Per the table's MUMPS-only scope, OS-wrapped capability is not in scope and is scored **None** — never Basic or Minimal. Wrapping is a severe blocker for MUMPS code management, not a bridge to it.

**For the VA / Community column** (informational; no scoring labels — see the scoping caveat above): the cell carries a descriptive note (package name, scope qualifier, or "VistA-shaped" where applicable) when a community / VA package exists, or a short note where nothing widely-known exists. Presence is only *presence* — not parity with gold-standard tools.

**N/A** — concept does not apply at this scope (e.g., type checking on an untyped language).

| Category | Gold Standard | IRIS (MUMPS routine) | YottaDB (`.m`) | VA / Community packages |
|----------|---------------|----------------------|----------------|--------------------------|
| **Runtime / REPL** | History, completion, multiline | **Basic** — `iris terminal` | **Minimal** — `ydb` direct mode (bare; no history / completion) | none |
| **Syntax check** | Per-file, fast, exit-code | **Basic** — routine compile (on first use) | **Basic** — `zcompile` | (`^XINDEX` does deeper static analysis — see Linting rows) |
| **Linting (style)** | Configurable, hundreds of rules | **None** | **None** | `^XINDEX` (VA Toolkit) |
| **Linting (logic)** | Unused vars, unreachable code, missing returns | **None** | **None** | `^XINDEX` (control-flow + reachability) |
| **Type checking** | Full static analysis | **N/A**<br>untyped | **N/A**<br>untyped | **N/A**<br>language-level |
| **Formatting** | Canonical, deterministic, idempotent | **None** | **None** | no canonical formatter |
| **Test runner** | Auto-discovery, parallel, rich output | **None** — `%UnitTest` requires OS-class wrapper — **blocker** for MUMPS code improvement (forces test code into ObjectScript classes; leaves the MUMPS routines themselves untested in any MUMPS-aware sense) | **None** | `%ut` / M-Unit (OSEHRA) |
| **Single-test selection** | Path + name | **None** — only via OS-class wrapper — **blocker** | **None** — only via `%ut` | via `%ut` |
| **Test watcher** | Reruns on save | **None** | **None** | none |
| **Coverage (line)** | HTML + lcov | **None** — `%UnitTest.Coverage` instrumentation works on MAC routines, but the driver requires an OS-class wrapper — **blocker** for MUMPS code improvement | **None** | no widely-adopted community line-coverage tool |
| **Coverage (branch)** | Branch + condition | **None** | **None** | none |
| **Benchmarking** | Statistical, repeatable | **Minimal** — `$ZHOROLOG` primitive only | **Minimal** — `$ZHOROLOG` primitive only | none |
| **Profiling** | Flame graphs, line timing | **Full** — `^%SYS.MONLBL`, `^SystemPerformance` (engine-level; works on any compiled routine) | **None** | none widely-adopted |
| **Debugging (interactive)** | Breakpoints, step, inspect | **Basic** — `ZBREAK` in terminal (Studio / VS Code support is OS-first) | **Basic** — in-runtime `ZBREAK` only | none |
| **Debugging (DAP / IDE)** | DAP server, IDE-agnostic | **Basic** — VS Code extension (routine-level, second-class) | **None** | none |
| **Documentation gen** | Extract comments → HTML / MD | **None** — Documatic is `.cls`-only via `///` convention — to document MUMPS routines requires wrapping them in classes and rewriting comments as `///`, **same OS-class-wrapper blocker pattern** as the test framework (see note above). Not a partial fill — a redirect into ObjectScript that leaves the underlying MUMPS routines undocumented. | **None** | no canonical M-source doc generator |
| **Dependency mgmt** | Lockfile, registry | **None** — IPM is class-centric — no MUMPS-routine manifest unit | **None** | **KIDS** (Kernel Installation & Distribution System; VA Kernel; VistA-shaped) |
| **Build / tasks** | Standard task runner | **Basic** — Makefile around `iris session` | **Basic** — Makefile-only | KIDS install / build workflow (VistA-shaped) |
| **Pre-commit hooks** | Block bad commits before push | **None** | **None** | none |
| **CI pipeline** | One-command full check | **Basic** — Docker + `iris session` (no MUMPS-specific harness) | **Basic** — Makefile-only | none |
| **Snapshot testing** | Compare to baseline; auto-update | **None** | **None** | none |
| **Fixture management** | Composable, scoped test state | **None** — only via OS test class — **blocker** for MUMPS code improvement | **None** | `%ut` setup / teardown |
| **Mock / stub** | Standard library | **None** | **None** | none |
| **Database export** | Portable text format | **Full** — `$SYSTEM.OBJ.Export` (engine-level) | **Full** — `mupip extract` (ZWR / GO) | FileMan-derived utilities (VistA-shaped) |
| **Database import / fixture load** | Load known state | **Full** — `$SYSTEM.OBJ.Import` (engine-level) | **Full** — `mupip load`, `%GI` | FileMan-derived utilities |
| **Database diff** | What changed between runs | **None** | **None** | none |
| **Database state snapshot** | Before/after comparison | **None** — ad-hoc | **None** — ad-hoc | ad-hoc |
| **Crash / lockup cleanup** | Recover from bad process exit | **Full** — SMP / journal recovery (engine-level) | **Full** — `mupip rundown`, `lke` | none |
| **System administration UI** | Web admin | **Full** — System Management Portal | **Basic** — YDBGUI (Vue.js + M backend, since 2022; narrower scope than SMP) | none |
| **Foreign-language API**<br>(see [§4.4](#44-foreign-language-integration-embedded-language-vs-embedded-database)) | First-class FFI | **None** — Native API targets classes; embedded Python is OS-only | **Full** — stable C API; foreign language hosts YDB | no community FFI |
| **Containerised deployment** | Official images | **Full** — InterSystems Docker images | **Basic** — community / marketplace | none |
| **Source-control integration** | Editor + CI hooks | **Basic** — same hooks; `.m` exports as plain text | **Basic** — plain git over `.m` files | VA-internal Forum is not git-like |
| **Symbol introspection** | List functions / exports | **Basic** — `%RD` (routine directory) | **Basic** — `%RD`, manual | `^XINDEX` cross-references; KIDS routine catalog |
| **Security scan** | CVE / advisory check | **None** | **None** | none |
| **Complexity metrics** | Cyclomatic complexity | **None** | **None** | `^XINDEX` complexity output |
| **Dead code detection** | Unused functions / labels | **None** | **None** | `^XINDEX` flags unreferenced labels |
| **Package publishing** | Public registry | **None** — IPM is class-centric | **None** | **KIDS** distributions; **OSEHRA** / **WorldVistA** repositories |

### 5.1 Where both engines fall short of the gold standard

Even taking the union of IRIS, YottaDB, **and** the VA / Community ecosystem, a number of mainstream-language toolchain categories have **no credible answer anywhere in the M world**:

1. **Formatter.** No canonical layout tool exists for M — neither vendor-shipped nor in the community. Style is enforced by convention, code review, and discipline.
2. **Linter (style + logic).** Neither engine surfaces unused variables, unreachable code, missing `QUIT`, undefined labels, or style violations as first-class diagnostics. The `^XINDEX` static analyser **partially** plugs this gap, but it is a VA Toolkit routine — not an InterSystems or YottaDB tool — and is only present where VistA (or a standalone Toolkit install) is available. There is no `ruff`/`clippy`-class linter for general M code.
3. **Test watcher.** No equivalent of `cargo watch` / `pytest-watch` in any tier.
4. **Branch / condition coverage.** IRIS provides line coverage via `%UnitTest.Coverage` (driven from an OS class); neither engine provides branch coverage; nothing in the community fills this.
5. **Benchmarking harness.** Only `$ZHOROLOG`-based primitives; no `criterion` or `pytest-benchmark` analogue.
6. **Snapshot testing.** No equivalent of `jest`'s snapshots or `syrupy`.
7. **Mocking / stubbing.** No framework anywhere.
8. **Database diff / state snapshot.** Critical for testing globals-bound code, absent in both engines and unaddressed by the community.
9. **Complexity metrics.** `^XINDEX` reports some complexity statistics, but not in a form comparable to `radon` / `gocyclo` / `cargo-cyclo`. ◐ partial via XINDEX.
10. **Dead-code detection.** `^XINDEX` flags unreferenced labels — useful, but again partial. No `vulture`-equivalent for M.
11. **Security scanner (M-specific).** No CVE / advisory pipeline targeting M code anywhere in the ecosystem.
12. **Cross-engine, MUMPS-native package manager.** IPM is OS-centric (and so excluded from the MUMPS scope); KIDS is VistA-shaped; YottaDB has nothing first-party. The community has not produced a `npm` / `cargo` / `uv` equivalent for cross-engine MUMPS routines.

The **VA / Community column** in §5's matrix captures where the M ecosystem has real partial fills — most of them anchored on `^XINDEX`, KIDS, and `%ut`. None of these reach the maturity bar of mainstream-language tooling, and they are concentrated in the VistA developer's lifecycle (testing, distribution, static analysis) rather than spread across the full toolchain.

### 5.2 Where the engines diverge most sharply

| Capability | IRIS | YottaDB |
|------------|------|---------|
| **Licensing posture** | Commercial; tooling gated | Open source (AGPL); reproducible without licence negotiation |
| **Primary language surface** | ObjectScript classes (`.cls`) — a proprietary superset | ANSI MUMPS only (`.m`) |
| **IDE story** | Studio (legacy) + VS Code extension, both ObjectScript-first | None; editor-agnostic plain-text workflow |
| **Type system** | Class-typed (ObjectScript classes only) | Untyped (M is untyped by definition) |
| **Profiler** | First-class (`^%SYS.MONLBL`, `^SystemPerformance`) | None integrated |
| **Package manager** | IPM/ZPM (ObjectScript-centric) | None |
| **Documentation generator** | Documatic (ObjectScript-only via `///`) | None |
| **System admin UI** | System Management Portal (decades mature; comprehensive) | YDBGUI + YDBGDEGUI + YDBAdminOpsGUI (Vue.js, M backend, since 2022; younger and narrower in scope) |
| **Embedded other language** | Embedded Python, embedded SQL (inside ObjectScript only) | None |
| **Foreign-language extensibility** | Native API (.NET, Java, Python, Node.js) | C API + bindings (Go, Python, Node.js, Rust, Lua, Perl) |
| **Test framework posture** | First-party `%UnitTest` (ObjectScript classes only) | Community `%ut` (M-Unit) |
| **Documentation availability** | Vendor-controlled, login-gated for some | Public Git repo |

### 5.3 What the MUMPS-only matrix reveals

The matrix above is **deliberately MUMPS-vs-MUMPS only**: ObjectScript is excluded because it isn't MUMPS ([§4.1.1](#411-objectscript-what-it-is-and-why-it-isnt-ansi-standard-mumps)) and tools that target ObjectScript don't help a developer writing pure MUMPS. With that scope enforced and the VA / Community column made explicit, three observations emerge:

**1. The IRIS-vs-YottaDB gap, for MUMPS code, is small.** Once OS-specific tooling is excluded, IRIS's advantages narrow to a handful of engine-level capabilities — the profiler (`^%SYS.MONLBL`), more mature web admin (SMP, decades of accumulated scope), and official Docker images. YDB has matched IRIS on the runtime / admin / database-export tier (YDBGUI, `mupip extract`, etc.); IRIS holds an edge on profiling and container polish. **Neither approaches the gold standard.**

**2. Most of the genuinely MUMPS-aware tooling lives in the VA / Community column, not in either vendor.** `^XINDEX` (static analysis), KIDS (package management and distribution), and `%ut` / M-Unit (testing) are the canonical answers for those concerns in MUMPS. They are pure M source, run on either engine, and predate both vendors' modern tooling efforts. **The MUMPS-aware ecosystem is mostly community / VA-driven, not vendor-driven** — and the vendors have, for different reasons, invested elsewhere (IRIS in ObjectScript; YottaDB in the runtime and the C API).

**3. Even with the VA / Community column, large gaps remain.** Formatter, deeper linter, branch coverage, benchmarking, snapshot testing, mocking, doc generator, true cyclomatic complexity, security scanner, generic / non-VistA package manager — categories where neither vendor *nor* community has a credible answer. These are the gaps that motivate building vendor-neutral, source-level M tooling on a shared parser foundation.

The companion document, [gap-analysis-and-remediation-strategy.md](gap-analysis-and-remediation-strategy.md), describes one such effort grounded in YottaDB but designed to be portable to any conformant M engine via a shared parser foundation ([`tree-sitter-m`](https://github.com/rafael5/tree-sitter-m)) and a vendor-neutral grammar surface ([`m-standard`](https://github.com/rafael5/m-standard)). Because that parser targets the ANSI / pragmatic MUMPS surface (not ObjectScript), tools built on it would fill gaps in **all four** columns of §5's matrix — they would be MUMPS-aware first-party tooling that complements both engines and the VA / Community ecosystem alike.

---

## 6. The Real Question: Developer Experience for a Legacy MUMPS Codebase

The preceding chapters analysed each engine's tooling on its own merits. But the question that motivates most M tooling work is concrete and specific: **what is the developer experience for someone maintaining a large, legacy MUMPS codebase — for example, the U.S. Department of Veterans Affairs' VistA system, with roughly 40,000 routines of pure ANSI MUMPS?**

This question deserves a direct answer, because the engine-level tooling story (§4.1, §4.2) and the language-surface analysis (§3) both miss it. The codebase in question:

- Is overwhelmingly `.m` files — hand-written ANSI MUMPS, decades of accumulated procedural code.
- Has **no `.cls` files**, no `&sql(...)`, no embedded Python, no `##class()`, no `///` doc comments, no `$$$Foo` macros.
- Uses dot-blocks, naked references, `$DATA` / `$ORDER` / `$PIECE` traversals over hierarchical globals — the classical M idiom.
- Conforms primarily to the VA SAC / XINDEX rule set (a stricter subset of ANSI), not to InterSystems-extended ObjectScript.

For this codebase, the question is not "what does ObjectScript give me?" — there is no ObjectScript involved. The question is: **what tooling actually treats my code as MUMPS, and what does my daily edit / test / debug / ship loop look like?**

### 6.1 The IRIS-based VistA scenario

A team adopts IRIS to host a legacy MUMPS codebase. The engine runs the code (IRIS supports the ANSI / pragmatic surface that VistA uses). Engine-level operations work cleanly: the System Management Portal admin UI, journal-based replication, official Docker images, `^%SYS.MONLBL` profiling, `$SYSTEM.OBJ.Export/Import`, and `ZBREAK`-based debugging all function regardless of the source language.

But the **developer-experience layer is mostly inaccessible**, because virtually all of IRIS's language-aware tooling targets ObjectScript. Specifically:

- **`%UnitTest` cannot test the existing routines** without re-casting them, or wrapping them, in ObjectScript classes. A 40,000-routine wrap-and-port effort is not a credible undertaking.
- **Documatic produces nothing** because there are no classes and no `///` doc comments.
- **IPM/ZPM has no manifest unit** — the package manager assumes ObjectScript classes as the unit of distribution.
- **Studio and VS Code provide a bare editor** with syntax highlighting but no MUMPS-specific completions, refactorings, or lints. The IntelliSense is tuned for ObjectScript.
- **The class compiler is irrelevant** — there are no classes.
- **Embedded SQL and embedded Python are unreachable** — both are OS-only language features.

What remains genuinely useful:
- **`^XINDEX`** — VistA's own static analyser (M source from the VA Kernel package). Actually MUMPS-aware and SAC-aware. **Not an IRIS tool** — it is part of the VistA distribution itself, so it is present regardless of which engine hosts VistA.
- **Routine compiler** — catches MUMPS syntax errors at first reference.
- **`^%SYS.MONLBL`** — profiles routines regardless of source language.
- **`ZBREAK` / `ZSHOW` / `ZSTEP`** — manual interactive debugging in the terminal.
- **SMP, journal, Docker, export/import** — engine-level features that don't care about the language.

That is approximately the YottaDB experience plus a profiler, a more mature web admin UI, and official container kits — at the cost of a commercial licence. (YottaDB now ships its own web admin via **YDBGUI**, since r1.36 / 2022, but its scope is narrower than IRIS's SMP.)

### 6.2 The YottaDB-based VistA scenario

YottaDB is pure ANSI MUMPS — it runs a legacy MUMPS codebase without translation. The runtime is mature and POSIX-composable. There is no ObjectScript layer to navigate around, because there is no ObjectScript layer. But there is also **no first-party developer-experience layer**: no formatter, no linter beyond `zcompile`, no test framework, no coverage tool, no profiler, no docs generator, no package manager, no IDE. (The `^XINDEX` static analyser is bundled with VistA itself, so any YottaDB-based VistA deployment has it — it is the same routine that runs on IRIS-based VistA.)

The community fills some gaps — M-Unit (`%ut`) for testing, ad-hoc patterns for everything else — but nothing reaches the polish of mainstream-language tooling.

Compared to IRIS-based VistA, YottaDB-based VistA loses:
- The integrated profiler (`^%SYS.MONLBL`).
- A more mature web admin UI — YottaDB ships **YDBGUI** (Vue.js + M backend, since 2022), but SMP has decades of accumulated scope.
- Some polish in container tooling.

It gains:
- Open-source licensing (AGPL-3.0) — no commercial licence negotiation, fully reproducible CI, no per-developer seat costs.
- `mupip` and YDB-specific recovery utilities (`lke`, `gde`, `dse`).
- A stable, public C API (`libyottadb.so`) with first-party language bindings (Go, Python) and several community bindings (Node.js, Rust, Lua, Perl).
- A public Git documentation tree (no login wall).

### 6.3 Side-by-side summary

> **About the IRIS-based VistA column.** Many of the IRIS rows below collapse to the same underlying fact: **the capability exists in IRIS, but only as an IOS-only feature** — i.e., available to a developer writing IOS classes (`.cls`), not to a developer maintaining `.m` MUMPS routines. Rather than spelling this out five different ways ("requires OS wrapper", "requires OS class", "no class manifest", "OS-first", "OS-tuned"), those rows are simply marked **◯** with a single annotation: **"IOS-only feature."** The structural cause is the same in every case (see [§4.1.3](#413-iris-tooling-by-file-scope-and-language) and the [OS-class-wrapper note in §5](#5-summary-table-mumps-vs-mumps--gold-standard-iris-yottadb-vacommunity)); listing it once is more useful than restating it per row.
>
> **About the VistA tools column.** This column lists VA-supplied M packages — principally **`^XINDEX`** (the VA Kernel Toolkit static analyser) and **KIDS** (Kernel Installation & Distribution System) — that *neither IRIS nor YottaDB ship*. They are bundled with VistA itself and run identically on either engine. Listing them here keeps the IRIS / YottaDB columns honest about what the *engines* ship for MUMPS code, while still acknowledging that a VistA codebase brings its own toolset.

| Capability the team actually needs | Gold standard | IRIS-based VistA | YottaDB-based VistA | VistA tools |
|------------------------------------|---------------|------------------|---------------------|-------------|
| Engine runs the code unmodified | ⬤ | ⬤ | ⬤ | — |
| Static analysis of MUMPS code | ⬤<br>ruff / clippy / staticcheck | ◯<br>none vendor-shipped | ◯<br>none vendor-shipped | `^XINDEX` |
| Test runner over pure MUMPS routines | ⬤ | ◯<br>IOS-only feature | <span style="font-size:1.5em;line-height:1">◐</span><br>community `%ut` (M-Unit) | — |
| Coverage over MUMPS routines | ⬤ | ◯<br>IOS-only feature | ◯<br>community efforts only | — |
| Profiler | ⬤ | ⬤<br>`^%SYS.MONLBL` | ◯<br>none integrated | — |
| Documentation generator | ⬤ | ◯<br>IOS-only feature | ◯<br>none | — |
| Package / dependency mgmt | ⬤ | ◯<br>IOS-only feature | ◯<br>none | KIDS |
| Formatter | ⬤ | ◯<br>none | ◯<br>none | — |
| Linter (style / logic) | ⬤ | ◯<br>none vendor-shipped | ◯<br>none vendor-shipped | `^XINDEX` |
| IDE support for MUMPS source | ⬤ | ◯<br>IOS-only feature | ◯<br>none | — |
| Interactive debugger | ⬤ | <span style="font-size:1.5em;line-height:1">◐</span><br>`ZBREAK` only (IDE step-debugger is an IOS-only feature) | <span style="font-size:1.5em;line-height:1">◐</span><br>`ZBREAK` only | — |
| Web admin UI | **N/A**<br>for runtime languages | ⬤<br>SMP (mature) | ⬤<br>YDBGUI (since 2022; narrower scope) | — |
| Foreign-language API (see [§4.4](#44-foreign-language-integration-embedded-language-vs-embedded-database)) | ⬤ | ◯<br>IOS-only feature | ⬤<br>stable C API; foreign language hosts YDB | — |
| Licensing posture for OSS / community work | ⬤<br>free | ◯<br>commercial; per-seat / instance | ⬤<br>AGPL-3.0; no negotiation | — |

### 6.4 The bottom line

**For a pure-MUMPS legacy codebase, the gap between IRIS and YottaDB is much narrower than the gap between either engine and the gold-standard developer experience of Python, Go, or Rust.** Most of IRIS's tooling investment is consumed by ObjectScript developers, and most of YottaDB's investment goes into the runtime itself. **Neither engine offers a developer experience that approaches what mainstream-language developers consider table stakes.**

This is the structural problem that motivates building **vendor-neutral, source-level M tooling** on top of a shared parser:

- A parser that targets the ANSI / pragmatic MUMPS surface (not ObjectScript) gives every downstream tool — formatter, linter, doc generator, complexity analyser, dead-code detector — the same input on either engine.
- A grammar surface that treats MUMPS as a first-class language (rather than as a mode of ObjectScript or as a secondary file format inside IRIS) is the only way to fill the source-language gaps for legacy MUMPS codebases.
- Vendor neutrality matters because the codebases that need this tooling most — VistA and similarly-shaped systems — must be able to run on either engine without lock-in.

The companion remediation strategy ([gap-analysis-and-remediation-strategy.md](gap-analysis-and-remediation-strategy.md)) describes one such effort, grounded in YottaDB for pragmatic reasons (open-source reproducibility) but designed around a portable parser foundation (`tree-sitter-m`) and a vendor-neutral grammar surface (`m-standard`) so the resulting tools serve the IRIS-MUMPS-routine column equally well as the YottaDB column.

---

## 7. Consolidated Gap Analysis

The §5 and §6.3 matrices score each engine separately. This section flips the perspective and asks the consolidated question: **which gold-standard developer-toolchain categories are missing from *both* engines for pure MUMPS code?**

The table below mirrors the category list from [§2.1 (Python)](#21-python) — the most comprehensive of the five gold-standard toolchain tables — **in the same order**. For each gold-standard category, IRIS-MUMPS and YottaDB statuses are summarised in the four-level scoring convention from [§5](#5-summary-table-mumps-vs-mumps--gold-standard-iris-yottadb-vacommunity) (**Full** / **Basic** / **Minimal** / **None**), and a final column classifies each row by gap severity.

**Gap classification:**

- **MAJOR — common gap** — *both* engines ship **None** for MUMPS code. These are the most severe gaps and the highest-leverage targets for vendor-neutral, source-level M tooling: a single tool built on a shared parser foundation can fill the gap on both engines simultaneously.
- **PARTIAL — common gap** — both engines ship something usable but well below the gold standard (Basic, Minimal, or some combination). Real, but less acute than a Major gap.
- **ENGINE-SPECIFIC** — one engine has a meaningful tool, the other does not. Not a common gap; the absence is single-engine.
- **N/A** — concept does not apply to M (e.g., type checking on an untyped language; import analysis where there is no import system).

**Scoping caveat carries forward:** as established in [§5's preface](#5-summary-table-mumps-vs-mumps--gold-standard-iris-yottadb-vacommunity), none of the IRIS / YottaDB tooling has been formally scoped against the gold-standard exemplars for actual feature parity. The Full / Basic / Minimal labels reflect *engine-shipping maturity*, not *parity with the exemplar*. Quantifying the remaining distance to gold-standard parity is a follow-on project.

| # | Gold-standard category | Exemplar (Python ref) | IRIS (MUMPS) | YottaDB (MUMPS) | Gap classification |
|---|------------------------|-----------------------|:------------:|:---------------:|--------------------|
|  1 | Runtime / REPL          | `ipython`, `ptpython`              | **Basic** — `iris terminal` | **Minimal** — `ydb` direct mode (bare) | **PARTIAL — common gap** |
|  2 | Syntax check            | `ruff`, `py_compile`               | **Basic** — routine compile | **Basic** — `zcompile`                 | **PARTIAL — common gap** |
|  3 | Linting (style)         | `ruff`, `flake8`, `pycodestyle`    | **None**                    | **None**                               | **MAJOR — common gap**   |
|  4 | Linting (logic)         | `pylint`, `ruff`                   | **None**                    | **None**                               | **MAJOR — common gap**   |
|  5 | Type checking           | `mypy`, `pyright`                  | **N/A** — untyped language  | **N/A** — untyped language             | **N/A**                  |
|  6 | Formatting              | `ruff format`, `black`             | **None**                    | **None**                               | **MAJOR — common gap**   |
|  7 | Test runner             | `pytest`, `unittest`               | **None** (IOS-only)         | **None**                               | **MAJOR — common gap**   |
|  8 | Single-test selection   | `pytest tests/x.py::test_y`        | **None** (IOS-only)         | **None**                               | **MAJOR — common gap**   |
|  9 | Test watcher            | `pytest-watch`, `ptw`              | **None**                    | **None**                               | **MAJOR — common gap**   |
| 10 | Coverage                | `coverage.py`, `pytest-cov`        | **None** (driver IOS-only)  | **None**                               | **MAJOR — common gap**   |
| 11 | Benchmarking            | `pytest-benchmark`, `timeit`       | **Minimal** — `$ZHOROLOG`   | **Minimal** — `$ZHOROLOG`              | **PARTIAL — common gap** |
| 12 | Profiling               | `cProfile`, `py-spy`               | **Full** — `^%SYS.MONLBL`   | **None**                               | **ENGINE-SPECIFIC** (IRIS-only) |
| 13 | Debugging               | `pdb`, `ipdb`, `debugpy`           | **Basic** — `ZBREAK` etc.   | **Basic** — `ZBREAK` etc.              | **PARTIAL — common gap** |
| 14 | Documentation           | `pdoc`, `sphinx`, `mkdocs`         | **None** (IOS-only)         | **None**                               | **MAJOR — common gap**   |
| 15 | Dependency mgmt         | `uv`, `pip`, `poetry`              | **None** (IOS-only)         | **None**                               | **MAJOR — common gap**   |
| 16 | Build / tasks           | `make`, `tox`, `nox`               | **Basic** — Makefile + `iris session` | **Basic** — Makefile + `ydb -run` | **PARTIAL — common gap** |
| 17 | Import analysis         | `isort`, `ruff --select I`         | **N/A** — no import system  | **N/A** — no import system             | **N/A**                  |
| 18 | Security scan           | `bandit`, `safety`                 | **None**                    | **None**                               | **MAJOR — common gap**   |
| 19 | Complexity              | `radon`, `ruff`                    | **None**                    | **None**                               | **MAJOR — common gap**   |
| 20 | Dead code               | `vulture`                          | **None**                    | **None**                               | **MAJOR — common gap**   |
| 21 | Fixture management      | `pytest fixtures`, `factory_boy`   | **None** (IOS-only)         | **None**                               | **MAJOR — common gap**   |
| 22 | Snapshot testing        | `syrupy`                           | **None**                    | **None**                               | **MAJOR — common gap**   |
| 23 | Pre-commit hooks        | `pre-commit`                       | **None**                    | **None**                               | **MAJOR — common gap**   |
| 24 | CI script               | `tox`, `nox`, GitHub Actions       | **Basic** — Docker + `iris session` | **Basic** — Makefile + `ydb -run` | **PARTIAL — common gap** |
| 25 | Environment check       | `pyenv`, `tox`                     | **N/A** — no equivalent     | **N/A** — no equivalent                | **N/A**                  |
| 26 | Package publishing      | `twine`, `flit`, `uv publish`      | **None** (IOS-only)         | **None**                               | **MAJOR — common gap**   |

### Tally

Of the **26 gold-standard categories** from §2.1:

- **16 are MAJOR common gaps** — both engines ship **None** for MUMPS code. These are the highest-leverage remediation targets: linting (style and logic), formatting, test runner, single-test selection, test watcher, coverage, documentation, dependency management, security scan, complexity, dead-code, fixture management, snapshot testing, pre-commit hooks, package publishing.
- **6 are PARTIAL common gaps** — both engines ship something below gold standard: runtime/REPL, syntax check, benchmarking, debugging, build/tasks, CI script.
- **1 is ENGINE-SPECIFIC** — IRIS-only: profiling (`^%SYS.MONLBL`).
- **0 are YottaDB-only** — there is no gold-standard category where YottaDB ships a meaningful first-party tool that IRIS lacks (within the MUMPS scope; YottaDB's foreign-language API and YDBGUI are not in §2.1's category list).
- **3 are N/A** — type checking, import analysis, environment check (these don't apply to M).

**22 of the 23 applicable categories are common gaps** (16 major + 6 partial). Only profiling is single-engine. **No category is fully solved on both engines for MUMPS code.**

### Why this consolidation matters

The 16 major common gaps are the strategic high-water mark for M tooling investment. **A single vendor-neutral, source-level tool — built on a shared MUMPS parser foundation (e.g., [`tree-sitter-m`](https://github.com/rafael5/tree-sitter-m)) — can fill each of these gaps for both engines simultaneously.** That is the economy of leverage that justifies treating M as a portable language with portable tooling, rather than as a feature of a vendor's runtime that each vendor solves separately (and neither does for MUMPS code).

The 6 partial common gaps are second-tier targets: tools where both engines ship something usable but below gold standard, so the remediation work is to *augment* rather than to *originate*.

The single engine-specific item (profiling, IRIS-only) is the only category where a remediation effort would be *YottaDB-side only*, with no parallel benefit to IRIS.

This consolidated view is precisely what the companion document [gap-analysis-and-remediation-strategy.md](gap-analysis-and-remediation-strategy.md) builds its sequencing on — the major common gaps are the natural Tier-1 targets for any M-language toolchain effort.

---

## 8. Rank-Ordered Developer Impact: Where to Invest First

The §7 consolidated table inventories *what is missing*. This closing section ranks the same gold-standard categories by **developer impact** — which tools, in absolute terms, do the most to improve **productivity, efficiency, code quality, and rapid code evolution**. The ranking is **independent of which engine implements them**: it asks the universal question, *"if a single tool from this list could be added to a developer's day, which would matter most?"*

The categories cluster into four tiers. Within each tier, ordering is by approximate daily-use frequency × magnitude of impact.

### Tier 1 — The development loop (transformative impact)

These are the tools whose **absence is felt every single edit**. They form the inner loop of modern software development: write code → check it → run a test → see the result. Without them, every other quality activity is harder.

| Rank | Category | Why it sits here |
|------|----------|------------------|
| 1 | **Test runner** | The single most foundational tool. Without a test framework, no quality activity is possible — refactoring is unsafe, CI has nothing to gate on, coverage cannot be measured. Mainstream developers run tests dozens of times per hour; M developers running tests once per session is a defining gap. |
| 2 | **Linter (logic)** | Catches whole categories of bugs (unused vars, unreachable code, missing returns, undefined labels) **at edit time**, before they reach a test or production. Every keystroke is implicitly checked by IDE-integrated linters in mainstream languages; the absence in M means bugs surface only at runtime. |
| 3 | **Formatter** | Eliminates style debate, makes diffs review-friendly, enforces canonical layout that downstream tools (linters, AST analysers) can rely on. Runs invisibly on every save in mainstream languages. |
| 4 | **Single-test selection** | Without it, the test loop devolves to "run all tests, wait, scroll for the relevant failure." With it, the loop is sub-second. The difference compounds over a workday. |
| 5 | **Test watcher** | Auto-rerun on save; sub-second feedback. Once a developer has experienced this loop (Rust's `cargo watch`, Python's `pytest-watch`), going back is painful. |

**Tier 1 summary:** these five tools, used together, are the single biggest developer-experience gap between modern languages and M. They are also tightly coupled — adding any one without the others delivers a fraction of the value.

### Tier 2 — Quality gates and team scaling (high impact)

These tools move quality work from "individual discipline" to "automated guarantee." They are run periodically rather than on every edit, but they are how teams scale quality across many contributors.

| Rank | Category | Why it sits here |
|------|----------|------------------|
| 6 | **CI script** | Every commit gets the full quality battery (lint, format-check, test, type-check). The bedrock of multi-developer collaboration. Currently both engines have *Basic* (Makefile + container); the gap is in CI-shaped harnesses tuned for M. |
| 7 | **Coverage** | Measures test thoroughness; identifies untested code paths. Quality investment compounds when coverage is visible per-PR. |
| 8 | **Linter (style)** | Secondary to logic linting, but pairs with the formatter to enforce a consistent codebase. |
| 9 | **Pre-commit hooks** | Catches lint / format / basic-type errors *before* a bad commit reaches the remote, saving CI cycles and faster feedback. Cheap to implement on top of a linter and formatter. |
| 10 | **Debugger** | When a bug resists static analysis, an interactive debugger (step / breakpoint / inspect) is the canonical recovery tool. Both engines provide `ZBREAK` at the engine level (basic) but lack mainstream IDE-integrated step-debugging for MUMPS code. |

### Tier 3 — Maintenance and ecosystem (medium impact)

These tools become important *after* a project has scale: shared knowledge, shared dependencies, code health over time.

| Rank | Category | Why it sits here |
|------|----------|------------------|
| 11 | **Documentation generator** | Critical for onboarding new contributors and for long-term maintainability. Less daily-use than testing/linting, but every codebase eventually needs it. |
| 12 | **Dependency management** | Becomes critical when projects need to share or consume libraries. For a single-team codebase, less acute; for an ecosystem, indispensable. |
| 13 | **Dead code detection** | Periodic cleanup; identifies labels, routines, and exports no longer referenced. Quality-of-life. |
| 14 | **Complexity metrics** | Code-health monitoring; flags routines that have grown unwieldy. Useful in CI as a "no new complexity above threshold" gate. |
| 15 | **Fixture management** | Test-infrastructure scaffolding that becomes valuable once test runner + single-test selection exist. Without those, fixture management is moot. |

### Tier 4 — Specialised or quality-of-life (lower impact)

These tools matter, but either operate in narrow contexts (performance work, deployment, sharing) or are quality-of-life polish on top of capabilities already minimally present.

| Rank | Category | Why it sits here |
|------|----------|------------------|
| 16 | **Snapshot testing** | Useful for specific patterns (CLI output, generated text); not a daily-use tool for most code. |
| 17 | **Build / tasks** | Both engines already have *Basic* coverage via Makefile. The gap is convenience, not capability. |
| 18 | **Runtime / REPL** | Quality-of-life for exploration; both engines have *something* (Basic / Minimal). Improvements are incremental, not transformative. |
| 19 | **Syntax check** | Already exists at compile time on both engines (*Basic*). Gap is in editor-integrated speed and granular reporting. |
| 20 | **Profiling** | Critical when performance work is on the agenda; idle the rest of the time. IRIS already has *Full* (`^%SYS.MONLBL`); YDB lacks it. Not daily-use. |
| 21 | **Benchmarking** | Only used in performance-critical work. `$ZHOROLOG` covers the primitive case. |
| 22 | **Security scan** | Important pre-deployment, less important pre-commit. Not daily-use. |
| 23 | **Package publishing** | Only matters when sharing artefacts publicly. Until M has a vibrant package ecosystem, this is mostly aspirational. |

### Closing observation

The ranking is steeply skewed toward **Tier 1**. The five tools at the top — test runner, logic linter, formatter, single-test selection, test watcher — are not five separable items but a single integrated **inner loop** that every modern language ecosystem provides and the M ecosystem does not. **Filling those five gaps would close the most consequential portion of the M developer-experience deficit, regardless of which engine the code runs on.** Every tool below them depends on or is amplified by them.

The ranking also confirms a striking economy: **the highest-impact gaps are also the most universal** — they are MUMPS-language gaps, not engine-specific gaps, and they are best filled by source-level tools built on a shared parser foundation. The companion remediation strategy ([gap-analysis-and-remediation-strategy.md](gap-analysis-and-remediation-strategy.md)) prioritises the inner-loop tools first, on exactly this reasoning.

### 8.5 Validation: empirical grounding for the ranking

The ranking above is informed by primary research where empirical data exists, and by engineering judgment where it does not. This subsection documents both — and is honest about the limits of the evidence base, since most research targets mainstream languages, not M.

#### Tier 1 — strongest empirical support

**Test automation as a foundational capability.** The clearest evidence comes from the DORA / Accelerate research programme:

- Forsgren, Humble & Kim (2018), *Accelerate: The Science of Lean Software and DevOps* (IT Revolution). Based on four years of DORA research, **23,000+ respondents from 2,000+ organisations**, identifies **test automation** as one of the technical capabilities *most strongly correlated with high software-delivery performance* — alongside version control, continuous integration, continuous delivery, and loosely-coupled architecture.
- [DORA / Test Automation capability](https://dora.dev/capabilities/test-automation/) summarises the core finding: fast, reliable automated test suites drive *higher software stability, reduced team burnout, and lower deployment pain*.

**Fast feedback loop (test runner + watcher + single-test selection).** Foundational TDD research:

- Erdogmus, Morisio & Torchiano (2005), [*"On the Effectiveness of the Test-First Approach to Programming"*](https://www.researchgate.net/publication/3189711) (IEEE TSE 31(3)). Establishes that the test-first feedback cycle reduces error-detection latency from hours to minutes and bounds the scope of introduced bugs — supporting Tier 1's emphasis on fast iteration.
- Tosi, Lavazza et al. (2017), [*"An industry experiment on the effects of test-driven development on external quality and productivity"*](https://link.springer.com/article/10.1007/s10664-016-9490-0) (Empirical Software Engineering). Industry experiment with 24 professionals; mixed productivity findings but consistent quality improvements.

**Static analysis (linter) impact.** Strong industrial evidence:

- Sadowski, Aftandilian, Eagle, Miller-Cushon & Jaspan (2018), [*"Lessons from Building Static Analysis Tools at Google"*](https://cacm.acm.org/research/lessons-from-building-static-analysis-tools-at-google/) (CACM 61(4)). Documents Google's Tricorder system, which prevents *hundreds of bugs per day* from entering the Google codebase. Confirms static analysis as a high-leverage tool when integrated into the developer workflow — and characterises why ad-hoc bug-filing approaches fail (84% of bugs not fixed) but compiler-integrated checks succeed.

**Linters and formatters in practice.** Industry survey data:

- [Stack Overflow Annual Developer Survey 2024](https://survey.stackoverflow.co/2024/) — among build / dev tools, **Ruff** (Python linter + formatter) scores **84% admired** (highest in its category), and **Cargo** (Rust dep manager + test runner + build tool) scores **83% admired**. Tools that bundle the Tier 1 capabilities consistently rank at the top of developer-satisfaction surveys, supporting their primacy in the ranking.

#### Tier 2 — solid empirical support for CI; coverage is more nuanced

**Continuous integration:**

- Vasilescu, Yu, Wang, Devanbu & Filkov (2015), [*"Quality and productivity outcomes relating to continuous integration in GitHub"*](https://web.cs.ucdavis.edu/~filkov/papers/pr_soc_lan.pdf) (FSE 2015). Large-scale GitHub study: CI-using projects merge PRs significantly faster, and core developers using CI discover more bugs.
- Hilton, Tunnell, Huang, Marinov & Dig (2016), [*"Usage, Costs, and Benefits of Continuous Integration in Open-Source Projects"*](https://dl.acm.org/doi/10.5555/3155562.3155575) (ASE 2016). Documents adoption patterns and quantifies productivity benefits.

**Coverage — a useful signal, not a guarantee:**

- Inozemtseva & Holmes (2014), *"Coverage is Not Strongly Correlated with Test Suite Effectiveness"* (ICSE 2014). Important counter-point: coverage is a useful indicator but does **not** guarantee test quality. This is why Coverage sits at #7 (Tier 2, high impact) rather than Tier 1 — its value is conditional on having good tests already.

**Code review (related to pre-commit hooks):**

- Bacchelli & Bird (2013), *"Expectations, Outcomes, and Challenges of Modern Code Review"* (ICSE 2013). Establishes modern code review as a high-impact quality activity; pre-commit hooks shift some of that work to an earlier, faster checkpoint.

#### Tier 3 / 4 — weaker empirical grounding, more reliance on cross-language consensus

For documentation generators, dependency managers, complexity metrics, and the specialised tools in Tier 4, direct empirical comparison studies are sparse. The ranking here relies on:

- **Cross-language consensus** — every mainstream language (Python, JS/TS, Go, Rust, Java) ships these tools at this approximate level of priority, as documented in [§2's gold-standard tables](#2-the-gold-standard--top-5-language-toolchains).
- **Frequency of daily use** as a proxy — tools that operate periodically (security scan, package publishing) are placed below tools that operate continuously.
- **Stack Overflow Developer Survey** popularity rankings, which consistently place dependency managers (Cargo, uv, npm) among the most-admired tools, validating their Tier 3 placement.

#### The SPACE framework as a sanity check

- Forsgren, Storey, Maddila, Zimmermann, Houck & Butler (2021), [*"The SPACE of Developer Productivity"*](https://queue.acm.org/detail.cfm?id=3454124) (CACM 64(6)). The five SPACE dimensions — **S**atisfaction, **P**erformance, **A**ctivity, **C**ommunication, **E**fficiency — provide a useful sanity check. Tier 1 tools touch all five (they affect satisfaction *and* performance *and* efficiency); lower-tier tools tend to touch one or two. The tier ordering is broadly consistent with SPACE coverage.

#### Limitations and caveats

1. **Most research targets mainstream languages.** M-specific empirical productivity data is scarce. The ranking transfers cross-language conclusions on the assumption that the M development cycle is structurally similar — a defensible but unverified premise.
2. **No empirical study directly compares all 23 categories head-to-head.** The ranking synthesises research where it exists and engineering judgment where it doesn't.
3. **"Productivity" is multi-dimensional.** SPACE makes this explicit: no single metric captures it. The ranking reflects an *unweighted* aggregate across productivity, efficiency, quality, and rapid code evolution. A team weighting one dimension heavily (e.g., a research lab prioritising exploration velocity) would justifiably re-rank some categories.
4. **Ordering *within* a tier is judgment-based.** Cross-tier ordering (Tier 1 above Tier 2 etc.) is research-supported; intra-tier ordering (e.g., test runner #1 vs logic linter #2) is informed by tool-dependency graphs rather than direct comparative studies.

#### Suggested primary sources for follow-up

- Forsgren, Humble & Kim (2018), *Accelerate: The Science of Lean Software and DevOps* (IT Revolution Press)
- DORA's annual *State of DevOps* reports at [dora.dev/research](https://dora.dev/research/)
- Forsgren, Storey et al. (2021), [*"The SPACE of Developer Productivity"*](https://queue.acm.org/detail.cfm?id=3454124) (CACM 64(6))
- Sadowski et al. (2018), [*"Lessons from Building Static Analysis Tools at Google"*](https://cacm.acm.org/research/lessons-from-building-static-analysis-tools-at-google/) (CACM 61(4))
- Vasilescu et al. (2015), [*"Quality and productivity outcomes relating to continuous integration in GitHub"*](https://web.cs.ucdavis.edu/~filkov/papers/pr_soc_lan.pdf) (FSE 2015)
- [Stack Overflow Annual Developer Survey](https://survey.stackoverflow.co/) (annual; useful for tool popularity / satisfaction)
- [JetBrains State of Developer Ecosystem](https://www.jetbrains.com/lp/devecosystem-2024/) (annual; complementary tool-popularity data)

---

*End of m-tool-gap-analysis document.*
