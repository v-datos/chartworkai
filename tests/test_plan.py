"""Behavioural tests for :mod:`chartworkai.plan` — regenerating ``docs/phase_plan.md``.

The phase plan is the document that decays fastest, so ``generate_phase_plan`` is
half derivation and half preservation: agent rows, the dispatch queue, blockers and
the decision table are *derived* from repository state, while the orchestrator note,
the exit criteria and the completed-phase list are *carried over* from whatever a
human last wrote. Each class below owns one of those two halves for one section.

Two properties get their own classes because they are the ones that break silently:

* ``TestPhaseTitle`` covers DIVERGENCE-3 — a phase title containing ``&`` is
  truncated by the shell reference and must not be by Python;
* ``TestGeneratedPlanStaysCompliant`` runs the checker over the *generated* file,
  because a generator that quietly makes its own project non-compliant is worse
  than no generator at all.
"""

from __future__ import annotations

import datetime as _dt
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import pytest
from conftest import (
    REPO_ROOT,
    SEED_DECISION,
    charter_text,
    decision_text,
    findings,
    remove,
    report_for,
    write,
)

from chartworkai.models import Status
from chartworkai.plan import generate_phase_plan

# --- Constants ---------------------------------------------------------------

SHELL_PLAN = REPO_ROOT / "scripts" / "generate_phase_plan.sh"
HAS_SH = shutil.which("sh") is not None
needs_sh = pytest.mark.skipif(
    not HAS_SH or sys.platform == "win32",
    reason=(
        "Shell/Python parity is a POSIX guarantee: the scaffold ships POSIX sh "
        "scripts, and byte-comparing them on Windows fails on line endings and "
        "permission bits rather than on any real divergence. Windows users drive "
        "the Python CLI."
    ),
)

TODAY = _dt.date(2026, 1, 2)
PLAN_FILE = "docs/phase_plan.md"
CORE_INPUTS = ("PROJECT_CHARTER.md", "STATUS.md", "TASKS.md", "AGENTS.md")

DEFAULT_CRITERIA = [
    "- [ ] Define and implement deliverables.",
    "- [ ] QA reproducibility report filed at docs/reproducibility/phase_N.md",
]
DEFAULT_NOTE = "Ready for routing."
DEFAULT_QUEUE = "- None queued."
DEFAULT_BLOCKERS = "- None currently filed."
DEFAULT_COMPLETED = "- **Phase 0** — Scoping and install."
NO_DECISIONS_ROW = "| - | - | No decisions filed yet | - | - |"

ROSTER = """# Agents

## Shared conventions

Work in small, reviewable steps and record every decision.

## 1. Orchestrator

Routes the next dispatch.

## 2. Domain Expert

Owns what the numbers mean.

## 3. Producer

Builds the canonical artifacts.

## 4. QA / Reproducibility Engineer

Verifies before every phase close.

## 5. Visualization Specialist (optional)

Draws the figures.
"""

TASKS_WITH_OWNERS = """# Tasks

## In Progress

- [ ] **T-001 — Draft the data dictionary**
  Owner: Domain Expert
  Started: 2026-01-01

- [ ] **T-004 — Wire the export job**
  Owner: Producer

## Queued

- [ ] **T-002 — Record the second decision**
- [ ] **T-003 — Review the roster**

## Blockers

- [ ] **B-001 — Waiting on the vendor contract**

## Done

- [x] **T-000 — Write the charter**
"""


# --- Helpers -----------------------------------------------------------------


def existing_plan(*sections: str, note: Optional[str] = None) -> str:
    """A hand-written plan carrying *sections*, for the carry-over tests."""
    lines = [
        "# Phase Plan — Demo",
        "",
        "**Last updated:** 2026-01-02",
        "**Current phase:** Phase 1 — build",
    ]
    if note is not None:
        lines.append(f"**Orchestrator note:** {note}")
    lines += ["", *sections, ""]
    return "\n".join(lines)


def charter_with(root: Path, *extra: str, **kwargs) -> None:
    """Rewrite the charter as the compliant baseline plus *extra* lines."""
    write(root, "PROJECT_CHARTER.md", charter_text(**kwargs) + "\n".join(extra) + "\n")


def body(root: Path) -> str:
    return (root / PLAN_FILE).read_text(encoding="utf-8")


def section(text: str, heading: str) -> List[str]:
    """Non-blank lines under the H2 whose title starts with *heading*.

    A deliberately independent parser: the tests must not agree with the module
    under test merely because they share its section reader.
    """
    collected: List[str] = []
    collecting = False
    for line in text.splitlines():
        if line.startswith("## "):
            collecting = line[3:].lower().startswith(heading.lower())
            continue
        if collecting and line.strip():
            collected.append(line)
    return collected


def table_rows(text: str, heading: str) -> List[str]:
    """Data rows of the table under *heading*, minus the header and rule lines."""
    rows = [line for line in section(text, heading) if line.startswith("|")]
    return rows[2:]


def cells(row: str) -> List[str]:
    return [cell.strip() for cell in row.strip().strip("|").split("|")]


def line_starting(text: str, prefix: str) -> str:
    for line in text.splitlines():
        if line.startswith(prefix):
            return line
    raise AssertionError(f"no line starting with {prefix!r} in:\n{text}")


def run_shell_plan(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["sh", str(SHELL_PLAN), str(root)], capture_output=True, text=True)


