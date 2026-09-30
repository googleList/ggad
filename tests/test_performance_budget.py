import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from performance_budget_check import audit  # noqa: E402


BASE_CSS = """
.brand img { width: 42px; height: 42px; }
.home-guide img { aspect-ratio: 16 / 9; }
.photo-frame img { aspect-ratio: 1.05; }
.policy-image img { aspect-ratio: 1.15; }
.article-thumb img { aspect-ratio: 16 / 9; }
.managed-visual img { aspect-ratio: 16 / 10; }
.ad-type-card img { aspect-ratio: 16 / 9; }
"""

BASE_JS = """
iconStylesheet.media = "print";
iconStylesheet.media = "all";
"""


class PerformanceBudgetTests(unittest.TestCase):
    def fixture(self, html: str, css: str = BASE_CSS) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        root.joinpath("styles.css").write_text(css, encoding="utf-8")
        root.joinpath("script.js").write_text(BASE_JS, encoding="utf-8")
        root.joinpath("index.html").write_text(
            '<script src="script.js" defer></script>' + html, encoding="utf-8"
        )
        return root

    def test_versioned_local_script_name_passes(self) -> None:
        root = self.fixture('<img src="logo.svg" alt="Brand">')
        root.joinpath("script.js").rename(root / "site-v2.js")
        root.joinpath("index.html").write_text(
            '<script src="site-v2.js" defer></script><img src="logo.svg" alt="Brand">',
            encoding="utf-8",
        )
        self.assertEqual(audit(root), [])

    def test_missing_referenced_script_fails(self) -> None:
        root = self.fixture('<img src="logo.svg" alt="Brand">')
        root.joinpath("script.js").unlink()
        self.assertTrue(any("is missing" in error for error in audit(root)))

    def test_valid_external_image_passes(self) -> None:
        root = self.fixture(
            '<img src="https://example.com/hero.jpg" alt="Team planning" '
            'width="1200" height="800" decoding="async" fetchpriority="high">'
        )
        self.assertEqual(audit(root), [])

    def test_external_image_without_dimensions_fails(self) -> None:
        root = self.fixture(
            '<img src="https://example.com/hero.jpg" alt="Team planning" decoding="async">'
        )
        errors = audit(root)
        self.assertTrue(any("needs width and height" in error for error in errors))

    def test_unsplash_image_requires_responsive_sources(self) -> None:
        root = self.fixture(
            '<img src="https://images.unsplash.com/photo-1?w=1200" alt="Team planning" '
            'width="1200" height="800" decoding="async">'
        )
        errors = audit(root)
        self.assertTrue(any("needs responsive srcset and sizes" in error for error in errors))

    def test_responsive_unsplash_image_passes(self) -> None:
        root = self.fixture(
            '<img src="https://images.unsplash.com/photo-1?w=1200" '
            'srcset="https://images.unsplash.com/photo-1?w=480 480w, '
            'https://images.unsplash.com/photo-1?w=640 640w, '
            'https://images.unsplash.com/photo-1?w=1200 1200w" sizes="100vw" '
            'alt="Team planning" width="1200" height="800" decoding="async">'
        )
        self.assertEqual(audit(root), [])

    def test_unsplash_image_requires_mid_mobile_candidate(self) -> None:
        root = self.fixture(
            '<img src="https://images.unsplash.com/photo-1?w=1200" '
            'srcset="https://images.unsplash.com/photo-1?w=480 480w, '
            'https://images.unsplash.com/photo-1?w=1200 1200w" sizes="100vw" '
            'alt="Team planning" width="1200" height="800" decoding="async">'
        )
        errors = audit(root)
        self.assertTrue(any("560-700px mobile candidate" in error for error in errors))

    def test_blocking_css_import_fails(self) -> None:
        root = self.fixture('<img src="logo.svg" alt="Brand">', '@import url("x.css");\n' + BASE_CSS)
        errors = audit(root)
        self.assertTrue(any("render-blocking @import" in error for error in errors))

    def test_unstable_critical_image_rule_fails(self) -> None:
        root = self.fixture('<img src="logo.svg" alt="Brand">', BASE_CSS.replace("aspect-ratio: 16 / 9", "object-fit: cover", 1))
        errors = audit(root)
        self.assertTrue(any("does not reserve a stable image box" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
