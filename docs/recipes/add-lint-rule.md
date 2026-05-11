---
id: recipe:add-lint-rule
title: Ship a new M-MOD or M-XINDX lint rule with fixer linkage
intent: Ship a new M-MOD-* lint rule with fixer linkage and corpus validation
touches:
  - tool:m-cli
  - cmd:m-cli#lint
  - tool:m-modern-corpus
  - tool:tree-sitter-m
verified_on: "2026-05-11"
ci_verifiable: false
manual_checklist_url: https://github.com/m-dev-tools/.github/blob/main/docs/recipes/add-lint-rule.md#manual-checklist
tier: tier-1
notes: "Repo-side recipe for m-cli. Not ci_verifiable because the workflow needs a maintainer-owned m-cli clone and reaches into m-modern-corpus / tree-sitter-m fixtures the runner can't synthesise. The manual checklist below is the gate."
---

# Ship a new M-MOD or M-XINDX lint rule with fixer linkage

## Prerequisites

- A working clone of [`m-cli`](https://github.com/m-dev-tools/m-cli) at
  `~/m-dev-tools/m-cli`.
- Sibling clones of
  [`m-modern-corpus`](https://github.com/m-dev-tools/m-modern-corpus)
  and [`tree-sitter-m`](https://github.com/m-dev-tools/tree-sitter-m)
  in the same parent dir (m-cli's `make lint-modern` / `make vista`
  targets discover them relative to itself).
- Python 3.12 + `uv`. `make install` has run once; `.venv/` exists.
- A rule ID picked from the right track:
  - **`M-MOD-NN`** for greenfield modernization rules (engine- and
    dialect-neutral). Lives in `src/m_cli/lint/_modern.py`.
  - **`M-XINDX-NN`** when porting an XINDEX scanner rule 1:1. Lives
    in `src/m_cli/lint/rules.py`. Use the same numeric N as XINDEX
    so the provenance is grep-able.

## Steps

```bash
# step 1 — enter the m-cli working tree
cd ~/m-dev-tools/m-cli

# step 2 — branch off main
git switch -c add-rule-m-mod-<nn>

# step 3 — TDD red: write the test FIRST. The test asserts the new
#   rule fires on a known-bad fixture and is silent on a known-good
#   one. Add cases to the matching test file in tests/lint/:
$EDITOR tests/lint/test_modern_rules.py

# step 4 — confirm RED (no rule registered yet)
.venv/bin/pytest tests/lint/test_modern_rules.py::test_m_mod_<nn>

# step 5 — implement the rule. Add ONE module-level `register(Rule(...))`
#   block in src/m_cli/lint/_modern.py (M-MOD track) or
#   src/m_cli/lint/rules.py (XINDEX track). The check function takes
#   (src, tree, path, index, ctx) and yields Diagnostic objects. See
#   M-MOD-001 (line-length, _modern.py:152) for the canonical shape.
$EDITOR src/m_cli/lint/_modern.py

# step 6 — green
.venv/bin/pytest tests/lint/test_modern_rules.py::test_m_mod_<nn>

# step 7 — if the rule has an auto-fix, wire fixer_id to the matching
#   m fmt rule (so `--format=json` reports it and the LSP can offer
#   the Quick Fix). Add a row to tests/test_lint_fixer_linkage.py.
$EDITOR src/m_cli/lint/_modern.py tests/test_lint_fixer_linkage.py

# step 8 — full unit + type + coverage gate (matches m-cli's CI)
make check

# step 9 — regenerate dist/lint-rules.json so `m lint --list-rules
#   --json` and every downstream agent (the catalog generator, the
#   LSP, the VS Code extension) sees the new rule
make manifest

# step 10 — drift gate: regenerated dist/*.json must equal the
#   committed copies. Hand-edits to dist/lint-rules.json are erased.
make check-manifest

# step 11 — corpus regression: run the new rule against
#   m-modern-corpus and confirm the false-positive rate is sane (the
#   "default" profile target is ~3 findings/routine; isolated new
#   rules should add far fewer)
make lint-modern

# step 12 — commit + push + PR. squash-merge once review is green.
git add src/m_cli/lint/_modern.py tests/lint/test_modern_rules.py \
        tests/test_lint_fixer_linkage.py dist/lint-rules.json
git commit -m "feat(lint): add M-MOD-<NN> <one-line rule description>"
git push -u origin add-rule-m-mod-<nn>
gh pr create --fill --base main
```

## Expected output

The final line of `pytest tests/lint/test_modern_rules.py::test_m_mod_<nn>` (step 6) must contain: `1 passed`.
The final line of `make check` must contain: `OK`.
The final line of `make check-manifest` must contain: `clean`.
The final line of `make lint-modern` must contain: `findings`.
`gh pr create` must return a `https://github.com/m-dev-tools/m-cli/pull/<N>` URL.

## Failure triage

- **Step 4 (RED) accidentally passes** — your test imports the wrong
  module, or the rule ID collides with an existing one. `grep -rn
  M-MOD-<nn> src/ tests/` to find the collision.
- **Step 6 still fails** — `_modern.py`'s rules consume the
  `NodeIndex` (single-pass AST cache). If the rule needs a node type
  the index doesn't yet bucket, add it there too; don't walk
  `tree.root_node` from the rule body.
- **Step 8 `make check` red on mypy** — Diagnostic / Rule are
  dataclasses with strict types; pass `severity=Severity.X` and
  `category=Category.Y`, not raw strings.
- **Step 10 `make check-manifest` drift** — never hand-edit
  `dist/lint-rules.json`. Re-run `make manifest`; the registry is
  the single source.
- **Step 11 corpus regression** — the new rule false-positives on
  modern code. Tighten the AST predicate, add an inline-disable
  directive scenario test (`; m-lint: disable=M-MOD-<NN>`), or move
  the rule into the `pedantic` profile so it's opt-in only.

See `recipe:investigate-failure` for cross-cutting triage paths.

## Manual checklist

Use this section as both the PR description body (when opening the
PR) and the verification gate (when re-running the recipe to bump
`verified_on`).

- [ ] Rule ID picked from the right track: `M-MOD-NN` (modernization)
      or `M-XINDX-NN` (XINDEX port — same N as XINDEX).
- [ ] Test written first in `tests/lint/` (M-MOD) or
      `tests/test_lint_rules.py` (XINDEX); confirmed RED.
- [ ] Rule registered via a single `register(Rule(...))` block in
      `src/m_cli/lint/_modern.py` or `src/m_cli/lint/rules.py`. One
      block per rule; no shared registrations.
- [ ] `severity` (ERROR / WARNING / STYLE / INFO) and `category`
      (bug / security / concurrency / performance / style /
      complexity / documentation / portability / modernization) both
      declared at registration.
- [ ] If the rule supersedes an XINDEX rule, `Rule.replaces=(...)` is
      set and `tests/test_lint_profiles.py::TestSacClassification`
      passes.
- [ ] If the rule has an auto-fix, `fixer_id` points at a real
      `m fmt` rule and `tests/test_lint_fixer_linkage.py` is updated.
- [ ] `make check` green (lint + mypy + cov).
- [ ] `make manifest` re-run; `make check-manifest` clean;
      `dist/lint-rules.json` carries the new entry.
- [ ] `make lint-modern` over `m-modern-corpus` shows the new rule's
      additions are bounded (no flood). Inline-disable directive
      tested.
- [ ] PR open against `m-dev-tools/m-cli`; squash-merge intended.
- [ ] After merge: catalog regen on `.github` (`make catalog`) picks
      up the new rule via `m-cli`'s `lint_rules_url` pointer.
