---
kind: ai-discoverability-repo-inventory
schema_version: "1"
maturity_levels: [M0, M1, M2, M3, M4, M5]
---

# Repo Inventory

This file tracks metadata maturity across all `m-dev-tools` repositories. Use
it during Phase 2 and update it whenever a repo gains new machine-readable
metadata, validation, or CI drift checks.

## Maturity Levels

| Level | Meaning |
|---|---|
| `M0` | Prose only |
| `M1` | Has local AI instructions |
| `M2` | Has machine-readable metadata |
| `M3` | Metadata is schema-validated |
| `M4` | Org catalog generated from metadata |
| `M5` | CI prevents metadata drift |

## Inventory

| Repo | Role | CLAUDE.md/AGENTS.md | Manifest | JSON Capabilities | Schema | CI Drift Check | Catalog Source | Maturity | Notes |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| `.github` | Org profile, catalog, tracking | no | `tools.json` | partial | `tools.schema.json` | no | manual | M2 | Add validation script and CI |
| `m-cli` | Canonical `m` command surface | yes | partial | no | no | no | manual | M1 | Needs `m capabilities --json` and `m help --json` |
| `m-stdlib` | STD* runtime library | yes | yes | n/a | partial | partial | manifest | M3 | Manifest should drive catalog summaries |
| `m-standard` | Language facts and grammar surface | yes | yes | n/a | partial | partial | integrated outputs | M3 | Owns language semantics |
| `tree-sitter-m` | Parser and bindings | unknown | partial | unknown | unknown | unknown | manual | M1 | Audit required |
| `m-test-engine` | YottaDB test container | unknown | no | no | no | no | manual | M0 | Needs minimal tool metadata |
| `m-cli-extras` | Out-of-tree m-cli plugins | unknown | no | partial | no | no | manual | M1 | Plugin entry points should be discoverable |
| `tree-sitter-m-vscode` | VS Code syntax/LSP client | yes | package metadata | partial | no | no | manual | M2 | Audit extension contribution metadata |
| `m-stdlib-vscode` | VS Code STD* hover/completion | unknown | package metadata | partial | no | no | manual | M2 | Audit manifest discovery behavior |
| `m-modern-corpus` | Validation corpus | unknown | no | no | no | no | manual | M0 | Needs corpus metadata summary |
| `m-tools` | Archived historical seed | yes | no | no | no | no | manual | M1 | Historical docs only |

## Audit Instructions

For each repo:

1. Confirm README location and quality.
2. Confirm `CLAUDE.md` or `AGENTS.md`.
3. Identify machine-readable metadata.
4. Identify schema or validation.
5. Identify CI drift checks.
6. Record gaps in `discoveries.md` or `remediation-backlog.md`.
7. Update maturity level.

