"""Distribution-level public API and schema contract tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from importlib import resources
from pathlib import Path
from typing import Any, Dict, Iterable

from conftest import load_manifest

import chartworkai_crewai
from chartworkai_crewai import (
    CapturePolicy,
    CrewAIAdapter,
    HandoffSpec,
    RecordedRun,
    RecordWriteError,
)

PUBLIC_NAMES = {
    "CapturePolicy",
    "CrewAIAdapter",
    "HandoffSpec",
    "RecordedRun",
    "RecordWriteError",
}


def json_resources(node) -> Iterable[Any]:
    for child in node.iterdir():
        if child.is_dir():
            yield from json_resources(child)
        elif child.name.endswith(".json"):
            yield child


def load_schema() -> Dict[str, Any]:
    candidates = []
    for resource in json_resources(resources.files("chartworkai_crewai")):
        data = json.loads(resource.read_text(encoding="utf-8"))
        version = data.get("properties", {}).get("schema_version", {})
        if version.get("const") == 1:
            candidates.append(data)
    assert len(candidates) == 1, "ship exactly one discoverable run-manifest schema for v1"
    return candidates[0]


def assert_schema_type(value: Any, expected: str) -> None:
    checks = {
        "array": lambda item: isinstance(item, list),
        "boolean": lambda item: isinstance(item, bool),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "null": lambda item: item is None,
        "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
        "object": lambda item: isinstance(item, dict),
        "string": lambda item: isinstance(item, str),
    }
    assert checks[expected](value)


def test_public_api_is_exported_from_package_root() -> None:
    assert PUBLIC_NAMES <= set(chartworkai_crewai.__all__)
    assert CapturePolicy is chartworkai_crewai.CapturePolicy
    assert CrewAIAdapter is chartworkai_crewai.CrewAIAdapter
    assert HandoffSpec is chartworkai_crewai.HandoffSpec
    assert RecordedRun is chartworkai_crewai.RecordedRun
    assert RecordWriteError is chartworkai_crewai.RecordWriteError


def test_package_import_does_not_require_or_import_crewai() -> None:
    source_root = Path(__file__).resolve().parents[1] / "src"
    chartworkai_source = Path(__file__).resolve().parents[3] / "src"
    code = """
import importlib.abc
import sys

class RefuseCrewAI(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "crewai" or fullname.startswith("crewai."):
            raise RuntimeError("chartworkai_crewai attempted to import CrewAI")
        return None

sys.meta_path.insert(0, RefuseCrewAI())
import chartworkai_crewai
assert "crewai" not in sys.modules
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(source_root), str(chartworkai_source), env.get("PYTHONPATH", "")]
    )

    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr


def test_distribution_metadata_uses_and_ships_the_strict_readme() -> None:
    integration_root = Path(__file__).resolve().parents[1]
    pyproject = (integration_root / "pyproject.toml").read_text(encoding="utf-8")
    project_section = pyproject.split("[project]", 1)[1].split("\n[", 1)[0]
    sdist_section = pyproject.split("[tool.hatch.build.targets.sdist]", 1)[1].split("\n[", 1)[0]

    assert (integration_root / "README.md").is_file()
    assert 'readme = "README.md"' in project_section
    assert '"/README.md"' in sdist_section

    dependency_block = project_section.split("dependencies = [", 1)[1].split("]", 1)[0].lower()
    assert "crewai" not in dependency_block
    assert "chromadb" not in dependency_block


def test_schema_v1_is_packaged_and_declares_the_manifest_shape() -> None:
    schema = load_schema()

    assert schema["$schema"].startswith("https://json-schema.org/")
    assert schema["type"] == "object"
    assert schema.get("additionalProperties") is False
    assert {
        "schema_version",
        "run_id",
        "adapter",
        "runtime",
        "chartworkai",
        "crew",
        "execution",
        "tasks",
        "usage",
        "artifacts",
        "capture",
        "output",
    } <= set(schema["required"])
    assert schema["properties"]["run_id"]["pattern"].startswith("^cwrun_")


def test_generated_manifest_satisfies_required_top_level_schema_types(project: Path, crew) -> None:
    record = CrewAIAdapter(project_root=project).kickoff(crew)
    manifest = load_manifest(project, record)
    schema = load_schema()

    for key in schema["required"]:
        assert key in manifest
    for key, rule in schema["properties"].items():
        if key not in manifest or "type" not in rule:
            continue
        expected = rule["type"]
        if isinstance(expected, list):
            assert any(
                _value_matches_schema_type(manifest[key], candidate) for candidate in expected
            )
        else:
            assert_schema_type(manifest[key], expected)


def _value_matches_schema_type(value: Any, expected: str) -> bool:
    try:
        assert_schema_type(value, expected)
    except AssertionError:
        return False
    return True
