# DEC-003 — Phase 1 direction: software-app first; build the profile system; package four extensions

**Date:** 2026-06-07
**Authority:** Framework Architect / Orchestrator
**Status:** Decided

## Context

Phase 0 closed. The user set Phase-1 direction: build `software-app` as the first reference profile, and prioritize four packaged extensions (external-tracker sync, claims gate, experiment log, assistant primer).

## Ruling

1. Implement the profile / deliverable-type model (DEC-002) with `software-app` as the reference non-data profile and `data-science` as the documented default.
2. Make the compliance checker profile-aware: the `docs/data/` triad is required only for data profiles (data-science, database, competition-ml); a `Profile:` line in PROJECT_CHARTER.md selects the profile (first token; default data-science → backward-compatible).
3. Add framework-repo self-detection so the framework's own product-surface placeholders don't fail its own check (resolves FW-001).
4. The four chosen extensions set the Phase-2 priority order.

## Rationale

`software-app` is the highest-value agnosticism proof (web/app, zero data pipeline). Keeping `data-science` as the default preserves backward compatibility with all existing installs.

## Implementation notes (shipped this session)

- `framework.json` v0.4.0: `profiles` + `default_profile`; the data-contract triad moved out of universal `required_files` into the `data-science` profile.
- `profiles/README.md`, `profiles/software-app.md`, `profiles/data-science.md`.
- `scripts/check_framework_compliance.sh`: first-token profile detection, conditional triad, framework-repo placeholder scope.
- **Verified four ways:** framework self-check PASS; a filled software-app project with no triad PASS; a default data-science project missing the triad FAIL (still gated); bootstrap smoke test exits 0 with the AGENTS graduation gate intact.
- **Dogfood note:** the first checker draft had two bugs (a regex that matched "non-data-science"; a too-shallow placeholder prune) — both surfaced immediately by running the framework's own verification.

## Consequences per agent

- **Template & Docs Engineer:** next, de-Python the templates + add a charter `## Stack` block + wire profile selection into the bootstrap (T-004).
- **Dogfood & Compliance QA:** the verify gate now covers profile detection in both directions.

## Related

DEC-002 (profile model). Resolves FW-001, FW-006; partially addresses FW-005.
