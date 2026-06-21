#!/usr/bin/env python3
"""schema_update.py — shared schema-migration core for mneme's wiki-update skill.

Detects when a vault's frozen schema snapshot (its ``CLAUDE.md``) is behind the
plugin's bundled schema and prepares the migration. This module is the
must-not-drift logic the ``wiki-update`` skill orchestrates; the skill itself
handles the interactive prompts, backups, and writes.

Two halves:

  * **Detection (U2)** — version parsing/compare, archive base resolution,
    owner-name personalization + validation, and the ``--report`` JSON the skill
    branches on.
  * **Merge (U3)** — frontmatter split + deterministic reconstruction, the
    ``git merge-file`` 3-way body merge with fence-aware conflict parsing, and
    the ``difflib`` overwrite fallback.

Frontmatter/version parsing is REUSED from ``obsidian.py`` (``split_frontmatter``,
``read_schema_version``) rather than reimplemented, so this module can never
drift from the parser the maintenance suite already depends on.

Standard library only (plus ``git`` as an external binary for the merge, with a
stdlib fallback when it is absent).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import obsidian  # sibling module in ${CLAUDE_PLUGIN_ROOT}/scripts

OWNER_TOKEN = "{{OWNER_NAME}}"
TODAY_TOKEN = "{{TODAY}}"


# --- Plugin layout ---------------------------------------------------------

def plugin_root() -> Path:
    """Resolve the plugin install root. Honors ${CLAUDE_PLUGIN_ROOT}; falls back
    to the parent of this script's directory (scripts/ -> root)."""
    env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent


def canonical_template(root: Path) -> Path:
    return root / "skills" / "wiki-setup" / "assets" / "CLAUDE-template.md"


def canonical_templates_dir(root: Path) -> Path:
    return root / "skills" / "wiki-setup" / "assets" / "templates"


def history_root(root: Path) -> Path:
    return root / "schema-history"


def resolve_base(version: str, root: Path) -> Path | None:
    """Path to the archived bundle for ``version``, or None when that version
    predates the archive."""
    if not version:
        return None
    d = history_root(root) / version
    return d if d.is_dir() else None


# --- Version detection + compare -------------------------------------------

def _semver_tuple(v: str):
    """Parse a dotted version into a 3-tuple of ints, or None if unparseable.
    Pads short versions (``0.7`` -> ``(0, 7, 0)``) so comparisons are stable."""
    if not isinstance(v, str):
        return None
    raw = v.strip()
    if not raw:
        return None
    try:
        parts = [int(p) for p in raw.split(".")]
    except ValueError:
        return None
    if not parts:
        return None
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def compare(current: str, bundled: str) -> str:
    """One of 'up-to-date' / 'behind' / 'ahead' / 'unknown'."""
    c = _semver_tuple(current)
    b = _semver_tuple(bundled)
    if c is None or b is None:
        return "unknown"
    if c == b:
        return "up-to-date"
    return "behind" if c < b else "ahead"


def read_version_from_file(path: Path) -> str:
    """Read schema_version from any CLAUDE.md-shaped file's frontmatter (the
    bundled template), or '' if unavailable. Mirrors obsidian.read_schema_version,
    which is vault-relative."""
    if not path.is_file():
        return ""
    fields, _raw, _body = obsidian.split_frontmatter(
        path.read_text(encoding="utf-8", errors="replace")
    )
    return str(fields.get("schema_version", ""))


# --- Owner-name personalization + validation -------------------------------

def personalize(text: str, owner_name: str, today: str | None = None) -> str:
    """Forward-only substitution of schema tokens into their personalized form.
    Never reverse-tokenizes. ``today`` is optional because the body carries no
    {{TODAY}} token — only the frontmatter does."""
    out = text.replace(OWNER_TOKEN, owner_name)
    if today is not None:
        out = out.replace(TODAY_TOKEN, today)
    return out


def validate_owner_name(name) -> tuple[bool, str]:
    """Guard the substitution payload (KTD-7). Reject empty names, names carrying
    template braces, and names with embedded newlines."""
    if not isinstance(name, str) or not name.strip():
        return False, "owner name is empty"
    if "{{" in name or "}}" in name:
        return False, "owner name contains template braces ({{ or }})"
    if "\n" in name or "\r" in name:
        return False, "owner name contains a newline"
    return True, ""


# --- Settings lookup (owner-name source) -----------------------------------

def default_settings_path() -> Path:
    return Path.home() / ".config" / "mneme" / "settings.json"


def owner_name_from_settings(vault_path, settings_path: Path | None = None):
    """Return the owner_name recorded for the vault whose vault_path matches,
    or None. Tolerates a missing/malformed settings file."""
    settings_path = settings_path or default_settings_path()
    try:
        data = json.loads(Path(settings_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    target = str(vault_path)
    for entry in (data.get("vaults") or {}).values():
        if str(entry.get("vault_path", "")) == target:
            owner = entry.get("owner_name")
            return owner or None
    return None


# --- Report ----------------------------------------------------------------

def build_report(vault: Path, root: Path, settings_path: Path | None = None) -> dict:
    """The JSON the skill branches on, mirroring the lint --report contract shape."""
    current = obsidian.read_schema_version(vault)
    bundled = read_version_from_file(canonical_template(root))
    status = compare(current, bundled)
    base = resolve_base(current, root)
    owner = owner_name_from_settings(vault, settings_path)
    return {
        "current_version": current,
        "bundled_version": bundled,
        "status": status,
        "base_available": base is not None,
        "owner_name_source": "settings" if owner else "absent",
    }


# --- CLI -------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="mneme vault schema migration core")
    parser.add_argument("vault", help="absolute path to the vault")
    parser.add_argument("--report", action="store_true",
                        help="print the drift-detection report as JSON")
    args = parser.parse_args(argv)

    vault = Path(args.vault)
    root = plugin_root()

    if args.report:
        json.dump(build_report(vault, root), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
