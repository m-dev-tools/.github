---
created: 2026-05-11
last_modified: 2026-05-11
revisions: 0
doc_type: [PROPOSAL, DESIGN, PLAN]
lifecycle: active
owner: rmrich5
status: accepted
accepted_on: 2026-05-11
---

# Docs Discoverability — m-dev-tools

> Accepted standard for treating every document in the m-dev-tools org
> as a first-class, CI-enforced artifact. Anchors the next phase of the
> org's docs-as-code stack on top of the existing manifest / catalog /
> link-check infrastructure in `profile/`.

This document records the **accepted** org-wide documentation standard,
the CI checks that enforce it, and a phased remediation plan for the
108 existing docs across the seven tier-1 and tier-2 repos. The seven
open questions raised during the proposal phase were resolved on
2026-05-11 and folded into §4–§9. The full Q&A is preserved in §13 as
the design record. Execution progress is tracked in
[`phases-tracker.md`](phases-tracker.md).

---

## 1. Why this is needed

The org already has strong infrastructure for *machine-readable*
artifacts:

- `profile/repo.meta.schema.json` — per-repo manifest schema.
- `profile/tools.json` + `task_index.json` — catalog consumed by agents.
- `profile/build/validate-catalog.py`, `check-links.py`,
  `check-freshness.py` — CI gates that already run per-PR and weekly.
- Per-repo `make check-docs-prose` — enforces that `docs/` holds only
  prose.

What is *not yet* enforced is anything about the prose inside `docs/`:

| Concern | Today | Gap |
|---|---|---|
| Doc has a stated *type* | Frontmatter exists on m-stdlib modules only | No org-wide schema, no enforcement |
| Doc is discoverable | First-pass `docs/README.md` indexes exist in 7 repos | Hand-curated; can drift silently |
| Filename describes content | Mixed: `evolution.md`, `linter-profiles-guide.md` (actually a proposal), `discoveries.md` | No convention; misleading names persist |
| Doc has an owner | Implicit (CODEOWNERS at repo level only) | No per-doc owner; orphaned docs accumulate |
| Doc has a lifecycle | None | Active plans and superseded plans look identical |
| Doc is fresh | `check-freshness.py` exists for manifests | Not extended to prose |
| Cross-repo refs are valid | `check-links.py` covers catalog URLs | Doesn't yet crawl `docs/` markdown links |
| Plan and execution are distinct files | Often merged (`PLAN, BUILD-LOG` combinations seen in 6 docs) | No norm forcing split |

The org has already done the hard work on machine-readable artifacts;
prose docs are the last unguarded surface. This proposal extends the
existing pipeline rather than starting a parallel one.

---

## 2. Goals & non-goals

### Goals

1. **Every doc declares what it is.** Frontmatter with a typed
   `doc_type` from a fixed vocabulary. Combinations allowed and
   meaningful.
2. **Every doc is reachable from the org catalog.** Org-level builder
   walks each repo's `docs/` and produces a single index keyed by type,
   repo, lifecycle, and recency.
3. **Filenames tell humans what's inside without opening the file.**
   Suffix or numeric-prefix conventions tied to doc_type.
4. **CI rejects drift.** The same per-PR + weekly cron pipeline that
   guards `tools.json` guards `docs/`.
5. **Existing docs are remediated, not abandoned.** Phased rollout with
   a warn-only period so legacy docs can be migrated without a flag day.

### Non-goals

- **Prose style guide.** This proposal pins *structure and metadata*,
  not voice, tone, line length, or heading style. Those belong in a
  separate (later) doc and are partly handled by `markdownlint`.
- **Replacing repo-level READMEs.** Top-level `README.md` remains the
  public face of each repo; this proposal governs `docs/` only.
- **Authoring guidance.** "How to write a good ADR" is out of scope
  here — referenced templates handle that.
- **Generated-doc enforcement.** Anything regenerated from
  `dist/*.json` is already covered by the manifest drift gates.

---

## 3. Principles

