# mneme — Backlog

Tracks planned skills, plugin improvements, and open design questions.
Requirements context: [`docs/brainstorms/mneme-wiki-plugin-requirements.md`](docs/brainstorms/mneme-wiki-plugin-requirements.md)

---

## Skills Roadmap

### Ingestion

| Skill | Description | Priority |
|-------|-------------|----------|
| `wiki-ingest` | Process an external source into a structured wiki page. | **High** |
| `wiki-capture` | Lightweight quick-capture for a note or idea, for later full processing. | **High** |
| `wiki-new` | Scaffold a new page from a template, varying by page type (concept, source, topic, entity). | Medium |

### Retrieval

| Skill | Description | Priority |
|-------|-------------|----------|
| `wiki-find` | Locate pages by keyword, concept, or tag; return title, type, status, and a one-line excerpt per match. | **High** |
| `wiki-query` | Synthesize an answer from across wiki pages for distributed knowledge. | Medium |
| `wiki-relate` | Surface pages connected to a current topic or working context. | Low |

### Maintenance

| Skill | Description | Priority |
|-------|-------------|----------|
| `wiki-lint` | Check structural consistency — frontmatter completeness, tag health, link validity. | Medium |
| `wiki-audit` | Surface stale, thin, or structurally inconsistent pages. | Low |
| `wiki-gaps` | Identify pages that should exist based on broken wiki links or unreferenced concepts. | Low |

### Agents

| Agent | Description | Priority |
|-------|-------------|----------|
| Ingestion agent | Processes a batch of sources end-to-end, creating or updating pages for each, without per-source confirmation. | Low |
| Maintenance agent | Runs `wiki-audit` and `wiki-gaps` as a pipeline; returns a prioritized to-do list without per-step user confirmation. | Low |

### Setup & Configuration

| Skill | Description | Priority |
|-------|-------------|----------|
| `wiki-config` | Update vault configuration post-setup (name, description, default vault, etc.). | Low |

---

## Plugin Improvements

| Item | Description | Priority |
|------|-------------|----------|
| `AGENTS.md` support | Write an `AGENTS.md` alongside `CLAUDE.md` during `wiki-setup` so other agent frameworks (e.g. OpenAI Codex) can operate in the vault with the same schema. Only needed if switching from Claude Code. | Low |

---

## Open Design Questions

### Vault maintenance queue

**Idea:** A file created by `wiki-setup` inside each vault that tracks items needing attention — primarily raw files dropped into `raw/` that haven't been ingested yet. The ingestion agent (or a future `wiki-ingest` skill) could read this queue to know what to process next.

**Open questions:**
- What is the file called and where does it live? (`queue.md` at vault root? `meta/queue.md`?)
- Is it owner-written, agent-written, or both?
- How does a file get added — automatically when dropped into `raw/`, or manually?
- How does it relate to `log.md` and `index.md`? Should the agent check it before asking what to ingest?
- Should it be a simple list or carry metadata per item (date added, source type, priority)?

**Status:** Idea needs more shape before designing the vault file or wiring it into `wiki-setup`.
