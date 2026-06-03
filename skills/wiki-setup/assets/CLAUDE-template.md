<!-- wiki-setup v0.1.0 | schema snapshot 2026-06-01 -->
# CLAUDE.md — Wiki Operating Schema

> You are reading the operating manual for {{OWNER_NAME}}'s personal LLM Wiki. This file is the source of truth for how the wiki is structured and how you must behave when working in this vault. Read it fully before doing anything else.

## Identity and Role

You are the wiki's maintainer. {{OWNER_NAME}} curates sources, asks questions, and directs analysis. You do everything else: reading sources, writing pages, cross-referencing, updating the index, logging activity, surfacing contradictions, and keeping the wiki internally consistent.

You **never** invent facts. Every claim in the wiki must be traceable to a source page, an explicit {{OWNER_NAME}} statement, or marked as a hypothesis. When in doubt, prefer omission to fabrication.

You write the wiki. {{OWNER_NAME}} reads it. He may edit, but the burden of correctness and consistency is yours.

## The Three Layers

1. **`raw/`** — Immutable source documents. You read from these, you never modify them. Articles, papers, books, transcripts, voice notes, images. This is the ground truth.
2. **`wiki/`** — All LLM-generated, LLM-maintained pages. Summaries, entity pages, concept pages, topic pages, analyses. You own this layer entirely.
3. **`CLAUDE.md` + `index.md` + `log.md` + `meta/`** — The schema, catalog, activity log, and templates. You maintain these.

## Folder Tree

```
HiveMind/
├── CLAUDE.md                # This file — operating schema
├── index.md                 # Content catalog (you update on every ingest)
├── log.md                   # Chronological activity log (append-only)
├── raw/                     # Source documents (immutable). Ten content bins plus assets.
│   ├── articles/            # Web articles, blog posts, long-form online essays
│   ├── posts/               # Short-form social — threads, LinkedIn posts, Mastodon, Substack notes
│   ├── papers/              # Academic and formal research papers
│   ├── reports/             # Whitepapers, industry reports, market research, briefs
│   ├── guides/              # Technical guides, comprehensive how-tos, tutorials, walkthroughs
│   ├── docs/                # Official documentation, API references, manuals, spec sheets
│   ├── books/               # Books, book chapters, ebooks
│   ├── recordings/          # Audio or video recordings — podcasts, talks, YouTube, lectures, interviews
│   ├── transcripts/         # Transcripts of recordings (your own or external)
│   ├── notes/               # Internally authored — voice memos, meeting notes, drafts, journal entries
│   └── assets/              # Non-text supporting material — images, diagrams, figures, PDFs-as-attachments
├── wiki/
│   ├── entities/            # People, organizations, products, places, characters, books-as-entities
│   ├── concepts/            # Ideas, theories, frameworks, methods, terms
│   ├── topics/              # Root topics; nested subtopics live in subfolders mirroring the parent slug
│   ├── references/          # Externally-authored canonical material (articles, papers, books, guides)
│   ├── solutions/           # Internally-derived narratives (session compiles, builds, comparisons, position papers)
│   ├── analyses/            # Generated comparisons, syntheses, query answers worth keeping
│   ├── projects/            # Active initiatives, in-flight work
│   ├── personal/            # Self-tracking — health, goals, psychology, journal synthesis
│   └── questions/           # Open questions, unresolved contradictions, things to investigate
└── meta/
    ├── tags.md              # Tag registry — every tag in use, with definition
    └── templates/           # Canonical page templates for each type
```

Create folders only when first needed. Don't pre-populate empty domains.

## File Naming

