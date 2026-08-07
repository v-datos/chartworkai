"""Load the packaged ChartworkAI framework contract.

``framework.json`` is the source of truth for profiles, required artifacts, and
scaffold layout.  The wheel carries the same file under ``chartworkai/_assets``;
editable installs read it from the repository root.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Dict, Mapping, Tuple

from chartworkai.assets import asset_root


@lru_cache(maxsize=1)
def load_manifest() -> Dict[str, Any]:
    """Return the validated framework manifest bundled with this installation."""
    path = asset_root() / "framework.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"could not load packaged framework manifest: {path}") from exc

    required_keys = {
        "schema_version",
        "name",
        "version",
        "default_profile",
        "legacy_profile",
        "generic_profile",
        "custom_profiles",
        "profiles",
        "required_files",
        "required_directories",
        "scaffold_directories",
        "managed_files",
        "reference_directories",
        "scaffold_support_files",
        "core_operating_files",
        "living_documents",
        "presence_rules",
    }
    missing = sorted(required_keys - manifest.keys())
    if missing:
        raise RuntimeError(f"framework manifest is missing required keys: {', '.join(missing)}")

    presets = manifest["profiles"]
    if not isinstance(presets, dict) or not presets:
        raise RuntimeError("framework manifest must define at least one profile")
    generic = manifest["generic_profile"]
    if not isinstance(generic, dict) or not generic.get("name"):
        raise RuntimeError("framework manifest generic_profile must be a named object")
    if generic["name"] in presets:
        raise RuntimeError("framework manifest generic_profile name conflicts with a preset")
    profiles = {generic["name"]: generic, **presets}
    if manifest["default_profile"] not in profiles:
        raise RuntimeError("framework manifest default_profile is not a declared profile")
    if manifest["legacy_profile"] not in profiles:
        raise RuntimeError("framework manifest legacy_profile is not a declared profile")

    custom = manifest["custom_profiles"]
    custom_keys = {"schema_version", "project_file", "name_pattern", "required_fields"}
    if not isinstance(custom, dict) or not custom_keys <= custom.keys():
        raise RuntimeError("framework manifest custom_profiles contract is incomplete")
    if not isinstance(custom["required_fields"], list) or not custom["required_fields"]:
        raise RuntimeError("framework manifest custom_profiles.required_fields must be a list")

    for name, profile in profiles.items():
        if not isinstance(profile, dict):
            raise RuntimeError(f"framework profile {name!r} must be an object")
        for key in (
            "requires_data_contracts",
            "required_files",
            "required_directories",
            "scaffold_directories",
        ):
            if key not in profile:
                raise RuntimeError(f"framework profile {name!r} is missing {key!r}")
    return manifest


MANIFEST = load_manifest()
DEFAULT_PROFILE: str = MANIFEST["default_profile"]
LEGACY_PROFILE: str = MANIFEST["legacy_profile"]
GENERIC_PROFILE: Mapping[str, Any] = MANIFEST["generic_profile"]
PRESET_PROFILES: Mapping[str, Mapping[str, Any]] = MANIFEST["profiles"]
PROFILES: Mapping[str, Mapping[str, Any]] = {
    GENERIC_PROFILE["name"]: GENERIC_PROFILE,
    **PRESET_PROFILES,
}
KNOWN_PROFILES: Tuple[str, ...] = tuple(PROFILES)
DATA_PROFILES = frozenset(
    name for name, profile in PROFILES.items() if profile["requires_data_contracts"]
)
STRICT_PROFILE: str = next(
    (name for name in KNOWN_PROFILES if name in DATA_PROFILES), DEFAULT_PROFILE
)

REQUIRED_FILES: Tuple[str, ...] = tuple(MANIFEST["required_files"])
REQUIRED_DIRECTORIES: Tuple[str, ...] = tuple(MANIFEST["required_directories"])
SCAFFOLD_DIRECTORIES: Tuple[str, ...] = tuple(MANIFEST["scaffold_directories"])
MANAGED_FILES: Tuple[str, ...] = tuple(MANIFEST["managed_files"])
REFERENCE_DIRECTORIES: Tuple[str, ...] = tuple(MANIFEST["reference_directories"])
SCAFFOLD_SUPPORT_FILES: Tuple[str, ...] = tuple(MANIFEST["scaffold_support_files"])
CORE_OPERATING_FILES: Tuple[str, ...] = tuple(MANIFEST["core_operating_files"])
LIVING_DOCUMENTS: Tuple[str, ...] = tuple(MANIFEST["living_documents"])
PRESENCE_RULES: Mapping[str, Mapping[str, Any]] = MANIFEST["presence_rules"]
CUSTOM_PROFILE_RULES: Mapping[str, Any] = MANIFEST["custom_profiles"]
CUSTOM_PROFILE_FILE: str = CUSTOM_PROFILE_RULES["project_file"]


def profile_required_files(profile: str) -> Tuple[str, ...]:
    return tuple(PROFILES[profile]["required_files"])


def profile_required_directories(profile: str) -> Tuple[str, ...]:
    return tuple(PROFILES[profile]["required_directories"])


def profile_scaffold_directories(profile: str) -> Tuple[str, ...]:
    return tuple(PROFILES[profile]["scaffold_directories"])
