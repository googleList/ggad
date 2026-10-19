#!/usr/bin/env python3
"""Fetch optimized variants of the photograph already used by the homepage."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "hero"
PHOTO = "https://images.unsplash.com/photo-1557804506-669a67965ba0"
VARIANTS = (
    (800, 450, 35, "avif"), (1200, 675, 35, "avif"),
    (1600, 900, 30, "avif"), (2000, 1125, 30, "avif"),
    (800, 450, 50, "jpg"), (1200, 675, 50, "jpg"),
)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = {"source": PHOTO, "license": "https://unsplash.com/license", "variants": []}
    for width, height, quality, image_format in VARIANTS:
        query = urlencode({"fm": image_format, "fit": "crop", "w": width, "h": height, "q": quality})
        url = f"{PHOTO}?{query}"
        with urlopen(url, timeout=30) as response:
            image = response.read()
            mime = response.headers.get_content_type()
        expected = "image/avif" if image_format == "avif" else "image/jpeg"
        if mime != expected:
            raise ValueError(f"Unexpected response type {mime} for {url}")
        filename = f"team-{width}.{image_format}"
        (OUTPUT / filename).write_bytes(image)
        manifest["variants"].append({
            "file": filename, "width": width, "height": height, "quality": quality,
            "format": image_format, "bytes": len(image),
            "sha256": hashlib.sha256(image).hexdigest(), "url": url,
        })
        print(f"{filename}: {len(image)} bytes")
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
