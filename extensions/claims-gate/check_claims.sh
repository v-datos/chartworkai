#!/usr/bin/env sh
# POSIX-compliant verification script for the Claims Gate extension.
# Checks that all 'Promoted' claims meet the evidence tier requirements
# (Tier 1 or Tier 2) and have a valid source link/reference.
#
# Usage: scripts/check_claims.sh [claims_gate_file]

set -eu

claims_file="${1:-docs/investigation/claims_gate.md}"

if [ ! -f "$claims_file" ]; then
  printf 'Error: Claims file not found at: %s\n' "$claims_file" >&2
  exit 1
fi

printf 'Checking claims gate ledger: %s\n' "$claims_file"

failures=0
promoted_count=0
staged_count=0
demoted_count=0
total_count=0

# Read file line-by-line in a POSIX-compatible way
while IFS= read -r line || [ -n "$line" ]; do
  # Skip lines that are not table rows
  if ! printf '%s' "$line" | grep -q '^[[:space:]]*|'; then
    continue
  fi

  # Skip headers and dividers
  if printf '%s' "$line" | grep -qE '^[[:space:]]*\|[[:space:]]*-+'; then
    continue
  fi
  if printf '%s' "$line" | grep -qE '^[[:space:]]*\|[[:space:]]*ID[[:space:]]*\|'; then
    continue
  fi

  # Skip placeholder rows (contain {{...}} tokens)
  if printf '%s' "$line" | grep -q '{{'; then
    continue
  fi

  total_count=$((total_count + 1))

  # Extract columns by splitting on '|'
  # Columns: 1=empty, 2=ID, 3=Claim, 4=Source, 5=Tier, 6=Status, 7=Date
  id="$(printf '%s' "$line" | cut -d'|' -f2 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  claim="$(printf '%s' "$line" | cut -d'|' -f3 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  source="$(printf '%s' "$line" | cut -d'|' -f4 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  tier="$(printf '%s' "$line" | cut -d'|' -f5 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  status="$(printf '%s' "$line" | cut -d'|' -f6 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

  case "$status" in
    Promoted|promoted)
      promoted_count=$((promoted_count + 1))
      
      # Check evidence tier
      case "$tier" in
        "Tier 1"|"Tier 2"|"tier 1"|"tier 2")
          # Valid tier
          ;;
        *)
          printf 'FAIL: Promoted claim %s ("%s") must be Tier 1 or Tier 2. Found: %s\n' "$id" "$claim" "$tier" >&2
          failures=$((failures + 1))
          ;;
      esac

      # Check source link/reference
      if [ -z "$source" ] || [ "$source" = "Pending" ] || [ "$source" = "pending" ] || [ "$source" = "None" ] || [ "$source" = "none" ]; then
        printf 'FAIL: Promoted claim %s ("%s") lacks a valid source reference/link.\n' "$id" "$claim" >&2
        failures=$((failures + 1))
      fi
      ;;
    Staged|staged)
      staged_count=$((staged_count + 1))
      ;;
    Demoted|demoted)
      demoted_count=$((demoted_count + 1))
      ;;
    *)
      printf 'WARNING: Claim %s ("%s") has unrecognized status: %s\n' "$id" "$claim" "$status"
      ;;
  esac
done < "$claims_file"

printf '\nSummary:\n'
printf '  Total Claims: %d\n' "$total_count"
printf '  Promoted:     %d\n' "$promoted_count"
printf '  Staged:       %d\n' "$staged_count"
printf '  Demoted:      %d\n' "$demoted_count"
printf '  Violations:   %d\n' "$failures"

if [ "$failures" -gt 0 ]; then
  printf '\nClaims gate validation failed with %d violation(s).\n' "$failures" >&2
  exit 1
fi

printf '\nClaims gate validation passed.\n'
exit 0
