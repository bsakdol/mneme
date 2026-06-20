# wiki-audit

Audit an mneme LLM Wiki vault for **stale, thin, or inconsistent pages**.

Second stage of the maintenance order of operations: **wiki-lint → wiki-audit → wiki-gaps**.

## What it does

Runs the bundled checker and adds a model-reasoning pass. Every audit finding is **judgment-tier** — reported for you to decide; nothing is auto-fixed.

| Dimension | Source | Notes |
|-----------|--------|-------|
| `orphan` | deterministic | Page with zero inbound links (body + frontmatter edges). |
| `stub` | deterministic | `status: stub` page, with its inbound-link count. |
| `stale-reference` | deterministic | Reference page whose `last_checked` is absent or older than 6 months. |
| `conflict-callout` | deterministic | An unresolved `> [!conflict]` callout. |
| stale claims | reasoning | A newer source has superseded an older claim still phrased as current. |
| concept-graduation | reasoning | A pattern that now meets the graduation bar but lacks its own concept page. |
| suggested investigations | reasoning | Open questions or sources worth seeking. |

## Prerequisites

- A vault bootstrapped with `mneme:wiki-setup` (or name a vault when you invoke).
- `python3` in `PATH`.

## Invocation

```
mneme:wiki-audit
```

or say "audit the vault" / "find stale or thin pages" in a session.

## What you get

- A findings report grouped by dimension (deterministic + reasoning), all judgment-tier.
- Guided, owner-present handling of items you choose to act on now (the rest can go to `wiki-triage`).
- A `log.md` entry (action `lint`).
- A handoff suggestion to `wiki-gaps` (or the `wiki-steward` agent for a full automated pass).
