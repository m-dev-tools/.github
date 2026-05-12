"""Tests for validate-docs.py — Phase 1 Track A (P1.3).

Mirrors the test_validate_catalog.py pattern: load the hyphen-named
script via importlib, exercise the validator's typed API on synthetic
docs/ trees under tmp_path, assert the issues list shape.

The validator's surface is ``walk(docs_root, repo_meta_path=None,
schema_path=None) -> list[Issue]`` where each ``Issue`` is a
namedtuple-ish ``(severity, path, message)``. Empty list = clean.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE = REPO_ROOT / "profile"
BUILD = PROFILE / "build"

_validator_path = BUILD / "validate-docs.py"
_spec = importlib.util.spec_from_file_location("_validate_docs", _validator_path)
_validate_docs = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_validate_docs)


# ---------------------------------------------------------------- helpers ---


def _write_doc(path: Path, frontmatter: dict | None, body: str = "# Body\n") -> None:
    """Write a markdown file with optional YAML frontmatter.

    Uses minimal YAML emission (str/int/list scalars + flow-style lists)
    matching what the production corpus emits. Avoids the PyYAML
    dependency in tests.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    parts: list[str] = []
    if frontmatter is not None:
        parts.append("---\n")
        for key, value in frontmatter.items():
            parts.append(f"{key}: {_yaml_scalar(value)}\n")
        parts.append("---\n")
    parts.append(body)
    path.write_text("".join(parts), encoding="utf-8")


def _yaml_scalar(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_yaml_scalar(v) for v in value) + "]"
    return str(value)


def _write_repo_meta(path: Path, docs_block: dict | None = None) -> None:
    """Write a minimal repo.meta.json. Only the `docs` block matters here."""
    meta = {
        "id": "tool:test-fixture",
        "repo": "https://github.com/m-dev-tools/test-fixture",
        "role": "Test fixture",
        "language": ["python"],
        "license": "MIT",
        "agent_instructions": "AGENTS.md",
        "verified_on": "2026-05-12",
        "exposes": {"commands": "dist/commands.json"},
        "verification_commands": ["make check"],
    }
    if docs_block is not None:
        meta["docs"] = docs_block
    path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


# ---------------------------------------------------------------- happy ---


def test_clean_prose_doc(tmp_path):
    docs = tmp_path / "docs"
    _write_doc(
        docs / "good-guide.md",
        {
            "created": "2026-01-01",
            "last_modified": "2026-05-01",
            "revisions": 3,
            "doc_type": ["GUIDE"],
            "lifecycle": "active",
        },
    )
    _write_doc(docs / "README.md", {
        "created": "2026-01-01",
        "last_modified": "2026-05-01",
        "revisions": 1,
        "doc_type": ["REFERENCE"],
        "lifecycle": "active",
    })
    issues = _validate_docs.walk(docs)
    assert issues == []


def test_clean_generated_doc(tmp_path):
    """A doc with `generated: true` declared in docs.generated_paths
    passes with just `generated` + `last_modified`."""
    docs = tmp_path / "docs"
    _write_doc(docs / "README.md", {
        "created": "2026-01-01",
        "last_modified": "2026-05-01",
        "revisions": 1,
        "doc_type": ["REFERENCE"],
        "lifecycle": "active",
    })
    _write_doc(
        docs / "modules" / "stdjson.md",
        {"generated": True, "last_modified": "2026-05-10"},
    )
    repo_meta = tmp_path / "repo.meta.json"
    _write_repo_meta(repo_meta, docs_block={"generated_paths": ["docs/modules/*.md"]})

    issues = _validate_docs.walk(docs, repo_meta_path=repo_meta)
    assert issues == []


# ---------------------------------------------------------------- failures ---


def test_missing_frontmatter(tmp_path):
    docs = tmp_path / "docs"
    _write_doc(docs / "bare.md", frontmatter=None)
    issues = _validate_docs.walk(docs)
    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert "frontmatter" in issues[0].message.lower()
    assert issues[0].path.name == "bare.md"


def test_missing_required_key(tmp_path):
    docs = tmp_path / "docs"
    _write_doc(
        docs / "no-doctype.md",
        {
            "created": "2026-01-01",
            "last_modified": "2026-05-01",
            "revisions": 3,
            "lifecycle": "active",
            # doc_type intentionally absent
        },
    )
    issues = _validate_docs.walk(docs)
    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert "doc_type" in issues[0].message


