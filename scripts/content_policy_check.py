#!/usr/bin/env python3
"""Reject legacy account-selling and storefront artifacts from the public site."""

from __future__ import annotations

import argparse
from pathlib import Path


TEXT_EXTENSIONS = {".html", ".js", ".json", ".md", ".txt", ".xml"}
EXCLUDED_PARTS = {".git", ".audit-shots", "reports", "__pycache__"}
EXCLUDED_FILES = {"scripts/content_policy_check.py", "tests/test_content_policy_check.py"}
FORBIDDEN_TEXT = ("开户", "開戶")
FORBIDDEN_PATHS = {
    "account-guidance.html",
    "articles/ad-account-materials.html",
    "admin.html",
    "admin.js",
    "app.js",
    "backend-api.js",
    "home.js",
    "order-detail.html",
    "order-detail.js",
    "product.html",
    "product-data.js",
    "query.html",
    "query.js",
    "success.html",
    "success.js",
    "assets/usdt-trc20-qr.png",
    "data/store.json",
}
FORBIDDEN_PREFIXES = (
    "current-site-seo/",
    "data/backups/",
    "detail-order-sn/",
    "order-detail/",
    "product/",
    "query/",
    "success/",
    "supabase/",
)


def normalized_relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def validate_repository(root: Path) -> list[str]:
    errors: list[str] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        relative = normalized_relative(path, root)
        parts = set(path.relative_to(root).parts)
        if parts & EXCLUDED_PARTS or relative in EXCLUDED_FILES:
            continue

        if relative in FORBIDDEN_PATHS or relative.startswith(FORBIDDEN_PREFIXES):
            errors.append(f"forbidden legacy artifact: {relative}")
            continue

        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"non-UTF-8 text file: {relative}")
            continue

        for phrase in FORBIDDEN_TEXT:
            if phrase in content:
                errors.append(f"legacy account-opening phrase {phrase!r}: {relative}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    errors = validate_repository(root)

    if errors:
        print(f"Content policy check failed with {len(errors)} issue(s):")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Content policy check passed: no legacy account-selling or storefront artifacts found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