@pytest.fixture
def staffed(project: Path) -> Path:
    """The compliant fixture project, plus a numbered roster and owned tasks."""
    write(project, "AGENTS.md", ROSTER)
    write(project, "TASKS.md", TASKS_WITH_OWNERS)
    return project


@pytest.fixture
def bare(tmp_path: Path) -> Path:
    root = tmp_path / "bare"
    root.mkdir()
    return root


# --- Guard rails: the inputs must be there -----------------------------------


class TestMissingInputs:
    @pytest.mark.parametrize("relative", CORE_INPUTS)
    def test_a_missing_core_file_raises(self, project, relative):
        remove(project, relative)
        with pytest.raises(FileNotFoundError):
            generate_phase_plan(project)

    @pytest.mark.parametrize("relative", CORE_INPUTS)
    def test_the_error_names_the_missing_file(self, project, relative):
        remove(project, relative)
        with pytest.raises(FileNotFoundError) as excinfo:
            generate_phase_plan(project)
        assert relative in str(excinfo.value)

    @pytest.mark.parametrize("relative", CORE_INPUTS)
    def test_an_empty_core_file_counts_as_missing(self, project, relative):
        write(project, relative, "")
        with pytest.raises(FileNotFoundError) as excinfo:
            generate_phase_plan(project)
        assert relative in str(excinfo.value)

    def test_every_missing_file_is_named(self, bare):
        with pytest.raises(FileNotFoundError) as excinfo:
            generate_phase_plan(bare)
        message = str(excinfo.value)
        for relative in CORE_INPUTS:
            assert relative in message

    def test_the_message_explains_what_failed(self, bare):
        with pytest.raises(FileNotFoundError) as excinfo:
            generate_phase_plan(bare)
        assert "cannot generate a phase plan" in str(excinfo.value)

    def test_files_present_are_not_named(self, project):
        remove(project, "STATUS.md")
        with pytest.raises(FileNotFoundError) as excinfo:
            generate_phase_plan(project)
        message = str(excinfo.value)
        assert "STATUS.md" in message
        assert "TASKS.md" not in message

    def test_nothing_is_written_when_the_inputs_are_incomplete(self, project):
        before = body(project)
        remove(project, "AGENTS.md")
        with pytest.raises(FileNotFoundError):
            generate_phase_plan(project)
        assert body(project) == before

    def test_no_plan_file_is_created_when_the_inputs_are_incomplete(self, bare):
        with pytest.raises(FileNotFoundError):
            generate_phase_plan(bare)
        assert not (bare / PLAN_FILE).exists()

    def test_whitespace_only_core_file_is_not_treated_as_missing(self, project):
        write(project, "TASKS.md", "   \n\n")
        # Whitespace is still content; the guard is deliberately about emptiness.
        generate_phase_plan(project, today=TODAY)
        assert (project / PLAN_FILE).is_file()


# --- write=False -------------------------------------------------------------


class TestWriteFlag:
    def test_dry_run_leaves_the_file_untouched(self, project):
        before = body(project)
        generate_phase_plan(project, today=TODAY, write=False)
        assert body(project) == before

    def test_dry_run_does_not_create_a_missing_plan(self, project):
        remove(project, PLAN_FILE)
        generate_phase_plan(project, today=TODAY, write=False)
        assert not (project / PLAN_FILE).exists()

    def test_dry_run_still_returns_a_summary(self, project):
        summary = generate_phase_plan(project, today=TODAY, write=False)
        assert summary["file"] == PLAN_FILE
        assert summary["current_phase"] == 1
        assert summary["lines"] > 0

    def test_dry_run_reports_written_false(self, project):
        assert generate_phase_plan(project, today=TODAY, write=False)["written"] is False

    def test_writing_reports_written_true(self, project):
        assert generate_phase_plan(project, today=TODAY, write=True)["written"] is True

    def test_write_defaults_to_true(self, project):
        generate_phase_plan(project, today=TODAY)
        assert "**Last updated:** 2026-01-02" in body(project)

    def test_dry_run_and_write_agree_on_the_line_count(self, project):
        dry = generate_phase_plan(project, today=TODAY, write=False)
        wet = generate_phase_plan(project, today=TODAY, write=True)
        assert dry["lines"] == wet["lines"] == len(body(project).splitlines())

    def test_writing_creates_the_docs_directory(self, project):
        shutil.rmtree(project / "docs")
        generate_phase_plan(project, today=TODAY)
        assert (project / PLAN_FILE).is_file()

    def test_a_string_root_is_accepted(self, project):
        generate_phase_plan(str(project), today=TODAY)
        assert (project / PLAN_FILE).is_file()


# --- Current phase -----------------------------------------------------------


