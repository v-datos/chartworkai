"""Behavioural tests for every check in :mod:`chartworkai.checks`.

Each test starts from the fully compliant fixture built by ``make_project`` and
mutates exactly one thing, so a failure names the broken check directly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import (
    DATA_TRIAD,
    REQUIRED_FILES,
    SEED_DECISION,
    STATUS_DATE,
    VALID_STATUSES,
    age,
    append,
    charter_text,
    decision_text,
    fail_messages,
    findings,
    has_fail,
    only,
    paths_failed,
    phase_plan_text,
    remove,
    report_for,
    status_with_entries,
    status_with_lines,
    statuses,
    warn_messages,
    write,
)

from chartworkai.checks import DATA_PROFILES, detect_framework_repo, detect_profile
from chartworkai.models import Status

DUPLICATE_H2_TARGETS = (
    "PROJECT_CHARTER.md",
    "AGENTS.md",
    "docs/phase_plan.md",
    "STATUS.md",
    "TASKS.md",
    "docs/data/data_dictionary.md",
    "docs/data/lineage.md",
    "docs/data/watchlist.md",
)


def duplicate_last_h2(project: Path, rel: str) -> str:
    """Append a copy of the file's last ``## `` heading and return it."""
    path = project / rel
    text = path.read_text(encoding="utf-8")
    heading = [line for line in text.splitlines() if line.startswith("## ")][-1]
    path.write_text(text + f"\n{heading}\n\nRepeated section.\n", encoding="utf-8")
    return heading


# --- Baseline ----------------------------------------------------------------


class TestBaseline:
    def test_minimal_project_is_fully_compliant(self, project):
        report = report_for(project)
        assert report.failed == 0, fail_messages(report)
        assert report.warnings == 0, warn_messages(report)
        assert report.passed > 0
        assert report.ok(strict=True)
        assert report.exit_code(strict=True) == 0

    def test_every_finding_uses_a_valid_status(self, project):
        remove(project, "STATUS.md")  # force a mix of pass/fail into the report
        write(project, "docs/domain/README.md", "# Domain\n\n{{TOKEN}}\n")
        report = report_for(project)
        assert {f.status for f in report.findings} <= VALID_STATUSES
        assert report.failed > 0

    def test_report_metadata_is_populated(self, project):
        report = report_for(project)
        assert report.tool == "chartworkai"
        assert report.version
        assert report.project_root == str(project.resolve())


# --- 1. Profile detection ----------------------------------------------------


class TestProfileDetection:
    @pytest.mark.parametrize("profile", sorted(DATA_PROFILES))
    def test_data_profiles_require_the_triad(self, make, profile):
        project = make(profile=profile, with_data_triad=False)
        report = report_for(project)

        assert report.profile == profile
        assert report.is_data_profile is True
        missing = paths_failed(report, "required_file")
        assert set(DATA_TRIAD) <= set(missing)

    @pytest.mark.parametrize("profile", ["software-app", "investigation", "deployed-service"])
    def test_non_data_profiles_skip_the_triad(self, make, profile):
        project = make(profile=profile, with_data_triad=False)
        report = report_for(project)

        assert report.profile == profile
        assert report.is_data_profile is False
        assert report.failed == 0, fail_messages(report)
        contracts = only(report, "data_contracts")
        assert contracts.status == Status.PASS
        assert "skipped" in contracts.message
        assert not any(p in DATA_TRIAD for p in paths_failed(report, "required_file"))

    def test_missing_profile_line_defaults_to_data_profile(self, make):
        project = make(profile=None, with_data_triad=False)
        report = report_for(project)

        assert report.profile is None
        assert report.is_data_profile is True
        assert set(DATA_TRIAD) <= set(paths_failed(report, "required_file"))

    def test_missing_charter_defaults_to_data_profile(self, project):
        remove(project, "PROJECT_CHARTER.md")
        assert detect_profile(project) == (None, True)
        assert report_for(project).is_data_profile is True

    def test_unparseable_profile_value_defaults_to_data_profile(self, project):
        # "Profile:" present but no [A-Za-z0-9_-] token follows it.
        write(project, "PROJECT_CHARTER.md", "# Charter\n\n**Profile:** !!!\n")
        profile, is_data = detect_profile(project)
        assert profile is None
        assert is_data is True

    @pytest.mark.parametrize(
        "profile",
        [
            "non-data-science",
            "not-data-science",
            "data-sciences",
            "predata-science",
            "database-migration",
            "competition-ml-lite",
        ],
    )
    def test_a_profile_resembling_a_known_one_is_rejected_not_silently_accepted(
        self, make, profile
    ):
        """REGRESSION (two of them, pulling in opposite directions).

        Substring matching must never promote a profile to data — ``non-data-science``
        is not ``data-science``. But an unrecognised value must not be silently
        treated as *non-data* either: that turned a typo into a way to drop the
        data-contract requirement. So an unknown profile fails the check and is read
        the strictest way until it is fixed.
        """
        project = make(profile=profile, with_data_triad=False)
        report = report_for(project)

        assert report.profile == profile
        assert report.is_data_profile is True, "an unknown profile must read as strict"
        assert "profile" in {f.check for f in report.of_status(Status.FAIL)}
        # And the strict reading must actually bite: the triad is now demanded.
        assert set(DATA_TRIAD) <= set(paths_failed(report, "required_file"))

    @pytest.mark.parametrize("profile", sorted(DATA_PROFILES))
    def test_a_known_data_profile_passes_the_profile_check(self, make, profile):
        report = report_for(make(profile=profile))
        assert "profile" not in {f.check for f in report.of_status(Status.FAIL)}

    def test_profile_is_read_through_bold_markdown_decoration(self, project):
        write(project, "PROJECT_CHARTER.md", charter_text(profile="database"))
        assert detect_profile(project) == ("database", True)


