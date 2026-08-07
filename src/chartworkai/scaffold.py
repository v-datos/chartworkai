"""Bootstrapping a new project — the Python port of ``init_project_from_framework.sh``.

The generated documents are kept byte-identical to the shell scaffold so the two
implementations can be diffed against each other in CI. Where they must differ,
the difference is deliberate and noted here (currently: nothing).
"""

from __future__ import annotations

import datetime as _dt
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from chartworkai.assets import asset_root, template_path
from chartworkai.manifest import (
    DEFAULT_PROFILE,
    KNOWN_PROFILES,
    MANAGED_FILES,
    PROFILES,
    REFERENCE_DIRECTORIES,
    SCAFFOLD_DIRECTORIES,
    SCAFFOLD_SUPPORT_FILES,
    profile_scaffold_directories,
)
from chartworkai.profile_config import (
    effective_custom_profile,
    load_custom_profile,
    serialize_custom_profile,
)
from chartworkai.safety import (
    UnsafePathError,
    resolve_within,
    safe_copy,
    safe_mkdir,
    safe_write,
)

#: Everything init writes or replaces. All of it can represent real human work — a
#: curated decision index or domain note is no less someone's effort than the charter
#: — so init refuses when any of it already exists unless explicitly forced.
CANONICAL_DOCS = MANAGED_FILES
BASE_DIRS = SCAFFOLD_DIRECTORIES
DATA_DIRS = profile_scaffold_directories("data-science")
REFERENCE_DIRS = REFERENCE_DIRECTORIES
SHELL_SCRIPTS = SCAFFOLD_SUPPORT_FILES


def slugify(project_name: str) -> str:
    """Derive a machine-friendly slug, matching the shell implementation."""
    return re.sub(r"[^a-z0-9]+", "_", project_name.lower()).strip("_")


def _write(root: Path, relative: str, body: str) -> None:
    safe_write(root, relative, body)


def existing_canonical_docs(root: Path, today: Optional[_dt.date] = None) -> List[str]:
    """Everything in *root* that init would overwrite or delete.

    Includes the ``_framework_*`` reference directories, because refreshing one
    destroys whatever the user may have put inside it.
    """
    clashes = [relative for relative in CANONICAL_DOCS if (root / relative).exists()]

    # Date-stamped seeds and the copied helper scripts are generated names, so they
    # cannot live in a static list — but overwriting them is the same data loss.
    day = today or _dt.date.today()
    dynamic = [
        f"docs/decisions/{day:%Y%m%d}_DEC001_charter_v1.md",
        f"docs/handoffs/{day:%Y-%m-%d}_orchestrator.md",
    ]
    dynamic += [f"scripts/{Path(s).name}" for s in SHELL_SCRIPTS]
    clashes += [relative for relative in dynamic if (root / relative).exists()]

    clashes += sorted(p.name for p in root.glob("_framework_*") if p.is_dir() or p.is_symlink())
    return clashes


