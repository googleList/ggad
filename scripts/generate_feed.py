#!/usr/bin/env python3
"""Generate a deterministic RSS feed from validated Article JSON-LD."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

try:
    from structured_data_check import ROOT, SchemaParser, flatten_schema, schema_types
except ModuleNotFoundError:  # Imported as scripts.generate_feed by tests.
    from scripts.structured_data_check import ROOT, SchemaParser, flatten_schema, schema_types


FEED_PATH = ROOT / "feed.xml"
ATOM_NS = "http://www.w3.org/2005/Atom"
DC_NS = "http://purl.org/dc/elements/1.1/"
ElementTree.register_namespace("atom", ATOM_NS)
ElementTree.register_namespace("dc", DC_NS)


def article_schema(path: Path) -> dict[str, Any] | None:
    parser = SchemaParser()
    parser.feed(path.read_text(encoding="utf-8"))
    for block in parser.blocks:
        parsed = json.loads(block)
        for schema in flatten_schema(parsed):
            if "Article" in schema_types(schema):
                return schema
    return None


def collect_articles(root: Path = ROOT) -> list[dict[str, str]]:
    articles = []
    for path in sorted((root / "articles").glob("*.html")):
        schema = article_schema(path)
        if not schema:
            continue
        articles.append(
            {
                "title": str(schema["headline"]),
                "description": str(schema["description"]),
                "url": str(schema["mainEntityOfPage"]),
                "published": str(schema["datePublished"]),
                "modified": str(schema["dateModified"]),
                "language": str(schema.get("inLanguage", "zh-CN")),
                "category": str(schema.get("articleSection", "Marketing")),
            }
        )
    return sorted(articles, key=lambda item: (item["modified"], item["url"]), reverse=True)


def rfc_date(value: str) -> str:
    parsed = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return format_datetime(parsed)


def build_feed(articles: list[dict[str, str]]) -> bytes:
    rss = ElementTree.Element("rss", {"version": "2.0"})
    channel = ElementTree.SubElement(rss, "channel")
    ElementTree.SubElement(channel, "title").text = "振润达广告投放与SEO文章"
    ElementTree.SubElement(channel, "link").text = "https://shumaojs.com/articles.html"
    ElementTree.SubElement(channel, "description").text = (
        "Google Ads、SEM、SEO、建站、GEO、转化追踪与广告管理文章。"
    )
    ElementTree.SubElement(channel, "language").text = "zh-CN"
    ElementTree.SubElement(channel, "lastBuildDate").text = rfc_date(
        max((item["modified"] for item in articles), default="2026-09-29")
    )
    ElementTree.SubElement(
        channel,
        f"{{{ATOM_NS}}}link",
        {"href": "https://shumaojs.com/feed.xml", "rel": "self", "type": "application/rss+xml"},
    )
    for article in articles:
        item = ElementTree.SubElement(channel, "item")
        ElementTree.SubElement(item, "title").text = article["title"]
        ElementTree.SubElement(item, "link").text = article["url"]
        ElementTree.SubElement(item, "guid", {"isPermaLink": "true"}).text = article["url"]
        ElementTree.SubElement(item, "description").text = article["description"]
        ElementTree.SubElement(item, "pubDate").text = rfc_date(article["published"])
        ElementTree.SubElement(item, "category").text = article["category"]
        ElementTree.SubElement(item, f"{{{DC_NS}}}language").text = article["language"]
    ElementTree.indent(rss, space="  ")
    return ElementTree.tostring(rss, encoding="utf-8", xml_declaration=True) + b"\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if feed.xml is missing or stale.")
    args = parser.parse_args()
    articles = collect_articles()
    expected = build_feed(articles)
    if args.check:
        if not FEED_PATH.exists() or FEED_PATH.read_bytes() != expected:
            print("ERROR: feed.xml is missing or stale; run python scripts/generate_feed.py")
            return 1
        print(f"RSS feed is current with {len(articles)} article(s).")
        return 0
    FEED_PATH.write_bytes(expected)
    print(f"Generated feed.xml with {len(articles)} article(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
