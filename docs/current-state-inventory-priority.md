# Current-State Inventory and Priority

**Supplements:** [`AI-discoverability-plan.md`](AI-discoverability-plan.md) §3.4
**Purpose:** Replace the tier-1 / tier-2 / tier-3 "do these in order" framing
from §3.4 with a **dependency-graph-driven priority** based on actual
work-still-remaining and how many downstream items each one unblocks.
**Premise:** "Do the easiest thing next" is a local minimum. "Do the
highest-leverage thing next" — the item with the most downstream
dependents — wins on global progress.

---

## 1. What's changed since §3.4 was written

§3.4 (in `AI-discoverability-plan.md`) was authored when *no* repo
shipped the Phase-0 contract. It correctly framed tier-1 as the
foundation. With tier-1 + tier-2 now done, that table is **stale as a
priority guide** (it still reads correctly as historical context).

| §3.4 framing | Reality on 2026-05-10 |
|---|---|
| "tier-1 repos must satisfy the §3 contract before any org-level work" | All three tier-1 + all three tier-2 repos now do. |
| "Until tier-1 emits machine-readable artifacts, the org catalog is fiction." | Catalog is no longer fiction — `phase0-smoke` is green against all six published manifests. |
| Priority = tier-richness ("biggest leverage win") | Now: priority = downstream-dependents (which next action unblocks the most others). |

---

## 2. Current-state inventory

### 2.1 Repos that ship the Phase-0 contract today

Every one of these has, on `main`: `AGENTS.md` (canonical) + `CLAUDE.md`
symlink + `dist/repo.meta.json` validating against the org schema +
`make check-manifest` + `make check-docs-prose` + CI wired.

| Repo | Tier | `exposes.*` payloads | Verified |
|---|---|---|---|
| `m-cli` | 1 | `commands` · `lint_rules` · `fmt_rules` (3 generated JSONs in `dist/`) | Phase-0 smoke ✓ |
| `m-stdlib` | 1 | `modules` · `errors` (2 generated JSONs in `dist/`) | Phase-0 smoke ✓ |
| `m-standard` | 1 | 9 payloads under `integrated/` (commands.tsv, grammar-surface.json, …) | Phase-0 smoke ✓ |
| `tree-sitter-m` | 2 | `node_types` · `grammar` · `grammar_metadata` (3 generated JSONs in `src/`) | canonical Track-A validator ✓ |
| `m-modern-corpus` | 2 | `manifest` · `stats` (generated from corpus subdirs) · `licenses` | canonical Track-A validator ✓ |
| `m-test-engine` | 2 | `lifecycle` (hand-authored) · `dockerfile` · `compose` | canonical Track-A validator ✓ |

### 2.2 Repos that do NOT yet ship the Phase-0 contract

These are the **tier-3** repos from §3.4. None has `AGENTS.md` or
`dist/repo.meta.json`.

| Repo | Notes |
|---|---|
| `tree-sitter-m-vscode` | Has `CLAUDE.md` (not yet `AGENTS.md`); `package.json` declares the extension. |
| `m-stdlib-vscode` | No `CLAUDE.md`, no `AGENTS.md`, no `dist/`. |
| `m-cli-extras` | No `CLAUDE.md`, no `AGENTS.md`, no `dist/`. Plugin host. |

### 2.3 Org-level (.github) state

| Surface | State |
|---|---|
| `profile/repo.meta.schema.json` | Published — `additionalProperties: false`, typedID regex in `exposes` description. **Not yet enforced everywhere** (typedID regex hoisted into `$defs` only partly — see Phase-1 Track A2). |
| `profile/build/validate-repo-meta.py` | Track A — done; `.git`-ancestor walk + raw-GitHub URL resolver land. |
| `profile/build/phase0-smoke.py` | Track E — done; `make phase0-smoke` green against `main` URLs. |
| `profile/tools.json` | **Hand-curated, 354 lines.** Mixes intent-routing (`task_index`) with summary (`tools.*`) with inlined facts (subcommand lists, module counts) — Phase-1 Track A scope is to split + slim. |
| `profile/task_index.json` | Doesn't exist yet — it's still embedded in `tools.json`. Phase-1 Track A4 extracts it. |
| `profile/llms.txt` | 49 lines — doesn't quite match llmstxt.org strict form (Phase-1 Track C). |
| `make catalog` + `make validate-catalog` | Don't exist as real generators yet. `make validate-catalog` runs `python -m json.tool` (parse-only). Phase-1 Track D. |
| `make check-docs-prose` | ✓ live, blocking PRs. |
| `make phase0-smoke` | ✓ live, manual-trigger. |

