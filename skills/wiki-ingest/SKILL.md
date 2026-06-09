---
name: wiki-ingest
description: >
  Ingests a source into the owner's LLM Wiki vault. Use when the user says
  "ingest this", "add this to my wiki", "add this to the wiki", "process this
  for my wiki", "ingest [URL or file]", or passes any URL, file path, or text
  content they want added to their wiki. Also use when the user says "ingest
  raw/..." to process a file already placed in the vault's raw/ folder.

  This skill works from any directory — it is not limited to the vault itself.
  That is its primary purpose: extending the LLM Wiki so it can be used and
  updated from any project context.

  If the user names a vault explicitly (e.g. "into work-vault"), use that vault.
  Otherwise use the configured default vault.
---

# wiki-ingest

Ingest a source into your LLM Wiki vault from any directory.

## Step 1: Vault Resolution

**Check for an inline vault override first.**

If the invocation explicitly names a target vault (e.g. "into work-vault"), extract
that vault name. Look up its path in `~/.config/mneme/settings.json`:

```bash
python3 -c "
import json, sys
with open('$HOME/.config/mneme/settings.json') as f:
    d = json.load(f)
print(d.get('vaults', {}).get(sys.argv[1], {}).get('vault_path', ''))
" "<vault-name>"
```

If a non-empty path is returned, set VAULT_PATH and continue to Step 2.

If the vault name is not registered, tell the owner:

> **Vault `<name>` not found.** Check the registered vaults in
> `~/.config/mneme/settings.json`, or run `mneme:wiki-setup` to create one.

Exit the skill.

---

**If no vault was named**, run the resolver:

```bash
bash "{skill_base_dir}/scripts/resolve-vault.sh"
```

Branch on the token:

| Token | Action |
|-------|--------|
| `VAULT_PATH:<path>` | Set VAULT_PATH. Announce the target vault briefly, then continue to Step 2. |
| `NO_DEFAULT` | Exit with the message below. |
| `NOT_CONFIGURED` | Exit with the message below. |

**If `NO_DEFAULT`:**

> **No default vault configured.**
>
> Run `mneme:wiki-setup` to create a vault (it will be set as your default), or
> run `mneme:wiki-config` to set an existing vault as the default.

**If `NOT_CONFIGURED`:**

> **No mneme vaults configured.**
>
> Run `mneme:wiki-setup` to create and register your first vault.

---

## Step 2: Read Vault Schema

Read `VAULT_PATH/CLAUDE.md` fully before doing anything else.

This file is the vault's operating contract. Every decision from this point
forward — page types, frontmatter fields, raw/ folder structure, classification
rules, linking conventions, the confirmation gate, and bookkeeping formats — is
defined there. Do not proceed until you have read it completely.

---

## Step 3: Get Source

Check whether the invocation context already contains a source: a URL, a file
path, or pasted content. If it does, use it directly — do not ask.

If no source was provided, use **AskUserQuestion**:

- question: `"What would you like to ingest?"`
- header: `"Source"`
- options:
  - label: `"A URL (Recommended)"`, description: `"Paste a web address to fetch"`
  - label: `"A file path"`, description: `"Absolute path or path relative to the vault"`
  - label: `"Paste text"`, description: `"Type or paste content directly"`

---

## Step 4: Execute Ingest Workflow

Follow the **Ingest Workflow** defined in `VAULT_PATH/CLAUDE.md` exactly, using
the source from Step 3.

The vault's CLAUDE.md is the authority for all ingest behavior from this point
forward. This skill's job was to get you into the right vault context — CLAUDE.md
takes it from here.
