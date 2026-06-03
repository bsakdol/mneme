---
date: 2026-06-01
topic: mneme-wiki-plugin
---

# mneme Plugin

## Summary

A Claude Code plugin for full-lifecycle LLM wiki management: ingesting knowledge, retrieving it on demand, and maintaining wiki health over time. Skills are prefixed `wiki-*` and installed as `mneme:wiki-*`. Autonomous multi-step workflows ship as agents alongside guided interactive skills.

---

## Problem Frame

Managing a personal knowledge wiki with LLM tooling creates three recurring friction points: getting new knowledge *in* consistently, getting relevant knowledge *back out* when needed, and keeping the wiki *healthy* over time — stale pages, gaps, and structural inconsistencies that accumulate without active tooling. These three problems are tightly coupled (poor maintenance degrades retrieval; poor ingestion creates gaps), but today they require separate, unconnected interventions. A unified plugin with a consistent `wiki-*` namespace addresses all three without requiring context-switching between tools or approaches.

---

## Actors

- A1. **Wiki owner** — the human user interacting with `wiki-*` skills; may also trigger autonomous agent runs.
- A2. **Maintenance agent** — autonomous pipeline actor; runs audit and gap detection without per-step user confirmation.
- A3. **Ingestion agent** — autonomous pipeline actor; processes batches of sources end-to-end.

---

## Key Flows

- F1. **Single-source ingestion**
  - **Trigger:** A1 invokes `wiki-ingest` with a source (URL, document, or conversation transcript).
  - **Actors:** A1
  - **Steps:** A1 provides source → skill extracts key content → skill proposes page type and metadata → A1 confirms or adjusts → page is created in the vault.
  - **Outcome:** A structured wiki page exists for the source, linked and tagged appropriately.
  - **Covered by:** R5

- F2. **Retrieval and synthesis**
  - **Trigger:** A1 invokes `wiki-query` with a question or topic.
  - **Actors:** A1
  - **Steps:** Skill searches vault for relevant pages → synthesizes an answer across matches → surfaces source citations.
  - **Outcome:** A1 receives a synthesized answer grounded in the wiki's existing content.
  - **Covered by:** R7, R8

- F3. **Maintenance sweep**
  - **Trigger:** A1 triggers the maintenance agent.
  - **Actors:** A1, A2
  - **Steps:** A2 runs audit → A2 runs gap detection → A2 consolidates findings → A2 produces prioritized to-do list → A1 reviews and acts.
  - **Outcome:** A prioritized list of maintenance actions; A1 can work through items using individual `wiki-*` skills.
  - **Covered by:** R10, R11, R13

---

## Requirements

**Plugin structure**

- R1. The plugin is named `mneme`; the manifest lives at `.claude-plugin/plugin.json`.
- R2. All skills use the `wiki-*` prefix; the prefix must not repeat the plugin name within the skill name (e.g., `wiki-find`, not `wiki-mneme-find`).
- R3. The plugin installs at user scope for global availability across projects.

**Ingestion (representative skills — not exhaustive)**

- R4. A `wiki-new` skill scaffolds a new page from a template, varying by page type (concept, source, topic, entity).
- R5. A `wiki-ingest` skill processes an external source into a structured wiki page.
- R6. A `wiki-capture` skill provides lightweight quick-capture for a note or idea, for later full processing.

**Retrieval (representative skills — not exhaustive)**

- R7. A `wiki-find` skill locates pages by keyword, concept, or tag and returns title, type, status, and a one-line excerpt per match.
- R8. A `wiki-query` skill synthesizes an answer from across wiki pages for distributed knowledge.
- R9. A `wiki-relate` skill surfaces pages connected to a current topic or working context.

**Maintenance (representative skills — not exhaustive)**

- R10. A `wiki-audit` skill surfaces stale, thin, or structurally inconsistent pages.
- R11. A `wiki-gaps` skill identifies pages that should exist based on broken wiki links or unreferenced concepts.
- R12. A `wiki-lint` skill checks structural consistency — frontmatter completeness, tag health, link validity.

**Agents**

- R13. A maintenance agent runs `wiki-audit` and `wiki-gaps` as a pipeline and returns a prioritized to-do list without requiring per-step user confirmation.
- R14. An ingestion agent processes a batch of sources end-to-end, creating or updating pages for each, without requiring per-source confirmation.

**Setup and configuration**

- R15. A `wiki-setup` skill handles initial vault configuration.
- R16. A `wiki-config` skill allows updating configuration post-setup.

---

## Success Criteria

- A wiki owner can move through all three lifecycle stages (ingest, retrieve, maintain) using only `mneme:wiki-*` commands — no need for external tooling or manual file management.
- The maintenance agent can be triggered and run to completion without user hand-holding; the output is actionable enough that the owner can immediately prioritize work.
- A planning agent consuming this doc can design the plugin's component structure, skill list expansion strategy, and agent definitions without inventing the plugin's purpose, scope, or namespace conventions.

---

## Scope Boundaries

### Deferred for later

- Comprehensive final skill list — this doc establishes categories and representative examples; full enumeration belongs in planning or a subsequent brainstorm.
- Hook-based automation (e.g., a `SessionEnd` hook for auto-capture or auto-sync).
- Cross-vault or multi-vault support.
- Marketplace publication — initial target is local/personal install.

### Outside this product's identity

- General note-taking or task management — this plugin manages a wiki, not an inbox or to-do system.
- LLM-agnostic wiki tooling — the plugin is purpose-built for Claude Code; adapting it to other LLM toolchains is a different product.

---

## Key Decisions

- **`mneme` as plugin name:** Short form of Mnemosyne (one of the original three Muses — specifically of memory). Concise, memorable, and thematically precise. Portable across any LLM wiki setup, not tied to a specific vault.
- **`wiki-*` prefix for all skills:** Chosen for semantic clarity in the namespace (`mneme:wiki-find`). The plugin name and skill prefix intentionally overlap in meaning — accepted as the clearest read, not a naming conflict.
- **Blank slate, not a refactor:** This plugin has zero relationship to an earlier `second-brain`-named plugin. Design decisions are not constrained by the old `sb-*` skill patterns.

---

## Dependencies / Assumptions

- The vault follows a consistent directory and frontmatter convention that skills can rely on (e.g., pages under `wiki/`, frontmatter with `title`, `type`, `status`, `updated`). The exact convention is determined during planning.
- Claude Code plugin namespacing convention is `plugin-name:skill-name`; skills are auto-discovered from `skills/*/SKILL.md`.

---

## Outstanding Questions

### Resolve Before Planning

(none)

### Deferred to Planning

- [Affects R4, R15][Needs research] What page types and frontmatter schema should the plugin assume? Should this match an existing vault structure, or define a portable convention the vault is expected to follow?
- [Affects R13, R14][Technical] How should agents be defined in the plugin manifest — as `agents/*.md` with a system prompt, or as skills that invoke subagents internally?
- [Affects R7–R9][Technical] Does retrieval use grep-based search, an index file, or LLM-driven semantic search over the vault? The answer affects which skills are feasible without external dependencies.