def init_project(
    target_dir,
    project_name: str,
    project_slug: Optional[str] = None,
    profile: str = DEFAULT_PROFILE,
    profile_file: Optional[Path] = None,
    today: Optional[_dt.date] = None,
    force: bool = False,
) -> Dict[str, Any]:
    """Create a project scaffold and return a summary of what was written.

    Refuses to clobber an existing governance layer unless *force* is set. Adding
    ChartworkAI to an existing repository is fine — only the canonical documents
    are protected, so a project with a README, source tree or git history
    initializes normally.

    Raises:
        ValueError: the profile or custom profile is invalid, or canonical documents exist and
            *force* is not set.
        NotADirectoryError: the target exists but is not a directory.
    """
    custom_definition = None
    if profile_file is not None:
        custom_definition = load_custom_profile(Path(profile_file))
        profile = custom_definition["name"]
        profile_spec = effective_custom_profile(custom_definition)
    else:
        if profile not in KNOWN_PROFILES:
            raise ValueError(
                f"unknown profile {profile!r}. Choose one of: {', '.join(KNOWN_PROFILES)}"
            )
        profile_spec = PROFILES[profile]

    root = Path(target_dir).resolve()
    if root.exists() and not root.is_dir():
        raise NotADirectoryError(f"target exists and is not a directory: {root}")

    if not force:
        clashes = existing_canonical_docs(root, today)
        if clashes:
            raise ValueError(
                "refusing to overwrite an existing governance layer in "
                f"{root} — found {', '.join(clashes)}. "
                "Re-run with --force to overwrite (this discards their contents)."
            )

    slug = project_slug or slugify(project_name)
    day = today or _dt.date.today()
    iso = f"{day:%Y-%m-%d}"
    stamp = f"{day:%Y%m%d}"
    is_data_profile = bool(profile_spec["requires_data_contracts"])

    directories: List[str] = list(BASE_DIRS) + list(profile_spec["scaffold_directories"])
    for relative in directories:
        safe_mkdir(root, relative)

    # Reference material the user prunes once the project is customized.
    source = asset_root()
    for name in REFERENCE_DIRS:
        destination = resolve_within(root, f"_framework_{name}")
        if destination.is_symlink():
            raise UnsafePathError(
                f"refusing to replace a symlinked reference directory: {destination}"
            )
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source / name, destination)

    # The shell scripts travel too, so a scaffolded project still verifies for
    # anyone who does not have the Python package installed.
    for relative in SHELL_SCRIPTS:
        script = source / relative
        if script.is_file():
            destination = safe_copy(root, f"scripts/{script.name}", script)
            destination.chmod(0o755)

    if custom_definition is not None:
        _write(root, "chartworkai.profile.json", serialize_custom_profile(custom_definition))

    _write(
        root,
        "PROJECT_CHARTER.md",
        _charter(project_name, profile, profile_spec, iso, stamp),
    )

    agents_template = (
        "templates/AGENTS.generic.template.md"
        if custom_definition is not None or profile == DEFAULT_PROFILE
        else "templates/AGENTS.template.md"
    )
    agents = template_path(agents_template).read_text(encoding="utf-8")
    agents = (
        agents.replace("{{PROJECT_NAME}}", project_name)
        .replace("{{PROJECT_SLUG}}", slug)
        .replace("{{DEFAULT_ROLE_LIST}}", ", ".join(profile_spec["default_roles"]))
    )
    _write(root, "AGENTS.md", agents)

    _write(root, "docs/phase_plan.md", _phase_plan(project_name, iso, stamp))
    _write(root, "STATUS.md", _status(project_name, iso))
    _write(root, "TASKS.md", _tasks(iso))
    _write(root, "docs/decisions/README.md", _decisions_readme())
    _write(root, f"docs/decisions/{stamp}_DEC001_charter_v1.md", _seed_decision(project_name, iso))
    _write(root, "docs/handoffs/README.md", _handoffs_readme())
    _write(root, f"docs/handoffs/{iso}_orchestrator.md", _seed_handoff(project_name, iso))
    _write(root, "docs/domain/README.md", _domain_readme(project_name))
    _write(root, "docs/style_guide.md", _style_guide(project_name))

    if is_data_profile:
        _write(root, "docs/data/data_dictionary.md", _data_dictionary(iso))
        _write(root, "docs/data/lineage.md", _lineage(iso))
        _write(root, "docs/data/watchlist.md", _watchlist(iso))

    return {
        "project_root": str(root),
        "project": project_name,
        "slug": slug,
        "profile": profile,
        "profile_kind": "custom"
        if custom_definition is not None
        else ("generic" if profile == DEFAULT_PROFILE else "preset"),
        "extends": custom_definition["extends"] if custom_definition is not None else None,
        "is_data_profile": is_data_profile,
        "validation_commands": list(profile_spec.get("validation_commands", [])),
        "reference_dirs": [f"_framework_{name}" for name in REFERENCE_DIRS],
    }


# --- Generated documents -----------------------------------------------------
# Each mirrors the corresponding heredoc in init_project_from_framework.sh.


