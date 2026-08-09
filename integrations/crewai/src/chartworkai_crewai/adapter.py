"""Local, non-streaming CrewAI execution recording."""

from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import mimetypes
import os
import re
import stat
import time
import uuid
from importlib import metadata
from pathlib import Path
from typing import Any, Iterable

from chartworkai.safety import resolve_within, safe_mkdir
from chartworkai.state import file_handoff, read_state

from . import __version__
from .capture import (
    MAX_OUTPUT_BYTES,
    CaptureBudget,
    CaptureLimitError,
    apply_redaction,
    fit_to_limit,
    json_value,
    redact_text,
    serialize,
    truncate_utf8,
)
from .models import CapturePolicy, HandoffSpec, RecordedRun, RecordWriteError
from .schema import validate_manifest

_RUN_DIRECTORY = "docs/integrations/crewai/runs"
_DIRECTORY_CREATE_ATTEMPTS = 3
_TEMP_CREATE_ATTEMPTS = 3
_SUPPORTED_VERSION = re.compile(r"^1\.15\.(\d+)(?:\D.*)?$")
_MAX_INPUT_KEYS = 256
_MAX_TASK_RECORDS = 1_000
_MAX_ARTIFACTS = 256
_MAX_ARTIFACT_BYTES = 64 * 1024 * 1024
_MAX_TOTAL_ARTIFACT_BYTES = 256 * 1024 * 1024
_MAX_ARTIFACT_PATH_CHARS = 1_024
_MAX_TASK_REFS = 256
_MAX_TASK_REF_CHARS = 256
_MAX_METADATA_CHARS = 512
_MAX_ERROR_MESSAGE_BYTES = 2 * 1024
_MAX_HANDOFF_ARTIFACT_LINES = 32
_MAX_HANDOFF_LIMITATIONS_CHARS = 4_000
_DIRECTORY_OPEN_FLAG = getattr(os, "O_DIRECTORY", 0)
_NOFOLLOW_OPEN_FLAG = getattr(os, "O_NOFOLLOW", 0)
_OPEN_SUPPORTS_DIR_FD = os.open in getattr(os, "supports_dir_fd", set())
_USAGE_FIELDS = (
    "total_tokens",
    "prompt_tokens",
    "cached_prompt_tokens",
    "completion_tokens",
    "reasoning_tokens",
    "cache_creation_tokens",
    "successful_requests",
)


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _timestamp(value: dt.datetime) -> str:
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _enum_value(value: Any) -> str | None:
    if value is None:
        return None
    return _bounded_text(getattr(value, "value", value), "enum value", _MAX_METADATA_CHARS)


def _public_id(value: Any) -> str | None:
    if value is None:
        return None
    return _bounded_text(value, "public id", _MAX_METADATA_CHARS)


def _bounded_text(value: Any, label: str, max_chars: int) -> str:
    text = value if isinstance(value, str) else str(value)
    if len(text) > max_chars:
        raise ValueError(f"{label} exceeds the {max_chars}-character limit")
    return text


def _bounded_tuple(values: Iterable[Any], limit: int, label: str) -> tuple[Any, ...]:
    iterator = iter(values)
    items = []
    for _ in range(limit + 1):
        try:
            items.append(next(iterator))
        except StopIteration:
            break
    if len(items) > limit:
        raise ValueError(f"{label} exceeds the {limit}-item limit")
    return tuple(items)


def _has_control_characters(value: str) -> bool:
    return any(ord(character) < 32 or 127 <= ord(character) <= 159 for character in value)


def _runtime_version() -> str:
    try:
        version = metadata.version("crewai")
    except metadata.PackageNotFoundError as exc:
        raise RuntimeError(
            "CrewAI is not installed; install a supported CrewAI runtime separately"
        ) from exc
    match = _SUPPORTED_VERSION.match(version)
    if match is None or int(match.group(1)) < 10:
        raise RuntimeError(
            f"unsupported CrewAI version {version}; chartworkai-crewai 0.1 supports "
            "CrewAI >=1.15.10,<1.16"
        )
    return version