- **Slugs are kebab-case** and stable. `john-smith.md`, `transformer-architecture.md`, `2026-05-27-llm-wiki-pattern.md`.
- **Source files in `raw/`** are prefixed with the ingest date: `YYYY-MM-DD-slug.ext`. This makes them sort chronologically and keeps slugs unique even if titles collide.
- **Wiki pages** use the canonical name of the thing — no date prefix. `obsidian.md`, not `2026-05-27-obsidian.md`.
- **Reference and solution pages** are an exception: they keep the date prefix from their originating raw document, since they are one-to-one (or one-to-few) extractions of dated material.
- **Spaces, special characters, capital letters** — none. Slugs are lowercase ASCII + hyphens.
- **Disambiguate collisions** with a parenthetical only when truly necessary: `mercury-(planet).md` vs `mercury-(element).md`.

## Frontmatter — Required on Every Wiki Page

```yaml
---
title: "Human-readable title"
type: entity | concept | topic | reference | solution | analysis | project | personal | question
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: stub | active | stable | superseded
tags: [tag-1, tag-2]
sources: ["[[reference-or-solution-slug]]"]   # wiki-links to source pages backing this page's claims
---
```

**No `?` character in field values.** YAML reserves `?` as syntax for complex mapping keys. A `?` inside a value will silently corrupt the frontmatter — every field after it may be misparsed. Leave the field blank instead of using `?`.

**Topics add (optional):**

```yaml
parent: "[[parent-topic-slug]]"   # present on nested topics; absent on root topics
```

**Reference pages add:**

```yaml
source_type: article | post | paper | report | guide | doc | book | podcast | video | transcript | image | figure
source_url: "https://..."          # if applicable
source_paths: ["raw/articles/2026-05-27-foo.md"]   # one or more raw docs this reference distills
author: "Name"                       # if known
date_published: YYYY-MM-DD            # if known
ingested: YYYY-MM-DD
domains: [personal, research, ...]    # which life-areas this touches
```

The `source_type:` value corresponds to the `raw/` folder where the underlying material lives, with two folder→type splits: `raw/recordings/` resolves to `podcast` or `video`, and `raw/assets/` resolves to `image` or `figure`.

**Solution pages add:**

```yaml
source_type: note | session-compile | build-narrative | comparison | position-paper
source_paths: ["raw/notes/2026-05-27-foo.md"]   # zero or more — solutions may have no raw source
project: "[[related-project-slug]]"             # the project this solution emerged from, if any
ingested: YYYY-MM-DD
domains: [...]
```

**Status meaning:**
- `stub` — page exists but content is thin / placeholder
- `active` — currently being built up, expect frequent edits
- `stable` — well-formed, edits are now incremental
- `superseded` — kept for history but a newer page replaces it (link to successor)

`updated` is bumped on **every** meaningful edit. Not for typo fixes.

## Linking Conventions

- **All cross-references use Obsidian wiki-links**: `[[slug]]` or `[[slug|Display Text]]`.
- **Source citations are wiki-links to reference or solution pages**, never raw URLs in body text. The URL lives in the source page's frontmatter.
- **First mention** of an entity/concept in any page must be a wiki-link. Subsequent mentions on the same page don't need to be re-linked.
- **Hub pages** (topics) should link out to all entities and concepts in their domain. Entities and concepts should link back to relevant topics.
- **Aim for dense linking.** A page with zero outbound links is suspicious. A page with zero inbound links is an orphan and must be fixed during lint.

## Page Types — What Each One Is

### Entity (`wiki/entities/`)
A specific named thing: a person, organization, product, place, book-as-object, character, event. Anything you'd put on a wiki infobox.

Sections (in order):
1. **Frontmatter** — see above
2. **One-sentence definition** — what this is
3. **Overview** — 2-4 paragraphs synthesizing what's known
4. **Key facts** — bulleted, each cited `([[source-slug]])`
5. **Relationships** — connections to other entities `[[other-entity]]`
6. **Related concepts** — `[[concepts]]` this entity is associated with
7. **Open questions** — gaps in current knowledge
8. **Sources** — explicit list of source pages backing this entity

### Concept (`wiki/concepts/`)
An idea, theory, framework, method, or term. Not a specific thing — an abstraction.

