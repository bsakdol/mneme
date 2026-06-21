# wiki-gaps

Find **pages that should exist** in an mneme LLM Wiki vault — and catch index/disk drift.

Third stage of the maintenance order of operations: **wiki-lint → wiki-audit → wiki-gaps**.

## What it does

Runs the bundled checker. Both dimensions are **judgment-tier** — reported for you to decide; the skill never auto-creates pages or rewrites the index.

| Dimension | Notes |
|-----------|-------|
| `missing-page` | A `[[target]]` referenced by **N+ pages** (default 3, the schema's graduation bar) with no page of its own — a concept worth graduating. Pass `--min-refs` to tune. |
| `count-drift` | `index.md` per-type entry counts disagree with the files on disk. |

`missing-page` is the counterpart to `wiki-lint`'s broken-link handling: a dangling link referenced *widely* is a missing page (here), while a *one-off* dangling link is a lint broken-link. The split keeps each finding in exactly one place.

## Prerequisites

- A vault bootstrapped with `mneme:wiki-setup` (or name a vault when you invoke).
- `python3` in `PATH`.

## Invocation

```
mneme:wiki-gaps
```

or say "find missing pages" / "what should the wiki have that it doesn't" in a session.

## What you get

- A list of missing-page candidates with referrer counts, plus any index/disk drift.
- Guided, owner-present page creation or index reconciliation for items you choose to act on.
- A `log.md` entry (action `lint`).
- A handoff suggestion to the `wiki-steward` agent (full automated pass) and `wiki-triage`.
