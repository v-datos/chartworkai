"""Custom profiles are bounded project data, never executable configuration."""

from __future__ import annotations

import json

import pytest

from chartworkai.profile_config import (
    MAX_PROFILE_BYTES,
    ProfileConfigError,
    effective_custom_profile,
    load_custom_profile,
    validate_custom_profile,
)


def definition(**overrides):
    value = {
        "schema_version": 1,
        "name": "legal-research",
        "description": "Evidence-backed legal research.",
        "extends": "generic",
        "required_files": ["docs/evidence/source_register.md"],
        "required_directories": ["docs/evidence"],
        "scaffold_directories": ["docs/evidence"],
        "default_roles": [
            "Orchestrator",
            "Legal Researcher",
            "QA / Reproducibility Engineer",
        ],
        "validation_commands": ["make verify"],
    }
    value.update(overrides)
    return value


class TestCustomProfileSchema:
    def test_a_complete_profile_is_normalized(self):
        assert validate_custom_profile(definition()) == definition()

    @pytest.mark.parametrize("extends", ["generic", "software-app", "data-science"])
    def test_a_custom_profile_can_extend_the_core_or_a_preset(self, extends):
        assert validate_custom_profile(definition(extends=extends))["extends"] == extends

    def test_a_data_preset_contributes_its_existing_contract(self):
        custom = effective_custom_profile(
            validate_custom_profile(definition(extends="data-science"))
        )
        assert custom["requires_data_contracts"] is True
        assert "docs/data/data_dictionary.md" in custom["required_files"]
        assert "docs/evidence/source_register.md" in custom["required_files"]

    @pytest.mark.parametrize(
        "bad_path",
        [
            "/tmp/escape",
            "../escape",
            "docs/../escape",
            "docs\\escape",
            "C:/Windows/System32",
            ".",
            "docs//x",
        ],
    )
    def test_artifact_paths_must_stay_inside_the_project(self, bad_path):
        with pytest.raises(ProfileConfigError, match="project-relative POSIX paths"):
            validate_custom_profile(definition(required_files=[bad_path]))

    def test_unknown_fields_are_rejected_instead_of_ignored(self):
        with pytest.raises(ProfileConfigError, match="unknown fields: requred_files"):
            validate_custom_profile(definition(requred_files=[]))

    def test_builtin_names_cannot_be_shadowed(self):
        with pytest.raises(ProfileConfigError, match="conflicts with a built-in profile"):
            validate_custom_profile(definition(name="software-app"))

    def test_universal_artifacts_cannot_be_redeclared(self):
        with pytest.raises(ProfileConfigError, match="repeats universal framework artifacts"):
            validate_custom_profile(definition(required_files=["STATUS.md"]))

    def test_orchestrator_remains_part_of_the_core_contract(self):
        with pytest.raises(ProfileConfigError, match="must include Orchestrator"):
            validate_custom_profile(definition(default_roles=["Researcher", "QA"]))

    def test_quality_authority_remains_part_of_the_core_contract(self):
        with pytest.raises(ProfileConfigError, match="must include a QA"):
            validate_custom_profile(definition(default_roles=["Orchestrator", "Researcher"]))

    def test_validation_commands_are_data_and_must_be_single_line(self):
        with pytest.raises(ProfileConfigError, match="single-line"):
            validate_custom_profile(definition(validation_commands=["make test\nrm -rf /"]))


class TestCustomProfileFileSafety:
    def test_loads_a_regular_bounded_json_file(self, tmp_path):
        path = tmp_path / "profile.json"
        path.write_text(json.dumps(definition()), encoding="utf-8")
        assert load_custom_profile(path)["name"] == "legal-research"

    def test_rejects_a_symlink(self, tmp_path):
        target = tmp_path / "target.json"
        target.write_text(json.dumps(definition()), encoding="utf-8")
        link = tmp_path / "profile.json"
        link.symlink_to(target)
        with pytest.raises(ProfileConfigError, match="symlinked"):
            load_custom_profile(link)

    def test_rejects_an_oversized_file_before_parsing(self, tmp_path):
        path = tmp_path / "profile.json"
        path.write_text("x" * (MAX_PROFILE_BYTES + 1), encoding="utf-8")
        with pytest.raises(ProfileConfigError, match="size limit"):
            load_custom_profile(path)
