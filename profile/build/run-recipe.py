#!/usr/bin/env python3
"""Phase-3 Track C — the lightweight recipe runner.

Reads one Markdown recipe file:

  1. Split on ``---`` boundaries to extract YAML frontmatter.
  2. Validate frontmatter against ``profile/recipe.schema.json``.
  3. If ``ci_verifiable: false`` → print ``SKIP: <recipe> (manual
     checklist; see <manual_checklist_url>)`` and exit 0.
  4. Extract the FIRST bash-fenced block under ``## Steps``.
  5. Create a ``mktemp -d`` directory; cd into it.
  6. Run the bash block as a single ``bash -c "set -e; <body>"`` and
     capture stdout + stderr.
  7. Read ``## Expected output``'s "must contain: <substring>"
     assertions; each must appear in captured stdout — diff and fail
     with context on mismatch.
  8. Clean up the temp directory on success or failure.
  9. Print ``OK: <recipe-file>`` on success.

Exit codes (the CI gate in Track D branches on these):

  * 0 — success
  * 1 — frontmatter invalid (schema violation or YAML parse error)
  * 2 — command sequence exited non-zero
  * 3 — expected-output substring not found in captured stdout
  * 4 — recipe file unreadable

CLI::

    run-recipe.py path/to/recipe.md
    run-recipe.py --validate-only path/to/recipe.md

``--validate-only`` skips the ``mktemp -d`` + ``bash`` execution stage
and only validates the recipe's frontmatter, presence of a Steps bash
block, and a non-empty ``## Expected output`` section. CI uses this mode
to gate recipe shape without needing the M toolchain installed.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROFILE = Path(__file__).resolve().parents[1]
RECIPE_SCHEMA_PATH = PROFILE / "recipe.schema.json"

EXIT_OK = 0
EXIT_FRONTMATTER_INVALID = 1
EXIT_COMMAND_FAILED = 2
EXIT_EXPECTED_MISSING = 3
EXIT_FILE_UNREADABLE = 4

# ---- Markdown / frontmatter parsing ----------------------------------------

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n(.*)$", re.DOTALL)
# A bash-fenced block under ## Steps. Tolerant of preceding whitespace.
# We extract the FIRST such block; subsequent blocks are ignored.
STEPS_HEADER_RE = re.compile(r"(?m)^##\s+Steps\s*$")
NEXT_H2_RE = re.compile(r"(?m)^##\s+\S")
BASH_FENCE_RE = re.compile(r"```(?:bash|sh)\s*\n(.*?)\n```", re.DOTALL)
EXPECTED_HEADER_RE = re.compile(r"(?m)^##\s+Expected output\s*$")
# "must contain: <substring>" — backticks around the substring optional;
# we strip them. Captures everything from "must contain:" up to the
# trailing period or end of line.
MUST_CONTAIN_RE = re.compile(r"must contain:\s*(.+?)\s*\.?\s*$", re.IGNORECASE | re.MULTILINE)


def _coerce_scalar(s: str) -> str | bool | int | float:
    """Coerce a YAML-shaped scalar.

    Supported: booleans (true/false/yes/no, case-insensitive), ints,
    floats, quoted strings, bare strings. Dates are left as strings —
    the recipe-schema's ``verified_on`` field is a string pattern, and
    keeping them as strings sidesteps PyYAML's datetime auto-conversion.
    """
    s = s.strip()
    if not s:
        return ""
    # Quoted string?
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    # Booleans.
    low = s.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    # Numbers.
    if re.fullmatch(r"-?\d+", s):
        try:
            return int(s)
        except ValueError:
            pass
    if re.fullmatch(r"-?\d+\.\d+", s):
        try:
            return float(s)
        except ValueError:
            pass
    return s


def _parse_minimal_yaml(text: str) -> dict:
    """Parse the narrow YAML subset recipe frontmatter uses.

    Supports:
      ``key: value``
      ``key:`` followed by ``- value`` lines (a list)
      ``# comments`` and blank lines

    Nothing else — no nested mappings, no flow style. The recipe-schema
    contract is intentionally simple, so this 30-line parser handles
    everything frontmatter throws at it without pulling pyyaml into the
    CI dependency closure.
    """
    out: dict = {}
    current_key: str | None = None
    current_list: list | None = None
    for raw_line in text.splitlines():
        # Strip trailing whitespace + comments. Don't strip leading — we
        # need indentation for list items.
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        # Indented list item: "  - foo"
        stripped = line.lstrip()
        if stripped.startswith("- ") or stripped == "-":
            if current_list is None:
                raise ValueError(f"unexpected list item without preceding key: {raw_line!r}")
            value = stripped[1:].strip()
            if value:
                current_list.append(_coerce_scalar(value))
            continue
        # Top-level "key: value" or "key:".
        if line[0] in " \t":
            # Indented but not a list item — unsupported.
            raise ValueError(f"unexpected indented line: {raw_line!r}")
        if ":" not in line:
            raise ValueError(f"expected `key: value` or `key:`, got: {raw_line!r}")
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        # Inline comment? Strip everything from " #" onward (but only
        # outside quoted strings — the recipe contract never quotes
        # `#` so this conservative strip suffices).
        if value and " #" in value and not (value.startswith('"') or value.startswith("'")):
            value = value.split(" #", 1)[0].rstrip()
        if value == "":
            # Open list: subsequent "- " lines populate it.
            current_list = []
            out[key] = current_list
            current_key = key
        else:
            out[key] = _coerce_scalar(value)
            current_list = None
            current_key = key
    return out


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body). Raises ValueError on failure."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError("no YAML frontmatter (`---` block) at top of recipe")
    fm_text = m.group(1)
    body = m.group(2)
    try:
        fm = _parse_minimal_yaml(fm_text)
    except ValueError as exc:
        raise ValueError(f"YAML parse error in frontmatter: {exc}") from exc
    if not isinstance(fm, dict):
        raise ValueError(f"frontmatter is not a mapping: got {type(fm).__name__}")
    return fm, body


def validate_frontmatter(fm: dict) -> list[str]:
    """Validate frontmatter against recipe.schema.json. Returns list of error strings."""
    errors: list[str] = []
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        errors.append(f"jsonschema is required (pip install jsonschema): {exc}")
        return errors
    try:
        schema = json.loads(RECIPE_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot load recipe.schema.json: {exc}")
        return errors
    validator = Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(fm), key=lambda e: list(e.absolute_path)):
        path = "/".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"frontmatter: at {path}: {err.message}")
    return errors


def extract_first_bash_block_under_steps(body: str) -> str | None:
    """Find the FIRST ```bash ...``` fence appearing after a ``## Steps`` header.

    Returns the fence's body (without the fence lines), or None if no
    such block exists.
    """
    m = STEPS_HEADER_RE.search(body)
    if not m:
        return None
    region_start = m.end()
    # Cap at the next H2 header so we don't accidentally grab a fence
    # from a later section.
    nxt = NEXT_H2_RE.search(body, region_start)
    region_end = nxt.start() if nxt else len(body)
    region = body[region_start:region_end]
    fence = BASH_FENCE_RE.search(region)
    return fence.group(1) if fence else None


def extract_expected_substrings(body: str) -> list[str]:
    """Read every ``must contain: <substring>`` assertion under ``## Expected output``."""
    m = EXPECTED_HEADER_RE.search(body)
    if not m:
        return []
    region_start = m.end()
    nxt = NEXT_H2_RE.search(body, region_start)
    region_end = nxt.start() if nxt else len(body)
    region = body[region_start:region_end]
    out: list[str] = []
    for line_match in MUST_CONTAIN_RE.finditer(region):
        raw = line_match.group(1).strip()
        # Strip surrounding backticks: `0/0 failed` → 0/0 failed.
        if len(raw) >= 2 and raw[0] == "`" and raw[-1] == "`":
            raw = raw[1:-1]
        out.append(raw)
    return out


