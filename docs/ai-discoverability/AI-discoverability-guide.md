# AI Discoverability Guide for m-dev-tools

**Document type:** Architecture and implementation guide  
**Scope:** How to make the m-dev-tools GitHub organization discoverable,
processable, and usable by AI coding agents  
**Audience:** Maintainers of the m-dev-tools organization and its associated
repositories  
**Primary artifacts:** `.github/profile/llms.txt`,
`.github/profile/tools.json`, `.github/profile/tools.schema.json`

---

## 1. Purpose

The goal is that a newcomer to M (MUMPS) should be able to point Claude, Codex,
or another AI coding agent at the `m-dev-tools` organization and say:

> Use m-dev-tools to create an M application that does XYZ using TDD, CI/CD,
> and the best practices of the m-dev-tools stack.

For that to work, the org needs to expose more than prose documentation. AI
agents need a stable, machine-readable route from user intent to:

- the right repository,
- the right command,
- the right manifest,
- the right local repo instructions,
- the right workflow,
- the right verification gates.

The organizing principle is:

> Humans maintain intent and architecture; tools generate inventory.

Manual prose should explain why the ecosystem exists and how the pieces fit.
Machine-readable manifests should describe what actually exists today.

---

## 2. First Principles: What AI Agents Need

AI agents are effective when a codebase gives them the same affordances that
good language ecosystems give human developers: one obvious entrypoint, a
discoverable command surface, machine-readable metadata, fast feedback, and
repo-local operating instructions.

### 2.1 A Root Entrypoint

Agents need to know where to begin. For m-dev-tools, the root entrypoints are:

- `.github/profile/README.md` for human overview,
- `.github/profile/llms.txt` for compact AI-oriented reading order,
- `.github/profile/tools.json` for machine-readable org routing,
- `.github/profile/tools.schema.json` for validation.

The README answers "what is this?". `llms.txt` answers "what should an AI read
first?". `tools.json` answers "where should this request be routed?".

### 2.2 Intent Routing

Agents do not start with perfect knowledge of repo boundaries. They start with
plain-English requests:

- "create a new M app",
- "parse JSON",
- "write an HTTP client",
- "add a lint rule",
- "explain this M intrinsic",
- "run the test suite",
- "add VS Code hover support".

The org catalog must translate those intents into stable targets:

- `cmd:m-cli#new`,
- `cmd:m-cli#test`,
- `module:m-stdlib#STDJSON`,
- `module:m-stdlib#STDHTTP`,
- `data:m-standard#grammar-surface`,
- `tool:tree-sitter-m`,
- `workflow:tdd_inner_loop`.

This is why `tools.json` has a `task_index`: it is the first lookup table for
AI work.

### 2.3 Machine-Readable Capabilities

Agents need metadata that can be parsed without guessing from prose. Examples:

- command names and arguments,
- lint profiles and rule IDs,
- available STD* modules,
- function signatures,
- examples,
- error catalogs,
- schema versions,
- repo relationships,
- validation commands.

This metadata should live close to the code that owns it, then be aggregated
into the org catalog.

### 2.4 Local Operating Instructions

The org root should not try to encode every local convention. Each repo should
have local agent instructions such as `CLAUDE.md` or `AGENTS.md` that explain:

- setup commands,
- test commands,
- style rules,
- repo-specific guardrails,
- generated files,
- validation gates,
- architectural ownership.

The org catalog routes the agent to a repo. The repo-local instructions tell
the agent how to work there.

### 2.5 Fast Verification

Agents need commands that prove their work. For m-dev-tools, the default
verification loop is:

```bash
m doctor
m test
m fmt --check
m lint
m coverage
```

When a repo has its own gates, those repo-local gates take precedence.

---

## 3. Lessons From Go, Rust, and Python

The m-dev-tools stack is intentionally modeled after the developer experience
of mainstream language tools, especially Go, Rust, and Python.

### 3.1 Go

Go works well for agents and humans because the toolchain is unified:

- `go help` exposes the command surface,
- `go test ./...` gives one obvious test command,
- `go fmt` gives canonical formatting,
- `go vet` gives a standard static analysis pass,
- `go list -json` exposes structured package metadata,
- `go env` exposes environment state.

The m-dev-tools analogue should be:

```bash
m help
m help --json
m capabilities --json
m doctor --json
m test
m fmt
m lint
m coverage
```

### 3.2 Rust

Rust works well because Cargo gives project-level orchestration:

- `cargo new`,
- `cargo test`,
- `cargo fmt`,
- `cargo clippy`,
- `cargo doc`,
- `cargo metadata`.

The m-dev-tools analogue is `m-cli`:

```bash
m new
m test
m fmt
m lint
m doc
m ci init
```

