# TASKS — {{PROJECT_NAME}}

Live dispatch queue. Update on every dispatch and every completion.

**Convention:** Tasks move top-to-bottom: Queued -> In Progress -> Done. Done tasks are pruned to a rolling 30 entries; the rest live in handoff notes.

**Format rule:** Use checkbox bullets, not Markdown tables. This keeps task movement simple and makes diffs readable.

---

## In Progress

- [ ] **T-{{nnn}} - {{task}}**
  Owner: {{agent}}
  Started: {{YYYY-MM-DD}}
  Inputs: {{paths}}
  Expected output: {{artifact or handoff}}
  Done criteria: {{one-line test}}
  Notes: {{}}

---

## Queued (next 5)

Ordered by priority. Top of list is next dispatch.

- [ ] **T-{{nnn}} - {{task}}**
  Owner: {{agent}}
  Inputs needed: {{paths}}
  Done criteria: {{}}
  Rationale: {{why now}}

- [ ] **T-{{nnn}} - {{task}}**
  Owner: {{agent}}
  Inputs needed: {{paths}}
  Done criteria: {{}}
  Rationale: {{}}

---

## Backlog

Anything not in the next-5 queue but tracked for future phases.

- [ ] **T-{{nnn}} - {{task}}**
  Phase: {{}}
  Owner: {{}}
  Notes: {{}}

---

## Done

- [x] **T-{{nnn}} - {{task}}**
  Owner: {{}}
  Completed: {{YYYY-MM-DD}}
  Handoff: `docs/handoffs/...`

---

## Blockers

Tasks blocked on input from another agent or external dependency.

- [ ] **T-{{nnn}} - {{task}}**
  Blocked on: {{what}}
  Blocker owner: {{who}}
  Filed: {{YYYY-MM-DD}}
