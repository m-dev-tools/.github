# Phase 1 — Exit evidence

**Captured:** 2026-05-11T03:27:21Z (P1-D landing).

Per [`phase1-plan.md` §5 D4](phase1-plan.md): a clean run of `make catalog`
+ `make validate-catalog` + the catalog-builder test suite is the
documented exit gate.

## `make catalog` — idempotent

Running `python3 profile/build/build-catalog.py --write profile/tools.json`
twice in a row produces byte-identical output:

```
byte-identical ✓
```

## `make validate-catalog` — schema-strict

```
OK: /home/rafael/m-dev-tools/.github/profile/tools.json + /home/rafael/m-dev-tools/.github/profile/task_index.json
```

## `pytest profile/build/` — 26 / 26

```
..........................                                               [100%]
26 passed in 0.18s
```

Coverage: 22 cases from P1-B (build-catalog + validate-catalog TDD) +
4 cases from P1-D (consumed_by inverse-edge computation, sorted +
deduplicated, archived-entry carryover, non-archived entries NOT
carried).

## What this proves

1. The catalog can be regenerated from live tier-1 + tier-2 + tier-3
   manifest state without drift against the committed `profile/tools.json`
   — the drift gate `make check-catalog` would pass.
2. The committed catalog validates against the post-P1-A strict
   `tools.schema.json` (and `task_index.json` against
   `task_index.schema.json`).
3. The generator is byte-deterministic — the CI drift gate produces
   a reliable signal (no false positives from non-determinism).
4. Both new P1-D behaviors (`consumed_by` computation, archived
   carryover) have pinned regression tests.

## Phase 1 closed

All ten [`phase1-plan.md` §9 "Done — Definition"](phase1-plan.md)
criteria met by the combined P1-A + P1-B + P1-C + P1-D landings.