# --- 2. Framework-repo detection ---------------------------------------------


class TestFrameworkRepoDetection:
    #: A manifest that actually names this framework and carries the keys it ships.
    VALID_MANIFEST = json.dumps(
        {
            "name": "chartworkai",
            "version": "0.1.0",
            "profiles": {},
            "required_files": [],
            "required_directories": [],
        }
    )

    @pytest.mark.parametrize(
        "manifest, template, expected",
        [
            (VALID_MANIFEST, "templates/x.template.md", True),
            (VALID_MANIFEST, None, False),
            (None, "templates/x.template.md", False),
            (None, None, False),
            # Detection *relaxes* checks, so the markers have to prove themselves:
            # a bare pair of markers used to be enough for any consumer project to
            # silence its own leftover-scaffold and placeholder failures.
            ("{}", "templates/x.template.md", False),
            ('{"name": "chartworkai"}', "templates/x.template.md", False),
            (VALID_MANIFEST, "templates/charter.md", False),
            ("not json", "templates/x.template.md", False),
            (VALID_MANIFEST.replace("chartworkai", "other"), "templates/x.template.md", False),
        ],
    )
    def test_detection_requires_a_validated_manifest(self, project, manifest, template, expected):
        if manifest is not None:
            write(project, "framework.json", manifest + "\n")
        if template is not None:
            write(project, template, "# Template\n")

        assert detect_framework_repo(project) is expected
        assert report_for(project).framework_repo is expected

    @pytest.mark.parametrize(
        "rel", ["templates/charter.md", "agents/orchestrator.md", "prompts/kickoff.md"]
    )
    def test_framework_repo_narrows_the_placeholder_scan(self, make, rel):
        framework = make(framework_repo=True)
        write(framework, rel, "# Product surface\n\nOwner: {{OWNER}}\n")
        assert only(report_for(framework), "placeholders").status == Status.PASS

        consumer = make(framework_repo=False)
        write(consumer, rel, "# Product surface\n\nOwner: {{OWNER}}\n")
        assert only(report_for(consumer), "placeholders").status == Status.FAIL

    @pytest.mark.parametrize("rel", ["STATUS.md", "TASKS.md", "docs/domain/README.md"])
    def test_framework_repo_still_scans_core_docs_and_docs_tree(self, make, rel):
        framework = make(framework_repo=True)
        append(framework, rel, "\nOwner: {{OWNER}}\n")
        assert only(report_for(framework), "placeholders").status == Status.FAIL

    def test_framework_repo_disables_the_assistant_name_check(self, make):
        framework = make(framework_repo=True)
        append(framework, "AGENTS.md", "\nWorks with Claude Code and Cursor alike.\n")
        assert only(report_for(framework), "tool_leak").status == Status.PASS

        consumer = make(framework_repo=False)
        append(consumer, "AGENTS.md", "\nWorks with Claude Code and Cursor alike.\n")
        assert has_fail(report_for(consumer), "tool_leak", "Assistant name leak")

    def test_framework_repo_skips_the_leftover_scaffold_check(self, make):
        framework = make(framework_repo=True)
        (framework / "_framework_templates").mkdir()
        assert findings(report_for(framework), "leftover_scaffold") == []

        consumer = make(framework_repo=False)
        (consumer / "_framework_templates").mkdir()
        assert has_fail(report_for(consumer), "leftover_scaffold")


# --- 3. Required files -------------------------------------------------------