def _input_keys(inputs: dict[str, Any] | None) -> tuple[list[str], int, bool]:
    if not inputs:
        return [], 0, False
    if len(inputs) > _MAX_INPUT_KEYS:
        raise ValueError(f"inputs exceeds the {_MAX_INPUT_KEYS}-key limit")
    keys = []
    truncated = False
    for key in inputs:
        text = key if isinstance(key, str) else str(key)
        if len(text) > _MAX_METADATA_CHARS:
            digest = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]
            suffix = f"...[sha256:{digest}]"
            text = text[: _MAX_METADATA_CHARS - len(suffix)] + suffix
            truncated = True
        keys.append(text)
    return sorted(keys), 0, truncated


def _task_refs(values: Iterable[str]) -> tuple[str, ...]:
    refs = _bounded_tuple(values, _MAX_TASK_REFS, "task_refs")
    return tuple(_bounded_text(value, "task reference", _MAX_TASK_REF_CHARS) for value in refs)


def _artifact_paths(values: Iterable[str | Path]) -> tuple[str | Path, ...]:
    paths = _bounded_tuple(values, _MAX_ARTIFACTS, "artifact_paths")
    for value in paths:
        text = str(value)
        if not text:
            raise ValueError("artifact path must not be empty")
        if len(text) > _MAX_ARTIFACT_PATH_CHARS:
            raise ValueError(
                f"artifact path exceeds the {_MAX_ARTIFACT_PATH_CHARS}-character limit"
            )
        if _has_control_characters(text):
            raise ValueError("artifact path contains unsupported control characters")
        if "`" in text:
            raise ValueError("artifact path must not contain backticks")
    return paths


def _bounded_sequence(value: Any, limit: int) -> tuple[list[Any], int]:
    if value is None:
        return [], 0
    total = len(value)
    return list(value[:limit]), max(0, total - limit)


def _structured_output(output: Any, budget: CaptureBudget) -> Any | None:
    json_dict = getattr(output, "json_dict", None)
    if json_dict is not None:
        return json_value(json_dict, budget)
    pydantic = getattr(output, "pydantic", None)
    if pydantic is not None:
        return json_value(pydantic, budget)
    return None


def _task_records(
    crew: Any,
    output: Any,
    mode: str,
    budget: CaptureBudget | None,
) -> tuple[list[dict[str, Any]], int, int]:
    crew_tasks_source = getattr(crew, "tasks", []) or []
    crew_tasks, omitted_crew_tasks = _bounded_sequence(crew_tasks_source, _MAX_TASK_RECORDS)
    outputs_source = getattr(output, "tasks_output", []) or []
    outputs, omitted_outputs = _bounded_sequence(outputs_source, _MAX_TASK_RECORDS)
    count = max(len(crew_tasks), len(outputs))
    omitted = max(omitted_crew_tasks, omitted_outputs)
    records: list[dict[str, Any]] = []
    for index in range(count):
        task = crew_tasks[index] if index < len(crew_tasks) else None
        task_output = outputs[index] if index < len(outputs) else None
        agent = getattr(task_output, "agent", None)
        if agent is None and task is not None:
            agent = getattr(getattr(task, "agent", None), "role", None)
        name = getattr(task_output, "name", None)
        if name is None and task is not None:
            name = getattr(task, "name", None)
        record: dict[str, Any] = {
            "index": index,
            "id": _public_id(getattr(task, "id", None)),
            "name": (
                None if name is None else _bounded_text(name, "task name", _MAX_METADATA_CHARS)
            ),
            "agent": (
                None if agent is None else _bounded_text(agent, "task agent", _MAX_METADATA_CHARS)
            ),
            "status": "completed" if task_output is not None else "not_completed",
            "output_format": _enum_value(getattr(task_output, "output_format", None)),
            "tool_failure_count": len(getattr(task_output, "tool_failures", []) or []),
        }
        if mode == "full" and task_output is not None:
            if budget is None:
                raise CaptureLimitError("full capture requires an output budget")
            record["content"] = {
                "raw": json_value(getattr(task_output, "raw", ""), budget),
                "structured": _structured_output(task_output, budget),
            }
        records.append(record)
    return records, omitted, len(crew_tasks_source)


