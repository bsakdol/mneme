"""report.py — the maintenance report contract (U8).

Single source of the report format shared between the producer
(``wiki-steward``, which writes a report) and the consumer (``wiki-triage``,
which reads it and updates item status). A report lives at
``VAULT/meta/maintenance-reports/YYYY-MM-DD-HHMM.md`` and is both human-readable
and machine-parseable:

  - ``write_report(meta, items)`` renders findings to markdown
  - ``parse_report(text)`` recovers them
  - ``set_status(text, id, status)`` flips one item's status in place

write/parse round-trip, so wiki-triage can read a steward report, change a
status, and write it back without drift. Standard library only.

Each finding renders as one checklist line with a stable id and an explicit
status, so both the human and the parser read the same source of truth:

    - [ ] broken-link-ab12cd34 · safe · wiki/concepts/foo.md — detail → action · status:open
"""

from __future__ import annotations

import re
from dataclasses import dataclass

STATUSES = ("open", "applied", "skipped")
CATEGORY_ORDER = ("lint", "audit", "gaps")
CATEGORY_TITLE = {"lint": "Lint", "audit": "Audit", "gaps": "Gaps"}
_TITLE_TO_CATEGORY = {v: k for k, v in CATEGORY_TITLE.items()}


@dataclass
class ReportItem:
    id: str
    category: str
    tier: str
    page: str
    detail: str
    proposed_action: str = ""
    status: str = "open"


_LINE_RE = re.compile(
    r"^- \[(?P<box>[ xX])\] "
    r"(?P<id>\S+) · (?P<tier>\S+) · (?P<page>\S+) — "
    r"(?P<body>.*?) · status:(?P<status>\w+)\s*$"
)


def item_from_finding(finding) -> ReportItem:
    """Build a ReportItem from an obsidian.Finding (or any object/dict with the
    matching fields). New findings start ``open``."""
    get = (lambda k: finding.get(k)) if isinstance(finding, dict) else (lambda k: getattr(finding, k))
    return ReportItem(
        id=get("id"),
        category=get("category"),
        tier=get("tier"),
        page=get("page"),
        detail=get("detail"),
        proposed_action=get("proposed_action") or "",
        status="open",
    )


def _render_item(item: ReportItem) -> str:
    box = "x" if item.status == "applied" else " "
    body = f"{item.detail} → {item.proposed_action}" if item.proposed_action else item.detail
    return f"- [{box}] {item.id} · {item.tier} · {item.page} — {body} · status:{item.status}"


def _parse_item(line: str):
    m = _LINE_RE.match(line)
    if not m:
        return None
    body = m.group("body")
    detail, action = body.split(" → ", 1) if " → " in body else (body, "")
    return ReportItem(
        id=m.group("id"),
        category="",  # filled by parse_report from the section header
        tier=m.group("tier"),
        page=m.group("page"),
        detail=detail,
        proposed_action=action,
        status=m.group("status"),
    )


def write_report(meta: dict, items) -> str:
    """Render a maintenance report. ``meta`` carries vault, timestamp, actor,
    and an optional summary. ``items`` is an iterable of ReportItem."""
    items = list(items)
    by_tier: dict = {}
    by_status: dict = {}
    for it in items:
        by_tier[it.tier] = by_tier.get(it.tier, 0) + 1
        by_status[it.status] = by_status.get(it.status, 0) + 1

    lines = [
        f"# Maintenance Report — {meta.get('timestamp', '')}",
        "",
        f"- **Vault:** {meta.get('vault', '')}",
        f"- **Actor:** {meta.get('actor', '')}",
        f"- **Findings:** {len(items)}"
        + (f" ({', '.join(f'{k}: {by_tier[k]}' for k in sorted(by_tier))})" if by_tier else ""),
        f"- **Status:** {', '.join(f'{k}: {by_status[k]}' for k in sorted(by_status)) or 'none'}",
    ]
    if meta.get("summary"):
        lines += ["", meta["summary"]]

    for cat in CATEGORY_ORDER:
        cat_items = [it for it in items if it.category == cat]
        if not cat_items:
            continue
        lines += ["", f"## {CATEGORY_TITLE[cat]}", ""]
        lines += [_render_item(it) for it in cat_items]

    return "\n".join(lines).rstrip() + "\n"


def parse_report(text: str):
    """Recover the ReportItem list from a report's markdown."""
    items = []
    current_cat = ""
    for line in text.splitlines():
        if line.startswith("## "):
            current_cat = _TITLE_TO_CATEGORY.get(line[3:].strip(), "")
        elif line.startswith("- ["):
            it = _parse_item(line)
            if it:
                it.category = current_cat
                items.append(it)
    return items


def set_status(text: str, item_id: str, new_status: str) -> str:
    """Return ``text`` with the status of the line whose id matches flipped to
    ``new_status`` (and its checkbox synced). Used by wiki-triage."""
    if new_status not in STATUSES:
        raise ValueError(f"unknown status {new_status!r}; expected one of {STATUSES}")
    out = []
    for line in text.splitlines():
        m = _LINE_RE.match(line)
        if m and m.group("id") == item_id:
            it = _parse_item(line)
            it.status = new_status
            out.append(_render_item(it))
        else:
            out.append(line)
    result = "\n".join(out)
    return result + "\n" if text.endswith("\n") else result
