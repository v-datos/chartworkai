"""Execution and governance semantics for the public adapter API."""

from __future__ import annotations

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import pytest
from conftest import FakeCrew, fake_output, load_manifest, manifests, resolve_record_path

from chartworkai_crewai import CrewAIAdapter, HandoffSpec, RecordWriteError

REQUIRED_MANIFEST_KEYS = {
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
}


def assert_utc_iso8601(value: str) -> None:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.utcoffset() == timezone.utc.utcoffset(parsed)


def test_sync_success_records_a_schema_v1_manifest(project: Path, crew: FakeCrew) -> None:
    record = CrewAIAdapter(project_root=project).kickoff(
        crew,
        inputs={"topic": "public information"},
        task_refs=["T-018"],
    )

    manifest = load_manifest(project, record)
    assert record.output is crew.output
    assert record.run_id.startswith("cwrun_")
    assert record.handoff_path is None
    assert resolve_record_path(project, record.manifest_path).is_file()
    assert REQUIRED_MANIFEST_KEYS <= set(manifest)
    assert manifest["schema_version"] == 1
    assert manifest["run_id"] == record.run_id
    assert manifest["adapter"]["name"] == "chartworkai-crewai"
    assert manifest["adapter"]["version"] == "0.1.0"
    assert manifest["runtime"]["name"] == "crewai"
    assert manifest["runtime"]["api"] == "kickoff"
    assert manifest["chartworkai"] == {
        "project": "Adapter Test Project",
        "profile": "generic",
        "phase": 4,
        "task_refs": ["T-018"],
    }
    assert manifest["crew"]["id"] == str(crew.id)
    assert manifest["crew"]["name"] == "research-crew"
    assert manifest["crew"]["process"] == "sequential"
    assert manifest["crew"]["task_count"] == 1
    assert manifest["execution"]["status"] == "succeeded"
    assert manifest["execution"]["input_keys"] == ["topic"]
    assert manifest["execution"]["error"] is None
    assert manifest["execution"]["duration_ms"] >= 0
    assert_utc_iso8601(manifest["execution"]["started_at"])
    assert_utc_iso8601(manifest["execution"]["ended_at"])
    assert manifest["tasks"][0]["id"] == str(crew.tasks[0].id)
    assert manifest["tasks"][0]["name"] == "research"
    assert manifest["tasks"][0]["agent"] == "Researcher"
    assert manifest["tasks"][0]["output_format"] == "RAW"
    assert manifest["tasks"][0]["tool_failure_count"] == 0
    assert manifest["usage"]["total_tokens"] == 42
    assert manifest["capture"]["mode"] == "metadata"
    assert manifest["capture"]["redactor_id"] == "default-v1"
    assert manifest["capture"]["truncated"] is False
    assert crew.calls == [{"inputs": {"topic": "public information"}}]


def test_async_success_uses_native_akickoff(project: Path, crew: FakeCrew) -> None:
    record = asyncio.run(
        CrewAIAdapter(project_root=project).akickoff(
            crew,
            inputs={"topic": "async"},
            task_refs=["T-018"],
        )
    )

    manifest = load_manifest(project, record)
    assert record.output is crew.output
    assert manifest["runtime"]["api"] == "akickoff"
    assert manifest["execution"]["status"] == "succeeded"
    assert crew.calls == [{"inputs": {"topic": "async"}}]


def test_kickoff_arguments_are_passed_through_unchanged(project: Path, crew: FakeCrew) -> None:
    inputs = {"topic": "passthrough"}
    input_files = {"brief": object()}
    checkpoint = object()

    CrewAIAdapter(project_root=project).kickoff(
        crew,
        inputs=inputs,
        input_files=input_files,
        from_checkpoint=checkpoint,
    )

    assert crew.calls == [
        {
            "inputs": inputs,
            "input_files": input_files,
            "from_checkpoint": checkpoint,
        }
    ]


def test_failed_execution_records_manifest_and_preserves_exception(project: Path, output) -> None:
    original = RuntimeError("crew execution failed")
    crew = FakeCrew(output, error=original)

    with pytest.raises(RuntimeError) as caught:
        CrewAIAdapter(project_root=project).kickoff(crew, inputs={"topic": "failure"})

    assert caught.value is original
    manifest = load_manifest(project)
    assert manifest["execution"]["status"] == "failed"
    assert manifest["execution"]["error"]["type"] == "RuntimeError"
    assert manifest["output"] is None
    assert not list((project / "docs" / "handoffs").glob("*.md"))


