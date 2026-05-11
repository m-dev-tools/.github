#!/usr/bin/env python3
"""Phase 5 Track B — link-checking gate.

Walks every URL surfaced by the catalog:

* ``profile/llms.txt`` — Markdown link targets.
* ``profile/tools.json`` — top-level ``$schema`` + every ``*_url``
  field across every ``tools.<key>`` entry.
* ``profile/task_index.json`` — top-level ``$schema`` + every
  ``doc`` field across every category/row.

For each URL, issues a HEAD request (15s timeout). 200/301/302 count
as OK when ``--allow-redirects`` is on (the default). A 405 Method
Not Allowed retries with a GET. Anything else surfaces as ``FAIL``
with the HTTP status + message.

Binary URLs (``.whl`` / ``.tar.gz`` / ``.tgz`` / ``.zip`` / ``.gz``)
work the same way — HEAD only, no body decode. Same defense as
``validate-repo-meta.py`` after Phase 5 Track B0.

Modes:

* ``--offline`` — inventory only. No network. Status column reads
  ``INVENTORIED``. Used by per-PR CI.
* default — full HEAD walk. Used by the weekly cron firing.

Exit codes:

* ``0`` — all URLs OK (or all INVENTORIED in --offline mode).
* ``1`` — any URL FAIL.
* ``2`` — fixture/parse error.
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
DEFAULT_TASK_INDEX = PROFILE / "task_index.json"
DEFAULT_LLMS_TXT = PROFILE / "llms.txt"

MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
URL_RE = re.compile(r"^https?://")

# Status priority for aggregator + sort (lower = better).
_STATUS_PRIORITY = {
    "OK": 0,
    "INVENTORIED": 1,
    "FAIL": 2,
}


# ---- inventory helpers -----------------------------------------------------


def extract_urls_from_tools_json(tools: dict[str, Any]) -> list[tuple[str, str]]:
    """Return ``(label, url)`` rows for every URL in ``tools.json``.

    Surfaces:
      * top-level ``$schema``
      * every ``tools.<key>.<field>_url`` value that's an http(s) URL
    """
    out: list[tuple[str, str]] = []
    schema = tools.get("$schema")
    if isinstance(schema, str) and URL_RE.match(schema):
        out.append(("$schema", schema))
    tools_map = tools.get("tools", {})
    if isinstance(tools_map, dict):
        for key, entry in tools_map.items():
            if not isinstance(entry, dict):
                continue
            for field, value in entry.items():
                if not isinstance(value, str):
                    continue
                if not field.endswith("_url"):
                    continue
                if not URL_RE.match(value):
                    continue
                out.append((f"tools.{key}.{field}", value))
    return out


def extract_urls_from_task_index(ti: dict[str, Any]) -> list[tuple[str, str]]:
    """Return ``(label, url)`` rows for every URL in ``task_index.json``."""
    out: list[tuple[str, str]] = []
    schema = ti.get("$schema")
    if isinstance(schema, str) and URL_RE.match(schema):
        out.append(("$schema", schema))
    categories = ti.get("categories", {})
    if isinstance(categories, dict):
        for cat_name, cat in categories.items():
            if not isinstance(cat, dict):
                continue
            for row_name, row in cat.items():
                if not isinstance(row, dict):
                    continue
                doc = row.get("doc")
                if isinstance(doc, str) and URL_RE.match(doc):
                    out.append((f"categories.{cat_name}.{row_name}.doc", doc))
    return out


def extract_urls_from_llms_txt(text: str) -> list[tuple[str, str]]:
    """Return ``(label, url)`` rows for every Markdown-link URL in
    ``llms.txt``. Labels are the line index where the link appeared."""
    out: list[tuple[str, str]] = []
    for line_idx, line in enumerate(text.splitlines(), start=1):
        for m in MD_LINK_RE.finditer(line):
            url = m.group(1)
            if URL_RE.match(url):
                out.append((f"llms.txt:L{line_idx}", url))
    return out


# ---- single-URL check ------------------------------------------------------


def check_url(url: str, *, allow_redirects: bool = True, timeout: float = 15.0) -> dict[str, Any]:
    """HEAD-check one URL. Returns
    ``{"status": "OK"|"FAIL", "http_status": int|None, "message": str}``.

    On 405, retries with a GET. ``allow_redirects`` is informational
    here — urllib follows 3xx natively; the final 200 is what we see.
    """
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            status = getattr(resp, "status", 200)
            return {"status": "OK", "http_status": status, "message": ""}
    except urllib.error.HTTPError as exc:
        if exc.code == 405:
            try:
                with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
                    status = getattr(resp, "status", 200)
                    return {"status": "OK", "http_status": status, "message": ""}
            except urllib.error.HTTPError as exc2:
                return {
                    "status": "FAIL",
                    "http_status": exc2.code,
                    "message": str(exc2.reason or exc2),
                }
            except (urllib.error.URLError, TimeoutError) as exc2:
                return {
                    "status": "FAIL",
                    "http_status": None,
                    "message": str(exc2.reason if hasattr(exc2, "reason") else exc2),
                }
        return {"status": "FAIL", "http_status": exc.code, "message": str(exc.reason or exc)}
    except (urllib.error.URLError, TimeoutError) as exc:
        msg = str(exc.reason) if hasattr(exc, "reason") else str(exc)
        return {"status": "FAIL", "http_status": None, "message": msg}


# ---- driver ----------------------------------------------------------------


def check_links_impl(
    urls: list[tuple[str, str]],
    *,
    allow_redirects: bool = True,
) -> tuple[list[dict[str, Any]], str]:
    """Walk each ``(label, url)`` pair, return ``(rows, worst_status)``
    sorted worst-first."""
    rows: list[dict[str, Any]] = []
    for label, url in urls:
        result = check_url(url, allow_redirects=allow_redirects)
        rows.append(
            {
                "label": label,
                "url": url,
                "status": result["status"],
                "http_status": result["http_status"],
                "message": result["message"],
            }
        )
    rows.sort(
        key=lambda r: (
            -_STATUS_PRIORITY.get(r["status"], 0),
            r["label"],
        )
    )
    worst = "OK"
    for r in rows:
        if _STATUS_PRIORITY[r["status"]] > _STATUS_PRIORITY[worst]:
            worst = r["status"]
    return rows, worst


# ---- table formatting ------------------------------------------------------


def format_table(title: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return f"### {title}\n\n(no entries)\n"
    lines = [f"### {title}", "", "| status | label | url | http |", "|---|---|---|---|"]
    for r in rows:
        h = r.get("http_status")
        h_text = "—" if h is None else str(h)
        lines.append(f"| {r['status']} | `{r['label']}` | {r['url']} | {h_text} |")
    lines.append("")
    return "\n".join(lines)


# ---- CLI -------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Link-checking gate over llms.txt + tools.json + task_index.json."
    )
    parser.add_argument("--tools-json", type=Path, default=DEFAULT_TOOLS_JSON)
    parser.add_argument("--task-index", type=Path, default=DEFAULT_TASK_INDEX)
    parser.add_argument("--llms-txt", type=Path, default=DEFAULT_LLMS_TXT)
    parser.add_argument(
        "--offline",
        action="store_true",
        help=(
            "Inventory URLs only — don't fetch. Status column reads "
            "INVENTORIED. Used by per-PR CI to avoid network flake."
        ),
    )
    parser.add_argument(
        "--allow-redirects",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Follow 3xx redirects (default ON).",
    )
    args = parser.parse_args(argv)

    inventory: list[tuple[str, str]] = []
    try:
        if args.tools_json.exists():
            inventory.extend(
                extract_urls_from_tools_json(
                    json.loads(args.tools_json.read_text(encoding="utf-8"))
                )
            )
        if args.task_index.exists():
            inventory.extend(
                extract_urls_from_task_index(
                    json.loads(args.task_index.read_text(encoding="utf-8"))
                )
            )
        if args.llms_txt.exists():
            inventory.extend(
                extract_urls_from_llms_txt(args.llms_txt.read_text(encoding="utf-8"))
            )
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read catalog input: {exc}", file=sys.stderr)
        return 2

    if args.offline:
        rows = [
            {
                "label": label,
                "url": url,
                "status": "INVENTORIED",
                "http_status": None,
                "message": "",
            }
            for label, url in inventory
        ]
        worst = "OK"
        print(format_table("Inventory (offline)", rows))
        print(f"check-links: clean (offline; {len(rows)} URLs catalogued)")
        return 0

    rows, worst = check_links_impl(inventory, allow_redirects=args.allow_redirects)
    print(format_table("Link check", rows))
    if worst == "FAIL":
        n_fail = sum(1 for r in rows if r["status"] == "FAIL")
        print(f"check-links: FAIL ({n_fail} broken URL(s))", file=sys.stderr)
        return 1
    print(f"check-links: clean ({len(rows)} URL(s) OK)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
