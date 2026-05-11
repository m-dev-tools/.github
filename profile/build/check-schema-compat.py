#!/usr/bin/env python3
"""Phase 5 Track D — schema-version policing gate.

Diffs ``profile/tools.schema.json`` + ``profile/task_index.schema.json``
between a base ref (default ``origin/main``) and a head ref (default
``HEAD``). Enforces:

* If ``schema_compat`` bumps in either schema, ``schema-changelog.md``
  must be modified in the same diff. Otherwise:
  ``MISSING_CHANGELOG_ROW``.
* If a non-additive change happens *without* a ``schema_compat`` bump,
  surface ``NON_ADDITIVE_WITHOUT_BUMP``. The heuristic catches three
  common breakage shapes:

    1. A required field is removed (consumer still producing it now
       fails ``additionalProperties: false``).
    2. An enum value disappears (consumer producing the removed value
       now rejects).
    3. ``additionalProperties`` tightens from ``true`` (or unset) to
       ``false`` (extras previously accepted now reject).

  False positives are acceptable per phase5-plan.md §9: the maintainer
  can bump ``schema_compat`` + add a changelog row.

Exit codes:

* ``0`` — pass.
* ``1`` — gate failed (one of the codes above).
* ``2`` — fixture / git error.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE_REL = "profile"
SCHEMA_FILES = (
    "tools.schema.json",
    "task_index.schema.json",
)
CHANGELOG_REL = "profile/schema-changelog.md"


# ---- pure-function analyzer ----------------------------------------------


def _check_required_shrunk(base: dict, head: dict, details: list[str]) -> bool:
    """Return True if any required field present in base disappeared in head."""
    base_req = set(base.get("required", []) or [])
    head_req = set(head.get("required", []) or [])
    removed = base_req - head_req
    if removed:
        for field in sorted(removed):
            details.append(
                f"required field {field!r} removed (consumers producing it "
                f"may now fail validation)"
            )
        return True
    return False


def _check_enums_shrunk(base: dict, head: dict, details: list[str]) -> bool:
    """Walk the ``properties`` of both schemas; if any property's enum
    list shrunk, that's a breaking change."""
    base_props = base.get("properties", {}) or {}
    head_props = head.get("properties", {}) or {}
    broke = False
    for prop_name, base_prop in base_props.items():
        if not isinstance(base_prop, dict):
            continue
        base_enum = base_prop.get("enum")
        if not isinstance(base_enum, list):
            continue
        head_prop = head_props.get(prop_name)
        if not isinstance(head_prop, dict):
            continue
        head_enum = head_prop.get("enum")
        if not isinstance(head_enum, list):
            continue
        removed = set(base_enum) - set(head_enum)
        if removed:
            for val in sorted(map(str, removed)):
                details.append(
                    f"enum value {val!r} removed from {prop_name}.enum "
                    f"(consumers producing it now reject)"
                )
            broke = True
    return broke


def _check_additional_properties_tightened(
    base: dict, head: dict, details: list[str]
) -> bool:
    base_ap = base.get("additionalProperties", True)
    head_ap = head.get("additionalProperties", True)
    # `True` (or unset) → `False` is the breaking direction. Going the
    # other way (False → True) is loosening; not a regression.
    if base_ap is True and head_ap is False:
        details.append(
            "additionalProperties tightened from true to false at the "
            "top level (extras previously accepted now reject)"
        )
        return True
    # Dict-form (a sub-schema) → False is also tightening. We treat any
    # non-False base + False head as tightening.
    if base_ap is not False and head_ap is False:
        details.append(
            "additionalProperties tightened to false (extras previously "
            "accepted now reject)"
        )
        return True
    return False


def _is_non_additive(base: dict, head: dict, details: list[str]) -> bool:
    """Apply the three heuristics; True if any fired."""
    found = False
    if _check_required_shrunk(base, head, details):
        found = True
    if _check_enums_shrunk(base, head, details):
        found = True
    if _check_additional_properties_tightened(base, head, details):
        found = True
    return found


