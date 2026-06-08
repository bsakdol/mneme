---
title: "feat: Add wiki-ingest skill"
date: 2026-06-08
status: active
origin: docs/brainstorms/mneme-wiki-plugin-requirements.md
---

# feat: Add wiki-ingest skill

`wiki-ingest` is the primary single-source ingestion skill for the mneme plugin. It processes a source (URL, file path, or pasted text) into a structured wiki page, following the vault's own Ingest Workflow defined in CLAUDE.md.

---

## Problem Frame

The vault schema documents a complete Ingest Workflow in CLAUDE.md, but that workflow is written for conversational in-vault use — it assumes the model is already operating in a vault session. `wiki-ingest` packages that workflow as an invokable plugin skill that:

- Resolves the target vault automatically from global settings
- Handles all three source input modes (URL, file path, pasted text) uniformly
- Enforces the confirmation gate (surface takeaways, wait for owner approval) before writing anything
- Keeps bookkeeping (index.md, log.md) consistent after every ingest

---

## Requirements Traceability

| Requirement | Description |
|-------------|-------------|
| R5 | `wiki-ingest` processes an external source into a structured wiki page (see origin: `docs/brainstorms/mneme-wiki-plugin-requirements.md`) |
| F1 | Single-source ingestion flow: owner provides source → skill extracts content → skill proposes type and metadata → owner confirms → page created in vault |

---

## Scope Boundaries

### In scope
- Single-source ingestion: URL, file path (already in `raw/` or external), pasted text
- Reference page creation (externally authored content)
- Solution page creation (internally authored content)
- Entity and concept page creation/update during ingest
- index.md and log.md bookkeeping after every ingest

### Deferred to Follow-Up Work
- Batch/multi-source ingestion — belongs to the ingestion agent (R14)
- Quick-capture for notes without full processing — `wiki-capture` (R6)
- Scaffolding a page from a template without a source — `wiki-new` (R4)

### Outside this product's identity
- LLM-agnostic ingestion tooling
- Ingesting sources into non-mneme vaults

---

## Key Technical Decisions

**Two-tier vault resolution.** The skill resolves the target vault in priority order:
1. **Inline override** — the invocation explicitly names a vault (e.g. `/wiki-ingest https://... into work-vault`). Parsed before running any script; bypasses auto-resolution.
2. **Global default** — `default_vault` in `~/.config/mneme/settings.json`.

If neither resolves, the skill exits with a message directing the owner to `wiki-setup` or `wiki-config`. A helper script (`scripts/resolve-vault.sh`) encapsulates tier 2 following the `vault-guard.sh` precedent — token-based output, clean exit codes — so future skills can reuse it.

**Project-level vault association deferred.** A future enhancement (tracked in BACKLOG.md under `wiki-config`) could let owners configure a per-project default via `.claude/settings.local.json`. Not warranted until the simpler two-tier resolution proves insufficient.

**Hybrid source input (inline + interactive).** If the invocation context already contains a source (URL, file path, or pasted text), use it without prompting. If not, ask with `AskUserQuestion`. There is no artificial forcing of one mode; the skill handles both naturally.

**CLAUDE.md is read before any action.** The vault schema's First-Read Checklist mandates reading CLAUDE.md at the start of every session. The skill enforces this in its early steps so all subsequent decisions — page type, frontmatter fields, linking conventions — are grounded in the vault's own schema rather than the plugin's hardcoded assumptions.

**Confirmation gate before writing any files.** The skill surfaces key takeaways (TL;DR, key claims, entities, concepts, proposed pages, detected conflicts) in chat and waits for the owner's response before creating anything. This directly mirrors Ingest Workflow steps 4–5 in CLAUDE.md. No pages are written until the owner confirms or adjusts the plan.

**No Haiku agent dispatch for content creation.** Unlike wiki-setup's parallel Haiku agents for deterministic folder/file scaffolding, ingestion requires contextual reasoning throughout — classifying the source, extracting claims, resolving cross-links, detecting contradictions. The main model handles all of this inline. Bookkeeping updates (index.md, log.md) also run inline since they depend on the content just created.

**File path sub-cases.** Three cases are handled explicitly: (1) path is already inside `VAULT_PATH/raw/` — skip archiving, read in place; (2) external file path — read content, determine raw category, copy into appropriate `raw/<category>/` bin; (3) pasted text — save to `raw/notes/YYYY-MM-DD-<slug>.md` using a title the owner provides.

---

## Output Structure

```
skills/wiki-ingest/
├── SKILL.md              # Skill definition and step instructions
├── README.md             # User-facing documentation
└── scripts/
    └── resolve-vault.sh  # Read default vault path from settings.json
```

