# Prompt: Initial Planning — generate the first PROJECT_CHARTER

Use this prompt at project kickoff. Paste your project brief in place of `{{BRIEF}}` and run.

---

```
You are the Orchestrator for a new project. The user has provided the
following project brief:

----- BEGIN BRIEF -----
{{BRIEF}}
----- END BRIEF -----

Your task is to produce a first-draft PROJECT_CHARTER.md following the template
at templates/PROJECT_CHARTER.template.md.

Specifically, fill in:

1. **Mission** — one paragraph that a stranger could read and correctly predict
   what the project will and won't do. Be specific about scope (data, audience,
   time range) and about output type (report? product? dashboard?). Avoid
   aspirational language; prefer verifiable claims.

2. **Non-goals** — at least 3 explicit items the project will NOT do, each with
   a one-line justification. This is where most charters fail; be aggressive
   about cutting scope.

3. **Research / product questions** — 5–10 numbered questions, grouped by the
   phase that will answer them. Each question should be answerable, not a topic.
   "How does X relate to Y?" is a topic; "What is the slope of X over period
   P, with CI?" is a question.

4. **Objectives** — a table mapping objectives to owning agents to deliverables.
   Objectives are verifiable; deliverables are file paths.

5. **Phases** — 4–7 phases, each with a one-line goal and an explicit exit
   criterion. Exit criteria are gated on quality, not dates.

6. **Team** — minimum: Orchestrator, Domain Expert (renamed for the domain),
   Producer (e.g., Data Engineer), Analyst, QA/Reproducibility. Optional roles
   pulled from agents/_optional/ as the brief warrants.

7. **Success criteria** — a 3-5 item bulleted list. Each item should be
   testable.

8. **Risks** — at least 5 rows in the risk table, with mitigation and owner.

9. **Glossary** — define any domain terms a new team member would need.

Constraints:
- Do not invent technical specifics the brief doesn't support.
- When the brief is ambiguous, raise a clarifying question in a "## Open
  questions for the user" section at the bottom rather than guessing.
- Keep the draft to ~300 lines or less. Detail belongs in linked docs, not
  the charter.

Output format: a single markdown file ready to commit as PROJECT_CHARTER.md.
```
