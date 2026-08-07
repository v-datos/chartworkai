# Profile: generic

**Use when:** the project does not fit a preset, or its deliverable-specific rules have not
been defined yet.

## Contract

The generic profile installs only ChartworkAI's universal governance layer: charter, roles,
phase plan, status, tasks, decisions, handoffs, and domain knowledge. It adds no assumptions
about source code, data, reports, infrastructure, or deployment.

## Verification

The project defines its own validation commands in `PROJECT_CHARTER.md`. ChartworkAI records
and checks the governance contract; it does not execute project commands implicitly.

## Default roles

- Orchestrator
- Domain Expert
- Producer
- Reviewer
- QA / Reproducibility Engineer

Use `--profile-file` when these defaults are not enough. A custom profile extends this generic
core or one of the six presets and can add roles, required artifacts, directories, and validation
commands.
