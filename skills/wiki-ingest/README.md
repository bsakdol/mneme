# wiki-ingest

A Claude Code skill that ingests a source — URL, file, or pasted text — into your LLM Wiki vault. It works from any directory, so you can add to your wiki without leaving the project you're currently working in.

---

## What This Skill Does

1. Resolves your target vault (from the current project context, your configured default, or a vault you name inline)
2. Reads the vault's `CLAUDE.md` operating schema to ground all ingest decisions
3. Accepts the source — URL, file path, or pasted text
4. Follows the vault's Ingest Workflow: fetches and archives the source, surfaces key takeaways for your review, waits for confirmation, then creates the appropriate wiki pages and updates bookkeeping

All ingest behavior — page structure, frontmatter, classification rules, linking conventions — is governed by the vault's own `CLAUDE.md`. The skill provides vault context; the schema does the rest.

---

## Prerequisites

- **A configured vault** — run `mneme:wiki-setup` first if you haven't already
- **Claude Code** (CLI or desktop app) running with the `mneme` plugin installed

---

## Installation

This skill is distributed as part of the `mneme` plugin.

---

## Invocation

### With a source inline

```
mneme:wiki-ingest https://example.com/some-article
```

```
mneme:wiki-ingest raw/articles/2026-06-08-my-notes.md
```

### Without a source (interactive)

```
mneme:wiki-ingest
```

The skill will ask what you'd like to ingest.

### Into a specific vault

When you have multiple vaults configured, name the target explicitly:

```
mneme:wiki-ingest https://example.com/article into work-vault
```

If you don't specify a vault, the skill auto-resolves one using the order below.

---

## Vault Selection

The skill resolves the target vault in this priority order:

| Priority | Source | How it's set |
|----------|--------|--------------|
| 1 | Inline — `into <vault-name>` in the invocation | Typed in the command |
| 2 | Global default — `default_vault` in `~/.config/mneme/settings.json` | Set via `mneme:wiki-setup` or `mneme:wiki-config` |

If no default is configured and no vault is named, the skill exits with a message directing you to `mneme:wiki-setup` or `mneme:wiki-config`.

---

## What You Get

After a confirmed ingest:

- A new **reference** or **solution** page in `wiki/references/` or `wiki/solutions/`
- The source archived under `raw/<category>/YYYY-MM-DD-<slug>.<ext>`
- Any new or updated **entity** and **concept** pages linked from the reference
- An updated entry in `index.md`
- A new entry appended to `log.md`

The exact page structure (sections, frontmatter fields, linking conventions) follows the vault's `CLAUDE.md` schema. No pages are written until you confirm the proposed ingest plan.

---

## Troubleshooting

**"No mneme vaults configured."**
Run `mneme:wiki-setup` to create and register your first vault.

**"Vault `<name>` not found."**
The vault name you specified isn't registered. Check `~/.config/mneme/settings.json`, or run `mneme:wiki-config` to register or rename vaults.

**The skill exits saying no default is configured.**
Make a vault the default via `mneme:wiki-config`, or name the vault inline: `mneme:wiki-ingest into <vault-name>`.
