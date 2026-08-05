# DEC-006 — License the public core under Apache 2.0

**Date:** 2026-08-04
**Authority:** Orchestrator (with the user)
**Status:** Decided

## Context

DEC-004 set an open-core model: a free public core with paid profile and extension packs. The formal licence for that core was left open — an independent product review listed *"Which formal license supports the chosen open-core boundary?"* among the decisions still needed. An initial MIT licence was committed as a placeholder while the choice was pending.

Options considered:

- **MIT** — shortest and most permissive; no explicit patent grant, no trademark clause, no requirement to state modifications.
- **Apache License 2.0** — permissive with an **express patent grant and patent-retaliation clause**, an explicit **trademark reservation**, and a requirement that modified files be marked and any `NOTICE` be preserved. Chosen.
- Copyleft (GPL/AGPL) — rejected: it would prevent the commercial adoption the go-to-market depends on, since ChartworkAI is meant to be dropped into proprietary repositories.

## Ruling

License the public ChartworkAI core under the **Apache License, Version 2.0**, with a `NOTICE` file. Update `LICENSE`, `NOTICE`, `pyproject.toml` (`license = "Apache-2.0"` plus the OSI classifier), `README.md`, `CONTRIBUTING.md`, and `CHANGELOG.md` accordingly.

## Rationale

- **Patent grant.** Apache 2.0 grants contributors' patent rights to users and terminates that grant for anyone who initiates patent litigation. For a tool aimed at agencies and enterprise teams, this materially lowers legal-review friction — the exact audience DEC-004 targets. MIT is silent on patents, which enterprise counsel routinely flags.
- **Trademark reservation.** Apache 2.0 explicitly withholds trademark rights. That protects the "ChartworkAI" name while the code stays free, which is the boundary an open-core business needs: anyone may fork the code, nobody may ship a fork *as ChartworkAI*.
- **State-your-changes.** Requiring modified files to be marked supports the provenance ethic the product itself sells.
- **Ecosystem fit.** Apache 2.0 is the default for infrastructure and developer tooling and is on every corporate allow-list; it is not meaningfully harder to comply with than MIT for ordinary use.

The cost is a longer licence file and a small compliance obligation (retain `NOTICE`, mark changes). That is an acceptable trade for the patent and trademark protection.

## Implementation notes

- `LICENSE` is the verbatim Apache 2.0 text with the appendix copyright filled in as "Copyright 2026 ChartworkAI contributors".
- `NOTICE` records the copyright and the rename from the AI Workflow Framework.
- The paid profile and extension packs are **not** covered by this licence; they remain proprietary under DEC-004's open-core boundary.

## Consequences per agent

- **Release & Compliance Engineer:** ship `LICENSE` and `NOTICE` in the sdist and wheel; keep the PyPI classifier in sync.
- **Template & Docs Engineer:** no consumer-facing template carries a licence header; generated projects are the user's own work and are unlicensed by ChartworkAI.

## Revisited 2026-08-05 — reaffirmed against CrewAI's MIT

The choice was questioned on the grounds that CrewAI, the closest comparable project, is MIT-licensed. Reaffirmed, for two reasons the original ruling did not spell out:

1. **The categories differ.** MIT is the norm among agent *libraries* competing on frictionless adoption (CrewAI, LangChain, AutoGen). Apache 2.0 is the norm among *infrastructure and governance* tooling sold into enterprises (Kubernetes, Airflow, Kafka, Docker, OpenTelemetry, dbt). ChartworkAI is the second kind. Copying a competitor's licence would import a choice fitted to their product strategy, not ours.
2. **Trademark protection is now load-bearing.** DEC-007 established the name only after a clearance check ruled out a colliding alternative. Under MIT, nothing prevents a fork from shipping *as ChartworkAI*; Apache 2.0 §6 explicitly withholds trademark rights. Having paid the cost of picking a defensible name, giving away the protection would be incoherent.

The accepted costs are unchanged and small: a longer licence, the `NOTICE` obligation, and incompatibility with GPLv2 (GPLv3 is fine) — narrow for a standalone zero-dependency CLI that nobody vendors as a library.

No change to the ruling. Recorded so the question is not re-litigated from scratch.

## Related

- DEC-004 (open-core product model), DEC-005 (rename), DEC-007 (final name and clearance).
