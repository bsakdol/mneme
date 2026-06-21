---
name: wiki-triage
description: Work an mneme maintenance report — walk the owner through the judgment-required items the wiki-steward agent left open, apply the approved ones, and update the report. Use when the owner says "triage the maintenance report", "work the maintenance to-do list", "resolve the wiki findings", "work the steward report", or invokes mneme:wiki-triage. Reads the latest (or a named) report in meta/maintenance-reports/, presents open items by category, applies what the owner approves following the vault's workflows, and flips each item's status. Operates on the default vault in ~/.config/mneme/settings.json unless a vault is named. Standalone — never invokes another skill.
---

# Wiki Triage

Work the **judgment-required items** in a maintenance report produced by the `wiki-steward` agent. The steward already applied the safe and low-risk fixes; everything left is a decision only the owner can make. Use `AskUserQuestion` for every choice.

## Step 1 — Resolve the vault

If the owner named a vault, use it. Otherwise:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/resolve-vault.sh"
```

Branch on the token: `VAULT_PATH:<path>` → continue; `NO_DEFAULT` → tell the owner to run `mneme:wiki-config` or name a vault, then stop; `NOT_CONFIGURED` → tell the owner to run `mneme:wiki-setup`, then stop.

## Step 2 — Read the vault's operating schema

Read `VAULT_PATH/CLAUDE.md` fully — it is the authority for *how* to action each item (page conventions, the conflict policy, the graduation bar, hygiene rules).

## Step 3 — Locate the report

If the owner named a report, use it. Otherwise pick the most recent:

```bash
ls -1 "$VAULT_PATH/meta/maintenance-reports/" | sort | tail -1
```

If the directory is empty or missing, there's nothing to triage — tell the owner to dispatch the `wiki-steward` agent first, then stop.

## Step 4 — Read and filter to open items

Read the report. Each finding is one line:

```
- [ ] <id> · <tier> · <page> — <detail> → <action> · status:open
```

Collect the items with `status:open`. If none are open, tell the owner the report is fully worked, suggest a fresh `wiki-steward` pass, and stop.

## Step 5 — Present open items by category

Summarize the open items grouped by category (Lint / Audit / Gaps), with counts. Lead with the highest-leverage clusters (e.g. missing-page candidates referenced by many pages, unresolved conflicts).

## Step 6 — Work each cluster

For each cluster, use `AskUserQuestion` with options **Fix now / Skip / Defer**. When the owner chooses **Fix now**, action the item following the vault's own workflows — create the page (tracing to real sources, cross-linked, `updated:` set), wire an orphan into a topic, merge a tag and update `meta/tags.md`, resolve a conflict per the conflict policy, graduate a concept. Honor hygiene rules: never delete a page without explicit confirmation, never fabricate content, bump `updated:` on every touched page.

## Step 7 — Update the report and bookkeeping

After each item is actioned, update its line in the report:
- **Fixed** → flip the checkbox to `- [x]` and `status:open` → `status:applied`.
- **Skipped** → leave the checkbox and set `status:skipped`.
- **Deferred** → leave it `status:open` for a later pass.

Then: bump `updated:` on touched pages; if you created pages, add them to `index.md` and reconcile the catalog against disk; append one `log.md` entry (action `lint`) summarizing what was actioned.

## Step 8 — Handoff

Report how many items were fixed, skipped, and remain open. If items remain:

> N item(s) still open in this report — re-run `mneme:wiki-triage` any time to continue. For a fresh detection pass, dispatch the **`wiki-steward`** agent.
