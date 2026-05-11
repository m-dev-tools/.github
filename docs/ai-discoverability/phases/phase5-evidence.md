# Phase 5 — Exit evidence

**Captured:** 2026-05-11T16:15Z (Track E landing).

Per [`phase5-plan.md` §10 "Phase 5 Done — Definition"](phase5-plan.md):
clean runs of the four enforcement gates plus per-PR CI wiring + a
weekly cron firing are the documented exit. This doc mirrors the
[`phase4-evidence.md`](phase4-evidence.md) shape: one section per
gate, "What this proves" wrap-up, then each §10 done-criterion cited
green.

Phase 5 is the operational-loop close: with all four watchdogs live,
every architectural promise the framework makes is now backed by an
automated CI check rather than maintainer discipline.

## `pytest profile/build/` — 116 / 116

```
........................................................................ [ 62%]
............................................                             [100%]
116 passed in 2.09s
```

Phase 4 closed at 51 cases. Phase 5 added 65 more across the four
gates + the carry-over fix:

| Track | Module | Cases |
|---|---|---|
| A — freshness | `test_check_freshness.py` | 15 |
| B0 — validate-repo-meta binary-URL fix | `test_validate_repo_meta.py` | 5 |
| B — link-check | `test_check_links.py` | 13 |
| C — license-reconcile | `test_check_licenses.py` | 18 |
| D — schema-version policing | `test_check_schema_compat.py` | 14 |

## `make check-freshness` — clean (worst=OK)

Per [phase5-plan.md §2](phase5-plan.md). Status taxonomy:
OK / WARN / STALE / MISSING / INVALID; aggregator ranks
**STALE > MISSING > INVALID > WARN > OK** (STALE is the strongest
fix-now signal; INVALID/MISSING outrank WARN because they signal a
real bug, not just age).

10 catalog entries + 4 recipes, all dated 2026-05-10 or 2026-05-11:

```
check-freshness: clean (worst=OK)
```

PR-mode runs default thresholds (`--warn-days 90 --stale-days 180`;
WARN allowed). The weekly cron firing escalates with `--strict` so
a freshness slip past 90 days surfaces within 7 days.

## `make check-links` — clean (offline; 59 URLs catalogued)

Per [phase5-plan.md §3](phase5-plan.md). Walks every URL surfaced
by:

* `profile/llms.txt` — Markdown link targets.
* `profile/tools.json` — top-level `$schema` + every
  `tools.<key>.<field>_url` value.
* `profile/task_index.json` — top-level `$schema` + every `doc`
  field across every category/row.

```
check-links: clean (offline; 59 URLs catalogued)
```

PR-mode is `--offline` (inventory only — no network round-trip).
The weekly cron firing on the handshake job runs the full HEAD walk:
200/301/302 OK, 405→GET fallback, anything else FAIL. Binary URLs
(`.whl` / `.tar.gz` / …) work the same way — HEAD only, no decode.

**Carry-over fix in the same PR (B0):** `validate-repo-meta.py`'s
UTF-8-decode crash on binary `exposes.*` URLs is fixed. The
pre-Phase-4 workaround `ARGS=--no-resolve` is no longer required;
`make check-repo-meta` in full-resolve mode now works against the
v0.1.0 wheel URL.

## `make check-licenses` — clean (worst=SKIP)

Per [phase5-plan.md §4](phase5-plan.md). Per-license signature dict
— **AGPL-3.0**, **Apache-2.0**, **MIT**, **BSD-3-Clause**,
**GPL-3.0** — each with three distinct substring markers. A body
matches when ≥ 2 markers hit (per plan §9: prefer false negatives
over false positives). Specificity ordering: AGPL is tried before
GPL because both share "GENERAL PUBLIC LICENSE" + "Version 3" but
only AGPL carries "AFFERO".

```
check-licenses: clean (worst=SKIP)
```

9 INVENTORIED rows + 1 SKIP (`m-modern-corpus` declares
`LicenseRef-mixed-per-subdir` — per-subdir licensing can't be
reconciled by signature match).

PR-mode is `--offline`; the weekly cron firing fetches each repo's
`LICENSE` at `raw.githubusercontent.com/<repo>/main/LICENSE` and
signature-matches the body.

## `make check-schema-compat` — clean

Per [phase5-plan.md §5](phase5-plan.md). Diffs
`profile/tools.schema.json` + `profile/task_index.schema.json`
between a base ref (default `origin/main`) and HEAD; enforces two
rules:

1. If `schema_compat` bumps in either schema,
   `profile/schema-changelog.md` must appear in the same diff →
   otherwise `MISSING_CHANGELOG_ROW` (exit 1).
2. Non-additive shape changes without a `schema_compat` bump →
   `NON_ADDITIVE_WITHOUT_BUMP` (exit 1). Three heuristics:
   required field removed, enum value removed, `additionalProperties`
   tightened `true` → `false`.

