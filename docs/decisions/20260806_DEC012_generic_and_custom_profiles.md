# DEC-012 — Make presets optional and support custom profiles

**Date:** 2026-08-06
**Authority:** Framework Architect / Dogfood & Compliance QA
**Status:** Decided

## Context

ChartworkAI's six deliverable profiles were implemented as a closed CLI choice. They are useful
presets, but treating them as the universe of supported projects contradicts the product's
project-agnostic mission. Legal work, hardware programs, policy projects, education, fieldwork,
and future domains should not have to mislabel themselves to initialize the governance core.

Older ChartworkAI projects may omit the `Profile:` line and historically receive the
`data-science` contract. Changing that interpretation would silently weaken their checks.

## Ruling

1. `generic` is the default for new initialization and installs only the universal governance
   contract.
2. The existing six profiles remain unchanged as optional, manifest-defined presets.
3. A custom JSON profile may extend `generic` or one preset and add required files, required and
   scaffold directories, default roles, and validation commands.
4. Initialization validates and copies the custom contract to `chartworkai.profile.json`; the
   Python checker enforces it on later runs.
5. Validation commands are recorded in the charter and reported by the checker but never executed
   implicitly.
6. Projects with no `Profile:` line retain the legacy `data-science` interpretation.
7. The dependency-free shell tools support `generic` and the six presets. When a custom profile is
   detected, the shell checker delegates to the installed Python package rather than parsing JSON
   with ad hoc shell logic.
8. The framework contract version advances from 1.1.0 to 1.2.0. Package versioning remains
   independent under DEC-008.

## Security constraints

- Custom profile JSON is bounded to 64 KiB and must be a regular, non-symlinked file.
- Unknown fields, invalid schema versions, preset-name shadowing, duplicate values, multiline
  commands, and absolute or traversing paths are rejected.
- Required artifacts must resolve inside the project before they count as present.
- Profile commands are data, not executable configuration.

## Backward compatibility

- `--profile data-science`, `software-app`, `database`, `competition-ml`, `investigation`, and
  `deployed-service` retain their profile requirements and scaffold layouts.
- The standalone shell and Python scaffolds remain byte-identical for `generic` and all presets.
- Legacy projects without a profile continue to receive the data-contract triad requirement.

## Related

- T-025, DEC-002, DEC-003, DEC-011, FW-006.
