---
title: "feat: Add wiki maintenance suite (wiki-lint, wiki-audit, wiki-gaps, wiki-triage + wiki-steward agent)"
date: 2026-06-20
status: completed
origin: docs/brainstorms/mneme-wiki-plugin-requirements.md
---

# feat: Add wiki maintenance suite

The maintenance lifecycle stage as **three standalone detection skills, one actioner skill, and one agent that ties them together**:

- **`wiki-lint`** (R12) — structural consistency: frontmatter, tags, links.
- **`wiki-audit`** (R10) — stale, thin, or inconsistent pages.
- **`wiki-gaps`** (R11) — pages that should exist (broken-link targets, unreferenced concepts).
- **`wiki-triage`** — reads a maintenance report and walks the owner through applying the judgment-required items.
- **`wiki-steward`** (agent, R13 / A2) — the autonomous conductor: runs the three detection skills, applies the safe and low-risk fixes without confirmation, and emits a prioritized report of what's left. **Runs headless by default** (autonomous, no prompts).

Each of the three detection skills performs a **complete standalone function** — invoking one never depends on another. They share only **bundled assets** (a vault resolver and a shared Obsidian-awareness library), never another skill.

This plan is the maintenance-stage analogue of `2026-06-08-001-feat-wiki-ingest-skill-plan.md`.

---

## Problem Frame

The vault schema documents a complete **Lint Workflow** in CLAUDE.md (10 check dimensions), written for conversational in-vault use and run entirely by hand. A real maintenance pass (performed manually 2026-06-20 against the Hive-Mind vault) surfaced four facts that shape this design:

1. **Findings sort into three risk tiers.** *Safe* (deterministic, one correct outcome), *low-risk* (reversible, mechanical, no new prose, no correctness judgment), and *judgment* (irreversible or contentful decisions). The first two are automatable; the third is not.

2. **Naive checking over an Obsidian vault over-reports.** The manual pass flagged 19 "broken" links; only 2 were real. The rest were Obsidian *inert-link* contexts: escaped pipes in tables (`[[slug\|Display]]`) and wiki-links inside code spans (`` `[[wiki-link]]` ``). Any check that doesn't model these cries wolf — and an auto-fixer that "corrects" a false positive does damage. This logic must live in **one** place so it can't drift across the three skills.

3. **The maintenance space is three distinct skills plus a conductor** (R12 lint, R10 audit, R11 gaps; R13 agent). Each skill answers a different question and must stand alone; the agent runs them as a pipeline.

4. **Unattended operation is an agent's job, not a skill's.** A skill can stop and ask the owner; a headless run has no owner to ask. Running detect→fix→report to completion without confirmation is what `wiki-steward` exists to do.

---

## Requirements Traceability

| Requirement | Realized as |
|-------------|-------------|
| R12 | `wiki-lint` skill — frontmatter, tag, and link consistency. Standalone. |
| R10 | `wiki-audit` skill — stale / thin / inconsistent pages. Standalone. |
| R11 | `wiki-gaps` skill — pages that should exist. Standalone. |
| R13 / A2 | `wiki-steward` agent — autonomous pipeline over the three skills; applies safe + low-risk, reports the rest. *(R13 scopes the agent to audit + gaps; this plan deliberately expands it to also run lint, for one complete pass over all categories.)* |
| R13 / A2 (support) | `wiki-triage` skill — interactive consumer of the agent's report; the human-facing way to work the prioritized to-do list R13's flow hands to the owner (a deliberate plan-local addition, not a separate R-id). |

This plan **resolves the brainstorm's open question** *"how should agents be defined — `agents/*.md` or skills that invoke subagents?"* — per owner direction, as **`agents/*.md`**, establishing the plugin's `agents/` directory. *(The R14 ingestion agent is explicitly out of scope here; it is a separate plan that will reuse this `agents/` mechanism.)*

