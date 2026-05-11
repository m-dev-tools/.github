#!/usr/bin/env python3
"""Validate the org catalog: profile/tools.json + profile/task_index.json.

Validates each file against its own schema using the Draft 2020-12
JSON-Schema validator. Then asserts no key collision between the two
top-level shapes (a future-proofing guard: after P1-A `task_index`
moved into its own file, the two documents share no top-level key —
this validator fails loudly if that invariant ever breaks).

Returns 0 on success, non-zero on failure with one error per line on
stderr.

Usage:
    validate-catalog.py [--tools PATH] [--task-index PATH]

Defaults to the canonical pair under profile/.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROFILE = Path(__file__).resolve().parents[1]
DEFAULT_TOOLS = PROFILE / "tools.json"
DEFAULT_TASK_INDEX = PROFILE / "task_index.json"
TOOLS_SCHEMA = PROFILE / "tools.schema.json"
TASK_INDEX_SCHEMA = PROFILE / "task_index.schema.json"


def _load_json(path: Path, errors: list[str]) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"cannot read {path}: file does not exist")
        return None
    except OSError as exc:
        errors.append(f"cannot read {path}: {exc}")
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        errors.append(f"{path}: invalid JSON: {exc}")
        return None


def _validate_against(data: dict, schema: dict, label: str, errors: list[str]) -> None:
    """Validate `data` against `schema` using Draft 2020-12.

    Collects every violation (not just the first) so the operator sees
    all problems in one pass. Falls back to a single `jsonschema.validate`
    call if the iterator API isn't available for any reason.
    """
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        errors.append(f"{label}: jsonschema is required (pip install jsonschema): {exc}")
        return
    validator = Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        path = "/".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"{label}: at {path}: {err.message}")


def validate(tools_path: Path, task_index_path: Path) -> list[str]:
    """Top-level entry point. Returns a list of error strings (empty on success)."""
    errors: list[str] = []

    tools_schema = _load_json(TOOLS_SCHEMA, errors)
    task_index_schema = _load_json(TASK_INDEX_SCHEMA, errors)
    tools = _load_json(Path(tools_path), errors)
    task_index = _load_json(Path(task_index_path), errors)

    if tools is not None and tools_schema is not None:
        _validate_against(tools, tools_schema, "tools.json", errors)
    if task_index is not None and task_index_schema is not None:
        _validate_against(task_index, task_index_schema, "task_index.json", errors)

    # Composite check: the two documents must share no top-level keys.
    # After P1-A the contract is "task_index lives in its own file";
    # this guards against future drift where someone re-inlines it.
    if isinstance(tools, dict) and isinstance(task_index, dict):
        collisions = set(tools).intersection(task_index)
        # `$schema`, `schema_compat`, `schema_version`, `kind` are
        # expected to appear in BOTH (each file declares its own
        # framing). Those are not collisions — flag only data-shape
        # overlaps.
        meta_keys = {"$schema", "schema_compat", "schema_version", "kind", "_comment"}
        real_collisions = collisions - meta_keys
        if real_collisions:
            errors.append(
                "merged shape: tools.json and task_index.json share data keys "
                f"{sorted(real_collisions)} — after P1-A these must be disjoint"
            )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    parser.add_argument(
        "--tools",
        type=Path,
        default=DEFAULT_TOOLS,
        help=f"Path to tools.json (default: {DEFAULT_TOOLS})",
    )
    parser.add_argument(
        "--task-index",
        type=Path,
        default=DEFAULT_TASK_INDEX,
        help=f"Path to task_index.json (default: {DEFAULT_TASK_INDEX})",
    )
    args = parser.parse_args(argv)

    errors = validate(args.tools, args.task_index)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {args.tools} + {args.task_index}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
