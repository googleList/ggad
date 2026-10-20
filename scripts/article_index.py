#!/usr/bin/env python3
"""Keep the article hub's static cards and ItemList in the same priority order."""

from __future__ import annotations

import argparse
import json
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin


class ArticleIndexParser(HTMLParser):
    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=True)
        self.source = source
        self.offsets = [0]
        for line in source.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))
        self.canonical = ""
        self.cards: list[dict] = []
        self.card: dict | None = None
        self.in_heading = False
        self.schema_start: int | None = None
        self.schemas: list[tuple[int, int, dict]] = []

    def absolute_offset(self) -> int:
        line, column = self.getpos()
        return self.offsets[line - 1] + column

    def handle_starttag(self, tag: str, attrs: list) -> None:
        values = dict(attrs)
        if tag == "link" and values.get("rel") == "canonical":
            self.canonical = values.get("href", "")
        if tag == "article" and "data-article-card" in values:
            if self.card is not None:
                raise ValueError("nested article cards")
            self.card = {
                "start": self.absolute_offset(), "attrs": attrs,
                "opening_length": len(self.get_starttag_text()),
                "priority": int(values.get("data-search-priority") or 0),
                "href": "", "heading": [],
            }
        if self.card is not None:
            if tag == "h3":
                self.in_heading = True
            if tag == "a" and self.in_heading:
                self.card["href"] = values.get("href", "")
        if tag == "script" and values.get("type") == "application/ld+json":
            self.schema_start = self.absolute_offset() + len(self.get_starttag_text())

    def handle_data(self, data: str) -> None:
        if self.card is not None and self.in_heading:
            self.card["heading"].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "h3":
            self.in_heading = False
        if tag == "article" and self.card is not None:
            self.card["end"] = self.source.index(">", self.absolute_offset()) + 1
            self.card["name"] = " ".join("".join(self.card.pop("heading")).split())
            self.cards.append(self.card)
            self.card = None
        if tag == "script" and self.schema_start is not None:
            start, end = self.schema_start, self.absolute_offset()
            block = json.loads(self.source[start:end])
            if isinstance(block, dict) and block.get("@type") == "CollectionPage":
                self.schemas.append((start, end, block))
            self.schema_start = None


def parse_index(source: str) -> ArticleIndexParser:
    parser = ArticleIndexParser(source)
    parser.feed(source)
    parser.close()
    if parser.card is not None or not parser.cards:
        raise ValueError("missing or unclosed article cards")
    if not parser.canonical or len(parser.schemas) != 1:
        raise ValueError("expected canonical and one CollectionPage schema")
    urls = []
    for card in parser.cards:
        if not card["name"] or not card["href"]:
            raise ValueError("card needs a linked h3 heading")
        urls.append(urljoin(parser.canonical, card["href"]))
    if len(set(urls)) != len(urls):
        raise ValueError("duplicate article card URL")
    return parser


def synchronize(source: str) -> str:
    parser = parse_index(source)
    cards = sorted(parser.cards, key=lambda card: -card["priority"])
    for left, right in zip(parser.cards, parser.cards[1:]):
        if source[left["end"]:right["start"]].strip():
            raise ValueError("non-card content between article cards; refusing rewrite")

    rendered = []
    for card in cards:
        attrs = "".join(
            f" {name}" if value is None else f' {name}="{escape(value, quote=True)}"'
            for name, value in card["attrs"]
            if name not in {"hidden", "data-article-page"}
        )
        body = source[card["start"] + card["opening_length"]:card["end"]]
        rendered.append(f"<article{attrs}>" + body)

    start, end, schema = parser.schemas[0]
    listing = schema.get("mainEntity")
    if not isinstance(listing, dict) or listing.get("@type") != "ItemList":
        raise ValueError("CollectionPage needs an ItemList mainEntity")
    listing["itemListElement"] = [
        {"@type": "ListItem", "position": index,
         "url": urljoin(parser.canonical, card["href"]), "name": card["name"]}
        for index, card in enumerate(cards, 1)
    ]
    if "numberOfItems" in listing:
        listing["numberOfItems"] = len(cards)
    replacements = [
        (parser.cards[0]["start"], parser.cards[-1]["end"], "\n\n        ".join(rendered)),
        (start, end, "\n" + json.dumps(schema, ensure_ascii=False, indent=2) + "\n  "),
    ]
    for start, end, replacement in sorted(replacements, reverse=True):
        source = source[:start] + replacement + source[end:]
    return source


def validate_article_index(source: str) -> list[str]:
    try:
        if synchronize(source) != source:
            return ["articles.html: card order, static visibility or ItemList differs; run scripts/article_index.py --write"]
        return []
    except (ValueError, KeyError, TypeError) as exc:
        return [f"articles.html: invalid article index ({exc})"]


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--write", action="store_true", help="synchronize cards and schema in place")
    args = cli.parse_args()
    path = Path(__file__).resolve().parents[1] / "articles.html"
    source = path.read_text(encoding="utf-8")
    if args.write:
        path.write_text(synchronize(source), encoding="utf-8", newline="\n")
        print("Synchronized article cards and ItemList.")
        return 0
    errors = validate_article_index(source)
    for error in errors:
        print(error)
    print(f"Article index: {len(errors)} error(s).")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
