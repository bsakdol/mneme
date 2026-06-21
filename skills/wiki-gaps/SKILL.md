---
name: wiki-gaps
description: Find pages that should exist in an mneme LLM Wiki vault — concepts referenced across many pages with no page of their own, and index/disk count drift. Use when the owner says "find gaps", "find missing pages", "what should exist", "what's missing from the wiki", or invokes mneme:wiki-gaps. Runs the bundled checker; missing-page and count-drift findings are judgment-tier, so the skill reports and guides rather than auto-creating pages. Operates on the default vault in ~/.config/mneme/settings.json unless a vault is named. Standalone — never invokes another skill.
---

# Wiki Gaps

Surface **pages that should exist but don't**, and catalog drift, in an mneme LLM Wiki vault. Third stage of the maintenance order of operations: **wiki-lint → wiki-audit → wiki-gaps**.

Findings are **judgment-tier** — the skill never auto-creates pages or rewrites the index without the owner. Use `AskUserQuestion` for every choice.

## Step 1 — Resolve the vault

If the owner named a vault, use it. Otherwise:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/resolve-vault.sh"
```

Branch on the token: `VAULT_PATH:<path>` → set `VAULT_PATH` and continue; `NO_DEFAULT` → tell the owner to run `mneme:wiki-config` or name a vault, then stop; `NOT_CONFIGURED` → tell the owner to run `mneme:wiki-setup`, then stop.

## Step 2 — Read the vault's operating schema

Read `VAULT_PATH/CLAUDE.md` fully — it defines the concept-graduation bar (when a referenced pattern earns its own page) and the index.md format you reconcile against.

## Step 3 — Run the checker

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/wiki-gaps/scripts/gaps_checks.py" "<VAULT_PATH>" --report
```

Pass `--min-refs N` to change how many referrers make a dangling target count as a missing page (default 3, matching the schema's "3+ references" bar).

Dimensions (judgment-tier): `missing-page` (a `[[target]]` referenced by N+ pages with no page) and `count-drift` (index.md per-type counts disagree with disk).

## Step 4 — Present and guide

Summarize in chat:

- **Missing pages** — list each candidate with its referrer count. For each, the question is whether it has met the graduation bar in `CLAUDE.md` and deserves a concept/entity page, or whether the references should point elsewhere.
- **Count drift** — where the index and disk disagree.

Use `AskUserQuestion` to offer, per cluster: create a page now (with the owner present — follow the ingest/page conventions, cross-link it, bump `updated:`), reconcile the index against disk, or leave items for `mneme:wiki-triage`. Never fabricate page content — a new page must trace to real sources or be marked a stub.

## Step 5 — Bookkeeping

Append one `log.md` entry with action `lint`, noting counts and anything created or reconciled. If you reconciled the index, say so.

## Step 6 — Handoff

> Gaps done — that completes the manual maintenance pass (lint → audit → gaps). For an unattended sweep that applies the safe fixes and writes a prioritized report, dispatch the **`wiki-steward`** agent; then work the report's judgment items with **`mneme:wiki-triage`**.
