"""Runtime-independent fixtures for the ChartworkAI CrewAI adapter contract."""

from __future__ import annotations

import json
import sys
import threading
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

import pytest

INTEGRATION_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = INTEGRATION_ROOT / "src"
CHARTWORKAI_SOURCE_ROOT = Path(__file__).resolve().parents[3] / "src"
for source_root in (SOURCE_ROOT, CHARTWORKAI_SOURCE_ROOT):
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))


@dataclass
class FakeNamedValue:
    value: str


@dataclass
class FakeAgent:
    role: str


@dataclass
class FakeTaskOutput:
    description: str
    name: str
    expected_output: str
    raw: str
    json_dict: Optional[Dict[str, Any]]
    agent: str
    output_format: FakeNamedValue = field(default_factory=lambda: FakeNamedValue("RAW"))
    pydantic: Any = None
    messages: List[Dict[str, Any]] = field(default_factory=list)
    tool_failures: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class FakeTask:
    id: UUID
    name: str
    agent: FakeAgent
    output_format: FakeNamedValue
    output: FakeTaskOutput


@dataclass
class FakeUsage:
    total_tokens: int = 42
    prompt_tokens: int = 30
    completion_tokens: int = 12

    def model_dump(self, **_kwargs: Any) -> Dict[str, int]:
        return {
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
        }


@dataclass
class FakeCrewOutput:
    raw: str
    json_dict: Optional[Dict[str, Any]]
    tasks_output: List[FakeTaskOutput]
    token_usage: FakeUsage = field(default_factory=FakeUsage)
    pydantic: Any = None


class FakeCrew:
    """The documented public Crew surface used by the adapter, and nothing else."""

    def __init__(self, output: FakeCrewOutput, error: Optional[BaseException] = None) -> None:
        self.id = UUID("11111111-1111-4111-8111-111111111111")
        self.name = "research-crew"
        self.process = FakeNamedValue("sequential")
        self.output = output
        self.error = error
        self.calls: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self.tasks = [
            FakeTask(
                id=UUID("22222222-2222-4222-8222-222222222222"),
                name="research",
                agent=FakeAgent("Researcher"),
                output_format=FakeNamedValue("RAW"),
                output=output.tasks_output[0],
            )
        ]

    def kickoff(self, **kwargs: Any) -> FakeCrewOutput:
        with self._lock:
            self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.output

    async def akickoff(self, **kwargs: Any) -> FakeCrewOutput:
        with self._lock:
            self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.output


def fake_output(
    *,
    raw: str = "A concise governed result.",
    structured: Optional[Dict[str, Any]] = None,
    tool_failures: Optional[List[Dict[str, Any]]] = None,
) -> FakeCrewOutput:
    structured = structured or {"finding": "No material exception."}
    task_output = FakeTaskOutput(
        description="Research the assigned topic.",
        name="research",
        expected_output="A concise result.",
        raw=raw,
        json_dict=structured,
        agent="Researcher",
        tool_failures=tool_failures or [],
    )
    return FakeCrewOutput(raw=raw, json_dict=structured, tasks_output=[task_output])


@pytest.fixture
def output() -> FakeCrewOutput:
    return fake_output()


@pytest.fixture(autouse=True)
def fake_crewai_distribution(monkeypatch):
    """Exercise the adapter without installing or importing the CrewAI runtime."""
    real_version = metadata.version

    def version(distribution_name: str) -> str:
        if distribution_name == "crewai":
            return "1.15.10"
        return real_version(distribution_name)

    monkeypatch.setattr(metadata, "version", version)


@pytest.fixture
def crew(output: FakeCrewOutput) -> FakeCrew:
    return FakeCrew(output)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "governed-project"
    (root / "docs" / "handoffs").mkdir(parents=True)
    (root / "PROJECT_CHARTER.md").write_text(
        "# Project Charter - Adapter Test Project\n\n**Profile:** generic\n",
        encoding="utf-8",
    )
    (root / "docs" / "phase_plan.md").write_text(
        "# Phase Plan\n\n**Current phase:** Phase 4 - integrations\n",
        encoding="utf-8",
    )
    return root


def resolve_record_path(project: Path, value: Any) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project / path


def manifests(project: Path) -> List[Path]:
    return sorted((project / "docs" / "integrations" / "crewai" / "runs").glob("*.json"))


def load_manifest(project: Path, record: Any = None) -> Dict[str, Any]:
    paths = manifests(project)
    if record is None:
        assert len(paths) == 1
        path = paths[0]
    else:
        path = resolve_record_path(project, record.manifest_path)
    return json.loads(path.read_text(encoding="utf-8"))
