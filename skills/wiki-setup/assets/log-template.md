---
title: "Activity Log"
type: meta
updated: {{TODAY}}
---
# Activity Log

Append-only chronological record. Newest entries at the bottom.

Header format: `## [YYYY-MM-DD HH:MM] <action> | <subject>`

Actions: `ingest`, `query`, `analysis`, `lint`, `refactor`, `schema-change`, `note`.

Quick navigation: `grep "^## \[" log.md | tail -10` for the last 10 entries.

---
