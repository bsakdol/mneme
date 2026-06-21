"""Tests for lint_checks.py. Run: cd skills/wiki-lint/scripts && python3 -m unittest test_lint_checks"""

import tempfile
import types
import unittest
from pathlib import Path

import lint_checks
import obsidian


def _page(path: Path, *, title="T", type_="concept", status="active",
          tags=None, parent=None, source_paths=None, extra="", body="Body.\n"):
    fm = ["---", f'title: "{title}"', f"type: {type_}",
          "created: 2026-01-01", "updated: 2026-01-01", f"status: {status}"]
    fm.append("tags: [" + ", ".join(tags or []) + "]")
    if parent:
        fm.append(f'parent: "{parent}"')
    if source_paths:
        fm.append("source_paths: [" + ", ".join(f'"{s}"' for s in source_paths) + "]")
    if extra:
        fm.append(extra)
    fm.append("---")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(fm) + "\n" + body, encoding="utf-8")


class LintFixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self._tmp.name)
        w = self.vault / "wiki"
        _page(w / "concepts" / "transformer.md", title="Transformer", tags=["llm", "arch"])
        _page(w / "concepts" / "attention.md", tags=["llms"],
              body="See [[transformer]] for context.\n")  # live, resolves
        _page(w / "references" / "2026-01-01-widget.md", type_="reference", tags=["arch"])
        # broken.md: [[widget]] has a unique date-prefix candidate (safe);
        #            [[nonexistent-xyz]] has none (judgment)
        _page(w / "concepts" / "broken.md", tags=["arch"],
              body="A [[widget]] and a [[nonexistent-xyz]] link.\n")
        # thin.md: missing title and status
        (w / "concepts").mkdir(parents=True, exist_ok=True)
        (w / "concepts" / "thin.md").write_text(
            "---\ntype: concept\ncreated: 2026-01-01\nupdated: 2026-01-01\ntags: [arch]\n---\nThin.\n",
            encoding="utf-8")
        _page(w / "concepts" / "questionable.md", tags=["arch"], extra="author: ?")
        _page(w / "topics" / "llm-tooling.md", type_="topic", tags=["arch"])
        _page(w / "topics" / "llm-tooling" / "claude.md", type_="topic",
              tags=["arch"], parent="[[wrong-parent]]")  # mismatch -> safe
        _page(w / "references" / "2026-02-02-bad.md", type_="reference",
              tags=["arch"], source_paths=["raw/articles/missing.md"])
        # [[widely-missing]] referenced by 3 pages -> a missing-page signal that
        # lint must NOT report as broken-link (wiki-gaps owns it)
        for n in ("ref-a", "ref-b", "ref-c"):
            _page(w / "concepts" / f"{n}.md", tags=["arch"],
                  body="mentions [[widely-missing]] here.\n")
        # link-form coverage: [[widget]] has a unique candidate (2026-01-01-widget),
        # so plain / anchored / escaped-pipe forms are all safe-fixable, while the
        # code-span copy must be left untouched.
        _page(w / "concepts" / "linkforms.md", tags=["arch"],
              body=("Live [[widget]] here.\n"
                    "Anchored [[widget#section]] too.\n"
                    "Table | [[widget\\|W]] | x |\n"
                    "Code span: `[[widget]]` stays.\n"))

    def tearDown(self):
        self._tmp.cleanup()

    def _detect(self):
        return lint_checks.detect(self.vault, types.SimpleNamespace())

    def _dims(self):
        return {f.dimension for f in self._detect()}

    def test_dimensions_detected(self):
        dims = self._dims()
        for expected in ("broken-link", "frontmatter-missing",
                         "frontmatter-bare-question", "parent-path-mismatch",
                         "source-paths-missing-raw", "tag-single-use", "tag-near-synonym"):
            self.assertIn(expected, dims, f"expected {expected} in {dims}")

    def test_broken_link_tiers(self):
        bl = [f for f in self._detect() if f.dimension == "broken-link"]
        tiers = {f.detail.split("]]")[0].lstrip("[") : f.tier for f in bl}
        self.assertEqual(tiers.get("widget"), obsidian.Tier.SAFE.value)
        self.assertEqual(tiers.get("nonexistent-xyz"), obsidian.Tier.JUDGMENT.value)

    def test_live_resolving_link_not_flagged(self):
        bl = [f for f in self._detect() if f.dimension == "broken-link"]
        self.assertFalse(any("transformer" in f.detail for f in bl))

    def test_missing_page_candidate_not_reported_as_broken_link(self):
        bl = [f for f in self._detect() if f.dimension == "broken-link"]
        self.assertFalse(any("widely-missing" in f.detail for f in bl),
                         "multi-referenced dangling link should route to gaps, not lint")
        # the one-off dangling link is still reported
        self.assertTrue(any("nonexistent-xyz" in f.detail for f in bl))

    def test_fix_safe_applies_only_safe(self):
        result = lint_checks.fix_safe(self.vault, types.SimpleNamespace())
        applied_dims = {a["dimension"] for a in result["applied"]}
        self.assertEqual(applied_dims, {"broken-link", "parent-path-mismatch"})
        # broken-link safe fix rewrote the unique candidate
        broken = (self.vault / "wiki" / "concepts" / "broken.md").read_text()
        self.assertIn("[[2026-01-01-widget]]", broken)
        self.assertIn("[[nonexistent-xyz]]", broken)  # judgment one untouched
        # parent corrected to match folder
        claude = (self.vault / "wiki" / "topics" / "llm-tooling" / "claude.md").read_text()
        self.assertIn("[[llm-tooling]]", claude)

    def test_fix_safe_is_idempotent(self):
        lint_checks.fix_safe(self.vault, types.SimpleNamespace())
        second = lint_checks.fix_safe(self.vault, types.SimpleNamespace())
        self.assertEqual(second["applied"], [])

    def test_fix_safe_handles_all_link_forms_and_spares_code_spans(self):
        lint_checks.fix_safe(self.vault, types.SimpleNamespace())
        text = (self.vault / "wiki" / "concepts" / "linkforms.md").read_text()
        # plain, anchored, and escaped-pipe live links all rewritten
        self.assertIn("Live [[2026-01-01-widget]] here.", text)
        self.assertIn("[[2026-01-01-widget#section]]", text)
        self.assertIn("[[2026-01-01-widget\\|W]]", text)  # escaped pipe preserved
        # the code-span copy is inert and must be left exactly as written
        self.assertIn("`[[widget]]`", text)


if __name__ == "__main__":
    unittest.main()
