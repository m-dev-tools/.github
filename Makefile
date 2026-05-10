.PHONY: validate-catalog check-repo-meta phase0-smoke

validate-catalog:
	python3 -m json.tool profile/tools.json >/tmp/m-dev-tools-tools-json-check
	python3 -m json.tool profile/tools.schema.json >/tmp/m-dev-tools-tools-schema-check

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
