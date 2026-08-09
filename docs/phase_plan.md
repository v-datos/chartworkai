# Phase Plan — ChartworkAI: Productization

> ⚠️ **STOP — READ BEFORE EDITING.**
> 1. Read this entire file first. 2. Edit sections **in place** — never append a second copy of a section. 3. Hard cap: **200 lines**. 4. If a section is duplicated or this file exceeds the cap, prune to a single canonical form before adding anything.

**Last updated:** 2026-08-09
**Current phase:** Phase 4 — ChartworkAI package & launch
**Orchestrator note:** Phases 1–3 are complete and verified (see `docs/reproducibility/`). Phase 4 remains active. T-021 is in progress: the operator pack and evidence gate are being prepared before three external partner engagements.

## Active agents

| Agent | Status | Current task | Blocking on |
|---|---|---|---|
| Orchestrator | Active | Recruit and screen T-021 partners | Three external partners |
| Framework Architect | Standby | DEC-013 filed; available for scope questions | — |
| Integrations Engineer | Idle | T-018 closed | — |
| Docs & GTM Engineer | Idle | T-019 closed | — |
| Template & Docs Engineer | Idle | Available for assignment | — |
| Dogfood & Compliance QA | Active | Validate T-021 evidence gate | — |
| Audit & Research Analyst | Active | Review beta evidence design | — |

## Current phase exit criteria (Phase 4)

- [x] Scaffold-cleanup check (`_framework_*`) and tool-specific leak checker (T-011).
- [x] Project initialization script copies extensions and guides cleanup (T-011).
- [x] Repositioning and generalization to drop assistant-exclusive framing (T-012).
- [x] Product model and go-to-market strategy defined (DEC-004) (T-012).
- [x] ChartworkAI 0.1.0 published through staged OIDC after TestPyPI proof (T-020).
- [x] `framework.json` drives runtime, shell projections, and profile tables (T-016).
- [x] Generic initialization and project-owned custom profiles pass all gates (T-025).
- [x] ChartworkAI 0.2.0 published through staged OIDC after TestPyPI proof (T-026).
- [x] Public CrewAI governance adapter passes DEC-013 Amendment A, including the dependency embargo and hardened capture/write gates (T-018).
- [x] Docs site and landing page are published (T-019).
- [ ] Three external design partners complete measured installs (T-021).

## Dispatch queue

- T-021 — **In progress:** finalize the operator pack, then run three paid external engagements

## Open blockers

- Three external design partners have not yet been identified or scheduled.
- Outreach recipients or an owner-authorized recruitment channel are still required.

## Decision log (recent)

| ID | Date | Topic | Status | Authority |
|---|---|---|---|---|
| [DEC-014](decisions/20260809_DEC014_concierge_beta_terms.md) | 2026-08-09 | Set the T-021 concierge beta commercial terms | Decided | Orchestrator (with the user) |
| [DEC-013](decisions/20260807_DEC013_crewai_runtime_adapter.md) | 2026-08-07 | Establish the CrewAI runtime-adapter boundary and run-manifest contract | Decided | Framework Architect / Orchestrator (with the user) |
| [DEC-012](decisions/20260806_DEC012_generic_and_custom_profiles.md) | 2026-08-06 | Make presets optional and support custom profiles | Decided | Framework Architect / Dogfood & Compliance QA |
| [DEC-011](decisions/20260806_DEC011_authoritative_manifest.md) | 2026-08-06 | Make framework.json the executable contract | Decided | Framework Architect / Dogfood & Compliance QA |
| [DEC-010](decisions/20260806_DEC010_trusted_publishing.md) | 2026-08-06 | Publish through staged OIDC workflows | Decided | Orchestrator / Dogfood & Compliance QA |
| [DEC-009](decisions/20260805_DEC009_release_audit_remediation.md) | 2026-08-05 | Three pre-release audits gate the first publication | Decided | Orchestrator / Dogfood & Compliance QA |
| [DEC-008](decisions/20260805_DEC008_versioning_scheme.md) | 2026-08-05 | Version the framework and the package separately, with prefixed tags | Decided | Orchestrator |
| [DEC-007](decisions/20260804_DEC007_final_product_name.md) | 2026-08-04 | Final public name is ChartworkAI | Decided | Orchestrator (with the user) |
| [DEC-006](decisions/20260804_DEC006_apache_license.md) | 2026-08-04 | License the public core under Apache 2.0 | Decided | Orchestrator (with the user) |
| [DEC-005](decisions/20260804_DEC005_chartwork_rename.md) | 2026-08-04 | Rename to Chartwork; reposition as the governance layer; ship a Python package | Decided | Orchestrator (with the user) |
| [DEC-004](decisions/20260613_DEC004_product_model.md) | 2026-06-13 | Product model and go-to-market strategy | Decided | Orchestrator |
| [DEC-003](decisions/20260607_DEC003_phase1_profiles.md) | 2026-06-07 | Phase 1 direction: software-app first; build the profile system; package four extensions | Decided | Framework Architect / Orchestrator |
| [DEC-002](decisions/20260607_DEC002_profile_model.md) | 2026-06-07 | Adopt a profile / deliverable-type model; this project uses a non-data-science profile | Decided | Framework Architect |
| [DEC-001](decisions/20260607_DEC001_self_host.md) | 2026-06-07 | Self-host: manage the framework's productization with the framework | Decided | Orchestrator |

(For full history see `docs/decisions/`.)

## Completed phases

- **Phase 1 — Agnosticism core (2026-06-07):** profile/deliverable-type model + profile-aware checker (FW-001 resolved); de-Pythoned base templates + charter `## Stack` block; profile-aware bootstrap; Software/Deployment/Frontend optional roles; `PORTABILITY.md` (stack/assistant/locale). software-app proven; data profiles still gated. See `docs/reproducibility/phase_1.md`.
- **Phase 0 — Install & baseline (2026-06-07):** dogfood-installed; 9-project audit recorded; DEC-001/002/003; FW-001 found.
- **Pre-Phase-0 groundwork (2026-06-07):** four consistency fixes; framework v0.3.0.
