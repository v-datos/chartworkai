# Profiles (deliverable types)

A **profile** tailors the framework to what a project actually ships. Declare it in `PROJECT_CHARTER.md` with a line near the top:

```
**Profile:** software-app
```

The profile determines: which artifacts are **required** (notably whether the `docs/data/` contract triad is required), the meaning of **"reproducibility"**, the **default role roster**, and directory emphasis. New scaffolds default to `generic`; projects created before profiles existed and still lacking a `Profile:` line retain the legacy `data-science` behavior. An unrecognised value requires a valid project-owned `chartworkai.profile.json`, otherwise it is rejected as a likely typo.

<!-- BEGIN GENERATED PROFILE TABLE -->
| Profile | Deliverable | Data contracts | "Reproducible" means |
|---|---|---|---|
| [`generic`](generic.md) | a project-defined deliverable | not required | the project-defined validation commands pass |
| [`data-science`](data-science.md) | reproducible analysis / report | required | byte-identical rebuild from raw |
| [`software-app`](software-app.md) | running / deployable software | not required | build + tests pass |
| [`database`](database.md) | a curated dataset | required | deterministic rebuild + quality baselines |
| [`competition-ml`](competition-ml.md) | a scored submission | required | submission regenerates from a recorded run |
| [`investigation`](investigation.md) | evidence-backed findings | not required | every claim traces to an archived source at an evidence tier |
| [`deployed-service`](deployed-service.md) | a deployed service + infrastructure | not required | config + image digest + job URI trace a release |
<!-- END GENERATED PROFILE TABLE -->

The six deliverable-specific presets are intentionally small and evidence-backed. They are accelerators, not the universe of supported projects. Use the `generic` core directly or initialize with `--profile-file` for a custom contract that extends `generic` or a preset. See [`../templates/custom_profile.template.json`](../templates/custom_profile.template.json).

Some profiles pair naturally with an optional module from [`extensions/`](../extensions/) — `competition-ml` with `experiment-log`, `investigation` with `claims-gate`. Those specs say so.
