# DEC-011 — Make framework.json the executable contract

**Date:** 2026-08-06
**Authority:** Framework Architect / Dogfood & Compliance QA
**Status:** Decided

## Context

`framework.json` described profiles and required artifacts, but Python and POSIX shell
implemented separate hard-coded copies. Tests treated the checker as authoritative and
only asserted that the manifest had not drifted from it. Adding a profile or changing a
required artifact therefore required coordinated edits across code, scripts, and docs.

The POSIX scripts cannot parse JSON safely without adding `jq` or embedding an ad hoc
parser. Requiring the installed Python package would also remove their standalone use.

## Ruling

1. `framework.json` is the source of truth for profile names, the default profile,
   required files and directories, scaffold layout, managed files, and product inventory.
2. Python loads the packaged manifest directly at runtime through
   `chartworkai.manifest`.
3. POSIX scripts source `scripts/framework_config.sh`, a checked-in projection generated
   only by `scripts/sync_framework_manifest.py`.
4. The profile tables in `profiles/README.md` and `IMPLEMENTATION_GUIDE.md` are generated
   by the same command.
5. Tests and CI run the generator in check mode and fail on any drift.
6. The framework contract version advances from 1.0.0 to 1.1.0. Package versioning
   remains independent under DEC-008.

## Rationale

Direct JSON loading is the smallest reliable implementation for Python. A generated shell
projection keeps the shell scripts dependency-free and POSIX-compatible while making
duplication mechanical and verifiable instead of hand-maintained. Generated documentation
prevents the public profile list from becoming a third authority.

## Consequences per agent

- **Framework Architect:** changes profile/file rules in `framework.json` first.
- **Template & Docs Engineer:** runs `python scripts/sync_framework_manifest.py` and
  commits all generated projections with the manifest change.
- **Dogfood & Compliance QA:** runs the generator with `--check`, both compliance
  implementations, full tests, scaffold parity, and package installation.

## Related

- T-016, FW-002, DEC-008, DEC-003.
