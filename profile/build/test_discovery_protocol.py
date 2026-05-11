"""Tests for the Phase-3 Track C handshake script + recipe runner.

Two scripts under test:

  * ``profile/build/test-discovery-protocol.py`` — the 8-step discovery
    handshake (parent plan §5.2). Validates that an AI agent can route
    intent → typed-ID → manifest pointer → entry with signature + example.
  * ``profile/build/run-recipe.py`` — the recipe runner. Reads a Markdown
    recipe with YAML frontmatter, validates against ``recipe.schema.json``,
    extracts the first bash block under ``## Steps``, runs it in a fresh
    ``mktemp -d``, and diffs the documented ``## Expected output``
    substring assertions against the captured stdout.

TDD discipline: these tests are written FIRST and confirmed RED (the
two scripts don't exist yet at C1). C2/C3 implement them and turn the
suite green. Mirror style of ``test_validate_catalog.py`` and
``test_build_catalog.py``: load hyphen-named scripts by file path,
prefer ``tmp_path`` fixtures, exercise public callables (not the CLI
``main`` wrapper) where possible — and the CLI wrapper via subprocess
for end-to-end checks.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE = REPO_ROOT / "profile"
BUILD = PROFILE / "build"
FIXTURES = BUILD / "fixtures"

HANDSHAKE_SCRIPT = BUILD / "test-discovery-protocol.py"
RECIPE_RUNNER = BUILD / "run-recipe.py"


# Defined exit codes (script-level contract; tests assert specific values
# so D4 / CI can branch on them).
EXIT_OK = 0
EXIT_LLMS_LINK_BROKEN = 10
EXIT_TOOLS_SCHEMA_VIOLATION = 11
EXIT_TASK_INDEX_MALFORMED = 12
EXIT_MANIFEST_FETCH_FAIL = 13
EXIT_MANIFEST_ENTRY_INCOMPLETE = 14
EXIT_FIXTURE_MISSING = 20
EXIT_INTENT_UNMATCHED = 15


# ---------------------------------------------------------------- helpers ----


def _load_module(path: Path, alias: str):
    spec = importlib.util.spec_from_file_location(alias, path)
    assert spec and spec.loader, f"cannot load {path}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_handshake(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run test-discovery-protocol.py via subprocess. Captures stdout/stderr.

    Subprocess invocation rather than in-process so we exercise the CLI
    contract (exit codes, stderr framing) that CI ultimately depends on.
    """
    return subprocess.run(
        [sys.executable, str(HANDSHAKE_SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=cwd,
    )


def _run_recipe(
    arg: str | Path,
    cwd: Path | None = None,
    *,
    extra_args: tuple[str, ...] = (),
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RECIPE_RUNNER), *extra_args, str(arg)],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=cwd,
    )


# ---------------------------------------------------------- fixture sanity ---


def test_fixture_directory_exists():
    assert FIXTURES.is_dir(), f"fixtures/ should exist at {FIXTURES}"


def test_fixture_files_present():
    expected = {
        "llms.txt",
        "tools.json",
        "task_index.json",
        "stdlib-manifest.json",
        "repo.meta.json",
    }
    actual = {p.name for p in FIXTURES.iterdir()}
    missing = expected - actual
    assert not missing, f"missing fixtures: {missing}"


def test_fixture_tools_json_parses():
    data = json.loads((FIXTURES / "tools.json").read_text(encoding="utf-8"))
    assert "tools" in data
    assert "m-stdlib" in data["tools"]


def test_fixture_task_index_resolves_json_parse_to_stdjson():
    """The 'parse JSON in M' intent maps to module:m-stdlib#STDJSON in the fixture."""
    data = json.loads((FIXTURES / "task_index.json").read_text(encoding="utf-8"))
    row = data["categories"]["lib"]["json_parse"]
    assert row["primary"] == "module:m-stdlib#STDJSON"


# ============================================================== handshake ===


# ---- C1 step 1: intent → typed-ID resolution -------------------------------


def test_intent_resolves_to_typed_id():
    """Fixture task_index.lib.json_parse.primary is module:m-stdlib#STDJSON.

    The handshake script's intent-matcher must return the same typed-ID
    when given the intent string. Exercises the in-process callable so
    we don't have to round-trip stdout.
    """
    handshake = _load_module(HANDSHAKE_SCRIPT, "_handshake_c1_intent")
    task_index = json.loads((FIXTURES / "task_index.json").read_text(encoding="utf-8"))
    primary = handshake.match_intent("parse JSON in M", task_index)
    assert primary == "module:m-stdlib#STDJSON"


