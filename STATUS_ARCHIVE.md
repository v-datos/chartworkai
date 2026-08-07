# STATUS archive — ChartworkAI

Historical `STATUS.md` entries, moved here to keep the live file within its
line budget. Newest first; the current entry lives in [`STATUS.md`](STATUS.md).

This file contains archived status reports for the AI Workflow Framework productization project.

---

## 2026-06-07 — Phase 2: T-007 external-tracker sync (first extension)

**Prepared by:** Orchestrator

**Shipped:**
- Established `extensions/` as the home for optional, opt-in modules (with a catalog README).
- `extensions/external-tracker-sync/` — README + `integration.template.md` + a tracker-agnostic `sync_tracker.sh`. Mirrors `TASKS.md` / `STATUS.md` to ClickUp/Linear/Notion/etc. Principles: the repo is the source of truth, the tracker is a one-way read-only mirror, and integration config lives in `docs/integrations/` — never pasted into `AGENTS.md` (the audit caught one project doing exactly that).
- Listed in `framework.json` + `INITIALIZATION_GUIDE.md`.

**Verified:** `sh -n` clean; a dry run mirrors STATUS + TASKS; the framework still passes its own check.

**Next:** T-007b — the remaining three extensions (claims gate, experiment log, assistant primer).

---

## 2026-06-07 — Phase 1 CLOSED (T-005 + agnosticism core complete)

**Prepared by:** Orchestrator

**Shipped (T-005):**
- Three optional software roles in `agents/_optional/`: Software Engineer (software-app producer), Frontend Engineer, Deployment Engineer — the roles the audit showed were missing for deployed-app projects.
- `PORTABILITY.md` — how the framework travels across any tech stack, any modern AI assistant, and any language/locale (keep only the checker's structural labels in English).
- Rostered in `templates/AGENTS.template.md` + `INITIALIZATION_GUIDE.md`.

**Phase 1 (Agnosticism core) is complete and verified** — see `docs/reproducibility/phase_1.md`. The framework now natively supports non-data-science projects end to end.

**Promoted to Phase 2 — Productization.** Next: package the four chosen extensions (T-007, starting with external-tracker sync) and the structural living-doc fix (T-008).

---

## 2026-06-07 — Phase 1: T-004 (de-Python templates + profile-aware bootstrap)

**Prepared by:** Orchestrator

**Shipped:**
- Charter template gains a `## Stack` block (language/runtime, package manager, build/test/**verify** commands) + a `Profile:` line; the verify command is the project's profile-specific definition of "reproducible."
- Shared conventions de-Pythoned: tooling, the reproducibility contract, the repo-layout note, and the notebooks rule are now profile-neutral (the data-science layout/notebooks are explicitly marked as such).
- The bootstrap is profile-aware: `init_project_from_framework.sh ... [PROFILE]` writes a `Profile:` line + Stack block and **skips the `data/` layout + contract triad for non-data profiles**.
- **Verified:** a software-app bootstrap creates no `docs/data`; a data-science bootstrap creates the triad; both exit 0.

**Next:** T-005 — software/deployment/frontend optional roles + an i18n / multi-assistant note, then Phase 1 closes → Phase 2 (the four extensions).

---

## 2026-06-07 — Phase 1: profile system keystone

**Prepared by:** Orchestrator

**Shipped:**
- The **profile / deliverable-type model** — `framework.json` v0.4.0 (`profiles` + `default_profile`), and `profiles/{README,software-app,data-science}.md`.
- A **profile-aware compliance checker** — the `docs/data/` contract triad is required only for data profiles; a `Profile:` line in the charter selects the profile; framework-repo self-detection scopes the placeholder scan to operating artifacts (**resolves FW-001**).
- **Verified four ways:** framework self-check PASS; a filled `software-app` project with no data triad PASS; a default data-science project missing the triad FAIL (still gated); bootstrap smoke test exits 0 with the AGENTS graduation gate intact.

**Decisions filed:** DEC-003 (Phase-1 direction: software-app first; profile system; four packaged extensions).

**Dogfood note:** running the framework's own verification immediately caught two bugs in the first checker draft (a regex matching "non-data-science"; a too-shallow placeholder prune) — both fixed. Dogfooding paying for itself.

**Next:** T-004 — de-Python the templates, add a charter `## Stack` block, wire profile selection into the bootstrap.

---

## 2026-06-07 — Phase 0: dogfood install

**Prepared by:** Orchestrator

**Shipped this week:**
- Four framework consistency fixes (CI removed in favor of a local `make verify`; bootstrap now instantiates the rich `AGENTS.md` with compliance as a graduation gate; the methodology's six "phases" renamed to "stages"; `docs/domain/` scaffolded + compliance-checked, `docs/weekly/` dropped, reproducibility reports standardized to `phase_{N}.md`). Framework bumped to v0.3.0.
- Cross-project audit of 9 real implementations spanning research, competition ML, curated databases, investigative journalism, a deployed service and a Node/TypeScript web app — across three different AI assistants and two human languages.
- Dogfood install: the framework now runs on itself — charter, roster, phased roadmap, decisions, and this status file.

**In progress:**
- Phase 0 close: run + triage the compliance checker on the framework repo; await user sign-off on charter v1 and OQ1–OQ4.

**Decisions filed:**
- DEC-001 — self-host the productization with the framework (dogfood).
- DEC-002 — adopt a profile / deliverable-type model; this project uses a non-data-science profile.

**Blockers:** none.

**Next:** on sign-off, promote to Phase 1 (Agnosticism core) and dispatch the Framework Architect to draft the profile model + the per-profile reproducibility contract.
