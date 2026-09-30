import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from seo_quality_check import (  # noqa: E402
    PageParser,
    validate_hreflang,
    validate_social_image,
    validate_unique_metadata,
)


class HreflangQualityTests(unittest.TestCase):
    @staticmethod
    def page(alternates: dict[str, str], language: str) -> PageParser:
        parser = PageParser()
        parser.hreflang = alternates
        parser.lang = language
        return parser

    def test_valid_reciprocal_cluster(self) -> None:
        en = "https://shumaojs.com/en.html"
        hk = "https://shumaojs.com/hk.html"
        pages = {
            en: ("en.html", self.page({"en-us": en, "zh-hant-hk": hk}, "en-US")),
            hk: ("hk.html", self.page({"en-us": en, "zh-hant-hk": hk}, "zh-Hant-HK")),
        }
        self.assertEqual(validate_hreflang(pages), [])

    def test_missing_self_reference_is_rejected(self) -> None:
        en = "https://shumaojs.com/en.html"
        hk = "https://shumaojs.com/hk.html"
        pages = {
            en: ("en.html", self.page({"zh-hant-hk": hk}, "en-US")),
            hk: ("hk.html", self.page({"en-us": en, "zh-hant-hk": hk}, "zh-Hant-HK")),
        }
        errors = validate_hreflang(pages)
        self.assertTrue(any("missing a self-reference" in error for error in errors))

    def test_missing_return_link_is_rejected(self) -> None:
        en = "https://shumaojs.com/en.html"
        hk = "https://shumaojs.com/hk.html"
        pages = {
            en: ("en.html", self.page({"en-us": en, "zh-hant-hk": hk}, "en-US")),
            hk: ("hk.html", self.page({"zh-hant-hk": hk}, "zh-Hant-HK")),
        }
        errors = validate_hreflang(pages)
        self.assertTrue(any("does not return-link" in error for error in errors))

    def test_language_mismatch_is_rejected(self) -> None:
        en = "https://shumaojs.com/en.html"
        hk = "https://shumaojs.com/hk.html"
        pages = {
            en: ("en.html", self.page({"en-us": en, "zh-hant-hk": hk}, "en-US")),
            hk: ("hk.html", self.page({"en-us": en, "zh-hans-cn": hk}, "zh-Hant-HK")),
        }
        errors = validate_hreflang(pages)
        self.assertTrue(any("does not match target language" in error for error in errors))


class MetadataUniquenessTests(unittest.TestCase):
    @staticmethod
    def page(title: str, description: str) -> PageParser:
        parser = PageParser()
        parser.title_parts = [title]
        parser.description = description
        return parser

    def test_unique_metadata_passes(self) -> None:
        pages = {
            "https://shumaojs.com/us.html": (
                "us.html",
                self.page("US Google Ads management", "Campaign management for US businesses."),
            ),
            "https://shumaojs.com/hk.html": (
                "hk.html",
                self.page("香港 Google Ads 管理", "面向香港企業的廣告管理服務。"),
            ),
        }
        self.assertEqual(validate_unique_metadata(pages), [])

    def test_duplicate_title_and_description_are_rejected(self) -> None:
        pages = {
            "https://shumaojs.com/one.html": (
                "one.html",
                self.page("Google Ads guide", "A practical advertising guide."),
            ),
            "https://shumaojs.com/two.html": (
                "two.html",
                self.page("google ads guide", "  A practical   advertising guide. "),
            ),
        }
        errors = validate_unique_metadata(pages)
        self.assertTrue(any("duplicate title" in error for error in errors))
        self.assertTrue(any("duplicate meta description" in error for error in errors))


class SocialImageTests(unittest.TestCase):
    def test_svg_social_image_is_rejected(self) -> None:
        errors = validate_social_image(
            "guide.html", "og:image", "https://shumaojs.com/assets/og-cover.svg"
        )
        self.assertTrue(any("rather than SVG" in error for error in errors))

    def test_missing_social_image_is_rejected(self) -> None:
        self.assertTrue(validate_social_image("guide.html", "twitter:image", ""))

    def test_existing_png_social_image_passes(self) -> None:
        self.assertEqual(
            validate_social_image(
                "guide.html", "og:image", "https://shumaojs.com/assets/og-cover.png"
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