def _charter(
    project_name: str,
    profile: str,
    profile_spec: Dict[str, Any],
    iso: str,
    stamp: str,
) -> str:
    validation_commands = list(profile_spec.get("validation_commands", []))
    verify_command = validation_commands[0] if validation_commands else "{{VERIFY_COMMAND}}"
    additional_validation = ""
    if len(validation_commands) > 1:
        rendered = "\n".join(f"  - `{command}`" for command in validation_commands[1:])
        additional_validation = f"\n- Additional validation commands:\n{rendered}"
    team = ", ".join(profile_spec["default_roles"])
    return f"""# Project Charter - {project_name}

Owner: Orchestrator agent
Status: Living document
Last updated: {iso}
Profile: {profile}

## Stack

How this project is built and verified. The verify command is this project's definition of "reproducible" (it varies by profile — see profiles/ in the framework).

- Language / runtime: {{{{LANGUAGE_RUNTIME}}}}
- Package / environment manager: {{{{PACKAGE_MANAGER}}}}
- Build command: {{{{BUILD_COMMAND}}}}
- Test command: {{{{TEST_COMMAND}}}}
- Verify command: {verify_command}{additional_validation}

## Mission

Initialize {project_name} as a multi-agent project with explicit scope, roles, decisions, handoffs, task tracking, and reproducibility expectations.

## Non-goals

- Do not begin implementation work until Phase 0 setup is reviewed.
- Do not let decisions live only in chat.
- Do not duplicate living-document sections.

## Questions

- Q1. What is the project trying to deliver?
- Q2. Which agents own the main workstreams?
- Q3. What artifacts prove each phase is complete?

## Phases

### Phase 0 - Initialization

Set up charter, agents, decisions, handoffs, domain notes, task tracking, and status cadence.

Exit criteria:

- Framework compliance check passes.
- First decision file exists.
- First handoff file exists.
- Orchestrator can propose the next dispatch from docs/phase_plan.md and TASKS.md.

### Phase 1 - First Deliverable

Produce the first project-specific deliverable under the agent workflow.

Exit criteria:

- Deliverable has a handoff note.
- Required validation command passes.
- STATUS.md and TASKS.md reflect the new state.

## Team

Roles are defined in AGENTS.md. Profile roles: {team}.

## Success Criteria

- Every major claim is traceable to an artifact, handoff, or decision.
- The current phase and task queue are unambiguous.
- Reproducibility checks are run before phase closure.

## Decision Log

| Date | Decision | Owner | File |
|---|---|---|---|
| {iso} | Project initialized from ChartworkAI | Orchestrator | docs/decisions/{stamp}_DEC001_charter_v1.md |

## Risks

| Risk | Impact | Mitigation | Owner |
|---|---|---|---|
| Scope remains too vague | High | Orchestrator updates this charter before dispatching specialists | Orchestrator |
| Agent outputs drift | Medium | Handoffs and TASKS.md are required for every deliverable | Orchestrator |
| Reproducibility is deferred | High | QA owns validation before phase close | QA / Reproducibility Engineer |

## Change Log

- {iso}: Initial framework scaffold created.
"""


def _phase_plan(project_name: str, iso: str, stamp: str) -> str:
    return f"""# Phase Plan - {project_name}

Last updated: {iso}
Current phase: Phase 0 - Initialization
Orchestrator note: Framework scaffold is installed; the next dispatch is to customize the charter and agent roster.

## Active Agents

| Agent | Status | Current task | Blocking on |
|---|---|---|---|
| Orchestrator | Active | Customize charter and first dispatch | Project brief |
| QA / Reproducibility Engineer | Waiting | Validate scaffold | Orchestrator updates |

## Current Phase Exit Criteria

- [ ] PROJECT_CHARTER.md is project-specific.
- [ ] AGENTS.md roles are customized.
- [ ] docs/phase_plan.md reflects the next dispatch.
- [ ] TASKS.md has a live queue.
- [ ] ./scripts/check_framework_compliance.sh passes.

## Recent Decisions

| Date | Decision | File |
|---|---|---|
| {iso} | Project initialized from ChartworkAI | docs/decisions/{stamp}_DEC001_charter_v1.md |

## Open Blockers

- Project-specific brief, domain, and first deliverable still need refinement.
"""


def _status(project_name: str, iso: str) -> str:
    return f"""# STATUS

## {iso} - Framework Initialization

Prepared by: Orchestrator

### Current Objective

Initialize {project_name} under ChartworkAI and prepare the first project-specific dispatch.

### Completed This Update

- Created canonical framework files.
- Seeded first decision.
- Seeded first handoff.
- Scaffolded operating docs (decisions, handoffs, domain).
- Ran framework compliance check.

### Open Risks

- Charter and agent roles still need project-specific customization.

### Next Sprint Priorities

- Customize PROJECT_CHARTER.md.
- Customize AGENTS.md.
- Replace generic data contracts with project-specific contracts.
"""


