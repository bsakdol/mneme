#!/usr/bin/env python3
"""lint_checks.py — wiki-lint category checks (R12): frontmatter, tags, links.

Standalone per-skill check script. Imports the shared Obsidian-awareness core
and CLI runner from ${CLAUDE_PLUGIN_ROOT}/scripts (with a relative fallback so
the script and its tests run from a clean checkout).

Dimensions (tier in parens):
  broken-link            safe if a unique date-prefix candidate exists, else judgment
  frontmatter-missing    judgment  (missing title/type/created/updated/status)
  frontmatter-bare-question  judgment  (a field whose value is a bare '?')
  parent-path-mismatch   safe  (nested-topic parent must match its folder)
  source-paths-missing-raw  judgment  (source_paths entry with no raw file)
  tag-single-use         judgment
  tag-near-synonym       judgment

Safe fixes (--fix-safe): unique-candidate broken links, parent-path mismatches.
There are no low-risk-tier fixes in this category.
"""

import os
import re
import sys

_ROOT = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

import checkrunner  # noqa: E402
import obsidian  # noqa: E402
from obsidian import Finding, Tier  # noqa: E402

REQUIRED_FIELDS = ("title", "type", "created", "updated", "status")
_DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}-")


def _strip_date(slug: str) -> str:
    return _DATE_PREFIX.sub("", slug)


def _unique_candidate(target: str, valid: set) -> str | None:
    """The single existing slug that matches target ignoring a date prefix, or
    None when there is zero or more than one — only a unique match is safe."""
    stem = _strip_date(target)
    cands = [v for v in valid if v != target and _strip_date(v) == stem]
    return cands[0] if len(cands) == 1 else None


def _expected_parent(path, vault) -> str | None:
    """For wiki/topics/<parent>/<child>.md return <parent>; for a root topic
    (wiki/topics/<root>.md) return None (no parent expected)."""
    rel = path.relative_to(vault)
    parts = rel.parts
    if len(parts) >= 2 and parts[0] == "wiki" and parts[1] == "topics":
        # wiki/topics/<...>/file.md
        middle = parts[2:-1]
        return middle[-1] if middle else None
    return None


def _norm_tag(tag: str) -> str:
    t = tag.lstrip("#").strip().lower().replace("-", "").replace("_", "")
    return t[:-1] if t.endswith("s") else t


