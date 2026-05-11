#!/usr/bin/env python3
"""Phase 5 Track A — freshness gate over ``verified_on`` fields.

Walks two sources:

* ``profile/tools.json`` — each ``tools.<key>.verified_on`` field.
* ``docs/recipes/*.md`` — each recipe's frontmatter ``verified_on``.

Per entry, classifies the age:

  OK       — age <= warn_days
  WARN     — warn_days < age <= stale_days
  STALE    — age > stale_days
  MISSING  — verified_on field absent
  INVALID  — verified_on not parseable as YYYY-MM-DD

Aggregator status is the worst row's status, ranked
``STALE > MISSING > INVALID > WARN > OK`` (per phase5-plan.md §9
risk note "prefer false negatives over false positives" — STALE is
the strongest fix-now signal).

Output: a Markdown table per source, sorted worst-first.

CLI exit codes:

  0  — pass (no STALE/MISSING/INVALID by default; WARN allowed unless --strict)
  1  — gate failed
  2  — fixture/network failure (reserved; not raised in offline mode)

Default thresholds: ``--warn-days 90 --stale-days 180`` (90/180 from
phase5-plan.md §2 A2 — tunable per invocation; the Makefile target
uses the defaults).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE = REPO_ROOT / "profile"
DEFAULT_TOOLS_JSON = PROFILE / "tools.json"
DEFAULT_RECIPES_DIR = REPO_ROOT / "docs" / "recipes"

# Status priority for aggregator + sort (lower = better, higher = worse).
STATUS_PRIORITY = {
    "OK": 0,
    "WARN": 1,
    "INVALID": 2,
    "MISSING": 3,
    "STALE": 4,
}

# YAML frontmatter parser is intentionally minimal — same trick
# run-recipe.py uses. Recipes only need `id` + `verified_on`, both
# scalar strings.
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n", re.DOTALL)
_VERIFIED_ON_RE = re.compile(r"^\s*verified_on:\s*\"?([0-9-]+)\"?\s*$", re.MULTILINE)
_ID_RE = re.compile(r"^\s*id:\s*([^\s]+)\s*$", re.MULTILINE)


# ---- pure classification core ----------------------------------------------


def _parse_verified_on(value: str | None) -> date | None:
    if value is None:
        return None
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"invalid verified_on: {value!r}")
    return datetime.strptime(value, "%Y-%m-%d").date()


def _classify(age_days: int, warn_days: int, stale_days: int) -> str:
    if age_days > stale_days:
        return "STALE"
    if age_days > warn_days:
        return "WARN"
    return "OK"


def check_freshness_impl(
    entries: list[dict[str, Any]],
    today: date,
    warn_days: int,
    stale_days: int,
) -> tuple[list[dict[str, Any]], str]:
    """Pure-function freshness classifier.

    Returns ``(rows, worst_status)`` where ``rows`` is the input
    augmented with ``status`` + ``age_days`` (None on MISSING/INVALID),
    sorted worst-first.
    """
    rows: list[dict[str, Any]] = []
    for entry in entries:
        row = dict(entry)
        raw = entry.get("verified_on")
        if raw is None:
            row["status"] = "MISSING"
            row["age_days"] = None
        else:
            try:
                parsed = _parse_verified_on(raw)
            except ValueError:
                row["status"] = "INVALID"
                row["age_days"] = None
            else:
                assert parsed is not None
                age = (today - parsed).days
                row["age_days"] = age
                row["status"] = _classify(age, warn_days, stale_days)
        rows.append(row)

    rows.sort(
        key=lambda r: (
            -STATUS_PRIORITY.get(r["status"], 0),  # worst-first
            -(r["age_days"] or 0),                  # then oldest-first
            r.get("id", ""),
        )
    )
    worst = "OK"
    for r in rows:
        if STATUS_PRIORITY[r["status"]] > STATUS_PRIORITY[worst]:
            worst = r["status"]
    return rows, worst


# ---- ingest helpers --------------------------------------------------------


def entries_from_tools_json(tools: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract one entry per tools.<key>.

    The catalog's per-tool entries carry ``id`` and ``verified_on``.
    """
    out: list[dict[str, Any]] = []
    tools_map = tools.get("tools", {})
    if not isinstance(tools_map, dict):
        return out
    for key, entry in tools_map.items():
        if not isinstance(entry, dict):
            continue
        row: dict[str, Any] = {"id": entry.get("id") or f"tool:{key}"}
        if "verified_on" in entry:
            row["verified_on"] = entry["verified_on"]
        out.append(row)
    return out


