"""Tests for check-licenses.py — Phase 5 Track C1 (RED) before C2 (GREEN).

Tests target the pure-function classifier + the catalog walker.
Network is mocked via ``urllib.request.urlopen`` patches so the suite
stays offline.
"""

from __future__ import annotations

import importlib.util
import json
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD = REPO_ROOT / "profile" / "build"

_path = BUILD / "check-licenses.py"
_spec = importlib.util.spec_from_file_location("_check_licenses", _path)
_check_licenses = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_check_licenses)


# ----- canonical-text fixtures (excerpts long enough to trip 2+ markers) -----

AGPL_BODY = """\
                    GNU AFFERO GENERAL PUBLIC LICENSE
                       Version 3, 19 November 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

                            Preamble

  The GNU Affero General Public License is a free, copyleft license
for software and other kinds of works...
"""

GPL_BODY = """\
                    GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

                            Preamble

  The GNU General Public License is a free, copyleft license for
software and other kinds of works.
"""

MIT_BODY = """\
MIT License

Copyright (c) 2026 m-dev-tools

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
"""

APACHE_BODY = """\
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.
   ...
"""


# ----------------------------------------------- identify_license signature


def test_identify_agpl_text() -> None:
    assert _check_licenses.identify_license(AGPL_BODY) == "AGPL-3.0"


def test_identify_gpl_text_distinguished_from_agpl() -> None:
    """GPL-3.0 must NOT match AGPL-3.0 — the "AFFERO" marker is what
    separates them. Critical because both share the "GENERAL PUBLIC
    LICENSE" + "Version 3" phrasing."""
    assert _check_licenses.identify_license(GPL_BODY) == "GPL-3.0"


def test_identify_mit_text() -> None:
    assert _check_licenses.identify_license(MIT_BODY) == "MIT"


def test_identify_apache_text() -> None:
    assert _check_licenses.identify_license(APACHE_BODY) == "Apache-2.0"


def test_identify_unknown_text_returns_none() -> None:
    """Defensive: a random license blob the matcher doesn't recognize
    returns None so the caller can surface UNKNOWN rather than guess."""
    assert _check_licenses.identify_license("custom proprietary notice\n") is None


def test_identify_requires_two_markers() -> None:
    """Per plan §9, prefer false negatives over false positives. A
    text containing exactly ONE AGPL marker (e.g. only "Affero" in a
    sentence elsewhere) must NOT match."""
    one_marker = "This file refers to Affero in passing.\n"
    assert _check_licenses.identify_license(one_marker) is None


# ----------------------------------------------- check_one classification


def test_check_one_declared_agpl_file_matches() -> None:
    result = _check_licenses.check_one(
        slug="m-cli",
        declared="AGPL-3.0",
        license_body=AGPL_BODY,
    )
    assert result["status"] == "OK"
    assert result["declared"] == "AGPL-3.0"
    assert result["detected"] == "AGPL-3.0"


def test_check_one_declared_agpl_file_is_mit_is_mismatch() -> None:
    result = _check_licenses.check_one(
        slug="m-cli",
        declared="AGPL-3.0",
        license_body=MIT_BODY,
    )
    assert result["status"] == "MISMATCH"
    assert result["detected"] == "MIT"


def test_check_one_missing_file_is_missing() -> None:
    result = _check_licenses.check_one(
        slug="m-cli",
        declared="AGPL-3.0",
        license_body=None,
    )
    assert result["status"] == "MISSING"
    assert result["detected"] is None


def test_check_one_mit_declared_mit_file_ok() -> None:
    """Proves the matcher isn't hard-coded to AGPL."""
    result = _check_licenses.check_one(
        slug="m-stdlib-vscode",
        declared="MIT",
        license_body=MIT_BODY,
    )
    assert result["status"] == "OK"


def test_check_one_skip_for_mixed_per_subdir() -> None:
    """The m-modern-corpus declared license is
    ``LicenseRef-mixed-per-subdir``. Per the plan: SKIP with a
    documented reason, not an error."""
    result = _check_licenses.check_one(
        slug="m-modern-corpus",
        declared="LicenseRef-mixed-per-subdir",
        license_body=None,  # file may or may not exist; SKIP either way
    )
    assert result["status"] == "SKIP"
    assert "per-subdir" in result.get("reason", "").lower()


def test_check_one_unknown_declared_is_skip() -> None:
    """If a repo declares a license that's outside the known-signature
    set, SKIP (not MISMATCH) — we don't have the signature to verify
    against, but the declaration itself isn't a bug."""
    result = _check_licenses.check_one(
        slug="weird-thing",
        declared="WTFPL",
        license_body=AGPL_BODY,
    )
    assert result["status"] == "SKIP"


# ----------------------------------------------- driver / CLI


