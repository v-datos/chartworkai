"""Adversarial tests for the write, read, and name-allocation guards.

Every test here is a *regression* test: each one reproduces a specific way the tool
could be made to write outside the project, destroy work it was pointed at, leak a
file it was never pointed at, or lose an audit record under concurrency. They are
grouped by the property being defended rather than by module, because the same
property has to hold in **both** implementations — the Python entry points and the
reference shell scripts — and a fix applied to only one of them is the failure mode
these tests exist to catch.

The threat model is deliberate: ChartworkAI writes into other people's repositories,
often driven by an agent acting on text it did not author. "The path came from
somewhere untrusted" is the normal case, not the exotic one.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from conftest import has_fail, only, run_shell_checker

from chartworkai.checks import run_checks
from chartworkai.safety import (
    UnsafePathError,
    create_exclusive,
    safe_copy,
    safe_mkdir,
    safe_read,
    safe_write,
)
from chartworkai.scaffold import init_project
from chartworkai.state import file_decision, file_handoff

posix_only = pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "These guards are a POSIX guarantee: the reference implementation is a "
        "POSIX sh script, and Windows symlinks need a privilege the runner does not "
        "have, so a failure there reflects the platform rather than a divergence in "
        "the product. Windows users drive the Python CLI."
    ),
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SHELL_INIT = REPO_ROOT / "scripts" / "init_project_from_framework.sh"
SHELL_PLAN = REPO_ROOT / "scripts" / "generate_phase_plan.sh"


def run_shell(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["sh", str(script), *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )


def scaffolded(root: Path, profile: str = "software-app") -> Path:
    init_project(root, project_name="Guarded", profile=profile)
    return root


# --- Property 1: a write never lands outside the project ---------------------


@posix_only
class TestWritesStayInside:
    """``..`` and symlinks are the two ways a write leaves the project."""

    @pytest.mark.parametrize(
        "relative",
        [
            "../escaped.md",
            "../../escaped.md",
            "docs/../../escaped.md",
            "docs/./../../escaped.md",
        ],
    )
    def test_dot_dot_is_refused(self, tmp_path: Path, relative: str) -> None:
        root = tmp_path / "proj"
        root.mkdir()
        with pytest.raises(UnsafePathError):
            safe_write(root, relative, "x")
        assert not (tmp_path / "escaped.md").exists()

    def test_symlinked_file_is_refused_not_followed(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        root.mkdir()
        outside = tmp_path / "outside.md"
        outside.write_text("PRECIOUS", encoding="utf-8")
        (root / "STATUS.md").symlink_to(outside)

        with pytest.raises(UnsafePathError):
            safe_write(root, "STATUS.md", "clobbered")
        assert outside.read_text(encoding="utf-8") == "PRECIOUS"

    def test_symlinked_parent_directory_is_refused(self, tmp_path: Path) -> None:
        """A symlinked *directory* carries a write out just as effectively."""
        root = tmp_path / "proj"
        root.mkdir()
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (root / "docs").symlink_to(elsewhere)

        with pytest.raises(UnsafePathError):
            safe_write(root, "docs/phase_plan.md", "x")
        assert list(elsewhere.iterdir()) == []

    def test_mkdir_refuses_to_build_through_a_symlink(self, tmp_path: Path) -> None:
        """Finding 2: ``mkdir -p`` through a symlinked ``docs/`` built the whole tree
        outside, and every later write then landed there."""
        root = tmp_path / "proj"
        root.mkdir()
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (root / "docs").symlink_to(elsewhere)

        with pytest.raises(UnsafePathError):
            safe_mkdir(root, "docs/decisions")
        assert list(elsewhere.iterdir()) == []

    def test_mkdir_creates_the_root_itself(self, tmp_path: Path) -> None:
        """The guard must still do the job it replaced: a fresh target has no root."""
        created = safe_mkdir(tmp_path / "brand-new", "docs/decisions")
        assert created.is_dir()
        assert created == (tmp_path / "brand-new" / "docs" / "decisions").resolve()

    def test_copy_refuses_a_symlinked_destination(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        (root / "scripts").mkdir(parents=True)
        source = tmp_path / "source.sh"
        source.write_text("#!/bin/sh\n", encoding="utf-8")
        outside = tmp_path / "outside.sh"
        outside.write_text("PRECIOUS", encoding="utf-8")
        (root / "scripts" / "check.sh").symlink_to(outside)

        with pytest.raises(UnsafePathError):
            safe_copy(root, "scripts/check.sh", source)
        assert outside.read_text(encoding="utf-8") == "PRECIOUS"


@posix_only
class TestInitStaysInside:
    """The same property, at the entry point a user actually runs."""

    def test_python_init_refuses_symlinked_docs(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        root.mkdir()
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (root / "docs").symlink_to(elsewhere)

        with pytest.raises(UnsafePathError):
            init_project(root, project_name="X", profile="software-app")
        assert list(elsewhere.iterdir()) == []

    @pytest.mark.parametrize("guard", ["docs", "scripts", "src", "tests"])
    def test_shell_init_refuses_symlinked_tree_dirs(self, tmp_path: Path, guard: str) -> None:
        """Finding 2, shell side. Fixing only the Python entry point left the
        documented reference implementation destructive."""
        root = tmp_path / "proj"
        root.mkdir()
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (root / guard).symlink_to(elsewhere)

        proc = run_shell(SHELL_INIT, str(root), "X", "x", "software-app")
        assert proc.returncode != 0
        assert "symlink" in proc.stderr
        assert list(elsewhere.iterdir()) == []


# --- Property 2: existing work is never silently destroyed -------------------


@posix_only
class TestNoSilentOverwrite:
    """Finding 3: the collision set missed the files init writes *last*."""

    @pytest.mark.parametrize(
        "kept",
        [
            "docs/decisions/{stamp}_DEC001_charter_v1.md",
            "docs/handoffs/{iso}_orchestrator.md",
            "scripts/check_framework_compliance.sh",
            "scripts/generate_phase_plan.sh",
        ],
    )
    def test_python_init_refuses_when_a_seeded_path_exists(self, tmp_path: Path, kept: str) -> None:
        import datetime as _dt

        root = tmp_path / "proj"
        scaffolded(root)
        day = _dt.date.today()
        target = root / kept.format(stamp=f"{day:%Y%m%d}", iso=f"{day:%Y-%m-%d}")

        # Clear everything the first run made *except* the one file under test, so the
        # only thing that can stop a second run is that file being in the clash set.
        for path in sorted(root.rglob("*"), reverse=True):
            if path == target or target in path.parents:
                continue
            if path.is_file() or path.is_symlink():
                path.unlink()
        target.write_text("MY WORK", encoding="utf-8")

        with pytest.raises(ValueError):
            init_project(root, project_name="X", profile="software-app")
        assert target.read_text(encoding="utf-8") == "MY WORK"

    def test_shell_init_refuses_when_a_copied_script_exists(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        (root / "scripts").mkdir(parents=True)
        (root / "scripts" / "check_framework_compliance.sh").write_text("MY WORK", encoding="utf-8")

        proc = run_shell(SHELL_INIT, str(root), "X", "x", "software-app")
        assert proc.returncode != 0
        assert "check_framework_compliance.sh" in proc.stderr
        assert (root / "scripts" / "check_framework_compliance.sh").read_text(
            encoding="utf-8"
        ) == "MY WORK"

    def test_shell_force_replaces_rather_than_nests(self, tmp_path: Path) -> None:
        """Finding 6: ``cp -R src dest`` nests when ``dest`` exists, so ``--force``
        left the old reference tree in place *and* buried a copy inside it."""
        root = tmp_path / "proj"
        assert run_shell(SHELL_INIT, str(root), "X", "x", "software-app").returncode == 0
        stale = root / "_framework_templates" / "STALE.md"
        stale.write_text("stale", encoding="utf-8")

        proc = run_shell(SHELL_INIT, str(root), "X", "x", "software-app", "--force")
        assert proc.returncode == 0
        assert not (root / "_framework_templates" / "templates").exists()
        assert not stale.exists()

    def test_shell_force_refuses_a_symlinked_reference_dir(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        assert run_shell(SHELL_INIT, str(root), "X", "x", "software-app").returncode == 0
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (elsewhere / "keep.md").write_text("PRECIOUS", encoding="utf-8")
        import shutil

        shutil.rmtree(root / "_framework_templates")
        (root / "_framework_templates").symlink_to(elsewhere)

        proc = run_shell(SHELL_INIT, str(root), "X", "x", "software-app", "--force")
        assert proc.returncode != 0
        assert (elsewhere / "keep.md").read_text(encoding="utf-8") == "PRECIOUS"


@posix_only
class TestPhasePlanGenerator:
    """Finding 4: the two generators disagreed about a symlinked target."""

    def test_python_refuses_a_symlinked_phase_plan(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        scaffolded(root)
        outside = tmp_path / "outside.md"
        outside.write_text("PRECIOUS", encoding="utf-8")
        (root / "docs" / "phase_plan.md").unlink()
        (root / "docs" / "phase_plan.md").symlink_to(outside)

        with pytest.raises(UnsafePathError):
            from chartworkai.plan import generate_phase_plan

            generate_phase_plan(root)
        assert outside.read_text(encoding="utf-8") == "PRECIOUS"

    def test_shell_refuses_a_symlinked_phase_plan(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        scaffolded(root)
        outside = tmp_path / "outside.md"
        outside.write_text("PRECIOUS", encoding="utf-8")
        (root / "docs" / "phase_plan.md").unlink()
        (root / "docs" / "phase_plan.md").symlink_to(outside)

        proc = run_shell(SHELL_PLAN, str(root))
        assert proc.returncode != 0
        assert "symlink" in proc.stderr
        assert outside.read_text(encoding="utf-8") == "PRECIOUS"
        assert (root / "docs" / "phase_plan.md").is_symlink()


# --- Property 3: a read never leaves the project -----------------------------


@posix_only
class TestReadsStayInside:
    """Finding 5: reads escape too, and a report is an exfiltration channel."""

    def test_safe_read_refuses_an_escaping_symlink(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        root.mkdir()
        secret = tmp_path / "secret.md"
        secret.write_text("SECRET-EXTERNAL", encoding="utf-8")
        (root / "NOTES.md").symlink_to(secret)

        with pytest.raises(UnsafePathError):
            safe_read(root, "NOTES.md")

    def test_safe_read_allows_a_link_that_stays_inside(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        root.mkdir()
        (root / "real.md").write_text("INSIDE", encoding="utf-8")
        (root / "alias.md").symlink_to(root / "real.md")

        assert safe_read(root, "alias.md") == "INSIDE"

    def test_external_content_never_reaches_the_report(self, tmp_path: Path) -> None:
        """The end-to-end version: a planted link must not surface a file from
        elsewhere on the machine in ``--json`` output or an MCP tool result."""
        root = tmp_path / "proj"
        scaffolded(root)
        secret = tmp_path / "secret.md"
        secret.write_text("SECRET-EXTERNAL {{LEAK}}", encoding="utf-8")
        (root / "docs" / "domain" / "README.md").unlink()
        (root / "docs" / "domain" / "README.md").symlink_to(secret)

        report = run_checks(root)
        assert "SECRET-EXTERNAL" not in json.dumps(report.to_dict())

    def test_the_link_itself_is_reported(self, tmp_path: Path) -> None:
        """Refusing to follow it silently would hide a planted link. Fail loudly."""
        root = tmp_path / "proj"
        scaffolded(root)
        secret = tmp_path / "secret.md"
        secret.write_text("SECRET-EXTERNAL", encoding="utf-8")
        (root / "docs" / "domain" / "EXTRA.md").symlink_to(secret)

        report = run_checks(root)
        finding = only(report, "escaping_symlinks")
        assert finding.status == "fail"
        assert "docs/domain/EXTRA.md" in finding.details

    def test_a_clean_project_passes(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        scaffolded(root)
        assert only(run_checks(root), "escaping_symlinks").status == "pass"

    def test_links_inside_the_project_are_not_flagged(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        scaffolded(root)
        (root / "docs" / "alias.md").symlink_to(root / "PROJECT_CHARTER.md")
        assert only(run_checks(root), "escaping_symlinks").status == "pass"

    def test_a_virtualenv_does_not_trip_the_check(self, tmp_path: Path) -> None:
        """Scoping matters: a venv is *full* of legitimate links to outside the
        project. Flagging those would bury the one case that matters."""
        root = tmp_path / "proj"
        scaffolded(root)
        binaries = root / ".venv" / "bin"
        binaries.mkdir(parents=True)
        (binaries / "python3").symlink_to(sys.executable)

        assert only(run_checks(root), "escaping_symlinks").status == "pass"

    def test_a_broken_link_is_not_an_escape(self, tmp_path: Path) -> None:
        """Nothing is followed, so nothing leaves the project."""
        root = tmp_path / "proj"
        scaffolded(root)
        (root / "docs" / "dangling.md").symlink_to(root / "docs" / "nope.md")
        assert only(run_checks(root), "escaping_symlinks").status == "pass"

    def test_shell_checker_agrees(self, tmp_path: Path) -> None:
        """The property has to hold in both implementations or it holds in neither."""
        root = tmp_path / "proj"
        scaffolded(root)
        clean = run_shell_checker(root)
        assert "no symlinks escape the project" in clean.out

        secret = tmp_path / "secret.md"
        secret.write_text("SECRET-EXTERNAL", encoding="utf-8")
        (root / "docs" / "domain" / "EXTRA.md").symlink_to(secret)

        dirty = run_shell_checker(root)
        assert dirty.code != 0
        assert "docs/domain/EXTRA.md" in dirty.out
        assert "SECRET-EXTERNAL" not in dirty.out

    def test_shell_checker_ignores_a_virtualenv(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        scaffolded(root)
        binaries = root / ".venv" / "bin"
        binaries.mkdir(parents=True)
        (binaries / "python3").symlink_to(sys.executable)

        assert "no symlinks escape the project" in run_shell_checker(root).out


# --- Property 4: an audit record is never lost -------------------------------


@posix_only
class TestExclusiveCreation:
    """Finding 7: choosing a free name and writing it were two separate steps."""

    def test_create_exclusive_does_not_clobber(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        root.mkdir()
        safe_write(root, "note.md", "FIRST")
        assert create_exclusive(root, "note.md", "SECOND") is None
        assert (root / "note.md").read_text(encoding="utf-8") == "FIRST"

    def test_create_exclusive_honours_the_path_guard(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        root.mkdir()
        with pytest.raises(UnsafePathError):
            create_exclusive(root, "../escaped.md", "x")
        assert not (tmp_path / "escaped.md").exists()

    def test_concurrent_decisions_get_distinct_ids(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        scaffolded(root)
        workers = 32

        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(
                pool.map(
                    lambda i: file_decision(
                        root, f"distinct title {i}", "Orchestrator", "context", "ruling"
                    ),
                    range(workers),
                )
            )

        ids = [entry["id"] for entry in results]
        assert [item for item, n in Counter(ids).items() if n > 1] == []
        files = {entry["file"] for entry in results}
        assert len(files) == workers
        for relative in files:
            assert (root / relative).is_file()

    def test_concurrent_handoffs_all_survive(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        scaffolded(root)
        workers = 32

        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(
                pool.map(
                    lambda _: file_handoff(root, "QA", "produced", "location"),
                    range(workers),
                )
            )

        files = [entry["file"] for entry in results]
        assert [item for item, n in Counter(files).items() if n > 1] == []
        assert len(files) == workers
        for relative in files:
            assert (root / relative).is_file()

    def test_sequential_handoffs_still_suffix_in_order(self, tmp_path: Path) -> None:
        """The retry loop must not change the single-threaded naming contract."""
        root = tmp_path / "proj"
        scaffolded(root)
        names = [Path(file_handoff(root, "QA", "p", "l")["file"]).name for _ in range(3)]
        assert names[0].endswith("_qa.md")
        assert names[1].endswith("_qa_2.md")
        assert names[2].endswith("_qa_3.md")

    def test_a_filed_decision_still_satisfies_the_naming_rule(self, tmp_path: Path) -> None:
        """Regression guard: the allocation rewrite must not change the filename
        shape the checker enforces."""
        root = tmp_path / "proj"
        scaffolded(root)
        file_decision(root, "Adopt a thing", "Orchestrator", "c", "r")
        assert not has_fail(run_checks(root), "decision_naming")


# --- Round-4 regressions: what the previous fixes did not actually cover ---------


@posix_only
class TestShellGuardsEveryComponent:
    """The first fix checked only *top-level* directory symlinks. That left four
    distinct escapes open in the shell tools, all of which reproduced."""

    def test_nested_directory_symlink_is_refused(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        (root / "docs").mkdir(parents=True)
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (root / "docs" / "decisions").symlink_to(elsewhere)

        proc = run_shell(SHELL_INIT, str(root), "X", "x", "software-app")
        assert proc.returncode != 0
        assert list(elsewhere.iterdir()) == []

    def test_a_dangling_symlink_does_not_create_its_target(self, tmp_path: Path) -> None:
        """`> link` follows a dangling link and creates the external file."""
        root = tmp_path / "proj"
        root.mkdir()
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (root / "PROJECT_CHARTER.md").symlink_to(elsewhere / "charter.md")

        proc = run_shell(SHELL_INIT, str(root), "X", "x", "software-app")
        assert proc.returncode != 0
        assert not (elsewhere / "charter.md").exists()

    def test_force_does_not_write_through_a_file_symlink(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        assert run_shell(SHELL_INIT, str(root), "X", "x", "software-app").returncode == 0
        outside = tmp_path / "outside.md"
        outside.write_text("PRECIOUS", encoding="utf-8")
        (root / "STATUS.md").unlink()
        (root / "STATUS.md").symlink_to(outside)

        proc = run_shell(SHELL_INIT, str(root), "X", "x", "software-app", "--force")
        assert proc.returncode != 0
        assert outside.read_text(encoding="utf-8") == "PRECIOUS"

    def test_generator_refuses_a_symlinked_docs_parent(self, tmp_path: Path) -> None:
        """Guarding only the plan *file* misses a symlinked `docs/` above it."""
        root = tmp_path / "proj"
        scaffolded(root)
        elsewhere = tmp_path / "elsewhere"
        shutil.copytree(root / "docs", elsewhere)
        (elsewhere / "phase_plan.md").write_text("PRECIOUS", encoding="utf-8")
        shutil.rmtree(root / "docs")
        (root / "docs").symlink_to(elsewhere)

        proc = run_shell(SHELL_PLAN, str(root))
        assert proc.returncode != 0
        assert (elsewhere / "phase_plan.md").read_text(encoding="utf-8") == "PRECIOUS"


@posix_only
class TestGeneratorHandlesSpaces:
    """Word-splitting `$(find ...)` dropped decisions and still exited 0 — a
    governance log that silently loses entries is worse than one that fails."""

    def test_a_decision_with_a_space_still_reaches_the_plan(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        scaffolded(root)
        decisions = root / "docs" / "decisions"
        seed = next(p for p in decisions.glob("*DEC001*.md"))
        spaced = decisions / "20260101_DEC002_has space.md"
        spaced.write_text(
            seed.read_text(encoding="utf-8").replace("DEC-001", "DEC-002"), encoding="utf-8"
        )

        proc = run_shell(SHELL_PLAN, str(root))
        assert proc.returncode == 0
        plan = (root / "docs" / "phase_plan.md").read_text(encoding="utf-8")
        assert "DEC-001" in plan
        assert "DEC-002" in plan


class TestStateDoesNotDiscloseExternalFiles:
    """`state` feeds an MCP tool result straight to an assistant. Finding 2: its
    readers were never given the project root, so a planted link disclosed any file
    the process could read."""

    def _planted(self, tmp_path: Path) -> Path:
        root = tmp_path / "proj"
        scaffolded(root)
        secret = tmp_path / "secret.md"
        secret.write_text(
            "# Project Charter - SECRET-EXTERNAL\n\nProfile: software-app\n"
            "- Verify command: SECRET-VERIFY\n",
            encoding="utf-8",
        )
        (root / "PROJECT_CHARTER.md").unlink()
        (root / "PROJECT_CHARTER.md").symlink_to(secret)
        return root

    @pytest.mark.skipif(sys.platform == "win32", reason="symlinks need a Windows privilege")
    def test_external_charter_is_not_disclosed(self, tmp_path: Path) -> None:
        from chartworkai.state import read_state

        payload = json.dumps(read_state(self._planted(tmp_path)))
        assert "SECRET-EXTERNAL" not in payload
        assert "SECRET-VERIFY" not in payload

    @pytest.mark.skipif(sys.platform == "win32", reason="symlinks need a Windows privilege")
    def test_external_decision_body_is_not_disclosed(self, tmp_path: Path) -> None:
        from chartworkai.state import read_state

        root = tmp_path / "proj"
        scaffolded(root)
        secret = tmp_path / "secret.md"
        secret.write_text("# DEC-999 — SECRET-DECISION-TITLE\n", encoding="utf-8")
        (root / "docs" / "decisions" / "20260101_DEC002_planted.md").symlink_to(secret)

        assert "SECRET-DECISION-TITLE" not in json.dumps(read_state(root))


class TestRejectionLeavesNoTrace:
    """Finding 6: the writers created `docs/decisions/` before the guard ran, so a
    refused call still built directories outside the project."""

    @pytest.mark.skipif(sys.platform == "win32", reason="symlinks need a Windows privilege")
    @pytest.mark.parametrize("call", ["decision", "handoff"])
    def test_a_refused_write_creates_nothing_outside(self, tmp_path: Path, call: str) -> None:
        root = tmp_path / "proj"
        root.mkdir()
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (root / "docs").symlink_to(elsewhere)

        with pytest.raises(UnsafePathError):
            if call == "decision":
                file_decision(root, "Title", "Orchestrator", "context", "ruling")
            else:
                file_handoff(root, "QA", "produced", "location")

        assert list(elsewhere.iterdir()) == []


class TestDecisionIdsAreUniqueUnderContention:
    """Finding 3. The previous guard made the *filename* exclusive, but the filename
    carries the title slug — so distinct titles produced distinct filenames, both
    creates succeeded, and both records claimed the same ID. Measured before the fix:
    64 calls, 64 files, 6 distinct IDs."""

    def test_distinct_titles_still_get_distinct_ids(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        scaffolded(root)
        workers = 64

        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(
                pool.map(
                    lambda i: file_decision(
                        root, f"distinct title {i}", "Orchestrator", "context", "ruling"
                    ),
                    range(workers),
                )
            )

        ids = [entry["id"] for entry in results]
        assert sorted(Counter(ids).values()) == [1] * workers, "duplicate decision IDs"
        assert len({entry["file"] for entry in results}) == workers
        for entry in results:
            assert (root / entry["file"]).is_file()

    def test_no_reservation_files_are_left_behind(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        scaffolded(root)
        with ThreadPoolExecutor(max_workers=16) as pool:
            list(
                pool.map(
                    lambda i: file_decision(root, f"title {i}", "Orchestrator", "c", "r"),
                    range(16),
                )
            )
        assert list((root / "docs" / "decisions").glob("*_pending.md")) == []

    def test_every_namespace_allocates_independently(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        scaffolded(root)
        for namespace in ("DQ", "SC", "MD"):
            entry = file_decision(
                root, f"first {namespace}", "Orchestrator", "c", "r", namespace=namespace
            )
            assert entry["id"] == f"{namespace}-001"


# --- Round-5 regressions: spoofing, hostile input, and quoting -------------------


class TestFrameworkIdentityCannotBeSpoofed:
    """Being recognised as the framework repo *relaxes* checks — most importantly it
    stops reporting leftover `_framework_*` scaffold. An empty `framework.json` beside
    an empty `templates/` used to be enough for a consumer project to silence its own
    failures."""

    def _leftover_failures(self, root: Path) -> int:
        return len(
            [
                f
                for f in run_checks(root).findings
                if f.check == "leftover_scaffold" and f.status == "fail"
            ]
        )

    def test_a_fresh_scaffold_reports_its_leftovers(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        scaffolded(root)
        assert self._leftover_failures(root) > 0

    @pytest.mark.parametrize(
        "manifest",
        [
            "{}",
            '{"name": "chartworkai"}',
            '{"name": "something-else", "version": "1", "profiles": {}, '
            '"required_files": [], "required_directories": []}',
            "not json at all",
        ],
        ids=["empty", "name-only", "wrong-name", "unparseable"],
    )
    def test_a_planted_manifest_does_not_silence_them(self, tmp_path: Path, manifest: str) -> None:
        root = tmp_path / "proj"
        scaffolded(root)
        (root / "framework.json").write_text(manifest, encoding="utf-8")
        (root / "templates").mkdir()
        assert self._leftover_failures(root) > 0

    def test_a_full_manifest_without_real_templates_does_not_qualify(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        scaffolded(root)
        (root / "framework.json").write_text(
            json.dumps(
                {
                    "name": "chartworkai",
                    "version": "1.0.0",
                    "profiles": {},
                    "required_files": [],
                    "required_directories": [],
                }
            ),
            encoding="utf-8",
        )
        (root / "templates").mkdir()
        assert self._leftover_failures(root) > 0

    def test_the_real_repository_is_still_recognised(self) -> None:
        from chartworkai.checks import detect_framework_repo

        assert detect_framework_repo(REPO_ROOT)


class TestMcpSurvivesHostileInput:
    """Tool arguments arrive from an assistant acting on text it did not author, so
    malformed input is reachable, not exotic. One bad message must not end the session
    for every later request."""

    def _serve(self, *lines: str) -> list:
        import io

        from chartworkai.mcp_server import serve

        out = io.StringIO()
        serve(stdin=io.StringIO("".join(line + "\n" for line in lines)), stdout=out)
        return [json.loads(entry) for entry in out.getvalue().splitlines()]

    HELLO = (
        '{"jsonrpc":"2.0","id":1,"method":"initialize","params":'
        '{"protocolVersion":"2024-11-05","capabilities":{},'
        '"clientInfo":{"name":"t","version":"1"}}}'
    )
    LIST = '{"jsonrpc":"2.0","id":9,"method":"tools/list"}'

    def test_deep_nesting_is_rejected_and_the_server_keeps_going(self) -> None:
        deep = (
            '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":'
            + "[" * 10000
            + "]" * 10000
            + "}"
        )
        replies = self._serve(self.HELLO, deep, self.LIST)

        assert [r.get("id") for r in replies][0] == 1
        assert "error" in replies[1]
        assert replies[-1]["id"] == 9 and "result" in replies[-1]

    def test_an_oversized_message_is_refused_unparsed(self) -> None:
        from chartworkai.mcp_server import MAX_MESSAGE_BYTES

        huge = (
            '{"jsonrpc":"2.0","id":3,"method":"tools/list","params":{"x":"'
            + "A" * (MAX_MESSAGE_BYTES + 10)
            + '"}}'
        )
        replies = self._serve(self.HELLO, huge, self.LIST)

        assert "error" in replies[1]
        assert "exceeds" in replies[1]["error"]["message"]
        assert replies[-1]["id"] == 9 and "result" in replies[-1]

    def test_ordinary_traffic_is_unaffected(self) -> None:
        replies = self._serve(self.HELLO, self.LIST)
        assert len(replies) == 2
        assert {tool["name"] for tool in replies[1]["result"]["tools"]} == {
            "chartworkai_check",
            "chartworkai_state",
            "chartworkai_file_decision",
            "chartworkai_file_handoff",
        }


@posix_only
class TestShellCheckerHandlesSpacesInThePath:
    """`find $targets` unquoted searched nonexistent paths, printed nothing, and the
    check reported a false PASS — a compliance tool that silently passes is worse than
    one that errors."""

    def test_a_placeholder_is_found_under_a_path_containing_a_space(self, tmp_path: Path) -> None:
        root = tmp_path / "has space"
        scaffolded(root)
        # Make it look like a framework checkout, which is the branch that split.
        shutil.copy(REPO_ROOT / "framework.json", root / "framework.json")
        (root / "templates").mkdir(exist_ok=True)
        (root / "templates" / "AGENTS.template.md").write_text("x", encoding="utf-8")
        (root / "STATUS.md").write_text("# Status\n\n{{UNRESOLVED}}\n", encoding="utf-8")

        result = run_shell_checker(root)
        assert "unresolved {{PLACEHOLDER}} tokens remain" in result.out
        assert has_fail(run_checks(root), "placeholders")
