# Parallel multi-repo git hygiene

> *Why parallel Claude sessions across the m-dev-tools org cause "git problems," and the workflow that eliminates them.*

This doc captures the diagnostic findings from a session that
investigated why concurrent agent work across `m-cli`, `m-stdlib`,
`m-test-engine`, … felt brittle around `git commit` / `git push` /
branch coordination, and the working agreement we settled on.

## TL;DR

1. The 12 sub-repos under `~/m-dev-tools/` are **fully independent git
   repos**. No submodules, no shared `.git`. Concurrent commits in
   different repos cannot collide at the git layer.
2. The pain is **not** a git-engine race. It comes from a **scope
   confusion**: a single agent session edits across repo boundaries,
   and a *different* parallel session then sweeps the stray edits into
   the wrong commit.
3. The fix is procedural, not technical: **one Claude session ↔ one
   repo ↔ one branch**, launched from inside the sub-repo. Cross-repo
   features happen *sequentially*, leaves first.
4. A small set of cheap guardrails (workspace tripwire CLAUDE.md, per-
   repo pytest cache pin, `make scope-check`) catches the residual
   mistakes early.

## The org as three tiers

```
~/m-dev-tools/                  ← workspace dir (NOT a git repo)
├── .github/                    ← tier 1: org-policy repo
├── m-cli/         ┐
├── m-stdlib/      │
├── m-standard/    │ tier 2: functional repos
├── m-test-engine/ │ (where features actually live)
├── m-tools/       │
├── tree-sitter-m/ │
├── …              ┘
└── CLAUDE.md                   ← workspace tripwire
```

- **Tier 1 — `.github/`**: org-policy repo. Holds CONTRIBUTING,
  AI-discoverability framework, docs-discoverability spec, layout
  conventions, schemas. **Read-mostly** during feature work in other
  repos.
- **Tier 2 — functional repos**: where features ship. May depend on
  each other at runtime (`m-cli` consumes `m-stdlib`,
  `m-test-engine`, `tree-sitter-m`, …).
- **Tier 3 — `~/m-dev-tools/` itself**: a convenience folder. **Not a
  repo.** Never run a Claude session here.

## What is actually shared at the filesystem level

The repos are independent, but a few things sit at the workspace level
and *are* shared by any session running anywhere in the tree:

| Path | Shared state | Risk |
|---|---|---|
| `~/m-dev-tools/.pytest_cache/` | pytest cache when rootdir resolves to workspace | parallel test runs in sibling repos stomp each other |
| `~/m-dev-tools/.claude/scheduled_tasks.lock` | scheduler lock | by design — a lock is meant to serialize |
| `~/claude/memory/` | single memory dir for any session whose project hash maps to `m-dev-tools/` | concurrent writes to `MEMORY.md` index |
| Same branch name across repos (e.g. `docs-discoverability-phase0`) | nothing physically — but coordinated work | one session may edit multiple repos to "advance the branch" |

The first one is fixable in code (pin `cache_dir` per repo). The
others are addressed by the procedural rules below.

## The root cause: scope confusion

A Claude session launched in `~/m-dev-tools/` (the workspace, not a
sub-repo) has *no scope*. When the user asks it to "implement X in
m-cli that uses the new STDJSON API," the agent cheerfully:

1. Edits files in `m-stdlib/` (adds the new API)
2. Edits files in `m-cli/` (consumes it)
3. Runs `git add -A && git commit` from whatever cwd it ended on

`git status` only sees the cwd's repo. The edits in the *other* repo
become orphans. A **parallel** session running in that other repo —
working on something completely different — runs its own `git add` and
unintentionally bundles the orphans into its commit. The user
discovers the mix-up at PR review time, often days later.

This is the dominant failure mode. Eliminate it and the "git problems"
mostly disappear.

## Working agreement

### Rule 1 — One session ↔ one repo ↔ one branch

Every Claude session launches with `cwd` set to a specific sub-repo:

```bash
cd ~/m-dev-tools/m-cli && claude
```

Never launch from `~/m-dev-tools/`. The workspace-root `CLAUDE.md` is
a tripwire that tells future-you (and future agents) this.

### Rule 2 — Worktrees for parallel branches in the same repo

If you need two agents working on the same repo on different branches,
use a git worktree, not a second clone:

```bash
cd ~/m-dev-tools/m-cli
git worktree add ../m-cli-wt-featX featX
cd ../m-cli-wt-featX && claude
```

Worktrees share the underlying `.git` object store but have fully
isolated working trees and index files. No `index.lock` contention.

### Rule 3 — Cross-repo features go sequentially, leaves first

When an `m-cli` feature needs a new `m-stdlib` primitive:

1. **Session A in `m-stdlib/`** — TDD the primitive, commit, push,
   (tag if release-bound).
2. **Session B in `m-cli/`** — bump the m-stdlib reference (path
   dep / version / git ref), implement consuming logic, commit, push.

Two repos, two sessions, two commits. No single session is permitted
to edit both trees, even when the changes feel "one feature."

### Rule 4 — Path-deps for fast iteration, but commit scope is still single-repo

