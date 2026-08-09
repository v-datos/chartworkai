#!/usr/bin/env python3
"""Build MkDocs inputs from the repository's canonical documentation."""

from __future__ import annotations

import argparse
import os
import re
import shutil
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"
SOURCES = WEBSITE / "sources"
DEFAULT_OUTPUT = WEBSITE / ".generated"
GUIDE_TOKEN = "<!-- CANONICAL_IMPLEMENTATION_GUIDE -->"

PUBLIC_DOCS = {
    PurePosixPath("README.md"): PurePosixPath("overview.md"),
    PurePosixPath("INITIALIZATION_GUIDE.md"): PurePosixPath("initialization.md"),
    PurePosixPath("SOP.md"): PurePosixPath("operating-model.md"),
    PurePosixPath("FRAMEWORK_OVERVIEW.md"): PurePosixPath("concepts.md"),
    PurePosixPath("PORTABILITY.md"): PurePosixPath("portability.md"),
    PurePosixPath("SECURITY.md"): PurePosixPath("security.md"),
    PurePosixPath("CONTRIBUTING.md"): PurePosixPath("contributing.md"),
    PurePosixPath("CHANGELOG.md"): PurePosixPath("changelog.md"),
    PurePosixPath("extensions/README.md"): PurePosixPath("extensions.md"),
    PurePosixPath("integrations/crewai/README.md"): PurePosixPath("integrations/crewai.md"),
}
PUBLIC_LINKS = {
    **PUBLIC_DOCS,
    PurePosixPath("IMPLEMENTATION_GUIDE.md"): PurePosixPath("index.md"),
    PurePosixPath("extensions"): PurePosixPath("extensions.md"),
    PurePosixPath("profiles"): PurePosixPath("profiles/index.md"),
}

for profile in sorted((ROOT / "profiles").glob("*.md")):
    destination = "index.md" if profile.name == "README.md" else profile.name
    PUBLIC_DOCS[PurePosixPath(profile.relative_to(ROOT).as_posix())] = (
        PurePosixPath("profiles") / destination
    )

PUBLIC_LINKS.update(PUBLIC_DOCS)

MARKDOWN_LINK = re.compile(
    r"(?P<prefix>!?\[(?:[^\[\]]|!\[[^\]]*\]\([^)]+\))*\]\()"
    r"(?P<target>[^)]+)(?P<suffix>\))"
)


def _repo_url(path: PurePosixPath, *, directory: bool = False) -> str:
    kind = "tree" if directory else "blob"
    return f"https://github.com/v-datos/chartworkai/{kind}/main/{path.as_posix()}"


def _relative_site_link(
    destination: PurePosixPath,
    mapped_target: PurePosixPath,
    fragment: str,
) -> str:
    base = destination.parent.as_posix()
    relative = os.path.relpath(mapped_target.as_posix(), base if base != "." else ".")
    return PurePosixPath(relative).as_posix() + fragment


def rewrite_links(
    text: str,
    *,
    source: PurePosixPath,
    destination: PurePosixPath,
) -> str:
    """Point canonical relative links at their public site or repository location."""

    def replace(match: re.Match[str]) -> str:
        target = match.group("target").strip()
        if target.startswith(("#", "http://", "https://", "mailto:")):
            return match.group(0)

        path_text, separator, fragment_text = target.partition("#")
        fragment = f"#{fragment_text}" if separator else ""
        resolved = PurePosixPath(os.path.normpath((source.parent / path_text).as_posix()))

        mapped = PUBLIC_LINKS.get(resolved)
        if mapped is not None:
            replacement = _relative_site_link(destination, mapped, fragment)
        elif (ROOT / resolved).is_dir():
            replacement = _repo_url(resolved, directory=True) + fragment
        elif (ROOT / resolved).is_file():
            replacement = _repo_url(resolved) + fragment
        else:
            replacement = target

        return f"{match.group('prefix')}{replacement}{match.group('suffix')}"

    return MARKDOWN_LINK.sub(replace, text)


def _write_document(
    output: Path,
    *,
    source: PurePosixPath,
    destination: PurePosixPath,
) -> None:
    text = (ROOT / source).read_text(encoding="utf-8")
    rendered = rewrite_links(text, source=source, destination=destination)
    target = output / destination
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")


def generate(output: Path = DEFAULT_OUTPUT) -> Path:
    """Generate the complete MkDocs source tree and return its path."""

    home_template = (SOURCES / "home.md").read_text(encoding="utf-8")
    if home_template.count(GUIDE_TOKEN) != 1:
        raise ValueError(f"website/sources/home.md must contain exactly one {GUIDE_TOKEN}")

    guide = (ROOT / "IMPLEMENTATION_GUIDE.md").read_text(encoding="utf-8")
    heading = "# Implementation Guide"
    if not guide.startswith(f"{heading}\n"):
        raise ValueError("IMPLEMENTATION_GUIDE.md must start with its canonical H1")
    guide = guide.replace(heading, "## Implementation Guide", 1)
    guide = rewrite_links(
        guide,
        source=PurePosixPath("IMPLEMENTATION_GUIDE.md"),
        destination=PurePosixPath("index.md"),
    )

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    (output / "index.md").write_text(
        home_template.replace(GUIDE_TOKEN, guide),
        encoding="utf-8",
    )

    for source, destination in PUBLIC_DOCS.items():
        _write_document(output, source=source, destination=destination)

    for source_name in ("cli.md", "404.md"):
        shutil.copy2(SOURCES / source_name, output / source_name)

    shutil.copytree(SOURCES / "assets", output / "assets", dirs_exist_ok=True)
    for asset_name in ("chartworkai_mark.png", "chartworkai_banner.png"):
        shutil.copy2(ROOT / "assets" / asset_name, output / "assets" / asset_name)

    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Generated MkDocs source directory.",
    )
    args = parser.parse_args()
    generated = generate(args.output.resolve())
    print(f"generated documentation sources in {generated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
