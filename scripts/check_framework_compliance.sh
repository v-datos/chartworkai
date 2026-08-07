#!/usr/bin/env sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if [ ! -f "$SCRIPT_DIR/framework_config.sh" ]; then
  printf 'error: generated framework configuration is missing: %s\n' \
    "$SCRIPT_DIR/framework_config.sh" >&2
  exit 1
fi
# shellcheck source=framework_config.sh
. "$SCRIPT_DIR/framework_config.sh"

case "${1:-}" in
  --self-audit|"") PROJECT_ROOT="." ;;
  *) PROJECT_ROOT="$1" ;;
esac
# Physical path, used to decide whether a symlink leaves the project.
PROJECT_ABS="$(CDPATH= cd -P "$PROJECT_ROOT" 2>/dev/null && pwd)" || PROJECT_ABS=""

failures=0

# --- Profile awareness (deliverable type) -----------------------------------
# Data profiles require the docs/data/ contract triad; others do not.
#
# Defaults only. The charter is NOT read here: reading it during setup happened
# before the symlink guard could run, so a charter symlinked outside the project had
# its Profile: value parsed and echoed in a failure message one line ahead of the
# link being rejected. Parsing is deferred to detect_profile_settings(), invoked
# after confinement passes.
DATA_PROFILE=1
PROFILE_KNOWN=1
project_profile=""
profile_rule="$CW_LEGACY_PROFILE"

# Framework identity is ASSERTED by the caller, never inferred from the audited
# tree. It relaxes the placeholder, scaffold and assistant-name checks, and any
# signal read out of the directory under audit can be reproduced inside it — the
# previous marker-based detection was spoofable by copying a manifest, and this
# implementation was the weaker of the two (it substring-matched raw text, so a
# non-JSON file containing the right words was enough).
#
#   scripts/check_framework_compliance.sh [PROJECT_ROOT] [--self-audit]
FRAMEWORK_REPO=0
for _arg in "$@"; do
  [ "$_arg" = "--self-audit" ] && FRAMEWORK_REPO=1
done

info() {
  printf '%s\n' "$1"
}

pass() {
  printf 'PASS %s\n' "$1"
}

fail() {
  printf 'FAIL %s\n' "$1"
  failures=$((failures + 1))
}

check_file() {
  path="$1"
  if [ -f "$PROJECT_ROOT/$path" ]; then
    pass "$path"
  else
    fail "$path is missing"
  fi
}

check_dir() {
  path="$1"
  if [ -d "$PROJECT_ROOT/$path" ]; then
    pass "$path/"
  else
    fail "$path/ is missing"
  fi
}

count_markdown_files() {
  dir="$1"
  if [ ! -d "$PROJECT_ROOT/$dir" ]; then
    printf '0'
    return
  fi
  find "$PROJECT_ROOT/$dir" -maxdepth 1 -type f -name '*.md' | wc -l | tr -d ' '
}

count_decision_files() {
  dir="$CW_DECISION_DIRECTORY"
  if [ ! -d "$PROJECT_ROOT/$dir" ]; then
    printf '0'
    return
  fi
  find "$PROJECT_ROOT/$dir" -maxdepth 1 -type f -name "$CW_DECISION_GLOB" ! -name "$CW_DECISION_EXCLUDE" | wc -l | tr -d ' '
}

check_duplicate_h2() {
  path="$1"
  file="$PROJECT_ROOT/$path"
  if [ ! -f "$file" ]; then
    return
  fi
  duplicate_headings="$(
    awk '/^## / { count[$0]++ } END { for (heading in count) if (count[heading] > 1) print heading }' "$file"
  )"
  if [ -z "$duplicate_headings" ]; then
    pass "$path has no duplicate H2 headings"
  else
    fail "$path has duplicate H2 headings: $(printf '%s' "$duplicate_headings" | tr '\n' ';')"
  fi
}