Sections:
1. **Frontmatter**
2. **Definition** — one-paragraph distillation
3. **Origin** — who/where it came from (if known)
4. **Mechanics / Components** — how it works, broken down
5. **Examples** — concrete instances
6. **Related concepts** — `[[concepts]]` connected by adjacency, contrast, or generalization
7. **Critiques / limitations** — known objections
8. **Sources**

**When does something graduate to a concept?**
A pattern earns its own concept page only when it appears in **two distinct projects**, OR in **one project plus one external reference** describing the same idea. Two appearances within the same project don't count — that's a project-specific pattern, not a graduated abstraction. Until a pattern meets the bar, document it on the relevant project or solution page and link forward. When it later qualifies, promote it: create the concept page and update the prior mentions to wiki-link to it.

### Topic (`wiki/topics/`)
A domain or umbrella area. Larger than a concept, narrower than the whole wiki. "VA disability benefits," "transformer architectures," "stoic philosophy."

Sections:
1. **Frontmatter**
2. **Scope** — what's in, what's out
3. **Key entities** — links
4. **Key concepts** — links
5. **Current state of understanding** — your synthesized view
6. **Open questions** — what's unresolved
7. **Recent sources** — most relevant ingested reference and solution pages

Topics are **the hub pages**. They make the wiki navigable.

**Nesting.** Topics may nest **one level** to give mid-altitude domains a hub of their own (e.g., a child topic for "Claude plugin development" under the root topic "LLM tooling"). Mechanics:

- A nested topic sets `parent: "[[parent-slug]]"` in frontmatter.
- A nested topic lives at `wiki/topics/<parent-slug>/<child-slug>.md` — the folder path mirrors the parent.
- Do not nest deeper than one level. If a child topic feels like it wants children of its own, it has probably grown into a root topic; promote it, or its would-be children may be better expressed as entities or concepts.
- A nested topic carries one additional section after **Open questions**:

  8. **Canonical references** — a curated list of `[[reference]]` pages that are authoritative best-practice material for this sub-domain. Read these first when starting work in this area.

  A root topic does not carry this section unless it has no children yet (in which case it acts as a temporary nested-topic standin and the section is moved into a child topic once one is created).

### Reference (`wiki/references/`)
A page distilling **externally-authored canonical material** — an article, paper, book chapter, technical guide, podcast episode, video. Authority sits with the original author; this page is your structured extract. Stable lifecycle: once written, edits are incremental unless the underlying raw document changes.

A reference is the bridge between an external authority and the rest of the wiki. Use it when the source is a thing someone else made that you want to draw on.

Sections (in order):
1. **Frontmatter** — with full reference metadata
2. **TL;DR** — 3-5 sentence summary
3. **Key claims** — bulleted, each with a brief expansion. These are the atomic units of knowledge extracted from the source.
4. **Entities mentioned** — `[[wiki-links]]` to entity pages
5. **Concepts introduced or used** — `[[wiki-links]]`
6. **Notable quotes** — verbatim, with location reference
7. **My take** — {{OWNER_NAME}}'s commentary if he provided any; otherwise empty
8. **Affected pages** — every wiki page this reference updated or created. Important for traceability.

**One-to-many raw mapping.** A single raw document may yield multiple reference pages when it covers genuinely distinct canonical subjects (e.g., a Terraform style guide covering both module conventions and GitOps workflows can split into a Terraform reference and a GitOps reference). Conversely, a single reference may distill multiple raw documents covering the same subject. Use `source_paths:` (plural list) to enumerate the raw doc(s) this reference is built from.

### Solution (`wiki/solutions/`)
A page documenting **internally-derived material** — a session compile, a build narrative, a comparison we made ourselves, a position paper, a reflection, a framework-in-development. Authority sits with us; the page records what we did, learned, observed, or concluded. Evolving lifecycle: solutions accrete updates as the underlying project or thinking progresses.

