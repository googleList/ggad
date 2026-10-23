import sys
import unittest
from datetime import date
from pathlib import Path
from xml.etree import ElementTree
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from seo_quality_check import validate_sitemap_metadata  # noqa: E402


def sitemap(entries: str) -> ElementTree.Element:
    return ElementTree.fromstring(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{entries}</urlset>"
    )


class SitemapMetadataTests(unittest.TestCase):
    def test_default_sitemap_day_uses_the_editorial_calendar(self) -> None:
        root = sitemap("<url><loc>https://shumaojs.com/</loc><lastmod>2026-10-24</lastmod></url>")
        with patch("seo_quality_check.editorial_today", return_value=date(2026, 10, 24)):
            self.assertEqual(validate_sitemap_metadata(root), [])
        future = sitemap("<url><loc>https://shumaojs.com/</loc><lastmod>2026-10-25</lastmod></url>")
        with patch("seo_quality_check.editorial_today", return_value=date(2026, 10, 24)):
            self.assertTrue(any("future lastmod" in error for error in validate_sitemap_metadata(future)))

    def test_valid_unique_urls_and_dates_pass(self) -> None:
        root = sitemap(
            "<url><loc>https://shumaojs.com/</loc><lastmod>2026-09-29</lastmod></url>"
            "<url><loc>https://shumaojs.com/guide.html</loc><lastmod>2026-09-28</lastmod></url>"
        )
        self.assertEqual(validate_sitemap_metadata(root, date(2026, 9, 29)), [])

    def test_duplicate_missing_invalid_and_future_values_fail(self) -> None:
        root = sitemap(
            "<url><loc>https://shumaojs.com/</loc><lastmod>2026-09-30</lastmod></url>"
            "<url><loc>https://shumaojs.com/</loc><lastmod>not-a-date</lastmod></url>"
            "<url><loc>https://shumaojs.com/missing.html</loc></url>"
        )
        errors = validate_sitemap_metadata(root, date(2026, 9, 29))
        self.assertTrue(any("duplicate URL" in error for error in errors))
        self.assertTrue(any("future lastmod" in error for error in errors))
        self.assertTrue(any("invalid lastmod" in error for error in errors))
        self.assertTrue(any("missing lastmod" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