---

## Implementation Units

### U1. Vault resolver script

**Goal:** A reusable bash script that implements tiers 2 and 3 of vault resolution — project-level `.claude/settings.local.json` lookup, then global `default_vault` fallback — and returns a clear token. Inline overrides (tier 1) are handled in SKILL.md before this script runs.

**Requirements:** Supports R5; enables vault resolution for this skill and future `wiki-*` skills.

**Dependencies:** None

**Files:**
- `skills/wiki-ingest/scripts/resolve-vault.sh` (new)

**Approach:**
Takes the current working directory as its first argument (the caller passes `"$PWD"`). Prints one of three tokens to stdout:
- `VAULT_PATH:<absolute-path>` with exit 0 — vault resolved (from project settings or global default)
- `NO_DEFAULT` with exit 1 — `~/.config/mneme/settings.json` exists but no vault could be auto-resolved
- `NOT_CONFIGURED` with exit 2 — `~/.config/mneme/settings.json` does not exist

**Resolution logic:**
1. Walk up from the given cwd looking for `.claude/settings.local.json`. If found and it contains `mneme.vault`, look up that vault name in `~/.config/mneme/settings.json` to get its path. If the name is registered, print `VAULT_PATH:<path>` and exit 0.
2. Read `default_vault` from `~/.config/mneme/settings.json`. If set and non-empty, look up the vault path and print `VAULT_PATH:<path>`, exit 0.
3. If `~/.config/mneme/settings.json` does not exist: print `NOT_CONFIGURED`, exit 2.
4. If settings.json exists but no vault resolved: print `NO_DEFAULT`, exit 1.

No side effects — the script only reads. Use `python3` for all JSON parsing.

**Patterns to follow:** `skills/wiki-setup/scripts/vault-guard.sh` — token-based stdout, clean exit codes, no side effects.

**Test scenarios:**
- Project settings found: `.claude/settings.local.json` in cwd has `mneme.vault: "work-vault"` and `work-vault` is registered in settings.json → prints `VAULT_PATH:<work-vault-path>`, exits 0
- Project settings in parent: `.claude/settings.local.json` is two levels above cwd, has valid `mneme.vault` → script walks up and finds it, prints `VAULT_PATH:<path>`, exits 0
- No project settings, default set: no `.claude/settings.local.json` found, `default_vault` in settings.json is set → prints `VAULT_PATH:<default-vault-path>`, exits 0
- No project settings, no default: settings.json exists but `default_vault` is absent or empty and no project settings found → prints `NO_DEFAULT`, exits 1
- Not configured: `~/.config/mneme/settings.json` does not exist → prints `NOT_CONFIGURED`, exits 2
- Project vault name not in registry: `.claude/settings.local.json` names a vault that isn't in settings.json → falls through to `default_vault`; if that's also absent, prints `NO_DEFAULT`
- Malformed JSON in either file: script handles parse errors gracefully, does not crash; falls through to next resolution tier

**Verification:** Run the script with crafted fixture files covering each scenario; confirm token and exit code match expected values.

---

### U2. SKILL.md

**Goal:** Define the `wiki-ingest` skill — its trigger description and the full 9-step interaction flow from invocation through bookkeeping completion.

**Requirements:** R5, F1

**Dependencies:** U1 (vault resolver script referenced in Step 1)

**Files:**
- `skills/wiki-ingest/SKILL.md` (new)

**Approach:**

The skill is a **vault context bridge** — it resolves the target vault and reads its CLAUDE.md so the model is fully grounded in the vault's operating schema, then executes the Ingest Workflow as defined there. All behavioral logic (page types, frontmatter, classification, confirmation gate, linking, bookkeeping) lives in the vault's CLAUDE.md, not in this skill. This keeps the vault schema as the single source of truth and means the skill works correctly regardless of how the schema evolves.

**Step 1 — Vault resolution**
Run `bash "{skill_base_dir}/scripts/resolve-vault.sh"`. Branch on token:
- `VAULT_PATH:<path>` → set VAULT_PATH, announce the target vault, continue
- `NO_DEFAULT` → use `AskUserQuestion` to ask which configured vault to use (list known vaults from settings.json if any) or accept a typed path; set VAULT_PATH
- `NOT_CONFIGURED` → inform the owner no vault is configured and direct them to run `mneme:wiki-setup` first; exit the skill

**Step 2 — Read vault schema**
Read `VAULT_PATH/CLAUDE.md` fully. This file is the vault's operating contract. All ingest behavior — page types, frontmatter fields, classification rules, confirmation steps, linking conventions, and bookkeeping formats — is defined there. Do not proceed until it is read completely.

