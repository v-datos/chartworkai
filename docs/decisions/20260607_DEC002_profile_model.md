# DEC-002 — Adopt a profile / deliverable-type model; this project uses a non-data-science profile

**Date:** 2026-06-07
**Authority:** Framework Architect
**Status:** Decided

## Context

The cross-project audit (9 implementations, see `docs/domain/README.md`) shows the framework's drift is almost entirely one root cause: **data-science assumptions baked into the base** — a mandatory data-contract triad, "reproducibility = byte-identical rebuild from raw," and a "research report" deliverable shape. These broke or were reinvented in most non-data-science projects. Critically, the compliance *checker* is already ~90% agnostic (a Node/TS project passes 27/27); the bias lives in prose and in a few mandatory artifacts.

This very repo is the first test: it has no data pipeline, so the required `docs/data/` triad does not naturally apply.

## Ruling

1. Adopt a **profile / deliverable-type** model as the framework's core agnosticism mechanism. Initial closed set (each traces to ≥2 audited projects): `research-report`, `database`, `competition-ml`, `software-app`, `investigation`, `deployed-service`.
2. A profile determines: directory layout, which artifacts are **required**, the meaning of "reproducibility" (a per-profile verify command), and the default role roster.
3. **This project** uses a `methodology / software` (non-data-science) profile that does **not** require the data-contract triad.

## Rationale

Profiles convert the framework's hidden data-science assumptions into one explicit, swappable choice — the smallest change that makes the framework honestly agnostic without weakening the validated core.

## Implementation notes (interim, until Phase 1 ships profiles)

- The compliance checker still hard-requires `docs/data/{data_dictionary,lineage,watchlist}.md`. Until T-006 makes the triad profile-conditional, this project **repurposes** that layer honestly: `watchlist.md` becomes the framework **issue tracker** (FW-### items); `data_dictionary.md` and `lineage.md` are honest "N/A for this profile" stubs pointing here.
- Phase 1 tasks T-002 (profile model) and T-006 (profile-aware checker) make the triad optional for non-data profiles.

## Consequences per agent

- **Framework Architect:** owns the profile set and the per-profile reproducibility contract (T-002/T-003).
- **Template & Docs Engineer:** implements profiles in `framework.json` + the checker + templates (T-004/T-006).
- **Dogfood & Compliance QA:** newly discovered issue **FW-001** — the checker assumes a consumer layout and flags the framework's *own* `templates/`/`agents/`/`prompts/` placeholder tokens when run on the framework repo; logged in the watchlist, fixed in T-006.

## Related

- DEC-001 (self-host). Watchlist FW-001, FW-005 (reproducibility), FW-006 (profiles).
