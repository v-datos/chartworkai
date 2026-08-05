#!/usr/bin/env sh
set -eu

PROJECT_ROOT="${1:-.}"
# Physical path, used to decide whether a symlink leaves the project.
PROJECT_ABS="$(CDPATH= cd -P "$PROJECT_ROOT" 2>/dev/null && pwd)" || PROJECT_ABS=""

failures=0

# --- Profile awareness (deliverable type) -----------------------------------
# Data profiles require the docs/data/ contract triad; others do not.
# The profile is the first token after a "Profile:" line in PROJECT_CHARTER.md;
# if absent, default to data-science (backward-compatible).
DATA_PROFILE=1
PROFILE_KNOWN=1
charter_for_profile="$PROJECT_ROOT/PROJECT_CHARTER.md"
if [ -f "$charter_for_profile" ]; then
  project_profile="$(sed -n 's/.*Profile:[*[:space:]]*\([A-Za-z0-9_-][A-Za-z0-9_-]*\).*/\1/p' "$charter_for_profile" | head -n 1)"
  case "$project_profile" in
    data-science|database|competition-ml) DATA_PROFILE=1 ;;
    software-app|investigation|deployed-service) DATA_PROFILE=0 ;;
    "") DATA_PROFILE=1 ;;
    # An unrecognised value is a typo. Treat it as a data profile — the strictest
    # reading — so a misspelling cannot be used to drop the data-contract
    # requirement, and report it separately as a failure.
    *) DATA_PROFILE=1; PROFILE_KNOWN=0 ;;
  esac
fi

# Framework-repo self-detection: the framework's OWN repo legitimately contains
# {{...}} tokens across its product surface (templates/agents/prompts/examples and
# the docs that teach placeholders). Consumer projects have no root framework.json.
FRAMEWORK_REPO=0
if [ -f "$PROJECT_ROOT/framework.json" ] && [ -d "$PROJECT_ROOT/templates" ]; then
  FRAMEWORK_REPO=1