1. **Docs-as-code.** Same review, same CI, same blast radius as source.
   No separate "docs platform" with its own auth and storage.
2. **Schema before tooling.** Every check is a thin runner over a
   versioned JSON schema in `profile/`. Schemas are the contract;
   scripts are replaceable.
3. **Single source of truth per topic.** If two docs cover the same
   subject, one is canonical and the other links to it. The catalog
   surfaces duplicates so they get merged or one gets marked
   `superseded`.
4. **Lifecycle is explicit.** A frozen plan from six months ago and an
   active plan from yesterday must look different *in metadata*, not
   only by reading-and-dating.
5. **Naming follows content, not history.** A file named `*-guide.md`
   that is structurally a design proposal is a bug. CI catches it.
6. **The index is generated.** Hand-curated indexes drift the day after
   they're written. `docs/README.md` is rebuilt from frontmatter.
7. **Combinations are first-class refactoring signals.** `[PLAN,
   BUILD-LOG]` is allowed today, but the catalog flags it as a
   split-candidate. Same for `[PLAN, ROADMAP]`, `[SURVEY, PLAN]`.
8. **Warn before block.** Every new gate ships warn-only first; we let
   one weekly cron pass before flipping to blocking.

---

## 4. The vocabulary

Established in a first pass (2026-05-11) and now stamped into every
doc's `doc_type` field. Reproduced here for reference; the canonical
list lives in `profile/docs.schema.json` (proposed below).

**Types** (23) — `HISTORY` · `ARCHITECTURE` · `DESIGN` · `ADR` · `SPEC`
· `REFERENCE` · `GUIDE` · `TUTORIAL` · `ROADMAP` · `PLAN` · `RESEARCH`
· `SURVEY` · `GAP-ANALYSIS` · `STATUS` · `EXPLAINER` · `NOTES` ·
`WORKED-EXAMPLE` · `SETUP` · `INTEGRATION` · `PROPOSAL` · `BUILD-LOG`
· `CHANGELOG` · `POSTMORTEM`.

**Connections** (6, lowercase) — `history` · `function` · `design` ·
`architecture` · `planning` · `implementation`.

Connections are **optional** in frontmatter (Phase 1 decision). The
first-pass labeling already captured connections per-doc in each
repo's `docs/README.md`; they'll be harvested retroactively into
frontmatter when the doc catalog builder lands in Phase 3. Whether
to make them required is revisited then.

The four Diátaxis quadrants map cleanly onto a subset, which is a
useful sanity check that the taxonomy is coherent:

| Diátaxis | Our type |
|---|---|
| Tutorial (learning-oriented) | `TUTORIAL` |
| How-to (task-oriented) | `GUIDE` |
| Reference (information-oriented) | `REFERENCE` |
| Explanation (understanding-oriented) | `EXPLAINER` |

The remaining 19 types cover artifacts Diátaxis doesn't address
explicitly: decisions (`ADR`, `PROPOSAL`), forward-looking work
(`PLAN`, `ROADMAP`), backward-looking artifacts (`HISTORY`,
`BUILD-LOG`, `CHANGELOG`, `POSTMORTEM`), analytical work (`SURVEY`,
`RESEARCH`, `GAP-ANALYSIS`), state snapshots (`STATUS`), and the
inevitable bucket (`NOTES`).

### Combinations and split-candidates

Combinations are allowed but flagged. The first-pass labeling surfaced
these patterns:

| Combination | Count | Refactor heuristic |
|---|---|---|
| `[PLAN, BUILD-LOG]` | 1 | Split into a frozen plan + a live log |
| `[PLAN, ROADMAP]` | 2 | Demote one to a section of the other |
| `[SURVEY, GAP-ANALYSIS]` | 4 | Often correct; survey describes, gap prescribes; consider whether two docs are clearer |
| `[GAP-ANALYSIS, PLAN]` | 2 | Split: gap is descriptive, plan is prescriptive |
| `[HISTORY, BUILD-LOG]` | 2 | Build-log freezes per release; history is the narrative |
| `[REFERENCE, STATUS]` | 1 | Reference is timeless; status is dated. Split |
| `[GUIDE, REFERENCE]` | 2 | Usually fine; pick one as primary, link the other |