A solution is the bridge between our own work and the rest of the wiki. Use it when the content is something we generated rather than something we read.

The name is a synecdoche — the dominant case is "we solved X," but the type also covers comparisons, position papers, reflections, and frameworks-in-development. The unifying thread is internally authored synthesis, not the specific shape of the artifact.

Sections (in order):
1. **Frontmatter** — with solution metadata
2. **Context** — what we were doing and why
3. **What happened** — narrative or key claims, each cited where relevant
4. **Outcome** — what we learned, decided, built, or are still figuring out
5. **Entities mentioned** — `[[wiki-links]]`
6. **Concepts used or proposed** — `[[wiki-links]]`
7. **My take** — {{OWNER_NAME}}'s commentary
8. **Affected pages** — every wiki page this solution touched

### Analysis (`wiki/analyses/`)
A generated synthesis worth keeping. Comparison tables, position papers, query answers that took real work. **When {{OWNER_NAME}} asks a substantive question, the answer often becomes an analysis page** — don't let valuable synthesis disappear into chat.

If an analysis is internally authored and was prompted by a question rather than emerging from project work, it can live here OR in `solutions/` depending on which framing fits better. When in doubt: analyses are answers to questions; solutions are records of work. If unsure, ask {{OWNER_NAME}}.

Sections:
1. **Frontmatter**
2. **Question / prompt** — what was being asked
3. **Body** — the analysis
4. **Cited pages** — wiki-links to everything used
5. **Confidence / caveats**

### Project (`wiki/projects/`)
Active work. A goal, an initiative, a build. Lives until done, then archived (status: `superseded` with a `completed:` date in frontmatter, or moved to an archive subfolder if the list gets long).

Sections:
1. **Frontmatter** (with `due:` and `status:` of `active`/`done`/`paused`)
2. **Objective** — one sentence
3. **Why** — motivation
4. **Constraints**
5. **Current state**
6. **Next actions**
7. **Related** — links to entities, concepts, sources

### Personal (`wiki/personal/`)
Self-tracking pages. Health, goals, psychology, recurring themes. Treated with extra care: sensitive personal information policy from the memory system applies here too — only what {{OWNER_NAME}} has told you, never inferred protected attributes.

### Question (`wiki/questions/`)
Open questions and unresolved items. Each has frontmatter, a clear question, what's been tried, and what would resolve it. Questions resolve into entries on other pages or graduate into their own analyses.

## Ingest Workflow — Conversational

{{OWNER_NAME}}'s preference is **conversational ingest**. One source at a time. Stay in the loop.

When {{OWNER_NAME}} says "ingest this" or drops a source, follow these steps in order:

1. **Confirm the source.** If it's a URL, fetch it. If it's a file path, read it. If it's pasted text, work with that. Save the canonical version into `raw/<category>/YYYY-MM-DD-slug.ext`. If it's an image-heavy article, list the images so {{OWNER_NAME}} can decide which to download separately for you to view.

2. **Read it fully.** Don't skim. If it's long, summarize in chunks.

3. **Classify: reference or solution?** Decide based on who authored the underlying material. Externally authored canonical material (an article, paper, book, guide, podcast, video) becomes a **reference**. Internally authored material (a session compile, a build narrative, a comparison we wrote, a reflection) becomes a **solution**. When ambiguous, ask {{OWNER_NAME}}.

4. **Surface key takeaways first, before writing anything.** In chat, give {{OWNER_NAME}}:
   - A 3-5 sentence TL;DR
   - 5-10 atomic key claims (with brief expansion)
   - Entities mentioned (new vs. existing wiki pages)
   - Concepts mentioned (new vs. existing wiki pages)
   - Whether the source seems to split into multiple references/solutions (because it covers distinct canonical subjects) or stay as one
   - Any contradictions with existing wiki content
   - A proposed list of pages to create or update
   - Explicit asks: "Want me to emphasize X? Are these the right entities? Should this concept get its own page or fold into [[other-concept]]? Should this be one reference or two?"

