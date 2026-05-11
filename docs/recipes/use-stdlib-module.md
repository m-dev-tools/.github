---
id: recipe:use-stdlib-module
title: Look up an m-stdlib symbol and call it correctly from M code
intent: Look up an m-stdlib symbol (signature + example) and call it correctly
touches:
  - cmd:m-cli#doc
  - cmd:m-cli#search
  - cmd:m-cli#examples
  - module:m-stdlib#STDJSON
  - module:m-stdlib#STDASSERT
  - cmd:m-cli#test
prereqs:
  - recipe:new-app-tdd-ci
verified_on: "2026-05-11"
ci_verifiable: true
tier: tier-1
notes: "Worked example: parse JSON via parse^STDJSON, assert the tree via ^STDASSERT, gate with m test. Demonstrates the lookup path: m search → m doc → m examples → copy a tested call."
---

# Look up an m-stdlib symbol and call it correctly from M code

## Prerequisites

- `recipe:new-app-tdd-ci` has run successfully on this machine; in
  particular `m doctor` is green.
- `m-stdlib`'s manifest (`dist/stdlib-manifest.json`) is reachable —
  bundled with the m-cli install. `m doc STDJSON` proves resolution.
- The recipe runs from a fresh `mktemp -d`; it builds a throwaway
  project named `parser-demo`, drops in a 10-line routine, then runs
  `m test` against it.

## Steps

```bash
# step 1 — scaffold the project we will demo against
m new parser-demo
cd parser-demo

# step 2 — find STDJSON via keyword search (agent flow: "I want JSON")
m search json

# step 3 — read parse^STDJSON's signature + parameters + raises
m doc parse^STDJSON

# step 4 — print the bundled, tested examples for parse^STDJSON
m examples parse^STDJSON

# step 5 — drop in a 10-line routine that parses a JSON array and
#   asserts the third element is the string "3". STDASSERT's pass/fail
#   counters get reported at the end of the routine; `m test` flunks
#   the suite if any fail counter is non-zero.
cat > routines/PARSEDEMO.m <<'EOF'
PARSEDEMO ; @summary  parse^STDJSON worked example
        quit
tParseArray(pass,fail) ; @test
        new rc,tree
        set rc=$$parse^STDJSON("[1,2,""3""]",.tree)
        do eq^STDASSERT(.pass,.fail,rc,1,"parse returns 1 on success")
        do eq^STDASSERT(.pass,.fail,tree(3),"s:3","third element is the string \"3\"")
        quit
EOF

# step 6 — wire it into the test discoverer as PARSEDEMOTST.m so
#   `m test` picks it up under the standard *TST.m convention
cat > tests/PARSEDEMOTST.m <<'EOF'
PARSEDEMOTST ; @summary  PARSEDEMO test suite
        new pass,fail
        do start^STDASSERT(.pass,.fail)
        do tParseArray^PARSEDEMO(.pass,.fail)
        do report^STDASSERT(pass,fail)
        quit
EOF

# step 7 — green run proves the worked example calls parse^STDJSON
#   correctly and the storage convention ("s:VALUE" for strings) is
#   what the manifest documented.
m test
```

## Expected output

The final line of `m search json` must contain: `STDJSON`.
The final line of `m doc parse^STDJSON` must contain: `parse`.
The final line of `m examples parse^STDJSON` must contain: `parse^STDJSON`.
The final line of `m test` must contain: `0/0 failed`.

## Failure triage

- **`m search json` returns nothing** — m-stdlib manifest didn't load.
  `m doctor` will flag the missing path; reinstall or set
  `M_STDLIB_MANIFEST` to the local checkout's
  `dist/stdlib-manifest.json`.
- **`m doc parse^STDJSON` errors** — same root cause; the manifest
  lookup table is the single source.
- **`m test` fails the assertion** — confirm the storage convention
  is current. `parse^STDJSON` stores a string element as `"s:VALUE"`
  (one M tree node per JSON value, prefix `s:` for string). If
  STDJSON's encoding has changed, regenerate this recipe and bump
  `verified_on`.

See `recipe:investigate-failure` for the broader triage tree.
