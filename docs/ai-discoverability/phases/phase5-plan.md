# Phase 5 Implementation Plan — Continuous Enforcement Hardening

**Parent plan:** [`AI-discoverability-plan.md`](../AI-discoverability-plan.md) §6
**Master doc:** [`AI-discoverability-architecture.md`](../AI-discoverability-architecture.md) §5 "Operational invariants"

**Phase 5 goal:** Every architectural promise that's currently held by
maintainer discipline gets an automated watchdog. Once a watchdog
exists for it, drifting away from the promise breaks CI — humans don't
have to remember.

**Phase 5 exit (parent-plan §7 Phase 5):** a stale catalog or broken
link is caught within 7 days. Concretely:

- `make check-freshness` + `make check-links` + `make check-licenses`
  + `make check-schema-compat` are real Make targets on `.github`.
- Per-PR CI runs `check-schema-compat` and the cheap subset
  (`check-freshness` over local manifests + lightweight license-shape
  validation).
- A weekly cron job firing `check-freshness --strict`, `check-links`
  (live URLs), and `check-licenses` (full LICENSE-file reconcile)
  catches drift within 7 days of merge.
- `docs/ai-discoverability/phases/phase5-evidence.md` captures the
  exit-gate output for each.

**Scope.** Building the four enforcement gates listed in
[parent plan §6.2 + §6.3](../AI-discoverability-plan.md#6-continuous-enforcement):

| Gate | What it watches | Failure mode it prevents |
|---|---|---|
| Freshness | `verified_on` fields across every `repo.meta.json` + recipe | Stale claims; "this worked in 2025" rotting into "this no longer compiles". |
| Link-check | Every URL in `llms.txt` + every `*_url` in `tools.json` + every `doc` in `task_index.json` | Pointer-URL rot. The whole "pointers, not facts" invariant fails silently if pointers 404. |
| License-reconcile | Declared `license` in `repo.meta.json` vs the actual `LICENSE` file's signature | Silent license-drift inside the org; a fork's LICENSE swap going unnoticed. |
| Schema-version | `schema_compat` bumps on any `*.schema.json` | A consumer pinned to v1 silently breaking when the org publishes v2. |

**Not in scope:**

- **PyPI publishing** — same deferral as Phase 4 (parent plan §5.3).
- **Auto-bumping `verified_on`.** Freshness is a *warning + report*
  surface; refreshing the date is a maintainer's act after they re-run
  the verification commands.
- **Rate-limit-friendly retry logic** for the live-URL scanner. The
  weekly cron firing in a public GitHub-Actions runner is well within
  raw.githubusercontent.com's anonymous quota. Add backoff only if
  CI actually flakes.
- **Multi-license per-file detection** (e.g. SPDX expressions).
  License-reconcile checks the project-level LICENSE file against the
  declared `license` field. Per-file license stamps are out of scope.

---

## 0. Blocking dependencies

All upstream phases closed. No external blockers.

Two carry-over follow-ups become Track-B prerequisites:

| Origin | Item | Lands in |
|---|---|---|
| Phase 4 D | `profile/build/validate-repo-meta.py` chokes on binary `exposes.*` URLs (UTF-8 decode of wheel bytes) | Track B (B0 — bug fix) |
| Phase 3 | `profile/build/run-recipe.py`'s `_parse_minimal_yaml` doesn't handle `>` block scalars or `[]` inline arrays | Out of scope. Track B's link-checker reads JSON not YAML; doesn't touch this. Stays as a recipe-runner improvement for a separate PR. |

Verification commands (re-runnable to confirm launch state):

```bash
cd .github
make catalog && make validate-catalog && make phase0-smoke
make handshake && make recipes-check
pytest profile/build/ -q
```

All should be green on `main` (51/51 pytest cases as of Phase 4
close).

---

## 1. Track Layout

Five tracks. Tracks A through D are independent of each other; Track
E integrates after all four finish.

```
+---------------------------------------------------+
| Tracks A / B / C / D — parallel, independent      |
| Each delivers one Make target + one CI step       |
+---+----------+----------+----------+--------------+
    |          |          |          |
    | A        | B        | C        | D
    | fresh    | links    | license  | schema-compat
    v          v          v          v
+----------------------------------------------------+
| Track E — Phase 5 evidence + close-out             |
| Runs in .github; waits until A+B+C+D land           |
+----------------------------------------------------+
```

### Track index — callable names

| Track | Purpose | Stages |
|---|---|---|
| **A** | Freshness gates over `repo.meta.json` + recipe `verified_on` | A1 → A4 |
| **B** | Link-checking over llms.txt + every `*_url` in tools.json + `doc` in task_index. Fixes Phase-4 carry-over (validate-repo-meta binary-decode bug) first. | B0 → B4 |
| **C** | License-reconcile: declared `license` vs `LICENSE`-file signature | C1 → C4 |
| **D** | Schema-version policing: schema_compat bumps require a `schema-changelog.md` row | D1 → D4 |
| **E** | Phase 5 evidence + close-out PR | E1 → E2 |

To call out work: `run A`, `run B0`, `run B through B2`, `run C+D in
parallel` (the four tracks have no file overlap; any pair is safe).

### Parallel safety guarantees

- **No file overlap.** Each track adds one new file under
  `profile/build/check-<gate>.py`, one new Make target, and one CI
  step. Track B additionally touches `validate-repo-meta.py` for the
  bug fix.
- **No shared mutable state.** All four gates are read-only over the
  catalog. None of them edit `tools.json` / `task_index.json` /
  `llms.txt`.
- **Schema additions are forward-compatible.** None of these tracks
  bump `schema_compat`; Track D *gates* future bumps but doesn't
  introduce one.

### Stage status conventions

Same as Phase 0 / 1 / 3 / 4. Each stage is one of: `todo`, `doing`,
`done`, `blocked`. A stage is `done` only when its verification
command exits 0.

---

## 2. Track A — Freshness gates

Runs in `.github`. Single-session work; ~half-day.

### A1 — TDD: `tests/test_check_freshness.py`

**Output:** new pytest module exercising `check_freshness_impl(data,
today, warn_days, stale_days)` (pure function over loaded data).

Cases:

- Recent `verified_on` (today) → `OK`.
- `verified_on` warn_days+1 → `WARN`.
- `verified_on` stale_days+1 → `STALE`.
- Missing `verified_on` → `MISSING` (treated as STALE for gate purposes).
- Malformed `verified_on` (not `YYYY-MM-DD`) → `INVALID`.
- Computes per-entry + an overall worst-case status.

Confirm RED before A2.

### A2 — Implement `profile/build/check-freshness.py`

**Output:** CLI tool that walks:

- Every `tools.<key>` entry in `profile/tools.json` (uses
  `repo_meta_url` to fetch the upstream `repo.meta.json`; falls back
  to the cached `verified_on` already on the catalog entry if
  network-unreachable).
- Every recipe under `docs/recipes/*.md` (parses YAML frontmatter via
  the same minimal parser `run-recipe.py` already uses).

Output (default): a Markdown table per source (catalog + recipes)
sorted worst-first. Per row: `id`, `verified_on`, `age_days`,
`status`.

Exit codes:

- `0` — all entries pass (no STALE; WARN allowed by default).
- `1` — any entry STALE, INVALID, or MISSING under `--strict`.
- `2` — fixture / network failure.

Defaults: `--warn-days 90`, `--stale-days 180`. CLI overrides
documented in the module docstring.

`--offline` mode: don't fetch upstream; only check `verified_on` as
recorded on `tools.json` + recipe frontmatter. Used by the per-PR
job.

### A3 — Makefile target + CI wiring

**Output:** new target in `.github/Makefile`:

```make
check-freshness:
	python3 profile/build/check-freshness.py --offline
```

**CI (per-PR):** new step in the `check` job in
`.github/.github/workflows/ci.yml` that runs `make check-freshness`.
Doesn't fail PRs on WARN; fails only on STALE / INVALID / MISSING.

**CI (weekly cron):** new step on the existing `handshake` cron
schedule that runs `check-freshness.py --strict` over the live
catalog (fetches upstream `repo.meta.json` to detect maintainers who
forgot to bump `verified_on` after re-verifying).

### A4 — Test sweep + ship

**Verify:** `pytest profile/build/test_check_freshness.py` green;
`make check-freshness` exits 0 against current `main`; commit, push
under a single `phase5-A` PR; CI green; squash-merge.

---

## 3. Track B — Link-checking

Runs in `.github`. Single-session work, but a bit larger because of
the carry-over fix in B0.

### B0 — Carry-over: fix `validate-repo-meta.py` binary URL bug

**Output:** edit `profile/build/validate-repo-meta.py`'s
`resolve_one` so non-text URLs (`.whl` / `.tar.gz` / `.zip` /
content-type not `text/*` and not `application/json`) are HEAD-
checked instead of GET-and-decoded. Adds a tiny case to
`test_validate_repo_meta.py` (or wherever its tests live) for the
new behaviour.

**Verify:** `make check-repo-meta META=/home/rafael/m-dev-tools/m-dev-tools-mcp/dist/repo.meta.json`
(full mode, no `--no-resolve`) returns OK against the v0.1.0 wheel
asset URL.

### B1 — TDD: `tests/test_check_links.py`

**Output:** new pytest module exercising the URL-walker.

Cases:

- llms.txt has 3 valid file://-fixture links → 0 failures.
- One link in tools.json returns 404 → 1 failure with URL printed.
- A binary asset (the v0.1.0 wheel) returns 200 via HEAD → OK
  (no decode attempted).
- A 405-on-HEAD endpoint falls back to GET → OK.
- An unreachable host (DNS failure) → 1 failure, structured exit.
- `--allow-redirects` flag follows 301/302 chains (default ON).

Confirm RED before B2.

### B2 — Implement `profile/build/check-links.py`

**Output:** CLI tool that collects every URL from:

- `profile/llms.txt` (via existing `extract_llms_links`).
- `profile/tools.json` — every `*_url` field plus the top-level
  `$schema`.
- `profile/task_index.json` — every `doc` field plus typed-ID-derived
  fetches (the `task_index.recipes` rows are skipped; they're not
  URLs).

Walks each URL via HEAD with a 405→GET fallback; allows 200, 301,
302 (after redirect-follow). Output: Markdown table sorted
worst-first; exits `0` if all 200/redirects, `1` if any failure,
`2` on transport error.

`--offline` mode: skip network entirely; just inventory URLs and
report the count (so the per-PR job can prove "we know about N
URLs" without hitting the network).

### B3 — Makefile target + CI wiring

**Output:** `make check-links` target.

**CI (per-PR):** new step that runs `check-links.py --offline`
(inventory only — no network).

**CI (weekly cron):** new step on the existing cron schedule that
runs `check-links.py` against the live URLs. Same cron firing as
the existing handshake-live step (one cron job, multiple steps).

### B4 — Ship

**Verify:** `pytest tests/test_check_links.py` green; both Make
targets green locally; single PR; CI green; merge.

---

## 4. Track C — License-reconcile

Runs in `.github`. Smaller than A/B; ~half-day.

### C1 — TDD: `tests/test_check_licenses.py`

**Output:** new pytest module.

Cases:

- declared `AGPL-3.0` + LICENSE file matches AGPL-3.0 signature → OK.
- declared `AGPL-3.0` + LICENSE file matches MIT signature → MISMATCH.
- declared `AGPL-3.0` + LICENSE file missing / 404 → MISSING.
- declared `MIT` + LICENSE file MIT → OK (proves the matcher isn't
  hard-coded to AGPL).
- declared `LicenseRef-mixed-per-subdir` (the m-modern-corpus case)
  → SKIP with a documented reason; not an error.

Signature matcher: substring-match against canonical license-text
markers. No external SPDX library — keeps the gate dependency-free.

Confirm RED before C2.

### C2 — Implement `profile/build/check-licenses.py`

**Output:** CLI tool that walks every `tools.<key>` entry in
`tools.json`. For each:

1. Read the entry's `license` field.
2. Fetch `<repo>/blob/main/LICENSE` (raw URL derived from the entry's
   `repo` field).
3. Match the body against a small dictionary of known license
   signatures (AGPL-3.0, GPL-3.0, MIT, Apache-2.0, BSD-3-Clause).
4. Report OK / MISMATCH / MISSING / SKIP per entry.

Exit codes: `0` all OK or SKIP; `1` any MISMATCH or MISSING; `2`
transport failure.

`--offline` mode: only validates that the declared `license` field
is in our known-signature dict — doesn't fetch the LICENSE file.

### C3 — Makefile target + CI wiring

**Output:** `make check-licenses` target.

**CI (per-PR):** offline mode only (sanity-check declared license
strings).

**CI (weekly cron):** full-fetch mode under the existing cron firing.

### C4 — Ship

**Verify:** `pytest tests/test_check_licenses.py` green; Make target
clean against current `main` (all 10 active repos are AGPL-3.0
except `m-stdlib-vscode` which is MIT — both signatures must
register OK); single PR; CI green; merge.

---

## 5. Track D — Schema-version policing

Runs in `.github`. Smallest of the four tracks; ~quarter-day.

### D1 — TDD: `tests/test_check_schema_compat.py`

**Output:** new pytest module.

Cases:

- PR diff has no schema change → `OK`.
- PR diff bumps `schema_compat: 1 → 2` in `tools.schema.json` and
  *also* modifies `docs/ai-discoverability/schema-changelog.md` →
  `OK`.
- PR diff bumps `schema_compat` without touching the changelog →
  `MISSING_CHANGELOG_ROW` (exit 1).
- PR diff modifies `tools.schema.json` *without* bumping
  `schema_compat`, but the diff is non-additive (removes a required
  field) → `NON_ADDITIVE_WITHOUT_BUMP` (exit 1).
- Pure additive diff (adds an optional field) without bump → `OK`.

The "non-additive" heuristic is deliberately conservative: detect
common patterns (removed required field, removed enum value,
tightened `additionalProperties` from `true` → `false`). False
positives are acceptable since the maintainer can bump and add the
changelog row.

Confirm RED before D2.

### D2 — Implement `profile/build/check-schema-compat.py`

**Output:** CLI tool that takes a base ref (default
`origin/main`) and a head ref (default `HEAD`), reads both versions
of `tools.schema.json` and `repo.meta.schema.json`, diffs them, and
applies the rules above.

`schema-changelog.md` lives under `docs/ai-discoverability/`
(verify path; Phase 1 P1-X created it). The check parses it
expecting one row per `schema_compat` value.

### D3 — Makefile target + CI wiring

**Output:** `make check-schema-compat` target.

**CI (per-PR):** new step that runs `check-schema-compat.py` with
the merge-base of the PR's base branch.

**CI (weekly cron):** not applicable; this is a per-PR gate by
design (catches the bump at PR time).

### D4 — Ship

**Verify:** existing tests/checks all stay green (no schema bump in
this Track); `pytest tests/test_check_schema_compat.py` green;
single PR; CI green; merge.

---

## 6. Track E — Phase 5 smoke + evidence

Runs in `.github`. Blocked by A4 ∧ B4 ∧ C4 ∧ D4.

### E1 — Phase 5 smoke

**Output:** evidence file `docs/ai-discoverability/phases/phase5-evidence.md`.

Mirrors `phase4-evidence.md` shape: one section per gate, "What this
proves" wrap-up, then each §10 done-criterion cited green.

Run:

```bash
make check-freshness                   # offline; PR-mode
make check-freshness -- --strict       # full-fetch; cron-mode dry-run
make check-links                       # offline
make check-links -- --no-offline       # cron-mode dry-run
make check-licenses
make check-schema-compat               # exits 0 — no schema change in this commit
pytest profile/build/                  # full suite
```

Capture each command's output. Capture one cron-job log link
(GitHub Actions URL) for the live runs.

### E2 — Close-out PR

Single PR. Commit subject: `phase5-E: smoke + evidence; Phase 5
closed`.

**Verify:** PR merged; `phase5-evidence.md` on `main`;
[`AI-discoverability-architecture.md`'s "Phase 5 outlook" section](../AI-discoverability-architecture.md#phase-5-outlook)
gets a brief edit to flip from "no plan yet" to "closed; see
`phases/phase5-evidence.md`".

---

## 7. Stage Matrix — Single-Glance View

| Stage | Blocked by | Verification |
|---|---|---|
| A1 | — | RED tests for `check_freshness_impl` |
| A2 | A1 | A1 tests green; `check-freshness.py` runs against fixtures |
| A3 | A2 | `make check-freshness` exits 0 |
| A4 | A3 | PR merged; CI step green per-PR; cron step green on first firing |
| B0 | — | `make check-repo-meta META=…` (full mode) green against the v0.1.0 wheel URL |
| B1 | B0 | RED tests for `check-links.py` |
| B2 | B1 | B1 tests green |
| B3 | B2 | `make check-links --offline` exits 0; `make check-links` (live) exits 0 |
| B4 | B3 | PR merged; CI per-PR + cron steps green |
| C1 | — | RED tests for `check-licenses.py` |
| C2 | C1 | C1 tests green |
| C3 | C2 | `make check-licenses` exits 0 |
| C4 | C3 | PR merged; CI per-PR + cron steps green |
| D1 | — | RED tests for `check-schema-compat.py` |
| D2 | D1 | D1 tests green |
| D3 | D2 | `make check-schema-compat` exits 0 against `main` |
| D4 | D3 | PR merged; CI per-PR step green |
| E1 | A4 ∧ B4 ∧ C4 ∧ D4 | `phase5-evidence.md` captures clean runs of all four gates + the seven §10 done-criteria cited green |
| E2 | E1 | PR merged; Phase 5 closed |

---

## 8. Calling Convention

Same shape as Phase 0 / 1 / 3 / 4.

- **`run A`** — execute Track A end-to-end (~half-day).
- **`run B`** — execute Track B end-to-end (~3/4 day with B0 fix).
- **`run B0`** — execute only the `validate-repo-meta.py` bug-fix
  stage.
- **`run C+D in parallel`** — spawn two independent sessions (no
  file overlap).
- **`resume B from B2`** — continue from a checkpoint; assumes B0
  and B1 done.

A Claude session given a track callout should:

1. Read this document.
2. Confirm blocking stage(s) are `done` on `main`.
3. Execute its stages in order.
4. Run the verification command at the end of each stage; halt on
   failure.
5. Report the final state when the track (or named substage) completes.

Do **not** advance a stage whose verification didn't exit 0. Halt
and report.

### Recommended order

If executing single-threaded:

1. **B0** (fixes the Phase-4 follow-up so Track B itself can use the
   full-resolve validator).
2. **A + B in parallel**, then **C + D in parallel** (or all four in
   parallel — no shared state).
3. **E** (smoke + evidence; close-out).

Total Phase 5 elapsed: ~2 weeks single-threaded; ~1 week with one
parallel pair.

---

## 9. Risk Notes

- **Network-flake noise in the weekly cron.** GitHub-Actions runners
  occasionally hit transient 5xx from raw.githubusercontent.com.
  Mitigation: each network gate is allowed two retries with 5-second
  backoff before flagging an error. Sustained 5xx still surfaces;
  one-shot blips don't.
- **License-signature matcher precision.** A small substring-match
  dictionary risks both false positives (treating GPL as AGPL) and
  false negatives (missing a newer AGPL variant). Mitigation: the
  matcher carries a per-license set of three or more distinct
  signature substrings — at least two must match. Concrete tradeoff:
  prefer false negatives (MISSING) over false positives (silent
  MISMATCH).
- **Schema-changelog detection.** Track D's "modified the changelog
  in the same PR" check uses the PR's file diff. If a contributor
  bumps `schema_compat` in one PR and adds the changelog row in a
  follow-up PR, the second PR's check passes (no bump in *that*
  diff). Acceptable: the per-PR gate is necessary but not sufficient;
  the schema_compat value pinned in `tools.json`'s
  `discovery_protocol.step_2_match_intent` row carries the
  authoritative version. A separate consistency check that
  `schema-changelog.md` covers every value `schema_compat` has held
  is a stretch goal (D5 — not gating Phase 5 exit).
- **Freshness threshold tuning.** The 90/180-day defaults are
  guesses. Track A2 ships them as `--warn-days` / `--stale-days`
  flags so a maintainer can re-tune without a code edit. The
  Makefile target uses the defaults; the cron job can override per
  the Workflow YAML.
- **Carry-over follow-up risk.** B0's `validate-repo-meta.py` fix
  changes the validator's behaviour on full-resolve mode. The
  existing `make check-repo-meta` calls all use `ARGS=--no-resolve`
  (workaround for the bug); removing the workaround is *out of
  scope* for B0 — just fix the bug, leave the call sites alone.
- **No live URLs in PR-mode CI.** Per-PR jobs run only the
  `--offline` variants of each gate. The live network round-trip
  belongs in the weekly cron firing. Otherwise CI becomes flaky on
  upstream transient issues, which destroys signal value.

---

## 10. Phase 5 Done — Definition

Phase 5 is done when **all** of these are true:

1. `profile/build/check-freshness.py` exists, is TDD-covered, and
   `make check-freshness` exits 0 on `main`.
2. `profile/build/check-links.py` exists, is TDD-covered, and both
   `make check-links` (live) + `make check-links --offline` exit 0
   on `main`. The `validate-repo-meta.py` binary-URL bug is fixed.
3. `profile/build/check-licenses.py` exists, is TDD-covered, and
   `make check-licenses` exits 0 across all 10 active repos.
4. `profile/build/check-schema-compat.py` exists, is TDD-covered,
   and `make check-schema-compat` exits 0 against `main` (no
   schema bump in any of the Phase 5 PRs).
5. `.github/.github/workflows/ci.yml` runs the four `--offline`
   variants on every push/PR.
6. The existing weekly cron job runs the four `--no-offline`
   variants once a week.
7. `docs/ai-discoverability/phases/phase5-evidence.md` captures
   clean runs of every gate, with each criterion in this list
   cited green (same pattern as `phase4-evidence.md`).

When all seven are true, the AI-discoverability framework's
operational loop is complete. Future phases (if any) address growth
scenarios — adding more repos, more tools, more catalog kinds —
rather than enforcement coverage.
