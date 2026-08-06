#!/usr/bin/env sh
# POSIX-compliant script to programmatically generate or update docs/phase_plan.md
# based on the actual repository state.
#
# Usage: scripts/generate_phase_plan.sh [PROJECT_ROOT]

set -eu

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

PROJECT_ROOT="${1:-.}"

charter_file="$PROJECT_ROOT/PROJECT_CHARTER.md"
status_file="$PROJECT_ROOT/STATUS.md"
tasks_file="$PROJECT_ROOT/TASKS.md"
agents_file="$PROJECT_ROOT/AGENTS.md"
phase_plan_file="$PROJECT_ROOT/docs/phase_plan.md"
decisions_dir="$PROJECT_ROOT/docs/decisions"

if [ ! -f "$charter_file" ] || [ ! -f "$status_file" ] || [ ! -f "$tasks_file" ] || [ ! -f "$agents_file" ]; then
  printf 'Error: Missing core framework files in %s\n' "$PROJECT_ROOT" >&2
  exit 1
fi

# Python refuses a symlinked phase plan, and a symlinked docs/ carries the write out
# just as effectively. Check every component, so the two implementations agree.
assert_inside "$PROJECT_ROOT" "docs/phase_plan.md"

printf 'Generating phase plan for: %s\n' "$PROJECT_ROOT"

# 1. Project Name
proj_name="$(grep -m1 '^# Project Charter —' "$charter_file" | sed 's/^# Project Charter — //' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
if [ -z "$proj_name" ]; then
  proj_name="AI Workflow Framework Project"
fi

# 2. Date
current_date="$(date +%Y-%m-%d)"

# 3. Current Phase Num and Name
current_phase_num="$(grep -E '^## [0-9]{4}-[0-9]{2}-[0-9]{2} — Phase [0-9]+' "$status_file" | head -n 1 | sed -n 's/.*Phase \([0-9][0-9]*\).*/\1/p' || true)"
if [ -z "$current_phase_num" ]; then
  current_phase_num="1"
fi

phase_line="$(grep -E "Phase $current_phase_num —" "$charter_file" | head -n 1 || true)"
if [ -n "$phase_line" ]; then
  phase_title="$(printf '%s' "$phase_line" | sed -n 's/.*\*\*Phase [0-9][0-9]* — \([A-Za-z0-9_ -][A-Za-z0-9_ -]*\).*/\1/p' | sed 's/ (.*//' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
else
  phase_title="Active Phase"
fi

# 4. Orchestrator Note (preserve from existing phase_plan if present, otherwise default)
orch_note="Ready for routing."
if [ -f "$phase_plan_file" ]; then
  # Accept the note with or without bold markers: the scaffold seeds it unbolded.
  existing_note="$(grep -m1 'Orchestrator note:' "$phase_plan_file" | sed 's/^.*Orchestrator note:\**[[:space:]]*//' || true)"
  if [ -n "$existing_note" ]; then
    orch_note="$existing_note"
  fi
fi

# 5. Extract Active Assignments (Owner -> In Progress Task mapping from TASKS.md)
# Using awk to create a mapping of Owner -> Task
assignments="$(awk '
  BEGIN { in_progress = 0; current_task = ""; }
  /^## In Progress/ { in_progress = 1; next; }
  /^## / { in_progress = 0; }
  in_progress && /^- \[[^]]*\]/ { current_task = $0; next; }
  in_progress && /Owner:/ {
    sub(/^[[:space:]]*Owner:[[:space:]]*/, "", $0);
    owner = $0;
    sub(/[[:space:]]*$/, "", owner);
    # Strip checkboxes and markdown bold markers
    sub(/^- \[[^]]*\][[:space:]]*/, "", current_task);
    gsub(/\*\*/, "", current_task);
    print owner "|||" current_task;
  }
' "$tasks_file")"

