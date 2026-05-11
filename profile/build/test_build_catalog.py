"""Tests for build-catalog.py — TDD: B3 (RED) before B4 (GREEN).

Strategy: the script is built around a `build(urls, fetcher,
prior_tools) -> dict` entry point. Tests inject a `fetcher` that maps
URL → string body (simulating raw.githubusercontent.com fetches), and a
`prior_tools` dict standing in for the committed tools.json (which
contributes `org`, `workflow`, `discovery_protocol`, `description`).

Three synthetic `repo.meta.json` fixtures cover the surface:
  * MINIMAL — only the required fields; no `consumes`, no `status`;
    single-element `language` array.
  * RICH — multiple exposes (resolved to *_url pointers), explicit
    `status`, `consumes`, multi-element `language`.
  * EXTRA_EXPOSES — exposes a kind the prior tools.json didn't carry
    (proves the build script is data-driven from manifests, not from a
    hardcoded allow-list).

Determinism (B5) is asserted explicitly: building twice produces
byte-identical output.

Drift detection: a separate test compares the live-fetched build output
against the committed tools.json (network gated — skipped if no network).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE = REPO_ROOT / "profile"
BUILD = PROFILE / "build"

_builder_path = BUILD / "build-catalog.py"
_spec = importlib.util.spec_from_file_location("_build_catalog", _builder_path)
_build_catalog = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_build_catalog)

import importlib.util as _iu

_v_spec = _iu.spec_from_file_location("_validate_catalog", BUILD / "validate-catalog.py")
_validate_catalog = _iu.module_from_spec(_v_spec)
assert _v_spec and _v_spec.loader
_v_spec.loader.exec_module(_validate_catalog)


# ----------------------------------------------------------------- fixtures -

# Synthetic raw-GitHub URLs for fixtures. The base is the same shape
# as production (raw.githubusercontent.com/<org>/<repo>/main/...) so
# the URL-construction logic gets exercised end-to-end.

URL_MIN = "https://raw.githubusercontent.com/m-dev-tools/min-tool/main/dist/repo.meta.json"
URL_RICH = "https://raw.githubusercontent.com/m-dev-tools/rich-tool/main/dist/repo.meta.json"
URL_EXTRA = "https://raw.githubusercontent.com/m-dev-tools/extra-tool/main/dist/repo.meta.json"

MIN_META = {
    "$schema": "https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/repo.meta.schema.json",
    "id": "tool:min-tool",
    "repo": "https://github.com/m-dev-tools/min-tool",
    "role": "Minimal synthetic fixture for build-catalog tests.",
    "language": ["python"],
    "license": "AGPL-3.0",
    "agent_instructions": "AGENTS.md",
    "verified_on": "2026-05-10",
    "exposes": {
        "manifest": "dist/manifest.json",
    },
    "verification_commands": ["make check"],
}

RICH_META = {
    "$schema": "https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/repo.meta.schema.json",
    "id": "tool:rich-tool",
    "repo": "https://github.com/m-dev-tools/rich-tool",
    "role": "Rich synthetic fixture exercising consumes, multi-language, status, multiple exposes.",
    "language": ["python", "c", "rust"],
    "license": "MIT",
    "agent_instructions": "AGENTS.md",
    "verified_on": "2026-05-10",
    "exposes": {
        "commands": "dist/commands.json",
        "lint_rules": "dist/lint-rules.json",
        "fmt_rules": "dist/fmt-rules.json",
    },
    "consumes": ["tool:min-tool"],
    "verification_commands": ["make check", "make check-manifest"],
    "status": "active",
    "notes": "rich fixture",
}

EXTRA_META = {
    "$schema": "https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/repo.meta.schema.json",
    "id": "tool:extra-tool",
    "repo": "https://github.com/m-dev-tools/extra-tool",
    "role": "Fixture exposing a kind never seen before — proves data-driven *_url emission.",
    "language": ["m"],
    "license": "AGPL-3.0",
    "agent_instructions": "AGENTS.md",
    "verified_on": "2026-05-10",
    "exposes": {
        "weird_payload_kind": "dist/weird.json",
    },
    "verification_commands": ["make check"],
}


def _meta_at_branch_url(meta_url: str) -> str:
    """Strip /dist/repo.meta.json to get the repo-root raw URL (with trailing slash)."""
    suffix = "/dist/repo.meta.json"
    assert meta_url.endswith(suffix), f"unexpected manifest URL shape: {meta_url}"
    return meta_url[: -len(suffix)] + "/"


PRIOR_TOOLS = {
    "$schema": "https://raw.githubusercontent.com/m-dev-tools/.github/main/profile/tools.schema.json",
    "schema_compat": 1,
    "schema_version": "1.0",
    "kind": "m-dev-tools.org-catalog",
    "description": "Carried over from prior tools.json — narrative kept by build-catalog.",
    "org": {
        "name": "m-dev-tools",
        "url": "https://github.com/m-dev-tools",
        "tagline": "Engine-neutral M (MUMPS) developer tools.",
    },
    "tools": {},
    "workflow": {
        "tdd_inner_loop": {
            "description": "Canonical TDD loop.",
            "steps": [{"n": 1, "action": "scaffold", "command": "m new myproj"}],
        }
    },
    "discovery_protocol": {
        "step_1_read": ["llms.txt", "tools.json", "task_index.json"],
    },
}


@pytest.fixture
def fetcher():
    """Mock fetcher: dict-keyed-by-URL → JSON-text body."""
    return {
        URL_MIN: json.dumps(MIN_META),
        URL_RICH: json.dumps(RICH_META),
        URL_EXTRA: json.dumps(EXTRA_META),
    }


# ------------------------------------------------------------ basic shape ---


def test_build_emits_required_top_level_keys(fetcher):
    out = _build_catalog.build([URL_MIN, URL_RICH], fetcher, PRIOR_TOOLS)
    for key in ("$schema", "schema_compat", "schema_version", "kind", "description",
                "org", "tools", "workflow", "discovery_protocol"):
        assert key in out, f"missing required top-level key: {key}"


def test_build_does_not_emit_task_index(fetcher):
    """Post-P1-A contract: task_index lives in its own file."""
    out = _build_catalog.build([URL_MIN, URL_RICH], fetcher, PRIOR_TOOLS)
    assert "task_index" not in out


def test_build_preserves_hand_curated_top_level(fetcher):
    out = _build_catalog.build([URL_MIN, URL_RICH], fetcher, PRIOR_TOOLS)
    assert out["org"] == PRIOR_TOOLS["org"]
    assert out["workflow"] == PRIOR_TOOLS["workflow"]
    assert out["discovery_protocol"] == PRIOR_TOOLS["discovery_protocol"]
    assert out["description"] == PRIOR_TOOLS["description"]


# ----------------------------------------------------------- tool translation


def test_minimal_meta_translates_to_summary_entry(fetcher):
    out = _build_catalog.build([URL_MIN], fetcher, PRIOR_TOOLS)
    assert "min-tool" in out["tools"]
    entry = out["tools"]["min-tool"]
    assert entry["id"] == "tool:min-tool"
    assert entry["repo"] == "https://github.com/m-dev-tools/min-tool"
    assert entry["role"] == MIN_META["role"]
    # Single-element language array collapses to a string (matches baseline shape)
    assert entry["language"] == "python"
    assert entry["license"] == "AGPL-3.0"
    assert entry["verified_on"] == "2026-05-10"
    assert entry["status"] == "active"  # default
    assert entry["repo_meta_url"] == URL_MIN
    # agent_instructions: relative path resolved against the repo's blob/main/ base
    assert entry["agent_instructions"].endswith("/AGENTS.md")
    assert "github.com/m-dev-tools/min-tool" in entry["agent_instructions"]
    # exposes.manifest → manifest_url, resolved against repo-root raw URL
    expected_manifest_url = _meta_at_branch_url(URL_MIN) + "dist/manifest.json"
    assert entry["manifest_url"] == expected_manifest_url


def test_rich_meta_translates(fetcher):
    out = _build_catalog.build([URL_RICH], fetcher, PRIOR_TOOLS)
    entry = out["tools"]["rich-tool"]
    # Multi-element language stays as array
    assert entry["language"] == ["python", "c", "rust"]
    assert entry["license"] == "MIT"
    assert entry["consumes"] == ["tool:min-tool"]
    # All three exposes turned into *_url pointers
    base = _meta_at_branch_url(URL_RICH)
    assert entry["commands_url"] == base + "dist/commands.json"
    assert entry["lint_rules_url"] == base + "dist/lint-rules.json"
    assert entry["fmt_rules_url"] == base + "dist/fmt-rules.json"


def test_extra_exposes_kind_passes_through(fetcher):
    """The script must not hardcode an allow-list of exposes kinds."""
    out = _build_catalog.build([URL_EXTRA], fetcher, PRIOR_TOOLS)
    entry = out["tools"]["extra-tool"]
    base = _meta_at_branch_url(URL_EXTRA)
    assert entry["weird_payload_kind_url"] == base + "dist/weird.json"


def test_tool_key_strips_typed_id_prefix(fetcher):
    """`tools.<key>` is the bare repo name; `id` carries the typed form."""
    out = _build_catalog.build([URL_RICH], fetcher, PRIOR_TOOLS)
    assert "rich-tool" in out["tools"]
    assert out["tools"]["rich-tool"]["id"] == "tool:rich-tool"


# --------------------------------------------------------- output discipline -


def test_output_is_validatable(fetcher, tmp_path):
    out = _build_catalog.build([URL_MIN, URL_RICH, URL_EXTRA], fetcher, PRIOR_TOOLS)
    out_path = tmp_path / "generated.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    # Reuse the live task_index for this assertion — the generated
    # tools.json must validate cleanly against tools.schema.json.
    errors = _validate_catalog.validate(out_path, PROFILE / "task_index.json")
    assert errors == [], errors


def test_dumps_is_deterministic(fetcher):
    """Same inputs → byte-identical serialisation. The script exposes
    `dumps(catalog)` which fixes sort + indent + trailing newline."""
    out_a = _build_catalog.build([URL_MIN, URL_RICH], fetcher, PRIOR_TOOLS)
    out_b = _build_catalog.build([URL_RICH, URL_MIN], fetcher, PRIOR_TOOLS)  # input order shuffled
    assert _build_catalog.dumps(out_a) == _build_catalog.dumps(out_b)


def test_dumps_has_trailing_newline_and_sorted_keys(fetcher):
    out = _build_catalog.build([URL_MIN, URL_RICH], fetcher, PRIOR_TOOLS)
    text = _build_catalog.dumps(out)
    assert text.endswith("\n")
    # Re-parse and confirm sort order is alphabetical at the top level
    parsed = json.loads(text)
    keys = list(parsed.keys())
    assert keys == sorted(keys), f"top-level keys not sorted: {keys}"


def test_two_runs_byte_identical(fetcher, tmp_path):
    """B5 determinism: running the full pipeline twice produces identical bytes."""
    first = _build_catalog.dumps(_build_catalog.build([URL_MIN, URL_RICH, URL_EXTRA], fetcher, PRIOR_TOOLS))
    second = _build_catalog.dumps(_build_catalog.build([URL_MIN, URL_RICH, URL_EXTRA], fetcher, PRIOR_TOOLS))
    assert first == second


# ---------------------------------------------------------- error reporting -


def test_invalid_manifest_raises(fetcher):
    """A manifest that fails repo.meta.schema.json validation must raise
    a clear error rather than silently producing a malformed entry."""
    fetcher_bad = dict(fetcher)
    bad = dict(MIN_META)
    del bad["repo"]  # required field
    fetcher_bad[URL_MIN] = json.dumps(bad)
    with pytest.raises(Exception) as exc:
        _build_catalog.build([URL_MIN], fetcher_bad, PRIOR_TOOLS)
    # The error message should name the offending URL or the missing key
    assert "min-tool" in str(exc.value) or "repo" in str(exc.value).lower(), exc.value


# --------------------------------------------- P1-D enhancements (inverse + archived)


def test_consumed_by_computed_from_forward_consumes(fetcher):
    """RICH_META declares consumes=['tool:min-tool']. build() should emit
    `consumed_by: ['tool:rich-tool']` on min-tool's entry."""
    out = _build_catalog.build([URL_MIN, URL_RICH], fetcher, PRIOR_TOOLS)
    assert "consumed_by" in out["tools"]["min-tool"]
    assert out["tools"]["min-tool"]["consumed_by"] == ["tool:rich-tool"]
    # rich-tool has no consumer in the fixture set; should NOT have consumed_by.
    assert "consumed_by" not in out["tools"]["rich-tool"]


