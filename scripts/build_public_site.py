#!/usr/bin/env python3
"""Stage only public website files, not repository reports or research data."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from urllib.parse import unquote, urlparse

from seo_quality_check import PageParser


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = (
    "budget-calculator.js", "site-v20260930.js", "styles.css", "favicon.ico",
    "robots.txt", "sitemap.xml", "feed.xml", "llms.txt", "site.webmanifest", "CNAME",
)
OPTIONAL_FILES = ("_headers", "_redirects", ".nojekyll")
PUBLIC_DATA = ("data/ad-learning.json",)


class ReferenceParser(PageParser):
    def handle_starttag(self, tag: str, attrs: list) -> None:
        super().handle_starttag(tag, attrs)
        if tag == "link":
            target = dict(attrs).get("href")
            if target:
                self.local_targets.append(target)


def validate_references(output: Path) -> None:
    errors = []
    for page in output.rglob("*.html"):
        parser = ReferenceParser()
        parser.feed(page.read_text(encoding="utf-8"))
        for target in parser.local_targets:
            parsed = urlparse(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            raw = unquote(parsed.path)
            candidate = (output / raw.lstrip("/")) if raw.startswith("/") else page.parent / raw
            resolved = candidate.resolve()
            if not resolved.is_relative_to(output):
                errors.append(f"{page.relative_to(output)}: reference escapes artifact: {target}")
            elif not resolved.exists():
                errors.append(f"{page.relative_to(output)}: unpublished reference: {target}")
    if errors:
        raise ValueError("\n".join(errors))


def build_public_site(root: Path, output: Path) -> list[str]:
    root, output = root.resolve(), output.resolve()
    if output.is_relative_to(root) or root.is_relative_to(output):
        raise ValueError("output must be outside the repository and not an ancestor of it")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("output must be a new or empty directory; existing files are never deleted")
    required = [root / name for name in (*PUBLIC_FILES, *PUBLIC_DATA, "index.html")]
    missing = [str(path.relative_to(root)) for path in required if not path.is_file()]
    if missing:
        raise ValueError(f"missing public files: {', '.join(missing)}")

    sources = set(required)
    sources.update(root.glob("*.html"))
    sources.update(root / name for name in OPTIONAL_FILES if (root / name).is_file())
    for directory in (root / "assets", root / "articles"):
        if directory.is_symlink():
            raise ValueError(f"symlink is not a public asset: {directory}")
        if directory.exists():
            for path in directory.rglob("*"):
                if path.is_symlink():
                    raise ValueError(f"symlink is not a public asset: {path}")
                if path.is_file() and (directory.name == "assets" or path.suffix == ".html"):
                    sources.add(path)

    for source in sources:
        if source.is_symlink() or not source.resolve().is_relative_to(root):
            raise ValueError(f"public source escapes repository: {source}")
    output.mkdir(parents=True, exist_ok=True)
    copied = []
    for source in sorted(sources):
        relative = source.relative_to(root)
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        copied.append(relative.as_posix())
    validate_references(output)
    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        files = build_public_site(ROOT, args.output)
    except ValueError as error:
        parser.exit(1, f"Public artifact build failed: {error}\n")
    print(f"Staged {len(files)} public files in {args.output.resolve()}")
    print("Reports, scripts, tests, research and SEO planning data are not website assets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
