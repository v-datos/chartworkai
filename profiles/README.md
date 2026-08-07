# Profiles (deliverable types)

A **profile** tailors the framework to what a project actually ships. Declare it in `PROJECT_CHARTER.md` with a line near the top:

```
**Profile:** software-app
```

The profile determines: which artifacts are **required** (notably whether the `docs/data/` contract triad is required), the meaning of **"reproducibility"** (a single project-defined *verify* command), the **default role roster**, and directory emphasis. The compliance checker reads the `Profile:` line; if absent it defaults to `data-science` (backward-compatible with every project created before profiles existed). An unrecognised value is rejected rather than silently accepted, because a typo would otherwise hand the project the wrong governance contract.

<!-- BEGIN GENERATED PROFILE TABLE -->
| Profile | Deliverable | Data contracts | "Reproducible" means |
|---|---|---|---|
| [`data-science`](data-science.md) | reproducible analysis / report | required | byte-identical rebuild from raw |
| [`software-app`](software-app.md) | running / deployable software | not required | build + tests pass |
| [`database`](database.md) | a curated dataset | required | deterministic rebuild + quality baselines |
| [`competition-ml`](competition-ml.md) | a scored submission | required | submission regenerates from a recorded run |
| [`investigation`](investigation.md) | evidence-backed findings | not required | every claim traces to an archived source at an evidence tier |
| [`deployed-service`](deployed-service.md) | a deployed service + infrastructure | not required | config + image digest + job URI trace a release |
<!-- END GENERATED PROFILE TABLE -->

The set is intentionally small and closed. New profiles are added by evidence, not speculation: each one above is drawn from real implementations, cited at the bottom of its spec. Five trace to two or more; `investigation` currently rests on one, which its spec says plainly.

Some profiles pair naturally with an optional module from [`extensions/`](../extensions/) — `competition-ml` with `experiment-log`, `investigation` with `claims-gate`. Those specs say so.
