---
name: wiki-update
description: Bring an existing mneme vault's schema up to the plugin's current bundled schema. Use when the owner says "update my wiki schema", "update the vault schema", "my wiki schema is out of date", "migrate my vault to the latest schema", "bring my wiki up to date", or invokes mneme:wiki-update. Detects schema drift by comparing the vault's CLAUDE.md schema_version against the bundled template, then — preserving the owner's hand-edits via a version-aware 3-way merge — refreshes CLAUDE.md and the nine page templates and additively creates any new schema folders. Always backs up before writing and never touches the owner's knowledge content (raw/, wiki/, index.md, log.md, meta/tags.md). Operates on the default vault registered in ~/.config/mneme/settings.json unless the owner names a vault. Standalone — it never invokes another skill; it suggests the next one.
---

# Wiki Update

Migrate an mneme vault's frozen schema snapshot (its `CLAUDE.md` and the nine page templates) to the plugin's current bundled schema, **preserving the owner's hand-edits** and **never modifying their knowledge content**.

You are running inside the owner's Claude Code session. Be concise. Use `AskUserQuestion` for every choice, with a recommended option first. Always back up before writing; never delete owner files.

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

## Step 2 — Detect schema drift

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/schema_update.py" "<VAULT_PATH>" --report
```

This prints JSON: `{current_version, bundled_version, status, base_available, owner_name_source}`. Branch on `status`:

| `status` | Action |
|----------|--------|
| `up-to-date` | Tell the owner the vault is already current (`current_version`). Skip to Step 8 (handoff). Do not write anything. |
| `ahead` | The vault's `schema_version` is **newer** than the installed plugin. Tell the owner their plugin is behind — suggest updating the `mneme` plugin — and stop without writing. (If they hand-edited `schema_version`, this is also where they'd notice.) |
| `unknown` | The vault's frontmatter is missing or malformed. Proceed with **explicit caution** via the overwrite path (Step 5), and warn that hand-edits cannot be auto-merged. |
| `behind` | Continue to Step 3. |

Announce the migration: `current_version → bundled_version`.

## Step 3 — Recover the owner name

The merge re-personalizes the schema, so you need the literal owner display name.

1. If `owner_name_source` is `settings`, read `owner_name` from the vault's entry in `~/.config/mneme/settings.json`. Use it.
2. Otherwise (legacy vault), **best-effort extract** it from `VAULT_PATH/CLAUDE.md` — the intro reads `the operating manual for <NAME>'s personal LLM Wiki`. Then confirm via `AskUserQuestion`:
   - **`<extracted name>` (Recommended)** — use the extracted name.
   - **Type a different name** — owner enters it.
3. If extraction finds **nothing**, ask outright with `AskUserQuestion` (no pre-fill) for the owner name.

Reject a name that is empty or contains `{{`/`}}` or a newline (re-ask). Once confirmed, **persist** it back to the vault's `settings.json` entry as `owner_name` (and add `created` from the vault's `CLAUDE.md` frontmatter if absent) so future runs skip this step. Store the confirmed value as `OWNER_NAME`.

## Step 4 — Back up

Before any write, copy the current schema files into a timestamped backup inside the vault:

```bash
TS=$(date +%Y%m%d-%H%M%S)
mkdir -p "<VAULT_PATH>/meta/backups/$TS/templates"
cp "<VAULT_PATH>/CLAUDE.md" "<VAULT_PATH>/meta/backups/$TS/CLAUDE.md"
cp "<VAULT_PATH>"/meta/templates/*.md "<VAULT_PATH>/meta/backups/$TS/templates/" 2>/dev/null || true
```

Back up **all nine templates unconditionally** — which ones change isn't known until Step 6. Announce the backup path; you will repeat it (with the restore command) in the completion report.

## Step 5 — Prepare the merge

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/schema_update.py" "<VAULT_PATH>" \
  --prepare --owner "<OWNER_NAME>" --today "<YYYY-MM-DD>"
```

This prints JSON: `{mode, outcome, conflict_count, merged_text, diff_text, reason}`. The core has already reconstructed the frontmatter deterministically (new `schema_version`, preserved `created`, `updated` = today) and merged the body. Branch:

- **`mode: merge`, `outcome: clean`** — summarize what changed (new sections, preserved edits), then go to Step 6 with `merged_text`.
- **`mode: merge`, `outcome: conflicts`** — `merged_text` contains `conflict_count` git conflict regions (between `<<<<<<<` / `=======` / `>>>>>>>` markers). Walk each region with `AskUserQuestion`:
  - **Keep the new schema version (Recommended)** — take the `ours` side.
  - **Keep my version** — take the `theirs` side.
  - **Show both / let me decide** — display both sides and resolve from the owner's reply.
  Produce a fully resolved text with **all markers removed**. Do not write a file that still contains conflict markers.
- **`mode: overwrite`** — there is no archived base for the vault's version (or `git` is unavailable; see `reason`). Present `diff_text` (current → updated) and confirm with `AskUserQuestion` before proceeding. On confirm, use `merged_text`. Note that hand-edits are recoverable from the Step 4 backup.

## Step 6 — Write and refresh

1. **Write the merged `CLAUDE.md` atomically** (so an interrupted write never leaves a half-merged file):

   ```bash
   # write the resolved text to <VAULT_PATH>/.CLAUDE.md.new, then:
   mv "<VAULT_PATH>/.CLAUDE.md.new" "<VAULT_PATH>/CLAUDE.md"
   ```

2. **Refresh the nine page templates.** For each `<name>.md` in `${CLAUDE_PLUGIN_ROOT}/skills/wiki-setup/assets/templates/`, compare the vault's `meta/templates/<name>.md` against the archived base `${CLAUDE_PLUGIN_ROOT}/schema-history/<current_version>/templates/<name>.md` (page templates carry no owner tokens, so this is a plain byte comparison):
   - **Unchanged** (or no archived base): copy the new canonical template over it.
   - **Owner-modified**: it was backed up in Step 4 — ask via `AskUserQuestion` whether to overwrite or keep theirs.
   Leave any extra, owner-added templates untouched.

3. **Additively create new schema folders.** Read the Folder Tree section of the **new** `CLAUDE.md` and `mkdir -p` any listed folder that does not yet exist. Never delete or move existing folders or files.

## Step 7 — Bookkeeping

Append one entry to `VAULT_PATH/log.md` using the schema's log format with action `schema-update`, noting `current_version → bundled_version`, conflicts resolved, templates refreshed, and folders added.

## Step 8 — Completion report

Report concisely:

- **Schema:** `current_version → bundled_version` (or "already current" if Step 2 was `up-to-date`).
- **Changed:** `CLAUDE.md`, N templates refreshed, M folders added.
- **Backup:** the `meta/backups/<TS>/` path, **with the restore command**: `cp <VAULT_PATH>/meta/backups/<TS>/CLAUDE.md <VAULT_PATH>/CLAUDE.md` (and the templates dir alongside).
- **Conflicts:** how many were resolved, if any.
- **Untouched:** the owner's content (`raw/`, `wiki/`, `index.md`, `log.md`, `meta/tags.md`) was not modified.

## Step 9 — Handoff

Close with a short "Next steps" offer (a suggestion, not an automatic action):

> Schema updated. A new schema can introduce fields or sections your existing pages don't have yet. Run **`mneme:wiki-lint`** to check your pages against the updated schema (frontmatter, links, tags), then **`mneme:wiki-audit`** and **`mneme:wiki-gaps`** for the rest of the maintenance pass.
