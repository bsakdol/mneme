# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A Claude Code **plugin** (`mneme`) that provides a growing collection of skills for building and maintaining a personal knowledge base as an LLM-powered wiki in Obsidian. The plugin is installed once; each skill operates on a user's Obsidian vault at runtime.

## Plugin Installation & Testing

There is no build step. Test by loading the plugin in a live Claude Code session.

**Load for the current session only (dev/testing):**
```bash
claude --plugin-dir /path/to/mneme
```

**Install at user scope (permanent):**
```bash
claude plugin marketplace add /path/to/mneme
claude plugin install mneme --scope user
```

**Install at project scope (commit to share with a team):**
```bash
cp -r /path/to/mneme ./.claude/skills/
```

**Verify after install:**
```
/mneme:wiki-setup
```

Skills are auto-discovered from `skills/*/SKILL.md` and namespaced as `mneme:<skill-name>`.

## Repository Structure

```
.claude-plugin/
  plugin.json          # Plugin manifest (name, version, description, keywords)
  marketplace.json     # Marketplace listing (owner, plugin list)
skills/
  <skill-name>/
    SKILL.md           # Skill definition — frontmatter + step-by-step instructions
    README.md          # User-facing documentation
    scripts/           # Bash helper scripts (sourced by skill steps)
    assets/            # Bundled files (templates, demo content, static assets)
docs/
  brainstorms/         # Planning and requirements documents
```

## Skill Anatomy

Each skill lives in `skills/<skill-name>/` and must have:

- **`SKILL.md`** — The operative file. Frontmatter defines the skill's `name` and a `description` that Claude Code uses as the trigger condition (when to auto-invoke). The body contains numbered step-by-step instructions that Claude executes when the skill is invoked.
- **`README.md`** — User-facing documentation (what it does, prerequisites, what you get).

The `SKILL.md` `description` field is load-bearing: it's the condition Claude evaluates to decide whether to auto-invoke the skill, so it must precisely describe trigger phrases and context.

### Skill conventions

- Use `{skill_base_dir}` as the placeholder for the skill's absolute path at invocation time. Claude Code resolves this from context. Always build subagent prompts with absolute paths derived from it.
- Use **`AskUserQuestion`** for all multi-choice interaction inside skills — never plain text prompts for things that need a selection.
- Always include a recommended option as the first item in `AskUserQuestion` options and note it as "Recommended".
- Dispatch parallel agents with **`model: haiku`** for deterministic file-creation tasks that don't require reasoning.
- Wait for all dispatched agents to confirm completion before proceeding to the next step.

## Adding a New Skill

1. Create `skills/<skill-name>/SKILL.md` with frontmatter (`name`, `description`) and numbered steps.
2. Create `skills/<skill-name>/README.md` with user-facing docs (what it does, prerequisites, invocation, what you get).
3. Add any bash helpers to `skills/<skill-name>/scripts/` and static assets to `skills/<skill-name>/assets/`.
4. The skill is immediately available after reinstalling or reloading the plugin — no manifest changes needed.

Skills follow the `wiki-*` prefix convention per the requirements doc (`docs/brainstorms/mneme-wiki-plugin-requirements.md`). The current skill (`wiki-setup`) is the first of a planned suite including `wiki-ingest`, `wiki-query`, `wiki-find`, `wiki-audit`, `wiki-gaps`, `wiki-lint`, `wiki-capture`, `wiki-new`, `wiki-relate`, and `wiki-config`.

## Versioning

- Plugin version lives in `.claude-plugin/plugin.json`.
- Each skill's bundled schema snapshot version is recorded in the first line comment of its `assets/CLAUDE-template.md` (e.g., `<!-- wiki-setup v0.1.0 | schema snapshot 2026-06-01 -->`).
- Bump both when the schema in `CLAUDE-template.md` changes.

### Version bump rules (semantic versioning)

After **every** change to this plugin, you must:

1. Update the `version` field in `.claude-plugin/plugin.json` following semver:
   - **patch** (`x.y.Z`) — bug fixes, copy/doc corrections, internal refactors with no behavior change
   - **minor** (`x.Y.0`) — new skills, new optional fields, backwards-compatible feature additions
   - **major** (`X.0.0`) — breaking changes to the vault schema contract, removed skills, or renamed frontmatter fields that require users to migrate existing vaults
2. Create a GitHub Release tagged `vx.y.z` with a brief description of what changed. Release notes live on GitHub — there is no `CHANGELOG.md` in this repo.
3. Rebuild the cowork-compatible plugin archive from the repo root:
   ```bash
   zip -r ../mneme.plugin . -x "*.DS_Store"
   ```

## The Vault Schema

`skills/wiki-setup/assets/CLAUDE-template.md` is the canonical LLM Wiki schema. It defines the three-layer vault structure (`raw/`, `wiki/`, `meta/`), all nine page types and their required sections, frontmatter fields, file naming rules, ingest/query/lint workflows, and hygiene rules. This file is written verbatim into each new vault (with `{{OWNER_NAME}}` substituted) and becomes the vault's operating contract.

When the schema evolves, update `CLAUDE-template.md` and bump the snapshot version comment on line 1. Existing vaults are **not** retroactively updated — the new schema only takes effect in freshly bootstrapped vaults.

## Global Settings

The `wiki-setup` skill registers vaults in `~/.config/mneme/settings.json` with structure:
```json
{
  "vaults": {
    "<vault-name>": { "vault_path": "...", "description": "..." }
  },
  "default_vault": "<vault-name>"
}
```
Future skills that need to know which vault to operate on should read `default_vault` from this file.
