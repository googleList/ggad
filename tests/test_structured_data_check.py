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
    def test_editorial_calendar_is_independent_of_utc_runner_day(self):
        from datetime import date, datetime, timezone

        self.assertEqual(MODULE.editorial_today(datetime(2026, 10, 23, 15, 59, tzinfo=timezone.utc)), date(2026, 10, 23))
        self.assertEqual(MODULE.editorial_today(datetime(2026, 10, 23, 16, 30, tzinfo=timezone.utc)), date(2026, 10, 24))

    def test_zoned_article_dates_compare_instants_without_allowing_future_times(self):
        from datetime import datetime, timezone

        now = datetime(2026, 10, 23, 16, 30, tzinfo=timezone.utc)
        schema = {"@type": "Article", "datePublished": "2026-09-11", "dateModified": "2026-10-24T00:20:55+08:00"}
        errors = MODULE.validate_page(Path("guide.html"), page(schema), now=now)
        self.assertFalse(any("future" in error for error in errors))
        schema["dateModified"] = "2026-10-24T01:00:00+08:00"
        self.assertTrue(any("dateModified cannot be in the future" in error for error in MODULE.validate_page(Path("guide.html"), page(schema), now=now)))
        schema["dateModified"] = "2026-10-24"
        self.assertFalse(any("future" in error for error in MODULE.validate_page(Path("guide.html"), page(schema), now=now)))
        schema["dateModified"] = "2026-10-25"
        self.assertTrue(any("future" in error for error in MODULE.validate_page(Path("guide.html"), page(schema), now=now)))

    def test_article_date_precision_and_timezone(self):
        from datetime import date, datetime

        self.assertEqual(MODULE.parse_article_date("2026-09-11"), date(2026, 9, 11))
        for value in ("2026-10-20T16:21:48+08:00", "2026-10-20T08:21:48Z"):
            with self.subTest(value=value):
                self.assertIsInstance(MODULE.parse_article_date(value), datetime)
                self.assertIsNotNone(MODULE.parse_article_date(value).utcoffset())
        for value in ("2026-02-30", "2026-10-20T16:21:48", "2026-10-20T16:21:48+00:60", "bad-date"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                MODULE.parse_article_date(value)

    def test_article_date_validation_handles_invalid_calendar_and_datetime_order(self):
        schema = {
            "@type": "Article",
            "datePublished": "2026-02-30",
            "dateModified": "2026-10-20T16:21:48",
        }
        errors = MODULE.validate_page(Path("guide.html"), page(schema))
        self.assertTrue(any("datePublished must use a valid" in error for error in errors))
        self.assertTrue(any("dateModified must use a valid" in error for error in errors))
        schema.update(datePublished="2026-10-19T18:00:00Z", dateModified="2026-10-20T01:00:00+08:00")
        errors = MODULE.validate_page(Path("guide.html"), page(schema))
        self.assertTrue(any("dateModified cannot be earlier" in error for error in errors))
        schema.update(datePublished="2026-10-20", dateModified="2026-10-20T01:00:00+08:00")
        errors = MODULE.validate_page(Path("guide.html"), page(schema))
        self.assertFalse(any("dateModified cannot be earlier" in error for error in errors))
        schema.update(datePublished="2026-10-20", dateModified="2026-10-19T18:00:00Z")
        errors = MODULE.validate_page(Path("guide.html"), page(schema))
        self.assertFalse(any("dateModified cannot be earlier" in error for error in errors))

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

    def test_professional_service_retains_required_local_identity_fields(self):
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
        self.assertFalse(any("taxID" in error for error in errors))

    def test_professional_service_does_not_require_registration_numbers(self):
        schema = {
            "@type": "ProfessionalService",
            "@id": MODULE.ORGANIZATION_ID,
            "name": "Example",
            "legalName": "Example Company Limited",
            "url": "https://example.com/guide.html",
            "address": {"@type": "PostalAddress", "addressCountry": "CN"},
            "areaServed": [{"@type": "Country", "name": "United States"}],
        }
        self.assertEqual(MODULE.validate_page(Path("index.html"), page(schema)), [])

    def test_public_organization_withholds_unconfirmed_registration_fields(self):
        import json

        def nodes(value):
            if isinstance(value, dict):
                yield value
                for child in value.values():
                    yield from nodes(child)
            elif isinstance(value, list):
                for child in value:
                    yield from nodes(child)

        root = Path(__file__).parents[1]
        definitions = []
        for source in list(root.glob("*.html")) + list((root / "articles").glob("*.html")):
            parser = MODULE.SchemaParser()
            parser.feed(source.read_text(encoding="utf-8"))
            for block in parser.blocks:
                for node in nodes(json.loads(block)):
                    if node.get("@id") == MODULE.ORGANIZATION_ID:
                        definitions.append(node)
                        for field in ("identifier", "taxID", "vatID", "foundingDate"):
                            self.assertNotIn(field, node, f"{source.name}: owner withdrew unconfirmed {field}")
        self.assertGreater(len(definitions), 1)

    def test_withdrawn_registration_is_not_retained_in_visible_pages(self):
        root = Path(__file__).parents[1]
        for name in ("index.html", "company.html"):
            source = (root / name).read_text(encoding="utf-8")
            self.assertNotIn("91530103MACQG57N6E", source)
            self.assertNotIn("统一社会信用代码", source)
        company = (root / "company.html").read_text(encoding="utf-8")
        self.assertNotIn("company-verification", company)
        for label in ("企业类型", "成立日期", "登记机关"):
            self.assertNotIn(label, company)

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
