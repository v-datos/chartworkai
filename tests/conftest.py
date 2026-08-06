"""Shared fixtures and helpers for the ChartworkAI test-suite.

The central idea: :func:`make_project` builds a *minimal, fully compliant* project
tree (zero failures, zero warnings). Every test then mutates exactly one thing and
asserts on the finding that mutation is supposed to produce. That keeps each test
readable and makes an unexpected extra finding impossible to miss.

Helpers are also importable directly (``from conftest import make_project``);
pytest puts ``tests/`` on ``sys.path`` because the package has no ``__init__.py``.
"""

from __future__ import annotations

import itertools
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

import pytest

from chartworkai.checks import run_checks
from chartworkai.cli import main as cli_main
from chartworkai.models import Finding, Report, Status

# --- Locations ---------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
SHELL_CHECKER = REPO_ROOT / "scripts" / "check_framework_compliance.sh"

# --- Fixture constants -------------------------------------------------------

STATUS_DATE = "2026-01-01"
#: Deliberately *newer* than STATUS_DATE so the baseline passes the staleness check.
PLAN_DATE = "2026-01-02"
SEED_DECISION = "20260101_DEC001_seed_decision.md"

DATA_TRIAD = (
    "docs/data/data_dictionary.md",
    "docs/data/lineage.md",
    "docs/data/watchlist.md",
)
REQUIRED_FILES = (
    "PROJECT_CHARTER.md",
    "AGENTS.md",
    "docs/phase_plan.md",
    "STATUS.md",
    "TASKS.md",
)
VALID_STATUSES = frozenset({Status.PASS, Status.FAIL, Status.WARN})


# --- Document templates ------------------------------------------------------


def charter_text(
    profile: Optional[str] = "data-science",
    decisions: Sequence[str] = (SEED_DECISION,),
    phases: Sequence[int] = (1, 2),
) -> str:
    lines = ["# Project Charter", ""]
    if profile is not None:
        lines += [f"**Profile:** {profile}", ""]
    lines += [
        "## Mission",
        "",
        "Deliver a governed pipeline for the demo project.",
        "",
        "## Phases",
        "",
    ]
    lines += [f"- Phase {n}: stage {n}" for n in phases]
    lines += ["", "## Decision Log", ""]
    lines += [f"- [Decision record](docs/decisions/{name})" for name in decisions]
    lines.append("")
    return "\n".join(lines)


AGENTS_TEXT = """# Agents

## Operating Rules

Work in small, reviewable steps and record every decision.

## Session Handoff

Write a handoff note before ending a session.
"""

TASKS_TEXT = """# Tasks

## In Progress

- [ ] Draft the data dictionary.

## Next

- [ ] Record the second decision.

## Done

- [x] Write the charter.
"""

DECISIONS_README = """# Decision Records

Numbered, immutable records of the decisions that shaped this project.
"""

HANDOFFS_README = """# Handoffs

One note per session boundary.
"""

DOMAIN_README = """# Domain

Vocabulary and business rules shared by humans and assistants.
"""


def status_text(date: str = STATUS_DATE, em_dash: bool = True) -> str:
    heading = f"## {date} — Kickoff" if em_dash else f"## {date}"
    return "\n".join(
        [
            "# Status",
            "",
            heading,
            "",
            "- Charter drafted.",
            "- Seed decision recorded.",
            "",
        ]
    )


def status_with_entries(count: int) -> str:
    """A STATUS.md with *count* dated ``## `` entries, newest first."""
    parts = ["# Status", ""]
    for index in range(count):
        day = 30 - index  # 2025-12-30 downwards: all older than PLAN_DATE
        parts += [f"## 2025-12-{day:02d} — Update {day}", "", f"- entry {day}", ""]
    return "\n".join(parts)


def status_with_lines(total: int) -> str:
    """A STATUS.md that is exactly *total* lines long (trailing newline included)."""
    lines = ["# Status", "", f"## {STATUS_DATE} — Kickoff", ""]
    while len(lines) < total:
        lines.append(f"- filler note {len(lines)}")
    return "\n".join(lines[:total]) + "\n"


def phase_plan_text(current_phase: int = 1, last_updated: str = PLAN_DATE) -> str:
    return "\n".join(
        [
            "# Phase Plan",
            "",
            f"**Last updated:** {last_updated}",
            f"**Current phase:** Phase {current_phase} — build",
            "",
            "## Milestones",
            "",
            "- Ship the governed pipeline.",
            "",
        ]
    )


def decision_text(name: str) -> str:
    return "\n".join(
        [
            f"# {name}",
            "",
            "## Context",
            "",
            "The project needs a durable record of its decisions.",
            "",
            "## Decision",
            "",
            "Adopt the charter, the decision log, and handoff notes.",
            "",
        ]
    )


# --- Filesystem helpers ------------------------------------------------------


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def append(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)
    return path