# 6. Extract exit criteria from existing phase_plan and update them based on TASKS.md
exit_criteria=""
if [ -f "$phase_plan_file" ]; then
  # Extract criteria checkboxes
  raw_criteria="$(awk '
    BEGIN { in_criteria = 0; }
    /^## Current phase exit criteria/ { in_criteria = 1; next; }
    /^## / { in_criteria = 0; }
    in_criteria && /^- \[[^]]*\]/ { print; }
  ' "$phase_plan_file")"
  
  # Update checkboxes
  old_ifs="$IFS"
  IFS='
'
  for line in $raw_criteria; do
    # Extract task IDs mentioned in the exit criteria (e.g. T-008)
    task_ids="$(printf '%s' "$line" | grep -oE 'T-[0-9]{3}[a-z]?' || true)"
    
    all_done=1
    has_tasks=0
    for tid in $task_ids; do
      has_tasks=1
      # Check if this task is marked completed in TASKS.md
      if ! grep -q "\- \[x\] \*\*$tid" "$tasks_file"; then
        all_done=0
      fi
    done
    
    clean_line="$(printf '%s' "$line" | sed 's/^- \[[ x]\] //')"
    if [ "$has_tasks" -eq 1 ] && [ "$all_done" -eq 1 ]; then
      exit_criteria="$exit_criteria
- [x] $clean_line"
    else
      # If it has no task references, preserve its original state
      orig_state="$(printf '%s' "$line" | sed -n 's/^- \[\([ x]\)\].*/\1/p')"
      exit_criteria="$exit_criteria
- [$orig_state] $clean_line"
    fi
  done
  IFS="$old_ifs"
fi

if [ -z "$exit_criteria" ]; then
  exit_criteria="
- [ ] Define and implement deliverables.
- [ ] QA reproducibility report filed at docs/reproducibility/phase_$current_phase_num.md"
fi

# 7. Recent Decisions
decisions_rows=""
if [ -d "$decisions_dir" ]; then
  # Find and sort files by name (which starts with date) descending
  # Split on newlines only. Default word-splitting broke on any decision whose
  # filename contains a space: it was silently dropped from the log while the script
  # still exited 0. A `while read` pipeline would fix the splitting but run the body
  # in a subshell, losing decisions_rows entirely.
  dec_old_ifs="$IFS"
  IFS='
'
  for dec_file in $(find "$decisions_dir" -maxdepth 1 -type f -name '*.md' ! -name 'README.md' | sort -r); do
    filename="$(basename "$dec_file")"
    title="$(grep -m1 '^# ' "$dec_file" | sed 's/^# //' || true)"
    # Split on the em dash with sed, not cut: cut requires a single-byte delimiter
    # and fails with "bad delimiter" on the multibyte em dash.
    dec_id="$(printf '%s' "$title" | sed 's/—.*//; s/[[:space:]]*$//')"
    dec_topic="$(printf '%s' "$title" | sed 's/^[^—]*—[[:space:]]*//')"
    
    dec_date="$(grep -i '^\*\*Date:\*\*' "$dec_file" | sed 's/.*\*\*Date:\*\*[[:space:]]*//;s/\*//g' | head -n 1 || true)"
    dec_auth="$(grep -i '^\*\*Authority:\*\*' "$dec_file" | sed 's/.*\*\*Authority:\*\*[[:space:]]*//;s/\*//g' | head -n 1 || true)"
    dec_status="$(grep -i '^\*\*Status:\*\*' "$dec_file" | sed 's/.*\*\*Status:\*\*[[:space:]]*//;s/\*//g' | head -n 1 || true)"
    
    decisions_rows="$decisions_rows
| [$dec_id](decisions/$filename) | $dec_date | $dec_topic | $dec_status | $dec_auth |"
  done
  IFS="$dec_old_ifs"
fi

if [ -z "$decisions_rows" ]; then
  decisions_rows="
| - | - | No decisions filed yet | - | - |"
fi

