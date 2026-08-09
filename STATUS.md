# STATUS — ChartworkAI (formerly AI Workflow Framework)

## 2026-08-09 — Concierge beta opened

**Prepared by:** Orchestrator

**In progress:**
- **T-021 dispatched** — a fixed-scope, 14-day paid concierge beta is being prepared
  for exactly three external design partners.
- **Evidence boundary defined** — completion requires three paid external installs,
  measured time to the first clean strict check, one governed action and follow-up per
  partner, and final publication permission for at least one case study.
- **Privacy boundary defined** — only de-identified attestations belong in Git; partner
  identities, repositories, payments, consent records, and raw notes remain private.

**Blocked on the project owner:** approve the commercial terms and identify or authorize
outreach to three external partners. T-021 remains open until the real engagements and
case-study approval are complete.

---

## 2026-08-09 — Public documentation site

**Prepared by:** Orchestrator

**Shipped:**
- **T-019 complete** — https://v-datos.github.io/chartworkai/ publishes the canonical
  implementation guide as ChartworkAI's responsive documentation front door.
- **Reproducible publishing** — generated sources, strict MkDocs builds, offline link and
  accessibility checks, protected CI, and OIDC GitHub Pages deployment are repository-owned.
- **Verified live** — PR #7 passed all 21 checks; Pages run 31338586422 deployed successfully;
  desktop and short-phone browser QA passed with search, deep links, navigation, and no console
  warnings or document overflow.

**Next:** dispatch T-021 — paid concierge beta with three design partners. Phase 4 remains open.

---

## 2026-08-07 — Generic core, public release, and CrewAI adapter

**Prepared by:** Orchestrator

**Shipped:**
- **Optional presets (T-025 / DEC-012)** — new initialization defaults to the
  project-agnostic `generic` core; the six existing preset flags retain their contracts.
- **Project-owned profiles** — `chartworkai init --profile-file FILE` validates and
  persists custom roles, required artifacts, directories, and validation commands while
  inheriting from generic or one preset.
- **Fail-closed safety** — bounded non-symlinked JSON, strict fields and schema version,
  confined artifact paths, no preset shadowing, and no implicit command execution.
- **Legacy compatibility** — old projects without a `Profile:` line still receive the
  `data-science` contract; generic and all presets retain standalone shell support.
- **Verified distribution** — full tests, shell/Python generic parity, both self-audits,
  wheel/sdist validation, clean-wheel generic/custom scaffolds, custom shell delegation,
  and artifact privacy checks pass.
- **ChartworkAI 0.2.0 published (T-026)** — the TestPyPI proof and clean install passed
  for commit `e82bde2`; tag `chartworkai-v0.2.0` points to that exact commit. The
  production OIDC workflow repeated provenance, Linux/macOS/Windows, package, secret,
  and personal-identifier gates before publishing. A fresh public install, version
  check, generic-default initialization, and state smoke test passed. PyPI and the
  matching GitHub release are live.
- **CrewAI governance adapter complete (T-018 / DEC-013)** — independent
  `chartworkai-crewai` 0.1.0 provides schema-v1 redacted immutable manifests, sync/async capture,
  explicit handoffs, and no automatic decisions. CrewAI remains user-supplied under the CVE
  embargo. Final QA passed 1,374 core and 75 adapter tests, strict self-audit at 33/0/0, strict
  Twine validation for four artifacts, offline CrewAI 1.15.10/1.15.13 checks, and a security
  re-audit with no blockers. The supported operating-system boundary is Linux and macOS.

**Next:** dispatch T-019 — docs site and landing page. Phase 4 remains open.

---

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
- **`framework.json` is authoritative (T-016)** — framework contract 1.1.0 now drives
  Python profile/file/layout behavior directly and generates the standalone POSIX shell
  projection plus public profile tables. CI rejects projection drift. FW-002 is resolved,
  and a built wheel proves the manifest and shell configuration ship correctly.

**Next:** build the CrewAI adapter (T-018).

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

Older entries: [`STATUS_ARCHIVE.md`](STATUS_ARCHIVE.md).