The missing long-term piece is a `cargo metadata` equivalent:

```bash
m metadata --json
m capabilities --json
```

### 3.3 Python

Python's modern toolchain demonstrates the value of machine-readable project
configuration:

- `pyproject.toml` stores tool configuration,
- `ruff` exposes fast lint and format,
- `pytest` standardizes test discovery,
- `coverage.py` emits reports for CI,
- package metadata is introspectable.

The m-dev-tools analogue is:

- `.m-cli.toml` or `[tool.m-cli]` in `pyproject.toml`,
- `m lint`,
- `m fmt`,
- `m test`,
- `m coverage`,
- `m-stdlib` manifest for API discovery.

---

## 4. Target Discoverability Architecture

The intended architecture is layered.

| Layer | Artifact | Owner | Purpose |
|---|---|---|---|
| AI entrypoint | `.github/profile/llms.txt` | `.github` repo | Compact reading order and guardrails |
| Human overview | `.github/profile/README.md` | `.github` repo | Explains ecosystem and repository roles |
| Org catalog | `.github/profile/tools.json` | generated in `.github` repo | Intent to repo/tool/module/workflow routing |
| Catalog schema | `.github/profile/tools.schema.json` | `.github` repo | Contract for `tools.json` |
| Repo metadata | per-repo `tool.meta.json` or command JSON | each repo | Source of truth for repo capabilities |
| API metadata | `m-stdlib/dist/stdlib-manifest.json` | `m-stdlib` | STD* modules, labels, signatures, examples |
| Language metadata | `m-standard/integrated/*` | `m-standard` | Commands, functions, ISVs, errors, grammar surface |
| Parser metadata | generated parser/package metadata | `tree-sitter-m` | AST/parser capabilities and bindings |
| Local instructions | `CLAUDE.md` or `AGENTS.md` | each repo | How to work in that repo |

The org catalog should be the master index, but not the master source for every
detail. It should aggregate details from the owning repos.

---

## 5. Canonical Root Files

### 5.1 `llms.txt`

`llms.txt` is the small, high-signal doorway for AI agents. It should point to:

- the profile README,
- `tools.json`,
- `tools.schema.json`,
- `m-cli`,
- `m-cli/CLAUDE.md`,
- `m-cli` guide,
- `m-stdlib`,
- `m-stdlib` manifest,
- `m-standard`,
- `m-standard` grammar surface,
- `tree-sitter-m`,
- `m-test-engine`,
- historical gap-analysis docs.

It should also include guardrails:

- use `m-stdlib` before duplicating runtime helpers,
- use `m-standard` for language semantics,
- use `tree-sitter-m` for parser behavior,
- do not invent STD* APIs or `m` commands.

### 5.2 `tools.json`

`tools.json` is the machine-readable master index for the org. It should
answer:

- What repos exist?
- What does each repo own?
- What commands or modules does each repo expose?
- Which repos consume or produce which metadata?
- Which task should start in which repo?
- What workflow should an agent follow for a new app?

Important sections:

- `org`
- `tools`
- `task_index`
- `workflow`
- `discovery_protocol`

### 5.3 `tools.schema.json`

The schema makes `tools.json` enforceable. It should validate:

- required top-level keys,
- tool entries with `repo` and `role`,
- workflow steps,
- stable IDs,
- machine-readable links,
- allowed reference shapes.

The schema should be permissive for additive fields, but strict for fields that
agents depend on.

---

## 6. Stable IDs

Stable IDs prevent ambiguity. A string such as `m-cli#test` is useful, but it
does not say whether the target is a tool, command, module, task, document, or
workflow. Prefer typed IDs.

Recommended ID forms:

```text
tool:m-cli
cmd:m-cli#test
cmd:m-cli#ci.init
module:m-stdlib#STDJSON
doc:m-dev-tools#m-tool-gap-analysis
data:m-standard#grammar-surface
workflow:tdd_inner_loop
task:workflow.scaffold_new_project
```

Implementation sequence:

1. Add `id` to every top-level tool entry.
2. Add `id` to every `m-cli` subcommand.
3. Add `id` to every `m-stdlib` module summary.
4. Add `id` to every task in `task_index`.
5. Migrate `primary` and `see_also` fields to typed IDs.
6. Preserve old references in `aliases` during the transition.
7. Update `tools.schema.json` to require IDs.

Recommended schema pattern:

```json
{
  "catalogId": {
    "type": "string",
    "pattern": "^(tool|cmd|module|doc|data|workflow|task):[a-z0-9._-]+(#[A-Za-z0-9._-]+)?$"
  }
}
```

---

## 7. Metadata Ownership Model

To keep metadata accurate as repos change, do not hand-maintain the full org
catalog. Use repo-local sources of truth and generate the aggregate catalog.

