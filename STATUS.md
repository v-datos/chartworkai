# STATUS — ChartworkAI (formerly AI Workflow Framework)

## 2026-08-06 — Phase 4: ChartworkAI package

**Prepared by:** Orchestrator

**Shipped:**
- **Renamed to ChartworkAI** and repositioned as *the governance layer for agentic work* (DEC-005). `aiwf` was taken on PyPI; `chartworkai` is available and ties to `PROJECT_CHARTER.md`.
- **`chartworkai` Python package scaffolded** — `pyproject.toml` + `src/chartworkai/` (`models.py`, `checks.py`, `cli.py`), **zero runtime dependencies**, Python ≥3.9.
- **Compliance checker ported** — all 16 checks, with `--json`, `--strict`, `--quiet`. Verified 8/8 exit-code parity against the shell reference, including the absolute-path false-positive and `non-data-science` profile regressions.
- **Release hygiene** — LICENSE (Apache-2.0), SECURITY.md, CONTRIBUTING.md, CHANGELOG.md, and a CI workflow that tests py3.9–3.13 on Linux/macOS/Windows, lints, dogfoods `chartworkai check --strict`, and gates shell/Python parity.
- **Two release defects fixed** — the installer now ships `generate_phase_plan.sh` to consumers, and that generator no longer fails with `cut: bad delimiter` on the multibyte em dash (which silently blanked every decision ID).
- **Apache License 2.0** adopted for the public core (DEC-006), with a `NOTICE` file — chosen over MIT for its express patent grant and trademark reservation, which fit the open-core boundary.
- **MCP server shipped (T-017)** — `chartworkai mcp` speaks JSON-RPC 2.0 over stdio using the standard library alone, exposing `chartworkai_check`, `chartworkai_state`, `chartworkai_file_decision`, and `chartworkai_file_handoff`. Any assistant can now enforce governance directly instead of waiting for a human to relay output. Added `src/chartworkai/state.py` and a `chartworkai state` command.

- **`init` and `plan` ported (T-015)** — `chartworkai init` and `chartworkai plan` complete the CLI. Framework assets now ride inside the wheel (hatchling `force-include`), so a plain `pip install` can scaffold a project with no clone of this repo — proven by installing the built wheel into a clean venv and scaffolding outside the repository. Shell and Python scaffolds are **byte-identical** (60/60 files, across profiles), now enforced by a CI job.
- **Bug fixed in both implementations** — the bootstrap named its seed decision `YYYYMMDD_charter_v1.md`, which fails the checker's own `YYYYMMDD_<NS>###_<title>.md` rule; every freshly scaffolded project was failing on a file the bootstrapper wrote. Now `YYYYMMDD_DEC001_charter_v1.md`.

- **ChartworkAI 0.1.0 published (T-020)** — TestPyPI proof and clean installation passed
  for commit `8938896`; tag `chartworkai-v0.1.0` points to that exact commit. The
  protected OIDC workflow repeated provenance, Linux/macOS/Windows, package, secret,
  and personal-identifier gates before publishing to PyPI. A fresh production
  `pip install chartworkai==0.1.0` and `chartworkai init` smoke test passed. The public
  GitHub release carries the changelog notes.

**Next:** make `framework.json` authoritative (T-016), then build the CrewAI adapter
(T-018).

---

## 2026-06-13 — Phase 3: T-011, T-012 Install UX & Launch (Phase 3 Complete)

**Prepared by:** Template & Docs Engineer

**Shipped:**
- Install UX (T-011): Shipped leftover `_framework_*` scaffold detection and tool-specific leak checker (slash commands and assistant name leaks) in `scripts/check_framework_compliance.sh`.
- CLI installer upgrades (T-011): Updated `scripts/init_project_from_framework.sh` to copy optional extensions to `_framework_extensions/` and guide the user on cleaning up temporary scaffolds.
- Repositioning & GTM (T-012): Drafted `docs/decisions/20260613_DEC004_product_model.md` defining the open-core business model (free CLI/core + paid profile packs/extensions) and target buyers (solo AI power-users, agencies, and teams). Linked the decision in `PROJECT_CHARTER.md` and answered open questions OQ1/OQ4.
- Phase 3 Close: Created phase 3 reproducibility report in `docs/reproducibility/phase_3.md` and updated `PROJECT_CHARTER.md` change log.

