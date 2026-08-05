# DEC-008 — Version the framework and the package separately, with prefixed tags

**Date:** 2026-08-05
**Authority:** Orchestrator
**Status:** Decided

## Context

This repository ships two artifacts with genuinely different maturities:

- **The framework** — the Markdown contracts, templates, agent specs, prompts and profiles. Declared in `framework.json`, currently **1.0.0**, tagged `v1.0.0`, and validated across nine real implementations.
- **The `chartworkai` Python package** — new, unpublished, with a public API (CLI flags, `--json` schema, MCP tool names) that has never met an external user. Declared in `pyproject.toml`, currently **0.1.0**.

Forcing one number on both is wrong in either direction: publishing the package as 1.0.0 would promise API stability we have no evidence for, and demoting the framework to 0.x would misrepresent something already proven in production. A prior review flagged the skew as needing an explicit decision.

The tag namespace is the real problem. `v1.0.0` already exists, so tagging the package release `v0.1.0` would read as the project going backwards.

## Ruling

1. **Keep the two versions independent.** `framework.json` versions the framework contracts; `pyproject.toml` versions the Python package. Neither is derived from the other.
2. **Namespace the tags by artifact.** Package releases are tagged **`chartworkai-vX.Y.Z`** (first: `chartworkai-v0.1.0`). The bare `vX.Y.Z` namespace stays reserved for the framework, where `v1.0.0` already lives.
3. **The package stays 0.x until an external user has run it.** While 0.x, the CLI surface, the `--json` report schema and the MCP tool names may change in a minor release; the `CHANGELOG` must say so. 1.0.0 is the promise that they will not.
4. **`CHANGELOG.md` covers both**, labelling each entry with the artifact it belongs to when ambiguous.

## Rationale

Semantic versioning is a promise about compatibility, and the honest promise differs per artifact. Consumers of the framework depend on file conventions that have been stable for months; consumers of the package will depend on flags and a JSON schema written this week. Prefixed tags are the standard way repositories with more than one release stream stay legible, and they cost nothing.

## Implementation notes

- First package release: `chartworkai-v0.1.0`, artifacts `chartworkai-0.1.0-py3-none-any.whl` and `chartworkai-0.1.0.tar.gz`, both passing `twine check`.
- `RELEASING.md` documents the sequence; publishing requires PyPI credentials and is performed by a human.
- `chartwork` (unsuffixed) remains unclaimed on PyPI and should be registered as a placeholder pointing at `chartworkai`, so the obvious near-miss of our own name cannot be squatted (DEC-007).

## Consequences per agent

- **Release & Compliance Engineer:** bump only the artifact that changed; tag with the matching prefix; never publish from CI without an explicit decision to automate it.
- **Framework Architect:** a breaking change to the CLI surface, the `--json` schema, or the MCP tool names is a minor bump while 0.x, and must be recorded in the changelog.

## Related

- DEC-007 (final product name), DEC-006 (Apache 2.0), DEC-004 (open-core model).
