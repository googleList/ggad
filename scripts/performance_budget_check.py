#!/usr/bin/env python3
"""Enforce static performance safeguards that protect LCP and CLS."""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {".git", ".audit-shots", "reports"}
MAX_CSS_BYTES = 55 * 1024
MAX_JS_BYTES = 18 * 1024
STABLE_IMAGE_SELECTORS = (
    ".brand img",
    ".home-guide img",
    ".photo-frame img",
    ".policy-image img",
    ".article-thumb img",
    ".managed-visual img",
    ".ad-type-card img",
)


class ImageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.images: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "img":
            return
        self.images.append({key.lower(): value or "" for key, value in attrs})


def html_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.html")
        if not any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts)
    )


def css_block(css: str, selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*\{{(?P<body>[^}}]+)\}}", css)
    return match.group("body") if match else ""


def audit(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    css_path = root / "styles.css"
    js_path = root / "script.js"

    if css_path.stat().st_size > MAX_CSS_BYTES:
        errors.append(
            f"styles.css exceeds {MAX_CSS_BYTES} bytes ({css_path.stat().st_size} bytes)"
        )
    if js_path.stat().st_size > MAX_JS_BYTES:
        errors.append(
            f"script.js exceeds {MAX_JS_BYTES} bytes ({js_path.stat().st_size} bytes)"
        )

    css = css_path.read_text(encoding="utf-8")
    if re.search(r"@import\s", css, flags=re.IGNORECASE):
        errors.append("styles.css contains a render-blocking @import")
    for selector in STABLE_IMAGE_SELECTORS:
        block = css_block(css, selector)
        if not block:
            errors.append(f"styles.css is missing the critical image rule {selector}")
        elif "aspect-ratio" not in block and not (
            re.search(r"\bwidth\s*:", block) and re.search(r"\bheight\s*:", block)
        ):
            errors.append(f"{selector} does not reserve a stable image box")

    js = js_path.read_text(encoding="utf-8")
    if "iconStylesheet.media = \"print\"" not in js:
        errors.append("icon stylesheet is no longer loaded with the non-blocking media pattern")
    if "iconStylesheet.media = \"all\"" not in js:
        errors.append("icon stylesheet does not switch to all media after loading")

    for page in html_files(root):
        relative = page.relative_to(root).as_posix()
        parser = ImageParser()
        parser.feed(page.read_text(encoding="utf-8"))
        for index, image in enumerate(parser.images, start=1):
            src = image.get("src", "").strip()
            if not src:
                errors.append(f"{relative}: image {index} is missing src")
                continue
            if not image.get("alt", "").strip():
                errors.append(f"{relative}: image {src!r} is missing useful alt text")
            parsed = urlparse(src)
            if parsed.scheme not in {"http", "https"}:
                continue
            if not image.get("width") or not image.get("height"):
                errors.append(f"{relative}: external image {src!r} needs width and height")
            if image.get("decoding", "").lower() != "async":
                errors.append(f"{relative}: external image {src!r} should decode asynchronously")
            if parsed.netloc == "images.unsplash.com" and (
                not image.get("srcset", "").strip() or not image.get("sizes", "").strip()
            ):
                errors.append(
                    f"{relative}: Unsplash image {src!r} needs responsive srcset and sizes"
                )
            if image.get("fetchpriority", "").lower() == "high" and image.get(
                "loading", ""
            ).lower() == "lazy":
                errors.append(f"{relative}: high-priority image {src!r} cannot be lazy-loaded")

    return errors


def main() -> int:
    errors = audit()
    print(
        f"Performance budgets: styles.css {ROOT.joinpath('styles.css').stat().st_size} bytes, "
        f"script.js {ROOT.joinpath('script.js').stat().st_size} bytes."
    )
    for error in errors:
        print(f"ERROR: {error}")
    print(f"Result: {len(errors)} performance budget error(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
