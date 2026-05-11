#!/usr/bin/env python3
"""Build profile/tools.json from each onboarded repo's dist/repo.meta.json.

Phase-1 Track B's generator. For each URL in TIER_1 ∪ TIER_2:

  1. Fetch the manifest from raw.githubusercontent.com.
  2. Validate it against profile/repo.meta.schema.json (Draft 2020-12).
  3. Translate it to a `tools.<key>` summary entry per
     profile/tools.schema.json's $defs.tool:
        - id, repo, role, license, agent_instructions, verified_on,
          status (default "active") come from the manifest.
        - language: array → string when single element, array otherwise
          (matches the post-P1-A baseline shape).
        - Each `exposes.<key>` becomes `<key>_url` in the output,
          constructed from the repo's main-branch raw prefix +
          relative path. Existing absolute URLs are passed through.
        - repo_meta_url is the TIER_N URL itself.
        - consumes / consumed_by passed through if present.
  4. Carry top-level narrative keys ($schema, schema_compat,
     schema_version, kind, description, org, workflow,
     discovery_protocol) from the prior committed tools.json so we
     don't lose hand-curated content. task_index is intentionally NOT
     emitted here — it lives in its own file post-P1-A.
  5. Emit deterministically: sorted keys, 2-space indent, trailing
     newline. Two runs against the same input must be byte-identical.

Usage:
    build-catalog.py [--write PATH] [--prior PATH] [--no-network]

  --write    write the result here; default stdout.
  --prior    path to the prior tools.json to read narrative keys from
             (default: profile/tools.json).
  --no-network  for dry-runs: skip fetches and emit only the prior
                tools.json's framing without any tools.* entries.

Exits 0 on success, non-zero on fetch / validation failure.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

PROFILE = Path(__file__).resolve().parents[1]
PRIOR_TOOLS_DEFAULT = PROFILE / "tools.json"
REPO_META_SCHEMA = PROFILE / "repo.meta.schema.json"

# Reuse the canonical Track-A validator so the schema-check path stays
# in one place (matches the phase0-smoke pattern).
_validator_path = Path(__file__).with_name("validate-repo-meta.py")
_spec = importlib.util.spec_from_file_location("_validate_repo_meta", _validator_path)
_validate_repo_meta = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_validate_repo_meta)


# ----- the canonical TIER_1 + TIER_2 + TIER_3 list (nine onboarded repos) ---

TIER_1 = [
    "https://raw.githubusercontent.com/m-dev-tools/m-cli/main/dist/repo.meta.json",
    "https://raw.githubusercontent.com/m-dev-tools/m-stdlib/main/dist/repo.meta.json",
    "https://raw.githubusercontent.com/m-dev-tools/m-standard/main/dist/repo.meta.json",
]

TIER_2 = [
    "https://raw.githubusercontent.com/m-dev-tools/tree-sitter-m/main/dist/repo.meta.json",
    "https://raw.githubusercontent.com/m-dev-tools/m-test-engine/main/dist/repo.meta.json",
    "https://raw.githubusercontent.com/m-dev-tools/m-modern-corpus/main/dist/repo.meta.json",
]

TIER_3 = [
    "https://raw.githubusercontent.com/m-dev-tools/tree-sitter-m-vscode/main/dist/repo.meta.json",
    "https://raw.githubusercontent.com/m-dev-tools/m-stdlib-vscode/main/dist/repo.meta.json",
    "https://raw.githubusercontent.com/m-dev-tools/m-cli-extras/main/dist/repo.meta.json",
]

# Top-level keys we copy from the prior tools.json verbatim. These hold
# hand-curated narrative that the catalog generator doesn't synthesise.
CARRIED_TOP_LEVEL = (
    "$schema",
    "schema_compat",
    "schema_version",
    "kind",
    "description",
    "org",
    "workflow",
    "discovery_protocol",
)

_RAW_META_RE = re.compile(
    r"^(https?://raw\.githubusercontent\.com/[^/]+/([^/]+)/([^/]+))/dist/repo\.meta\.json$"
)

URL_RE = re.compile(r"^https?://")


# --------------------------------------------------------------- url helpers


def repo_root_url(meta_url: str) -> str:
    """Given `.../<org>/<repo>/<branch>/dist/repo.meta.json`, return
    `.../<org>/<repo>/<branch>/` with trailing slash.

    Falls back to one-segment-up if the URL doesn't end in the canonical
    suffix (defensive — callers should pass canonical URLs).
    """
    suffix = "/dist/repo.meta.json"
    if meta_url.endswith(suffix):
        return meta_url[: -len(suffix)] + "/"
    return meta_url.rsplit("/", 1)[0] + "/"


def github_blob_url(meta_url: str, relative: str) -> str:
    """Translate a raw.githubusercontent.com manifest URL + a relative
    path into a human-facing github.com/<org>/<repo>/blob/<branch>/<path>
    URL. Used for `agent_instructions` since the baseline tools.json
    points humans at blob URLs (rendered Markdown), not raw URLs.

    If the manifest URL doesn't match the canonical raw-github shape,
    falls back to resolving against the repo-root raw URL.
    """
    m = _RAW_META_RE.match(meta_url)
    if not m:
        return repo_root_url(meta_url) + relative.lstrip("/")
    _, repo, branch = m.group(1), m.group(2), m.group(3)
    org_repo = m.group(0)  # full original — unused beyond the regex bookkeeping
    # Extract the org from the matched prefix manually.
    # Prefix: https://raw.githubusercontent.com/<org>/<repo>/<branch>
    prefix = m.group(1)  # captured group 1 is the full repo-root prefix
    parts = prefix.split("/")
    # parts: ['https:', '', 'raw.githubusercontent.com', '<org>', '<repo>', '<branch>']
    if len(parts) < 6:
        return repo_root_url(meta_url) + relative.lstrip("/")
    org, repo_name, branch_name = parts[3], parts[4], parts[5]
    return f"https://github.com/{org}/{repo_name}/blob/{branch_name}/{relative.lstrip('/')}"


def resolve_exposes_value(meta_url: str, value: str) -> str:
    """If `value` is already absolute, pass through. Otherwise resolve
    against the repo-root raw URL of the manifest."""
    if URL_RE.match(value):
        return value
    return repo_root_url(meta_url) + value.lstrip("/")


# ------------------------------------------------------------------ fetching


def network_fetcher(url: str) -> str:
    """Default fetcher: HTTP GET, 20s timeout, UTF-8 decode."""
    with urllib.request.urlopen(url, timeout=20) as resp:
        return resp.read().decode("utf-8")


def _fetch(fetcher: Callable[[str], str] | dict, url: str) -> str:
    """Indirection: tests pass a dict (URL → body); production uses
    `network_fetcher` (a callable). Either is accepted."""
    if isinstance(fetcher, dict):
        if url not in fetcher:
            raise KeyError(f"fixture fetcher has no entry for {url}")
        return fetcher[url]
    return fetcher(url)


# ----------------------------------------------------- manifest → tool entry


def _validate_manifest(meta: dict, url: str) -> None:
    """Validate `meta` against repo.meta.schema.json. Raises ValueError
    with the URL in the message on failure."""
    errors: list[str] = []
    _validate_repo_meta.validate_schema(meta, errors)
    if errors:
        joined = "; ".join(errors)
        repo_hint = meta.get("id") or meta.get("repo") or url
        raise ValueError(f"manifest at {url} ({repo_hint}) failed schema check: {joined}")


def translate_manifest(meta: dict, url: str) -> tuple[str, dict]:
    """Translate a `repo.meta.json` payload + its source URL into a
    `(tools_key, entry_dict)` pair suitable for inclusion under
    `tools.<key>` in the generated catalog.

    The `tools_key` is the bare repo name (typed-ID prefix stripped):
    `tool:m-cli` → `"m-cli"`.
    """
    _validate_manifest(meta, url)

    typed_id = meta["id"]
    if not typed_id.startswith("tool:"):
        raise ValueError(f"manifest at {url} has non-tool id: {typed_id!r}")
    key = typed_id[len("tool:") :]

    # Language: collapse single-element arrays back to a string so the
    # generated catalog matches the post-P1-A baseline's shape (the
    # schema accepts both forms via oneOf).
    lang = meta["language"]
    if isinstance(lang, list) and len(lang) == 1:
        lang_out: str | list[str] = lang[0]
    else:
        lang_out = list(lang) if isinstance(lang, list) else lang

    entry: dict = {
        "id": typed_id,
        "repo": meta["repo"],
        "role": meta["role"],
        "language": lang_out,
        "license": meta["license"],
        "agent_instructions": github_blob_url(url, meta["agent_instructions"])
        if not URL_RE.match(meta["agent_instructions"])
        else meta["agent_instructions"],
        "verified_on": meta["verified_on"],
        "status": meta.get("status", "active"),
        "repo_meta_url": url,
    }

    # Translate each exposes.<kind> into <kind>_url.
    for kind, path in meta.get("exposes", {}).items():
        entry[f"{kind}_url"] = resolve_exposes_value(url, path)

    # Passthrough consumes / consumed_by if present.
    if "consumes" in meta:
        entry["consumes"] = list(meta["consumes"])
    if "consumed_by" in meta:  # not in current repo.meta schema but defensive
        entry["consumed_by"] = list(meta["consumed_by"])

    return key, entry


# -------------------------------------------------------- top-level assembly


def build(
    urls: list[str],
    fetcher: Callable[[str], str] | dict,
    prior_tools: dict,
) -> dict:
    """Assemble the full generated tools.json dict.

    - Carries CARRIED_TOP_LEVEL keys from `prior_tools` verbatim.
    - Generates `tools` from `urls` via translate_manifest.
    - Never emits `task_index` (post-P1-A contract).
    """
    out: dict = {}
    for key in CARRIED_TOP_LEVEL:
        if key in prior_tools:
            out[key] = prior_tools[key]

    tools: dict[str, dict] = {}
    for url in urls:
        body = _fetch(fetcher, url)
        meta = json.loads(body)
        tools_key, entry = translate_manifest(meta, url)
        if tools_key in tools:
            raise ValueError(f"duplicate tool key {tools_key!r} (second source: {url})")
        tools[tools_key] = entry
    out["tools"] = tools

    return out


def dumps(catalog: dict) -> str:
    """Serialise deterministically: sorted keys, 2-space indent, trailing newline.

    json.dumps(sort_keys=True) sorts dict keys recursively, which is
    exactly the determinism property we want. Trailing newline keeps
    POSIX text-file convention so `git diff` doesn't whinge.
    """
    return json.dumps(catalog, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


# ----------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    parser.add_argument(
        "--write",
        type=Path,
        default=None,
        help="Write the generated tools.json here (default: stdout).",
    )
    parser.add_argument(
        "--prior",
        type=Path,
        default=PRIOR_TOOLS_DEFAULT,
        help=f"Prior tools.json — narrative keys are copied from it. (default: {PRIOR_TOOLS_DEFAULT})",
    )
    parser.add_argument(
        "--no-network",
        action="store_true",
        help="Dry-run: skip manifest fetches; emit only the prior tools.json's framing.",
    )
    parser.add_argument(
        "--urls",
        nargs="+",
        help="Override the TIER_1 + TIER_2 + TIER_3 URL list.",
    )
    args = parser.parse_args(argv)

    try:
        prior_tools = json.loads(args.prior.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read --prior {args.prior}: {exc}", file=sys.stderr)
        return 1

    if args.no_network:
        urls: list[str] = []
    elif args.urls:
        urls = list(args.urls)
    else:
        urls = TIER_1 + TIER_2 + TIER_3

    try:
        catalog = build(urls, network_fetcher, prior_tools)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        print(f"ERROR: network fetch failed: {exc}", file=sys.stderr)
        return 1
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    text = dumps(catalog)
    if args.write:
        args.write.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
