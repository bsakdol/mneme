"""Tests for gaps_checks.py. Run: cd skills/wiki-gaps/scripts && python3 -m unittest test_gaps_checks"""

import tempfile
import types
import unittest
from pathlib import Path

import gaps_checks


def _page(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\ntitle: T\ntype: concept\ncreated: 2026-01-01\n"
                    "updated: 2026-01-01\nstatus: active\ntags: [t]\n---\n" + body,
                    encoding="utf-8")


class GapsFixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self._tmp.name)
        w = self.vault / "wiki"
        # [[graduate-me]] referenced by 3 pages, no page -> missing-page
        for n in ("a", "b", "c"):
            _page(w / "concepts" / f"{n}.md", "talks about [[graduate-me]] here.\n")
        # [[seen-once]] referenced by 1 page -> NOT a missing page
        _page(w / "concepts" / "d.md", "a one-off [[seen-once]] mention.\n")
        # a real page so disk counts are non-zero
        _page(w / "concepts" / "real.md", "standalone.\n")
        # index that undercounts concepts (5 on disk: a,b,c,d,real; index lists 1)
        (self.vault / "index.md").write_text(
            "# Index\n\n## Concepts\n- [[real|Real]] — a page.\n\n## Entities\n",
            encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def _detect(self, min_refs=None):
        return gaps_checks.detect(self.vault, types.SimpleNamespace(min_refs=min_refs))

    def test_missing_page_threshold(self):
        mp = {f.detail for f in self._detect() if f.dimension == "missing-page"}
        self.assertTrue(any("graduate-me" in d for d in mp))
        self.assertFalse(any("seen-once" in d for d in mp))  # only 1 referrer

    def test_min_refs_override(self):
        mp = {f.detail for f in self._detect(min_refs=1) if f.dimension == "missing-page"}
        self.assertTrue(any("seen-once" in d for d in mp))  # now included

    def test_count_drift_detected(self):
        cd = [f for f in self._detect() if f.dimension == "count-drift"]
        concepts = [f for f in cd if "Concepts" in f.detail]
        self.assertTrue(concepts)
        self.assertIn("disk has 5", concepts[0].detail)

    def test_all_judgment_tier(self):
        self.assertTrue(all(f.tier == "judgment" for f in self._detect()))


if __name__ == "__main__":
    unittest.main()
