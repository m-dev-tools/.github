# AI-discoverability — framework reference set

Every document that explains **why** and **how** the AI-discoverability
framework exists. Curated together so a future maintainer (human or
agent) can replay the design decisions before changing anything.

The framework itself lives at the repo root (`profile/tools.json`,
`profile/task_index.json`, the schemas, the build scripts). This
directory holds the prose that justifies it.

## Read this first

If you're new to the framework:

1. **[`AI-discoverability-guide.md`](AI-discoverability-guide.md)** —
   the user-facing intro. Explains what an "AI-discoverable" repo
   looks like and what it costs an agent to consume.
2. **[`AI-discoverability-plan.md`](AI-discoverability-plan.md)** —
   the de-novo design plan. Three layers (repo-local facts → org
   routing → agent operability), success criteria, the architectural
   inversion vs. the prior hand-maintained `tools.json` approach.
3. **[`current-state-inventory-priority.md`](current-state-inventory-priority.md)** —
   the as-of-Phase-1 snapshot that re-ranked outstanding work by
   downstream-dependent priority. Historical, but useful context for
   why the phase order is what it is.

## Phase plans + exit evidence

Five phases, two docs each — the plan and the evidence file that
captures clean-run output for the phase's exit gate.

| Phase | Plan | Exit evidence | State |
|---|---|---|---|
| 0 — Repo-local manifests + CI drift gates | [`phase0-plan.md`](phase0-plan.md) | [`phase0-status.md`](phase0-status.md) | Closed 2026-05-10 |
| 1 — Org routing layer (`tools.json` as build output) | [`phase1-plan.md`](phase1-plan.md) | [`phase1-evidence.md`](phase1-evidence.md) | Closed 2026-05-10 |
| 2 — Tier-2 + tier-3 onboarding | (folded into Phase 1) | — | Closed 2026-05-10 |
| 3 — Recipes + discovery handshake | [`phase3-plan.md`](phase3-plan.md) | [`phase3-evidence.md`](phase3-evidence.md) | Closed 2026-05-11 |
| 4 — MCP server (`m-dev-tools-mcp`) | [`phase4-plan.md`](phase4-plan.md) | [`phase4-evidence.md`](phase4-evidence.md) | Closed 2026-05-11 |

Phase 0 used a different naming convention (`-status.md` instead of
`-evidence.md`). The convention stabilized starting Phase 1 — both
later phases write a single `phase<N>-evidence.md` file that cites
each done-criterion green.

## What this directory is NOT

- The framework itself. That's `profile/tools.json`,
  `profile/task_index.json`, `profile/*.schema.json`, and
  `profile/build/`.
- Recipes. Those are mechanically-runnable Markdown files under
  [`../recipes/`](../recipes/), gated by `make recipes-check`.
- Org history / archived projects. That's [`../history/`](../history/) —
  e.g. the m-tools archive.