class TestRequiredFiles:
    def test_all_required_files_pass_on_the_baseline(self, project):
        report = report_for(project)
        passing = {f.path for f in findings(report, "required_file", Status.PASS)}
        assert set(REQUIRED_FILES) <= passing

    @pytest.mark.parametrize("rel", REQUIRED_FILES)
    def test_each_missing_required_file_fails(self, project, rel):
        remove(project, rel)
        report = report_for(project)

        matching = [f for f in findings(report, "required_file", Status.FAIL) if f.path == rel]
        assert len(matching) == 1
        assert matching[0].message == f"{rel} is missing"

    def test_a_directory_does_not_satisfy_a_required_file(self, project):
        remove(project, "STATUS.md")
        (project / "STATUS.md").mkdir()
        assert "STATUS.md" in paths_failed(report_for(project), "required_file")


# --- 4. Decisions ------------------------------------------------------------


class TestDecisions:
    def test_baseline_passes(self, project):
        report = report_for(project)
        assert only(report, "seed_decision").status == Status.PASS
        assert "docs/decisions" not in paths_failed(report, "required_dir")

    def test_missing_decisions_dir_fails(self, project):
        remove(project, "docs/decisions")
        report = report_for(project)
        assert "docs/decisions" in paths_failed(report, "required_dir")
        assert "docs/decisions/README.md" in paths_failed(report, "required_file")
        assert only(report, "seed_decision").status == Status.FAIL

    def test_missing_decisions_readme_fails(self, project):
        remove(project, "docs/decisions/README.md")
        report = report_for(project)
        assert "docs/decisions/README.md" in paths_failed(report, "required_file")
        assert "docs/decisions" not in paths_failed(report, "required_dir")

    def test_readme_alone_is_not_a_seed_decision(self, project):
        remove(project, f"docs/decisions/{SEED_DECISION}")
        report = report_for(project)
        seed = only(report, "seed_decision")
        assert seed.status == Status.FAIL
        assert "at least one seed decision" in seed.message

    def test_a_non_readme_decision_satisfies_the_seed_requirement(self, make):
        project = make(decisions=("20260101_DQ002_data_quality.md",))
        assert only(report_for(project), "seed_decision").status == Status.PASS


# --- 5. Handoffs -------------------------------------------------------------


class TestHandoffs:
    def test_readme_satisfies_the_handoff_requirement(self, project):
        report = report_for(project)
        assert only(report, "handoff_present").status == Status.PASS
        assert "docs/handoffs" not in paths_failed(report, "required_dir")

    def test_a_note_without_a_readme_also_satisfies_it(self, project):
        remove(project, "docs/handoffs/README.md")
        write(project, "docs/handoffs/2026-01-01_session.md", "# Handoff\n\nPicked up phase 1.\n")
        assert only(report_for(project), "handoff_present").status == Status.PASS

    def test_empty_handoffs_dir_fails(self, project):
        remove(project, "docs/handoffs/README.md")
        report = report_for(project)
        assert only(report, "handoff_present").status == Status.FAIL
        assert "docs/handoffs" not in paths_failed(report, "required_dir")

    def test_missing_handoffs_dir_fails_both_findings(self, project):
        remove(project, "docs/handoffs")
        report = report_for(project)
        assert "docs/handoffs" in paths_failed(report, "required_dir")
        assert only(report, "handoff_present").status == Status.FAIL


# --- 6. Domain ---------------------------------------------------------------


class TestDomain:
    def test_baseline_passes(self, project):
        report = report_for(project)
        assert "docs/domain" not in paths_failed(report, "required_dir")
        assert "docs/domain/README.md" not in paths_failed(report, "required_file")

    def test_missing_domain_dir_fails(self, project):
        remove(project, "docs/domain")
        report = report_for(project)
        assert "docs/domain" in paths_failed(report, "required_dir")
        assert "docs/domain/README.md" in paths_failed(report, "required_file")

    def test_missing_domain_readme_fails(self, project):
        remove(project, "docs/domain/README.md")
        report = report_for(project)
        assert "docs/domain/README.md" in paths_failed(report, "required_file")
        assert "docs/domain" not in paths_failed(report, "required_dir")


# --- 7. Data contracts -------------------------------------------------------


class TestDataContracts:
    @pytest.mark.parametrize("rel", DATA_TRIAD)
    def test_each_missing_contract_fails_for_a_data_profile(self, project, rel):
        remove(project, rel)
        report = report_for(project)
        assert rel in paths_failed(report, "required_file")

    @pytest.mark.parametrize("rel", DATA_TRIAD)
    def test_missing_contracts_are_ignored_for_a_non_data_profile(self, make, rel):
        project = make(profile="software-app")
        remove(project, rel)
        report = report_for(project)
        assert report.failed == 0, fail_messages(report)


