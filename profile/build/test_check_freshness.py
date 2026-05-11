"""Tests for check-freshness.py — Phase 5 Track A1 (RED) before A2 (GREEN).

Strategy: exercise the pure function
``check_freshness_impl(entries, today, warn_days, stale_days) ->
(rows, worst_status)`` directly, plus a few CLI-level exit-code
assertions for the wrapper. The pure function takes a list of
``{"id": str, "verified_on": str | None}`` dicts; the CLI builds
that list from the catalog + recipes.

Status taxonomy (per phase5-plan.md §2 A1):

  OK       — age <= warn_days
  WARN     — warn_days < age <= stale_days (default 90 < age <= 180)
  STALE    — age > stale_days
  MISSING  — verified_on field absent
  INVALID  — verified_on present but not YYYY-MM-DD

Aggregator status is the worst row's status. Sort order in the
output is worst-first.
"""

from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD = REPO_ROOT / "profile" / "build"

_path = BUILD / "check-freshness.py"
_spec = importlib.util.spec_from_file_location("_check_freshness", _path)
_check_freshness = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_check_freshness)


TODAY = date(2026, 5, 11)


# --------------------------------------------------------------- pure function


def test_status_ok_for_today() -> None:
    rows, worst = _check_freshness.check_freshness_impl(
        [{"id": "tool:m-cli", "verified_on": "2026-05-11"}],
        today=TODAY,
        warn_days=90,
        stale_days=180,
    )
    assert rows[0]["status"] == "OK"
    assert rows[0]["age_days"] == 0
    assert worst == "OK"


def test_status_ok_at_warn_boundary() -> None:
    """At exactly warn_days, still OK — the threshold is exclusive."""
    rows, worst = _check_freshness.check_freshness_impl(
        [{"id": "tool:m-cli", "verified_on": "2026-02-10"}],  # 90 days ago
        today=TODAY,
        warn_days=90,
        stale_days=180,
    )
    assert rows[0]["age_days"] == 90
    assert rows[0]["status"] == "OK"
    assert worst == "OK"


def test_status_warn_past_threshold() -> None:
    rows, worst = _check_freshness.check_freshness_impl(
        [{"id": "tool:m-cli", "verified_on": "2026-02-09"}],  # 91 days ago
        today=TODAY,
        warn_days=90,
        stale_days=180,
    )
    assert rows[0]["age_days"] == 91
    assert rows[0]["status"] == "WARN"
    assert worst == "WARN"


def test_status_stale_past_threshold() -> None:
    rows, worst = _check_freshness.check_freshness_impl(
        [{"id": "tool:m-cli", "verified_on": "2025-11-11"}],  # 181 days ago
        today=TODAY,
        warn_days=90,
        stale_days=180,
    )
    assert rows[0]["age_days"] == 181
    assert rows[0]["status"] == "STALE"
    assert worst == "STALE"


def test_status_missing_verified_on() -> None:
    rows, worst = _check_freshness.check_freshness_impl(
        [{"id": "tool:m-cli"}],  # no verified_on at all
        today=TODAY,
        warn_days=90,
        stale_days=180,
    )
    assert rows[0]["status"] == "MISSING"
    assert rows[0]["age_days"] is None
    assert worst == "MISSING"


def test_status_invalid_format() -> None:
    rows, worst = _check_freshness.check_freshness_impl(
        [{"id": "tool:m-cli", "verified_on": "2026/05/11"}],  # wrong separators
        today=TODAY,
        warn_days=90,
        stale_days=180,
    )
    assert rows[0]["status"] == "INVALID"
    assert rows[0]["age_days"] is None
    assert worst == "INVALID"


def test_aggregator_picks_worst_status() -> None:
    """Worst status is STALE > INVALID/MISSING > WARN > OK. STALE
    must surface to the top of the rows list."""
    rows, worst = _check_freshness.check_freshness_impl(
        [
            {"id": "tool:fresh", "verified_on": "2026-05-11"},  # OK
            {"id": "tool:warn", "verified_on": "2026-02-09"},   # WARN
            {"id": "tool:old", "verified_on": "2025-11-11"},    # STALE
            {"id": "tool:none"},                                # MISSING
        ],
        today=TODAY,
        warn_days=90,
        stale_days=180,
    )
    assert worst == "STALE"
    # Worst-first sort order
    assert rows[0]["id"] == "tool:old"
    assert rows[0]["status"] == "STALE"
    # OK entries come last
    assert rows[-1]["id"] == "tool:fresh"
    assert rows[-1]["status"] == "OK"


def test_status_priority_invalid_outranks_warn_but_not_stale() -> None:
    """INVALID is worse than WARN but better than STALE for the
    aggregator. (A bogus date string is a real bug worth flagging,
    but a stale-but-parseable date is still a stronger 'fix this now'
    signal.)"""
    _, worst1 = _check_freshness.check_freshness_impl(
        [
            {"id": "tool:warn", "verified_on": "2026-02-09"},
            {"id": "tool:bad", "verified_on": "garbage"},
        ],
        today=TODAY, warn_days=90, stale_days=180,
    )
    assert worst1 == "INVALID"

    _, worst2 = _check_freshness.check_freshness_impl(
        [
            {"id": "tool:bad", "verified_on": "garbage"},
            {"id": "tool:old", "verified_on": "2025-11-11"},
        ],
        today=TODAY, warn_days=90, stale_days=180,
    )
    assert worst2 == "STALE"


