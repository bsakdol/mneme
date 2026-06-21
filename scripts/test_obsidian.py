"""Unit tests for obsidian.py — the shared Obsidian-awareness core.

Run: python3 -m unittest scripts/test_obsidian.py
(or:  cd scripts && python3 -m unittest test_obsidian)

The acceptance bar from the plan: every known inert-link context is classified
correctly (none of the inert ones treated as live/broken), and link-graph
inbound counts are correct on a known fixture.
"""

import tempfile
import unittest
from pathlib import Path

import obsidian


class TestInertClassification(unittest.TestCase):
    def _live_inert(self, body):
        live, inert = obsidian.extract_links(body)
        return {l.target for l in live}, {l.target for l in inert}

    def test_inline_code_span_is_inert(self):
        live, inert = self._live_inert("See `[[code-span]]` for syntax.")
        self.assertIn("code-span", inert)
        self.assertNotIn("code-span", live)

    def test_fenced_block_is_inert(self):
        body = "Example:\n\n```\n[[fenced-link]]\n```\n\nDone."
        live, inert = self._live_inert(body)
        self.assertIn("fenced-link", inert)
        self.assertNotIn("fenced-link", live)

    def test_tilde_fence_is_inert(self):
        body = "~~~\n[[tilde-fenced]]\n~~~\n"
        live, inert = self._live_inert(body)
        self.assertIn("tilde-fenced", inert)

    def test_html_comment_is_inert(self):
        live, inert = self._live_inert("<!-- [[commented-out]] -->")
        self.assertIn("commented-out", inert)
        self.assertNotIn("commented-out", live)

    def test_plain_link_is_live(self):
        live, inert = self._live_inert("A real [[plain-link]] here.")
        self.assertIn("plain-link", live)
        self.assertEqual(inert, set())

    def test_blockquote_link_is_live(self):
        # A wiki-link inside a blockquote is a real link in Obsidian.
        live, inert = self._live_inert("> see [[quoted-link]] above")
        self.assertIn("quoted-link", live)

    def test_escaped_pipe_table_link_resolves_and_is_live(self):
        # The 2026-06-20 false-positive case: [[slug\|Display]] in a table.
        live, inert = obsidian.extract_links("| [[real-target\\|Nice Name]] | x |")
        targets = {l.target for l in live}
        self.assertIn("real-target", targets)  # NOT "real-target\\"
        self.assertEqual(inert, [])


class TestResolution(unittest.TestCase):
    def test_escaped_pipe(self):
        t, d, a = obsidian.resolve_target(r"slug\|Display Text")
        self.assertEqual(t, "slug")
        self.assertEqual(d, "Display Text")

    def test_plain_pipe(self):
        t, d, a = obsidian.resolve_target("slug|Display")
        self.assertEqual((t, d), ("slug", "Display"))

    def test_heading_anchor(self):
        t, d, a = obsidian.resolve_target("page#Some Heading")
        self.assertEqual(t, "page")
        self.assertEqual(a, "Some Heading")

    def test_block_anchor(self):
        t, d, a = obsidian.resolve_target("page#^block-id")
        self.assertEqual(t, "page")
        self.assertEqual(a, "^block-id")


class TestEmbedsAndLines(unittest.TestCase):
    def test_embed_detected(self):
        live, _ = obsidian.extract_links("![[diagram.png]]")
        self.assertTrue(live[0].is_embed)

    def test_line_numbers(self):
        live, _ = obsidian.extract_links("line one\nline two [[here]]\nline three")
        self.assertEqual(live[0].line, 2)


class TestFrontmatter(unittest.TestCase):
    def test_scalars_and_lists(self):
        text = (
            "---\n"
            'title: "What is X?"\n'
            "type: concept\n"
            "tags: [a, b, c]\n"
            "sources:\n"
            '  - "[[ref-one]]"\n'
            '  - "[[ref-two]]"\n'
            "author:\n"
            "---\n"
            "Body here.\n"
        )
        fields, raw, body = obsidian.split_frontmatter(text)
        self.assertEqual(fields["title"], "What is X?")
        self.assertEqual(fields["type"], "concept")
        self.assertEqual(fields["tags"], ["a", "b", "c"])
        self.assertEqual(fields["sources"], ["[[ref-one]]", "[[ref-two]]"])
        self.assertEqual(fields["author"], "")
        self.assertEqual(body.strip(), "Body here.")

    def test_no_frontmatter(self):
        fields, raw, body = obsidian.split_frontmatter("# Just a heading\n")
        self.assertEqual(fields, {})
        self.assertTrue(body.startswith("# Just a heading"))

    def test_bare_question_detected(self):
        fields = {"author": "?", "title": "What is X?", "tags": ["ok", "?"]}
        bad = obsidian.bare_question_fields(fields)
        self.assertIn("author", bad)   # value is solely '?'
        self.assertIn("tags", bad)     # a list item is solely '?'
        self.assertNotIn("title", bad)  # '?' within a value is fine

    def test_frontmatter_link_targets(self):
        self.assertEqual(
            obsidian.frontmatter_link_targets(["[[ref-one]]", "[[ref-two]]"]),
            ["ref-one", "ref-two"],
        )