# --- 8. Duplicate H2 ---------------------------------------------------------


class TestDuplicateH2:
    def test_unique_headings_pass_for_every_target(self, project):
        report = report_for(project)
        checked = {f.path for f in findings(report, "duplicate_h2")}
        assert checked == set(DUPLICATE_H2_TARGETS)
        assert set(statuses(report, "duplicate_h2")) == {Status.PASS}

    @pytest.mark.parametrize("rel", DUPLICATE_H2_TARGETS)
    def test_repeated_heading_fails_and_is_listed(self, project, rel):
        heading = duplicate_last_h2(project, rel)
        report = report_for(project)

        matching = [f for f in findings(report, "duplicate_h2", Status.FAIL) if f.path == rel]
        assert len(matching) == 1
        assert matching[0].message == f"{rel} has duplicate H2 headings"
        assert matching[0].details == [heading]

    def test_missing_targets_are_not_reported(self, make):
        project = make(profile="software-app", with_data_triad=False)
        checked = {f.path for f in findings(report_for(project), "duplicate_h2")}
        assert checked == set(DUPLICATE_H2_TARGETS) - set(DATA_TRIAD)

    def test_h1_and_h3_repeats_are_not_duplicate_h2(self, project):
        append(project, "AGENTS.md", "\n# Agents\n\n### Notes\n\n### Notes\n")
        report = report_for(project)
        matching = [f for f in findings(report, "duplicate_h2") if f.path == "AGENTS.md"]
        assert matching[0].status == Status.PASS


# --- 9. Placeholders ---------------------------------------------------------


class TestPlaceholders:
    def test_baseline_has_no_placeholders(self, project):
        assert only(report_for(project), "placeholders").status == Status.PASS

    def test_token_in_an_active_doc_fails_with_path_line_content(self, project):
        write(project, "docs/domain/README.md", "# Domain\n\nOwner: {{OWNER}}\n")
        finding = only(report_for(project), "placeholders")

        assert finding.status == Status.FAIL
        assert finding.message == "unresolved {{PLACEHOLDER}} tokens remain"
        expected = "docs/domain/README.md:3:Owner: {{OWNER}}"
        assert finding.details == [expected]

    @pytest.mark.parametrize("rel", ["config.json", "settings.yaml", "settings.yml", "notes.md"])
    def test_every_scanned_suffix_is_covered(self, project, rel):
        write(project, rel, "value: {{TOKEN}}\n")
        assert only(report_for(project), "placeholders").status == Status.FAIL

    @pytest.mark.parametrize("rel", ["notes.txt", "script.py", "Makefile"])
    def test_unscanned_suffixes_are_ignored(self, project, rel):
        write(project, rel, "value: {{TOKEN}}\n")
        assert only(report_for(project), "placeholders").status == Status.PASS

    @pytest.mark.parametrize(
        "rel",
        [
            ".git/description.md",
            ".github/ISSUE_TEMPLATE.md",
            ".venv/share/doc.md",
            "venv/share/doc.md",
            "node_modules/pkg/package.json",
            "outputs/report.md",
            "data/raw/schema.md",
            "data/staging/schema.md",
            "data/processed/schema.md",
        ],
    )
    def test_pruned_directories_are_not_scanned(self, project, rel):
        write(project, rel, "Owner: {{OWNER}}\n")
        assert only(report_for(project), "placeholders").status == Status.PASS

    @pytest.mark.parametrize(
        "rel",
        [
            "_framework_templates/charter.md",
            "_framework_agents/agent.md",
            "_framework_prompts/prompt.md",
            "_framework_extensions/claims_gate.md",
            "_framework_anything_at_all/notes.md",
        ],
    )
    def test_every_framework_scaffold_dir_is_pruned(self, project, rel):
        """DIVERGENCE-1: the shell prunes only three scaffold dirs; Python prunes all."""
        write(project, rel, "Owner: {{OWNER}}\n")
        report = report_for(project)
        assert only(report, "placeholders").status == Status.PASS
        # The scaffold itself is still reported once, by the check that owns it.
        assert has_fail(report, "leftover_scaffold")

    def test_data_dir_prune_is_anchored_at_the_project_root(self, project):
        """``data/raw`` is pruned; a same-named path elsewhere is still scanned."""
        write(project, "docs/data/raw_notes.md", "Owner: {{OWNER}}\n")
        assert only(report_for(project), "placeholders").status == Status.FAIL

    def test_single_brace_tokens_are_not_placeholders(self, project):
        write(project, "docs/domain/README.md", "# Domain\n\nUse {OWNER} and {{}} sparingly.\n")
        assert only(report_for(project), "placeholders").status == Status.PASS

    def test_all_offending_lines_are_listed(self, project):
        write(project, "docs/domain/README.md", "{{A}}\nplain\n{{B}}\n")
        finding = only(report_for(project), "placeholders")
        assert len(finding.details) == 2
        assert finding.details[0].endswith(":1:{{A}}")
        assert finding.details[1].endswith(":3:{{B}}")