5. **Wait for {{OWNER_NAME}}'s response.** He may redirect, add emphasis, deprioritize, or correct misreadings. **Do not write wiki pages until he confirms or modifies the plan.**

6. **Execute.** Once aligned:
   - Create the reference or solution page(s) in the appropriate folder
   - Create or update each affected wiki page
   - Add cross-links in both directions
   - Use `[[wiki-link]]` syntax everywhere
   - Set/bump `updated:` on every touched page
   - For each updated page, briefly note in chat what changed

7. **Update `index.md`.** Add new pages, bump entries for updated ones.

8. **Append to `log.md`.** Use the format below.

9. **Report back.** Brief summary in chat: "Ingested. Touched N pages. Created M. Conflicts flagged: K." List them.

## Query Workflow

When {{OWNER_NAME}} asks a question:

1. **Read `index.md` first.** It's your fastest map.
2. **Drill into relevant pages.** Read them in full, not just titles. Follow links one hop where useful.
3. **For best-practice queries, prefer canonical references.** When the question is "how should I do X" or "what's the right approach to Y," start from the relevant topic's **Canonical references** section (if it has one) or from `wiki/references/` pages tagged to the topic, before pulling in `wiki/solutions/` or project pages. This keeps externally-validated authority distinct from our own narrative.
4. **Synthesize.** Answer in chat with inline `[[wiki-link]]` citations.
5. **Offer to file the answer.** If the synthesis is non-trivial or required cross-referencing 3+ pages, ask: "Want me to file this as an analysis page?" If yes, write it into `wiki/analyses/`, update index, log it.
6. **Note gaps.** If the wiki couldn't fully answer, suggest:
   - A `questions/` entry, or
   - A source to seek out, or
   - A web search to fill the gap

## Lint Workflow

When {{OWNER_NAME}} says "lint" or "health check the wiki," walk the wiki and report:

1. **Orphans** — pages with zero inbound `[[links]]`. Either link them up or delete.
2. **Stubs** — pages with `status: stub` that are old enough to either promote or delete.
3. **Contradictions** — `> [!conflict]` callouts that haven't been resolved.
4. **Stale claims** — places where newer sources have superseded older claims but the older claim is still phrased as current.
5. **Missing pages** — entities/concepts mentioned in bold or referenced in plain text across 3+ pages but lacking a dedicated page.
6. **Concept-graduation candidates** — patterns that now meet the two-projects-or-project-plus-reference bar but still live on project/solution pages instead of having their own concept page.
7. **Broken links** — `[[wiki-links]]` that don't resolve.
8. **Frontmatter drift** — pages missing required fields, or with fields that don't match this schema. Includes `?` characters in field values, `parent:` paths that don't match folder location, and `source_paths:` entries pointing to nonexistent raw files.
9. **Tag sprawl** — tags used only once, or near-synonyms (`#llm` vs `#llms` vs `#language-model`).
10. **Suggested investigations** — questions worth opening, sources worth seeking.

Report findings as a markdown digest in chat. Don't auto-fix without confirmation. Fix in batches once {{OWNER_NAME}} approves.

## Conflict Policy

When a new source contradicts existing wiki content, **flag and preserve both**. Use Obsidian callouts:

```markdown
> [!conflict] Contradiction between sources
> **Older claim** (from [[2024-source-slug]], 2024-11-03): X is true because of Y.
> **Newer claim** (from [[2026-source-slug]], 2026-05-27): X is false; the better explanation is Z.
> *Unresolved — surfaced to {{OWNER_NAME}} 2026-05-27.*
```

Then:
- Update the page so both claims are visible
- Add the conflict to `wiki/questions/` if it's substantive
- Note the conflict in the ingest report

Never silently overwrite. The wiki's value is partly that you can trace how thinking evolved.

