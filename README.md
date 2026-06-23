# mneme

A Claude Code plugin for building and maintaining a personal knowledge base as an LLM-powered wiki in Obsidian.

The plugin packages a growing collection of skills that cover the full lifecycle of an LLM Wiki: initial setup, source ingest, knowledge querying, and ongoing maintenance. Each skill follows the canonical mneme schema so all your wikis stay structurally consistent across installs and machines.

## Why "mneme"?

**Mneme** (Greek *Μνήμη*, "memory") was the Muse of memory — one of the three original Muses worshipped in Boeotia before the canonical nine, alongside Aoide ("song") and Melete ("practice"). She is the daughter of Mnemosyne, the Titaness who personified memory itself.

The name fits the plugin's purpose: this is a tool for *remembering* — capturing sources, synthesizing them into durable knowledge, and keeping that knowledge organized so nothing you've learned slips away. Where a muse inspires, Mneme remembers. Pronounced *NEE-mee*.

---

## Skills

| Skill | Invocation | What it does |
|-------|-----------|--------------|
| [wiki-setup](skills/wiki-setup/README.md) | `mneme:wiki-setup` | Bootstraps an empty Obsidian vault into a ready-to-use LLM Wiki — folder structure, personalized CLAUDE.md, bookkeeping files, page templates, and a live first-ingest demo. |
| [wiki-ingest](skills/wiki-ingest/README.md) | `mneme:wiki-ingest` | Ingests a source (URL, file, or pasted text) into the vault following the Ingest Workflow. |
| [wiki-lint](skills/wiki-lint/README.md) | `mneme:wiki-lint` | Structural consistency — frontmatter, links, tags. Applies safe fixes on approval. |
| [wiki-audit](skills/wiki-audit/README.md) | `mneme:wiki-audit` | Stale, thin, or inconsistent pages — orphans, stubs, stale references, conflicts. |
| [wiki-gaps](skills/wiki-gaps/README.md) | `mneme:wiki-gaps` | Pages that should exist — concepts referenced widely with no page, and index drift. |
| [wiki-triage](skills/wiki-triage/README.md) | `mneme:wiki-triage` | Walks you through the judgment items in a maintenance report and applies the approved ones. |

**Agent**

| Agent | How to run | What it does |
|-------|-----------|--------------|
| [wiki-steward](agents/wiki-steward.md) | dispatched (e.g. "run the steward"), or scheduled | Autonomous maintenance: runs lint + audit + gaps, applies the safe/low-risk fixes unattended, writes a prioritized report, and returns a summary. Headless — no prompts. |

---

## Maintenance — order of operations

Maintenance has two lanes over the same findings:

- **Manual (interactive):** `wiki-lint` → `wiki-audit` → `wiki-gaps`. Each detects its category, applies the safe fixes with you present, and hands off to the next. Use when you want to work through issues yourself.
- **Automated (hands-off):** dispatch the **`wiki-steward`** agent for a full sweep — it applies the safe/low-risk fixes and writes a report to `meta/maintenance-reports/` — then run **`wiki-triage`** to work the report's judgment items.

The split that keeps them tidy: the agent only ever applies **safe** and **low-risk** fixes; everything requiring judgment (creating pages, resolving conflicts, merging tags) is reported, never auto-done. Maintenance requires the mneme plugin to be installed (the vault's own `CLAUDE.md` points at it).

---

## Installation

**User-level** (applies across all projects):

Register the plugin source, then install it to your user scope:

From GitHub (HTTPS):
```bash
claude plugin marketplace add https://github.com/bsakdol/mneme
claude plugin install mneme --scope user
```

From GitHub (SSH):
```bash
claude plugin marketplace add git@github.com:bsakdol/mneme
claude plugin install mneme --scope user
```

From a local clone:
```bash
claude plugin marketplace add /path/to/mneme
claude plugin install mneme --scope user
```

**Project-level** (scoped to one repo; commit the result to share with your team):

Copy the plugin directory into `.claude/skills/` at the repo root, then commit it:

```bash
cp -r /path/to/mneme ./.claude/skills/
```

Claude Code loads project-scoped plugins after you accept the workspace trust dialog for that directory.

**Development / Testing** (load for the current session without installing permanently):

```bash
claude --plugin-dir /path/to/mneme
```

---

After installation, all skills in `skills/` are available and namespaced as `mneme:<skill-name>`. No additional configuration is required.

To verify, open Claude Code and run:

```
/mneme:wiki-setup
```

---

## How Your Vault Works

The wiki uses a strict three-layer architecture:

| Layer | Folder | Who writes it | What it is |
|-------|--------|--------------|------------|
| Source storage | `raw/` | You | Original documents — articles, papers, notes, transcripts. **Immutable once placed.** |
| Synthesis | `wiki/` | Claude | Every summary, concept, entity, analysis, and hub page. You read it; Claude maintains it. |
| Schema & bookkeeping | `CLAUDE.md`, `index.md`, `log.md`, `meta/` | Claude | Operating rules, content catalog, activity log, templates. |

The separation matters: `raw/` is ground truth, `wiki/` is interpretation. Claude never invents — every claim on a wiki page traces back to a raw source.

---

## How Sessions Work

Every Claude Code session in your vault starts with the same contract, defined in `CLAUDE.md`:

1. Read `CLAUDE.md` fully
2. Read `index.md` to see what's in the wiki
3. Check the last 10 entries of `log.md` for recent activity
4. Then engage with your request

You don't need to ask Claude to do this — `CLAUDE.md` instructs it automatically. The wiki only works if every session starts grounded in the current state.

---

## Command Reference

These phrases work in any Claude Code session opened in your vault.

**Ingest a new source**
```
Ingest this: [paste URL or text]
```

**Process a file you dropped into `raw/`**
```
Ingest raw/articles/YYYY-MM-DD-filename.md
```

**Reconcile after adding several files at once**
```
Reconcile raw/ — ingest anything new
```

**Check the vault for issues**
```
Run a healthcheck on the wiki
```

**Search what you already know**
```
What do I know about [topic]?
```

**Capture an open question before you lose it**
```
Add this question to the wiki: [your question]
```

**Start tracking a new project**
```
Start a project: [name and what it's for]
```

**Review active projects**
```
What projects am I currently tracking?
```

**Ask for a synthesis worth keeping**
```
Compare X and Y based on what's in the wiki — file it as an analysis if it's non-trivial
```

---

## Requirements

- Claude Code CLI or desktop app
- No external MCP servers or internet access required at runtime. Core lifecycle stages (setup, ingest, query) need no additional plugins; **maintenance** (lint/audit/gaps plus the steward agent) is provided by mneme itself, so those commands require the plugin to be installed.
- Individual skills may have their own prerequisites — see each skill's README

---

## Versioning

Skills ship with a snapshot of the canonical schema. The snapshot version is recorded inside each skill's bundled assets. When the schema evolves, reinstall the updated plugin version; existing vaults are not affected.
