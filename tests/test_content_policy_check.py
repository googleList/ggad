import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "content_policy_check.py"
SPEC = importlib.util.spec_from_file_location("content_policy_check", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ContentPolicyCheckTests(unittest.TestCase):
    def test_clean_consulting_site_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text("广告管理与投放咨询", encoding="utf-8")
            self.assertEqual(MODULE.validate_repository(root), [])

    def test_legacy_account_opening_copy_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text("广告开户代投", encoding="utf-8")
            errors = MODULE.validate_repository(root)
            self.assertTrue(any("legacy account-opening phrase" in error for error in errors))

    def test_legacy_storefront_artifact_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "admin.js").write_text("const orders = [];", encoding="utf-8")
            errors = MODULE.validate_repository(root)
            self.assertIn("forbidden legacy artifact: admin.js", errors)

    def test_generated_reports_are_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports = root / "reports"
            reports.mkdir()
            (reports / "deployment-drift.md").write_text("old 开户 URL", encoding="utf-8")
            self.assertEqual(MODULE.validate_repository(root), [])


if __name__ == "__main__":
    unittest.main()
