# Framework Overview

## Philosophy

A multi-agent project works when three things are true at once:

1. **Scope is fixed** for a bounded window. The PROJECT_CHARTER states mission, non-goals, and the current phase. Changes are decisions, not drifts.
2. **Roles are specified**, not performed ad hoc. Every agent has a Spec (inputs, outputs, scope owned, scope not owned) and a System Prompt that can be pasted into a runtime session verbatim.
3. **Interfaces are contracts.** Between agents flow named artifacts: canonical data tables, decision files, handoff notes. Nothing passes agent-to-agent except through these.

The Orchestrator is the connective tissue — maintains the charter and phase plan, routes work, records decisions. Never does the domain work.

## The six stages

Every project using this framework goes through these stages. They are not all sequential — stages 5 and 6 run concurrently and recursively.

### Stage 1 — Initialization

**Goal:** A PROJECT_CHARTER v1 and a clear "what is this project actually trying to do."

**Outputs:**
- `PROJECT_CHARTER.md` — mission, non-goals, research/product questions, success criteria.
- Initial glossary of domain terms.
- A one-paragraph statement of "done" you could defend to a stranger.

**Done when:** You can paste the charter to someone unfamiliar and they can correctly predict what the project will and won't do.

### Stage 2 — Strategy

**Goal:** A phased roadmap with exit criteria per phase, plus a risk register.

**Outputs:**
- Phase list inside `PROJECT_CHARTER.md` — each phase has entry conditions and exit criteria.
- Risk register (probability × impact × mitigation × owner).
- Objectives table traceable to research/product questions.

**Done when:** Phase exits are gated on quality, not dates, and every top risk has a named owner.

### Stage 3 — Agent Design

**Goal:** Every role spec'd, every handoff contract explicit.

**Outputs:**
- `AGENTS.md` with:
  - Shared conventions (repo layout, tooling, units, code style, reproducibility contract).
  - Per-agent Spec (mission / scope owned / scope not owned / inputs / outputs / conventions / handoff contracts / escalation triggers).
  - Per-agent System Prompt (paste-ready block).
  - Handoff-contract summary table at the bottom.
- Orchestrator is always agent 1; QA/Reproducibility is always present even on small projects.

**Done when:** You can look at the handoff-contract table and trace an artifact from raw source to final output through named agents.

### Stage 4 — Contracts Setup

**Goal:** The interfaces between agents exist before work begins.

**Outputs:**
- `docs/data/data_dictionary.md` (or equivalent artifact dictionary) — every canonical output column/field documented.
- `docs/data/watchlist.md` — known anomalies, open questions, data-quality issues with IDs (e.g., DQ-001 through DQ-013).
- `docs/data/lineage.md` — source-to-output traceability.
- `docs/style_guide.md` — colors, fonts, file naming, units, decision conventions.
- `docs/decisions/` — directory initialized with a README explaining the decision-log format.
- `docs/handoffs/` — directory initialized.

**Done when:** An agent can answer "what should I produce, and in what format?" by reading only `docs/` without asking a human.

### Stage 5 — Execution

**Goal:** Agents produce artifacts; the Orchestrator routes; decisions accumulate.

**The execution loop:**

```
┌──────────────────────────────────────────────────────────┐
│  Orchestrator assesses state (phase_plan + open items)   │
│                         ↓                                │
│  Orchestrator dispatches the next agent with a ticket    │
│                         ↓                                │
│  Agent reads charter + relevant decisions + inputs       │
│                         ↓                                │
│  Agent produces artifact + handoff note                  │
│                         ↓                                │
│  Agent flags decisions to the right authority            │
│                         ↓                                │
│  Orchestrator updates phase_plan, routes next            │
└──────────────────────────────────────────────────────────┘
```

**Cadence suggestions:**
- One dispatch per session is normal. Parallel dispatches for independent work.
- Decisions filed same-day, not retroactively.
- Handoff notes are short (half-page max) — they're pointers, not the work itself.

### Stage 6 — Monitoring & Reflection

**Goal:** Catch drift early; amend the charter deliberately, not accidentally.

**Outputs:**
- Weekly or milestone `STATUS.md` — what shipped, what's blocked, what changed.
- Periodic retros — prompt `07_reflection.md` — that ask "what's stuck, what's drifting, what should we upgrade."
- Charter change-log entries for every scope change.

**Done when:** The charter's `## Change log` section truthfully reflects the project's trajectory, and there are no silent scope expansions.

## How the pieces compose

```
PROJECT_CHARTER.md      — mission / phases / success criteria
         │
         ├──► AGENTS.md           — who does what, handoff contracts
         │
         ├──► docs/data/          — data / artifact contracts
         │     ├── data_dictionary.md
         │     ├── watchlist.md
         │     └── lineage.md
         │
         ├──► docs/decisions/     — dated, authority-stamped rulings
         │     └── YYYYMMDD_topic.md
         │
         ├──► docs/handoffs/      — inter-agent artifact notices
         │     └── YYYY-MM-DD_agent.md
         │
         ├──► docs/phase_plan.md  — current phase, active agents, blockers
         │
         └──► STATUS.md + TASKS.md — weekly pulse + dispatch queue
```

## Anti-patterns this framework is designed against

- **"Just ask the AI" without a charter** — scope drift guaranteed.
- **Agents that edit each other's artifacts** — ownership becomes unclear.
- **Decisions buried in chat** — impossible to audit; contradict themselves within a month.
- **Orchestrator deciding science / product calls** — undermines domain experts; kills trust.
- **Handoffs as chat messages, not files** — loses the traceability that makes the framework worth using.

See [`IMPROVEMENTS.md`](IMPROVEMENTS.md) for the specific friction real projects hit and the upgrades added as a result.