It also resolves the plan's three implementation open questions (research-backed, owner-confirmed): plugin-root references use **`${CLAUDE_PLUGIN_ROOT}`**; the agent **calls the per-skill check scripts directly** (which import the shared `scripts/obsidian.py`) rather than invoking skills, with **no `skills:` preload** (since `AskUserQuestion` is unavailable to subagents and the agent must be headless-safe); the agent uses **`model: opus`** (alias, not pinned). Per owner direction it additionally **extends and slims the vault schema** (`CLAUDE-template.md`, U10, `schema_version` `0.2.0 → 0.3.0`) — adding the data-contract elements the checks need and replacing the procedural Lint Workflow with a pointer to the suite — and adds **skill-handoff progressive disclosure** across the detection skills.

---

## Scope Boundaries

### In scope
- Three standalone detection skills: `wiki-lint`, `wiki-audit`, `wiki-gaps`. Each detects its category and, interactively, offers to apply the safe/low-risk fixes in that category and guides the judgment ones.
- `wiki-triage` skill — interactive report consumer/actioner.
- `wiki-steward` agent — autonomous conductor (safe + low-risk); runs headless by default.
- One bundled, shared **Obsidian-awareness library** (`scripts/obsidian.py`) — link parsing, inert-context classification, vault link-graph — consumed by each skill's own category check script and by the agent.
- Per-skill check scripts (`skills/<skill>/scripts/<cat>_checks.py`), each importing the shared core and implementing only its category's dimensions + fixes.
- Promotion of `resolve-vault.sh` to plugin-level `scripts/` (deferred trigger from the wiki-ingest plan — now fired).
- The maintenance **report format** and the `meta/maintenance-reports/` convention (created on demand).
- **Skill handoff / progressive disclosure** — each detection skill ends with a "Next steps" suggestion of the next skill in the order of operations (suggestion, never a dependency).
- **Extending + slimming the vault schema** (`CLAUDE-template.md`, U10) — add the data-contract elements the checks need (`last_checked`, bare-`?` rule, forward-link annotation), replace the Lint Workflow how-to with a suite pointer, keep Hygiene Rules, narrow the README runtime-independence claim, bump `schema_version` `0.2.0 → 0.3.0`.
- READMEs for the four skills; top-level `README.md` order-of-operations section; plugin `CLAUDE.md` updated to document the `agents/` mechanism, the `${CLAUDE_PLUGIN_ROOT}` convention, and the handoff convention.

### Deferred / out of scope
- **The R14 ingestion agent** — separate plan; only the `agents/` mechanism is shared.
- **Autonomy beyond low-risk** — the agent never autonomously does judgment-tier work (page creation, promotions, orphan wiring, conflict resolution, tag merges); those always route to the report.
- **Stale-claims *detection*** (semantic) — surfaced by the agent's / `wiki-audit`'s model reasoning, not the check script.
- **Scheduling / invocation** — out of scope. The agent runs headless by default; how and when it is triggered is outside the plugin.

### Outside this product's identity
- LLM-agnostic tooling; non-mneme vaults.

---

## Key Technical Decisions