### 2.4 Cross-repo guardrails active today

| Gate | Where | Effect |
|---|---|---|
| `make check-docs-prose` | every tier-1 + tier-2 repo + `.github` | `docs/` non-prose fails the build (one-time fix per repo + future guard) |
| `make check-manifest` | every tier-1 + tier-2 repo | Manifest invariants fail the build |
| `phase0-smoke` | `.github` (manual) | Every published manifest's `exposes.*` resolves |
| Layout-conventions doc | `.github/CONTRIBUTING.md` + each AGENTS.md | Standardizes the dir conventions across repos |

---

## 3. Outstanding work — every undone item

Pulled from the parent plan's §7 "Phased Execution" and `phase1-plan.md`,
filtered to what's *actually* not done as of 2026-05-10.

### 3.1 In `.github` (org routing layer — Phase 1)

| ID | Description | Source |
|---|---|---|
| **P1-A** | Tighten `tools.schema.json` (typedID regex everywhere, drop inlined-facts allow, split `schema_compat`/`schema_version`) + add `task_index.schema.json` + extract `task_index.json` + slim `tools.json` to summary shape | [phase1-plan.md §2](phase1-plan.md) |
| **P1-B** | TDD `build-catalog.py` + `validate-catalog.py` | [phase1-plan.md §3](phase1-plan.md) |
| **P1-C** | Rewrite `llms.txt` to strict llmstxt.org form | [phase1-plan.md §4](phase1-plan.md) |
| **P1-D** | `make catalog` + real `make validate-catalog` + CI wiring | [phase1-plan.md §5](phase1-plan.md) |
| **P1-X** | Add `schema-changelog.md` row for the `additionalProperties: false` tightening | [phase1-plan.md §8 risk](phase1-plan.md) |

### 3.2 In tier-3 repos (Phase-0 contract adoption)

| ID | Description |
|---|---|
| **T3-vscode-ts** | Onboard `tree-sitter-m-vscode` (rename CLAUDE.md → AGENTS.md, `dist/repo.meta.json` pointing at `package.json` + `syntaxes/`, Makefile gates, CI) |
| **T3-vscode-stdlib** | Onboard `m-stdlib-vscode` (start from scratch — no CLAUDE.md to rename) |
| **T3-extras** | Onboard `m-cli-extras` (plugin host — `dist/repo.meta.json` exposes plugin entry-points JSON) |

### 3.3 In `.github` (agent-operability — Phase 3)

| ID | Description |
|---|---|
| **P3-recipes** | The seven priority recipes (new-app-tdd-ci, use-stdlib-module, add-stdlib-module, add-lint-rule, add-m-cli-command, investigate-failure, add-editor-support) |
| **P3-handshake** | `profile/build/test-discovery-protocol.py` — the end-to-end §9 success-criteria test |

### 3.4 In `.github` + external (MCP — Phase 4)

| ID | Description |
|---|---|
| **P4-mcp** | `m-dev-tools-mcp` PyPI package — wraps `tools.json` + `task_index.json` + discovery protocol with `route_intent`/`describe`/`verify` |

### 3.5 In `.github` (continuous enforcement — Phase 5)

| ID | Description |
|---|---|
| **P5-freshness** | `make check-freshness` — fail if any `verified_on` > 90 days |
| **P5-links** | `make check-links` — HEAD every URL in `tools.json` + `llms.txt` |
| **P5-licenses** | `make check-licenses` — reconcile `license` field with `gh api repos/...` |
| **P5-schema-version** | CI check: non-additive `*.schema.json` change → require `schema_compat` bump + `schema-changelog.md` row |

---

## 4. Dependency graph