# --- 10. TASKS shape ---------------------------------------------------------


class TestTasksShape:
    def test_baseline_passes_all_three_rules(self, project):
        report = report_for(project)
        assert statuses(report, "tasks_shape") == [Status.PASS] * 3

    @pytest.mark.parametrize("count", [0, 2, 3])
    def test_wrong_number_of_in_progress_sections_fails(self, project, count):
        body = "# Tasks\n\n"
        for index in range(count):
            body += f"## In Progress\n\n- [ ] task {index}\n\n"
        if count == 0:
            body += "## Backlog\n\n- [ ] task\n"
        write(project, "TASKS.md", body)

        report = report_for(project)
        assert has_fail(report, "tasks_shape", f"exactly one In Progress section; found {count}")

    def test_exactly_one_in_progress_section_passes(self, project):
        report = report_for(project)
        assert any(
            f.status == Status.PASS and "exactly one In Progress" in f.message
            for f in findings(report, "tasks_shape")
        )

    @pytest.mark.parametrize("row", ["| Task | Owner |", "  | Task | Owner |", "|---|---|"])
    def test_markdown_table_rows_fail(self, project, row):
        append(project, "TASKS.md", f"\n{row}\n")
        assert has_fail(report_for(project), "tasks_shape", "Markdown table rows")

    def test_missing_checkbox_bullets_fails(self, project):
        write(project, "TASKS.md", "# Tasks\n\n## In Progress\n\n- draft the dictionary\n")
        assert has_fail(report_for(project), "tasks_shape", "must contain checkbox bullets")

    @pytest.mark.parametrize("bullet", ["- [ ] todo", "- [x] done", "- [X] done", "  - [ ] nested"])
    def test_checkbox_variants_are_accepted(self, project, bullet):
        write(project, "TASKS.md", f"# Tasks\n\n## In Progress\n\n{bullet}\n")
        assert not has_fail(report_for(project), "tasks_shape", "checkbox bullets")

    def test_check_is_skipped_when_tasks_file_is_missing(self, project):
        remove(project, "TASKS.md")
        assert findings(report_for(project), "tasks_shape") == []


# --- 11. Phase <-> charter sync ----------------------------------------------


class TestPhaseCharterSync:
    def test_matching_phase_passes(self, project):
        assert only(report_for(project), "phase_sync").status == Status.PASS

    def test_phase_absent_from_charter_fails(self, project):
        write(project, "docs/phase_plan.md", phase_plan_text(current_phase=4))
        finding = only(report_for(project), "phase_sync")
        assert finding.status == Status.FAIL
        assert "Phase 4 is not found in PROJECT_CHARTER.md" in finding.message

    def test_phase_number_must_not_match_a_longer_number(self, make):
        project = make()
        write(project, "PROJECT_CHARTER.md", charter_text(phases=(12,)))
        write(project, "docs/phase_plan.md", phase_plan_text(current_phase=1))
        assert only(report_for(project), "phase_sync").status == Status.FAIL

    @pytest.mark.parametrize(
        "body",
        [
            "# Phase Plan\n\n**Last updated:** 2026-01-02\n\n## Milestones\n\n- work\n",
            "# Phase Plan\n\n**Current phase:** discovery\n",
        ],
    )
    def test_unparseable_current_phase_fails(self, project, body):
        write(project, "docs/phase_plan.md", body)
        finding = only(report_for(project), "phase_sync")
        assert finding.status == Status.FAIL
        assert "does not declare a parseable current phase" in finding.message

    @pytest.mark.parametrize("rel", ["docs/phase_plan.md", "PROJECT_CHARTER.md"])
    def test_check_is_skipped_when_an_input_is_missing(self, project, rel):
        remove(project, rel)
        assert findings(report_for(project), "phase_sync") == []


# --- 12. Decisions linked from the charter -----------------------------------


