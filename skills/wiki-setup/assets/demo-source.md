
*Adapted from the LLM Wiki pattern documentation for use as a demo source.*

# The LLM Wiki Pattern: Building a Personal Knowledge Base with Language Models

The LLM Wiki pattern is an approach to personal knowledge management in which a large language model agent serves as the active maintainer of a structured wiki, while the human owner acts as curator and reader. Rather than requiring the owner to write, organize, and link articles by hand, the pattern delegates that labor to the agent. The owner's role is to supply source material, confirm the agent's proposed actions, and ask questions. The result is a knowledge base that grows through conversation rather than through manual note-taking.

## The Core Insight

Most personal knowledge management systems fail because they require too much ongoing maintenance from the person who is supposed to benefit from them. The LLM Wiki pattern inverts the typical relationship: the agent writes, the owner reads. This single inversion resolves the maintenance burden that causes conventional wikis and note systems to go stale.

A second principle reinforces the first: source documents are never modified. Once a document enters the system it is preserved exactly as received. All synthesis, summarization, and cross-referencing happens in a separate layer that the agent controls. This separation means the original record is always recoverable, and any error in the synthesized wiki can be corrected without losing the underlying material.

## The Three-Layer Architecture

The pattern organizes its vault into three functional layers.

The **raw layer** (`raw/`) holds immutable source documents — articles, transcripts, reports, notes, or any other material the owner wants to ingest. Files in `raw/` are never edited after ingest. They serve as the authoritative record from which all wiki content is derived. A typical path looks like `raw/articles/2025-06-01-some-article-title.md`.

The **wiki layer** (`wiki/`) holds all LLM-maintained synthesis pages, organized by type. Each page is a structured Markdown file with a consistent frontmatter schema. The agent creates, updates, and links these pages as it processes source documents and answers queries. The owner reads these pages but does not edit them directly.

The **schema and bookkeeping layer** consists of a small set of files that ground every session. `CLAUDE.md` is the primary schema document: it defines the page type system, naming conventions, frontmatter fields, and the rules the agent must follow when writing or updating any page. `index.md` is a hand-maintained or agent-maintained entry point listing key pages. `log.md` records every ingest and significant agent action, providing an audit trail. A `meta/` directory may hold additional configuration or statistics pages.

## The Ingest Workflow

Ingest is the process of adding a new source document to the vault. The workflow is conversational and proceeds one source at a time.

The owner provides a source document — by pasting text, dropping a file, or pointing the agent to a path. The agent reads the document and, before writing anything, surfaces its proposed takeaways: a TL;DR, a list of key claims it intends to extract, named entities it expects to create or update, and any concepts or topics the document touches. The owner reviews this surface-level summary and either confirms or redirects. If the owner confirms, the agent executes: it writes the raw file, creates or updates wiki pages, logs the ingest in `log.md`, and reports what it did. No page is written without the owner's explicit confirmation.

This step-before-execution discipline serves two purposes. It catches misreadings before they propagate into the wiki, and it keeps the owner informed about how the knowledge base is growing without requiring them to read every page the agent writes.

## The Query Workflow

Querying the wiki is equally conversational. The owner asks a question in natural language. The agent reads the relevant wiki pages — using `index.md` and internal links to navigate — and synthesizes an answer from what it finds. If the answer requires combining information across multiple pages, the agent does that synthesis inline.

For non-trivial answers, the agent offers to file the result as an analysis page in the wiki. This means useful reasoning does not disappear at the end of a session; it becomes part of the knowledge base available for future queries. The owner chooses whether to accept, modify, or discard the proposed page.

## Page Types

The wiki layer uses a typed page system to impose consistent structure. The standard types are: **entities** (people, organizations, products), **concepts** (ideas, frameworks, mental models), **topics** (subject areas that aggregate related pages), **references** (bibliographic entries for specific sources), **solutions** (how-to procedures or worked answers to recurring problems), **analyses** (reasoning pages produced by the agent in response to queries), **projects** (ongoing efforts), **personal** (owner-specific context, used sparingly), and **questions** (open questions to be answered by future ingest or research). Each type has a defined frontmatter schema specified in `CLAUDE.md`.

## Tools Used in Practice

The LLM Wiki pattern is tool-agnostic in principle but has been implemented most visibly using three tools. **Obsidian** (by Obsidian.md) provides the vault management layer: it stores files as plain Markdown, renders internal links, and offers a graph view that makes the web of connections between pages visible at a glance. **Claude** (by Anthropic) serves as the LLM agent: its long context window allows it to read multiple wiki pages in a single session, and its instruction-following characteristics make it well-suited to operating within a strict schema. **Claude Code** is the runtime environment in which the agent executes: it has filesystem access, can read and write files directly, and maintains session context across a conversation.

## Getting Started

To adopt the pattern, a practitioner needs a Markdown-based vault (Obsidian is the standard choice), an LLM agent with filesystem access, and a `CLAUDE.md` schema document that defines the rules for the specific vault. The schema document is the most important artifact: it is what transforms a general-purpose language model into a consistent wiki maintainer. A reference implementation of `CLAUDE.md`, along with starter templates for each page type, is sufficient to begin ingesting documents and building a wiki from the first session.
