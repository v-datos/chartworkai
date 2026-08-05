"""The manifest must not drift from the code and files it describes.

``framework.json`` is the machine-readable description of the product: which
profiles exist, what each requires, and which templates, prompts, scripts and
extensions ship. Nothing enforces it at runtime, so without these tests it can
quietly describe a product that no longer exists — a rename or a new profile is
enough. The checker is the source of truth for behaviour; the manifest must agree
with it and point only at files that are really there.
"""

from __future__ import annotations

import json

import pytest
from conftest import REPO_ROOT

from chartworkai.checks import DATA_PROFILES, KNOWN_PROFILES

MANIFEST_PATH = REPO_ROOT / "framework.json"
MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
PROFILES = MANIFEST["profiles"]

#: Inventory keys whose values are paths that must exist in the repository.
INVENTORY_KEYS = ("templates", "prompts", "scripts", "extensions")


class TestProfilesAgreeWithTheChecker:
    """The manifest and ``checks.py`` must describe the same six profiles."""

    def test_the_manifest_lists_exactly_the_known_profiles(self):
        assert set(PROFILES) == set(KNOWN_PROFILES)

    def test_the_default_profile_is_one_of_them(self):
        assert MANIFEST["default_profile"] in PROFILES

    @pytest.mark.parametrize("name", sorted(PROFILES))
    def test_the_data_contract_flag_matches_the_checker(self, name):
        """A mismatch here would require the triad in docs but not in the tool."""
        assert PROFILES[name]["requires_data_contracts"] is (name in DATA_PROFILES)

    @pytest.mark.parametrize("name", sorted(PROFILES))
    def test_data_profiles_declare_the_triad_and_others_declare_nothing(self, name):
        required = PROFILES[name]["required_files"]
        if name in DATA_PROFILES:
            assert required == [
                "docs/data/data_dictionary.md",
                "docs/data/lineage.md",
                "docs/data/watchlist.md",
            ]
            assert PROFILES[name]["required_directories"] == ["docs/data"]
        else:
            assert required == []
            assert PROFILES[name]["required_directories"] == []


class TestEveryProfileIsFullyDescribed:
    """Half-described profiles are how "planned" features get advertised as real."""

    @pytest.mark.parametrize("name", sorted(PROFILES))
    def test_the_spec_file_exists(self, name):
        spec = REPO_ROOT / PROFILES[name]["spec"]
        assert spec.is_file(), f"{name} points at a missing spec: {spec}"

    @pytest.mark.parametrize("name", sorted(PROFILES))
    def test_the_spec_names_the_profile(self, name):
        text = (REPO_ROOT / PROFILES[name]["spec"]).read_text(encoding="utf-8")
        assert f"# Profile: {name}" in text

    @pytest.mark.parametrize("name", sorted(PROFILES))
    def test_reproducibility_and_roles_are_declared(self, name):
        spec = PROFILES[name]
        assert spec["reproducibility"].strip()
        assert spec["default_roles"], f"{name} declares no roles"
        assert "Orchestrator" in spec["default_roles"]

    @pytest.mark.parametrize("name", sorted(PROFILES))
    def test_the_profiles_index_links_the_spec(self, name):
        index = (REPO_ROOT / "profiles" / "README.md").read_text(encoding="utf-8")
        assert f"{name}.md" in index

    @pytest.mark.parametrize("name", sorted(PROFILES))
    def test_recommended_extensions_exist(self, name):
        for relative in PROFILES[name].get("recommended_extensions", []):
            assert (REPO_ROOT / relative).is_dir(), f"{name} recommends a missing {relative}"


class TestInventoryPointsAtRealFiles:
    """Every path the manifest advertises must be in the repository."""

    @pytest.mark.parametrize("key", INVENTORY_KEYS)
    def test_the_listed_paths_exist(self, key):
        missing = [rel for rel in MANIFEST[key] if not (REPO_ROOT / rel).exists()]
        assert not missing, f"{key} lists paths that do not exist: {missing}"

    @pytest.mark.parametrize("key", INVENTORY_KEYS)
    def test_the_inventory_is_not_empty(self, key):
        assert MANIFEST[key]

    def test_every_shipped_prompt_is_listed(self):
        """A new prompt that nobody registers is invisible to anyone reading the manifest."""
        on_disk = {f"prompts/{p.name}" for p in (REPO_ROOT / "prompts").glob("*.md")}
        assert on_disk == set(MANIFEST["prompts"])

    def test_every_shipped_extension_is_listed(self):
        on_disk = {
            f"extensions/{d.name}"
            for d in (REPO_ROOT / "extensions").iterdir()
            if d.is_dir() and not d.name.startswith(("_", "."))
        }
        assert on_disk == set(MANIFEST["extensions"])

    def test_every_profile_spec_on_disk_is_a_known_profile(self):
        """A stray spec file would document a profile the tool rejects."""
        on_disk = {p.stem for p in (REPO_ROOT / "profiles").glob("*.md") if p.stem != "README"}
        assert on_disk == set(KNOWN_PROFILES)


class TestVersionsAreCoherent:
    def test_the_framework_version_looks_like_semver(self):
        parts = MANIFEST["version"].split(".")
        assert len(parts) == 3 and all(p.isdigit() for p in parts)

    def test_the_manifest_is_not_the_package_version(self):
        """DEC-008: the framework contracts and the Python package version apart.

        This is a reminder, not a coincidence — if they are ever made equal it
        should be a deliberate decision rather than a copy-paste.
        """
        import chartworkai

        assert MANIFEST["version"] != chartworkai.__version__