class TestCurrentPhase:
    def test_phase_comes_from_the_status_heading(self, project):
        write(project, "STATUS.md", "# Status\n\n## 2026-01-01 — Phase 3 kickoff\n\n- go\n")
        assert generate_phase_plan(project, today=TODAY)["current_phase"] == 3

    def test_a_hyphen_separator_is_accepted(self, project):
        write(project, "STATUS.md", "# Status\n\n## 2026-01-01 - Phase 3 kickoff\n\n- go\n")
        assert generate_phase_plan(project, today=TODAY)["current_phase"] == 3

    def test_the_newest_entry_wins(self, project):
        write(
            project,
            "STATUS.md",
            "# Status\n\n## 2026-01-05 — Phase 4 review\n\n- b\n\n"
            "## 2026-01-01 — Phase 2 kickoff\n\n- a\n",
        )
        assert generate_phase_plan(project, today=TODAY)["current_phase"] == 4

    def test_multi_digit_phases_parse(self, project):
        write(project, "STATUS.md", "# Status\n\n## 2026-01-01 — Phase 12 kickoff\n\n- go\n")
        assert generate_phase_plan(project, today=TODAY)["current_phase"] == 12

    def test_phase_defaults_to_one_when_no_heading_declares_it(self, project):
        assert generate_phase_plan(project, today=TODAY)["current_phase"] == 1

    def test_an_undated_heading_is_not_a_phase_marker(self, project):
        write(project, "STATUS.md", "# Status\n\n## Phase 7 notes\n\n- go\n")
        assert generate_phase_plan(project, today=TODAY)["current_phase"] == 1

    def test_a_heading_without_a_separator_is_not_a_phase_marker(self, project):
        write(project, "STATUS.md", "# Status\n\n## 2026-01-01 Phase 7\n\n- go\n")
        assert generate_phase_plan(project, today=TODAY)["current_phase"] == 1

    def test_a_phase_mentioned_only_in_the_body_is_ignored(self, project):
        write(project, "STATUS.md", "# Status\n\n## 2026-01-01 — Kickoff\n\n- Phase 9 starts\n")
        assert generate_phase_plan(project, today=TODAY)["current_phase"] == 1

    def test_the_phase_appears_in_the_generated_header(self, project):
        write(project, "STATUS.md", "# Status\n\n## 2026-01-01 — Phase 3 kickoff\n\n- go\n")
        generate_phase_plan(project, today=TODAY)
        assert line_starting(body(project), "**Current phase:**").startswith(
            "**Current phase:** Phase 3 —"
        )

    def test_the_phase_appears_in_the_exit_criteria_heading(self, project):
        write(project, "STATUS.md", "# Status\n\n## 2026-01-01 — Phase 3 kickoff\n\n- go\n")
        generate_phase_plan(project, today=TODAY)
        assert "## Current phase exit criteria (Phase 3)" in body(project)


# --- Phase title -------------------------------------------------------------


class TestPhaseTitle:
    def test_title_comes_from_the_bold_charter_line(self, project):
        charter_with(project, "**Phase 1 — Deliver the pipeline.** Details follow.")
        assert generate_phase_plan(project, today=TODAY)["phase_title"] == "Deliver the pipeline"

    def test_a_hyphen_separator_is_accepted(self, project):
        charter_with(project, "**Phase 1 - Deliver the pipeline.**")
        assert generate_phase_plan(project, today=TODAY)["phase_title"] == "Deliver the pipeline"

    def test_an_ampersand_in_the_title_survives(self, project):
        """DIVERGENCE-3 regression.

        The shell reads the title through ``[A-Za-z0-9_ -]``, so
        "Package & launch" arrives as "Package". Python must keep the whole title.
        """
        write(project, "STATUS.md", "# Status\n\n## 2026-01-01 — Phase 4 kickoff\n\n- go\n")
        charter_with(project, "**Phase 4 — Package & launch.** Ship it.", phases=(1, 2, 3, 4))
        summary = generate_phase_plan(project, today=TODAY)
        assert summary["phase_title"] == "Package & launch"
        assert "**Current phase:** Phase 4 — Package & launch" in body(project)

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("**Phase 1 — Data & modelling.**", "Data & modelling"),
            ("**Phase 1 — Ship it**", "Ship it"),
            ("**Phase 1 — Build (beta).**", "Build"),
            ("**Phase 1 — R&D, round 2.**", "R&D, round 2"),
            ("**Phase 1 — 100% coverage!**", "100% coverage!"),
            ("**Phase 1 — snake_case title.**", "snake_case title"),
        ],
    )
    def test_titles_are_read_up_to_a_dot_star_or_paren(self, project, raw, expected):
        charter_with(project, raw)
        assert generate_phase_plan(project, today=TODAY)["phase_title"] == expected

    def test_title_falls_back_when_the_charter_has_no_bold_phase_line(self, project):
        assert generate_phase_plan(project, today=TODAY)["phase_title"] == "Active Phase"

    def test_title_falls_back_when_only_another_phase_is_titled(self, project):
        charter_with(project, "**Phase 9 — Something else.**")
        assert generate_phase_plan(project, today=TODAY)["phase_title"] == "Active Phase"

    def test_the_matching_phase_number_is_used(self, project):
        write(project, "STATUS.md", "# Status\n\n## 2026-01-01 — Phase 2 kickoff\n\n- go\n")
        charter_with(
            project,
            "**Phase 1 — First stage.**",
            "**Phase 2 — Second stage.**",
            phases=(1, 2),
        )
        assert generate_phase_plan(project, today=TODAY)["phase_title"] == "Second stage"


