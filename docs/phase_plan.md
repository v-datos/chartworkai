# Phase Plan — ChartworkAI: Productization

> ⚠️ **STOP — READ BEFORE EDITING.**
> 1. Read this entire file first. 2. Edit sections **in place** — never append a second copy of a section. 3. Hard cap: **200 lines**. 4. If a section is duplicated or this file exceeds the cap, prune to a single canonical form before adding anything.

**Last updated:** 2026-08-07
**Current phase:** Phase 4 — ChartworkAI package & launch
**Orchestrator note:** Phases 1–3 are complete and verified (see `docs/reproducibility/`). Phase 4 ships the product as software: `chartworkai` 0.2.0 is live on PyPI, and framework contract 1.2.0 makes the generic core the initialization default while retaining six optional presets and adding bounded project-owned profiles. T-025 and its public package release T-026 are complete; next dispatch is the CrewAI adapter (T-018).

## Active agents

| Agent | Status | Current task | Blocking on |
|---|---|---|---|
| Orchestrator | Idle | Available for assignment | — |
| Framework Architect | Idle | Available for assignment | — |
| Template & Docs Engineer | Idle | Available for assignment | — |
| Dogfood & Compliance QA | Idle | Available for assignment | — |
| Audit & Research Analyst | Standby | Available for assignment | — |

## Current phase exit criteria (Phase 4)

- [x] Scaffold-cleanup check (`_framework_*`) and tool-specific leak checker (T-011).
- [x] Project initialization script copies extensions and guides cleanup (T-011).
- [x] Repositioning and generalization to drop assistant-exclusive framing (T-012).
- [x] Product model and go-to-market strategy defined (DEC-004) (T-012).
- [x] ChartworkAI 0.1.0 published through staged OIDC after TestPyPI proof (T-020).
- [x] `framework.json` drives runtime, shell projections, and profile tables (T-016).
- [x] Generic initialization and project-owned custom profiles pass all gates (T-025).
- [x] ChartworkAI 0.2.0 published through staged OIDC after TestPyPI proof (T-026).

## Dispatch queue (next up)

- T-018 — CrewAI adapter (`chartworkai export/ingest crewai`)
- T-019 — Docs site + landing page
- T-021 — Paid concierge beta with three design partners

## Open blockers

- None currently filed.

## Decision log (recent)

| ID | Date | Topic | Status | Authority |
|---|---|---|---|---|
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
