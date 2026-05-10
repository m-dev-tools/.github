#!/usr/bin/env python3
"""Phase 0 smoke test — fetch each tier-1 repo.meta.json and follow its
`exposes` pointers.

For each URL in TIER_1:
  1. Fetch the repo.meta.json. Assert HTTP 200.
  2. Validate it against repo.meta.schema.json.
  3. For each `exposes.*` value: fetch as a URL constructed relative
     to the manifest's location. Assert HTTP 200. If the URL ends in
     `.json`, parse it. Otherwise (`.tsv`, etc.) accept HTTP 200 in
     Phase 0 — per-kind schemas land in Phase 1.
  4. Assert `verified_on` is within 90 days of today.

Path-resolution model: each `exposes.*` value is resolved RELATIVE TO
THE REPO ROOT (the directory the manifest's containing repo would
unpack into). Concretely: the manifest is expected to live at
`<repo-root>/dist/repo.meta.json`, so the repo root is two URL path
segments above the manifest URL. The plan's B3 example body and the
schema's own description both stipulate repo-root-relative paths.

Override the production URL list with --urls for testing against
feature-branch raw URLs before merges happen:

    phase0-smoke.py \
        --urls https://raw.githubusercontent.com/m-dev-tools/m-stdlib/phase0-B-repo-meta/dist/repo.meta.json \
               https://raw.githubusercontent.com/m-dev-tools/m-standard/phase0-c-repo-meta/dist/repo.meta.json \
               https://raw.githubusercontent.com/m-dev-tools/m-cli/phase0-D/dist/repo.meta.json

Exits 0 only when every step for every URL succeeds.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "repo.meta.schema.json"

# Reuse validate-repo-meta.py's validation logic so the smoke test
# gracefully degrades to the inline conservative check when jsonschema
# isn't installed (matching the single-manifest validator's behavior).
_validator_path = Path(__file__).with_name("validate-repo-meta.py")
_spec = importlib.util.spec_from_file_location("_validate_repo_meta", _validator_path)
_validate_repo_meta = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_validate_repo_meta)

TIER_1 = [
    "https://raw.githubusercontent.com/m-dev-tools/m-stdlib/main/dist/repo.meta.json",
    "https://raw.githubusercontent.com/m-dev-tools/m-standard/main/dist/repo.meta.json",
    "https://raw.githubusercontent.com/m-dev-tools/m-cli/main/dist/repo.meta.json",
]

VERIFIED_ON_GRACE_DAYS = 90

URL_RE = re.compile(r"^https?://")


def fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=20) as resp:
        return resp.read().decode("utf-8")


def repo_root_from_manifest_url(url: str) -> str:
    """Given the manifest URL ending in `/dist/repo.meta.json`, return the
    repo-root URL (with trailing slash) so relative paths join cleanly.
    """
    suffix = "/dist/repo.meta.json"
    if not url.endswith(suffix):
        # Fall back to one-level-up resolution.
        return url.rsplit("/", 1)[0] + "/"
    return url[: -len(suffix)] + "/"


def resolve_one(repo_root: str, value: str) -> str:
    if URL_RE.match(value):
        return value
    return repo_root + value.lstrip("/")


def validate_schema(data: dict, schema: dict, errors: list[str]) -> None:
    # Delegate to the single-manifest validator so the inline-fallback
    # behavior stays in one place. validate_schema mutates `errors`.
    _validate_repo_meta.validate_schema(data, errors)


def check_verified_on(value: str, errors: list[str]) -> None:
    try:
        when = dt.date.fromisoformat(value)
    except ValueError:
        errors.append(f"verified_on is not a valid ISO date: {value!r}")
        return
    age = (dt.date.today() - when).days
    if age > VERIFIED_ON_GRACE_DAYS:
        errors.append(
            f"verified_on is {age} days old (> {VERIFIED_ON_GRACE_DAYS}d) — "
            "regenerate the manifest and bump the date."
        )
    elif age < 0:
        errors.append(f"verified_on is in the future: {value}")


def smoke_one(url: str, schema: dict | None) -> tuple[bool, list[str], list[str]]:
    errors: list[str] = []
    trail: list[str] = []
    trail.append(f"  manifest: {url}")
    try:
        body = fetch(url)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        errors.append(f"cannot fetch manifest {url}: {exc}")
        return False, trail, errors
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        errors.append(f"manifest is invalid JSON: {exc}")
        return False, trail, errors

    validate_schema(data, schema, errors)
    if errors:
        return False, trail, errors

    if "verified_on" in data:
        check_verified_on(data["verified_on"], errors)

    repo_root = repo_root_from_manifest_url(url)
    exposes = data.get("exposes", {})
    for label, value in exposes.items():
        target = resolve_one(repo_root, value)
        trail.append(f"  exposes[{label}]: {target}")
        try:
            payload = fetch(target)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            errors.append(f"exposes[{label}]: cannot fetch {target}: {exc}")
            continue
        if target.endswith(".json"):
            try:
                json.loads(payload)
            except json.JSONDecodeError as exc:
                errors.append(f"exposes[{label}]: {target} is invalid JSON: {exc}")

    return not errors, trail, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    parser.add_argument(
        "--urls",
        nargs="+",
        help="Override the TIER_1 production URL list (e.g. feature-branch raw URLs).",
    )
    args = parser.parse_args()

    urls = args.urls if args.urls else TIER_1

    print(f"phase0-smoke: checking {len(urls)} tier-1 manifest(s)")
    all_ok = True
    for url in urls:
        ok, trail, errors = smoke_one(url, None)
        status = "OK" if ok else "FAIL"
        print(f"{status}  {url}")
        for line in trail[1:]:  # skip the manifest line, already shown above
            print(line)
        for err in errors:
            print(f"  ERROR: {err}", file=sys.stderr)
        all_ok = all_ok and ok

    summary = "PASS" if all_ok else "FAIL"
    print(f"\nphase0-smoke: {summary}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