For fast feedback during cross-repo work, link locally via uv:

```toml
# m-cli/pyproject.toml
[tool.uv.sources]
m-stdlib = { path = "../m-stdlib", editable = true }
```

You get instant test feedback when editing `m-stdlib`, but the
*commits* in `m-stdlib` still happen in a session whose cwd is
`m-stdlib/`. The path link is a runtime convenience, not a license to
bundle edits.

The M-language equivalent: routine path resolution already handles
local cross-repo lookup; no special setup needed.

### Rule 5 — `.github/` is read-only during feature work

Org policy lives in `.github/`. During feature work in `m-cli`:

- **Read** `.github/CONTRIBUTING.md`,
  `.github/docs/docs-discoverability/`,
  `.github/docs/ai-discoverability/` as reference material.
- If a discoverability check fails, the fix usually belongs in the
  consumer repo (add the missing metadata, doc, manifest entry).
- If the *standard itself* is wrong, open a separate session in
  `.github/`, change the standard there, PR it separately. Never
  bundle "I updated org policy AND used the new policy in m-cli"
  into one commit.

### Rule 6 — Coordinated cross-repo branches use a tracking doc

When multiple repos legitimately need the same branch name to advance
a cross-cutting initiative (e.g. `docs-discoverability-phase0` lives
in `m-standard`, `m-stdlib`, `m-tools`, `tree-sitter-m` today),
coordinate via a **single tracking document** in `.github/` — not by
one session editing all the repos at once.

- One driver doc says "phase 0 needs X in m-stdlib, Y in m-cli, Z in
  tree-sitter-m."
- One session per repo executes its slice.
- Land in dependency order: leaves first, consumers last.

## Cheap guardrails (already implemented)

### Workspace-root tripwire

`~/m-dev-tools/CLAUDE.md` declares the directory is **not a repo** and
forbids launching sessions there. Future agents read it on first turn.

### Per-repo pytest `cache_dir` pin

Every Python repo in the org pins
`cache_dir = ".pytest_cache"` inside its `[tool.pytest.ini_options]`
block. Stops pytest from walking up to `~/m-dev-tools/` and creating
a shared cache that parallel runs in sibling repos would corrupt.

Repos pinned today: `m-cli`, `m-cli-extras`, `m-dev-tools-mcp`,
`m-standard`. Add the same line to any new Python repo in the org.

### `make scope-check` (m-cli template)

`m-cli/Makefile` ships a `scope-check` target that walks every sibling
repo and reports any with uncommitted edits. Run it before committing
or pushing when you've been doing cross-repo work:

```bash
make scope-check
```

It does **not** fail on pending sibling edits (those may be legitimate
work in another session) — it just surfaces them so you can confirm
ownership before committing.

The target is a template. Copy it into other repos' Makefiles if you
find yourself reaching for it there. Eventually it should graduate to
a shared `~/scripts/bin/scope-check` script invoked from each repo's
Makefile.

## Diagnostic recipes

### "Why is sibling-repo X dirty?"

```bash
cd ~/m-dev-tools/<X>
git status                       # what changed
git log -1 --stat                # what's already committed
ls -la .git/index.lock 2>/dev/null  # stale lock from a crashed session?
```

If `.git/index.lock` exists but no process holds it (`fuser .git/index.lock`),
delete it — a previous session crashed mid-commit. Otherwise leave it
alone, another session may be mid-commit right now.

### "Two sessions clobbered each other's commits in the same repo"

You launched two sessions with the same cwd. Use worktrees instead
(rule 2). To recover: `git reflog` shows every HEAD movement; the
clobbered commit is still reachable by SHA for an hour or so before
gc.

### "My branch diverged from origin even though I never pulled"

A parallel session in a worktree of the same repo pushed first. Pull,
rebase your local commits onto the new origin tip, push.

### "Tests pass locally but fail in CI after a 'docs-only' commit"

Check `git diff <before> <after> -- ../m-stdlib` (or any sibling
repo). A previous session leaked edits — they shipped in this PR.

## Out of scope

- **Hook-based enforcement.** A pre-commit hook that fails when
  sibling repos are dirty would be too aggressive; sibling work is
  legitimately concurrent. `scope-check` is informational on
  purpose.
- **Workspace-level git tooling** (`mu`, `meta`, `gita`). Not adopted
  today — the procedural rules above are sufficient for a workspace of
  this size. Revisit if the workspace grows past ~25 repos.
- **Per-session memory isolation.** Mentioned in the diagnostic
  session as a concern; addressed indirectly by rule 1 (launching
  sessions from inside specific sub-repos means they resolve to
  distinct project hashes and therefore distinct memory dirs).

## See also

- `~/m-dev-tools/CLAUDE.md` — the workspace tripwire.
- `m-cli/Makefile` — `scope-check` template.
- [`AI-discoverability-architecture.md`](../ai-discoverability/AI-discoverability-architecture.md)
  — how repos expose themselves to AI clients (the *what*; this doc is
  the *how-do-I-actually-work*).
- Each functional repo's `CLAUDE.md` — the per-repo guardrails that
  ride on top of these org-wide practices.