# ---- driver ----------------------------------------------------------------


def run_recipe(recipe_path: Path, validate_only: bool = False) -> int:
    # 1. Read file.
    try:
        text = recipe_path.read_text(encoding="utf-8")
    except (FileNotFoundError, IsADirectoryError) as exc:
        print(f"ERROR: cannot read recipe {recipe_path}: {exc}", file=sys.stderr)
        return EXIT_FILE_UNREADABLE
    except OSError as exc:
        print(f"ERROR: cannot read recipe {recipe_path}: {exc}", file=sys.stderr)
        return EXIT_FILE_UNREADABLE

    # 2. Parse + validate frontmatter.
    try:
        fm, body = split_frontmatter(text)
    except ValueError as exc:
        print(f"ERROR: {recipe_path}: {exc}", file=sys.stderr)
        return EXIT_FRONTMATTER_INVALID

    errors = validate_frontmatter(fm)
    if errors:
        for e in errors:
            print(f"ERROR: {recipe_path}: {e}", file=sys.stderr)
        return EXIT_FRONTMATTER_INVALID

    # 3. Manual-checklist shortcut.
    if fm.get("ci_verifiable") is False:
        url = fm.get("manual_checklist_url", "<no manual_checklist_url>")
        print(f"SKIP: {recipe_path} (manual checklist; see {url})")
        return EXIT_OK

    # 4. Extract bash block under ## Steps.
    bash_body = extract_first_bash_block_under_steps(body)
    if not bash_body:
        print(
            f"ERROR: {recipe_path}: no ```bash ...``` fence found under '## Steps'",
            file=sys.stderr,
        )
        return EXIT_FRONTMATTER_INVALID

    # 4b. --validate-only short-circuit: verify the recipe parses + has a
    # Steps block + has Expected-output assertions, but do NOT execute the
    # command sequence. Used by CI when the runner environment lacks the
    # toolchain a ci_verifiable recipe needs (m-cli, m-test-engine, …).
    # Full executable verification is a maintainer's responsibility when
    # bumping `verified_on`, plus a future scheduled CI job that
    # bootstraps the toolchain.
    if validate_only:
        expected = extract_expected_substrings(body)
        if not expected:
            print(
                f"ERROR: {recipe_path}: ci_verifiable: true recipe must declare "
                f"at least one 'must contain: …' assertion under '## Expected output'",
                file=sys.stderr,
            )
            return EXIT_FRONTMATTER_INVALID
        print(f"VALIDATE: {recipe_path} (frontmatter + steps + {len(expected)} assertions OK)")
        return EXIT_OK

    # 5–6. mktemp -d, run.
    tmpdir = Path(tempfile.mkdtemp(prefix="recipe-"))
    try:
        try:
            result = subprocess.run(
                ["bash", "-c", "set -e\n" + bash_body],
                capture_output=True,
                text=True,
                cwd=tmpdir,
                timeout=600,
            )
        except subprocess.TimeoutExpired as exc:
            print(f"ERROR: {recipe_path}: command sequence timed out: {exc}", file=sys.stderr)
            return EXIT_COMMAND_FAILED

        if result.returncode != 0:
            print(
                f"ERROR: {recipe_path}: command sequence exited "
                f"non-zero (rc={result.returncode})",
                file=sys.stderr,
            )
            if result.stdout.strip():
                print("--- captured stdout ---", file=sys.stderr)
                print(result.stdout, file=sys.stderr)
            if result.stderr.strip():
                print("--- captured stderr ---", file=sys.stderr)
                print(result.stderr, file=sys.stderr)
            return EXIT_COMMAND_FAILED

        # 7. Verify expected-output substring assertions.
        expected = extract_expected_substrings(body)
        if not expected:
            # No assertions = nothing to verify. Treat as success.
            print(f"OK: {recipe_path}")
            return EXIT_OK

        captured = result.stdout
        missing = [s for s in expected if s not in captured]
        if missing:
            print(
                f"ERROR: {recipe_path}: expected substring(s) not found in stdout:",
                file=sys.stderr,
            )
            for m in missing:
                print(f"  missing: {m!r}", file=sys.stderr)
            print("--- captured stdout ---", file=sys.stderr)
            print(captured, file=sys.stderr)
            return EXIT_EXPECTED_MISSING

        print(f"OK: {recipe_path}")
        return EXIT_OK

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    parser.add_argument("recipe", type=Path, help="Path to the recipe Markdown file.")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help=(
            "Validate frontmatter, Steps block presence, and "
            "Expected-output assertions without executing the recipe. "
            "Used by CI environments that lack the runtime toolchain "
            "(m-cli, m-test-engine, …) the recipe needs."
        ),
    )
    args = parser.parse_args(argv)
    return run_recipe(args.recipe, validate_only=args.validate_only)


if __name__ == "__main__":
    raise SystemExit(main())