**Step 3 — Get source**
If the invocation context already contains a source (URL, file path, or pasted text), use it directly. Otherwise, use `AskUserQuestion` to ask:
- "A URL to fetch"
- "A file path" (absolute or vault-relative)
- "Paste text" (type or paste content directly)

**Step 4 — Execute Ingest Workflow**
Follow the Ingest Workflow defined in `VAULT_PATH/CLAUDE.md` exactly, using the source from Step 3. The vault's CLAUDE.md is the authority for all ingest behavior from this point forward.

**Skill description (frontmatter):**
The `description` field must capture all trigger phrases and source formats so Claude Code auto-invokes correctly. Trigger patterns include: "ingest this [URL/file/text]", "add this to my wiki", "process this source", "ingest raw/...", inline invocation with a URL or file argument, and references to dropping a file into `raw/`. Must also clarify that the skill works from any directory — not just the vault — which is its primary distinction from conversational ingest.

**Patterns to follow:**
- `skills/wiki-setup/SKILL.md` — step structure, `AskUserQuestion` for multi-choice interactions, `{skill_base_dir}` placeholder, settings.json read pattern
- `skills/wiki-setup/assets/CLAUDE-template.md` Ingest Workflow section — what Step 4 delegates to (the authority the vault's CLAUDE.md will contain)

**Test scenarios:**
- URL ingest from outside vault directory: invoke with a URL from a non-vault working directory → vault is resolved from settings.json, CLAUDE.md is read, ingest proceeds per vault schema
- File already in raw/: invoke with a path inside `raw/` → vault's CLAUDE.md Ingest Workflow handles it per its own rules
- No vault configured: settings.json absent → owner directed to run `wiki-setup` first; no source processing attempted
- Multiple vaults, no default: `NO_DEFAULT` token → interactive vault selection before any ingest action
- `AskUserQuestion` used for all multi-choice decisions (vault selection, source type) — no plain text menus

**Verification:** Load the skill from a non-vault directory (`claude --plugin-dir /path/to/mneme`), invoke with a source, and confirm: (1) vault is resolved from settings.json without requiring the owner to be in the vault directory, (2) vault's CLAUDE.md governs all ingest behavior, (3) output matches what conversational ingest from within the vault would produce.

---

### U3. README.md

**Goal:** User-facing documentation for `wiki-ingest` that explains what it does, how to invoke it, and what the owner gets.

**Requirements:** R5

**Dependencies:** U2 (documents the behavior defined in SKILL.md)

**Files:**
- `skills/wiki-ingest/README.md` (new)

**Approach:**
Follow the `wiki-setup` README structure. Include:
- What it does (one paragraph — processes a source into a structured wiki page)
- Prerequisites (mneme plugin installed, at least one vault configured via `wiki-setup`)
- Invocation forms (inline with a URL/path argument; interactive without one)
- What you get (pages created, raw archive, index/log updated)
- A note that the vault's CLAUDE.md governs all page structure decisions — the skill follows the schema, it does not override it

**Patterns to follow:** `skills/wiki-setup/README.md`

**Test scenarios:**
- Test expectation: none — documentation only; no behavioral logic to verify

**Verification:** README accurately reflects the skill behavior after U2 is finalized.

---

## Deferred Implementation Notes

- **Multiple-vault selection UX**: When `NO_DEFAULT` is returned and the owner has multiple configured vaults, the step should list them by name. The exact `AskUserQuestion` shape depends on how many vaults are typical in practice; treat as an execution-time judgment call.
- **Gated/paywalled URLs**: WebFetch may return partial or empty content for authenticated pages. The skill should detect a failed/empty fetch and fall back to asking the owner to paste the content. Exact detection threshold is implementation-time.
- **Image-heavy sources**: CLAUDE.md mentions listing images so the owner can decide which to download separately. The exact UX (inline list vs. `AskUserQuestion`) is an implementation-time call.
- **resolve-vault.sh placement**: Currently scoped to `skills/wiki-ingest/scripts/`. When a second skill needs vault resolution, promote to a plugin-level `scripts/` directory (to be established) and update both skill references.

---

## System-Wide Impact

No existing files are modified. Three new files are added under `skills/wiki-ingest/`. The plugin version in `.claude-plugin/plugin.json` must be bumped (minor bump — new skill added).

---

## Dependencies / Prerequisites

- A vault bootstrapped with `mneme:wiki-setup` (settings.json at `~/.config/mneme/settings.json` present, vault CLAUDE.md present)
- `python3` available in PATH (used by `resolve-vault.sh` to parse the settings JSON)