check_no_placeholders() {
  if [ "$FRAMEWORK_REPO" -eq 1 ]; then
    # Framework repo: scan only this project's own operating artifacts. Its product
    # surface (templates/agents/prompts/examples + placeholder-teaching docs) is excluded.
    # Positional parameters, not a space-joined string: an unquoted `find $targets`
    # splits on whitespace, so a project path containing a space made find search
    # nonexistent paths, print nothing, and the check report a false PASS.
    set --
    for t in $(cw_core_operating_files); do
      [ -f "$PROJECT_ROOT/$t" ] && set -- "$@" "$PROJECT_ROOT/$t"
    done
    [ -d "$PROJECT_ROOT/docs" ] && set -- "$@" "$PROJECT_ROOT/docs"
    if [ "$#" -eq 0 ]; then
      pass "no unresolved {{PLACEHOLDER}} tokens in active docs/config"
      return
    fi
    matches="$(
      find "$@" \
        -type f \( -name '*.md' -o -name '*.json' -o -name '*.yaml' -o -name '*.yml' \) \
        -exec grep -Hn '{{[^}][^}]*}}' {} \; 2>/dev/null || true
    )"
  else
    matches="$(
      find "$PROJECT_ROOT" \
        -path "$PROJECT_ROOT/.git" -prune -o \
        -path "$PROJECT_ROOT/.github" -prune -o \
        -path "$PROJECT_ROOT/.venv" -prune -o \
        -path "$PROJECT_ROOT/venv" -prune -o \
        -path "$PROJECT_ROOT/node_modules" -prune -o \
        -path "$PROJECT_ROOT/data/raw" -prune -o \
        -path "$PROJECT_ROOT/data/staging" -prune -o \
        -path "$PROJECT_ROOT/data/processed" -prune -o \
        -path "$PROJECT_ROOT/outputs" -prune -o \
        -path "$PROJECT_ROOT/_framework_templates" -prune -o \
        -path "$PROJECT_ROOT/_framework_agents" -prune -o \
        -path "$PROJECT_ROOT/_framework_prompts" -prune -o \
        -type f \( -name '*.md' -o -name '*.json' -o -name '*.yaml' -o -name '*.yml' \) \
        -exec grep -Hn '{{[^}][^}]*}}' {} \; 2>/dev/null || true
    )"
  fi
  if [ -z "$matches" ]; then
    pass "no unresolved {{PLACEHOLDER}} tokens in active docs/config"
  else
    fail "unresolved {{PLACEHOLDER}} tokens remain"
    printf '%s\n' "$matches"
  fi
}

check_tasks_shape() {
  path="$PROJECT_ROOT/TASKS.md"
  if [ ! -f "$path" ]; then
    return
  fi
  count="$(grep -c '^## In Progress$' "$path" || true)"
  if [ "$count" -eq 1 ]; then
    pass "TASKS.md has exactly one In Progress section"
  else
    fail "TASKS.md must have exactly one In Progress section; found $count"
  fi
  if grep -Eq '^[[:space:]]*\|' "$path"; then
    fail "TASKS.md uses Markdown table rows; use checkbox bullets instead"
  else
    pass "TASKS.md uses checkbox/bullet format instead of Markdown tables"
  fi
  if grep -Eq '^[[:space:]]*- \[[ xX]\]' "$path"; then
    pass "TASKS.md contains checkbox bullets"
  else
    fail "TASKS.md must contain checkbox bullets"
  fi
}

check_phase_matches_charter() {
  phase_file="$PROJECT_ROOT/docs/phase_plan.md"
  charter_file="$PROJECT_ROOT/PROJECT_CHARTER.md"
  if [ ! -f "$phase_file" ] || [ ! -f "$charter_file" ]; then
    return
  fi
  phase_number="$(
    sed -n 's/.*Current phase:.*Phase[[:space:]]*\([0-9][0-9]*\).*/\1/p' "$phase_file" | head -n 1
  )"
  if [ -z "$phase_number" ]; then
    fail "docs/phase_plan.md does not declare a parseable current phase"
    return
  fi
  if grep -Eq "Phase[[:space:]]*$phase_number([^0-9]|$)" "$charter_file"; then
    pass "docs/phase_plan.md current phase appears in PROJECT_CHARTER.md"
  else
    fail "docs/phase_plan.md current phase Phase $phase_number is not found in PROJECT_CHARTER.md"
  fi
}