def test_recording_failure_after_success_preserves_output(project: Path, crew: FakeCrew) -> None:
    runs = project / "docs" / "integrations" / "crewai" / "runs"
    runs.parent.mkdir(parents=True)
    runs.write_text("not a directory", encoding="utf-8")

    with pytest.raises(RecordWriteError) as caught:
        CrewAIAdapter(project_root=project).kickoff(crew)

    assert caught.value.output is crew.output
    assert len(crew.calls) == 1


def test_concurrent_runs_get_distinct_non_overwriting_records(
    project: Path, crew: FakeCrew
) -> None:
    adapter = CrewAIAdapter(project_root=project)

    with ThreadPoolExecutor(max_workers=8) as pool:
        records = list(
            pool.map(
                lambda index: adapter.kickoff(crew, task_refs=[f"T-{index}"]),
                range(16),
            )
        )

    assert len({record.run_id for record in records}) == 16
    assert len({str(record.manifest_path) for record in records}) == 16
    assert len(manifests(project)) == 16
    assert all(load_manifest(project, record)["run_id"] == record.run_id for record in records)


def test_handoff_is_opt_in_and_references_the_manifest_and_artifacts(
    project: Path, crew: FakeCrew
) -> None:
    artifact = project / "reports" / "result.md"
    artifact.parent.mkdir()
    artifact.write_text("Result\n", encoding="utf-8")

    record = CrewAIAdapter(project_root=project).kickoff(
        crew,
        artifact_paths=["reports/result.md"],
        handoff=HandoffSpec(
            agent="Research Crew",
            next_agent="Reviewer",
            produced="Research result",
            limitations="One tool retry was observed.",
            verification="Review the run manifest and result hash.",
        ),
    )

    assert record.handoff_path is not None
    handoff_path = resolve_record_path(project, record.handoff_path)
    handoff = handoff_path.read_text(encoding="utf-8")
    assert record.run_id in handoff
    assert "docs/integrations/crewai/runs/" in handoff
    assert "reports/result.md" in handoff
    assert "Research Crew" in handoff
    assert "Reviewer" in handoff


def test_tool_failures_are_counted_and_disclosed_in_an_explicit_handoff(
    project: Path,
) -> None:
    crew = FakeCrew(fake_output(tool_failures=[{"tool": "search", "error": "timeout"}]))
    handoff = HandoffSpec(agent="Crew", next_agent="Reviewer", produced="Partial evidence")

    record = CrewAIAdapter(project_root=project).kickoff(crew, handoff=handoff)
    manifest = load_manifest(project, record)
    handoff_text = resolve_record_path(project, record.handoff_path).read_text(encoding="utf-8")

    assert manifest["tasks"][0]["tool_failure_count"] == 1
    assert "1 tool failure(s)" in handoff_text


def test_no_handoff_is_written_when_not_requested(project: Path, crew: FakeCrew) -> None:
    record = CrewAIAdapter(project_root=project).kickoff(crew)

    assert record.handoff_path is None
    assert not list((project / "docs" / "handoffs").glob("*.md"))


def test_no_handoff_is_written_for_failed_execution(project: Path, output) -> None:
    crew = FakeCrew(output, error=RuntimeError("failed"))
    handoff = HandoffSpec(agent="Crew", next_agent="Reviewer", produced="Nothing")

    with pytest.raises(RuntimeError):
        CrewAIAdapter(project_root=project).kickoff(crew, handoff=handoff)

    assert not list((project / "docs" / "handoffs").glob("*.md"))


def test_adapter_never_creates_a_decision(project: Path, crew: FakeCrew) -> None:
    handoff = HandoffSpec(agent="Crew", next_agent="Reviewer", produced="Evidence")
    CrewAIAdapter(project_root=project).kickoff(crew, handoff=handoff)

    assert not (project / "docs" / "decisions").exists()
    serialized = json.dumps(load_manifest(project))
    assert "file_decision" not in serialized
    assert "decision" not in serialized.lower()
