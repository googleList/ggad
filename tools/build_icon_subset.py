#!/usr/bin/env python3
"""Build the site's Tabler subset: pip install -r tools/requirements-icons.txt."""

from __future__ import annotations

import hashlib
import io
import json
import re
from pathlib import Path
from urllib.request import urlopen

from fontTools import subset
from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "icons"
VERSION = "3.46.0"
SOURCE = f"https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@{VERSION}"
ICON_NAMES = (
    "ad-2", "article", "book-2", "brand-facebook", "brand-google", "brand-meta",
    "brand-telegram", "brand-x", "building-store", "chart-line", "circle",
    "circle-check", "coin", "external-link", "file-certificate", "file-description",
    "home", "lock", "menu-2", "message-circle", "photo", "search", "shield-check",
    "speakerphone", "tools", "world-www", "x",
)


def download(path: str) -> bytes:
    with urlopen(f"{SOURCE}/{path}", timeout=30) as response:
        return response.read()


def main() -> None:
    css = download("dist/tabler-icons.min.css").decode("utf-8")
    source_font = download("dist/fonts/tabler-icons.woff2")
    license_text = download("LICENSE").decode("utf-8")
    glyphs = {
        name: int(codepoint, 16)
        for name, codepoint in re.findall(
            r'\.ti-([a-z0-9-]+):before\{content:"\\([0-9a-f]+)"\}', css
        )
        if name in ICON_NAMES
    }
    missing = set(ICON_NAMES) - glyphs.keys()
    if missing:
        raise ValueError(f"Missing upstream icons: {sorted(missing)}")

    font = TTFont(io.BytesIO(source_font), recalcTimestamp=False)
    options = subset.Options()
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=glyphs.values())
    subsetter.subset(font)
    font.flavor = "woff2"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    font_path = OUTPUT / "tabler-subset-v1.woff2"
    font.save(font_path)

    rules = [
        f"/* Tabler Icons {VERSION}, MIT License. See LICENSE.txt. */",
        '@font-face{font-family:"tabler-icons";font-style:normal;font-weight:400;'
        'font-display:swap;src:url("./tabler-subset-v1.woff2") format("woff2")}',
        '.ti{font-family:"tabler-icons"!important;speak:none;font-style:normal;'
        'font-weight:normal;font-variant:normal;text-transform:none;line-height:1;'
        '-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}',
    ]
    rules.extend(
        f'.ti-{name}:before{{content:"\\{glyphs[name]:x}"}}' for name in ICON_NAMES
    )
    (OUTPUT / "tabler-subset-v1.css").write_text("\n".join(rules) + "\n", encoding="utf-8")
    (OUTPUT / "LICENSE.txt").write_text(license_text, encoding="utf-8")
    manifest = {
        "library": "@tabler/icons-webfont",
        "version": VERSION,
        "source": SOURCE,
        "sourceFontSha256": hashlib.sha256(source_font).hexdigest(),
        "sourceFontBytes": len(source_font),
        "subsetFontBytes": font_path.stat().st_size,
        "subsetFontSha256": hashlib.sha256(font_path.read_bytes()).hexdigest(),
        "glyphs": {name: f"{glyphs[name]:x}" for name in ICON_NAMES},
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Built {len(glyphs)} icons: {len(source_font)} -> {font_path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
