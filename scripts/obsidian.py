"""obsidian.py — shared Obsidian-awareness core for the mneme maintenance suite.

This module is the single source of the must-not-drift logic that every
category check depends on:

  - Obsidian-aware wiki-link extraction and resolution
  - inert-context classification (code spans / fences, HTML comments)
  - the vault-wide link graph (inbound / outbound)
  - the shared Finding shape and tier enum consumed by the report

Dangling wiki-links (targets with no page) are not special-cased here: the
schema has no "forward link" annotation, so a check that cares reports them as
broken-link findings and lets the owner decide.

It is a LIBRARY, not a CLI. The per-skill check scripts
(skills/<skill>/scripts/<cat>_checks.py) and the wiki-steward agent import it
via ``${CLAUDE_PLUGIN_ROOT}/scripts`` on ``sys.path``:

    import os, sys
    sys.path.insert(0, os.path.join(os.environ["CLAUDE_PLUGIN_ROOT"], "scripts"))
    import obsidian

Standard library only (no PyYAML): the vault frontmatter is flat by schema, so
a minimal line parser is sufficient and keeps the suite dependency-free.
"""

from __future__ import annotations

import bisect
import hashlib
import re
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path


# --- Tiers -----------------------------------------------------------------

class Tier(str, Enum):
    """Risk tier of a finding. Drives what runs unattended (see plan)."""
    SAFE = "safe"            # deterministic, single correct outcome
    LOW_RISK = "low-risk"    # reversible, mechanical, no new prose/judgment
    JUDGMENT = "judgment"    # irreversible or contentful — report only


# Page stems that always resolve, even without a wiki/ file backing them.
SPECIAL_TARGETS = frozenset({"CLAUDE", "index", "log", "tags"})


# --- Findings --------------------------------------------------------------

@dataclass
class Finding:
    """The shared finding shape emitted by every category check and rendered
    into the maintenance report (U8)."""
    id: str
    category: str          # "lint" | "audit" | "gaps"
    dimension: str         # e.g. "broken-link"
    tier: str              # a Tier value
    page: str              # vault-relative path
    detail: str
    proposed_action: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def make_id(category: str, dimension: str, page: str, key: str = "") -> str:
    """Stable, content-derived finding id — deterministic across runs so the
    report and wiki-triage can match an item to its prior status."""
    basis = f"{category}:{dimension}:{page}:{key}"
    digest = hashlib.sha1(basis.encode("utf-8")).hexdigest()[:8]
    return f"{dimension}-{digest}"


def build_report(category: str, findings: list, schema_version: str = "") -> dict:
    """Assemble the --report JSON envelope shared by all category scripts."""
    by_tier: dict = {}
    for f in findings:
        by_tier[f.tier] = by_tier.get(f.tier, 0) + 1
    return {
        "schema_version": schema_version,
        "category": category,
        "counts": {"total": len(findings), "by_tier": by_tier},
        "findings": [f.to_dict() for f in findings],
    }


# --- Inert-region masking --------------------------------------------------

# Fenced code blocks: ``` or ~~~ runs, multiline, matching the opening fence.
_FENCE_RE = re.compile(r"(?ms)^[ \t]*(`{3,}|~{3,}).*?^[ \t]*\1[ \t]*$")
_HTML_COMMENT_RE = re.compile(r"(?s)<!--.*?-->")
_INLINE_CODE_RE = re.compile(r"`+[^`\n]*`+")


def _blank(match: re.Match) -> str:
    # Replace every non-newline char with a space: same length, lines preserved,
    # so character offsets and line numbers stay valid against the original.
    return re.sub(r"[^\n]", " ", match.group(0))


def mask_inert(text: str) -> str:
    """Blank out inert regions (fenced code, HTML comments, inline code) while
    preserving length and newlines. A wiki-link whose span survives masking is
    *live*; one that is blanked was *inert* (illustrative / code-span)."""
    text = _FENCE_RE.sub(_blank, text)
    text = _HTML_COMMENT_RE.sub(_blank, text)
    text = _INLINE_CODE_RE.sub(_blank, text)
    return text


# --- Wiki-link extraction --------------------------------------------------

# [[target]] | [[target|display]] | [[target\|display]] | ![[embed]] | [[t#anchor]]
_WIKILINK_RE = re.compile(r"(!?)\[\[([^\[\]]+?)\]\]")


@dataclass
class WikiLink:
    raw: str               # full matched text, e.g. "[[a#b\\|c]]"
    target: str            # resolved slug, e.g. "a"
    display: str | None    # display text after the (possibly escaped) pipe
    anchor: str | None     # heading or ^block anchor after '#'
    is_embed: bool         # leading '!' — a transclusion/embed
    line: int              # 1-based line number in the body


def resolve_target(inner: str):
    """Given the inside of [[...]], return (target_slug, display, anchor).

    Handles the escaped display pipe used inside Markdown tables (``\\|``),
    heading/block anchors (``#``), and surrounding whitespace.
    """
    inner_norm = inner.replace(r"\|", "|")        # escaped table pipe -> pipe
    display = None
    if "|" in inner_norm:
        link_part, display = inner_norm.split("|", 1)
    else:
        link_part = inner_norm
    anchor = None
    if "#" in link_part:
        link_part, anchor = link_part.split("#", 1)
    return (
        link_part.strip(),
        display.strip() if display is not None else None,
        anchor.strip() if anchor else None,
    )


def _line_indexer(body: str):
    starts = [0]
    for i, ch in enumerate(body):
        if ch == "\n":
            starts.append(i + 1)

    def line_of(pos: int) -> int:
        return bisect.bisect_right(starts, pos)

    return line_of


