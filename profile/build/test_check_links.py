"""Tests for check-links.py — Phase 5 Track B1 (RED) before B2 (GREEN).

Pure-function inventory helpers + the URL-walker, tested with
``unittest.mock.patch`` over ``urllib.request.urlopen`` so the unit
suite is network-free.
"""

from __future__ import annotations

import importlib.util
import json
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD = REPO_ROOT / "profile" / "build"

_path = BUILD / "check-links.py"
_spec = importlib.util.spec_from_file_location("_check_links", _path)
_check_links = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_check_links)


# ----------------------------------------------------------- inventory


def test_extract_urls_from_tools_json_captures_star_url_fields() -> None:
    """Every *_url field on every tools.<key> entry surfaces, plus the
    top-level $schema."""
    tools = {
        "$schema": "https://schema.example.invalid/tools.schema.json",
        "tools": {
            "m-cli": {
                "id": "tool:m-cli",
                "repo_meta_url": "https://example.invalid/m-cli/repo.meta.json",
                "commands_url": "https://example.invalid/m-cli/commands.json",
                "verified_on": "2026-05-11",
            },
            "m-stdlib": {
                "id": "tool:m-stdlib",
                "modules_url": "https://example.invalid/m-stdlib/manifest.json",
            },
        },
    }
    urls = _check_links.extract_urls_from_tools_json(tools)
    by_label = {label: url for label, url in urls}
    assert by_label["$schema"] == "https://schema.example.invalid/tools.schema.json"
    assert (
        by_label["tools.m-cli.repo_meta_url"]
        == "https://example.invalid/m-cli/repo.meta.json"
    )
    assert (
        by_label["tools.m-cli.commands_url"]
        == "https://example.invalid/m-cli/commands.json"
    )
    assert by_label["tools.m-stdlib.modules_url"]
    # verified_on must NOT surface — not a URL.
    assert not any("verified_on" in label for label, _ in urls)


def test_extract_urls_from_task_index_captures_doc_fields() -> None:
    """Each row's optional ``doc`` field surfaces as a URL row."""
    ti = {
        "$schema": "https://schema.example.invalid/task_index.schema.json",
        "categories": {
            "lib": {
                "json_parse": {
                    "intent": "Parse JSON in M",
                    "primary": "module:m-stdlib#STDJSON",
                    # no doc — should not surface
                },
            },
            "infra": {
                "agent_integration": {
                    "intent": "Point my MCP agent at the catalog",
                    "primary": "tool:m-dev-tools-mcp",
                    "doc": "https://example.invalid/agent-integration.md",
                },
            },
        },
    }
    urls = _check_links.extract_urls_from_task_index(ti)
    by_label = {label: url for label, url in urls}
    assert by_label["$schema"] == "https://schema.example.invalid/task_index.schema.json"
    assert (
        by_label["categories.infra.agent_integration.doc"]
        == "https://example.invalid/agent-integration.md"
    )
    # json_parse has no doc — must not surface
    assert "categories.lib.json_parse.doc" not in by_label


def test_extract_urls_from_llms_txt_captures_markdown_links() -> None:
    text = (
        "# org\n\n"
        "Start: [tools.json](https://example.invalid/tools.json)\n"
        "Schema: [tools.schema.json](https://example.invalid/tools.schema.json)\n"
    )
    urls = _check_links.extract_urls_from_llms_txt(text)
    by_url = {url for _label, url in urls}
    assert "https://example.invalid/tools.json" in by_url
    assert "https://example.invalid/tools.schema.json" in by_url


# ----------------------------------------------------------- check_url


def _mock_resp(status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    resp.status = status
    resp.read = MagicMock(return_value=b"")
    return resp


def test_check_url_200_is_ok() -> None:
    with patch("urllib.request.urlopen", return_value=_mock_resp(200)):
        result = _check_links.check_url("https://example.invalid/x")
    assert result["status"] == "OK"
    assert result["http_status"] == 200


def test_check_url_404_is_fail() -> None:
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.HTTPError(
            "https://example.invalid/x", 404, "Not Found", hdrs={}, fp=None
        ),
    ):
        result = _check_links.check_url("https://example.invalid/x")
    assert result["status"] == "FAIL"
    assert result["http_status"] == 404


def test_check_url_405_on_head_falls_back_to_get() -> None:
    """If HEAD returns 405, retry with GET. The walker uses a Request
    object with method='HEAD'; on 405 it falls back to a no-method GET."""
    call_count = {"head": 0, "get": 0}

    def _fake_urlopen(req_or_url, **_kwargs):
        # urllib passes a Request object for the explicit-method call,
        # a bare string for the GET fallback.
        if hasattr(req_or_url, "get_method") and req_or_url.get_method() == "HEAD":
            call_count["head"] += 1
            raise urllib.error.HTTPError(
                "https://example.invalid/x", 405, "Method Not Allowed", hdrs={}, fp=None
            )
        call_count["get"] += 1
        return _mock_resp(200)

    with patch("urllib.request.urlopen", side_effect=_fake_urlopen):
        result = _check_links.check_url("https://example.invalid/x")
    assert call_count["head"] == 1
    assert call_count["get"] == 1
    assert result["status"] == "OK"


