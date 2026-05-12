---
created: 2026-05-12
last_modified: 2026-05-12
revisions: 1
doc_type: [SETUP]
lifecycle: active
owner: rmrich5
title: "Getting started with m-dev-tools"
---

# Getting started with m-dev-tools

Install path for a fresh developer machine, end-to-end through to
a green `m doctor`. Two flavors: a one-line bootstrap installer and
a manual path for users who prefer to step through it.

## Audience

Developers setting up the [m-dev-tools](../../profile/README.md)
toolchain (`m-cli`, `m-stdlib`, `m-test-engine`, …) for the first
time on Linux or macOS.

## Prerequisites

The installer detects these and prints install commands for anything
missing — no `sudo` is ever invoked. You need:

| Tool | Why |
|---|---|
| `git` | Cloning the sibling repos |
| `docker` (daemon reachable) | `m-test-engine` runs YottaDB in a container |
| `python` ≥ 3.12 | `m-cli` is a Python package |
| `uv` | `m-cli`'s venv + dependency manager |
| `make` | Drives the per-repo verification targets |

## Quick install (preferred) — `setup.sh`

The interactive bootstrap installer at
[`setup.sh`](../../setup.sh) handles OS detection, pre-flight
checks, `m-cli` clone, sibling-repo wiring, venv install, engine
boot, and `m doctor` verification in one shot.

```bash
# Review-first form (recommended):
curl -O https://raw.githubusercontent.com/m-dev-tools/.github/main/setup.sh
less ./setup.sh
bash ./setup.sh

# Or, for the convinced:
bash <(curl -fsSL https://raw.githubusercontent.com/m-dev-tools/.github/main/setup.sh)
```

Flags:

- `-y`, `--yes` — non-interactive; accept defaults
- `-d PATH`, `--dir PATH` — install root (default: `~/m-dev-tools`)
- `-h`, `--help` — usage

Idempotent — re-running on an already-installed host skips the
clones and re-verifies via `m doctor`.

## Manual install (alternative)

If you want to step through the install yourself:

```bash
# 1. Clone m-cli (it bootstraps the rest)
git clone https://github.com/m-dev-tools/m-cli ~/m-dev-tools/m-cli
cd ~/m-dev-tools/m-cli

# 2. Let m-cli pull its sibling repos, install the venv, and start
#    the test engine
make bootstrap

# 3. Add m-cli to your PATH (paste into ~/.bashrc or ~/.zshrc)
export PATH="$HOME/m-dev-tools/m-cli/.venv/bin:$PATH"

# 4. Verify
m --version
m doctor
```

`make bootstrap` is the same target `setup.sh` delegates to — the
installer just wraps it with OS detection and pre-flight checks.

## What `m doctor` confirms

- Each sibling repo is on its expected branch and reachable.
- The YottaDB container is running and `docker exec`-reachable.
- `m-stdlib`'s manifest is loadable.
- `m fmt`, `m lint`, `m test`, and `m coverage` round-trip on a
  smoke routine.

A green `m doctor` is the contract: every other `m` subcommand
assumes these invariants.

## Next steps

1. **TDD walkthrough.** Exercise every `m` subcommand end-to-end
   against a small data-analysis app:
   `~/m-dev-tools/m-cli/docs/m-tdd-lifecycle-walkthrough.md`.
2. **Start your own project.**

   ```bash
   mkdir -p ~/m-work && cd ~/m-work
   m new myapp && cd myapp
   m ci init --write
   m test tests
   ```
3. **VS Code (optional).** Install
   [`tree-sitter-m-vscode`](https://github.com/m-dev-tools/tree-sitter-m-vscode)
   for syntax + LSP and
   [`m-stdlib-vscode`](https://github.com/m-dev-tools/m-stdlib-vscode)
   for STD\*-aware hover / goto-def / completion.
4. **AI agents (optional).** If you use Claude Code / Codex /
   Continue, install the MCP server per the
   [AI users guide](../ai-discoverability/ai-users-guide.md) so
   the agent can resolve M-tooling intent without guessing.

## Troubleshooting

If `m doctor` reports a failure, the message tells you which
invariant broke. Common cases:

- **Docker daemon not reachable** — start it (`sudo systemctl start
  docker` on Linux; launch Docker Desktop on macOS).
- **`m-test-engine` container missing** — re-run `make bootstrap`;
  it pulls the image and starts the container.
- **Python venv stale** — `cd ~/m-dev-tools/m-cli && rm -rf .venv &&
  make bootstrap` does a clean reinstall.

For anything else, open an issue at
<https://github.com/m-dev-tools/m-cli/issues> with the full
`m doctor --verbose` output.