check_decisions_linked_from_charter() {
  charter_file="$PROJECT_ROOT/PROJECT_CHARTER.md"
  decision_dir="$PROJECT_ROOT/$CW_DECISION_DIRECTORY"
  if [ ! -f "$charter_file" ] || [ ! -d "$decision_dir" ]; then
    return
  fi

  found=0
  missing=0
  for file in "$decision_dir"/*.md; do
    [ -e "$file" ] || continue
    base="$(basename "$file")"
    cw_decision_excluded "$base" && continue
    found=$((found + 1))
    if grep -q "$CW_DECISION_DIRECTORY/$base" "$charter_file"; then
      :
    else
      fail "decision file $CW_DECISION_DIRECTORY/$base is not linked from PROJECT_CHARTER.md"
      missing=$((missing + 1))
    fi
  done

  if [ "$found" -eq 0 ]; then
    fail "no decision files found to link from PROJECT_CHARTER.md"
  elif [ "$missing" -eq 0 ]; then
    pass "all decision files are linked from PROJECT_CHARTER.md"
  fi
}

check_living_doc_decay() {
  plan_file="$PROJECT_ROOT/docs/phase_plan.md"
  status_file="$PROJECT_ROOT/STATUS.md"
  
  if [ ! -f "$plan_file" ] || [ ! -f "$status_file" ]; then
    return
  fi
  
  # 1. Staleness check: compare Last updated in phase_plan.md with top date in STATUS.md
  status_date_raw="$(grep -m1 '^## ' "$status_file" | sed -n 's/## \([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}\) —.*/\1/p' || true)"
  plan_date_raw="$(grep -i 'Last updated:' "$plan_file" | sed -n 's/.*Last updated:[*[:space:]]*\([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}\).*/\1/p' || true)"
  
  if [ -n "$status_date_raw" ] && [ -n "$plan_date_raw" ]; then
    status_date_int="$(printf '%s' "$status_date_raw" | tr -d '-')"
    plan_date_int="$(printf '%s' "$plan_date_raw" | tr -d '-')"
    if [ "$plan_date_int" -lt "$status_date_int" ]; then
      fail "docs/phase_plan.md is stale. Last updated ($plan_date_raw) is older than latest STATUS.md entry ($status_date_raw). Run ./scripts/generate_phase_plan.sh to rebuild it."
    else
      pass "docs/phase_plan.md is up to date relative to STATUS.md"
    fi
  fi
  
  # 2. General 14-day staleness warn (modification time check)
  # POSIX find will output the path if modified > 14 days ago.
  for file in "$plan_file" "$status_file"; do
    if [ -f "$file" ]; then
      if [ -n "$(find "$file" -mtime +14 -print 2>/dev/null || true)" ]; then
        info "WARNING: $(basename "$file") has not been updated in over 14 days. Ensure it reflects active progress."
      fi
    fi
  done
  
  # 3. STATUS-bloat check
  status_lines="$(wc -l < "$status_file" | tr -d ' ')"
  if [ "$status_lines" -gt 150 ]; then
    fail "STATUS.md has bloated to $status_lines lines (exceeds 150 limit). Archive older weekly updates to prevent decay."
  else
    pass "STATUS.md line count is within limits ($status_lines lines)"
  fi
  
  status_entries="$(grep -c '^## ' "$status_file" || true)"
  if [ "$status_entries" -gt 5 ]; then
    info "WARNING: STATUS.md contains $status_entries entries. Consider archiving historical entries to keep it lightweight."
  fi
}

check_decision_log_rules() {
  decision_dir="$PROJECT_ROOT/$CW_DECISION_DIRECTORY"
  plan_file="$PROJECT_ROOT/docs/phase_plan.md"
  
  if [ ! -d "$decision_dir" ]; then
    return
  fi
  
  # 1. Enforce ID namespace prefixing
  invalid_files=0
  for file in "$decision_dir"/*.md; do
    [ -e "$file" ] || continue
    base="$(basename "$file")"
    cw_decision_excluded "$base" && continue
    # Patterns like 20260607_DEC003_phase1_profiles.md
    if ! printf '%s' "$base" | grep -Eq '^[0-9]{8}_(DEC|DQ|SC|MD|dec|dq|sc|md)[0-9]{3}_[a-zA-Z0-9_-]+\.md$'; then
      fail "decision file $base does not match pattern YYYYMMDD_<namespace>###_<title>.md (valid namespaces: DEC, DQ, SC, MD)"
      invalid_files=$((invalid_files + 1))
    fi
  done
  if [ "$invalid_files" -eq 0 ]; then
    pass "all decision file names conform to namespace ID patterns (DEC, DQ, SC, MD)"
  fi
  
  # 2. Sparse-decision warning: > 3 phases (i.e. phase >= 3) and < 3 decisions
  if [ -f "$plan_file" ]; then
    current_phase="$(sed -n 's/.*Current phase:.*Phase[[:space:]]*\([0-9][0-9]*\).*/\1/p' "$plan_file" | head -n 1 || true)"
    if [ -n "$current_phase" ] && [ "$current_phase" -ge 3 ]; then
      decision_count="$(count_decision_files)"
      if [ "$decision_count" -lt 3 ]; then
        info "WARNING: Sparse decision log. Found only $decision_count decisions for Phase $current_phase. Consider capturing more context."
      fi
    fi
  fi
}

