"""Locating the framework assets that get copied into a new project.

The templates, agent specs, prompts and extensions are the product's content, and
they live at the repository root rather than inside the package. A wheel carries
them via ``force-include`` in ``pyproject.toml``; an editable install does not, so
this resolves both cases instead of assuming one.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

#: Directories copied into a new project as ``_framework_*`` reference material.
REFERENCE_DIRS = ("templates", "agents", "prompts", "extensions")

#: Shell scripts copied into a new project so it works without the package too.
SHELL_SCRIPTS = (
    "scripts/check_framework_compliance.sh",
    "scripts/generate_phase_plan.sh",
)


def _candidates() -> List[Path]:
    here = Path(__file__).resolve().parent
    return [
        here / "_assets",  # wheel: force-included at build time
        here.parents[1],  # editable install: src/chartworkai -> repo root
        here.parents[0],
    ]


def asset_root() -> Path:
    """The directory holding ``templates/``, ``agents/``, ``prompts/``, ``extensions/``."""
    for candidate in _candidates():
        if (candidate / "templates").is_dir() and (candidate / "agents").is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not locate the ChartworkAI assets (templates/, agents/, prompts/, "
        "extensions/). If you are running from a source checkout, run from the "
        "repository root; otherwise reinstall the package."
    )


def template_path(relative: str) -> Path:
    """Absolute path to one packaged asset, e.g. ``templates/AGENTS.template.md``."""
    path = asset_root() / relative
    if not path.exists():
        raise FileNotFoundError(f"packaged asset is missing: {relative}")
    return path