These are *targets for future refactor*, not immediate CI failures.

---

## 5. Frontmatter schema

Lands as `profile/docs.schema.json` (new, sibling of the existing
manifest schemas). Versioned via `schema-changelog.md`. Validated by a
new `profile/build/validate-docs.py`.

```yaml
---
# Required
created:        2026-04-15           # ISO date, first git commit
last_modified:  2026-05-09           # ISO date, latest git commit
revisions:      7                    # int, commit count on this file
doc_type:       [ADR, DESIGN]        # one or more from the 23-vocab
lifecycle:      active               # draft | active | frozen | superseded | deprecated

# Strongly encouraged
title:          "ADR-0007: Use STDASSERT as the test protocol"
owner:          rmrich5              # GitHub handle of accountable owner
connections:    [design, architecture]   # 0–3 from the 6-vocab

# Optional, semantic links between docs
replaces:       [adr/0003-...md]     # this doc supersedes those
supersedes:     [adr/0003-...md]     # alias of `replaces`
superseded_by:  adr/0011-...md       # this doc was retired by that
related:        [docs/guides/m-tdd-guide.md]

# Optional, lifecycle
freeze_after:   2026-09-01           # for plans that should be frozen at a date
review_after:   2026-12-01           # surface in the freshness report after this

# Optional, exclusion
generated:      true                 # if true, this doc is machine-generated;
                                     # see §5.1 — docs-QA CI skips it
---
```

Notes:

- `created`, `last_modified`, `revisions` are populated by tooling from
  `git log --follow`, never hand-edited. CI verifies they match.
- `doc_type` is the type vocabulary list. Combinations remain explicit.
- `lifecycle` is the new field this proposal introduces. Default for
  the org-wide backfill: `active`.
- `owner` defaults to the repo's top contributor if unset; the warning
  surfaces in the catalog so it can be reassigned.

### Lifecycle states

| State | Meaning | Visible in catalog | Counts toward freshness gate |
|---|---|---|---|
| `draft` | In progress, not yet authoritative | Yes, flagged | No |
| `active` | Current and authoritative | Yes | Yes (warning at `review_after`) |
| `frozen` | Locked snapshot (e.g., a release plan) | Yes, marked | No |
| `superseded` | Retired in favor of another doc | Yes, with link | No |
| `deprecated` | Kept for archaeology only; do not act on it | Folded into history view | No |

This is the single biggest authoring change: forward-looking work
(`PLAN`, `ROADMAP`, `PROPOSAL`) gets `lifecycle: draft` while being
written, flips to `active` at acceptance, and to `frozen` when locked.
Live build-logs and trackers stay `active` indefinitely; release plans
flip to `frozen` at GA.

### 5.1 Generated documents — excluded from docs QA

**Rule.** Documents that are produced by a generator (e.g., m-stdlib's
`docs/modules/std*.md` written by `make manifest`) are **out of scope
for docs QA/CI**. Their lifecycle is machine-driven: the generator is
the source of truth, and the existing manifest drift gate
(`make check-manifest` in each generating repo) already guards their
integrity.

**How a doc is marked generated.** Frontmatter field
`generated: true`. Set by the generator on every regeneration; never
hand-edited.

**What the docs validator does with `generated: true` docs.**

1. Skips all docs-QA checks listed in §9 (frontmatter validation,
   filename rules, required sections, README index membership,
   markdownlint).