def test_check_licenses_impl_aggregates_worst() -> None:
    """Driver aggregates per-tool results; worst surfaces first."""
    rows, worst = _check_licenses.check_licenses_impl(
        [
            {"slug": "m-cli", "declared": "AGPL-3.0", "license_body": AGPL_BODY},
            {"slug": "m-stdlib-vscode", "declared": "MIT", "license_body": MIT_BODY},
            {"slug": "m-modern-corpus", "declared": "LicenseRef-mixed-per-subdir",
             "license_body": None},
            {"slug": "broken", "declared": "AGPL-3.0", "license_body": MIT_BODY},
        ]
    )
    assert worst == "MISMATCH"
    assert rows[0]["slug"] == "broken"
    assert rows[0]["status"] == "MISSING" or rows[0]["status"] == "MISMATCH"


def test_check_licenses_impl_all_ok() -> None:
    rows, worst = _check_licenses.check_licenses_impl(
        [
            {"slug": "m-cli", "declared": "AGPL-3.0", "license_body": AGPL_BODY},
            {"slug": "m-stdlib-vscode", "declared": "MIT", "license_body": MIT_BODY},
        ]
    )
    assert worst == "OK"
    assert all(r["status"] == "OK" for r in rows)


def test_cli_offline_validates_declared_field_only(tmp_path, capsys) -> None:
    """--offline must NOT touch the network. The mode only sanity-
    checks that the declared `license` field is in our known set."""
    tools = {
        "tools": {
            "m-cli": {"id": "tool:m-cli", "license": "AGPL-3.0", "repo": "https://github.com/m-dev-tools/m-cli"},
            "m-stdlib-vscode": {"id": "tool:m-stdlib-vscode", "license": "MIT", "repo": "https://github.com/m-dev-tools/m-stdlib-vscode"},
            "m-modern-corpus": {"id": "tool:m-modern-corpus", "license": "LicenseRef-mixed-per-subdir", "repo": "https://github.com/m-dev-tools/m-modern-corpus"},
        }
    }
    tools_path = tmp_path / "tools.json"
    tools_path.write_text(json.dumps(tools), encoding="utf-8")

    with patch(
        "urllib.request.urlopen",
        side_effect=AssertionError("network must not be touched in --offline mode"),
    ):
        rc = _check_licenses.main(["--offline", "--tools-json", str(tools_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "AGPL-3.0" in out
    assert "MIT" in out
    # Known declared licenses surface as INVENTORIED (not MISSING) in
    # offline mode — file-fetch deferred to the cron firing.
    assert "INVENTORIED" in out
    # m-modern-corpus's LicenseRef-mixed-per-subdir stays SKIP either way.
    assert "SKIP" in out


def test_cli_full_fetch_finds_mismatch(tmp_path) -> None:
    """Full-fetch mode: declared AGPL + LICENSE file body is MIT →
    MISMATCH → rc=1."""
    tools = {
        "tools": {
            "lying": {
                "id": "tool:lying",
                "license": "AGPL-3.0",
                "repo": "https://github.com/m-dev-tools/lying",
            }
        }
    }
    tools_path = tmp_path / "tools.json"
    tools_path.write_text(json.dumps(tools), encoding="utf-8")

    resp = MagicMock()
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    resp.read = MagicMock(return_value=MIT_BODY.encode("utf-8"))
    resp.status = 200

    with patch("urllib.request.urlopen", return_value=resp):
        rc = _check_licenses.main(["--tools-json", str(tools_path)])
    assert rc == 1


def test_cli_full_fetch_all_ok(tmp_path) -> None:
    """Full-fetch mode: declared AGPL + LICENSE file is AGPL → OK → rc=0."""
    tools = {
        "tools": {
            "honest": {
                "id": "tool:honest",
                "license": "AGPL-3.0",
                "repo": "https://github.com/m-dev-tools/honest",
            }
        }
    }
    tools_path = tmp_path / "tools.json"
    tools_path.write_text(json.dumps(tools), encoding="utf-8")

    resp = MagicMock()
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    resp.read = MagicMock(return_value=AGPL_BODY.encode("utf-8"))
    resp.status = 200

    with patch("urllib.request.urlopen", return_value=resp):
        rc = _check_licenses.main(["--tools-json", str(tools_path)])
    assert rc == 0


def test_cli_missing_license_file_reports_missing(tmp_path) -> None:
    """A 404 on the LICENSE file → MISSING → rc=1."""
    tools = {
        "tools": {
            "nofile": {
                "id": "tool:nofile",
                "license": "AGPL-3.0",
                "repo": "https://github.com/m-dev-tools/nofile",
            }
        }
    }
    tools_path = tmp_path / "tools.json"
    tools_path.write_text(json.dumps(tools), encoding="utf-8")

    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.HTTPError(
            "https://example.invalid/LICENSE", 404, "Not Found", hdrs={}, fp=None
        ),
    ):
        rc = _check_licenses.main(["--tools-json", str(tools_path)])
    assert rc == 1
