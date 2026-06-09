#!/usr/bin/env bash
# resolve-vault.sh
# Returns the default vault path from ~/.config/mneme/settings.json.
#
# Usage:
#   resolve-vault.sh
#
# Exit codes:
#   0  — default vault is configured; path printed to stdout
#   1  — settings.json exists but default_vault is absent or empty
#   2  — ~/.config/mneme/settings.json does not exist
#
# Output (stdout):
#   VAULT_PATH:<absolute-path>  — default vault resolved
#   NO_DEFAULT                  — settings.json exists but no default_vault set
#   NOT_CONFIGURED              — settings.json does not exist

set -uo pipefail

SETTINGS="${HOME}/.config/mneme/settings.json"

# ── 1. Existence check ────────────────────────────────────────────────────────

if [ ! -f "$SETTINGS" ]; then
    echo "NOT_CONFIGURED"
    exit 2
fi

# ── 2. Read default vault ─────────────────────────────────────────────────────

result=$(python3 - "$SETTINGS" <<'EOF'
import sys, json
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
    name = data.get("default_vault", "")
    if not name:
        print("NO_DEFAULT")
    else:
        path = data.get("vaults", {}).get(name, {}).get("vault_path", "")
        if path:
            print("VAULT_PATH:" + path)
        else:
            print("NO_DEFAULT")
except Exception:
    print("NOT_CONFIGURED")
EOF
)

case "$result" in
    VAULT_PATH:*)
        echo "$result"
        exit 0
        ;;
    NO_DEFAULT)
        echo "NO_DEFAULT"
        exit 1
        ;;
    *)
        echo "NOT_CONFIGURED"
        exit 2
        ;;
esac
