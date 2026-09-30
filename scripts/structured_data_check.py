#!/usr/bin/env python3
"""Validate JSON-LD semantics against each page's canonical URL and language."""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {".git", ".audit-shots", "reports"}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ORGANIZATION_ID = "https://shumaojs.com/#organization"
COMPANY_URL = "https://shumaojs.com/company.html"


class SchemaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang = ""
        self.canonical = ""
        self.robots = ""
        self.h1_parts: list[str] = []
        self.blocks: list[str] = []
        self._jsonld: list[str] | None = None
        self._in_h1 = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        tag = tag.lower()
        if tag == "html":
            self.lang = values.get("lang", "").strip()
        elif tag == "h1":
            self._in_h1 = True
        elif tag == "link" and "canonical" in values.get("rel", "").lower().split():
            self.canonical = values.get("href", "").strip()
        elif tag == "meta" and values.get("name", "").lower() == "robots":
            self.robots = values.get("content", "").lower()
        elif tag == "script" and values.get("type", "").lower() == "application/ld+json":
            self._jsonld = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "h1":
            self._in_h1 = False
        elif tag.lower() == "script" and self._jsonld is not None:
            self.blocks.append("".join(self._jsonld))
            self._jsonld = None

    def handle_data(self, data: str) -> None:
        if self._in_h1:
            self.h1_parts.append(data)
        if self._jsonld is not None:
            self._jsonld.append(data)

    @property
    def h1(self) -> str:
        return " ".join("".join(self.h1_parts).split())


def flatten_schema(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for value_item in value for item in flatten_schema(value_item)]
    if not isinstance(value, dict):
        return []
    graph = value.get("@graph")
    if isinstance(graph, list):
        return [value] + [item for graph_item in graph for item in flatten_schema(graph_item)]
    return [value]