check_no_leftover_scaffolds() {
  if [ "$FRAMEWORK_REPO" -eq 1 ]; then
    return
  fi
  
  found_scaffold=0
  for dir in "$PROJECT_ROOT"/_framework_*; do
    if [ -d "$dir" ]; then
      fail "Leftover framework scaffold directory found: $(basename "$dir"). Please clean it up to avoid clutter."
      found_scaffold=$((found_scaffold + 1))
    fi
  done
  if [ "$found_scaffold" -eq 0 ]; then
    pass "no leftover _framework_* scaffold directories present"
  fi
}

detect_profile_settings() {
  # Only ever called once confinement has passed, so this read cannot follow a link
  # out of the project. The profile is the first token after a "Profile:" line;
  # if absent, use the manifest's legacy profile (backward-compatible).
  charter_for_profile="$PROJECT_ROOT/PROJECT_CHARTER.md"
  [ -f "$charter_for_profile" ] || return 0
  project_profile="$(sed -n 's/.*Profile:[*[:space:]]*\([A-Za-z0-9_-][A-Za-z0-9_-]*\).*/\1/p' "$charter_for_profile" | head -n 1)"
  if [ -z "$project_profile" ]; then
    project_profile="$CW_LEGACY_PROFILE"
  elif ! cw_profile_known "$project_profile"; then
    DATA_PROFILE=1
    PROFILE_KNOWN=0
    profile_rule="$CW_STRICT_PROFILE"
    return
  fi
  profile_rule="$project_profile"
  if cw_profile_requires_data_contracts "$project_profile"; then
    DATA_PROFILE=1
  else
    DATA_PROFILE=0
  fi
}

