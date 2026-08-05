# Project Charter — {{PROJECT_NAME}}

**Owner:** Orchestrator agent. Only the Orchestrator modifies this document.
**Status:** Living document — revised at every phase transition and whenever a Shared Convention or scope item changes.
**Last updated:** {{DATE}}
**Profile:** {{PROFILE}}  (see `profiles/README.md` for options)

---

## Stack

How this project is built and verified. The **verify command** is this project's definition of "reproducible" — its meaning varies by profile (see `profiles/`).

- **Language / runtime:** {{LANGUAGE_RUNTIME}}
- **Package / environment manager:** {{PACKAGE_MANAGER}}
- **Build command:** {{BUILD_COMMAND}}
- **Test command:** {{TEST_COMMAND}}
- **Verify command:** {{VERIFY_COMMAND}}

---

## 1. Mission

{{One-paragraph statement of what this project exists to do. Be specific about scope (what data / what audience / what time range) and about the kind of output (research report? product? decision support tool?). Avoid aspirational language; favor verifiable claims.}}

Numbered objectives, each verifiable:

1. {{Goal 1}}
2. {{Goal 2}}
3. {{Goal 3}}

State explicitly what optimization target this project does NOT have (e.g., "this is a research project, not a competition entry; speed and rubric coverage are not the targets — rigor and reproducibility are.").

## 2. Non-goals

The following are explicitly out of scope (revisit at phase transitions):

- {{Out-of-scope item 1, with one-line justification}}
- {{Out-of-scope item 2}}
- {{Out-of-scope item 3}}

## 3. Research / product questions

Tracked and refined through the project. Current set:

**{{Phase 2 theme}}:**
- Q1. {{question}}
- Q2. {{question}}

**{{Phase 3 theme}}:**
- Q3. {{question}}

**{{Phase 5 theme}}:**
- Q4. {{question}}

**{{Phase 6 theme}}:**
- Q5. {{question}}

## 4. Objectives (traceable to questions)

Each objective is owned by one or more agents and is marked done when its deliverables pass QA reproducibility.

| # | Objective | Owning agents | Deliverables | Status |
|---|---|---|---|---|
| O1 | {{Canonical processed data layer or equivalent}} | {{agents}} | {{paths}} | Not started |
| O2 | {{e.g., Descriptive baseline}} | {{agents}} | {{paths}} | Not started |
| O3 | {{...}} | {{agents}} | {{paths}} | Not started |
| O4 | {{...}} | {{agents}} | {{paths}} | Not started |
| O5 | {{Synthesis / report}} | {{agents}} | {{paths}} | Not started |
| O6 | End-to-end verification | QA / Reproducibility Engineer | the project's **verify command** (see `## Stack`) passes from a clean checkout | Not started |

## 5. Phases and milestones

Phases are gated on quality, not dates. Multiple phases can run in parallel after the foundation is stable.

**Phase 0 — Scoping & infrastructure.** Repo init, environment pinning, local verification command, directory structure, style guide, initial charter, AGENTS.md. Exit: infrastructure passes the verification smoke test.

**Phase 1 — {{Foundation phase}}.** {{What this builds — the substrate every other phase depends on.}} Exit: {{specific artifact} validates and reproduces.

**Phase 2 — {{e.g., Descriptive baseline}}.** {{Goal.}} Exit: {{specific sign-off}}.

**Phase 3 — {{...}}.** {{Goal.}} Exit: {{specific sign-off}}.

**Phase 4 — {{External integration / dependency phase if applicable}}.** {{Goal.}} Exit: {{...}}.

**Phase 5 — {{Attribution / advanced analysis}}.** {{Goal.}} Exit: {{...}}.

**Phase 6 — {{Forecasting / projection / generalization}}.** {{Goal.}} Exit: {{...}}.

**Phase 7 — Synthesis & deliverables.** {{Final report, dashboard, packaging.}} Exit: QA reproducibility check passes; all sections signed off.

Milestone dates are not set. Phase exits are gated on quality, not time.

## 6. Team

Roles defined in [`AGENTS.md`](AGENTS.md). At minimum:

- Orchestrator
- {{Domain Expert Title — e.g., Marine Ecologist, Clinical Lead, Product Manager}}
- {{Producer role — e.g., Data Engineer, Software Engineer}}
- {{Analyst role — e.g., Statistician, Researcher}}
- QA / Reproducibility Engineer

Optional: {{list optional roles in use, e.g., Geospatial Analyst, Causal Inference Specialist, Forecasting Specialist, External Data Specialist, Scientific Writer, Visualization Engineer}}.

Not every agent is active in every phase. The Orchestrator maintains the active-agent list in [`docs/phase_plan.md`](docs/phase_plan.md).

## 7. Success criteria

The project is considered successful when all of the following hold:

- Every research/product question in §3 has a documented answer or a documented reason it couldn't be answered, with sensitivity analyses for headline claims.
- `make reproduce` succeeds on a fresh clone, rebuilding all data, figures, and reports.
- {{Domain Expert}} has signed off on every claim in the final deliverable.
- {{Project-specific success criterion}}.
- {{Project-specific success criterion}}.

## 8. Decision log

Decisions that change Shared Conventions, scope, or phase gating are recorded here and in `docs/decisions/`. Format: one-liner here, full rationale in the decision file.

| Date | Decision | Owner | File |
|---|---|---|---|
| {{DATE}} | Project scoped per this charter v1 | Orchestrator | `docs/decisions/{{YYYYMMDD}}_charter_v1.md` |

## 9. Risks and mitigations

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| {{Risk 1}} | {{H/M/L}} | {{H/M/L}} | {{Plan}} | {{agent}} |
| {{Risk 2}} | {{H/M/L}} | {{H/M/L}} | {{Plan}} | {{agent}} |
| Reproducibility debt accumulates | Medium | High | QA runs milestone check; no phase closes with failing reproduce | QA / Reproducibility Engineer |
| Agent handoffs drift out of sync | Medium | Medium | Handoff-note discipline enforced by Orchestrator | Orchestrator |

## 10. Glossary

- **{{TERM_1}}** — {{definition}}
- **{{TERM_2}}** — {{definition}}
- **{{TERM_3}}** — {{definition}}

## 11. Change log

- **v1 ({{DATE}})** — Initial charter. {{N}} agent roles, {{N}} objectives, {{N}} phases, {{N}} questions.

---

*Pair with [`AGENTS.md`](AGENTS.md) (agent specifications) and [`docs/phase_plan.md`](docs/phase_plan.md) (current state).*
