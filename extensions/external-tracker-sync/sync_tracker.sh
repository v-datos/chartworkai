#!/usr/bin/env sh
set -eu
# Tracker-agnostic mirror of TASKS.md / STATUS.md to an external tracker.
# Copy to your project's scripts/ and implement push_to_tracker() for your tracker
# (ClickUp / Linear / Notion / Jira / Asana / ...). The repo is the source of truth;
# this is a ONE-WAY (repo -> tracker) mirror. Never sync the other direction.
#
# Usage: scripts/sync_tracker.sh [PROJECT_ROOT]
# Token: export TRACKER_TOKEN in the environment (never commit it).

PROJECT_ROOT="${1:-.}"
TRACKER_TOKEN="${TRACKER_TOKEN:-}"        # set in the environment for real syncs
TRACKER_ENDPOINT="${TRACKER_ENDPOINT:-}"  # set to your tracker's API endpoint

tasks_file="$PROJECT_ROOT/TASKS.md"
status_file="$PROJECT_ROOT/STATUS.md"

# Implement this for your tracker. Receives a title and a body and should
# create/update the matching tracker item. Until implemented it is a safe no-op.
push_to_tracker() {
  title="$1"
  body="$2"
  if [ -z "$TRACKER_TOKEN" ] || [ -z "$TRACKER_ENDPOINT" ]; then
    printf 'WOULD SYNC (set TRACKER_TOKEN + TRACKER_ENDPOINT to enable): %s\n' "$title"
    return 0
  fi
  # Example (pseudo) — replace with your tracker's real API call:
  # curl -sf -H "Authorization: $TRACKER_TOKEN" -H 'Content-Type: application/json' \
  #   -d "$(printf '{"title":"%s","body":%s}' "$title" "$(printf '%s' "$body" | jq -Rs .)")" \
  #   "$TRACKER_ENDPOINT" >/dev/null
  printf 'SYNCED: %s\n' "$title"
}

[ -f "$status_file" ] || { echo "no STATUS.md at $PROJECT_ROOT" >&2; exit 1; }
[ -f "$tasks_file" ]  || { echo "no TASKS.md at $PROJECT_ROOT"  >&2; exit 1; }

# Mirror the current STATUS pulse (top entry) and the TASKS queue.
status_title="$(grep -m1 '^## ' "$status_file" | sed 's/^## //')"
push_to_tracker "STATUS: ${status_title:-update}" "$(cat "$status_file")"
push_to_tracker "TASKS" "$(cat "$tasks_file")"

printf 'Mirrored STATUS + TASKS from %s\n' "$PROJECT_ROOT"