def test_invalid_doc_type_enum(tmp_path):
    docs = tmp_path / "docs"
    _write_doc(
        docs / "weird.md",
        {
            "created": "2026-01-01",
            "last_modified": "2026-05-01",
            "revisions": 3,
            "doc_type": ["FAKE-TYPE"],
            "lifecycle": "active",
        },
    )
    issues = _validate_docs.walk(docs)
    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert "FAKE-TYPE" in issues[0].message


def test_invalid_lifecycle_enum(tmp_path):
    docs = tmp_path / "docs"
    _write_doc(
        docs / "bad-lifecycle.md",
        {
            "created": "2026-01-01",
            "last_modified": "2026-05-01",
            "revisions": 3,
            "doc_type": ["GUIDE"],
            "lifecycle": "bogus",
        },
    )
    issues = _validate_docs.walk(docs)
    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert "bogus" in issues[0].message


def test_generated_marker_without_repo_meta_declaration(tmp_path):
    """A file with `generated: true` whose path isn't declared in
    docs.generated_paths is suspicious (typo / accidental hiding)."""
    docs = tmp_path / "docs"
    _write_doc(
        docs / "hand-written.md",
        {"generated": True, "last_modified": "2026-05-10"},
    )
    repo_meta = tmp_path / "repo.meta.json"
    _write_repo_meta(repo_meta, docs_block={"generated_paths": []})
    issues = _validate_docs.walk(docs, repo_meta_path=repo_meta)
    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert "generated" in issues[0].message.lower()
    assert "docs.generated_paths" in issues[0].message


def test_path_declared_generated_but_marker_missing(tmp_path):
    """A file whose path matches docs.generated_paths but lacks
    `generated: true` is suspicious (stale glob / hand-edit on a
    generated doc)."""
    docs = tmp_path / "docs"
    _write_doc(
        docs / "modules" / "stdjson.md",
        {
            "created": "2026-01-01",
            "last_modified": "2026-05-01",
            "revisions": 1,
            "doc_type": ["REFERENCE"],
            "lifecycle": "active",
        },
    )
    repo_meta = tmp_path / "repo.meta.json"
    _write_repo_meta(repo_meta, docs_block={"generated_paths": ["docs/modules/*.md"]})
    issues = _validate_docs.walk(docs, repo_meta_path=repo_meta)
    assert len(issues) == 1
    assert "generated" in issues[0].message.lower()


def test_recipes_subdir_skipped(tmp_path):
    """Files under docs/recipes/ follow recipe.schema.json, not
    docs.schema.json — validate-docs.py leaves them to recipes-check.
    README.md inside recipes/ is still treated as a normal doc."""
    docs = tmp_path / "docs"
    _write_doc(
        docs / "recipes" / "some-recipe.md",
        {
            "id": "recipe:some-recipe",
            "title": "Some recipe",
            "intent": "Test fixture",
            "verified_on": "2026-05-12",
            "ci_verifiable": True,
        },
    )
    _write_doc(
        docs / "recipes" / "README.md",
        {
            "created": "2026-01-01",
            "last_modified": "2026-05-01",
            "revisions": 1,
            "doc_type": ["REFERENCE"],
            "lifecycle": "active",
        },
    )
    issues = _validate_docs.walk(docs)
    # The recipe is skipped; the README is validated and clean.
    assert issues == []


# ---------------------------------------------------------------- CLI ---


def test_main_clean_exits_zero(tmp_path):
    docs = tmp_path / "docs"
    _write_doc(
        docs / "good.md",
        {
            "created": "2026-01-01",
            "last_modified": "2026-05-01",
            "revisions": 1,
            "doc_type": ["GUIDE"],
            "lifecycle": "active",
        },
    )
    rc = _validate_docs.main(["--docs-root", str(docs)])
    assert rc == 0


def test_main_error_exits_nonzero(tmp_path):
    docs = tmp_path / "docs"
    _write_doc(docs / "bare.md", frontmatter=None)
    rc = _validate_docs.main(["--docs-root", str(docs)])
    assert rc == 1


def test_main_warn_only_exits_zero_on_error(tmp_path):
    """--warn-only converts errors to warnings; rc=0 even with issues.
    Phase 1 default per docs-discoverability-spec.md §10 Phase 1."""
    docs = tmp_path / "docs"
    _write_doc(docs / "bare.md", frontmatter=None)
    rc = _validate_docs.main(["--docs-root", str(docs), "--warn-only"])
    assert rc == 0


def test_main_missing_docs_root_exits_nonzero(tmp_path):
    rc = _validate_docs.main(["--docs-root", str(tmp_path / "nope")])
    assert rc == 2
