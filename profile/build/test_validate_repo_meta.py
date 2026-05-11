"""Tests for validate-repo-meta.py.

Phase 5 Track B0 — pinning the binary-URL behaviour. Pre-Track-B,
``resolve_one()`` blindly UTF-8-decoded every fetched body, which
made full-resolve validation fail against any `exposes.*` URL that
pointed at a binary asset (e.g. m-dev-tools-mcp's v0.1.0 wheel).
The fix uses HEAD-only for non-text extensions; this test pins the
behaviour so a future regression surfaces immediately.

Test strategy: monkey-patch ``urllib.request.urlopen`` so we control
the server's response shape. No real network round-trip.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD = REPO_ROOT / "profile" / "build"

_path = BUILD / "validate-repo-meta.py"
_spec = importlib.util.spec_from_file_location("_validate_repo_meta", _path)
_validate_repo_meta = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_validate_repo_meta)


def _mock_response(*, body: bytes = b"", status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    resp.read = MagicMock(return_value=body)
    resp.status = status
    return resp


def test_resolve_one_text_url_decodes_body() -> None:
    """Smoke: a .json URL still fetches + JSON-validates. Pinning the
    pre-Track-B0 happy path so the fix doesn't regress text handling."""
    errors: list[str] = []
    valid_json = b'{"hello": "world"}'
    with patch(
        "urllib.request.urlopen", return_value=_mock_response(body=valid_json)
    ):
        _validate_repo_meta.resolve_one(
            base="https://example.invalid/",
            value="dist/repo.meta.json",
            errors=errors,
            label="repo_meta",
        )
    assert errors == []


def test_resolve_one_invalid_json_text_url_reports() -> None:
    errors: list[str] = []
    with patch(
        "urllib.request.urlopen", return_value=_mock_response(body=b"not json")
    ):
        _validate_repo_meta.resolve_one(
            base="https://example.invalid/",
            value="dist/something.json",
            errors=errors,
            label="bad_json",
        )
    assert len(errors) == 1
    assert "invalid JSON" in errors[0]


def test_resolve_one_binary_wheel_url_no_decode() -> None:
    """Track B0 contract: a .whl URL must NOT trigger UTF-8 decode of
    the body. Validator returns success on HEAD-equivalent 200, no
    errors raised. Mirrors the real-world v0.1.0 wheel asset URL
    shape that crashed pre-Track-B0 validate-repo-meta."""
    errors: list[str] = []
    # Random non-UTF-8 bytes — would crash .decode("utf-8")
    bogus_bytes = b"\xab\xcd\xef\x00\x01\x02"
    with patch(
        "urllib.request.urlopen", return_value=_mock_response(body=bogus_bytes)
    ):
        _validate_repo_meta.resolve_one(
            base="https://github.com/m-dev-tools/m-dev-tools-mcp/releases/download/v0.1.0/",
            value="m_dev_tools_mcp-0.1.0-py3-none-any.whl",
            errors=errors,
            label="release_wheel",
        )
    assert errors == [], f"binary URL should not raise decode errors; got {errors!r}"


def test_resolve_one_binary_tarball_url_no_decode() -> None:
    """Same contract for .tar.gz."""
    errors: list[str] = []
    with patch(
        "urllib.request.urlopen", return_value=_mock_response(body=b"\x1f\x8b")
    ):
        _validate_repo_meta.resolve_one(
            base="https://example.invalid/",
            value="dist/payload.tar.gz",
            errors=errors,
            label="tarball",
        )
    assert errors == []


def test_resolve_one_binary_url_fetch_failure_reports() -> None:
    """HEAD failures (404, transport) still surface as errors."""
    import urllib.error

    errors: list[str] = []
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("simulated dns failure"),
    ):
        _validate_repo_meta.resolve_one(
            base="https://nonexistent.invalid/",
            value="dist/foo.whl",
            errors=errors,
            label="dead_link",
        )
    assert len(errors) == 1
    assert "cannot fetch" in errors[0]
