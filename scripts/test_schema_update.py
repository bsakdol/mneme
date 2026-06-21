"""Unit tests for schema_update.py — the schema-migration core.

Run: python3 -m unittest scripts/test_schema_update.py
(or:  cd scripts && python3 -m unittest test_schema_update)

Covers U2 (detection: compare, resolve_base, personalize, validate_owner_name,
the whole-bundle drift guard, report) and U3 (the 3-way merge engine).
"""

import filecmp
import tempfile
import unittest
from pathlib import Path

import schema_update

# Real repo root, derived from the module location (independent of
# CLAUDE_PLUGIN_ROOT, which may be set in the surrounding session).
REPO_ROOT = Path(schema_update.__file__).resolve().parent.parent


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _claude(schema_version="0.7.0", owner="Jordan", created="2026-01-01"):
    """A personalized vault CLAUDE.md — the tokenized template (_tmpl) rendered
    with an owner + created date. Shares the single frontmatter literal in _tmpl."""
    body = "\n# {{OWNER_NAME}}'s wiki\n\n{{OWNER_NAME}} curates sources.\n"
    return schema_update.personalize(_tmpl(schema_version, body), owner, created)


class TestCompare(unittest.TestCase):
    def test_equal_is_up_to_date(self):
        self.assertEqual(schema_update.compare("0.7.0", "0.7.0"), "up-to-date")

    def test_older_is_behind(self):
        self.assertEqual(schema_update.compare("0.7.0", "0.8.0"), "behind")

    def test_newer_is_ahead(self):
        self.assertEqual(schema_update.compare("0.9.0", "0.8.0"), "ahead")

    def test_none_current_is_unknown(self):
        self.assertEqual(schema_update.compare("", "0.8.0"), "unknown")
        self.assertEqual(schema_update.compare("not-a-version", "0.8.0"), "unknown")

    def test_multidigit_segments(self):
        # 0.9.0 < 0.10.0 — integer compare, not lexical
        self.assertEqual(schema_update.compare("0.9.0", "0.10.0"), "behind")
        self.assertEqual(schema_update.compare("0.10.0", "0.9.0"), "ahead")

    def test_short_version_padding(self):
        self.assertEqual(schema_update.compare("0.7", "0.7.0"), "up-to-date")


