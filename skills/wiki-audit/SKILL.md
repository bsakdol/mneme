---
name: wiki-audit
description: Audit an mneme LLM Wiki vault for stale, thin, or inconsistent pages — orphans, stubs, stale references, and unresolved conflict callouts. Use when the owner says "audit the vault", "audit the wiki", "find stale pages", "find thin pages", "find orphans", or invokes mneme:wiki-audit. Runs the bundled checker and surfaces findings for the owner to act on; audit findings are all judgment-tier, so nothing is auto-fixed. Also surfaces semantic concerns (stale claims, concept-graduation candidates, investigations) via reasoning over the vault. Operates on the default vault in ~/.config/mneme/settings.json unless a vault is named. Standalone — never invokes another skill.
---

# Wiki Audit

Surface **stale, thin, or inconsistent pages** in an mneme LLM Wiki vault. Second stage of the maintenance order of operations: **wiki-lint → wiki-audit → wiki-gaps**.

Audit findings are all **judgment-tier** — the skill reports and guides; it never auto-deletes, auto-promotes, or rewrites. Use `AskUserQuestion` for every choice.

## Step 1 — Resolve the vault

If the owner named a vault, use it. Otherwise:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/resolve-vault.sh"
```

Branch on the token: `VAULT_PATH:<path>` → set `VAULT_PATH` and continue; `NO_DEFAULT` → tell the owner to run `mneme:wiki-config` or name a vault, then stop; `NOT_CONFIGURED` → tell the owner to run `mneme:wiki-setup`, then stop.

## Step 2 — Read the vault's operating schema

Read `VAULT_PATH/CLAUDE.md` fully — it defines status meanings, the stale-reference rule, the conflict policy, and the concept-graduation bar you will reason against.

## Step 3 — Run the deterministic checker

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/wiki-audit/scripts/audit_checks.py" "<VAULT_PATH>" --report
```

Dimensions (all judgment-tier): `orphan` (zero inbound links), `stub` (status: stub, with inbound count), `stale-reference` (reference `last_checked` absent or older than 6 months), `conflict-callout` (unresolved `> [!conflict]`).

## Step 4 — Add the semantic reasoning pass

The deterministic checker can't catch everything the schema's Lint/maintenance intent covers. Read the relevant pages and reason about:

- **Stale claims** — places where a newer source has superseded an older claim still phrased as current.
- **Concept-graduation candidates** — a pattern that now meets the vault's graduation bar (two distinct projects, or one project plus one external reference) but still lives on a project/solution page instead of its own concept page.
- **Suggested investigations** — open questions worth filing or sources worth seeking.

These are model-judgment findings; present them alongside the deterministic ones, clearly labeled.

## Step 5 — Present and guide

Summarize all findings in chat, grouped by dimension with counts. Then use `AskUserQuestion` per cluster to either act on items now (with the owner present, honoring hygiene rules — never delete without confirmation, bump `updated:`, no fabrication) or leave them for `mneme:wiki-triage`.

## Step 6 — Bookkeeping

Append one `log.md` entry with action `lint` (the schema's maintenance action), noting counts and anything actioned.

## Step 7 — Handoff

> Audit done. Next: **`mneme:wiki-gaps`** (pages that should exist). For a hands-off sweep of all three categories plus a written report, dispatch the **`wiki-steward`** agent, then work the report with **`mneme:wiki-triage`**.
