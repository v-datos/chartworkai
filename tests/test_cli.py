"""CLI contract tests plus the differential parity suite against the shell reference.

``scripts/check_framework_compliance.sh`` is the reference implementation. The
parity class runs both checkers over identical fixtures and asserts their exit
codes agree, except for the two divergences documented in ``chartworkai.checks``,
which get their own explicit tests.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import (
    SEED_DECISION,
    SHELL_CHECKER,
    VALID_STATUSES,
    age,
    append,
    charter_text,
    decision_text,
    phase_plan_text,
    remove,
    run_chartworkai_subprocess,
    run_shell_checker,
    status_text,
    status_with_entries,
    status_with_lines,
    write,
)

from chartworkai import __version__
from chartworkai.models import Status

TOP_LEVEL_KEYS = {
    "tool",
    "version",
    "project_root",
    "profile",
    "is_data_profile",
    "framework_repo",
    "summary",
    "findings",
}
SUMMARY_KEYS = {"passed", "failed", "warnings", "ok"}
FINDING_KEYS = {"check", "status", "message", "path", "details"}


# --- JSON contract ------------------------------------------------------------


class TestJsonContract:
    def test_stdout_is_pure_json(self, cli, project):
        result = cli("check", str(project), "--json")
        payload = json.loads(result.out)  # would raise on any extra output
        assert isinstance(payload, dict)
        assert result.out.lstrip().startswith("{")
        assert result.out.rstrip().endswith("}")
        assert result.err == ""

    def test_stdout_is_pure_json_out_of_process(self, project):
        result = run_chartworkai_subprocess(project, "--json")
        assert json.loads(result.out)["summary"]["ok"] is True
        assert result.err == ""

    def test_top_level_keys(self, cli, project):
        payload = json.loads(cli("check", str(project), "--json").out)
        assert set(payload) == TOP_LEVEL_KEYS
        assert payload["tool"] == "chartworkai"
        assert payload["version"] == __version__
        assert payload["project_root"] == str(project.resolve())

    def test_summary_keys_and_types(self, cli, project):
        payload = json.loads(cli("check", str(project), "--json").out)
        summary = payload["summary"]
        assert set(summary) == SUMMARY_KEYS
        assert summary["failed"] == 0
        assert summary["warnings"] == 0
        assert summary["passed"] == len(payload["findings"])
        assert summary["ok"] is True

    def test_finding_keys_and_statuses(self, cli, project):
        # A mix of all three statuses: a missing file (fail) plus a stale mtime
        # (warn). STATUS.md must stay in place or the decay check bails out.
        remove(project, "docs/domain/README.md")
        age(project / "docs/phase_plan.md", days=20)
        payload = json.loads(cli("check", str(project), "--json").out)

        assert payload["findings"]
        for finding in payload["findings"]:
            assert set(finding) == FINDING_KEYS
            assert finding["status"] in VALID_STATUSES
            assert isinstance(finding["message"], str) and finding["message"]
            assert finding["path"] is None or isinstance(finding["path"], str)
            assert isinstance(finding["details"], list)

        statuses = {f["status"] for f in payload["findings"]}
        assert {Status.PASS, Status.FAIL, Status.WARN} <= statuses

    def test_details_carry_the_offending_lines(self, cli, project):
        write(project, "docs/domain/README.md", "# Domain\n\nOwner: {{OWNER}}\n")
        payload = json.loads(cli("check", str(project), "--json").out)

        placeholders = [f for f in payload["findings"] if f["check"] == "placeholders"]
        assert placeholders[0]["status"] == Status.FAIL
        expected = "docs/domain/README.md:3:Owner: {{OWNER}}"
        assert placeholders[0]["details"] == [expected]

    @pytest.mark.parametrize(
        "profile, is_data", [("data-science", True), ("software-app", False), (None, True)]
    )
    def test_profile_fields(self, cli, make, profile, is_data):
        project = make(profile=profile)
        payload = json.loads(cli("check", str(project), "--json").out)
        assert payload["profile"] == profile
        assert payload["is_data_profile"] is is_data
        assert payload["framework_repo"] is False

    def test_framework_repo_flag(self, cli, make):
        project = make(framework_repo=True)
        payload = json.loads(cli("check", str(project), "--json").out)
        assert payload["framework_repo"] is True

    def test_summary_ok_is_false_when_failing(self, cli, project):
        remove(project, "TASKS.md")
        payload = json.loads(cli("check", str(project), "--json").out)
        assert payload["summary"]["ok"] is False
        assert payload["summary"]["failed"] >= 1

    def test_strict_flips_ok_for_warnings_only(self, cli, project):
        age(project / "STATUS.md", days=20)

        lenient = json.loads(cli("check", str(project), "--json").out)
        strict = json.loads(cli("check", str(project), "--json", "--strict").out)

        assert lenient["summary"]["warnings"] == 1
        assert lenient["summary"]["failed"] == 0
        assert lenient["summary"]["ok"] is True
        assert strict["summary"]["ok"] is False


# --- Exit codes ---------------------------------------------------------------


class TestExitCodes:
    def test_zero_when_compliant(self, cli, project):
        assert cli("check", str(project)).code == 0

    @pytest.mark.parametrize("rel", ["PROJECT_CHARTER.md", "AGENTS.md", "docs/decisions"])
    def test_one_when_anything_fails(self, cli, project, rel):
        remove(project, rel)
        assert cli("check", str(project)).code == 1

    def test_two_without_a_subcommand(self, cli):
        result = cli()
        assert result.code == 2
        assert "usage:" in result.out

    def test_two_without_a_subcommand_out_of_process(self):
        proc = subprocess.run([sys.executable, "-m", "chartworkai"], capture_output=True, text=True)
        assert proc.returncode == 2

    def test_strict_turns_a_warning_into_exit_one(self, cli, project):
        age(project / "STATUS.md", days=20)
        assert cli("check", str(project)).code == 0
        assert cli("check", str(project), "--strict").code == 1

    def test_strict_leaves_a_clean_project_at_zero(self, cli, project):
        assert cli("check", str(project), "--strict").code == 0

    def test_json_and_text_modes_agree_on_the_exit_code(self, cli, project):
        remove(project, "STATUS.md")
        assert cli("check", str(project)).code == cli("check", str(project), "--json").code == 1

    def test_in_process_and_subprocess_agree(self, cli, project):
        remove(project, "TASKS.md")
        assert cli("check", str(project)).code == run_chartworkai_subprocess(project).code == 1


# --- Text rendering -----------------------------------------------------------


class TestTextOutput:
    def test_header_names_the_tool_profile_and_root(self, cli, project):
        out = cli("check", str(project)).out
        assert f"ChartworkAI {__version__}" in out
        assert str(project.resolve()) in out
        assert "Profile: data-science  (project)" in out

    def test_default_profile_label_when_absent(self, cli, make):
        project = make(profile=None)
        assert "Profile: data-science (default)" in cli("check", str(project)).out

    def test_framework_repo_scope_label(self, cli, make):
        project = make(framework_repo=True)
        assert "(framework repo)" in cli("check", str(project)).out

    def test_summary_and_verdict_lines(self, cli, project):
        out = cli("check", str(project)).out
        assert "0 failed, 0 warning(s)." in out
        assert "ChartworkAI check passed." in out

    def test_failure_verdict_reports_the_count(self, cli, project):
        remove(project, "STATUS.md")
        out = cli("check", str(project)).out
        assert "ChartworkAI check failed with" in out

    def test_strict_verdict_mentions_warnings(self, cli, project):
        age(project / "STATUS.md", days=20)
        out = cli("check", str(project), "--strict").out
        assert "1 warning(s) under --strict" in out

    def test_quiet_suppresses_pass_lines(self, cli, project):
        verbose = cli("check", str(project)).out
        quiet = cli("check", str(project), "--quiet").out
        assert "PASS " in verbose
        assert "PASS " not in quiet
        assert "ChartworkAI check passed." in quiet

    def test_quiet_keeps_failures_and_warnings(self, cli, project):
        remove(project, "docs/domain/README.md")
        age(project / "docs/phase_plan.md", days=20)
        out = cli("check", str(project), "--quiet").out
        assert "FAIL docs/domain/README.md is missing" in out
        assert "WARN " in out
        assert "PASS " not in out

    def test_failure_details_are_indented_under_the_finding(self, cli, project):
        write(project, "docs/domain/README.md", "# Domain\n\nOwner: {{OWNER}}\n")
        out = cli("check", str(project), "--quiet").out
        assert "FAIL unresolved {{PLACEHOLDER}} tokens remain" in out
        assert "     " + "docs/domain/README.md:3:Owner: {{OWNER}}" in out

    def test_path_defaults_to_the_current_directory(self, cli, project, monkeypatch):
        monkeypatch.chdir(project)
        result = cli("check")
        assert result.code == 0
        assert str(project.resolve()) in result.out


# --- Differential parity against the shell reference --------------------------


def _noop(project: Path) -> None:
    pass


def _remove_status(project: Path) -> None:
    remove(project, "STATUS.md")


def _remove_charter(project: Path) -> None:
    remove(project, "PROJECT_CHARTER.md")


def _remove_phase_plan(project: Path) -> None:
    remove(project, "docs/phase_plan.md")


def _remove_decisions_dir(project: Path) -> None:
    remove(project, "docs/decisions")


def _remove_domain_readme(project: Path) -> None:
    remove(project, "docs/domain/README.md")


def _empty_handoffs(project: Path) -> None:
    remove(project, "docs/handoffs/README.md")


def _handoff_note_only(project: Path) -> None:
    remove(project, "docs/handoffs/README.md")
    write(project, "docs/handoffs/2026-01-01_session.md", "# Handoff\n\nPhase 1 picked up.\n")


def _remove_seed_decision(project: Path) -> None:
    remove(project, f"docs/decisions/{SEED_DECISION}")


def _data_profile_without_triad(project: Path) -> None:
    remove(project, "docs/data")


def _non_data_profile_without_triad(project: Path) -> None:
    write(project, "PROJECT_CHARTER.md", charter_text(profile="software-app"))
    remove(project, "docs/data")


def _substring_profile_without_triad(project: Path) -> None:
    # REGRESSION: "non-data-science" contains "data-science" but is not that profile.
    # It is not a known profile either, so both implementations must reject it and
    # read it the strictest way — a typo must not become a way to drop the triad.
    write(project, "PROJECT_CHARTER.md", charter_text(profile="non-data-science"))
    remove(project, "docs/data")


def _duplicate_h2(project: Path) -> None:
    append(project, "AGENTS.md", "\n## Operating Rules\n\nRepeated section.\n")


def _placeholder_in_docs(project: Path) -> None:
    write(project, "docs/domain/README.md", "# Domain\n\nOwner: {{OWNER}}\n")


def _placeholder_in_pruned_dir(project: Path) -> None:
    write(project, "outputs/report.md", "Owner: {{OWNER}}\n")
    write(project, "data/raw/schema.md", "Owner: {{OWNER}}\n")


def _tasks_two_in_progress(project: Path) -> None:
    write(
        project,
        "TASKS.md",
        "# Tasks\n\n## In Progress\n\n- [ ] one\n\n## In Progress\n\n- [ ] two\n",
    )


def _tasks_table(project: Path) -> None:
    append(project, "TASKS.md", "\n| Task | Owner |\n|---|---|\n")


def _tasks_without_checkboxes(project: Path) -> None:
    write(project, "TASKS.md", "# Tasks\n\n## In Progress\n\n- draft the dictionary\n")


def _phase_mismatch(project: Path) -> None:
    write(project, "docs/phase_plan.md", phase_plan_text(current_phase=9))


def _phase_unparseable(project: Path) -> None:
    write(project, "docs/phase_plan.md", "# Phase Plan\n\n**Last updated:** 2026-01-02\n")


def _unlinked_decision(project: Path) -> None:
    name = "20260102_DEC002_unlinked.md"
    write(project, f"docs/decisions/{name}", decision_text(name))


def _bad_decision_name(project: Path) -> None:
    write(project, "docs/decisions/scratch_notes.md", "# Notes\n")


def _stale_plan_date(project: Path) -> None:
    write(project, "docs/phase_plan.md", phase_plan_text(last_updated="2025-12-31"))


def _bloated_status(project: Path) -> None:
    write(project, "STATUS.md", status_with_lines(151))


def _many_status_entries(project: Path) -> None:
    write(project, "STATUS.md", status_with_entries(6))


def _stale_mtimes(project: Path) -> None:
    age(project / "STATUS.md", days=20)
    age(project / "docs/phase_plan.md", days=20)


def _leftover_scaffold(project: Path) -> None:
    (project / "_framework_agents").mkdir()


def _absolute_paths(project: Path) -> None:
    # REGRESSION: none of these may be read as tool-specific slash commands.
    append(
        project,
        "AGENTS.md",
        "\n- Deployed to /etc/app by the release job.\n"
        "- Logs rotate into /var/log/output nightly.\n"
        "- Wheels live in /usr/local/share/wheels.\n"
        "- Overrides load from /config/app.yaml at boot.\n"
        "- Health is served at /status/live.\n",
    )


def _slash_command(project: Path) -> None:
    append(project, "AGENTS.md", "\n- Start every session with /read to load the charter.\n")


def _assistant_name(project: Path) -> None:
    append(project, "STATUS.md", "\n- Paired with Claude Code on the pipeline.\n")


def _framework_repo_product_surface(project: Path) -> None:
    write(project, "framework.json", '{\n  "name": "chartworkai"\n}\n')
    write(project, "templates/PROJECT_CHARTER.md", "# Charter\n\nOwner: {{OWNER}}\n")
    write(project, "agents/orchestrator.md", "Owner: {{OWNER}}\n")


def _framework_repo_assistant_names(project: Path) -> None:
    _framework_repo_product_surface(project)
    append(project, "AGENTS.md", "\n- Verified with Claude Code, Cursor, and Qwen.\n")


#: ``id -> (mutation, expected exit code for BOTH implementations)``
PARITY_CASES = {
    "compliant": (_noop, 0),
    "missing_charter": (_remove_charter, 1),
    "missing_status": (_remove_status, 1),
    "missing_phase_plan": (_remove_phase_plan, 1),
    "missing_decisions_dir": (_remove_decisions_dir, 1),
    "missing_domain_readme": (_remove_domain_readme, 1),
    "empty_handoffs_dir": (_empty_handoffs, 1),
    "handoff_note_without_readme": (_handoff_note_only, 0),
    "no_seed_decision": (_remove_seed_decision, 1),
    "data_profile_without_triad": (_data_profile_without_triad, 1),
    "non_data_profile_without_triad": (_non_data_profile_without_triad, 0),
    "substring_profile_without_triad": (_substring_profile_without_triad, 1),
    "duplicate_h2": (_duplicate_h2, 1),
    "placeholder_in_docs": (_placeholder_in_docs, 1),
    "placeholder_in_pruned_dir": (_placeholder_in_pruned_dir, 0),
    "tasks_two_in_progress": (_tasks_two_in_progress, 1),
    "tasks_table_rows": (_tasks_table, 1),
    "tasks_without_checkboxes": (_tasks_without_checkboxes, 1),
    "phase_mismatch": (_phase_mismatch, 1),
    "phase_unparseable": (_phase_unparseable, 1),
    "unlinked_decision": (_unlinked_decision, 1),
    "bad_decision_name": (_bad_decision_name, 1),
    "stale_plan_date": (_stale_plan_date, 1),
    "bloated_status": (_bloated_status, 1),
    "many_status_entries": (_many_status_entries, 0),
    "stale_mtimes": (_stale_mtimes, 0),
    "leftover_scaffold": (_leftover_scaffold, 1),
    "absolute_paths_in_core_docs": (_absolute_paths, 0),
    "slash_command_in_core_doc": (_slash_command, 1),
    "assistant_name_in_core_doc": (_assistant_name, 1),
    "framework_repo_product_surface": (_framework_repo_product_surface, 0),
    "framework_repo_assistant_names": (_framework_repo_assistant_names, 0),
}


class TestShellParity:
    def test_the_reference_implementation_is_present(self):
        assert SHELL_CHECKER.is_file()

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason=(
            "Shell/Python parity is a POSIX guarantee: the reference checker is a "
            "POSIX sh script whose path handling and line endings differ on Windows, "
            "so a mismatch there reflects the shell, not a divergence in the product. "
            "Windows users drive the Python CLI."
        ),
    )
    @pytest.mark.parametrize(
        "mutate, expected",
        list(PARITY_CASES.values()),
        ids=list(PARITY_CASES),
    )
    def test_exit_codes_agree_with_the_shell_reference(self, make, mutate, expected):
        project = make()
        mutate(project)

        shell = run_shell_checker(project)
        python = run_chartworkai_subprocess(project)

        # `set -eu` means a broken shell run can exit 1 without reaching its
        # verdict; require the verdict so agreement is never accidental.
        verdict = "passed." if expected == 0 else "failed with"
        assert shell.err == "", shell.err
        assert f"Framework installation check {verdict}" in shell.out, shell.out

        assert shell.code == expected, f"shell reference changed behaviour:\n{shell.out}"
        assert python.code == expected, f"python checker diverged:\n{python.out}"

    def test_divergence_1_python_prunes_every_framework_scaffold(self, make):
        """DIVERGENCE-1: the shell prunes 3 scaffold dirs, Python prunes them all.

        The shell therefore reports one root cause (a leftover scaffold) twice.
        Exit codes still agree because the scaffold itself fails either way.
        """
        project = make()
        write(project, "_framework_extensions/claims_gate.md", "Owner: {{OWNER}}\n")

        shell = run_shell_checker(project)
        python = run_chartworkai_subprocess(project, "--json")
        payload = json.loads(python.out)
        placeholders = [f for f in payload["findings"] if f["check"] == "placeholders"]

        assert placeholders[0]["status"] == Status.PASS  # new, narrower behaviour
        assert "unresolved {{PLACEHOLDER}} tokens remain" in shell.out  # shell double-reports
        assert [f["check"] for f in payload["findings"] if f["status"] == Status.FAIL] == [
            "leftover_scaffold"
        ]
        assert shell.code == 1 and python.code == 1

    def test_divergence_2_python_reads_status_dates_without_an_em_dash(self, make):
        """DIVERGENCE-2: the shell only parses ``## YYYY-MM-DD —`` headings.

        This is the one fixture where the exit codes legitimately differ: the
        shell silently skips the staleness check, Python catches the stale plan.
        """
        project = make()
        write(project, "STATUS.md", status_text(date="2026-06-01", em_dash=False))
        write(project, "docs/phase_plan.md", phase_plan_text(last_updated="2026-01-02"))

        shell = run_shell_checker(project)
        python = run_chartworkai_subprocess(project)

        assert shell.code == 0, f"shell unexpectedly parsed the date:\n{shell.out}"
        assert python.code == 1
        assert "is stale" in python.out

    def test_divergence_2_control_case_with_an_em_dash_agrees(self, make):
        project = make()
        write(project, "STATUS.md", status_text(date="2026-06-01", em_dash=True))
        write(project, "docs/phase_plan.md", phase_plan_text(last_updated="2026-01-02"))

        shell = run_shell_checker(project)
        python = run_chartworkai_subprocess(project)

        assert shell.code == 1
        assert python.code == 1
