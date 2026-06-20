# wiki-lint

Lint an mneme LLM Wiki vault for **structural consistency** — frontmatter, links, and tags — and apply the safe fixes on approval.

First stage of the maintenance order of operations: **wiki-lint → wiki-audit → wiki-gaps**.

## What it does

Runs the bundled Obsidian-aware checker over your vault and reports findings by risk tier:

| Dimension | Tier | Notes |
|-----------|------|-------|
| `broken-link` | safe / judgment | Safe when there's exactly one date-prefix candidate (a slug typo); judgment for a genuine one-off dangling link. Dangling links referenced by 3+ pages are routed to `wiki-gaps` as missing-page candidates instead. |
| `parent-path-mismatch` | safe | A nested topic's `parent:` must match its folder. |
| `frontmatter-missing` | judgment | Missing `title`/`type`/`created`/`updated`/`status`. |
| `frontmatter-bare-question` | judgment | A field whose value is a bare `?`. |
| `source-paths-missing-raw` | judgment | A `source_paths:` entry with no matching raw file. |
| `tag-single-use` | judgment | A tag used on only one page. |
| `tag-near-synonym` | judgment | Tags that look like variants of each other (`llm` vs `llms`). |

**Safe** findings can be auto-applied (idempotent, reversible). **Judgment** findings are reported for you to decide — the skill never auto-creates pages, deletes anything, or rewrites prose.

The Obsidian-awareness lives in the shared `scripts/obsidian.py` core: escaped table pipes, code spans, fenced blocks, HTML comments, anchors, and embeds are handled correctly, so illustrative `[[links]]` in code are never flagged.

## Prerequisites

- A vault bootstrapped with `mneme:wiki-setup` and registered in `~/.config/mneme/settings.json` (or name a vault when you invoke).
- `python3` in `PATH`.

## Invocation

```
mneme:wiki-lint
```

or just say "lint the wiki" / "check my frontmatter and links" in a session.

## What you get

- A tiered findings report in chat.
- Safe fixes applied on approval, with an exact list of what changed.
- A `log.md` entry (action `lint`).
- A handoff suggestion to `wiki-audit` (or the `wiki-steward` agent for a full automated pass).