def test_consumed_by_is_sorted_and_deduplicated(fetcher):
    """When multiple consumers reference the same producer, consumed_by
    is sorted and deduplicated."""
    # Inject a second consumer of min-tool by mutating EXTRA_META in the fetcher.
    fetcher_aug = dict(fetcher)
    extra_with_consumes = dict(EXTRA_META)
    extra_with_consumes["consumes"] = ["tool:min-tool"]
    fetcher_aug[URL_EXTRA] = json.dumps(extra_with_consumes)
    out = _build_catalog.build([URL_MIN, URL_RICH, URL_EXTRA], fetcher_aug, PRIOR_TOOLS)
    consumers = out["tools"]["min-tool"]["consumed_by"]
    assert consumers == sorted(consumers), f"not sorted: {consumers}"
    assert len(consumers) == len(set(consumers)), f"duplicates: {consumers}"
    assert set(consumers) == {"tool:rich-tool", "tool:extra-tool"}


def test_archived_entries_carried_from_prior(fetcher):
    """Repos with `status: 'archived'` in the prior tools.json should be
    carried verbatim into the regenerated output — they don't ship a
    manifest by design (e.g. m-tools)."""
    prior = json.loads(json.dumps(PRIOR_TOOLS))  # deep copy
    prior["tools"] = {
        "archived-thing": {
            "id": "tool:archived-thing",
            "repo": "https://github.com/m-dev-tools/archived-thing",
            "role": "ARCHIVED — historical reference",
            "language": "markdown",
            "license": "AGPL-3.0",
            "agent_instructions": "https://github.com/m-dev-tools/archived-thing/blob/main/README.md",
            "verified_on": "2026-05-10",
            "status": "archived",
            "notes": "Carried over from prior.",
        }
    }
    out = _build_catalog.build([URL_MIN], fetcher, prior)
    assert "archived-thing" in out["tools"], (
        "archived entry from prior tools.json was lost; "
        f"got: {sorted(out['tools'].keys())}"
    )
    archived = out["tools"]["archived-thing"]
    assert archived["status"] == "archived"
    assert archived["id"] == "tool:archived-thing"


def test_non_archived_prior_entries_not_carried(fetcher):
    """Only `status: 'archived'` survives the prior-tools merge. A prior
    `status: 'active'` entry whose manifest is gone should NOT come back
    via this codepath — that'd hide real onboarding regressions."""
    prior = json.loads(json.dumps(PRIOR_TOOLS))
    prior["tools"] = {
        "active-thing": {
            "id": "tool:active-thing",
            "repo": "https://github.com/m-dev-tools/active-thing",
            "role": "Should NOT be carried — no manifest fetched.",
            "language": "python",
            "license": "AGPL-3.0",
            "agent_instructions": "https://...",
            "verified_on": "2026-05-10",
            "status": "active",
        }
    }
    out = _build_catalog.build([URL_MIN], fetcher, prior)
    assert "active-thing" not in out["tools"], (
        "active-status prior entry was silently carried; would hide a "
        "missing manifest. Only archived entries should carry over."
    )
