# Project Charter — ChartworkAI: Productization

**Owner:** Orchestrator agent. Only the Orchestrator modifies this document.
**Status:** Living document — revised at every phase transition and whenever scope changes.
**Last updated:** 2026-06-13
**Profile:** software-app (this methodology/docs repo ships software — scripts, templates, the checker) — see `docs/decisions/20260607_DEC002_profile_model.md`

> This project **dogfoods the framework on itself**: the framework's own productization is run using the framework's charter / roles / decisions / handoffs / phases.

---

## Stack

- **Profile:** software-app — verification = the framework's own checks, not a data rebuild.
- **Language / runtime:** POSIX `sh` (scripts) + Markdown (templates/docs); no application runtime.
- **Package / environment manager:** none (zero runtime dependencies).
- **Build command:** none (the product is text + shell scripts).
- **Test command:** `sh -n scripts/*.sh` + a bootstrap smoke test into a temp dir.
- **Verify command:** `./scripts/check_framework_compliance.sh .` passes, the bootstrap smoke test behaves, and no tool-specific assumption leaked into a canonical doc.

---

## 1. Mission

Evolve the AI Workflow Framework from a validated-but-data-science-shaped internal methodology into a **project-agnostic, sellable product** that can run any complex, long-lived multi-agent project — across domains, tech stacks, languages, and AI assistants — without forcing data-science assumptions on its users.

Numbered objectives, each verifiable:

1. A non-data-science project (e.g. a web app) can be initialized and pass the compliance check **without inventing data contracts**.
2. "Reproducibility" has a documented, profile-specific meaning for at least four deliverable profiles.
3. The recurring real-world extensions (external-tracker sync, experiment log, claims gate, milestone reproducibility report, preregistered analysis plan, assistant primer) are available as optional, templated modules.
4. Living-document decay (stale or bloated `phase_plan.md` / `STATUS.md`) is caught automatically by the compliance checker.
5. The framework passes its own installation check (self-hosting), and its positioning is domain- and assistant-agnostic.
6. A documented product model and a credible path to a first sale.

This is a **framework-design and productization** project. "Rigor and reproducibility" here mean *the framework working across domains*, not statistical analysis.

## 2. Non-goals

- **Not** rewriting the validated core (charter / roles-as-contracts / decisions / handoffs). It is proven across 9 implementations and stays. Changes are additive.
- **Not** building hosted SaaS / billing in this engagement — the product *model* is decided; commerce implementation is out of scope.
- **Not** retrofitting the 9 audited projects to new conventions — they are evidence, not migration targets.
- **Not** adding domain analysis tooling (stats, geospatial, ML) to the core — those become optional profile/role packs, never base requirements.

## 3. Questions (grouped by phase)

**Phase 1 — Agnosticism:**
- Q1. What is the minimal "profile" abstraction that captures deliverable-type differences (directory layout, required artifacts, reproducibility meaning, default roles)?
- Q2. What does "verified / reproducible" mean per profile, and how is it expressed as a single command?

**Phase 2 — Productization:**
- Q3. Which recurring extensions are worth packaging first, and what is each one's minimal template?
- Q4. How do we stop living-document decay structurally rather than by exhortation?

**Phase 3 — Launch:**
- Q5. What is the product model (open-core / CLI installer / template marketplace) and the first target buyer?

## 4. Objectives (traceable to questions)

| # | Objective | Owning agents | Deliverables | Status |
|---|---|---|---|---|
| O1 | Profile / deliverable-type model | Framework Architect + Template & Docs Engineer | `profiles/` spec, `framework.json` schema, profile-aware checker | Done |
| O2 | Pluggable reproducibility | Framework Architect | per-profile verify contract + docs | Done |
| O3 | De-Pythoned, parameterized templates | Template & Docs Engineer | tokenized build/test/validate commands + charter `## Stack` block | Done |
| O4 | Packaged extension modules | Template & Docs Engineer | templates for the 6 recurring extensions | Done |
| O5 | Living-document decay controls | Dogfood & Compliance QA | generated `phase_plan`, staleness + bloat checks | Done |
| O6 | Self-hosting + agnostic positioning | Orchestrator + Template & Docs Engineer | framework passes own check; README repositioned | Done |
| O7 | Product model + go-to-market | Orchestrator (with user) | product-model decision + path to first sale | Done |

## 5. Phases and milestones

Phases are gated on quality, not dates.

