#!/usr/bin/env python3
"""Fail CI on objective, local SEO integrity errors for the static site."""

from __future__ import annotations

import json
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
SITE_ORIGIN = "https://shumaojs.com"
EXCLUDED_DIRS = {".git", ".audit-shots", "reports"}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang = ""
        self.title_parts: list[str] = []
        self.description = ""
        self.robots = ""
        self.canonical = ""
        self.og_image = ""
        self.twitter_image = ""
        self.hreflang: dict[str, str] = {}
        self.h1_count = 0
        self.local_targets: list[str] = []
        self.jsonld_parts: list[list[str]] = []
        self._in_title = False
        self._jsonld: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        tag = tag.lower()
        if tag == "html":
            self.lang = values.get("lang", "").strip()
        elif tag == "title":
            self._in_title = True
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "meta":
            name = values.get("name", "").lower()
            property_name = values.get("property", "").lower()
            if name == "description":
                self.description = values.get("content", "").strip()
            elif name == "robots":
                self.robots = values.get("content", "").lower()
            elif name == "twitter:image":
                self.twitter_image = values.get("content", "").strip()
            if property_name == "og:image":
                self.og_image = values.get("content", "").strip()
        elif tag == "link":
            rel_values = values.get("rel", "").lower().split()
            if "canonical" in rel_values:
                self.canonical = values.get("href", "").strip()
            if "alternate" in rel_values and values.get("hreflang"):
                language = values["hreflang"].strip().lower()
                self.hreflang[language] = values.get("href", "").strip()
        elif tag in {"a", "img", "script", "link"}:
            target = values.get("href") or values.get("src")
            if target:
                self.local_targets.append(target.strip())

        if tag == "script" and values.get("type", "").lower() == "application/ld+json":
            self._jsonld = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
        elif tag == "script" and self._jsonld is not None:
            self.jsonld_parts.append(self._jsonld)
            self._jsonld = None

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        if self._jsonld is not None:
            self._jsonld.append(data)

    @property
    def title(self) -> str:
        return " ".join("".join(self.title_parts).split())


def html_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.html")
        if not any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts)
    )


