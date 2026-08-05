# Prompt: Phase Roadmap — generate the phased plan

Use after PROJECT_CHARTER.md mission/questions are stable.

---

```
You are the Orchestrator. PROJECT_CHARTER.md is attached.

Your task is to produce a detailed phase roadmap to insert into
PROJECT_CHARTER.md §5 Phases and to seed docs/phase_plan.md.

For each phase, produce:

1. **Phase number and name** — short, descriptive (e.g., "Phase 1 — Data
   foundation").

2. **Goal** — one sentence stating what changes in the project state when this
   phase completes.

3. **Entry conditions** — what must be true for this phase to begin (which
   prior phases / artifacts must exist).

4. **Active agents** — which roles do the work of this phase.

5. **Key deliverables** — bullet list of file paths or artifacts produced.

6. **Exit criteria** — explicit, verifiable items. The phase closes when ALL
   are true. Always include a QA reproducibility check as the final criterion.

7. **Risks specific to this phase** — what could derail it.

Sequencing rules:
- Phase 0 is always: scoping & infrastructure (repo, env, local verification, docs).
- Phase 1 is always: foundation (the substrate every other phase depends on —
  for data projects this is the canonical processed layer).
- Late phases can run in parallel after the foundation is stable; flag
  parallelism explicitly.
- Final phase is always: synthesis & reproducibility — the closure that
  packages everything for delivery.

Constraints:
- 4–7 phases total. More than that becomes unmanageable.
- Exit criteria are quality gates, not dates. Do not include any milestone
  dates.
- Do not duplicate detail that belongs in agent specs — point to AGENTS.md
  by role name where appropriate.

Then produce a separate docs/phase_plan.md draft using
templates/phase_plan.template.md, populated for Phase 0 / Phase 1.

Output: two markdown blocks — one for the charter §5 update, one for
docs/phase_plan.md.
```
