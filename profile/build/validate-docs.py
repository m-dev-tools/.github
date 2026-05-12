#!/usr/bin/env python3
"""Validate prose-doc frontmatter against profile/docs.schema.json.

Walks ``docs/`` for every ``*.md`` file, extracts the YAML frontmatter
block, and validates it against the docs schema. Skips ``docs/recipes/``
(those have their own schema; ``make recipes-check`` covers them).

Files marked ``generated: true`` get the §5.1 generated-doc treatment:
the prose checks are skipped, but the file's path must appear in the
repo's ``repo.meta.json:docs.generated_paths`` and vice versa (the
declaration is bidirectional — neither a stray marker nor a stale glob
can silently hide a hand-written doc).

Sibling of validate-catalog.py / validate-repo-meta.py / check-freshness.py.

Phase 1 default invocation (per spec §10):

    validate-docs.py --warn-only --docs-root docs/ --repo-meta dist/repo.meta.json

Exit codes:

  0 — no issues, or only issues seen under --warn-only
  1 — at least one error (and --warn-only not set)
  2 — docs-root or schema missing / unreadable
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE = REPO_ROOT / "profile"
DEFAULT_DOCS_ROOT = REPO_ROOT / "docs"
DEFAULT_SCHEMA = PROFILE / "docs.schema.json"

# Subtrees with their own schema / their own validator. Hardcoded for
# Phase 1 — when other "out-of-scope" subtrees emerge (e.g. an MCP
# manifest under docs/mcp/), promote this to a config field in
# repo.meta.json:docs.
SKIP_SUBDIRS = ("recipes",)


class Issue(NamedTuple):
    severity: str  # "error" | "warn"
    path: Path
    message: str


# ---------------------------------------------------------- frontmatter ---

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?\n)---\s*\n", re.DOTALL)
# A YAML scalar key: alnum + underscore + hyphen, followed by `:` and a
# value. Greedy through the rest of the line.
_KV_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*?)\s*$")


def _strip_quotes(s: str) -> str:
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    return s


def _parse_value(raw: str):
    """Parse a single YAML scalar or flow-style list. Minimal — handles
    the patterns our corpus uses (string / int / bool / [A, B, C]).
    """
    raw = raw.strip()
    if raw == "":
        return ""
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if inner == "":
            return []
        return [_parse_value(item) for item in _split_flow_list(inner)]
    if raw in ("true", "True"):
        return True
    if raw in ("false", "False"):
        return False
    # Integer (no leading +, no underscores)
    if re.fullmatch(r"-?[0-9]+", raw):
        return int(raw)
    return _strip_quotes(raw)


def _split_flow_list(inner: str) -> list[str]:
    """Split `A, B, "C, D"` on commas not inside quotes. Quoted strings
    with embedded commas are kept whole."""
    parts: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    for ch in inner:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
            buf.append(ch)
        elif ch == ",":
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    return parts


def parse_frontmatter(text: str) -> dict | None:
    """Return the parsed frontmatter dict, or None if no block is present.

    Returns an empty dict if the block exists but contains no parseable
    key-value pairs (distinct from None — the file *has* a delimited
    block, just an empty one).
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return None
    block = match.group(1)
    data: dict = {}
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        if line == "" or line.lstrip().startswith("#"):
            continue
        kv = _KV_RE.match(line)
        if not kv:
            # Block-style continuation lines (e.g. nested list items
            # starting with `  -`) are silently skipped in this minimal
            # parser. The corpus's prose-doc frontmatter is flow-style
            # only; if a doc starts using block-style we'll see the
            # required-key check fire and surface the gap.
            continue
        key, raw_value = kv.group(1), kv.group(2)
        data[key] = _parse_value(raw_value)
    return data


# ---------------------------------------------------------- core walk ---


def _load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _generated_globs(repo_meta_path: Path | None) -> list[str]:
    if repo_meta_path is None:
        return []
    try:
        meta = _load_json(repo_meta_path)
    except (OSError, json.JSONDecodeError):
        return []
    docs_block = meta.get("docs") or {}
    return list(docs_block.get("generated_paths") or [])


def _path_matches_globs(rel: str, globs: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel, g) for g in globs)