def canonical_to_sitemap_url(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    return f"{SITE_ORIGIN}/" if relative == "index.html" else f"{SITE_ORIGIN}/{relative}"


def resolve_local_target(page: Path, target: str) -> Path | None:
    if target.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
        return None
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc:
        return None
    clean = parsed.path
    if not clean:
        return None
    if clean.startswith("/"):
        candidate = ROOT / clean.lstrip("/")
    else:
        candidate = page.parent / clean
    if clean.endswith("/"):
        candidate = candidate / "index.html"
    return candidate.resolve()


def validate_hreflang(
    parsed_pages: dict[str, tuple[str, PageParser]],
) -> list[str]:
    errors: list[str] = []
    for source_url, (relative, parser) in parsed_pages.items():
        if not parser.hreflang:
            continue
        if source_url not in parser.hreflang.values():
            errors.append(f"{relative}: hreflang cluster is missing a self-reference")
        for language, target_url in parser.hreflang.items():
            target = parsed_pages.get(target_url)
            if target is None:
                errors.append(
                    f"{relative}: hreflang {language!r} points to a missing or non-canonical page {target_url!r}"
                )
                continue
            target_relative, target_parser = target
            if language != "x-default" and language != target_parser.lang.lower():
                errors.append(
                    f"{relative}: hreflang {language!r} does not match target language {target_parser.lang!r}"
                )
            if source_url not in target_parser.hreflang.values():
                errors.append(
                    f"{relative}: hreflang target {target_relative} does not return-link to this page"
                )
    return errors


def validate_unique_metadata(
    parsed_pages: dict[str, tuple[str, PageParser]],
) -> list[str]:
    """Reject exact title or description reuse across indexable pages."""
    errors: list[str] = []
    titles: dict[str, str] = {}
    descriptions: dict[str, str] = {}

    for relative, parser in parsed_pages.values():
        title_key = parser.title.casefold()
        description_key = " ".join(parser.description.split()).casefold()

        if title_key:
            if title_key in titles:
                errors.append(f"{relative}: duplicate title also used by {titles[title_key]}")
            else:
                titles[title_key] = relative

        if description_key:
            if description_key in descriptions:
                errors.append(
                    f"{relative}: duplicate meta description also used by {descriptions[description_key]}"
                )
            else:
                descriptions[description_key] = relative

    return errors


def validate_social_image(relative: str, label: str, value: str) -> list[str]:
    errors: list[str] = []
    if not value:
        return [f"{relative}: missing {label}"]
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.netloc != "shumaojs.com":
        return [f"{relative}: {label} must use an HTTPS shumaojs.com URL"]
    if Path(parsed.path).suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        errors.append(f"{relative}: {label} must use PNG, JPEG, or WebP rather than SVG")
    target = ROOT / parsed.path.lstrip("/")
    if not target.is_file():
        errors.append(f"{relative}: {label} target does not exist: {parsed.path}")
    return errors


def validate_sitemap_metadata(root: ElementTree.Element, today: date | None = None) -> list[str]:
    """Validate URL uniqueness and truthful ISO last-modified dates."""
    errors: list[str] = []
    today = today or date.today()
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    seen_urls: set[str] = set()

    for node in root.findall("sm:url", namespace):
        loc_node = node.find("sm:loc", namespace)
        lastmod_node = node.find("sm:lastmod", namespace)
        loc = (loc_node.text or "").strip() if loc_node is not None else ""
        lastmod = (lastmod_node.text or "").strip() if lastmod_node is not None else ""

        if not loc:
            errors.append("sitemap.xml: URL entry is missing loc")
        elif loc in seen_urls:
            errors.append(f"sitemap.xml: duplicate URL {loc}")
        else:
            seen_urls.add(loc)

        if not lastmod:
            errors.append(f"sitemap.xml: {loc or 'URL entry'} is missing lastmod")
            continue
        try:
            modified = date.fromisoformat(lastmod)
        except ValueError:
            errors.append(f"sitemap.xml: {loc or 'URL entry'} has invalid lastmod {lastmod!r}")
            continue
        if modified > today:
            errors.append(f"sitemap.xml: {loc or 'URL entry'} has future lastmod {lastmod}")

    return errors


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    canonicals: dict[str, str] = {}
    parsed_pages: dict[str, tuple[str, PageParser]] = {}
    pages = html_files()

    sitemap_root = ElementTree.parse(ROOT / "sitemap.xml").getroot()
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_urls = {
        (node.text or "").strip()
        for node in sitemap_root.findall("sm:url/sm:loc", namespace)
        if node.text
    }
    errors.extend(validate_sitemap_metadata(sitemap_root))

    for page in pages:
        relative = page.relative_to(ROOT).as_posix()
        parser = PageParser()
        try:
            parser.feed(page.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            errors.append(f"{relative}: file is not valid UTF-8")
            continue

        indexable = "noindex" not in parser.robots and relative != "404.html"
        if not parser.lang:
            errors.append(f"{relative}: missing html lang")
        if not parser.title:
            errors.append(f"{relative}: missing title")
        elif len(parser.title) > 70:
            warnings.append(f"{relative}: title is {len(parser.title)} characters")
        if indexable and not parser.description:
            errors.append(f"{relative}: missing meta description")
        elif len(parser.description) > 180:
            warnings.append(f"{relative}: description is {len(parser.description)} characters")
        if parser.h1_count != 1:
            errors.append(f"{relative}: expected exactly one h1, found {parser.h1_count}")

        if indexable:
            expected = canonical_to_sitemap_url(page)
            if not parser.canonical:
                errors.append(f"{relative}: missing canonical")
            elif parser.canonical != expected:
                errors.append(f"{relative}: canonical {parser.canonical!r} does not match {expected!r}")
            if parser.canonical in canonicals:
                errors.append(f"{relative}: duplicate canonical also used by {canonicals[parser.canonical]}")
            elif parser.canonical:
                canonicals[parser.canonical] = relative
            if expected not in sitemap_urls:
                errors.append(f"{relative}: indexable page missing from sitemap")
            parsed_pages[expected] = (relative, parser)
            errors.extend(validate_social_image(relative, "og:image", parser.og_image))
            errors.extend(validate_social_image(relative, "twitter:image", parser.twitter_image))

        for block in parser.jsonld_parts:
            try:
                json.loads("".join(block))
            except json.JSONDecodeError as exc:
                errors.append(f"{relative}: invalid JSON-LD ({exc.msg})")

        for target in parser.local_targets:
            resolved = resolve_local_target(page, target)
            if resolved is not None and ROOT.resolve() in resolved.parents and not resolved.exists():
                errors.append(f"{relative}: broken local target {target!r}")

    errors.extend(validate_hreflang(parsed_pages))
    errors.extend(validate_unique_metadata(parsed_pages))

    for url in sorted(sitemap_urls):
        parsed = urlparse(url)
        if parsed.netloc != "shumaojs.com":
            errors.append(f"sitemap.xml: unexpected host in {url}")

    print(f"Checked {len(pages)} HTML pages and {len(sitemap_urls)} sitemap URLs.")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    print(f"Result: {len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