```
            ┌─────────────────────────────────────────────────┐
            │                  P1-A                           │  (schemas + task_index split)
            │  Foundation — without this nothing else makes   │
            │  sense; downstream consumers need stable        │
            │  schema + a clean task_index source             │
            └─────────────────┬───────────────────────────────┘
                              │
                ┌─────────────┼────────────────┐
                ▼             ▼                ▼
       ┌──────────────┐ ┌──────────┐  ┌────────────────┐
       │    P1-B      │ │  P1-C    │  │ T3-* (×3)      │   (parallel-safe: B is .github;
       │ build/       │ │ llms.txt │  │ tier-3 repos   │    T3 is per-repo; C is
       │ validate     │ │          │  │                │    independent)
       │ catalog      │ │          │  │                │
       └──────┬───────┘ └─────┬────┘  └────┬───────────┘
              │               │            │
              └───────┬───────┘            │
                      ▼                    │
              ┌────────────┐               │
              │    P1-D    │               │
              │ make +     │               │
              │ CI wiring  │               │
              └─────┬──────┘               │
                    │                      │
                    ▼                      │
              ┌──────────────────────────┐ │
              │  Phase 1 EXIT            │◀┘  (T3 manifests get picked up by P1-B
              │  (= Phase 2 mechanical-  │     once that ships; no extra wiring)
              │  pickup verified)        │
              └─────────┬────────────────┘
                        │
              ┌─────────┼────────────┐
              ▼         ▼            ▼
        ┌─────────┐ ┌────────┐ ┌──────────────┐
        │ P3-*    │ │ P4-mcp │ │ P5-* (×4)    │
        │ recipes │ │        │ │ continuous   │
        │ +       │ │        │ │ enforcement  │
        │ hand-   │ │        │ │              │
        │ shake   │ │        │ │              │
        └─────────┘ └────────┘ └──────────────┘
                                       ▲
                                       │
                                  ┌────┴────┐
                                  │ P1-X    │  (schema-changelog —
                                  │ (small) │   prerequisite for P5-schema-version)
                                  └─────────┘
```

---

## 5. Priority by downstream leverage

Each row's "Downstream" column counts how many *other items in this list*
are unblocked by completing it. Ties broken by external-visibility
(does an AI agent see a difference?).

| Rank | Item | Downstream count | What completing it unblocks |
|---|---|---|---|
| **1** | **P1-A** (schemas + task_index split) | **6** | P1-B, P1-D, P3-handshake, P4-mcp, P5-schema-version, the entire downstream MCP ↔ catalog story |
| **2** | **P1-B** (build-catalog + validate-catalog) | **5** | P1-D, T3-* mechanical pickup, P4-mcp data source, P5-links (over generated catalog URLs), Phase-2 exit criterion |
| **3** | **P1-D** (make catalog + CI wiring) | **3** | Phase-1 exit, P5-freshness (needs `verified_on` enforcement loop), P5-schema-version |
| **4** | **T3-* onboarding (×3)** | **0 formal, +1 for Phase-2 exit** | Each tier-3 repo is independent — but once they ship `dist/repo.meta.json`, P1-B picks them up *for free* on the next catalog run. The "0 downstream" is technically right; the **timing leverage** is high if done *while* P1-B is in flight. |
| **5** | **P1-C** (llms.txt → llmstxt.org) | **1** | P1-D (link-check on llms.txt URLs); high agent-visibility independently. |
| **6** | **P3-handshake** (`test-discovery-protocol.py`) | **0** | Exits §9 success criteria 1–4 mechanically. Catches link rot. Terminal but valuable. |
| **7** | **P3-recipes** (×7) | **0** | Exits §9 success criteria 5–7. Highest agent-facing-deliverable value; not blocked by anything but Phase 1. |
| **8** | **P4-mcp** | **0** | Turns the catalog into a protocol surface. External leverage (Claude/Codex/Continue point at it directly). |
| **9** | **P5-* (×4)** | **0** | Continuous enforcement — drift-rot prevention. |
| **10** | **P1-X** (schema-changelog) | **+1 for P5-schema-version** | One-line file; precondition for P5-schema-version's CI check to make sense. Trivial to ship alongside P1-A. |

**Ties broken by external visibility:**

- T3-* ranks higher than P1-C numerically because completing it makes the
  catalog richer once P1-B exists. P1-C's downstream is technically only
  P1-D; T3-*'s downstream is "everything visible through the catalog."
- P3-recipes ranks above P4-mcp because recipes are what an agent *uses*;
  MCP is the *protocol* for finding them. Recipes work without MCP; MCP
  is hollow without recipes.

---

## 6. Recommended execution order

### 6.1 The dependency-driven sequence

```
1.  P1-A             [SINGLE-THREADED — foundation]
                     ↓
2.  P1-B   ∥   P1-C   ∥   T3-* (×3)     [PARALLEL — different files / different repos]
                     ↓
3.  P1-D             [INTEGRATES B + C; final Phase 1 gate]
                     ↓
4.  P3-handshake ∥ P3-recipes (start)   [PARALLEL — handshake is one script; recipes are 7 files]
                     ↓
5.  P4-mcp           [external package; can defer behind P5]
                     ↓
6.  P5-* (×4)        [continuous enforcement; layer in as cron jobs]
                     ↓
7.  P1-X if not already bundled into P1-A
```

