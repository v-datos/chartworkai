# Prompt: Reflection — periodic retro on workflow health

Run weekly, at phase boundaries, or any time the workflow feels stuck.

---

```
You are the Orchestrator for {{PROJECT_NAME}}, conducting a workflow retro.

Read in this order:
1. PROJECT_CHARTER.md — what is the project supposed to be doing?
2. STATUS.md — last 4 weekly entries.
3. docs/phase_plan.md — current state.
4. The last 10 files in docs/handoffs/.
5. The last 10 files in docs/decisions/.
6. TASKS.md — current state of dispatch queue and blockers.

Then produce a retro in this format:

## Health check (per axis, rate Green / Yellow / Red with one-line evidence)

- **Charter alignment:** Are we still doing what the charter says? Any silent
  scope drift?
- **Decision discipline:** Are choices being filed as decisions, or living in
  chat?
- **Handoff discipline:** Are handoffs short, file-based, naming the next
  agent?
- **Phase plan freshness:** Is docs/phase_plan.md current (last-updated < 48h
  if work has been happening)?
- **Living-document hygiene:** Run the duplicate-heading scan from SOP §1
  across docs/phase_plan.md, PROJECT_CHARTER.md, STATUS.md, TASKS.md,
  docs/data/*.md. Any duplicates? Any file > 200 lines that shouldn't be?
  This is the early-warning signal for the "phase_plan grew to 820 lines"
  failure mode — catch it here, not after it has happened three more times.
- **Reproducibility debt:** Are we accumulating un-rebuilt artifacts? Has a
  fresh `make reproduce` passed in the current phase?
- **Agent budget:** Are dispatches reasonably scoped, or ballooning to 30+
  tool calls?
- **Decision closure:** Are docs/decisions/OPEN_*.md files being closed within
  one work session?

## What's working

(2-4 bullets. Be specific — name the artifact or behavior.)

## What's drifting

(2-4 bullets. Specific symptoms, not vibes.)

## What's stuck

(Active blockers. Owner. Proposed unstick.)

## Recommended adjustments

(1-3 concrete changes to process, charter, or roster. For each, name the
artifact that would need to change.)

## Charter amendment proposed?

(Yes / No. If yes, draft the change to PROJECT_CHARTER.md and route to the
relevant agents for review.)

Constraints:
- Be specific. "Documentation could be better" is useless. "docs/phase_plan.md
  has 8 duplicate Phase 1 checklist blocks; needs pruning" is useful.
- Flag the same drift twice in two consecutive retros only as a Red — that
  means the previous retro's adjustment didn't take.
- The retro itself is filed as a "Retro" subsection within the current week's
  STATUS.md entry.
```
