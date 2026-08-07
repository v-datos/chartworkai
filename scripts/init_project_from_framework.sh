#!/usr/bin/env sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
FRAMEWORK_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
if [ ! -f "$SCRIPT_DIR/framework_config.sh" ]; then
  printf 'error: generated framework configuration is missing: %s\n' \
    "$SCRIPT_DIR/framework_config.sh" >&2
  exit 1
fi
# shellcheck source=framework_config.sh
. "$SCRIPT_DIR/framework_config.sh"

# Refuse to write through a symlink at ANY component of a path under BASE.
# A top-level check is not enough: a symlinked docs/decisions/ carries a write out
# just as effectively, a *dangling* link makes the write create its external target,
# and --force follows a file symlink instead of replacing it. Mirrors the Python
# guard in src/chartworkai/safety.py.
#
# Usage: assert_inside BASE RELATIVE_PATH
assert_inside() {
  _prefix="$1"
  _old_ifs="$IFS"
  IFS='/'
  # shellcheck disable=SC2086
  set -- $2
  IFS="$_old_ifs"
  for _part in "$@"; do
    [ -n "$_part" ] || continue
    _prefix="$_prefix/$_part"
    if [ -L "$_prefix" ]; then
      printf 'error: refusing to write through a symlink: %s
' "$_prefix" >&2
      exit 1
    fi
  done
}

usage() {
  cat <<'USAGE'
Usage:
  scripts/init_project_from_framework.sh TARGET_DIR PROJECT_NAME [PROJECT_SLUG] [PROFILE] [--force]

Refuses to overwrite an existing governance layer unless --force is given.

Creates a minimal project scaffold from ChartworkAI. Run from the repository root.
PROFILE defaults to the framework manifest's default. Non-data profiles skip
profile-specific data contracts and layout.

Example:
  scripts/init_project_from_framework.sh ../my_app "My App" my_app software-app
USAGE
  printf 'Profiles: %s (default: %s)\n' "$CW_KNOWN_PROFILES" "$CW_DEFAULT_PROFILE"
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

FORCE=0
ARGS=""
for arg in "$@"; do
  if [ "$arg" = "--force" ]; then
    FORCE=1
  else
    ARGS="$ARGS
$arg"
  fi
done
# Rebuild the positional list without --force, tolerating spaces in values.
OLD_IFS="$IFS"; IFS='
'
set -- $(printf '%s' "$ARGS" | sed '/^$/d')
IFS="$OLD_IFS"

if [ "$#" -lt 2 ] || [ "$#" -gt 4 ]; then
  usage
  exit 2
fi

TARGET_DIR="$1"
PROJECT_NAME="$2"
PROJECT_SLUG="${3:-}"
PROFILE="${4:-$CW_DEFAULT_PROFILE}"

# An unrecognised profile is a typo, not an extension point: accepting one hands
# the project the wrong governance contract with no warning.
if ! cw_profile_known "$PROFILE"; then
  printf 'error: unknown profile %s. Choose one of: %s\n' \
    "$PROFILE" "$CW_KNOWN_PROFILES" >&2
  exit 1
fi

DATE_ISO="$(date +%Y-%m-%d)"
DATE_STAMP="$(date +%Y%m%d)"

# Never silently replace an existing governance layer. Adding ChartworkAI to a repo
# that already has other files is fine; only these documents are protected.
if [ "$FORCE" -eq 0 ] && [ -d "$TARGET_DIR" ]; then
  CLASHES=""
  for rel in $(cw_managed_files); do
    [ -e "$TARGET_DIR/$rel" ] && CLASHES="$CLASHES $rel"
  done
  for rel in "docs/decisions/${DATE_STAMP}_DEC001_charter_v1.md" \
             "docs/handoffs/${DATE_ISO}_orchestrator.md" \
             $(cw_scaffold_support_files); do
    [ -e "$TARGET_DIR/$rel" ] && CLASHES="$CLASHES $rel"
  done
  for dir in "$TARGET_DIR"/_framework_*; do
    [ -d "$dir" ] && CLASHES="$CLASHES $(basename "$dir")"
  done
  if [ -n "$CLASHES" ]; then
    printf 'error: refusing to overwrite an existing governance layer in %s — found:%s\n' \
      "$TARGET_DIR" "$CLASHES" >&2
    printf 'Re-run with --force to overwrite (this discards their contents).\n' >&2
    exit 1
  fi
fi

if [ -z "$PROJECT_SLUG" ]; then
  PROJECT_SLUG="$(printf '%s' "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9][^a-z0-9]*/_/g; s/^_//; s/_$//')"