### 6.2 What this gets you per merge

| After completing | You can do | You cannot yet do |
|---|---|---|
| P1-A | Ship anything that needs a tight schema (P1-B testing, T3-* validators, P5-schema-version stub) | Run the catalog generator; agents can't follow `task_index` from the canonical home yet |
| P1-A + P1-B + T3-* | Run `build-catalog.py` against all 9 repos and get a generated `tools.json` covering tier-1+2+3 | Detect catalog drift in CI; gate on it |
| Phase 1 EXIT (after P1-D) | Schedule `build-catalog` regenerations, gate drift in CI, point any agent at the org URL and have it route to a repo | Agent can't yet follow `task_index.intent → typed-ID → exposes.*` end-to-end with smoke proof |
| + P3-handshake | Catch broken links + schema drift weekly in CI | Agent can't yet run an end-to-end TDD recipe |
| + P3-recipes | Hit every §9 success criterion mechanically | — |
| + P4-mcp | Claude/Codex/Continue native protocol surface | — |
| + P5-* | Drift-rot prevention on a 7-day SLA | — |

### 6.3 Parallelism opportunities — do these together if you have the bandwidth

- **P1-B and T3-\* (×3) and P1-C** — four independent work surfaces.
  P1-B is in `.github/profile/build/`; T3-* is in three separate repos;
  P1-C is `.github/profile/llms.txt`. **No file overlap → no merge
  conflicts.** Maximum parallelism here.
- **P3-handshake and P3-recipes** — handshake is one script in
  `.github/profile/build/`; recipes are seven Markdown files in
  `.github/docs/recipes/`. Parallel-safe.

### 6.4 The "easy first" temptation and why it's wrong here

The easy items are: **P1-C** (llms.txt rewrite, ~40 lines), **P3-recipes**
(prose-only Markdown), **T3-* onboarding** (mechanical, pattern already
proven). All three feel productive — there's a draft PR within an
hour. None of them **unblocks anything else**.

Spending a week on three easy PRs (P1-C + two T3 onboardings) leaves
you with no `build-catalog.py`, no tightened schemas, and the catalog
still hand-curated and drift-prone. The same week spent on P1-A
unblocks **six downstream items**, after which the easy work can run
in parallel against the new contract and pick itself up mechanically.

The Phase 0 + Phase 2 work in this org has been dependency-ordered for
this exact reason — and it's why everything since 2026-05-09 has
landed cleanly without rework.

---

## 7. Recommended **next** move

**Ship P1-A as a single coherent PR in `.github`.**

Concretely:

1. Author the audit note for `phase1-plan.md` § A1 (1 paragraph in PR body).
2. Tighten `profile/tools.schema.json` per Track A2.
3. Add `profile/task_index.schema.json` per Track A3.
4. Extract `profile/task_index.json` from `tools.json` per Track A4.
5. Slim `profile/tools.json` to summary shape per Track A5.
6. Create `profile/schema-changelog.md` with one row noting the
   non-additive tightening (folds **P1-X** into the same PR).
7. Verify with `check-jsonschema` against the new schemas (A6).
8. Single PR, single commit, `phase1-A: schema tightening + task_index split + schema-changelog`.

After that, **kick off P1-B, P1-C, and T3-* in parallel** — three
independent threads that all sit on the new schema.

That sequence cuts the longest dependency chain (the only one that
sits in front of the entire Phase 1 + 3 + 4 stack) in a single ship —
which is the precise pattern that makes "highest-leverage first"
outperform "easiest first."

---

## 8. How to use this doc

- Treat it as the single source of truth for "what's left and what
  unblocks what" until Phase 1 lands.
- Update §2 when a repo's contract changes (e.g. tier-3 onboarding
  lands).
- Update §3 when an item ships (move it from outstanding → §2).
- Reframe §5 if a real dependency changes (e.g. if P4-mcp turns out
  to need something from P3-handshake, edit the graph in §4 and the
  rank in §5).
- The doc is meant to be **read-then-act**. If you find yourself
  reading it without acting on §7, the next move is to fix §7 (the
  recommendation is wrong) or commit to executing it.