def entries_from_recipes_dir(recipes_dir: Path) -> list[dict[str, Any]]:
    """Walk every ``.md`` file under ``recipes_dir`` (except README.md),
    parse frontmatter, and emit ``{id, verified_on}`` rows."""
    out: list[dict[str, Any]] = []
    if not recipes_dir.is_dir():
        return out
    for path in sorted(recipes_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        m = _FRONTMATTER_RE.match(text)
        if not m:
            continue
        fm = m.group(1)
        id_match = _ID_RE.search(fm)
        verified_match = _VERIFIED_ON_RE.search(fm)
        row: dict[str, Any] = {
            "id": id_match.group(1) if id_match else f"recipe:{path.stem}",
        }
        if verified_match:
            row["verified_on"] = verified_match.group(1)
        out.append(row)
    return out


# ---- table formatting -------------------------------------------------------


def format_table(title: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return f"### {title}\n\n(no entries)\n"
    lines = [f"### {title}", "", "| status | id | verified_on | age_days |", "|---|---|---|---|"]
    for r in rows:
        v = r.get("verified_on", "—")
        a = r.get("age_days")
        a_text = "—" if a is None else str(a)
        lines.append(f"| {r['status']} | `{r['id']}` | {v} | {a_text} |")
    lines.append("")
    return "\n".join(lines)


# ---- CLI -------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Freshness gate over verified_on fields in the catalog + recipes."
    )
    parser.add_argument(
        "--tools-json",
        type=Path,
        default=DEFAULT_TOOLS_JSON,
        help="Path to profile/tools.json (default: repo's committed copy).",
    )
    parser.add_argument(
        "--recipes-dir",
        type=Path,
        default=DEFAULT_RECIPES_DIR,
        help="Path to docs/recipes/ (default: repo's committed dir).",
    )
    parser.add_argument(
        "--warn-days",
        type=int,
        default=90,
        help="Age above this (and below --stale-days) emits WARN.",
    )
    parser.add_argument(
        "--stale-days",
        type=int,
        default=180,
        help="Age above this emits STALE.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat WARN as failure (exit 1). Default: only STALE/MISSING/INVALID fail.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help=(
            "Don't fetch upstream repo.meta.json — rely on the verified_on "
            "field already on the catalog entry. Currently the only mode "
            "implemented; reserved flag for symmetry with link-check/license-reconcile."
        ),
    )
    parser.add_argument(
        "--today",
        type=str,
        help="Override 'today' as YYYY-MM-DD (test/fixture use).",
    )
    args = parser.parse_args(argv)

    today = date.today() if not args.today else datetime.strptime(args.today, "%Y-%m-%d").date()

    try:
        tools = json.loads(args.tools_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read {args.tools_json}: {exc}", file=sys.stderr)
        return 2

    catalog_entries = entries_from_tools_json(tools)
    recipe_entries = entries_from_recipes_dir(args.recipes_dir)

    catalog_rows, catalog_worst = check_freshness_impl(
        catalog_entries, today=today, warn_days=args.warn_days, stale_days=args.stale_days
    )
    recipe_rows, recipe_worst = check_freshness_impl(
        recipe_entries, today=today, warn_days=args.warn_days, stale_days=args.stale_days
    )

    print(format_table("Catalog (tools.json)", catalog_rows))
    print(format_table("Recipes (docs/recipes/)", recipe_rows))

    overall = max(
        (catalog_worst, recipe_worst),
        key=lambda s: STATUS_PRIORITY[s],
    )
    fail_statuses = {"STALE", "MISSING", "INVALID"}
    if args.strict:
        fail_statuses.add("WARN")

    if overall in fail_statuses:
        print(f"check-freshness: FAIL (worst={overall})", file=sys.stderr)
        return 1
    print(f"check-freshness: clean (worst={overall})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
