# Watchlist — Framework issues & risks (FW-###)

Repurposed for this profile: instead of data-quality anomalies, this tracks framework issues and risks surfaced by the audit and by dogfooding. See `docs/decisions/20260607_DEC002_profile_model.md`.

## Open

| ID | Severity | Issue | Owner | Next action / task |
|---|---|---|---|---|
| FW-002 | Low | `framework.json` requires `docs/handoffs/README.md` while the checker accepts README-*or*-a-note | Template & Docs Engineer | Reconcile manifest ↔ checker |
| FW-003 | Low | Committed cruft (`.DS_Store`, `.idea/`) in the framework repo | Template & Docs Engineer | Clean + gitignore (Phase 3) |
| FW-004 | High | README / FRAMEWORK_OVERVIEW still carry origin-project + data-science framing | Template & Docs Engineer | Repositioning (T-012, Phase 3) |
| FW-005 | High | "Reproducibility = byte-identical rebuild" assumed in base prose | Framework Architect | Per-profile reproducibility now defined (DEC-003); de-Python base prose in T-004 |
| FW-007 | Med | Living-document decay (stale/bloated phase_plan & STATUS) not caught | Dogfood & Compliance QA | Generate phase_plan + decay checks (T-008) |
| FW-008 | Med | Recurring extensions unpackaged | Template & Docs Engineer | Extension modules (T-007) |
| FW-009 | Low | Handoffs collapse with a single sequential agent | Framework Architect | TASKS-findings within phase; formal at close (T-010) |
| FW-010 | Med | `_framework_*` scaffold cleanup skipped; no checker guard | Template & Docs Engineer | Fail-on-leftover-scaffold (T-011) |

## Decided / Resolved

| ID | Issue | Resolution |
|---|---|---|
| FW-001 | Checker assumed a consumer layout; flagged the framework's own templates/agents/prompts placeholders | Resolved 2026-06-07 (T-006): framework-repo self-detection scopes the placeholder scan to this project's operating artifacts. |
| FW-006 | No deliverable-type / profile concept | Resolved 2026-06-07 (T-002): profile model in framework.json v0.4.0 + `profiles/`; checker is profile-aware. |

## How to add an entry

Append a row under Open with the next FW-### id, a severity (Low/Med/High), the issue, an owner, and the resolving task. Move to Decided/Resolved when closed.