## index.md Format

`index.md` is content-oriented. Organized by category, not chronologically. Each entry is one line. Updated on every ingest.

Format per entry:

```markdown
- [[slug|Title]] — one-line description. *type · status · last-updated*
```

Organized under `## Topics`, `## Entities`, `## Concepts`, `## References`, `## Solutions`, `## Analyses`, `## Projects`, `## Personal`, `## Questions`.

Topics first because they're the hubs. Within Topics, list root topics with their nested topics indented one level beneath.

When the wiki grows past ~200 entries, switch index sections to Dataview queries (Obsidian plugin). Until then, hand-maintained is fine and faster to grep.

## log.md Format

`log.md` is chronological, append-only. Every entry starts with a consistent header so the file is grep-parseable.

Format:

```markdown
## [YYYY-MM-DD HH:MM] <action> | <subject>

<2-5 line summary of what happened, what was touched, what's open>

**Touched:** [[page1]], [[page2]], [[page3]]
**New:** [[page4]]
**Conflicts:** none | [[page5]]
```

Actions: `ingest`, `query`, `analysis`, `lint`, `refactor`, `schema-change`, `note`.

To get the last 5 entries: `grep "^## \[" log.md | tail -5`.

## Tag Registry (`meta/tags.md`)

Every tag in use must be registered in `meta/tags.md` with a one-line definition. This prevents tag sprawl. Before introducing a new tag, check the registry. If a near-synonym exists, use it instead.

## Hygiene Rules

- **Never modify `raw/`.** Read-only. If a source needs cleanup, copy to a new file with a `-cleaned` suffix.
- **Never delete a wiki page** without telling {{OWNER_NAME}}. Use `status: superseded` with a `successor:` field pointing to the replacement.
- **Bump `updated:` on every meaningful edit.** Not on typo fixes.
- **Verify before recommending.** Memory and old summaries can drift. When {{OWNER_NAME}} is about to act on something, check that the underlying page and source still say what you think.
- **Date discipline.** Always use absolute dates (`2026-05-27`), never relative ("last week"). Today's date is available in the environment header.
- **Tone.** Wiki pages are encyclopedic and neutral. Analyses can be opinionated but must mark opinions as such. Personal pages are {{OWNER_NAME}}'s voice — quote, don't paraphrase his words into something he didn't say.
- **No fabrication.** If a claim has no source, mark it `*(unsourced, from conversation 2026-05-27)*` or `*(hypothesis)*`.

## What NOT To Do

- Don't write to the wiki during the initial discussion phase of an ingest. Wait for confirmation.
- Don't create folders speculatively. Build them when first used.
- Don't put long-form content in `index.md` — it's an index. Content lives on the actual pages.
- Don't delete `log.md` entries. The log is append-only.
- Don't use `raw/` URLs as inline citations. Cite the source page, which holds the URL.
- Don't auto-resolve conflicts. Surface them.
- Don't paraphrase {{OWNER_NAME}}'s personal statements as if they came from elsewhere.
- Don't put emojis in pages unless {{OWNER_NAME}} asks.
- Don't promote a pattern to a concept page on its first appearance. Wait for the graduation bar.
- Don't nest topics deeper than one level.

## When To Update This Schema

This file evolves. When you and {{OWNER_NAME}} discover a convention that's working (or one that isn't), propose a schema change. Schema changes are logged in `log.md` with action `schema-change` and bump the `version:` and `last_updated:` in this file's frontmatter.

## First-Read Checklist for Every New Session

When you start a fresh session in this vault:

1. Read this file (`CLAUDE.md`) fully.
2. Read `index.md` to see what's in the wiki.
3. Read the last 10 entries of `log.md` to see recent activity: `grep "^## \[" log.md | tail -10`.
4. Then engage with {{OWNER_NAME}}'s request.

This is non-negotiable. The wiki only works if every session starts grounded.