2. Asserts only that:
   - `generated: true` is present
   - The file path is declared in the repo's `repo.meta.json` under a
     new `docs.generated_paths:` field (so a typo or stray marker
     can't accidentally hide a hand-written doc from CI)
   - The file's `last_modified` matches the latest generator run
     (drift gate; identical guarantee to the existing
     `dist/*.json` drift check, applied to generated prose)

**Where the rule lives.** `profile/docs.schema.json` carries the
`generated` field; `profile/repo.meta.schema.json` is extended with
`docs.generated_paths` (a list of path globs) so the exclusion is
declared at repo-manifest time, not silently per-file.

**What today's generated docs look like.** The 32 `m-stdlib/docs/modules/std*.md`
files are the only known generated docs in the org as of 2026-05-11.
Their existing frontmatter already carries `module:`, `tag:`, `phase:`,
`stable:`, `since:`, `synopsis:`, etc. The generator simply adds
`generated: true` on the next `make manifest` run, and the
docs-QA gate stops trying to validate them against the prose schema.

---

## 6. Standard repo layout for `docs/`

Already partly enforced by `make check-docs-prose`. This proposal pins
the subtree convention:

```
<repo>/docs/
├── README.md             # generated index — DO NOT hand-edit
├── adr/                  # ADRs (numbered NNNN-slug.md), self-contained
│   └── README.md         # generated index of ADRs (optional)
├── plans/                # PLAN, PROPOSAL, ROADMAP
├── guides/               # GUIDE, TUTORIAL, EXPLAINER, SETUP, INTEGRATION
│                         # — organised by Diátaxis quadrant (see below)
├── reference/            # REFERENCE (often auto-generated; see §5.1)
├── research/             # RESEARCH, SURVEY, GAP-ANALYSIS
├── history/              # HISTORY, BUILD-LOG, CHANGELOG, POSTMORTEM
└── status/               # STATUS, dated trackers
```

Subdirs are *recommended*, not mandatory — repos with only a handful
of docs (e.g., `tree-sitter-m-vscode`) keep them at top-level. The
CI gate enforces that *if a subdir exists, the docs inside it have a
matching `doc_type`*. A `PLAN` doc may not live in `guides/`; a `GUIDE`
doc may not live in `plans/`.

**`guides/` follows Diátaxis.** Within `guides/`, each doc belongs to
exactly one of the four quadrants defined by the [Diátaxis
framework](https://diataxis.fr):

| Quadrant | Our type | Audience question | Filename pattern |
|---|---|---|---|
| Tutorial (learning) | `TUTORIAL` | "I'm new — teach me." | `*-tutorial.md` |
| How-to (task) | `GUIDE` | "I have a job — help me do it." | `*-guide.md` or `*-how-to.md` |
| Reference (info) | `REFERENCE` | "I need a fact — show me." | content-derived (no suffix required) |
| Explanation | `EXPLAINER` | "I want to understand — explain it." | `*-explainer.md` |

`SETUP` and `INTEGRATION` docs are a subspecies of how-to and live in
`guides/` too (`*-setup.md`, `*-integration.md`). The CI gate enforces
the Diátaxis filename pattern within `guides/`.

This is a major reshuffle for `m-cli/docs/plans/` (which today contains
surveys, status reports, history, and design proposals labeled
`PLAN`). Migration is part of the remediation plan in §10.

---

## 7. Filename conventions

Goal: the filename alone tells a reader what the doc is, without
opening it.

| Doc type | Filename pattern | Examples |
|---|---|---|
| `ADR` | `NNNN-slug.md` (4-digit) | `0007-stdassert-as-test-protocol.md` |
| `PLAN` | `*-plan.md` | `m-stdlib-implementation-plan.md` |
| `ROADMAP` | `*-roadmap.md` | `m-libraries-roadmap.md` |
| `PROPOSAL` | `*-proposal.md` | `m-environment-tool-proposal.md` |
| `SPEC` | `*-spec.md` or `spec.md` | `spec.md`, `m-doc-grammar-spec.md` |
| `GUIDE` | `*-guide.md` or `*-how-to.md` (Diátaxis how-to) | `m-linting-user-guide.md` |
| `TUTORIAL` | `*-tutorial.md` (Diátaxis tutorial) | `accsum-tutorial.md` |
| `SURVEY` | `*-survey.md` | `m-linting-survey.md` |
| `GAP-ANALYSIS` | `*-gaps.md` | `ydb-dev-tools-gaps.md` |
| `STATUS` (snapshot) | `*-status-YYYY-MM-DD.md` (dated) | `m-linter-status-2026-04-30.md` |
| `STATUS` (live tracker) | `*-tracker.md` (no date — continually updated) | `phases-tracker.md`, `module-tracker.md` |
| `POSTMORTEM` | `postmortem-YYYY-MM-DD-slug.md` | `postmortem-2026-04-29-cache-stampede.md` |
| `BUILD-LOG` | `build-log.md` or `*-build-log.md` | `build-log.md` |
| `CHANGELOG` | `changelog.md` (always at repo root or `tracking/`) | |
| `HISTORY` | `*-history.md` or `evolution.md` | `m-cli-history.md` |
| `WORKED-EXAMPLE` | `*-worked-example.md` or `example-*.md` | `worked-example-accsum.md` |
| `SETUP` | `*-setup.md` | `lsp-setup.md` |
| `INTEGRATION` | `*-integration.md` | `pre-commit-integration.md` |
| `NOTES` | `*-notes.md` | `tree-sitter-notes.md` |
| `EXPLAINER` | `*-explainer.md` or content-derived | `vista-meta-bootstrap-explainer.md` |
| `REFERENCE` | content-derived; no required suffix | `stdjson.md`, `commands.md` |

Rules:

- **No `and` in filenames.** `gap-analysis-and-remediation-strategy.md`
  is two docs in a trench coat. Split.
- **kebab-case.** No underscores, no spaces, no camelCase.
- **No filename collisions across `doc_type` families.** A `*-guide.md`
  may not appear under `plans/`; if its content is a design proposal,
  rename to `*-proposal.md` and move it.
- **Status docs are date-stamped.** Two `m-linter-status.md` files
  shouldn't replace each other — they should sit next to each other
  with their dates.

The CI gate enforces filename ↔ doc_type consistency.

---

## 8. Per-doc-type required sections

Each doc_type gets a minimal required-structure check. Templates live
in `.github/docs/templates/` (proposed). CI checks heading presence,
not heading order or contents.

| Doc type | Required H2 sections |
|---|---|
| `ADR` | Status · Context · Decision · Consequences |
| `PLAN` | Goal · Scope · Phases · Success criteria |
| `ROADMAP` | Horizon · Themes · Sequence |
| `PROPOSAL` | Problem · Proposal · Alternatives considered · Open questions |
| `SURVEY` | Scope · Method · Findings · Synthesis |
| `GAP-ANALYSIS` | Target · Current state · Gaps · Recommendations |
| `POSTMORTEM` | Summary · Timeline · Impact · Root cause · Action items |
| `STATUS` | As of · Summary · Per-area state · Next |
| `BUILD-LOG` | (none — chronological entries) |
| `GUIDE` | Audience · Prerequisites · Walkthrough |
| `TUTORIAL` | What you'll build · Prerequisites · Steps · Next |
| `EXPLAINER` | (none — narrative) |
| `SPEC` | Scope · Definitions · Normative requirements · Examples |
| `REFERENCE` | (frontmatter `synopsis:` field carries the summary) |

These mirror well-established templates (Michael Nygard's ADRs,
Google's SRE postmortem template, the Diátaxis types).

---

## 9. CI enforcement

A new `profile/build/validate-docs.py` script runs per-PR on every
repo, mirroring how `validate-repo-meta.py` runs today. Lives as a
make target `make check-docs` in each repo's Makefile.

### Phase 1 — frontmatter and indexing (warn-only, then blocking)

0. **Generated-doc gate (always first).** If `generated: true`, the
   validator runs only the §5.1 sanity checks (declared path, drift
   vs. generator) and skips every check below. This rule is
   non-overridable.
1. **Frontmatter present.** Every non-generated `.md` under `docs/`
   has a valid YAML frontmatter block.
2. **Required keys present.** `created`, `last_modified`, `revisions`,
   `doc_type`, `lifecycle`.
3. **`doc_type` values valid.** Each entry in the list is one of the 23
   known types.
4. **`lifecycle` value valid.** One of the five known states.
5. **`created` / `last_modified` / `revisions` match git.** Tooling
   recomputes and compares; mismatch is auto-fixable.
6. **`docs/README.md` exists.** Top-level index per repo.
7. **No orphans.** Every `.md` file under `docs/` is referenced by
   `docs/README.md`.
8. **No dangling refs.** Every link in `docs/README.md` resolves.

### Phase 2 — naming and structure (warn-only, then blocking)

9. **Filename matches doc_type.** Per the table in §7.
10. **Filename is content-derived.** No `and`; kebab-case; no
    `temp`/`draft`/`new`/`copy` prefixes.
11. **Required H2 sections present.** Per the table in §8.
12. **`markdownlint` clean.** Standard ruleset, repo-overridable.

### Phase 3 — cross-repo and freshness (extend existing weekly cron)

13. **Cross-repo links valid.** Extend the existing
    `check-links.py` to crawl `docs/`.
14. **Freshness gate.** `lifecycle: active` docs whose
    `last_modified` is older than `review_after` (or 12 months by
    default) surface as warnings.
15. **Supersession integrity.** If A says `superseded_by: B`, then B
    must say `replaces: [A]`. Bidirectional check.
16. **Combination warnings.** Docs with refactor-candidate
    combinations (table in §4) surface as warnings in the catalog.

### Phase 4 — org-level catalog (new builder)

17. **`build-doc-catalog.py`** — new sibling of `build-catalog.py`.
    Walks every repo's `docs/`, harvests frontmatter, produces
    `profile/docs.json` keyed by type / repo / lifecycle / freshness.
    Runs in the same weekly cron as the live catalog drift gate.
18. **`docs.schema.json`** — pinned schema for the catalog output, so
    downstream consumers (LLM agents, the m-cli `m doc` family) can
    rely on a stable contract.

Every check is opt-in via repo's `make check-docs` target, mirroring
how `check-docs-prose` already works. Per-PR run uses `--offline`;
weekly cron does the cross-repo walk.

---

## 10. Remediation plan

The bulk work is already done — see §11 — but the existing corpus
still needs cleanup.

### Phase 0 — DONE (2026-05-11)

- Vocabulary established (23 types, 6 connections).
- `docs/README.md` written in every repo (7 indexes, 108 entries).
- Frontmatter applied to every existing doc (108 files).
- Initial cross-repo refactor candidates surfaced (see §4 table).
- Standard accepted (this document) and 7 open questions resolved
  (see §13).

### Phase 1 — Schema + warn-only CI (target: 2026-Q2 weeks 1–4)

- Land `profile/docs.schema.json`.
- Land `profile/build/validate-docs.py` + tests.
- Land `make check-docs` in each repo's Makefile.
- Wire into per-repo CI as **warn-only** for two cron cycles.
- Backfill `lifecycle` field across all 108 docs (default `active`).
- Backfill `owner` field across all 108 docs (default: repo's primary
  committer per `git shortlog`).

### Phase 2 — Block on new docs (target: 2026-Q2 weeks 5–8)

- Flip CI to **blocking** for any new `.md` added under `docs/`.
- Legacy docs remain warn-only.
- First batch of legacy remediations:
  - Rename mis-named files per §7 (estimated ~15 files org-wide
    based on the first-pass labeling).
  - Split confirmed combinations:
    `m-cli/docs/plans/m-linting-implementation-plan.md`
    → `m-linting-implementation-plan.md` (frozen) + `m-linting-build-log.md` (live).
    Similar for `tree-sitter-m/docs/build-log.md` (which is
    `[BUILD-LOG, HISTORY]`).
  - Move mis-placed docs out of `plans/` in m-cli (the 4 docs that
    are surveys, history, or design proposals).

### Phase 3 — Block everywhere; org catalog (target: 2026-Q3)

- Flip CI to **blocking** on legacy docs too. Any doc that hasn't been
  remediated by this point gets a `lifecycle: deprecated` stamp and
  drops out of the freshness gate.
- Land `profile/build/build-doc-catalog.py` + `profile/docs.json`.
- Publish a rendered HTML view in the `.github` repo (mirroring how
  `profile/README.md` surfaces today).

### Phase 4 — Cross-repo and freshness (target: 2026-Q4)

- Extend `check-links.py` to crawl `docs/`.
- Wire freshness warnings into the weekly cron.
- Auto-PR for `last_modified` / `revisions` drift (since these are
  derived from git, they should auto-update on commit; a hook in each
  repo can do this).

### Remediation budget

| Phase | Approx. effort |
|---|---|
| Phase 1 (schema + tooling + warn-only) | ~3 dev-days |
| Phase 2 (block-on-new + first remediation batch) | ~2 dev-days |
| Phase 3 (block-on-legacy + catalog) | ~3 dev-days |
| Phase 4 (cross-repo + freshness) | ~2 dev-days |
| **Total** | **~10 dev-days** spread across Q2–Q4 |

This is small because the org's existing pipeline absorbs most of the
work — there are no new auth surfaces, no new storage, no new
deployment targets. Doc-lint is one more validator under
`profile/build/`.

---

## 11. Mapping to existing infrastructure

| Existing piece | What we extend |
|---|---|
| `profile/repo.meta.schema.json` | Reference, no change. The new docs schema is a sibling. |
| `profile/tools.json` / `task_index.json` | No change. Catalog stays canonical for *tool* discovery. |
| `profile/build/validate-catalog.py` | Pattern to copy for `validate-docs.py`. |
| `profile/build/check-links.py` | Extend to crawl `docs/` markdown. |
| `profile/build/check-freshness.py` | Extend to honor doc-level `review_after`. |
| `profile/build/build-catalog.py` | Pattern to copy for `build-doc-catalog.py`. |
| `make check-docs-prose` (per-repo) | Co-located with new `make check-docs`. |
| `.github/.github/workflows/ci.yml` | One new step: `make check-docs`. |
| Weekly cron handshake | One new job: docs catalog drift + freshness. |

No new languages, no new dependencies beyond `pyyaml` (already a
transitive dep of `jsonschema`-based validators).

---

## 12. Industry references

The pattern below is a synthesis from public-facing engineering org
practices. Direct lifts and inspirations:

- **Spotify Backstage TechDocs** — docs-as-code shipped from each
  service's repo; central catalog harvests metadata. The
  org-catalog-via-per-repo-manifest model here mirrors that.
- **Michael Nygard's ADR template** — Status / Context / Decision /
  Consequences. Adopted verbatim for the ADR required-sections row.
- **Google SRE Workbook — postmortem template** — Summary / Timeline /
  Impact / Root cause / Action items. Adopted verbatim.
- **Diátaxis (Daniele Procida)** — Tutorial / How-to / Reference /
  Explanation. Used as a sanity check on our type vocabulary (§4).
- **Stripe API docs** — single source of truth, generated catalog,
  freshness flags. Pattern for §9 Phase 3.
- **GitHub's `.github` repo convention** — already in use here. This
  proposal adds doc-level metadata to that surface.
- **Daniele Procida's "Documentation system" talk (PyCon AU 2017)** —
  background for the lifecycle states distinction.
- **Cosmic Python (Harry Percival & Bob Gregory) ADR practice** —
  per-decision file, numbered, never edited after acceptance.

The combinable-types approach (§4) is less standard. Most orgs pick a
single canonical type per doc; we explicitly allow combinations because
they surface refactoring debt rather than hiding it. The catalog will
flag combinations as split-candidates, not errors.

---

## 13. Resolved decisions (2026-05-11)

All seven open questions raised during the proposal phase were resolved
on 2026-05-11. The resolutions are folded into the body of this
document (sections noted below); the Q&A is preserved here as the
design record.

### Q1 — Adopt Diátaxis as the layout for `guides/`?

**Decision: YES.** Every doc under `guides/` belongs to exactly one
Diátaxis quadrant. Filename and required-section rules tighten
accordingly. *(Folded into §6, §7, §8.)*

### Q2 — Per-doc OWNERS vs. frontmatter `owner`?

**Decision: frontmatter `owner` for now.** A `.github/CODEOWNERS`-style
file remains available as an escalation path if review routing becomes
painful, but is not part of Phase 1. *(Folded into §5.)*

### Q3 — Should `frozen` plans move to `docs/history/`?

**Decision: leave in place; mark in frontmatter only.** Moving frozen
docs would break inbound links across repos and across the existing
catalog. The catalog renders frozen docs in a separate view based on
`lifecycle: frozen`. *(Folded into §5 — lifecycle table.)*

### Q4 — Connections (`connections: […]`) — required or optional?

**Decision: optional. Harvest retroactively. Revisit later.** Phase 1
leaves the field optional in the frontmatter schema. Phase 3's catalog
builder will harvest connections from each repo's existing
`docs/README.md` (which already captured them in the first pass) into
the central catalog. Whether to make them required is revisited when
the catalog is in production. *(Folded into §4.)*

### Q5 — Generated documents

**Decision: generated documents are excluded from docs QA/CI.** They
have a machine-driven lifecycle and their integrity is already
guarded by the existing manifest drift gates. The exclusion is a
**rule, not a guideline** — it is enforced by:

1. The `generated: true` frontmatter field, which the validator honors
   as a hard short-circuit.
2. A new `docs.generated_paths` array in `repo.meta.json` declaring
   which path globs are generated, so the marker can't be applied to
   hand-written docs to silence CI.
3. A drift check that the file's `last_modified` matches the latest
   generator run.

*(Folded into §5.1 as the canonical statement of the rule. §9 check #0
implements it.)*

### Q6 — Cross-repo doc links

**Decision: full URLs.** Same convention as the existing catalog. An
`org:/` shorthand is deferred indefinitely; the cost of maintaining
full URLs is small relative to the cost of adopting a non-standard
link syntax that breaks every existing markdown renderer.

### Q7 — Migration of `m-cli/docs/plans/`

**Decision: one PR with movement-only changes, then per-doc PRs for
substantive splits.** This isolates filesystem moves (reviewable as a
diff of paths) from content changes (reviewable as a diff of text).
The movement-only PR is mechanical; the split PRs each address one
combination from the §4 refactor-candidate table. *(Reflected in §10
Phase 2.)*

---

## Appendix A — comparison to the first-pass output

The first-pass index applied 23 types and 6 connections to 108 docs.
The distribution:

- 32 docs are `[REFERENCE]` (one-third — m-stdlib modules dominate).
- 9 docs are `[ADR]` (m-standard 6, tree-sitter-m 6 — both numbered).
- 11 docs carry combinations from §4's table (refactor candidates).
- 9 docs are STATUS-typed (live trackers, mostly in m-stdlib).

That distribution is healthy: most docs are single-typed, the
combinations are concentrated in the planning/execution split that
the §6 layout standard separates, and the live trackers are already
in `tracking/`. No huge surprises; the remediation work is small and
mostly mechanical.

---

## Appendix B — what this proposal does NOT do

- It does not change the existing manifest schemas (`repo.meta`,
  `tools.json`, `task_index.json`). Those are for machine-readable
  artifacts; this is for prose.
- It does not require existing docs to be rewritten — only re-stamped
  with frontmatter (already done) and possibly renamed/moved.
- It does not introduce a separate docs build system. Same Python,
  same `make`, same CI as everything else.
- It does not require an external service. The org catalog is one
  more JSON file in `profile/`.

---

*End of proposal. Pending review before any Phase 1 work begins.*
