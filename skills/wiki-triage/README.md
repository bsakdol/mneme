# wiki-triage

Work the **judgment-required items** in a maintenance report — the human-facing counterpart to the autonomous `wiki-steward` agent.

The steward applies the safe and low-risk fixes and writes a report; wiki-triage walks you through what's left.

## What it does

- Finds the latest (or a named) report in `meta/maintenance-reports/`.
- Presents the open items grouped by category (lint / audit / gaps).
- For each cluster, asks **Fix now / Skip / Defer**, and applies the approved actions following the vault's own workflows and hygiene rules.
- Updates each item's status in the report (`applied` / `skipped` / left `open`), bumps `updated:` on touched pages, reconciles `index.md` for any new pages, and logs the pass.

It never deletes a page without confirmation, never fabricates content, and only acts on what you approve.

## Prerequisites

- A report produced by the `wiki-steward` agent (or run the manual `wiki-lint` → `wiki-audit` → `wiki-gaps` pass first).
- A vault bootstrapped with `mneme:wiki-setup` (or name a vault when you invoke).

## Invocation

```
mneme:wiki-triage
```

or say "triage the maintenance report" / "work the wiki to-do list" in a session.

## What you get

- A guided pass through the open judgment items, applying the ones you approve.
- An updated report (statuses flipped), a reconciled index where pages were created, and a `log.md` entry.
- A count of what was fixed, skipped, and what remains.
