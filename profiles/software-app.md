# Profile: software-app

**Deliverable:** running, deployable software — a web app, service, CLI, or library.
**Declare:** add `**Profile:** software-app` near the top of `PROJECT_CHARTER.md`.

## Required artifacts

Universal only: `PROJECT_CHARTER.md`, `AGENTS.md`, `docs/phase_plan.md`, `STATUS.md`, `TASKS.md`, `docs/decisions/README.md` + ≥1 seed decision, `docs/handoffs/README.md` (or a note), `docs/domain/README.md`. **The `docs/data/` contract triad is NOT required** — if the app has a data layer, document it in `docs/domain/` or a project-defined location.

## Reproducibility / verify

"Reproducible" = a single **verify command** builds the software and runs its automated tests green from a clean checkout — e.g. `make verify`, or `npm run build && npm test`, or the project's equivalent. Declare it in the charter `## Stack` block and in `AGENTS.md` Shared Conventions. There is no raw→processed data rebuild.

## Default roles

Orchestrator · Domain Expert (product / user owner) · Software Engineer (producer) · Frontend Engineer (if there is a UI) · Deployment Engineer (if it ships) · QA Engineer. Drop Frontend/Deployment when not applicable; add specialists as needed.

## Layout emphasis

The project's idiomatic source layout (e.g. `src/` for the language), `tests/`, and deployment config. No `data/raw → processed` pipeline is assumed.

## Evidence

A Node/TypeScript trip-planning web app containing no Python at all — the project that proved the checker was already language-agnostic — and a deployed geospatial detection service. See the cross-project audit in `docs/domain/README.md`.