fi

IS_DATA_PROFILE=0
if cw_profile_requires_data_contracts "$PROFILE"; then
  IS_DATA_PROFILE=1
fi

mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"

# Every directory this scaffold will build, checked component by component before
# anything is created.
ALL_SCAFFOLD_DIRS="$(cw_scaffold_directories
for _profile in $CW_KNOWN_PROFILES; do
  cw_profile_scaffold_directories "$_profile"
done)"
for guard in $ALL_SCAFFOLD_DIRS; do
  assert_inside "." "$guard"
done

for directory in $(cw_scaffold_directories) $(cw_profile_scaffold_directories "$PROFILE"); do
  mkdir -p "$directory"
done

# Remove first: `cp -R src dest` nests inside dest when it already exists, which
# under --force left stale files behind and broke parity with the Python entry point.
for ref in $(cw_reference_directories); do
  if [ -L "./_framework_$ref" ]; then
    printf 'error: refusing to replace a symlinked reference directory: _framework_%s\n' "$ref" >&2
    exit 1
  fi
  rm -rf "./_framework_$ref"
  cp -R "$FRAMEWORK_ROOT/$ref" "./_framework_$ref"
done
# Every file this scaffold writes. Checked here so --force cannot follow a symlink.
for guard in $(cw_managed_files) $(cw_scaffold_support_files) \
             "docs/decisions/${DATE_STAMP}_DEC001_charter_v1.md" \
             "docs/handoffs/${DATE_ISO}_orchestrator.md"; do
  assert_inside "." "$guard"
done

for support in $(cw_scaffold_support_files); do
  cp "$FRAMEWORK_ROOT/$support" "./scripts/$(basename "$support")"
  chmod +x "./scripts/$(basename "$support")"
done

cat > PROJECT_CHARTER.md <<EOF
# Project Charter - $PROJECT_NAME

Owner: Orchestrator agent
Status: Living document
Last updated: $DATE_ISO
Profile: $PROFILE

## Stack

How this project is built and verified. The verify command is this project's definition of "reproducible" (it varies by profile — see profiles/ in the framework).

- Language / runtime: {{LANGUAGE_RUNTIME}}
- Package / environment manager: {{PACKAGE_MANAGER}}
- Build command: {{BUILD_COMMAND}}
- Test command: {{TEST_COMMAND}}
- Verify command: {{VERIFY_COMMAND}}

## Mission

Initialize $PROJECT_NAME as a multi-agent project with explicit scope, roles, decisions, handoffs, task tracking, and reproducibility expectations.

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

Roles are defined in AGENTS.md. Minimum active roles are Orchestrator, Domain Expert, Producer, Analyst, and QA / Reproducibility Engineer.

## Success Criteria

- Every major claim is traceable to an artifact, handoff, or decision.
- The current phase and task queue are unambiguous.
- Reproducibility checks are run before phase closure.

## Decision Log

| Date | Decision | Owner | File |
|---|---|---|---|
| $DATE_ISO | Project initialized from ChartworkAI | Orchestrator | docs/decisions/${DATE_STAMP}_DEC001_charter_v1.md |

## Risks

| Risk | Impact | Mitigation | Owner |
|---|---|---|---|
| Scope remains too vague | High | Orchestrator updates this charter before dispatching specialists | Orchestrator |
| Agent outputs drift | Medium | Handoffs and TASKS.md are required for every deliverable | Orchestrator |
| Reproducibility is deferred | High | QA owns validation before phase close | QA / Reproducibility Engineer |

## Change Log

- $DATE_ISO: Initial framework scaffold created.
EOF

sed -e "s|{{PROJECT_NAME}}|$PROJECT_NAME|g" -e "s|{{PROJECT_SLUG}}|$PROJECT_SLUG|g" \
  "$FRAMEWORK_ROOT/templates/AGENTS.template.md" > AGENTS.md

cat > docs/phase_plan.md <<EOF
# Phase Plan - $PROJECT_NAME

Last updated: $DATE_ISO
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
| $DATE_ISO | Project initialized from ChartworkAI | docs/decisions/${DATE_STAMP}_DEC001_charter_v1.md |

## Open Blockers

- Project-specific brief, domain, and first deliverable still need refinement.
EOF

cat > STATUS.md <<EOF
# STATUS

## $DATE_ISO - Framework Initialization

Prepared by: Orchestrator

