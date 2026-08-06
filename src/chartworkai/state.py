"""Reading and writing a project's governance state.

The compliance checker answers *is this project healthy?*. This module answers the
other two questions an orchestrating agent needs: *where does the project stand?*
and *how do I record what was decided or handed off?*
"""

from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from chartworkai.checks import (
    CURRENT_PHASE_RE,
    _decision_files,
    _read,
    detect_profile,
)
from chartworkai.safety import create_exclusive, resolve_within

NAMESPACES = ("DEC", "DQ", "SC", "MD")

_TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
# Capture only to end of line. A character class including \s would let an empty
# "Date:" line swallow the next line's content — the same hazard guarded against in
# checks.PROFILE_RE.
_FIELD_RE = "^[*\\t ]*{label}:([^\\n]*)"
_TASK_RE = re.compile(r"^\s*- \[([ xX])\]\s*(.+?)\s*$")
_VERIFY_RE = re.compile(r"Verify command:([^\n]*)", re.IGNORECASE)
_BACKTICKED_RE = re.compile(r"`([^`]+)`")
_CHARTER_PREFIX_RE = re.compile(r"^project charter\s*[—:-]\s*", re.IGNORECASE)
_DECISION_ID_RE = re.compile(r"^\d{8}_([A-Za-z]+)(\d{3})_")


def _field(text: str, label: str) -> Optional[str]:
    match = re.search(_FIELD_RE.format(label=label), text, re.MULTILINE | re.IGNORECASE)
    if not match:
        return None
    return match.group(1).replace("*", "").strip() or None


def _today() -> _dt.date:
    return _dt.date.today()


def _project_name(charter: str, fallback: str) -> str:
    match = _TITLE_RE.search(charter)
    if not match:
        return fallback
    return _CHARTER_PREFIX_RE.sub("", match.group(1).strip()) or fallback


def _verify_command(charter: str) -> Optional[str]:
    """The project's verify command, preferring the backticked span in a prose line.

    An unfilled or empty ``Verify command:`` line yields ``None`` rather than
    inventing a value from the surrounding text — handing an agent a garbage verify
    command is worse than admitting there isn't one.
    """
    match = _VERIFY_RE.search(charter)
    if not match:
        return None
    value = match.group(1).replace("*", "").strip()
    if not value:
        return None
    backticked = _BACKTICKED_RE.search(value)
    return (backticked.group(1) if backticked else value).strip() or None