@needs_sh
class TestPhaseTitleDivergesFromShell:
    """DIVERGENCE-3, demonstrated against the reference implementation itself."""

    @staticmethod
    def _fixture(root: Path) -> None:
        write(
            root,
            "PROJECT_CHARTER.md",
            "# Project Charter — Demo\n\n## Phases\n\n**Phase 4 — Package & launch.** Ship it.\n",
        )
        write(root, "STATUS.md", "# Status\n\n## 2026-01-05 — Phase 4 kickoff\n\n- go\n")
        write(
            root,
            "TASKS.md",
            "# Tasks\n\n## In Progress\n\n- [ ] **T-001 — Do it**\n  Owner: Orchestrator\n",
        )
        write(root, "AGENTS.md", "# Agents\n\n## 1. Orchestrator\n\nRoutes.\n")
        (root / "docs").mkdir(parents=True, exist_ok=True)

    def test_the_shell_truncates_at_the_ampersand(self, bare):
        self._fixture(bare)
        proc = run_shell_plan(bare)
        assert proc.returncode == 0, proc.stderr
        assert line_starting(body(bare), "**Current phase:**") == (
            "**Current phase:** Phase 4 — Package"
        )

    def test_python_keeps_the_whole_title(self, bare):
        self._fixture(bare)
        generate_phase_plan(bare, today=TODAY)
        assert line_starting(body(bare), "**Current phase:**") == (
            "**Current phase:** Phase 4 — Package & launch"
        )


# --- Orchestrator note -------------------------------------------------------


class TestOrchestratorNote:
    def test_the_existing_note_is_carried_over(self, project):
        write(project, PLAN_FILE, existing_plan(note="Waiting on the vendor."))
        generate_phase_plan(project, today=TODAY)
        assert "**Orchestrator note:** Waiting on the vendor." in body(project)

    def test_a_default_note_is_used_when_there_is_none(self, project):
        write(project, PLAN_FILE, existing_plan())
        generate_phase_plan(project, today=TODAY)
        assert f"**Orchestrator note:** {DEFAULT_NOTE}" in body(project)

    def test_a_default_note_is_used_when_the_plan_is_missing(self, project):
        remove(project, PLAN_FILE)
        generate_phase_plan(project, today=TODAY)
        assert f"**Orchestrator note:** {DEFAULT_NOTE}" in body(project)

    def test_only_the_first_note_is_kept(self, project):
        write(
            project,
            PLAN_FILE,
            existing_plan(note="First note.") + "\n**Orchestrator note:** Second note.\n",
        )
        generate_phase_plan(project, today=TODAY)
        notes = [line for line in body(project).splitlines() if "Orchestrator note:" in line]
        assert notes == ["**Orchestrator note:** First note."]

    def test_an_unbolded_note_is_carried_over(self, project):
        """The scaffold seeds the note unbolded; the first regeneration must keep it."""
        write(project, PLAN_FILE, "# Phase Plan\n\nOrchestrator note: plain text.\n")
        generate_phase_plan(project, today=TODAY)
        assert "**Orchestrator note:** plain text." in body(project)

    def test_punctuation_and_markup_in_the_note_survive(self, project):
        note = "Blocked on `vendor-api` — see [DEC-002](decisions/x.md); 50% done."
        write(project, PLAN_FILE, existing_plan(note=note))
        generate_phase_plan(project, today=TODAY)
        assert f"**Orchestrator note:** {note}" in body(project)

    def test_the_note_survives_repeated_regeneration(self, project):
        write(project, PLAN_FILE, existing_plan(note="Keep me."))
        for _ in range(3):
            generate_phase_plan(project, today=TODAY)
        assert "**Orchestrator note:** Keep me." in body(project)


# --- Exit criteria -----------------------------------------------------------


