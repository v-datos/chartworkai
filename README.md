<p align="center">
  <img src="https://raw.githubusercontent.com/v-datos/chartworkai/main/assets/chartworkai_banner.png" alt="ChartworkAI — the governance layer for agentic work" width="840">
</p>

# ChartworkAI

[![CI](https://github.com/v-datos/chartworkai/actions/workflows/ci.yml/badge.svg)](https://github.com/v-datos/chartworkai/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/chartworkai.svg)](https://pypi.org/project/chartworkai/)
[![Python](https://img.shields.io/pypi/pyversions/chartworkai.svg)](https://pypi.org/project/chartworkai/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

**The governance layer for agentic work.**

> Agent frameworks orchestrate. ChartworkAI governs. Charter, decisions, handoffs, and phase gates that survive across sessions, assistants, and months — works with CrewAI, LangGraph, Claude Code, Cursor, or plain humans.

Agent runtimes are good at *executing* work and have no memory of *why* anything was decided: their state is scoped to a single run and vanishes when the process exits. ChartworkAI is the other half — a repository-native governance layer where scope, authority, decisions, and handoffs live as version-controlled Markdown, so any session, teammate, or assistant can reconstruct the project from the repo alone.

It is deliberately runtime-agnostic and works with any language, stack, assistant, or human language.

```bash
pip install chartworkai                                   # zero runtime dependencies

chartworkai init ./my-project --name "My Project"          # generic governance core
chartworkai check .                                       # is it installed and healthy?
chartworkai check . --json                                # machine-readable, for CI and agents
chartworkai plan .                                        # rebuild the phase plan from state
chartworkai mcp                                           # serve it to an AI assistant
```

The default `generic` profile is project-agnostic. The six optional presets — `software-app`, `data-science`, `database`, `competition-ml`, `investigation`, `deployed-service` — add proven defaults for common deliverables. A web app is never asked for a data dictionary.

For a project outside those presets, define its roles, required artifacts, directories, and validation commands in a JSON profile:

```bash
chartworkai init ./case-review --name "Case Review" \
    --profile-file ./case-review.profile.json
```

Start from [`templates/custom_profile.template.json`](templates/custom_profile.template.json). The validated contract is copied to `chartworkai.profile.json` in the new project and enforced by `chartworkai check`. Validation commands are recorded, never executed implicitly.

A fresh scaffold **deliberately fails `check`** until you fill in the placeholders and delete the `_framework_*` reference folders. That is the graduation gate, not a bug.

## Use it from your AI assistant (MCP)

`chartworkai mcp` speaks the Model Context Protocol over stdio, so an assistant can enforce governance itself instead of waiting for you to relay output. Point your assistant's MCP config at it:

```json
{
  "mcpServers": {
    "chartworkai": {
      "command": "chartworkai",
      "args": ["mcp"]
    }
  }
}
```

Four tools become available:

| Tool | Purpose |
|---|---|
| `chartworkai_check` | Verify the governance layer is installed and healthy |
| `chartworkai_state` | Where the project stands: phase, tasks, blockers, recent decisions and handoffs |
| `chartworkai_file_decision` | Record a dated, authority-stamped decision (auto-numbered per `DEC`/`DQ`/`SC`/`MD` namespace) |
| `chartworkai_file_handoff` | Write the handoff note that lets the next agent resume |

## What this gives you

- A **PROJECT_CHARTER** skeleton — mission, non-goals, research questions, phased roadmap, success criteria, risks, change log.
- An **AGENTS.md** pattern — every role has a Spec (for humans) and a paste-ready System Prompt (for the AI runtime). Handoff contracts are explicit.
- A **decision log** convention with authority-stamped rulings, so domain calls stay traceable.
- **Data / artifact contracts** — data dictionary, lineage, watchlist templates that keep producers and consumers in sync.
- **Reusable prompts** for the recurring moments: initial planning, agent generation, orchestration turn, decision capture, handoff write-up, reflection.
- A **Standard Operating Procedure** — the literal checklist to run at session start, when dispatching, when a decision arises, and at phase closure.

## Definition of Installed

A project has **not** been initialized from this framework until these artifacts exist in the project root:

- `PROJECT_CHARTER.md`
- `AGENTS.md`
- `docs/phase_plan.md`
- `STATUS.md`
- `TASKS.md`
- `docs/decisions/README.md` plus at least one seed decision file
- `docs/handoffs/README.md` or at least one dated handoff note
- `docs/domain/README.md`

**Data presets only** (`data-science`, `database`, `competition-ml`) additionally require the contract triad. A custom profile inherits this requirement only when it extends a data preset:

- `docs/data/data_dictionary.md`
- `docs/data/lineage.md`
- `docs/data/watchlist.md`

Run the compliance checker from the target project root:

```bash
./scripts/check_framework_compliance.sh
```

If you are running it from this framework repo against another project:

```bash
./scripts/check_framework_compliance.sh /path/to/project
```

## Fast Bootstrap

From this framework repo, create a compliance-checked scaffold with:

```bash
scripts/init_project_from_framework.sh /path/to/new_project "Project Name" project_slug
```

The bootstrap script copies the reference templates/prompts/agents into `_framework_*` directories, creates the canonical operating files, seeds the first decision and handoff, installs the compliance checker, and runs it before finishing.

## When to use it

Use it when:
- You'll run the project over **many sessions** and need continuity between them.
- The work has **≥3 distinguishable roles** (e.g. ingestion, domain expertise, analysis, QA).
- You want every claim **auditable back to the agent that produced it**.
- Reproducibility matters — outputs must be regenerable from source.

## When **not** to use it

- Single-shot tasks that fit in one session.
- Prototypes where speed beats traceability.
- Projects with fewer than three distinct workstreams.

## How to read this repo

Start here, then follow in order:

**→ Just want to use it? Read [`IMPLEMENTATION_GUIDE.md`](IMPLEMENTATION_GUIDE.md) first — the single do-this playbook (bootstrap → customize → operate → ship), readable by you or an AI agent.**

1. [`FRAMEWORK_OVERVIEW.md`](FRAMEWORK_OVERVIEW.md) — the six workflow stages and the philosophy behind them.
2. [`SOP.md`](SOP.md) — the runbook. What to do at session start, at dispatch, at decision, at phase close.
3. [`INITIALIZATION_GUIDE.md`](INITIALIZATION_GUIDE.md) — step-by-step for standing up a new project from these templates.
4. [`IMPROVEMENTS.md`](IMPROVEMENTS.md) — the friction real projects hit, and the upgrades baked in as a result.
5. [`templates/`](templates/) — the artifacts you copy and fill in.
6. [`agents/`](agents/) — generic role specs + system prompts. Pick the ones you need.
7. [`prompts/`](prompts/) — reusable prompts for the power moments.
8. [`examples/research_case_study.md`](examples/research_case_study.md) — a worked example showing each piece in real use.

## Design principles

- **Charter is single source of truth.** Scope, phases, roles all flow from it.
- **Roles are contracts, not titles.** Each agent has explicit inputs, outputs, scope owned, scope *not* owned.
- **Decisions are first-class artifacts.** Anything that changes scope, schema, or shared convention gets a dated, authority-stamped file in `docs/decisions/`.
- **Handoffs are the currency.** Agents don't "finish" — they produce a handoff note that names the next agent and the next input.
- **Orchestrator doesn't do work.** Coordinates, routes, records decisions. Never overrides a domain expert on their own turf.
- **Reproducibility or it didn't happen.** No phase closes until a clean rebuild passes.

## License

Apache License 2.0 — see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE). Use it commercially, modify it, and redistribute it; retain the copyright and NOTICE, state significant changes you make, and note that the licence includes an express patent grant. Provided without warranty.
