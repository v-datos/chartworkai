"""Validation and resolution for project-owned ChartworkAI profiles."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping

from chartworkai.manifest import (
    CUSTOM_PROFILE_FILE,
    CUSTOM_PROFILE_RULES,
    KNOWN_PROFILES,
    PROFILES,
    REQUIRED_DIRECTORIES,
    REQUIRED_FILES,
)

MAX_PROFILE_BYTES = 64 * 1024


class ProfileConfigError(ValueError):
    """A custom profile is missing, unsafe, or does not match the schema."""


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProfileConfigError(f"{field} must be a non-empty string")
    return value.strip()


def _strings(value: Any, field: str, *, allow_empty: bool = True) -> List[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ProfileConfigError(f"{field} must be an array of strings")
    cleaned = [_string(item, field) for item in value]
    if not allow_empty and not cleaned:
        raise ProfileConfigError(f"{field} must contain at least one value")
    if len(cleaned) != len(set(cleaned)):
        raise ProfileConfigError(f"{field} contains duplicate values")
    return cleaned


def _relative_paths(value: Any, field: str) -> List[str]:
    paths = _strings(value, field)
    for item in paths:
        path = PurePosixPath(item)
        if (
            item == "."
            or item.endswith("/")
            or item.startswith("/")
            or "\\" in item
            or ":" in item
            or "\x00" in item
            or path.as_posix() != item
            or any(part in ("", ".", "..") for part in path.parts)
        ):
            raise ProfileConfigError(
                f"{field} entries must be normalized project-relative POSIX paths: {item!r}"
            )
    return paths


def _commands(value: Any) -> List[str]:
    commands = _strings(value, "validation_commands", allow_empty=False)
    for command in commands:
        if "\n" in command or "\r" in command or "\x00" in command:
            raise ProfileConfigError("validation_commands entries must be single-line strings")
        if len(command) > 1000:
            raise ProfileConfigError("validation_commands entries must be at most 1000 characters")
    return commands


def _unique(*groups: Iterable[str]) -> List[str]:
    return list(dict.fromkeys(item for group in groups for item in group))


def validate_custom_profile(value: Any) -> Dict[str, Any]:
    """Return a normalized custom-profile definition or raise a precise error."""
    if not isinstance(value, dict):
        raise ProfileConfigError("custom profile must be a JSON object")

    required = set(CUSTOM_PROFILE_RULES["required_fields"])
    missing = sorted(required - value.keys())
    unknown = sorted(value.keys() - required)
    if missing:
        raise ProfileConfigError(f"custom profile is missing fields: {', '.join(missing)}")
    if unknown:
        raise ProfileConfigError(f"custom profile has unknown fields: {', '.join(unknown)}")

    schema_version = value["schema_version"]
    expected_version = CUSTOM_PROFILE_RULES["schema_version"]
    if schema_version != expected_version:
        raise ProfileConfigError(
            f"unsupported custom profile schema_version {schema_version!r}; "
            f"expected {expected_version}"
        )

    name = _string(value["name"], "name")
    if not re.fullmatch(CUSTOM_PROFILE_RULES["name_pattern"], name):
        raise ProfileConfigError(
            "name must start with a lowercase letter or digit and contain only "
            "lowercase letters, digits, and hyphens (maximum 64 characters)"
        )
    if name in KNOWN_PROFILES:
        raise ProfileConfigError(f"custom profile name {name!r} conflicts with a built-in profile")

    extends = _string(value["extends"], "extends")
    if extends not in KNOWN_PROFILES:
        raise ProfileConfigError(
            f"extends must name generic or one of the built-in presets: {', '.join(KNOWN_PROFILES)}"
        )

    required_files = _relative_paths(value["required_files"], "required_files")
    required_directories = _relative_paths(value["required_directories"], "required_directories")
    overlap = sorted(set(required_files) & set(required_directories))
    if overlap:
        raise ProfileConfigError(
            "paths cannot be both required files and directories: " + ", ".join(overlap)
        )
    repeated_files = sorted(set(required_files) & (set(REQUIRED_FILES) | {CUSTOM_PROFILE_FILE}))
    repeated_directories = sorted(set(required_directories) & set(REQUIRED_DIRECTORIES))
    if repeated_files or repeated_directories:
        repeated = repeated_files + repeated_directories
        raise ProfileConfigError(
            "custom profile repeats universal framework artifacts: " + ", ".join(repeated)
        )

    default_roles = _strings(value["default_roles"], "default_roles", allow_empty=False)
    if "Orchestrator" not in default_roles:
        raise ProfileConfigError("default_roles must include Orchestrator")
    if not any(
        re.search(r"\b(?:QA|Quality|Reproducibility)\b", role, re.IGNORECASE)
        for role in default_roles
    ):
        raise ProfileConfigError(
            "default_roles must include a QA, Quality, or Reproducibility role"
        )

    return {
        "schema_version": schema_version,
        "name": name,
        "description": _string(value["description"], "description"),
        "extends": extends,
        "required_files": required_files,
        "required_directories": required_directories,
        "scaffold_directories": _relative_paths(
            value["scaffold_directories"], "scaffold_directories"
        ),
        "default_roles": default_roles,
        "validation_commands": _commands(value["validation_commands"]),
    }


def load_custom_profile(path: Path) -> Dict[str, Any]:
    """Load one bounded, regular, non-symlinked custom-profile JSON file."""
    path = Path(path)
    try:
        if path.is_symlink():
            raise ProfileConfigError(f"refusing to read a symlinked custom profile: {path}")
        if not path.is_file():
            raise ProfileConfigError(f"custom profile file does not exist: {path}")
        if path.stat().st_size > MAX_PROFILE_BYTES:
            raise ProfileConfigError(
                f"custom profile exceeds the {MAX_PROFILE_BYTES}-byte size limit: {path}"
            )
        value = json.loads(path.read_text(encoding="utf-8"))
    except ProfileConfigError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProfileConfigError(f"could not parse custom profile JSON: {path}") from exc
    return validate_custom_profile(value)


def effective_custom_profile(definition: Mapping[str, Any]) -> Dict[str, Any]:
    """Overlay a validated custom definition on its built-in base contract."""
    base = PROFILES[definition["extends"]]
    return {
        **base,
        "name": definition["name"],
        "description": definition["description"],
        "required_files": _unique(base["required_files"], definition["required_files"]),
        "required_directories": _unique(
            base["required_directories"], definition["required_directories"]
        ),
        "scaffold_directories": _unique(
            base["scaffold_directories"], definition["scaffold_directories"]
        ),
        "default_roles": list(definition["default_roles"]),
        "validation_commands": list(definition["validation_commands"]),
        "extends": definition["extends"],
        "custom": True,
    }


def serialize_custom_profile(definition: Mapping[str, Any]) -> str:
    """Stable project-local representation used by init and check."""
    return json.dumps(dict(definition), indent=2, ensure_ascii=False) + "\n"