def test_intent_unmatched_returns_none():
    handshake = _load_module(HANDSHAKE_SCRIPT, "_handshake_c1_intent_none")
    task_index = json.loads((FIXTURES / "task_index.json").read_text(encoding="utf-8"))
    primary = handshake.match_intent("calibrate the rocket booster", task_index)
    assert primary is None


# ---- C1 step 2: manifest URL fetches and has signature + example -----------


def test_manifest_url_fetches_and_parses_module_entry():
    """Resolving module:m-stdlib#STDJSON through tools.json points at a
    manifest URL. Fetch (file://) it, look up STDJSON, assert the labels
    map has signature + example/examples fields on at least one entry.
    """
    handshake = _load_module(HANDSHAKE_SCRIPT, "_handshake_c1_manifest")
    tools = json.loads((FIXTURES / "tools.json").read_text(encoding="utf-8"))
    manifest_url = handshake.resolve_module_manifest_url("module:m-stdlib#STDJSON", tools)
    assert manifest_url is not None
    # Resolve the file:// URL against the fixtures directory.
    body = handshake.fetch(manifest_url, base_dir=FIXTURES)
    manifest = json.loads(body)
    entry = handshake.find_module_entry("STDJSON", manifest)
    assert entry is not None, "STDJSON entry missing from manifest"
    has_signature, has_example = handshake.entry_has_signature_and_example(entry)
    assert has_signature, f"STDJSON entry has no signature field: {entry!r}"
    assert has_example, f"STDJSON entry has no example/examples field: {entry!r}"


# ---- C1 step 3: broken llms.txt link → nonzero ------------------------------


def test_broken_llms_txt_link_fails_with_nonzero_exit(tmp_path):
    """Build a llms.txt fixture pointing at a guaranteed-invalid host;
    confirm the handshake exits with EXIT_LLMS_LINK_BROKEN.
    """
    bad_fixtures = tmp_path / "fixtures"
    bad_fixtures.mkdir()
    # Mirror the real fixture set, but corrupt llms.txt.
    for name in ("tools.json", "task_index.json", "stdlib-manifest.json", "repo.meta.json"):
        (bad_fixtures / name).write_text(
            (FIXTURES / name).read_text(encoding="utf-8"), encoding="utf-8"
        )
    (bad_fixtures / "llms.txt").write_text(
        "# bad fixture\n\n"
        "- [bogus](https://example.invalid/nope/this/will/never/resolve): broken on purpose\n",
        encoding="utf-8",
    )
    result = _run_handshake("--offline", "--fixtures", str(bad_fixtures))
    assert result.returncode != 0, (
        f"expected non-zero on broken llms.txt link, got 0. stdout={result.stdout!r}"
    )
    assert result.returncode == EXIT_LLMS_LINK_BROKEN, (
        f"expected EXIT_LLMS_LINK_BROKEN={EXIT_LLMS_LINK_BROKEN}, "
        f"got {result.returncode}. stderr={result.stderr!r}"
    )


# ---- C1 step 4: schema violation in tools.json → nonzero --------------------


def test_schema_violation_in_tools_json_fails_with_nonzero_exit(tmp_path):
    bad_fixtures = tmp_path / "fixtures"
    bad_fixtures.mkdir()
    for name in ("llms.txt", "task_index.json", "stdlib-manifest.json", "repo.meta.json"):
        (bad_fixtures / name).write_text(
            (FIXTURES / name).read_text(encoding="utf-8"), encoding="utf-8"
        )
    tools = json.loads((FIXTURES / "tools.json").read_text(encoding="utf-8"))
    # additionalProperties: false at top level — unknown key trips validation.
    tools["surprise_top_level_field"] = {"x": 1}
    (bad_fixtures / "tools.json").write_text(json.dumps(tools, indent=2), encoding="utf-8")

    result = _run_handshake("--offline", "--fixtures", str(bad_fixtures))
    assert result.returncode == EXIT_TOOLS_SCHEMA_VIOLATION, (
        f"expected EXIT_TOOLS_SCHEMA_VIOLATION={EXIT_TOOLS_SCHEMA_VIOLATION}, "
        f"got {result.returncode}. stderr={result.stderr!r}"
    )


# ---- C1 step 5: malformed typed-ID in task_index → nonzero ------------------


