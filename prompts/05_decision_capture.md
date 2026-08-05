# Prompt: Decision Capture — distill a discussion into a decision file

Use when a discussion (chat, code review, agent exchange) has produced a
ruling that needs to be filed.

---

```
You are the Orchestrator. A discussion has reached a conclusion that warrants
a decision file.

Source material (paste below):
----- BEGIN SOURCE -----
{{TRANSCRIPT_OR_NOTES}}
----- END SOURCE -----

Your task is to produce a decision file at docs/decisions/{{YYYYMMDD}}_{{slug}}.md
following the template at templates/decisions/YYYYMMDD_decision.template.md.

Steps:

1. **Identify the authority.** Which agent's expertise covers this ruling?
   - Domain question → Domain Expert
   - Schema / data quality → Producer (with Domain Expert input on interpretation)
   - Statistical method → Analyst
   - Scope or process → Orchestrator
   - Reproducibility / testing → QA Engineer
   If multiple authorities, list all and name the lead.

2. **Assign an ID.** Read docs/data/watchlist.md for the next available
   {{prefix}}-NNN. If this is a non-data decision, pick an appropriate prefix
   (SC- for scope, MD- for methodology, etc.).

3. **Extract the context.** What situation prompted the decision? What
   evidence (counts, examples) was presented? What options were on the table?
   Be quantitative where the source allows.

4. **State the ruling.** Use Option A / B / C language if alternatives were
   compared. The ruling must be precise enough that an implementer cannot
   reasonably misinterpret it. If sub-rules apply (e.g., "use X if condition
   A; use Y if condition B"), enumerate them.

5. **Write the rationale.** Why this option beats the alternatives. Cite
   evidence or domain reasoning. Anticipate the reader six months from now.

6. **Implementation notes.** Concrete next steps for the implementing agent.
   Include code-shape hints if relevant. Specify which files change, which
   schemas update, whether a rebuild is needed.

7. **Consequences per affected agent.** Who has to change what?

8. **Cross-references.** Link to related decisions, superseded decisions,
   and relevant artifacts.

Constraints:
- Do not invent context the source doesn't provide. If the source is thin,
  flag it as "context to be expanded" and note what's missing.
- Use neutral, precise language. The decision file is permanent project
  history.
- The Status field starts as "Decided" (not "Resolved" — that requires
  implementation verification).

Also produce:
- A one-line entry to append to PROJECT_CHARTER.md §8 Decision log.
- A one-line entry to update in docs/data/watchlist.md (move from Open to
  Decided, or add new row).

Output: three blocks — the decision file, the charter line, the watchlist
update.
```
