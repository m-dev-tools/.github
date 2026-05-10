.PHONY: validate-ai-tracking validate-catalog

validate-ai-tracking:
	python3 docs/ai-discoverability/scripts/validate-tracking.py
	python3 -m json.tool profile/tools.json >/tmp/m-dev-tools-tools-json-check
	python3 -m json.tool profile/tools.schema.json >/tmp/m-dev-tools-tools-schema-check

validate-catalog:
	python3 -m json.tool profile/tools.json >/tmp/m-dev-tools-tools-json-check
	python3 -m json.tool profile/tools.schema.json >/tmp/m-dev-tools-tools-schema-check
