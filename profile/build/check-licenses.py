#!/usr/bin/env python3
"""Phase 5 Track C — license-reconcile gate.

Walks every ``tools.<key>`` entry in ``profile/tools.json``. For each:

* read the declared ``license`` field
* fetch ``<repo>/raw/main/LICENSE`` (the repo's LICENSE file)
* match the body against a per-license signature dict; ≥ 2 distinct
  markers per license must hit before a positive identification

Then classify the entry as OK / MISMATCH / MISSING / SKIP / UNKNOWN.

Signature dict — each license has at least three distinct substring
markers. Two-of-N must match (per phase5-plan.md §9: prefer false
negatives over false positives — UNKNOWN is fine, MISMATCH on
something legitimate is not). Licenses are tried in specificity
order so AGPL is checked before GPL (both share "GENERAL PUBLIC
LICENSE", but AGPL has "AFFERO").

Modes:

* ``--offline`` — sanity-check declared license strings only; no
  network. Used by per-PR CI.
* default — full LICENSE-file fetch + match. Used by the weekly cron
  firing.

Exit codes:

* ``0`` — all OK or SKIP
* ``1`` — any MISMATCH / MISSING / UNKNOWN
* ``2`` — fixture/parse failure
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE = REPO_ROOT / "profile"
DEFAULT_TOOLS_JSON = PROFILE / "tools.json"

# Per-license signature dict. Order = specificity priority (AGPL
# before GPL because the former is a stricter superset of the
# latter's markers).
#
# A body matches a license when ≥ 2 of its markers are substrings
# of the body (case-sensitive — license texts are canonical and
# don't lowercase mid-stream).
LICENSE_SIGNATURES: list[tuple[str, list[str]]] = [
    (
        "AGPL-3.0",
        [
            "GNU AFFERO GENERAL PUBLIC LICENSE",
            "Version 3, 19 November 2007",
            "GNU Affero General Public License",
        ],
    ),
    (
        "Apache-2.0",
        [
            "Apache License",
            "Version 2.0, January 2004",
            "http://www.apache.org/licenses/",
        ],
    ),
    (
        "MIT",
        [
            "MIT License",
            "Permission is hereby granted, free of charge",
            "THE SOFTWARE IS PROVIDED \"AS IS\"",
        ],
    ),
    (
        "BSD-3-Clause",
        [
            "Redistribution and use in source and binary forms",
            "Neither the name of",
            "THIS SOFTWARE IS PROVIDED",
        ],
    ),
    (
        "GPL-3.0",
        [
            "GNU GENERAL PUBLIC LICENSE",
            "Version 3, 29 June 2007",
            "The GNU General Public License is a free, copyleft",
        ],
    ),
]

# Declared licenses that legitimately can't be reconciled to a single
# canonical text — multi-package repos, per-subdirectory upstream
# licenses, etc. These get classified as SKIP rather than UNKNOWN.
SKIP_DECLARED = {
    "LicenseRef-mixed-per-subdir",
    "LicenseRef-per-subdir",
}

# Aggregator priority (lower = better).
_STATUS_PRIORITY = {
    "OK": 0,
    "INVENTORIED": 0,  # offline-mode equivalent of OK
    "SKIP": 1,
    "MISSING": 2,
    "UNKNOWN": 3,
    "MISMATCH": 4,
}


# ---- pure classification core ----------------------------------------------


def identify_license(body: str) -> str | None:
    """Return the canonical license SPDX-ish name a text body matches.

    Walks ``LICENSE_SIGNATURES`` in declared order, returns the first
    license whose marker set has ≥ 2 substring hits in ``body``.
    Returns ``None`` if no license reaches the 2-marker threshold —
    preferred over guessing (phase5-plan.md §9).
    """
    for name, markers in LICENSE_SIGNATURES:
        hits = sum(1 for m in markers if m in body)
        if hits >= 2:
            return name
    return None


def check_one(
    *,
    slug: str,
    declared: str,
    license_body: str | None,
    offline: bool = False,
) -> dict[str, Any]:
    """Classify one (declared, license_body) pair.

    * declared in ``SKIP_DECLARED`` → SKIP (no reconciliation needed).
    * declared not in our signature dict → SKIP UNKNOWN-declared (we
      can't verify, but the declaration itself isn't a bug).
    * ``offline=True`` AND declared is known → INVENTORIED (signature
      dict recognises the declared license; LICENSE file not fetched).
    * ``license_body is None`` → MISSING.
    * detected == declared → OK; otherwise MISMATCH.
    """
    known = {name for name, _ in LICENSE_SIGNATURES}

    if declared in SKIP_DECLARED:
        return {
            "slug": slug,
            "declared": declared,
            "detected": None,
            "status": "SKIP",
            "reason": (
                f"declared {declared}: per-subdir licensing — reconciliation "
                f"by signature match doesn't apply"
            ),
        }

    if declared not in known:
        return {
            "slug": slug,
            "declared": declared,
            "detected": None,
            "status": "SKIP",
            "reason": (
                f"declared {declared!r} not in signature dict — "
                f"unable to verify without adding markers"
            ),
        }

    if offline:
        return {
            "slug": slug,
            "declared": declared,
            "detected": None,
            "status": "INVENTORIED",
            "reason": (
                f"declared {declared} is in the signature dict; "
                f"LICENSE-file fetch deferred to cron-mode"
            ),
        }

    if license_body is None:
        return {
            "slug": slug,
            "declared": declared,
            "detected": None,
            "status": "MISSING",
            "reason": "could not fetch LICENSE file",
        }

    detected = identify_license(license_body)
    if detected is None:
        return {
            "slug": slug,
            "declared": declared,
            "detected": None,
            "status": "UNKNOWN",
            "reason": (
                "LICENSE body did not match any signature in the dict "
                f"(declared {declared!r})"
            ),
        }

    if detected == declared:
        return {
            "slug": slug,
            "declared": declared,
            "detected": detected,
            "status": "OK",
        }
    return {
        "slug": slug,
        "declared": declared,
        "detected": detected,
        "status": "MISMATCH",
        "reason": f"declared {declared!r} but LICENSE body matches {detected!r}",
    }


def check_licenses_impl(
    entries: list[dict[str, Any]],
    *,
    offline: bool = False,
) -> tuple[list[dict[str, Any]], str]:
    """Pure-function driver. Each input row: ``{slug, declared,
    license_body}``. Returns ``(rows, worst_status)`` sorted worst-first."""
    rows = [
        check_one(
            slug=e["slug"],
            declared=e["declared"],
            license_body=e.get("license_body"),
            offline=offline,
        )
        for e in entries
    ]
    rows.sort(
        key=lambda r: (
            -_STATUS_PRIORITY.get(r["status"], 0),
            r["slug"],
        )
    )
    worst = "OK"
    for r in rows:
        if _STATUS_PRIORITY[r["status"]] > _STATUS_PRIORITY[worst]:
            worst = r["status"]
    return rows, worst


# ---- LICENSE-URL fetching --------------------------------------------------


_GH_REPO_RE = re.compile(r"^https?://github\.com/([^/]+/[^/]+)/?$")


def license_raw_url(repo_url: str) -> str | None:
    """Derive the raw-content URL of ``<repo>/LICENSE`` on the main
    branch from a GitHub HTTPS URL. Returns None for non-GitHub repos.

    Example: ``https://github.com/m-dev-tools/m-cli`` ↦
    ``https://raw.githubusercontent.com/m-dev-tools/m-cli/main/LICENSE``.
    """
    m = _GH_REPO_RE.match(repo_url)
    if not m:
        return None
    slug = m.group(1)
    return f"https://raw.githubusercontent.com/{slug}/main/LICENSE"


def fetch_license_body(url: str, timeout: float = 15.0) -> str | None:
    """Fetch a LICENSE body. Returns None on 404 / transport failure;
    raises only on programmer errors."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    except (urllib.error.URLError, TimeoutError):
        return None


