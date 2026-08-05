# Reproducibility Report — Phase 2 (Productization)

**Date:** 2026-06-13
**Author:** Dogfood & Compliance QA
**Phase:** 2 — Productization (closing)
**Verify command (software-app profile):** `./scripts/check_framework_compliance.sh .` passes, the bootstrap smoke test behaves, and `sh -n` passes on all scripts.

## Result: PASS

| Check | Result |
|---|---|
| `sh -n` on all scripts (including extensions and generator) | PASS |
| Framework self-check (`check_framework_compliance.sh .`) | PASS (exit 0) |
| Multi-extension packaging (external-tracker, claims-gate, experiment-log, assistant-primer) | PASS (all templated and verified) |
| Living-document decay controls (staleness and STATUS-bloat checks) | PASS (correctly warning or failing on violations) |
| Decision-log prefix validation (DEC, DQ, SC, MD) | PASS (correctly enforcing namespace prefixes) |
| Sparse-decision warnings | PASS (warning logged when decisions are sparse) |
| Dual-weight handoff convention documented | PASS (updated in SOP.md and AGENTS.md) |

## Exit criteria (Phase 2)

- [x] The four chosen extensions packaged (T-007, T-007b)
- [x] Structural living-doc fix: generate `phase_plan` from state + staleness / STATUS-bloat checks (T-008)
- [x] Decision-log hardening: ID namespaces + sparse-decision warn (T-009)
- [x] Handoff resolution: TASKS findings within a phase; formal handoff at phase close (T-010)

## Carried forward

- FW-002 (reconcile handoffs README/note checker rule), FW-003 (gitignore cruft), FW-004 (repositioning prose), and FW-010 (fail-on-leftover-scaffold check) remain open for Phase 3. See `docs/data/watchlist.md`.

**Phase 2 closes.** Promote to Phase 3 (Install UX & launch).
