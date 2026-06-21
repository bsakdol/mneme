#!/usr/bin/env python3
"""gaps_checks.py — wiki-gaps category checks (R11): pages that should exist.

Standalone per-skill check script over the shared Obsidian-awareness core.

Dimensions (all judgment-tier — gaps reports, the owner decides):
  missing-page  a dangling link target referenced by >= --min-refs pages (default 3)
                but having no page of its own (a concept worth graduating)
  count-drift   index.md per-type entry counts disagree with the files on disk

gaps has no safe or low-risk fixes; creating pages and rewriting the index are
owner decisions.
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

# index.md section title -> wiki/ subfolder
_INDEX_SECTIONS = {
    "Topics": "topics", "Entities": "entities", "Concepts": "concepts",
    "References": "references", "Solutions": "solutions", "Analyses": "analyses",
    "Projects": "projects", "Personal": "personal", "Questions": "questions",
}
_ENTRY_RE = re.compile(r"^\s*- \[\[")


def detect(vault, args):
    findings = []
    min_refs = getattr(args, "min_refs", None) or obsidian.MISSING_PAGE_MIN_REFS

    # missing-page: dangling targets referenced widely enough to deserve a page
    for target, pages in sorted(obsidian.dangling_referrers(vault).items()):
        if len(pages) >= min_refs:
            findings.append(Finding(
                obsidian.make_id("gaps", "missing-page", target),
                "gaps", "missing-page", Tier.JUDGMENT.value, sorted(pages)[0],
                f"[[{target}]] is referenced by {len(pages)} pages but has no page",
                "create the page (graduate the concept) or correct the references"))

    findings.extend(_count_drift(vault))
    return findings


def _count_drift(vault):
    index = vault / "index.md"
    if not index.is_file():
        return []
    sections = _parse_index_counts(index.read_text(encoding="utf-8", errors="replace"))
    out = []
    for title, folder in _INDEX_SECTIONS.items():
        idx_count = sections.get(title, 0)
        disk = vault / "wiki" / folder
        disk_count = len(list(disk.rglob("*.md"))) if disk.is_dir() else 0
        if idx_count != disk_count:
            out.append(Finding(
                obsidian.make_id("gaps", "count-drift", folder),
                "gaps", "count-drift", Tier.JUDGMENT.value, "index.md",
                f"index lists {idx_count} under {title}, disk has {disk_count}",
                "reconcile index.md against disk"))
    return out


def _parse_index_counts(text: str) -> dict:
    counts: dict = {}
    current = None
    for line in text.split("\n"):
        if line.startswith("## "):
            current = line[3:].strip()
            counts.setdefault(current, 0)
        elif current and _ENTRY_RE.match(line):
            counts[current] += 1
    return counts


def _add_args(parser):
    parser.add_argument("--min-refs", type=int, dest="min_refs",
                        help="how many referrers make a dangling target a missing page (default 3)")


if __name__ == "__main__":
    sys.exit(checkrunner.run("gaps", detect, add_args=_add_args))
