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
agents/
  <agent-name>.md      # Subagent definitions (autonomous; namespaced mneme:<agent-name>)
scripts/               # Plugin-root shared code, referenced via ${CLAUDE_PLUGIN_ROOT}/scripts/
  resolve-vault.sh     # Shared default-vault resolver
  obsidian.py          # Shared Obsidian-awareness core (link parse, inert classify, link-graph)
  report.py            # Maintenance report contract (write / parse / status)
  checkrunner.py       # Shared CLI for the per-skill check scripts
skills/
  <skill-name>/
    SKILL.md           # Skill definition — frontmatter + step-by-step instructions
    README.md          # User-facing documentation
    scripts/           # Skill-local helper scripts (e.g. per-skill check scripts)
    assets/            # Bundled files (templates, demo content, static assets)
docs/
  brainstorms/         # Planning and requirements documents
  plans/               # Implementation plans
```

## Skill Anatomy

Each skill lives in `skills/<skill-name>/` and must have:

- **`SKILL.md`** — The operative file. Frontmatter defines the skill's `name` and a `description` that Claude Code uses as the trigger condition (when to auto-invoke). The body contains numbered step-by-step instructions that Claude executes when the skill is invoked.
- **`README.md`** — User-facing documentation (what it does, prerequisites, what you get).

The `SKILL.md` `description` field is load-bearing: it's the condition Claude evaluates to decide whether to auto-invoke the skill, so it must precisely describe trigger phrases and context.

### Skill conventions

- Use `{skill_base_dir}` as the placeholder for the skill's absolute path at invocation time, for files **inside the skill's own directory**. Claude Code resolves this from context.
- Reference **plugin-root shared files** (`scripts/`, other skills, `agents/`) via **`${CLAUDE_PLUGIN_ROOT}/...`** — the documented env-var substitution for the plugin install root (an established convention; cf. Anthropic's `hookify`). Do **not** use relative traversal (`{skill_base_dir}/../../scripts/`) — it is unreliable after a marketplace install.
- Use **`AskUserQuestion`** for all multi-choice interaction inside skills — never plain text prompts for things that need a selection. (Subagents cannot use `AskUserQuestion`; autonomous agents must complete without prompts.)
- Always include a recommended option as the first item in `AskUserQuestion` options and note it as "Recommended".
- **Skill handoff (progressive disclosure):** end a skill with a short "Next steps" suggestion of the next skill in the order of operations. The handoff is a *suggestion*, never a hard dependency or a `Skill`-tool call — skills stay independently invocable.
- Dispatch parallel agents with **`model: haiku`** for deterministic file-creation tasks that don't require reasoning.
- Wait for all dispatched agents to confirm completion before proceeding to the next step.

## Adding a New Skill

1. Create `skills/<skill-name>/SKILL.md` with frontmatter (`name`, `description`) and numbered steps.
2. Create `skills/<skill-name>/README.md` with user-facing docs (what it does, prerequisites, invocation, what you get).
3. Add any bash helpers to `skills/<skill-name>/scripts/` and static assets to `skills/<skill-name>/assets/`.
4. The skill is immediately available after reinstalling or reloading the plugin — no manifest changes needed.

Skills follow the `wiki-*` prefix convention per the requirements doc (`docs/brainstorms/mneme-wiki-plugin-requirements.md`). Implemented: `wiki-setup`, `wiki-ingest`, and the maintenance suite (`wiki-lint`, `wiki-audit`, `wiki-gaps`, `wiki-triage`) plus the `wiki-steward` agent. Still planned: `wiki-query`, `wiki-find`, `wiki-capture`, `wiki-new`, `wiki-relate`, `wiki-config`.

## Agents

Autonomous subagents live in `agents/<name>.md` at the plugin root and are namespaced `mneme:<name>` (the `agents/` directory was established by the maintenance suite). An agent file is frontmatter + a system prompt:

- **Frontmatter:** `name`, a load-bearing `description` (when to dispatch), a `tools` allowlist, and `model` (use an **alias** like `opus`, not a pinned id, for forward-compatibility). Omit a `skills:` preload for headless agents — preloading interactive skill bodies is an anti-pattern.
- **System prompt:** the operating contract. Agents run **headless** — they cannot use `AskUserQuestion`, so every step must be decidable without prompts. Reuse shared logic by calling `${CLAUDE_PLUGIN_ROOT}/scripts/...` directly rather than invoking interactive skills.

A skill can stop and ask the owner; an agent cannot. Unattended, run-to-completion work (e.g. `wiki-steward`) belongs in an agent; human-in-the-loop work belongs in a skill.

## Shared scripts (`scripts/`)

Plugin-root `scripts/` holds code shared across skills and agents, referenced via `${CLAUDE_PLUGIN_ROOT}/scripts/`. The maintenance suite keeps its **must-not-drift logic** here (`obsidian.py` Obsidian-awareness, `report.py` report contract, `checkrunner.py` CLI, `resolve-vault.sh`), while each skill keeps its category-specific checks in its own `skills/<skill>/scripts/`. Scripts are stdlib-only Python 3 / bash and carry `test_*.py` unit tests run with `python3 -m unittest`.

## Versioning

- Plugin version lives in `.claude-plugin/plugin.json`.
- Each skill's bundled schema version is recorded in the `schema_version` field of the frontmatter in its `assets/CLAUDE-template.md` (semver, e.g., `schema_version: 0.2.0`). The `generated_by` field records which skill scaffolded the vault as a static `plugin:skill` identifier (e.g., `mneme:wiki-setup`) — no version suffix.
- Bump `schema_version` when the schema in `CLAUDE-template.md` changes.

### Version bump rules (semantic versioning)

After **every** change to this plugin, you must:

1. Update the `version` field in `.claude-plugin/plugin.json` following semver:
   - **patch** (`x.y.Z`) — bug fixes, copy/doc corrections, internal refactors with no behavior change
   - **minor** (`x.Y.0`) — new skills, new optional fields, backwards-compatible feature additions
   - **major** (`X.0.0`) — breaking changes to the vault schema contract, removed skills, or renamed frontmatter fields that require users to migrate existing vaults
2. Create a GitHub Release tagged `vx.y.z` with a brief description of what changed. Release notes live on GitHub — there is no `CHANGELOG.md` in this repo.

## The Vault Schema

`skills/wiki-setup/assets/CLAUDE-template.md` is the canonical LLM Wiki schema. It defines the three-layer vault structure (`raw/`, `wiki/`, `meta/`), all nine page types and their required sections, frontmatter fields, file naming rules, ingest/query/lint workflows, and hygiene rules. This file is written verbatim into each new vault (with `{{OWNER_NAME}}` and `{{TODAY}}` substituted) and becomes the vault's operating contract.

When the schema evolves, update `CLAUDE-template.md` and bump the `schema_version` field in its frontmatter. Existing vaults are **not** retroactively updated — the new schema only takes effect in freshly bootstrapped vaults.

## Global Settings

The `wiki-setup` skill registers vaults in `~/.config/mneme/settings.json` with structure:
```json
{
  "vaults": {
    "<vault-name>": {
      "vault_path": "...",
      "description": "...",
      "owner_name": "...",
      "created": "YYYY-MM-DD"
    }
  },
  "default_vault": "<vault-name>"
}
```
Future skills that need to know which vault to operate on should read `default_vault` from this file. `owner_name` and `created` capture the values `wiki-setup` substituted into the vault's `CLAUDE.md`, so `wiki-update` can re-personalize the schema during a migration without re-deriving them. The fields are **additive** — readers that only need `vault_path`/`default_vault` are unaffected, and a missing `owner_name` (legacy vault) is handled by `wiki-update` falling back to extraction + confirmation.
