#!/usr/bin/env sh
# POSIX-compliant script to programmatically append runs to the Experiment Log.
#
# Usage:
#   scripts/log_run.sh \
#     --run-id "RUN-001" \
#     --model "ResNet50" \
#     --params "lr=1e-3, bs=32, epochs=10" \
#     --val-score "0.842 F1" \
#     --test-score "0.835 LB" \
#     --artifacts "[weights](file:///outputs/models/run_001.pt)" \
#     --notes "Baseline CNN run"

set -eu

log_file="docs/experiments/experiment_log.md"
run_id=""
model=""
params=""
val_score=""
test_score=""
commit=""
artifacts=""
notes=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --run-id) run_id="$2"; shift 2 ;;
    --model) model="$2"; shift 2 ;;
    --params) params="$2"; shift 2 ;;
    --val-score) val_score="$2"; shift 2 ;;
    --test-score) test_score="$2"; shift 2 ;;
    --commit) commit="$2"; shift 2 ;;
    --artifacts) artifacts="$2"; shift 2 ;;
    --notes) notes="$2"; shift 2 ;;
    --log-file) log_file="$2"; shift 2 ;;
    *) printf 'Error: Unknown option: %s\n' "$1" >&2; exit 1 ;;
  esac
done

if [ -z "$run_id" ]; then
  printf 'Error: --run-id is required\n' >&2
  exit 1
fi
if [ -z "$model" ]; then
  printf 'Error: --model is required\n' >&2
  exit 1
fi

if [ ! -f "$log_file" ]; then
  printf 'Error: Experiment log file not found at: %s\n' "$log_file" >&2
  exit 1
fi

# Get current date in YYYY-MM-DD
date_str="$(date +%Y-%m-%d)"

# Retrieve Git commit hash if not provided and in a Git repo
if [ -z "$commit" ]; then
  if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    commit="$(git rev-parse --short HEAD)"
  else
    commit="N/A"
  fi
fi

# Append formatted markdown table row to log file
row="| $run_id | $date_str | $model | $params | $commit | $val_score | $test_score | $artifacts | $notes |"
printf '%s\n' "$row" >> "$log_file"

printf 'Successfully logged run %s to %s\n' "$run_id" "$log_file"
