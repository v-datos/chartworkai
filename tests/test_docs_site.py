from pathlib import Path

import pytest

from website.build_site import GUIDE_TOKEN, generate, rewrite_links

ROOT = Path(__file__).resolve().parents[1]


def test_site_home_is_generated_from_the_canonical_implementation_guide(tmp_path: Path) -> None:
    output = generate(tmp_path / "docs")
    home = (output / "index.md").read_text(encoding="utf-8")
    guide = (ROOT / "IMPLEMENTATION_GUIDE.md").read_text(encoding="utf-8")

    assert GUIDE_TOKEN not in home
    assert '<h1 id="cw-hero-title">Chartwork<span>AI</span></h1>' in home
    assert "## Implementation Guide" in home
    assert "## 0. The mental model (read this first)" in home
    assert guide.count("## 7. Keep it healthy") == home.count("## 7. Keep it healthy") == 1
    assert "pip install chartworkai" in home


def test_site_generator_copies_public_docs_profiles_and_brand_assets(tmp_path: Path) -> None:
    output = generate(tmp_path / "docs")

    expected = (
        "overview.md",
        "cli.md",
        "profiles/index.md",
        "profiles/generic.md",
        "integrations/crewai.md",
        "assets/chartworkai_mark.png",
        "assets/stylesheets/chartworkai.css",
        "assets/javascripts/chartworkai.js",
    )
    assert all((output / path).is_file() for path in expected)
    assert (output / "assets/chartworkai_mark.png").read_bytes() == (
        ROOT / "assets/chartworkai_mark.png"
    ).read_bytes()


def test_site_link_rewriter_prefers_public_pages_and_links_other_sources_to_github() -> None:
    rendered = rewrite_links(
        "[guide](IMPLEMENTATION_GUIDE.md) [profile](profiles/generic.md) "
        "[template](templates/custom_profile.template.json)",
        source=Path("README.md"),
        destination=Path("overview.md"),
    )

    assert "[profile](profiles/generic.md)" in rendered
    assert "https://github.com/v-datos/chartworkai/blob/main/templates/" in rendered
    assert "IMPLEMENTATION_GUIDE.md" not in rendered


def test_site_link_rewriter_handles_nested_badge_links() -> None:
    rendered = rewrite_links(
        "[![License](https://img.shields.io/example.svg)](LICENSE)",
        source=Path("README.md"),
        destination=Path("overview.md"),
    )

    assert "](https://github.com/v-datos/chartworkai/blob/main/LICENSE)" in rendered


def test_site_generator_rejects_a_missing_home_insertion_point(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from website import build_site

    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / "home.md").write_text("# No insertion point\n", encoding="utf-8")
    monkeypatch.setattr(build_site, "SOURCES", sources)

    with pytest.raises(ValueError, match="exactly one"):
        build_site.generate(tmp_path / "output")
