# Initialization Guide

How to stand up a new project from this framework, step-by-step.

## Prerequisites

- A one-paragraph description of the project (what, why, for whom).
- Access to an AI coding assistant (such as Claude Code, Cursor, Qwen, Codex, etc.) with a long-running workspace.
- A git-initialized directory for the new project.

## Step 0 — Copy the framework scaffold

Fast path:

```bash
scripts/init_project_from_framework.sh ~/projects/my_new_project "My New Project" my_new_project
```

This creates a minimal initialized project, copies reference templates/prompts/agents into `_framework_*` directories, seeds decisions/handoffs, installs the compliance checker, and runs it. After bootstrap, customize `PROJECT_CHARTER.md`, `AGENTS.md`, `docs/phase_plan.md`, `TASKS.md`, and `docs/data/`.

Manual path:

```bash
# From the framework repo:
NEW_PROJECT=~/projects/my_new_project
mkdir -p "$NEW_PROJECT"
cd "$NEW_PROJECT"

# Copy templates and agents as starting points:
cp -r /path/to/chartworkai/templates ./_framework_templates
cp -r /path/to/chartworkai/agents ./_framework_agents
cp -r /path/to/chartworkai/prompts ./_framework_prompts
cp -r /path/to/chartworkai/scripts ./scripts

# Create the project structure:
mkdir -p docs/{decisions,handoffs,data,domain,reproducibility}
mkdir -p src tests data/{raw,interim,processed,external} reports/{figures,tables,draft}
touch docs/.gitkeep
git init
```

## Step 1 — Write the PROJECT_CHARTER

```bash
cp _framework_templates/PROJECT_CHARTER.template.md PROJECT_CHARTER.md
```

Open `PROJECT_CHARTER.md` and fill in the `{{}}` placeholders. To do this with AI help, paste the project brief into your AI assistant session and run the planning prompt:

```
# Apply the prompt in prompts/01_initial_planning.md (e.g. using /read prompts/01_initial_planning.md in Claude Code, or pasting its content)
```

That prompt asks the AI assistant to produce a first-draft charter from your brief. Review, edit, commit.

**Do not skip this step.** A project without a charter is a project without a rudder.

## Step 2 — Generate the AGENTS.md roster

```bash
cp _framework_templates/AGENTS.template.md AGENTS.md
```

Decide which roles you need. Every project needs:

- **Orchestrator** — always.
- **QA/Reproducibility Engineer** — always.
- **Domain Expert** — whoever owns the domain truth. Rename for your domain (e.g., "Marine Ecologist", "Clinical Lead", "Product Manager", "Legal Counsel").
- At least one **producer** role (Data Engineer, Software Engineer, Writer, etc.).
- At least one **analyst / reviewer** role (Statistician, QA reviewer, Editor, etc.).

Optional roles from `agents/_optional/`:
- Geospatial Analyst (spatial data)
- Causal Inference Specialist (attribution questions)
- Forecasting Specialist (projections)
- External Data Specialist (third-party source integration)
- Scientific Writer (report authoring)
- Visualization Engineer (dashboards, figures)
- Software Engineer (the producer for software-app projects)
- Frontend Engineer (UI / client)
- Deployment Engineer (build, release, hosting, rollback)

For a non-Python stack, a different AI assistant, or non-English content, see [`PORTABILITY.md`](PORTABILITY.md).

For optional add-ons (e.g. external-tracker sync), see [`extensions/`](extensions/).

Copy each chosen role's file from `_framework_agents/` into your `AGENTS.md`, customizing the mission, inputs, and outputs to your project. Fill placeholders.

Run the prompt in `prompts/02_agent_generation.md` to let the AI assistant draft role-specific System Prompts from the charter.

## Step 3 — Set up contracts

From `_framework_templates/`:

```bash
cp data_contracts/data_dictionary.template.md docs/data/data_dictionary.md
cp data_contracts/watchlist.template.md docs/data/watchlist.md
cp data_contracts/lineage.template.md docs/data/lineage.md
cp phase_plan.template.md docs/phase_plan.md
cp style_guide.template.md docs/style_guide.md
cp STATUS.template.md STATUS.md
cp TASKS.template.md TASKS.md
```