class TestResolveBase(unittest.TestCase):
    def test_archived_version_resolves(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "schema-history" / "0.7.0").mkdir(parents=True)
            self.assertIsNotNone(schema_update.resolve_base("0.7.0", root))

    def test_unarchived_version_is_none(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "schema-history" / "0.7.0").mkdir(parents=True)
            self.assertIsNone(schema_update.resolve_base("0.5.0", root))

    def test_empty_version_is_none(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(schema_update.resolve_base("", Path(d)))


class TestPersonalize(unittest.TestCase):
    def test_substitutes_owner_and_today(self):
        out = schema_update.personalize("Hi {{OWNER_NAME}} on {{TODAY}}", "Jordan", "2026-06-21")
        self.assertEqual(out, "Hi Jordan on 2026-06-21")

    def test_owner_only_leaves_today_token(self):
        out = schema_update.personalize("{{OWNER_NAME}} / {{TODAY}}", "Jordan")
        self.assertEqual(out, "Jordan / {{TODAY}}")

    def test_no_tokens_is_byte_identical(self):
        text = "No tokens here.\n```\ncode\n```\n"
        self.assertEqual(schema_update.personalize(text, "Jordan"), text)


class TestValidateOwnerName(unittest.TestCase):
    def test_accepts_normal_name(self):
        ok, _ = schema_update.validate_owner_name("Jordan Smith")
        self.assertTrue(ok)

    def test_rejects_empty(self):
        self.assertFalse(schema_update.validate_owner_name("")[0])
        self.assertFalse(schema_update.validate_owner_name("   ")[0])

    def test_rejects_template_braces(self):
        self.assertFalse(schema_update.validate_owner_name("{{X}}")[0])

    def test_rejects_newline(self):
        self.assertFalse(schema_update.validate_owner_name("Jor\ndan")[0])


class TestOwnerNameFromSettings(unittest.TestCase):
    def test_reads_owner_for_matching_vault(self):
        with tempfile.TemporaryDirectory() as d:
            settings = _write(Path(d) / "settings.json",
                              '{"vaults": {"personal": {"vault_path": "/v", "owner_name": "Jordan"}}}')
            self.assertEqual(schema_update.owner_name_from_settings("/v", settings), "Jordan")

    def test_absent_owner_is_none(self):
        with tempfile.TemporaryDirectory() as d:
            settings = _write(Path(d) / "settings.json",
                              '{"vaults": {"personal": {"vault_path": "/v"}}}')
            self.assertIsNone(schema_update.owner_name_from_settings("/v", settings))

    def test_malformed_settings_is_none(self):
        with tempfile.TemporaryDirectory() as d:
            settings = _write(Path(d) / "settings.json", "not json")
            self.assertIsNone(schema_update.owner_name_from_settings("/v", settings))


class TestReport(unittest.TestCase):
    def _root_with_template(self, d, bundled="0.8.0"):
        root = Path(d)
        _write(canonical := schema_update.canonical_template(root), _claude(schema_version=bundled))
        (root / "schema-history" / "0.7.0").mkdir(parents=True)
        return root

    def test_behind_with_base_available(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as vd:
            root = self._root_with_template(d, bundled="0.8.0")
            _write(Path(vd) / "CLAUDE.md", _claude(schema_version="0.7.0"))
            rep = schema_update.build_report(Path(vd), root)
            self.assertEqual(rep["status"], "behind")
            self.assertEqual(rep["current_version"], "0.7.0")
            self.assertEqual(rep["bundled_version"], "0.8.0")
            self.assertTrue(rep["base_available"])

    def test_up_to_date_report(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as vd:
            root = self._root_with_template(d, bundled="0.7.0")
            _write(Path(vd) / "CLAUDE.md", _claude(schema_version="0.7.0"))
            rep = schema_update.build_report(Path(vd), root)
            self.assertEqual(rep["status"], "up-to-date")

    def test_report_has_all_contract_keys(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as vd:
            root = self._root_with_template(d)
            _write(Path(vd) / "CLAUDE.md", _claude(schema_version="0.7.0"))
            rep = schema_update.build_report(Path(vd), root)
            for key in ("current_version", "bundled_version", "status",
                        "base_available", "owner_name_source"):
                self.assertIn(key, rep)


class TestDriftGuard(unittest.TestCase):
    """KTD-5: every file under schema-history/<latest>/ must be byte-identical to
    the canonical bundle — CLAUDE-template.md AND all nine templates."""

    def test_whole_bundle_byte_identical(self):
        bundled = schema_update.read_version_from_file(
            schema_update.canonical_template(REPO_ROOT))
        self.assertTrue(bundled, "could not read bundled schema_version")
        archive = schema_update.history_root(REPO_ROOT) / bundled
        self.assertTrue(archive.is_dir(),
                        f"no archived bundle for latest version {bundled}")

        # CLAUDE-template.md
        self.assertTrue(filecmp.cmp(
            schema_update.canonical_template(REPO_ROOT),
            archive / "CLAUDE-template.md", shallow=False),
            "archived CLAUDE-template.md drifted from canonical")

        # The nine templates — enumerate from canonical so a missing/extra
        # archived file also fails.
        canon_templates = sorted(
            p.name for p in schema_update.canonical_templates_dir(REPO_ROOT).glob("*.md"))
        arch_templates = sorted(
            p.name for p in (archive / "templates").glob("*.md"))
        self.assertEqual(canon_templates, arch_templates,
                         "archived template set differs from canonical set")
        for name in canon_templates:
            self.assertTrue(filecmp.cmp(
                schema_update.canonical_templates_dir(REPO_ROOT) / name,
                archive / "templates" / name, shallow=False),
                f"archived template {name} drifted from canonical")


BASE_BODY = (
    "\n# CLAUDE.md\n\n"
    "## Section A\nOwned by {{OWNER_NAME}}.\n\n"
    "## Section B\nOld B content.\n"
)
NEW_BODY = (
    "\n# CLAUDE.md\n\n"
    "## Section A\nOwned by {{OWNER_NAME}}.\n\n"
    "## Section B\nNew B content.\n\n"
    "## Section C\nBrand new.\n"
)


def _tmpl(schema_version, body):
    return (
        "---\n"
        "title: Wiki Operating Schema\n"
        "type: schema\n"
        f"schema_version: {schema_version}\n"
        "created: {{TODAY}}\n"
        "updated: {{TODAY}}\n"
        "generated_by: mneme:wiki-setup\n"
        "---\n"
        + body
    )


def _make_root(d, old="0.7.0", new="0.8.0"):
    """Fake plugin root: canonical template at `new`, archived base at `old`."""
    root = Path(d)
    _write(schema_update.canonical_template(root), _tmpl(new, NEW_BODY))
    _write(root / "schema-history" / old / "CLAUDE-template.md", _tmpl(old, BASE_BODY))
    return root


def _make_vault(vd, schema_version="0.7.0", owner="Jordan", created="2026-01-01",
                body=BASE_BODY):
    text = schema_update.personalize(_tmpl(schema_version, body), owner, created)
    _write(Path(vd) / "CLAUDE.md", text)
    return Path(vd)


@unittest.skipUnless(schema_update.git_available(), "git not available")
class TestThreeWayMerge(unittest.TestCase):
    def test_no_edits_clean_fast_forward(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as vd:
            root = _make_root(d)
            vault = _make_vault(vd)
            r = schema_update.prepare_update(vault, "Jordan", "2026-06-21", root)
            self.assertEqual(r["mode"], "merge")
            self.assertEqual(r["outcome"], "clean")
            self.assertEqual(r["conflict_count"], 0)
            self.assertIn("## Section C", r["merged_text"])        # schema addition
            self.assertIn("New B content.", r["merged_text"])      # schema change
            self.assertIn("schema_version: 0.8.0", r["merged_text"])
            self.assertIn("created: 2026-01-01", r["merged_text"])  # preserved
            self.assertIn("updated: 2026-06-21", r["merged_text"])  # today

    def test_edit_in_untouched_section_preserved(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as vd:
            root = _make_root(d)
            edited = BASE_BODY.replace("Owned by {{OWNER_NAME}}.",
                                       "Owned by {{OWNER_NAME}}.\nMy personal note.")
            vault = _make_vault(vd, body=edited)
            r = schema_update.prepare_update(vault, "Jordan", "2026-06-21", root)
            self.assertEqual(r["outcome"], "clean")
            self.assertIn("My personal note.", r["merged_text"])   # owner edit kept
            self.assertIn("## Section C", r["merged_text"])        # schema addition kept

    def test_edit_in_changed_section_conflicts(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as vd:
            root = _make_root(d)
            edited = BASE_BODY.replace("Old B content.", "My custom B content.")
            vault = _make_vault(vd, body=edited)
            r = schema_update.prepare_update(vault, "Jordan", "2026-06-21", root)
            self.assertEqual(r["outcome"], "conflicts")
            self.assertGreaterEqual(r["conflict_count"], 1)
            self.assertIn("<<<<<<<", r["merged_text"])

    def test_name_as_substring_no_false_conflict(self):
        # Owner adds an incidental self-reference using their own name in an
        # untouched section — it must survive without a spurious conflict.
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as vd:
            root = _make_root(d)
            edited = BASE_BODY.replace("Owned by {{OWNER_NAME}}.",
                                       "Owned by {{OWNER_NAME}}.\nJordan likes patterns.")
            vault = _make_vault(vd, owner="Jordan", body=edited)
            r = schema_update.prepare_update(vault, "Jordan", "2026-06-21", root)
            self.assertEqual(r["outcome"], "clean")
            self.assertIn("Jordan likes patterns.", r["merged_text"])

    def test_overwrite_fallback_when_no_base(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as vd:
            root = _make_root(d, old="0.7.0", new="0.8.0")
            vault = _make_vault(vd, schema_version="0.5.0")  # not archived
            r = schema_update.prepare_update(vault, "Jordan", "2026-06-21", root)
            self.assertEqual(r["mode"], "overwrite")
            self.assertTrue(r["diff_text"])
            self.assertIn("## Section C", r["merged_text"])

    def test_overwrite_fallback_when_git_unavailable(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as vd:
            root = _make_root(d)
            vault = _make_vault(vd)
            r = schema_update.prepare_update(vault, "Jordan", "2026-06-21", root, git_ok=False)
            self.assertEqual(r["mode"], "overwrite")
            self.assertEqual(r["reason"], "git unavailable")


class TestFenceAwareConflictCount(unittest.TestCase):
    def test_markers_inside_fence_ignored(self):
        text = (
            "intro\n```\n<<<<<<< not a real conflict\n=======\n>>>>>>> still inside fence\n```\nouttro\n"
        )
        self.assertEqual(schema_update.count_conflicts(text), 0)

    def test_real_conflict_outside_fence_counted(self):
        text = "intro\n<<<<<<< theirs\nmine\n=======\nyours\n>>>>>>> ours\noutro\n"
        self.assertEqual(schema_update.count_conflicts(text), 1)

    def test_mixed_only_counts_outside_fence(self):
        text = (
            "<<<<<<< real\na\n=======\nb\n>>>>>>> real\n"
            "```\n<<<<<<< fake\n```\n"
        )
        self.assertEqual(schema_update.count_conflicts(text), 1)


class TestReconstructFrontmatter(unittest.TestCase):
    def test_deterministic_fields(self):
        theirs = {"title": "Wiki Operating Schema", "type": "schema",
                  "schema_version": "0.7.0", "created": "2026-01-01",
                  "updated": "2026-03-03", "generated_by": "mneme:wiki-setup"}
        bundled = {"title": "Wiki Operating Schema", "type": "schema",
                   "schema_version": "0.8.0", "created": "{{TODAY}}",
                   "updated": "{{TODAY}}", "generated_by": "mneme:wiki-setup"}
        fm = schema_update.reconstruct_frontmatter(theirs, bundled, "2026-06-21")
        self.assertIn("schema_version: 0.8.0", fm)   # new
        self.assertIn("created: 2026-01-01", fm)     # preserved from theirs
        self.assertIn("updated: 2026-06-21", fm)     # today
        self.assertTrue(fm.startswith("---\n") and fm.endswith("---\n"))


if __name__ == "__main__":
    unittest.main()
