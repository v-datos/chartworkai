"""Behavioural tests for :mod:`chartworkai.scaffold` and :mod:`chartworkai.assets`.

``init_project`` is the product's first impression: whatever it writes is what a
user sees before they have read a line of documentation. So the tests here assert
on the *post-conditions a fresh project must satisfy*, not on the prose of the
generated files:

* the layout matches the profile (data profiles get the ``docs/data`` triad and the
  ``data/`` + ``reports/`` tree; the others must not be given empty folders);
* every generated cross-reference resolves — most importantly the seed decision,
  whose filename must satisfy ``checks.DECISION_NAME_RE`` or every freshly
  bootstrapped project fails its own compliance check on day one;
* running the checker over a fresh scaffold yields *exactly* the intended
  graduation gate — unresolved placeholders plus the leftover ``_framework_*``
  reference dirs — and nothing else. That pins the designed onboarding UX: fill in
  the placeholders, delete the scaffolds, go green.

The last class is a differential suite: the shell scaffold and the Python scaffold
are run into two temp dirs and compared byte for byte. ``scaffold.py`` promises the
two stay identical, so the promise is tested rather than trusted.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Set

import pytest
from conftest import REPO_ROOT, findings, report_for

from chartworkai import assets
from chartworkai.assets import asset_root, template_path
from chartworkai.checks import DATA_PROFILES, DECISION_NAME_RE
from chartworkai.manifest import (
    REFERENCE_DIRECTORIES as REFERENCE_DIRS,
)
from chartworkai.manifest import (
    SCAFFOLD_SUPPORT_FILES as SHELL_SCRIPTS,
)
from chartworkai.models import Status
from chartworkai.scaffold import BASE_DIRS, DATA_DIRS, init_project, slugify

# --- Constants ---------------------------------------------------------------

SHELL_INIT = REPO_ROOT / "scripts" / "init_project_from_framework.sh"
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

#: A frozen "today" so every generated filename and date is assertable.
FROZEN = _dt.date(2026, 3, 4)
STAMP = "20260304"
ISO = "2026-03-04"

NAME = "Chart Works Demo"
SLUG = "chart_works_demo"
SEED_DECISION = f"{STAMP}_DEC001_charter_v1.md"
SEED_HANDOFF = f"{ISO}_orchestrator.md"

DATA_PROFILE_NAMES = ("data-science", "database", "competition-ml")
NON_DATA_PROFILE_NAMES = ("software-app", "investigation", "deployed-service")
ALL_PROFILES = DATA_PROFILE_NAMES + NON_DATA_PROFILE_NAMES
GENERIC_PROFILE = "generic"

#: Documents every scaffold writes, whatever the profile.
COMMON_FILES = (
    "PROJECT_CHARTER.md",
    "AGENTS.md",
    "STATUS.md",
    "TASKS.md",
    "docs/phase_plan.md",
    "docs/style_guide.md",
    "docs/decisions/README.md",
    f"docs/decisions/{SEED_DECISION}",
    "docs/handoffs/README.md",
    f"docs/handoffs/{SEED_HANDOFF}",
    "docs/domain/README.md",
)
#: Documents that must name the project, so a reader never sees a generic stub.
NAME_BEARING_FILES = (
    "PROJECT_CHARTER.md",
    "AGENTS.md",
    "STATUS.md",
    "docs/phase_plan.md",
    "docs/style_guide.md",
    "docs/domain/README.md",
    f"docs/decisions/{SEED_DECISION}",
    f"docs/handoffs/{SEED_HANDOFF}",
)
DATA_TRIAD = (
    "docs/data/data_dictionary.md",
    "docs/data/lineage.md",
    "docs/data/watchlist.md",
)
#: Trees that only a data profile is allowed to create.
DATA_ONLY_ROOTS = ("docs/data", "data", "reports")

DECISION_LINK_RE = re.compile(r"docs/decisions/([A-Za-z0-9._-]+\.md)")

#: The exact pipeline ``init_project_from_framework.sh`` uses to derive a slug.
SHELL_SLUG_PIPELINE = (
    "printf '%s' \"$1\" | tr '[:upper:]' '[:lower:]' "
    "| sed 's/[^a-z0-9][^a-z0-9]*/_/g; s/^_//; s/_$//'"
)


# --- Helpers -----------------------------------------------------------------


def build(
    root: Path,
    *,
    name: str = NAME,
    slug: Optional[str] = None,
    profile: str = "data-science",
    profile_file: Optional[Path] = None,
    today: Optional[_dt.date] = FROZEN,
    force: bool = False,
) -> Dict[str, Any]:
    """Scaffold into *root* with the frozen date unless told otherwise."""
    return init_project(
        root,
        name,
        project_slug=slug,
        profile=profile,
        profile_file=profile_file,
        today=today,
        force=force,
    )


def tree(root: Path) -> Set[str]:
    """Every path under *root*, relative and POSIX-normalised (dirs included)."""
    return {p.relative_to(root).as_posix() for p in root.rglob("*")}


def files_under(root: Path) -> Set[str]:
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def shell_slugify(value: str) -> str:
    """Derive a slug the way the shell scaffold does, including its trailing trim."""
    proc = subprocess.run(
        ["sh", "-c", SHELL_SLUG_PIPELINE, "sh", value],
        capture_output=True,
        text=True,
        check=True,
    )
    # Command substitution in the shell script strips trailing newlines.
    return proc.stdout.rstrip("\n")


def run_shell_scaffold(target: Path, name: str, slug: str, profile: str):
    """Run the reference shell scaffold into *target*."""
    return subprocess.run(
        ["sh", str(SHELL_INIT), str(target), name, slug, profile],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )


@pytest.fixture
def scaffold(tmp_path: Path) -> Path:
    """A freshly bootstrapped data-science project at the frozen date."""
    root = tmp_path / "proj"
    build(root)
    return root


# --- slugify -----------------------------------------------------------------


class TestSlugify:
    """The slug is a filesystem and import-path identifier: it must stay boring."""

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("My App", "my_app"),
            ("MY APP", "my_app"),
            ("MiXeD CaSe 42", "mixed_case_42"),
            ("Chart Works Demo", "chart_works_demo"),
        ],
    )
    def test_lowercases_and_joins_words(self, value, expected):
        assert slugify(value) == expected

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("a---b", "a_b"),
            ("a  b", "a_b"),
            ("Hello, World!", "hello_world"),
            ("A/B testing", "a_b_testing"),
            ("R&D Pipeline", "r_d_pipeline"),
            ("dots.in.name", "dots_in_name"),
            ("tab\there", "tab_here"),
        ],
    )
    def test_runs_of_non_alphanumerics_collapse_to_one_underscore(self, value, expected):
        assert slugify(value) == expected

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("--lead", "lead"),
            ("trail--", "trail"),
            ("_x_", "x"),
            ("  Leading and trailing  ", "leading_and_trailing"),
        ],
    )
    def test_leading_and_trailing_underscores_are_stripped(self, value, expected):
        assert slugify(value) == expected

    @pytest.mark.parametrize("value", ["", "   ", "___", "!!!", "-", "***"])
    def test_empty_ish_input_yields_an_empty_slug(self, value):
        assert slugify(value) == ""

    @pytest.mark.parametrize(
        "value, expected",
        [("2026", "2026"), ("9lives", "9lives"), ("Project 2026", "project_2026")],
    )
    def test_digits_survive(self, value, expected):
        assert slugify(value) == expected

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("Café Project", "caf_project"),
            ("naïve-résumé", "na_ve_r_sum"),
            ("über", "ber"),
            ("ÉCOLE", "cole"),
            ("日本語 project", "project"),
            ("emoji 🚀 rocket", "emoji_rocket"),
        ],
    )
    def test_non_ascii_is_treated_as_a_separator(self, value, expected):
        assert slugify(value) == expected

    def test_result_is_always_a_safe_identifier_body(self):
        for value in ["Café Project", "R&D Pipeline", "  A/B  ", "Ω omega", "9lives"]:
            slug = slugify(value)
            assert re.fullmatch(r"[a-z0-9_]*", slug), slug
            assert not slug.startswith("_") and not slug.endswith("_")

    def test_already_slugged_input_is_idempotent(self):
        assert slugify("snake_case_name") == "snake_case_name"
        assert slugify(slugify("Some Project Name")) == slugify("Some Project Name")


@needs_sh
class TestSlugifyMatchesShell:
    """``slugify`` must agree with the ``tr | sed`` pipeline in the shell scaffold."""

    @pytest.mark.parametrize(
        "value",
        [
            "My App",
            "MY APP",
            "Chart Works Demo",
            "  Leading and trailing  ",
            "Hello, World!",
            "a---b",
            "Project 2026",
            "2026",
            "___",
            "!!!",
            "",
            "   ",
            "-",
            "_x_",
            "snake_case_name",
            "kebab-case-name",
            "dots.in.name",
            "A/B testing",
            "R&D Pipeline",
            "100% coverage",
            "MiXeD CaSe 42",
            "x",
            "X",
            "9lives",
            "a  b",
            "--lead",
            "trail--",
            "Café Project",
            "naïve-résumé",
            "über",
            "ÉCOLE",
            "Ω omega",
            "日本語 project",
            "emoji 🚀 rocket",
        ],
    )
    def test_python_and_shell_derive_the_same_slug(self, value):
        assert slugify(value) == shell_slugify(value)


class TestSlugifyKnownDivergences:
    """Two exotic inputs where Python and the shell cannot agree.

    Both are recorded rather than silently tolerated: a change in either direction
    should be a deliberate decision, not a surprise.
    """

    def test_dotted_capital_i_keeps_the_combining_mark_as_a_separator(self):
        # ``str.lower()`` expands U+0130 to "i" + U+0307; the shell's byte-oriented
        # ``tr``/``sed`` drop both bytes and produce "istanbul".
        assert slugify("İstanbul") == "i_stanbul"

    def test_newlines_collapse_even_though_sed_is_line_oriented(self):
        # ``sed`` cannot see across a line boundary, so the shell keeps the newline.
        assert slugify("new\nline") == "new_line"


# --- Directory layout --------------------------------------------------------


class TestDirectoryLayout:
    def test_plain_init_uses_the_domain_agnostic_generic_core(self, tmp_path):
        root = tmp_path / "generic"
        summary = init_project(root, NAME, today=FROZEN)
        assert summary["profile"] == "generic"
        assert summary["profile_kind"] == "generic"
        assert summary["is_data_profile"] is False
        assert "Profile: generic" in (root / "PROJECT_CHARTER.md").read_text(encoding="utf-8")
        assert not (root / "docs/data").exists()

    def test_generic_agent_template_contains_no_data_science_layout(self, tmp_path):
        root = tmp_path / "generic"
        init_project(root, NAME, today=FROZEN)
        agents = (root / "AGENTS.md").read_text(encoding="utf-8")
        assert "data-science" not in agents
        assert "Data Engineer" not in agents
        assert "Orchestrator, Domain Expert, Producer, Reviewer" in agents

    @pytest.mark.parametrize("profile", ALL_PROFILES)
    @pytest.mark.parametrize("relative", BASE_DIRS)
    def test_base_directories_exist_for_every_profile(self, tmp_path, profile, relative):
        root = tmp_path / profile
        build(root, profile=profile)
        assert (root / relative).is_dir()

    @pytest.mark.parametrize("profile", DATA_PROFILE_NAMES)
    @pytest.mark.parametrize("relative", DATA_DIRS)
    def test_data_profiles_get_the_data_layout(self, tmp_path, profile, relative):
        root = tmp_path / profile
        build(root, profile=profile)
        assert (root / relative).is_dir()

    @pytest.mark.parametrize("profile", NON_DATA_PROFILE_NAMES)
    @pytest.mark.parametrize("relative", DATA_DIRS)
    def test_non_data_profiles_do_not_get_the_data_layout(self, tmp_path, profile, relative):
        root = tmp_path / profile
        build(root, profile=profile)
        assert not (root / relative).exists()

    @pytest.mark.parametrize("profile", NON_DATA_PROFILE_NAMES)
    @pytest.mark.parametrize("top", DATA_ONLY_ROOTS)
    def test_non_data_profiles_leave_no_empty_data_roots(self, tmp_path, profile, top):
        root = tmp_path / profile
        build(root, profile=profile)
        assert not (root / top).exists()

    @pytest.mark.parametrize("profile", DATA_PROFILE_NAMES)
    def test_data_profiles_get_the_contract_triad(self, tmp_path, profile):
        root = tmp_path / profile
        build(root, profile=profile)
        for relative in DATA_TRIAD:
            assert (root / relative).is_file()

    @pytest.mark.parametrize("profile", NON_DATA_PROFILE_NAMES)
    def test_non_data_profiles_skip_the_contract_triad(self, tmp_path, profile):
        root = tmp_path / profile
        build(root, profile=profile)
        for relative in DATA_TRIAD:
            assert not (root / relative).exists()

    def test_the_profile_split_matches_the_checkers_definition(self):
        assert set(DATA_PROFILE_NAMES) == set(DATA_PROFILES)
        assert not set(NON_DATA_PROFILE_NAMES) & set(DATA_PROFILES)

    def test_target_directory_is_created_when_absent(self, tmp_path):
        root = tmp_path / "deep" / "nested" / "proj"
        build(root)
        assert (root / "PROJECT_CHARTER.md").is_file()

    def test_reproducibility_directory_exists_for_the_qa_gate(self, scaffold):
        assert (scaffold / "docs" / "reproducibility").is_dir()


# --- Reference material ------------------------------------------------------


class TestReferenceMaterial:
    @pytest.mark.parametrize("name", REFERENCE_DIRS)
    def test_reference_directory_is_copied(self, scaffold, name):
        assert (scaffold / f"_framework_{name}").is_dir()

    @pytest.mark.parametrize("name", REFERENCE_DIRS)
    def test_reference_directory_is_not_empty(self, scaffold, name):
        copied = scaffold / f"_framework_{name}"
        assert any(p.is_file() for p in copied.rglob("*")), f"_framework_{name} is empty"

    @pytest.mark.parametrize("name", REFERENCE_DIRS)
    def test_reference_directory_mirrors_the_packaged_asset(self, scaffold, name):
        source = asset_root() / name
        copied = scaffold / f"_framework_{name}"
        assert files_under(copied) == files_under(source)

    def test_exactly_four_reference_directories_are_created(self, scaffold):
        assert sorted(p.name for p in scaffold.glob("_framework_*")) == sorted(
            f"_framework_{name}" for name in REFERENCE_DIRS
        )

    def test_summary_lists_the_reference_directories(self, tmp_path):
        summary = build(tmp_path / "proj")
        assert summary["reference_dirs"] == [f"_framework_{name}" for name in REFERENCE_DIRS]

    @pytest.mark.parametrize("relative", SHELL_SCRIPTS)
    def test_shell_script_lands_in_scripts(self, scaffold, relative):
        assert (scaffold / "scripts" / Path(relative).name).is_file()

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="POSIX permission bits do not exist on Windows; chmod is a no-op there.",
    )
    @pytest.mark.parametrize("relative", SHELL_SCRIPTS)
    def test_shell_script_is_executable(self, scaffold, relative):
        path = scaffold / "scripts" / Path(relative).name
        assert os.access(path, os.X_OK)
        assert path.stat().st_mode & stat.S_IXUSR

    @pytest.mark.parametrize("relative", SHELL_SCRIPTS)
    def test_shell_script_is_a_byte_copy_of_the_packaged_one(self, scaffold, relative):
        source = asset_root() / relative
        copied = scaffold / "scripts" / Path(relative).name
        assert copied.read_bytes() == source.read_bytes()

    def test_a_scaffolded_project_can_run_its_own_shell_checker(self, scaffold):
        assert (scaffold / "scripts" / "check_framework_compliance.sh").is_file()
        assert (scaffold / "scripts" / "generate_phase_plan.sh").is_file()


# --- Generated documents -----------------------------------------------------


class TestGeneratedDocuments:
    @pytest.mark.parametrize("relative", COMMON_FILES)
    def test_common_file_exists(self, scaffold, relative):
        assert (scaffold / relative).is_file()

    @pytest.mark.parametrize("relative", COMMON_FILES)
    def test_common_file_is_not_empty(self, scaffold, relative):
        assert (scaffold / relative).read_text(encoding="utf-8").strip()

    @pytest.mark.parametrize("relative", NAME_BEARING_FILES)
    def test_generated_file_names_the_project(self, scaffold, relative):
        assert NAME in (scaffold / relative).read_text(encoding="utf-8")

    def test_charter_records_the_profile(self, tmp_path):
        root = tmp_path / "proj"
        build(root, profile="software-app")
        assert "Profile: software-app" in (root / "PROJECT_CHARTER.md").read_text(encoding="utf-8")

    def test_charter_keeps_the_stack_placeholders_for_the_user_to_fill(self, scaffold):
        charter = (scaffold / "PROJECT_CHARTER.md").read_text(encoding="utf-8")
        for token in ("{{LANGUAGE_RUNTIME}}", "{{VERIFY_COMMAND}}"):
            assert token in charter

    def test_tasks_file_uses_checkbox_bullets(self, scaffold):
        tasks = (scaffold / "TASKS.md").read_text(encoding="utf-8")
        assert "- [ ] **T-001" in tasks
        assert "- [x] **T-000" in tasks

    def test_files_are_written_as_utf8(self, scaffold):
        # The seed decision carries an em dash; a mis-encoded write would corrupt it.
        assert "—" in (scaffold / f"docs/decisions/{SEED_DECISION}").read_text(encoding="utf-8")


class TestAgentsSubstitution:
    def test_project_name_token_is_replaced(self, scaffold):
        assert "{{PROJECT_NAME}}" not in (scaffold / "AGENTS.md").read_text(encoding="utf-8")

    def test_project_slug_token_is_replaced(self, scaffold):
        assert "{{PROJECT_SLUG}}" not in (scaffold / "AGENTS.md").read_text(encoding="utf-8")

    def test_substituted_values_appear(self, scaffold):
        agents = (scaffold / "AGENTS.md").read_text(encoding="utf-8")
        assert NAME in agents
        assert SLUG in agents

    def test_explicit_slug_overrides_the_derived_one(self, tmp_path):
        root = tmp_path / "proj"
        summary = build(root, slug="custom_slug")
        assert summary["slug"] == "custom_slug"
        agents = (root / "AGENTS.md").read_text(encoding="utf-8")
        assert "custom_slug" in agents
        assert SLUG not in agents

    def test_derived_slug_is_used_when_none_is_given(self, tmp_path):
        assert build(tmp_path / "proj")["slug"] == slugify(NAME)

    def test_other_template_placeholders_survive_as_the_users_homework(self, scaffold):
        # Only the two project tokens are substituted; the rest are the graduation gate.
        assert "{{Domain Expert Title}}" in (scaffold / "AGENTS.md").read_text(encoding="utf-8")


# --- The seed decision -------------------------------------------------------


class TestSeedDecision:
    def test_seed_decision_exists(self, scaffold):
        assert (scaffold / "docs" / "decisions" / SEED_DECISION).is_file()

    def test_seed_decision_name_matches_the_checkers_pattern(self, scaffold):
        """Regression: the seed used to be ``YYYYMMDD_charter_v1.md``.

        That name fails ``decision_naming`` in every freshly bootstrapped project,
        so the scaffold shipped a project that could never pass its own checker.
        """
        decisions = [
            p for p in (scaffold / "docs" / "decisions").glob("*.md") if p.name != "README.md"
        ]
        assert decisions, "the scaffold must seed at least one decision"
        for path in decisions:
            assert DECISION_NAME_RE.match(path.name), path.name

    def test_seed_decision_uses_the_dec_namespace_and_first_number(self, scaffold):
        name = SEED_DECISION
        assert name.startswith(f"{STAMP}_DEC001_")

    def test_charter_links_the_decision_that_exists_on_disk(self, scaffold):
        charter = (scaffold / "PROJECT_CHARTER.md").read_text(encoding="utf-8")
        referenced = set(DECISION_LINK_RE.findall(charter))
        assert referenced == {SEED_DECISION}
        for name in referenced:
            assert (scaffold / "docs" / "decisions" / name).is_file()

    def test_phase_plan_links_the_decision_that_exists_on_disk(self, scaffold):
        plan = (scaffold / "docs" / "phase_plan.md").read_text(encoding="utf-8")
        referenced = set(DECISION_LINK_RE.findall(plan))
        assert referenced == {SEED_DECISION}
        for name in referenced:
            assert (scaffold / "docs" / "decisions" / name).is_file()

    def test_charter_and_plan_agree_on_the_decision_path(self, scaffold):
        charter = (scaffold / "PROJECT_CHARTER.md").read_text(encoding="utf-8")
        plan = (scaffold / "docs" / "phase_plan.md").read_text(encoding="utf-8")
        assert set(DECISION_LINK_RE.findall(charter)) == set(DECISION_LINK_RE.findall(plan))

    def test_tasks_links_the_handoff_that_exists_on_disk(self, scaffold):
        tasks = (scaffold / "TASKS.md").read_text(encoding="utf-8")
        assert f"docs/handoffs/{SEED_HANDOFF}" in tasks
        assert (scaffold / "docs" / "handoffs" / SEED_HANDOFF).is_file()


# --- Injectable date ---------------------------------------------------------


class TestInjectableToday:
    @pytest.mark.parametrize(
        "day, stamp, iso",
        [
            (_dt.date(2026, 3, 4), "20260304", "2026-03-04"),
            (_dt.date(1999, 12, 31), "19991231", "1999-12-31"),
            (_dt.date(2030, 1, 1), "20300101", "2030-01-01"),
        ],
    )
    def test_generated_filenames_use_the_injected_date(self, tmp_path, day, stamp, iso):
        root = tmp_path / stamp
        build(root, today=day)
        assert (root / "docs" / "decisions" / f"{stamp}_DEC001_charter_v1.md").is_file()
        assert (root / "docs" / "handoffs" / f"{iso}_orchestrator.md").is_file()

    def test_generated_dates_use_the_injected_date(self, tmp_path):
        root = tmp_path / "proj"
        build(root, today=_dt.date(2030, 1, 1))
        for relative in ("PROJECT_CHARTER.md", "STATUS.md", "TASKS.md", "docs/phase_plan.md"):
            text = (root / relative).read_text(encoding="utf-8")
            assert "2030-01-01" in text
            assert ISO not in text

    def test_data_contracts_use_the_injected_date(self, tmp_path):
        root = tmp_path / "proj"
        build(root, today=_dt.date(2030, 1, 1))
        for relative in DATA_TRIAD:
            assert "Last updated: 2030-01-01" in (root / relative).read_text(encoding="utf-8")

    def test_omitting_today_uses_the_real_date(self, tmp_path):
        root = tmp_path / "proj"
        before = _dt.date.today()
        build(root, today=None)
        after = _dt.date.today()
        names = {p.name for p in (root / "docs" / "decisions").glob("*_DEC001_*.md")}
        assert names <= {f"{d:%Y%m%d}_DEC001_charter_v1.md" for d in (before, after)}
        assert len(names) == 1


# --- The summary contract ----------------------------------------------------


class TestSummary:
    def test_summary_keys_are_stable(self, tmp_path):
        summary = build(tmp_path / "proj")
        assert set(summary) == {
            "project_root",
            "project",
            "slug",
            "profile",
            "profile_kind",
            "extends",
            "is_data_profile",
            "validation_commands",
            "reference_dirs",
        }

    def test_summary_reports_the_resolved_root(self, tmp_path):
        root = tmp_path / "proj"
        summary = build(root)
        assert Path(summary["project_root"]) == root.resolve()

    def test_summary_echoes_name_profile_and_slug(self, tmp_path):
        summary = build(tmp_path / "proj", profile="database")
        assert summary["project"] == NAME
        assert summary["profile"] == "database"
        assert summary["slug"] == SLUG
        assert summary["profile_kind"] == "preset"

    @pytest.mark.parametrize("profile", ALL_PROFILES)
    def test_summary_flags_data_profiles(self, tmp_path, profile):
        summary = build(tmp_path / profile, profile=profile)
        assert summary["is_data_profile"] is (profile in DATA_PROFILES)

    def test_summary_is_json_serialisable(self, tmp_path):
        json.dumps(build(tmp_path / "proj"))

    def test_a_string_target_is_accepted(self, tmp_path):
        summary = build(str(tmp_path / "proj"))
        assert Path(summary["project_root"]).is_dir()

    @pytest.mark.parametrize("profile", ["rocket-science", "", "Data-Science", "software_app"])
    def test_an_unknown_profile_is_rejected(self, tmp_path, profile):
        """REGRESSION: a typo used to be accepted and silently treated as non-data,
        handing the project the wrong governance contract with no warning."""
        with pytest.raises(ValueError, match="unknown profile"):
            build(tmp_path / "proj", profile=profile)
        assert not (tmp_path / "proj" / "PROJECT_CHARTER.md").exists()

    def test_the_error_names_the_valid_profiles(self, tmp_path):
        with pytest.raises(ValueError) as excinfo:
            build(tmp_path / "proj", profile="nope")
        for known in ("data-science", "software-app", "investigation"):
            assert known in str(excinfo.value)


class TestCustomProfileScaffold:
    @staticmethod
    def write_profile(tmp_path, **overrides):
        value = {
            "schema_version": 1,
            "name": "legal-research",
            "description": "Evidence-backed legal research.",
            "extends": "generic",
            "required_files": ["docs/evidence/source_register.md"],
            "required_directories": ["docs/evidence"],
            "scaffold_directories": ["docs/evidence"],
            "default_roles": [
                "Orchestrator",
                "Legal Researcher",
                "Source Reviewer",
                "QA / Reproducibility Engineer",
            ],
            "validation_commands": ["make verify-evidence", "make review-sources"],
        }
        value.update(overrides)
        path = tmp_path / "custom-profile.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_custom_contract_is_persisted_and_scaffolded(self, tmp_path):
        root = tmp_path / "project"
        summary = build(root, profile_file=self.write_profile(tmp_path))

        assert summary["profile"] == "legal-research"
        assert summary["profile_kind"] == "custom"
        assert summary["extends"] == "generic"
        assert summary["validation_commands"] == ["make verify-evidence", "make review-sources"]
        assert (root / "chartworkai.profile.json").is_file()
        assert (root / "docs/evidence").is_dir()

        charter = (root / "PROJECT_CHARTER.md").read_text(encoding="utf-8")
        agents = (root / "AGENTS.md").read_text(encoding="utf-8")
        assert "Profile: legal-research" in charter
        assert "Verify command: make verify-evidence" in charter
        assert "`make review-sources`" in charter
        assert "Legal Researcher" in agents

    def test_custom_required_artifacts_are_enforced(self, tmp_path):
        root = tmp_path / "project"
        build(root, profile_file=self.write_profile(tmp_path))
        report = report_for(root)
        required_failures = {
            finding.path for finding in findings(report, "required_file", Status.FAIL)
        }
        assert "docs/evidence/source_register.md" in required_failures
        assert findings(report, "custom_profile", Status.PASS)
        assert findings(report, "validation_commands", Status.PASS)

    def test_validation_commands_are_never_executed_implicitly(self, tmp_path):
        marker = tmp_path / "must-not-exist"
        root = tmp_path / "project"
        path = self.write_profile(
            tmp_path,
            validation_commands=[f"touch {marker}"],
            required_files=[],
        )
        build(root, profile_file=path)
        report_for(root)
        assert not marker.exists()

    def test_extending_a_data_preset_keeps_its_contract(self, tmp_path):
        root = tmp_path / "project"
        path = self.write_profile(tmp_path, extends="data-science")
        summary = build(root, profile_file=path)
        assert summary["is_data_profile"] is True
        for relative in DATA_TRIAD:
            assert (root / relative).is_file()

    def test_invalid_custom_profile_writes_nothing(self, tmp_path):
        root = tmp_path / "project"
        path = self.write_profile(tmp_path, required_files=["../escape"])
        with pytest.raises(ValueError, match="project-relative POSIX paths"):
            build(root, profile_file=path)
        assert not root.exists()


# --- Re-running --------------------------------------------------------------


class TestRerun:
    """Re-running init must never destroy work.

    REGRESSION: init used to rewrite the charter, status and tasks unconditionally,
    so a second run — or a run into the wrong directory — silently discarded whatever
    the team had written.
    """

    def test_rerunning_refuses_instead_of_clobbering(self, scaffold):
        with pytest.raises(ValueError, match="refusing to overwrite"):
            build(scaffold)

    def test_the_refusal_names_the_documents_at_risk(self, scaffold):
        with pytest.raises(ValueError) as excinfo:
            build(scaffold)
        message = str(excinfo.value)
        assert "PROJECT_CHARTER.md" in message
        assert "--force" in message

    def test_a_refused_rerun_changes_nothing(self, scaffold):
        (scaffold / "PROJECT_CHARTER.md").write_text("# mine\n", encoding="utf-8")
        before = tree(scaffold)
        with pytest.raises(ValueError):
            build(scaffold)
        assert tree(scaffold) == before
        assert (scaffold / "PROJECT_CHARTER.md").read_text(encoding="utf-8") == "# mine\n"

    def test_force_overwrites_deliberately(self, scaffold):
        (scaffold / "STATUS.md").write_text("# clobbered\n", encoding="utf-8")
        build(scaffold, force=True)
        assert "Framework Initialization" in (scaffold / "STATUS.md").read_text(encoding="utf-8")

    def test_force_refreshes_the_reference_directories(self, scaffold):
        stray = scaffold / "_framework_templates" / "STRAY.md"
        stray.write_text("left over from an older framework version\n", encoding="utf-8")
        build(scaffold, force=True)
        assert not stray.exists()
        assert files_under(scaffold / "_framework_templates") == files_under(
            asset_root() / "templates"
        )

    def test_force_leaves_user_files_alone(self, scaffold):
        keep = scaffold / "src" / "app.py"
        keep.write_text("print('hello')\n", encoding="utf-8")
        build(scaffold, force=True)
        assert keep.read_text(encoding="utf-8") == "print('hello')\n"

    def test_force_is_idempotent_for_the_generated_tree(self, scaffold):
        before = tree(scaffold)
        build(scaffold, force=True)
        assert tree(scaffold) == before

    def test_init_into_an_existing_repo_without_governance_is_allowed(self, tmp_path):
        """Adding ChartworkAI to a real project must still work — only the
        canonical documents are protected, not the presence of other files."""
        root = tmp_path / "existing"
        (root / "src").mkdir(parents=True)
        (root / "README.md").write_text("# My app\n", encoding="utf-8")
        (root / "src" / "main.py").write_text("print('hi')\n", encoding="utf-8")

        build(root, profile="software-app")

        assert (root / "PROJECT_CHARTER.md").is_file()
        assert (root / "README.md").read_text(encoding="utf-8") == "# My app\n"
        assert (root / "src" / "main.py").read_text(encoding="utf-8") == "print('hi')\n"

    def test_a_target_that_is_a_file_fails_cleanly(self, tmp_path):
        blocker = tmp_path / "afile"
        blocker.write_text("not a directory\n", encoding="utf-8")
        with pytest.raises(NotADirectoryError):
            build(blocker)

    def test_force_with_a_new_date_writes_a_second_seed_decision(self, scaffold):
        build(scaffold, today=_dt.date(2026, 3, 5), force=True)
        names = sorted(p.name for p in (scaffold / "docs" / "decisions").glob("*_DEC001_*.md"))
        assert names == ["20260304_DEC001_charter_v1.md", "20260305_DEC001_charter_v1.md"]


# --- Post-conditions: what the checker says about a fresh scaffold ------------


class TestFreshScaffoldPostConditions:
    """The designed onboarding UX, pinned.

    A brand new project must fail on exactly two things — both of which are
    instructions to the user, not defects: fill in the placeholders, then delete the
    ``_framework_*`` reference dirs. Any other failure means the scaffold ships
    broken governance.
    """

    @pytest.mark.parametrize("profile", ALL_PROFILES)
    def test_only_the_graduation_gate_fails(self, tmp_path, profile):
        root = tmp_path / profile
        build(root, profile=profile)
        report = report_for(root)
        assert {f.check for f in report.of_status(Status.FAIL)} == {
            "placeholders",
            "leftover_scaffold",
        }

    @pytest.mark.parametrize("profile", ALL_PROFILES)
    def test_a_fresh_scaffold_raises_no_warnings(self, tmp_path, profile):
        root = tmp_path / profile
        build(root, profile=profile)
        assert report_for(root).warnings == 0

    def test_every_reference_directory_is_reported_once(self, scaffold):
        report = report_for(scaffold)
        reported = {f.path for f in findings(report, "leftover_scaffold", Status.FAIL)}
        assert reported == {f"_framework_{name}" for name in REFERENCE_DIRS}

    def test_the_placeholder_failure_points_at_documents_the_user_owns(self, scaffold):
        report = report_for(scaffold)
        offenders = findings(report, "placeholders", Status.FAIL)[0].details
        sources = {detail.split(":", 1)[0] for detail in offenders}
        assert sources == {"AGENTS.md", "PROJECT_CHARTER.md"}

    @pytest.mark.parametrize("profile", ALL_PROFILES)
    def test_deleting_the_reference_dirs_leaves_only_placeholders(self, tmp_path, profile):
        root = tmp_path / profile
        build(root, profile=profile)
        for path in root.glob("_framework_*"):
            shutil.rmtree(path)
        report = report_for(root)
        assert {f.check for f in report.of_status(Status.FAIL)} == {"placeholders"}
        assert report.warnings == 0

    def test_resolving_the_placeholders_too_makes_the_project_pass(self, scaffold):
        for path in scaffold.glob("_framework_*"):
            shutil.rmtree(path)
        for relative in ("AGENTS.md", "PROJECT_CHARTER.md"):
            path = scaffold / relative
            text = re.sub(r"\{\{[^}]*\}\}", "filled in", path.read_text(encoding="utf-8"))
            path.write_text(text, encoding="utf-8")
        report = report_for(scaffold)
        assert report.failed == 0, [f.message for f in report.of_status(Status.FAIL)]
        assert report.ok(strict=True)

    def test_the_scaffold_is_not_mistaken_for_the_framework_repo(self, scaffold):
        # A consumer project has no root framework.json, so placeholder pruning and
        # the leftover-scaffold check both apply to it.
        assert report_for(scaffold).framework_repo is False

    @pytest.mark.parametrize("profile", ALL_PROFILES)
    def test_the_detected_profile_round_trips_through_the_charter(self, tmp_path, profile):
        root = tmp_path / profile
        build(root, profile=profile)
        report = report_for(root)
        assert report.profile == profile
        assert report.is_data_profile is (profile in DATA_PROFILES)


# --- assets.py ---------------------------------------------------------------


class TestAssetRoot:
    def test_asset_root_holds_templates_and_agents(self):
        root = asset_root()
        assert (root / "templates").is_dir()
        assert (root / "agents").is_dir()
        assert (root / "framework.json").is_file()

    def test_asset_root_holds_every_reference_directory(self):
        root = asset_root()
        for name in REFERENCE_DIRS:
            assert (root / name).is_dir(), name

    def test_asset_root_holds_the_shell_scripts(self):
        root = asset_root()
        for relative in SHELL_SCRIPTS:
            assert (root / relative).is_file(), relative

    def test_asset_root_is_one_of_the_declared_candidates(self):
        # True for both install shapes: the wheel's ``_assets`` and a src checkout.
        assert asset_root() in assets._candidates()

    def test_asset_root_returns_an_absolute_path(self):
        assert asset_root().is_absolute()

    def test_asset_root_raises_when_no_candidate_carries_the_assets(self, monkeypatch, tmp_path):
        monkeypatch.setattr(assets, "_candidates", lambda: [tmp_path])
        with pytest.raises(FileNotFoundError, match="Could not locate the ChartworkAI assets"):
            assets.asset_root()

    def test_asset_root_rejects_a_partial_candidate(self, monkeypatch, tmp_path):
        (tmp_path / "templates").mkdir()  # templates without agents is not enough
        monkeypatch.setattr(assets, "_candidates", lambda: [tmp_path])
        with pytest.raises(FileNotFoundError):
            assets.asset_root()

    def test_asset_root_takes_the_first_viable_candidate(self, monkeypatch, tmp_path):
        winner = tmp_path / "winner"
        (winner / "templates").mkdir(parents=True)
        (winner / "agents").mkdir(parents=True)
        (winner / "framework.json").write_text("{}\n", encoding="utf-8")
        monkeypatch.setattr(assets, "_candidates", lambda: [tmp_path, winner, REPO_ROOT])
        assert assets.asset_root() == winner

    def test_candidates_covers_both_the_wheel_and_the_editable_install(self):
        here = Path(assets.__file__).resolve()
        assert assets._candidates() == [
            here.parents[0] / "_assets",  # wheel: force-included at build time
            here.parents[2],  # editable install: src/chartworkai -> repo root
            here.parents[1],
        ]


class TestTemplatePath:
    def test_agents_template_resolves(self):
        path = template_path("templates/AGENTS.template.md")
        assert path.is_file()
        assert path.name == "AGENTS.template.md"

    def test_agents_template_still_carries_the_project_tokens(self):
        text = template_path("templates/AGENTS.template.md").read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}" in text
        assert "{{PROJECT_SLUG}}" in text

    @pytest.mark.parametrize("relative", SHELL_SCRIPTS)
    def test_shell_scripts_resolve(self, relative):
        assert template_path(relative).is_file()

    def test_a_bogus_relative_path_raises(self):
        with pytest.raises(FileNotFoundError, match="packaged asset is missing"):
            template_path("templates/NOT_A_REAL_TEMPLATE.md")

    def test_a_bogus_directory_raises(self):
        with pytest.raises(FileNotFoundError, match="packaged asset is missing"):
            template_path("no_such_dir/file.md")

    def test_the_error_names_the_missing_asset(self):
        with pytest.raises(FileNotFoundError) as excinfo:
            template_path("templates/missing.md")
        assert "templates/missing.md" in str(excinfo.value)

    def test_returned_path_is_anchored_at_the_asset_root(self):
        assert template_path("templates/AGENTS.template.md").parent == asset_root() / "templates"


# --- Differential parity against the shell scaffold --------------------------


@needs_sh
class TestShellParity:
    """The shell and Python scaffolds must produce the same project, byte for byte.

    ``scaffold.py`` states the two implementations are kept identical so CI can diff
    them. These tests are that diff. The shell runs first and its seed-decision
    stamp is fed back into Python as ``today=``, so the pair cannot disagree merely
    because the clock rolled over between the two runs.
    """

    @staticmethod
    def _both(tmp_path: Path, name: str, slug: str, profile: str):
        shell_root = tmp_path / "shell"
        python_root = tmp_path / "python"

        proc = run_shell_scaffold(shell_root, name, slug, profile)
        assert proc.returncode == 0, proc.stderr

        seeds = sorted((shell_root / "docs" / "decisions").glob("*_DEC001_*.md"))
        assert len(seeds) == 1, seeds
        day = _dt.datetime.strptime(seeds[0].name[:8], "%Y%m%d").date()

        init_project(python_root, name, project_slug=slug, profile=profile, today=day)
        return shell_root, python_root

    @pytest.mark.parametrize("profile", ["generic", "software-app", "data-science"])
    def test_file_sets_are_identical(self, tmp_path, profile):
        shell_root, python_root = self._both(tmp_path, "Parity Demo", "parity_demo", profile)
        assert tree(python_root) == tree(shell_root)

    @pytest.mark.parametrize("profile", ["generic", "software-app", "data-science"])
    def test_every_file_is_byte_identical(self, tmp_path, profile):
        shell_root, python_root = self._both(tmp_path, "Parity Demo", "parity_demo", profile)
        differing = [
            relative
            for relative in sorted(files_under(shell_root))
            if (shell_root / relative).read_bytes() != (python_root / relative).read_bytes()
        ]
        assert differing == []

    @pytest.mark.parametrize("profile", ["database", "investigation", "deployed-service"])
    def test_the_remaining_profiles_agree_too(self, tmp_path, profile):
        shell_root, python_root = self._both(tmp_path, "Parity Demo", "parity_demo", profile)
        assert tree(python_root) == tree(shell_root)
        for relative in sorted(files_under(shell_root)):
            assert (shell_root / relative).read_bytes() == (python_root / relative).read_bytes()

    def test_names_with_spaces_and_punctuation_survive_both_paths(self, tmp_path):
        shell_root, python_root = self._both(
            tmp_path, "Chart Works: Demo #2", "chart_works_demo_2", "data-science"
        )
        assert tree(python_root) == tree(shell_root)
        for relative in sorted(files_under(shell_root)):
            assert (shell_root / relative).read_bytes() == (python_root / relative).read_bytes()

    @pytest.mark.parametrize("profile", ["generic", "software-app", "data-science"])
    def test_both_scaffolds_produce_the_same_compliance_verdict(self, tmp_path, profile):
        shell_root, python_root = self._both(tmp_path, "Parity Demo", "parity_demo", profile)
        shell_report = report_for(shell_root)
        python_report = report_for(python_root)
        assert [(f.check, f.status) for f in python_report.findings] == [
            (f.check, f.status) for f in shell_report.findings
        ]

    def test_executable_bits_match(self, tmp_path):
        shell_root, python_root = self._both(tmp_path, "Parity Demo", "parity_demo", "software-app")
        for relative in SHELL_SCRIPTS:
            name = Path(relative).name
            assert os.access(python_root / "scripts" / name, os.X_OK)
            assert os.access(shell_root / "scripts" / name, os.X_OK)