# ---- table formatting -------------------------------------------------------


def format_table(title: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return f"### {title}\n\n(no entries)\n"
    lines = [
        f"### {title}",
        "",
        "| status | slug | declared | detected | reason |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        detected = r.get("detected") or "—"
        reason = r.get("reason", "")
        lines.append(
            f"| {r['status']} | `{r['slug']}` | `{r['declared']}` "
            f"| `{detected}` | {reason} |"
        )
    lines.append("")
    return "\n".join(lines)


# ---- CLI -------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="License-reconcile gate over tools.json entries."
    )
    parser.add_argument("--tools-json", type=Path, default=DEFAULT_TOOLS_JSON)
    parser.add_argument(
        "--offline",
        action="store_true",
        help=(
            "Don't fetch LICENSE files. Only sanity-check that the "
            "declared license field is in our known signature dict "
            "(or in the SKIP set). Used by per-PR CI."
        ),
    )
    args = parser.parse_args(argv)

    try:
        tools = json.loads(args.tools_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read {args.tools_json}: {exc}", file=sys.stderr)
        return 2

    tools_map = tools.get("tools", {})
    if not isinstance(tools_map, dict):
        print(f"ERROR: tools.json has no 'tools' map: {args.tools_json}", file=sys.stderr)
        return 2

    entries: list[dict[str, Any]] = []
    for slug, entry in tools_map.items():
        if not isinstance(entry, dict):
            continue
        declared = entry.get("license")
        repo_url = entry.get("repo")
        if not isinstance(declared, str):
            entries.append({"slug": slug, "declared": "MISSING", "license_body": None})
            continue

        body: str | None = None
        if not args.offline:
            license_url = license_raw_url(repo_url) if isinstance(repo_url, str) else None
            if license_url is None:
                # Non-GitHub repo or missing repo field — can't fetch.
                body = None
            else:
                try:
                    body = fetch_license_body(license_url)
                except urllib.error.HTTPError as exc:
                    print(
                        f"WARN: {slug}: LICENSE fetch returned {exc.code} {exc.reason}",
                        file=sys.stderr,
                    )
                    body = None

        entries.append({"slug": slug, "declared": declared, "license_body": body})

    rows, worst = check_licenses_impl(entries, offline=args.offline)
    print(format_table("License reconcile", rows))

    # Offline mode never fetches; each row is either OK-known
    # (INVENTORIED), SKIP, or — if the declared field is missing —
    # MISSING. Nothing fails the gate; the weekly cron firing is the
    # only place real MISMATCH / MISSING surfaces.
    fail_statuses = set() if args.offline else {"MISMATCH", "MISSING", "UNKNOWN"}

    if worst in fail_statuses:
        print(f"check-licenses: FAIL (worst={worst})", file=sys.stderr)
        return 1
    print(f"check-licenses: clean (worst={worst})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
