#!/usr/bin/env python3
"""Phase-3 Track C — the 8-step discovery handshake.

Mechanically exercises §5.2 of the AI-discoverability plan and §13's
success criteria. One script that proves an AI agent can route from
plain-English intent → typed-ID → manifest pointer → callable entry,
end-to-end, against either live ``raw.githubusercontent.com`` URLs or
a bundled offline fixture set.

Eight steps (parent plan §5.2 verbatim):

  1. Fetch ``llms.txt`` → parses, every URL it lists returns HTTP 200.
  2. Fetch ``tools.json`` → validates against ``tools.schema.json``.
  3. Match a sample intent (``"parse JSON in M"``) against
     ``task_index.json.categories.lib.json_parse.intent``.
  4. Resolve the primary typed-ID (``module:m-stdlib#STDJSON``) through
     ``tools.json`` → find ``tools.m-stdlib.modules_url`` (or
     ``manifest_url``).
  5. Fetch that manifest URL.
  6. Find ``STDJSON`` in the manifest → assert ``signature`` and
     ``example``/``examples`` fields exist on at least one entry.
  7. Print the routing trail (one line per step) to stdout.
  8. Exit 0 on full success; non-zero with structured stderr on any
     failure. Specific exit codes (see EXIT_* constants) so CI can
     branch on failure category — not just "non-zero".

CLI::

    test-discovery-protocol.py            # live (default)
    test-discovery-protocol.py --live     # explicit
    test-discovery-protocol.py --offline  # use ``fixtures/``
    test-discovery-protocol.py --offline --fixtures path/to/fixtures

When ``--live`` and the network is unreachable, the script logs a
warning to stderr and falls back to ``--offline`` (CI's network is
always up; local dev without network shouldn't fail loudly). When
``--offline`` and a fixture is missing, the script fails with
``EXIT_FIXTURE_MISSING``.

Determinism: the routing trail printed to stdout is byte-identical
across runs against the same inputs. No timestamps, no random IDs.
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

PROFILE = Path(__file__).resolve().parents[1]
TOOLS_SCHEMA_PATH = PROFILE / "tools.schema.json"
TASK_INDEX_SCHEMA_PATH = PROFILE / "task_index.schema.json"
DEFAULT_FIXTURES = Path(__file__).resolve().parent / "fixtures"

# Live URLs (mirror llms.txt's "Start here" anchors).
LIVE_LLMS = "https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/llms.txt"
LIVE_TOOLS = "https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/tools.json"
LIVE_TASK_INDEX = (
    "https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/task_index.json"
)

# Default sample intent + expected primary typed-ID (parent plan §5.2).
DEFAULT_INTENT = "parse JSON in M"
DEFAULT_MODULE_TYPED_ID = "module:m-stdlib#STDJSON"

TYPED_ID_RE = re.compile(
    r"^(tool|cmd|module|rule|doc|data|workflow|task|recipe):"
    r"[a-z0-9_-]+(#[A-Za-z0-9._-]+)?$"
)

# URL regex (allow file:// for offline fixtures).
URL_RE = re.compile(r"^(https?|file)://")

# Markdown link target capture: [label](URL "optional title") — title trimmed.
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


# ---- Exit codes (script-level contract; tests assert specific values) -------

EXIT_OK = 0
# 1–9 reserved for argparse / unexpected exceptions (subprocess gives us 1
# automatically on a Python-level exception bubbling out of main).
EXIT_LLMS_LINK_BROKEN = 10
EXIT_TOOLS_SCHEMA_VIOLATION = 11
EXIT_TASK_INDEX_MALFORMED = 12
EXIT_MANIFEST_FETCH_FAIL = 13
EXIT_MANIFEST_ENTRY_INCOMPLETE = 14
EXIT_INTENT_UNMATCHED = 15
EXIT_FIXTURE_MISSING = 20


# =================================================================== I/O ====


def fetch(url: str, base_dir: Path | None = None, timeout: float = 20.0) -> str:
    """Fetch a URL. Supports https://, http://, and (for offline fixtures)
    file:// URLs of the form ``file://./<name>`` relative to ``base_dir``.

    Returns the body as UTF-8 text. Raises on transport or decode errors —
    callers translate the exception into a specific exit code.
    """
    if url.startswith("file://"):
        rel = url[len("file://") :]
        # Accept both file://./name and file:///abs/name.
        if rel.startswith("./"):
            if base_dir is None:
                raise FileNotFoundError(f"file:// URL with no base_dir: {url}")
            path = base_dir / rel[2:]
        elif rel.startswith("/"):
            path = Path(rel)
        else:
            if base_dir is None:
                raise FileNotFoundError(f"file:// URL with no base_dir: {url}")
            path = base_dir / rel
        if not path.exists():
            raise FileNotFoundError(f"fixture not found: {path}")
        return path.read_text(encoding="utf-8")
    # http / https
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def head_or_get(url: str, base_dir: Path | None, timeout: float = 15.0) -> int:
    """Return the HTTP status code (or 200 for an existing file://).

    For file:// URLs, returns 200 if the file exists, 404 otherwise.
    For http(s) URLs, attempts a HEAD request, falls back to GET on 405.
    """
    if url.startswith("file://"):
        rel = url[len("file://") :]
        if rel.startswith("./") and base_dir is not None:
            return 200 if (base_dir / rel[2:]).exists() else 404
        if rel.startswith("/"):
            return 200 if Path(rel).exists() else 404
        if base_dir is not None and (base_dir / rel).exists():
            return 200
        return 404
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        # 405 Method Not Allowed → fall back to GET.
        if exc.code == 405:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                return resp.status
        return exc.code


# ============================================================ llms parsing ==


def extract_llms_links(text: str) -> list[str]:
    """Pull every Markdown-link URL from an llms.txt body.

    Order-preserving: the routing trail prints in the same order links
    appeared. Duplicates kept — the link-checker walks each one.
    """
    return [m.group(1) for m in MD_LINK_RE.finditer(text)]


# ============================================================ intent match ==


def match_intent(query: str, task_index: dict) -> str | None:
    """Match ``query`` against ``task_index.json``'s intents.

    First pass: exact ``intent`` string match (case-insensitive).
    Second pass: keyword overlap — every non-stopword token in the
    query appears in the intent string. The matcher prefers
    ``categories.lib.*`` over the others for the canonical
    parent-plan §5.2 case (json_parse).

    Returns the matched entry's ``primary`` typed-ID or ``None`` when
    nothing matches.
    """
    if not isinstance(task_index, dict):
        return None
    categories = task_index.get("categories", {})
    if not isinstance(categories, dict):
        return None

    needle = query.lower().strip()
    keywords = [t for t in re.findall(r"[a-z0-9]+", needle) if len(t) > 2]

    # First pass — exact match.
    for _cat_name, cat in categories.items():
        if not isinstance(cat, dict):
            continue
        for _row_name, row in cat.items():
            if not isinstance(row, dict):
                continue
            intent_str = str(row.get("intent", "")).lower()
            if intent_str == needle:
                primary = row.get("primary")
                return primary if isinstance(primary, str) else None

    # Second pass — every keyword present in the intent.
    # Score = (hits, leading_keyword_bonus). Higher is better.
    # leading_keyword_bonus rewards intents that *start* with a query
    # keyword — "Parse JSON text into an M tree" should beat
    # "What does parse^STDJSON do?" for the query "parse JSON in M".
    best: tuple[int, int, str] | None = None
    for _cat_name, cat in categories.items():
        if not isinstance(cat, dict):
            continue
        for _row_name, row in cat.items():
            if not isinstance(row, dict):
                continue
            intent_str = str(row.get("intent", "")).lower()
            hits = sum(1 for kw in keywords if kw in intent_str)
            # Require ≥ 2 keyword hits for a fuzzy match to avoid false
            # positives like "calibrate the rocket booster" matching
            # anything generic.
            if hits >= max(2, len(keywords) - 1):
                # Position bonus: if the intent's first word matches any
                # query keyword, +10. Earlier ties of hits then break by
                # earliest-first-keyword position.
                first_word = re.findall(r"[a-z0-9]+", intent_str)
                first_word = first_word[0] if first_word else ""
                leading = 10 if first_word in keywords else 0
                primary = row.get("primary")
                if isinstance(primary, str):
                    score = (hits, leading)
                    candidate = (score[0], score[1], primary)
                    if best is None or (candidate[0], candidate[1]) > (best[0], best[1]):
                        best = candidate
    return best[2] if best else None


# ============================================================ typed-ID nav ==


def parse_typed_id(typed_id: str) -> tuple[str, str, str | None]:
    """Return (kind, slug, member). Raises ValueError on malformed input."""
    if not TYPED_ID_RE.match(typed_id):
        raise ValueError(f"malformed typed-ID: {typed_id!r}")
    kind, rest = typed_id.split(":", 1)
    if "#" in rest:
        slug, member = rest.split("#", 1)
        return kind, slug, member
    return kind, rest, None


def resolve_module_manifest_url(typed_id: str, tools: dict) -> str | None:
    """Given ``module:<repo>#<symbol>``, return the manifest URL the
    catalog points at — preferring ``modules_url`` then ``manifest_url``.
    """
    kind, slug, _member = parse_typed_id(typed_id)
    if kind != "module":
        return None
    tools_map = tools.get("tools", {})
    if not isinstance(tools_map, dict):
        return None
    entry = tools_map.get(slug)
    if not isinstance(entry, dict):
        return None
    for key in ("modules_url", "manifest_url", "stdlib_manifest_url"):
        v = entry.get(key)
        if isinstance(v, str):
            return v
    # Fallback: any *_url that looks manifest-shaped.
    for k, v in entry.items():
        if isinstance(v, str) and k.endswith("_url") and "manifest" in v:
            return v
    return None


def find_module_entry(symbol: str, manifest: dict) -> dict | None:
    """Look up ``symbol`` in a stdlib-shaped manifest.

    Two supported shapes:
      * ``modules`` is a dict keyed by symbol → entry.
      * ``modules`` is a list of entries with a ``name`` field.
    """
    modules = manifest.get("modules")
    if isinstance(modules, dict):
        v = modules.get(symbol)
        return v if isinstance(v, dict) else None
    if isinstance(modules, list):
        for m in modules:
            if isinstance(m, dict) and m.get("name") == symbol:
                return m
    return None


def entry_has_signature_and_example(entry: dict) -> tuple[bool, bool]:
    """Return (has_signature, has_example).

    The stdlib-manifest shape nests per-label data under ``labels``: an
    entry counts as having ``signature`` / ``example`` if at least one
    label exposes them. Falls back to top-level fields for non-stdlib
    manifests.
    """
    has_sig = False
    has_ex = False

    def _check_dict(d: dict) -> None:
        nonlocal has_sig, has_ex
        if "signature" in d and d["signature"]:
            has_sig = True
        if d.get("example") or d.get("examples"):
            has_ex = True

    _check_dict(entry)

    labels = entry.get("labels")
    if isinstance(labels, dict):
        for v in labels.values():
            if isinstance(v, dict):
                _check_dict(v)
    elif isinstance(labels, list):
        for v in labels:
            if isinstance(v, dict):
                _check_dict(v)

    return has_sig, has_ex


# ====================================================== schema validation ==


def _validate_against_schema(
    data: dict, schema_path: Path, label: str, errors: list[str]
) -> None:
    """Validate ``data`` against the schema at ``schema_path``.

    Uses ``jsonschema`` (Draft 2020-12). If ``jsonschema`` is missing,
    appends an error — Phase 3 onwards we require it. This is consistent
    with ``validate-catalog.py``.
    """
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        errors.append(f"{label}: jsonschema is required (pip install jsonschema): {exc}")
        return
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label}: cannot load schema {schema_path}: {exc}")
        return
    validator = Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        path = "/".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"{label}: at {path}: {err.message}")


def _validate_typed_ids_in_task_index(task_index: dict, errors: list[str]) -> None:
    """Inline grammar check on every typed-ID in task_index.

    The full schema does this too, but we surface a dedicated error code
    when the failure is *only* a typed-ID grammar violation — so CI can
    distinguish "schema drift" (EXIT_TOOLS_SCHEMA_VIOLATION) from "bad
    intent row" (EXIT_TASK_INDEX_MALFORMED).
    """
    categories = task_index.get("categories", {})
    if not isinstance(categories, dict):
        return
    for cat_name, cat in categories.items():
        if not isinstance(cat, dict):
            continue
        for row_name, row in cat.items():
            if not isinstance(row, dict):
                continue
            for field in ("primary",):
                v = row.get(field)
                if isinstance(v, str) and not TYPED_ID_RE.match(v):
                    errors.append(
                        f"task_index.categories.{cat_name}.{row_name}.{field}: "
                        f"malformed typed-ID: {v!r}"
                    )
            see_also = row.get("see_also")
            if isinstance(see_also, list):
                for i, v in enumerate(see_also):
                    if isinstance(v, str) and not TYPED_ID_RE.match(v):
                        errors.append(
                            f"task_index.categories.{cat_name}.{row_name}.see_also[{i}]: "
                            f"malformed typed-ID: {v!r}"
                        )


# ================================================================== driver ==


class HandshakeFailure(Exception):
    """Raised when a handshake step fails. Carries an exit code."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


def _resolve_offline_urls(fixtures: Path) -> tuple[str, str, str]:
    """Map the canonical (llms, tools, task_index) URLs to file:// for offline.

    Each fixture must exist; otherwise fail with EXIT_FIXTURE_MISSING.
    """
    needed = {
        "llms.txt": fixtures / "llms.txt",
        "tools.json": fixtures / "tools.json",
        "task_index.json": fixtures / "task_index.json",
    }
    missing = [str(p) for p in needed.values() if not p.exists()]
    if missing:
        raise HandshakeFailure(
            EXIT_FIXTURE_MISSING,
            "missing offline fixture(s): " + ", ".join(missing),
        )
    return (
        f"file://./llms.txt",
        f"file://./tools.json",
        f"file://./task_index.json",
    )


def run_handshake(
    *,
    offline: bool,
    fixtures: Path,
    intent: str = DEFAULT_INTENT,
    expected_typed_id: str | None = DEFAULT_MODULE_TYPED_ID,
    out: Any = sys.stdout,
    err: Any = sys.stderr,
) -> int:
    """Run the 8-step handshake. Returns the exit code.

    Network-fail-soft: if ``offline`` is False and the live llms.txt
    fetch raises a URL error, we warn to stderr and fall back to the
    offline fixtures (CI sees the network; local dev may not).
    """
    trail: list[str] = []
    base_dir = fixtures if offline else None
    llms_url = LIVE_LLMS
    tools_url = LIVE_TOOLS
    task_index_url = LIVE_TASK_INDEX

    if offline:
        try:
            llms_url, tools_url, task_index_url = _resolve_offline_urls(fixtures)
        except HandshakeFailure as exc:
            print(f"ERROR: {exc}", file=err)
            return exc.code
        base_dir = fixtures

    def _emit(line: str) -> None:
        trail.append(line)
        print(line, file=out)

    # ---- Step 1 — fetch llms.txt, link-check every URL ----------------------
    try:
        llms_body = fetch(llms_url, base_dir=base_dir)
    except (urllib.error.URLError, TimeoutError, FileNotFoundError) as exc:
        if not offline:
            # Live fetch failed — fall back to offline.
            print(
                f"WARN: live llms.txt fetch failed ({exc}); falling back to --offline",
                file=err,
            )
            return run_handshake(
                offline=True,
                fixtures=fixtures,
                intent=intent,
                expected_typed_id=expected_typed_id,
                out=out,
                err=err,
            )
        print(f"ERROR: cannot fetch llms.txt {llms_url}: {exc}", file=err)
        return EXIT_LLMS_LINK_BROKEN
    _emit(f"step 1 — fetched llms.txt ({len(llms_body)} bytes)")

    links = extract_llms_links(llms_body)
    for link in links:
        try:
            status = head_or_get(link, base_dir=base_dir)
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"ERROR: llms.txt link unreachable: {link}: {exc}", file=err)
            return EXIT_LLMS_LINK_BROKEN
        if status >= 400:
            print(f"ERROR: llms.txt link returned HTTP {status}: {link}", file=err)
            return EXIT_LLMS_LINK_BROKEN
        _emit(f"  link OK ({status}): {link}")

    # ---- Step 2 — fetch tools.json, schema-validate -------------------------
    try:
        tools_body = fetch(tools_url, base_dir=base_dir)
        tools = json.loads(tools_body)
    except (urllib.error.URLError, TimeoutError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot load tools.json: {exc}", file=err)
        return EXIT_TOOLS_SCHEMA_VIOLATION
    _emit(f"step 2 — fetched tools.json (kind={tools.get('kind', '?')!r})")

    errs: list[str] = []
    _validate_against_schema(tools, TOOLS_SCHEMA_PATH, "tools.json", errs)
    if errs:
        for e in errs:
            print(f"ERROR: {e}", file=err)
        return EXIT_TOOLS_SCHEMA_VIOLATION
    _emit("  tools.json validates against tools.schema.json")

    # ---- Step 3 — fetch task_index, validate, and match intent --------------
    try:
        ti_body = fetch(task_index_url, base_dir=base_dir)
        task_index = json.loads(ti_body)
    except (urllib.error.URLError, TimeoutError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot load task_index.json: {exc}", file=err)
        return EXIT_TASK_INDEX_MALFORMED
    _emit(f"step 3 — fetched task_index.json ({len(task_index.get('categories', {}))} categories)")

    errs = []
    _validate_against_schema(task_index, TASK_INDEX_SCHEMA_PATH, "task_index.json", errs)
    _validate_typed_ids_in_task_index(task_index, errs)
    if errs:
        for e in errs:
            print(f"ERROR: {e}", file=err)
        return EXIT_TASK_INDEX_MALFORMED

    primary = match_intent(intent, task_index)
    if primary is None:
        print(f"ERROR: intent did not match any task_index entry: {intent!r}", file=err)
        return EXIT_INTENT_UNMATCHED
    _emit(f"  intent {intent!r} → primary {primary}")

    if expected_typed_id is not None and primary != expected_typed_id:
        print(
            f"ERROR: intent {intent!r} resolved to {primary!r}, "
            f"expected {expected_typed_id!r}",
            file=err,
        )
        return EXIT_INTENT_UNMATCHED

    # ---- Step 4 — resolve typed-ID through tools.json -----------------------
    try:
        parse_typed_id(primary)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=err)
        return EXIT_TASK_INDEX_MALFORMED

    manifest_url = resolve_module_manifest_url(primary, tools)
    if not manifest_url:
        print(
            f"ERROR: cannot resolve manifest URL for {primary} via tools.json",
            file=err,
        )
        return EXIT_MANIFEST_FETCH_FAIL
    _emit(f"step 4 — typed-ID {primary} → manifest_url {manifest_url}")

    # ---- Step 5 — fetch manifest --------------------------------------------
    try:
        manifest_body = fetch(manifest_url, base_dir=base_dir)
        manifest = json.loads(manifest_body)
    except (urllib.error.URLError, TimeoutError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot fetch manifest {manifest_url}: {exc}", file=err)
        return EXIT_MANIFEST_FETCH_FAIL
    _emit(f"step 5 — fetched manifest ({len(manifest_body)} bytes)")

    # ---- Step 6 — find the symbol entry, assert signature + example --------
    _kind, _slug, symbol = parse_typed_id(primary)
    if symbol is None:
        print(f"ERROR: typed-ID has no #symbol member: {primary}", file=err)
        return EXIT_MANIFEST_ENTRY_INCOMPLETE
    entry = find_module_entry(symbol, manifest)
    if entry is None:
        print(f"ERROR: symbol {symbol!r} not found in manifest", file=err)
        return EXIT_MANIFEST_ENTRY_INCOMPLETE
    has_sig, has_ex = entry_has_signature_and_example(entry)
    if not (has_sig and has_ex):
        print(
            f"ERROR: entry {symbol!r} missing required fields "
            f"(signature={has_sig}, example={has_ex})",
            file=err,
        )
        return EXIT_MANIFEST_ENTRY_INCOMPLETE
    _emit(f"step 6 — {symbol} entry has signature ✓ and example ✓")

    _emit("step 7 — routing trail complete (see above)")
    _emit("step 8 — exit 0 (success)")
    return EXIT_OK


# ============================================================ argparse glue ==


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--live",
        action="store_true",
        help="(default) Fetch llms.txt / tools.json / task_index.json from raw GitHub.",
    )
    mode.add_argument(
        "--offline",
        action="store_true",
        help=f"Use bundled fixtures instead of the network (default fixtures: {DEFAULT_FIXTURES}).",
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=DEFAULT_FIXTURES,
        help="Directory containing llms.txt + tools.json + task_index.json + stdlib-manifest.json fixtures.",
    )
    parser.add_argument(
        "--intent",
        default=DEFAULT_INTENT,
        help=f"Sample intent string to route through task_index (default: {DEFAULT_INTENT!r}).",
    )
    args = parser.parse_args(argv)

    offline = args.offline  # --live is the implicit default
    return run_handshake(
        offline=offline,
        fixtures=args.fixtures,
        intent=args.intent,
    )


if __name__ == "__main__":
    raise SystemExit(main())
