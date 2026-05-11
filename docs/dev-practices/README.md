---
created: 2026-05-11
last_modified: 2026-05-11
revisions: 2
doc_type: [REFERENCE, GUIDE]
lifecycle: active
owner: rmrich5
title: "dev-practices — working in the m-dev-tools org"
---

# dev-practices — working in the m-dev-tools org

How to *develop* in this org without fighting the tooling. Where the
org-wide standards (AI-discoverability, docs-discoverability,
CONTRIBUTING, layout conventions) tell you **what** the result has to
look like, this section captures **how** to actually get day-to-day
work done across 12+ interconnected sibling repos.

If you remember nothing else, remember the first rule. It catches the
great majority of failure modes that exist; the rest exist for the
residue.

---

## The five rules

### Rule 1 — One session ↔ one repo

**Don't run two Claude sessions on the same repo at the same time.**

With 12+ repos in the org, parallel work means parallel *repos* — not
parallel *sessions on one repo*. Two sessions on `m-cli` will clobber
each other on `main`, on the working tree, on each other's branch
state. Two sessions on `m-cli` + `m-stdlib` will not collide at all —
separate working trees come for free.

This rule alone catches ~90% of "git problems" people hit working in
this org. Adopt it first; only add the rest if you're already
following this one.

### Rule 2 — Feature branches, not `main`

**Start every session on a feature branch.**

```bash
cd ~/m-dev-tools/m-cli
git switch -c <slug-of-what-this-session-does>
```

If Rule 1 ever slips, at least each session's commits land on its own
branch instead of stacking on `main`. Direct-to-`main` is only safe
when you're certain you're the only actor in this repo today.

### Rule 3 — Cross-repo features go sequentially, leaves first

**Two repos, two sessions, two PRs — in dependency order.**

When `m-cli` needs a new `m-stdlib` primitive:

1. Session A in `m-stdlib/` — TDD the primitive, commit, push, tag
   if release-bound.
2. Session B in `m-cli/` — bump the m-stdlib reference, implement the
   consumer, commit, push.

Never let one session edit both repos, even when the changes feel
"one feature".

### Rule 4 — `.github/` is read-only during feature work

**Don't edit `.github/` from a session whose purpose is implementing
in `m-cli` / `m-stdlib` / etc.**

`.github/` holds org policy: CONTRIBUTING, schemas, the
AI-discoverability framework, the docs-discoverability spec, layout
conventions. Implementation work in functional repos consumes those —
it shouldn't be modifying them. Change `.github/` in a session whose
explicit purpose is `.github/` work, where you can also bump
`profile/repo.meta.json` and regenerate the catalog intentionally.

### Rule 5 — Glance at `git status` before saying "commit"

**Three seconds. If you see files you don't recognize, stop.**

The agent already runs `git status` before staging. Read what it shows
you. Unfamiliar files (especially from another repo, or on a branch
you didn't expect to be on) are the warning sign — investigate before
committing. This is the backstop for the residual cases where the
rules above slipped.

---

## Going deeper

The rules above are the practice. The strategic doc carries the
analysis behind them — three-tier model, what's shared at the
filesystem level (workspace pytest cache, scheduler lock, memory dir),
guardrails (workspace-root tripwire, `make scope-check`), diagnostic
recipes for specific failure modes ("Why is sibling-repo X dirty?",
"Two sessions clobbered each other's commits in the same repo", etc.),
and escape hatches like `git worktree` for the rare case you truly
need concurrent sessions on the same repo.

- **[`parallel-multi-repo-git-hygiene.md`](parallel-multi-repo-git-hygiene.md)**
  — full rules with rationale, three-tier model, filesystem
  shared-state inventory, guardrails, diagnostic recipes.

---

## Adding a practice

A new doc lives in this folder when:

1. It's a *workflow* concern (how to work), not a content concern
   (what the work should produce).
2. It applies across more than one repo in the org.
3. It's stable enough to document — not a one-off experiment.

New docs follow the
[docs-discoverability spec](../docs-discoverability/docs-discoverability-spec.md)
filename and frontmatter conventions.

---

## Audience and relationship to other doc sections

If you only ever change one repo at a time and run one session, this
section is reassurance reading — your default workflow already
respects the rules. If you regularly run more than one session, read
at least the five rules above.

| Section | What it answers |
|---|---|
| `docs/ai-discoverability/` | Why and how the framework exposes repos to AI clients. |
| `docs/docs-discoverability/` | Why and how human-facing docs are surfaced consistently. |
| `docs/recipes/` | Reproducible step-by-step procedures for specific tasks. |
| `docs/history/` | How the org-wide architecture evolved. |
| **`docs/dev-practices/`** | **How to actually do development work in the org.** |
