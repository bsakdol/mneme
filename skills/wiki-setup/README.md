# wiki-setup

A Claude Code skill that bootstraps an empty Obsidian vault into a ready-to-use LLM Wiki. Running this skill in a fresh vault produces the canonical folder structure, a personalized CLAUDE.md operating schema, skeleton bookkeeping files, nine page-type templates, and at least one real piece of ingested wiki content — so you can start your second ingest immediately.

---

## What This Skill Does

1. Verifies the target directory is empty (refuses with a clear message if it isn't)
2. Collects your vault name, display name, and a short description
3. Walks through three narrated scaffold phases while background agents build the vault in parallel
4. Prompts you to choose a tutorial depth (minimal / standard / full)
5. Ingests the bundled LLM Wiki overview article at your chosen depth, producing real wiki content you keep

When it exits, your vault is ready. `CLAUDE.md` is your operating schema. `index.md` is your content catalog. `log.md` is your activity record. `meta/templates/` holds the nine page-type shapes. And `wiki/` has at least one reference page from the demo ingest.

---

## Prerequisites

- **Obsidian** installed and a new, empty vault directory created. The skill refuses if the directory contains any unexpected files.
- **Claude Code** (CLI or desktop app) running with the `mneme` plugin installed.

---

## Installation

This skill is distributed as part of the `mneme` plugin.

---

## Invocation

Open Claude Code and type:

```
mneme:wiki-setup
```

The skill will ask where to set up the wiki — either your current working directory or a path you provide. Expect the full bootstrap (scaffold + minimal demo) to take about 60–90 seconds.

---

## What You Get

### File structure

```
YourVault/
├── CLAUDE.md                  # Operating schema — read this before every session
├── index.md                   # Content catalog — updated on every ingest
├── log.md                     # Activity log — append-only
├── raw/                       # Source documents (11 subfolders)
│   ├── articles/
│   │   └── YYYY-MM-DD-llm-wiki-pattern-overview.md   # Demo source
│   ├── posts/
│   ├── papers/
│   ├── reports/
│   ├── guides/
│   ├── docs/
│   ├── books/
│   ├── recordings/
│   ├── transcripts/
│   ├── notes/
│   └── assets/
├── wiki/                      # LLM-maintained synthesis (9 subfolders)
│   ├── entities/
│   ├── concepts/
│   ├── topics/
│   ├── references/
│   │   └── YYYY-MM-DD-llm-wiki-pattern-overview.md   # Demo reference page (all depths)
│   ├── solutions/
│   ├── analyses/
│   ├── projects/
│   ├── personal/
│   └── questions/
└── meta/
    ├── tags.md                # Tag registry
    └── templates/             # 9 page-type templates
```

### Tutorial depth

The skill asks how much of a walkthrough you want. Choose based on how familiar you are with the LLM Wiki pattern:

| Depth | What Claude does | Best for |
|-------|-----------------|----------|
| **Minimal** | Runs the ingest silently, then gives a brief orientation paragraph | Returning users or anyone who's read the plugin README |
| **Standard** | Narrates each ingest decision as it happens; tours the main sections of CLAUDE.md afterward | Most first-time users |
| **Full** | Explains every page type and folder before ingesting; narrates every decision; walks through the finished pages and invites questions | Anyone who wants to deeply understand the schema before their first real ingest |

Demo pages created at each depth:

- **All depths** — `wiki/references/YYYY-MM-DD-llm-wiki-pattern-overview.md`
- **Standard and Full** — also `wiki/concepts/llm-wiki.md`
- **Full only** — also `wiki/topics/llm-tooling.md`

---

## First Steps After Bootstrap

1. Read `CLAUDE.md` fully — it is your operating contract for every future session.
2. Read `index.md` to see what's already in the wiki.
3. Find a source you want to ingest and tell Claude.

See the [plugin README](../../README.md) for the full command reference and an explanation of how vault sessions work.

---

## Troubleshooting

**The skill says the vault directory does not exist.**
The path you entered doesn't point to a real directory. Create the vault in Obsidian first (File → New Vault), then run `mneme:wiki-setup` again.

**The skill says the vault is not empty.**
The skill writes the canonical schema from scratch and refuses to run in a directory that already has content, to avoid collisions. Create a new, empty Obsidian vault and run the skill there.

**The skill accepts `Welcome.md` automatically.**
Obsidian creates `Welcome.md` in every new vault. The skill removes it silently if it's the only file present — this is expected behavior.

**The demo ingest produces fewer pages than expected.**
The number of pages depends on your chosen tutorial depth. Minimal creates one reference page; Standard adds a concept page; Full adds a topic hub. See the tutorial depth table above.

---

## Versioning

This skill ships a snapshot of the canonical LLM Wiki schema. The snapshot version is recorded in the first line of `assets/CLAUDE-template.md`. When the canonical schema evolves, install a newer version of the skill in a fresh vault to get the updated schema. Existing vaults are not affected.

---

## License and Attribution

The `assets/demo-source.md` file is an adapted version of the LLM Wiki pattern documentation included for use as a bootstrap demo. Attribution is noted at the top of that file.