### 7.1 Repo-Local Sources

Recommended ownership:

| Repo | Source of truth |
|---|---|
| `m-cli` | `m capabilities --json`, `m help --json`, lint profile JSON |
| `m-stdlib` | `dist/stdlib-manifest.json` |
| `m-standard` | `integrated/*.json`, `integrated/*.tsv` |
| `tree-sitter-m` | parser metadata, package metadata, grammar surface input |
| `m-test-engine` | container/tool metadata |
| VS Code repos | package metadata plus extension contribution metadata |
| `.github` | generated org catalog, schema, `llms.txt`, profile README |

### 7.2 Generated Org Catalog

Add a generator in the `.github` repo, for example:

```text
.github/profile/scripts/build-tools-json.py
```

The generator should:

1. read repo-local manifests,
2. read `m-stdlib/dist/stdlib-manifest.json`,
3. read `m-cli` command capabilities,
4. read `m-standard` machine-readable references,
5. emit `.github/profile/tools.json`,
6. validate against `.github/profile/tools.schema.json`.

### 7.3 Drift Checks

Every repo should fail CI if generated metadata is stale.

Examples:

```bash
make manifest
git diff --exit-code dist/stdlib-manifest.json
```

For the `.github` repo:

```bash
make catalog
python -m json.tool profile/tools.json
python -m json.tool profile/tools.schema.json
python scripts/validate-tools-json.py
git diff --exit-code profile/tools.json
```

---

## 8. Desired Per-Repo Contracts

### 8.1 `m-cli`

`m-cli` should become self-describing.

Recommended commands:

```bash
m help --json
m capabilities --json
m doctor --json
m lint --list-profiles --json
m manifest --json
```

The JSON should include:

- subcommands,
- options,
- examples,
- config files,
- output formats,
- lint profiles,
- rule IDs,
- pre-commit hooks,
- verification commands,
- consumed manifests.

### 8.2 `m-stdlib`

`m-stdlib` should keep `dist/stdlib-manifest.json` as the detailed API source
of truth.

The org catalog should not manually duplicate all module details. It should
store a summary and a manifest pointer:

```json
{
  "id": "tool:m-stdlib",
  "manifest": "https://raw.githubusercontent.com/m-dev-tools/m-stdlib/main/dist/stdlib-manifest.json",
  "module_count": 32,
  "categories": ["testing", "data", "text", "io", "network"]
}
```

As the stdlib grows, the manifest drives:

- `m doc`,
- `m search`,
- `m examples`,
- `m errors`,
- VS Code hover/goto/completion,
- org catalog summaries.

### 8.3 `m-standard`

`m-standard` owns language semantics. Agents should use it for:

- command names,
- intrinsic functions,
- intrinsic special variables,
- operators,
- errors,
- grammar surface,
- ANSI/YottaDB/IRIS/SAC compatibility.

The org catalog should link to the machine-readable integrated outputs, not
copy the tables.

### 8.4 `tree-sitter-m`

`tree-sitter-m` owns parser and AST behavior. Agents should use it when work
involves:

- grammar changes,
- parse errors,
- AST node types,
- syntax highlighting,
- parser bindings,
- editor integration.

The catalog should identify which repos consume it, especially `m-cli` and
`tree-sitter-m-vscode`.

### 8.5 `m-test-engine`

`m-test-engine` owns the lightweight YottaDB runtime substrate. Its metadata
should describe:

- image name,
- container name,
- mount path,
- lifecycle commands,
- smoke checks,
- destructive cleanup commands,
- relationship to heavier VistA infrastructure.

### 8.6 Editor Repos

VS Code repos should expose:

- extension ID,
- marketplace publisher,
- settings,
- commands,
- consumed manifests,
- language-server launch behavior.

---

## 9. Agent Discovery Protocol

An AI agent should follow this order:

1. Read `.github/profile/llms.txt`.
2. Read `.github/profile/tools.json`.
3. Match user request to `task_index`.
4. Resolve typed `primary` and `see_also` IDs into `tools`.
5. Load the owning repo README and `CLAUDE.md` or `AGENTS.md`.
6. Load machine-readable manifests for symbol-level work.
7. Use `workflow.tdd_inner_loop` for new app work.
8. Make changes in the owning repo.
9. Run nearest verification gates.
10. If a command/API/token is absent from the manifests, state the gap rather
    than inventing it.

This protocol should live in both prose and machine-readable form:

- prose in this guide and `llms.txt`,
- machine-readable instructions in `tools.json.discovery_protocol`.

---

## 10. Priority Roadmap

### Phase 0: Completed Foundation

Status: done or started.