def _build_link(m: re.Match, line_of) -> WikiLink:
    target, display, anchor = resolve_target(m.group(2))
    return WikiLink(
        raw=m.group(0),
        target=target,
        display=display,
        anchor=anchor,
        is_embed=(m.group(1) == "!"),
        line=line_of(m.start()),
    )


def extract_links(body: str):
    """Return (live_links, inert_links) for a page body.

    Live links are real references that must resolve. Inert links appeared
    inside code spans / fences / HTML comments — illustrative, never broken.
    """
    masked = mask_inert(body)
    line_of = _line_indexer(body)
    live, inert = [], []
    for m in _WIKILINK_RE.finditer(body):
        link = _build_link(m, line_of)
        if masked[m.start():m.end()].strip() == "":
            inert.append(link)
        else:
            live.append(link)
    return live, inert


# --- Frontmatter (minimal flat-YAML) --------------------------------------

_FRONTMATTER_RE = re.compile(r"(?s)\A---\n(.*?)\n---[ \t]*\n?")


def split_frontmatter(text: str):
    """Return (fields, raw_frontmatter, body).

    Minimal flat-YAML parser: scalars, quoted scalars, inline ``[a, b]`` lists
    and block ``- item`` lists. The schema uses no nested maps, so this is
    sufficient and keeps the suite stdlib-only.
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, "", text
    raw = m.group(1)
    return _parse_flat_yaml(raw), raw, text[m.end():]


def _strip_scalar(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


def _parse_flat_yaml(raw: str) -> dict:
    fields: dict = {}
    lines = raw.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            i += 1
            continue
        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest == "":
            items = []
            j = i + 1
            while j < len(lines) and lines[j].lstrip().startswith("- "):
                items.append(_strip_scalar(lines[j].lstrip()[2:]))
                j += 1
            if items:
                fields[key] = items  # block list
                i = j
            else:
                fields[key] = ""     # empty scalar (e.g. "author:")
                i += 1
            continue
        if rest.startswith("[") and rest.endswith("]"):
            inner = rest[1:-1].strip()
            fields[key] = [_strip_scalar(x) for x in inner.split(",")] if inner else []
        else:
            fields[key] = _strip_scalar(rest)
        i += 1
    return fields


def bare_question_fields(fields: dict):
    """Return field names whose value is a bare '?' (an unfilled placeholder).
    A '?' *within* a value is valid and is not reported."""
    bad = []
    for k, v in fields.items():
        if isinstance(v, str) and v.strip() == "?":
            bad.append(k)
        elif isinstance(v, list) and any(
            isinstance(x, str) and x.strip() == "?" for x in v
        ):
            bad.append(k)
    return bad


_FM_LINK_RE = re.compile(r"\[\[([^\[\]]+?)\]\]")


def frontmatter_link_targets(value):
    """Resolve [[...]] targets embedded in a frontmatter scalar or list value."""
    targets = []
    values = value if isinstance(value, list) else [value]
    for v in values:
        if not isinstance(v, str):
            continue
        for m in _FM_LINK_RE.finditer(v):
            target, _disp, _anchor = resolve_target(m.group(1))
            if target:
                targets.append(target)
    return targets


# --- Vault traversal + link graph -----------------------------------------

def iter_wiki_pages(vault: Path):
    """Yield every wiki page path (wiki/**/*.md), sorted for determinism."""
    wiki = vault / "wiki"
    if wiki.is_dir():
        yield from sorted(wiki.rglob("*.md"))


def valid_target_slugs(vault: Path):
    """Set of slugs that a wiki-link may resolve to: every wiki page stem plus
    the special bookkeeping targets."""
    slugs = set(SPECIAL_TARGETS)
    for p in iter_wiki_pages(vault):
        slugs.add(p.stem)
    return slugs


@dataclass
class LinkGraph:
    outbound: dict   # slug -> set(target slug)
    inbound: dict    # slug -> set(source slug)
    pages: dict      # slug -> Path


# Frontmatter fields that carry wiki-links and therefore create graph edges.
_FRONTMATTER_LINK_FIELDS = ("sources", "parent", "project", "successor")


def build_link_graph(vault: Path) -> LinkGraph:
    """Build the inbound/outbound wiki-link graph across all wiki pages.

    Edges come from live body links and from wiki-link-bearing frontmatter
    fields (sources/parent/project/successor) so orphan detection sees the
    true inbound set. Inert links and embeds do not create edges.
    """
    pages = {p.stem: p for p in iter_wiki_pages(vault)}
    outbound = {s: set() for s in pages}
    inbound = {s: set() for s in pages}
    for slug, path in pages.items():
        text = path.read_text(encoding="utf-8", errors="replace")
        fields, _raw, body = split_frontmatter(text)
        targets = set()
        live, _inert = extract_links(body)
        for link in live:
            if link.target and not link.is_embed:
                targets.add(link.target)
        for fk in _FRONTMATTER_LINK_FIELDS:
            if fk in fields:
                targets.update(frontmatter_link_targets(fields[fk]))
        for t in targets:
            outbound[slug].add(t)
            if t in inbound:
                inbound[t].add(slug)
    return LinkGraph(outbound=outbound, inbound=inbound, pages=pages)


def read_schema_version(vault: Path) -> str:
    """Read schema_version from the vault's CLAUDE.md frontmatter (the live
    authority), or '' if unavailable."""
    claude = vault / "CLAUDE.md"
    if not claude.is_file():
        return ""
    fields, _raw, _body = split_frontmatter(
        claude.read_text(encoding="utf-8", errors="replace")
    )
    return str(fields.get("schema_version", ""))
