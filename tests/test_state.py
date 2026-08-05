"""Behavioural tests for :mod:`chartworkai.state` — reading and writing project state.

Reading is tested the way ``read_state`` is used: start from the fully compliant
fixture built by ``make_project``, mutate exactly one document, assert on the one
field that mutation is supposed to move.

Writing is tested against the contract that actually matters downstream — a file
``chartworkai.checks`` accepts, and that ``read_state`` can parse back. Today's date
is frozen through the ``today`` fixture so filenames stay deterministic.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import pytest
from conftest import (
    SEED_DECISION,
    charter_text,
    decision_text,
    fail_messages,
    phase_plan_text,
    remove,
    report_for,
    warn_messages,
    write,
)

from chartworkai import state as state_module
from chartworkai.checks import DECISION_NAME_RE
from chartworkai.state import (
    NAMESPACES,
    file_decision,
    file_handoff,
    next_decision_id,
    read_state,
)

STATE_KEYS = {
    "project_root",
    "project",
    "profile",
    "is_data_profile",
    "current_phase",
    "verify_command",
    "tasks",
    "recent_decisions",
    "recent_handoffs",
}
TASK_KEYS = {"in_progress", "queued", "blockers"}
DECISION_KEYS = {"file", "title", "date", "authority", "status"}
HANDOFF_KEYS = {"file", "title"}

#: A fixed "today" so generated filenames are assertable.
FROZEN_TODAY = _dt.date(2026, 3, 4)
STAMP = "20260304"
DASHED = "2026-03-04"


@pytest.fixture
def today(monkeypatch) -> _dt.date:
    """Freeze ``state._today`` so date-stamped filenames are deterministic."""
    monkeypatch.setattr(state_module, "_today", lambda: FROZEN_TODAY)
    return FROZEN_TODAY


@pytest.fixture
def empty(tmp_path: Path) -> Path:
    """A bare directory: no governance layer at all."""
    root = tmp_path / "bare"
    root.mkdir()
    return root


def charter_with(project: Path, *extra: str) -> None:
    """Rewrite the charter as the compliant baseline plus *extra* lines."""
    write(project, "PROJECT_CHARTER.md", charter_text() + "\n".join(extra) + "\n")


def tasks_with(project: Path, *lines: str) -> None:
    write(project, "TASKS.md", "\n".join(("# Tasks", "") + lines) + "\n")


# --- Shape of the state document ---------------------------------------------


class TestStateShape:
    def test_top_level_keys(self, project):
        assert set(read_state(project)) == STATE_KEYS

    def test_task_and_record_keys(self, project):
        state = read_state(project)
        assert set(state["tasks"]) == TASK_KEYS
        assert set(state["recent_decisions"][0]) == DECISION_KEYS

    def test_handoff_keys(self, project):
        write(project, "docs/handoffs/2026-01-02_analyst.md", "# Handoff — Analyst\n")
        assert set(read_state(project)["recent_handoffs"][0]) == HANDOFF_KEYS

    def test_the_whole_document_is_json_serialisable(self, project):
        # `chartworkai state` json.dumps this verbatim; a stray Path would break it.
        assert json.loads(json.dumps(read_state(project))) == read_state(project)

    def test_project_root_is_absolute_and_resolved(self, project):
        assert read_state(project)["project_root"] == str(project.resolve())

    def test_project_root_resolves_a_relative_path(self, project, monkeypatch):
        monkeypatch.chdir(project.parent)
        assert read_state(project.name)["project_root"] == str(project.resolve())

    def test_baseline_values(self, project):
        state = read_state(project)
        assert state["profile"] == "data-science"
        assert state["is_data_profile"] is True
        assert state["current_phase"] == 1
        assert state["verify_command"] is None
        assert state["tasks"]["in_progress"] == ["Draft the data dictionary."]
        assert state["tasks"]["queued"] == ["Record the second decision."]
        assert state["tasks"]["blockers"] == []

    @pytest.mark.parametrize(
        "profile, is_data", [("data-science", True), ("software-app", False), (None, True)]
    )
    def test_profile_mirrors_the_checker(self, make, profile, is_data):
        state = read_state(make(profile=profile))
        assert state["profile"] == profile
        assert state["is_data_profile"] is is_data


# --- Project name -------------------------------------------------------------


class TestProjectName:
    @pytest.mark.parametrize(
        "heading, expected",
        [
            ("# Project Charter — Acme Pipeline", "Acme Pipeline"),
            ("# Project Charter: Acme Pipeline", "Acme Pipeline"),
            ("# Project Charter - Acme Pipeline", "Acme Pipeline"),
            ("# project charter — lowercase prefix", "lowercase prefix"),
            ("# PROJECT CHARTER — SHOUTED PREFIX", "SHOUTED PREFIX"),
            ("# Acme Pipeline", "Acme Pipeline"),
            ("#   Padded Title   ", "Padded Title"),
        ],
    )
    def test_the_h1_names_the_project(self, project, heading, expected):
        write(project, "PROJECT_CHARTER.md", f"{heading}\n\nBody.\n")
        assert read_state(project)["project"] == expected

    def test_a_bare_charter_prefix_is_not_stripped(self, project):
        # Nothing follows "Project Charter", so there is no separator to strip.
        write(project, "PROJECT_CHARTER.md", "# Project Charter\n")
        assert read_state(project)["project"] == "Project Charter"

    @pytest.mark.parametrize(
        "charter",
        [
            "No heading at all.\n",
            "",
            "## Only an H2\n",
            "# Project Charter — \n",  # prefix strips to nothing
            "#NoSpaceAfterHash\n",
        ],
    )
    def test_falls_back_to_the_directory_name(self, project, charter):
        write(project, "PROJECT_CHARTER.md", charter)
        assert read_state(project)["project"] == project.name

    def test_missing_charter_falls_back_to_the_directory_name(self, project):
        remove(project, "PROJECT_CHARTER.md")
        assert read_state(project)["project"] == project.name

    def test_the_first_h1_wins(self, project):
        write(project, "PROJECT_CHARTER.md", "# First\n\n# Second\n")
        assert read_state(project)["project"] == "First"


# --- Verify command -----------------------------------------------------------


class TestVerifyCommand:
    @pytest.mark.parametrize(
        "line, expected",
        [
            ("**Verify command:** `pytest -q`", "pytest -q"),
            ("Verify command: `make test`", "make test"),
            ("**Verify command:** Run `pytest -q` before every merge.", "pytest -q"),
            ("**Verify command:** `first` then `second`", "first"),
            ("**verify COMMAND:** `case insensitive`", "case insensitive"),
            ("- Verify command: `bin/verify --all`", "bin/verify --all"),
        ],
    )
    def test_prefers_the_backticked_span(self, project, line, expected):
        charter_with(project, line)
        assert read_state(project)["verify_command"] == expected

    @pytest.mark.parametrize(
        "line, expected",
        [
            ("**Verify command:** pytest -q", "pytest -q"),
            ("Verify command: ./scripts/verify.sh --strict", "./scripts/verify.sh --strict"),
            ("**Verify command:** make test   ", "make test"),
        ],
    )
    def test_returns_the_plain_line_without_backticks(self, project, line, expected):
        charter_with(project, line)
        assert read_state(project)["verify_command"] == expected

    def test_none_when_the_charter_never_mentions_one(self, project):
        assert read_state(project)["verify_command"] is None

    def test_none_when_the_charter_is_missing(self, project):
        remove(project, "PROJECT_CHARTER.md")
        assert read_state(project)["verify_command"] is None

    def test_the_first_declaration_wins(self, project):
        charter_with(project, "**Verify command:** `first`", "", "**Verify command:** `second`")
        assert read_state(project)["verify_command"] == "first"

    @pytest.mark.parametrize("line", ["**Verify command:**", "Verify command:"])
    def test_an_empty_declaration_does_not_absorb_the_next_line(self, project, line):
        """REGRESSION: an unfilled declaration must yield None, not the next line.

        Handing an agent a garbage verify command is worse than admitting there
        isn't one. Same hazard checks.PROFILE_RE guards against.
        """
        charter_with(project, line, "", "## Mission", "", "Ship the pipeline.")
        assert read_state(project)["verify_command"] is None


# --- Current phase ------------------------------------------------------------


class TestCurrentPhase:
    @pytest.mark.parametrize("number", [1, 2, 7, 12])
    def test_parsed_from_the_phase_plan(self, project, number):
        write(project, "docs/phase_plan.md", phase_plan_text(current_phase=number))
        assert read_state(project)["current_phase"] == number

    def test_returned_as_an_integer(self, project):
        assert isinstance(read_state(project)["current_phase"], int)

    @pytest.mark.parametrize(
        "plan",
        [
            "# Phase Plan\n\n**Last updated:** 2026-01-02\n",
            "# Phase Plan\n\n**Current phase:** discovery\n",
            "# Phase Plan\n\nPhase 3 is next.\n",
            "",
        ],
    )
    def test_none_when_unparseable(self, project, plan):
        write(project, "docs/phase_plan.md", plan)
        assert read_state(project)["current_phase"] is None

    def test_none_when_the_plan_is_missing(self, project):
        remove(project, "docs/phase_plan.md")
        assert read_state(project)["current_phase"] is None

    def test_matching_is_case_insensitive(self, project):
        write(project, "docs/phase_plan.md", "# Plan\n\ncurrent phase: phase 4 — build\n")
        assert read_state(project)["current_phase"] == 4


# --- Tasks --------------------------------------------------------------------


class TestTasks:
    def test_bold_markers_are_stripped(self, project):
        tasks_with(project, "## In Progress", "", "- [ ] **Ship** the **loader**")
        assert read_state(project)["tasks"]["in_progress"] == ["Ship the loader"]

    def test_checked_and_unchecked_bullets_are_both_collected(self, project):
        tasks_with(project, "## In Progress", "", "- [ ] open", "- [x] closed", "- [X] shouted")
        assert read_state(project)["tasks"]["in_progress"] == ["open", "closed", "shouted"]

    def test_indented_bullets_are_collected(self, project):
        tasks_with(project, "## In Progress", "", "  - [ ] nested item")
        assert read_state(project)["tasks"]["in_progress"] == ["nested item"]

    @pytest.mark.parametrize(
        "line",
        ["- plain bullet", "* [ ] wrong marker", "- [] no space", "1. [ ] numbered", "prose"],
    )
    def test_non_checkbox_lines_are_ignored(self, project, line):
        tasks_with(project, "## In Progress", "", line)
        assert read_state(project)["tasks"]["in_progress"] == []

    def test_bullets_before_the_first_heading_are_ignored(self, project):
        tasks_with(project, "- [ ] orphan", "", "## In Progress", "", "- [ ] real")
        assert read_state(project)["tasks"]["in_progress"] == ["real"]

    def test_blockers_section(self, project):
        tasks_with(project, "## Blockers", "", "- [ ] Waiting on **vendor** access")
        assert read_state(project)["tasks"]["blockers"] == ["Waiting on vendor access"]

    def test_queued_section(self, project):
        tasks_with(project, "## Queued", "", "- [ ] later work")
        assert read_state(project)["tasks"]["queued"] == ["later work"]

    def test_next_stands_in_for_queued(self, project):
        tasks_with(project, "## Next", "", "- [ ] next work")
        assert read_state(project)["tasks"]["queued"] == ["next work"]

    def test_queued_wins_over_next_when_both_exist(self, project):
        tasks_with(
            project,
            "## Next",
            "",
            "- [ ] from next",
            "",
            "## Queued",
            "",
            "- [ ] from queued",
        )
        assert read_state(project)["tasks"]["queued"] == ["from queued"]

    @pytest.mark.parametrize(
        "heading", ["## In Progress", "## in progress", "## In Progress (this week)"]
    )
    def test_section_headings_match_on_prefix_case_insensitively(self, project, heading):
        tasks_with(project, heading, "", "- [ ] item")
        assert read_state(project)["tasks"]["in_progress"] == ["item"]

    def test_unrelated_sections_are_not_reported(self, project):
        tasks_with(project, "## Done", "", "- [x] finished")
        assert read_state(project)["tasks"] == {"in_progress": [], "queued": [], "blockers": []}

    def test_missing_tasks_file_yields_empty_sections(self, project):
        remove(project, "TASKS.md")
        assert read_state(project)["tasks"] == {"in_progress": [], "queued": [], "blockers": []}


# --- Recent decisions ---------------------------------------------------------


class TestRecentDecisions:
    def test_fields_are_parsed_from_the_file(self, project):
        write(
            project,
            "docs/decisions/20260201_DEC002_pick_a_warehouse.md",
            "# DEC-002 — Pick a warehouse\n\n"
            "**Date:** 2026-02-01\n**Authority:** Orchestrator\n**Status:** Decided\n",
        )
        record = read_state(project)["recent_decisions"][0]
        assert record["file"] == "docs/decisions/20260201_DEC002_pick_a_warehouse.md"
        assert record["title"] == "DEC-002 — Pick a warehouse"
        assert record["date"] == "2026-02-01"
        assert record["authority"] == "Orchestrator"
        assert record["status"] == "Decided"

    def test_missing_fields_come_back_as_none(self, project):
        record = read_state(project)["recent_decisions"][0]
        assert record["date"] is None
        assert record["authority"] is None
        assert record["status"] is None

    def test_title_falls_back_to_the_file_stem(self, project):
        write(project, "docs/decisions/20260202_DEC003_untitled.md", "no heading here\n")
        assert read_state(project)["recent_decisions"][0]["title"] == "20260202_DEC003_untitled"

    def test_newest_first(self, project):
        for stamp, number in [("20260102", "002"), ("20260305", "003"), ("20251201", "004")]:
            name = f"{stamp}_DEC{number}_entry.md"
            write(project, f"docs/decisions/{name}", decision_text(name))
        dates = [d["file"] for d in read_state(project)["recent_decisions"]]
        assert dates == sorted(dates, reverse=True)
        assert dates[0].endswith("20260305_DEC003_entry.md")

    def test_capped_at_five(self, project):
        for index in range(8):
            name = f"202602{index + 10:02d}_DEC{index + 10:03d}_entry.md"
            write(project, f"docs/decisions/{name}", decision_text(name))
        records = read_state(project)["recent_decisions"]
        assert len(records) == 5
        assert records[0]["file"].endswith("20260217_DEC017_entry.md")

    def test_readme_is_not_a_decision(self, project):
        remove(project, f"docs/decisions/{SEED_DECISION}")
        assert read_state(project)["recent_decisions"] == []

    def test_empty_when_the_directory_is_missing(self, project):
        remove(project, "docs/decisions")
        assert read_state(project)["recent_decisions"] == []

    def test_non_markdown_files_are_ignored(self, project):
        write(project, "docs/decisions/notes.txt", "# Not a decision\n")
        assert len(read_state(project)["recent_decisions"]) == 1


# --- Recent handoffs ----------------------------------------------------------


class TestRecentHandoffs:
    def test_empty_when_only_a_readme_exists(self, project):
        assert read_state(project)["recent_handoffs"] == []

    def test_empty_when_the_directory_is_missing(self, project):
        remove(project, "docs/handoffs")
        assert read_state(project)["recent_handoffs"] == []

    def test_title_comes_from_the_h1(self, project):
        write(project, "docs/handoffs/2026-02-01_analyst.md", "# Handoff — Analyst\n\nBody.\n")
        record = read_state(project)["recent_handoffs"][0]
        assert record == {
            "file": "docs/handoffs/2026-02-01_analyst.md",
            "title": "Handoff — Analyst",
        }

    def test_title_falls_back_to_the_file_stem(self, project):
        write(project, "docs/handoffs/2026-02-01_analyst.md", "no heading\n")
        assert read_state(project)["recent_handoffs"][0]["title"] == "2026-02-01_analyst"

    def test_newest_first_and_capped_at_five(self, project):
        for day in range(1, 9):
            write(project, f"docs/handoffs/2026-02-{day:02d}_agent.md", f"# Handoff {day}\n")
        records = read_state(project)["recent_handoffs"]
        assert len(records) == 5
        assert records[0]["file"] == "docs/handoffs/2026-02-08_agent.md"
        assert records[-1]["file"] == "docs/handoffs/2026-02-04_agent.md"


# --- Degrading gracefully -----------------------------------------------------


class TestDegradesGracefully:
    def test_a_directory_with_nothing_in_it(self, empty):
        state = read_state(empty)
        assert set(state) == STATE_KEYS
        assert state["project"] == "bare"
        assert state["profile"] is None
        assert state["current_phase"] is None
        assert state["verify_command"] is None
        assert state["recent_decisions"] == []
        assert state["recent_handoffs"] == []

    def test_a_root_that_does_not_exist(self, tmp_path):
        state = read_state(tmp_path / "nowhere")
        assert state["project"] == "nowhere"
        assert state["tasks"] == {"in_progress": [], "queued": [], "blockers": []}

    def test_a_root_that_is_a_file(self, tmp_path):
        path = tmp_path / "notadir.md"
        path.write_text("# Not a project\n", encoding="utf-8")
        assert read_state(path)["project"] == "notadir.md"

    @pytest.mark.parametrize(
        "rel",
        [
            "PROJECT_CHARTER.md",
            "TASKS.md",
            "docs/phase_plan.md",
            "docs/decisions",
            "docs/handoffs",
            "docs",
        ],
    )
    def test_removing_any_input_never_raises(self, project, rel):
        remove(project, rel)
        assert set(read_state(project)) == STATE_KEYS

    def test_undecodable_bytes_are_replaced_not_raised(self, project):
        (project / "PROJECT_CHARTER.md").write_bytes(b"# Caf\xe9 Charter\n")
        assert read_state(project)["project"].startswith("Caf")

    def test_a_directory_named_like_a_document(self, project):
        remove(project, "TASKS.md")
        (project / "TASKS.md").mkdir()
        assert read_state(project)["tasks"]["in_progress"] == []


# --- next_decision_id ---------------------------------------------------------


class TestNextDecisionId:
    @pytest.mark.parametrize("namespace", NAMESPACES)
    def test_starts_at_one_on_an_empty_project(self, empty, namespace):
        assert next_decision_id(empty, namespace) == 1

    def test_counts_only_the_requested_namespace(self, make):
        project = make(decisions=())
        for name in ("20260101_DEC001_a.md", "20260102_DEC002_b.md", "20260103_SC001_c.md"):
            write(project, f"docs/decisions/{name}", decision_text(name))
        assert next_decision_id(project, "DEC") == 3
        assert next_decision_id(project, "SC") == 2
        assert next_decision_id(project, "DQ") == 1
        assert next_decision_id(project, "MD") == 1

    @pytest.mark.parametrize("namespace", ["dec", "DEC", "Dec"])
    def test_the_namespace_argument_is_case_insensitive(self, project, namespace):
        assert next_decision_id(project, namespace) == 2

    def test_lowercase_namespaces_on_disk_still_count(self, make):
        project = make(decisions=())
        write(project, "docs/decisions/20260101_dec004_legacy.md", "# legacy\n")
        assert next_decision_id(project, "DEC") == 5

    def test_it_takes_the_highest_not_the_count(self, make):
        project = make(decisions=())
        for name in ("20260101_DEC001_a.md", "20260102_DEC009_b.md"):
            write(project, f"docs/decisions/{name}", decision_text(name))
        assert next_decision_id(project, "DEC") == 10

    @pytest.mark.parametrize(
        "name", ["README.md", "scratch_notes.md", "DEC001_no_date.md", "20260101_DEC1_short.md"]
    )
    def test_files_outside_the_naming_convention_are_ignored(self, make, name):
        project = make(decisions=())
        write(project, f"docs/decisions/{name}", "# Notes\n")
        assert next_decision_id(project, "DEC") == 1

    def test_missing_directory_is_treated_as_empty(self, project):
        remove(project, "docs/decisions")
        assert next_decision_id(project, "DEC") == 1


# --- file_decision ------------------------------------------------------------


class TestFileDecision:
    def test_return_contract(self, project, today):
        result = file_decision(project, "Adopt Postgres", "Orchestrator", "ctx", "ruling")
        assert set(result) == {"id", "file", "charter_row", "next_step"}
        assert result["id"] == "DEC-002"
        assert result["file"] == f"docs/decisions/{STAMP}_DEC002_adopt_postgres.md"
        assert (project / result["file"]).is_file()
        assert "PROJECT_CHARTER.md" in result["next_step"]

    def test_charter_row_carries_the_path_title_and_authority(self, project, today):
        result = file_decision(project, "Adopt Postgres", "Orchestrator", "ctx", "ruling")
        row = result["charter_row"]
        assert result["file"] in row
        assert row.startswith(f"| {DASHED} |")
        assert "Adopt Postgres" in row
        assert "Orchestrator" in row

    def test_the_body_records_every_field(self, project, today):
        result = file_decision(
            project, "Adopt Postgres", "Orchestrator", "the context", "the ruling"
        )
        body = (project / result["file"]).read_text(encoding="utf-8")
        assert body.startswith("# DEC-002 — Adopt Postgres\n")
        assert f"**Date:** {DASHED}" in body
        assert "**Authority:** Orchestrator" in body
        assert "**Status:** Decided" in body
        assert "## Context\n\nthe context" in body
        assert "## Ruling\n\nthe ruling" in body

    def test_rationale_is_included_when_given(self, project, today):
        result = file_decision(project, "T", "A", "c", "r", rationale="  because  ")
        assert "## Rationale\n\nbecause" in (project / result["file"]).read_text(encoding="utf-8")

    @pytest.mark.parametrize("rationale", ["", "   ", "\n\t"])
    def test_rationale_section_is_omitted_when_blank(self, project, today, rationale):
        result = file_decision(project, "T", "A", "c", "r", rationale=rationale)
        assert "## Rationale" not in (project / result["file"]).read_text(encoding="utf-8")

    def test_directories_are_created_when_missing(self, empty, today):
        result = file_decision(empty, "First decision", "Owner", "c", "r")
        assert (empty / "docs" / "decisions").is_dir()
        assert (empty / result["file"]).is_file()

    def test_ids_increment_within_a_namespace(self, empty, today):
        ids = [file_decision(empty, f"t{n}", "A", "c", "r")["id"] for n in range(3)]
        assert ids == ["DEC-001", "DEC-002", "DEC-003"]

    def test_namespaces_do_not_interfere(self, empty, today):
        assert file_decision(empty, "a", "A", "c", "r", namespace="DEC")["id"] == "DEC-001"
        assert file_decision(empty, "b", "A", "c", "r", namespace="SC")["id"] == "SC-001"
        assert file_decision(empty, "c", "A", "c", "r", namespace="DEC")["id"] == "DEC-002"
        assert file_decision(empty, "d", "A", "c", "r", namespace="SC")["id"] == "SC-002"
        assert file_decision(empty, "e", "A", "c", "r", namespace="DQ")["id"] == "DQ-001"
        assert file_decision(empty, "f", "A", "c", "r", namespace="MD")["id"] == "MD-001"

    @pytest.mark.parametrize("namespace", ["dec", "sc", "Dq", "mD"])
    def test_lowercase_namespaces_are_accepted_and_upper_cased(self, empty, today, namespace):
        result = file_decision(empty, "title", "A", "c", "r", namespace=namespace)
        upper = namespace.upper()
        assert result["id"] == f"{upper}-001"
        assert result["file"] == f"docs/decisions/{STAMP}_{upper}001_title.md"

    @pytest.mark.parametrize("namespace", ["XX", "", "DECISION", "DE C", "dec ", "0", "DEC1"])
    def test_unknown_namespaces_are_rejected(self, empty, namespace):
        with pytest.raises(ValueError) as excinfo:
            file_decision(empty, "title", "A", "c", "r", namespace=namespace)
        assert "DEC, DQ, SC, MD" in str(excinfo.value)

    def test_nothing_is_written_when_the_namespace_is_rejected(self, empty):
        with pytest.raises(ValueError):
            file_decision(empty, "title", "A", "c", "r", namespace="XX")
        assert not (empty / "docs" / "decisions").exists()

    def test_a_repeated_title_gets_a_fresh_id_not_an_overwrite(self, empty, today):
        first = file_decision(empty, "Same title", "A", "c", "r")
        second = file_decision(empty, "Same title", "A", "c", "r")
        assert first["file"] != second["file"]
        assert len(list((empty / "docs" / "decisions").glob("*.md"))) == 2


# --- The integration guarantee: filenames the checker accepts ------------------


NASTY_TITLES = [
    "Adopt Postgres",
    "Use PostgreSQL — not MySQL!",
    "  leading and trailing space  ",
    "Ünïcödé Títle",
    "决定采用中文标题",
    "!!! ??? ***",
    "___",
    "",
    "   ",
    "3.14 / 2 = 1.57",
    "path/like/title.md",
    "Title with\nnewline",
    "Title\twith\ttabs",
    "quotes \"and\" 'apostrophes'",
    "a" * 200,
    "Ünïcödé" * 30,
    "back`ticks` and |pipes|",
    "<script>alert(1)</script>",
    "../../escape attempt",
]


class TestGeneratedNamesMatchTheChecker:
    """The critical contract: what ``file_decision`` writes, ``checks`` must accept."""

    @pytest.mark.parametrize("title", NASTY_TITLES, ids=range(len(NASTY_TITLES)))
    @pytest.mark.parametrize("namespace", NAMESPACES)
    def test_filename_matches_decision_name_re(self, empty, today, title, namespace):
        result = file_decision(empty, title, "Owner", "c", "r", namespace=namespace)
        name = Path(result["file"]).name
        assert DECISION_NAME_RE.match(name), name

    @pytest.mark.parametrize("title", NASTY_TITLES, ids=range(len(NASTY_TITLES)))
    def test_the_file_lands_inside_docs_decisions(self, empty, today, title):
        result = file_decision(empty, title, "Owner", "c", "r")
        path = (empty / result["file"]).resolve()
        assert path.parent == (empty / "docs" / "decisions").resolve()
        assert path.is_file()

    @pytest.mark.parametrize("title", ["a" * 200, "Ünïcödé" * 30, "word " * 60])
    def test_long_titles_are_truncated_to_the_slug_limit(self, empty, today, title):
        name = Path(file_decision(empty, title, "Owner", "c", "r")["file"]).name
        slug = name[len(f"{STAMP}_DEC001_") : -len(".md")]
        assert 0 < len(slug) <= 48
        assert not slug.endswith("_")

    @pytest.mark.parametrize("title", ["", "   ", "___", "决定采用中文标题", "!!! ??? ***"])
    def test_titles_with_no_usable_characters_fall_back_to_untitled(self, empty, today, title):
        assert file_decision(empty, title, "Owner", "c", "r")["file"].endswith("_untitled.md")

    def test_a_filed_decision_keeps_the_project_compliant(self, project, today):
        """End to end: file a decision, link it, and the checker still passes clean."""
        result = file_decision(project, "Adopt Postgres", "Orchestrator", "ctx", "ruling")
        charter = project / "PROJECT_CHARTER.md"
        charter.write_text(
            charter.read_text(encoding="utf-8") + f"\n{result['charter_row']}\n",
            encoding="utf-8",
        )
        report = report_for(project)
        assert report.failed == 0, fail_messages(report)
        assert report.warnings == 0, warn_messages(report)

    def test_an_unlinked_decision_is_the_only_thing_the_checker_complains_about(
        self, project, today
    ):
        file_decision(project, "Adopt Postgres", "Orchestrator", "ctx", "ruling")
        report = report_for(project)
        assert [f.check for f in report.findings if f.status == "fail"] == ["decisions_linked"]


# --- Round trip ---------------------------------------------------------------


class TestWrittenFilesParseBack:
    def test_a_filed_decision_reads_back_through_read_state(self, project, today):
        result = file_decision(
            project, "Adopt Postgres", "Orchestrator", "ctx", "ruling", namespace="SC"
        )
        record = read_state(project)["recent_decisions"][0]
        assert record["file"] == result["file"]
        assert record["title"] == "SC-001 — Adopt Postgres"
        assert record["date"] == DASHED
        assert record["authority"] == "Orchestrator"
        assert record["status"] == "Decided"

    def test_a_filed_handoff_reads_back_through_read_state(self, project, today):
        result = file_handoff(project, "Data Engineer", "a loader", "src/etl")
        record = read_state(project)["recent_handoffs"][0]
        assert record["file"] == result["file"]
        assert record["title"] == f"Handoff — Data Engineer — {DASHED}"

    def test_filing_both_leaves_a_readable_state_document(self, empty, today):
        file_decision(empty, "Adopt Postgres", "Orchestrator", "ctx", "ruling")
        file_handoff(empty, "Analyst", "a report", "docs/report.md")
        state = read_state(empty)
        assert len(state["recent_decisions"]) == 1
        assert len(state["recent_handoffs"]) == 1
        assert json.dumps(state)


# --- file_handoff -------------------------------------------------------------


class TestFileHandoff:
    def test_return_contract(self, project, today):
        result = file_handoff(project, "Data Engineer", "a loader", "src/etl")
        assert result == {
            "file": f"docs/handoffs/{DASHED}_data_engineer.md",
            "agent": "Data Engineer",
        }
        assert (project / result["file"]).is_file()

    def test_the_body_records_every_field(self, project, today):
        result = file_handoff(
            project,
            "Data Engineer",
            "  a loader  ",
            "  src/etl  ",
            limitations="no backfill",
            verification="pytest -q",
            next_agent="Analyst",
        )
        body = (project / result["file"]).read_text(encoding="utf-8")
        assert body.startswith(f"# Handoff — Data Engineer — {DASHED}\n")
        assert "## What was produced\n\na loader" in body
        assert "## Where it lives\n\nsrc/etl" in body
        assert "## Known limitations\n\nno backfill" in body
        assert "## How to verify\n\npytest -q" in body
        assert "## Next agent in chain\n\nAnalyst" in body

    @pytest.mark.parametrize("blank", ["", "   "])
    def test_optional_fields_get_documented_defaults(self, project, today, blank):
        result = file_handoff(
            project, "Agent", "p", "l", limitations=blank, verification=blank, next_agent=blank
        )
        body = (project / result["file"]).read_text(encoding="utf-8")
        assert "None recorded." in body
        assert "See the project's verify command in PROJECT_CHARTER.md." in body
        assert "Orchestrator, to route the next dispatch." in body

    def test_directories_are_created_when_missing(self, empty, today):
        result = file_handoff(empty, "Agent", "p", "l")
        assert (empty / "docs" / "handoffs").is_dir()
        assert (empty / result["file"]).is_file()

    @pytest.mark.parametrize(
        "agent, slug",
        [
            ("Data Engineer", "data_engineer"),
            ("QA & Parity Engineer", "qa_parity_engineer"),
            ("agent-007", "agent_007"),
            ("Ünïcödé", "n_c_d"),
            ("", "untitled"),
            ("!!!", "untitled"),
            ("a" * 80, "a" * 48),
        ],
    )
    def test_the_agent_name_is_slugged_into_the_filename(self, empty, today, agent, slug):
        result = file_handoff(empty, agent, "p", "l")
        assert result["file"] == f"docs/handoffs/{DASHED}_{slug}.md"
        assert result["agent"] == agent

    def test_a_second_note_from_the_same_agent_on_the_same_day_is_kept(self, empty, today):
        """Handoffs are an audit trail — a same-day repeat must not destroy the first."""
        first = file_handoff(empty, "Agent", "first produce", "l")
        second = file_handoff(empty, "Agent", "second produce", "l")
        third = file_handoff(empty, "Agent", "third produce", "l")

        assert first["file"] != second["file"] != third["file"]
        assert second["file"].endswith("_2.md")
        assert third["file"].endswith("_3.md")
        assert "first produce" in (empty / first["file"]).read_text(encoding="utf-8")
        assert "second produce" in (empty / second["file"]).read_text(encoding="utf-8")
        assert len(list((empty / "docs" / "handoffs").glob("*.md"))) == 3


# --- Dates --------------------------------------------------------------------


class TestDates:
    def test_the_frozen_fixture_is_what_lands_in_the_names(self, empty, today):
        assert file_decision(empty, "t", "A", "c", "r")["file"].split("/")[-1].startswith(STAMP)
        assert file_handoff(empty, "a", "p", "l")["file"].split("/")[-1].startswith(DASHED)

    def test_unpatched_writers_stamp_the_real_today(self, empty):
        real = _dt.date.today()
        assert file_decision(empty, "t", "A", "c", "r")["id"] == "DEC-001"
        assert (empty / "docs" / "decisions" / f"{real:%Y%m%d}_DEC001_t.md").is_file()
        assert (empty / file_handoff(empty, "a", "p", "l")["file"]).name == f"{real:%Y-%m-%d}_a.md"