fi

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
  dir="docs/decisions"
  if [ ! -d "$PROJECT_ROOT/$dir" ]; then
    printf '0'
    return
  fi
  find "$PROJECT_ROOT/$dir" -maxdepth 1 -type f -name '*.md' ! -name 'README.md' | wc -l | tr -d ' '
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
    scan_targets=""
    for t in PROJECT_CHARTER.md AGENTS.md STATUS.md TASKS.md; do
      [ -f "$PROJECT_ROOT/$t" ] && scan_targets="$scan_targets $PROJECT_ROOT/$t"
    done
    [ -d "$PROJECT_ROOT/docs" ] && scan_targets="$scan_targets $PROJECT_ROOT/docs"
    matches="$(
      find $scan_targets \
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
  decision_dir="$PROJECT_ROOT/docs/decisions"
  if [ ! -f "$charter_file" ] || [ ! -d "$decision_dir" ]; then
    return
  fi

  found=0
  missing=0
  for file in "$decision_dir"/*.md; do
    [ -e "$file" ] || continue
    base="$(basename "$file")"
    [ "$base" = "README.md" ] && continue
    found=$((found + 1))
    if grep -q "docs/decisions/$base" "$charter_file"; then
      :
    else
      fail "decision file docs/decisions/$base is not linked from PROJECT_CHARTER.md"
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
  decision_dir="$PROJECT_ROOT/docs/decisions"
  plan_file="$PROJECT_ROOT/docs/phase_plan.md"
  
  if [ ! -d "$decision_dir" ]; then
    return
  fi
  
  # 1. Enforce ID namespace prefixing
  invalid_files=0
  for file in "$decision_dir"/*.md; do
    [ -e "$file" ] || continue
    base="$(basename "$file")"
    [ "$base" = "README.md" ] && continue
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
      decision_count="$(find "$decision_dir" -maxdepth 1 -type f -name '*.md' ! -name 'README.md' | wc -l | tr -d ' ')"
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

check_no_escaping_symlinks() {
  # A governance document must be a real file inside the project. A symlink pointing
  # outside is either a mistake or an attempt to have the tool read and report on a
  # file it was never pointed at. Mirrors the Python checker's escaping_symlinks.
  escaped=0
  if [ -n "$PROJECT_ABS" ]; then
    # Scoped to what the checker reads — core docs and docs/ — not the whole tree:
    # a virtualenv is full of legitimate links out, and flagging those would bury the
    # one case that matters.
    scan_targets="$PROJECT_ROOT/PROJECT_CHARTER.md $PROJECT_ROOT/AGENTS.md"
    scan_targets="$scan_targets $PROJECT_ROOT/STATUS.md $PROJECT_ROOT/TASKS.md"
    if [ -L "$PROJECT_ROOT/docs" ]; then
      scan_targets="$scan_targets $PROJECT_ROOT/docs"
      doc_links=""
    elif [ -d "$PROJECT_ROOT/docs" ]; then
      doc_links="$(find "$PROJECT_ROOT/docs" -type l 2>/dev/null)"
    else
      doc_links=""
    fi
    for link in $(printf '%s\n%s\n' "$scan_targets" "$doc_links"); do
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
    done
  fi
  if [ "$escaped" -eq 0 ]; then
    pass "no symlinks escape the project"
  fi
}

check_tool_leaks() {
  leaks=0
  for t in PROJECT_CHARTER.md AGENTS.md STATUS.md TASKS.md; do
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

if [ "$PROFILE_KNOWN" -eq 0 ]; then
  fail "unknown profile '$project_profile' in PROJECT_CHARTER.md — expected one of data-science, software-app, database, competition-ml, investigation, deployed-service. Treating it as a data profile until fixed."
else
  pass "profile is recognised"
fi

check_file "PROJECT_CHARTER.md"
check_file "AGENTS.md"
check_file "docs/phase_plan.md"
check_file "STATUS.md"
check_file "TASKS.md"

check_dir "docs/decisions"
check_file "docs/decisions/README.md"
decision_count="$(count_decision_files)"
if [ "$decision_count" -ge 1 ]; then
  pass "docs/decisions contains at least one seed decision"
else
  fail "docs/decisions needs at least one seed decision besides README.md"
fi

check_dir "docs/handoffs"
handoff_count="$(count_markdown_files "docs/handoffs")"
if [ -f "$PROJECT_ROOT/docs/handoffs/README.md" ] || [ "$handoff_count" -ge 1 ]; then
  pass "docs/handoffs has README.md or at least one handoff note"
else
  fail "docs/handoffs needs README.md or at least one handoff note"
fi

check_dir "docs/domain"
check_file "docs/domain/README.md"

if [ "$DATA_PROFILE" -eq 1 ]; then
  check_file "docs/data/data_dictionary.md"
  check_file "docs/data/lineage.md"
  check_file "docs/data/watchlist.md"
else
  info "Profile is non-data: docs/data/ contract triad not required (skipped)."
fi

info ""
info "Checking stronger operating rules"
check_duplicate_h2 "PROJECT_CHARTER.md"
check_duplicate_h2 "AGENTS.md"
check_duplicate_h2 "docs/phase_plan.md"
check_duplicate_h2 "STATUS.md"
check_duplicate_h2 "TASKS.md"
check_duplicate_h2 "docs/data/data_dictionary.md"
check_duplicate_h2 "docs/data/lineage.md"
check_duplicate_h2 "docs/data/watchlist.md"
check_no_placeholders
check_tasks_shape
check_phase_matches_charter
check_decisions_linked_from_charter
check_living_doc_decay
check_decision_log_rules
check_no_leftover_scaffolds
check_tool_leaks
check_no_escaping_symlinks

info ""
if [ "$failures" -eq 0 ]; then
  info "Framework installation check passed."
  exit 0
fi

info "Framework installation check failed with $failures issue(s)."
exit 1
