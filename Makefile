.PHONY: catalog validate-catalog check-catalog check-repo-meta phase0-smoke check-docs-prose recipes-check handshake

# Phase-1 Track B's generator. Fetches each TIER_1+TIER_2+TIER_3 repo's
# dist/repo.meta.json, validates it, translates it into a `tools.<key>`
# summary entry with *_url pointer fields, carries archived entries
# from the prior tools.json, computes consumed_by inverse-edges, and
# writes back to profile/tools.json. Deterministic — running twice
# produces byte-identical output. The drift gate (check-catalog,
# below) regenerates and asserts no diff against the committed file.
catalog:
	python3 profile/build/build-catalog.py --write profile/tools.json

# Phase-1 Track B's validator. Schema-strict (Draft 2020-12) against
# profile/tools.schema.json + profile/task_index.schema.json, plus a
# key-collision guard between the two files' top-level shapes. Replaces
# the prior parse-only target which only ran `python -m json.tool`.
validate-catalog:
	python3 profile/build/validate-catalog.py

# Phase-1 Track D's drift gate. Mirrors each tier-1 repo's
# `make check-manifest`: regenerate the catalog from live manifest
# state, then `git diff --exit-code` against the committed file.
# Used by CI on every push/PR.
check-catalog:
	$(MAKE) catalog
	@git diff --exit-code profile/tools.json profile/task_index.json \
	    || { echo "ERROR: catalog drift — run 'make catalog' and commit." >&2; exit 1; }
	$(MAKE) validate-catalog
	@echo "check-catalog: clean"

# Phase-0 Track A: validate a repo.meta.json file or URL against the org-level
# repo.meta.schema.json contract. Used by tier-1 repos' make check-manifest
# targets and by the meta-repo's phase0-smoke test.
#
#   make check-repo-meta META=profile/repo.meta.example.json
#   make check-repo-meta META=https://.../dist/repo.meta.json
#   make check-repo-meta META=path/to/repo.meta.json ARGS=--no-resolve
check-repo-meta:
	@if [ -z "$(META)" ]; then \
		echo "usage: make check-repo-meta META=<path-or-url> [ARGS=--no-resolve]"; \
		exit 2; \
	fi
	python3 profile/build/validate-repo-meta.py $(META) $(ARGS)

# Phase-0 Track E: the full tier-1 smoke test. Fetches each tier-1 repo's
# dist/repo.meta.json from main, validates it, follows its `exposes`
# pointers, and asserts each payload returns HTTP 200 (and parses as JSON
# for .json targets).
#
#   make phase0-smoke
#   make phase0-smoke URLS="<url1> <url2> <url3>"   # dry-run against feature branches
phase0-smoke:
	@if [ -n "$(URLS)" ]; then \
		python3 profile/build/phase0-smoke.py --urls $(URLS); \
	else \
		python3 profile/build/phase0-smoke.py; \
	fi

# Guardrail: docs/ holds only human-readable prose. Non-prose artifacts
# (generated data, JSON/TSV output, copy-paste examples, scaffolding
# templates) belong under a top-level domain-specific directory — not docs/.
# Same target name as in tier-1 repos so a contributor moving between
# repos finds it predictable.
check-docs-prose:
	@if [ ! -d docs ]; then echo "check-docs-prose: no docs/ directory ✓"; exit 0; fi; \
	violations=$$(find docs -type f \
	    ! -name '*.md' ! -name '*.markdown' \
	    ! -name '*.png' ! -name '*.jpg' ! -name '*.jpeg' \
	    ! -name '*.gif' ! -name '*.svg' ! -name '*.webp' \
	    ! -name '.gitkeep'); \
	if [ -n "$$violations" ]; then \
	  echo "ERROR: non-prose files under docs/ — move to a top-level domain dir:" >&2; \
	  echo "$$violations" >&2; \
	  exit 1; \
	fi; \
	echo "check-docs-prose: docs/ is prose-only ✓"

# Phase-3 Track D: structural gate over every recipe under docs/recipes/.
# Validates frontmatter, presence of a ``## Steps`` bash block, and at
# least one ``must contain: …`` row under ``## Expected output`` — but
# does NOT execute the bash. The full executable run is a maintainer's
# job when bumping ``verified_on`` (the toolchain a recipe drives may
# not be installable in the meta-repo's CI image).
recipes-check:
	@found=0; failed=0; \
	for recipe in docs/recipes/*.md; do \
	  [ "$$(basename $$recipe)" = "README.md" ] && continue; \
	  found=$$((found+1)); \
	  python3 profile/build/run-recipe.py --validate-only $$recipe || failed=$$((failed+1)); \
	done; \
	if [ "$$found" -eq 0 ]; then echo "ERROR: no recipes found under docs/recipes/" >&2; exit 1; fi; \
	if [ "$$failed" -gt 0 ]; then echo "ERROR: $$failed recipe(s) failed --validate-only" >&2; exit 1; fi; \
	echo "recipes-check: $$found recipe(s) clean"

# Phase-3 Track D: the 8-step discovery-protocol handshake test. Drives
# the recipe runner + offline fixture set through the same flow an
# external AI agent would follow (intent → typed-ID → manifest →
# example → recipe). Defaults to --offline (bundled fixtures); the CI
# weekly cron explicitly invokes the script with --live to surface
# upstream URL drift between merges.
handshake:
	python3 profile/build/test-discovery-protocol.py --offline
