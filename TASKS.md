# TASKS — ChartworkAI

Last updated: 2026-08-07

## In Progress

## Queued (Phase 4 — ChartworkAI package & launch)

- [ ] **T-018 — CrewAI adapter (`chartworkai export/ingest crewai`)**
  Owner: Integrations Engineer
  Done criteria: CrewAI run IDs, traces, and outputs recorded as handoffs/decisions in the repo
- [ ] **T-019 — Docs site + landing page**
  Owner: Docs & GTM Engineer
  Done criteria: published site with the implementation guide as the front door
- [ ] **T-021 — Paid concierge beta with three design partners**
  Owner: Orchestrator (with the user)
  Done criteria: three external installs, measured setup time, and permission to publish one case study

## Backlog

- [ ] **T-022 — Retire the shell scripts** once the Python CLI reaches parity and one release has shipped with both
- [ ] **T-023 — Implement the four planned profiles** (database, competition-ml, investigation, deployed-service) or cut them from the docs
- [ ] **T-024 — LangGraph / Claude Code adapters** after the CrewAI adapter proves the pattern

## Done

- [x] **T-026 — Publish ChartworkAI 0.2.0 to PyPI + GitHub** — 2026-08-07 —
  Findings: TestPyPI workflow
  https://github.com/v-datos/chartworkai/actions/runs/31185596989 and a clean exact-version
  installation passed for commit `e82bde2`. Tag `chartworkai-v0.2.0` points to that
  exact commit. Production workflow
  https://github.com/v-datos/chartworkai/actions/runs/31185946789 passed provenance,
  Linux/macOS/Windows, package, secret, and personal-identifier gates before publishing.
  A fresh production `pip install chartworkai==0.2.0`, version check, generic-default
  initialization, and state smoke test passed. PyPI:
  https://pypi.org/project/chartworkai/0.2.0/. GitHub release:
  https://github.com/v-datos/chartworkai/releases/tag/chartworkai-v0.2.0.
- [x] **T-025 — Make presets optional and support custom profiles** — 2026-08-07 —
  Findings: framework contract 1.2.0 makes the domain-neutral `generic` core the
  initialization default while preserving the six presets and the legacy no-profile
  `data-science` behavior. Validated `--profile-file` contracts can extend generic or a
  preset with roles, artifacts, directories, and non-executed validation commands. Full
  tests, generic shell/Python parity, both self-audits, wheel/sdist checks, clean-wheel
  generic/custom scaffolds, shell delegation, and artifact privacy checks pass.
- [x] **T-016 — Make `framework.json` authoritative** — 2026-08-06 — Findings:
  DEC-011 makes framework contract 1.1.0 the source of truth for profiles, required
  artifacts, managed files, and scaffold layout. Python loads the packaged manifest
  directly; POSIX scripts and both profile tables use generated projections checked by
  CI. FW-002 is resolved through manifest-defined presence rules. Full tests, shell/Python
  parity, both compliance implementations, wheel/sdist checks, clean wheel installation,
  scaffold smoke testing, and artifact privacy checks pass.
- [x] **T-020 — Publish v0.1.0 to PyPI + GitHub release** — 2026-08-06 — Findings:
  TestPyPI proof and clean installation passed for commit `8938896`; the production tag
  `chartworkai-v0.1.0` points to that exact commit. The protected OIDC workflow passed
  provenance, Linux/macOS/Windows, package, secret, and personal-identifier gates before
  publishing. A fresh production `pip install chartworkai==0.1.0` and `chartworkai init`
  smoke test passed. PyPI: https://pypi.org/project/chartworkai/0.1.0/. GitHub release:
  https://github.com/v-datos/chartworkai/releases/tag/chartworkai-v0.1.0.
