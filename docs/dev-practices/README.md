# dev-practices — working in the m-dev-tools org

How to *develop* in this org without fighting the tooling. Where the
org-wide standards (AI-discoverability, docs-discoverability,
CONTRIBUTING, layout conventions) tell you **what** the result has to
look like, this section captures **how** to actually get day-to-day
work done across 12+ interconnected sibling repos without git
clashes, leaked edits, or wasted cycles.

These are not policies — those live at the repo root (`CONTRIBUTING.md`,
`profile/`, the schemas). These are *practices* a maintainer or agent
follows when sitting down to do the work.

## Index

- **[`parallel-multi-repo-git-hygiene.md`](parallel-multi-repo-git-hygiene.md)**
  — Why parallel Claude sessions across `m-cli`, `m-stdlib`,
  `m-test-engine`, … cause "git problems," and the workflow that
  eliminates them. Read this first if you run more than one agent
  session at once.

## Audience

Anyone (human or agent) doing implementation work across multiple repos
in the m-dev-tools org. If you're only changing one repo and only ever
have one session open, you can probably skip this section — the
per-repo `CLAUDE.md` and the org `CONTRIBUTING.md` cover the basics.

## Relationship to other doc sections

| Section | What it answers |
|---|---|
| `docs/ai-discoverability/` | Why and how the framework exposes repos to AI clients. |
| `docs/docs-discoverability/` | Why and how human-facing docs are surfaced consistently. |
| `docs/recipes/` | Reproducible step-by-step procedures for specific tasks. |
| `docs/history/` | How the org-wide architecture evolved. |
| **`docs/dev-practices/`** | **How to actually do development work in the org.** |
