"""Tests for audit_checks.py. Run: cd skills/wiki-audit/scripts && python3 -m unittest test_audit_checks"""

import tempfile
import types
import unittest
from pathlib import Path

import audit_checks


def _page(path, *, type_="concept", status="active", last_checked=None, body="Body.\n"):
    fm = ["---", "title: T", f"type: {type_}", "created: 2026-01-01",
          "updated: 2026-01-01", f"status: {status}", "tags: [t]"]
    if last_checked is not None:
        fm.append(f"last_checked: {last_checked}")
    fm.append("---")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(fm) + "\n" + body, encoding="utf-8")


class AuditFixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self._tmp.name)
        w = self.vault / "wiki"
        # hub links to several pages so they aren't orphans
        _page(w / "topics" / "hub.md", type_="topic",
              body="Links [[linked]], [[stubby]], [[fresh-ref]], [[old-ref]], [[no-date-ref]].\n")
        _page(w / "concepts" / "linked.md")
        _page(w / "concepts" / "orphan.md")  # nothing links here
        _page(w / "concepts" / "stubby.md", status="stub")
        _page(w / "references" / "fresh-ref.md", type_="reference", last_checked="2026-06-01")
        _page(w / "references" / "old-ref.md", type_="reference", last_checked="2025-01-01")
        _page(w / "references" / "no-date-ref.md", type_="reference")  # last_checked absent
        # conflict callouts
        (w / "concepts" / "conflicted.md").write_text(
            "---\ntitle: C\ntype: concept\ncreated: 2026-01-01\nupdated: 2026-01-01\n"
            "status: active\ntags: [t]\n---\n"
            "> [!conflict] Contradiction\n> Older vs newer.\n> *Unresolved — surfaced 2026-06-01.*\n\n"
            "> [!conflict] Settled one\n> This was reconciled; both noted.\n",
            encoding="utf-8")
        # link conflicted from hub too (avoid orphan noise in assertions)
        hub = w / "topics" / "hub.md"
        hub.write_text(hub.read_text().replace("[[no-date-ref]].",
                                               "[[no-date-ref]], [[conflicted]], [[orphan-skip]]."),
                       encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def _detect(self, today="2026-06-20"):
        return audit_checks.detect(self.vault, types.SimpleNamespace(today=today))

    def test_dimensions(self):
        dims = {f.dimension for f in self._detect()}
        for d in ("orphan", "stub", "stale-reference", "conflict-callout"):
            self.assertIn(d, dims)

    def test_orphan_only_unlinked(self):
        orphans = {f.page for f in self._detect() if f.dimension == "orphan"}
        self.assertIn("wiki/concepts/orphan.md", orphans)
        self.assertNotIn("wiki/concepts/linked.md", orphans)

    def test_stale_reference_logic(self):
        stale = {f.page for f in self._detect() if f.dimension == "stale-reference"}
        self.assertIn("wiki/references/old-ref.md", stale)       # >6mo
        self.assertIn("wiki/references/no-date-ref.md", stale)   # absent
        self.assertNotIn("wiki/references/fresh-ref.md", stale)  # recent

    def test_only_unresolved_conflicts_flagged(self):
        conflicts = [f for f in self._detect() if f.dimension == "conflict-callout"]
        self.assertEqual(len(conflicts), 1)  # the "Settled one" is not flagged

    def test_all_judgment_tier(self):
        self.assertTrue(all(f.tier == "judgment" for f in self._detect()))


if __name__ == "__main__":
    unittest.main()