def test_check_url_dns_failure_is_fail() -> None:
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("nodename nor servname provided"),
    ):
        result = _check_links.check_url("https://nonexistent.invalid/")
    assert result["status"] == "FAIL"
    assert result["http_status"] is None
    assert "nodename" in result["message"]


def test_check_url_redirect_followed_by_default() -> None:
    """A 302 followed by a 200 counts as OK when --allow-redirects is on
    (the default). urllib.request.urlopen follows redirects natively,
    so we just simulate the final 200 here."""
    with patch("urllib.request.urlopen", return_value=_mock_resp(200)):
        result = _check_links.check_url(
            "https://example.invalid/redirect-to-x", allow_redirects=True
        )
    assert result["status"] == "OK"


# ----------------------------------------------------------- driver / CLI


def test_check_links_impl_aggregates_worst() -> None:
    """Driver aggregates per-URL results. Worst-first ordering."""
    urls = [
        ("$schema", "https://example.invalid/ok-a"),
        ("tools.x.repo_meta_url", "https://example.invalid/bad"),
        ("tools.y.modules_url", "https://example.invalid/ok-b"),
    ]

    def _fake_check(url, **_kwargs):
        if url.endswith("/bad"):
            return {"status": "FAIL", "http_status": 404, "message": "Not Found"}
        return {"status": "OK", "http_status": 200, "message": ""}

    with patch.object(_check_links, "check_url", side_effect=_fake_check):
        rows, worst = _check_links.check_links_impl(urls, allow_redirects=True)
    assert worst == "FAIL"
    # Worst-first
    assert rows[0]["status"] == "FAIL"
    assert rows[0]["url"].endswith("/bad")


def test_check_links_impl_all_ok_returns_OK() -> None:
    urls = [("a", "https://example.invalid/a"), ("b", "https://example.invalid/b")]
    with patch.object(
        _check_links,
        "check_url",
        return_value={"status": "OK", "http_status": 200, "message": ""},
    ):
        rows, worst = _check_links.check_links_impl(urls, allow_redirects=True)
    assert worst == "OK"
    assert all(r["status"] == "OK" for r in rows)


def test_cli_offline_inventories_without_network(tmp_path, capsys) -> None:
    """--offline must NOT touch the network. Patch urlopen to blow up
    so an accidental fetch is caught."""
    tools = {"tools": {"m-cli": {"repo_meta_url": "https://example.invalid/a.json"}}}
    ti = {"categories": {}}
    llms = "# org\n[a](https://example.invalid/b.json)\n"

    tools_path = tmp_path / "tools.json"
    ti_path = tmp_path / "task_index.json"
    llms_path = tmp_path / "llms.txt"
    tools_path.write_text(json.dumps(tools), encoding="utf-8")
    ti_path.write_text(json.dumps(ti), encoding="utf-8")
    llms_path.write_text(llms, encoding="utf-8")

    with patch(
        "urllib.request.urlopen",
        side_effect=AssertionError("network must not be touched in --offline mode"),
    ):
        rc = _check_links.main(
            [
                "--offline",
                "--tools-json", str(tools_path),
                "--task-index", str(ti_path),
                "--llms-txt", str(llms_path),
            ]
        )
    out = capsys.readouterr().out
    assert rc == 0
    # Both URLs got inventoried
    assert "example.invalid/a.json" in out
    assert "example.invalid/b.json" in out
    # Status column should say INVENTORIED / SKIPPED — not OK (since
    # nothing was actually fetched)
    assert "INVENTORIED" in out or "SKIPPED" in out


def test_cli_failure_returns_rc1(tmp_path) -> None:
    tools = {"tools": {"x": {"repo_meta_url": "https://example.invalid/404"}}}
    tools_path = tmp_path / "tools.json"
    tools_path.write_text(json.dumps(tools), encoding="utf-8")
    ti_path = tmp_path / "task_index.json"
    ti_path.write_text(json.dumps({"categories": {}}), encoding="utf-8")
    llms_path = tmp_path / "llms.txt"
    llms_path.write_text("# x\n", encoding="utf-8")

    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.HTTPError(
            "https://example.invalid/404", 404, "Not Found", hdrs={}, fp=None
        ),
    ):
        rc = _check_links.main(
            [
                "--tools-json", str(tools_path),
                "--task-index", str(ti_path),
                "--llms-txt", str(llms_path),
            ]
        )
    assert rc == 1


def test_cli_committed_inventory_runs_offline(capsys) -> None:
    """Smoke against the real committed catalog. --offline mode never
    hits the network; just sanity-checks inventory works against the
    committed files."""
    rc = _check_links.main(["--offline"])
    out = capsys.readouterr().out
    assert rc == 0
    # At least the tools.json $schema URL should appear in the inventory
    assert "tools.schema.json" in out
