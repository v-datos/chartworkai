# Profile: competition-ml

**Deliverable:** a scored submission, plus the experiment log that explains how you got it. A leaderboard number nobody can reproduce is not a deliverable.
**Declare:** add `**Profile:** competition-ml` near the top of `PROJECT_CHARTER.md`.

## Required artifacts

Universal, **plus** the `docs/data/` contract triad. Competition data is given rather than built, so `data_dictionary.md` documents the *provided* schema and — more usefully — the leakage traps, target definition and split strategy you had to reason about.

Adopt the **`experiment-log` extension** (`extensions/experiment-log/`). It is effectively required here: the audit found every competition project rebuilt some version of a run tracker by hand.

## Reproducibility / verify

"Reproducible" = **the submitted artifact regenerates from a recorded run**. Declare a verify command in `## Stack` that reproduces the current best submission from a logged run id, with:

- **seeds fixed** and recorded per run,
- **the exact data split** recoverable, not re-randomised,
- **the score** attached to the run that produced it, local and leaderboard.

Where training happens in the cloud, byte-identical local rebuild is not achievable and pretending otherwise is worse than admitting it: record the **run/job URI, image digest and hyperparameters** instead, and make *that* the reproducibility claim. One audited project trained on GCP, which left `data/processed/` and a local rebuild structurally hollow.

## Default roles

Orchestrator · Domain Expert (owns the metric and what leakage looks like) · Data Engineer · Analyst / Modeller · QA / Reproducibility Engineer.

## Layout emphasis

`data/raw/` for the provided data (never edited), `src/` for features and models, `submissions/` for scored artifacts, `docs/experiments/experiment_log.md` for the run ledger. Notebooks are for exploration; anything used twice moves into `src/`.

## Watch for

Handoff notes collapse to zero on competition projects — the audit saw this repeatedly, because one person iterates alone and nothing crosses an agent boundary. That is fine: use the lightweight convention (a `Findings` line under the task in `TASKS.md`) within a phase, and write a real handoff only at phase close. The thing you must not skip is the experiment log, because "what did I change when the score jumped?" is unanswerable afterwards.

## Evidence

A Kaggle-style tabular competition entry, and a bird-audio classification competition whose training ran in the cloud — the case that showed a local rebuild is not always the honest reproducibility claim. See the cross-project audit in `docs/domain/README.md`.