**Verified:**
- `sh -n` syntax check clean on compliance linter and initialization scripts (pass).
- Tested scaffold-cleanup check on simulated consumer project structures to verify it catches leftover `_framework_*` folders (pass).
- Tested tool-specific leak checker on simulated consumer projects to verify it catches slash commands and assistant names (pass).
- Verified target project initialization and installer guidance (pass).
- Compliance linter passes cleanly on the framework repository (pass).

**Next:** Product launch.

---

## 2026-06-13 — Phase 2: T-008, T-009, T-010 structural living-doc fixes and hardening (Phase 2 Complete)

**Prepared by:** Template & Docs Engineer

**Shipped:**
- Auto-generation of `phase_plan.md` (T-008): Shipped `scripts/generate_phase_plan.sh` to compile `docs/phase_plan.md` dynamically from the current repository state (matching agent states, exit criteria completion, recent decisions, and dispatch queue).
- Decay and Bloat Linter Controls (T-008): Updated `scripts/check_framework_compliance.sh` with staleness checks (comparing `phase_plan.md` date with `STATUS.md` date) and `STATUS.md` line count (150 lines cap) / entry count bloat warnings.
- Decision Log Hardening (T-009): Updated `SOP.md` with namespace prefixing rules (`DEC-`, `DQ-`, `SC-`, `MD-`). Configured the compliance checker to enforce this filename format and print warnings for sparse decision logs.
- Handoff Resolution (T-010): Standardized the dual-weight handoff rule in `SOP.md` and `AGENTS.md` (brief summaries in `TASKS.md` findings within a phase; full markdown handoffs only at phase boundaries).

**Verified:**
- `sh -n` syntax check clean on `generate_phase_plan.sh` (pass).
- Tested staleness, bloat, decision log namespaces, and sparse decision warnings on test fixtures (all fail or warn correctly with exit code 1 or 0).
- Successfully ran `./scripts/generate_phase_plan.sh .` to generate a clean, updated `docs/phase_plan.md` (pass).
- Compliance linter passes cleanly on the framework repository (pass).

**Next:** Phase 2 closes. Prepare for Phase 3 (Launch & Install UX: linting leftover scaffolds, tool-leak checkers, CLI installer, positioning decisions).

---

## 2026-06-13 — Phase 2: T-007b package remaining extensions (claims gate, experiment log, assistant primer)

**Prepared by:** Template & Docs Engineer

**Shipped:**
- Packaged the remaining three extensions under `extensions/` as optional, opt-in modules:
  - `claims-gate/` — Staging table and evidence-tier promotion for investigative/knowledge-base profiles. Includes a `check_claims.sh` verification script to ensure no unverified (Tier 3) assertions are promoted to findings.
  - `experiment-log/` — Run and score-tracking ledger for competition/ML profiles. Includes a `log_run.sh` automation script to log hyperparameters and metrics programmatically.
  - `assistant-primer/` — Repo-native onboarding guide for AI assistants. Includes a `verify_primer.sh` script to keep onboarding docs in sync with `PROJECT_CHARTER.md` and `AGENTS.md`.
- Updated catalog in `extensions/README.md` and registered them in the `framework.json` manifest.

**Verified:**
- Checked syntax of all scripts using `sh -n` (all pass).
- Tested `check_claims.sh` on valid and invalid claim files, verifying correct exit codes and error reports.
- Tested `log_run.sh` by appending runs to the experiment log.
- Tested `verify_primer.sh` on aligned and misaligned primer configurations.
- Framework repository compliance checker runs and passes (exit 0).

**Next:** T-008 — structural living-document decay fixes (phase_plan generation + staleness & bloat checks).

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

Older entries: [`STATUS_ARCHIVE.md`](STATUS_ARCHIVE.md).
