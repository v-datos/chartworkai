# Profile: database

**Deliverable:** a curated dataset that other people or systems depend on — the data *is* the product, not an input to a report.
**Declare:** add `**Profile:** database` near the top of `PROJECT_CHARTER.md`.

## Required artifacts

Universal, **plus** the `docs/data/` contract triad: `data_dictionary.md`, `lineage.md`, `watchlist.md`. This is the profile the triad was designed for. Consumers cannot see your build; the dictionary is the interface, lineage is how they judge whether a column means what they assume, and the watchlist is where known defects live instead of in someone's memory.

## Reproducibility / verify

"Reproducible" = a **deterministic rebuild that meets stated quality baselines**, not byte-identical output. Upstream sources change, so pinning bytes would make every refresh look like a regression. Declare a verify command in `## Stack` that rebuilds from raw and asserts:

- **row counts** within an expected band, per table,
- **primary keys unique** and not null,
- **referential integrity** across the tables you publish,
- **coverage** of the dimensions you promise (time range, regions, categories).

A refresh that breaks a baseline is a decision, not a silent update: record what changed upstream and what you did about it.

## Default roles

Orchestrator · Domain Expert (owns what a field *means*) · Data Engineer (producer) · QA / Reproducibility Engineer. Add **External Data Specialist** from `agents/_optional/` when you ingest third-party sources — every source needs a manifest recording its URL, licence, pull date and coverage, or you cannot answer "may we republish this?" later.

## Layout emphasis

`data/raw/` (immutable), `data/external/{source}/` with a manifest per source, `data/processed/` for what you publish, and `docs/data/` as the contract. Publishing artifacts (exports, dumps, API schemas) belong under `reports/` or a `dist/` of your choosing.

## Watch for

The audit found the decision log is most often neglected on database projects — the work feels mechanical, so schema and definition choices get made in commit messages rather than decisions. A year later nobody can say why a column was dropped. If your phase count is climbing and `docs/decisions/` is not, that is the drift to correct.

## Evidence

A curated national waste-to-energy dataset — the project where the contract triad fitted better than any other artifact the framework ships — and an investigative dataset built for publication. See the cross-project audit in `docs/domain/README.md`.