def test_malformed_typed_id_in_task_index_fails_with_nonzero_exit(tmp_path):
    bad_fixtures = tmp_path / "fixtures"
    bad_fixtures.mkdir()
    for name in ("llms.txt", "tools.json", "stdlib-manifest.json", "repo.meta.json"):
        (bad_fixtures / name).write_text(
            (FIXTURES / name).read_text(encoding="utf-8"), encoding="utf-8"
        )
    ti = json.loads((FIXTURES / "task_index.json").read_text(encoding="utf-8"))
    ti["categories"]["lib"]["json_parse"]["primary"] = "NOT_A_TYPED_ID"
    (bad_fixtures / "task_index.json").write_text(json.dumps(ti, indent=2), encoding="utf-8")

    result = _run_handshake("--offline", "--fixtures", str(bad_fixtures))
    assert result.returncode == EXIT_TASK_INDEX_MALFORMED, (
        f"expected EXIT_TASK_INDEX_MALFORMED={EXIT_TASK_INDEX_MALFORMED}, "
        f"got {result.returncode}. stderr={result.stderr!r}"
    )


# ---- C2: end-to-end offline success path ------------------------------------


def test_handshake_offline_succeeds_against_fixtures():
    result = _run_handshake("--offline", "--fixtures", str(FIXTURES))
    assert result.returncode == EXIT_OK, (
        f"offline handshake should succeed, got rc={result.returncode}, "
        f"stderr={result.stderr!r}, stdout={result.stdout!r}"
    )
    # The routing trail is the script's primary observable output.
    assert "step 1" in result.stdout.lower() or "llms.txt" in result.stdout.lower()
    assert "STDJSON" in result.stdout


