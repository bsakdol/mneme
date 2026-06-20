#!/usr/bin/env python3
"""audit_checks.py — wiki-audit category checks (R10): stale / thin / inconsistent pages.

Standalone per-skill check script over the shared Obsidian-awareness core.

Dimensions (all judgment-tier — audit reports, the owner decides):
  orphan           page with zero inbound links
  stub             page with status: stub (with inbound count)
  stale-reference  reference page whose last_checked is absent or older than 6 months
  conflict-callout an unresolved > [!conflict] callout

audit has no safe or low-risk fixes; every finding routes to the report.
"""

import datetime
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

_STALE_DAYS = 182  # ~6 months, matching the vault's stale-reference rule
_CONFLICT_RE = re.compile(r"^\s*>\s*\[!conflict\]", re.IGNORECASE)


def _parse_today(value):
    if value:
        return datetime.date.fromisoformat(value)
    return datetime.date.today()


def _stale_reason(last_checked: str, today: datetime.date):
    if not last_checked:
        return "last_checked is absent"
    try:
        when = datetime.date.fromisoformat(last_checked.strip())
    except ValueError:
        return f"last_checked '{last_checked}' is not a valid date"
    if (today - when).days > _STALE_DAYS:
        return f"last_checked {last_checked} is older than 6 months"
    return None


def _conflict_blocks(body: str):
    """Yield (line_number, block_text) for each > [!conflict] callout."""
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        if _CONFLICT_RE.match(lines[i]):
            block = [lines[i]]
            j = i + 1
            while j < len(lines) and lines[j].lstrip().startswith(">"):
                block.append(lines[j])
                j += 1
            yield i + 1, "\n".join(block)
            i = j
        else:
            i += 1


def detect(vault, args):
    findings = []
    graph = obsidian.build_link_graph(vault)
    today = _parse_today(getattr(args, "today", None))

    for slug, path in sorted(graph.pages.items()):
        rel = str(path.relative_to(vault))
        fields, _raw, body = obsidian.split_frontmatter(
            path.read_text(encoding="utf-8", errors="replace"))

        if not graph.inbound.get(slug):
            findings.append(Finding(
                obsidian.make_id("audit", "orphan", rel),
                "audit", "orphan", Tier.JUDGMENT.value, rel,
                "zero inbound links", "link it from a relevant topic/page, or remove it"))

        if fields.get("status") == "stub":
            inbound = len(graph.inbound.get(slug, ()))
            findings.append(Finding(
                obsidian.make_id("audit", "stub", rel),
                "audit", "stub", Tier.JUDGMENT.value, rel,
                f"status: stub ({inbound} inbound link(s))", "promote with content or delete"))

        if fields.get("type") == "reference":
            reason = _stale_reason(fields.get("last_checked", ""), today)
            if reason:
                findings.append(Finding(
                    obsidian.make_id("audit", "stale-reference", rel),
                    "audit", "stale-reference", Tier.JUDGMENT.value, rel,
                    reason, "re-check the live source via the Update workflow"))

        for line_no, block in _conflict_blocks(body):
            if "unresolved" in block.lower():
                findings.append(Finding(
                    obsidian.make_id("audit", "conflict-callout", rel, str(line_no)),
                    "audit", "conflict-callout", Tier.JUDGMENT.value, rel,
                    f"unresolved conflict callout (line {line_no})",
                    "resolve the contradiction or open a question"))

    return findings


def _add_args(parser):
    parser.add_argument("--today", help="override today's date (YYYY-MM-DD) for staleness")


if __name__ == "__main__":
    sys.exit(checkrunner.run("audit", detect, add_args=_add_args))