**Three standalone skills, each owning its checks — sharing only a thin core.** Each detection skill is independently invocable and ships **its own category check script** under `skills/<skill>/scripts/`. The only things they share are **bundled plugin assets** at the plugin root (`scripts/resolve-vault.sh`, `scripts/obsidian.py`) — never another skill. The shared `scripts/obsidian.py` keeps the must-not-drift Obsidian-awareness logic (link parsing, inert-context classification, vault link-graph) in **one place** so it can't be re-derived (and re-broken) three times, while each skill's own checks stay with the skill. (`${CLAUDE_PLUGIN_ROOT}/scripts/` is an established plugin convention — cf. Anthropic's `hookify`.)

**Per-skill check scripts over a shared core — not a monolith.** Instead of one `--category`-switched script, each skill bundles a focused check script (`skills/wiki-lint/scripts/lint_checks.py`, `skills/wiki-audit/scripts/audit_checks.py`, `skills/wiki-gaps/scripts/gaps_checks.py`) that `import`s the shared `scripts/obsidian.py` and implements only its category's dimensions + fixes. Each exposes `--report` (detect → JSON), `--fix-safe`, `--fix-lowrisk`. A skill runs its own script; the **agent runs all three** and merges. Nothing orchestrates the skills — the shared core is a library, the per-skill scripts are leaves.

**Three risk tiers define what runs unattended.**
- **Safe** — deterministic, single correct outcome: unique-candidate broken-link slug fix; `last_checked` backfill (to the page's `ingested` date — never "today"); `parent:` path correction.
- **Low-risk** — reversible, mechanical, *no new prose, no correctness judgment*: strip stale `(forward link)` annotations once the target page exists; de-bracket illustrative/code-span phantom links the checker classified as non-links; frontmatter field hygiene.
- **Judgment (report only)** — page creation (missing/graduation), stub promote/delete, orphan wiring, conflict resolution, tag merges, stale-claim rewrites, `index.md` entry rewriting.

`wiki-steward` autonomously applies **safe + low-risk** and reports judgment. The detection skills, run interactively, can apply safe + low-risk in their category with the owner present and surface judgment items for `wiki-triage` or inline handling. *(Reviewed and owner-confirmed: applying low-risk fixes headless — no human, no git precondition — is a deliberate accepted risk. Mitigation is discipline, not a gate: low-risk classification stays conservative and the agent never auto-applies judgment-tier work.)*

**Obsidian-awareness (one place, mandatory).** Before flagging links, `scripts/obsidian.py` strips inline/fenced code spans, treats `\|` as the display pipe, resolves `[[a#anchor]]`→`a`, and treats `CLAUDE`/`index`/`log`/`tags` as valid targets. It distinguishes sanctioned forward-links (annotated / known-deferred) from accidental breaks. It flags only a **bare `?`** as an entire frontmatter value, not `?` *within* a value (this validity rule and the forward-link annotation are added to the data contract by U10's schema extension). Acceptance gate: 0 broken-link false positives across a fixture vault enumerating known inert-link contexts **and** the 2026-06-20 Hive-Mind pass (not the single pass alone).

**Agent vs. skills — conductor vs. operations.** `wiki-steward` is an `agents/*.md` subagent (namespaced `mneme:wiki-steward`) with its own context, `model: opus` (alias, **not** a pinned id, for forward-compatibility), a system prompt encoding the maintenance philosophy (the tier boundary, Obsidian-awareness reliance, report-first, no fabrication, the vault CLAUDE.md as schema authority), and a `tools` allowlist (`Bash`, `Read`, `Write`, `Edit`, `Glob`, `Grep`). It is autonomous and runs headless by default. **`AskUserQuestion` is unavailable to subagents**, so the agent cannot — and must not — drive the interactive skill flows; it must complete end-to-end with no prompts (it may be schedule-triggered with no human present). **Composition (resolved):** the agent **calls the three per-skill check scripts directly via `Bash`** (each imports the shared `scripts/obsidian.py`), merges their reports, runs its semantic pass, then applies their `--fix-safe`/`--fix-lowrisk`. It carries the 3 semantic-dimension definitions inline in its system prompt (kept in sync with `wiki-audit`'s body). **No `skills:` preload** — preloading interactive skill bodies into a headless agent is an anti-pattern. It does not call skills through the `Skill` tool. The DRY core is `scripts/obsidian.py` + the per-skill scripts, reused identically by skills and agent. The detection skills stay the human-facing, standalone entrypoints to each category; `wiki-triage` is the human-facing way to work the agent's report.

**Schema-version-aware, not schema-snapshot-bearing.** No unit ships a `CLAUDE-template.md` snapshot; all read `VAULT_PATH/CLAUDE.md` as the live authority for the **data contract** — page types, frontmatter fields, naming (the `wiki-ingest` precedent). The one schema-coupled check (the `?` rule) keys off the vault's `schema_version`. **Authority split (changed by U10):** the *procedural* lint dimensions previously lived in the vault CLAUDE.md's Lint Workflow; U10 slims that out, so the **suite itself** (`scripts/obsidian.py` + the per-skill check scripts + skill bodies) now owns the per-dimension detect/fix procedure, while the vault CLAUDE.md remains authority for *what a valid page is*. U10 also **extends** that data contract with the elements the checks need (`last_checked`, the bare-`?` validity rule, the `(forward link)` annotation), and — owner-directed — removes the judgment-dimension *definitions* along with the procedure, making the suite their sole home. Because U10 edits `CLAUDE-template.md`, this plan **does** bump `schema_version` one minor: `0.2.0 → 0.3.0` (the current canonical value is `0.2.0`) — superseding this plan's earlier "no `schema_version` bump" assumption.

**Plugin-root references via `${CLAUDE_PLUGIN_ROOT}` (resolved).** The shared `scripts/` live at the plugin root, referenced as `${CLAUDE_PLUGIN_ROOT}/scripts/resolve-vault.sh` and `${CLAUDE_PLUGIN_ROOT}/scripts/obsidian.py` (the per-skill check scripts import the latter). `${CLAUDE_PLUGIN_ROOT}` is the documented env-var substitution for the plugin install root, valid in SKILL.md bodies, agent markdown, and the scripts themselves. The plan's earlier hedge is settled: there is **no** `{plugin_base_dir}` placeholder, and relative traversal (`{skill_base_dir}/../../scripts/`) is **discouraged and unreliable after install** — the plugin cache only guarantees the plugin's own tree. Per-skill assets that stay inside a skill keep using `{skill_base_dir}`; only cross-skill / plugin-root references use `${CLAUDE_PLUGIN_ROOT}`.

**Skill handoff / progressive disclosure (new).** Each detection skill ends with a natural-language handoff suggesting the next skill in the maintenance order of operations — mirroring `compound-engineering`'s `ce-brainstorm` Phase-4 handoff. There is no formal skill-chaining tool; the convention is a closing "Next steps" offer (and the skills never *depend* on each other — handoff is a suggestion, not a call). Two documented lanes (see README, U9): **manual lane** `wiki-lint → wiki-audit → wiki-gaps`; **automated lane** `wiki-steward` (one pass over all categories) `→ wiki-triage` (work the report). `wiki-lint` hands off to `wiki-audit`, `wiki-audit` to `wiki-gaps`, and `wiki-gaps` points to `wiki-steward` / `wiki-triage` for a comprehensive automated pass.

**Vault schema: extend + slim (U10, owner-directed; reviewed).** U10 makes one coherent `0.2.0 → 0.3.0` edit to `CLAUDE-template.md`: it **extends** the data contract with the elements the checks need (`last_checked`, the bare-`?` validity rule, the `(forward link)` annotation), and **fully slims** the procedural Lint Workflow how-to into a short `## Maintenance` pointer to the suite (the judgment-dimension definitions go too). Hygiene Rules stay. The README's runtime-independence claim is narrowed so it no longer promises plugin-free maintenance. Accepted trade: a plugin-less vault has no in-vault maintenance guidance — chosen for non-duplication over self-containment.

**Report is the contract from agent to `wiki-triage`.** Written to `VAULT_PATH/meta/maintenance-reports/YYYY-MM-DD-HHMM.md` — human-readable markdown with a machine-parseable findings list (stable `id`, category, tier, page, proposed action, per-item `status:` of `applied`/`open`/`skipped`). `wiki-steward` produces it; `wiki-triage` consumes and updates it.

---

## Output Structure

```
agents/
└── wiki-steward.md              # NEW — autonomous conductor (R13 / A2); establishes agents/
scripts/
├── resolve-vault.sh             # PROMOTED from skills/wiki-ingest/scripts/
└── obsidian.py                  # NEW — shared Obsidian-awareness library (link parse, inert classify, link-graph)
skills/wiki-lint/{SKILL.md, README.md, scripts/lint_checks.py}    # NEW (R12)
skills/wiki-audit/{SKILL.md, README.md, scripts/audit_checks.py}  # NEW (R10)
skills/wiki-gaps/{SKILL.md, README.md, scripts/gaps_checks.py}    # NEW (R11)
skills/wiki-triage/{SKILL.md, README.md}   # NEW — report consumer/actioner
skills/wiki-ingest/SKILL.md                # MODIFIED — resolve-vault.sh reference → ${CLAUDE_PLUGIN_ROOT}
skills/wiki-setup/assets/CLAUDE-template.md # MODIFIED (U10) — extend data contract + slim Lint Workflow → pointer; schema_version 0.2.0→0.3.0
README.md                                  # MODIFIED (U9 order-of-operations + skills table; U10 runtime-independence claim)
CLAUDE.md                                  # MODIFIED (U9) — agents/, ${CLAUDE_PLUGIN_ROOT}, handoff conventions
```

At runtime, in the vault: `meta/maintenance-reports/YYYY-MM-DD-HHMM.md` (on demand).

---

## Implementation Units

### U1. Promote `resolve-vault.sh` + establish plugin-level `scripts/`
**Goal:** Move `resolve-vault.sh` to plugin-level `scripts/` so all skills and the agent share one resolver.
**Dependencies:** none.
**Files:** `scripts/resolve-vault.sh` (moved); `skills/wiki-ingest/SKILL.md` (modified); remove empty `skills/wiki-ingest/scripts/`.
**Approach:** `git mv skills/wiki-ingest/scripts/resolve-vault.sh scripts/resolve-vault.sh`; update the wiki-ingest reference from `{skill_base_dir}/scripts/resolve-vault.sh` to `${CLAUDE_PLUGIN_ROOT}/scripts/resolve-vault.sh`; remove the now-empty `skills/wiki-ingest/scripts/`; document the `${CLAUDE_PLUGIN_ROOT}` convention in the plugin CLAUDE.md (U9). **Resolved:** the reference mechanism is `${CLAUDE_PLUGIN_ROOT}` — not `{plugin_base_dir}` (does not exist) and not relative traversal (unreliable after install).
**Verification:** `wiki-ingest` still resolves the default vault from a non-vault dir (regression) under both `--plugin-dir` and a user-scope install — the installed-cache path is exactly where relative traversal would have broken, so `${CLAUDE_PLUGIN_ROOT}` must resolve correctly there.

### U2. Shared Obsidian-awareness core — `scripts/obsidian.py`
**Goal:** One importable Python module owning the must-not-drift logic every category check depends on. No CLI of its own — it's a library the per-skill check scripts (U3–U5) and the agent (U7) import via `${CLAUDE_PLUGIN_ROOT}/scripts/`.
**Dependencies:** U10 (the schema defines `last_checked`, the bare-`?` validity rule, and the `(forward link)` annotation the consumers validate against). Runtime: stdlib; `python3`.
**Responsibilities (the single source for):**
- *Link extraction + resolution:* strip inline/fenced code spans, treat `\|` as the display pipe, resolve `[[a#anchor]]`→`a`, treat `CLAUDE`/`index`/`log`/`tags` as valid targets, distinguish sanctioned forward-links from accidental breaks.
- *Inert-context classification:* escaped pipes in tables, code spans, fenced/nested code blocks, HTML comments, frontmatter `[[...]]`, block anchors `^id`, embeds `![[...]]`, blockquotes.
- *Vault link-graph:* inbound/outbound index, so `wiki-audit`'s orphan/stub checks share one graph instead of each re-walking links.
- *Shared finding shape + tier enum* used by all category scripts and consumed by the U8 report.
**Verification:** unit fixtures enumerating every inert-link context above → none classified as broken; link-graph inbound counts correct on a known fixture; importable from a script running out of a skill dir via `${CLAUDE_PLUGIN_ROOT}/scripts/`. (The end-to-end 0-false-positive gate lives with the per-skill scripts in U3–U5 + the live Hive-Mind pass.)
**Test expectation:** pure-logic module — unit tests for link classification and graph construction are the primary coverage.

### U3–U5. The three detection skills (`wiki-lint`, `wiki-audit`, `wiki-gaps`)
**Goal:** Each a standalone skill = a `SKILL.md` + its own bundled check script (`skills/<self>/scripts/<cat>_checks.py`, importing `scripts/obsidian.py`). Flow: resolve vault (`${CLAUDE_PLUGIN_ROOT}/scripts/resolve-vault.sh`) → read `VAULT_PATH/CLAUDE.md` (schema authority) → run its own check script `--report` → present findings → (interactive) `AskUserQuestion` to apply safe/low-risk in-category (its script's `--fix-safe`/`--fix-lowrisk`) and guide judgment items → bookkeeping (`log.md` `lint`; reconcile `index.md` count-drift for `wiki-gaps`) → **handoff:** closing "Next steps" offer (`wiki-lint → wiki-audit → wiki-gaps`; `wiki-gaps` points to `wiki-steward` / `wiki-triage`).
**Dependencies:** U1, U2.
**Files (per skill):** `skills/<self>/{SKILL.md, README.md}` + `skills/<self>/scripts/<cat>_checks.py` (+ its unit-test fixtures).
**Checks owned by each script** (each emits the shared finding shape with a per-dimension tier):
- *`lint_checks.py` (R12):* `broken-link` (via core; safe only on unique date-prefix candidate), `frontmatter-missing` (judgment), `frontmatter-bare-question` (judgment), `parent-path-mismatch` (safe), `source-paths-missing-raw` (judgment), `last-checked-missing` (safe), `stale-forward-annotation` (low-risk), `phantom-illustrative-link` (low-risk), `tag-single-use`/`tag-near-synonym` (judgment).
- *`audit_checks.py` (R10):* `orphan` (judgment), `stub` (+inbound; judgment), `stale-reference` (judgment), `conflict-callout` (classify resolved-vs-open; judgment) — all over the core's link-graph.
- *`gaps_checks.py` (R11):* `missing-page` (+referrer count, `--min-refs` default 3; judgment), `count-drift` (index vs disk; judgment).
**Per-script output:** `--report` → `{schema_version, category, counts, findings:[{id,category,dimension,tier,page,detail,proposed_action}]}`; `--fix-safe`/`--fix-lowrisk` → `{applied:[...], skipped:[...]}`. Idempotent; never touch judgment-tier findings.
**Semantic dimensions (`wiki-audit` only):** `stale-claims`, `concept-graduation`, `suggested-investigations` are *not* script-detectable; `wiki-audit`'s `SKILL.md` body defines and surfaces them via model reasoning — the same definitions the `wiki-steward` agent carries in its system prompt (F5).
**Standalone guarantee:** none invokes another skill; the only shared code is the imported `scripts/obsidian.py`. The handoff is a **suggestion** (natural-language progressive disclosure), never a dependency or a `Skill`-tool call.
**Descriptions (frontmatter):** category-specific trigger phrases — e.g. wiki-lint: "lint the wiki", "check frontmatter/links/tags"; wiki-audit: "audit the vault", "find stale/thin pages"; wiki-gaps: "find missing pages", "what should exist".
**Patterns:** `wiki-ingest/SKILL.md` (vault-bridge, `AskUserQuestion`); `${CLAUDE_PLUGIN_ROOT}/scripts/` for the shared core (cf. `hookify`) and `{skill_base_dir}` for in-skill assets; `compound-engineering` `ce-brainstorm` Phase-4 handoff for the closing offer. The vault CLAUDE.md remains authority for the page schema the checks validate against.
**Verification:** each invoked alone from a non-vault dir produces correct in-category findings, applies only safe/low-risk on approval, ends with the correct handoff; **0 broken-link false positives** across the inert-link fixture (U2) **and** the live 2026-06-20 Hive-Mind pass; `--fix-*` diff never touches judgment-tier items.

### U6. `wiki-triage/SKILL.md` — report consumer
**Goal:** Read the latest (or named) report → read `VAULT_PATH/CLAUDE.md` (authority for actioning) → present open items by category → `AskUserQuestion` per cluster (fix/skip/defer) → apply per vault workflows → update item `status:`, bump touched `updated:`, append `log.md`, reconcile `index.md` → **handoff:** when all items are actioned, confirm the report is clear and suggest the next pass (re-dispatch `wiki-steward`).
**Dependencies:** U8 (format), U7 (producer).
**Description:** "triage the maintenance report", "work the to-do list", "resolve wiki findings".
**Verification:** produce a report via `wiki-steward`, run `wiki-triage`, action one approved item end-to-end, confirm report status updates.

### U7. `agents/wiki-steward.md` — autonomous conductor (R13 / A2)
**Goal:** Define the agent that runs the three categories as one autonomous, headless pipeline.
**Dependencies:** U1, U2, U3–U5 (it calls the per-skill check scripts), U8 (report format). *(No dependency on U6: the only shared artifact is the U8 report format — the agent produces it, `wiki-triage` consumes it. No build-order cycle.)*
**Approach:** subagent definition — frontmatter (`name: wiki-steward`; load-bearing `description` of when to dispatch; `tools` allowlist [`Bash`, `Read`, `Write`, `Edit`, `Glob`, `Grep`] — **no `Skill` / `AskUserQuestion`**, the latter unavailable to subagents anyway; `model: opus` (alias, not pinned); **no `skills:` preload** — preloading interactive skill bodies into a headless agent is an anti-pattern, and the agent calls the per-skill check scripts directly) + a system prompt encoding: mandate (run to completion, autonomously, headless by default, no prompts — may be schedule-triggered with no human); authority (vault CLAUDE.md = schema authority, read first); the **safe + low-risk** boundary (never judgment-tier); the **3 semantic dimensions** (`stale-claims`, `concept-graduation`, `suggested-investigations`) defined inline as the headless authority (kept in sync with `wiki-audit`'s body — F5); pipeline (resolve vault via `${CLAUDE_PLUGIN_ROOT}/scripts/resolve-vault.sh` → run each `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/scripts/<cat>_checks.py --report` → merge → semantic reasoning pass → each script's `--fix-safe`+`--fix-lowrisk` → write report → `log.md` `lint` → return summary); no-fabrication discipline verbatim from the schema. **Composition:** calls the per-skill scripts directly (which import the shared `scripts/obsidian.py`); does not invoke the skills via `Skill`.
**Verification:** dispatch via the `Agent` tool against Hive-Mind — applies only safe + low-risk, report lists every judgment item, `log.md` appended, summary returned, **zero prompts** (headless-safe); idempotent on re-dispatch; `model: opus` alias resolves.

### U8. Report format + `meta/maintenance-reports/`
**Goal:** Stable dual-audience report. Header (vault, timestamp, actor, counts, summary) + findings grouped by category, each `- [ ] <id> · <tier> · <page> — <detail> → <action>` with `status:`. Created on demand; reports accumulate (dated).
**Dependencies:** U2 (finding shape).
**Verification:** generate → parse back → all `id`s/statuses recoverable by `wiki-triage`.

### U9. READMEs + plugin CLAUDE.md
**Goal:** User-facing docs for the four skills; an **order-of-operations** section in the top-level `README.md` (two lanes: manual `wiki-lint → wiki-audit → wiki-gaps`; automated `wiki-steward → wiki-triage`) plus the new rows in the skills table; and the plugin `CLAUDE.md` documenting the `agents/` mechanism + the `wiki-steward` agent, the `${CLAUDE_PLUGIN_ROOT}` convention for plugin-root scripts (vs. `{skill_base_dir}` for in-skill assets), and the skill-handoff / progressive-disclosure convention.
**Dependencies:** U3–U7, U10.
**Files:** `skills/wiki-lint/README.md`, `skills/wiki-audit/README.md`, `skills/wiki-gaps/README.md`, `skills/wiki-triage/README.md` (new); `README.md`, `CLAUDE.md` (modified).
**Patterns:** `wiki-setup`/`wiki-ingest` READMEs; existing `README.md` skills table.

### U10. Extend + slim the vault schema (`CLAUDE-template.md`) + reconcile README + `schema_version` bump
**Goal:** Make `CLAUDE-template.md` the correct, sufficient contract for the suite in one coherent edit (one bump): **extend** it with the data-contract elements the checks rely on, **slim** the procedural Lint Workflow out, and **reconcile** the README's runtime-independence claim.
**Dependencies:** none (foundational schema change; U2's checks validate against it). The slim's `## Maintenance` pointer names the suite skills by reference — writing it does not require them to exist yet, but the end-to-end pointer check in Verification runs once U3–U7 land.
**Files:** `skills/wiki-setup/assets/CLAUDE-template.md` (modified); `README.md` (modified — the runtime-independence claim).
**Approach (F1 — extend):** add the data-contract elements the checks need, landing them in sections that survive the slim: the `last_checked` frontmatter field (in the frontmatter-field definitions), the **bare-`?`** validity rule (a bare `?` as an entire value is an unfilled placeholder; `?` *within* a value like `title: "What is X?"` is valid — this replaces the current "any `?` in a field value" wording at the Frontmatter-drift line), and the `(forward link)` annotation convention (near the existing "link forward" concept text).
**Approach (F2 — full slim, owner-directed):** replace the entire `## Lint Workflow` section (the 10-dimension how-to, *including* the judgment-dimension descriptions) with a brief `## Maintenance` pointer — maintenance is performed by the mneme suite (`mneme:wiki-lint` / `wiki-audit` / `wiki-gaps` interactively, or `mneme:wiki-steward` for an autonomous pass); keep the trigger phrases ("lint" / "health check the wiki") routed to the suite. **Keep** Hygiene Rules unchanged.
**Approach (F2 — README):** narrow the README's "No external MCP servers, additional plugins, or internet access required at runtime" claim so it no longer promises the *maintenance* lifecycle works without the plugin. Bump `schema_version` `0.2.0 → 0.3.0` (one minor covers extend + slim).
**Accepted trade-offs (owner-directed, reviewed):** (1) full slim removes the in-vault *definitions* of the judgment dimensions (stale claims, concept-graduation, orphans, suggested investigations); the suite becomes their sole home, so a plugin-less conversational session has no maintenance guidance — accepted for non-duplication. (2) The README claim is narrowed rather than the vault kept self-contained.
**Verification:** bootstrap a fresh vault via `wiki-setup`; its `CLAUDE.md` defines `last_checked`, carries the bare-`?` validity rule and the `(forward link)` convention, carries the slim `## Maintenance` pointer (no 10-step how-to), Hygiene Rules intact, `schema_version` = `0.3.0`; the README no longer claims plugin-free maintenance; the per-skill check scripts' rules (`last-checked-missing`, bare-`?`, `stale-forward-annotation`) match the schema definitions.
**Test expectation:** none — documentation/schema content change; covered by the wiki-setup bootstrap verification above.

---

## Deferred Implementation Notes
- **Resolved — skill → plugin-root reference.** `${CLAUDE_PLUGIN_ROOT}` (env-var substitution). Not `{plugin_base_dir}` (nonexistent), not relative traversal (unreliable after install). See U1.
- **Resolved — agent ↔ skill composition.** The agent calls the per-skill check scripts directly (each imports `scripts/obsidian.py`); **no `skills:` preload** (preloading interactive skill bodies into a headless agent is an anti-pattern), and it never invokes skills via the `Skill` tool (`AskUserQuestion` is unavailable to subagents; the agent must be headless-safe). See U7.
- **Resolved — agent model.** `model: opus` alias, not a pinned id, for forward-compatibility. See U7.
- **`--min-refs` for `missing-page`** — schema says "3+"; start at 3, expose the flag.
- **Report retention** — accumulate for now; `--prune` out of scope.
- **Schema documentation of `meta/maintenance-reports/`** — if durable, fold into the U10 edit (the `schema_version` bump is already happening there).

---

## System-Wide Impact
- **New:** `agents/wiki-steward.md` (+ `agents/` dir), `scripts/obsidian.py` (shared core), `scripts/resolve-vault.sh` (promoted), `skills/wiki-lint` (+ `scripts/lint_checks.py`), `skills/wiki-audit` (+ `scripts/audit_checks.py`), `skills/wiki-gaps` (+ `scripts/gaps_checks.py`), `skills/wiki-triage`.
- **Modified:** `skills/wiki-ingest/SKILL.md` (resolver path → `${CLAUDE_PLUGIN_ROOT}`); plugin `CLAUDE.md` (agents/ mechanism, `${CLAUDE_PLUGIN_ROOT}` convention, handoff convention); `README.md` (order of operations + skills table; runtime-independence claim narrowed, U10); `skills/wiki-setup/assets/CLAUDE-template.md` (extend data contract + slim Lint Workflow → suite pointer, U10).
- **Runtime, in vault:** `meta/maintenance-reports/` (on demand); `log.md` + `index.md` updated by runs.
- **Version:** minor bump (new agent + four skills) — `0.3.0` → **`0.4.0`** in `.claude-plugin/plugin.json` + a `v0.4.0` GitHub Release. **Schema:** `schema_version` bumps one minor (U10 edits `CLAUDE-template.md`) — `0.2.0 → 0.3.0`.

---

## Dependencies / Prerequisites
- A vault bootstrapped with `mneme:wiki-setup` (`~/.config/mneme/settings.json`; vault `CLAUDE.md`, `schema_version ≥ 0.2.0` — current canonical value).
- `python3` in PATH.
- The `wiki-steward` agent runs headless by default; triggering it (on a schedule or otherwise) is external to the plugin.
