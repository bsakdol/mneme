# wiki-update

Bring an existing mneme vault's schema up to the plugin's current bundled schema — **without losing your hand-edits and without touching your knowledge content**.

When `mneme:wiki-setup` bootstraps a vault, it writes the schema (`CLAUDE.md` + the nine page templates) into the vault as a frozen, personalized snapshot. When the plugin's schema later evolves, your vault doesn't get the update automatically. `wiki-update` closes that gap.

## What it does

1. **Detects drift** — compares your vault's `CLAUDE.md` `schema_version` against the bundled schema. If you're already current (or *ahead* of the installed plugin), it tells you and stops.
2. **Recovers your owner name** — from `settings.json` (recorded by newer `wiki-setup` runs), or by extracting it from your `CLAUDE.md` and asking you to confirm. The confirmed name is saved back so future updates are seamless.
3. **Backs up first** — copies your current `CLAUDE.md` and all nine templates into `meta/backups/<timestamp>/` before writing anything.
4. **Merges, preserving your edits** — reconstructs the exact schema you started from (the archived template at your version) and performs a version-aware **3-way merge**, so schema improvements land while your hand-edits are kept. Where an edit collides with a schema change, it surfaces the conflict and lets you choose.
5. **Refreshes templates and folders** — updates unmodified page templates, asks before overwriting ones you've changed, and additively creates any new schema folders. Never deletes anything.

### Safety contract

- **Your content is never touched.** `raw/`, `wiki/`, `index.md`, `log.md`, and `meta/tags.md` are out of scope — only the schema (`CLAUDE.md` + `meta/templates/`) is migrated.
- **Always reversible.** Every run backs up the schema files first and prints the one-line restore command in its report.
- **Hand-edits are preserved or surfaced.** A clean 3-way merge keeps your edits silently; a conflicting edit is shown to you, never silently discarded.
- **Atomic write.** The new `CLAUDE.md` is written via temp-file-and-rename, so an interrupted run can't leave a half-merged file.

When the plugin has no archived base for your (older) schema version, or `git` isn't available, it falls back to a backup-and-overwrite that shows you the full diff before writing — your previous version stays in the backup.

## Prerequisites

- A vault bootstrapped with `mneme:wiki-setup` and registered in `~/.config/mneme/settings.json` (or name a vault when you invoke).
- `python3` in `PATH`. `git` in `PATH` enables the 3-way merge (without it, the backup-and-overwrite fallback is used).

## Invocation

```
mneme:wiki-update
```

or just say "update my wiki schema" / "my vault schema is out of date" / "bring my wiki up to date" in a session.

## What you get

- A drift report (`current → bundled` schema version).
- A merged `CLAUDE.md` that carries the new schema and keeps your edits, with any conflicts resolved interactively.
- Refreshed page templates and any new schema folders.
- A timestamped backup and the restore command.
- A `log.md` entry (action `schema-update`).
- A handoff suggestion to `wiki-lint`, since a new schema may add fields your existing pages don't have yet.