check_no_escaping_symlinks() {
  # A governance document must be a real file inside the project. A symlink pointing
  # outside is either a mistake or an attempt to have the tool read and report on a
  # file it was never pointed at. Mirrors the Python checker's escaping_symlinks.
  #
  # This runs FIRST and aborts, before any check that reads or echoes file content.
  # Reporting the escape at the end was useless: by then `check_duplicate_h2` had
  # already printed headings read straight out of the external file.
  escaped=0
  if [ -n "$PROJECT_ABS" ]; then
    # Scoped to what the checker reads — core docs and docs/ — not the whole tree:
    # a virtualenv is full of legitimate links out, and flagging those would bury the
    # one case that matters.
    #
    # Newline-separated, iterated with `read`: word-splitting dropped any path
    # containing a space, which is exactly the path an attacker would choose.
    link_list="$(
      for core in $(cw_core_operating_files); do
        [ -L "$PROJECT_ROOT/$core" ] && printf '%s\n' "$PROJECT_ROOT/$core"
      done
      if [ -L "$PROJECT_ROOT/docs" ]; then
        printf '%s\n' "$PROJECT_ROOT/docs"
      elif [ -d "$PROJECT_ROOT/docs" ]; then
        find "$PROJECT_ROOT/docs" -type l 2>/dev/null
      fi
    )"
    while IFS= read -r link; do
      [ -n "$link" ] || continue
      [ -L "$link" ] || continue
      target="$(readlink "$link")"
      case "$target" in
        /*) abs_target="$target" ;;
        *)  abs_target="$(dirname "$link")/$target" ;;
      esac
      # A broken link resolves to nothing, so nothing is followed and nothing escapes.
      resolved_dir="$(CDPATH= cd -P "$(dirname "$abs_target")" 2>/dev/null && pwd)" || continue
      [ -n "$resolved_dir" ] || continue
      resolved="$resolved_dir/$(basename "$abs_target")"
      case "$resolved" in
        "$PROJECT_ABS"/*) ;;
        *)
          fail "symlink resolves outside the project and was not followed: ${link#"$PROJECT_ROOT"/} -> $resolved"
          escaped=$((escaped + 1))
          ;;
      esac
    done <<EOF
$link_list
EOF
  fi
  if [ "$escaped" -eq 0 ]; then
    pass "no symlinks escape the project"
  else
    # Stop here. Every later check reads these files, and several echo what they read.
    info ""
    info "Framework installation check failed with $failures issue(s)."
    exit 1
  fi
}

check_tool_leaks() {
  leaks=0
  for t in $(cw_core_operating_files); do
    file="$PROJECT_ROOT/$t"
    [ -f "$file" ] || continue
    
    # 1. Look for known tool-specific slash commands (a closed set, so absolute
    #    paths like /etc/app or /var/log do not false-positive as "leaks").
    matches_slash="$(grep -En '(^|[[:space:]])/(read|ask|route|clear|compact|init|agents|model|review|commit|cost|help|plan|think|resume|undo|redo|memory|mcp|doctor|config|status|context)([[:space:]]|[.,;:!?)]|$)' "$file" || true)"
    if [ -n "$matches_slash" ]; then
      fail "Tool-specific slash command leak in $t:"
      printf '%s\n' "$matches_slash"
      leaks=$((leaks + 1))
    fi
    
    # 2. Look for assistant name leaks in core operating files of consumer projects
    if [ "$FRAMEWORK_REPO" -eq 0 ]; then
      matches_names="$(grep -E -Hn 'Claude Code|Cursor|ChatGPT|Copilot|Kimi|Qwen' "$file" || true)"
      if [ -n "$matches_names" ]; then
        fail "Assistant name leak in $t (ensure operating documents remain assistant-agnostic):"
        printf '%s\n' "$matches_names"
        leaks=$((leaks + 1))
      fi
    fi
  done
  
  if [ "$leaks" -eq 0 ]; then
    pass "no tool-specific leaks or slash commands found in core operating docs"
  fi
}

info "Checking AI workflow framework installation in: $PROJECT_ROOT"
info ""

check_no_escaping_symlinks

# Safe to read the charter only now: the guard above exits on an escaping link.
detect_profile_settings

if [ "$PROFILE_KNOWN" -eq 0 ]; then
  if [ -f "$PROJECT_ROOT/$CW_CUSTOM_PROFILE_FILE" ]; then
    if command -v chartworkai >/dev/null 2>&1; then
      info "Custom profile detected; delegating to the Python checker."
      exec chartworkai check "$PROJECT_ROOT"
    fi
    fail "custom profile '$project_profile' requires the ChartworkAI Python package; run: chartworkai check '$PROJECT_ROOT'"
  else
    fail "unknown profile '$project_profile' in PROJECT_CHARTER.md — expected one of $CW_KNOWN_PROFILES or a valid $CW_CUSTOM_PROFILE_FILE. Treating it as a data profile until fixed."
  fi
else
  pass "profile is recognised"
fi

for required_file in $(cw_required_files) $(cw_profile_required_files "$profile_rule"); do
  check_file "$required_file"
done
for required_dir in $(cw_required_directories) $(cw_profile_required_directories "$profile_rule"); do
  check_dir "$required_dir"
done

decision_count="$(count_decision_files)"
if [ "$decision_count" -ge "$CW_DECISION_MINIMUM" ]; then
  pass "docs/decisions contains at least one seed decision"
else
  fail "docs/decisions needs at least one seed decision besides README.md"
fi

handoff_count="$(count_markdown_files "$CW_HANDOFF_DIRECTORY")"
if [ "$handoff_count" -ge "$CW_HANDOFF_MINIMUM" ]; then
  pass "docs/handoffs has README.md or at least one handoff note"
else
  fail "docs/handoffs needs README.md or at least one handoff note"
fi

if [ "$DATA_PROFILE" -eq 0 ]; then
  info "Profile is non-data: docs/data/ contract triad not required (skipped)."
fi

info ""
info "Checking stronger operating rules"
for living_document in $(cw_living_documents); do
  check_duplicate_h2 "$living_document"
done
check_no_placeholders
check_tasks_shape
check_phase_matches_charter
check_decisions_linked_from_charter
check_living_doc_decay
check_decision_log_rules
check_no_leftover_scaffolds
check_tool_leaks

info ""
if [ "$failures" -eq 0 ]; then
  info "Framework installation check passed."
  exit 0
fi

info "Framework installation check failed with $failures issue(s)."
exit 1