def test_handshake_missing_fixture_dir_fails_cleanly(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    result = _run_handshake("--offline", "--fixtures", str(empty))
    assert result.returncode == EXIT_FIXTURE_MISSING, (
        f"expected EXIT_FIXTURE_MISSING={EXIT_FIXTURE_MISSING}, "
        f"got {result.returncode}. stderr={result.stderr!r}"
    )


# ---- C4: determinism — two runs byte-identical (modulo timestamp lines) -----


def test_handshake_two_runs_byte_identical_offline():
    a = _run_handshake("--offline", "--fixtures", str(FIXTURES))
    b = _run_handshake("--offline", "--fixtures", str(FIXTURES))
    assert a.returncode == 0 and b.returncode == 0, (a, b)
    # Exclude any line containing the literal token ``timestamp`` from the
    # comparison so the script may, if it wishes, surface wall-clock info.
    norm_a = "\n".join(line for line in a.stdout.splitlines() if "timestamp" not in line.lower())
    norm_b = "\n".join(line for line in b.stdout.splitlines() if "timestamp" not in line.lower())
    assert norm_a == norm_b, (
        f"handshake non-deterministic between runs.\n"
        f"--- run 1 ---\n{norm_a}\n--- run 2 ---\n{norm_b}\n"
    )


# ============================================================ recipe runner =


# Minimal CI-verifiable recipe — the runner shells out, so we use commands
# guaranteed to be on any Linux dev host (echo, true).
SIMPLE_RECIPE = """\
---
id: recipe:fixture-echo
title: Smoke test for the recipe runner
intent: Smoke test for the recipe runner fixture
touches:
  - cmd:m-cli#test
verified_on: 2026-05-11
ci_verifiable: true
tier: tier-1
---

# Smoke test for the recipe runner

## Prerequisites

Bash and `echo` on PATH.

## Steps

```bash
echo hello recipe-runner
echo 0/0 failed
```

## Expected output

The captured stdout must contain: `hello recipe-runner`.
The captured stdout must contain: `0/0 failed`.

## Failure triage

None — this is a smoke fixture.
"""


MANUAL_CHECKLIST_RECIPE = """\
---
id: recipe:fixture-manual
title: Manual-only recipe fixture
intent: Manual-only recipe fixture
touches:
  - tool:m-cli
verified_on: 2026-05-11
ci_verifiable: false
manual_checklist_url: https://github.com/m-dev-tools/.github/blob/main/docs/recipes/manual-checklist.md
tier: tier-1
---

# Manual-only

## Prerequisites

Human eyeballs.

## Steps

```bash
echo this should be skipped
```

## Expected output

The captured stdout must contain: `this should be skipped`.
"""


FAILING_RECIPE = """\
---
id: recipe:fixture-failing
title: Recipe whose body exits non-zero
intent: Recipe whose body exits non-zero (fixture)
touches:
  - cmd:m-cli#test
verified_on: 2026-05-11
ci_verifiable: true
tier: tier-1
---

# Failing

## Steps

```bash
echo about to fail
false
```

## Expected output

The captured stdout must contain: `about to fail`.
"""


MISSING_EXPECTED_RECIPE = """\
---
id: recipe:fixture-missing-expected
title: Recipe whose expected substring is missing
intent: Recipe whose expected substring is missing (fixture)
touches:
  - cmd:m-cli#test
verified_on: 2026-05-11
ci_verifiable: true
tier: tier-1
---

# Missing expected

## Steps

```bash
echo only this line
```

## Expected output

The captured stdout must contain: `THIS WILL NEVER APPEAR`.
"""


BAD_FRONTMATTER_RECIPE = """\
---
id: not-a-typed-id
title: Bad frontmatter — id is malformed
intent: Bad frontmatter fixture
touches:
  - cmd:m-cli#test
verified_on: 2026-05-11
ci_verifiable: true
---

# Bad

## Steps

```bash
echo never reached
```

## Expected output

The captured stdout must contain: `never reached`.
"""


def _write_recipe(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


# Exit codes from the runner (per Track C spec).
RUN_OK = 0
RUN_FRONTMATTER_INVALID = 1
RUN_COMMAND_FAILED = 2
RUN_EXPECTED_MISSING = 3
RUN_FILE_UNREADABLE = 4


def test_recipe_runner_happy_path(tmp_path):
    p = _write_recipe(tmp_path, "smoke.md", SIMPLE_RECIPE)
    result = _run_recipe(p)
    assert result.returncode == RUN_OK, (
        f"smoke recipe should succeed; rc={result.returncode}, "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert "OK:" in result.stdout


def test_recipe_runner_skips_manual_checklist(tmp_path):
    p = _write_recipe(tmp_path, "manual.md", MANUAL_CHECKLIST_RECIPE)
    result = _run_recipe(p)
    assert result.returncode == RUN_OK, (
        f"ci_verifiable=false should exit 0 with SKIP; "
        f"rc={result.returncode}, stderr={result.stderr!r}"
    )
    assert "SKIP" in result.stdout
    # Should reference the manual checklist URL the user has to consult.
    assert "manual-checklist" in result.stdout or "manual_checklist_url" in result.stdout


def test_recipe_runner_fails_on_nonzero_exit(tmp_path):
    p = _write_recipe(tmp_path, "failing.md", FAILING_RECIPE)
    result = _run_recipe(p)
    assert result.returncode == RUN_COMMAND_FAILED, (
        f"expected RUN_COMMAND_FAILED={RUN_COMMAND_FAILED}, "
        f"got {result.returncode}. stderr={result.stderr!r}"
    )


def test_recipe_runner_fails_on_missing_expected_output(tmp_path):
    p = _write_recipe(tmp_path, "missing-expected.md", MISSING_EXPECTED_RECIPE)
    result = _run_recipe(p)
    assert result.returncode == RUN_EXPECTED_MISSING, (
        f"expected RUN_EXPECTED_MISSING={RUN_EXPECTED_MISSING}, "
        f"got {result.returncode}. stderr={result.stderr!r}"
    )


def test_recipe_runner_fails_on_bad_frontmatter(tmp_path):
    p = _write_recipe(tmp_path, "bad.md", BAD_FRONTMATTER_RECIPE)
    result = _run_recipe(p)
    assert result.returncode == RUN_FRONTMATTER_INVALID, (
        f"expected RUN_FRONTMATTER_INVALID={RUN_FRONTMATTER_INVALID}, "
        f"got {result.returncode}. stderr={result.stderr!r}"
    )


def test_recipe_runner_fails_on_unreadable_file(tmp_path):
    result = _run_recipe(tmp_path / "does-not-exist.md")
    assert result.returncode == RUN_FILE_UNREADABLE, (
        f"expected RUN_FILE_UNREADABLE={RUN_FILE_UNREADABLE}, "
        f"got {result.returncode}. stderr={result.stderr!r}"
    )


def test_recipe_runner_uses_fresh_mktemp_directory(tmp_path):
    """The body of a recipe runs in a fresh `mktemp -d`, not in the
    recipe file's directory. Confirm by writing a recipe that creates a
    sentinel file inside its working dir, then asserting the recipe
    file's own directory is unchanged.
    """
    body = """\
---
id: recipe:fixture-pwd-check
title: Recipe runs in mktemp -d
intent: Recipe runs in a fresh mktemp dir (fixture)
touches:
  - cmd:m-cli#test
verified_on: 2026-05-11
ci_verifiable: true
tier: tier-1
---

# pwd

## Steps

```bash
touch sentinel-from-recipe
pwd
```

## Expected output

The captured stdout must contain: `/tmp`.
"""
    p = _write_recipe(tmp_path, "pwd.md", body)
    result = _run_recipe(p)
    assert result.returncode == RUN_OK, (
        f"rc={result.returncode}, stderr={result.stderr!r}, stdout={result.stdout!r}"
    )
    # Sentinel should NOT be in the recipe file's directory.
    assert not (tmp_path / "sentinel-from-recipe").exists(), (
        "recipe ran in the recipe-file directory, not a mktemp -d"
    )


# ====================================================== --validate-only ===


VALIDATE_ONLY_RECIPE_NO_ASSERTIONS = """\
---
id: recipe:fixture-no-assertions
title: Validate-only fails when no must-contain assertions are declared
intent: Validate-only fails when no must-contain assertions are declared
touches:
  - cmd:m-cli#test
verified_on: 2026-05-11
ci_verifiable: true
tier: tier-1
---

# No assertions

## Steps

```bash
echo hello
```

## Expected output

(no must-contain rows)
"""


def test_recipe_runner_validate_only_happy_path(tmp_path):
    """--validate-only on a well-formed recipe must exit 0 without running
    the bash block. We assert exit 0 + 'VALIDATE:' in stdout."""
    p = _write_recipe(tmp_path, "smoke.md", SIMPLE_RECIPE)
    result = _run_recipe(p, extra_args=("--validate-only",))
    assert result.returncode == RUN_OK, (
        f"validate-only should succeed; rc={result.returncode}, "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert "VALIDATE:" in result.stdout
    # The bash block must not have executed — no 'OK:' (the exec-mode
    # success token) and no echo'd stdout from the recipe body.
    assert "OK:" not in result.stdout
    assert "hello recipe-runner" not in result.stdout


def test_recipe_runner_validate_only_still_skips_manual(tmp_path):
    """ci_verifiable: false short-circuits earlier than the validate-only
    branch, so we still get a SKIP line on manual recipes."""
    p = _write_recipe(tmp_path, "manual.md", MANUAL_CHECKLIST_RECIPE)
    result = _run_recipe(p, extra_args=("--validate-only",))
    assert result.returncode == RUN_OK
    assert "SKIP" in result.stdout


def test_recipe_runner_validate_only_rejects_bad_frontmatter(tmp_path):
    p = _write_recipe(tmp_path, "bad.md", BAD_FRONTMATTER_RECIPE)
    result = _run_recipe(p, extra_args=("--validate-only",))
    assert result.returncode == RUN_FRONTMATTER_INVALID


def test_recipe_runner_validate_only_rejects_missing_assertions(tmp_path):
    """ci_verifiable: true with no 'must contain: …' rows must fail
    validation — otherwise CI is gating on nothing."""
    p = _write_recipe(tmp_path, "no-assertions.md", VALIDATE_ONLY_RECIPE_NO_ASSERTIONS)
    result = _run_recipe(p, extra_args=("--validate-only",))
    assert result.returncode == RUN_FRONTMATTER_INVALID, (
        f"recipe with zero must-contain assertions should be rejected; "
        f"rc={result.returncode}, stderr={result.stderr!r}"
    )


def test_repo_recipes_all_pass_validate_only():
    """Every committed recipe under docs/recipes/ must pass
    --validate-only. This is the same gate CI runs."""
    recipes_dir = Path(__file__).resolve().parents[2] / "docs" / "recipes"
    md_files = sorted(p for p in recipes_dir.glob("*.md") if p.name != "README.md")
    assert md_files, f"no recipes found under {recipes_dir}"
    for recipe in md_files:
        result = _run_recipe(recipe, extra_args=("--validate-only",))
        assert result.returncode == RUN_OK, (
            f"{recipe.name} failed --validate-only; "
            f"rc={result.returncode}, stderr={result.stderr!r}, "
            f"stdout={result.stdout!r}"
        )