def _slug(text: str, limit: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return (slug[:limit].rstrip("_")) or "untitled"


# --- Reading -----------------------------------------------------------------


def _tasks_by_section(root: Path) -> Dict[str, List[str]]:
    path = root / "TASKS.md"
    sections: Dict[str, List[str]] = {}
    if not path.is_file():
        return sections
    current: Optional[str] = None
    for line in _read(path, root).splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections.setdefault(current, [])
            continue
        if current is None:
            continue
        match = _TASK_RE.match(line)
        if match:
            sections[current].append(match.group(2).replace("**", "").strip())
    return sections


def _recent_decisions(root: Path, limit: int = 5) -> List[Dict[str, Any]]:
    decisions: List[Dict[str, Any]] = []
    for path in sorted(_decision_files(root), reverse=True)[:limit]:
        text = _read(path, root)
        title_match = _TITLE_RE.search(text)
        decisions.append(
            {
                "file": f"docs/decisions/{path.name}",
                "title": title_match.group(1).strip() if title_match else path.stem,
                "date": _field(text, "Date"),
                "authority": _field(text, "Authority"),
                "status": _field(text, "Status"),
            }
        )
    return decisions


def _recent_handoffs(root: Path, limit: int = 5) -> List[Dict[str, Any]]:
    directory = root / "docs" / "handoffs"
    if not directory.is_dir():
        return []
    notes = sorted((p for p in directory.glob("*.md") if p.name != "README.md"), reverse=True)
    handoffs = []
    for path in notes[:limit]:
        title_match = _TITLE_RE.search(_read(path, root))
        handoffs.append(
            {
                "file": f"docs/handoffs/{path.name}",
                "title": title_match.group(1).strip() if title_match else path.stem,
            }
        )
    return handoffs


def read_state(project_root) -> Dict[str, Any]:
    """Summarise where the project stands, for an agent deciding what to do next."""
    root = Path(project_root).resolve()
    charter = _read(root / "PROJECT_CHARTER.md", root)
    plan = _read(root / "docs" / "phase_plan.md", root)

    phase_match = CURRENT_PHASE_RE.search(plan)
    profile, is_data_profile = detect_profile(root)
    sections = _tasks_by_section(root)

    def section(*names: str) -> List[str]:
        for name in names:
            for key, value in sections.items():
                if key.lower().startswith(name.lower()):
                    return value
        return []

    return {
        "project_root": str(root),
        "project": _project_name(charter, root.name),
        "profile": profile,
        "is_data_profile": is_data_profile,
        "current_phase": int(phase_match.group(1)) if phase_match else None,
        "verify_command": _verify_command(charter),
        "tasks": {
            "in_progress": section("In Progress"),
            "queued": section("Queued", "Next"),
            "blockers": section("Blockers"),
        },
        "recent_decisions": _recent_decisions(root),
        "recent_handoffs": _recent_handoffs(root),
    }


# --- Writing -----------------------------------------------------------------


def next_decision_id(root: Path, namespace: str) -> int:
    """The next free number in *namespace*, so IDs never collide."""
    highest = 0
    for path in _decision_files(root):
        match = _DECISION_ID_RE.match(path.name)
        if match and match.group(1).upper() == namespace.upper():
            highest = max(highest, int(match.group(2)))
    return highest + 1


#: Bounded so a directory that cannot accept a new file fails loudly instead of
#: spinning. Any real contention resolves in a handful of attempts.
_MAX_ID_ATTEMPTS = 100


def _number_is_taken(root: Path, namespace: str, number: int, ignore: Path) -> bool:
    """Does a decision other than *ignore* already carry this namespace + number?"""
    for path in _decision_files(root):
        if path == ignore:
            continue
        match = _DECISION_ID_RE.match(path.name)
        if match and match.group(1).upper() == namespace.upper() and int(match.group(2)) == number:
            return True
    return False


def _decision_body(identifier, title, today, authority, context, ruling, rationale):
    """The decision record itself. Rebuilt per attempt: it embeds the ID."""
    body = [
        f"# {identifier} — {title}",
        "",
        f"**Date:** {today:%Y-%m-%d}",
        f"**Authority:** {authority}",
        "**Status:** Decided",
        "",
        "## Context",
        "",
        context.strip(),
        "",
        "## Ruling",
        "",
        ruling.strip(),
        "",
    ]
    if rationale.strip():
        body += ["## Rationale", "", rationale.strip(), ""]
    return body


def file_decision(
    project_root,
    title: str,
    authority: str,
    context: str,
    ruling: str,
    rationale: str = "",
    namespace: str = "DEC",
) -> Dict[str, Any]:
    """Write a dated, authority-stamped decision record and return its metadata.

    The caller is still responsible for linking the file from ``PROJECT_CHARTER.md``;
    the compliance checker enforces that, and this function reports the exact line
    to add so an agent can complete the job.
    """
    namespace = namespace.upper()
    if namespace not in NAMESPACES:
        raise ValueError(f"namespace must be one of {', '.join(NAMESPACES)}; got {namespace!r}")

    root = Path(project_root).resolve()
    today = _today()

    # Allocating the number and writing the file are separate reads of the directory,
    # so two agents recording a decision at the same moment both see the same number
    # free. An exclusive create on the *final* filename does not fix this, because
    # that name carries the title slug: two different titles produce two different
    # filenames, both creates succeed, and both records claim the same ID. (Measured:
    # 64 concurrent calls, 64 files, 6 distinct IDs.)
    #
    # So claim the number itself. The reservation name depends only on the namespace
    # and number, which makes O_EXCL a genuine mutex over the ID. It is also a valid
    # decision filename, so a concurrent reader scanning for the highest number sees
    # the reservation immediately and moves past it — and if this process dies before
    # the rename, what is left behind is the complete record under a duller name
    # rather than a hole in the sequence.
    # Re-derive the number on every attempt rather than walking upward from a stale
    # one. The rename below frees the reservation name, so a blind +1 walk can land
    # on a slot whose owner has already completed — handing out a duplicate ID. A
    # reservation is itself a valid decision filename, so it is counted here and the
    # re-read is authoritative.
    for _ in range(_MAX_ID_ATTEMPTS):
        number = next_decision_id(root, namespace)
        identifier = f"{namespace}-{number:03d}"
        body = _decision_body(identifier, title, today, authority, context, ruling, rationale)
        reserved = f"docs/decisions/{today:%Y%m%d}_{namespace}{number:03d}_pending.md"
        claimed = create_exclusive(root, reserved, "\n".join(body))
        if claimed is None:
            continue
        # Holding the reservation is not by itself proof the number is ours: the
        # rename below frees the reservation name, so a reader that derived this
        # number before the previous owner claimed it can acquire the slot after
        # that owner renames away. Acquiring strictly follows their rename, though,
        # so their completed file is already on disk by the time we look.
        if _number_is_taken(root, namespace, number, claimed):
            claimed.unlink()
            continue
        break
    else:
        raise RuntimeError(
            f"could not allocate a free {namespace} decision id after "
            f"{_MAX_ID_ATTEMPTS} attempts in {root / 'docs' / 'decisions'}"
        )

    name = f"{today:%Y%m%d}_{namespace}{number:03d}_{_slug(title)}.md"
    relative = f"docs/decisions/{name}"
    claimed.replace(resolve_within(root, relative))

    return {
        "id": identifier,
        "file": relative,
        "charter_row": f"| {today:%Y-%m-%d} | {title} | {authority} | `{relative}` |",
        "next_step": (
            "Add charter_row to the Decision log table in PROJECT_CHARTER.md — "
            "the compliance checker fails until every decision is linked."
        ),
    }


def file_handoff(
    project_root,
    agent: str,
    produced: str,
    location: str,
    limitations: str = "",
    verification: str = "",
    next_agent: str = "",
) -> Dict[str, Any]:
    """Write a dated handoff note — the currency passed between agents."""
    root = Path(project_root).resolve()
    today = _today()
    stem = f"{today:%Y-%m-%d}_{_slug(agent)}"

    body = [
        f"# Handoff — {agent} — {today:%Y-%m-%d}",
        "",
        "## What was produced",
        "",
        produced.strip(),
        "",
        "## Where it lives",
        "",
        location.strip(),
        "",
        "## Known limitations",
        "",
        limitations.strip() or "None recorded.",
        "",
        "## How to verify",
        "",
        verification.strip() or "See the project's verify command in PROJECT_CHARTER.md.",
        "",
        "## Next agent in chain",
        "",
        next_agent.strip() or "Orchestrator, to route the next dispatch.",
        "",
    ]
    # Handoffs are an audit trail: never silently overwrite an earlier note from the
    # same agent on the same day. Testing "does this name exist?" and then writing it
    # is two steps, and a second agent can take the name in between; O_EXCL makes
    # claiming the name and creating the file one step, so the loser just moves on.
    text = "\n".join(body)
    for attempt in range(1, _MAX_ID_ATTEMPTS + 1):
        name = f"{stem}.md" if attempt == 1 else f"{stem}_{attempt}.md"
        if create_exclusive(root, f"docs/handoffs/{name}", text) is not None:
            break
    else:
        raise RuntimeError(
            f"could not allocate a free handoff name for {stem} after "
            f"{_MAX_ID_ATTEMPTS} attempts in {root / 'docs' / 'handoffs'}"
        )
    return {"file": f"docs/handoffs/{name}", "agent": agent}
