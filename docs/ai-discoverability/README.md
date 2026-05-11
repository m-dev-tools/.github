# AI-discoverability — framework reference set

Every document that explains **why** and **how** the AI-discoverability
framework exists. Curated together so a future maintainer (human or
agent) can replay the design decisions before changing anything.

The framework itself lives at the repo root (`profile/tools.json`,
`profile/task_index.json`, the schemas, the build scripts). This
directory holds the prose that justifies it.

## Master doc — read this first

**[`AI-discoverability-architecture.md`](AI-discoverability-architecture.md)** —
the foundational architecture document. First principles → design →
implementation, with the three-layer diagram and the component flow.
Reading this end-to-end gives an agent (or a human) everything needed
to extend the framework: adding a new repo, a new MCP tool, a new
manifest kind. Every other doc here is a deeper drill-down into one
slice of the same architecture.

## Companion design docs

- **[`AI-discoverability-guide.md`](AI-discoverability-guide.md)** —
  user-facing introduction. Pre-dates the master doc; useful as a
  lighter-weight explainer for newcomers.
- **[`AI-discoverability-plan.md`](AI-discoverability-plan.md)** —
  the de-novo design plan. Spells out the three layers, success
  criteria, and the architectural inversion vs. the prior
  hand-maintained `tools.json` approach. The architecture doc cites
  this as the canonical reference for design rationale.

## Phase plans + exit evidence

All under [`phases/`](phases/). One plan + one evidence file per phase,
both committed at landing time.

| Phase | Plan | Exit evidence | State |
|---|---|---|---|
| 0 — Repo-local manifests + CI drift gates | [`phases/phase0-plan.md`](phases/phase0-plan.md) | [`phases/phase0-status.md`](phases/phase0-status.md) | Closed 2026-05-10 |
| 1 — Org routing layer (`tools.json` as build output) | [`phases/phase1-plan.md`](phases/phase1-plan.md) | [`phases/phase1-evidence.md`](phases/phase1-evidence.md) | Closed 2026-05-10 |
| 2 — Tier-2 + tier-3 onboarding | (folded into Phase 1) | — | Closed 2026-05-10 |
| 3 — Recipes + discovery handshake | [`phases/phase3-plan.md`](phases/phase3-plan.md) | [`phases/phase3-evidence.md`](phases/phase3-evidence.md) | Closed 2026-05-11 |
| 4 — MCP server (`m-dev-tools-mcp`) | [`phases/phase4-plan.md`](phases/phase4-plan.md) | [`phases/phase4-evidence.md`](phases/phase4-evidence.md) | Closed 2026-05-11 |
| 5 — Continuous enforcement hardening | [`phases/phase5-plan.md`](phases/phase5-plan.md) | [`phases/phase5-evidence.md`](phases/phase5-evidence.md) | Closed 2026-05-11 |

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
