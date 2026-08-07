# Implementation Guide

A single, do-this playbook for running **any** project with ChartworkAI. Readable top-to-bottom by a person **or** an AI agent. Deeper detail lives in the docs this guide points to ([`README.md`](README.md), [`INITIALIZATION_GUIDE.md`](INITIALIZATION_GUIDE.md), [`SOP.md`](SOP.md), [`profiles/`](profiles/), [`extensions/`](extensions/), [`PORTABILITY.md`](PORTABILITY.md)).

---

## 0. The mental model (read this first)

- **You + your AI assistant together are the Orchestrator.** There are no separate programs.
- **"Agents" are roles your assistant plays one at a time** — you instantiate one by pasting its System Prompt from `AGENTS.md` plus a dispatch ticket.
- **All project state lives in version-controlled Markdown, never in chat.** The repo *is* the memory and the contract — so any new session, teammate, or different AI assistant resumes by reading files.
- **Definition of "installed/healthy" = `./scripts/check_framework_compliance.sh .` passes.** That checker is the ground truth throughout.

The loop, in one sentence: **read state → propose ONE dispatch → the agent produces an artifact + a handoff → file any decisions → update the plan → repeat; at phase boundaries, run the verify command and file a reproducibility report.**

---

## 1. Pick the generic core, a preset, or a custom profile

Running `chartworkai init` without a profile installs the project-agnostic `generic` core. The six named profiles are optional presets, not a closed list of project categories. A profile decides which artifacts are required and what "reproducible" means.

<!-- BEGIN GENERATED PROFILE TABLE -->
| Profile | Deliverable | Data contracts | "Reproducible" means |
|---|---|---|---|
| [`generic`](profiles/generic.md) | a project-defined deliverable | not required | the project-defined validation commands pass |
| [`data-science`](profiles/data-science.md) | reproducible analysis / report | required | byte-identical rebuild from raw |
| [`software-app`](profiles/software-app.md) | running / deployable software | not required | build + tests pass |
| [`database`](profiles/database.md) | a curated dataset | required | deterministic rebuild + quality baselines |
| [`competition-ml`](profiles/competition-ml.md) | a scored submission | required | submission regenerates from a recorded run |
| [`investigation`](profiles/investigation.md) | evidence-backed findings | not required | every claim traces to an archived source at an evidence tier |
| [`deployed-service`](profiles/deployed-service.md) | a deployed service + infrastructure | not required | config + image digest + job URI trace a release |
<!-- END GENERATED PROFILE TABLE -->

Each built-in profile has a spec in [`profiles/`](profiles/) covering its required artifacts, verify contract, and default roles. For another project type, copy [`templates/custom_profile.template.json`](templates/custom_profile.template.json), set `extends` to `generic` or one of the six presets, and define project-specific roles, required artifacts, scaffold directories, and validation commands. Custom commands are recorded in the charter but never executed implicitly.

---

## 2. Bootstrap (one command)

Run from the framework repo root:

Either the CLI (recommended — works from a plain `pip install`, anywhere):

```
pip install chartworkai
chartworkai init ~/projects/trip_planner --name "Trip Planner"
```

Add `--profile software-app` for that preset, or `--profile-file ./my-profile.json` for a custom contract.

…or the shell script, run from a clone of this repository:

```
scripts/init_project_from_framework.sh  ~/projects/trip_planner  "Trip Planner"  trip_planner  software-app
```

For `generic` and the six presets, both entry points produce a byte-identical scaffold; CI diffs them on every change. Custom JSON profiles use the Python package because robust JSON parsing is deliberately not reimplemented in POSIX shell.

This creates the canonical operating files (`PROJECT_CHARTER.md`, `AGENTS.md`, `STATUS.md`, `TASKS.md`, `docs/phase_plan.md`, decisions/handoffs/domain seeds, and — for data profiles — `docs/data/` contracts), copies reference material into `_framework_*` folders, and runs the compliance check.

> The fresh scaffold **deliberately fails the check** (unfilled `{{placeholders}}` + the temporary `_framework_*` folders). That is the *graduation gate*, not an error.

---

## 3. Customize (make it yours)

Fill these in. Use the paste-ready prompts in [`prompts/`](prompts/) to draft each with your assistant.

