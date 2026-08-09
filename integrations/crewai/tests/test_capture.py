"""Capture modes, redaction, and data-minimisation guarantees."""

from __future__ import annotations

import json
from pathlib import Path

from conftest import FakeCrew, fake_output, load_manifest

from chartworkai_crewai import CapturePolicy, CrewAIAdapter


def manifest_text(project: Path, record) -> str:
    return json.dumps(load_manifest(project, record), sort_keys=True)


def test_metadata_is_the_default_and_persists_no_output_content(project: Path) -> None:
    secret_result = "private-result-that-must-not-be-recorded"
    crew = FakeCrew(fake_output(raw=secret_result, structured={"result": secret_result}))

    record = CrewAIAdapter(project_root=project).kickoff(crew)
    manifest = load_manifest(project, record)

    assert manifest["capture"]["mode"] == "metadata"
    assert manifest["output"] is None
    assert secret_result not in manifest_text(project, record)
    assert "raw" not in manifest["tasks"][0]
    assert "json" not in manifest["tasks"][0]


def test_summary_captures_only_the_callers_summary(project: Path) -> None:
    raw = "long private underlying output"
    crew = FakeCrew(fake_output(raw=raw, structured={"private": raw}))
    policy = CapturePolicy(
        mode="summary",
        summarizer=lambda output: {"summary": "Approved summary", "quality": "reviewed"},
    )

    record = CrewAIAdapter(project_root=project, capture=policy).kickoff(crew)
    manifest = load_manifest(project, record)

    assert manifest["capture"]["mode"] == "summary"
    assert manifest["output"] == {
        "summary": "Approved summary",
        "quality": "reviewed",
    }
    assert raw not in manifest_text(project, record)


def test_full_capture_records_redacted_crew_and_task_outputs(project: Path) -> None:
    crew = FakeCrew(
        fake_output(
            raw="shareable raw result",
            structured={"finding": "shareable structured result"},
        )
    )

    record = CrewAIAdapter(
        project_root=project,
        capture=CapturePolicy(mode="full"),
    ).kickoff(crew)
    serialized = manifest_text(project, record)

    assert "shareable raw result" in serialized
    assert "shareable structured result" in serialized
    assert load_manifest(project, record)["capture"]["mode"] == "full"


def test_full_capture_recursively_redacts_secret_keys_and_bearer_tokens(project: Path) -> None:
    api_secret = "test-secret-value"
    secrets = {
        "api_key": api_secret,
        "password": "correct-horse-battery-staple",
        "nested": {"authorization": "Bearer top-secret-token"},
        "safe": "retain this value",
    }
    crew = FakeCrew(fake_output(raw="Bearer raw-secret-token", structured=secrets))

    record = CrewAIAdapter(
        project_root=project,
        capture=CapturePolicy(mode="full"),
    ).kickoff(crew)
    serialized = manifest_text(project, record)

    assert "retain this value" in serialized
    assert api_secret not in serialized
    assert "correct-horse-battery-staple" not in serialized
    assert "top-secret-token" not in serialized
    assert "raw-secret-token" not in serialized
    assert "redact" in serialized.lower()


def test_input_values_are_never_written_even_in_full_capture(project: Path) -> None:
    input_secret = "input-only-secret-7d47e8"
    crew = FakeCrew(fake_output())

    record = CrewAIAdapter(
        project_root=project,
        capture=CapturePolicy(mode="full"),
    ).kickoff(
        crew,
        inputs={"customer_token": input_secret, "topic": "also private"},
    )
    manifest = load_manifest(project, record)
    serialized = manifest_text(project, record)

    assert manifest["execution"]["input_keys"] == ["customer_token", "topic"]
    assert input_secret not in serialized
    assert "also private" not in serialized


def test_capture_limit_truncates_deterministically_and_marks_manifest(project: Path) -> None:
    large_value = "large-output-marker-" + ("x" * 50_000)
    crew = FakeCrew(fake_output(raw=large_value, structured={"payload": large_value}))
    policy = CapturePolicy(mode="full", max_bytes=4096)

    record = CrewAIAdapter(project_root=project, capture=policy).kickoff(crew)
    manifest = load_manifest(project, record)
    serialized = manifest_text(project, record)
    manifest_path = Path(record.manifest_path)
    if not manifest_path.is_absolute():
        manifest_path = project / manifest_path

    assert manifest["capture"]["truncated"] is True
    assert large_value not in serialized
    assert len(serialized.encode("utf-8")) < len(large_value.encode("utf-8"))
    assert manifest_path.stat().st_size <= policy.max_bytes
