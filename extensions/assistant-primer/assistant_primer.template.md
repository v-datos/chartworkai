# AI Assistant Primer & Repo Orientation

Welcome to the project! This is a repo-native onboarding guide to help you orient yourself and understand the rules, tools, and layout of this workspace.

---

## 1. Project Profile & Stack

This project runs on the following configuration:

- **Profile:** {{PROFILE_NAME_HERE — e.g. software-app, data-science, etc. must match PROJECT_CHARTER.md}}
- **Verify Command:** {{VERIFY_COMMAND_HERE — e.g. ./scripts/check_framework_compliance.sh . must match PROJECT_CHARTER.md}}

---

## 2. Directory Structure & Entry Points

Key files and folders you should know about:

| Directory/File | Purpose | Key Entry Point |
|---|---|---|
| `PROJECT_CHARTER.md` | Project mission, goals, and change log | Read first |
| `AGENTS.md` | Rostered agent roles and specifications | Check before coding |
| `STATUS.md` | Current phase status (updated in-place) | Update on changes |
| `TASKS.md` | Task list and checklist (updated in-place) | Update on progress |
| `docs/phase_plan.md` | Current phase active queue | Check for next steps |
| `docs/decisions/` | Archive of technical design decisions | Check for context |
| `docs/handoffs/` | Handoff notes between sessions/agents | Read latest handoff |
| `scripts/` | Shell verification and build scripts | Run to verify |
| `{{CODE_DIR/}}` | Core source code (e.g. `src/` or `lib/`) | Main implementation |

---

## 3. Rostered Roles

These are the active roles authorized in `AGENTS.md`:

- **{{Role 1}}**: {{Short description of Role 1 mission}}
- **{{Role 2}}**: {{Short description of Role 2 mission}}
- **{{Role 3}}**: {{Short description of Role 3 mission}}

---

## 4. Rules of Engagement

To keep the repository clean and compliant, you MUST follow these guidelines:

1. **In-place updates:** Never append duplicate sections to `PROJECT_CHARTER.md`, `STATUS.md`, `TASKS.md`, or `docs/phase_plan.md`. Always update these documents in place.
2. **Dated decision records:** When proposing a design change, file a dated decision record in `docs/decisions/` (format: `YYYYMMDD_decision_title.md`) and link it from `PROJECT_CHARTER.md`.
3. **Run verification:** Run the project's verification command:
   ```bash
   {{VERIFY_COMMAND_HERE}}
   ```
   and ensure it passes before you conclude your turn.
4. **No leftover scaffold files:** Ensure you clean up any scratch scripts or temporary files. Do not leave behind untracked files in the repository.
5. **No secret leaks:** Never commit API keys, passwords, or personal credentials. Use environment variables.