**Phase 0 — Install & baseline.** Dogfood-install the framework on itself; capture the 9-project audit as domain knowledge; file the foundational decisions. The four consistency fixes already shipped (see Change log) are the Phase-0 groundwork. Exit: operating artifacts present; charter + roadmap + roster exist; audit findings recorded in `docs/domain/`; foundational decisions filed; the compliance checker has been run and its results triaged.

**Phase 1 — Agnosticism core (Tier 1: A–D).** Profile / deliverable-type model; pluggable reproducibility (extend `make verify`); de-Python prose + charter `## Stack` block; add software / deployment / frontend optional roles + an i18n / multi-assistant note; make the checker profile- and framework-layout-aware. Exit: a `software-app` profile installs and passes compliance with **no** data-contract triad; reproducibility documented for ≥4 profiles.

**Phase 2 — Productization (Tier 2: E–H).** Package the recurring extensions; structural living-doc fix (generate `phase_plan.md`, add staleness + bloat checks); decision-log hardening (ID namespaces + trigger heuristic); handoff resolution (TASKS "Findings" within a phase, formal handoff at phase close). Exit: each module templated + documented; decay checks active and self-passing.

**Phase 4 — ChartworkAI package & launch.** Ship the product as software: the `chartworkai` Python package (CLI + `--json`), release hygiene and CI, the remaining command ports (`init`, `plan`), a single authoritative schema, an MCP server so any assistant can drive it, runtime adapters (CrewAI first), a docs site, and publication to PyPI. Exit: `pip install chartworkai` works from PyPI, CI is green on supported platforms, and three external design partners have installed it.

**Phase 3 — Install UX & launch (Tier 3: I + GTM).** Scaffold-cleanup check (`_framework_*`); tool-specific-leak linter; a real installer; repositioning (drop origin-project framing; lead with multi-domain, multi-assistant, decision-governance); choose the product model. Exit: a stranger can initialize a non-DS project in one pass; positioning is agnostic; product model + first-sale path documented.

## 6. Team

Roles defined in `AGENTS.md`. Minimum active roles: Orchestrator, Framework Architect (the renamed Domain Expert), Template & Docs Engineer (the renamed Producer), Dogfood & Compliance QA (the renamed QA / Reproducibility role). Optional: Audit & Research Analyst.

## 7. Success criteria

- A web-app (non-data-science) project initializes and passes compliance with no fabricated data contracts.
- "Reproducibility" is documented as a profile-specific verification command for ≥4 profiles.
- The 6 recurring extensions exist as optional templated modules.
- `phase_plan.md` / `STATUS.md` decay is caught by the compliance checker.
- The framework passes its own installation check; README/positioning carry no domain- or assistant-specific framing.
- A product model and first-sale path are documented and agreed with the user.

## 8. Decision log

Decisions that change scope, conventions, or phase gating are recorded here and in `docs/decisions/`.

| Date | Decision | Owner | File |
|---|---|---|---|
| 2026-06-07 | Self-host: manage the framework's productization with the framework (dogfood) | Orchestrator | `docs/decisions/20260607_DEC001_self_host.md` |
| 2026-06-07 | Adopt a profile / deliverable-type model; this project uses a non-data-science profile | Framework Architect | `docs/decisions/20260607_DEC002_profile_model.md` |
| 2026-06-07 | Phase 1 direction: software-app first; build the profile system; package four extensions | Framework Architect / Orchestrator | `docs/decisions/20260607_DEC003_phase1_profiles.md` |
| 2026-06-13 | Product model and go-to-market strategy | Orchestrator | `docs/decisions/20260613_DEC004_product_model.md` |
| 2026-08-04 | Rename from AI Workflow Framework; reposition as the governance layer; ship a Python package | Orchestrator | `docs/decisions/20260804_DEC005_chartwork_rename.md` |
| 2026-08-04 | License the public core under Apache 2.0 | Orchestrator | `docs/decisions/20260804_DEC006_apache_license.md` |
| 2026-08-04 | Final public name is ChartworkAI (amends DEC-005) | Orchestrator | `docs/decisions/20260804_DEC007_final_product_name.md` |
| 2026-08-05 | Version framework and package separately, with prefixed tags | Orchestrator | `docs/decisions/20260805_DEC008_versioning_scheme.md` |
| 2026-08-05 | Three pre-release audits gate the first publication | Orchestrator / Dogfood & Compliance QA | `docs/decisions/20260805_DEC009_release_audit_remediation.md` |

