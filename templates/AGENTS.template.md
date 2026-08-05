# AGENTS.md — Operating Document for {{PROJECT_NAME}}

**Status:** Living document. Edit the "Shared Conventions" section first when changing anything global — every agent below references it.

**How to use this file:**
Each agent has two parts — a **Spec** (for humans designing and routing work) and a **System Prompt** (the text to paste into an agent runtime). Specs can be revised freely. System prompts should be updated together with their Spec to stay in sync.

---

## Table of contents

1. [Orchestrator](#1-orchestrator)
2. [{{Domain Expert Title}}](#2-domain-expert)
3. [{{Producer Role e.g. Data Engineer}}](#3-data-engineer)
4. [{{Analyst Role}}](#4-analyst)
5. [QA / Reproducibility Engineer](#5-qa--reproducibility-engineer)
6. [{{Optional roles…}}]

---

## Shared conventions

Every agent operates within these rules. Violations are escalated to the Orchestrator.

**Repository layout** — the tree below is the **data-science** profile's; other profiles use their idiomatic layout, only `docs/` is universal (see `profiles/`). Paths relative to repo root `{{PROJECT_SLUG}}/`:

```
data/
  raw/                       # Immutable source data
  external/{source}/         # Third-party datasets with MANIFEST per source
  interim/                   # Intermediate build artifacts
  processed/                 # Canonical {{output format, e.g., parquet}} tables
src/{{PROJECT_SLUG}}/
  io/                        # Loaders + schema validators
  transform/                 # Cleaning, joining, aggregation
  features/                  # Derived metrics
  models/                    # Statistical / causal / forecasting modules
  viz/                       # Reusable plotting
tests/                       # pytest (or equivalent) suite
notebooks/                   # Numbered by phase
reports/
  figures/                   # Publication-grade outputs
  draft/                     # In-progress narrative
docs/                        # Planning, decisions, handoffs, contracts
```

**Canonical processed artifacts** (every analytic agent consumes these, not raw):

- `{{table_or_artifact_1}}` — {{purpose, primary key}}
- `{{table_or_artifact_2}}` — {{purpose, primary key}}
- `{{master_table}}` — denormalized roll-up for fast analytics

**Keys & types:** {{state primary key conventions, type rules, units, coordinate reference system if applicable}}.

**Tooling:** Declared in the charter `## Stack` block — {{language/runtime, package manager, core stack}} (any language).

**Code style:** {{linter, formatter, type-checker, line length, quote style}}.

**Notebooks rule** *(data-science profile)***:** Notebooks are for exploration and narrative. Any function used more than once moves to `src/{{PROJECT_SLUG}}/`. Notebooks must never import from other notebooks; the verify command flags this.

**Reproducibility contract:** Every output is regenerable from the project's **verify command** (charter `## Stack`) on a clean checkout; nothing merges without it passing. What "reproducible" means is set by the profile (see `profiles/`).

**Communication:** Every agent writes a **handoff note** when completing a deliverable — a short markdown block stating: what was produced, where it lives, known limitations, and the next agent in the chain. Handoff notes accumulate in `docs/handoffs/YYYY-MM-DD_{agent}.md`.

**Escalation:** Any agent blocked for more than one work session, or encountering a decision that changes shared conventions, escalates to the Orchestrator via a decision request in `docs/decisions/OPEN_*.md`.

**Agent operating protocol:** Every dispatch ticket must name:

- **Input checklist:** exact files, data, decisions, and handoffs the agent must read.
- **Output schema:** exact files, records, reports, or artifacts the agent must create or update.
- **Escalation triggers:** conditions that stop execution and require a decision request.
- **Allowed files:** paths the agent may edit for this dispatch.
- **Required validation command:** command, check, or inspection proving the output is usable.
- **Handoff template:** expected next-agent handoff note and recipient.

---

## 1. Orchestrator

(See [`agents/orchestrator.md`](agents/orchestrator.md) for full Spec + System Prompt. Paste both into this section when assembling AGENTS.md for the project.)

---

## 2. {{Domain Expert Title}}

(See [`agents/domain_expert.md`](agents/domain_expert.md). Customize the system prompt's "key context you already hold" section with project-specific domain knowledge.)

---

## 3. {{Producer Role e.g. Data Engineer}}

(See [`agents/data_engineer.md`](agents/data_engineer.md).)

---

## 4. {{Analyst Role}}

(See [`agents/analyst.md`](agents/analyst.md).)

---

## 5. QA / Reproducibility Engineer

(See [`agents/qa_engineer.md`](agents/qa_engineer.md).)

---

## (Optional roles)

Add from [`agents/_optional/`](agents/_optional/) as needed.

**Data / research:** Geospatial Analyst · Causal Inference Specialist · Forecasting Specialist · External Data Specialist · Scientific Writer · Visualization Engineer.

**Software / app:** Software Engineer (the producer for software-app projects) · Frontend Engineer · Deployment Engineer.

---

## Handoff-contract summary (quick reference)

| From → To | Artifact | When |
|---|---|---|
| {{Producer}} → All analytic agents | Canonical processed tables + data dictionary | End of foundation phase, then on every rebuild |
| {{Domain Expert}} → {{Producer}} | Domain rules, aggregation specs | Foundation phase |
| {{Domain Expert}} → {{Analyst}} | Variable definitions, what to test | Analysis phase onward |
| {{Analyst}} → {{Domain Expert}} | Results for vetting | After each analysis |
| All agents → QA / Reproducibility | Code + outputs at phase boundary | Phase boundaries |
| QA / Reproducibility → Orchestrator | Phase reproducibility report | Phase closure |
| Every agent → Orchestrator | Handoff notes, decision requests | Continuous |

---

*End of AGENTS.md. Pair with [`PROJECT_CHARTER.md`](PROJECT_CHARTER.md) and [`docs/phase_plan.md`](docs/phase_plan.md).*
