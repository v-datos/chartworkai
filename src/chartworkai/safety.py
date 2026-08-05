"""Guards for every write ChartworkAI performs.

This tool writes into other people's repositories, sometimes driven by an AI agent
acting on text it did not author. Two properties therefore have to hold for every
write, not most of them:

* it lands **inside the project root** — a path that escapes via ``..`` or a symlink
  is refused rather than followed;
* it does not **silently replace someone's work** — governance documents are the
  record the product exists to protect.

A governance document is always a real file. Refusing to write through a symlink is
deliberate: following one is how a write leaves the project without anybody noticing.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional


class UnsafePathError(ValueError):
    """A write was refused because its target is outside the project or a symlink."""


def resolve_within(root, relative: str) -> Path:
    """Return ``root/relative``, refusing anything that leaves *root*.

    Raises:
        UnsafePathError: the target is a symlink, or resolves outside *root*.
    """
    root_path = Path(root).resolve()

    # Reject `..` outright rather than reasoning about it. The ancestor walk below
    # asks the OS whether a path exists, and the OS normalises `..` away before
    # answering — so `docs/../../out.md` reported an ancestor of *root*, passed the
    # check, and then wrote to root's parent. A governance path never needs `..`.
    parts = Path(relative).parts
    if ".." in parts:
        raise UnsafePathError(f"refusing a path containing '..': {relative}")
    if Path(relative).is_absolute():
        raise UnsafePathError(f"refusing an absolute path: {relative}")

    target = root_path / relative

    if target.is_symlink():
        raise UnsafePathError(
            f"refusing to write through a symlink: {relative} -> {target.resolve()}. "
            "Governance documents must be real files inside the project."
        )

    # Check the nearest existing ancestor: a symlinked *parent directory* carries a
    # write outside just as effectively as a symlinked file, and `..` escapes here too.
    ancestor = target.parent
    while not ancestor.exists() and ancestor != ancestor.parent:
        ancestor = ancestor.parent

    try:
        ancestor.resolve().relative_to(root_path)
    except ValueError:
        raise UnsafePathError(
            f"refusing to write outside the project: {relative} resolves under "
            f"{ancestor.resolve()}, which is not inside {root_path}"
        ) from None

    return target


def safe_mkdir(root, relative: str) -> Path:
    """Create ``root/relative`` and its parents, refusing to escape *root*.

    Directory creation needs the same guard as writing: ``mkdir -p`` through a
    symlinked ``docs/`` silently builds the tree somewhere else, and every later
    write then lands outside the project.
    """
    root_path = Path(root).resolve()
    root_path.mkdir(parents=True, exist_ok=True)
    current = root_path
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            raise UnsafePathError(
                "refusing to build the project tree through a symlink: "
                f"{current} -> {current.resolve()}"
            )
        if current.exists():
            try:
                current.resolve().relative_to(root_path)
            except ValueError:
                raise UnsafePathError(
                    f"refusing to build the project tree outside {root_path}: {current}"
                ) from None
        else:
            current.mkdir()
    return current


def safe_copy(root, relative: str, source: Path) -> Path:
    """Copy *source* to ``root/relative`` under the same guard as a write."""
    path = resolve_within(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, path)
    return path


def safe_read(root, relative) -> str:
    """Read a project file, refusing to follow a symlink that leaves *root*.

    Reads escape too: a symlinked ``docs/domain/README.md`` pointing outside the
    project would otherwise have its contents surface verbatim in a ``--json``
    report or an MCP tool result.
    """
    root_path = Path(root).resolve()
    path = Path(relative)
    if not path.is_absolute():
        path = root_path / path
    if path.is_symlink() or path.exists():
        try:
            path.resolve().relative_to(root_path)
        except ValueError:
            raise UnsafePathError(
                "refusing to read through a symlink that leaves the project: "
                f"{path} -> {path.resolve()}"
            ) from None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def safe_write(root, relative: str, content: str) -> Path:
    """Write *content* to ``root/relative`` after checking it stays inside *root*."""
    path = resolve_within(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def create_exclusive(root, relative: str, content: str) -> Optional[Path]:
    """Write only if the file does not exist, atomically. ``None`` if taken.

    An audit record is allocated a name and then written; between those steps a
    concurrent caller can claim the same name and one record silently overwrites the
    other. ``O_EXCL`` makes claiming and creating a single operation, so the caller
    retries with the next free name instead of losing a record.
    """
    path = resolve_within(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError:
        return None
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        stream.write(content)
    return path


def existing_paths(root, relatives) -> list:
    """Which of *relatives* already exist under *root* — the collision set."""
    root_path = Path(root)
    return [rel for rel in relatives if (root_path / rel).exists()]