def _tasks(iso: str) -> str:
    return f"""# TASKS

Last updated: {iso}

## In Progress

- [ ] **T-001 - Customize charter and agent roster**
  Owner: Orchestrator
  Started: {iso}
  Inputs: PROJECT_CHARTER.md, AGENTS.md, project brief
  Expected output: Project-specific charter and agent roster
  Done criteria: PROJECT_CHARTER.md and AGENTS.md describe this project specifically
  Notes: First dispatch after bootstrap

## Queued

- [ ] **T-002 - Define first producer deliverable**
  Owner: Orchestrator
  Inputs needed: Project brief
  Done criteria: First specialist dispatch is ready
  Rationale: Unblocks execution

## Backlog

- [ ] **T-003 - Replace generic data contracts with project-specific contracts**
  Phase: Phase 0
  Owner: Producer
  Notes: Update docs/data/ after canonical artifacts are known.

## Done

- [x] **T-000 - Bootstrap project from framework**
  Owner: Orchestrator
  Completed: {iso}
  Handoff: docs/handoffs/{iso}_orchestrator.md

## Blockers

- No blockers currently filed.
"""


def _decisions_readme() -> str:
    return """# Decision Log

Create dated decision files here for choices that change scope, schema, interpretation, phase gates, or shared conventions.
"""


def _seed_decision(project_name: str, iso: str) -> str:
    return f"""# DEC-001 — Project Initialized from ChartworkAI

Date: {iso}
Authority: Orchestrator
Status: Decided

## Context

{project_name} needs durable multi-agent project structure before execution begins.

## Ruling

Use ChartworkAI as the operating model for this project.

## Rationale

The framework provides explicit chartering, agent ownership, decisions, handoffs, status, tasks, and data contracts.

## Implementation Notes

Use PROJECT_CHARTER.md, AGENTS.md, docs/phase_plan.md, STATUS.md, TASKS.md, docs/decisions/, docs/handoffs/, and docs/data/ as canonical operating artifacts.
"""


def _handoffs_readme() -> str:
    return """# Handoffs

Every completed deliverable gets a dated handoff note in this directory.
"""


def _seed_handoff(project_name: str, iso: str) -> str:
    return f"""# Handoff: Orchestrator - {iso}

## What was produced

- Framework scaffold for {project_name}.
- Seed decision and seed handoff.
- Initial phase plan, status, tasks, and data contract files.

## Known limitations

- Project-specific details still need to replace the generic bootstrap defaults.

## Next agent in chain

Orchestrator should customize the charter and agent roster before dispatching a specialist.
"""


def _domain_readme(project_name: str) -> str:
    return f"""# Domain Knowledge

Domain artifacts for {project_name}, maintained by the Domain Expert. Every
project records its domain meaning here in the repo, regardless of field.

Expected artifacts (create as the project needs them):

- groupings.md — categorical groupings / classifications used downstream.
- variable_definitions.md — canonical definition of every key variable or term.
- analytic_guidelines.md — rules for aggregation, edge cases, and interpretation.
"""


def _style_guide(project_name: str) -> str:
    return f"""# Style Guide - {project_name}

Optional but recommended. Delete this file if the project ships no shared style.

- Naming: file, artifact, and identifier conventions.
- Units and formats: canonical units, ISO 8601 dates, number formats.
- Code style: linter, formatter, type checker, line length.
- Visual style: colors, fonts, sizing (only if the project ships figures or UI).
- Decision-log convention: dated, authority-stamped files in docs/decisions/.
"""


def _data_dictionary(iso: str) -> str:
    return f"""# Data Dictionary

Last updated: {iso}

## Canonical Artifacts

No project-specific canonical artifacts have been defined yet.
"""


def _lineage(iso: str) -> str:
    return f"""# Lineage

Last updated: {iso}

## Source to Output Flow

Project-specific lineage has not been defined yet.
"""


def _watchlist(iso: str) -> str:
    return f"""# Watchlist

Last updated: {iso}

| ID | Status | Owner | Issue | Next action |
|---|---|---|---|---|
| W-001 | Open | Orchestrator | Project-specific data contracts are not defined | Customize docs/data/ |
"""