class TestDecisionsLinked:
    def test_linked_decisions_pass(self, project):
        assert only(report_for(project), "decisions_linked").status == Status.PASS

    def test_unlinked_decision_fails_with_its_path(self, project):
        name = "20260102_DEC002_unlinked.md"
        write(project, f"docs/decisions/{name}", decision_text(name))
        report = report_for(project)

        assert paths_failed(report, "decisions_linked") == [f"docs/decisions/{name}"]
        assert has_fail(report, "decisions_linked", "is not linked from PROJECT_CHARTER.md")

    def test_every_unlinked_decision_is_reported(self, make):
        project = make(decisions=("20260101_DEC001_a.md", "20260102_DEC002_b.md"))
        write(project, "PROJECT_CHARTER.md", charter_text(decisions=()))
        report = report_for(project)
        assert len(findings(report, "decisions_linked", Status.FAIL)) == 2

    def test_readme_does_not_need_to_be_linked(self, project):
        failed = paths_failed(report_for(project), "decisions_linked")
        assert "docs/decisions/README.md" not in failed

    def test_no_decisions_at_all_fails(self, project):
        remove(project, f"docs/decisions/{SEED_DECISION}")
        finding = only(report_for(project), "decisions_linked")
        assert finding.status == Status.FAIL
        assert "no decision files found to link" in finding.message

    @pytest.mark.parametrize("rel", ["PROJECT_CHARTER.md", "docs/decisions"])
    def test_check_is_skipped_when_an_input_is_missing(self, project, rel):
        remove(project, rel)
        assert findings(report_for(project), "decisions_linked") == []


# --- 13. Living-document decay ------------------------------------------------


class TestLivingDocDecay:
    def test_fresh_plan_passes(self, project):
        assert only(report_for(project), "plan_staleness").status == Status.PASS

    def test_plan_older_than_status_fails(self, project):
        write(project, "docs/phase_plan.md", phase_plan_text(last_updated="2025-12-31"))
        finding = only(report_for(project), "plan_staleness")
        assert finding.status == Status.FAIL
        assert "2025-12-31" in finding.message and STATUS_DATE in finding.message

    def test_plan_dated_same_day_as_status_passes(self, project):
        write(project, "docs/phase_plan.md", phase_plan_text(last_updated=STATUS_DATE))
        assert only(report_for(project), "plan_staleness").status == Status.PASS

    @pytest.mark.parametrize("body", ["# Status\n\nno dated headings here\n"])
    def test_staleness_is_skipped_without_a_dated_status_heading(self, project, body):
        write(project, "STATUS.md", body)
        assert findings(report_for(project), "plan_staleness") == []

    def test_status_within_the_line_budget_passes(self, project):
        write(project, "STATUS.md", status_with_lines(150))
        finding = only(report_for(project), "status_bloat")
        assert finding.status == Status.PASS
        assert "150 lines" in finding.message

    def test_bloated_status_fails(self, project):
        write(project, "STATUS.md", status_with_lines(151))
        finding = only(report_for(project), "status_bloat")
        assert finding.status == Status.FAIL
        assert "151 lines" in finding.message

    @pytest.mark.parametrize("count, warns", [(1, False), (5, False), (6, True), (9, True)])
    def test_status_entry_count_warns_above_five(self, project, count, warns):
        write(project, "STATUS.md", status_with_entries(count))
        report = report_for(project)
        entry_warnings = findings(report, "status_entries", Status.WARN)
        assert bool(entry_warnings) is warns
        if warns:
            assert f"contains {count} entries" in entry_warnings[0].message

    def test_fresh_files_do_not_warn_about_mtime(self, project):
        assert findings(report_for(project), "mtime_staleness") == []

    @pytest.mark.parametrize("rel", ["docs/phase_plan.md", "STATUS.md"])
    def test_stale_mtime_warns(self, project, rel):
        age(project / rel, days=15)
        report = report_for(project)

        warnings = findings(report, "mtime_staleness", Status.WARN)
        assert [f.path for f in warnings] == [rel]
        assert "over 14 days" in warnings[0].message
        assert report.failed == 0, fail_messages(report)
        assert report.ok(strict=False) and not report.ok(strict=True)

    def test_just_inside_the_window_does_not_warn(self, project):
        age(project / "STATUS.md", days=13)
        assert findings(report_for(project), "mtime_staleness") == []

    @pytest.mark.parametrize("rel", ["docs/phase_plan.md", "STATUS.md"])
    def test_check_is_skipped_when_an_input_is_missing(self, project, rel):
        remove(project, rel)
        report = report_for(project)
        assert findings(report, "plan_staleness") == []
        assert findings(report, "status_bloat") == []


# --- 14. Decision naming ------------------------------------------------------


