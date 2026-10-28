#!/usr/bin/env python3
"""Check the site's article-only RSS contract against its mixed article/tool hub."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse
from xml.etree import ElementTree

try:
    from article_index import parse_index, validate_article_index
    from generate_feed import collect_articles
    from structured_data_check import ROOT, SchemaParser, flatten_schema, schema_types
except ModuleNotFoundError:
    from scripts.article_index import parse_index, validate_article_index
    from scripts.generate_feed import collect_articles
    from scripts.structured_data_check import ROOT, SchemaParser, flatten_schema, schema_types


ORIGIN = "https://shumaojs.com"
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def check_coverage(root: Path = ROOT) -> dict:
    root = root.resolve()
    source = (root / "articles.html").read_text(encoding="utf-8")
    index = parse_index(source)
    errors = validate_article_index(source)
    article_urls = {item["url"] for item in collect_articles(root)}
    listed_urls = [urljoin(index.canonical, card["href"]) for card in index.cards]
    feed = ElementTree.parse(root / "feed.xml")
    feed_urls = [item.findtext("link", default="").strip() for item in feed.findall("channel/item")]
    sitemap = ElementTree.parse(root / "sitemap.xml")
    sitemap_urls = {node.text.strip() for node in sitemap.findall("sm:url/sm:loc", SITEMAP_NS) if node.text}
    tools = []
    if index.canonical != ORIGIN + "/articles.html":
        errors.append("Article hub has an unexpected canonical URL")
    if len(feed_urls) != len(set(feed_urls)):
        errors.append("RSS has duplicate item URLs")
    for url in sorted(article_urls - set(listed_urls)):
        errors.append(f"Article missing from hub: {url}")
    for url in sorted(article_urls - set(feed_urls)):
        errors.append(f"Article missing from RSS: {url}")
    for url in sorted(set(feed_urls) - article_urls):
        errors.append(f"RSS item is not an editorial Article: {url}")
    for url in listed_urls:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "shumaojs.com" or parsed.query or parsed.fragment:
            errors.append(f"Hub item needs a local canonical HTTPS URL: {url}")
            continue
        target = (root / unquote(parsed.path).lstrip("/")).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            errors.append(f"Hub item has no safe local file: {url}")
            continue
        page = SchemaParser()
        page.feed(target.read_text(encoding="utf-8"))
        schemas = [schema for block in page.blocks for schema in flatten_schema(json.loads(block))]
        types = {kind for schema in schemas for kind in schema_types(schema)}
        if page.canonical != url:
            errors.append(f"Hub item differs from target canonical: {url}")
        if "noindex" in page.robots:
            errors.append(f"Hub lists a noindex page: {url}")
        if url not in sitemap_urls:
            errors.append(f"Hub item missing from sitemap: {url}")
        if url in article_urls:
            if "Article" not in types:
                errors.append(f"Editorial page has no Article schema: {url}")
        elif "WebApplication" in types and "Article" not in types:
            tools.append(url)
        else:
            errors.append(f"Non-editorial hub item is not a declared WebApplication: {url}")
    return {"articles": len(article_urls), "hubItems": len(listed_urls), "rssItems": len(feed_urls),
            "toolItems": tools, "sitemapUrls": len(sitemap_urls), "errors": errors}


def main() -> int:
    try:
        result = check_coverage()
    except (OSError, ValueError, KeyError, TypeError, ElementTree.ParseError) as exc:
        print(f"Discovery coverage could not be checked: {exc}")
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(bool(result["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
