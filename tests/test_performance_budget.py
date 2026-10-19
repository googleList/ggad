import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from performance_budget_check import audit, audit_icon_assets  # noqa: E402


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

    def test_bounded_hero_cannot_use_viewport_width_column(self) -> None:
        css = BASE_CSS + "\n.hero { grid-template-columns: 1fr minmax(320px, 42vw); }"
        errors = audit(self.fixture('<img src="logo.svg" alt="Brand">', css))
        self.assertTrue(any("bounded container" in error for error in errors))

    def icon_fixture(self) -> Path:
        root = self.fixture('<img src="logo.svg" alt="Brand">')
        directory = root / "assets" / "icons"
        directory.mkdir(parents=True)
        font = b"wOF2-test-font"
        (directory / "tabler-subset-v1.woff2").write_bytes(font)
        (directory / "tabler-subset-v1.css").write_text(
            '.ti-home:before{content:"\\eac1"}', encoding="utf-8"
        )
        (directory / "manifest.json").write_text(json.dumps({
            "subsetFontBytes": len(font),
            "subsetFontSha256": hashlib.sha256(font).hexdigest(),
            "glyphs": {"home": "eac1"},
        }), encoding="utf-8")
        return root

    def test_local_icon_subset_passes(self) -> None:
        self.assertEqual(audit_icon_assets(self.icon_fixture(), "assets/icons/tabler-subset-v1.css"), [])

    def test_full_external_icon_font_fails(self) -> None:
        root = self.icon_fixture()
        errors = audit_icon_assets(root, "https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.46.0")
        self.assertTrue(any("full external icon font" in error for error in errors))

    def test_missing_icon_glyph_mapping_fails(self) -> None:
        root = self.icon_fixture()
        (root / "assets/icons/tabler-subset-v1.css").write_text("", encoding="utf-8")
        errors = audit_icon_assets(root, "assets/icons/tabler-subset-v1.css")
        self.assertTrue(any("glyph mapping: home" in error for error in errors))

    def test_corrupt_or_oversized_icon_font_fails(self) -> None:
        root = self.icon_fixture()
        (root / "assets/icons/tabler-subset-v1.woff2").write_bytes(b"x" * 15000)
        errors = audit_icon_assets(root, "assets/icons/tabler-subset-v1.css")
        self.assertTrue(any("exceed" in error for error in errors))
        self.assertTrue(any("does not match" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