## 9. Risks and mitigations

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| Scope creep: profiles balloon into many bespoke configs | High | High | Keep profiles a minimal closed set; each must trace to ≥2 audited projects | Framework Architect |
| Over-fitting to these 9 domains | Medium | Medium | Design profiles to be open/extensible; validate against a held-out domain | Framework Architect |
| Changes break the validated core or existing installs | Medium | High | Core stays additive; every change gated by Dogfood QA (bootstrap + compliance + example projects) | Dogfood & Compliance QA |
| Dogfooding decay (we stop using our own rituals) | Medium | Medium | No phase closes unless our own compliance check passes | Orchestrator |
| Productization distracts from a usable v1 | Medium | Medium | Tier 1 ships before Tier 2/3; each tier independently valuable | Orchestrator |

## 10. Glossary

- **Profile / deliverable-type** — a named configuration (research-report, database, competition-ml, software-app, investigation, deployed-service) that sets directory layout, required artifacts, the meaning of "reproducibility," and default roles.
- **Agnosticism** — the framework working across domains, stacks, languages, and AI assistants without data-science assumptions leaking in.
- **Dogfood / self-hosting** — using the framework to manage the framework's own development.
- **The audit set** — the 9 real implementations reviewed on 2026-06-07 that form this project's evidence base (see `docs/domain/README.md`).
- **Generic core vs DS-specific shell** — the validated, portable concepts (charter/roles/decisions/handoffs) vs the data-science defaults that must become optional.
- **Pluggable reproducibility** — replacing "byte-identical rebuild from raw" with a per-profile verification command.

## 11. Change log

- **v1 (2026-06-07)** — Initial charter. Follows the cross-project audit of 9 implementations and the four consistency fixes shipped the same day (CI → local `make verify`; bootstrap now instantiates the rich `AGENTS.md` with compliance as a graduation gate; the methodology's six "phases" renamed to "stages"; `docs/domain/` scaffolded + compliance-checked, `docs/weekly/` dropped, repro reports standardized to `phase_{N}.md`; framework bumped to v0.3.0). 4 roles, 7 objectives, 4 phases.
- **v1.1 (2026-06-07)** — Phase 0 closed; Phase 1 profile keystone shipped: profile/deliverable-type model (`framework.json` v0.4.0 + `profiles/`), profile-aware checker (FW-001 resolved), `software-app` proven (a non-data project passes with no data contracts). DEC-003 filed.
- **v1.2 (2026-06-13)** — Phase 2 closed: packaged all four extensions (external-tracker, claims-gate, experiment-log, assistant-primer), shipped `scripts/generate_phase_plan.sh` living-doc generator, added staleness and bloat compliance checks, and resolved handoff and decision-log prefix conventions.
- **v1.3 (2026-06-13)** — Phase 3 closed: generalized tool leaks, drafted open-core product model & go-to-market decision (DEC-004), verified compliance checks (including leftover framework folder check and leak checker), and finalized phase-3 reproducibility report.
- **v1.4 (2026-06-13)** — **Released as v1.0.0.** Productization (Phases 0–3) complete and independently verified; tightened the tool-leak slash-command check to a closed set of known assistant commands (no more absolute-path false-positives); bumped `framework.json` to 1.0.0; tagged the release.

## Open questions for the user

- **OQ1 — Product model:** open-core (free framework + paid profile packs / onboarding / support), a CLI installer + library, or a template marketplace? → **Answered (2026-06-13): Open-core model (free CLI bootstrap + base templates; paid premium profile packs & extensions) — DEC-004.**
- **OQ2 — Profile priority:** which profile to build first? (`software-app` looks highest-value from the audits; then `database`, `investigation`, `competition-ml`.) → **Answered (2026-06-07): software-app first — built and verified.**
- **OQ3 — Extension priority:** which packaged modules matter most to you? (claims-gate, experiment-log, external-tracker sync, assistant-primer, milestone-repro, preregistered-plan.) → **Answered (2026-06-07): external-tracker sync, claims gate, experiment log, assistant primer (Phase 2).**
- **OQ4 — Positioning / buyer:** who is the first target buyer (solo AI power-users, agencies, research labs, engineering teams)? → **Answered (2026-06-13): Solo AI power-users, agile agencies, and software development teams — DEC-004.**

---

*Pair with `AGENTS.md` (agent specifications) and `docs/phase_plan.md` (current state).*
