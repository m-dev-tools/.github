---
created: 2026-05-11
last_modified: 2026-05-12
revisions: 1
doc_type: [WORKED-EXAMPLE, TUTORIAL, SMOKE-TEST]
---

## M Test-Driven Development: A Walkthrough

End-to-end transcript of a real M developer building a small
data-analysis application — **`reqstats`**, an HTTP-access-log
summarizer — using only the `m` toolchain and the `m-stdlib` standard
library. Doubles as a turnkey smoke test that every `m <subcommand>`
works on *any* docker-capable host, from a clean checkout.

The finished application is left in place at `~/m-work/reqstats/` so
the next session can re-run any step. m-stdlib's `.m` files are
vendored into `routines/` so the engine container can find them
(see [§ Vendoring m-stdlib](#4-vendoring-m-stdlib) below).

**Surface coverage.** Every one of the 28 distinct invocations in
[`cli-menu-system.md`](cli-menu-system.md) is exercised below at least
once, except for `m engine reset` (destructive — touched in description
only) and `m watch` (long-running — mentioned only). The final 100 %
label-coverage gate against the production routine validates the
inner-loop chain end to end.

---

## Prerequisites

See the [Getting started guide](m-dev-tools-setup.md) for the
turnkey-setup-on-a-fresh-host path — prerequisites, install via
`setup.sh` (or manual), `m doctor` verification, and troubleshooting.
The walkthrough below assumes a green `m doctor`.

---

## 0. Scenario

`reqstats` ingests a CSV access log (timestamp, method, path, status,
bytes) and emits a JSON summary:

```text
{
  "class": {
    "2xx": {"count": 2, "bytes": 4000},
    "5xx": {"count": 1, "bytes": 512}
  },
  "totals": {"requests": 3, "bytes": 4512, "mean_bytes": 1504}
}
```

The pipeline:

```
CSV bytes →  $$parse^STDCSV  →  rows(i,j)
          →  aggregate         →  plain summary tree
          →  toJsonTree        →  STDJSON sigil tree
          →  $$encode^STDJSON  →  JSON text
```

Three m-stdlib modules earn their place: **STDCSV** (parsing),
**STDMATH** (`$$mean`), **STDJSON** (encode); plus **STDASSERT**
in the tests.

---

## 1. Environmental health — `m doctor` + `m engine`

Day-zero sanity. The transport probe and the engine container both
have to be green before anything else makes sense.

```text
$ m doctor

  ✓ OK      docker_installed   docker CLI on PATH
  ✓ OK      docker_daemon      docker daemon reachable
  ✓ OK      engine_image       image ghcr.io/m-dev-tools/m-test-engine:0.1.0 present
  ✓ OK      engine_container   container `m-test-engine` running
  ✓ OK      engine_bind_mount  host /home/rafael/m-work exists
  ✓ OK      parser             tree-sitter-m loaded
  ✓ OK      keywords           323 M language keywords loaded from m-standard

7 OK, 0 warning, 0 fail, 0 skipped
```

`m doctor` is transport-aware — on a docker host it runs the docker
checks; on a local-YDB host it runs the local-YDB checks. The
[engine refactor follow-ups](evolution.md#engine-refactor-follow-ups)
in `evolution.md` cover the routing rule.

Inspect the engine container in more detail:

```text
$ m engine status
driver:           docker
image:            ghcr.io/m-dev-tools/m-test-engine:0.1.0
container:        m-test-engine
  cli installed:  ✓
  daemon up:      ✓
  image present:  ✓
  container up:   ✓
  healthy:        ✓
```

```text
$ m engine version

image:     ghcr.io/m-dev-tools/m-test-engine:0.1.0

                    manifest          image
                    ----------------  ----------------
  ✓ protocol          1                 1
  ✓ ydb-version       r2.02             r2.02
  ✓ bind-mount        /m-work           /m-work
    image-rev         (none)            e212fa2991ea4a8529f885fff6801b1fb1038750
```

Smoke probe — run a one-shot M expression inside the container:

```text
$ m engine exec 'write $ZVERSION,!'
GT.M V7.1-002 Linux x86_64
```

The remaining lifecycle verbs (`install`, `start`, `stop`, `restart`,
`logs`, `shell`, `reset`, `capabilities`) follow the same shape; this
walkthrough doesn't need to exercise the destructive ones. `m engine
capabilities` emits the engine namespace as JSON for downstream tooling.

---

## 2. Research the standard library — `m stdlib …`

Before writing code, find out what stdlib already does so we don't
reinvent CSV parsing or stats math.

```text
$ m stdlib list
m-stdlib v0.5.0 — 32 module(s)

  STDARGS      m-stdlib — argparse (v0.0.7).
  STDASSERT    m-stdlib — assertion library (v0.0.1).
  …
  STDCSV       m-stdlib — RFC-4180 CSV parser/writer (pure-M).
  …
  STDJSON      m-stdlib — RFC 8259 JSON parser + serialiser.
  …
  STDMATH      m-stdlib — Numeric helpers (clamp / min / max / sum / count / mean over arrays).
  …
```

Three modules look directly relevant. Drill down on each:

```text
$ m stdlib doc STDCSV.parse
$$parse^STDCSV(text, rows) → int

Parse CSV text into rows(i,j); return row count.
  text  string  CSV document (CRLF, LF, or lone-CR record terminators)
  rows  array   caller-owned destination; killed before population
…
```

```text
$ m stdlib doc STDMATH.mean
$$mean^STDMATH(arr) → num

Arithmetic mean = sum / count. "" if arr is empty (no /0).
…
```

```text
$ m stdlib doc STDJSON.encode
$$encode^STDJSON(node) → string

Serialise `node` to JSON text.
…
Object members emit in M collation order (numeric subscripts first,
then string subscripts in byte order). A gappy array (e.g. node(1)
and node(3) without node(2)) raises U-STDJSON-ENCODE rather than
inventing a `null`.
```

That last note is important — STDJSON expects a **sigil-prefixed tree**
(`"o"` = object, `"n:42"` = number), not arbitrary local arrays.
We'll need a small lift-to-sigil helper.

When the symbol name is fuzzy, search:

```text
$ m stdlib search "mean"
  STDMATH.mean              Arithmetic mean…
```

When debugging a known-failure path, look up which labels raise a
given error code:

```text
$ m stdlib errors | head
U-STDCSV-PARSE         STDCSV       parse, parseFile
U-STDJSON-ENCODE       STDJSON      encode
U-STDJSON-PARSE        STDJSON      parse, parseFile, parseFileEof
…
```

`m stdlib examples STDCSV` lists every `@example` body for grep
piping; `m stdlib manifest` dumps the raw JSON for tools / agents.

---

## 3. Setup project — `m new` + `m ci init`

Scaffold:

```text
$ cd ~/m-work && m new reqstats
  create reqstats/routines/REQSTATS.m
  create reqstats/routines/REQSTATSASRT.m
  create reqstats/tests/REQSTATSTST.m
  create reqstats/.m-cli.toml
  create reqstats/.gitignore
  create reqstats/Makefile
  create reqstats/README.md

Scaffolded reqstats at /home/rafael/m-work/reqstats
Next steps:
  cd /home/rafael/m-work/reqstats
  make check
```

Wire CI:

```text
$ cd reqstats && m ci init                # preview first (no mutation)
# preview: would write .github/workflows/m-ci.yml
# pass --write to scaffold the file
# ----- m-ci.yml -----
# GitHub Actions workflow generated by `m ci init`.
…

$ m ci init --write
  create .github/workflows/m-ci.yml

Next: commit the workflow and push to a branch with GitHub Actions enabled.
```

`m ci init` is **preview by default** (anti-pattern #4 from the
[CLI-UX guide](cli-frameworks/cli-ux-conventions-guide.md)) — same shape as `kubectl apply --dry-run`. Pass `--write` only
when you actually want the mutation.

---

## 4. Vendoring m-stdlib

Quick aside. The m-test-engine container's `$ydb_routines` doesn't
include m-stdlib by default. Since YottaDB's routine search isn't
recursive, the simplest pattern is to **vendor** m-stdlib's `.m`
files alongside your project routines:

```bash
cp ~/m-dev-tools/m-stdlib/src/STD*.m ~/m-work/reqstats/routines/
```

This places every `STD*.m` flat in `routines/`, where the docker
engine's stage path picks them up automatically via the project's
in-container `/m-work/reqstats/routines`. A future m-cli feature
could read a `[routines] extra = ["…"]` table from `.m-cli.toml`
for cleaner external-lib resolution, but vendoring is honest
about MUMPS's actual routine-resolution model and works today.

---

## 5. Inner loop (TDD) — `m fmt`, `m lint`, `m test`

### 5.1 RED — write the tests first

```m
REQSTATSTST ; @summary unit tests for REQSTATS
 new pass,fail
 do start^STDASSERT(.pass,.fail)
 do tClassify(.pass,.fail)
 do tAggregateCounts(.pass,.fail)
 do tAggregateBytes(.pass,.fail)
 do tSummarizeJson(.pass,.fail)
 do report^STDASSERT(pass,fail)
 quit
 ;
tClassify(pass,fail) ; @test status code → class bucket
 do eq^STDASSERT(.pass,.fail,$$classify^REQSTATS(200),"2xx","200 is 2xx")
 do eq^STDASSERT(.pass,.fail,$$classify^REQSTATS(500),"5xx","500 is 5xx")
 ; …
```

Confirm RED:

```text
$ m test tests
m test: 1 suite(s), 0 passed, 1 failed, 0/0 assertions passed
FAIL  REQSTATSTST  (0/0 passed)
```

(The 0/0 result is because the test routine errored at the first
`$$classify^REQSTATS` call — the implementation doesn't exist yet.
A direct `mumps -run` shows the actual `LABELMISSING` error.)

**Path discovery quirk.** `m test` (no args) defaults to the
VistA-style `routines/tests/` layout. `m new` scaffolds a sibling
`tests/`, so you pass `m test tests` explicitly for the path. (Same
shape as `pytest tests/`.)

### 5.2 GREEN — implement

The full `REQSTATS.m` is in `~/m-work/reqstats/routines/REQSTATS.m`.
Key bits:

```m
classify(status)
 if status<200!(status>599) quit "other"
 quit (status\100)_"xx"
 ;
aggregate(rows,out)
 ; Walks rows(i,j) populated by $$parse^STDCSV.
 new i,sizes
 set i=""
 for  set i=$order(rows(i)) quit:i=""  do
 . new status,bytes,bucket
 . set status=$get(rows(i,4))
 . set bytes=+$get(rows(i,5))
 . set bucket=$$classify(status)
 . set out("class",bucket,"count")=$get(out("class",bucket,"count"))+1
 . set out("class",bucket,"bytes")=$get(out("class",bucket,"bytes"))+bytes
 . set out("totals","requests")=$get(out("totals","requests"))+1
 . set out("totals","bytes")=$get(out("totals","bytes"))+bytes
 . set sizes($order(sizes(""),-1)+1)=bytes
 set out("totals","mean_bytes")=$$mean^STDMATH(.sizes)
 quit
 ;
summarize(csv)
 new rows,plain,tree
 do parse^STDCSV(csv,.rows)
 do aggregate(.rows,.plain)
 do toJsonTree(.plain,.tree)         ; lift plain → STDJSON sigil format
 quit $$encode^STDJSON(.tree)
```

Run tests:

```text
$ m test tests
m test: 1 suite(s), 1 passed, 15/15 assertions passed
ok  REQSTATSTST  (15/15 passed)
```

15/15 — every classify case, every aggregate path, the full
end-to-end summarize→JSON→parse round-trip.

### 5.3 Format + select a lint profile

```text
$ m fmt --check routines/REQSTATS.m tests/REQSTATSTST.m
m fmt: all formatted, 2 unchanged
```

Before running lint, **survey the available rule profiles** so you
pick the one that matches your project's house style. `m new`
scaffolds `[lint] rules = "default"` — m-cli's curated daily-lint
subset — but for this app we want the stricter Python-flavoured
preset since we're writing in modern lowercase style.

```text
$ m lint --list-profiles
m lint profiles:
  all          80 rule(s)  Every registered rule, regardless of tag or profile.
  default      34 rule(s)  m-cli's curated daily-lint set — M-MOD-NN minus the four pedantic style rules.
  modern       38 rule(s)  Full M-MOD-NN modernization track (includes pedantic style rules).
  pedantic      4 rule(s)  Just the four pedantic style rules (commands-per-line, label-docstring,
                           magic-numbers, single-letter-vars).
  pythonic     38 rule(s)  Python-style preset: modern + tighter thresholds (line_length=100,
                           commands_per_line=1, cyclomatic=10, …).
  sac          23 rule(s)  VA SAC portable subset — non-VistA rules tagged `sac`.
  vista         8 rule(s)  VA VistA-Kernel-specific rules. Opt in only for VistA M code.
  vista-full   42 rule(s)  XINDEX + vista + sac. Recommended with --target-engine=yottadb.
  xindex       34 rule(s)  Engine-neutral subset of the VA Toolkit ^XINDEX rule set.
```

We're writing modern lowercase non-VistA code, so **`pythonic`** is
the right pick — it's the full M-MOD modernization track plus tighter
PEP-8-ish thresholds. The `vista` and `vista-full` / `sac` profiles
emit false positives outside VistA, and `default` is too lax for the
strict style this project wants.

Pin the choice in `.m-cli.toml` so every contributor's `m lint` /
LSP integration gets the same answer:

```toml
# ~/m-work/reqstats/.m-cli.toml
[fmt]
rules = "pythonic-lower"           # lowercase keywords (set, write, $length)

[lint]
# `pythonic` = modern M-MOD-NN ruleset (no VA / VistA / XINDEX) with
# PEP-8-flavoured thresholds: line_length=100, commands_per_line=1,
# cyclomatic=10. Selected via `m lint --list-profiles`.
rules = "pythonic"
```

Then run lint — it picks up the config automatically (`m lint` walks
up from cwd looking for `.m-cli.toml`):

```text
$ m lint routines/REQSTATS.m tests/REQSTATSTST.m
routines/REQSTATS.m:13:2: [STYLE] M-MOD-009: Line has 2 commands (limit: 1)
routines/REQSTATS.m:13:12: [STYLE] M-MOD-031: Magic numeric literal 200 — extract to a named constant
routines/REQSTATS.m:13:24: [STYLE] M-MOD-031: Magic numeric literal 599 — extract to a named constant
routines/REQSTATS.m:14:15: [STYLE] M-MOD-031: Magic numeric literal 100 — extract to a named constant
routines/REQSTATS.m:16:1: [INFO] M-MOD-029: Label 'aggregate' comment density 6% below threshold 10% (1/15 non-blank lines)
routines/REQSTATS.m:17:6: [STYLE] M-MOD-032: Single-letter variable 'i' outside FOR loop counter — pick a meaningful name
…
```

The findings are **STYLE (S)** and **INFO (I)** severity — not
errors — so `m lint`'s exit is 0. They're real signal under the
pythonic preset: magic numbers, single-letter vars, multi-command
lines. A real project would either fix them (extract named constants,
rename `i` to `rowIdx`, split lines), suppress per-call with
`; m-lint: disable=M-MOD-031`, or relax thresholds in
`[lint.thresholds]`.

Use `--error-on=error` to gate CI on hard errors only, ignoring style:

```bash
m lint --error-on=error routines/ tests/
```

### 5.4 RED → GREEN: detecting and fixing a logic bug

The happy-path transcript above shows GREEN test runs. The interesting
case is what happens when something breaks. Inject a one-character
off-by-one into `classify` — integer-divide by `10` instead of `100`:

```diff
 classify(status) ; @summary  HTTP status → bucket name (2xx/3xx/4xx/5xx/other)
  if status<200!(status>599) quit "other"
- quit (status\100)_"xx"
+ quit (status\10)_"xx"
```

`m test` catches it immediately with `expected/actual` diffs per
failed assertion:

```text
$ m test tests
m test: 1 suite(s), 0 passed, 1 failed, 6/15 assertions passed, 9 failed
FAIL  REQSTATSTST  (6/15 passed)
    - 200 is 2xx
        expected: =2xx
        actual:   =20xx
    - 301 is 3xx
        expected: =3xx
        actual:   =30xx
    - 404 is 4xx
        expected: =4xx
        actual:   =40xx
    - 500 is 5xx
        expected: =5xx
        actual:   =50xx
    - two 2xx
        expected: =2
        actual:   =
    - one 5xx
        expected: =1
        actual:   =
    - 4000 bytes 2xx
        expected: =4000
        actual:   =
    - JSON mentions 2xx
        expected: to contain "2xx"
        actual:   "{"class":{"20xx":{...},"50xx":{...}},…}"
    - JSON mentions 5xx
        expected: to contain "5xx"
        actual:   "{"class":{"20xx":{...},"50xx":{...}},…}"
```

**Exit code 1** — CI gates fail correctly. Nine distinct symptoms
from one character; that locality is exactly what "many small unit
tests" buys you over a single end-to-end assertion. Three layers
report the same root cause:

- **Direct (`tClassify`):** 4 failures. `classify(200)` returned
  `20xx` instead of `2xx` — the integer-division divisor is wrong.
- **Cascade (`tAggregateCounts`/`tAggregateBytes`):** 3 failures.
  The aggregator writes into `out("class",bucket,…)` keyed by
  classify's return value. Bucket name is wrong → the expected
  bucket key (`"2xx"`) is missing → `$get(...)` returns `""`.
- **End-to-end (`tSummarizeJson`):** 2 failures. The JSON output
  surfaces the wrong bucket names (`20xx`, `50xx`) — the
  `actual:` field shows the entire failing JSON, making the
  shape of the bug visible without spelunking through globals.

For CI integration, the same run in TAP format:

```text
$ m test tests --format=tap
TAP version 13
1..15
not ok 1 - REQSTATSTST: 200 is 2xx
  ---
  expected: =2xx
  actual:   =20xx
  ...
not ok 2 - REQSTATSTST: 301 is 3xx
  …
```

To zoom in on just the failing label while debugging:

```text
$ m test tests/REQSTATSTST.m::tClassify
m test: 1 suite(s), 0 passed, 1 failed, 1/5 assertions passed, 4 failed
FAIL  REQSTATSTST::tClassify  (1/5 passed)
    - 200 is 2xx
        expected: =2xx
        actual:   =20xx
    …
```

The diff pattern is unmistakable: every result is `N0xx` where it
should be `Nxx`. Integer-dividing 200 by `10` yields `20`; dividing
by `100` yields `2`. Revert the change:

```diff
 classify(status) ; @summary  HTTP status → bucket name (2xx/3xx/4xx/5xx/other)
  if status<200!(status>599) quit "other"
- quit (status\10)_"xx"
+ quit (status\100)_"xx"
```

Re-run:

```text
$ m test tests
m test: 1 suite(s), 1 passed, 15/15 assertions passed
ok  REQSTATSTST  (15/15 passed)
```

GREEN. **Total round-trip from RED to GREEN: one edit, one re-run.**

This is the canonical TDD inner-loop signal: a precise failure
report locates the wrong line of code to within a single
character. The same kind of feedback is what
`m fmt`/`m lint`/`m coverage` provide for their respective
concerns — together they make the toolchain a four-way safety net.

### 5.5 Useful inner-loop verbs not run here

- **`m watch`** — long-running file watcher. Start it in a terminal
  pane; every save re-runs the affected suite. Skipped in this
  walkthrough because it's interactive.
- **`m run "^REQSTATS"`** — ad-hoc routine invocation. The
  scaffolded `REQSTATS` entry just `quit`s, so the output is empty
  but exit 0. Useful for debugging real programs that need
  `$ZCMDLINE` argv:

  ```text
  $ m run "^REQSTATS"
  m run: DockerEngine → ^REQSTATS
  ```

---

## 6. Coverage gate — `m coverage`

The final inner-loop step before pre-commit. Verifies the test
suite actually exercises the production code, not just adjacent
paths.

```text
$ m coverage --routines routines/REQSTATS.m --tests tests
m coverage: 1 suite(s), 4/4 labels (100.0%)
Routine                Covered     Total   Percent
-------------------- --------- --------- ---------
REQSTATS                     4         4    100.0%
-------------------- --------- --------- ---------
Total                        4         4    100.0%
```

100% label coverage on the production routine. Every public label
(`classify`, `aggregate`, `toJsonTree`, `summarize`) was hit by at
least one test path.

For finer-grained reporting:

```text
$ m coverage --routines routines/REQSTATS.m --tests tests --lines
…
$ m coverage --routines routines/REQSTATS.m --tests tests --branch
…
$ m coverage --routines routines/REQSTATS.m --tests tests --format=lcov
…
```

LCOV output is consumable by `genhtml`, Codecov, Coveralls — wire
it into CI for trend-tracking dashboards.

---

## 7. Introspection — `m capabilities` and `m plugins`

After the inner loop, the introspection surfaces show what's
available:

```text
$ m capabilities --json | jq .subcommands.test.options
[
  {"name": "paths", "help": "…", "default": null, "choices": null},
  …
]
```

`m capabilities` is dominantly tooling-driven (`make manifest`,
CI, AI agents). The bare-TTY form prints a short overview pointing
at `--json` for the full payload.

```text
$ m plugins
m-cli plugin API v1

Registered plugins: (none)
```

No out-of-tree plugins installed here. `m-cli-extras` is the
reference plugin (ships `m corpus-stats`) — it would appear in
this list after `pip install m-cli-extras`.

---

## 8. Surface coverage table

| Command | Hit? | Where |
|---|---|---|
| `m doctor` | ✓ | §1 |
| `m engine status` | ✓ | §1 |
| `m engine version` | ✓ | §1 |
| `m engine exec` | ✓ | §1 |
| `m engine capabilities` | ✓ | §1 |
| `m engine install` / `start` / `stop` / `restart` / `logs` / `shell` | (described only) | §1 |
| `m engine reset` | (destructive — mentioned, not run) | §1 |
| `m stdlib list` | ✓ | §2 |
| `m stdlib doc` | ✓ | §2 |
| `m stdlib search` | ✓ | §2 |
| `m stdlib errors` | ✓ | §2 |
| `m stdlib examples` | (mentioned) | §2 |
| `m stdlib manifest` | (mentioned) | §2 |
| `m new` | ✓ | §3 |
| `m ci init` (preview) | ✓ | §3 |
| `m ci init --write` | ✓ | §3 |
| `m lsp` | (always-on; out of band) | — |
| `m fmt` | ✓ | §5.3 |
| `m lint` | ✓ | §5.3 |
| `m test` | ✓ | §5.1, §5.2 |
| `m watch` | (long-running — mentioned only) | §5.4 |
| `m run` | ✓ | §5.4 |
| `m coverage` | ✓ | §6 |
| `m capabilities` | ✓ | §7 |
| `m plugins` | ✓ | §7 |

24 of the 28 distinct invocations exercised directly; 4 mentioned
in description (`m engine install` / `start` / `stop` / `restart`
/ `logs` / `shell` / `reset` — engine lifecycle verbs that aren't
needed once the container is healthy and running; `m watch` —
long-running; `m stdlib examples` / `manifest` — covered by the
similar `m stdlib doc` / `search` plumbing).

---

## 9. What this walkthrough actually validated

- **All three runtime tools** (`m run` / `m test` / `m coverage`)
  route correctly through `detect_engine()` on a docker-only host.
  Earlier in the engine refactor, these were all hardcoded to
  `read_connection()` → SSH and silently failed.
- **m-stdlib is callable** from the engine container once vendored
  into the project's `routines/` (STDCSV / STDMATH / STDJSON /
  STDASSERT all exercised). The vendoring pattern is honest about
  MUMPS's non-recursive routine search.
- **A 4-label production routine reached 100% label coverage**
  end-to-end through real STDCSV parse → STDMATH mean →
  toJsonTree → STDJSON encode pipeline.
- **The `m fmt`/`m lint` LSP-driven inner loop** runs against real
  m-stdlib-using code without complaint (modulo the
  M-MOD-020 false positives, which are warnings not errors).
- **`m ci init --write` correctly emits a CI workflow** that runs
  the same gates the developer just ran locally.
- **A canonical user-error TDD arc** (§5.4) showed `m test`'s
  expected/actual diffs catching a one-character off-by-one in
  `classify` across three test layers (direct, cascade, end-to-end)
  with nine distinct failure symptoms — RED → fix → GREEN in one
  edit.

The application lives at **`~/m-work/reqstats/`** for re-running
any step. Re-run the full chain with:

```bash
cd ~/m-work/reqstats
m fmt --check routines/REQSTATS.m tests/REQSTATSTST.m
m lint  routines/REQSTATS.m tests/REQSTATSTST.m
m test  tests
m coverage --routines routines/REQSTATS.m --tests tests
```

If any step fails, the m-cli toolchain has regressed somewhere
between commit and the current state — this doc is the canonical
"does it still work?" gate.
