---
created: 2026-05-11
last_modified: 2026-05-11
revisions: 0
doc_type: [GUIDE]
lifecycle: active
owner: rmrich5
title: "Multi-session git worktrees — m-dev-tools"
related: [parallel-multi-repo-git-hygiene.md]
---

# Multi-session git worktrees — m-dev-tools

> The day-to-day mechanics of git worktrees as used in this org.
> [`parallel-multi-repo-git-hygiene.md`](parallel-multi-repo-git-hygiene.md)
> §Rule 2 names the rule ("worktrees for parallel branches in the same
> repo"); this guide is the operational manual.

## Audience and prerequisites

You should read this when:

- You routinely run more than one Claude Code session, and
- At least two of those sessions touch the **same repo** at the same
  time on **different branches**.

If every concurrent session is in a different repo, you don't need
worktrees — separate working trees come for free. See
[`parallel-multi-repo-git-hygiene.md`](parallel-multi-repo-git-hygiene.md)
§Rule 1 for the simpler single-repo-per-session rule.

## Layout convention

Worktrees live as **siblings of the main checkout** under
`~/m-dev-tools/`, named `<repo>-<branch-slug>`:

```
~/m-dev-tools/
├── m-cli/                       ← main checkout, always on `main`
├── m-cli-engine-phase2/         ← worktree on `engine-phase2`
├── m-cli-docs-frontmatter/      ← worktree on `docs-frontmatter`
├── m-stdlib/                    ← main checkout, on `main`
├── m-stdlib-stdfoo-h2/          ← worktree on `stdfoo-h2`
├── m-test-engine/
├── .github/
└── CLAUDE.md                    ← workspace tripwire (NOT a repo)
```

Rules:

1. **Main checkout always tracks `main`** — read-mostly, used for
   `git pull`, cross-repo grepping, and as the source of new worktrees.
2. **Each feature branch gets its own sibling worktree** for the
   duration of that work.
3. **Branch slug = directory suffix.** If the branch is
   `feat/track-c2`, the worktree is `m-cli-feat-track-c2/` (replace
   `/` with `-` in the directory name).

## Setup

### One worktree on an existing local branch

```bash
cd ~/m-dev-tools/m-cli
git worktree add ../m-cli-engine-phase2 engine-phase2
```

### One worktree on a new branch (create + check out in one step)

```bash
cd ~/m-dev-tools/m-cli
git worktree add ../m-cli-stdlib-bump -b chore/stdlib-bump
```

### One worktree on a remote-only branch

```bash
cd ~/m-dev-tools/m-cli
git fetch origin
git worktree add ../m-cli-someones-pr origin/someones-pr
```

This sets up a tracking branch automatically.

## What you get

After `git worktree add`, the new directory is a **fully-functional
checkout** of the repo. It shares the underlying `.git` object store
with the main checkout (so it's cheap on disk — only the working tree
is duplicated), but the index, `HEAD`, working tree, and branch
checkout are independent.

Two concrete consequences:

- **No `index.lock` contention** between sessions. Each worktree has
  its own `.git/worktrees/<name>/index`.
- **The same branch cannot be in two worktrees at once.** If you try,
  git refuses with a helpful error pointing at the existing
  checkout. This is a *feature*, not a limitation — it's the
  mechanism that prevents the cross-session collision.

## Daily usage

### Each Claude session points to one worktree

In each session, start with:

```bash
cd ~/m-dev-tools/m-cli-engine-phase2
```

…and stay there. Tell the agent at the top of the session:

> *"You're working in `~/m-dev-tools/m-cli-engine-phase2` on branch
> `engine-phase2`. Don't touch other worktrees or the main checkout."*

The agent will respect that. Without the directive, an agent reading
`git status` from the main checkout might think it needs to clean
something up that belongs to a different session.

### Status across all your worktrees

```bash
git -C ~/m-dev-tools/m-cli worktree list
```

Lists every worktree of `m-cli`, the SHA each is parked on, and the
branch name. Same info from any worktree path — they all share the
underlying `.git`.

### Updating `main` in the main checkout, then refreshing worktrees

```bash
# In the main checkout — pull updated main
cd ~/m-dev-tools/m-cli
git pull --ff-only origin main

# In each worktree — pick up new origin refs (does NOT change your branch)
cd ~/m-dev-tools/m-cli-engine-phase2
git fetch origin
```

If you want to rebase the worktree's branch onto the new `main`, do
it explicitly inside the worktree:

```bash
cd ~/m-dev-tools/m-cli-engine-phase2
git rebase origin/main
```

## Cleanup

When a branch is merged or abandoned:

```bash
# From the main checkout (or any sibling worktree)
git -C ~/m-dev-tools/m-cli worktree remove ../m-cli-engine-phase2
git -C ~/m-dev-tools/m-cli branch -d engine-phase2   # optional
```

`worktree remove` will refuse if the worktree has uncommitted changes.
Decide:

- **Want to keep them**: commit / stash / push, then retry.
- **Sure you don't**: `git worktree remove --force …` (destructive on
  the worktree's uncommitted state only; cannot affect committed
  history).

