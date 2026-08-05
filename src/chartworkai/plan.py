"""Regenerating ``docs/phase_plan.md`` from repository state.

The phase plan is the living document that decays fastest: it is edited by hand,
goes stale, and quietly contradicts the charter. Generating it from state — tasks,
decisions, roster, status — is the structural fix. Python port of
``generate_phase_plan.sh``.

Sections a human owns (the orchestrator note, exit criteria, completed phases) are
carried over from the existing file rather than overwritten; everything else is
derived.

DIVERGENCE-3  Phase titles are read up to the first ``.``, ``*`` or ``(`` rather
              than through a restrictive character class. The shell reference
              silently truncates any title containing ``&`` — "Phase 4 — Package &
              launch" became "Package". This reads the full title.
"""

from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from chartworkai.checks import _decision_files, _read
from chartworkai.safety import safe_write
from chartworkai.state import _field, _tasks_by_section

_CHARTER_TITLE_RE = re.compile(r"^#\s+Project Charter\s*[—-]\s*(.+)$", re.MULTILINE)
_STATUS_PHASE_RE = re.compile(r"^##\s+\d{4}-\d{2}-\d{2}\s*[—-]\s*Phase\s*(\d+)", re.MULTILINE)
_CHARTER_PHASE_RE = "\\*\\*Phase {number} [—-] ([^.*(]+)"
# Accept the note with or without bold markers: the scaffold seeds it unbolded, and
# discarding a human's seeded note on the first regeneration is not acceptable.
_ORCH_NOTE_RE = re.compile(r"^\*{0,2}Orchestrator note:\*{0,2}\s*(.+)$", re.MULTILINE)
# A bullet, with or without a checkbox. Blockers are routinely written as plain
# bullets, and dropping one makes the plan claim the opposite of the truth.
_BULLET_RE = re.compile(r"^\s*-\s+(?:\[[ xX]\]\s*)?(.+?)\s*$")
_ROLE_RE = re.compile(r"^##\s+\d+\.\s+(.+?)\s*$", re.MULTILINE)
_TASK_ID_RE = re.compile(r"T-\d{3}[a-z]?")
_CRITERION_RE = re.compile(r"^- \[([ xX])\]\s*(.+?)\s*$")
_DECISION_TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def _section_lines(text: str, heading_prefix: str) -> List[str]:
    """Lines under every H2 whose title starts with *heading_prefix*."""
    collecting = False
    lines: List[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            collecting = line[3:].strip().lower().startswith(heading_prefix.lower())
            continue
        if collecting:
            lines.append(line)
    return lines


def _bullets(text: str, heading_prefix: str) -> List[str]:
    """Every bullet in a section, checkbox or plain, matching the shell reference."""
    items: List[str] = []
    for line in _section_lines(text, heading_prefix):
        match = _BULLET_RE.match(line)
        if match:
            items.append(match.group(1).replace("**", "").strip())
    return items


def _project_name(charter: str, fallback: str) -> str:
    match = _CHARTER_TITLE_RE.search(charter)
    return match.group(1).strip() if match else fallback


def _current_phase(status: str, charter: str) -> Tuple[int, str]:
    match = _STATUS_PHASE_RE.search(status)
    number = int(match.group(1)) if match else 1
    title_match = re.search(_CHARTER_PHASE_RE.format(number=number), charter)
    title = title_match.group(1).strip() if title_match else "Active Phase"
    return number, title


def _exit_criteria(existing: str, tasks_text: str) -> List[str]:
    """Carry the criteria forward, ticking any whose referenced tasks are all done."""
    criteria: List[str] = []
    for line in _section_lines(existing, "Current phase exit criteria"):
        match = _CRITERION_RE.match(line)
        if not match:
            continue
        state, body = match.group(1), match.group(2)
        ids = _TASK_ID_RE.findall(body)
        if ids and all(f"- [x] **{identifier}" in tasks_text for identifier in ids):
            state = "x"
        criteria.append(f"- [{state}] {body}")
    if not criteria:
        criteria = [
            "- [ ] Define and implement deliverables.",
            "- [ ] QA reproducibility report filed at docs/reproducibility/phase_N.md",
        ]
    return criteria


def _active_agents(agents_text: str, tasks_text: str) -> List[str]:
    """One row per role, matched to any In-Progress task it owns."""
    owners: Dict[str, str] = {}
    current: Optional[str] = None
    collecting = False
    for line in tasks_text.splitlines():
        if line.startswith("## "):
            collecting = line[3:].strip().lower().startswith("in progress")
            continue
        if not collecting:
            continue
        task = re.match(r"^\s*- \[[ xX]\]\s*(.+?)\s*$", line)
        if task:
            current = task.group(1).replace("**", "").strip()
            continue
        owner = re.match(r"^\s*Owner:\s*(.+?)\s*$", line)
        if owner and current:
            owners.setdefault(owner.group(1).strip(), current)

    rows: List[str] = []
    for role in _ROLE_RE.findall(agents_text):
        name = role.replace("(optional)", "").strip()
        task = owners.get(name)
        if task:
            rows.append(f"| {name} | Active | {task} | — |")
        elif "optional" in role.lower():
            rows.append(f"| {name} | Standby | Available for assignment | — |")
        else:
            rows.append(f"| {name} | Idle | Available for assignment | — |")
    if not rows:
        rows = ["| Orchestrator | Active | Route the next dispatch | — |"]
    return rows


def _decision_rows(root: Path) -> List[str]:
    rows: List[str] = []
    for path in sorted(_decision_files(root), reverse=True):
        text = _read(path)
        title_match = _DECISION_TITLE_RE.search(text)
        title = title_match.group(1).strip() if title_match else path.stem
        # Titles read "DEC-004 — Topic"; split on the em dash without using cut,
        # which cannot take a multibyte delimiter.
        identifier, _, topic = title.partition("—")
        rows.append(
            "| [{id}](decisions/{file}) | {date} | {topic} | {status} | {authority} |".format(
                id=identifier.strip() or path.stem,
                file=path.name,
                date=_field(text, "Date") or "-",
                topic=topic.strip() or title,
                status=_field(text, "Status") or "-",
                authority=_field(text, "Authority") or "-",
            )
        )
    return rows or ["| - | - | No decisions filed yet | - | - |"]


def generate_phase_plan(
    project_root, today: Optional[_dt.date] = None, write: bool = True
) -> Dict[str, Any]:
    """Rebuild the phase plan from current state. Returns a summary."""
    root = Path(project_root).resolve()
    charter = _read(root / "PROJECT_CHARTER.md")
    status = _read(root / "STATUS.md")
    tasks_text = _read(root / "TASKS.md")
    agents_text = _read(root / "AGENTS.md")

    missing = [
        name
        for name, text in (
            ("PROJECT_CHARTER.md", charter),
            ("STATUS.md", status),
            ("TASKS.md", tasks_text),
            ("AGENTS.md", agents_text),
        )
        if not text
    ]
    if missing:
        raise FileNotFoundError(
            "cannot generate a phase plan; missing or empty: " + ", ".join(missing)
        )

    plan_path = root / "docs" / "phase_plan.md"
    existing = _read(plan_path)
    day = today or _dt.date.today()

    number, title = _current_phase(status, charter)
    note_match = _ORCH_NOTE_RE.search(existing)
    note = note_match.group(1).strip() if note_match else "Ready for routing."
    sections = _tasks_by_section(root)

    queued = [f"- {item}" for item in sections.get("Queued", [])] or ["- None queued."]
    for key, value in sections.items():
        if key.lower().startswith("queued") and value:
            queued = [f"- {item}" for item in value]
            break

    blockers = [f"- {item}" for item in _bullets(tasks_text, "Blockers")] or [
        "- None currently filed."
    ]
    completed = [
        line for line in _section_lines(existing, "Completed phases") if line.startswith("- ")
    ] or ["- **Phase 0** — Scoping and install."]

    body = "\n".join(
        [
            f"# Phase Plan — {_project_name(charter, root.name)}",
            "",
            "> ⚠️ **STOP — READ BEFORE EDITING.**",
            "> 1. Read this entire file first. 2. Edit sections **in place** — never append a "
            "second copy of a section. 3. Hard cap: **200 lines**. 4. If a section is "
            "duplicated or this file exceeds the cap, prune to a single canonical form "
            "before adding anything.",
            "",
            f"**Last updated:** {day:%Y-%m-%d}",
            f"**Current phase:** Phase {number} — {title}",
            f"**Orchestrator note:** {note}",
            "",
            "## Active agents",
            "",
            "| Agent | Status | Current task | Blocking on |",
            "|---|---|---|---|",
            *_active_agents(agents_text, tasks_text),
            "",
            f"## Current phase exit criteria (Phase {number})",
            "",
            *_exit_criteria(existing, tasks_text),
            "",
            "## Dispatch queue (next up)",
            "",
            *queued,
            "",
            "## Open blockers",
            "",
            *blockers,
            "",
            "## Decision log (recent)",
            "",
            "| ID | Date | Topic | Status | Authority |",
            "|---|---|---|---|---|",
            *_decision_rows(root),
            "",
            "(For full history see `docs/decisions/`.)",
            "",
            "## Completed phases",
            "",
            *completed,
            "",
        ]
    )

    if write:
        safe_write(root, "docs/phase_plan.md", body)

    return {
        "file": "docs/phase_plan.md",
        "current_phase": number,
        "phase_title": title,
        "lines": len(body.splitlines()),
        "written": write,
    }
