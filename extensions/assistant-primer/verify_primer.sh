#!/usr/bin/env sh
# POSIX-compliant verification script for the Assistant Primer extension.
# Cross-references the AI primer (.ai-primer.md) against PROJECT_CHARTER.md and
# AGENTS.md to verify that the profile, verify command, and active roles are in sync.
#
# Usage: scripts/verify_primer.sh [primer_file]

set -eu

primer_file="${1:-.ai-primer.md}"
charter_file="PROJECT_CHARTER.md"
agents_file="AGENTS.md"

if [ ! -f "$primer_file" ]; then
  printf 'Error: AI primer file not found at: %s\n' "$primer_file" >&2
  exit 1
fi

if [ ! -f "$charter_file" ]; then
  printf 'Error: PROJECT_CHARTER.md not found in the current directory.\n' >&2
  exit 1
fi

if [ ! -f "$agents_file" ]; then
  printf 'Error: AGENTS.md not found in the current directory.\n' >&2
  exit 1
fi

printf 'Verifying AI primer alignment: %s\n' "$primer_file"

failures=0

# 1. Verify Profile name alignment
charter_profile="$(sed -n 's/.*Profile:[*[:space:]]*\([A-Za-z0-9_-][A-Za-z0-9_-]*\).*/\1/p' "$charter_file" | head -n 1)"
if [ -n "$charter_profile" ]; then
  if grep -qi "$charter_profile" "$primer_file"; then
    printf 'PASS: Profile "%s" matches PROJECT_CHARTER.md\n' "$charter_profile"
  else
    printf 'FAIL: Profile "%s" declared in PROJECT_CHARTER.md is not mentioned in %s\n' "$charter_profile" "$primer_file" >&2
    failures=$((failures + 1))
  fi
else
  printf 'WARNING: Could not parse Profile from PROJECT_CHARTER.md\n'
fi

# 2. Verify Verify Command alignment
# Look for a line containing "verify command" in a list item or stack declaration
charter_verify="$(grep -i 'verify command' "$charter_file" | sed 's/.*verify command:[*[:space:]]*//i;s/`//g;s/^[[:space:]]*//;s/[[:space:]]*$//' | head -n 1)"
if [ -n "$charter_verify" ]; then
  # Grab the first token of the verify command to ensure it's referenced in the primer
  cmd_token="$(printf '%s' "$charter_verify" | awk '{print $1}')"
  if [ -n "$cmd_token" ] && grep -q "$cmd_token" "$primer_file"; then
    printf 'PASS: Verify command token "%s" matches PROJECT_CHARTER.md\n' "$cmd_token"
  else
    printf 'FAIL: Verify command "%s" from PROJECT_CHARTER.md is not mentioned in %s\n' "$charter_verify" "$primer_file" >&2
    failures=$((failures + 1))
  fi
else
  printf 'WARNING: Could not parse Verify command from PROJECT_CHARTER.md\n'
fi

# 3. Verify Agent Roster alignment
printf 'Checking agent roles...\n'
# Extract role names from AGENTS.md (lines starting with '## [0-9]+. ')
roles="$(grep -E '^## [0-9]+\. ' "$agents_file" | sed -E 's/^## [0-9]+\.[[:space:]]*//;s/[[:space:]]*$//')"

old_ifs="$IFS"
IFS='
'
for role in $roles; do
  # Remove optional notes from search token
  clean_role="$(printf '%s' "$role" | sed 's/ (optional)//g')"
  if grep -qi "$clean_role" "$primer_file"; then
    printf '  PASS: Role "%s" is rostered in the primer\n' "$clean_role"
  else
    printf '  FAIL: Role "%s" from AGENTS.md is missing from %s\n' "$clean_role" "$primer_file" >&2
    failures=$((failures + 1))
  fi
done
IFS="$old_ifs"

if [ "$failures" -gt 0 ]; then
  printf '\nAI primer verification failed with %d misalignment(s).\n' "$failures" >&2
  exit 1
fi

printf '\nAI primer verification passed.\n'
exit 0
