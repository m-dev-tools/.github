.PHONY: validate-ai-tracking validate-catalog check-repo-meta

validate-ai-tracking:
	python3 docs/ai-discoverability/scripts/validate-tracking.py
	python3 -m json.tool profile/tools.json >/tmp/m-dev-tools-tools-json-check
	python3 -m json.tool profile/tools.schema.json >/tmp/m-dev-tools-tools-schema-check

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
