---
name: wiki-setup
description: >
  Bootstraps an empty Obsidian vault into a ready-to-use LLM Wiki following the
  canonical mneme schema. Use when the user says "set up a new wiki",
  "bootstrap my vault", "initialize my LLM wiki", or explicitly invokes
  mneme:wiki-setup. Prompts for vault location (current directory or
  an absolute path the user provides), then collects vault name, owner name,
  and vault description before scaffolding. The target directory must already
  exist and be essentially empty — silently removes Obsidian's default
  Welcome.md, ignores .DS_Store, refuses if anything else is present. Creates
  the full folder
  tree (raw/ with 11 bins, wiki/ with 9 page-type folders, meta/), writes a
  personalized CLAUDE.md (owner's display name substituted throughout), skeleton
  bookkeeping files (index.md, log.md, meta/tags.md), nine canonical page-type
  templates in meta/templates/, and walks the owner through a live first-ingest
  demo at their chosen depth: minimal (source reference page only), standard
  (source page + concept page with cross-links), or full (source + concept +
  topic hub + guided tour). After the skill exits, the owner can immediately
  ingest a second source using the Ingest Workflow in CLAUDE.md.
---

# wiki-setup

Bootstrap an empty Obsidian vault into a ready-to-use LLM Wiki.

## Assets

This skill ships bundled assets in the `assets/` directory next to this SKILL.md.
The base directory of this skill is provided in your context at invocation time.
Before executing any phase, note the absolute paths to these assets:

- `{skill_base_dir}/assets/CLAUDE-template.md` — parameterized CLAUDE.md schema (contains `{{OWNER_NAME}}` and `{{TODAY}}` tokens)
- `{skill_base_dir}/assets/index-template.md` — skeleton index.md (contains `{{TODAY}}` token)
- `{skill_base_dir}/assets/log-template.md` — skeleton log.md (contains `{{TODAY}}` token)
- `{skill_base_dir}/assets/demo-source.md` — bundled LLM Wiki overview article
- `{skill_base_dir}/assets/templates/` — directory containing the nine page-type templates

Resolve `{skill_base_dir}` from the "Base directory for this skill" value in your context. Use absolute paths when constructing subagent prompts.

---

## Step 1: Vault Location

First, resolve the current working directory absolute path.

Use **AskUserQuestion** with:
- question: `"Where should the wiki be set up?"`
- header: `"Vault location"`
- options:
  - label: `"Current directory (Recommended)"`, description: the resolved absolute path of cwd
  - label: `"Different location"`, description: `"I'll type the full path to my Obsidian vault"`

If they select **Current directory**, set VAULT_PATH to the cwd absolute path.

If they select **Different location** (or **Other**), use a second **AskUserQuestion** with:
- question: `"Enter the full absolute path to your Obsidian vault:"`
- header: `"Vault path"`
- options (provide 2 plausible examples based on common macOS locations, e.g. `~/Documents/vault` and `~/Desktop/vault`; the user will type their actual path via Other)

Set VAULT_PATH to exactly what they enter.

---

## Step 2: Vault Guard

Run the bundled guard script:

```bash
bash "{skill_base_dir}/scripts/vault-guard.sh" "{VAULT_PATH}"
```

The script checks for path existence and unexpected content, then removes `Welcome.md` only if the vault is otherwise empty. It prints one of three tokens to stdout:

| Output | Exit code | Meaning |
|--------|-----------|---------|
| `READY` | 0 | Vault is empty and ready; proceed to Step 3 |
| `NOT_FOUND` | 1 | Path does not exist |
| `NOT_EMPTY` | 2 | Vault contains unexpected files or folders |

**If `NOT_FOUND`**, output this message and exit:

> **The vault directory does not exist.**
>
> The path `{VAULT_PATH}` could not be found. Create the Obsidian vault first (File → New Vault in the Obsidian app), then run `mneme:wiki-setup` again.

**If `NOT_EMPTY`**, output this message and exit:

> **This skill requires an empty vault.**
>
> The directory `{VAULT_PATH}` contains existing files or folders. The wiki-setup skill writes a canonical schema from scratch; running it in a non-empty directory risks conflicting with your existing content.
>
> **Next step:** Create a new, empty Obsidian vault, then run `mneme:wiki-setup` again.

Write no files. Take no further action. Exit the skill.

**If `READY`**, continue to Step 3.

---

## Step 3: Vault Configuration

**Interaction rule for this entire step:** Ask one question at a time using **AskUserQuestion**. Do not ask multiple questions in a single message. Do not present questions as a numbered or bulleted list. Wait for the reply before presenting the next question.

**Question 1 — Vault name:**

Use **AskUserQuestion** with:
- question: `"What would you like to name this vault? No spaces — use hyphens or underscores."`
- header: `"Vault name"`
- options: 3 common examples, e.g. `personal (Recommended)`, `work`, `research` — mark the first as recommended; the user types their actual name via Other

If the response contains a space, immediately use **AskUserQuestion** again with the same question, noting: "Vault names cannot contain spaces — try `{spaces-replaced-with-hyphens}` instead." Re-ask until you receive a valid name. Store as VAULT_NAME.

**Question 2 — Owner name:**

Use **AskUserQuestion** with:
- question: `"What name should the wiki use for you? This will appear throughout CLAUDE.md wherever the wiki refers to its owner — for example, \"Jordan curates sources\" or \"Jordan reads the wiki.\""`
- header: `"Owner name"`
- options: 3 plausible example names such as a first name, a full name, and a nickname (e.g. `Jordan (Recommended)`, `Jordan Smith`, `jsmith`) — mark the first as recommended; the owner types their actual name via Other

Store the response as OWNER_NAME.

**Question 3 — Vault description:**

Before presenting this question, derive a natural recommended description from VAULT_NAME and OWNER_NAME. Use both to infer intent — a vault named `work` for `Bob` suggests "Bob's work research and reference wiki"; one named `personal` for `Alice` suggests "Alice's personal second brain". Use your judgment; do not mechanically fill a template.

Use **AskUserQuestion** with:
- question: `"Give this vault a short description:"`
- header: `"Description"`
- options:
  - label: your derived recommendation followed by `(Recommended)` — e.g. `"Jordan's personal research wiki (Recommended)"`
  - label: `"Type my own"`, description: `"I'll enter a custom description"`

If they select the recommendation directly, use it as VAULT_DESCRIPTION. If they select "Type my own" or Other, use what they type as VAULT_DESCRIPTION.

**Question 4 — Tutorial depth:**

Use **AskUserQuestion** with:
- question: `"How much of a walkthrough would you like during setup?"`
- header: `"Tutorial depth"`
- options:
  - label: `"Standard (Recommended)"`, description: `"Guided tour of the vault structure, CLAUDE.md, and a narrated demo ingest"`
  - label: `"Minimal"`, description: `"Brief orientation — what was created and how to run your first ingest"`
  - label: `"Full"`, description: `"Deep dive into the schema, every page type, the ingest workflow, and fully narrated demo"`

Store as DEMO_DEPTH.

---

## Step 4: Bootstrap Preamble

Tell the owner:

> Your wiki bootstrap is starting now. I'll narrate all three phases, then all the scaffold work runs in parallel in the background. The whole process takes about 60 seconds.

---

## Step 5: Scaffold Narration

Narrate all three phases in sequence — do not dispatch any agents yet.

> **Phase 1 — Source Storage (`raw/`)**
>
> The `raw/` folder is where all your source documents live: articles, papers, notes, recordings, transcripts, and more. It is strictly read-only — you and I read from here, but nothing in `raw/` is ever modified once it's placed. The eleven subfolders map to every content type, and files are date-prefixed so they sort chronologically. I'm placing the demo source article here now, ready for your first ingest.

> **Phase 2 — Synthesis Pages (`wiki/`)**
>
> The `wiki/` folder is where I work. Every page here is written and maintained by me: entities, concepts, topic hubs, reference extracts, solution narratives, analyses, projects, personal tracking, and open questions. You read it; I write it. The nine subfolders map directly to the nine page types defined in the schema.

> **Phase 3 — Schema and Bookkeeping**
>
> The final layer is the wiki's operating system. `CLAUDE.md` is the schema — every agent session starts by reading it fully before doing anything else. `index.md` is your content catalog, updated on every ingest. `log.md` is the append-only activity record, `meta/tags.md` prevents tag sprawl, and `meta/templates/` holds the canonical page shapes for all nine page types. I'm setting all of these up now, with your name substituted throughout CLAUDE.md.

---

## Step 6: Scaffold Dispatch

Dispatch all **seven agents simultaneously** (in parallel) using **model: haiku**. These agents perform deterministic file-creation tasks that do not require a larger model. Substitute SKILL_ASSETS_DIR, VAULT_PATH, OWNER_NAME, and TODAY (YYYY-MM-DD) in each prompt.

**Agent 1 — raw/ layer**
```
Your task: set up the raw/ layer of a new LLM Wiki vault.

The vault is located at: VAULT_PATH

1. Create these 11 folders inside VAULT_PATH (use mkdir -p):
   VAULT_PATH/raw/articles/
   VAULT_PATH/raw/posts/
   VAULT_PATH/raw/papers/
   VAULT_PATH/raw/reports/
   VAULT_PATH/raw/guides/
   VAULT_PATH/raw/docs/
   VAULT_PATH/raw/books/
   VAULT_PATH/raw/recordings/
   VAULT_PATH/raw/transcripts/
   VAULT_PATH/raw/notes/
   VAULT_PATH/raw/assets/

2. Read the file at: SKILL_ASSETS_DIR/assets/demo-source.md
   Write its contents verbatim to: VAULT_PATH/raw/articles/TODAY-llm-wiki-pattern-overview.md

Do not create any wiki/, meta/, or other directories or files. That is your complete task.
```

**Agent 2 — wiki/ layer**
```
Your task: set up the wiki/ layer of a new LLM Wiki vault.

The vault is located at: VAULT_PATH

Create these 9 folders inside VAULT_PATH (use mkdir -p):
   VAULT_PATH/wiki/entities/
   VAULT_PATH/wiki/concepts/
   VAULT_PATH/wiki/topics/
   VAULT_PATH/wiki/references/
   VAULT_PATH/wiki/solutions/
   VAULT_PATH/wiki/analyses/
   VAULT_PATH/wiki/projects/
   VAULT_PATH/wiki/personal/
   VAULT_PATH/wiki/questions/

Do not create any raw/, meta/, or other directories or files. That is your complete task.
```

**Agent 3 — CLAUDE.md**
```
Your task: write CLAUDE.md for a new LLM Wiki vault.

The vault is located at: VAULT_PATH

1. Read the file at: SKILL_ASSETS_DIR/assets/CLAUDE-template.md
2. Replace every occurrence of the string {{OWNER_NAME}} with: OWNER_NAME_VALUE
3. Replace every occurrence of the string {{TODAY}} with: TODAY_VALUE
4. Write the result to: VAULT_PATH/CLAUDE.md

Do not create any other files or folders. That is your complete task.
```

**Agent 4 — Page Templates**
```
Your task: install the nine page-type templates for a new LLM Wiki vault.

The vault is located at: VAULT_PATH

1. Create the directory VAULT_PATH/meta/templates/
2. Read and copy each of the following files from SKILL_ASSETS_DIR/assets/templates/
   to VAULT_PATH/meta/templates/, preserving filenames exactly:
   entity.md, concept.md, topic.md, reference.md, solution.md,
   analysis.md, project.md, personal.md, question.md

Do not create any other files or folders. That is your complete task.
```

**Agent 5 — index.md**
```
Your task: write index.md for a new LLM Wiki vault.

The vault is located at: VAULT_PATH

1. Read the file at: SKILL_ASSETS_DIR/assets/index-template.md
2. Replace every occurrence of the string {{TODAY}} with: TODAY_VALUE
3. Write the result to: VAULT_PATH/index.md

Do not create any other files or folders. That is your complete task.
```

**Agent 6 — log.md**
```
Your task: write log.md for a new LLM Wiki vault.

The vault is located at: VAULT_PATH

1. Read the file at: SKILL_ASSETS_DIR/assets/log-template.md
2. Replace every occurrence of the string {{TODAY}} with: TODAY_VALUE
3. Write the result to: VAULT_PATH/log.md

Do not create any other files or folders. That is your complete task.
```

**Agent 7 — meta/tags.md**
```
Your task: write the skeleton meta/tags.md for a new LLM Wiki vault.

The vault is located at: VAULT_PATH

1. Create the directory VAULT_PATH/meta/ if it does not exist
2. Write the following content verbatim to VAULT_PATH/meta/tags.md:

# Tag Registry

Every tag in use must be registered here with a one-line definition.
Before introducing a new tag, check this file. If a near-synonym exists, use it instead.

| Tag | Definition |
|-----|------------|

*(No tags yet — add a row here each time you introduce a new tag)*

That is your complete task.
```

Wait for **all seven agents** to confirm completion before proceeding.

---

## Step 7: Demo Ingest

**Ingest interaction rule — applies for the entire duration of this step:**
Any question you would ask the owner must be presented using **AskUserQuestion** — never plain text. Always include a recommended option (mark it first in the list and note it as "Recommended"). The owner should be able to accept your recommendation with a single click; they should only need to type when no reasonable recommendation exists.

---

**Read CLAUDE.md first.** The scaffold is complete and CLAUDE.md is now authoritative for all operations in this vault. Before doing anything else, read it fully:

```
VAULT_PATH/CLAUDE.md
```

Use its Ingest Workflow to ingest the demo source that was placed during the scaffold:

```
VAULT_PATH/raw/articles/TODAY-llm-wiki-pattern-overview.md
```

Follow CLAUDE.md's instructions precisely — page structure, frontmatter fields, section headings, cross-linking conventions, and index/log update format are all defined there. Do not invent structure that contradicts the schema.

The depth of explanation and narration you provide to the owner during this process is controlled by DEMO_DEPTH:

**Minimal** — Perform the ingest following CLAUDE.md with minimal narration. After it completes, give the owner a brief orientation: what was created, where to find it, and a one-paragraph explanation of how to run their next ingest. Keep it concise.

**Standard** — Walk the owner through the ingest step-by-step as you execute it, explaining the key decisions at each stage (why this page type, what goes in each section, how cross-links are chosen). After the ingest, tour the main sections of CLAUDE.md the owner will rely on for ongoing use.

**Full** — Before ingesting, give a thorough explanation of the vault structure: the role of each folder, every page type and when to use it, how the ingest workflow operates end-to-end, and how CLAUDE.md governs future sessions. Then perform the ingest with detailed narration of every decision. After completing, walk the owner through the finished pages and invite questions.

---

## Step 8: Settings Registration

Register the vault in `~/.config/mneme/settings.json`.

**Read the existing settings file** if it exists:

```bash
cat ~/.config/mneme/settings.json 2>/dev/null
```

**If the file does not exist** (or the directory doesn't exist), create it:

```bash
mkdir -p ~/.config/mneme
```

Then write `~/.config/mneme/settings.json` with:

```json
{
  "vaults": {
    "VAULT_NAME": {
      "vault_path": "VAULT_PATH",
      "description": "VAULT_DESCRIPTION"
    }
  },
  "default_vault": "VAULT_NAME"
}
```

**If the file already exists**, parse it and add the new vault entry under `vaults`. Then:

- If this is the only vault, set it as `default_vault`.
- If other vaults already exist, use **AskUserQuestion** with:
  - question: `"Would you like to make VAULT_NAME your default vault? The current default is {current default_vault value}. The default vault is used by other mneme skills when no vault is specified."`
  - header: `"Default vault"`
  - options:
    - label: `"Yes, make it the default"`, description: `"Switch the default to VAULT_NAME"`
    - label: `"No, keep current default"`, description: `"Leave {current default_vault value} as the default"`

  Update `default_vault` if they select yes; leave it unchanged if they select no.

Write the updated JSON back to `~/.config/mneme/settings.json`.

---

## Step 9: Completion Report

After the settings file is written, report:

> **Bootstrap complete.** Here's what was created:
>
> **Vault:** `VAULT_NAME` at `VAULT_PATH`
> **Structure:** `raw/` (11 bins) · `wiki/` (9 folders) · `meta/`
> **Schema:** `CLAUDE.md` (personalized for OWNER_NAME) · `index.md` · `log.md` · `meta/tags.md` · 9 page templates in `meta/templates/`
> **Demo content:** [list the wiki pages created at the chosen depth]
> **Settings:** Registered in `~/.config/mneme/settings.json`
>
> **What's next:** Open `VAULT_PATH` in Obsidian and read `CLAUDE.md` fully — it is your operating guide for everything below.
>
> **Command reference:**
> - **Ingest a new source** — *"Ingest this: [URL or paste text]"*
> - **Process a file you dropped into `raw/`** — *"Ingest raw/articles/YYYY-MM-DD-filename.md"*
> - **Reconcile after adding several files at once** — *"Reconcile raw/ — ingest anything new"*
> - **Check the vault for issues** — *"Run a healthcheck on the wiki"*
> - **Search what you already know** — *"What do I know about [topic]?"*
> - **Capture an open question before you lose it** — *"Add this question to the wiki: [your question]"*
> - **Start tracking a new project** — *"Start a project: [name and what it's for]"*
> - **Review active projects** — *"What projects am I currently tracking?"*
