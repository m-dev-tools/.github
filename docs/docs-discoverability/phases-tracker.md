---
created: 2026-05-11
last_modified: 2026-05-11
revisions: 2
doc_type: [STATUS]
lifecycle: active
owner: rmrich5
title: "Docs Discoverability — Phases Tracker"
---

# Docs Discoverability — Phases Tracker

> Live progress tracker for the org-wide documentation standard
> accepted on 2026-05-11. The standard itself is in
> [`README.md`](README.md). This document tracks execution; the
> README is the contract.

**Status values** — `done` · `in-progress` · `not-started` · `blocked` · `deferred`

**Update protocol** — this tracker is updated *in the same commit* as
any change that moves a row's status. Cadence is event-driven, not
scheduled. Closed items stay in the table marked `done`; history is
one of the legal values.

---

## 1. Phase summary

| Phase | Theme | Target | Status | Reference |
|---|---|---|---|---|
| 0 | Vocabulary, frontmatter, indexes, acceptance | 2026-05-11 | done | [§10 P0](README.md#phase-0--done-2026-05-11) |
| 1 | Schema + warn-only CI | 2026-Q2 weeks 1–4 | not-started | [§10 P1](README.md#phase-1--schema--warn-only-ci-target-2026-q2-weeks-14) |
| 2 | Block on new docs; first remediations | 2026-Q2 weeks 5–8 | not-started | [§10 P2](README.md#phase-2--block-on-new-docs-target-2026-q2-weeks-58) |
| 3 | Block everywhere; org catalog | 2026-Q3 | not-started | [§10 P3](README.md#phase-3--block-everywhere-org-catalog-target-2026-q3) |
| 4 | Cross-repo + freshness | 2026-Q4 | not-started | [§10 P4](README.md#phase-4--cross-repo-and-freshness-target-2026-q4) |

A phase flips to `in-progress` when any of its rows below leave
`not-started`, and to `done` when every row reaches `done`.

---

## 2. Phase 0 — DONE (2026-05-11)

| ID | Item | Status | Date | Notes |
|---|---|---|---|---|
| P0.1 | Vocabulary established (23 types + 6 connections) | done | 2026-05-11 | Folded into README §4 |
| P0.2 | `docs/README.md` indexes generated in every repo | done | 2026-05-11 | 7 repos, 108 entries |
| P0.3 | Frontmatter applied to every existing doc | done | 2026-05-11 | 108 files; script is idempotent |
| P0.4 | Standard accepted; 7 open questions resolved | done | 2026-05-11 | README §13 captures the Q&A |
| P0.5 | Phases tracker created (this file) | done | 2026-05-11 | |

---

## 3. Phase 1 — Schema + warn-only CI

Target: **2026-Q2 weeks 1–4**. Owner default: rmrich5 unless reassigned.

| ID | Item | Status | Target | Blocked-by | Notes |
|---|---|---|---|---|---|
| P1.1 | Land `profile/docs.schema.json` | not-started | Q2 wk 1 | — | Sibling of repo.meta.schema.json |
| P1.2 | Extend `profile/repo.meta.schema.json` with `docs.generated_paths` array | not-started | Q2 wk 1 | — | Enables §5.1 exclusion rule |
| P1.3 | Land `profile/build/validate-docs.py` + tests | not-started | Q2 wk 2 | P1.1, P1.2 | Copy pattern from validate-catalog.py |
| P1.4 | Add `make check-docs` target to each of the 7 repos | not-started | Q2 wk 2 | P1.3 | One PR per repo |
| P1.5 | Wire CI step into per-repo workflows (warn-only) | not-started | Q2 wk 3 | P1.4 | Don't block PRs yet |
| P1.6 | Backfill `lifecycle: active` across all 108 docs | not-started | Q2 wk 3 | P1.1 | Default value; one-time pass |
| P1.7 | Backfill `owner:` across all 108 docs | not-started | Q2 wk 3 | P1.1 | From `git shortlog -sn` per repo |
| P1.8 | Add `generated: true` to m-stdlib `docs/modules/std*.md` | not-started | Q2 wk 4 | P1.2 | Done by `make manifest` regeneration |
| P1.9 | Declare m-stdlib's `docs/modules/` in `docs.generated_paths` | not-started | Q2 wk 4 | P1.2 | One-line edit to repo.meta.json |
| P1.10 | Run weekly cron once with warn-only CI; review noise | not-started | end of Q2 wk 4 | P1.5 | Decision gate before Phase 2 |

---

## 4. CI checks — implementation status

The 18 checks defined in [README §9](README.md#9-ci-enforcement).
Each check lands in the indicated phase.

| # | Check | Phase | Status | Implementation note |
|---|---|---|---|---|
| 0 | Generated-doc gate (skip if `generated: true`) | 1 | not-started | Hard short-circuit; first check evaluated |
| 1 | Frontmatter present | 1 | not-started | YAML block at top |
| 2 | Required keys present | 1 | not-started | created, last_modified, revisions, doc_type, lifecycle |
| 3 | `doc_type` values valid | 1 | not-started | From the 23-vocab in docs.schema.json |
| 4 | `lifecycle` value valid | 1 | not-started | One of 5 states |
| 5 | created/last_modified/revisions match git | 1 | not-started | Auto-fixable; tooling regenerates |
| 6 | `docs/README.md` exists | 1 | not-started | Per-repo gate |
| 7 | No orphans (every `.md` in index) | 1 | not-started | Bidirectional check |
| 8 | No dangling refs in `README.md` | 1 | not-started | Local link resolution |
| 9 | Filename matches doc_type | 2 | not-started | Per README §7 table |
| 10 | Filename content-derived (no `and`, kebab-case) | 2 | not-started | |
| 11 | Required H2 sections per doc_type | 2 | not-started | Per README §8 table |
| 12 | markdownlint clean | 2 | not-started | Standard ruleset, repo-overridable |
| 13 | Cross-repo links valid (extend `check-links.py`) | 3 | not-started | Reuses existing weekly cron |
| 14 | Freshness gate (`review_after` honored) | 3 | not-started | Extends `check-freshness.py` |
| 15 | Supersession bidirectional (A.superseded_by ↔ B.replaces) | 3 | not-started | Catalog-time check |
| 16 | Combination warnings in catalog | 3 | not-started | Refactor-candidate surface |
| 17 | `build-doc-catalog.py` + `profile/docs.json` | 4 | not-started | Sibling of build-catalog.py |
| 18 | `docs.schema.json` pinned for catalog output | 4 | not-started | Contract for downstream agents |

---

## 5. Legacy remediation backlog (Phase 2)

Per [Q7 decision](README.md#q7--migration-of-m-clidocsplans): one PR for
movement-only changes, then per-doc PRs for substantive splits.

### 5.1 Renames (filename ↔ doc_type mismatch)

| ID | Repo | From | To | Reason | Status |
|---|---|---|---|---|---|
| R1 | m-cli | `docs/plans/linter-profiles-guide.md` | `docs/plans/linter-profiles-proposal.md` | `[DESIGN, PROPOSAL]` mislabeled "guide" | not-started |
| R2 | m-cli | `docs/evolution.md` | `docs/history/m-cli-history.md` | Generic name; also moves into `history/` per §6 | not-started |
| R3 | m-cli | `docs/plans/m-cli-history-and-evolution.md` | `docs/history/m-cli-evolution.md` | Has `and`; doc_type is `[HISTORY, EXPLAINER]`; also moves | not-started |
| R4 | m-tools | `docs/m-tool-gap-analysis.md` | `docs/m-tool-gaps.md` | Align with `*-gaps.md` convention | not-started |
| R5 | m-tools | `docs/ydb-dev-tools-gap-analysis.md` | `docs/ydb-dev-tools-gaps.md` | Same; file is also a redirect stub | not-started |
| R6 | m-tools | `docs/gap-analysis-and-remediation-strategy.md` | (split — see S4 below) | Has `and`; superseded by split | not-started |

### 5.2 Moves (subdir ↔ doc_type mismatch — m-cli `docs/plans/`)

Single PR per [§10 Phase 2](README.md#phase-2--block-on-new-docs-target-2026-q2-weeks-58)
movement-only convention.

| ID | File (currently in `m-cli/docs/plans/`) | Move to | doc_type | Status |
|---|---|---|---|---|
| M1 | `language-cli-survey.md` | `docs/research/` | `[SURVEY, GAP-ANALYSIS]` | not-started |
| M2 | `m-corpus-catalog.md` | `docs/reference/` | `[REFERENCE, RESEARCH]` | not-started |
| M3 | `m-linter-status-2026-04-30.md` | `docs/status/` | `[STATUS, POSTMORTEM]` | not-started |
| M4 | `m-linting-survey.md` | `docs/research/` | `[SURVEY, GAP-ANALYSIS]` | not-started |
| M5 | `iris-ydb-portability.md` | (stays in `plans/`) | `[PLAN, RESEARCH]` | n/a |
| M6 | `m-env-implementation-plan.md` | (stays in `plans/`) | `[PLAN]` | n/a |
| M7 | `m-environment-tool.md` | (stays in `plans/`) | `[PROPOSAL, DESIGN]` | n/a |

### 5.3 Splits (combination doc_types — per-doc PRs)

Per [README §4 refactor heuristics](README.md#combinations-and-split-candidates).

| ID | File | Combination | Split target | Status |
|---|---|---|---|---|
| S1 | m-cli `docs/plans/m-linting-implementation-plan.md` | `[PLAN, BUILD-LOG]` | frozen plan + live build-log | not-started |
| S2 | tree-sitter-m `docs/build-log.md` | `[BUILD-LOG, HISTORY]` | live build-log + `docs/history/tree-sitter-m-history.md` | not-started |
| S3 | tree-sitter-m `docs/vista-parse-error-categories.md` | `[GAP-ANALYSIS, PLAN]` | gaps doc + remediation plan | not-started |
| S4 | m-tools `docs/gap-analysis-and-remediation-strategy.md` | `[GAP-ANALYSIS, PLAN]` | `docs/m-tools-gaps.md` + `docs/m-tools-remediation-plan.md` | not-started |
| S5 | m-tools `docs/implementation.md` | `[REFERENCE, STATUS]` | timeless reference + dated status | not-started |
| S6 | m-cli `docs/evolution.md` | `[HISTORY, BUILD-LOG]` | history (R2) + per-release build-logs | not-started |

### 5.4 Reviews (combinations flagged "usually fine; confirm before splitting")

| ID | File | Combination | Action | Status |
|---|---|---|---|---|
| V1 | m-cli `docs/guide.md` | `[GUIDE, REFERENCE]` | confirm primary; link the secondary | not-started |
| V2 | m-standard `docs/m-standards-guide.md` | `[GUIDE, REFERENCE]` | same | not-started |
| V3 | m-standard `docs/m-libraries-remediation.md` | `[PLAN, ROADMAP]` | demote one to a section of the other | not-started |
| V4 | m-cli `docs/plans/language-cli-survey.md` | `[SURVEY, GAP-ANALYSIS]` | typical pair; confirm whether two docs are clearer | not-started |
| V5 | m-cli `docs/plans/m-linting-survey.md` | `[SURVEY, GAP-ANALYSIS]` | same | not-started |
| V6 | m-stdlib `docs/testing/modern-m-corpus-test-results.md` | `[RESEARCH, GAP-ANALYSIS]` | same | not-started |
| V7 | m-tools `docs/m-tool-gap-analysis.md` | `[GAP-ANALYSIS, SURVEY]` | same | not-started |

---

## 6. Phase 2–4 (placeholder)

Detailed rows are added when the prior phase reaches `done`. Phase 2
will inherit the legacy remediation backlog above as concrete rows;
Phase 3 will add the catalog builder and freshness gate rows; Phase 4
will add the cross-repo link extension and the freshness-cron rows.

---

## 7. Open issues encountered during execution

Captured here as a running log so they survive across owner changes.

| Date | Issue | Phase | Resolution |
|---|---|---|---|
| 2026-05-11 | Two PRs were titled `docs: ...` but their squash-merge actually contained docs + parallel Phase 1/Phase 2 work that had been committed onto the feature branch during the same session (m-cli PR #13 had docs + Phase 1b doctor + Phase 2 engine; m-test-engine PR #3 had docs + Phase 1a engine-contract + Phase 2-prep bind-mount). Root cause: feature branches were created at local `main`'s tip, but `main` had received parallel commits while the session was in flight, so the new branch inherited them. The dirty working tree blocked the planned post-creation reset to the docs-only commit. | 0 | m-cli: PR #13 closed; engine + Phase 1b preserved on `engine-phase2`; clean docs-only PR #14 opened and merged; `engine-phase2` later rebased onto post-merge `main` with the dedup working as designed. m-test-engine: PR #3 had already merged before discovery; tree-SHA verification confirmed `origin/main` is byte-identical to the redundant preservation branches, which were then deleted. **Lesson for future passes**: before pushing a feature branch, run `git log <branch> ^origin/main --oneline` and confirm the listed commits match the scope implied by the branch name and the PR title. Catch the mismatch *before* the PR is opened, not after merge. |