- [x] **T-015 — Port `init` and `plan` to Python** — 2026-08-05 — Findings: `chartworkai init` and `chartworkai plan` shipped. Assets (templates, agents, prompts, extensions, profiles, shell scripts) now ride inside the wheel via hatchling `force-include`, with `assets.py` resolving either a wheel or an editable checkout — verified by installing the built wheel into a clean venv and scaffolding outside the repo. Scaffolds are **byte-identical** to the shell bootstrap across profiles (60/60 files), now enforced by a CI job. One documented divergence: the shell truncates a phase title at `&`; Python reads it in full. Fixed a real bug in BOTH implementations — the seed decision was named `YYYYMMDD_charter_v1.md`, failing the checker's own naming rule in every freshly bootstrapped project.
- [x] **T-018b — Document MCP setup in the implementation guide** — 2026-08-04 — Findings: MCP config snippet and tool table added to both README and IMPLEMENTATION_GUIDE, plus the CLI commands block.
- [x] **T-017 — MCP server (`chartworkai mcp`)** — 2026-08-04 — Findings: JSON-RPC 2.0 over stdio implemented with the standard library alone, preserving the zero-dependency promise (an SDK purely to speak a documented wire protocol would have broken it). Four tools: `chartworkai_check`, `chartworkai_state`, `chartworkai_file_decision`, `chartworkai_file_handoff`. Added `src/chartworkai/state.py` for reading project state and writing auto-numbered decision/handoff records; generated decision filenames satisfy the compliance checker's own naming rule. Also added `chartworkai state` to the CLI.
- [x] **T-016b — License the public core under Apache 2.0** — 2026-08-04 — Findings: DEC-006. Chosen over MIT for its express patent grant (lowers enterprise legal-review friction) and trademark reservation (protects the ChartworkAI name while the code stays free — the boundary open-core needs). Added `NOTICE`; updated pyproject, README, CONTRIBUTING, CHANGELOG.
- [x] **T-014 — Release hygiene + CI** — 2026-08-04 — Findings: Added LICENSE (Apache-2.0) + NOTICE, SECURITY.md (threat model verified: no network calls in any script), CONTRIBUTING.md, CHANGELOG.md, and `.github/workflows/ci.yml` (py3.9–3.13 on Linux/macOS/Windows, ruff, `sh -n`, dogfooded `chartworkai check --strict`, and a shell/Python parity gate). Fixed a README clause that contradicted the license.
- [x] **T-013 — Port the compliance checker to Python with tests and `--json`** — 2026-08-04 — Findings: Scaffolded the `chartworkai` package (zero runtime deps) and ported all 16 checks. Verified 8/8 exit-code parity with the shell reference across fresh-scaffold, clean-project, assistant-leak, absolute-path, slash-command, malformed-decision, missing-triad, and `non-data-science` scenarios. Two documented divergences: prune all `_framework_*` dirs from the placeholder scan; parse the STATUS date from any `## YYYY-MM-DD` heading.
- [x] **T-012 — Repositioning + product model + GTM** — 2026-06-13.
- [x] **T-011 — Install UX (I)** — 2026-06-13.
- [x] **T-010 — Handoff resolution (H)** — 2026-06-13.
- [x] **T-009 — Decision-log hardening (G)** — 2026-06-13.
- [x] **T-008 — Structural living-doc fix (F)** — 2026-06-13.
- [x] **T-007b — Package the remaining extensions** — 2026-06-13.
- [x] **T-007 — External-tracker sync extension** — 2026-06-07.
- [x] **T-006 — Profile-aware compliance checker** — 2026-06-07.
- [x] **T-005 — Optional software/deployment/frontend roles + portability note** — 2026-06-07.
- [x] **T-004 — De-Python templates + charter `## Stack` block + profile-aware bootstrap** — 2026-06-07.
- [x] **T-003 — Pluggable reproducibility (initial)** — 2026-06-07.
- [x] **T-002 — Profile / deliverable-type model** — 2026-06-07.
- [x] **T-001 — Phase 0 close** — 2026-06-07.
- [x] **T-000 — Cross-project audit (9) + four consistency fixes + dogfood install** — 2026-06-07.

## Blockers

- None currently filed.