- Add `.github/profile/tools.json`.
- Add `.github/profile/llms.txt`.
- Add `.github/profile/tools.schema.json`.
- Add `$schema` pointer to `tools.json`.
- Add initial `discovery_protocol` to `tools.json`.
- Keep `.github/profile/README.md` as the human-facing overview.

### Phase 1: Harden the Current Catalog

Priority: immediate.

Tasks:

1. Add typed stable IDs to tools, commands, modules, tasks, workflows, docs, and
   data sources.
2. Migrate `primary` and `see_also` references to typed IDs.
3. Keep old references as `aliases` temporarily.
4. Tighten `tools.schema.json` to validate IDs.
5. Add a lightweight `validate-tools-json.py` script.
6. Add a Makefile target in `.github`:

```bash
make validate-catalog
```

### Phase 2: Make Repos Self-Describing

Priority: high.

Tasks:

1. Add `m capabilities --json` to `m-cli`.
2. Add `m help --json` to `m-cli`.
3. Add JSON output to lint profile listing.
4. Ensure `m-stdlib` manifest includes module/category/function/example/error
   metadata needed by agents.
5. Add or normalize repo-local metadata files for non-CLI repos.
6. Ensure every repo has `CLAUDE.md` or `AGENTS.md`.

### Phase 3: Generate `tools.json`

Priority: high.

Tasks:

1. Add `.github/profile/scripts/build-tools-json.py`.
2. Pull summaries from repo-local metadata.
3. Pull STD* module summaries from `m-stdlib` manifest.
4. Pull language metadata pointers from `m-standard`.
5. Pull command metadata from `m-cli`.
6. Emit deterministic JSON.
7. Validate generated JSON.
8. Fail CI if generated output is stale.

### Phase 4: Add CI Enforcement

Priority: high.

Tasks:

1. Add `.github` repo CI for JSON parse and schema validation.
2. Add stale-catalog check.
3. Add per-repo checks for generated manifests.
4. Add link checks for raw manifest URLs and docs URLs.
5. Add schema-version compatibility checks.

### Phase 5: Improve Agent Usability

Priority: medium.

Tasks:

1. Add task recipes:

```text
.github/docs/recipes/new-app-tdd-ci.md
.github/docs/recipes/add-stdlib-module.md
.github/docs/recipes/add-lint-rule.md
.github/docs/recipes/add-editor-support.md
```

2. Add generated `AI-INDEX.md` from `tools.json`.
3. Add examples showing complete agent flows:
   - new app,
   - JSON parsing,
   - HTTP request,
   - adding a lint rule,
   - adding a STD* module.
4. Add "do not invent" failure examples and correct routing.

### Phase 6: Publish and Consume Metadata Everywhere

Priority: medium.

Tasks:

1. Ensure `m-cli` can consume the org catalog when useful.
2. Let editor integrations surface catalog links.
3. Let docs pages link back to stable IDs.
4. Use stable IDs in issues, PR templates, and changelogs.
5. Publish versioned catalog snapshots if external tools start depending on
   them.

---

## 11. Recommended File Layout

Target `.github` repo layout:

```text
.github/
  CONTRIBUTING.md
  docs/
    AI-discoverability-guide.md
    recipes/
      new-app-tdd-ci.md
      add-stdlib-module.md
      add-lint-rule.md
      add-editor-support.md
  profile/
    README.md
    llms.txt
    tools.json
    tools.schema.json
    AI-INDEX.md
    scripts/
      build-tools-json.py
      validate-tools-json.py
```

---

## 12. Maintenance Rules

1. Do not hand-copy detailed API inventory into `tools.json` when a repo-local
   manifest exists.
2. Keep detailed STD* function metadata in `m-stdlib`.
3. Keep language semantics in `m-standard`.
4. Keep parser details in `tree-sitter-m`.
5. Keep command behavior in `m-cli`.
6. Keep org-level routing in `.github/profile/tools.json`.
7. Use schema versions for every machine-readable contract.
8. Prefer additive schema changes under version 1.
9. Bump schema version only when existing consumers would break.
10. Make generated metadata deterministic and CI-checked.

---

## 13. Success Criteria

The refactor is successful when an AI agent can:

1. start at `llms.txt`,
2. read `tools.json`,
3. route a user request to the correct repo and command,
4. load repo-local instructions,
5. use manifests for APIs and language facts,
6. scaffold an M project,
7. write a failing test,
8. implement using `m-stdlib`,
9. run `m test`, `m fmt --check`, `m lint`, and `m coverage`,
10. avoid inventing APIs or commands that are not in the catalog.

For a newcomer, the intended experience should feel closer to Go, Rust, or
modern Python than to historical M tooling:

- one obvious command surface,
- one obvious test runner,
- one obvious formatter,
- one obvious linter,
- one obvious standard-library manifest,
- one obvious AI-readable org index.

