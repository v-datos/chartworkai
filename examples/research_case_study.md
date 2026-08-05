# Worked Example: A Long-Running Research Project

ChartworkAI was extracted from the workflow of a **marine research project** — a multi-year analysis of roughly three decades of monitoring data, run over many sessions with an AI coding assistant. The project itself is private; what follows is the structure, because the structure is the transferable part.

Read it as a worked example when wiring up your own project: every section below is a framework artifact, shown as it actually looked in use rather than as a template.

---

## Charter — `PROJECT_CHARTER.md`

The charter named:

- **Mission**: 5 numbered goals (long-term trends, spatial separation, driver attribution, scenario forecasting, deliverables for decision-makers).
- **Non-goals**: explicitly excluded primary data collection, experiment design, finer-than-station modelling, global comparisons, and an unrelated integration that the original brief had attached. That last exclusion is the one that saved the most time.
- **10 research questions** in 4 phase-grouped buckets (descriptive, spatial, attribution, forecasting).
- **9 objectives** mapped to owning agents and deliverable file paths.
- **7 phases** (Phase 0 scoping → Phase 7 synthesis & deliverables), each with quality-gated exits.
- An **11-agent roster** detailed in `AGENTS.md`.

Written in week 1 and amended about three times across the project — each amendment recorded in the change log rather than made silently.

---

## Roster — `AGENTS.md`

Eleven roles. The framework's core five mapped as:

| Framework role | Project role |
|---|---|
| Orchestrator | Orchestrator |
| Domain Expert | **Marine Ecologist** |
| Producer | **Data Engineer** |
| Analyst | **Statistician** |
| QA / Reproducibility | QA / Reproducibility Engineer |

All six optional roles were activated — Geospatial Analyst, External Data Specialist, Causal Inference Specialist, Forecasting Specialist, Scientific Writer, Visualization Engineer — because this project genuinely needed each. **A simpler project would skip most of them**, and should.

Each role had a paste-ready System Prompt carrying project-specific context: the disease outbreak that reshaped the study system, the extreme-heat year, the major storm, and the nested site/station sampling design. That context had to be in the prompt because the agent needed it on every dispatch, not just the first.

---

## Decision log — `docs/decisions/`

Decisions were filed as `YYYYMMDD_DQ###_short_title.md`. Each carried:

- an **Authority** header (e.g. "Authority: Marine Ecologist"),
- a **Status** (Decided | Resolved | Open),
- **Context** with quantitative evidence — e.g. *"1,012 of 1,023 station-year rows show sum(species) ≠ Total"*,
- a **Ruling** in Option A/B/C form when alternatives were compared,
- **Rationale** written for the reader six months later,
- **Implementation notes** with code the producer could paste directly.

Thirteen data-quality decisions accumulated through Phases 0–2. Representative examples:

- **DQ-005** — count provenance: which source to trust when a summary column disagreed with the raw records.
- **DQ-009** — negative values in a derived metric: treated as a data anomaly and nulled, not silently clipped.
- **DQ-013** — total-column provenance, resolved as Option C: use per-species columns for species-level rows, and the field-computed total for community-level rows.

Three months in, *"why did we pick that definition for the total?"* was a one-file-read answer. That is the whole return on the practice.

---

## Data contracts — `docs/data/`

- `data_dictionary.md` — every column of 8 canonical tables, with type, units, source and the decisions that shaped it.
- `lineage.md` — raw column → processed column traceability.
- `watchlist.md` — the DQ-### tracker with severities and statuses.
- `raw_schemas.md` — schema stubs for the 12 raw source files.

The dictionary was updated on every schema change. It was the producer's responsibility and it never lagged, because a stale dictionary silently poisons every downstream agent.

---

## Phase plan — `docs/phase_plan.md`

Tracked current phase, active agents (Active / Idle / Waiting), the per-phase checklist, open blockers, the next five dispatches, risk flags and completed phases.

**Friction the framework now corrects:** this file grew duplicated "Phase N checklist" blocks across regenerations — the same checklist appended roughly eight times, in contradictory states. That single failure motivated the update-in-place rule, the 200-line cap, and the duplicate-heading check. It is now generated from repository state rather than hand-edited.

---

## Handoff notes — `docs/handoffs/`

Format `YYYY-MM-DD_{agent}.md`, each naming what was produced (with paths), where it lives, known limitations, and the next agent in the chain with a suggested dispatch ticket.

Sessions could end mid-work and resume cleanly the next day, because the handoff carried the state rather than the conversation.

---

## The execution loop in practice

A typical day:

1. **Session start** — read the phase plan and the last three handoffs; identify the next dispatch from the queue.
2. **Dispatch** — the Orchestrator (operator + assistant) instantiated the named agent with its System Prompt plus a ticket: inputs, outputs, done-criteria.
3. **Work** — the agent read the relevant charter excerpts, decisions and input artifacts, produced its output, and sometimes filed an open decision.
4. **Handoff** — the agent wrote its note; the Orchestrator updated the phase plan.
5. **Decisions** — any rulings filed the same day, watchlist updated.

Across roughly six weeks, those artifacts accumulated and stayed coherent. New sessions reconstructed prior state by reading files, with **no dependency on chat history** — which is the property the whole framework exists to produce.

---

## What the project got wrong (and the framework now mitigates)

1. **No lightweight weekly pulse.** A `docs/weekly/` directory was defined and stayed empty; the full phase-plan update was too heavy to do often. Hence `STATUS.md` — one screen, lighter than the plan, heavier than nothing.
2. **Dispatch-queue drift.** "Next five moves" lived inside the phase plan and went stale. Hence `TASKS.md` with explicit Queued / In Progress / Done sections.
3. **Manual "what's next?".** The operator repeatedly asked the assistant what to dispatch. Hence `prompts/04_orchestration_turn.md`, which answers from state.
4. **Interrupted long runs.** Work was lost when a long dispatch was cut off mid-flight. Still an open recommendation: checkpoint during long runs.
5. **Decision-closure lag.** A few open decisions lingered unresolved. Hence the closure check at session start in `SOP.md`.

---

## Artifact-to-template mapping

How the project's files map onto what ChartworkAI ships:

```
research_project/
  PROJECT_CHARTER.md          → templates/PROJECT_CHARTER.template.md
  AGENTS.md                   → templates/AGENTS.template.md (+ agents/*.md)
  docs/decisions/             → templates/decisions/
  docs/handoffs/              → templates/handoffs/
  docs/data/data_dictionary   → templates/data_contracts/data_dictionary
  docs/data/watchlist.md      → templates/data_contracts/watchlist
  docs/data/lineage.md        → templates/data_contracts/lineage
  docs/phase_plan.md          → templates/phase_plan
  docs/style_guide.md         → templates/style_guide
```

The shipped templates are stripped of this project's specifics — no domain vocabulary, no particular schema library — but keep the section structure that worked.