def _usage(output: Any) -> dict[str, int]:
    value = getattr(output, "usage_metrics", None)
    if value is None:
        token_usage = getattr(output, "token_usage", None)
        model_dump = getattr(token_usage, "model_dump", None)
        value = model_dump() if callable(model_dump) else token_usage
    if not isinstance(value, dict):
        return {}
    usage: dict[str, int] = {}
    for field in _USAGE_FIELDS:
        item = value.get(field)
        if isinstance(item, int) and not isinstance(item, bool) and item >= 0:
            usage[field] = item
    return usage


def _open_confined_artifact(root: Path, relative: Path) -> int:
    """Open an artifact by walking from an anchored project-root descriptor."""
    if not _DIRECTORY_OPEN_FLAG or not _NOFOLLOW_OPEN_FLAG or not _OPEN_SUPPORTS_DIR_FD:
        raise OSError("this platform lacks descriptor-anchored, no-follow artifact traversal")
    if not relative.parts:
        raise ValueError("artifact path must name a file")

    directory_flags = (
        os.O_RDONLY | _DIRECTORY_OPEN_FLAG | _NOFOLLOW_OPEN_FLAG | getattr(os, "O_CLOEXEC", 0)
    )
    directory_descriptor = os.open(root, directory_flags)
    try:
        for component in relative.parts[:-1]:
            next_descriptor = os.open(
                component,
                directory_flags,
                dir_fd=directory_descriptor,
            )
            try:
                os.close(directory_descriptor)
            except Exception:
                os.close(next_descriptor)
                raise
            directory_descriptor = next_descriptor

        file_flags = (
            os.O_RDONLY
            | _NOFOLLOW_OPEN_FLAG
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        descriptor = os.open(
            relative.parts[-1],
            file_flags,
            dir_fd=directory_descriptor,
        )
    except Exception:
        os.close(directory_descriptor)
        raise
    try:
        os.close(directory_descriptor)
    except Exception:
        os.close(descriptor)
        raise
    return descriptor


def _artifact_record(root: Path, relative_value: str | Path) -> dict[str, Any]:
    relative = Path(relative_value)
    path = resolve_within(root, str(relative))
    descriptor = _open_confined_artifact(root, relative)
    try:
        file_stat = os.fstat(descriptor)
        if not stat.S_ISREG(file_stat.st_mode):
            raise FileNotFoundError(f"artifact is not a regular file: {relative}")
        if file_stat.st_size > _MAX_ARTIFACT_BYTES:
            raise ValueError(f"artifact {relative} exceeds the {_MAX_ARTIFACT_BYTES}-byte limit")
        digest = hashlib.sha256()
        size = 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, _MAX_ARTIFACT_BYTES + 1 - size))
            if not chunk:
                break
            size += len(chunk)
            if size > _MAX_ARTIFACT_BYTES:
                raise ValueError(
                    f"artifact {relative} exceeds the {_MAX_ARTIFACT_BYTES}-byte limit"
                )
            digest.update(chunk)
    finally:
        os.close(descriptor)

    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return {
        "path": relative.as_posix(),
        "sha256": digest.hexdigest(),
        "size_bytes": size,
        "media_type": media_type,
    }


def _artifact_records(root: Path, artifact_paths: tuple[str | Path, ...]) -> list[dict[str, Any]]:
    records = []
    total_bytes = 0
    for path in artifact_paths:
        record = _artifact_record(root, path)
        total_bytes += record["size_bytes"]
        if total_bytes > _MAX_TOTAL_ARTIFACT_BYTES:
            raise ValueError(
                f"artifact set exceeds the {_MAX_TOTAL_ARTIFACT_BYTES}-byte aggregate hashing limit"
            )
        records.append(record)
    return records


def _captured_output(
    output: Any,
    policy: CapturePolicy,
    budget: CaptureBudget,
) -> Any | None:
    if policy.mode == "metadata":
        return None
    if policy.mode == "summary":
        if policy.summarizer is None or not callable(policy.summarizer):
            raise ValueError("summary capture requires a callable summarizer")
        return json_value(policy.summarizer(output), budget)
    return {
        "raw": json_value(getattr(output, "raw", ""), budget),
        "structured": _structured_output(output, budget),
    }