class TestDecisionNaming:
    @pytest.mark.parametrize(
        "name",
        [
            "20260101_DEC001_seed.md",
            "20260101_DQ012_data_quality.md",
            "20260101_SC999_scope-cut.md",
            "20260101_MD000_model_choice.md",
            "20260101_dec002_lowercase.md",
            "20260101_dq003_lowercase.md",
        ],
    )
    def test_conforming_names_pass(self, make, name):
        project = make(decisions=(name,))
        finding = only(report_for(project), "decision_naming")
        assert finding.status == Status.PASS

    @pytest.mark.parametrize(
        "name",
        [
            "decision.md",
            "2026-01-01_DEC001_seed.md",
            "20260101_XYZ001_seed.md",
            "20260101_DEC01_seed.md",
            "20260101_DEC0001_seed.md",
            "20260101_DEC001.md",
            "20260101_DEC001_seed with spaces.md",
            "20260101_Dec001_seed.md",
            "2026010_DEC001_seed.md",
        ],
    )
    def test_non_conforming_names_fail(self, make, name):
        project = make(decisions=(name,))
        report = report_for(project)
        assert paths_failed(report, "decision_naming") == [f"docs/decisions/{name}"]
        assert has_fail(report, "decision_naming", "YYYYMMDD_<namespace>###_<title>.md")

    def test_readme_is_exempt_from_naming(self, project):
        assert only(report_for(project), "decision_naming").status == Status.PASS

    def test_check_is_skipped_without_a_decisions_dir(self, project):
        remove(project, "docs/decisions")
        assert findings(report_for(project), "decision_naming") == []

    @pytest.mark.parametrize(
        "phase, count, warns",
        [(2, 1, False), (3, 1, True), (3, 2, True), (3, 3, False), (4, 1, True), (4, 3, False)],
    )
    def test_sparse_decision_log_warning(self, make, phase, count, warns):
        names = tuple(f"20260101_DEC00{i}_seed.md" for i in range(1, count + 1))
        project = make(decisions=names)
        write(project, "PROJECT_CHARTER.md", charter_text(decisions=names, phases=(phase,)))
        write(project, "docs/phase_plan.md", phase_plan_text(current_phase=phase))

        warnings = findings(report_for(project), "sparse_decisions", Status.WARN)
        assert bool(warnings) is warns
        if warns:
            assert f"only {count} decisions at Phase {phase}" in warnings[0].message


# --- 15. Leftover scaffolds ---------------------------------------------------


class TestLeftoverScaffolds:
    def test_clean_project_passes(self, project):
        assert only(report_for(project), "leftover_scaffold").status == Status.PASS

    @pytest.mark.parametrize(
        "name",
        [
            "_framework_templates",
            "_framework_agents",
            "_framework_prompts",
            "_framework_extensions",
        ],
    )
    def test_each_scaffold_dir_fails(self, project, name):
        (project / name).mkdir()
        report = report_for(project)
        assert paths_failed(report, "leftover_scaffold") == [name]
        assert has_fail(report, "leftover_scaffold", "Leftover framework scaffold directory")

    def test_every_scaffold_dir_is_reported(self, project):
        (project / "_framework_agents").mkdir()
        (project / "_framework_templates").mkdir()
        assert sorted(paths_failed(report_for(project), "leftover_scaffold")) == [
            "_framework_agents",
            "_framework_templates",
        ]

    def test_a_plain_file_is_not_a_scaffold_dir(self, project):
        write(project, "_framework_notes.md", "# Notes\n\nNothing to clean up.\n")
        assert only(report_for(project), "leftover_scaffold").status == Status.PASS


# --- 16. Tool leaks -----------------------------------------------------------

CORE_DOCS = ("PROJECT_CHARTER.md", "AGENTS.md", "STATUS.md", "TASKS.md")

ABSOLUTE_PATH_LINES = [
    "The bundle is deployed to /etc/app by the release job.",
    "Rotated logs land in /var/log/output every night.",
    "Shared wheels live in /usr/local/share/wheels.",
    "Scratch space is /tmp/scratch during a run.",
    "Model artefacts sync to /opt/models/current.",
    "The developer checkout sits at /home/user/project.",
    "Overrides are read from /config/app.yaml at boot.",
    "Health is exposed at /status/live for the load balancer.",
]

SLASH_COMMAND_LINES = [
    "Start every session with /read to load the charter.",
    "Use /ask when a requirement is ambiguous.",
    "Then /route the work to the right specialist.",
    "Run /init once per repository.",
    "Finish with /review before merging.",
    "Draft the approach with /plan.",
    "Check /status, then continue.",
    "Compact the transcript with /compact)",
]


