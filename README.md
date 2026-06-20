# mneme

A Claude Code plugin for building and maintaining a personal knowledge base as an LLM-powered wiki in Obsidian.

The plugin packages a growing collection of skills that cover the full lifecycle of an LLM Wiki: initial setup, source ingest, knowledge querying, and ongoing maintenance. Each skill follows the canonical mneme schema so all your wikis stay structurally consistent across installs and machines.

---

## Skills

| Skill | Invocation | What it does |
|-------|-----------|--------------|
| [wiki-setup](skills/wiki-setup/README.md) | `mneme:wiki-setup` | Bootstraps an empty Obsidian vault into a ready-to-use LLM Wiki — folder structure, personalized CLAUDE.md, bookkeeping files, page templates, and a live first-ingest demo. |

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
