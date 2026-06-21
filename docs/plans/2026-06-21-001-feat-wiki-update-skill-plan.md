---
title: "feat: Add wiki-update skill (vault schema migration)"
date: 2026-06-21
status: completed
origin: docs/brainstorms/mneme-wiki-plugin-requirements.md
---

# feat: Add `wiki-update` skill — vault schema migration

A new interactive `mneme:wiki-update` skill that brings an existing vault's frozen schema snapshot up to the plugin's current bundled schema, **preserving the owner's hand-edits** through a version-aware 3-way merge and never touching the owner's knowledge content.

When `wiki-setup` bootstraps a vault it writes `CLAUDE-template.md` into the vault **verbatim** (substituting `{{OWNER_NAME}}` / `{{TODAY}}`) as `CLAUDE.md`, plus the nine page templates into `meta/templates/`. That snapshot is frozen at the `schema_version` of the day. When the plugin's schema later evolves, existing vaults receive nothing — the owner must hand-port changes or live with drift. `wiki-update` closes that loop.

This plan is the schema-lifecycle analogue of the maintenance suite (`docs/plans/2026-06-20-001-feat-wiki-maintenance-plan.md`) and reuses its conventions: `resolve-vault.sh` for vault targeting, a stdlib-only `--report`-emitting Python core in plugin-root `scripts/`, `AskUserQuestion` for every choice, and a "Next steps" handoff to the maintenance suite.

---

## Problem Frame

The vault schema is a **personalized snapshot, not a live reference**. The single source of drift truth is one field — `schema_version` in the vault's `CLAUDE.md` frontmatter (currently `0.7.0`) versus the plugin's bundled `skills/wiki-setup/assets/CLAUDE-template.md` frontmatter. Detection is therefore a clean single-field semver comparison; the difficulty is **applying** an update safely:

1. **Re-personalization** — regenerating from the new template re-introduces `{{OWNER_NAME}}` / `{{TODAY}}` tokens, but the literal owner name is not stored anywhere structured today. It lives only inside `CLAUDE.md` prose.
2. **Hand-edit preservation** — the owner may have edited their `CLAUDE.md` (it is the vault's operating manual). A naive overwrite destroys those edits. Because the owner's current `schema_version` is recorded in frontmatter, we *can* reconstruct the exact base template they started from and 3-way merge their edits forward — if the plugin retains historical schema templates.
3. **Content safety** — the owner's actual knowledge (`raw/`, `wiki/`, `index.md`, `log.md`, `meta/tags.md`, any custom templates) must never be modified or deleted by a schema update.

Points 1 and 2 reinforce each other: storing the owner name (and other setup variables) in `settings.json` is what makes a faithful 3-way merge possible, because it lets us render the archived base template into the same personalized space as the owner's live file.

---

## Requirements Traceability

`wiki-update` is a **planning-discovered capability** not enumerated in the origin requirements doc. The origin lists `wiki-config` (R16, *"updating configuration post-setup"* — i.e. `settings.json`) and `wiki-setup` (R15, initial bootstrap), but no skill owns **schema migration of an existing vault**. This plan adds that skill and traces to the schema-versioning contract the origin assumed in *Dependencies / Assumptions* (*"the vault follows a consistent directory and frontmatter convention that skills can rely on"*).

| Origin anchor | How this plan relates |
|---|---|
| R15 (`wiki-setup`) | `wiki-update` is its forward-migration counterpart; shares the template assets and adds the settings-variable persistence (U4). |
| R16 (`wiki-config`) | Distinct concern — `wiki-config` edits `settings.json`; `wiki-update` migrates the in-vault schema. No overlap. |
| Maintenance suite (R10–R13) | `wiki-update` ends with an optional handoff to `wiki-lint` so the owner can reconcile content against any newly-required schema fields. |

---

## Scope Boundaries

### In scope

- A new interactive skill `skills/wiki-update/` (`SKILL.md` + `README.md`).
- A versioned **schema-history archive** of frozen schema bundles, seeded with the current `0.7.0`.
- A shared, unit-tested `scripts/schema_update.py` core (version detection, semver compare, base reconstruction, 3-way merge orchestration, `--report` JSON).
- An additive `wiki-setup` change to persist setup variables (owner name, created date) into `settings.json`.
- Refresh of `CLAUDE.md` (via merge) and the nine canonical `meta/templates/` (via modified-detection), plus additive creation of any newly-introduced schema folders.
- Repo docs: `CLAUDE.md` (implemented-skills list, archive + version-bump rule, settings schema), `plugin.json` version bump, GitHub release note.

### Deferred to Follow-Up Work

- Applying the 3-way merge strategy to the nine page templates (U5 uses modified-detection + backup for templates; full per-template merge is a later refinement).
- A headless/agent entry point for unattended schema updates (e.g. folding into `wiki-steward`). `wiki-update` is interactive-only because merges can produce conflicts that need a human.
- Batch update of multiple registered vaults in one invocation (default target is the single resolved vault).

### Outside this product's identity

- Migrating or rewriting the owner's existing wiki **pages** to match a new schema — `wiki-update` migrates the *operating manual and templates*, not content. Content reconciliation is the maintenance suite's job.
- Editing `settings.json` configuration values as a user-facing feature — that is `wiki-config` (R16).

---

## Key Technical Decisions

**KTD-1 — Converge-to-latest, not version-chained migrations.** There is one target state: the current bundled template. `wiki-update` converges the vault to it in a single step rather than replaying N intermediate migrations. Schema bumps are infrequent and the template is a document, not executable state, so chained migrations would be heavy infrastructure for little gain.

**KTD-2 — Version-aware 3-way merge preserves hand-edits.** Because `schema_version` is recorded in the vault, we reconstruct the exact base the owner started from (archived template at their version, re-personalized with their owner name + original `created` date) and 3-way merge: `theirs` = live `CLAUDE.md`, `base` = reconstructed original, `ours` = new template re-personalized. Clean hunks apply silently; conflicts surface for the owner to resolve interactively. Merge engine: **`git merge-file`** on temp files (no repo required) — a well-solved 3-way merge with standard conflict markers. Falls back to a presented unified diff + backup-and-overwrite when `git` is unavailable or no base is archived for the owner's version.

**KTD-3 — Frontmatter is reconstructed deterministically, not merged.** Splitting frontmatter from body before the merge avoids dumb conflicts on `updated:` / `schema_version:` lines. The canonical template frontmatter has exactly six keys — `title`, `type`, `schema_version`, `created`, `updated`, `generated_by` — and **none are owner-derived** (the owner name lives only in body prose). The body is 3-way merged; the frontmatter is rebuilt deterministically: `schema_version` = new (bundled), `created` = preserved from theirs, `updated` = today, `title`/`type`/`generated_by` = taken from the new template. No frontmatter key carries owner data, so there is nothing to personalize in the frontmatter.

**KTD-4 — Setup variables live in `settings.json` going forward.** `wiki-setup` records `owner_name` and `created` alongside the existing `vault_path` / `description`. `wiki-update` reads them when present; when absent (legacy vaults), it best-effort extracts the owner name from `CLAUDE.md`, confirms via `AskUserQuestion`, then **writes it back** so subsequent updates are seamless. Fully backwards-compatible: a missing field never breaks resolution.

**KTD-5 — Archive = all prior versions; canonical = latest; a test forbids drift across the *whole* bundle.** `schema-history/<version>/` (at plugin root) holds frozen bundles — `CLAUDE-template.md` **and** the nine `templates/*.md`. The bump rule snapshots the *outgoing* canonical bundle into the archive before editing. To make the merge base available today, the archive is **seeded with `0.7.0`** now. A unit test asserts byte-identity between `schema-history/<latest>/` and the canonical bundle for **every** file — `CLAUDE-template.md` and all nine templates — not just `CLAUDE-template.md`. This matters because U5's template modified-detection diffs each live template against its archived base; if a seeded template silently diverged, an unmodified owner template would be misclassified as modified (or a modified one silently overwritten), defeating the backup guarantee for exactly the files the archive exists to protect.

**KTD-6 — Always back up before writing; never delete owner files; restore is documented.** Before any write, the existing `CLAUDE.md` **and all nine page templates** are copied to a timestamped `meta/backups/<timestamp>/` inside the vault (back up unconditionally — the modified-detection that decides *which* templates change runs after backup, so a selective backup would be unsafe). The final `CLAUDE.md` write is **atomic** (write to a temp file in the same directory, then rename) so an interrupted run cannot leave a half-merged file with stray conflict markers. The completion report names the backup path and the one-line restore command. New schema folders are created additively; nothing in `raw/`, `wiki/`, or bookkeeping files is ever removed.

**KTD-7 — Owner-name substitution and conflict markers are made collision-safe.** Two hazards from rendering archived templates into the owner's space and merging Markdown:
- *Name-as-substring.* `wiki-setup` accepts short/common names (e.g. `jsmith`, even a single word that also appears in prose). Naive `{{OWNER_NAME}}` → name substitution is forward-only and safe, but the *reverse* assumption — that every occurrence of the name in `theirs` came from the schema — is not. The merge operates on the **token-substituted form**: `base` and `ours` are the archived/new templates with `{{OWNER_NAME}}` still tokenized, and `theirs` is normalized by **not** re-tokenizing — instead the owner name is treated as always-take-theirs on the few schema-origin name lines. The core validates the owner name (non-empty, no `{{`/`}}`, no newline) before use and the skill confirms it interactively, so a pathological name is caught before any write.
- *Marker collision.* The `CLAUDE.md` body is Markdown containing fenced code blocks that may legitimately include `<<<<<<<` / `=======` / `>>>>>>>` sequences. Conflict-region parsing is **fence-aware**: it tracks code-fence open/close state and only treats markers at column 0 *outside* a fenced block as `git merge-file` conflict markers. When the body contains literal marker-like content inside a fence, the merge still runs but the parser does not mis-detect it as a conflict.

---

## Output Structure

```
scripts/
  schema_update.py            # NEW — shared version/merge core (reuses obsidian.py; git merge-file)
  test_schema_update.py       # NEW — unit tests with fixtures
  obsidian.py                 # REUSED — split_frontmatter / read_schema_version (no change)
schema-history/               # NEW — plugin-wide frozen-bundle archive (alongside scripts/, agents/)
  0.7.0/
    CLAUDE-template.md        # NEW — seeded byte-identical to canonical
    templates/                # NEW — seeded copies of the nine page templates
skills/
  wiki-setup/
    SKILL.md                  # MODIFIED — Step 8 persists owner_name + created to settings.json
    assets/
      CLAUDE-template.md       # unchanged here (canonical "latest")
  wiki-update/                # NEW skill
    SKILL.md
    README.md
CLAUDE.md                     # MODIFIED — implemented skills, archive/bump rule, settings schema, BACKLOG.md rule
BACKLOG.md                    # MODIFIED — drop shipped items, add this change, codified as a standing step
.claude-plugin/plugin.json    # MODIFIED — version bump 0.4.0 -> 0.5.0
```

The archive lives at **plugin root** (`schema-history/`), alongside `scripts/` and `agents/` — it is plugin-wide state seeded by `wiki-setup`/the version-bump ritual and read by `wiki-update`, not a `wiki-setup` private asset. Both skills resolve it via `${CLAUDE_PLUGIN_ROOT}/schema-history/`. The per-unit `**Files:**` lists remain authoritative.

---

## Implementation Units

### U1. Seed the versioned schema-history archive

**Goal:** Create the frozen-bundle archive and seed it with the current `0.7.0` schema so the very first `wiki-update` has a merge base.

**Dependencies:** none.

**Files:**
- `schema-history/0.7.0/CLAUDE-template.md` (create — copy of canonical)
- `schema-history/0.7.0/templates/*.md` (create — copies of the nine canonical templates)

**Approach:** Byte-for-byte copy of the current canonical bundle (`skills/wiki-setup/assets/CLAUDE-template.md` + `skills/wiki-setup/assets/templates/*.md`) into the **plugin-root** `schema-history/0.7.0/`. No transformation. This establishes the archive layout that U7's version-bump rule maintains going forward. The canonical bundle stays in place as "latest"; the archive holds the immutable record of each released version. Plugin-root home (not under `wiki-setup/assets/`) reflects that the archive is plugin-wide state read by `wiki-update`, resolved via `${CLAUDE_PLUGIN_ROOT}/schema-history/`.

**Patterns to follow:** mirror the existing `skills/wiki-setup/assets/templates/` layout exactly.

**Test scenarios:** `Test expectation: none -- pure asset seeding; correctness is asserted by U2's byte-identity test over the whole bundle (KTD-5).`

**Verification:** `schema-history/0.7.0/CLAUDE-template.md` and all nine `schema-history/0.7.0/templates/*.md` exist and diff clean against the canonical bundle under `skills/wiki-setup/assets/`.

---

### U2. `scripts/schema_update.py` — version detection, compare, base reconstruction, `--report`

**Goal:** The deterministic, testable core: parse frontmatter, compare versions, locate/reconstruct the merge base, and emit a `--report` JSON the skill consumes.

**Requirements:** schema-versioning contract (origin *Dependencies / Assumptions*).

**Dependencies:** U1 (archive must exist to resolve a base).

**Files:**
- `scripts/schema_update.py` (create)
- `scripts/test_schema_update.py` (create)

**Approach:**
- **Reuse `obsidian.py`, do not reimplement.** `scripts/obsidian.py` already provides `split_frontmatter()` and `read_schema_version(vault)` (the latter is consumed by `checkrunner.py`) for exactly this flat-YAML CLAUDE.md frontmatter. Import and use them rather than writing a parallel parser — a second parser would risk drifting from the one the maintenance suite already depends on. `schema_update.py` adds only the migration-specific helpers below.
- `compare(current, bundled)` → one of `up-to-date` / `behind` / `ahead` / `unknown`. Semver compare (stdlib parse; no external deps). `unknown` when `read_schema_version` yields `None`.
- `resolve_base(version)` → path into plugin-root `schema-history/<version>/`, or `None` when that version predates the archive.
- `personalize(template_text, owner_name)` → substitute `{{OWNER_NAME}}` → owner name and `{{TODAY}}` → the relevant date so an archived template renders into the owner's space. Forward-only literal substitution; never reverse-tokenizes.
- `validate_owner_name(name)` → reject empty, names containing `{{`/`}}`, or newlines (KTD-7); the skill confirms interactively before any use.
- `--report` mode prints JSON mirroring the lint contract shape: `{current_version, bundled_version, status, base_available, owner_name_source}`.

**Patterns to follow:** `scripts/obsidian.py` (`split_frontmatter`, `read_schema_version`) for frontmatter/version parsing — **reused, not duplicated**; `lint_checks.py` for the `--report`-emitting CLI style; `report.py` for JSON contract discipline. `resolve-vault.sh` is the upstream vault resolver the skill calls first.

**Technical design (directional, not implementation spec):**
```
status = compare(parse(vault/CLAUDE.md).schema_version, parse(bundled).schema_version)
base   = resolve_base(current_version)        # None if pre-archive
# report tells the skill which branch to take before any mutation
```

**Test scenarios:**
- `read_schema_version` (reused from `obsidian.py`) returns the version for a well-formed CLAUDE.md, and `None` for missing/empty/malformed frontmatter without raising. (Verifies the reuse wiring, not a reimplementation.)
- `compare`: equal versions → `up-to-date`; vault older → `behind`; vault newer → `ahead`; `None` current → `unknown`.
- `compare` handles multi-digit/patch segments correctly (e.g. `0.9.0` < `0.10.0`).
- `resolve_base` returns the archive path for an archived version; `None` for a version not in the archive.
- `personalize` substitutes every `{{OWNER_NAME}}` and `{{TODAY}}` occurrence; leaves other text byte-identical; performs no reverse substitution.
- `validate_owner_name` accepts a normal name; rejects empty, names containing `{{`/`}}`, and names containing a newline (KTD-7).
- `--report` emits valid JSON with all contract keys for each status branch.
- **KTD-5 drift guard (whole bundle):** every file under `schema-history/<latest>/` — `CLAUDE-template.md` **and** all nine `templates/*.md` — is byte-identical to the canonical bundle under `skills/wiki-setup/assets/`. The test enumerates the archived files so a missing or extra file also fails.

**Verification:** `python3 -m unittest scripts/test_schema_update.py` passes; `--report` against a fixture vault prints the expected status.

---

### U3. 3-way merge engine in `schema_update.py`

**Goal:** Produce a merged `CLAUDE.md` that carries the new schema while preserving the owner's hand-edits, surfacing conflicts when edits collide with schema changes.

**Dependencies:** U2.

**Files:**
- `scripts/schema_update.py` (extend)
- `scripts/test_schema_update.py` (extend)

**Approach:**
- Split frontmatter from body (via `obsidian.py:split_frontmatter`) for `theirs` / `base` / `ours` (KTD-3). Reconstruct frontmatter deterministically; 3-way merge only the body.
- `base` = `personalize(resolve_base(current)/CLAUDE-template body, owner_name)`; `ours` = `personalize(bundled CLAUDE-template body, owner_name)`; `theirs` = live body. Re-personalizing both `base` and `ours` with the same owner name keeps schema-origin name lines identical on both sides so they never enter the conflict surface (KTD-7).
- Invoke `git merge-file -p theirs base ours` on temp files → merged text (exit 0) or conflict-marked text (exit >0).
- **Fence-aware conflict parsing (KTD-7):** scan the merged text tracking code-fence state (` ``` ` / `~~~` open/close); treat `<<<<<<<` / `=======` / `>>>>>>>` as real conflict markers only at column 0 **outside** a fence. Literal marker-like content inside a fenced block is not mis-counted as a conflict.
- Fallbacks: no `git` on PATH **or** `resolve_base` is `None` → return a `mode: overwrite` result carrying a unified diff (`difflib`) for the skill to show before backup-and-overwrite.
- Return a structured result: `{mode: merge|overwrite, outcome: clean|conflicts, conflict_count, merged_text, diff_text}`.

**Patterns to follow:** subprocess + tempfile usage kept stdlib-only; degrade gracefully like `resolve-vault.sh` branches on tokens.

**Technical design (directional, not implementation spec):**
```
frontmatter -> rebuilt deterministically (new schema_version, preserved created, updated=today)
body        -> git merge-file -p theirs base ours
  exit 0  -> clean
  exit >0 -> conflicts (markers preserved for interactive resolution)
no git / no base -> difflib unified diff + overwrite mode
```

**Test scenarios:**
- Owner made **no** body edits → merged body equals re-personalized new template (clean fast-forward).
- Owner edits a section the new schema did **not** touch → edit preserved, schema additions present, clean.
- Owner edits a section the new schema **also** changed → conflict markers present, `conflict_count >= 1`.
- Frontmatter reconstruction: `schema_version` = bundled, `created` preserved from theirs, `updated` = today — regardless of body merge outcome.
- `resolve_base` `None` (pre-archive version) → `mode: overwrite`, `diff_text` populated, no merge attempted.
- `git` absent (simulate via PATH) → `mode: overwrite` fallback, no exception.
- `personalize` applied to base/ours keeps owner name out of the conflict surface (no spurious name-line conflicts).
- **Name-as-substring:** owner name is a common word that also appears in owner-added prose → schema-origin name lines still don't conflict, and incidental occurrences in `theirs` are left untouched (no false conflicts).
- **Fence-aware parsing:** a body whose fenced code block contains literal `<<<<<<<` / `=======` / `>>>>>>>` lines yields `conflict_count == 0` when the merge is otherwise clean; a real conflict outside any fence is still counted.

**Verification:** unit tests cover clean / preserved-edit / conflict / overwrite-fallback paths; conflict markers are parseable.

---

### U4. Persist setup variables in `settings.json` (`wiki-setup` Step 8)

**Goal:** Record `owner_name` and `created` in the vault's `settings.json` entry so future regen/merge needs no extraction. Additive and backwards-compatible.

**Requirements:** R15; enables KTD-4.

**Dependencies:** none on U1–U3, but **must land before U5** — U5's primary (settings-driven) owner-name path reads the `owner_name` field this unit writes. If U5 lands first, its primary path is untestable end-to-end and every run falls through to best-effort extraction. Sequence U4 ahead of U5.

**Files:**
- `skills/wiki-setup/SKILL.md` (modify Step 8 — Settings Registration)
- `CLAUDE.md` (modify Global Settings section — document the new fields)

**Approach:** Extend the written vault entry from `{vault_path, description}` to `{vault_path, description, owner_name, created}`. Document the superset in the repo `CLAUDE.md` Global Settings block. Existing skills reading only `vault_path` / `default_vault` are unaffected.

**Patterns to follow:** the existing Step 8 JSON-merge logic (read-modify-write, preserve other vaults, default-vault prompt).

**Test scenarios:** `Test expectation: none -- SKILL.md is agent-executed prose, not unit-testable; the field contract is exercised live and consumed by U5.` (The drift guard for the *documented* schema is reviewer verification against U5's read logic.)

**Verification:** a fresh `wiki-setup` run writes `owner_name` + `created` into the vault entry; the repo `CLAUDE.md` settings example shows the superset.

---

### U5. `skills/wiki-update/SKILL.md` — the orchestration

**Goal:** The interactive skill: detect drift, recover the owner name, back up, merge (or overwrite), resolve conflicts with the owner, write results, refresh templates and folders, and hand off to maintenance.

**Requirements:** the `wiki-update` capability (this plan); ties to R15/R16/maintenance per traceability.

**Dependencies:** U2, U3 (core), U4 (settings fields it reads/writes), U1 (archive).

**Files:**
- `skills/wiki-update/SKILL.md` (create)

**Approach (step sequence, mirroring `wiki-lint`):**
1. **Resolve vault** — named arg or `resolve-vault.sh`; branch on `VAULT_PATH:` / `NO_DEFAULT` / `NOT_CONFIGURED` exactly as the maintenance skills do.
2. **Detect drift** — run `schema_update.py --report`; branch on status:
   - `up-to-date` → report "already current", offer the maintenance handoff, exit.
   - `ahead` → warn the vault is newer than the installed plugin; suggest updating the plugin; exit without writing.
   - `unknown` → legacy/malformed frontmatter; proceed via overwrite path with explicit caution.
   - `behind` → continue.
3. **Recover owner name** — from `settings.json` (`owner_name`); else best-effort extract from `CLAUDE.md` and confirm via `AskUserQuestion` (recommended = extracted guess). When extraction finds **nothing** (the owner edited away the anchor sentences), fall back to asking outright with no pre-fill rather than guessing. Run the value through `validate_owner_name` (KTD-7) before use; persist the confirmed value back to `settings.json` (KTD-4) so future runs skip this.
4. **Back up** — copy `CLAUDE.md` **and all nine page templates** into `meta/backups/<timestamp>/` (KTD-6; unconditional, because which templates change isn't known until step 6); announce the backup path.
5. **Merge** — invoke the core; on `clean`, show a concise summary of what changed; on `conflicts`, walk each (fence-aware) conflict region via `AskUserQuestion` (keep mine / take new / show both) until resolved; on `overwrite` fallback, present the unified diff and confirm before writing.
6. **Write & refresh** — write the merged `CLAUDE.md` **atomically** (temp file + rename, KTD-6) so an interrupted run never leaves a half-merged file; for the nine page templates, detect-modified vs archived base (diff) → unchanged ones refresh silently, modified ones are backed up and the owner is asked before overwrite; additively `mkdir -p` any new schema folders; never delete.
7. **Completion report** — old → new `schema_version`, files changed, backup location **and the one-line restore command** (copy the backup back over `CLAUDE.md`), conflicts resolved, templates refreshed, folders added.
8. **Next steps (handoff)** — suggest `mneme:wiki-lint` to reconcile existing pages against any newly-required fields; a *suggestion*, never an automatic `Skill` call (per repo conventions).

**Patterns to follow:** `skills/wiki-lint/SKILL.md` structure and tone; `${CLAUDE_PLUGIN_ROOT}/...` for all plugin-root references; `AskUserQuestion` for every choice with a recommended-first option.

**Test scenarios:** `Test expectation: none -- SKILL.md is agent-executed orchestration; the testable logic lives in U2/U3. Reviewer verifies every branch (up-to-date / behind / ahead / unknown), the backup-before-write ordering, and the conflict-resolution loop against the wiki-lint reference.`

**Verification:** live run against an out-of-date fixture vault updates the schema, preserves a planted hand-edit, surfaces a planted conflict, writes a backup, and leaves `raw/`/`wiki/` untouched.

---

### U6. `skills/wiki-update/README.md` — user docs

**Goal:** User-facing documentation: what it does, prerequisites, invocation, what you get, safety guarantees.

**Dependencies:** U5 (documents its behavior).

**Files:**
- `skills/wiki-update/README.md` (create)

**Approach:** Follow the maintenance-suite README shape. Emphasize the safety contract (backup-before-write, content never touched, hand-edits preserved or surfaced as conflicts) and the maintenance handoff.

**Test scenarios:** `Test expectation: none -- documentation.`

**Verification:** README covers trigger phrases, prerequisites (a registered vault), the backup guarantee, and the conflict-resolution UX.

---

### U7. Repo docs + `BACKLOG.md` + version bump + archive/bump rule

**Goal:** Make the plugin self-consistent: list the new skill, document the schema-history archive and the snapshot-on-bump rule, document the settings superset, **reconcile `BACKLOG.md` and codify a standing rule that keeps it current**, bump the version, note the release.

**Dependencies:** U1–U6.

**Files:**
- `CLAUDE.md` (modify — add `wiki-update` to implemented skills; add archive + "snapshot outgoing version into `schema-history/` before bumping `schema_version`" to the Versioning section; confirm Global Settings superset from U4; add the **BACKLOG.md maintenance rule** described below)
- `BACKLOG.md` (modify — remove `wiki-update` from planned work once shipped; **reconcile pre-existing drift**: the maintenance suite (`wiki-lint`, `wiki-audit`, `wiki-gaps`), `wiki-triage`, and the `wiki-steward` agent are already implemented in v0.4.0 but still listed as planned)
- `.claude-plugin/plugin.json` (modify — `0.4.0` → `0.5.0`, minor: new backwards-compatible skill)

**Approach:**
- Update the implemented-skills sentence in repo `CLAUDE.md`. Add the version-bump sub-rule: *when bumping `schema_version` in `CLAUDE-template.md`, first copy the outgoing canonical bundle into `schema-history/<old-version>/`* — this keeps `wiki-update`'s merge base available for the next migration.
- **Codify a `BACKLOG.md` maintenance rule** in repo `CLAUDE.md`, parallel to the version-bump rules: *every change that ships, defers, or reshapes a skill/agent/plugin feature must update `BACKLOG.md` in the same change — move shipped items out of the roadmap, add newly-planned ones, and revise priorities so the backlog never drifts from reality.* This is the governance fix the owner asked for; it makes "keep the backlog current" a checked step rather than an aspiration.
- **Reconcile `BACKLOG.md` now** for this change and the already-shipped maintenance suite, so the file starts from a true baseline.
- Bump `plugin.json` to `0.5.0`; create the GitHub release per repo policy (release notes live on GitHub, no CHANGELOG).

**Patterns to follow:** the existing repo `CLAUDE.md` "Version bump rules" section — add the BACKLOG.md rule as a sibling governance step so both fire on every change.

**Test scenarios:** `Test expectation: none -- docs/manifest. The byte-identity guard (U2) protects the archive-vs-canonical invariant this rule depends on.`

**Verification:** repo `CLAUDE.md` lists `wiki-update`, the archive/bump rule, and the BACKLOG.md maintenance rule; `BACKLOG.md` no longer lists shipped skills as planned and reflects this change; `plugin.json` reads `0.5.0`; release drafted.

---

## Deferred Implementation Notes

- **Exact `git merge-file` flags / temp-file choreography** — resolved at implementation against the installed `git`; the plan fixes the *strategy* (3-way, conflict markers, `-p` to stdout), not the invocation.
- **Owner-name extraction heuristic** — the precise prose pattern to scrape from a legacy `CLAUDE.md` is best chosen against real files; the design only commits to "best-effort extract → confirm → persist."
- **Conflict-region presentation granularity** — whether to present per-hunk or per-section is an interaction-design call best made while seeing real conflict output.
- **Page-template merge** — full 3-way merge for the nine templates is deferred (U5 uses modified-detection + backup); revisit if owners are found to hand-edit templates often.

---

## System-Wide Impact

- **`settings.json` schema (additive):** gains `owner_name` + `created` per vault. All existing readers use only `vault_path` / `default_vault`, so the change is transparent; `wiki-update` and `wiki-setup` are the only writers of the new fields.
- **Plugin asset layout:** introduces `schema-history/`, a new long-lived directory whose maintenance is now part of the version-bump ritual (U7). The byte-identity test (U2) is the guard against it drifting from canonical.
- **`CLAUDE-template.md` bump workflow:** every future `schema_version` bump now has a required predecessor step (snapshot to archive). Documented in repo `CLAUDE.md` so it is not forgotten.
- **Maintenance suite:** gains an upstream sibling — a schema update may introduce new required fields that `wiki-lint` then flags across existing pages, which is why U5 ends with that handoff.
- **`BACKLOG.md` governance (process change):** U7 codifies a standing rule in repo `CLAUDE.md` that every shipped/deferred/reshaped feature updates `BACKLOG.md` in the same change. This is a repo-wide workflow change beyond this feature — it also fixes existing drift (the v0.4.0 maintenance suite is still listed as planned). The rule sits alongside the version-bump rules so both are checked on every change.

---

## Dependencies / Prerequisites

- `git` available on PATH for the 3-way merge (graceful `difflib` + overwrite fallback when absent — U3).
- `python3` (stdlib only) — already the baseline for the maintenance scripts.
- A vault registered in `~/.config/mneme/settings.json` (the skill instructs the owner to run `wiki-setup` / `wiki-config` when not configured).
- The schema-history archive (U1) must exist before U2/U3/U5 can resolve a merge base.

---

## Risk Analysis & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Merge corrupts the owner's operating manual | Low | High | Backup-before-write (KTD-6); atomic write (temp + rename) prevents half-merged files on interruption; documented restore command; `git merge-file` is battle-tested; conflicts surfaced for human resolution. |
| Archive copy drifts from canonical, poisoning the merge base or template detection | Low | High | Whole-bundle byte-identity test (KTD-5, U2) covers `CLAUDE-template.md` **and** all nine templates — fails if any archived file ≠ canonical or is missing/extra. |
| Conflict markers collide with literal `<<<<<<<` inside fenced code in the manual | Medium | Medium | Fence-aware conflict parsing (KTD-7, U3) ignores marker-like content inside code fences. |
| Owner name is a common substring → spurious conflicts / mis-detected templates | Medium | Medium | Merge re-personalizes base+ours identically so schema name lines never conflict; `validate_owner_name` + interactive confirm (KTD-7). |
| Owner name mis-recovered → wrong name written throughout | Low | Medium | Confirm via `AskUserQuestion` before any write; ask outright (no pre-fill) when extraction finds nothing; persist confirmed value. |
| `git` unavailable in the owner's environment | Medium | Low | `difflib` diff + backup-and-overwrite fallback (U3); owner still gets the update, just without auto-merge. |
| Owner on a pre-archive schema version (no base) | Medium (early) | Low | Overwrite path with explicit caution + backup; hand-edits recoverable from the backup via the documented restore command. |
| Accidental deletion of owner content | Very low | High | Skill never deletes; folder creation is additive-only (`mkdir -p`); explicit scope boundary + reviewer check. |

---

## Alternative Approaches Considered

- **Backup-and-overwrite only (no merge).** Simpler, no archive, no `git`. Rejected as the *primary* path because it discards hand-edits — exactly the case the owner asked to preserve. Retained as the *fallback* when no base is archived or `git` is missing.
- **Version-chained migration scripts.** A directed migration per version step. Rejected (KTD-1): heavy infrastructure for a document that has no executable state and infrequent bumps; converge-to-latest reaches the same target state in one step.
- **Live-reference schema (vault points at the plugin template instead of copying it).** Would eliminate drift entirely but breaks the vault's self-contained, offline, personalized-snapshot identity and the `wiki-setup` contract. Out of scope — a different product shape.
- **Headless/agent update via `wiki-steward`.** Attractive for unattended runs, but merges can need human conflict resolution, which agents cannot prompt for. Deferred; `wiki-update` stays interactive.
