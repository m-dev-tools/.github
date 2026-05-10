#!/usr/bin/env python3
"""Validate a repo.meta.json file against repo.meta.schema.json.

Two stages:

1. Schema validation. Uses `jsonschema` (draft 2020-12) if installed,
   else falls back to a minimal inline check covering the schema's required
   fields and patterns. The inline path is deliberately conservative — it
   catches the common errors (missing fields, bad ID format, bad date) but
   defers full draft-2020-12 semantics to `jsonschema` when available.

2. Exposes resolution (default on; disable with --no-resolve). For each
   key in `exposes`, fetch the value as a path **relative to the repo
   root** (found by walking up from the manifest to a `.git` ancestor;
   falls back to the manifest's directory if no `.git` is found, which
   handles unit tests against fixtures outside a repo). For URL mode,
   the base is the raw-content prefix up to and including the branch
   (`https://raw.githubusercontent.com/<org>/<repo>/<branch>/`). If the
   resolved resource ends in `.json`, assert it parses. Otherwise
   (`.tsv` etc.) just assert it exists / returns HTTP 200.

Usage:
    validate-repo-meta.py <path-or-url> [--no-resolve]

Exits 0 on success, non-zero with one error per line on failure.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "repo.meta.schema.json"

REQUIRED_FIELDS = [
    "id",
    "repo",
    "role",
    "language",
    "license",
    "agent_instructions",
    "verified_on",
    "exposes",
    "verification_commands",
]

ID_RE = re.compile(r"^tool:[a-z0-9_-]+$")
DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
URL_RE = re.compile(r"^https?://")
ALLOWED_TOP = {
    "$schema",
    "id",
    "repo",
    "role",
    "language",
    "license",
    "agent_instructions",
    "verified_on",
    "exposes",
    "consumes",
    "verification_commands",
    "status",
    "notes",
}
ALLOWED_STATUS = {"active", "archived", "deprecated"}


RAW_GITHUB_RE = re.compile(
    r"^(https?://raw\.githubusercontent\.com/[^/]+/[^/]+/[^/]+/)"
)


def _find_repo_root(start: Path) -> Path:
    """Walk up from `start` looking for a `.git` directory or file.

    Returns the first ancestor that contains `.git`. Falls back to
    `start` if none found (handles validation against fixtures outside
    a git repo, e.g. the canonical example.json).
    """
    for ancestor in [start, *start.parents]:
        if (ancestor / ".git").exists():
            return ancestor
    return start


def _url_repo_base(target: str) -> str:
    """For a GitHub raw URL, return the prefix up to and including the
    branch (i.e. the repo-root equivalent). For any other URL, fall
    back to stripping the last path component.
    """
    m = RAW_GITHUB_RE.match(target)
    if m:
        return m.group(1)
    return target.rsplit("/", 1)[0] + "/"


def load(target: str) -> tuple[dict, str]:
    """Return (parsed json, base for resolving relative exposes paths).

    The base is the repo-root equivalent — for path mode, the nearest
    .git ancestor; for URL mode, the raw-content prefix up to the
    branch. Trailing slash is always present so naive string
    concatenation works.
    """
    if URL_RE.match(target):
        with urllib.request.urlopen(target, timeout=15) as resp:
            data = resp.read().decode("utf-8")
        return json.loads(data), _url_repo_base(target)
    path = Path(target).resolve()
    root = _find_repo_root(path.parent)
    return json.loads(path.read_text(encoding="utf-8")), str(root) + "/"


def _inline_validate(data: dict, errors: list[str]) -> None:
    """Conservative inline check used when jsonschema is unavailable."""
    if not isinstance(data, dict):
        errors.append("top-level value is not an object")
        return
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing required field: {field}")
    for key in data:
        if key not in ALLOWED_TOP:
            errors.append(f"unexpected top-level field: {key}")
    if "id" in data and not ID_RE.match(str(data["id"])):
        errors.append(f"id does not match ^tool:[a-z0-9_-]+$: {data['id']}")
    if "verified_on" in data and not DATE_RE.match(str(data["verified_on"])):
        errors.append(f"verified_on is not YYYY-MM-DD: {data['verified_on']}")
    if "language" in data:
        lang = data["language"]
        if not isinstance(lang, list) or not lang or not all(isinstance(x, str) for x in lang):
            errors.append("language must be a non-empty array of strings")
    if "exposes" in data:
        exp = data["exposes"]
        if not isinstance(exp, dict) or not exp:
            errors.append("exposes must be a non-empty object")
        else:
            for k, v in exp.items():
                if not isinstance(v, str) or not v:
                    errors.append(f"exposes[{k}] must be a non-empty string")
    if "verification_commands" in data:
        vc = data["verification_commands"]
        if not isinstance(vc, list) or not vc or not all(isinstance(x, str) and x for x in vc):
            errors.append("verification_commands must be a non-empty array of non-empty strings")
    if "consumes" in data:
        cs = data["consumes"]
        if not isinstance(cs, list) or not all(isinstance(x, str) and ID_RE.match(x) for x in cs):
            errors.append("consumes must be an array of typed IDs (tool:...)")
    if "status" in data and data["status"] not in ALLOWED_STATUS:
        errors.append(f"status must be one of {sorted(ALLOWED_STATUS)}: {data['status']}")


def validate_schema(data: dict, errors: list[str]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    try:
        import jsonschema  # type: ignore[import-not-found]
    except ImportError:
        _inline_validate(data, errors)
        return
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as exc:
        path = "/".join(str(p) for p in exc.absolute_path) or "<root>"
        errors.append(f"schema: at {path}: {exc.message}")


def resolve_one(base: str, value: str, errors: list[str], label: str) -> None:
    if URL_RE.match(value):
        target = value
    elif URL_RE.match(base):
        target = base + value
    else:
        local = Path(base) / value
        if not local.exists():
            errors.append(f"exposes[{label}]: {local} does not exist")
            return
        if value.endswith(".json"):
            try:
                json.loads(local.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"exposes[{label}]: {local} is invalid JSON: {exc}")
        return
    try:
        with urllib.request.urlopen(target, timeout=15) as resp:
            body = resp.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as exc:
        errors.append(f"exposes[{label}]: cannot fetch {target}: {exc}")
        return
    if target.endswith(".json"):
        try:
            json.loads(body)
        except json.JSONDecodeError as exc:
            errors.append(f"exposes[{label}]: {target} is invalid JSON: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    parser.add_argument("target", help="Path or URL of repo.meta.json")
    parser.add_argument(
        "--no-resolve",
        action="store_true",
        help="Skip resolving exposes payloads (validate schema only).",
    )
    args = parser.parse_args()

    errors: list[str] = []
    try:
        data, base = load(args.target)
    except (OSError, json.JSONDecodeError, urllib.error.URLError) as exc:
        print(f"ERROR: cannot load {args.target}: {exc}", file=sys.stderr)
        return 1

    validate_schema(data, errors)

    if not args.no_resolve and "exposes" in data and isinstance(data["exposes"], dict):
        for key, value in data["exposes"].items():
            if isinstance(value, str):
                resolve_one(base, value, errors, key)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {args.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
