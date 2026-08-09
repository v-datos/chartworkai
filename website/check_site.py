#!/usr/bin/env python3
"""Validate the built documentation site without making network requests."""

from __future__ import annotations

import argparse
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.h1_count = 0
        self.images_without_alt = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "h1":
            self.h1_count += 1
        if tag == "a" and values.get("href"):
            self.links.append(("href", values["href"] or ""))
        if tag in {"img", "script"} and values.get("src"):
            self.links.append(("src", values["src"] or ""))
        if tag == "link" and values.get("href"):
            self.links.append(("href", values["href"] or ""))
        if tag == "img" and "alt" not in values:
            self.images_without_alt += 1


def _local_target(site: Path, page: Path, raw_url: str) -> Path | None:
    if raw_url.startswith(("http://", "https://", "mailto:", "data:", "javascript:")):
        return None
    parsed = urlsplit(raw_url)
    if not parsed.path:
        return None
    path = Path(unquote(parsed.path))
    if path.is_absolute():
        parts = path.parts
        if len(parts) > 1 and parts[1] == "chartworkai":
            path = Path(*parts[2:])
        else:
            path = Path(*parts[1:])
        target = site / path
    else:
        target = page.parent / path
    if target.is_dir():
        target = target / "index.html"
    return target.resolve()


def check(site: Path) -> list[str]:
    failures: list[str] = []
    html_pages = sorted(site.rglob("*.html"))
    if not html_pages:
        return [f"no HTML pages found under {site}"]

    for page in html_pages:
        text = page.read_text(encoding="utf-8")
        parser = PageParser()
        parser.feed(text)
        relative = page.relative_to(site)

        if parser.h1_count != 1:
            failures.append(f"{relative}: expected one H1, found {parser.h1_count}")
        if parser.images_without_alt:
            failures.append(
                f"{relative}: {parser.images_without_alt} image(s) have no alt attribute"
            )
        if any(marker in text for marker in ("file://", "/Users/", "/home/runner/")):
            failures.append(f"{relative}: contains a local filesystem path")

        for attribute, raw_url in parser.links:
            target = _local_target(site, page, raw_url)
            if target is None:
                continue
            try:
                target.relative_to(site.resolve())
            except ValueError:
                failures.append(f"{relative}: {attribute} escapes the site: {raw_url}")
                continue
            if not target.exists():
                failures.append(f"{relative}: broken {attribute}: {raw_url}")

    homepage = (site / "index.html").read_text(encoding="utf-8")
    for required in (
        "ChartworkAI",
        "Implementation Guide",
        "pip install chartworkai",
        "The mental model",
    ):
        if required not in homepage:
            failures.append(f"index.html: missing required front-door content: {required}")
    if not (site / "search" / "search_index.json").is_file():
        failures.append("search/search_index.json: search index was not generated")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", type=Path, nargs="?", default=Path("site"))
    args = parser.parse_args()
    failures = check(args.site.resolve())
    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"site validation failed with {len(failures)} finding(s)")
        return 1
    print("site validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
