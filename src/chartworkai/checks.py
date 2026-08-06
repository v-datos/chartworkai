"""The ChartworkAI compliance checker.

A faithful Python port of ``scripts/check_framework_compliance.sh``. It answers one
question: *is this project's governance layer installed and healthy?*

Deliberate divergences from the shell implementation (both strict improvements):

DIVERGENCE-1  The placeholder scan prunes **every** ``_framework_*`` directory, not
              just the three the shell hard-codes. The installer also creates
              ``_framework_extensions/``, whose templates legitimately contain
              placeholder tokens; the shell therefore double-reported one root cause
              (leftover scaffold) as two unrelated failures.
DIVERGENCE-2  The ``STATUS.md`` date is parsed from any ``## YYYY-MM-DD`` heading
              rather than requiring an em dash to follow it.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import List, Optional, Tuple

from chartworkai.models import Report, Status

# --- Conventions -------------------------------------------------------------

#: Profiles whose deliverable is data, and which therefore require the
#: ``docs/data/`` contract triad.
DATA_PROFILES = frozenset({"data-science", "database", "competition-ml"})

#: Every profile the framework recognises. A value outside this set is a typo, not
#: an extension point: silently accepting one hands the project the wrong
#: governance contract with no warning.
KNOWN_PROFILES = (
    "data-science",
    "software-app",
    "database",
    "competition-ml",
    "investigation",
    "deployed-service",
)

CORE_DOCS = ("PROJECT_CHARTER.md", "AGENTS.md", "STATUS.md", "TASKS.md")

REQUIRED_FILES = (
    "PROJECT_CHARTER.md",
    "AGENTS.md",
    "docs/phase_plan.md",
    "STATUS.md",
    "TASKS.md",
)

DATA_CONTRACT_FILES = (
    "docs/data/data_dictionary.md",
    "docs/data/lineage.md",
    "docs/data/watchlist.md",
)

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

SCANNED_SUFFIXES = frozenset({".md", ".json", ".yaml", ".yml"})

#: Directories never scanned for placeholder tokens.
PRUNE_DIR_NAMES = frozenset({".git", ".github", ".venv", "venv", "node_modules", "outputs"})
PRUNE_RELPATHS = frozenset({"data/raw", "data/staging", "data/processed"})

PLACEHOLDER_RE = re.compile(r"\{\{[^}][^}]*\}\}")
# Only horizontal whitespace: a "Profile:" line with no value must not absorb the
# first token of the following line.
PROFILE_RE = re.compile(r"Profile:[*\t ]*([A-Za-z0-9_-]+)")
CURRENT_PHASE_RE = re.compile(r"Current phase:.*?Phase\s*(\d+)", re.IGNORECASE)
STATUS_DATE_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})", re.MULTILINE)
LAST_UPDATED_RE = re.compile(r"Last updated:[*\s]*(\d{4}-\d{2}-\d{2})", re.IGNORECASE)
DECISION_NAME_RE = re.compile(r"^\d{8}_(?:DEC|DQ|SC|MD|dec|dq|sc|md)\d{3}_[A-Za-z0-9_-]+\.md$")

#: A closed set of known assistant slash-commands. Deliberately closed so that an
#: ordinary absolute path (``/etc/app``) is not mistaken for a tool-specific leak.
SLASH_COMMAND_RE = re.compile(
    r"(?:^|\s)/(read|ask|route|clear|compact|init|agents|model|review|commit|cost|"
    r"help|plan|think|resume|undo|redo|memory|mcp|doctor|config|status|context)"
    r"(?=\s|[.,;:!?)]|$)"
)
ASSISTANT_NAME_RE = re.compile(r"Claude Code|Cursor|ChatGPT|Copilot|Kimi|Qwen")

STATUS_MAX_LINES = 150
STATUS_MAX_ENTRIES = 5
STALE_DAYS = 14


# --- Helpers -----------------------------------------------------------------


def _read(path: Path, root: Optional[Path] = None) -> str:
    """Read a file as text, tolerating undecodable bytes.

    When *root* is given, a symlink resolving outside it yields "" rather than the
    external file's contents: otherwise a planted link would surface a file from
    anywhere on the machine in a ``--json`` report or an MCP tool result. The
    ``escaping_symlinks`` check reports the link itself.
    """
    if root is not None:
        try:
            if path.is_symlink() or path.exists():
                path.resolve().relative_to(Path(root).resolve())
        except ValueError:
            return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _escaping_symlinks(root: Path) -> List[str]:
    """Governance paths that are symlinks resolving outside the project.

    Scoped to what the checker actually reads — the core documents and ``docs/`` —
    rather than the whole tree. A virtualenv or ``node_modules`` is *full* of
    legitimate links to outside the project; flagging those would bury the one case
    that matters: a planted link that makes the tool read and report a file it was
    never pointed at.
    """
    candidates: List[Path] = [root / name for name in CORE_DOCS]
    docs = root / "docs"
    if docs.is_symlink():
        candidates.append(docs)
    elif docs.is_dir():
        candidates.extend(sorted(docs.rglob("*")))

    escaped: List[str] = []
    for path in candidates:
        if not path.is_symlink():
            continue
        try:
            path.resolve().relative_to(root)
        except ValueError:
            escaped.append(_rel(root, path))
    return escaped


def _check_no_escaping_symlinks(root: Path, report: Report) -> None:
    """A governance document must be a real file inside the project.

    A symlink pointing outside is either a mistake or an attempt to have the tool
    read or report on something it was never pointed at.
    """
    escaped = _escaping_symlinks(root)
    if escaped:
        report.add(
            "escaping_symlinks",
            Status.FAIL,
            "symlinks resolve outside the project and were not followed",
            details=escaped,
        )
    else:
        report.add("escaping_symlinks", Status.PASS, "no symlinks escape the project")


def _rel(root: Path, path: Path) -> str:
    """A repo-relative path, always with forward slashes.

    The ``path`` field is part of the ``--json`` contract, so it must not change
    shape between platforms — a consumer matching on ``docs/phase_plan.md`` would
    otherwise miss it on Windows.
    """
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def detect_profile(root: Path) -> Tuple[Optional[str], bool]:
    """Return ``(profile, is_data_profile)`` from the charter's ``Profile:`` line.

    An absent or unparseable profile defaults to a data profile, which keeps every
    project created before profiles existed passing unchanged.

    An **unrecognised** value also defaults to a data profile — deliberately the
    strictest reading. Treating a typo as non-data would let ``Profile: data-sciece``
    silently drop the data-contract requirement, turning a misspelling into a way to
    weaken compliance. A separate check reports the unknown value as a failure.
    """
    charter = root / "PROJECT_CHARTER.md"
    if not charter.is_file():
        return None, True
    match = PROFILE_RE.search(_read(charter, root))
    if not match:
        return None, True
    profile = match.group(1)
    if profile not in KNOWN_PROFILES:
        return profile, True
    return profile, profile in DATA_PROFILES


#: Keys a real ``framework.json`` carries. Being recognised as the framework repo
#: *relaxes* checks, so the manifest has to prove itself rather than merely exist.
FRAMEWORK_MANIFEST_KEYS = frozenset(
    {"name", "version", "profiles", "required_files", "required_directories"}
)


def detect_framework_repo(root: Path) -> bool:
    """True when auditing ChartworkAI's own repo.

    Its product surface (templates, agent specs, prompts) legitimately contains
    placeholder tokens, and its ``templates/`` directory is not leftover scaffold.

    This is a *relaxation*, which makes it worth spoofing: an empty ``framework.json``
    beside an empty ``templates/`` used to be enough for a consumer project to
    suppress its own leftover-scaffold failures. So the manifest must actually parse,
    declare itself as this framework, and carry the keys the product ships — and the
    template directory must hold real templates.
    """
    manifest = root / "framework.json"
    if not manifest.is_file() or not (root / "templates").is_dir():
        return False

    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False

    if not isinstance(data, dict) or not FRAMEWORK_MANIFEST_KEYS.issubset(data):
        return False
    if str(data.get("name", "")).strip().lower() not in {"chartworkai", "chartwork"}:
        return False
    return any((root / "templates").glob("*.template.md"))


def _scaffold_dirs(root: Path) -> List[Path]:
    return sorted(p for p in root.glob("_framework_*") if p.is_dir())


def _is_pruned(root: Path, path: Path) -> bool:
    """True when *path* sits inside a directory excluded from placeholder scanning.

    Only *directory* components are considered — never the filename — and prune
    names are anchored at the project root, matching the shell reference. A file
    merely named ``_framework_notes.md``, or a nested ``docs/outputs/`` of real
    content, is therefore still scanned.
    """
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True

    directories = relative.parts[:-1]
    if not directories:
        return False

    head = directories[0]
    if head in PRUNE_DIR_NAMES:
        return True
    # DIVERGENCE-1: prune every bootstrap scaffold directory, not just the three
    # the shell hard-codes.
    if head.startswith("_framework_"):
        return True
    for index in range(len(directories)):
        if "/".join(directories[: index + 1]) in PRUNE_RELPATHS:
            return True
    return False


def _iter_scannable(root: Path, bases: List[Path]) -> List[Path]:
    files: List[Path] = []
    for base in bases:
        if base.is_file():
            if base.suffix in SCANNED_SUFFIXES:
                files.append(base)
            continue
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix not in SCANNED_SUFFIXES:
                continue
            if _is_pruned(root, path):
                continue
            files.append(path)
    return files


def _decision_files(root: Path) -> List[Path]:
    directory = root / "docs" / "decisions"
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.glob("*.md") if p.is_file() and p.name != "README.md")


# --- Individual checks -------------------------------------------------------


def _check_profile_is_known(root: Path, report: Report, profile: Optional[str]) -> None:
    """A charter profile outside the known set is a typo, and typos must not pass.

    Reported explicitly because the fail-safe in ``detect_profile`` would otherwise
    make a misspelling look like a stricter-than-usual project rather than a mistake.
    """
    if profile is None:
        report.add(
            "profile",
            Status.PASS,
            "no Profile declared; defaulting to data-science",
        )
        return
    if profile in KNOWN_PROFILES:
        report.add("profile", Status.PASS, f"profile: {profile}")
    else:
        report.add(
            "profile",
            Status.FAIL,
            f"unknown profile {profile!r} in PROJECT_CHARTER.md — expected one of "
            f"{', '.join(KNOWN_PROFILES)}. Treating it as a data profile until fixed.",
            path="PROJECT_CHARTER.md",
        )


def _check_required_files(root: Path, report: Report) -> None:
    for rel in REQUIRED_FILES:
        if (root / rel).is_file():
            report.add("required_file", Status.PASS, rel, path=rel)
        else:
            report.add("required_file", Status.FAIL, f"{rel} is missing", path=rel)


def _check_decisions_dir(root: Path, report: Report) -> None:
    if (root / "docs" / "decisions").is_dir():
        report.add("required_dir", Status.PASS, "docs/decisions/", path="docs/decisions")
    else:
        report.add("required_dir", Status.FAIL, "docs/decisions/ is missing", path="docs/decisions")

    readme = "docs/decisions/README.md"
    if (root / readme).is_file():
        report.add("required_file", Status.PASS, readme, path=readme)
    else:
        report.add("required_file", Status.FAIL, f"{readme} is missing", path=readme)

    if _decision_files(root):
        report.add(
            "seed_decision", Status.PASS, "docs/decisions contains at least one seed decision"
        )
    else:
        report.add(
            "seed_decision",
            Status.FAIL,
            "docs/decisions needs at least one seed decision besides README.md",
        )


def _check_handoffs(root: Path, report: Report) -> None:
    directory = root / "docs" / "handoffs"
    if directory.is_dir():
        report.add("required_dir", Status.PASS, "docs/handoffs/", path="docs/handoffs")
    else:
        report.add("required_dir", Status.FAIL, "docs/handoffs/ is missing", path="docs/handoffs")

    notes = [p for p in directory.glob("*.md")] if directory.is_dir() else []
    if (directory / "README.md").is_file() or notes:
        report.add(
            "handoff_present",
            Status.PASS,
            "docs/handoffs has README.md or at least one handoff note",
        )
    else:
        report.add(
            "handoff_present",
            Status.FAIL,
            "docs/handoffs needs README.md or at least one handoff note",
        )


def _check_domain(root: Path, report: Report) -> None:
    if (root / "docs" / "domain").is_dir():
        report.add("required_dir", Status.PASS, "docs/domain/", path="docs/domain")
    else:
        report.add("required_dir", Status.FAIL, "docs/domain/ is missing", path="docs/domain")

    readme = "docs/domain/README.md"
    if (root / readme).is_file():
        report.add("required_file", Status.PASS, readme, path=readme)
    else:
        report.add("required_file", Status.FAIL, f"{readme} is missing", path=readme)


def _check_data_contracts(root: Path, report: Report, is_data_profile: bool) -> None:
    if not is_data_profile:
        report.add(
            "data_contracts",
            Status.PASS,
            "Profile is non-data: docs/data/ contract triad not required (skipped)",
        )
        return
    for rel in DATA_CONTRACT_FILES:
        if (root / rel).is_file():
            report.add("required_file", Status.PASS, rel, path=rel)
        else:
            report.add("required_file", Status.FAIL, f"{rel} is missing", path=rel)


def _check_duplicate_h2(root: Path, report: Report) -> None:
    for rel in DUPLICATE_H2_TARGETS:
        path = root / rel
        if not path.is_file():
            continue
        seen: dict = {}
        for line in _read(path, root).splitlines():
            if line.startswith("## "):
                seen[line] = seen.get(line, 0) + 1
        duplicates = sorted(h for h, count in seen.items() if count > 1)
        if duplicates:
            report.add(
                "duplicate_h2",
                Status.FAIL,
                f"{rel} has duplicate H2 headings",
                path=rel,
                details=duplicates,
            )
        else:
            report.add("duplicate_h2", Status.PASS, f"{rel} has no duplicate H2 headings", path=rel)


def _check_placeholders(root: Path, report: Report, framework_repo: bool) -> None:
    if framework_repo:
        bases = [root / name for name in CORE_DOCS] + [root / "docs"]
    else:
        bases = [root]

    offenders: List[str] = []
    for path in _iter_scannable(root, bases):
        for number, line in enumerate(_read(path, root).splitlines(), start=1):
            if PLACEHOLDER_RE.search(line):
                offenders.append(f"{_rel(root, path)}:{number}:{line.strip()}")

    if offenders:
        report.add(
            "placeholders",
            Status.FAIL,
            "unresolved {{PLACEHOLDER}} tokens remain",
            details=offenders,
        )
    else:
        report.add(
            "placeholders",
            Status.PASS,
            "no unresolved {{PLACEHOLDER}} tokens in active docs/config",
        )


def _check_tasks_shape(root: Path, report: Report) -> None:
    path = root / "TASKS.md"
    if not path.is_file():
        return
    lines = _read(path, root).splitlines()

    count = sum(1 for line in lines if line.rstrip() == "## In Progress")
    if count == 1:
        report.add("tasks_shape", Status.PASS, "TASKS.md has exactly one In Progress section")
    else:
        report.add(
            "tasks_shape",
            Status.FAIL,
            f"TASKS.md must have exactly one In Progress section; found {count}",
            path="TASKS.md",
        )

    if any(line.lstrip().startswith("|") for line in lines):
        report.add(
            "tasks_shape",
            Status.FAIL,
            "TASKS.md uses Markdown table rows; use checkbox bullets instead",
            path="TASKS.md",
        )
    else:
        report.add(
            "tasks_shape",
            Status.PASS,
            "TASKS.md uses checkbox/bullet format instead of Markdown tables",
        )

    if any(re.match(r"^\s*- \[[ xX]\]", line) for line in lines):
        report.add("tasks_shape", Status.PASS, "TASKS.md contains checkbox bullets")
    else:
        report.add(
            "tasks_shape", Status.FAIL, "TASKS.md must contain checkbox bullets", path="TASKS.md"
        )


def _check_phase_matches_charter(root: Path, report: Report) -> None:
    plan = root / "docs" / "phase_plan.md"
    charter = root / "PROJECT_CHARTER.md"
    if not plan.is_file() or not charter.is_file():
        return

    match = CURRENT_PHASE_RE.search(_read(plan, root))
    if not match:
        report.add(
            "phase_sync",
            Status.FAIL,
            "docs/phase_plan.md does not declare a parseable current phase",
            path="docs/phase_plan.md",
        )
        return

    number = match.group(1)
    if re.search(rf"Phase\s*{number}(?:\D|$)", _read(charter, root)):
        report.add(
            "phase_sync",
            Status.PASS,
            "docs/phase_plan.md current phase appears in PROJECT_CHARTER.md",
        )
    else:
        report.add(
            "phase_sync",
            Status.FAIL,
            f"docs/phase_plan.md current phase Phase {number} is not found in PROJECT_CHARTER.md",
            path="docs/phase_plan.md",
        )


def _check_decisions_linked(root: Path, report: Report) -> None:
    charter = root / "PROJECT_CHARTER.md"
    if not charter.is_file() or not (root / "docs" / "decisions").is_dir():
        return

    decisions = _decision_files(root)
    if not decisions:
        report.add(
            "decisions_linked",
            Status.FAIL,
            "no decision files found to link from PROJECT_CHARTER.md",
        )
        return

    text = _read(charter, root)
    missing = [p.name for p in decisions if f"docs/decisions/{p.name}" not in text]
    if missing:
        for name in missing:
            report.add(
                "decisions_linked",
                Status.FAIL,
                f"decision file docs/decisions/{name} is not linked from PROJECT_CHARTER.md",
                path=f"docs/decisions/{name}",
            )
    else:
        report.add(
            "decisions_linked", Status.PASS, "all decision files are linked from PROJECT_CHARTER.md"
        )


def _check_living_doc_decay(root: Path, report: Report) -> None:
    plan = root / "docs" / "phase_plan.md"
    status = root / "STATUS.md"
    if not plan.is_file() or not status.is_file():
        return

    status_text = _read(status, root)
    plan_text = _read(plan, root)

    status_match = STATUS_DATE_RE.search(status_text)
    plan_match = LAST_UPDATED_RE.search(plan_text)
    if status_match and plan_match:
        status_date = status_match.group(1)
        plan_date = plan_match.group(1)
        if plan_date.replace("-", "") < status_date.replace("-", ""):
            report.add(
                "plan_staleness",
                Status.FAIL,
                f"docs/phase_plan.md is stale. Last updated ({plan_date}) is older than the "
                f"latest STATUS.md entry ({status_date}). Regenerate it.",
                path="docs/phase_plan.md",
            )
        else:
            report.add(
                "plan_staleness",
                Status.PASS,
                "docs/phase_plan.md is up to date relative to STATUS.md",
            )

    cutoff = time.time() - STALE_DAYS * 86400
    for path in (plan, status):
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if mtime < cutoff:
            report.add(
                "mtime_staleness",
                Status.WARN,
                f"{path.name} has not been updated in over {STALE_DAYS} days. "
                "Ensure it reflects active progress.",
                path=_rel(root, path),
            )

    line_count = len(status_text.splitlines())
    if line_count > STATUS_MAX_LINES:
        report.add(
            "status_bloat",
            Status.FAIL,
            f"STATUS.md has bloated to {line_count} lines (exceeds {STATUS_MAX_LINES} limit). "
            "Archive older updates to prevent decay.",
            path="STATUS.md",
        )
    else:
        report.add(
            "status_bloat",
            Status.PASS,
            f"STATUS.md line count is within limits ({line_count} lines)",
        )

    entries = sum(1 for line in status_text.splitlines() if line.startswith("## "))
    if entries > STATUS_MAX_ENTRIES:
        report.add(
            "status_entries",
            Status.WARN,
            f"STATUS.md contains {entries} entries. Consider archiving historical entries.",
            path="STATUS.md",
        )


def _check_decision_log_rules(root: Path, report: Report) -> None:
    if not (root / "docs" / "decisions").is_dir():
        return

    invalid = [p.name for p in _decision_files(root) if not DECISION_NAME_RE.match(p.name)]
    if invalid:
        for name in invalid:
            report.add(
                "decision_naming",
                Status.FAIL,
                f"decision file {name} does not match YYYYMMDD_<namespace>###_<title>.md "
                "(valid namespaces: DEC, DQ, SC, MD)",
                path=f"docs/decisions/{name}",
            )
    else:
        report.add(
            "decision_naming",
            Status.PASS,
            "all decision file names conform to namespace ID patterns (DEC, DQ, SC, MD)",
        )

    plan = root / "docs" / "phase_plan.md"
    if not plan.is_file():
        return
    match = CURRENT_PHASE_RE.search(_read(plan, root))
    if not match:
        return
    if int(match.group(1)) >= 3:
        count = len(_decision_files(root))
        if count < 3:
            report.add(
                "sparse_decisions",
                Status.WARN,
                f"Sparse decision log: only {count} decisions at Phase {match.group(1)}. "
                "Consider capturing more context.",
            )


def _check_leftover_scaffolds(root: Path, report: Report, framework_repo: bool) -> None:
    if framework_repo:
        return
    leftovers = _scaffold_dirs(root)
    if leftovers:
        for path in leftovers:
            report.add(
                "leftover_scaffold",
                Status.FAIL,
                f"Leftover framework scaffold directory found: {path.name}. Clean it up.",
                path=path.name,
            )
    else:
        report.add(
            "leftover_scaffold",
            Status.PASS,
            "no leftover _framework_* scaffold directories present",
        )


def _check_tool_leaks(root: Path, report: Report, framework_repo: bool) -> None:
    leaks = 0
    for rel in CORE_DOCS:
        path = root / rel
        if not path.is_file():
            continue
        lines = _read(path, root).splitlines()

        slash_hits = [
            f"{rel}:{number}:{line.strip()}"
            for number, line in enumerate(lines, start=1)
            if SLASH_COMMAND_RE.search(line)
        ]
        if slash_hits:
            report.add(
                "tool_leak",
                Status.FAIL,
                f"Tool-specific slash command leak in {rel}",
                path=rel,
                details=slash_hits,
            )
            leaks += 1

        # The framework's own docs must name assistants to document portability.
        if not framework_repo:
            name_hits = [
                f"{rel}:{number}:{line.strip()}"
                for number, line in enumerate(lines, start=1)
                if ASSISTANT_NAME_RE.search(line)
            ]
            if name_hits:
                report.add(
                    "tool_leak",
                    Status.FAIL,
                    f"Assistant name leak in {rel} (operating documents must stay "
                    "assistant-agnostic)",
                    path=rel,
                    details=name_hits,
                )
                leaks += 1

    if not leaks:
        report.add(
            "tool_leak",
            Status.PASS,
            "no tool-specific leaks or slash commands found in core operating docs",
        )


# --- Entry point -------------------------------------------------------------


def run_checks(project_root) -> Report:
    """Run every compliance check against *project_root* and return a Report."""
    root = Path(project_root).resolve()
    profile, is_data_profile = detect_profile(root)
    framework_repo = detect_framework_repo(root)

    report = Report(
        project_root=str(root),
        profile=profile,
        is_data_profile=is_data_profile,
        framework_repo=framework_repo,
    )

    _check_no_escaping_symlinks(root, report)
    _check_profile_is_known(root, report, profile)
    _check_required_files(root, report)
    _check_decisions_dir(root, report)
    _check_handoffs(root, report)
    _check_domain(root, report)
    _check_data_contracts(root, report, is_data_profile)

    _check_duplicate_h2(root, report)
    _check_placeholders(root, report, framework_repo)
    _check_tasks_shape(root, report)
    _check_phase_matches_charter(root, report)
    _check_decisions_linked(root, report)
    _check_living_doc_decay(root, report)
    _check_decision_log_rules(root, report)
    _check_leftover_scaffolds(root, report, framework_repo)
    _check_tool_leaks(root, report, framework_repo)

    return report