class TestToolLeaks:
    def test_clean_docs_pass(self, project):
        assert only(report_for(project), "tool_leak").status == Status.PASS

    @pytest.mark.parametrize("line", ABSOLUTE_PATH_LINES)
    @pytest.mark.parametrize("rel", CORE_DOCS)
    def test_absolute_paths_are_never_flagged(self, project, rel, line):
        """REGRESSION: ordinary filesystem paths must not read as slash commands."""
        append(project, rel, f"\n{line}\n")
        report = report_for(project)
        assert only(report, "tool_leak").status == Status.PASS
        assert report.failed == 0, fail_messages(report)

    @pytest.mark.parametrize("line", SLASH_COMMAND_LINES)
    def test_real_slash_commands_are_flagged(self, project, line):
        """REGRESSION: genuine assistant slash commands must still be caught."""
        append(project, "AGENTS.md", f"\n{line}\n")
        report = report_for(project)

        failures = findings(report, "tool_leak", Status.FAIL)
        assert [f.path for f in failures] == ["AGENTS.md"]
        assert "Tool-specific slash command leak" in failures[0].message
        assert failures[0].details[0].startswith("AGENTS.md:")
        assert failures[0].details[0].endswith(line)

    def test_a_slash_command_at_the_start_of_a_line_is_flagged(self, project):
        append(project, "AGENTS.md", "\n/read the charter first.\n")
        assert has_fail(report_for(project), "tool_leak", "slash command leak")

    @pytest.mark.parametrize("rel", CORE_DOCS)
    def test_every_core_doc_is_scanned_for_slash_commands(self, project, rel):
        append(project, rel, "\nStart with /read.\n")
        assert paths_failed(report_for(project), "tool_leak") == [rel]

    def test_non_core_docs_are_not_scanned(self, project):
        append(project, "docs/phase_plan.md", "\nStart with /read.\n")
        append(project, "docs/domain/README.md", "\nAsk Claude Code for help.\n")
        assert only(report_for(project), "tool_leak").status == Status.PASS

    @pytest.mark.parametrize(
        "name", ["Claude Code", "Cursor", "ChatGPT", "Copilot", "Kimi", "Qwen"]
    )
    def test_assistant_names_are_flagged_in_consumer_projects(self, project, name):
        append(project, "STATUS.md", f"\n- Paired with {name} on the pipeline.\n")
        report = report_for(project)

        failures = findings(report, "tool_leak", Status.FAIL)
        assert [f.path for f in failures] == ["STATUS.md"]
        assert "Assistant name leak" in failures[0].message
        assert name in failures[0].details[0]

    @pytest.mark.parametrize(
        "name", ["Claude Code", "Cursor", "ChatGPT", "Copilot", "Kimi", "Qwen"]
    )
    def test_assistant_names_are_allowed_in_the_framework_repo(self, make, name):
        project = make(framework_repo=True)
        append(project, "STATUS.md", f"\n- Portability verified with {name}.\n")
        assert only(report_for(project), "tool_leak").status == Status.PASS

    def test_both_leak_kinds_are_reported_separately(self, project):
        append(project, "AGENTS.md", "\nRun /read and ask Cursor for a summary.\n")
        report = report_for(project)
        messages = fail_messages(report, "tool_leak")
        assert len(messages) == 2
        assert any("slash command" in m for m in messages)
        assert any("Assistant name" in m for m in messages)


# --- Documented quirks and confirmed source defects ---------------------------


class TestPlaceholderScanScoping:
    """Regression tests for three false negatives found during the shell→Python port.

    Each of these once let a placeholder token escape the scan (Python exited 0
    where the shell reference correctly exited 1). Fixed in ``checks.py``; these
    tests keep them fixed.
    """

    def test_a_file_named_like_a_scaffold_is_still_scanned(self, project):
        """Only *directories* prune. A file merely named ``_framework_*`` is content."""
        write(project, "_framework_notes.md", "Owner: {{OWNER}}\n")
        assert only(report_for(project), "placeholders").status == Status.FAIL

    @pytest.mark.parametrize("rel", ["docs/outputs/report.md", "docs/domain/venv/notes.md"])
    def test_prune_dir_names_are_anchored_at_the_root(self, project, rel):
        """Prune names apply at the project root only, matching the shell reference.

        A nested ``docs/outputs/`` is real content and must still be scanned.
        """
        write(project, rel, "Owner: {{OWNER}}\n")
        assert only(report_for(project), "placeholders").status == Status.FAIL

    def test_profile_value_is_not_taken_from_the_next_line(self, project):
        """``Profile:`` with no value must not absorb the next line's first token."""
        write(project, "PROJECT_CHARTER.md", "# Charter\n\n**Profile:**\nsoftware-app\n")
        assert detect_profile(project) == (None, True)
