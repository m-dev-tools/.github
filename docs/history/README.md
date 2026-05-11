# Historical documents

Frozen, in-org copies of design documents from now-archived repositories in
the `m-dev-tools` org. The original repos remain read-only on GitHub; these
copies exist so the *why* behind the current org shape stays discoverable
inside `.github` itself, immune to upstream pruning or renames.

These documents are **not maintained**. They reflect the state of the world
at the moment they were imported. For the *current* shape of the org, start
at [`profile/README.md`](../../profile/README.md) and
[`profile/tools.json`](../../profile/tools.json).

## Contents

| Document | Source | Imported from commit | Why it's preserved |
|---|---|---|---|
| [`m-tool-gap-analysis.md`](m-tool-gap-analysis.md) | `m-dev-tools/m-tools/docs/m-tool-gap-analysis.md` | [`16fe3f7`](https://github.com/m-dev-tools/m-tools/commit/16fe3f7dc6982070809cd1d8290d01fedc5905ac) (2026-04-27) | The Go/Rust/Python toolchain comparison that produced the `m <subcommand>` design and `m-cli`'s CLI ergonomics. |
| [`m-tooling-tier1.md`](m-tooling-tier1.md) | `m-dev-tools/m-tools/docs/m-tooling-tier1.md` | [`16fe3f7`](https://github.com/m-dev-tools/m-tools/commit/16fe3f7dc6982070809cd1d8290d01fedc5905ac) (2026-04-27) | The scoped Tier-1 strategy that defined what `m-cli` shipped first (fmt / lint / test / coverage / watch / LSP). |
| [`gap-analysis-and-remediation-strategy.md`](gap-analysis-and-remediation-strategy.md) | `m-dev-tools/m-tools/docs/gap-analysis-and-remediation-strategy.md` | [`16fe3f7`](https://github.com/m-dev-tools/m-tools/commit/16fe3f7dc6982070809cd1d8290d01fedc5905ac) (2026-04-27) | The phased remediation roadmap that produced both `m-cli` and `m-stdlib`. |

## Provenance policy

- **Imported verbatim**, with a single `> Archived snapshot.` banner added
  after each H1 to make the rehosting fact visible inline.
- **No rewrites, no link-rot patching**, except where a *sibling-doc* link
  pointed at a file we did not rehost — those links were retargeted at the
  archived upstream repo (read-only) so they still resolve.
- **Typed IDs** for these documents live under
  [`profile/task_index.json`](../../profile/task_index.json) (category
  `history`). The grammar is `doc:m-dev-tools#<filename-without-extension>`.

## Adding a new historical doc

Trigger: another repo in the org is archived and contains design rationale
that future agents/contributors will benefit from reading.

1. Copy the file(s) verbatim into this directory.
2. Add the `> Archived snapshot.` banner immediately after the H1, citing
   the source repo, source commit hash, and date.
3. Append a row to the table above.
4. Add a `doc:m-dev-tools#<slug>` typed ID to `task_index.json` under
   the `history` category, with an `intent` line that names the
   plain-English question the doc answers.
5. Run `make validate-catalog` to confirm the typed IDs validate.
6. Open a PR titled `chore(history): rehost <repo>/<path>`.

## Not on this list

- **`m-tools/docs/implementation.md`** — implementation log; superseded by
  `m-cli/docs/evolution.md` and `m-cli/docs/plans/m-cli-history-and-evolution.md`.
- **`m-tools/docs/ydb-dev-tools-gap-analysis.md`** — 10-line stub; no
  preserved content worth rehosting.

Both remain reachable in the archived `m-tools` repo on GitHub for anyone
who wants the deeper context.