class TestExitCriteria:
    def test_criteria_are_carried_over_verbatim(self, project):
        write(
            project,
            PLAN_FILE,
            existing_plan(
                "## Current phase exit criteria (Phase 1)",
                "",
                "- [ ] Publish the data dictionary.",
                "- [ ] Land the export job.",
            ),
        )
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Current phase exit criteria") == [
            "- [ ] Publish the data dictionary.",
            "- [ ] Land the export job.",
        ]

    def test_a_criterion_flips_when_all_its_tasks_are_done(self, project):
        write(
            project,
            "TASKS.md",
            "# Tasks\n\n## In Progress\n\n- [x] **T-008 — a**\n- [x] **T-009 — b**\n",
        )
        write(
            project,
            PLAN_FILE,
            existing_plan(
                "## Current phase exit criteria (Phase 1)", "", "- [ ] Ship T-008 and T-009."
            ),
        )
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Current phase exit criteria") == [
            "- [x] Ship T-008 and T-009."
        ]

    def test_a_criterion_does_not_flip_when_one_task_is_open(self, project):
        write(
            project,
            "TASKS.md",
            "# Tasks\n\n## In Progress\n\n- [x] **T-008 — a**\n- [ ] **T-009 — b**\n",
        )
        write(
            project,
            PLAN_FILE,
            existing_plan(
                "## Current phase exit criteria (Phase 1)", "", "- [ ] Ship T-008 and T-009."
            ),
        )
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Current phase exit criteria") == [
            "- [ ] Ship T-008 and T-009."
        ]

    def test_a_criterion_does_not_flip_when_its_task_is_absent(self, project):
        write(
            project,
            PLAN_FILE,
            existing_plan("## Current phase exit criteria (Phase 1)", "", "- [ ] Ship T-042."),
        )
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Current phase exit criteria") == ["- [ ] Ship T-042."]

    def test_a_suffixed_task_id_is_recognised(self, project):
        write(project, "TASKS.md", "# Tasks\n\n## In Progress\n\n- [x] **T-008a — a**\n")
        write(
            project,
            PLAN_FILE,
            existing_plan("## Current phase exit criteria (Phase 1)", "", "- [ ] Ship T-008a."),
        )
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Current phase exit criteria") == ["- [x] Ship T-008a."]

    def test_criteria_without_task_ids_keep_their_open_state(self, project):
        write(project, "TASKS.md", "# Tasks\n\n## In Progress\n\n- [x] **T-008 — a**\n")
        write(
            project,
            PLAN_FILE,
            existing_plan(
                "## Current phase exit criteria (Phase 1)", "", "- [ ] Everything looks right."
            ),
        )
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Current phase exit criteria") == [
            "- [ ] Everything looks right."
        ]

    def test_criteria_without_task_ids_keep_their_closed_state(self, project):
        write(
            project,
            PLAN_FILE,
            existing_plan(
                "## Current phase exit criteria (Phase 1)", "", "- [x] Signed off by the owner."
            ),
        )
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Current phase exit criteria") == [
            "- [x] Signed off by the owner."
        ]

    def test_defaults_are_used_when_there_is_no_criteria_section(self, project):
        write(project, PLAN_FILE, existing_plan("## Milestones", "", "- Ship."))
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Current phase exit criteria") == DEFAULT_CRITERIA

    def test_defaults_are_used_when_the_criteria_section_is_empty(self, project):
        write(project, PLAN_FILE, existing_plan("## Current phase exit criteria (Phase 1)", ""))
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Current phase exit criteria") == DEFAULT_CRITERIA

    def test_defaults_are_used_when_the_plan_is_missing(self, project):
        remove(project, PLAN_FILE)
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Current phase exit criteria") == DEFAULT_CRITERIA

    def test_non_checkbox_lines_in_the_section_are_dropped(self, project):
        write(
            project,
            PLAN_FILE,
            existing_plan(
                "## Current phase exit criteria (Phase 1)",
                "",
                "Some prose that is not a criterion.",
                "- [ ] A real criterion.",
            ),
        )
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Current phase exit criteria") == ["- [ ] A real criterion."]

    def test_the_criteria_heading_is_matched_case_insensitively(self, project):
        write(
            project,
            PLAN_FILE,
            existing_plan("## CURRENT PHASE EXIT CRITERIA", "", "- [ ] Shout it."),
        )
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Current phase exit criteria") == ["- [ ] Shout it."]

    def test_criteria_from_a_later_section_are_not_absorbed(self, project):
        write(
            project,
            PLAN_FILE,
            existing_plan(
                "## Current phase exit criteria (Phase 1)",
                "",
                "- [ ] Mine.",
                "",
                "## Open blockers",
                "",
                "- [ ] Not mine.",
            ),
        )
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Current phase exit criteria") == ["- [ ] Mine."]


# --- Active agents -----------------------------------------------------------


class TestActiveAgents:
    def test_one_row_per_numbered_role(self, staffed):
        generate_phase_plan(staffed, today=TODAY)
        rows = table_rows(body(staffed), "Active agents")
        assert [cells(row)[0] for row in rows] == [
            "Orchestrator",
            "Domain Expert",
            "Producer",
            "QA / Reproducibility Engineer",
            "Visualization Specialist",
        ]

    def test_unnumbered_headings_are_not_roles(self, staffed):
        generate_phase_plan(staffed, today=TODAY)
        names = [cells(row)[0] for row in table_rows(body(staffed), "Active agents")]
        assert "Shared conventions" not in names

    def test_a_role_owning_an_in_progress_task_is_active(self, staffed):
        generate_phase_plan(staffed, today=TODAY)
        row = next(
            r for r in table_rows(body(staffed), "Active agents") if cells(r)[0] == "Domain Expert"
        )
        assert cells(row)[1] == "Active"
        assert cells(row)[2] == "T-001 — Draft the data dictionary"

    def test_the_task_text_is_stripped_of_bold_markers(self, staffed):
        generate_phase_plan(staffed, today=TODAY)
        assert "**T-001" not in body(staffed)

    def test_an_optional_role_is_on_standby(self, staffed):
        generate_phase_plan(staffed, today=TODAY)
        row = next(
            r
            for r in table_rows(body(staffed), "Active agents")
            if cells(r)[0] == "Visualization Specialist"
        )
        assert cells(row)[1] == "Standby"
        assert cells(row)[2] == "Available for assignment"

    def test_the_optional_marker_is_removed_from_the_name(self, staffed):
        generate_phase_plan(staffed, today=TODAY)
        assert "(optional)" not in body(staffed)

    def test_an_unassigned_role_is_idle(self, staffed):
        generate_phase_plan(staffed, today=TODAY)
        row = next(
            r for r in table_rows(body(staffed), "Active agents") if cells(r)[0] == "Orchestrator"
        )
        assert cells(row)[1] == "Idle"

    def test_every_row_has_four_columns(self, staffed):
        generate_phase_plan(staffed, today=TODAY)
        for row in table_rows(body(staffed), "Active agents"):
            assert len(cells(row)) == 4

    def test_owners_of_queued_tasks_do_not_count_as_active(self, staffed):
        write(
            staffed,
            "TASKS.md",
            "# Tasks\n\n## In Progress\n\n- [ ] **T-001 — a**\n\n"
            "## Queued\n\n- [ ] **T-002 — b**\n  Owner: Producer\n",
        )
        generate_phase_plan(staffed, today=TODAY)
        row = next(
            r for r in table_rows(body(staffed), "Active agents") if cells(r)[0] == "Producer"
        )
        assert cells(row)[1] == "Idle"

    def test_the_first_task_wins_when_an_owner_holds_two(self, staffed):
        write(
            staffed,
            "TASKS.md",
            "# Tasks\n\n## In Progress\n\n- [ ] **T-001 — first**\n  Owner: Producer\n\n"
            "- [ ] **T-002 — second**\n  Owner: Producer\n",
        )
        generate_phase_plan(staffed, today=TODAY)
        row = next(
            r for r in table_rows(body(staffed), "Active agents") if cells(r)[0] == "Producer"
        )
        assert cells(row)[2] == "T-001 — first"

    def test_a_default_row_is_written_when_there_are_no_roles(self, project):
        write(project, "AGENTS.md", "# Agents\n\n## Operating Rules\n\nBe careful.\n")
        generate_phase_plan(project, today=TODAY)
        rows = table_rows(body(project), "Active agents")
        assert rows == ["| Orchestrator | Active | Route the next dispatch | — |"]

    def test_owner_matching_is_exact(self, staffed):
        write(
            staffed,
            "TASKS.md",
            "# Tasks\n\n## In Progress\n\n- [ ] **T-001 — a**\n  Owner: Domain Experts\n",
        )
        generate_phase_plan(staffed, today=TODAY)
        row = next(
            r for r in table_rows(body(staffed), "Active agents") if cells(r)[0] == "Domain Expert"
        )
        assert cells(row)[1] == "Idle"


