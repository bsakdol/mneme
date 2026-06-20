"""checkrunner.py — shared CLI for the per-skill check scripts.

Each skill's check script (skills/<skill>/scripts/<cat>_checks.py) supplies a
``detect`` function and optional ``fix_safe`` / ``fix_lowrisk`` functions, then
calls ``checkrunner.run(...)``. This single-sources the --report / --fix-safe /
--fix-lowrisk CLI and the JSON envelopes so the three scripts stay consistent.

  detect(vault: Path, args) -> list[obsidian.Finding]
  fix_safe(vault: Path, args) -> {"applied": [...], "skipped": [...]}
  fix_lowrisk(vault: Path, args) -> same shape

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import obsidian


def run(category, detect, fix_safe=None, fix_lowrisk=None, add_args=None):
    parser = argparse.ArgumentParser(
        description=f"mneme {category} checks (Obsidian-aware)."
    )
    parser.add_argument("vault", help="absolute path to the vault root")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--report", action="store_true",
                      help="detect and emit findings as JSON (default)")
    mode.add_argument("--fix-safe", action="store_true",
                      help="apply safe-tier fixes")
    mode.add_argument("--fix-lowrisk", action="store_true",
                      help="apply low-risk-tier fixes")
    if add_args:
        add_args(parser)
    args = parser.parse_args()

    vault = Path(args.vault).expanduser()
    if not vault.is_dir():
        print(json.dumps({"error": f"vault not found: {vault}"}))
        return 2

    if args.fix_safe or args.fix_lowrisk:
        fixer = fix_safe if args.fix_safe else fix_lowrisk
        result = fixer(vault, args) if fixer else {"applied": [], "skipped": []}
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    findings = detect(vault, args)
    schema_version = obsidian.read_schema_version(vault)
    json.dump(obsidian.build_report(category, findings, schema_version),
              sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0