def test_empty_input_yields_OK() -> None:
    """No entries to check → OK by convention (no-op gate)."""
    rows, worst = _check_freshness.check_freshness_impl(
        [], today=TODAY, warn_days=90, stale_days=180,
    )
    assert rows == []
    assert worst == "OK"


# ------------------------------------------------------------------- ingest


def test_ingest_from_tools_json_extracts_verified_on(tmp_path: Path) -> None:
    """Catalog walker reads tools.<key>.verified_on for each entry,
    using the catalog id (or synthesized tool:<key>) as the row id."""
    tools = {
        "tools": {
            "m-cli": {"id": "tool:m-cli", "verified_on": "2026-05-11"},
            "m-stdlib": {"id": "tool:m-stdlib"},  # missing verified_on
        }
    }
    entries = _check_freshness.entries_from_tools_json(tools)
    by_id = {e["id"]: e for e in entries}
    assert by_id["tool:m-cli"]["verified_on"] == "2026-05-11"
    assert "verified_on" not in by_id["tool:m-stdlib"]


def test_ingest_from_recipes_parses_frontmatter(tmp_path: Path) -> None:
    """Recipe walker reads frontmatter's id + verified_on."""
    rdir = tmp_path / "recipes"
    rdir.mkdir()
    (rdir / "new-app-tdd-ci.md").write_text(
        "---\n"
        "id: recipe:new-app-tdd-ci\n"
        "title: scaffold demo\n"
        "intent: scaffold an app\n"
        "verified_on: \"2026-05-11\"\n"
        "ci_verifiable: true\n"
        "tier: tier-1\n"
        "---\n\n"
        "# body\n",
        encoding="utf-8",
    )
    entries = _check_freshness.entries_from_recipes_dir(rdir)
    assert len(entries) == 1
    assert entries[0]["id"] == "recipe:new-app-tdd-ci"
    assert entries[0]["verified_on"] == "2026-05-11"


def test_ingest_recipes_ignores_readme(tmp_path: Path) -> None:
    rdir = tmp_path / "recipes"
    rdir.mkdir()
    (rdir / "README.md").write_text("# overview\n", encoding="utf-8")
    (rdir / "real-recipe.md").write_text(
        "---\nid: recipe:demo\nverified_on: \"2026-05-11\"\n---\n",
        encoding="utf-8",
    )
    entries = _check_freshness.entries_from_recipes_dir(rdir)
    assert len(entries) == 1
    assert entries[0]["id"] == "recipe:demo"


# ------------------------------------------------------------------ CLI


def test_cli_exit_0_on_committed_catalog(capsys) -> None:
    """Smoke against the real catalog — should be all-OK or
    OK-with-WARN as long as nothing's STALE on `main`."""
    rc = _check_freshness.main(["--offline"])
    captured = capsys.readouterr()
    # On a fresh PR day, every entry is OK or close to it.
    # Allow rc=0 (default) and rc=1 only if the WARN-as-error flag
    # is on (not the default).
    assert rc == 0, (
        f"committed catalog should pass freshness with defaults; "
        f"rc={rc}\n{captured.out}"
    )


def test_cli_strict_promotes_warn_to_failure(tmp_path: Path) -> None:
    """--strict should additionally fail on WARN entries. Tested via
    a fixture catalog so the assertion is deterministic regardless of
    the real catalog's age."""
    tools = {
        "tools": {
            "stale-thing": {
                "id": "tool:stale-thing",
                "verified_on": "2025-11-11",  # 181 days old vs TODAY
            }
        }
    }
    fixture = tmp_path / "tools.json"
    fixture.write_text(__import__("json").dumps(tools), encoding="utf-8")

    rc_default = _check_freshness.main([
        "--offline",
        "--tools-json", str(fixture),
        "--recipes-dir", str(tmp_path / "no-such"),
        "--today", "2026-05-11",
    ])
    assert rc_default == 1, "STALE entries fail without --strict too"

    rc_strict = _check_freshness.main([
        "--offline",
        "--strict",
        "--tools-json", str(fixture),
        "--recipes-dir", str(tmp_path / "no-such"),
        "--today", "2026-05-11",
    ])
    assert rc_strict == 1


def test_cli_warn_only_passes_without_strict(tmp_path: Path) -> None:
    """Defaults: WARN doesn't fail; --strict makes it fail."""
    tools = {
        "tools": {
            "warn-thing": {
                "id": "tool:warn-thing",
                "verified_on": "2026-02-09",  # 91 days old → WARN
            }
        }
    }
    fixture = tmp_path / "tools.json"
    fixture.write_text(__import__("json").dumps(tools), encoding="utf-8")

    rc_default = _check_freshness.main([
        "--offline",
        "--tools-json", str(fixture),
        "--recipes-dir", str(tmp_path / "no-such"),
        "--today", "2026-05-11",
    ])
    assert rc_default == 0, "WARN doesn't fail by default"

    rc_strict = _check_freshness.main([
        "--offline",
        "--strict",
        "--tools-json", str(fixture),
        "--recipes-dir", str(tmp_path / "no-such"),
        "--today", "2026-05-11",
    ])
    assert rc_strict == 1, "--strict promotes WARN to failure"
