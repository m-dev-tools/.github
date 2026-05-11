"""Tests for check-schema-compat.py — Phase 5 Track D1 (RED) before D2 (GREEN).

Two layers:

* Pure-function ``check_schema_compat_impl(pairs, changelog_modified)``
  exercised with hand-built dicts. No filesystem, no git.
* CLI-level smoke against an ephemeral git repo set up in ``tmp_path``.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD = REPO_ROOT / "profile" / "build"

_path = BUILD / "check-schema-compat.py"
_spec = importlib.util.spec_from_file_location("_check_schema_compat", _path)
_check_schema_compat = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_check_schema_compat)


# ----------------------------------------------------------- fixture helpers


def _base_schema(schema_compat: int = 1) -> dict:
    """Minimal-shape baseline; ``additionalProperties: false``, two
    required keys, one enum."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "license"],
        "schema_compat": schema_compat,
        "schema_version": "1.0",
        "properties": {
            "id": {"type": "string"},
            "license": {"enum": ["AGPL-3.0", "MIT"]},
            "optional_field": {"type": "string"},
        },
    }


# --------------------------------------------------------- pure function


def test_no_schema_change_is_ok() -> None:
    base = _base_schema()
    head = _base_schema()
    result = _check_schema_compat.check_schema_compat_impl(
        pairs=[("tools.schema.json", base, head)],
        changelog_modified=False,
    )
    assert result["status"] == "OK"


def test_schema_compat_bump_with_changelog_modified_is_ok() -> None:
    """schema_compat 1→2 + the same PR modified schema-changelog.md → OK."""
    base = _base_schema(schema_compat=1)
    head = _base_schema(schema_compat=2)
    result = _check_schema_compat.check_schema_compat_impl(
        pairs=[("tools.schema.json", base, head)],
        changelog_modified=True,
    )
    assert result["status"] == "OK"
    assert result["bumped_files"] == ["tools.schema.json"]


def test_schema_compat_bump_without_changelog_fails() -> None:
    """schema_compat bumped but the changelog was NOT modified in this PR
    → MISSING_CHANGELOG_ROW."""
    base = _base_schema(schema_compat=1)
    head = _base_schema(schema_compat=2)
    result = _check_schema_compat.check_schema_compat_impl(
        pairs=[("tools.schema.json", base, head)],
        changelog_modified=False,
    )
    assert result["status"] == "MISSING_CHANGELOG_ROW"


def test_non_additive_required_removal_without_bump_fails() -> None:
    """A required field was removed without bumping schema_compat
    → NON_ADDITIVE_WITHOUT_BUMP. Removing a required field is a
    consumer-breaking change (consumers still producing it now fail
    additionalProperties)."""
    base = _base_schema()
    head = _base_schema()
    head["required"] = ["id"]  # "license" removed
    result = _check_schema_compat.check_schema_compat_impl(
        pairs=[("tools.schema.json", base, head)],
        changelog_modified=False,
    )
    assert result["status"] == "NON_ADDITIVE_WITHOUT_BUMP"
    assert any("license" in d for d in result["details"])


def test_non_additive_enum_value_removed_without_bump_fails() -> None:
    base = _base_schema()
    head = _base_schema()
    head["properties"]["license"]["enum"] = ["AGPL-3.0"]  # "MIT" removed
    result = _check_schema_compat.check_schema_compat_impl(
        pairs=[("tools.schema.json", base, head)],
        changelog_modified=False,
    )
    assert result["status"] == "NON_ADDITIVE_WITHOUT_BUMP"
    assert any("enum" in d.lower() and "MIT" in d for d in result["details"])


def test_non_additive_additional_properties_tightened_without_bump_fails() -> None:
    """additionalProperties: true → false is a consumer-breaking change
    (extra fields previously accepted now reject)."""
    base = _base_schema()
    base["additionalProperties"] = True
    head = _base_schema()
    head["additionalProperties"] = False
    result = _check_schema_compat.check_schema_compat_impl(
        pairs=[("tools.schema.json", base, head)],
        changelog_modified=False,
    )
    assert result["status"] == "NON_ADDITIVE_WITHOUT_BUMP"
    assert any("additionalProperties" in d for d in result["details"])


def test_additive_change_without_bump_is_ok() -> None:
    """Adding an optional field is additive — no bump needed."""
    base = _base_schema()
    head = _base_schema()
    head["properties"]["new_optional"] = {"type": "string"}
    result = _check_schema_compat.check_schema_compat_impl(
        pairs=[("tools.schema.json", base, head)],
        changelog_modified=False,
    )
    assert result["status"] == "OK"