# --- Dispatch queue ----------------------------------------------------------


class TestDispatchQueue:
    def test_queued_tasks_are_listed(self, staffed):
        generate_phase_plan(staffed, today=TODAY)
        assert section(body(staffed), "Dispatch queue") == [
            "- T-002 — Record the second decision",
            "- T-003 — Review the roster",
        ]

    def test_bold_markers_are_stripped(self, staffed):
        generate_phase_plan(staffed, today=TODAY)
        assert all("**" not in line for line in section(body(staffed), "Dispatch queue"))

    def test_a_default_is_used_when_there_is_no_queued_section(self, project):
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Dispatch queue") == [DEFAULT_QUEUE]

    def test_a_default_is_used_when_the_queued_section_is_empty(self, project):
        write(project, "TASKS.md", "# Tasks\n\n## In Progress\n\n- [ ] a\n\n## Queued\n\n")
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Dispatch queue") == [DEFAULT_QUEUE]

    def test_a_suffixed_queued_heading_still_matches(self, project):
        write(
            project,
            "TASKS.md",
            "# Tasks\n\n## In Progress\n\n- [ ] a\n\n## Queued (next up)\n\n- [ ] **T-9 — b**\n",
        )
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Dispatch queue") == ["- T-9 — b"]

    def test_done_and_backlog_tasks_stay_out_of_the_queue(self, staffed):
        generate_phase_plan(staffed, today=TODAY)
        queue = section(body(staffed), "Dispatch queue")
        assert not any("T-000" in line for line in queue)
        assert not any("T-001" in line for line in queue)


# --- Blockers ----------------------------------------------------------------


class TestBlockers:
    def test_checkbox_blockers_are_listed(self, staffed):
        generate_phase_plan(staffed, today=TODAY)
        assert section(body(staffed), "Open blockers") == [
            "- B-001 — Waiting on the vendor contract"
        ]

    def test_a_default_is_used_when_there_is_no_blockers_section(self, project):
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Open blockers") == [DEFAULT_BLOCKERS]

    def test_a_default_is_used_when_the_blockers_section_is_empty(self, project):
        write(project, "TASKS.md", "# Tasks\n\n## In Progress\n\n- [ ] a\n\n## Blockers\n\n")
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Open blockers") == [DEFAULT_BLOCKERS]

    def test_bold_markers_are_stripped(self, staffed):
        generate_phase_plan(staffed, today=TODAY)
        assert all("**" not in line for line in section(body(staffed), "Open blockers"))

    def test_plain_bullet_blockers_are_carried_over(self, project):
        """REGRESSION: dropping a blocker made the plan assert the opposite of the truth.

        Blockers are routinely written as plain bullets — the scaffold itself emits
        that form — and a dropped one was replaced by "None currently filed."
        """
        write(
            project,
            "TASKS.md",
            "# Tasks\n\n## In Progress\n\n- [ ] a\n\n## Blockers\n\n"
            "- Waiting on the vendor contract.\n",
        )
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Open blockers") == ["- Waiting on the vendor contract."]


# --- Decision rows -----------------------------------------------------------


