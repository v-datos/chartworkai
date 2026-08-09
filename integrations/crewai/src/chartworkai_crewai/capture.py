"""Bounded output capture, redaction, and serialization."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from .models import CapturePolicy

MAX_OUTPUT_BYTES = 256 * 1024
MAX_MANIFEST_BYTES = 1024 * 1024
MAX_CAPTURE_DEPTH = 32
MAX_CAPTURE_NODES = 20_000
MAX_COLLECTION_ITEMS = 2_000

_REDACTED = "[REDACTED]"
_TRUNCATED = "[TRUNCATED]"
_SECRET_KEYS = {
    "access_key",
    "access_token",
    "api_key",
    "apikey",
    "authorization",
    "bearer_token",
    "client_secret",
    "credential",
    "credentials",
    "password",
    "private_key",
    "refresh_token",
    "secret",
    "secret_key",
    "token",
}
_SECRET_KEY_SUFFIXES = ("_api_key", "_password", "_private_key", "_secret")
_SECRET_PATTERNS = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"(?<![\w.+-])[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"(?<!\w)(?:/Users|/home)/[^\s,;]+"),
    re.compile(
        r"(?i)\b(api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*"
        r"([^\s,;]+)"
    ),
)


class CaptureLimitError(ValueError):
    """Captured output exceeded a traversal or size safety bound."""


class CaptureBudget:
    """Shared work budget for one captured CrewAI output graph."""

    def __init__(
        self,
        *,
        max_text_bytes: int = MAX_OUTPUT_BYTES,
        max_nodes: int = MAX_CAPTURE_NODES,
    ) -> None:
        self.max_text_bytes = max_text_bytes
        self.max_nodes = max_nodes
        self.text_bytes = 0
        self.nodes = 0
        self._active: set[int] = set()

    def convert(self, value: Any, depth: int = 0) -> Any:
        if depth > MAX_CAPTURE_DEPTH:
            raise CaptureLimitError(
                f"capture exceeds the maximum nesting depth of {MAX_CAPTURE_DEPTH}"
            )
        self.nodes += 1
        if self.nodes > self.max_nodes:
            raise CaptureLimitError(f"capture exceeds the {self.max_nodes}-node work limit")

        if value is None or isinstance(value, (bool, int, float)):
            return value
        if isinstance(value, str):
            self.text_bytes += len(value.encode("utf-8", errors="replace"))
            if self.text_bytes > self.max_text_bytes:
                raise CaptureLimitError(
                    f"captured text exceeds the {self.max_text_bytes}-byte output budget"
                )
            return value

        model_dump = getattr(value, "model_dump", None)
        if callable(model_dump):
            value = model_dump(mode="json")

        if isinstance(value, Mapping):
            return self._mapping(value, depth)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return self._sequence(value, depth)
        raise TypeError(f"capture value of type {type(value).__name__} is not JSON serializable")

    def _mapping(self, value: Mapping[Any, Any], depth: int) -> dict[str, Any]:
        identity = id(value)
        if identity in self._active:
            raise CaptureLimitError("capture contains a reference cycle")
        self._active.add(identity)
        try:
            result: dict[str, Any] = {}
            for index, (key, item) in enumerate(value.items()):
                if index >= MAX_COLLECTION_ITEMS:
                    raise CaptureLimitError(
                        f"capture mapping exceeds {MAX_COLLECTION_ITEMS} entries"
                    )
                converted_key = self.convert(str(key), depth + 1)
                result[converted_key] = self.convert(item, depth + 1)
            return result
        finally:
            self._active.remove(identity)

    def _sequence(self, value: Sequence[Any], depth: int) -> list[Any]:
        identity = id(value)
        if identity in self._active:
            raise CaptureLimitError("capture contains a reference cycle")
        self._active.add(identity)
        try:
            result = []
            for index, item in enumerate(value):
                if index >= MAX_COLLECTION_ITEMS:
                    raise CaptureLimitError(
                        f"capture sequence exceeds {MAX_COLLECTION_ITEMS} entries"
                    )
                result.append(self.convert(item, depth + 1))
            return result
        finally:
            self._active.remove(identity)


def json_value(value: Any, budget: CaptureBudget | None = None) -> Any:
    """Convert supported values to JSON under a bounded traversal budget."""
    return (budget or CaptureBudget()).convert(value)


def _secret_key(key: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")
    return normalized in _SECRET_KEYS or normalized.endswith(_SECRET_KEY_SUFFIXES)


def redact_text(value: str) -> str:
    """Mask built-in bearer, API-key, password, and secret patterns."""
    redacted = value
    for pattern in _SECRET_PATTERNS:
        if pattern.groups == 2:
            redacted = pattern.sub(lambda match: f"{match.group(1)}={_REDACTED}", redacted)
        else:
            redacted = pattern.sub(_REDACTED, redacted)
    return redacted


def _redact(value: Any, *, depth: int = 0, count: list[int] | None = None) -> Any:
    if depth > MAX_CAPTURE_DEPTH:
        raise CaptureLimitError(
            f"redaction exceeds the maximum nesting depth of {MAX_CAPTURE_DEPTH}"
        )
    if count is None:
        count = [0]
    count[0] += 1
    if count[0] > MAX_CAPTURE_NODES:
        raise CaptureLimitError(f"redaction exceeds the {MAX_CAPTURE_NODES}-node work limit")
    if isinstance(value, dict):
        return {
            str(key): _REDACTED
            if _secret_key(str(key))
            else _redact(item, depth=depth + 1, count=count)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item, depth=depth + 1, count=count) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def apply_redaction(value: Any, policy: CapturePolicy) -> Any:
    """Run mandatory redaction around an optional trusted caller redactor."""
    manifest_budget = CaptureBudget(
        max_text_bytes=MAX_MANIFEST_BYTES,
        max_nodes=MAX_CAPTURE_NODES,
    )
    redacted = _redact(json_value(value, manifest_budget))
    if policy.redactor is not None:
        redacted = policy.redactor(redacted)
        redacted = _redact(
            json_value(
                redacted,
                CaptureBudget(
                    max_text_bytes=MAX_MANIFEST_BYTES,
                    max_nodes=MAX_CAPTURE_NODES,
                ),
            )
        )
    return redacted


def truncate_utf8(value: str, max_bytes: int) -> tuple[str, bool]:
    """Return a valid UTF-8 prefix no larger than ``max_bytes``."""
    encoded = value.encode("utf-8", errors="replace")
    if len(encoded) <= max_bytes:
        return value, False
    suffix = "...[TRUNCATED]"
    remaining = max(0, max_bytes - len(suffix.encode("utf-8")))
    prefix = encoded[:remaining].decode("utf-8", errors="ignore")
    return prefix + suffix, True


def serialize(manifest: dict[str, Any]) -> bytes:
    text = json.dumps(
        manifest,
        indent=2,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
    )
    return (text + "\n").encode()


def _halve_until_fit(
    manifest: dict[str, Any],
    container: dict[str, Any],
    key: str,
    omitted_key: str,
    max_bytes: int,
) -> bool:
    values = list(container[key])
    base_omitted = int(manifest["capture"][omitted_key])
    keep = len(values)
    while keep:
        keep //= 2
        container[key] = values[:keep]
        manifest["capture"][omitted_key] = base_omitted + len(values) - keep
        if len(serialize(manifest)) <= max_bytes:
            return True
    return len(serialize(manifest)) <= max_bytes


def fit_to_limit(manifest: dict[str, Any], max_bytes: int) -> dict[str, Any]:
    """Deterministically reduce capture in logarithmic serialization passes."""
    if max_bytes > MAX_MANIFEST_BYTES:
        raise ValueError(f"manifest limit exceeds the {MAX_MANIFEST_BYTES}-byte hard cap")
    if len(serialize(manifest)) <= max_bytes:
        return manifest

    manifest["capture"]["truncated"] = True
    if manifest.get("output") is not None:
        manifest["output"] = {"truncated": _TRUNCATED}
    for task in manifest["tasks"]:
        task.pop("content", None)
    if len(serialize(manifest)) <= max_bytes:
        return manifest

    candidates = (
        (manifest["execution"], "input_keys", "omitted_input_keys"),
        (manifest, "tasks", "omitted_tasks"),
        (manifest, "artifacts", "omitted_artifacts"),
    )
    for container, key, omitted_key in candidates:
        if _halve_until_fit(manifest, container, key, omitted_key, max_bytes):
            return manifest

    raise ValueError(f"manifest structural metadata exceeds the configured {max_bytes}-byte limit")