def test_additive_enum_added_without_bump_is_ok() -> None:
    """Adding an enum value is additive."""
    base = _base_schema()
    head = _base_schema()
    head["properties"]["license"]["enum"] = ["AGPL-3.0", "MIT", "Apache-2.0"]
    result = _check_schema_compat.check_schema_compat_impl(
        pairs=[("tools.schema.json", base, head)],
        changelog_modified=False,
    )
    assert result["status"] == "OK"


def test_non_additive_with_bump_and_changelog_is_ok() -> None:
    """A breaking change is acceptable IF schema_compat bumped AND the
    changelog was modified. This is the happy path for a real-world
    schema migration."""
    base = _base_schema(schema_compat=1)
    head = _base_schema(schema_compat=2)
    head["required"] = ["id"]
    result = _check_schema_compat.check_schema_compat_impl(
        pairs=[("tools.schema.json", base, head)],
        changelog_modified=True,
    )
    assert result["status"] == "OK"


def test_two_schemas_one_bumps_one_doesnt() -> None:
    """tools.schema.json bumps + changelog modified. task_index.schema.json
    untouched. Result: OK."""
    base_tools = _base_schema(schema_compat=1)
    head_tools = _base_schema(schema_compat=2)
    base_ti = _base_schema(schema_compat=1)
    head_ti = _base_schema(schema_compat=1)
    result = _check_schema_compat.check_schema_compat_impl(
        pairs=[
            ("tools.schema.json", base_tools, head_tools),
            ("task_index.schema.json", base_ti, head_ti),
        ],
        changelog_modified=True,
    )
    assert result["status"] == "OK"


# --------------------------------------------------------- CLI smoke


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=path, check=True)


def _commit_all(path: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=path, check=True)


def test_cli_no_change_returns_0(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    profile = tmp_path / "profile"
    profile.mkdir()
    (profile / "tools.schema.json").write_text(json.dumps(_base_schema()), encoding="utf-8")
    (profile / "schema-changelog.md").write_text("# Schema changelog\n", encoding="utf-8")
    _commit_all(tmp_path, "base")
    base_ref = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, capture_output=True, text=True, check=True
    ).stdout.strip()

    # No second commit needed; HEAD == base → no change.
    rc = _check_schema_compat.main(
        ["--base", base_ref, "--head", "HEAD", "--repo", str(tmp_path)]
    )
    assert rc == 0


def test_cli_bump_without_changelog_returns_1(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    profile = tmp_path / "profile"
    profile.mkdir()
    (profile / "tools.schema.json").write_text(json.dumps(_base_schema()), encoding="utf-8")
    (profile / "schema-changelog.md").write_text("# Schema changelog\n", encoding="utf-8")
    _commit_all(tmp_path, "base")
    base_ref = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, capture_output=True, text=True, check=True
    ).stdout.strip()

    # Bump schema_compat WITHOUT touching the changelog.
    bumped = _base_schema()
    bumped["schema_compat"] = 2
    (profile / "tools.schema.json").write_text(json.dumps(bumped), encoding="utf-8")
    _commit_all(tmp_path, "bump")

    rc = _check_schema_compat.main(
        ["--base", base_ref, "--head", "HEAD", "--repo", str(tmp_path)]
    )
    assert rc == 1


def test_cli_bump_with_changelog_returns_0(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    profile = tmp_path / "profile"
    profile.mkdir()
    (profile / "tools.schema.json").write_text(json.dumps(_base_schema()), encoding="utf-8")
    (profile / "schema-changelog.md").write_text("# Schema changelog\n", encoding="utf-8")
    _commit_all(tmp_path, "base")
    base_ref = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, capture_output=True, text=True, check=True
    ).stdout.strip()

    bumped = _base_schema()
    bumped["schema_compat"] = 2
    (profile / "tools.schema.json").write_text(json.dumps(bumped), encoding="utf-8")
    (profile / "schema-changelog.md").write_text(
        "# Schema changelog\n\n## v2\n\nBumped to v2.\n", encoding="utf-8"
    )
    _commit_all(tmp_path, "bump + changelog")

    rc = _check_schema_compat.main(
        ["--base", base_ref, "--head", "HEAD", "--repo", str(tmp_path)]
    )
    assert rc == 0


def test_cli_against_committed_main_returns_0() -> None:
    """Smoke: against the real `main` baseline, the gate should be a
    no-op (HEAD == base). Pins the gate doesn't false-positive on the
    current state."""
    rc = _check_schema_compat.main(["--base", "HEAD", "--head", "HEAD"])
    assert rc == 0