Fill them in enough to be useful as soon as work begins. They are living documents — don't over-engineer v0.

Also seed the required domain index: create `docs/domain/README.md` listing the domain artifacts this project will maintain (`groupings.md`, `variable_definitions.md`, `analytic_guidelines.md`). The compliance check requires this file.

## Step 4 — Seed the decision log

```bash
cp _framework_templates/decisions/YYYYMMDD_decision.template.md docs/decisions/README.md
# Edit README.md to explain to future agents how to add new decisions.
```

Add one real first-decision: `docs/decisions/YYYYMMDD_charter_v1.md` ruling "project scoped per charter v1, Orchestrator owns changes." This seeds the pattern.

Also add either `docs/handoffs/README.md` explaining the handoff convention, or a first dated handoff note. The framework is not installed until the handoff directory has one of those files.

## Step 5 — Run the planning prompt

Open an AI assistant session in the project directory. Run:

```
# Apply the prompt in prompts/03_phase_roadmap.md (e.g. using /read prompts/03_phase_roadmap.md or pasting its content)
```

This asks the AI assistant, acting as Orchestrator, to produce a phased roadmap based on your charter. Review, edit, paste into `PROJECT_CHARTER.md` §5 Phases.

## Step 6 — First dispatch

Run:

```
# Apply the prompt in prompts/04_orchestration_turn.md (e.g. using /read prompts/04_orchestration_turn.md or pasting its content)
```

This asks the Orchestrator to propose the first dispatch based on `docs/phase_plan.md`. Accept or edit.

## Step 7 — Commit and go

Before committing, run the installation check from the project root:

```bash
./scripts/check_framework_compliance.sh
```

This is the hard definition of installed. The check must pass before the project starts normal execution.

```bash
# Remove scaffold copies now that templates and extensions are customized:
rm -rf _framework_templates _framework_agents _framework_prompts _framework_extensions

git add .
git commit -m "Initialize project from ChartworkAI"
```

## Placeholders to replace

Every template uses these tokens. A global find-and-replace is fine as long as you verify per-file:

| Token | Meaning | Example |
|---|---|---|
| `{{PROJECT_NAME}}` | Full project name | Customer Retention Analysis |
| `{{PROJECT_SLUG}}` | Short machine-friendly name | `customer_retention` |
| `{{DOMAIN}}` | Subject-matter domain | Subscription analytics |
| `{{DOMAIN_EXPERT_TITLE}}` | Role name for domain expert | Retention Lead |
| `{{CANONICAL_ENTITY}}` | Primary record unit | customer-month |
| `{{STAKEHOLDER}}` | Who the output serves | the growth team |
| `{{TIME_RANGE}}` | Temporal scope | 2021–2025 |
| `{{DATA_SOURCE}}` | Primary data source | the billing export |
| `{{AUTHOR}}` | Project owner name | (your name) |
| `{{DATE}}` | ISO date | 2026-04-24 |

## Definition of Installed

A project is **not initialized** until all of these exist:

- `PROJECT_CHARTER.md`
- `AGENTS.md`
- `docs/phase_plan.md`
- `STATUS.md`
- `TASKS.md`
- `docs/decisions/README.md` plus at least one seed decision file
- `docs/handoffs/README.md` or at least one dated handoff note
- `docs/domain/README.md`
- `docs/data/data_dictionary.md`
- `docs/data/lineage.md`
- `docs/data/watchlist.md`

Verify this with:

```bash
./scripts/check_framework_compliance.sh
```

## What a healthy project looks like after one week

- `PROJECT_CHARTER.md` exists and is specific enough to defend to a stranger.
- `AGENTS.md` has at least 4 roles spec'd and one System Prompt battle-tested.
- `docs/decisions/` has 1–3 real decision files, not just the seed.
- `docs/handoffs/` has 1–3 handoff notes.
- `docs/phase_plan.md` is current (last-updated in the last 48 hours).
- `STATUS.md` has at least one entry.
- `TASKS.md` has a live dispatch queue.

If any of these are missing after a week, stop and fix them before continuing. The framework's value compounds with use; skipping the rituals breaks the compounding.
