---
name: wiki-lint
description: Lint an mneme LLM Wiki vault for structural consistency — frontmatter drift, broken/dangling links, and tag sprawl. Use when the owner says "lint the wiki", "lint my vault", "check frontmatter", "check links", "check tags", or invokes mneme:wiki-lint. Runs the bundled Obsidian-aware checker, applies safe fixes (unique-candidate broken-link slug corrections, nested-topic parent corrections) on approval, and surfaces judgment-tier items. Operates on the default vault registered in ~/.config/mneme/settings.json unless the owner names a vault. Standalone — it never invokes another skill; it suggests the next one.
---

# Wiki Lint

Detect and (on approval) fix **structural consistency** issues in an mneme LLM Wiki vault: frontmatter, links, and tags. This is the first stage of the maintenance order of operations: **wiki-lint → wiki-audit → wiki-gaps**.

You are running inside the user's Claude Code session. Be concise. Use `AskUserQuestion` for every choice.

## Step 1 — Resolve the vault

If the owner named a vault (path or registered name), use it as `VAULT_PATH`.

**Otherwise**, resolve the default vault:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/resolve-vault.sh"
```

Branch on the token printed:

| Token | Action |
|-------|--------|
| `VAULT_PATH:<path>` | Set `VAULT_PATH`. Announce the target vault briefly, then continue. |
| `NO_DEFAULT` | No default vault is set. Tell the owner to run `mneme:wiki-config` or name a vault, then stop. |
| `NOT_CONFIGURED` | No vault is registered. Tell the owner to run `mneme:wiki-setup` first, then stop. |

## Step 2 — Read the vault's operating schema

Read `VAULT_PATH/CLAUDE.md` fully before acting. It is the authority for what a valid page looks like (page types, frontmatter, naming, linking). Do not assume the schema — read it.

## Step 3 — Run the checker

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/wiki-lint/scripts/lint_checks.py" "<VAULT_PATH>" --report
```

This prints JSON: `{schema_version, category, counts, findings:[{id, category, dimension, tier, page, detail, proposed_action}]}`. Each finding carries a `tier` of `safe`, `low-risk`, or `judgment`.

## Step 4 — Present the findings

Summarize in chat, grouped by tier:

- **Safe** (one correct outcome, auto-fixable): unique-candidate broken-link slug fixes, nested-topic `parent:` corrections.
- **Judgment** (you decide): missing frontmatter, bare-`?` values, dangling one-off links, `source_paths:` pointing at missing raw files, single-use and near-synonym tags, duplicate slugs (same stem in two folders — an ambiguous link target).

Give counts per dimension and list the notable items. Keep it scannable.

## Step 5 — Offer to apply safe fixes

If there are any `safe`-tier findings, use `AskUserQuestion`:

- **Apply safe fixes (Recommended)** — run the fixer below, then report exactly what changed.
- **Review each first** — walk the safe findings one at a time.
- **Skip fixes** — leave everything for the report.

To apply:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/wiki-lint/scripts/lint_checks.py" "<VAULT_PATH>" --fix-safe
```

It prints `{applied:[...], skipped:[...]}`. Relay the applied list. The fixer is idempotent and never touches judgment-tier findings. (There are currently no low-risk-tier lint fixes; `--fix-lowrisk` is a no-op.)

## Step 6 — Guide the judgment items

For judgment-tier findings, do not auto-change anything. Offer, via `AskUserQuestion`, to either work a cluster interactively now (e.g. fill missing frontmatter, fix a mislinked target) or leave them for `mneme:wiki-triage`. Honor the vault's hygiene rules — never delete a page without confirmation, bump `updated:` on edits, no fabrication.

## Step 7 — Bookkeeping

Append one entry to `VAULT_PATH/log.md` using the schema's log format with action `lint`, noting counts and what was applied.

## Step 8 — Handoff

Close with a short "Next steps" offer (a suggestion, not an automatic action):

> Lint done. Next in the maintenance pass: **`mneme:wiki-audit`** (stale/thin/inconsistent pages), then **`mneme:wiki-gaps`** (pages that should exist). For a hands-off sweep of all three plus a written report, dispatch the **`wiki-steward`** agent.
