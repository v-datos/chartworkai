"""Regression tests for security boundaries in CrewAI execution recording."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pytest
from conftest import FakeCrew, fake_output, load_manifest, manifests

from chartworkai_crewai import CapturePolicy, CrewAIAdapter, HandoffSpec, RecordWriteError


def test_metadata_failure_does_not_persist_raw_email_path_or_github_token(
    project: Path, output
) -> None:
    email = "alice.private@example.com"
    private_path = "/Users/alice/Clients/secret/customer.csv"
    github_token = "gh" + "p_" + ("A" * 36)
    error = RuntimeError(f"notify {email}; read {private_path}; token={github_token}")

    with pytest.raises(RuntimeError) as caught:
        CrewAIAdapter(project_root=project).kickoff(FakeCrew(output, error=error))

    assert caught.value is error
    manifest = load_manifest(project)
    serialized = json.dumps(manifest, sort_keys=True)
    assert manifest["execution"]["error"] == {
        "type": "RuntimeError",
        "message_sha256": hashlib.sha256(str(error).encode("utf-8")).hexdigest(),
    }
    assert email not in serialized
    assert private_path not in serialized
    assert github_token not in serialized


def test_reused_crew_failure_does_not_reuse_stale_task_completion_or_output(
    project: Path,
) -> None:
    stale = "prior-success-output-must-not-enter-the-failed-run"
    crew = FakeCrew(fake_output(raw=stale, structured={"result": stale}))
    adapter = CrewAIAdapter(project_root=project, capture=CapturePolicy(mode="full"))
    adapter.kickoff(crew)

    failure = RuntimeError("second execution failed")
    crew.error = failure
    with pytest.raises(RuntimeError) as caught:
        adapter.kickoff(crew)

    assert caught.value is failure
    records = [json.loads(path.read_text(encoding="utf-8")) for path in manifests(project)]
    failed = next(record for record in records if record["execution"]["status"] == "failed")
    assert failed["output"] is None
    assert failed["usage"] == {}
    assert failed["tasks"] == []
    assert stale not in json.dumps(failed, sort_keys=True)


@pytest.mark.parametrize("mode", ["summary", "full"])
def test_content_capture_failure_message_is_redacted_and_bounded(
    project: Path, output, mode: str
) -> None:
    email = "alice.private@example.com"
    private_path = "/Users/alice/Clients/secret/customer.csv"
    github_token = "gh" + "p_" + ("A" * 36)
    raw_message = f"{email} {private_path} {github_token} " + ("sensitive " * 1_000)
    policy = CapturePolicy(
        mode=mode,
        summarizer=(lambda _output: {}) if mode == "summary" else None,
    )

    with pytest.raises(RuntimeError):
        CrewAIAdapter(project_root=project, capture=policy).kickoff(
            FakeCrew(output, error=RuntimeError(raw_message))
        )

    error = load_manifest(project)["execution"]["error"]
    assert error["type"] == "RuntimeError"
    assert len(error["message"].encode("utf-8")) <= 2 * 1024
    assert email not in error["message"]
    assert private_path not in error["message"]
    assert github_token not in error["message"]


def test_async_cancellation_records_cancelled_manifest_and_reraises_original(
    project: Path, output
) -> None:
    cancellation = asyncio.CancelledError("caller cancelled the governed run")
    crew = FakeCrew(output, error=cancellation)

    with pytest.raises(asyncio.CancelledError) as caught:
        asyncio.run(CrewAIAdapter(project_root=project).akickoff(crew))

    assert caught.value is cancellation
    manifest = load_manifest(project)
    assert manifest["execution"]["status"] == "cancelled"
    assert manifest["execution"]["error"]["type"] == "CancelledError"
    assert manifest["output"] is None
    assert manifest["tasks"] == []


def test_final_manifest_name_is_never_visible_with_partial_json(
    project: Path, crew: FakeCrew, monkeypatch
) -> None:
    real_write = os.write
    interrupted = False

    def interrupted_write(descriptor: int, content) -> int:
        nonlocal interrupted
        interrupted = True
        midpoint = max(1, len(content) // 2)
        real_write(descriptor, content[:midpoint])
        raise OSError("injected interruption during manifest write")

    monkeypatch.setattr(os, "write", interrupted_write)

    with pytest.raises(RecordWriteError) as caught:
        CrewAIAdapter(project_root=project).kickoff(crew)

    assert interrupted is True
    assert caught.value.output is crew.output
    run_directory = project / "docs" / "integrations" / "crewai" / "runs"
    assert list(run_directory.glob("*.json")) == []
    assert list(run_directory.glob(".*.tmp")) == []
    assert list(run_directory.iterdir()) == []


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
def test_parent_directory_symlink_swap_cannot_escape_artifact_hashing(
    project: Path, crew: FakeCrew, tmp_path: Path, monkeypatch
) -> None:
    approved_content = b"approved project artifact\n"
    outside_content = b"outside project secret\n"
    parent = project / "reports" / "stable-parent"
    parked_parent = project / "reports" / "stable-parent-before-swap"
    outside_parent = tmp_path / "outside-project"
    parent.mkdir(parents=True)
    outside_parent.mkdir()
    artifact_name = "result.txt"
    artifact = parent / artifact_name
    artifact.write_bytes(approved_content)
    (outside_parent / artifact_name).write_bytes(outside_content)
    real_open = os.open
    swapped = False

    def swapping_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        path_text = os.fspath(path)
        opening_artifact = path_text == str(artifact) or (
            path_text == artifact_name and dir_fd is not None
        )
        if opening_artifact and not swapped:
            parent.rename(parked_parent)
            parent.symlink_to(outside_parent, target_is_directory=True)
            swapped = True
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", swapping_open)
    monkeypatch.setattr(os, "supports_dir_fd", set(os.supports_dir_fd) | {swapping_open})

    try:
        record = CrewAIAdapter(project_root=project).kickoff(
            crew,
            artifact_paths=["reports/stable-parent/result.txt"],
        )
    except RecordWriteError:
        assert manifests(project) == []
    else:
        manifest = load_manifest(project, record)
        assert manifest["artifacts"][0]["sha256"] == hashlib.sha256(approved_content).hexdigest()
        assert manifest["artifacts"][0]["sha256"] != hashlib.sha256(outside_content).hexdigest()

    assert swapped is True


@pytest.mark.parametrize(
    "artifact_path",
    [
        "reports/result\n## injected-heading.md",
        "reports/`injected-code-span`.md",
    ],
)
def test_newline_or_backtick_artifact_path_is_rejected(
    project: Path, crew: FakeCrew, artifact_path: str
) -> None:
    path = project / artifact_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("maliciously named but otherwise valid", encoding="utf-8")

    with pytest.raises(ValueError):
        CrewAIAdapter(project_root=project).kickoff(crew, artifact_paths=[artifact_path])

    assert crew.calls == []
    assert manifests(project) == []


@pytest.mark.parametrize("field", ["agent", "next_agent"])
@pytest.mark.parametrize("malicious", ["Reviewer\n## injected-heading", "`Reviewer`"])
def test_newline_or_backtick_handoff_identity_is_rejected(field: str, malicious: str) -> None:
    values = {"agent": "Crew", "next_agent": "Reviewer", "produced": "Evidence"}
    values[field] = malicious

    with pytest.raises(ValueError):
        HandoffSpec(**values)


@pytest.mark.parametrize(
    "field,limit",
    [
        ("agent", 120),
        ("next_agent", 120),
        ("produced", 2_000),
        ("limitations", 4_000),
        ("verification", 2_000),
    ],
)
def test_handoff_field_length_boundary(field: str, limit: int) -> None:
    values = {"agent": "Crew", "next_agent": "Reviewer", "produced": "Evidence"}
    values[field] = "x" * limit
    HandoffSpec(**values)

    values[field] = "x" * (limit + 1)
    with pytest.raises(ValueError):
        HandoffSpec(**values)


@pytest.mark.parametrize(
    "field",
    ["agent", "next_agent", "produced", "limitations", "verification"],
)
@pytest.mark.parametrize(
    "malicious",
    [
        "text\x00control",
        "# injected H1",
        "## injected H2",
        "{{UNRESOLVED_PLACEHOLDER}}",
    ],
)
def test_handoff_rejects_controls_headings_and_placeholders_before_execution(
    field: str, malicious: str
) -> None:
    values = {"agent": "Crew", "next_agent": "Reviewer", "produced": "Evidence"}
    values[field] = malicious

    with pytest.raises(ValueError):
        HandoffSpec(**values)


def test_exactly_256_input_keys_are_allowed(project: Path, crew: FakeCrew) -> None:
    inputs = {f"key_{index:03d}": index for index in range(256)}

    record = CrewAIAdapter(project_root=project).kickoff(crew, inputs=inputs)

    assert len(load_manifest(project, record)["execution"]["input_keys"]) == 256


def test_more_than_256_input_keys_are_rejected_before_execution(
    project: Path, crew: FakeCrew
) -> None:
    inputs = {f"key_{index:03d}": index for index in range(257)}

    with pytest.raises(ValueError):
        CrewAIAdapter(project_root=project).kickoff(crew, inputs=inputs)

    assert crew.calls == []
    assert manifests(project) == []


def _crew_with_task_count(count: int) -> FakeCrew:
    output = fake_output()
    crew = FakeCrew(output)
    crew.tasks = crew.tasks * count
    output.tasks_output = output.tasks_output * count
    return crew


def test_exactly_1000_tasks_are_allowed(project: Path) -> None:
    crew = _crew_with_task_count(1_000)

    CrewAIAdapter(project_root=project).kickoff(crew)

    assert len(crew.calls) == 1


def test_more_than_1000_tasks_are_rejected_before_execution(project: Path) -> None:
    crew = _crew_with_task_count(1_001)

    with pytest.raises(ValueError):
        CrewAIAdapter(project_root=project).kickoff(crew)

    assert crew.calls == []
    assert manifests(project) == []


def test_excessive_artifact_count_is_rejected(project: Path, crew: FakeCrew) -> None:
    artifact = project / "reports" / "one.txt"
    artifact.parent.mkdir()
    artifact.write_text("one", encoding="utf-8")

    with pytest.raises(ValueError):
        CrewAIAdapter(project_root=project).kickoff(
            crew,
            artifact_paths=["reports/one.txt"] * 257,
        )

    assert crew.calls == []
    assert manifests(project) == []


def test_exactly_256_artifacts_are_allowed(project: Path, crew: FakeCrew) -> None:
    artifact_root = project / "reports"
    artifact_root.mkdir()
    paths = []
    for index in range(256):
        relative = f"reports/artifact_{index:03d}.txt"
        (project / relative).write_text(str(index), encoding="utf-8")
        paths.append(relative)

    record = CrewAIAdapter(project_root=project).kickoff(crew, artifact_paths=paths)

    assert len(load_manifest(project, record)["artifacts"]) == 256


def test_default_output_budget_is_256_kib_and_truncates_content(
    project: Path,
) -> None:
    policy = CapturePolicy(mode="full")
    large = "x" * ((256 * 1024) + 1)
    crew = FakeCrew(fake_output(raw=large, structured={"payload": large}))

    assert policy.max_bytes == 256 * 1024
    try:
        record = CrewAIAdapter(project_root=project, capture=policy).kickoff(crew)
    except RecordWriteError as exc:
        assert exc.output is crew.output
        assert manifests(project) == []
    else:
        manifest = load_manifest(project, record)
        assert manifest["capture"]["truncated"] is True
        assert large not in json.dumps(manifest)


def test_final_manifest_never_exceeds_one_mib(project: Path, crew: FakeCrew) -> None:
    inputs = {f"key_{index:03d}_" + ("x" * 20_000): None for index in range(64)}

    try:
        record = CrewAIAdapter(project_root=project).kickoff(crew, inputs=inputs)
    except RecordWriteError:
        assert manifests(project) == []
    else:
        assert Path(record.manifest_path).stat().st_size <= 1024 * 1024


@pytest.mark.parametrize("shape", ["cycle", "deep"])
def test_cyclic_or_excessively_deep_full_capture_fails_closed(project: Path, shape: str) -> None:
    structured: dict[str, Any] = {}
    if shape == "cycle":
        structured["self"] = structured
    else:
        cursor = structured
        for _ in range(2_000):
            child: dict[str, Any] = {}
            cursor["next"] = child
            cursor = child

    output = fake_output(structured=structured)
    crew = FakeCrew(output)
    adapter = CrewAIAdapter(project_root=project, capture=CapturePolicy(mode="full"))

    try:
        record = adapter.kickoff(crew)
    except RecordWriteError as exc:
        assert exc.output is output
        assert manifests(project) == []
    else:
        manifest = load_manifest(project, record)
        assert manifest["capture"]["truncated"] is True
        json.dumps(manifest, allow_nan=False)
