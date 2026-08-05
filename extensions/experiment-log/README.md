# Extension: experiment log (competition/ML profile)

Standardize and automate experiment tracking for competition or machine learning projects. This packages the run and score-tracking patterns that were rebuilt by hand in a Kaggle-style tabular competition and a bird-audio classification competition.

## Principles

- **Git-anchored reproducibility.** Every logged training run or experiment must be explicitly tied to a specific git commit hash and command.
- **Traceable artifacts.** Every row in the log references the exact location of its model weights, predictions, and submission files.
- **Metric comparison.** The ledger maintains side-by-side columns for local validation score and test/leaderboard score, helping track generalization and overfitting.
- **Automated logging.** To prevent manual updates from becoming stale or skipped, runs can be logged programmatically via a simple CLI script or a training hook.

## Adopt it

1. Copy `experiment_log.template.md` → `docs/experiments/experiment_log.md` (create the directory if needed).
2. Copy `log_run.sh` → your project's `scripts/` directory.
3. Call `scripts/log_run.sh` from the command line or embed it in your Python training/evaluation pipeline (e.g. via `subprocess` or a callback) at the end of a run.
4. Reference the best performing run's ID and commit hash when writing your handoff notes or updating `STATUS.md`.

## Files

- `experiment_log.template.md` — the markdown experiment table and schema template.
- `log_run.sh` — the CLI script to programmatically append runs to the log.