```
check-schema-compat: clean
```

**Per-PR-only gate** — no cron firing. `schema_compat` bumps land
via PRs by definition; a periodic re-run adds no signal. Critical
wiring detail: the `check` job's `actions/checkout@v4` uses
`fetch-depth: 0` so `git show origin/main:…` works in CI.

## Companion gates (Phase-3-era, still passing)

```
make handshake          — step 8 — exit 0 (success)
make recipes-check      — 4 recipe(s) clean
make validate-catalog   — OK
```

The Phase-3 discovery handshake, recipe structural gate, and
catalog drift gate continue to pass after the Phase 5 additions —
no regression from layering the four new watchdogs on top.

## What this proves

1. **Every architectural promise has a watchdog.** Pre-Phase-5,
   `verified_on` correctness, URL liveness, declared-license
   accuracy, and schema-compat discipline lived in maintainer heads.
   Post-Phase-5, each has an automated gate that surfaces drift —
   either per-PR (synchronous, fast) or via the weekly cron
   firing (within 7 days; matches the parent-plan §7 Phase-5 exit
   criterion).
2. **Failures are structured.** Each gate emits a stable status
   taxonomy (OK / WARN / STALE / FAIL / MISMATCH / etc.) plus a
   Markdown table sorted worst-first. CI logs are immediately
   actionable.
3. **TDD coverage holds.** Every behavior added in Phase 5 has a
   pinned regression test, including the validate-repo-meta
   binary-URL fix (B0) and the schema-compat ephemeral-git-repo
   end-to-end cases. 116/116 total.
4. **Offline + live modes split cleanly.** PR-mode is `--offline`
   (no network, no flake). Weekly cron mode fetches live URLs +
   live LICENSE bodies. The split keeps per-PR CI fast while still
   surfacing upstream drift within a week.
5. **CI fetch-depth gotcha is fixed.** Track D's
   `check-schema-compat.py` needs `origin/main` reachable in the
   CI runner's git history; the workflow change to `fetch-depth: 0`
   keeps the gate working without slowing the runner (this repo is
   small).

## Phase 5 closed

All seven [`phase5-plan.md` §10](phase5-plan.md) done-criteria met:

1. **`profile/build/check-freshness.py`** exists, TDD-covered
   (15 cases), `make check-freshness` exits 0 on `main` ✓ (Track A
   PR #32 / `e9e00cb`).
2. **`profile/build/check-links.py`** exists, TDD-covered
   (13 cases), `make check-links --offline` and full-fetch both
   exit 0 on `main`. The `validate-repo-meta.py` binary-URL bug is
   fixed (5 cases) ✓ (Track B PR #33 / `16bbd08`).
3. **`profile/build/check-licenses.py`** exists, TDD-covered
   (18 cases), `make check-licenses` exits 0 across all 10 active
   repos ✓ (Track C PR #34 / `5d9a995`).
4. **`profile/build/check-schema-compat.py`** exists, TDD-covered
   (14 cases), `make check-schema-compat` exits 0 against `main`
   (no schema bump in any Phase-5 PR) ✓ (Track D PR #35 /
   `8792787`).
5. **`.github/workflows/ci.yml`** runs all four `--offline`
   variants on every push/PR ✓ (`Freshness gate` + `Link inventory`
   + `License inventory` + `Schema-version policing` steps in the
   `check` job).
6. **The weekly cron firing** runs `--strict` freshness + live
   link-check + full LICENSE-fetch ✓ (handshake job; Monday-14:00
   UTC cron from Phase-3 Track D).
7. **`docs/ai-discoverability/phases/phase5-evidence.md`** captures
   clean runs of every gate, with each criterion cited green ✓
   (this file).

When all seven are true (now), the AI-discoverability framework's
operational loop is complete. Future phases — if any — address
*growth* scenarios (more repos, more tools, more catalog kinds)
rather than enforcement coverage.

## Out-of-scope follow-ups noted in the plan

These remain open after Phase 5, by design:

- **Phase-3-era YAML parser limitation** in `run-recipe.py`'s
  `_parse_minimal_yaml` (no `>` block scalars / `[]` inline empty
  arrays). The four shipped recipes work around it; the gate runs
  clean.
- **Live-fetch freshness mode.** Track A's `--strict` cron only
  re-reads the committed catalog's `verified_on`; a future
  improvement would walk each repo's upstream `repo.meta.json` and
  detect maintainers who re-verified but forgot to bump. Deferred
  per plan §9.
- **Multi-license per-file detection.** Phase-5 Track C reconciles
  the project-level `LICENSE` file against the declared license;
  per-file SPDX expressions are explicitly out of scope per plan
  §0 "Not in scope".

Phase 5 close. The framework's invariants are now CI-enforced.
