# Contributing

Thanks for helping improve ChartworkAI. This document covers the dev setup, the checks your PR has
to pass, and the one convention that surprises newcomers: **substantive changes need a decision
record.**

## Dev environment

Requires Python 3.9 or newer.

**Supported and tested range: 3.9 – 3.13.** `requires-python` is `>=3.9` with no upper
bound, which is the normal convention for a library — capping it makes pip resolve to
an older release instead of saying why. The practical consequence is that pip will
install this on 3.14 too, a version CI does not exercise. It is expected to work
(the suite passed there when it was last run) but it is not a version we verify, so
treat a 3.14 problem as unsupported until 3.14 is added to the matrix and to the
classifiers together.

```bash
git clone https://github.com/v-datos/chartworkai.git
cd chartworkai
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

That installs the `chartworkai` CLI in editable mode plus `pytest` and `ruff`. Run the tests:

```bash
pytest
```

The core has **zero runtime dependencies** and that is a hard constraint, not an accident.
ChartworkAI governs projects in any language and must never impose a dependency tree on the repo it
audits. A PR that adds a runtime dependency needs a decision record arguing the case.

## The project dogfoods itself

This repo is managed with its own framework (see
`docs/decisions/20260607_DEC001_self_host.md`). The compliance checker runs against this
repository, and **your PR must keep the self-check passing:**

```bash
./scripts/check_framework_compliance.sh .
```

Once the Python CLI is installed, the same check is available as:

```bash
chartworkai check .          # exit 0 = pass, 1 = failures
chartworkai check . --json   # machine-readable output
```

Both must exit 0 before you open a PR. The full verification loop, including a bootstrap smoke
test into a temp directory:

```bash
sh -n scripts/check_framework_compliance.sh
sh -n scripts/init_project_from_framework.sh
python scripts/sync_framework_manifest.py --check
scripts/init_project_from_framework.sh /tmp/cw-example "Example Project" example_project
scripts/check_framework_compliance.sh /tmp/cw-example
```

Gates that trip people up: no duplicate `##` headings in living documents, no unresolved
`{{placeholder}}` tokens in active docs, `TASKS.md` has exactly one **In Progress** section and
uses checkbox bullets rather than tables, the current phase number in `docs/phase_plan.md` also
appears in `PROJECT_CHARTER.md`, and every decision file is linked from the charter.

A freshly bootstrapped scaffold **deliberately fails** the check until you fill in the
placeholders and remove the temporary `_framework_*` directories. That is the graduation gate, not
a bug.

## Decision records

Anything that changes scope, a shared convention, a schema, or phase gating gets a dated,
authority-stamped file in `docs/decisions/`. This is the traceability the whole framework exists
to provide — skip it and the change will be questioned six months from now with no answer
available.

**Filename:** `YYYYMMDD_<NS>###_<title>.md` — for example
`docs/decisions/20260613_DEC004_product_model.md`.

The namespace `<NS>` is one of:

| Namespace | Use for |
|---|---|
| `DEC` | Scope, methodology, and design decisions |
| `DQ` | Data-quality rulings |
| `SC` | Scope-change rulings |
| `MD` | Methodology / domain rulings |

The checker enforces this pattern, so a malformed name fails the build.

**Contents** — start from `templates/decisions/YYYYMMDD_decision.template.md`. Each file carries a
Date / Authority / Status header, then Context (with the options considered), Ruling, Rationale,
Implementation notes, Consequences per agent, and Related decisions.

**Link it from the charter.** Every non-README decision must appear in the `## 8. Decision log`
table in `PROJECT_CHARTER.md`:

```markdown
| 2026-06-13 | Product model and go-to-market strategy | Orchestrator | `docs/decisions/20260613_DEC004_product_model.md` |
```

An unlinked decision file is a compliance failure.

## Pull requests

- **Keep them small and focused.** One concern per PR. A refactor and a behavior change in the
  same diff will be sent back.
- **Tests for behavior changes.** New CLI behavior or a bug fix needs a test that fails before
  your change and passes after it.
- **Update `CHANGELOG.md`.** Add an entry under `## [Unreleased]` in the appropriate
  Added / Changed / Fixed / Removed group.
- **Change framework rules in `framework.json` first.** If you add or change profiles,
  required artifacts, layout, templates, prompts, scripts, or extensions, run
  `python scripts/sync_framework_manifest.py` and commit its shell/documentation projections.
  `python scripts/sync_framework_manifest.py --check` must pass.
- **Fill in the PR template** (`.github/PULL_REQUEST_TEMPLATE.md`), including the verification
  commands you actually ran.
- Write commit subjects in the imperative mood and keep them under ~72 characters.

## Code style

**Shell** — POSIX `sh`, not bash. No bashisms: no arrays, no `[[ ]]`, no `local`. Every script
starts with `#!/usr/bin/env sh` and `set -eu`. Every script must parse cleanly:

```bash
sh -n scripts/your_script.sh
```

Quote your expansions. The scripts run against arbitrary user repositories where paths contain
spaces.

**Python** — formatted and linted with ruff (line length 100, target `py39`):

```bash
ruff format .
ruff check .
```

Type hints are required on public functions. Support Python 3.9 through 3.13, so no
match statements and no `X | Y` unions at runtime.

**Markdown** — direct and concrete. Document what the thing does and what it costs, not how
exciting it is. Templates use `{{placeholder}}` tokens; keep them consistent with the existing
set, since the checker scans for unresolved ones.

**Stay assistant-agnostic.** Core operating documents must not hard-code a specific AI assistant's
name, slash commands, or file conventions. The checker has a tool-leak gate for exactly this.

## Reporting bugs and vulnerabilities

Ordinary bugs: open a GitHub issue with your version, platform, shell, and a reproduction.

Security vulnerabilities: **do not open a public issue.** Follow [`SECURITY.md`](SECURITY.md).

## License

By contributing, you agree that your contributions are licensed under the Apache License 2.0
([`LICENSE`](LICENSE)).