1. **`PROJECT_CHARTER.md`** — the single source of truth. Fill: mission, ≥3 non-goals, the `Profile:` line, the `## Stack` block (declare your **verify command** — this is your "it works" gate), the phased roadmap, and success criteria. *(Draft from a one-paragraph brief with `prompts/01_initial_planning.md`; build the roadmap with `prompts/03_phase_roadmap.md`.)*
2. **`AGENTS.md`** — the roster. Always keep **Orchestrator** and a **QA / Reproducibility** role. Rename the **Domain Expert** for your field. Add a **Producer** (Data Engineer, or Software Engineer for apps) and any optional roles from [`agents/_optional/`](agents/_optional/) (e.g. Frontend Engineer, Deployment Engineer). Paste each role's Spec **and** its System Prompt, and resolve every `{{placeholder}}`. *(Draft with `prompts/02_agent_generation.md`.)*
3. **Data contracts** *(data profiles only)* — fill `docs/data/data_dictionary.md`, `lineage.md`, `watchlist.md`. Non-data profiles skip this.
4. **`docs/domain/README.md`** — what a new agent must know about your domain.
5. **Optional extensions** — copy any you want from `_framework_extensions/` (external-tracker sync, claims gate, experiment log, assistant primer). See [`extensions/README.md`](extensions/README.md).

---

## 4. Graduate (verify = "installed")

```
./scripts/check_framework_compliance.sh .      # repeat until it says "passed"
rm -rf ./_framework_*                           # delete the temporary reference folders
git init && git add -A && git commit -m "Initialize <project> from ChartworkAI"
```

When the checker passes, the project is **installed** and ready to run.

---

## 5. Operate (the daily loop)

Open your AI assistant in the project repo and run this cycle (full detail in [`SOP.md`](SOP.md)):

**a. Session start.** Read `docs/phase_plan.md`, the 3 most recent `docs/handoffs/`, and the open items in `TASKS.md`. (Or paste `prompts/04_orchestration_turn.md` — the assistant reads state and proposes the next step.)

**b. Dispatch ONE agent** with a complete ticket:

```
Dispatch → <Role>
  Inputs:    <exact files/paths to read>
  Output:    <exact files/paths to produce>
  Done when: <one-sentence, checkable test>
  Escalate:  <condition> → <which agent/authority>
  Handoff:   → <next agent>
```

**c. The agent produces the artifact + a handoff note** — the only currency between agents:

```
docs/handoffs/YYYY-MM-DD_<agent>.md
  What was produced · Where it lives · Known limitations · How to verify · Next agent
```
*(Within a phase, a one-line "Findings" under the task in `TASKS.md` is the lightweight equivalent; write a full handoff file at phase boundaries. Draft with `prompts/06_handoff_writeup.md`.)*

**d. File any real decision** (anything that changes scope, schema, a convention, or interpretation) as a dated, authority-stamped file. Use ID namespaces:

```
docs/decisions/YYYYMMDD_<NS>###_<short_title>.md      NS ∈ { DEC, DQ, SC, MD }
  Date · Authority · Status · Context · Ruling · Rationale · Consequences
```
Link it from `PROJECT_CHARTER.md` §Decision log. *(Draft with `prompts/05_decision_capture.md`.)*

**e. Update the living docs in place** — move the task in `TASKS.md`, refresh `docs/phase_plan.md`. Never append duplicate sections. You can rebuild the plan from current state any time:

```
./scripts/generate_phase_plan.sh .
```

Repeat a→e, one dispatch at a time.

---

## 6. Close a phase

1. Run your **verify command** (from `## Stack`) on a clean checkout.
2. File `docs/reproducibility/phase_<N>.md` (what was verified + the result).
3. Tick the charter's exit criteria, post a `STATUS.md` entry, promote to the next phase.
4. Optionally run a retro with `prompts/07_reflection.md`.

---

## 7. Keep it healthy

Run `./scripts/check_framework_compliance.sh .` regularly. It is your drift alarm — it fails on: unresolved placeholders, missing required files, duplicate headings, a `TASKS.md` that isn't a checkbox queue, a stale or bloated `STATUS.md`/`phase_plan.md`, decision files that break the namespace pattern, leftover `_framework_*` folders, and tool-specific leaks (assistant names / slash-commands) in core docs. Fix what it flags. Run `prompts/07_reflection.md` at each phase boundary.

---

## Quick reference

