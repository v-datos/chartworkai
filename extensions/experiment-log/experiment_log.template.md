# Experiment Log

Tracks model training runs, hyperparameters, validation performance, leaderboard scores, and resulting artifact locations.

## Ledger Schema

- **Run ID:** Unique identifier for the run (e.g., `RUN-001`).
- **Date:** Date of execution.
- **Model:** Model architecture or algorithm name.
- **Hyperparameters:** Key configuration details (learning rate, batch size, epochs, loss function, etc.).
- **Git Commit:** The 7-character commit hash representing the exact code used for the run.
- **Val Score:** Local validation metric (e.g. F1, RMSE, Accuracy) along with the split name.
- **Test Score:** Public leaderboard or test set score (leave empty if untested).
- **Artifacts:** Path to model weights and/or submission file.
- **Notes:** Brief description, findings, or observations from the run.

---

## Run Table

<!--
  GUIDE: Fill this table. You can use 'scripts/log_run.sh' to append rows programmatically.
-->

| Run ID | Date | Model | Hyperparameters | Git Commit | Val Score | Test Score | Artifacts | Notes |
|---|---|---|---|---|---|---|---|---|
| RUN-001 | {{2026-06-07}} | {{ResNet50}} | {{lr=1e-3, bs=32, epochs=10}} | {{a1b2c3d}} | {{0.842 F1}} | {{0.835 LB}} | [weights](file:///{{outputs/models/run_001.pt}}) | {{Baseline CNN run}} |
| RUN-002 | {{2026-06-07}} | {{ResNet50}} | {{lr=5e-4, bs=32, epochs=15}} | {{e5f6g7h}} | {{0.865 F1}} | {{0.858 LB}} | [weights](file:///{{outputs/models/run_002.pt}}) | {{Lower learning rate, more epochs; improved performance}} |
| RUN-003 | {{2026-06-08}} | {{EfficientNet-B0}} | {{lr=1e-3, bs=16, epochs=10}} | {{i9j0k1l}} | {{0.871 F1}} | {{0.862 LB}} | [weights](file:///{{outputs/models/run_003.pt}}) | {{Swapped backbone to EfficientNet; training is slower but scores improved}} |
