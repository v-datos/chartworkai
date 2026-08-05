# Phase Plan — {{PROJECT_NAME}}

**Last updated:** {{DATE TIME}}
**Current phase:** Phase {{N}} — {{name}}
**Orchestrator note:** {{One-sentence summary of where things stand right now.}}

> ## ⚠️ STOP — READ BEFORE EDITING THIS FILE ⚠️
>
> **This document has a SINGLE CANONICAL FORM. Sections are updated IN PLACE. Never append.**
>
> **Mandatory pre-edit checklist:**
>
> 1. **Read this file in full** before making any change. Not a partial read — the whole file.
> 2. **Scan for duplicate H2 headings** (`## Active agents`, `## Phase N checklist`, etc.). If any heading appears more than once, STOP. Prune to a single canonical instance — keep the most recent / most complete version — before adding anything new.
> 3. **Edit, don't paste.** Use a targeted find-and-replace to update the specific section. Never paste a fresh copy of this template onto existing content.
> 4. **Hard cap: 200 lines.** If the file exceeds 200 lines, it has drifted — prune duplicates before continuing.
>
> **What broke last time:** A precursor project's `phase_plan.md` grew to 820 lines because agents kept appending fresh "Phase N checklist" blocks instead of updating in place. This file became unreadable and its content unreliable. Do not let it happen again.
>
> See [`agents/_shared_conventions.md`](../agents/_shared_conventions.md) §Living-documents rule for the full convention.

---

## Active agents and current assignments

| Agent | Status | Current task | Blocking on |
|---|---|---|---|
| {{Agent}} | Active | {{task}} | {{nothing | what}} |
| {{Agent}} | Idle | {{next planned task}} | {{prerequisite}} |
| {{Agent}} | Waiting | {{later phase work}} | {{phase gate}} |

---

## Current phase exit criteria

Phase {{N}} closes when **all** of the following are true:

- [ ] {{exit criterion 1}}
- [ ] {{exit criterion 2}}
- [ ] {{exit criterion 3}}
- [ ] QA reproducibility report filed at `docs/reproducibility/phase_{{N}}.md`

---

## Phase {{N}} checklist

(Single canonical checklist for the current phase. Replace contents when phase advances.)

- [ ] {{deliverable 1}}
- [ ] {{deliverable 2}}
- [ ] {{deliverable 3}}

---

## Decision log (recent)

| ID | Date | Topic | Ruling | Authority |
|---|---|---|---|---|
| {{DQ-001}} | {{date}} | {{topic}} | {{see file}} | {{agent}} |

(For full history see `docs/decisions/`.)

---

## Open blockers

1. **{{Blocker description}}** — owned by {{agent}}. {{What it blocks.}}

---

## Dispatch queue (next 5 moves)

(Mirror of `TASKS.md` Queued section — keep in sync, or delete this section and rely on TASKS.md alone.)

1. **{{Agent}}** — {{task}}. Rationale: {{}}. Done-criteria: {{}}.
2. ...

---

## Risk flags

| Priority | Flag | Mitigation |
|---|---|---|
| {{H/M/L}} | {{}} | {{}} |

---

## Completed phases

- **Phase 0** ({{date}}): {{one-line summary of what closed it}}.
- **Phase 1** ({{date}}): {{}}.