def detect(vault, args):
    findings = []
    graph = obsidian.build_link_graph(vault)
    valid = obsidian.valid_target_slugs(vault)
    referrers = obsidian.dangling_referrers(vault)
    tag_pages: dict = {}  # tag -> set(page)

    for slug, path in sorted(graph.pages.items()):
        rel = str(path.relative_to(vault))
        text = path.read_text(encoding="utf-8", errors="replace")
        fields, _raw, body = obsidian.split_frontmatter(text)

        # broken-link
        live, _inert = obsidian.extract_links(body)
        for link in live:
            if link.is_embed or not link.target or link.target in valid:
                continue
            cand = _unique_candidate(link.target, valid)
            if cand:
                tier, action = Tier.SAFE.value, f"fix slug to [[{cand}]]"
            elif len(referrers.get(link.target, ())) >= obsidian.MISSING_PAGE_MIN_REFS:
                # referenced by many pages -> a missing-page signal owned by
                # wiki-gaps, not a one-off broken link. Don't double-report.
                continue
            else:
                tier, action = Tier.JUDGMENT.value, "create the page or correct the link"
            findings.append(Finding(
                obsidian.make_id("lint", "broken-link", rel, link.target),
                "lint", "broken-link", tier, rel,
                f"[[{link.target}]] does not resolve (line {link.line})", action))

        # frontmatter-missing
        missing = [f for f in REQUIRED_FIELDS if not fields.get(f)]
        if missing:
            findings.append(Finding(
                obsidian.make_id("lint", "frontmatter-missing", rel),
                "lint", "frontmatter-missing", Tier.JUDGMENT.value, rel,
                f"missing required field(s): {', '.join(missing)}",
                "fill in the missing frontmatter"))

        # frontmatter-bare-question
        for bad in obsidian.bare_question_fields(fields):
            findings.append(Finding(
                obsidian.make_id("lint", "frontmatter-bare-question", rel, bad),
                "lint", "frontmatter-bare-question", Tier.JUDGMENT.value, rel,
                f"field '{bad}' is a bare '?'", "leave the field empty or fill it in"))

        # parent-path-mismatch
        expected = _expected_parent(path, vault)
        declared = obsidian.frontmatter_link_targets(fields.get("parent", "")) if fields.get("parent") else []
        if expected and expected not in declared:
            findings.append(Finding(
                obsidian.make_id("lint", "parent-path-mismatch", rel),
                "lint", "parent-path-mismatch", Tier.SAFE.value, rel,
                f"parent should be [[{expected}]] to match folder", f"set parent to [[{expected}]]"))
        elif expected is None and declared and path.parent == (vault / "wiki" / "topics"):
            findings.append(Finding(
                obsidian.make_id("lint", "parent-path-mismatch", rel),
                "lint", "parent-path-mismatch", Tier.SAFE.value, rel,
                "root topic should not declare a parent", "remove the parent field"))

        # source-paths-missing-raw
        for sp in fields.get("source_paths", []) or []:
            if sp and not (vault / sp).exists():
                findings.append(Finding(
                    obsidian.make_id("lint", "source-paths-missing-raw", rel, sp),
                    "lint", "source-paths-missing-raw", Tier.JUDGMENT.value, rel,
                    f"source_paths entry '{sp}' has no raw file", "correct or remove the path"))

        # collect tags
        for tag in fields.get("tags", []) or []:
            if tag:
                tag_pages.setdefault(tag, set()).add(rel)

    # tag-single-use
    for tag, pages in sorted(tag_pages.items()):
        if len(pages) == 1:
            findings.append(Finding(
                obsidian.make_id("lint", "tag-single-use", tag),
                "lint", "tag-single-use", Tier.JUDGMENT.value, next(iter(pages)),
                f"tag '{tag}' is used on only one page", "merge into an existing tag or drop it"))

    # tag-near-synonym
    groups: dict = {}
    for tag in tag_pages:
        groups.setdefault(_norm_tag(tag), set()).add(tag)
    for norm, variants in sorted(groups.items()):
        if len(variants) > 1:
            findings.append(Finding(
                obsidian.make_id("lint", "tag-near-synonym", norm),
                "lint", "tag-near-synonym", Tier.JUDGMENT.value, "meta/tags.md",
                f"near-synonym tags: {', '.join(sorted(variants))}", "merge to a single canonical tag"))

    return findings


def fix_safe(vault, args):
    applied, skipped = [], []
    graph = obsidian.build_link_graph(vault)
    valid = obsidian.valid_target_slugs(vault)

    for slug, path in sorted(graph.pages.items()):
        rel = str(path.relative_to(vault))
        text = path.read_text(encoding="utf-8", errors="replace")
        fields, raw, body = obsidian.split_frontmatter(text)
        prefix = text[: len(text) - len(body)]  # frontmatter block (or "")
        changed = False

        # parent-path-mismatch (safe): correct the nested-topic parent, in the
        # frontmatter prefix only.
        expected = _expected_parent(path, vault)
        declared = obsidian.frontmatter_link_targets(fields.get("parent", "")) if fields.get("parent") else []
        if expected and expected not in declared and "parent:" in raw:
            prefix = re.sub(r"(?m)^parent:.*$", f'parent: "[[{expected}]]"', prefix, count=1)
            changed = True
            applied.append({"page": rel, "dimension": "parent-path-mismatch",
                            "detail": f"parent -> [[{expected}]]"})

        # broken-link (safe): rewrite unique-candidate links by their exact body
        # span, right-to-left so offsets stay valid. Replacing the span (not a
        # global string replace) means inert/code-span copies of the same link
        # are never touched, and anchored / escaped-pipe forms are handled by
        # swapping only the leading target slug inside the matched raw.
        live, _inert = obsidian.extract_links(body)
        edits = []
        for link in live:
            if link.is_embed or not link.target or link.target in valid:
                continue
            cand = _unique_candidate(link.target, valid)
            if cand:
                fixed_raw = link.raw.replace(link.target, cand, 1)  # leading slug only
                edits.append((link.start, link.end, fixed_raw, link.target, cand))
        if edits:
            for start, end, fixed_raw, old, new in sorted(edits, key=lambda e: e[0], reverse=True):
                body = body[:start] + fixed_raw + body[end:]
                applied.append({"page": rel, "dimension": "broken-link",
                                "detail": f"[[{old}]] -> [[{new}]]"})
            changed = True

        if changed:
            path.write_text(prefix + body, encoding="utf-8")

    return {"applied": applied, "skipped": skipped}


if __name__ == "__main__":
    sys.exit(checkrunner.run("lint", detect, fix_safe=fix_safe))
