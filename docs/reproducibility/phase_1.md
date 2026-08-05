# Reproducibility Report — Phase 1 (Agnosticism core)

**Date:** 2026-06-07
**Author:** Dogfood & Compliance QA
**Phase:** 1 — Agnosticism core (closing)
**Verify command (software-app profile):** `./scripts/check_framework_compliance.sh .` passes, the bootstrap smoke test behaves, and `sh -n` passes on the scripts.

## Result: PASS

| Check | Result |
|---|---|
| `sh -n` on both scripts | PASS |
| Framework self-check (`check_framework_compliance.sh .`, software-app profile) | PASS (exit 0) |
| Filled `software-app` project, no `docs/data/` triad | PASS (triad skipped) |
| Default `data-science` project missing the triad | FAIL as expected (still gated) |
| `software-app` bootstrap | exit 0; no `docs/data`, `Profile:` + `## Stack` present |
| `data-science` bootstrap | exit 0; data-contract triad created |
| FW-001 (checker assumed a consumer layout) | Resolved |

## Exit criteria (Phase 1)

- [x] Profile / deliverable-type model (T-002)
- [x] Profile-aware checker; triad required only for data profiles (T-006)
- [x] `software-app` passes with no data contracts; data profiles still gated
- [x] Per-profile reproducibility documented (T-003)
- [x] De-Pythoned templates + charter `## Stack` block + profile-aware bootstrap (T-004)
- [x] Software / Deployment / Frontend optional roles + portability note (T-005)

## Carried forward

- FW-002, FW-003, FW-004, FW-005 (base-prose residue), FW-007..FW-010 remain open (Phase 2–3). See `docs/data/watchlist.md`.

**Phase 1 closes.** Promote to Phase 2 (package the four chosen extensions).