### Pruning stale worktree pointers

If you ever bypass `git worktree remove` (e.g., `rm -rf` the
directory directly), the `.git/worktrees/<name>` pointer dangles.
Clean up with:

```bash
git -C ~/m-dev-tools/m-cli worktree prune
```

## Gotchas

### 1. The same branch can only live in one worktree

Trying to check out a branch that's already checked out elsewhere
fails:

```
fatal: 'engine-phase2' is already checked out at
'/home/rafael/m-dev-tools/m-cli-engine-phase2'
```

This is the mechanism that prevents two sessions from independently
mutating the same branch. If you see this error, switch into the
existing worktree instead of fighting it.

### 2. `.venv/` and `node_modules/` don't follow the worktree

These are generated artifacts, in `.gitignore`. A new worktree starts
without them. Run the repo's standard install command
(`make install`, `uv sync`, `npm install`, …) inside the worktree
once after creating it.

### 3. direnv works per-worktree

`.envrc` is a committed file, so it lands in each worktree. The first
time you `cd` into a worktree, run `direnv allow` once. After that,
direnv loads the same env as the main checkout.

### 4. pytest cache pinning

If the repo's `pyproject.toml` pins `cache_dir = ".pytest_cache"`
(per the org guardrail in
[`parallel-multi-repo-git-hygiene.md`](parallel-multi-repo-git-hygiene.md)
§"Per-repo pytest `cache_dir` pin"), the worktree gets its own
pytest cache automatically. If it doesn't, parallel test runs can
clash on `~/m-dev-tools/.pytest_cache/`. Fix at the repo level, not
the worktree level.

### 5. CI doesn't care about worktrees

Worktrees are a local convenience. CI clones the remote and works
from there. Anything that's committed pushes the same way regardless
of which worktree it came from.

### 6. Don't run a Claude session in the main checkout

The main checkout's role is `main`-tracking only. Sessions live in
sibling worktrees, never in the original directory. This is a
convention, but it prevents the failure mode where one session
switches branches in the main checkout and another session, also in
the main checkout, finds files it doesn't recognize.

## When NOT to use worktrees

- **Single-session work in a repo.** Use `git switch -c <branch>` in
  the main checkout. No worktree overhead needed.
- **Read-only inspection of another branch.** `git show
  <branch>:path/to/file` is cheaper than a whole worktree.
- **Throwaway one-off branches.** `switch -c` in the main checkout,
  do the work, `switch main`, delete the branch.

Worktrees pay off when work on a branch outlives a single session
**and** another session needs parallel access to the same repo.

## Bootstrapping the org for worktree workflow

If you're adopting this convention for the first time and want to
prepare the workspace:

```bash
# In each repo where you might have parallel sessions:
for repo in m-cli m-stdlib m-test-engine; do
  cd ~/m-dev-tools/$repo
  # Confirm the main checkout is on main (move there if not)
  git switch main 2>/dev/null
  # Create worktrees for any currently-active feature branches:
  for branch in $(git branch --format='%(refname:short)' | grep -v '^main$'); do
    slug=$(echo "$branch" | tr '/' '-')
    git worktree add "../${repo}-${slug}" "$branch" 2>/dev/null || true
  done
done

# Verify
for repo in m-cli m-stdlib m-test-engine; do
  echo "=== $repo ==="
  git -C ~/m-dev-tools/$repo worktree list
done
```

After this, each feature branch has its own working tree, the main
checkouts are clean on `main`, and any new session can be pointed at
the correct sibling directory at startup.

## Reference

- Git docs: <https://git-scm.com/docs/git-worktree>
- The org-level rule this implements:
  [`parallel-multi-repo-git-hygiene.md`](parallel-multi-repo-git-hygiene.md)
  §Rule 2.
- The session that surfaced the need:
  [`docs/docs-discoverability/phases-tracker.md`](../docs-discoverability/phases-tracker.md)
  §7, 2026-05-11 entry.
