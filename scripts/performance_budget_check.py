#!/usr/bin/env python3
"""Enforce static performance safeguards that protect LCP and CLS."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {".git", ".audit-shots", "reports"}
MAX_CSS_BYTES = 55 * 1024
MAX_JS_BYTES = 18 * 1024
MAX_ICON_ASSET_BYTES = 12 * 1024
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


class ScriptParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.sources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "script":
            return
        values = {key.lower(): value or "" for key, value in attrs}
        if values.get("src"):
            self.sources.append(values["src"])


def html_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.html")
        if not any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts)
    )


def css_block(css: str, selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*\{{(?P<body>[^}}]+)\}}", css)
    return match.group("body") if match else ""


def local_script_paths(root: Path) -> set[Path]:
    paths: set[Path] = set()
    for page in html_files(root):
        parser = ScriptParser()
        parser.feed(page.read_text(encoding="utf-8"))
        for source in parser.sources:
            parsed = urlparse(source)
            if parsed.scheme or parsed.netloc:
                continue
            candidate = (page.parent / parsed.path).resolve()
            try:
                candidate.relative_to(root.resolve())
            except ValueError:
                continue
            paths.add(candidate)
    return paths


def audit_icon_assets(root: Path, scripts: str) -> list[str]:
    errors: list[str] = []
    if "https://cdn.jsdelivr.net/npm/@tabler/icons-webfont" in scripts:
        errors.append("load the local icon subset instead of the full external icon font")
    if "assets/icons/tabler-subset-v1.css" not in scripts:
        return errors
    directory = root / "assets" / "icons"
    css_path = directory / "tabler-subset-v1.css"
    font_path = directory / "tabler-subset-v1.woff2"
    manifest_path = directory / "manifest.json"
    for path in (css_path, font_path, manifest_path):
        if not path.is_file():
            errors.append(f"local icon asset is missing: {path.name}")
    if errors:
        return errors
    font = font_path.read_bytes()
    if len(font) + css_path.stat().st_size > MAX_ICON_ASSET_BYTES:
        errors.append(f"local icon CSS and font exceed {MAX_ICON_ASSET_BYTES} bytes")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return errors + ["local icon manifest is invalid JSON"]
    if (
        len(font) != manifest.get("subsetFontBytes")
        or hashlib.sha256(font).hexdigest() != manifest.get("subsetFontSha256")
    ):
        errors.append("local icon font does not match its generated manifest")
    glyphs = manifest.get("glyphs")
    if not isinstance(glyphs, dict) or not glyphs:
        return errors + ["local icon manifest has no glyph mappings"]
    css = css_path.read_text(encoding="utf-8")
    mappings = dict(re.findall(r'\.ti-([a-z0-9-]+):before\{content:"\\([0-9a-f]+)"\}', css))
    for name, codepoint in glyphs.items():
        if mappings.get(name) != codepoint:
            errors.append(f"local icon CSS is missing its glyph mapping: {name}")
    return errors


def audit(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    css_path = root / "styles.css"

    css_size = len(css_path.read_bytes().replace(b"\r\n", b"\n"))
    if css_size > MAX_CSS_BYTES:
        errors.append(
            f"styles.css exceeds {MAX_CSS_BYTES} bytes ({css_size} normalized bytes)"
        )
    script_paths = local_script_paths(root)
    if not script_paths:
        errors.append("no local JavaScript asset is referenced by an HTML page")
    for js_path in sorted(script_paths):
        if not js_path.is_file():
            errors.append(f"referenced JavaScript asset is missing: {js_path.name}")
        elif js_path.stat().st_size > MAX_JS_BYTES:
            errors.append(
                f"{js_path.name} exceeds {MAX_JS_BYTES} bytes ({js_path.stat().st_size} bytes)"
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

    hero_block = css_block(css, ".hero")
    hero_columns = re.search(r"grid-template-columns\s*:\s*([^;]+)", hero_block)
    if hero_columns and re.search(r"\b\d+(?:\.\d+)?vw\b", hero_columns.group(1)):
        errors.append(
            ".hero grid columns must be sized from the bounded container, not the viewport"
        )

    existing_scripts = [path for path in script_paths if path.is_file()]
    combined_js = "\n".join(path.read_text(encoding="utf-8") for path in existing_scripts)
    errors.extend(audit_icon_assets(root, combined_js))
    if existing_scripts and "iconStylesheet.media = \"print\"" not in combined_js:
        errors.append("icon stylesheet is no longer loaded with the non-blocking media pattern")
    if existing_scripts and "iconStylesheet.media = \"all\"" not in combined_js:
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
            elif parsed.netloc == "images.unsplash.com":
                widths = {
                    int(width)
                    for width in re.findall(r"\s(\d+)w(?:,|$)", image.get("srcset", ""))
                }
                if not any(560 <= width <= 700 for width in widths):
                    errors.append(
                        f"{relative}: Unsplash image {src!r} needs a 560-700px mobile candidate"
                    )
            if image.get("fetchpriority", "").lower() == "high" and image.get(
                "loading", ""
            ).lower() == "lazy":
                errors.append(f"{relative}: high-priority image {src!r} cannot be lazy-loaded")

    return errors


def main() -> int:
    errors = audit()
    scripts = local_script_paths(ROOT)
    css_size = len((ROOT / "styles.css").read_bytes().replace(b"\r\n", b"\n"))
    script_summary = ", ".join(
        f"{path.name} {path.stat().st_size} bytes" for path in sorted(scripts) if path.is_file()
    ) or "none"
    print(
        f"Performance budgets: styles.css {css_size} normalized bytes, "
        f"JavaScript {script_summary}."
    )
    for error in errors:
        print(f"ERROR: {error}")
    print(f"Result: {len(errors)} performance budget error(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
