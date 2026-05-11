"""Tests for validate-catalog.py — TDD: B1 (RED) before B2 (GREEN).

Strategy: exercise the validator via its `validate(tools_path,
task_index_path) -> list[str]` API, which returns a list of error strings
(empty on success). The CLI `main()` wraps it. Tests cover:

  * the committed baseline pair validates clean (smoke);
  * a `tools.json` with an unknown top-level key fails under
    `additionalProperties: false`;
  * a `task_index.json` row with a malformed typed ID fails under the
    typedID regex;
  * a `tools.json` and `task_index.json` whose merged shape has a key
    collision is reported (defensive: future-proof against schema drift).

Tests use `tmp_path` with copies of the committed baseline, mutated to
trigger specific failures. The script is loaded by file path because
its name contains a hyphen (matches the validate-repo-meta.py pattern).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE = REPO_ROOT / "profile"
BUILD = PROFILE / "build"

# Load the hyphen-named script as a module. Same trick phase0-smoke uses
# for validate-repo-meta.
_validator_path = BUILD / "validate-catalog.py"
_spec = importlib.util.spec_from_file_location("_validate_catalog", _validator_path)
_validate_catalog = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_validate_catalog)


# ---------------------------------------------------------------- fixtures ---


@pytest.fixture
def baseline_tools() -> dict:
    return json.loads((PROFILE / "tools.json").read_text(encoding="utf-8"))


@pytest.fixture
def baseline_task_index() -> dict:
    return json.loads((PROFILE / "task_index.json").read_text(encoding="utf-8"))


def _write_pair(tmp_path: Path, tools: dict, task_index: dict) -> tuple[Path, Path]:
    tools_path = tmp_path / "tools.json"
    task_index_path = tmp_path / "task_index.json"
    tools_path.write_text(json.dumps(tools, indent=2), encoding="utf-8")
    task_index_path.write_text(json.dumps(task_index, indent=2), encoding="utf-8")
    return tools_path, task_index_path


# ---------------------------------------------------------------- happy path -


def test_baseline_pair_validates(baseline_tools, baseline_task_index, tmp_path):
    tools_path, task_index_path = _write_pair(tmp_path, baseline_tools, baseline_task_index)
    errors = _validate_catalog.validate(tools_path, task_index_path)
    assert errors == [], f"baseline should be clean, got: {errors}"


def test_main_baseline_exits_zero():
    rc = _validate_catalog.main(
        ["--tools", str(PROFILE / "tools.json"), "--task-index", str(PROFILE / "task_index.json")]
    )
    assert rc == 0


# ---------------------------------------------------------------- failures ---


def test_unknown_top_level_key_in_tools_fails(baseline_tools, baseline_task_index, tmp_path):
    bad = dict(baseline_tools)
    bad["task_index"] = {"categories": {}}  # forbidden in post-P1-A tools.json
    tools_path, task_index_path = _write_pair(tmp_path, bad, baseline_task_index)
    errors = _validate_catalog.validate(tools_path, task_index_path)
    assert errors, "expected validation error for unknown top-level key"
    assert any("task_index" in e or "additional" in e.lower() for e in errors), errors


def test_arbitrary_unknown_key_in_tools_fails(baseline_tools, baseline_task_index, tmp_path):
    bad = dict(baseline_tools)
    bad["not_a_real_field"] = {"x": 1}
    tools_path, task_index_path = _write_pair(tmp_path, bad, baseline_task_index)
    errors = _validate_catalog.validate(tools_path, task_index_path)
    assert errors
    assert any("not_a_real_field" in e or "additional" in e.lower() for e in errors), errors


def test_malformed_typed_id_in_task_index_fails(baseline_tools, baseline_task_index, tmp_path):
    bad_ti = json.loads(json.dumps(baseline_task_index))  # deep copy
    # Pick the workflow.scaffold_new_project intent (known to exist in baseline)
    bad_ti["categories"]["workflow"]["scaffold_new_project"]["primary"] = "NOT_A_TYPED_ID"
    tools_path, task_index_path = _write_pair(tmp_path, baseline_tools, bad_ti)
    errors = _validate_catalog.validate(tools_path, task_index_path)
    assert errors
    assert any("primary" in e or "NOT_A_TYPED_ID" in e or "pattern" in e.lower() for e in errors), errors


def test_malformed_typed_id_in_see_also_fails(baseline_tools, baseline_task_index, tmp_path):
    bad_ti = json.loads(json.dumps(baseline_task_index))
    bad_ti["categories"]["workflow"]["pre_commit"]["see_also"] = ["cmd:m-cli#fmt", "bogus:thing"]
    tools_path, task_index_path = _write_pair(tmp_path, baseline_tools, bad_ti)
    errors = _validate_catalog.validate(tools_path, task_index_path)
    assert errors
    assert any("pattern" in e.lower() or "bogus" in e for e in errors), errors


def test_missing_required_in_tool_entry_fails(baseline_tools, baseline_task_index, tmp_path):
    bad = json.loads(json.dumps(baseline_tools))
    # Pick any tool entry and drop a required field
    first_tool_key = next(iter(bad["tools"]))
    del bad["tools"][first_tool_key]["repo"]
    tools_path, task_index_path = _write_pair(tmp_path, bad, baseline_task_index)
    errors = _validate_catalog.validate(tools_path, task_index_path)
    assert errors
    assert any("repo" in e or "required" in e.lower() for e in errors), errors


def test_inlined_facts_block_in_tool_entry_fails(baseline_tools, baseline_task_index, tmp_path):
    """Inlined facts (objects in tool entries) are forbidden — only *_url
    pointer strings allowed for the pattern-property surface."""
    bad = json.loads(json.dumps(baseline_tools))
    first_tool_key = next(iter(bad["tools"]))
    # Inject something the pattern-property regex doesn't whitelist (no _url / _count suffix)
    bad["tools"][first_tool_key]["inlined_modules"] = {"STDJSON": {"signature": "parse"}}
    tools_path, task_index_path = _write_pair(tmp_path, bad, baseline_task_index)
    errors = _validate_catalog.validate(tools_path, task_index_path)
    assert errors
    assert any("inlined_modules" in e or "additional" in e.lower() for e in errors), errors


def test_unknown_top_level_key_in_task_index_fails(baseline_tools, baseline_task_index, tmp_path):
    bad_ti = json.loads(json.dumps(baseline_task_index))
    bad_ti["surprise_field"] = "boo"
    tools_path, task_index_path = _write_pair(tmp_path, baseline_tools, bad_ti)
    errors = _validate_catalog.validate(tools_path, task_index_path)
    assert errors
    assert any("surprise_field" in e or "additional" in e.lower() for e in errors), errors


def test_missing_file_reports_error(tmp_path):
    errors = _validate_catalog.validate(
        tmp_path / "does-not-exist.json", tmp_path / "also-missing.json"
    )
    assert errors
    assert any("does-not-exist" in e or "cannot" in e.lower() for e in errors), errors
