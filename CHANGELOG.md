# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [chartworkai 0.1.0] - 2026-08-05

First release of the Python package. The framework's Markdown contracts remain at 1.0.0
and are versioned separately (DEC-008).

> While the package is 0.x the CLI surface, the `--json` report schema and the MCP tool
> names may change in a minor release.

### Added

- **ChartworkAI Python package and CLI.** The framework ships as an installable package
  (`pip install chartworkai`) exposing `chartworkai check [PATH]` — the compliance linter, which exits
  0 on pass and 1 on failures. Supports `--json` for machine-readable output and `--strict`.
  Zero runtime dependencies, so it never imposes a dependency tree on the repository it audits.
- **`chartworkai init`** — scaffolds a project's governance layer from a plain
  `pip install`, with no clone of this repository. The templates, agent specs, prompts and
  extensions ship inside the wheel. Output is byte-identical to the shell bootstrap, and CI
  diffs the two on every change.
- **`chartworkai plan`** — regenerates `docs/phase_plan.md` from repository state (tasks,
  decisions, roster, status), carrying over the sections a human owns.
- **MCP server** — `chartworkai mcp` speaks the Model Context Protocol over stdio, so any
  assistant can call `chartworkai_check`, `chartworkai_state`, `chartworkai_file_decision`, and
  `chartworkai_file_handoff` natively. Implemented with the standard library alone to keep
  the zero-dependency promise.
- **`chartworkai state`** — prints where a project stands (phase, tasks, blockers, recent
  decisions and handoffs) as JSON.
- **`LICENSE`** — Apache License 2.0, with a `NOTICE` file. Chosen over MIT for its
  express patent grant and explicit trademark reservation, which suit the open-core
  boundary (DEC-006).
- **`SECURITY.md`** — supported versions, private vulnerability reporting through GitHub Security
  Advisories, and an honest security model covering the local-file/local-shell surface, the
  no-network / no-telemetry / no-credentials core, and the optional extensions that talk to
  third-party trackers.
- **`CONTRIBUTING.md`** — dev setup, the self-check every PR must keep passing, the decision-record
  convention, and code style for POSIX `sh` and Python.
- **`py.typed`** (PEP 561), so downstream type-checkers use the package's annotations.
- **Specs for the four remaining profiles** — `database`, `competition-ml`, `investigation`
  and `deployed-service` each now document their required artifacts, verify contract,
  default roles, layout and the real implementations they are drawn from. All six are
  first-class; nothing is advertised as "planned" any more. `framework.json` carries the
  full definition for each and is cross-checked against the checker by test.
- **CI now gates the distributables**: builds the sdist and wheel, runs `twine check`, fails
  if local artifacts leak into the sdist, installs *from the sdist* into a clean environment
  and scaffolds outside the repository, and asserts that `init` rejects unknown profiles and
  refuses to clobber. `ruff format --check` was added alongside `ruff check`.

### Fixed

Findings from three pre-release audits (DEC-009). The theme is that a governance tool
must never state something false:

- **The release process contradicted itself.** The runbook created the production tag
  before its "TestPyPI first" gate, while project state still described a manual token
  upload after the implementation had moved to OIDC. DEC-010 now records the publishing
  authority, TestPyPI must succeed against `main` before tagging, and the living
  documents report the actual release state.

Filesystem-safety and privacy findings from a fourth audit, all reproduced before fixing:

- **The shell bootstrap was still destructive.** The Python `init` had been hardened
  and the shell script had not, while the two were advertised as equivalent. It now
  refuses to overwrite an existing governance layer without `--force` and rejects
  unknown profiles, exactly as the Python entry point does.
- **The overwrite guard was too narrow.** It protected five documents; a curated
  decision index, domain note, style guide or data contract could still be replaced
  silently, and `_framework_*` directories were deleted outright. All of them are
  protected now.
- **Writes could escape the project through a symlink.** `chartworkai plan` would
  follow a symlinked `docs/phase_plan.md` and overwrite a file outside the
  repository. Every write now refuses a symlinked target or a path resolving outside
  the project root.
- **A typo in the charter could weaken compliance.** An unrecognised `Profile:` value
  was treated as non-data, so `data-sciece` silently dropped the data-contract
  requirement. An unknown profile is now read the strictest way *and* reported as a
  failure, in both implementations.
- **MCP tools accepted any path on the filesystem.** A tool argument is chosen by a
  model acting on text it did not author. Paths are now confined to the server's
  workspace, with `CHARTWORKAI_ALLOW_ANY_PATH=1` as a deliberate opt-out.

- **`init` refused nothing.** Re-running it — or pointing it at the wrong directory —
  silently rewrote the charter, status and tasks, discarding real work. It now refuses
  when canonical documents already exist and requires `--force` to overwrite. Adding
  ChartworkAI to an existing repository still works; only the canonical documents are
  protected.
- **Unknown profiles were accepted.** `--profile typo` was taken at face value and
  silently treated as non-data, handing the project the wrong governance contract. The
  value is now validated against the six known profiles.