def contains_key(value: Any, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(contains_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(contains_key(item, key) for item in value)
    return False


def schema_types(schema: dict[str, Any]) -> set[str]:
    raw = schema.get("@type", [])
    if isinstance(raw, str):
        return {raw}
    if isinstance(raw, list):
        return {item for item in raw if isinstance(item, str)}
    return set()


def contains_schema_type(value: Any, target: str) -> bool:
    if isinstance(value, dict):
        if target in schema_types(value):
            return True
        return any(contains_schema_type(item, target) for item in value.values())
    if isinstance(value, list):
        return any(contains_schema_type(item, target) for item in value)
    return False


def validate_page(path: Path, text: str) -> list[str]:
    parser = SchemaParser()
    parser.feed(text)
    if "noindex" in parser.robots:
        return []

    errors: list[str] = []
    schemas: list[dict[str, Any]] = []
    for index, block in enumerate(parser.blocks, start=1):
        try:
            parsed = json.loads(block)
        except json.JSONDecodeError as error:
            errors.append(f"JSON-LD block {index} is invalid: {error.msg}")
            continue
        schemas.extend(flatten_schema(parsed))
        if contains_schema_type(parsed, "Product"):
            errors.append(f"JSON-LD block {index} includes Product markup on a service-only site")
        for unsupported in ("aggregateRating", "review"):
            if contains_key(parsed, unsupported):
                errors.append(f"JSON-LD block {index} includes unverified '{unsupported}' markup")

    breadcrumbs = [item for item in schemas if "BreadcrumbList" in schema_types(item)]
    if path.name != "index.html" and not breadcrumbs:
        errors.append("indexable non-homepage is missing BreadcrumbList")
    for breadcrumb in breadcrumbs:
        elements = breadcrumb.get("itemListElement")
        if not isinstance(elements, list) or not elements:
            errors.append("BreadcrumbList has no itemListElement entries")
            continue
        last_item = elements[-1].get("item") if isinstance(elements[-1], dict) else None
        if last_item != parser.canonical:
            errors.append(f"BreadcrumbList final item '{last_item}' does not match canonical '{parser.canonical}'")

    for schema in schemas:
        types = schema_types(schema)
        if "Service" in types or "WebApplication" in types:
            provider = schema.get("provider")
            if not isinstance(provider, dict) or provider.get("@id") != ORGANIZATION_ID:
                errors.append("Service provider must reference the canonical organization @id")
            elif provider.get("url") != COMPANY_URL:
                errors.append("Service provider url must point to the company page")
        if "Article" in types:
            if schema.get("mainEntityOfPage") != parser.canonical:
                errors.append("Article mainEntityOfPage does not match canonical")
            if str(schema.get("inLanguage", "")).lower() != parser.lang.lower():
                errors.append("Article inLanguage does not match the html lang attribute")
            for field in ("headline", "image", "author", "publisher", "datePublished", "dateModified"):
                if not schema.get(field):
                    errors.append(f"Article is missing '{field}'")
            headline = " ".join(str(schema.get("headline", "")).split())
            if parser.h1 and headline.casefold() != parser.h1.casefold():
                errors.append("Article headline does not match the visible h1")
            author = schema.get("author")
            publisher = schema.get("publisher")
            if not isinstance(author, dict) or author.get("@id") != ORGANIZATION_ID:
                errors.append("Article author must reference the canonical organization @id")
            elif author.get("url") != COMPANY_URL:
                errors.append("Article author url must point to the company page")
            if not isinstance(publisher, dict) or publisher.get("@id") != ORGANIZATION_ID:
                errors.append("Article publisher must reference the canonical organization @id")
            elif publisher.get("url") != COMPANY_URL:
                errors.append("Article publisher url must point to the company page")
            logo = publisher.get("logo") if isinstance(publisher, dict) else None
            if not isinstance(logo, dict) or not logo.get("url"):
                errors.append("Article publisher must include a logo URL")
            for field in ("datePublished", "dateModified"):
                value = str(schema.get(field, ""))
                if value and not DATE_PATTERN.fullmatch(value):
                    errors.append(f"Article {field} must use YYYY-MM-DD")
            published_value = str(schema.get("datePublished", ""))
            modified_value = str(schema.get("dateModified", ""))
            if DATE_PATTERN.fullmatch(published_value) and DATE_PATTERN.fullmatch(modified_value):
                published = date.fromisoformat(published_value)
                modified = date.fromisoformat(modified_value)
                if published > date.today():
                    errors.append("Article datePublished cannot be in the future")
                if modified > date.today():
                    errors.append("Article dateModified cannot be in the future")
                if modified < published:
                    errors.append("Article dateModified cannot be earlier than datePublished")
        if "WebApplication" in types:
            if schema.get("url") != parser.canonical:
                errors.append("WebApplication url does not match canonical")
            if str(schema.get("inLanguage", "")).lower() != parser.lang.lower():
                errors.append("WebApplication inLanguage does not match the html lang attribute")
            if schema.get("offers"):
                errors.append("WebApplication must not expose Offer markup on this service-only site")
            if schema.get("isAccessibleForFree") is not True:
                errors.append("WebApplication must declare isAccessibleForFree as true")
        if "ProfessionalService" in types:
            if schema.get("url") != parser.canonical:
                errors.append("ProfessionalService url does not match canonical")
            for field in ("name", "legalName", "identifier", "taxID", "address", "areaServed"):
                if not schema.get(field):
                    errors.append(f"ProfessionalService is missing '{field}'")
            if schema.get("@id") != ORGANIZATION_ID:
                errors.append("ProfessionalService must use the canonical organization @id")
        if "CollectionPage" in types:
            item_list = schema.get("mainEntity")
            if not isinstance(item_list, dict) or "ItemList" not in schema_types(item_list):
                errors.append("CollectionPage mainEntity must be an ItemList")
                continue
            elements = item_list.get("itemListElement")
            if not isinstance(elements, list) or not elements:
                errors.append("CollectionPage ItemList has no entries")
                continue
            positions = [entry.get("position") for entry in elements if isinstance(entry, dict)]
            expected_positions = list(range(1, len(elements) + 1))
            if positions != expected_positions:
                errors.append("CollectionPage ItemList positions must be unique and consecutive from 1")
            urls = [entry.get("url") for entry in elements if isinstance(entry, dict)]
            if any(not url for url in urls):
                errors.append("CollectionPage ItemList entries must include a URL")
            elif len(urls) != len(set(urls)):
                errors.append("CollectionPage ItemList contains duplicate URLs")

    return errors


def html_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.html")
        if not any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts)
    )


def dynamic_product_markup_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.js")
        if not any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts)
        and re.search(r'["\']@type["\']\s*:\s*["\']Product["\']', path.read_text(encoding="utf-8"))
    )


def main() -> int:
    errors: list[str] = []
    files = html_files()
    for path in files:
        for error in validate_page(path, path.read_text(encoding="utf-8")):
            errors.append(f"{path.relative_to(ROOT).as_posix()}: {error}")
    for path in dynamic_product_markup_files():
        errors.append(
            f"{path.relative_to(ROOT).as_posix()}: dynamic Product structured data is not allowed "
            "on this service-only site"
        )
    print(f"Checked structured data on {len(files)} HTML pages.")
    for error in errors:
        print(f"ERROR: {error}")
    print(f"Result: {len(errors)} structured data error(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
