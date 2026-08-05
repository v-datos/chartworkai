# Profile: data-science (default)

**Deliverable:** reproducible quantitative analysis — figures, tables, and a report or dashboard.
**Declare:** `**Profile:** data-science` (or omit the line — this is the default).

## Required artifacts

Universal **plus** the `docs/data/` contract triad: `data_dictionary.md`, `lineage.md`, `watchlist.md` (and the `docs/data/` directory).

## Reproducibility / verify

Byte-identical rebuild from raw: the verify command rebuilds processed data, regenerates figures, and runs tests using only `data/raw/` and `data/external/`.

## Default roles

Orchestrator · Domain Expert · Data Engineer · Analyst · QA / Reproducibility Engineer; optional specialists in `agents/_optional/`.

## Evidence

A marine-ecology research project, a national waste-to-energy dataset, and two motorsport analyses — see the cross-project audit in `docs/domain/README.md`. This is the framework's original shape, and the profile every other one was carved away from.