class TestLinkGraph(unittest.TestCase):
    def _make_vault(self, tmp):
        vault = Path(tmp)
        (vault / "wiki" / "concepts").mkdir(parents=True)
        (vault / "wiki" / "entities").mkdir(parents=True)
        # alpha links to beta (body) and gamma (frontmatter source)
        (vault / "wiki" / "concepts" / "alpha.md").write_text(
            "---\ntitle: Alpha\nsources:\n  - \"[[gamma]]\"\n---\n"
            "Alpha references [[beta]] and `[[not-a-link]]`.\n",
            encoding="utf-8",
        )
        # beta links to nothing
        (vault / "wiki" / "concepts" / "beta.md").write_text(
            "---\ntitle: Beta\n---\nBeta stands alone.\n", encoding="utf-8"
        )
        # gamma is an entity, linked only via alpha's frontmatter
        (vault / "wiki" / "entities" / "gamma.md").write_text(
            "---\ntitle: Gamma\n---\nGamma entity.\n", encoding="utf-8"
        )
        return vault

    def test_inbound_outbound(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = self._make_vault(tmp)
            g = obsidian.build_link_graph(vault)
            self.assertEqual(g.outbound["alpha"], {"beta", "gamma"})
            self.assertEqual(g.inbound["beta"], {"alpha"})
            self.assertEqual(g.inbound["gamma"], {"alpha"})  # frontmatter edge
            self.assertEqual(g.inbound["alpha"], set())      # alpha is an orphan
            # the code-span link must NOT create an edge
            self.assertNotIn("not-a-link", g.outbound["alpha"])

    def test_slug_collisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            (vault / "wiki" / "concepts").mkdir(parents=True)
            (vault / "wiki" / "entities").mkdir(parents=True)
            (vault / "wiki" / "concepts" / "mercury.md").write_text(
                "---\ntitle: M\n---\nx\n", encoding="utf-8")
            (vault / "wiki" / "entities" / "mercury.md").write_text(
                "---\ntitle: M\n---\nx\n", encoding="utf-8")
            (vault / "wiki" / "concepts" / "unique.md").write_text(
                "---\ntitle: U\n---\nx\n", encoding="utf-8")
            cols = obsidian.slug_collisions(vault)
            self.assertEqual(set(cols), {"mercury"})
            self.assertEqual(cols["mercury"],
                             ["wiki/concepts/mercury.md", "wiki/entities/mercury.md"])

    def test_dangling_referrers(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            (vault / "wiki" / "concepts").mkdir(parents=True)
            for name in ("p1", "p2"):
                (vault / "wiki" / "concepts" / f"{name}.md").write_text(
                    "---\ntitle: X\n---\nlinks [[ghost]] and [[beta]].\n", encoding="utf-8")
            (vault / "wiki" / "concepts" / "beta.md").write_text(
                "---\ntitle: Beta\n---\nreal page.\n", encoding="utf-8")
            refs = obsidian.dangling_referrers(vault)
            self.assertEqual(refs.get("ghost"), {"wiki/concepts/p1.md", "wiki/concepts/p2.md"})
            self.assertNotIn("beta", refs)  # beta resolves, not dangling

    def test_valid_target_slugs_includes_specials(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = self._make_vault(tmp)
            slugs = obsidian.valid_target_slugs(vault)
            self.assertTrue({"alpha", "beta", "gamma"} <= slugs)
            self.assertTrue({"CLAUDE", "index", "log", "tags"} <= slugs)


class TestSchemaVersion(unittest.TestCase):
    def test_read_schema_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            (vault / "CLAUDE.md").write_text(
                "---\ntitle: Wiki Operating Schema\nschema_version: 0.3.0\n---\nbody\n",
                encoding="utf-8",
            )
            self.assertEqual(obsidian.read_schema_version(vault), "0.3.0")


if __name__ == "__main__":
    unittest.main()