class TestDecisionRows:
    def test_a_placeholder_row_is_used_when_there_are_no_decisions(self, project):
        shutil.rmtree(project / "docs" / "decisions")
        generate_phase_plan(project, today=TODAY)
        assert table_rows(body(project), "Decision log") == [NO_DECISIONS_ROW]

    def test_the_readme_is_not_a_decision(self, project):
        for path in (project / "docs" / "decisions").glob("*.md"):
            if path.name != "README.md":
                path.unlink()
        generate_phase_plan(project, today=TODAY)
        assert table_rows(body(project), "Decision log") == [NO_DECISIONS_ROW]

    def test_decisions_are_listed_newest_first(self, project):
        (project / "docs" / "decisions" / SEED_DECISION).unlink()
        for name in (
            "20260101_DEC001_first.md",
            "20260201_DEC002_second.md",
            "20260301_DEC003_third.md",
        ):
            write(project, f"docs/decisions/{name}", decision_text(name))
        generate_phase_plan(project, today=TODAY)
        rows = table_rows(body(project), "Decision log")
        files = [row.split("(decisions/")[1].split(")")[0] for row in rows]
        assert files == [
            "20260301_DEC003_third.md",
            "20260201_DEC002_second.md",
            "20260101_DEC001_first.md",
        ]

    def test_the_title_is_split_on_the_em_dash(self, project):
        write(
            project,
            f"docs/decisions/{SEED_DECISION}",
            "# DEC-001 — Adopt the governance layer\n\nDate: 2026-01-01\n"
            "Authority: Orchestrator\nStatus: Decided\n",
        )
        generate_phase_plan(project, today=TODAY)
        row = cells(table_rows(body(project), "Decision log")[0])
        assert row[0] == f"[DEC-001](decisions/{SEED_DECISION})"
        assert row[2] == "Adopt the governance layer"

    def test_date_status_and_authority_are_parsed(self, project):
        write(
            project,
            f"docs/decisions/{SEED_DECISION}",
            "# DEC-001 — Adopt it\n\nDate: 2026-01-01\nAuthority: Orchestrator\nStatus: Decided\n",
        )
        generate_phase_plan(project, today=TODAY)
        row = cells(table_rows(body(project), "Decision log")[0])
        assert row[1] == "2026-01-01"
        assert row[3] == "Decided"
        assert row[4] == "Orchestrator"

    def test_bold_field_labels_are_parsed_too(self, project):
        write(
            project,
            f"docs/decisions/{SEED_DECISION}",
            "# DEC-001 — Adopt it\n\n**Date:** 2026-01-01\n**Authority:** QA\n"
            "**Status:** Superseded\n",
        )
        generate_phase_plan(project, today=TODAY)
        row = cells(table_rows(body(project), "Decision log")[0])
        assert row[1] == "2026-01-01"
        assert row[3] == "Superseded"
        assert row[4] == "QA"

    def test_missing_fields_render_as_dashes(self, project):
        write(project, f"docs/decisions/{SEED_DECISION}", "# DEC-001 — Adopt it\n\nNo fields.\n")
        generate_phase_plan(project, today=TODAY)
        row = cells(table_rows(body(project), "Decision log")[0])
        assert row[1] == "-"
        assert row[3] == "-"
        assert row[4] == "-"

    def test_a_title_without_an_em_dash_fills_both_columns(self, project):
        write(project, f"docs/decisions/{SEED_DECISION}", "# Adopt the layer\n\nNo fields.\n")
        generate_phase_plan(project, today=TODAY)
        row = cells(table_rows(body(project), "Decision log")[0])
        assert row[0] == f"[Adopt the layer](decisions/{SEED_DECISION})"
        assert row[2] == "Adopt the layer"

    def test_a_file_without_a_title_falls_back_to_its_stem(self, project):
        write(project, f"docs/decisions/{SEED_DECISION}", "No heading here.\n")
        generate_phase_plan(project, today=TODAY)
        row = cells(table_rows(body(project), "Decision log")[0])
        assert row[0] == f"[{Path(SEED_DECISION).stem}](decisions/{SEED_DECISION})"

    def test_every_row_links_a_file_that_exists(self, project):
        write(project, "docs/decisions/20260201_DEC002_second.md", decision_text("DEC-002"))
        generate_phase_plan(project, today=TODAY)
        for row in table_rows(body(project), "Decision log"):
            name = row.split("(decisions/")[1].split(")")[0]
            assert (project / "docs" / "decisions" / name).is_file()

    def test_the_table_header_is_written_once(self, project):
        generate_phase_plan(project, today=TODAY)
        assert body(project).count("| ID | Date | Topic | Status | Authority |") == 1


# --- Completed phases --------------------------------------------------------


class TestCompletedPhases:
    def test_completed_phases_are_carried_over(self, project):
        write(
            project,
            PLAN_FILE,
            existing_plan(
                "## Completed phases",
                "",
                "- **Phase 0** — Scoping.",
                "- **Phase 1** — Foundation.",
            ),
        )
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Completed phases") == [
            "- **Phase 0** — Scoping.",
            "- **Phase 1** — Foundation.",
        ]

    def test_a_default_is_used_when_the_section_is_absent(self, project):
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Completed phases") == [DEFAULT_COMPLETED]

    def test_a_default_is_used_when_the_section_has_no_bullets(self, project):
        write(project, PLAN_FILE, existing_plan("## Completed phases", "", "Nothing yet."))
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Completed phases") == [DEFAULT_COMPLETED]

    def test_only_bulleted_lines_are_carried(self, project):
        write(
            project,
            PLAN_FILE,
            existing_plan("## Completed phases", "", "Prose line.", "- **Phase 0** — Scoping."),
        )
        generate_phase_plan(project, today=TODAY)
        assert section(body(project), "Completed phases") == ["- **Phase 0** — Scoping."]


# --- The generated document as a whole ---------------------------------------


