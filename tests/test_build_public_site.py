import sys
import json
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from build_public_site import PUBLIC_DATA, PUBLIC_FILES, build_public_site


class PublicSiteBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "repo"
        self.root.mkdir()
        for name in (*PUBLIC_FILES, *PUBLIC_DATA):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("public", encoding="utf-8")
        (self.root / "index.html").write_text('<html><link rel="stylesheet" href="styles.css"></html>', encoding="utf-8")

    def test_only_public_files_and_referenced_assets_are_staged(self):
        for name in ("assets/logo.svg", "articles/guide.html", "reports/private.html", "scripts/tool.py",
                     "tests/test.py", "data/seo-keywords.json", "data/collected-articles.json", ".git/config"):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("fixture", encoding="utf-8")
        output = self.base / "public"
        files = build_public_site(self.root, output)
        self.assertIn("assets/logo.svg", files)
        self.assertIn("articles/guide.html", files)
        self.assertIn("data/ad-learning.json", files)
        self.assertFalse((output / "reports").exists())
        self.assertFalse((output / "scripts").exists())
        self.assertFalse((output / "tests").exists())
        self.assertFalse((output / ".git").exists())
        self.assertFalse((output / "data/seo-keywords.json").exists())
        self.assertFalse((output / "data/collected-articles.json").exists())
        self.assertEqual((self.root / "index.html").read_bytes(), (output / "index.html").read_bytes())

    def test_missing_reference_blocks_deployment(self):
        (self.root / "index.html").write_text('<a href="reports/private.html">Private</a>', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unpublished reference"):
            build_public_site(self.root, self.base / "public")

    def test_revision_marker_records_actual_checkout(self):
        output = self.base / "public"
        revision = "a" * 40
        files = build_public_site(self.root, output, revision)
        self.assertIn("deployment.json", files)
        self.assertEqual(json.loads((output / "deployment.json").read_text(encoding="utf-8")), {"revision": revision})

    def test_invalid_revision_is_rejected_before_writing(self):
        output = self.base / "public"
        with self.assertRaisesRegex(ValueError, "complete lowercase Git SHA"):
            build_public_site(self.root, output, "not-a-sha")
        self.assertFalse(output.exists())

    def test_missing_required_file_is_not_silently_omitted(self):
        (self.root / "robots.txt").unlink()
        with self.assertRaisesRegex(ValueError, "missing public files"):
            build_public_site(self.root, self.base / "public")

    def test_unpublished_stylesheet_reference_is_rejected(self):
        (self.root / "index.html").write_text('<link rel="stylesheet" href="extra.css">', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unpublished reference"):
            build_public_site(self.root, self.base / "public")

    def test_output_cannot_be_inside_or_above_the_repository(self):
        for output in (self.root, self.root / "_site", self.base):
            with self.assertRaisesRegex(ValueError, "outside the repository"):
                build_public_site(self.root, output)

    def test_existing_files_are_never_deleted_or_overwritten(self):
        output = self.base / "public"
        output.mkdir()
        sentinel = output / "keep.txt"
        sentinel.write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "new or empty"):
            build_public_site(self.root, output)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_reference_cannot_escape_public_root(self):
        (self.root / "index.html").write_text('<a href="../outside.html">Outside</a>', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "escapes artifact"):
            build_public_site(self.root, self.base / "public")

    def test_symlink_public_file_is_rejected(self):
        source = self.root / "styles.css"
        source.unlink()
        target = self.base / "outside.css"
        target.write_text("outside", encoding="utf-8")
        try:
            source.symlink_to(target)
        except OSError:
            self.skipTest("symlink creation is not available")
        with self.assertRaisesRegex(ValueError, "escapes repository"):
            build_public_site(self.root, self.base / "public")


if __name__ == "__main__":
    unittest.main()