def _validate_one(
    path: Path,
    rel_path: str,
    text: str,
    schema: dict,
    generated_globs: list[str],
) -> list[Issue]:
    issues: list[Issue] = []
    frontmatter = parse_frontmatter(text)
    is_generated_by_path = _path_matches_globs(rel_path, generated_globs)
    is_generated_by_marker = (
        isinstance(frontmatter, dict) and frontmatter.get("generated") is True
    )

    if frontmatter is None:
        issues.append(Issue("error", path, "missing YAML frontmatter block"))
        # If the path was declared generated, also flag that the marker
        # is absent — same check #6 below, surfaced even on a bare file.
        if is_generated_by_path:
            issues.append(
                Issue(
                    "error",
                    path,
                    "path matches docs.generated_paths but `generated: true` is missing",
                )
            )
        return issues

    # Generated-doc bidirectional declaration check (§5.1).
    if is_generated_by_marker and not is_generated_by_path:
        issues.append(
            Issue(
                "error",
                path,
                "frontmatter has `generated: true` but path is not declared in docs.generated_paths",
            )
        )
    if is_generated_by_path and not is_generated_by_marker:
        issues.append(
            Issue(
                "error",
                path,
                "path matches docs.generated_paths but frontmatter lacks `generated: true`",
            )
        )

    # Defer to the JSON-Schema validator for everything else. The schema
    # itself handles the two variants (prose vs generated) via if/then.
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        issues.append(
            Issue(
                "error",
                path,
                f"jsonschema is required (pip install jsonschema): {exc}",
            )
        )
        return issues

    validator = Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(frontmatter), key=lambda e: list(e.absolute_path)):
        loc = "/".join(str(p) for p in err.absolute_path) or "<frontmatter>"
        issues.append(Issue("error", path, f"at {loc}: {err.message}"))

    return issues


def walk(
    docs_root: Path,
    repo_meta_path: Path | None = None,
    schema_path: Path | None = None,
) -> list[Issue]:
    """Walk ``docs_root`` and validate every ``.md`` file outside the
    skipped subdirs. Returns a list of Issue tuples; empty = clean.

    Raises FileNotFoundError if docs_root or schema doesn't exist — the
    CLI catches and exits 2. The tests catch it via main()'s rc=2.
    """
    docs_root = Path(docs_root)
    if not docs_root.is_dir():
        raise FileNotFoundError(f"docs root not found: {docs_root}")
    schema_path = Path(schema_path) if schema_path else DEFAULT_SCHEMA
    schema = _load_json(schema_path)
    generated_globs = _generated_globs(repo_meta_path)

    # Repo root is always the parent of docs_root — that's the layout
    # contract (every repo: <root>/docs/). The repo_meta path is used
    # only to read docs.generated_paths; it doesn't define the root.
    repo_root = docs_root.resolve().parent

    issues: list[Issue] = []
    for path in sorted(docs_root.rglob("*.md")):
        rel = path.resolve().relative_to(repo_root)
        rel_str = rel.as_posix()
        parts = rel.parts
        # Skip subtrees under docs/ that have their own schema. parts[0]
        # is "docs" (or whatever the docs dir is called); parts[1] is
        # the first subdir.
        if len(parts) >= 2 and parts[1] in SKIP_SUBDIRS:
            # Special-case: a recipes/README.md is a normal index doc,
            # not a recipe — it should still be validated.
            if parts[-1] != "README.md":
                continue
        text = path.read_text(encoding="utf-8")
        issues.extend(_validate_one(path, rel_str, text, schema, generated_globs))
    return issues


# ---------------------------------------------------------- CLI ---


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    parser.add_argument(
        "--docs-root",
        type=Path,
        default=DEFAULT_DOCS_ROOT,
        help=f"Directory to walk (default: {DEFAULT_DOCS_ROOT})",
    )
    parser.add_argument(
        "--repo-meta",
        type=Path,
        default=None,
        help="Path to dist/repo.meta.json (for docs.generated_paths). Optional.",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA,
        help=f"Path to docs.schema.json (default: {DEFAULT_SCHEMA})",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Print issues as warnings; exit 0 even with errors. Phase 1 default per spec §10.",
    )
    args = parser.parse_args(argv)

    try:
        issues = walk(args.docs_root, repo_meta_path=args.repo_meta, schema_path=args.schema)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not issues:
        print(f"validate-docs: {args.docs_root} clean")
        return 0

    label = "WARN" if args.warn_only else "ERROR"
    for issue in issues:
        print(f"{label}: {issue.path}: {issue.message}", file=sys.stderr)
    print(
        f"validate-docs: {len(issues)} issue(s) in {args.docs_root}",
        file=sys.stderr,
    )
    return 0 if args.warn_only else 1


if __name__ == "__main__":
    raise SystemExit(main())