**Canonical files**
| File | Purpose |
|---|---|
| `PROJECT_CHARTER.md` | Single source of truth: mission, non-goals, profile, `## Stack`, phases, success criteria, decision log |
| `AGENTS.md` | Roles-as-contracts: shared conventions + per-agent Spec & System Prompt |
| `docs/phase_plan.md` | Current phase, active agents, exit criteria, dispatch queue (regenerable) |
| `STATUS.md` | Weekly/milestone pulse — newest entry on top, keep it short |
| `TASKS.md` | Dispatch queue — checkbox bullets, one `## In Progress` |
| `docs/decisions/` | Dated, authority-stamped rulings (`DEC/DQ/SC/MD-###`) |
| `docs/handoffs/` | Inter-agent handoff notes (the currency) |
| `docs/domain/` | Domain knowledge the Domain Expert maintains |
| `docs/data/` | *(data profiles)* data_dictionary, lineage, watchlist |
| `docs/reproducibility/` | Phase-close verify reports |

**Commands**
```
scripts/init_project_from_framework.sh <dir> "Name" slug [profile]   # generic/preset bootstrap
./scripts/check_framework_compliance.sh .                            # verify / "installed"
./scripts/generate_phase_plan.sh .                                   # rebuild phase_plan from state

pip install chartworkai                                                # or use the CLI
chartworkai init <dir> --name "Name"                                  # generic bootstrap
chartworkai init <dir> --name "Name" --profile-file <file>            # custom bootstrap
chartworkai check . [--json] [--strict]                                # verify / "installed"
chartworkai plan .                                                     # rebuild phase_plan from state
chartworkai state .                                                    # where the project stands
chartworkai mcp                                                        # serve to an AI assistant
```

**Let your assistant enforce it (MCP).** Instead of remembering to run the checker, point your assistant's MCP config at `chartworkai mcp`:

```json
{ "mcpServers": { "chartworkai": { "command": "chartworkai", "args": ["mcp"] } } }
```

It then has `chartworkai_check` (health), `chartworkai_state` (phase, tasks, blockers, recent decisions/handoffs), `chartworkai_file_decision` (auto-numbered per namespace), and `chartworkai_file_handoff`. The loop in §5 becomes something the assistant does natively — read state, dispatch, record the decision, write the handoff — instead of something you have to police.

**Prompts (`prompts/`)** — paste into your assistant at the right moment
`01` draft the charter from a brief · `02` draft the roster · `03` build the phase roadmap · `04` "what's the next single dispatch?" · `05` capture a decision · `06` write a handoff · `07` run a reflection retro.

---

## Worked example — "Trip Planner" (software-app), compressed

```
# 1. Bootstrap
scripts/init_project_from_framework.sh ~/projects/trip_planner "Trip Planner" trip_planner software-app

# 2. Charter §Stack (filled)
Profile: software-app
- Build command:  pnpm build
- Test command:   pnpm test
- Verify command: pnpm build && pnpm test

# 3. Roster (AGENTS.md): Orchestrator · Travel Product Owner (Domain Expert) ·
#    Software Engineer · Frontend Engineer · QA Engineer

# 4. Graduate
./scripts/check_framework_compliance.sh .   →  "passed";  rm -rf ./_framework_*;  git commit

# 5. First dispatch
Dispatch → Software Engineer
  Inputs:    PROJECT_CHARTER.md §Stack, docs/domain/README.md
  Output:    src/itinerary/ + tests
  Done when: GET /itinerary returns a 3-day plan for a city; `pnpm test` green
  Escalate:  trip-scoring rule unclear → Travel Product Owner
  Handoff:   → QA Engineer
# → produces src/, then docs/handoffs/2026-06-13_software_engineer.md
# → decision filed: docs/decisions/20260613_SC001_sqlite_for_v1.md
```

---

## If you are an AI agent implementing this autonomously

1. Confirm the **profile** and the **verify command** from `PROJECT_CHARTER.md`. If absent, ask the human or infer from the stack, then record it.
2. Run `./scripts/check_framework_compliance.sh .`. Treat every failure as a task. Do not proceed to domain work until placeholders are resolved and the structure is in place.
3. Act as **Orchestrator**: read `docs/phase_plan.md` + recent handoffs/decisions, then propose and execute **exactly one** dispatch using the ticket format in §5b. Do not do domain work as the Orchestrator — adopt the specialist role (its System Prompt in `AGENTS.md`) for that.
4. For each completed dispatch: write the artifact, write a handoff (§5c), file any decision (§5d), update `TASKS.md` + `docs/phase_plan.md` **in place**.
5. Never invent state in chat. If it matters, it goes in a file. If two files disagree, the charter wins and you file a decision to reconcile.
6. At a phase boundary: run the verify command, file `docs/reproducibility/phase_<N>.md`, then promote the phase.
7. Re-run the compliance checker before declaring any milestone done.