### Current Objective

Initialize $PROJECT_NAME under ChartworkAI and prepare the first project-specific dispatch.

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
EOF

cat > TASKS.md <<EOF
# TASKS

Last updated: $DATE_ISO

## In Progress

- [ ] **T-001 - Customize charter and agent roster**
  Owner: Orchestrator
  Started: $DATE_ISO
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
  Completed: $DATE_ISO
  Handoff: docs/handoffs/${DATE_ISO}_orchestrator.md

## Blockers

- No blockers currently filed.
EOF

cat > docs/decisions/README.md <<EOF
# Decision Log

Create dated decision files here for choices that change scope, schema, interpretation, phase gates, or shared conventions.
EOF

cat > docs/decisions/${DATE_STAMP}_DEC001_charter_v1.md <<EOF
# DEC-001 — Project Initialized from ChartworkAI

Date: $DATE_ISO
Authority: Orchestrator
Status: Decided

## Context

$PROJECT_NAME needs durable multi-agent project structure before execution begins.

## Ruling

Use ChartworkAI as the operating model for this project.

## Rationale

The framework provides explicit chartering, agent ownership, decisions, handoffs, status, tasks, and data contracts.

## Implementation Notes

Use PROJECT_CHARTER.md, AGENTS.md, docs/phase_plan.md, STATUS.md, TASKS.md, docs/decisions/, docs/handoffs/, and docs/data/ as canonical operating artifacts.
EOF

cat > docs/handoffs/README.md <<EOF
# Handoffs

Every completed deliverable gets a dated handoff note in this directory.
EOF

cat > docs/handoffs/${DATE_ISO}_orchestrator.md <<EOF
# Handoff: Orchestrator - $DATE_ISO

## What was produced

- Framework scaffold for $PROJECT_NAME.
- Seed decision and seed handoff.
- Initial phase plan, status, tasks, and data contract files.

## Known limitations

- Project-specific details still need to replace the generic bootstrap defaults.

## Next agent in chain

Orchestrator should customize the charter and agent roster before dispatching a specialist.
EOF

if [ "$IS_DATA_PROFILE" -eq 1 ]; then
cat > docs/data/data_dictionary.md <<EOF
# Data Dictionary

Last updated: $DATE_ISO

## Canonical Artifacts

No project-specific canonical artifacts have been defined yet.
EOF

cat > docs/data/lineage.md <<EOF
# Lineage

Last updated: $DATE_ISO

## Source to Output Flow

Project-specific lineage has not been defined yet.
EOF

cat > docs/data/watchlist.md <<EOF
# Watchlist

Last updated: $DATE_ISO

| ID | Status | Owner | Issue | Next action |
|---|---|---|---|---|
| W-001 | Open | Orchestrator | Project-specific data contracts are not defined | Customize docs/data/ |
EOF
fi

cat > docs/domain/README.md <<EOF
# Domain Knowledge

Domain artifacts for $PROJECT_NAME, maintained by the Domain Expert. Every
project records its domain meaning here in the repo, regardless of field.

Expected artifacts (create as the project needs them):

- groupings.md — categorical groupings / classifications used downstream.
- variable_definitions.md — canonical definition of every key variable or term.
- analytic_guidelines.md — rules for aggregation, edge cases, and interpretation.
EOF

cat > docs/style_guide.md <<EOF
# Style Guide - $PROJECT_NAME

Optional but recommended. Delete this file if the project ships no shared style.

- Naming: file, artifact, and identifier conventions.
- Units and formats: canonical units, ISO 8601 dates, number formats.
- Code style: linter, formatter, type checker, line length.
- Visual style: colors, fonts, sizing (only if the project ships figures or UI).
- Decision-log convention: dated, authority-stamped files in docs/decisions/.
EOF

printf '\nInitialized %s at %s\n\n' "$PROJECT_NAME" "$(pwd)"
printf 'Next steps:\n'
printf '  1. Fill every {{...}} placeholder in AGENTS.md and the charter ## Stack block, then customize PROJECT_CHARTER.md.\n'
printf '  2. Explore optional extensions in ./_framework_extensions/ (copy templates and scripts if adopted).\n'
printf '  3. Re-run ./scripts/check_framework_compliance.sh until it passes.\n'
printf '  4. Delete the temporary ./_framework_* folders once customization is complete.\n\n'
printf 'Compliance check now (unresolved {{...}} placeholders are EXPECTED until you customize):\n\n'
./scripts/check_framework_compliance.sh . || true
