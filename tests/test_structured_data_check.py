import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "structured_data_check.py"
SPEC = importlib.util.spec_from_file_location("structured_data_check", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def page(schema, canonical="https://example.com/guide.html", lang="en-US"):
    import json

    return (
        f'<html lang="{lang}"><head><link rel="canonical" href="{canonical}">'
        f'<script type="application/ld+json">{json.dumps(schema)}</script></head></html>'
    )


class StructuredDataCheckTests(unittest.TestCase):
    def test_valid_article_and_breadcrumb(self):
        canonical = "https://example.com/guide.html"
        schema = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "Article",
                    "headline": "Guide",
                    "image": "https://example.com/image.svg",
                    "inLanguage": "en-US",
                    "mainEntityOfPage": canonical,
                    "datePublished": "2026-09-28",
                    "dateModified": "2026-09-28",
                    "author": {"@type": "Organization", "@id": MODULE.ORGANIZATION_ID, "name": "Example", "url": MODULE.COMPANY_URL},
                    "publisher": {"@type": "Organization", "@id": MODULE.ORGANIZATION_ID, "name": "Example", "url": MODULE.COMPANY_URL, "logo": {"@type": "ImageObject", "url": "https://example.com/logo.png"}},
                },
                {
                    "@type": "BreadcrumbList",
                    "itemListElement": [{"@type": "ListItem", "position": 1, "item": canonical}],
                },
            ],
        }
        self.assertEqual(MODULE.validate_page(Path("guide.html"), page(schema)), [])

    def test_article_url_language_and_breadcrumb_must_match(self):
        schema = [
            {
                "@type": "Article",
                "headline": "Guide",
                "image": "https://example.com/image.svg",
                "inLanguage": "zh-Hant-HK",
                "mainEntityOfPage": "https://example.com/wrong.html",
                "datePublished": "2026-09-28",
                "dateModified": "2026-09-28",
                "author": {"@type": "Organization", "@id": MODULE.ORGANIZATION_ID, "url": MODULE.COMPANY_URL},
                "publisher": {"@type": "Organization", "@id": MODULE.ORGANIZATION_ID, "url": MODULE.COMPANY_URL, "logo": {"@type": "ImageObject", "url": "https://example.com/logo.png"}},
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [{"@type": "ListItem", "position": 1, "item": "https://example.com/wrong.html"}],
            },
        ]
        errors = MODULE.validate_page(Path("guide.html"), page(schema))
        self.assertTrue(any("mainEntityOfPage" in error for error in errors))
        self.assertTrue(any("inLanguage" in error for error in errors))
        self.assertTrue(any("final item" in error for error in errors))

    def test_article_headline_must_match_visible_h1(self):
        schema = {
            "@type": "Article",
            "headline": "Schema headline",
            "image": "https://example.com/image.png",
            "inLanguage": "en-US",
            "mainEntityOfPage": "https://example.com/guide.html",
            "datePublished": "2026-09-29",
            "dateModified": "2026-09-29",
            "author": {"@type": "Organization", "@id": MODULE.ORGANIZATION_ID, "name": "Example", "url": MODULE.COMPANY_URL},
            "publisher": {"@type": "Organization", "@id": MODULE.ORGANIZATION_ID, "name": "Example", "url": MODULE.COMPANY_URL, "logo": {"@type": "ImageObject", "url": "https://example.com/logo.png"}},
        }
        html = page(schema).replace("</html>", "<body><h1>Visible headline</h1></body></html>")
        errors = MODULE.validate_page(Path("guide.html"), html)
        self.assertTrue(any("headline does not match" in error for error in errors))

    def test_article_organization_entities_must_be_canonical(self):
        schema = {
            "@type": "Article",
            "headline": "Guide",
            "image": "https://example.com/image.png",
            "inLanguage": "en-US",
            "mainEntityOfPage": "https://example.com/guide.html",
            "datePublished": "2026-09-29",
            "dateModified": "2026-09-29",
            "author": {"@type": "Organization", "name": "Example", "url": "https://shumaojs.com/"},
            "publisher": {"@type": "Organization", "name": "Example"},
        }
        errors = MODULE.validate_page(Path("guide.html"), page(schema))
        self.assertTrue(any("author must reference" in error for error in errors))
        self.assertTrue(any("publisher must reference" in error for error in errors))
        self.assertTrue(any("publisher must include a logo" in error for error in errors))

    def test_article_dates_must_be_truthful_and_ordered(self):
        schema = {
            "@type": "Article",
            "headline": "Guide",
            "image": "https://example.com/image.png",
            "inLanguage": "en-US",
            "mainEntityOfPage": "https://example.com/guide.html",
            "datePublished": "2999-09-29",
            "dateModified": "2026-09-28",
            "author": {"@type": "Organization", "@id": MODULE.ORGANIZATION_ID, "name": "Example", "url": MODULE.COMPANY_URL},
            "publisher": {"@type": "Organization", "@id": MODULE.ORGANIZATION_ID, "name": "Example", "url": MODULE.COMPANY_URL, "logo": {"@type": "ImageObject", "url": "https://example.com/logo.png"}},
        }
        errors = MODULE.validate_page(Path("guide.html"), page(schema))
        self.assertTrue(any("datePublished cannot be in the future" in error for error in errors))
        self.assertTrue(any("dateModified cannot be earlier" in error for error in errors))

    def test_unverified_rating_markup_is_rejected(self):
        schema = {
            "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": 1, "item": "https://example.com/guide.html"}],
            "aggregateRating": {"@type": "AggregateRating", "ratingValue": "5"},
        }
        errors = MODULE.validate_page(Path("guide.html"), page(schema))
        self.assertTrue(any("aggregateRating" in error for error in errors))

    def test_collection_page_requires_consecutive_unique_items(self):
        schema = {
            "@type": "CollectionPage",
            "mainEntity": {
                "@type": "ItemList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "url": "https://example.com/a"},
                    {"@type": "ListItem", "position": 3, "url": "https://example.com/a"},
                ],
            },
        }
        errors = MODULE.validate_page(Path("index.html"), page(schema))
        self.assertTrue(any("positions must be unique and consecutive" in error for error in errors))
        self.assertTrue(any("duplicate URLs" in error for error in errors))

    def test_valid_collection_page_passes(self):
        schema = {
            "@type": "CollectionPage",
            "mainEntity": {
                "@type": "ItemList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "url": "https://example.com/a"},
                    {"@type": "ListItem", "position": 2, "url": "https://example.com/b"},
                ],
            },
        }
        self.assertEqual(MODULE.validate_page(Path("index.html"), page(schema)), [])

    def test_product_schema_is_rejected(self):
        schema = {
            "@type": "Product",
            "name": "Legacy product",
            "offers": {"@type": "Offer", "price": "99", "priceCurrency": "USD"},
        }
        errors = MODULE.validate_page(Path("index.html"), page(schema))
        self.assertTrue(any("includes Product markup" in error for error in errors))

    def test_nested_product_schema_is_rejected(self):
        schema = {
            "@type": "WebPage",
            "mainEntity": {"@type": "Product", "name": "Legacy product"},
        }
        errors = MODULE.validate_page(Path("index.html"), page(schema))
        self.assertTrue(any("includes Product markup" in error for error in errors))

    def test_web_application_offer_is_rejected(self):
        schema = {
            "@type": "WebApplication",
            "name": "Free checklist",
            "url": "https://example.com/guide.html",
            "inLanguage": "en-US",
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        }
        errors = MODULE.validate_page(Path("index.html"), page(schema))
        self.assertTrue(any("must not expose Offer" in error for error in errors))
        self.assertTrue(any("isAccessibleForFree" in error for error in errors))

    def test_service_provider_must_reference_canonical_organization(self):
        schema = {
            "@type": "Service",
            "provider": {"@type": "Organization", "url": "https://shumaojs.com/"},
        }
        errors = MODULE.validate_page(Path("index.html"), page(schema))
        self.assertTrue(any("provider must reference" in error for error in errors))

    def test_valid_web_application_provider_passes(self):
        schema = {
            "@type": "WebApplication",
            "name": "Free checklist",
            "url": "https://example.com/guide.html",
            "inLanguage": "en-US",
            "isAccessibleForFree": True,
            "provider": {
                "@type": "Organization",
                "@id": MODULE.ORGANIZATION_ID,
                "url": MODULE.COMPANY_URL,
            },
        }
        self.assertEqual(MODULE.validate_page(Path("index.html"), page(schema)), [])

    def test_professional_service_requires_verified_identity_fields(self):
        schema = {
            "@type": "ProfessionalService",
            "@id": MODULE.ORGANIZATION_ID,
            "name": "Example",
            "url": "https://example.com/guide.html",
            "identifier": "123",
            "address": {"@type": "PostalAddress", "addressCountry": "CN"},
            "areaServed": [{"@type": "Country", "name": "United States"}],
        }
        errors = MODULE.validate_page(Path("index.html"), page(schema))
        self.assertTrue(any("legalName" in error for error in errors))
        self.assertTrue(any("taxID" in error for error in errors))

    def test_valid_professional_service_passes(self):
        schema = {
            "@type": "ProfessionalService",
            "@id": MODULE.ORGANIZATION_ID,
            "name": "Example",
            "legalName": "Example Company Limited",
            "url": "https://example.com/guide.html",
            "identifier": "123",
            "taxID": "123",
            "address": {"@type": "PostalAddress", "addressCountry": "CN"},
            "areaServed": [{"@type": "Country", "name": "United States"}],
        }
        self.assertEqual(MODULE.validate_page(Path("index.html"), page(schema)), [])


if __name__ == "__main__":
    unittest.main()