def check_schema_compat_impl(
    *,
    pairs: list[tuple[str, dict, dict]],
    changelog_modified: bool,
) -> dict[str, Any]:
    """Pure-function analyzer.

    ``pairs``: list of ``(filename, base_dict, head_dict)`` tuples.
    ``changelog_modified``: did ``schema-changelog.md`` appear in the
    PR's file diff?

    Returns:
        ``{"status": "OK" | "MISSING_CHANGELOG_ROW" | "NON_ADDITIVE_WITHOUT_BUMP",
           "bumped_files": [str],
           "non_additive_files": [str],
           "details": [str]}``
    """
    bumped_files: list[str] = []
    non_additive_files: list[str] = []
    details: list[str] = []

    for name, base, head in pairs:
        base_compat = base.get("schema_compat")
        head_compat = head.get("schema_compat")
        if (
            isinstance(base_compat, int)
            and isinstance(head_compat, int)
            and head_compat > base_compat
        ):
            bumped_files.append(name)
            details.append(
                f"{name}: schema_compat {base_compat} → {head_compat}"
            )

        non_additive_details: list[str] = []
        if _is_non_additive(base, head, non_additive_details):
            non_additive_files.append(name)
            for d in non_additive_details:
                details.append(f"{name}: {d}")

    if bumped_files and not changelog_modified:
        return {
            "status": "MISSING_CHANGELOG_ROW",
            "bumped_files": bumped_files,
            "non_additive_files": non_additive_files,
            "details": details,
        }

    if non_additive_files and not bumped_files:
        return {
            "status": "NON_ADDITIVE_WITHOUT_BUMP",
            "bumped_files": bumped_files,
            "non_additive_files": non_additive_files,
            "details": details,
        }

    return {
        "status": "OK",
        "bumped_files": bumped_files,
        "non_additive_files": non_additive_files,
        "details": details,
    }


# ---- git wrapper ----------------------------------------------------------


def _git_show(repo: Path, ref: str, path: str) -> str | None:
    """Return file contents at ``ref:path``, or None if the file
    doesn't exist at that ref (e.g. it's brand-new in HEAD)."""
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def _git_files_changed(repo: Path, base: str, head: str) -> set[str]:
    """Return the set of paths changed between ``base`` and ``head``."""
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}", f"{head}"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _load_pair(repo: Path, base: str, head: str, relpath: str) -> tuple[dict, dict] | None:
    """Load ``relpath`` at both refs as JSON. Returns ``None`` if the
    file doesn't exist at either ref."""
    base_text = _git_show(repo, base, relpath)
    head_text = _git_show(repo, head, relpath)
    if base_text is None or head_text is None:
        return None
    try:
        base_d = json.loads(base_text)
        head_d = json.loads(head_text)
    except json.JSONDecodeError:
        return None
    return base_d, head_d


# ---- CLI -------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0] if __doc__ else "",
    )
    parser.add_argument(
        "--base",
        default="origin/main",
        help="Base ref to diff from (default: origin/main).",
    )
    parser.add_argument(
        "--head",
        default="HEAD",
        help="Head ref to diff to (default: HEAD).",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=REPO_ROOT,
        help="Path to the git repo (default: this repo's root).",
    )
    args = parser.parse_args(argv)

    pairs: list[tuple[str, dict, dict]] = []
    for name in SCHEMA_FILES:
        relpath = f"{PROFILE_REL}/{name}"
        loaded = _load_pair(args.repo, args.base, args.head, relpath)
        if loaded is None:
            continue
        base_d, head_d = loaded
        pairs.append((name, base_d, head_d))

    try:
        changed = _git_files_changed(args.repo, args.base, args.head)
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: git diff failed: {exc}", file=sys.stderr)
        return 2

    changelog_modified = CHANGELOG_REL in changed

    result = check_schema_compat_impl(
        pairs=pairs, changelog_modified=changelog_modified
    )

    # Markdown summary on stdout (CI-friendly).
    print("### Schema-version policing")
    print()
    print(f"* base: `{args.base}`")
    print(f"* head: `{args.head}`")
    print(f"* schemas inspected: {[name for name, _, _ in pairs]}")
    print(f"* schema-changelog.md modified: {changelog_modified}")
    print(f"* bumped: {result['bumped_files']}")
    print(f"* non-additive: {result['non_additive_files']}")
    if result["details"]:
        print()
        print("Details:")
        for d in result["details"]:
            print(f"  * {d}")
    print()

    if result["status"] != "OK":
        print(f"check-schema-compat: FAIL ({result['status']})", file=sys.stderr)
        return 1
    print("check-schema-compat: clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