def _error_record(error: BaseException, mode: str) -> tuple[dict[str, str], bool]:
    try:
        message = str(error)
    except Exception:
        message = "<exception message unavailable>"
    encoded = message.encode("utf-8", errors="replace")
    record = {
        "type": _bounded_text(type(error).__name__, "exception type", 200),
        "message_sha256": hashlib.sha256(encoded).hexdigest(),
    }
    if mode == "metadata":
        return record, False
    safe_message, truncated = truncate_utf8(redact_text(message), _MAX_ERROR_MESSAGE_BYTES)
    record["message"] = safe_message
    return record, truncated


def _markdown_code(value: str) -> str:
    longest = max((len(run) for run in re.findall(r"`+", value)), default=0)
    fence = "`" * (longest + 1)
    padding = " " if value.startswith("`") or value.endswith("`") else ""
    return f"{fence}{padding}{value}{padding}{fence}"


class CrewAIAdapter:
    """Run a local CrewAI Crew and preserve bounded governance evidence."""

    def __init__(self, project_root: str | Path, capture: CapturePolicy | None = None) -> None:
        self.project_root = Path(project_root).resolve()
        if not self.project_root.is_dir():
            raise ValueError(f"project root is not a directory: {self.project_root}")
        self.capture = capture or CapturePolicy()

    def kickoff(
        self,
        crew: Any,
        *,
        inputs: dict[str, Any] | None = None,
        input_files: dict[str, Any] | None = None,
        from_checkpoint: Any | None = None,
        task_refs: Iterable[str] = (),
        artifact_paths: Iterable[str | Path] = (),
        handoff: HandoffSpec | None = None,
    ) -> RecordedRun:
        """Execute ``Crew.kickoff`` and write its immutable run manifest."""
        return self._kickoff_sync(
            crew,
            inputs=inputs,
            input_files=input_files,
            from_checkpoint=from_checkpoint,
            task_refs=_task_refs(task_refs),
            artifact_paths=_artifact_paths(artifact_paths),
            handoff=handoff,
        )

    async def akickoff(
        self,
        crew: Any,
        *,
        inputs: dict[str, Any] | None = None,
        input_files: dict[str, Any] | None = None,
        from_checkpoint: Any | None = None,
        task_refs: Iterable[str] = (),
        artifact_paths: Iterable[str | Path] = (),
        handoff: HandoffSpec | None = None,
    ) -> RecordedRun:
        """Execute native ``Crew.akickoff`` and write its immutable run manifest."""
        version = self._prepare(crew)
        run_id = f"cwrun_{uuid.uuid4().hex}"
        input_keys, omitted_input_keys, input_keys_truncated = _input_keys(inputs)
        task_refs = _task_refs(task_refs)
        artifact_paths = _artifact_paths(artifact_paths)
        started_at = _utc_now()
        started_clock = time.monotonic_ns()
        try:
            output = await crew.akickoff(
                **self._kickoff_arguments(inputs, input_files, from_checkpoint)
            )
        except asyncio.CancelledError as exc:
            self._record_terminal(
                crew,
                version,
                "akickoff",
                run_id,
                input_keys,
                omitted_input_keys,
                input_keys_truncated,
                task_refs,
                started_at,
                started_clock,
                exc,
                "cancelled",
            )
            raise
        except Exception as exc:
            self._record_terminal(
                crew,
                version,
                "akickoff",
                run_id,
                input_keys,
                omitted_input_keys,
                input_keys_truncated,
                task_refs,
                started_at,
                started_clock,
                exc,
                "failed",
            )
            raise
        return self._record_success(
            crew,
            output,
            version,
            "akickoff",
            run_id,
            input_keys,
            omitted_input_keys,
            input_keys_truncated,
            task_refs,
            artifact_paths,
            started_at,
            started_clock,
            handoff,
        )

    def _kickoff_sync(
        self,
        crew: Any,
        *,
        inputs: dict[str, Any] | None,
        input_files: dict[str, Any] | None,
        from_checkpoint: Any | None,
        task_refs: tuple[str, ...],
        artifact_paths: tuple[str | Path, ...],
        handoff: HandoffSpec | None,
    ) -> RecordedRun:
        version = self._prepare(crew)
        run_id = f"cwrun_{uuid.uuid4().hex}"
        input_keys, omitted_input_keys, input_keys_truncated = _input_keys(inputs)
        started_at = _utc_now()
        started_clock = time.monotonic_ns()
        try:
            output = crew.kickoff(**self._kickoff_arguments(inputs, input_files, from_checkpoint))
        except Exception as exc:
            self._record_terminal(
                crew,
                version,
                "kickoff",
                run_id,
                input_keys,
                omitted_input_keys,
                input_keys_truncated,
                task_refs,
                started_at,
                started_clock,
                exc,
                "failed",
            )
            raise
        return self._record_success(
            crew,
            output,
            version,
            "kickoff",
            run_id,
            input_keys,
            omitted_input_keys,
            input_keys_truncated,
            task_refs,
            artifact_paths,
            started_at,
            started_clock,
            handoff,
        )

    @staticmethod
    def _prepare(crew: Any) -> str:
        if bool(getattr(crew, "stream", False)):
            raise ValueError("streaming CrewAI execution is not supported")
        tasks = getattr(crew, "tasks", []) or []
        if len(tasks) > _MAX_TASK_RECORDS:
            raise ValueError(f"crew exceeds the {_MAX_TASK_RECORDS}-task limit")
        return _runtime_version()

    @staticmethod
    def _kickoff_arguments(
        inputs: dict[str, Any] | None,
        input_files: dict[str, Any] | None,
        from_checkpoint: Any | None,
    ) -> dict[str, Any]:
        arguments: dict[str, Any] = {"inputs": inputs}
        if input_files is not None:
            arguments["input_files"] = input_files
        if from_checkpoint is not None:
            arguments["from_checkpoint"] = from_checkpoint
        return arguments

    def _manifest(
        self,
        crew: Any,
        output: Any | None,
        version: str,
        api: str,
        run_id: str,
        input_keys: list[str],
        omitted_input_keys: int,
        input_keys_truncated: bool,
        task_refs: tuple[str, ...],
        artifact_paths: tuple[str | Path, ...],
        started_at: dt.datetime,
        started_clock: int,
        status: str,
        error: BaseException | None,
    ) -> dict[str, Any]:
        ended_at = _utc_now()
        state = read_state(self.project_root)
        process = _enum_value(getattr(crew, "process", None)) or "unknown"
        capture_truncated = omitted_input_keys > 0 or input_keys_truncated
        error_record = None
        if error is not None:
            error_record, error_truncated = _error_record(error, self.capture.mode)
            capture_truncated = capture_truncated or error_truncated

        task_records: list[dict[str, Any]] = []
        omitted_tasks = 0
        crew_task_count = len(getattr(crew, "tasks", []) or [])
        captured_output = None
        artifacts: list[dict[str, Any]] = []
        if status == "succeeded":
            if output is None:
                raise ValueError("successful CrewAI execution returned no output")
            budget = CaptureBudget(max_text_bytes=MAX_OUTPUT_BYTES)
            try:
                task_records, omitted_tasks, crew_task_count = _task_records(
                    crew, output, self.capture.mode, budget
                )
                captured_output = _captured_output(output, self.capture, budget)
            except CaptureLimitError:
                task_records, omitted_tasks, crew_task_count = _task_records(
                    crew, output, "metadata", None
                )
                captured_output = (
                    None if self.capture.mode == "metadata" else {"truncated": "[TRUNCATED]"}
                )
                capture_truncated = True
            artifacts = _artifact_records(self.project_root, artifact_paths)

        manifest: dict[str, Any] = {
            "schema_version": 1,
            "run_id": run_id,
            "adapter": {"name": "chartworkai-crewai", "version": __version__},
            "runtime": {"name": "crewai", "version": version, "api": api},
            "chartworkai": {
                "project": _bounded_text(state["project"], "project name", _MAX_METADATA_CHARS),
                "profile": (
                    None
                    if state["profile"] is None
                    else _bounded_text(state["profile"], "profile", _MAX_METADATA_CHARS)
                ),
                "phase": state["current_phase"],
                "task_refs": list(task_refs),
            },
            "crew": {
                "id": _public_id(getattr(crew, "id", None)),
                "name": _bounded_text(
                    getattr(crew, "name", None) or "crew", "crew name", _MAX_METADATA_CHARS
                ),
                "process": process,
                "task_count": crew_task_count,
            },
            "execution": {
                "status": status,
                "started_at": _timestamp(started_at),
                "ended_at": _timestamp(ended_at),
                "duration_ms": max(0, (time.monotonic_ns() - started_clock) // 1_000_000),
                "input_keys": list(input_keys),
                "error": error_record,
            },
            "tasks": task_records,
            "usage": _usage(output) if status == "succeeded" else {},
            "artifacts": artifacts,
            "capture": {
                "mode": self.capture.mode,
                "redactor_id": self.capture.redactor_id,
                "truncated": capture_truncated or omitted_tasks > 0,
                "omitted_input_keys": omitted_input_keys,
                "omitted_tasks": omitted_tasks,
                "omitted_artifacts": 0,
            },
            "output": captured_output,
        }
        manifest = apply_redaction(manifest, self.capture)
        manifest["execution"]["status"] = status
        if status != "succeeded":
            manifest["tasks"] = []
            manifest["usage"] = {}
            manifest["artifacts"] = []
            manifest["output"] = None
            redacted_error = manifest["execution"].get("error")
            final_error = dict(error_record or {})
            if self.capture.mode != "metadata" and isinstance(redacted_error, dict):
                if "message" in redacted_error:
                    final_error["message"] = str(redacted_error["message"])
            manifest["execution"]["error"] = final_error
        self._enforce_post_redaction_error_limit(manifest)
        if len(serialize(manifest.get("output"))) > MAX_OUTPUT_BYTES:
            manifest["output"] = {"truncated": "[TRUNCATED]"}
            manifest["capture"]["truncated"] = True
        manifest = fit_to_limit(manifest, self.capture.max_bytes)
        validate_manifest(manifest)
        return manifest

    def _enforce_post_redaction_error_limit(self, manifest: dict[str, Any]) -> None:
        error = manifest["execution"]["error"]
        if not isinstance(error, dict) or "message" not in error:
            return
        if self.capture.mode == "metadata":
            error.pop("message", None)
            return
        message, truncated = truncate_utf8(str(error["message"]), _MAX_ERROR_MESSAGE_BYTES)
        error["message"] = message
        if truncated:
            manifest["capture"]["truncated"] = True

    def _ensure_run_directory(self) -> None:
        for attempt in range(_DIRECTORY_CREATE_ATTEMPTS):
            try:
                safe_mkdir(self.project_root, _RUN_DIRECTORY)
                return
            except FileExistsError:
                if attempt == _DIRECTORY_CREATE_ATTEMPTS - 1:
                    raise

    def _open_run_directory(self) -> int:
        self._ensure_run_directory()
        flags = (
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        descriptor = os.open(self.project_root, flags)
        try:
            for part in Path(_RUN_DIRECTORY).parts:
                next_descriptor = os.open(part, flags, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = next_descriptor
            return descriptor
        except Exception:
            os.close(descriptor)
            raise

    @staticmethod
    def _write_all(descriptor: int, content: bytes) -> None:
        view = memoryview(content)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short write while creating run manifest")
            view = view[written:]

    def _write_manifest(self, run_id: str, manifest: dict[str, Any]) -> Path:
        content = serialize(manifest)
        directory_descriptor = self._open_run_directory()
        temporary_name: str | None = None
        temporary_descriptor: int | None = None
        final_name = f"{run_id}.json"
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        try:
            for _ in range(_TEMP_CREATE_ATTEMPTS):
                candidate = f".{run_id}.{uuid.uuid4().hex}.tmp"
                try:
                    temporary_descriptor = os.open(
                        candidate, flags, 0o644, dir_fd=directory_descriptor
                    )
                    temporary_name = candidate
                    break
                except FileExistsError:
                    continue
            if temporary_descriptor is None or temporary_name is None:
                raise FileExistsError("could not allocate a temporary manifest file")

            self._write_all(temporary_descriptor, content)
            os.fsync(temporary_descriptor)
            os.close(temporary_descriptor)
            temporary_descriptor = None

            try:
                os.link(
                    temporary_name,
                    final_name,
                    src_dir_fd=directory_descriptor,
                    dst_dir_fd=directory_descriptor,
                    follow_symlinks=False,
                )
            except (NotImplementedError, TypeError) as exc:
                raise OSError("this platform lacks atomic no-replace manifest publication") from exc
            os.fsync(directory_descriptor)
            os.unlink(temporary_name, dir_fd=directory_descriptor)
            temporary_name = None
            os.fsync(directory_descriptor)
        finally:
            if temporary_descriptor is not None:
                os.close(temporary_descriptor)
            if temporary_name is not None:
                try:
                    os.unlink(temporary_name, dir_fd=directory_descriptor)
                except FileNotFoundError:
                    pass
            os.close(directory_descriptor)

        relative = f"{_RUN_DIRECTORY}/{final_name}"
        return resolve_within(self.project_root, relative)

    def _record_terminal(
        self,
        crew: Any,
        version: str,
        api: str,
        run_id: str,
        input_keys: list[str],
        omitted_input_keys: int,
        input_keys_truncated: bool,
        task_refs: tuple[str, ...],
        started_at: dt.datetime,
        started_clock: int,
        execution_error: BaseException,
        status: str,
    ) -> None:
        try:
            manifest = self._manifest(
                crew,
                None,
                version,
                api,
                run_id,
                input_keys,
                omitted_input_keys,
                input_keys_truncated,
                task_refs,
                (),
                started_at,
                started_clock,
                status,
                execution_error,
            )
            self._write_manifest(run_id, manifest)
        except Exception as record_error:
            add_note = getattr(execution_error, "add_note", None)
            if callable(add_note):
                add_note(f"ChartworkAI could not record the {status} CrewAI run: {record_error}")

    def _record_success(
        self,
        crew: Any,
        output: Any,
        version: str,
        api: str,
        run_id: str,
        input_keys: list[str],
        omitted_input_keys: int,
        input_keys_truncated: bool,
        task_refs: tuple[str, ...],
        artifact_paths: tuple[str | Path, ...],
        started_at: dt.datetime,
        started_clock: int,
        handoff: HandoffSpec | None,
    ) -> RecordedRun:
        manifest_path: Path | None = None
        try:
            manifest = self._manifest(
                crew,
                output,
                version,
                api,
                run_id,
                input_keys,
                omitted_input_keys,
                input_keys_truncated,
                task_refs,
                artifact_paths,
                started_at,
                started_clock,
                "succeeded",
                None,
            )
            manifest_path = self._write_manifest(run_id, manifest)
            handoff_path = self._write_handoff(handoff, manifest, manifest_path)
        except Exception as exc:
            raise RecordWriteError(
                f"CrewAI execution succeeded but ChartworkAI recording failed: {exc}",
                output=output,
                manifest_path=manifest_path,
            ) from exc
        return RecordedRun(run_id, output, manifest_path, handoff_path)

    def _write_handoff(
        self,
        spec: HandoffSpec | None,
        manifest: dict[str, Any],
        manifest_path: Path,
    ) -> Path | None:
        if spec is None:
            return None
        relative_manifest = manifest_path.relative_to(self.project_root).as_posix()
        locations = [_markdown_code(relative_manifest)]
        shown_artifacts = manifest["artifacts"][:_MAX_HANDOFF_ARTIFACT_LINES]
        locations.extend(
            f"{_markdown_code(item['path'])} (sha256: {_markdown_code(item['sha256'])})"
            for item in shown_artifacts
        )
        if len(manifest["artifacts"]) > len(shown_artifacts):
            locations.append(
                f"{len(manifest['artifacts']) - len(shown_artifacts)} additional artifacts "
                "are listed in the run manifest."
            )

        failures = _tool_failure_count_from_manifest(manifest)
        limitations = spec.limitations.strip()
        if failures:
            warning = f"CrewAI reported {failures} tool failure(s); inspect the run manifest."
            limitations = f"{limitations}\n\n{warning}" if limitations else warning
        if len(limitations) > _MAX_HANDOFF_LIMITATIONS_CHARS:
            raise ValueError(
                "generated handoff limitations exceed the "
                f"{_MAX_HANDOFF_LIMITATIONS_CHARS}-character limit"
            )
        result = file_handoff(
            self.project_root,
            agent=spec.agent,
            produced=spec.produced,
            location="\n".join(locations),
            limitations=limitations,
            verification=spec.verification,
            next_agent=spec.next_agent,
        )
        return self.project_root / result["file"]


def _tool_failure_count_from_manifest(manifest: dict[str, Any]) -> int:
    return sum(int(task["tool_failure_count"]) for task in manifest["tasks"])
