"""Artifact integrity and project-confinement tests."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest
from conftest import FakeCrew, load_manifest

from chartworkai_crewai import CrewAIAdapter, RecordWriteError


def test_artifact_is_recorded_by_relative_path_hash_size_and_media_type(
    project: Path, crew: FakeCrew
) -> None:
    content = b"governed report\n"
    artifact = project / "reports" / "result.md"
    artifact.parent.mkdir()
    artifact.write_bytes(content)

    record = CrewAIAdapter(project_root=project).kickoff(
        crew,
        artifact_paths=["reports/result.md"],
    )
    manifest = load_manifest(project, record)

    assert manifest["artifacts"] == [
        {
            "path": "reports/result.md",
            "sha256": hashlib.sha256(content).hexdigest(),
            "size_bytes": len(content),
            "media_type": "text/markdown",
        }
    ]
    serialized = json.dumps(manifest)
    assert str(project.resolve()) not in serialized
    assert str(artifact.resolve()) not in serialized


def test_missing_artifact_is_rejected_after_success_and_output_is_preserved(
    project: Path, crew: FakeCrew
) -> None:
    with pytest.raises(RecordWriteError) as caught:
        CrewAIAdapter(project_root=project).kickoff(
            crew,
            artifact_paths=["reports/missing.md"],
        )

    assert caught.value.output is crew.output
    assert len(crew.calls) == 1


def test_outside_artifact_is_rejected_and_absolute_path_is_never_written(
    project: Path, crew: FakeCrew, tmp_path: Path
) -> None:
    outside = tmp_path / "outside-secret.txt"
    outside.write_text("outside", encoding="utf-8")

    with pytest.raises(RecordWriteError) as caught:
        CrewAIAdapter(project_root=project).kickoff(crew, artifact_paths=[outside])

    assert caught.value.output is crew.output
    for path in project.rglob("*.json"):
        assert str(outside) not in path.read_text(encoding="utf-8")


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
def test_symlinked_artifact_is_rejected(project: Path, crew: FakeCrew, tmp_path: Path) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    link = project / "reports" / "linked.txt"
    link.parent.mkdir()
    link.symlink_to(outside)

    with pytest.raises(RecordWriteError) as caught:
        CrewAIAdapter(project_root=project).kickoff(
            crew,
            artifact_paths=["reports/linked.txt"],
        )

    assert caught.value.output is crew.output


def test_existing_manifest_is_never_overwritten(project: Path, crew: FakeCrew, monkeypatch) -> None:
    """Fix UUID entropy so two executions contend for the same immutable record."""
    from uuid import UUID

    fixed = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    monkeypatch.setattr("uuid.uuid4", lambda: fixed)
    adapter = CrewAIAdapter(project_root=project)
    first = adapter.kickoff(crew)
    first_path = Path(first.manifest_path)
    if not first_path.is_absolute():
        first_path = project / first_path
    original = first_path.read_bytes()

    with pytest.raises(RecordWriteError) as caught:
        adapter.kickoff(crew)

    assert caught.value.output is crew.output
    assert first_path.read_bytes() == original
    assert len(list(first_path.parent.glob("*.json"))) == 1
