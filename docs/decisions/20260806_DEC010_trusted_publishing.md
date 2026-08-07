# DEC-010 — Publish through staged OIDC workflows

**Date:** 2026-08-06
**Authority:** Orchestrator (with the user) / Dogfood & Compliance QA
**Status:** Decided

## Context

DEC-008 established independent package versioning and the `chartworkai-vX.Y.Z` tag
namespace, but its implementation notes assumed a human would upload with long-lived
PyPI credentials and prohibited CI publishing. The release implementation later moved
to PyPI Trusted Publishing without recording that security decision. A pre-release
audit also found that the runbook pushed the production tag before the required
TestPyPI trial.

The choices are:

1. Return to a manually stored PyPI API token.
2. Keep Trusted Publishing, but allow a production tag before TestPyPI succeeds.
3. Use Trusted Publishing with an explicit TestPyPI-first gate and a protected
   production environment.

## Ruling

1. **The workflow uploads; a human authorizes.** `.github/workflows/publish.yml` uses
   OIDC to obtain a short-lived credential. No PyPI API token is stored in GitHub or in
   this repository.
2. **TestPyPI must succeed first.** The exact final commit is published manually to
   TestPyPI and installed from TestPyPI before any production tag is created.
3. **A production tag is the release trigger.** `chartworkai-vX.Y.Z` must point at the
   current tip of `main`, match the packaged version, and pass the complete release
   gate before the protected `pypi` environment is approved.
4. **Only `publish.yml` is trusted.** Neither PyPI instance may trust the historical
   `release.yml` filename because older reachable commits contain weaker versions of
   that workflow.
5. **The first release remains single-maintainer.** The aggregate `CI` check applies to
   administrators and the production environment requires explicit approval. A second
   independent reviewer and prevention of self-approval become required before adding
   another maintainer or selling enterprise release assurances.
6. This decision supersedes only DEC-008's manual-credential and no-CI publishing
   clauses. DEC-008's independent versions and prefixed tag namespace remain in force.

## Rationale

Trusted Publishing removes the long-lived release secret while binding each upload to
the repository, workflow filename, and GitHub environment. Requiring a successful
TestPyPI installation before creating the production tag preserves the staging gate:
the production workflow cannot begin until the artifact has already been exercised
through the same publishing mechanism.

The current project has one maintainer, so preventing self-approval would make releases
impossible rather than safer. Enforcing CI for administrators and retaining a separate
production approval are the strongest controls that do not fabricate a second reviewer.

## Implementation notes

- Pending publishers on both indexes use owner `v-datos`, repository `chartworkai`,
  workflow `publish.yml`, and environments `testpypi` / `pypi` respectively.
- `RELEASING.md` is ordered so TestPyPI verification precedes tag creation.
- Branch protection requires the stable aggregate `CI` job and includes administrators.
- The TestPyPI environment accepts only `main`.
- The production environment accepts only tags matching `chartworkai-v*`.

## Consequences per agent

- **Dogfood & Compliance QA:** record the successful TestPyPI run and installation
  before authorizing a tag.
- **Orchestrator:** never report a tag or upload as complete until the remote state
  confirms it.
- **Release & Compliance Engineer:** publish only through `publish.yml`; do not use
  `twine upload` or add a repository secret as a fallback.

## Related

- DEC-009 (pre-release audit gate), DEC-008 (versioning and tags), DEC-006 (license).
