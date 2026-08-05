# Prompt: Handoff Write-up — draft a handoff note from completed work

Use when an agent has finished a deliverable and needs to file the handoff.

---

```
You are {{AGENT_ROLE}} for {{PROJECT_NAME}}. You have just completed the
following work:

----- BEGIN WORK SUMMARY -----
{{WORK_SUMMARY: a description of what you did, files touched, decisions made
along the way, anything that didn't go as planned}}
----- END WORK SUMMARY -----

Your task is to produce a handoff note at docs/handoffs/{{YYYY-MM-DD}}_{{role}}.md
following the template at templates/handoffs/YYYY-MM-DD_agent.template.md.

The note must include:

1. **What was produced** — bullet list of deliverables with absolute or
   repo-relative file paths. State the change vs. prior state where relevant
   ("was: stub returning NotImplementedError; now: implemented with N tests").

2. **Where it lives** — filesystem locations, parquet table names if
   applicable, git branch/commit if relevant.

3. **What was decided along the way** — link any decision files created during
   this work. Flag any deferred decisions as `OPEN_*.md`.

4. **Known limitations** — MANDATORY section. Be honest about corners cut,
   assumptions made, edge cases not handled. If there are truly none, say so
   explicitly. This is what the next agent needs to plan around.

5. **How to verify** — specific commands or checks the next agent (or QA) can
   run to confirm the work behaves as advertised. Real commands, not
   pseudocode.

6. **Next agent in chain** — who consumes this work, what action they should
   take, what inputs they should use. Include a suggested dispatch ticket
   block (per SOP §2 format).

Constraints:
- Half-page maximum. The handoff is a pointer, not the work itself.
- Do not include narrative prose about how you felt about the task. Stick to
  what was produced, what's known, what's next.
- If the work spawned new TASKS.md entries (e.g., follow-up cleanup), list
  them in a "## Follow-ups added to TASKS.md" subsection.

Output: a single markdown file ready to commit at the path above, plus a
one-line update for TASKS.md (mark the in-progress task done, add any
follow-up tasks to the queue).
```