- **`chartworkai state` returned success for a directory that was not a project**,
  emitting a plausible-looking report. It now fails with a clear message — an agent
  reading that over MCP would otherwise take it as truth.
- **The MCP server echoed back any `protocolVersion` a client sent**, claiming
  conformance to revisions it does not implement. It now negotiates down to a version it
  actually supports.
- **The `--json` `path` field used backslashes on Windows**, so a consumer matching on
  `docs/phase_plan.md` silently missed on that platform. Paths are now always POSIX-style.
- **`init` on a file path raised a bare `NotADirectoryError` traceback.** All CLI entry
  points now fail with a message and exit 1.
- The version was hard-coded in three places, one of which is published in `--json`; it
  is now derived from the installed distribution, leaving `pyproject.toml` as the only
  place a release number is written.
- The bootstrap named its seed decision `YYYYMMDD_charter_v1.md`, which does not match the
  `YYYYMMDD_<NS>###_<title>.md` pattern the checker enforces — so every freshly scaffolded
  project failed its own decision-naming check on a file the bootstrapper had just written.
  It is now `YYYYMMDD_DEC001_charter_v1.md` in both implementations.
- Newly generated projects no longer refer to the tool by its former name.

## [1.0.0] - 2026-06-13

Productization complete. The framework stopped being one project's internal method and became a
portable product that installs into any repository.

### Added

- **Profile / deliverable-type model.** `framework.json` gains `profiles` and `default_profile`,
  with `data-science` and `software-app` shipping and `database`, `competition-ml`,
  `investigation`, and `deployed-service` mapped out. Profiles are documented in `profiles/`.
- **Four optional extension modules** under `extensions/`, each templated and documented:
  `external-tracker-sync` (mirror tasks to an issue tracker), `claims-gate` (staging ledger that
  claims must graduate before they can be cited), `experiment-log` (run logging), and
  `assistant-primer` (session priming).
- **`scripts/generate_phase_plan.sh`** — a living-document generator for `docs/phase_plan.md`,
  plus staleness and bloat checks so the plan cannot silently rot.
- **Optional roles** for software delivery: software engineer, deployment engineer, and frontend
  engineer, in `agents/_optional/`.
- **`PORTABILITY.md`** — what the framework assumes about a host repo and how to move it.
- **Decision-log namespaces.** Decision files are namespaced `DEC`, `DQ`, `SC`, or `MD` and the
  checker enforces the `YYYYMMDD_<NS>###_<title>.md` filename pattern.
- **Install-UX gates.** A scaffold-cleanup check that fails while leftover `_framework_*`
  directories remain, and a tool-leak check that fails when an assistant-specific name or slash
  command leaks into a core operating document.
- **Open-core product model** — free core (CLI, linter, base templates) with paid profile and
  extension packs, recorded in `docs/decisions/20260613_DEC004_product_model.md` (DEC-004).

### Changed

- **The compliance checker is profile-aware.** The `docs/data/` contract triad is required only
  for data profiles; a `Profile:` line in the charter selects the profile, and the framework repo
  detects itself so its own templates are not scanned as unresolved placeholders.
- **Templates are de-Pythonized.** Language- and stack-specific assumptions were removed from the
  base templates in favor of a `## Stack` block on the charter that declares the project's
  language, package manager, and build / test / verify commands.
- **The bootstrap script is profile-aware** — `init_project_from_framework.sh` scaffolds according
  to the selected profile and runs the compliance check before it finishes.

## [0.3.0] - 2026-06-07

### Changed

- Replaced CI workflows with local verification — the framework verifies itself where the work
  happens instead of depending on a hosted runner.
- The bootstrap now instantiates the rich `AGENTS.md` with compliance as a graduation gate: a
  fresh scaffold deliberately fails the check until its placeholders are filled in.
- Renamed the methodology's six "phases" to "stages", freeing "phase" to mean a project's own
  roadmap phases.
- Standardized reproducibility reports to `docs/reproducibility/phase_{N}.md`.

### Added

- `docs/domain/` scaffolding, included in the compliance check.

### Removed

- `docs/weekly/`.

## [0.2.0] - 2026-05-01

### Added

- `scripts/init_project_from_framework.sh` — the bootstrap script that scaffolds a new project
  from the templates.
- Stronger compliance checks in `scripts/check_framework_compliance.sh`, covering required files
  and directories, seed decisions, and handoff notes.
- `framework.json` as the machine-readable manifest of required files, templates, prompts, and
  scripts.
- A pull request template and generic role specs for the orchestrator, analyst, data engineer,
  domain expert, and QA engineer.

[Unreleased]: https://github.com/v-datos/chartworkai/compare/chartworkai-v0.1.0...HEAD
[chartworkai 0.1.0]: https://github.com/v-datos/chartworkai/releases/tag/chartworkai-v0.1.0
[1.0.0]: https://github.com/v-datos/chartworkai/releases/tag/v1.0.0