# 8. Dispatch Queue (extract from TASKS.md Queued section)
queued_tasks="$(awk '
  BEGIN { in_queued = 0; }
  /^## Queued/ { in_queued = 1; next; }
  /^## / { in_queued = 0; }
  in_queued && /^- \[[^]]*\]/ {
    sub(/^- \[[^]]*\][[:space:]]*/, "");
    gsub(/\*\*/, "");
    print "- " $0;
  }
' "$tasks_file")"

if [ -z "$queued_tasks" ]; then
  queued_tasks="- None queued."
fi

# 9. Open Blockers (extract from TASKS.md or STATUS.md)
blockers="$(awk '
  BEGIN { in_blockers = 0; }
  /^## Blockers/ { in_blockers = 1; next; }
  /^## / { in_blockers = 0; }
  in_blockers && /^- / { print; }
' "$tasks_file" || true)"

if [ -z "$blockers" ]; then
  blockers="- None currently filed."
fi

# 10. Completed Phases (preserve from phase_plan or generate)
completed_phases=""
if [ -f "$phase_plan_file" ]; then
  completed_phases="$(awk '
    BEGIN { in_completed = 0; }
    /^## Completed phases/ { in_completed = 1; next; }
    /^## / { in_completed = 0; }
    in_completed && /^- / { print; }
  ' "$phase_plan_file" || true)"
fi

if [ -z "$completed_phases" ]; then
  completed_phases="- **Phase 0** — Scoping and install."
fi

# Assemble the new docs/phase_plan.md
tmp_plan="$(mktemp)"

cat << EOF > "$tmp_plan"
# Phase Plan — $proj_name

> ⚠️ **STOP — READ BEFORE EDITING.**
> 1. Read this entire file first. 2. Edit sections **in place** — never append a second copy of a section. 3. Hard cap: **200 lines**. 4. If a section is duplicated or this file exceeds the cap, prune to a single canonical form before adding anything.

**Last updated:** $current_date
**Current phase:** Phase $current_phase_num — $phase_title
**Orchestrator note:** $orch_note

## Active agents

| Agent | Status | Current task | Blocking on |
|---|---|---|---|
EOF

# Write agents list
roles="$(grep -E '^## [0-9]+\. ' "$agents_file" | sed -E 's/^## [0-9]+\.[[:space:]]*//')"
old_ifs="$IFS"
IFS='
'
for role in $roles; do
  clean_role="$(printf '%s' "$role" | sed 's/ (optional)//g')"
  
  # Check if role has an assignment
  assignment_match="$(printf '%s\n' "$assignments" | grep "^$clean_role|||" || true)"
  if [ -n "$assignment_match" ]; then
    task_desc="$(printf '%s' "$assignment_match" | cut -d'|' -f4)"
    printf '| %s | Active | %s | — |\n' "$clean_role" "$task_desc" >> "$tmp_plan"
  else
    # Check if role is listed as standby/optional in AGENTS.md
    if printf '%s' "$role" | grep -q 'optional'; then
      printf '| %s | Standby | Available for assignment | — |\n' "$clean_role" >> "$tmp_plan"
    else
      printf '| %s | Idle | Available for assignment | — |\n' "$clean_role" >> "$tmp_plan"
    fi
  fi
done
IFS="$old_ifs"

cat << EOF >> "$tmp_plan"

## Current phase exit criteria (Phase $current_phase_num)
$exit_criteria

## Dispatch queue (next up)

$queued_tasks

## Open blockers

$blockers

## Decision log (recent)

| ID | Date | Topic | Status | Authority |
|---|---|---|---|---|$decisions_rows

(For full history see \`docs/decisions/\`.)

## Completed phases

$completed_phases
EOF

# Move temp file to overwrite docs/phase_plan.md
mv "$tmp_plan" "$phase_plan_file"
printf 'Successfully generated %s\n' "$phase_plan_file"