def remove(root: Path, rel: str) -> None:
    path = root / rel
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def age(path: Path, days: float) -> None:
    """Backdate a file's mtime by *days* (for the mtime-staleness check)."""
    stamp = time.time() - days * 86400
    os.utime(path, (stamp, stamp))


def make_project(
    root: Path,
    *,
    profile: Optional[str] = "data-science",
    decisions: Sequence[str] = (SEED_DECISION,),
    framework_repo: bool = False,
    with_data_triad: bool = True,
) -> Path:
    """Build a minimal project that passes every check with no warnings."""
    root.mkdir(parents=True, exist_ok=True)

    write(root, "PROJECT_CHARTER.md", charter_text(profile, decisions))
    write(root, "AGENTS.md", AGENTS_TEXT)
    write(root, "STATUS.md", status_text())
    write(root, "TASKS.md", TASKS_TEXT)
    write(root, "docs/phase_plan.md", phase_plan_text())

    write(root, "docs/decisions/README.md", DECISIONS_README)
    for name in decisions:
        write(root, f"docs/decisions/{name}", decision_text(name))

    write(root, "docs/handoffs/README.md", HANDOFFS_README)
    write(root, "docs/domain/README.md", DOMAIN_README)

    if with_data_triad:
        for rel in DATA_TRIAD:
            title = Path(rel).stem.replace("_", " ").title()
            write(root, rel, f"# {title}\n\n## Overview\n\nContract for {title}.\n")

    if framework_repo:
        # Framework identity relaxes checks, so detection demands a manifest that
        # names this framework and carries the keys the product ships, plus a real
        # *.template.md. A stub of two keys no longer qualifies — deliberately, so a
        # consumer project cannot silence its own failures by planting one.
        write(
            root,
            "framework.json",
            json.dumps(
                {
                    "name": "chartworkai",
                    "version": "0.1.0",
                    "profiles": {},
                    "required_files": [],
                    "required_directories": [],
                },
                indent=2,
            )
            + "\n",
        )
        write(root, "templates/PROJECT_CHARTER.template.md", "# Charter template\n")

    return root


# --- Result plumbing ---------------------------------------------------------


@dataclass
class Result:
    """Exit code plus captured streams from a checker invocation."""

    code: int
    out: str
    err: str = ""


def run_shell_checker(root: Path) -> Result:
    """Run the reference shell implementation against *root*."""
    proc = subprocess.run(
        ["sh", str(SHELL_CHECKER), str(root)],
        capture_output=True,
        text=True,
    )
    return Result(proc.returncode, proc.stdout, proc.stderr)


def run_chartworkai_subprocess(root: Path, *args: str) -> Result:
    """Run the Python CLI out-of-process (the way CI and users invoke it)."""
    proc = subprocess.run(
        [sys.executable, "-m", "chartworkai", "check", str(root), *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    return Result(proc.returncode, proc.stdout, proc.stderr)


# --- Report query helpers ----------------------------------------------------


def report_for(root: Path) -> Report:
    return run_checks(root)


def findings(
    report: Report, check: Optional[str] = None, status: Optional[str] = None
) -> List[Finding]:
    return [
        f
        for f in report.findings
        if (check is None or f.check == check) and (status is None or f.status == status)
    ]


def statuses(report: Report, check: str) -> List[str]:
    return [f.status for f in findings(report, check)]


def only(report: Report, check: str) -> Finding:
    """The single finding for *check* (asserts there is exactly one)."""
    matches = findings(report, check)
    assert len(matches) == 1, f"expected exactly one {check!r} finding, got {matches}"
    return matches[0]


def fail_messages(report: Report, check: Optional[str] = None) -> List[str]:
    return [f.message for f in findings(report, check, Status.FAIL)]


def warn_messages(report: Report, check: Optional[str] = None) -> List[str]:
    return [f.message for f in findings(report, check, Status.WARN)]


def has_fail(report: Report, check: str, needle: str = "") -> bool:
    return any(needle in f.message for f in findings(report, check, Status.FAIL))


def paths_failed(report: Report, check: str) -> List[Optional[str]]:
    return [f.path for f in findings(report, check, Status.FAIL)]


# --- Fixtures ----------------------------------------------------------------


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A minimal, fully compliant data-science project."""
    return make_project(tmp_path / "proj")


@pytest.fixture
def make(tmp_path: Path):
    """Factory for extra projects inside the same tmp_path."""
    counter = itertools.count()

    def _make(**kwargs) -> Path:
        return make_project(tmp_path / f"proj_{next(counter)}", **kwargs)

    return _make


@pytest.fixture
def cli(capsys):
    """Run ``chartworkai`` in-process and capture its exit code and streams."""

    def _run(*argv: str) -> Result:
        code = cli_main(list(argv))
        captured = capsys.readouterr()
        return Result(code, captured.out, captured.err)

    return _run