class TestGeneratedDocument:
    def test_the_project_name_comes_from_the_charter_title(self, project):
        charter_with(project)
        write(
            project,
            "PROJECT_CHARTER.md",
            charter_text().replace("# Project Charter", "# Project Charter — Demo Project", 1),
        )
        generate_phase_plan(project, today=TODAY)
        assert body(project).startswith("# Phase Plan — Demo Project\n")

    def test_the_name_falls_back_to_the_directory(self, project):
        generate_phase_plan(project, today=TODAY)
        assert body(project).startswith(f"# Phase Plan — {project.name}\n")

    def test_the_stop_banner_is_present(self, project):
        generate_phase_plan(project, today=TODAY)
        assert "> ⚠️ **STOP — READ BEFORE EDITING.**" in body(project)

    def test_the_last_updated_date_is_the_injected_one(self, project):
        generate_phase_plan(project, today=_dt.date(2030, 6, 7))
        assert "**Last updated:** 2030-06-07" in body(project)

    def test_omitting_today_uses_the_real_date(self, project):
        before = _dt.date.today()
        generate_phase_plan(project)
        after = _dt.date.today()
        stamps = {f"**Last updated:** {d:%Y-%m-%d}" for d in (before, after)}
        assert any(stamp in body(project) for stamp in stamps)

    def test_all_six_sections_are_written(self, project):
        generate_phase_plan(project, today=TODAY)
        headings = [line for line in body(project).splitlines() if line.startswith("## ")]
        assert len(headings) == 6
        assert headings[0] == "## Active agents"
        assert headings[-1] == "## Completed phases"

    def test_no_heading_is_duplicated(self, project):
        generate_phase_plan(project, today=TODAY)
        headings = [line for line in body(project).splitlines() if line.startswith("## ")]
        assert len(set(headings)) == len(headings)

    def test_the_document_stays_under_its_own_two_hundred_line_cap(self, staffed):
        summary = generate_phase_plan(staffed, today=TODAY)
        assert summary["lines"] <= 200

    def test_the_file_is_written_as_utf8(self, project):
        generate_phase_plan(project, today=TODAY)
        assert "—" in (project / PLAN_FILE).read_text(encoding="utf-8")

    def test_regeneration_is_stable(self, staffed):
        generate_phase_plan(staffed, today=TODAY)
        first = body(staffed)
        generate_phase_plan(staffed, today=TODAY)
        assert body(staffed) == first

    def test_regeneration_replaces_rather_than_appends(self, staffed):
        generate_phase_plan(staffed, today=TODAY)
        generate_phase_plan(staffed, today=TODAY)
        assert body(staffed).count("## Active agents") == 1


class TestSummary:
    def test_summary_keys_are_stable(self, project):
        summary = generate_phase_plan(project, today=TODAY)
        assert set(summary) == {"file", "current_phase", "phase_title", "lines", "written"}

    def test_summary_reports_the_relative_file(self, project):
        assert generate_phase_plan(project, today=TODAY)["file"] == PLAN_FILE

    def test_summary_line_count_matches_the_file(self, staffed):
        summary = generate_phase_plan(staffed, today=TODAY)
        assert summary["lines"] == len(body(staffed).splitlines())

    def test_summary_phase_matches_the_document(self, project):
        write(project, "STATUS.md", "# Status\n\n## 2026-01-01 — Phase 5 kickoff\n\n- go\n")
        charter_with(project, "**Phase 5 — Land it.**", phases=(1, 2, 3, 4, 5))
        summary = generate_phase_plan(project, today=TODAY)
        assert f"Phase {summary['current_phase']} — {summary['phase_title']}" in body(project)

    def test_summary_is_json_serialisable(self, project):
        json.dumps(generate_phase_plan(project, today=TODAY))


# --- The point of the whole exercise -----------------------------------------


class TestGeneratedPlanStaysCompliant:
    """A generator that breaks its own project's compliance is a liability."""

    def test_phase_sync_passes_after_generation(self, project):
        generate_phase_plan(project, today=TODAY)
        report = report_for(project)
        assert [f.status for f in findings(report, "phase_sync")] == [Status.PASS]

    def test_no_duplicate_h2_failures_after_generation(self, project):
        generate_phase_plan(project, today=TODAY)
        report = report_for(project)
        assert findings(report, "duplicate_h2", Status.FAIL) == []

    def test_the_project_still_passes_end_to_end(self, project):
        generate_phase_plan(project, today=TODAY)
        report = report_for(project)
        assert report.failed == 0, [f.message for f in report.of_status(Status.FAIL)]

    def test_a_later_phase_still_syncs_with_the_charter(self, project):
        write(project, "STATUS.md", "# Status\n\n## 2026-01-01 — Phase 3 kickoff\n\n- go\n")
        charter_with(project, "**Phase 3 — Deliver & verify.**", phases=(1, 2, 3))
        generate_phase_plan(project, today=TODAY)
        report = report_for(project)
        assert [f.status for f in findings(report, "phase_sync")] == [Status.PASS]

    def test_the_plan_is_not_stale_relative_to_status(self, project):
        generate_phase_plan(project, today=TODAY)
        report = report_for(project)
        assert [f.status for f in findings(report, "plan_staleness")] == [Status.PASS]

    def test_a_staffed_project_still_passes(self, staffed):
        generate_phase_plan(staffed, today=TODAY)
        report = report_for(staffed)
        assert report.failed == 0, [f.message for f in report.of_status(Status.FAIL)]

    def test_regenerating_a_fresh_scaffold_keeps_it_at_the_graduation_gate(self, tmp_path):
        from chartworkai.scaffold import init_project

        day = _dt.date(2026, 3, 4)
        root = tmp_path / "scaffolded"
        init_project(root, "Chart Works Demo", today=day)
        for path in root.glob("_framework_*"):
            shutil.rmtree(path)

        generate_phase_plan(root, today=day)
        report = report_for(root)
        assert {f.check for f in report.of_status(Status.FAIL)} == {"placeholders"}
        assert report.warnings == 0
