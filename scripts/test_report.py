"""Unit tests for report.py — the maintenance report contract.

Run: cd scripts && python3 -m unittest test_report

The acceptance bar from the plan (U8): generate -> parse back -> all ids and
statuses recoverable by wiki-triage.
"""

import unittest

import report
from report import ReportItem


def _sample_items():
    return [
        ReportItem("broken-link-aaaa1111", "lint", "safe",
                   "wiki/concepts/foo.md", "links to [[bar]] (unresolved)",
                   "fix slug to [[baz]]", "open"),
        ReportItem("orphan-bbbb2222", "audit", "judgment",
                   "wiki/entities/quux.md", "zero inbound links", "wire into a topic", "open"),
        ReportItem("missing-page-cccc3333", "gaps", "judgment",
                   "wiki/index.md", "[[widget]] referenced by 4 pages, no page", "create page", "open"),
    ]


class TestRoundTrip(unittest.TestCase):
    def test_write_then_parse_recovers_all(self):
        meta = {"vault": "/v/Hive-Mind", "timestamp": "2026-06-20-1430",
                "actor": "wiki-steward", "summary": "Routine pass."}
        text = report.write_report(meta, _sample_items())
        parsed = report.parse_report(text)
        self.assertEqual(len(parsed), 3)
        by_id = {it.id: it for it in parsed}
        self.assertEqual(set(by_id), {
            "broken-link-aaaa1111", "orphan-bbbb2222", "missing-page-cccc3333"})
        foo = by_id["broken-link-aaaa1111"]
        self.assertEqual(foo.category, "lint")
        self.assertEqual(foo.tier, "safe")
        self.assertEqual(foo.page, "wiki/concepts/foo.md")
        self.assertEqual(foo.detail, "links to [[bar]] (unresolved)")
        self.assertEqual(foo.proposed_action, "fix slug to [[baz]]")
        self.assertEqual(foo.status, "open")

    def test_categories_grouped(self):
        text = report.write_report({}, _sample_items())
        self.assertIn("## Lint", text)
        self.assertIn("## Audit", text)
        self.assertIn("## Gaps", text)
        # Lint section comes before Audit (CATEGORY_ORDER)
        self.assertLess(text.index("## Lint"), text.index("## Audit"))

    def test_header_counts(self):
        text = report.write_report({"actor": "wiki-steward"}, _sample_items())
        self.assertIn("**Findings:** 3", text)
        self.assertIn("status:open", text)


class TestStatusUpdates(unittest.TestCase):
    def test_set_status_applied_flips_checkbox(self):
        text = report.write_report({}, _sample_items())
        text2 = report.set_status(text, "broken-link-aaaa1111", "applied")
        parsed = {it.id: it for it in report.parse_report(text2)}
        self.assertEqual(parsed["broken-link-aaaa1111"].status, "applied")
        # checkbox synced
        line = [l for l in text2.splitlines() if "broken-link-aaaa1111" in l][0]
        self.assertTrue(line.startswith("- [x] "))
        # other items untouched
        self.assertEqual(parsed["orphan-bbbb2222"].status, "open")

    def test_set_status_skipped(self):
        text = report.write_report({}, _sample_items())
        text2 = report.set_status(text, "orphan-bbbb2222", "skipped")
        parsed = {it.id: it for it in report.parse_report(text2)}
        self.assertEqual(parsed["orphan-bbbb2222"].status, "skipped")

    def test_set_status_rejects_unknown(self):
        text = report.write_report({}, _sample_items())
        with self.assertRaises(ValueError):
            report.set_status(text, "orphan-bbbb2222", "bogus")

    def test_item_from_finding_dict(self):
        finding = {"id": "x-1", "category": "lint", "tier": "safe",
                   "page": "wiki/a.md", "detail": "d", "proposed_action": "a"}
        it = report.item_from_finding(finding)
        self.assertEqual(it.status, "open")
        self.assertEqual(it.id, "x-1")


if __name__ == "__main__":
    unittest.main()
