#!/usr/bin/env python3
"""Validate AI discoverability tracking docs.

This intentionally avoids third-party dependencies so it can run in CI, hooks,
or an AI agent workspace with only Python available.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TRACKING = ROOT / "docs" / "ai-discoverability"
PROFILE = ROOT / "profile"

VALID_STATUSES = {
    "todo",
    "doing",
    "blocked",
    "review",
    "done",
    "deferred",
    "superseded",
}

REQUIRED_FILES = [
    TRACKING / "README.md",
    TRACKING / "how-to-track.md",
    TRACKING / "roadmap.md",
    TRACKING / "implementation-tracker.md",
    TRACKING / "repo-inventory.md",
    TRACKING / "decisions.md",
    TRACKING / "discoveries.md",
    TRACKING / "remediation-backlog.md",
    TRACKING / "schema-changelog.md",
    TRACKING / "release-checklist.md",
    PROFILE / "llms.txt",
    PROFILE / "tools.json",
    PROFILE / "tools.schema.json",
]

ID_RE = re.compile(r"\b(AI|DISC|REM|ADR|SCH)-(\d{3})\b")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_markdown_table(path: Path, required_headers: list[str]) -> list[dict[str, str]]:
    """Return rows from the first markdown table containing required headers."""
    lines = read(path).splitlines()
    for idx, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        headers = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not all(header in headers for header in required_headers):
            continue
        if idx + 1 >= len(lines) or not lines[idx + 1].startswith("|"):
            continue
        rows: list[dict[str, str]] = []
        for row_line in lines[idx + 2 :]:
            if not row_line.startswith("|"):
                break
            cells = [cell.strip() for cell in row_line.strip().strip("|").split("|")]
            if len(cells) != len(headers):
                continue
            rows.append(dict(zip(headers, cells)))
        return rows
    return []


def collect_defined_ids(errors: list[str]) -> dict[str, set[str]]:
    defined: dict[str, set[str]] = {prefix: set() for prefix in ["AI", "DISC", "REM", "ADR", "SCH"]}

    task_rows = parse_markdown_table(
        TRACKING / "implementation-tracker.md",
        ["ID", "Phase", "Workstream", "Task", "Owner Repo", "Status", "Blocks", "Outputs", "Verification"],
    )
    for row in task_rows:
        task_id = row["ID"]
        if not re.fullmatch(r"AI-\d{3}", task_id):
            fail(errors, f"implementation-tracker.md has invalid task ID: {task_id}")
            continue
        if task_id in defined["AI"]:
            fail(errors, f"duplicate task ID: {task_id}")
        defined["AI"].add(task_id)

        status = row["Status"]
        if status not in VALID_STATUSES:
            fail(errors, f"{task_id} has invalid status: {status}")
        if status == "blocked" and not row["Blocks"]:
            fail(errors, f"{task_id} is blocked but has empty Blocks column")
        if status == "done":
            if not row["Outputs"]:
                fail(errors, f"{task_id} is done but has empty Outputs column")
            if not row["Verification"]:
                fail(errors, f"{task_id} is done but has empty Verification column")

    if not task_rows:
        fail(errors, "implementation-tracker.md task table not found")

    rem_rows = parse_markdown_table(
        TRACKING / "remediation-backlog.md",
        ["ID", "Source", "Repo", "Problem", "Proposed Fix", "Status", "Required For"],
    )
    for row in rem_rows:
        rem_id = row["ID"]
        if not re.fullmatch(r"REM-\d{3}", rem_id):
            fail(errors, f"remediation-backlog.md has invalid remediation ID: {rem_id}")
            continue
        if rem_id in defined["REM"]:
            fail(errors, f"duplicate remediation ID: {rem_id}")
        defined["REM"].add(rem_id)
        if row["Status"] not in VALID_STATUSES:
            fail(errors, f"{rem_id} has invalid status: {row['Status']}")

    discoveries = read(TRACKING / "discoveries.md")
    for match in re.finditer(r"^## (DISC-\d{3}):", discoveries, re.MULTILINE):
        disc_id = match.group(1)
        if disc_id in defined["DISC"]:
            fail(errors, f"duplicate discovery ID: {disc_id}")
        defined["DISC"].add(disc_id)

    decisions = read(TRACKING / "decisions.md")
    for match in re.finditer(r"^## (ADR-\d{3}):", decisions, re.MULTILINE):
        adr_id = match.group(1)
        if adr_id in defined["ADR"]:
            fail(errors, f"duplicate decision ID: {adr_id}")
        defined["ADR"].add(adr_id)

    schema_rows = parse_markdown_table(
        TRACKING / "schema-changelog.md",
        ["ID", "Date", "Contract", "Change", "Compatibility", "Related"],
    )
    for row in schema_rows:
        sch_id = row["ID"]
        if not re.fullmatch(r"SCH-\d{3}", sch_id):
            fail(errors, f"schema-changelog.md has invalid schema change ID: {sch_id}")
            continue
        if sch_id in defined["SCH"]:
            fail(errors, f"duplicate schema change ID: {sch_id}")
        defined["SCH"].add(sch_id)
        if row["Compatibility"] not in {"additive", "breaking", "clarification", "deprecated"}:
            fail(errors, f"{sch_id} has invalid compatibility: {row['Compatibility']}")

    return defined


def validate_references(errors: list[str], defined: dict[str, set[str]]) -> None:
    all_text = "\n".join(read(path) for path in TRACKING.rglob("*.md"))
    for prefix, number in ID_RE.findall(all_text):
        if number == "000":
            continue
        ref = f"{prefix}-{number}"
        if ref not in defined[prefix]:
            fail(errors, f"reference to undefined ID: {ref}")

    rem_rows = parse_markdown_table(
        TRACKING / "remediation-backlog.md",
        ["ID", "Source", "Repo", "Problem", "Proposed Fix", "Status", "Required For"],
    )
    for row in rem_rows:
        rem_id = row["ID"]
        source = row["Source"]
        if re.fullmatch(r"DISC-\d{3}", source) and source not in defined["DISC"]:
            fail(errors, f"{rem_id} references missing discovery source {source}")

    schema_rows = parse_markdown_table(
        TRACKING / "schema-changelog.md",
        ["ID", "Date", "Contract", "Change", "Compatibility", "Related"],
    )
    for row in schema_rows:
        related_ids = [f"{prefix}-{number}" for prefix, number in ID_RE.findall(row["Related"])]
        if not related_ids:
            fail(errors, f"{row['ID']} has no related ID")


def validate_json(errors: list[str]) -> None:
    for path in [PROFILE / "tools.json", PROFILE / "tools.schema.json"]:
        try:
            json.loads(read(path))
        except json.JSONDecodeError as exc:
            fail(errors, f"{path.relative_to(ROOT)} is invalid JSON: {exc}")


def validate_required_files(errors: list[str]) -> None:
    for path in REQUIRED_FILES:
        if not path.exists():
            fail(errors, f"required file missing: {path.relative_to(ROOT)}")


def main() -> int:
    errors: list[str] = []
    validate_required_files(errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    validate_json(errors)
    defined = collect_defined_ids(errors)
    validate_references(errors, defined)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("AI discoverability tracking validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
