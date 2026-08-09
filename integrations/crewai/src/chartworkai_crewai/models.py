"""Public value objects for the CrewAI adapter."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal

CaptureMode = Literal["metadata", "summary", "full"]
Summarizer = Callable[[Any], Any]
Redactor = Callable[[Any], Any]

_MAX_MANIFEST_BYTES = 1024 * 1024
_MAX_REDACTOR_ID_CHARS = 128
_MAX_HANDOFF_IDENTITY_CHARS = 120
_MAX_HANDOFF_PRODUCED_CHARS = 2_000
_MAX_HANDOFF_LIMITATIONS_CHARS = 4_000
_MAX_HANDOFF_VERIFICATION_CHARS = 2_000
_HEADING_RE = re.compile(r"(?m)^\s{0,3}#{1,2}(?!#)")
_PLACEHOLDER_RE = re.compile(r"{{[^{}\n]*}}")


def _has_control_characters(value: str, *, allow_layout: bool = False) -> bool:
    allowed = {"\n", "\t"} if allow_layout else set()
    return any(
        (ord(character) < 32 or 127 <= ord(character) <= 159) and character not in allowed
        for character in value
    )


def _validate_text(
    name: str,
    value: str,
    *,
    max_chars: int,
    required: bool = False,
    single_line: bool = False,
    handoff_content: bool = False,
) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if required and not value.strip():
        raise ValueError(f"{name} must not be empty")
    if len(value) > max_chars:
        raise ValueError(f"{name} exceeds the {max_chars}-character limit")
    if _has_control_characters(value, allow_layout=not single_line):
        raise ValueError(f"{name} contains unsupported control characters")
    if single_line and "`" in value:
        raise ValueError(f"{name} must not contain backticks")
    if handoff_content and _HEADING_RE.search(value):
        raise ValueError(f"{name} must not contain H1 or H2 Markdown headings")
    if handoff_content and _PLACEHOLDER_RE.search(value):
        raise ValueError(f"{name} contains an unresolved placeholder")


@dataclass(frozen=True)
class CapturePolicy:
    """Control how much CrewAI output is retained in a run manifest."""

    mode: CaptureMode = "metadata"
    summarizer: Summarizer | None = None
    redactor: Redactor | None = None
    redactor_id: str = "default-v1"
    max_bytes: int = 256 * 1024

    def __post_init__(self) -> None:
        if self.mode not in {"metadata", "summary", "full"}:
            raise ValueError("capture mode must be metadata, summary, or full")
        if self.mode == "summary" and not callable(self.summarizer):
            raise ValueError("summary capture requires a callable summarizer")
        if self.summarizer is not None and not callable(self.summarizer):
            raise TypeError("summarizer must be callable")
        if self.redactor is not None and not callable(self.redactor):
            raise TypeError("redactor must be callable")
        _validate_text(
            "redactor_id",
            self.redactor_id,
            max_chars=_MAX_REDACTOR_ID_CHARS,
            required=True,
            single_line=True,
        )
        if self.max_bytes <= 0:
            raise ValueError("max_bytes must be greater than zero")
        if self.max_bytes > _MAX_MANIFEST_BYTES:
            raise ValueError(
                f"max_bytes must not exceed the {_MAX_MANIFEST_BYTES}-byte safety limit"
            )


@dataclass(frozen=True)
class HandoffSpec:
    """Explicit governance identities and content for an optional handoff."""

    agent: str
    next_agent: str
    produced: str
    limitations: str = ""
    verification: str = ""

    def __post_init__(self) -> None:
        for name in ("agent", "next_agent"):
            _validate_text(
                name,
                getattr(self, name),
                max_chars=_MAX_HANDOFF_IDENTITY_CHARS,
                required=True,
                single_line=True,
                handoff_content=True,
            )
        _validate_text(
            "produced",
            self.produced,
            max_chars=_MAX_HANDOFF_PRODUCED_CHARS,
            required=True,
            handoff_content=True,
        )
        _validate_text(
            "limitations",
            self.limitations,
            max_chars=_MAX_HANDOFF_LIMITATIONS_CHARS,
            handoff_content=True,
        )
        _validate_text(
            "verification",
            self.verification,
            max_chars=_MAX_HANDOFF_VERIFICATION_CHARS,
            handoff_content=True,
        )


@dataclass(frozen=True)
class RecordedRun:
    """CrewAI output paired with the durable records created for the run."""

    run_id: str
    output: Any
    manifest_path: Path
    handoff_path: Path | None = None


class RecordWriteError(RuntimeError):
    """CrewAI succeeded, but its ChartworkAI governance record did not."""

    def __init__(
        self,
        message: str,
        *,
        output: Any,
        manifest_path: Path | None = None,
    ) -> None:
        super().__init__(message)
        self.output = output
        self.manifest_path = manifest_path
