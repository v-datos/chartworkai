# Standard Operating Procedure

Runbook for operating a project built on this framework. Written as checklists the human operator (you, with an AI coding assistant) follows at four moments: session start, dispatch, decision, phase close.

---

## 1. At session start

Before prompting any agent, do:

- [ ] Open `docs/phase_plan.md`. Confirm the **current phase** and **active agents**.
- [ ] **Documentation-hygiene check.** Scan `docs/phase_plan.md`, `PROJECT_CHARTER.md`, `STATUS.md`, `TASKS.md` for duplicate H2 headings or sections that appear more than once. If any are found, prune to a single canonical instance **before any dispatch**. (See `agents/_shared_conventions.md` §Living-documents rule.) A quick check:

  ```bash
  for f in docs/phase_plan.md PROJECT_CHARTER.md STATUS.md TASKS.md; do
    echo "=== $f ==="; grep -c '^## ' "$f"; grep '^## ' "$f" | sort | uniq -c | sort -rn | head
  done
  ```

  Any heading with count > 1 (other than dated entries in STATUS.md) is drift — fix it now.
- [ ] Skim the 3 most recent files in `docs/handoffs/` — understand what the last completed work was.
- [ ] Skim the 3 most recent files in `docs/decisions/` — understand what rulings are now binding.
- [ ] Check `TASKS.md` for the top of the dispatch queue.
- [ ] If the last session ended mid-dispatch, read the final handoff note and continue; do **not** re-plan from scratch.

Open questions to answer before dispatching:
- What is the single next deliverable?
- Which agent owns it?
- What are the done-criteria?
- What inputs does that agent need — are they all present?

If any input is missing, file the blocker in `TASKS.md` and dispatch the agent who produces that input first.

---

## 2. When dispatching an agent

Use the template in [`prompts/04_orchestration_turn.md`](prompts/04_orchestration_turn.md) if you want the Orchestrator to generate the dispatch ticket. Otherwise, the dispatch must include:

- [ ] **Role:** which AGENTS.md role is acting.
- [ ] **Inputs:** explicit file paths the agent should read.
- [ ] **Expected outputs:** file paths the agent will create or modify.
- [ ] **Done-criteria:** one-sentence test that says "this is finished."
- [ ] **Escalation triggers:** what would cause this agent to stop and file a decision request instead of proceeding.
- [ ] **Handoff target:** which agent comes next.
- [ ] **Living-documents reminder.** If the dispatch will modify a living document (`docs/phase_plan.md`, `PROJECT_CHARTER.md`, `AGENTS.md`, `STATUS.md`, `TASKS.md`, anything in `docs/data/`), the dispatch ticket explicitly says: *"Update IN PLACE per Shared Conventions §Living-documents rule. Read the file fully first; do not append duplicate sections."*

Example dispatch ticket:

> **Dispatch:** Data Engineer.
> **Inputs:** `data/raw/{source}/*.csv`, `docs/decisions/20260424_dq013_*.md`.
> **Outputs:** `data/processed/fact_X.parquet`, updated `src/project/transform/X.py`.
> **Done when:** `make data` rebuilds deterministically and new parquet passes schema validation.
> **Escalation:** if schema of raw source has changed, stop and file a decision request; do not silently fix.
> **Next:** Analyst will consume `fact_X.parquet` for Phase 2 EDA.

---

## 3. When a decision arises

A **decision** is any choice that:
- Changes a schema, contract, or shared convention, **or**
- Affects how results will be interpreted, **or**
- Resolves a conflict between two agents, **or**
- Allocates scope (what's in / out of a phase).

**Do not let decisions live in chat.** File them.

Steps:
- [ ] Identify the **authority** — which agent has the expertise to rule on this? (Domain Expert for domain calls; Data Engineer for schema; Orchestrator for scope.)
- [ ] Create `docs/decisions/YYYYMMDD_<ID>_<short_title>.md` using [`templates/decisions/YYYYMMDD_decision.template.md`](templates/decisions/YYYYMMDD_decision.template.md).
- [ ] Include: **Context** (the situation and the options considered), **Ruling** (the call, with a code block if implementation-relevant), **Rationale** (why this option beats the alternatives), **Instruction** (concrete next steps for the Data Engineer / whoever implements it).
- [ ] Update `PROJECT_CHARTER.md` §Decision log with a one-liner pointer.
- [ ] Update `docs/phase_plan.md` if this changes any active work.

**Numbering convention:** Use prefix namespaces to prevent collisions and keep IDs linkable:
* **`DEC-###`**: Methodology / framework-wide rulings.
* **`DQ-###`**: Data Quality or schema-level conventions.
* **`SC-###`**: Software Configuration / coding/architecture decisions.
* **`MD-###`**: Model Design / ML evaluation decisions.

Prompt [`prompts/05_decision_capture.md`](prompts/05_decision_capture.md) converts a discussion into a draft decision file.

---

## 4. When an agent completes a deliverable

Before marking done:

- [ ] **Determine Handoff Type:**
  * **Within a phase:** Write a summary under the task's `Findings` field directly in `TASKS.md` (lightweight handoff). A separate markdown file under `docs/handoffs/` is **not** required.
  * **At phase boundaries or human session end:** Write a formal handoff note at `docs/handoffs/YYYY-MM-DD_{agent}.md` using [`templates/handoffs/YYYY-MM-DD_agent.template.md`](templates/handoffs/YYYY-MM-DD_agent.template.md).
- [ ] `TASKS.md` updated: task moved from "In Progress" to "Done," and findings filled in.
- [ ] `docs/phase_plan.md` updated with the new state (e.g. by running `./scripts/generate_phase_plan.sh`).
- [ ] If this deliverable closes a phase, trigger the phase-close checklist (§5).

Prompt [`prompts/06_handoff_writeup.md`](prompts/06_handoff_writeup.md) drafts the handoff note from the work just completed.

---

## 5. At phase close

A phase closes when all items in its **exit criteria** (defined in the charter) are met, *and* QA/Reproducibility has run a clean rebuild.

- [ ] Open `PROJECT_CHARTER.md`. Tick each exit-criterion item for the closing phase.
- [ ] Dispatch QA/Reproducibility: fresh-clone rebuild + test suite. Produces `docs/reproducibility/phase_{N}.md`.
- [ ] Update `docs/phase_plan.md`: mark phase complete, promote next phase to "current," set new active agents.
- [ ] Run `prompts/07_reflection.md` — what worked, what drifted, what to upgrade for next phase.
- [ ] Append to `PROJECT_CHARTER.md` §Change log.
- [ ] Post a STATUS entry summarizing the phase close.

---

## 6. When you (the human) are uncertain

- If the question is **scope**: it's an Orchestrator call, recorded as a decision.
- If the question is **domain** (is this scientifically/biologically/medically/legally sound?): it's a Domain Expert call.
- If the question is **schema or reproducibility**: it's a Data Engineer call.
- If the question is **statistical validity**: it's an Analyst call.
- If the question is **safety / QA**: it's a QA Engineer call.

If you find yourself making one of these calls yourself without asking the relevant agent, stop, dispatch that agent, file the decision.

---

## 7. Cadence

- **Every session:** §1 session start + at least one dispatch.
- **Every completed deliverable:** §4 handoff.
- **Every decision moment:** §3 decision file.
- **Every week or phase boundary:** `STATUS.md` entry + `prompts/07_reflection.md`.
- **Every phase close:** §5 full checklist + reproducibility run.

Fewer rituals than this: things drift. More rituals than this: you'll stop doing them. This cadence is the minimum viable.
