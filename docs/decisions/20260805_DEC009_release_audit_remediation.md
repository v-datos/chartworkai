# DEC-009 — Three pre-release audits gate the first publication

**Date:** 2026-08-05
**Authority:** Orchestrator / Dogfood & Compliance QA
**Status:** Decided

## Context

Before publishing `chartworkai` 0.1.0, the package was audited three ways: by the author, by an external reviewer (Codex), and by an independent auditor agent (which terminated early on a session limit and produced nothing usable). The two completed audits found substantially different classes of defect, and the overlap between them was small:

- The **author's** pass found contract and type-system gaps: the version hard-coded in three places including the one published in `--json`, `state` returning success for a non-project, a missing `py.typed`, and a bare traceback on a bad `init` target.
- **Codex's** pass found behavioural and operational failures the author was too close to see: `init` silently destroying existing work, unknown profiles accepted, **CI red on Windows for three consecutive runs on `main`**, the repository still private so every published URL would 404, and non-compliant MCP version negotiation.

The author's initial verdict was "go with fixes." That was wrong: the CI status had never been checked, and the destructive `init` had been missed. Codex's "do not publish" was correct.

## Ruling

1. **Publication is gated on all blockers being closed**, not on the author's judgement that the package "feels ready". The blockers are: destructive `init`, unknown-profile acceptance, `state` reporting success for a non-project, MCP version negotiation, platform-dependent `--json` paths, and green CI.
2. **A governance tool must never state something false.** Where a defect made the tool assert something untrue — `state` describing a project that does not exist, `--json` paths that do not match on Windows, an MCP server claiming a protocol revision it does not implement — the fix is to fail honestly rather than to soften the output.
3. **`init` is non-destructive by default.** It refuses when canonical documents exist and requires `--force`. Adding ChartworkAI to an existing repository stays supported: only the canonical documents are protected, not the presence of other files.
4. **The Windows failures are scoped, not muted.** Shell/Python scaffold parity and POSIX permission bits are POSIX guarantees; those tests are skipped on Windows with a stated reason. The one genuine cross-platform defect they exposed — backslashes in the `--json` `path` field — was fixed in the product. Muting a red test to reach green is the failure mode this product exists to prevent, so each skip names why the assertion does not apply rather than that it is inconvenient.
5. **The release gates move into CI.** Building the artifacts, `twine check`, the sdist-install smoke test, and the safety assertions now run on every push instead of living only in `RELEASING.md`, where they depend on a human remembering.

## Rationale

The two audits agreeing would have been reassuring; the two audits finding *different* things is the actual result, and it argues for keeping more than one reviewer on a first release. An author auditing their own work reliably checks the things they were already thinking about.

## Consequences per agent

- **Dogfood & Compliance QA:** CI must be green — including Windows — before a tag is pushed. Check the run, do not assume it.
- **Framework Architect:** `--force`, the profile whitelist, and MCP negotiation are now part of the public surface; changing them while 0.x requires a changelog note.

## Related

- DEC-008 (versioning scheme), DEC-007 (final name), DEC-006 (Apache 2.0).
