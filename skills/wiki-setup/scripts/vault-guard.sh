#!/usr/bin/env bash
# vault-guard.sh
# Checks whether a vault directory is ready for wiki-setup bootstrap.
#
# Usage:
#   vault-guard.sh <vault_path>
#
# Exit codes:
#   0  — vault is ready (Welcome.md removed if it was the only non-system content)
#   1  — vault path does not exist or is not a directory
#   2  — vault contains unexpected files or folders (non-empty)
#
# Output (stdout):
#   READY       — vault passed all checks; safe to proceed
#   NOT_FOUND   — path does not exist
#   NOT_EMPTY   — vault has content beyond known-safe Obsidian/macOS artefacts

set -uo pipefail

VAULT_PATH="${1:-}"

if [ -z "$VAULT_PATH" ]; then
    echo "Usage: vault-guard.sh <vault_path>" >&2
    exit 1
fi

# ── 1. Path existence check ──────────────────────────────────────────────────

if [ ! -d "$VAULT_PATH" ]; then
    echo "NOT_FOUND"
    exit 1
fi

# ── 2. Emptiness check ───────────────────────────────────────────────────────
#
# Inspect only the top level of the vault (maxdepth 1).
# Known-safe artefacts that do NOT indicate user content:
#   Welcome.md   — Obsidian's default note in every new vault
#   .DS_Store    — macOS Finder metadata; user cannot prevent it
#   .obsidian/   — Obsidian's own configuration directory; always present
#                  in a vault created via the Obsidian app
#   .claude/     — Claude Code project settings; written when the vault is
#                  used as a Claude Code project root

OTHER=$(find "$VAULT_PATH" -maxdepth 1 -mindepth 1 \
    ! -name "Welcome.md" \
    ! -name ".DS_Store"  \
    ! -name ".obsidian"  \
    ! -name ".claude"    \
    2>/dev/null)

if [ -n "$OTHER" ]; then
    echo "NOT_EMPTY"
    exit 2
fi

# ── 3. Conditional cleanup ───────────────────────────────────────────────────
#
# The vault is otherwise empty — it is safe to remove Welcome.md now.
# We only reach this point if no unexpected content exists, so we are
# not silently deleting a file the user may have edited.

if [ -f "$VAULT_PATH/Welcome.md" ]; then
    rm -f "$VAULT_PATH/Welcome.md"
fi

echo "READY"
exit 0
