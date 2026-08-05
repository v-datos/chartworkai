# Data Dictionary — N/A for this profile

This project uses a **methodology / software** profile (see `docs/decisions/20260607_DEC002_profile_model.md`) and has **no tabular data layer**, so a column-level data dictionary does not apply.

This file is retained only because the current compliance checker hard-requires the `docs/data/` triad. Phase 1 task **T-006** makes the triad profile-conditional, after which this stub can be removed for non-data profiles.

The framework's true "artifact inventory" lives in `framework.json` (required files, templates, prompts, scripts). The framework's issue tracker is `docs/data/watchlist.md` (repurposed). This very stub is itself evidence for **FW-006** (the framework needs a profile model so non-data projects aren't forced to fabricate data contracts).
