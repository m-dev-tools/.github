---
id: recipe:add-stdlib-module
title: Add a new STD* module to m-stdlib (TDD, manifest, PR)
intent: Author a new STD* module in m-stdlib with TDD; regenerate the manifest
touches:
  - tool:m-stdlib
  - module:m-stdlib#STDASSERT
  - cmd:m-cli#test
  - cmd:m-cli#coverage
verified_on: "2026-05-11"
ci_verifiable: false
manual_checklist_url: https://github.com/m-dev-tools/.github/blob/main/docs/recipes/add-stdlib-module.md#manual-checklist
tier: tier-1
notes: "Repo-side recipe. Not ci_verifiable because it needs a maintainer-owned m-stdlib clone and a real PR — the recipe runner can't fabricate either. The manual checklist below is the gate; bump verified_on when a maintainer walks it end-to-end."
---

# Add a new STD* module to m-stdlib (TDD, manifest, PR)

## Prerequisites

- A working clone of [`m-stdlib`](https://github.com/m-dev-tools/m-stdlib)
  at `~/m-dev-tools/m-stdlib` (or wherever your dev tree lives).
- `m-cli` on `$PATH`; `m doctor` green.
- Write access (or a fork + branch) on `m-stdlib`.
- A proposed module name `STD<NAME>` — see m-stdlib's CLAUDE.md for the
  naming and scope rules (m-stdlib has architectural priority over
  consumer projects; if the primitive is missing here, this is the
  right place to add it).
- An issue on m-stdlib proposing the module so maintainers can sanity-
  check scope before the PR lands. Use the manual-checklist section at
  the bottom of this recipe as the issue body.

## Steps

```bash
# step 1 — enter the m-stdlib working tree (NOT a mktemp; this is a
#   repo-side recipe and the PR is the deliverable)
cd ~/m-dev-tools/m-stdlib

# step 2 — branch off main
git switch -c add-std<name>

# step 3 — TDD red: write tests/STD<NAME>TST.m FIRST. The suite must
#   call into the not-yet-existing STD<NAME> module via ^STDASSERT.
#   Skeleton (replace <NAME> and tFoo with the real entry points):
cat > tests/STD<NAME>TST.m <<'EOF'
STD<NAME>TST ; @summary  STD<NAME> test suite
        new pass,fail
        do start^STDASSERT(.pass,.fail)
        do tFoo^STD<NAME>TST(.pass,.fail)
        do report^STDASSERT(pass,fail)
        quit
tFoo(pass,fail) ; @test
        ; arrange / act / assert — see existing STD*TST.m files for shape
        do eq^STDASSERT(.pass,.fail,$$something^STD<NAME>("input"),"expected","sanity")
        quit
EOF

# step 4 — confirm RED (the module doesn't exist yet — m test must
#   fail with a "no such routine" style error from ydb)
m test tests/STD<NAME>TST.m

# step 5 — implement src/STD<NAME>.m matching the test surface.
#   Follow the storage / error-code / public-API conventions documented
#   in any neighbour module (STDJSON / STDREGEX / STDLOG are good shape
#   exemplars). Public labels need m-doc tags (M-DOC-001 enforces).
$EDITOR src/STD<NAME>.m

# step 6 — green
m test tests/STD<NAME>TST.m

# step 7 — coverage gate (per global CLAUDE.md: 85% per module unless
#   the module's CLAUDE.md says otherwise)
m coverage --min-percent=85 src/STD<NAME>.m

# step 8 — formatter + linter must be clean before the manifest gate
m fmt --check src/STD<NAME>.m tests/STD<NAME>TST.m
m lint --error-on=error src/STD<NAME>.m tests/STD<NAME>TST.m

# step 9 — regenerate dist/repo.meta.json + dist/stdlib-manifest.json
#   so the new module surfaces in `m doc` / `m search` / `m examples`
#   for every downstream agent
make manifest

# step 10 — drift gate: the regenerated manifests must equal the
#   committed ones (so the PR has no hidden manifest churn beyond the
#   STD<NAME> additions)
make check-manifest

# step 11 — full repo gate, same target m-stdlib's CI runs
make check

# step 12 — commit + push + PR. squash-merge once review is green.
git add src/STD<NAME>.m tests/STD<NAME>TST.m dist/
git commit -m "feat(STD<NAME>): add STD<NAME> module + tests + manifest"
git push -u origin add-std<name>
gh pr create --fill --base main
```

## Expected output

The final line of `m test tests/STD<NAME>TST.m` (step 6) must contain: `0/0 failed`.
The final line of `m coverage --min-percent=85 src/STD<NAME>.m` must contain: `pass`.
The final line of `m fmt --check` must contain: `clean`.
The final line of `m lint --error-on=error` must contain: `0 errors`.
The final line of `make check-manifest` must contain: `clean`.
The final line of `make check` must contain: `OK`.
`gh pr create` must return a `https://github.com/m-dev-tools/m-stdlib/pull/<N>` URL.

## Failure triage

- **Step 4 (RED) accidentally passes** — your test file is wired into
  the wrong routine, or `STD<NAME>` already exists. Rename and retry.
- **Step 6 still fails after implementation** — re-read the manifest
  example for a neighbour module; signature mismatch (pass-by-reference
  vs by-value) is the most common cause.
- **`make manifest` drift after step 9** — never hand-edit
  `dist/*.json`. Re-run `make manifest`; the autogenerator is the
  single source.
- **`make check-manifest` red** — the regenerator picked up an unstaged
  source change. `git status dist/` and either commit or revert.

See `recipe:investigate-failure` for cross-cutting triage paths.

## Manual checklist

Use this section as both the issue body (when proposing the module)
and the verification gate (when re-running the recipe to bump
`verified_on`). Every item must be true on a fresh clone of m-stdlib's
`main` before this recipe is considered verified.

- [ ] Module name follows the `STD<NAME>` convention; `<NAME>` is
      uppercase, 3-6 chars, not already taken.
- [ ] Module scope justified — primitive isn't already covered by a
      neighbour module (`m search <keyword>` returns no near match).
- [ ] `tests/STD<NAME>TST.m` written first; confirmed RED before any
      `src/STD<NAME>.m` byte was typed.
- [ ] `m test tests/STD<NAME>TST.m` green; `m coverage --min-percent=85
      src/STD<NAME>.m` green.
- [ ] `m fmt --check` clean; `m lint --error-on=error` zero errors.
- [ ] `make manifest` re-run; `make check-manifest` clean; both
      `dist/stdlib-manifest.json` and `dist/repo.meta.json` updated.
- [ ] Public labels carry M-doc tags (`@summary`, parameters, raises);
      `m doc <label>^STD<NAME>` returns the documented surface.
- [ ] `make check` green (the full local CI gate).
- [ ] PR open against `m-dev-tools/m-stdlib`; squash-merge intended.
- [ ] After merge: `m search <NAME>` finds the new module from any
      downstream project. (Confirms the manifest propagated.)
